"""Abstract base for sweep dispatch controllers (local + remote share this).

Owns the dispatch lifecycle:
    1. ``start(request)``  — validates, flips the active flag, calls ``_run()``
    2. ``cancel()``        — calls ``_cancel_impl()``, drops the active flag
    3. ``is_active``       — single source of truth for "a sweep is in flight"

Subclasses implement only the transport (``_run`` / ``_cancel_impl``).
Both progress events and the final completion event are forwarded to a
``DispatchObserver`` — controllers never touch GTK widgets directly.
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import ClassVar, Optional

from .observer import DispatchObserver
from .types import DispatchKind, DispatchRequest

_log = logging.getLogger(__name__)


class DispatchAlreadyActive(RuntimeError):
    """Raised when ``start()`` is called while the controller is busy."""


class DispatchValidationError(ValueError):
    """Raised when a ``DispatchRequest`` fails pre-flight validation."""


class SweepDispatchController(ABC):
    """Abstract orchestrator for one sweep dispatch.

    Lifecycle::

        ctrl = SubController(observer, ...)
        ctrl.start(request)        # raises DispatchValidationError on bad input
        ...                        # observer methods called as work progresses
        ctrl.cancel()              # optional; safe even if already complete
    """

    KIND: ClassVar[DispatchKind]  # set by subclass

    def __init__(self, observer: DispatchObserver) -> None:
        if not isinstance(observer, DispatchObserver):
            raise TypeError(f'observer must implement DispatchObserver, got {type(observer)}')
        self._observer = observer
        self._active = False
        self._request: Optional[DispatchRequest] = None

    # ── public API ────────────────────────────────────────────────
    @property
    def is_active(self) -> bool:
        """True iff a dispatch is in progress."""
        return self._active

    @property
    def kind(self) -> DispatchKind:
        return self.KIND

    def start(self, request: DispatchRequest) -> None:
        """Validate the request and launch the dispatch.

        Raises ``DispatchAlreadyActive`` if a previous dispatch is still
        in progress, or ``DispatchValidationError`` if the request is
        malformed (no experiments, non-positive duration, etc.).
        """
        if self._active:
            raise DispatchAlreadyActive(
                f'{self.KIND.value} dispatch already active'
            )
        self._validate(request)
        self._request = request
        self._active = True
        try:
            self._run(request)
        except BaseException as exc:
            # Transport refused to start — treat as immediate failure
            # so the observer restores the idle UI.
            self._active = False
            _log.exception('%s dispatch failed to start', self.KIND.value)
            self._observer.on_dispatch_complete(
                False, None,
                f'{self.KIND.value} dispatch failed to start: {exc}',
            )
            raise

    def cancel(self) -> None:
        """Best-effort cancel. No-op when the controller is idle."""
        if not self._active:
            return
        try:
            self._cancel_impl()
        except Exception:
            _log.exception('%s cancel raised', self.KIND.value)
        # Note: _active stays True until _emit_complete() fires from the
        # transport's own cleanup path; cancel only *requests* the stop.

    # ── subclass hooks ────────────────────────────────────────────
    def _validate(self, request: DispatchRequest) -> None:
        """Called from ``start()`` before the active flag flips."""
        if not request.experiments:
            raise DispatchValidationError('No experiments to dispatch')
        sp = request.sim_params
        if sp.replicates <= 0:
            raise DispatchValidationError(f'replicates must be > 0 (got {sp.replicates})')
        if sp.duration <= 0:
            raise DispatchValidationError(f'duration must be > 0 (got {sp.duration})')
        if sp.time_step is not None and sp.time_step <= 0:
            raise DispatchValidationError(
                f'time_step must be > 0 or None (got {sp.time_step})')

    @abstractmethod
    def _run(self, request: DispatchRequest) -> None:
        """Launch the actual dispatch. Called from the GTK thread."""

    @abstractmethod
    def _cancel_impl(self) -> None:
        """Transport-specific cancel."""

    # ── helpers for subclasses ────────────────────────────────────
    def _emit_status(self, message: str, level: str = 'info') -> None:
        try:
            self._observer.on_status(message, level)
        except Exception:
            _log.exception('observer.on_status raised')

    def _emit_row_started(self, row_index: int) -> None:
        try:
            self._observer.on_row_started(row_index)
        except Exception:
            _log.exception('observer.on_row_started raised')

    def _emit_row_completed(
        self, row_index: int, ok: int, errors: int, wall_seconds: float,
    ) -> None:
        try:
            self._observer.on_row_completed(row_index, ok, errors, wall_seconds)
        except Exception:
            _log.exception('observer.on_row_completed raised')

    def _emit_complete(
        self, success: bool, results_dir: Optional[str], message: str,
    ) -> None:
        """Mark the dispatch complete and notify the observer.

        Subclasses MUST call this exactly once per dispatch (success or
        failure). After this returns ``is_active`` is False.
        """
        self._active = False
        try:
            self._observer.on_dispatch_complete(success, results_dir, message)
        except Exception:
            _log.exception('observer.on_dispatch_complete raised')
