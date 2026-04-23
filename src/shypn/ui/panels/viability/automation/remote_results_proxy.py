#!/usr/bin/env python3
"""Remote Results Proxy — lazy-fetch architecture for sweep results.

Instead of downloading the entire results directory (potentially GB)
after a sweep completes, only ``summary.csv`` + ``config.json`` are
fetched immediately.  Individual condition directories are fetched
on-demand when the user requests plots, exports, or trajectory data.

Architecture:
    ┌────────────┐        summary.csv + config.json          ┌──────────┐
    │   Client   │ ◄──────────────── SSH ─────────────────── │  Server  │
    │ (UI panel) │       on-demand: condition_XYZ/            │  (data)  │
    └────────────┘                                           └──────────┘

The proxy tracks which conditions are locally available and which
remain remote-only.  When the UI needs trajectory data for a specific
condition, the proxy fetches just that condition's directory.

Author: Simão Eugénio
Date: April 2026
"""

import logging
import os
import shutil
import subprocess
from enum import Enum, auto
from pathlib import Path
from typing import Callable, Dict, Optional, Set

logger = logging.getLogger(__name__)


class FetchState(Enum):
    """Lifecycle state of a condition's data on the client."""

    REMOTE_ONLY = auto()   # Data exists only on server
    FETCHING = auto()      # Transfer in progress
    LOCAL = auto()         # Fully downloaded to client
    FAILED = auto()        # Fetch attempted but failed


class RemoteResultsProxy:
    """Lazy-fetch proxy for remote sweep results.

    After a sweep completes, only lightweight metadata (summary.csv,
    config.json) is fetched immediately.  Raw per-condition trajectory
    data is fetched on-demand when the user interacts with specific
    conditions in the results browser.

    Thread Safety:
        Fetch operations run synchronously on the calling thread.
        The caller (UI layer) should invoke ``fetch_condition`` from a
        background thread and marshal results back to the GTK main loop.

    Attributes:
        remote_run_dir: Absolute path to the run directory on the server.
        local_run_dir: Absolute path to the local run directory.
        ssh_host: SSH host identifier (hostname or user@host).
        conditions: Mapping of condition name → FetchState.
    """

    def __init__(
        self,
        remote_run_dir: str,
        local_run_dir: str,
        ssh_host: str,
        ssh_password: Optional[str] = None,
        ctl_socket_args: Optional[list] = None,
    ) -> None:
        """Initialize the remote results proxy.

        Args:
            remote_run_dir: Server-side path (e.g. ``/home/user/shypn/.../run_XXX``).
            local_run_dir: Client-side path where results are stored.
            ssh_host: SSH host for connections (e.g. ``user@1.2.3.4``).
            ssh_password: Optional SSH password (used via sshpass).
            ctl_socket_args: Optional SSH ControlMaster socket args.
        """
        self.remote_run_dir = remote_run_dir
        self.local_run_dir = Path(local_run_dir)
        self.ssh_host = ssh_host
        self._ssh_password = ssh_password
        self._ctl_socket_args = ctl_socket_args or []
        self._conditions: Dict[str, FetchState] = {}

    @property
    def conditions(self) -> Dict[str, FetchState]:
        """Read-only view of condition fetch states."""
        return dict(self._conditions)

    @property
    def local_conditions(self) -> Set[str]:
        """Set of condition names available locally."""
        return {
            name for name, state in self._conditions.items()
            if state == FetchState.LOCAL
        }

    @property
    def remote_only_conditions(self) -> Set[str]:
        """Set of condition names that exist only on the server."""
        return {
            name for name, state in self._conditions.items()
            if state == FetchState.REMOTE_ONLY
        }

    # ── Initialization ───────────────────────────────────────────────

    def register_conditions(self, condition_names: list[str]) -> None:
        """Register conditions discovered from summary.csv.

        Checks which conditions already have local directories and
        marks them accordingly.

        Args:
            condition_names: List of condition names from summary.csv.
        """
        for name in condition_names:
            local_dir = self.local_run_dir / f"condition_{name}"
            if local_dir.is_dir() and any(local_dir.iterdir()):
                self._conditions[name] = FetchState.LOCAL
            else:
                self._conditions[name] = FetchState.REMOTE_ONLY

    # ── Summary Fetch (immediate, lightweight) ───────────────────────

    def fetch_summary(self) -> Path:
        """Fetch only summary.csv and config.json from the server.

        Returns:
            Path to the local summary.csv file.

        Raises:
            RuntimeError: If the fetch fails.
        """
        self.local_run_dir.mkdir(parents=True, exist_ok=True)

        files_to_fetch = ['summary.csv', 'config.json']
        for filename in files_to_fetch:
            remote_path = f"{self.remote_run_dir}/{filename}"
            local_path = self.local_run_dir / filename
            self._scp_from(remote_path, str(local_path))

        summary_path = self.local_run_dir / 'summary.csv'
        if not summary_path.exists():
            raise RuntimeError(
                f"Failed to fetch summary.csv from {self.remote_run_dir}")

        return summary_path

    # ── On-Demand Condition Fetch ────────────────────────────────────

    def fetch_condition(
        self,
        condition_name: str,
        progress_cb: Optional[Callable[[str], None]] = None,
    ) -> Path:
        """Fetch a single condition's directory from the server.

        Idempotent: returns immediately if condition is already local.

        Args:
            condition_name: The condition identifier (e.g. ``CBD_extracellular_eq_15_Age_eq_55_pH_eq_7``).
            progress_cb: Optional callback for progress reporting.

        Returns:
            Path to the local condition directory.

        Raises:
            RuntimeError: If the fetch fails.
            KeyError: If condition_name is not registered.
        """
        if condition_name not in self._conditions:
            raise KeyError(
                f"Unknown condition: {condition_name!r}. "
                f"Registered: {list(self._conditions.keys())[:5]}...")

        state = self._conditions[condition_name]

        if state == FetchState.LOCAL:
            return self.local_run_dir / f"condition_{condition_name}"

        if state == FetchState.FETCHING:
            raise RuntimeError(
                f"Condition {condition_name!r} is already being fetched.")

        self._conditions[condition_name] = FetchState.FETCHING
        if progress_cb:
            progress_cb(f"Fetching condition: {condition_name}...")

        try:
            local_dir = self._fetch_condition_tar(condition_name)
            self._conditions[condition_name] = FetchState.LOCAL
            logger.info("Fetched condition %r → %s", condition_name, local_dir)
            return local_dir
        except Exception as e:
            self._conditions[condition_name] = FetchState.FAILED
            raise RuntimeError(
                f"Failed to fetch condition {condition_name!r}: {e}") from e

    def fetch_conditions_batch(
        self,
        condition_names: list[str],
        progress_cb: Optional[Callable[[str], None]] = None,
    ) -> Dict[str, Path]:
        """Fetch multiple conditions in a single tar stream.

        More efficient than individual fetches for batch operations.

        Args:
            condition_names: List of condition names to fetch.
            progress_cb: Optional callback for progress reporting.

        Returns:
            Mapping of condition_name → local directory path.

        Raises:
            RuntimeError: If the batch fetch fails.
        """
        # Filter to only conditions that need fetching
        to_fetch = [
            name for name in condition_names
            if self._conditions.get(name) in (FetchState.REMOTE_ONLY, FetchState.FAILED)
        ]

        if not to_fetch:
            return {
                name: self.local_run_dir / f"condition_{name}"
                for name in condition_names
                if self._conditions.get(name) == FetchState.LOCAL
            }

        if progress_cb:
            progress_cb(f"Fetching {len(to_fetch)} conditions...")

        for name in to_fetch:
            self._conditions[name] = FetchState.FETCHING

        try:
            # Build tar command for multiple directories
            dirs = " ".join(f"condition_{name}" for name in to_fetch)
            remote_parent = self.remote_run_dir
            tar_cmd = f"tar czf - -C {remote_parent} {dirs}"

            argv = self._build_ssh_argv(tar_cmd)
            self.local_run_dir.mkdir(parents=True, exist_ok=True)

            remote_proc = subprocess.Popen(
                argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            local_proc = subprocess.Popen(
                ['tar', 'xzf', '-', '-C', str(self.local_run_dir)],
                stdin=remote_proc.stdout, stderr=subprocess.PIPE)

            remote_proc.stdout.close()  # type: ignore[union-attr]
            _, local_err = local_proc.communicate(timeout=600)
            remote_proc.wait(timeout=30)

            if remote_proc.returncode != 0 or local_proc.returncode != 0:
                remote_err = (remote_proc.stderr.read()
                              if remote_proc.stderr else b'')
                if remote_proc.stderr:
                    remote_proc.stderr.close()
                raise RuntimeError(
                    f"Batch tar fetch failed: remote={remote_err.decode().strip()}, "
                    f"local={local_err.decode().strip()}")
            if remote_proc.stderr:
                remote_proc.stderr.close()

            # Mark all fetched conditions as LOCAL
            results = {}
            for name in to_fetch:
                local_dir = self.local_run_dir / f"condition_{name}"
                if local_dir.is_dir():
                    self._conditions[name] = FetchState.LOCAL
                    results[name] = local_dir
                else:
                    self._conditions[name] = FetchState.FAILED

            # Include already-local conditions in results
            for name in condition_names:
                if name not in results and self._conditions.get(name) == FetchState.LOCAL:
                    results[name] = self.local_run_dir / f"condition_{name}"

            return results

        except Exception as e:
            for name in to_fetch:
                self._conditions[name] = FetchState.FAILED
            raise RuntimeError(f"Batch fetch failed: {e}") from e

    # ── Utility ──────────────────────────────────────────────────────

    def is_condition_local(self, condition_name: str) -> bool:
        """Check if a condition's data is available locally."""
        return self._conditions.get(condition_name) == FetchState.LOCAL

    def condition_local_path(self, condition_name: str) -> Optional[Path]:
        """Get local path for a condition (None if not local)."""
        if self.is_condition_local(condition_name):
            return self.local_run_dir / f"condition_{condition_name}"
        return None

    def update_password(self, password: Optional[str]) -> None:
        """Update SSH password (e.g. after re-authentication)."""
        self._ssh_password = password

    def update_ctl_socket(self, ctl_socket_args: list) -> None:
        """Update ControlMaster socket args for connection reuse."""
        self._ctl_socket_args = ctl_socket_args

    # ── Private Helpers ──────────────────────────────────────────────

    def _fetch_condition_tar(self, condition_name: str) -> Path:
        """Fetch a single condition via tar pipe."""
        dir_name = f"condition_{condition_name}"
        tar_cmd = f"tar czf - -C {self.remote_run_dir} {dir_name}"

        argv = self._build_ssh_argv(tar_cmd)
        self.local_run_dir.mkdir(parents=True, exist_ok=True)

        remote_proc = subprocess.Popen(
            argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        local_proc = subprocess.Popen(
            ['tar', 'xzf', '-', '-C', str(self.local_run_dir)],
            stdin=remote_proc.stdout, stderr=subprocess.PIPE)

        remote_proc.stdout.close()  # type: ignore[union-attr]
        _, local_err = local_proc.communicate(timeout=300)
        remote_proc.wait(timeout=30)

        if remote_proc.returncode != 0 or local_proc.returncode != 0:
            remote_err = (remote_proc.stderr.read()
                          if remote_proc.stderr else b'')
            if remote_proc.stderr:
                remote_proc.stderr.close()
            raise RuntimeError(
                f"tar fetch for {condition_name!r} failed: "
                f"remote={remote_err.decode().strip()}, "
                f"local={local_err.decode().strip()}")
        if remote_proc.stderr:
            remote_proc.stderr.close()

        local_dir = self.local_run_dir / dir_name
        if not local_dir.is_dir():
            raise RuntimeError(
                f"Expected directory not created: {local_dir}")
        return local_dir

    def _scp_from(self, remote_path: str, local_path: str) -> None:
        """SCP a single file from the server."""
        argv = ['scp', '-C', '-o', 'StrictHostKeyChecking=no']
        argv += self._ctl_socket_args
        argv += [f"{self.ssh_host}:{remote_path}", local_path]

        if self._ssh_password and not self._ctl_socket_args:
            argv = ['sshpass', '-p', self._ssh_password] + argv

        result = subprocess.run(
            argv, capture_output=True, timeout=60)
        if result.returncode != 0:
            raise RuntimeError(
                f"scp failed: {result.stderr.decode().strip()}")

    def _build_ssh_argv(self, remote_cmd: str) -> list:
        """Build SSH command argv with password/socket handling."""
        argv = ['ssh', '-C', '-o', 'StrictHostKeyChecking=no']
        argv += self._ctl_socket_args
        argv += [self.ssh_host, remote_cmd]

        if self._ssh_password and not self._ctl_socket_args:
            argv = ['sshpass', '-p', self._ssh_password] + argv

        return argv
