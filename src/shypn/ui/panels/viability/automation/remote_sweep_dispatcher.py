#!/usr/bin/env python3
"""Remote Sweep Dispatcher — run CLI sweeps on a remote server via SSH.

Pipeline:
  1. Export sweep config JSON + model .shy to a temp staging area
  2. SCP both files to the remote project folder
  3. SSH run ``python -m shypn.cli.sweep`` on the remote
  4. SCP results back to the local project folder
  5. Signal completion so the ResultsBrowserView can load them

Requires:
  - SSH config alias (e.g. ``remote-gpu``) with ControlMaster
  - Remote repo at a known path with ``.venv`` and ``src/`` on PYTHONPATH
  - The remote branch must already have the CLI module installed

Author: Simão Eugénio
Date: April 2026
"""

import json
import logging
import os
import re
import shutil
import subprocess
import tempfile
import threading
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

logger = logging.getLogger(__name__)


class RemoteSweepSettings:
    """SSH/remote configuration for sweep dispatch.

    Persisted under ``~/.config/shypn/workspace.json`` →
    ``remote_sweep`` section.
    """

    DEFAULTS = {
        'ssh_host': 'remote-gpu',
        'remote_repo': '/home/simao/shypn',
        'remote_venv': '.venv/bin/python',
        'workers': 0,  # 0 = auto
    }

    def __init__(self, workspace_settings=None):
        self._ws = workspace_settings
        self._section = dict(self.DEFAULTS)
        if self._ws:
            saved = self._ws.settings.get('remote_sweep', {})
            self._section.update(saved)

    # ── accessors ────────────────────────────────────────────────────
    @property
    def ssh_host(self) -> str:
        return self._section['ssh_host']

    @ssh_host.setter
    def ssh_host(self, v: str):
        self._section['ssh_host'] = v

    @property
    def remote_repo(self) -> str:
        return self._section['remote_repo']

    @remote_repo.setter
    def remote_repo(self, v: str):
        self._section['remote_repo'] = v

    @property
    def remote_venv(self) -> str:
        return self._section['remote_venv']

    @remote_venv.setter
    def remote_venv(self, v: str):
        self._section['remote_venv'] = v

    @property
    def workers(self) -> int:
        return self._section['workers']

    @workers.setter
    def workers(self, v: int):
        self._section['workers'] = max(0, int(v))

    def save(self):
        """Persist to workspace.json."""
        if self._ws:
            self._ws.settings['remote_sweep'] = dict(self._section)
            self._ws.save()

    def to_dict(self) -> dict:
        return dict(self._section)


class RemoteSweepDispatcher:
    """Orchestrates a full remote sweep cycle (export → SCP → SSH → fetch).

    All heavy I/O runs on a background thread.  GTK callbacks are
    delivered via ``GLib.idle_add`` by the caller (automation category).
    """

    def __init__(self, settings: RemoteSweepSettings):
        self.settings = settings
        self._cancel = threading.Event()
        self._thread: Optional[threading.Thread] = None

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def cancel(self):
        """Request cancellation of a running dispatch."""
        self._cancel.set()

    # ── public entry point ───────────────────────────────────────────
    def dispatch(
        self,
        model_filepath: str,
        project_folder: str,
        experiment_manager,
        sim_params: dict,
        progress_cb: Optional[Callable[[str], None]] = None,
        complete_cb: Optional[Callable[[bool, str, str], None]] = None,
        ssh_password: Optional[str] = None,
    ):
        """Launch the remote sweep pipeline on a background thread.

        Args:
            model_filepath: Absolute local path to the ``.shy`` model file.
            project_folder: Absolute local path to the project root
                (e.g. ``workspace/projects/thesis``).
            experiment_manager: ``ExperimentManager`` instance (has
                ``export_sweep_config``).
            sim_params: Dict with keys ``replicates``, ``duration``,
                ``termination``, ``seed_base``, ``tau_epsilon``, ``max_tau``.
            progress_cb: Called on the **background** thread with a status
                string for each pipeline phase.  The caller must wrap in
                ``GLib.idle_add`` if touching GTK.
            complete_cb: ``(success: bool, local_results_dir: str, message: str)``
                — called when the pipeline finishes or fails.
            ssh_password: Optional SSH password (used via ``sshpass``).
                Never persisted to disk.
        """
        if self.is_running:
            if complete_cb:
                complete_cb(False, '', 'A remote sweep is already running.')
            return

        self._cancel.clear()
        self._thread = threading.Thread(
            target=self._run_pipeline,
            args=(model_filepath, project_folder, experiment_manager,
                  sim_params, progress_cb, complete_cb, ssh_password),
            daemon=True,
        )
        self._thread.start()

    # ── pipeline ─────────────────────────────────────────────────────
    def _run_pipeline(
        self,
        model_filepath: str,
        project_folder: str,
        experiment_manager,
        sim_params: dict,
        progress_cb,
        complete_cb,
        ssh_password: Optional[str] = None,
    ):
        staging = None
        try:
            host = self.settings.ssh_host
            remote_repo = self.settings.remote_repo
            remote_venv = self.settings.remote_venv
            workers = self.settings.workers

            # ── resolve project-relative path ────────────────────────
            # project_folder is absolute: .../workspace/projects/thesis
            # We need the repo-relative project path for the remote CLI
            project_abs = Path(project_folder).resolve()
            # Walk up to find 'workspace' anchor
            repo_root = self._find_repo_root(project_abs)
            if repo_root is None:
                raise RuntimeError(
                    f"Cannot determine repo root from project folder: {project_folder}")
            project_rel = str(project_abs.relative_to(repo_root))

            # Model path relative to project folder
            model_abs = Path(model_filepath).resolve()
            model_rel_to_project = str(model_abs.relative_to(project_abs))

            # ── 1. Export sweep config to staging ────────────────────
            self._emit(progress_cb, 'Exporting sweep config...')
            staging = Path(tempfile.mkdtemp(prefix='shypn_remote_'))
            config_path = staging / 'sweep_config.json'
            experiment_manager.export_sweep_config(
                filepath=str(config_path),
                model_path=model_rel_to_project,
                **sim_params,
            )

            if self._cancel.is_set():
                raise InterruptedError('Cancelled')

            # ── 2. SCP model + config to remote ─────────────────────
            self._emit(progress_cb, 'Uploading model and config to remote...')

            # Figure out remote project path
            remote_project = f"{remote_repo}/{project_rel}"
            # Determine where the model lives relative to the project
            remote_model_dir = f"{remote_project}/{Path(model_rel_to_project).parent}"
            remote_sweep_dir = f"{remote_project}"

            # Ensure remote directories exist
            self._ssh(host, f"mkdir -p {remote_model_dir} {remote_sweep_dir}",
                      password=ssh_password)

            # SCP model file
            self._scp_to(host, str(model_abs), f"{remote_model_dir}/",
                         password=ssh_password)

            # SCP sweep config
            self._scp_to(host, str(config_path),
                         f"{remote_sweep_dir}/sweep_config.json",
                         password=ssh_password)

            if self._cancel.is_set():
                raise InterruptedError('Cancelled')

            # ── 3. SSH run CLI on remote ─────────────────────────────
            self._emit(progress_cb, 'Running sweep on remote server...')

            workers_flag = f"--workers {workers}" if workers > 0 else ""
            remote_cmd = (
                f"cd {remote_repo} && "
                f"export PYTHONPATH=$PWD/src && "
                f"{remote_venv} -m shypn.cli.sweep "
                f"--project {project_rel} "
                f"--sweep sweep_config.json "
                f"{workers_flag} "
                f"--verbose"
            )

            stdout = self._ssh_stream(
                host, remote_cmd,
                password=ssh_password,
                progress_cb=progress_cb,
                cancel=self._cancel,
            )

            # Parse "Results: <path>" from output
            run_dir = self._parse_results_dir(stdout)
            if not run_dir:
                raise RuntimeError(
                    f"Could not parse results directory from remote output:\n{stdout}")

            # The CLI may emit a relative path (relative to remote repo).
            # SCP needs the absolute path on the remote.
            if not run_dir.startswith('/'):
                run_dir = f"{remote_repo}/{run_dir}"

            if self._cancel.is_set():
                raise InterruptedError('Cancelled')

            # ── 4. Fetch results back ────────────────────────────────
            self._emit(progress_cb, 'Fetching results from remote...')

            run_name = Path(run_dir).name
            local_results_base = project_abs / 'experiments' / 'results'
            local_results_base.mkdir(parents=True, exist_ok=True)
            local_run_dir = local_results_base / run_name

            self._scp_from(host, run_dir, str(local_run_dir),
                           password=ssh_password)

            # ── 5. Done ──────────────────────────────────────────────
            self._emit(progress_cb, f'Done — results at {local_run_dir.name}')

            if complete_cb:
                complete_cb(True, str(local_run_dir), f'Sweep complete: {run_name}')

        except InterruptedError:
            if complete_cb:
                complete_cb(False, '', 'Remote sweep cancelled.')
        except Exception as e:
            logger.exception("Remote sweep failed")
            if complete_cb:
                complete_cb(False, '', str(e))
        finally:
            # Clean up staging
            if staging and staging.exists():
                shutil.rmtree(staging, ignore_errors=True)

    # ── helpers ──────────────────────────────────────────────────────
    @staticmethod
    def _emit(cb, msg):
        if cb:
            cb(msg)

    @staticmethod
    def _find_repo_root(path: Path) -> Optional[Path]:
        """Walk up from *path* looking for a ``.git`` directory."""
        for parent in [path] + list(path.parents):
            if (parent / '.git').is_dir():
                return parent
        return None

    @staticmethod
    def _ssh(host: str, cmd: str, *, password: Optional[str] = None) -> str:
        """Run a command on the remote via SSH and return stdout (blocking)."""
        argv = ['ssh', host, cmd]
        if password:
            argv = ['sshpass', '-p', password] + argv
        result = subprocess.run(
            argv,
            capture_output=True, text=True, timeout=600,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"SSH command failed (exit {result.returncode}):\n"
                f"  cmd: {cmd}\n"
                f"  stderr: {result.stderr.strip()}")
        return result.stdout

    @staticmethod
    def _ssh_stream(
        host: str,
        cmd: str,
        *,
        password: Optional[str] = None,
        progress_cb: Optional[Callable[[str], None]] = None,
        cancel: Optional[threading.Event] = None,
    ) -> str:
        """Run a command on the remote via SSH, streaming stdout lines.

        Each non-empty line from stdout is forwarded to *progress_cb*
        in real time.  Returns the full stdout when the process exits.
        """
        argv = ['ssh', '-tt', host, cmd]
        if password:
            argv = ['sshpass', '-p', password, 'ssh', '-tt', host, cmd]
        proc = subprocess.Popen(
            argv,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,  # line-buffered
        )
        lines: list[str] = []
        try:
            for line in proc.stdout:              # type: ignore[union-attr]
                lines.append(line)
                stripped = line.strip()
                if stripped and progress_cb:
                    progress_cb(stripped)
                if cancel and cancel.is_set():
                    proc.terminate()
                    raise InterruptedError('Cancelled')
        finally:
            proc.stdout.close()                   # type: ignore[union-attr]
            proc.wait(timeout=30)

        if proc.returncode != 0:
            stderr = proc.stderr.read() if proc.stderr else ''
            proc.stderr.close() if proc.stderr else None
            raise RuntimeError(
                f"SSH command failed (exit {proc.returncode}):\n"
                f"  cmd: {cmd}\n"
                f"  stderr: {stderr.strip()}")
        if proc.stderr:
            proc.stderr.close()
        return ''.join(lines)

    @staticmethod
    def _scp_to(host: str, local_path: str, remote_path: str,
                *, password: Optional[str] = None):
        """SCP a local file/dir to the remote."""
        argv = ['scp', '-r', local_path, f'{host}:{remote_path}']
        if password:
            argv = ['sshpass', '-p', password] + argv
        result = subprocess.run(
            argv,
            capture_output=True, text=True, timeout=120,
        )
        if result.returncode != 0:
            raise RuntimeError(f"SCP upload failed: {result.stderr.strip()}")

    @staticmethod
    def _scp_from(host: str, remote_path: str, local_path: str,
                  *, password: Optional[str] = None):
        """SCP a remote file/dir to local."""
        argv = ['scp', '-r', f'{host}:{remote_path}', local_path]
        if password:
            argv = ['sshpass', '-p', password] + argv
        result = subprocess.run(
            argv,
            capture_output=True, text=True, timeout=120,
        )
        if result.returncode != 0:
            raise RuntimeError(f"SCP download failed: {result.stderr.strip()}")

    @staticmethod
    def _parse_results_dir(output: str) -> Optional[str]:
        """Extract the run directory from CLI output like ``Results: /path/to/run_xxx``."""
        for line in reversed(output.splitlines()):
            m = re.match(r'^Results:\s+(.+)$', line.strip())
            if m:
                return m.group(1).strip()
        return None
