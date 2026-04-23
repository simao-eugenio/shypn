#!/usr/bin/env python3
"""Pending-dispatch registry for resilient remote sweep recovery.

A dispatched remote sweep produces all of its heavy artifacts on the
server (in ``<project>/experiments/results/run_<ts>/``).  The client
only needs ``summary.csv`` + ``config.json`` (≤ a few MB) to populate
the Experiment Results browser; per-condition trajectory data is
fetched lazily by :class:`RemoteResultsProxy`.

If the GUI is closed, restarted, or interrupted between the moment the
SSH stream returns the run directory and the moment the summary fetch
completes, the run becomes invisible to the client even though the
server-side data is intact.  This registry persists the minimal state
required to recover such dispatches on the next project-open:

    {project}/experiments/.pending_dispatches.json
    [
      {
        "run_dir_remote": "/home/simao/data/results/canabidiol/run_20260421_204933",
        "run_dir_local":  ".../experiments/results/run_20260421_204933",
        "ssh_host":       "remote-gpu",
        "fetch_mode":     "summary_only",
        "created_at":     "2026-04-21T20:49:33"
      },
      ...
    ]

Recovery semantics:
    * Idempotent — registering the same ``run_dir_local`` twice
      replaces the prior entry.
    * Atomic — writes go through ``os.replace`` of a sibling tempfile
      so a crash mid-write never leaves a corrupt JSON.
    * Resilient to corruption — a malformed file is logged and treated
      as empty; the next write rewrites it cleanly.
    * Thread-safe — a module-level lock serialises all read/write
      operations so the dispatcher background thread and the GUI main
      thread never race.

Author: Simão Eugénio
Date: April 2026
"""

from __future__ import annotations

import json
import logging
import os
import tempfile
import threading
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Optional

logger = logging.getLogger(__name__)


# ── Data model ───────────────────────────────────────────────────────


@dataclass(frozen=True)
class PendingDispatch:
    """One unresolved remote sweep awaiting its summary fetch.

    All fields are JSON-serialisable strings so the on-disk format is
    forward-compatible (older clients can still read newer files and
    ignore unknown keys).

    Attributes:
        run_dir_remote: Absolute path on the server, as parsed from
            the CLI's ``Results: <path>`` line.
        run_dir_local:  Absolute path under
            ``<project>/experiments/results/`` where the local
            mirror lives (or will live).  Used as the unique key.
        ssh_host:       SSH destination (e.g. ``remote-gpu`` or
            ``user@host``).  Recovery requires key-based auth; the
            interactive password is intentionally not persisted.
        fetch_mode:     ``"summary_only"`` or ``"full"`` — controls
            which RemoteResultsProxy strategy the resume path uses.
        created_at:     ISO-8601 timestamp recorded at registration
            time.  Useful for stale-entry pruning policies.
    """

    run_dir_remote: str
    run_dir_local: str
    ssh_host: str
    fetch_mode: str = "summary_only"
    created_at: str = field(
        default_factory=lambda: datetime.now().isoformat(timespec="seconds")
    )

    def to_json(self) -> dict:
        """Return a JSON-serialisable dict (round-trips through ``from_json``)."""
        return asdict(self)

    @classmethod
    def from_json(cls, raw: dict) -> "PendingDispatch":
        """Reconstruct from a dict, ignoring unknown keys for forward compat."""
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in raw.items() if k in known})


# ── Registry ─────────────────────────────────────────────────────────


class DispatchRegistry:
    """Append-only registry of unresolved remote sweep dispatches.

    Each project owns exactly one registry file at
    ``<project>/experiments/.pending_dispatches.json``.  Instances are
    cheap to construct and hold no in-memory cache — every operation
    re-reads the file under a class-level lock so multiple instances in
    the same process see a consistent view.

    Typical lifecycle:

        registry = DispatchRegistry(project_root)
        registry.register(PendingDispatch(...))   # before fetch
        try:
            proxy.fetch_summary()
            registry.unregister(local_run_dir)    # after success
        except Exception:
            pass                                  # entry stays for recovery

    The class never raises on I/O failures; callers can rely on the
    registry being best-effort and continue normal operation if it is
    unavailable (e.g. read-only filesystem).
    """

    REGISTRY_FILENAME = ".pending_dispatches.json"

    # Class-level lock: every project's registry shares a single
    # serialisation point.  Operations are O(N) over a small list so
    # contention is negligible; a class lock is simpler and safer than
    # per-instance / per-file locks.
    _io_lock = threading.Lock()

    def __init__(self, project_root: Path | str) -> None:
        """Initialise the registry for a single project.

        Args:
            project_root: Absolute path to the project directory
                (the one that contains ``experiments/``).
        """
        self._project_root = Path(project_root)
        self._registry_path = (
            self._project_root / "experiments" / self.REGISTRY_FILENAME
        )

    # ── public properties ───────────────────────────────────────────

    @property
    def path(self) -> Path:
        """Absolute path to the on-disk registry file."""
        return self._registry_path

    # ── public operations ───────────────────────────────────────────

    def register(self, entry: PendingDispatch) -> None:
        """Add (or replace) an entry keyed by ``run_dir_local``.

        Replacement semantics make ``register`` idempotent: re-running
        the same dispatch overwrites the prior record rather than
        appending a duplicate.

        Args:
            entry: The dispatch to record.
        """
        with self._io_lock:
            entries = self._read_unlocked()
            entries = [e for e in entries if e.run_dir_local != entry.run_dir_local]
            entries.append(entry)
            self._write_unlocked(entries)
        logger.info("DispatchRegistry: registered %s", entry.run_dir_local)

    def unregister(self, run_dir_local: str) -> bool:
        """Remove the entry whose ``run_dir_local`` equals ``run_dir_local``.

        Args:
            run_dir_local: The local run directory used as the key.

        Returns:
            True if an entry was removed, False if no match was found.
        """
        with self._io_lock:
            entries = self._read_unlocked()
            kept = [e for e in entries if e.run_dir_local != run_dir_local]
            if len(kept) == len(entries):
                return False
            self._write_unlocked(kept)
        logger.info("DispatchRegistry: unregistered %s", run_dir_local)
        return True

    def pending(self) -> List[PendingDispatch]:
        """Return the current set of unresolved dispatches.

        The returned list is a fresh snapshot; modifications do not
        affect the on-disk file.
        """
        with self._io_lock:
            return list(self._read_unlocked())

    def clear(self) -> None:
        """Remove the registry file entirely (e.g. for project reset)."""
        with self._io_lock:
            try:
                self._registry_path.unlink()
            except FileNotFoundError:
                return
            except OSError as exc:
                logger.warning(
                    "DispatchRegistry: failed to clear %s: %s",
                    self._registry_path, exc,
                )

    # ── private helpers (must be called under _io_lock) ─────────────

    def _read_unlocked(self) -> List[PendingDispatch]:
        """Load entries from disk; treat missing/corrupt files as empty."""
        if not self._registry_path.exists():
            return []
        try:
            with self._registry_path.open("r", encoding="utf-8") as fh:
                raw = json.load(fh)
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning(
                "DispatchRegistry: %s is unreadable (%s); treating as empty",
                self._registry_path, exc,
            )
            return []
        if not isinstance(raw, list):
            logger.warning(
                "DispatchRegistry: %s has unexpected shape; treating as empty",
                self._registry_path,
            )
            return []
        out: List[PendingDispatch] = []
        for item in raw:
            if not isinstance(item, dict):
                continue
            try:
                out.append(PendingDispatch.from_json(item))
            except TypeError as exc:
                logger.warning(
                    "DispatchRegistry: skipping malformed entry %r: %s",
                    item, exc,
                )
        return out

    def _write_unlocked(self, entries: Iterable[PendingDispatch]) -> None:
        """Atomically replace the registry file with ``entries``.

        Uses ``tempfile.NamedTemporaryFile`` + ``os.replace`` to ensure
        the file is either fully old or fully new at any observation
        point, even across crashes.
        """
        try:
            self._registry_path.parent.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            logger.warning(
                "DispatchRegistry: cannot create %s: %s",
                self._registry_path.parent, exc,
            )
            return
        payload = [e.to_json() for e in entries]
        try:
            # Write to a sibling tempfile then rename — guarantees
            # atomicity on POSIX even if the process is killed.
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=str(self._registry_path.parent),
                prefix=".pending_dispatches.",
                suffix=".tmp",
                delete=False,
            ) as tmp:
                json.dump(payload, tmp, indent=2)
                tmp.flush()
                os.fsync(tmp.fileno())
                tmp_path = tmp.name
            os.replace(tmp_path, self._registry_path)
        except OSError as exc:
            logger.warning(
                "DispatchRegistry: failed to write %s: %s",
                self._registry_path, exc,
            )

    # ── convenience ─────────────────────────────────────────────────

    @classmethod
    def for_project(cls, project_root: Optional[Path | str]) -> Optional["DispatchRegistry"]:
        """Construct a registry, returning None if no project is open.

        Convenience helper for call-sites that may be invoked outside
        the context of an open project.

        Args:
            project_root: Project directory, or None.

        Returns:
            A DispatchRegistry, or None when ``project_root`` is None.
        """
        if project_root is None:
            return None
        return cls(project_root)
