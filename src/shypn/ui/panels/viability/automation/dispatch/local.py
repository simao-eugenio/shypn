"""Local sweep dispatch controller.

Wraps the existing ``BatchExecutor`` (in-process, multi-worker via
``multiprocessing``) and adapts its three-callback surface to the
typed observer protocol.

The category panel still owns the per-run output folder and the
results-browser refresh — those are local-only concerns that don't
exist on the remote path. This controller cares only about:

    * marshalling ``run_batch`` kwargs from a ``DispatchRequest``
    * translating progress / completion callbacks into observer events
    * propagating ``cancel()`` to the ``BatchExecutor``
"""
from __future__ import annotations

import logging
import time
from typing import Any, Dict, Optional

from gi.repository import GLib

from .base import SweepDispatchController
from .observer import DispatchObserver
from .types import DispatchKind, DispatchRequest

_log = logging.getLogger(__name__)


class LocalSweepDispatchController(SweepDispatchController):
    """Drives a sweep on the local box via ``BatchExecutor``.

    ``run_folder`` is set by the caller before ``start()`` so the
    controller knows where the (local-only) run directory lives; it is
    forwarded to the observer in ``on_dispatch_complete`` as the
    ``results_dir``.
    """

    KIND = DispatchKind.LOCAL

    def __init__(
        self,
        observer: DispatchObserver,
        batch_executor,
        run_folder: Optional[str] = None,
    ) -> None:
        super().__init__(observer)
        self._batch = batch_executor
        self._run_folder = run_folder
        # Maps experiment name → queue row index for the result callback.
        self._name_to_row: Dict[str, int] = {}
        # Per-row wall-clock for the on_row_completed payload.
        self._row_start: Dict[int, float] = {}

    # ── public ────────────────────────────────────────────────────
    def set_run_folder(self, run_folder: Optional[str]) -> None:
        self._run_folder = run_folder

    # ── SweepDispatchController hooks ─────────────────────────────
    def _run(self, request: DispatchRequest) -> None:
        self._name_to_row = {name: idx for (idx, name, _snap) in request.experiments}
        self._row_start.clear()

        sp = request.sim_params
        self._batch.run_batch(
            experiments=request.experiments,
            replicates=sp.replicates,
            duration=sp.duration,
            termination_condition=sp.termination,
            progress_callback=self._on_raw_progress,
            complete_callback=self._on_raw_complete,
            experiment_result_callback=self._on_raw_result,
            use_parallel=sp.use_parallel,
            use_tau_leaping=sp.use_tau_leaping,
            tau_epsilon=sp.tau_epsilon,
            max_tau=sp.max_tau,
            dt_manual=sp.time_step,
            seed_base=sp.seed_base,
            compressor_epsilon=sp.compressor_epsilon,
            compressor_min_gap=sp.compressor_min_gap,
            compressor_max_gap=sp.compressor_max_gap,
        )

    def _cancel_impl(self) -> None:
        try:
            self._batch.cancel()
        except Exception:
            _log.exception('local batch cancel raised')

    # ── BatchExecutor → observer adapters ─────────────────────────
    def _on_raw_progress(self, exp_index: int, status: str, progress: Any) -> None:
        """Background-thread callback. Delegates to GTK main loop."""
        if status == 'running':
            self._row_start[exp_index] = time.monotonic()
            GLib.idle_add(self._dispatch_row_started, exp_index)
        elif status in ('completed', 'failed', 'cancelled'):
            # Result callback already fired the typed completion; the raw
            # progress line just becomes an activity-log entry.
            GLib.idle_add(self._dispatch_status, f'[row {exp_index}] {status}: {progress}', 'info')
        else:
            GLib.idle_add(self._dispatch_status, f'[row {exp_index}] {status}', 'info')

    def _on_raw_result(self, name: str, result: Dict[str, Any]) -> None:
        """One experiment finished — extract counts and forward."""
        row = self._name_to_row.get(name, -1)
        ok = int(result.get('ok_replicates', result.get('ok', 0)) or 0)
        errors = int(result.get('error_replicates', result.get('errors', 0)) or 0)
        wall = float(result.get('wall_seconds') or 0.0)
        if wall <= 0 and row in self._row_start:
            wall = max(0.0, time.monotonic() - self._row_start[row])
        if 0 <= row:
            GLib.idle_add(self._dispatch_row_completed, row, ok, errors, wall)

    def _on_raw_complete(self) -> None:
        """Whole batch finished — observer drives the idle-state UI."""
        # BatchExecutor doesn't pass success/message; treat as success
        # unless cancellation was requested.
        cancelled = bool(getattr(self._batch, 'is_cancelled', False))
        success = not cancelled
        message = 'Local sweep cancelled.' if cancelled else 'Local sweep complete.'
        GLib.idle_add(self._dispatch_complete, success, self._run_folder, message)

    # ── GTK-thread trampolines ────────────────────────────────────
    def _dispatch_status(self, message: str, level: str) -> bool:
        self._emit_status(message, level)
        return False

    def _dispatch_row_started(self, row_index: int) -> bool:
        self._emit_row_started(row_index)
        return False

    def _dispatch_row_completed(
        self, row_index: int, ok: int, errors: int, wall_seconds: float,
    ) -> bool:
        self._emit_row_completed(row_index, ok, errors, wall_seconds)
        return False

    def _dispatch_complete(
        self, success: bool, results_dir: Optional[str], message: str,
    ) -> bool:
        self._emit_complete(success, results_dir, message)
        return False
