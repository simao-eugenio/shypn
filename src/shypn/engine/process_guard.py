"""Process guard — prevent orphan processes when SSH connections drop.

Problem
~~~~~~~
When a Python simulation is launched via ``ssh host 'python ...'``
without a PTY (``-T``), the remote process does **not** receive
``SIGHUP`` if the SSH connection dies.  It continues running at 100%
CPU until manually killed.

Solution (three layers)
~~~~~~~~~~~~~~~~~~~~~~~
1. **``PR_SET_PDEATHSIG``** (Linux) — ask the kernel to send
   ``SIGTERM`` to this process when its parent exits.  This covers the
   case where ``sshd`` forks a shell which forks Python: when ``sshd``
   is killed by the connection drop, the shell dies, and the kernel
   delivers the signal to Python.

2. **``SIGHUP`` / ``SIGTERM`` handler** — translate these signals into
   a ``SystemExit`` so that ``try/finally`` blocks (and GPU cleanup)
   run normally.

3. **Parent-alive watchdog** — a lightweight daemon thread that polls
   ``os.getppid()`` every few seconds.  On Linux, when a process is
   orphaned its PPID changes to 1 (``init``) or the subreaper PID.
   If the parent PID changes, the watchdog calls ``os._exit(1)``
   to terminate immediately.

Usage::

    from shypn.engine.process_guard import install_process_guard
    install_process_guard()   # call once at process start

The guard is idempotent — calling it multiple times is harmless.
It is a no-op on non-Linux platforms (macOS, Windows).
"""

from __future__ import annotations

import logging
import os
import signal
import sys
import threading

logger = logging.getLogger(__name__)

_installed = False
_lock = threading.Lock()


def install_process_guard(
    *,
    watchdog_interval: float = 5.0,
    enable_pdeathsig: bool = True,
    enable_signal_handlers: bool = True,
    enable_watchdog: bool = True,
) -> None:
    """Install all orphan-prevention mechanisms.

    Safe to call from any thread, but signal handlers are only installed
    from the main thread.  Idempotent.

    Parameters
    ----------
    watchdog_interval:
        Seconds between parent-alive checks (default 5).
    enable_pdeathsig:
        Set ``PR_SET_PDEATHSIG`` on Linux (default True).
    enable_signal_handlers:
        Install ``SIGHUP``/``SIGTERM`` handlers (default True).
    enable_watchdog:
        Start the parent-alive watchdog thread (default True).
    """
    global _installed
    with _lock:
        if _installed:
            return
        _installed = True

    if enable_pdeathsig:
        _set_pdeathsig()

    if enable_signal_handlers:
        _install_signal_handlers()

    if enable_watchdog:
        _start_watchdog(watchdog_interval)


# ── Layer 1: PR_SET_PDEATHSIG ───────────────────────────────────────

def _set_pdeathsig() -> None:
    """Ask the kernel to send SIGTERM when our parent process exits."""
    if sys.platform != "linux":
        return
    try:
        import ctypes
        import ctypes.util

        PR_SET_PDEATHSIG = 1
        SIGTERM = signal.SIGTERM.value

        libc = ctypes.CDLL(ctypes.util.find_library("c"), use_errno=True)
        result = libc.prctl(PR_SET_PDEATHSIG, SIGTERM, 0, 0, 0)
        if result != 0:
            errno = ctypes.get_errno()
            logger.debug("prctl(PR_SET_PDEATHSIG) failed: errno=%d", errno)
        else:
            logger.debug("PR_SET_PDEATHSIG(SIGTERM) set")
    except Exception as exc:
        logger.debug("PR_SET_PDEATHSIG failed: %s", exc)


# ── Layer 2: Signal handlers ────────────────────────────────────────

def _install_signal_handlers() -> None:
    """Install SIGHUP and SIGTERM handlers that raise SystemExit."""
    if threading.current_thread() is not threading.main_thread():
        logger.debug("Skipping signal handlers (not main thread)")
        return

    for sig in (signal.SIGHUP, signal.SIGTERM):
        try:
            prev = signal.getsignal(sig)
            # Don't override user-installed handlers (SIG_DFL/SIG_IGN are fine)
            if prev in (signal.SIG_DFL, signal.SIG_IGN, None):
                signal.signal(sig, _graceful_exit_handler)
                logger.debug("Installed handler for %s", sig.name)
        except (OSError, ValueError):
            # signal.signal() can fail in some embedded contexts
            pass


def _graceful_exit_handler(signum: int, frame) -> None:
    """Translate SIGHUP/SIGTERM into SystemExit for clean shutdown."""
    sig_name = signal.Signals(signum).name
    logger.info("Received %s — shutting down", sig_name)
    raise SystemExit(128 + signum)


# ── Layer 3: Parent-alive watchdog ───────────────────────────────────

def _start_watchdog(interval: float) -> None:
    """Start a daemon thread that exits if the parent process dies."""
    if sys.platform != "linux":
        return

    original_ppid = os.getppid()
    if original_ppid <= 1:
        # Already orphaned or running under init — no point watching
        logger.debug("Watchdog skipped: ppid=%d", original_ppid)
        return

    def _watchdog_loop():
        import time
        while True:
            time.sleep(interval)
            current_ppid = os.getppid()
            if current_ppid != original_ppid:
                logger.warning(
                    "Parent process died (ppid %d → %d) — exiting",
                    original_ppid, current_ppid,
                )
                # os._exit() is safe from a daemon thread — it skips
                # atexit handlers and finally blocks, but that's
                # acceptable for an emergency orphan kill.
                os._exit(1)

    t = threading.Thread(target=_watchdog_loop, daemon=True,
                         name="shypn-orphan-watchdog")
    t.start()
    logger.debug("Parent-alive watchdog started (ppid=%d, interval=%.1fs)",
                 original_ppid, interval)
