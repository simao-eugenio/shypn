"""CuPy-based GPU backend.

Requires ``cupy-cuda12x`` (or the matching variant for the host's
CUDA toolkit).  All CuPy imports are deferred to :meth:`probe` /
:meth:`__init__` so that the module can be imported safely on
CPU-only machines.
"""

from __future__ import annotations

import logging
import os
import site
import sys
from pathlib import Path
from typing import Optional

import numpy as np
from numpy.typing import NDArray

from .base import GPUBackend, GPUInfo

logger = logging.getLogger(__name__)


def _ensure_nvidia_lib_path() -> None:
    """Add pip-installed ``nvidia-*`` lib dirs to ``LD_LIBRARY_PATH``.

    When CUDA toolkit packages are installed via pip (e.g.
    ``nvidia-cuda-nvrtc-cu12``) their shared libraries live under
    ``site-packages/nvidia/<pkg>/lib/``.  CuPy's ``cuda-pathfinder``
    sometimes fails to locate them unless they are on
    ``LD_LIBRARY_PATH``.  This helper patches the environment once so
    that ``dlopen()`` succeeds for ``libnvrtc.so`` and friends.
    """
    added: list[str] = []
    for sp in site.getsitepackages() + [site.getusersitepackages()]:
        nvidia_root = Path(sp) / "nvidia"
        if nvidia_root.is_dir():
            for lib_dir in nvidia_root.glob("*/lib"):
                d = str(lib_dir)
                if d not in os.environ.get("LD_LIBRARY_PATH", ""):
                    added.append(d)
    if added:
        current = os.environ.get("LD_LIBRARY_PATH", "")
        os.environ["LD_LIBRARY_PATH"] = ":".join(added) + (":" + current if current else "")
        # Also update the runtime linker search via ctypes so already-
        # loaded libdl picks up the new paths without restart.
        try:
            import ctypes
            for d in added:
                try:
                    ctypes.CDLL("libdl.so.2").dlopen  # noqa: B018 — verify available
                except Exception:
                    break
            # On Linux, re-searching is automatic with LD_LIBRARY_PATH
            # but we can also force-load the specific lib we know is needed.
            for d in added:
                nvrtc = Path(d) / "libnvrtc.so.12"
                if nvrtc.exists():
                    ctypes.CDLL(str(nvrtc))
                    logger.debug("Pre-loaded %s", nvrtc)
                    break
        except Exception:
            pass
        logger.debug("Added to LD_LIBRARY_PATH: %s", ":".join(added))


class CuPyBackend(GPUBackend):
    """GPU backend implemented with CuPy.

    CuPy provides a NumPy-compatible array API on CUDA, plus cuRAND
    for device-side random number generation — both essential for the
    GPU replicate kernel.
    """

    def __init__(self, device_id: int = 0) -> None:
        import cupy as cp  # deferred — only reached when probe() passed

        self._cp = cp
        self._device = cp.cuda.Device(device_id)
        self._device.use()
        self._info = self._query_info(device_id)
        logger.info("CuPyBackend initialised: %s", self._info.device_name)

    # ── identification ───────────────────────────────────────────────

    @property
    def name(self) -> str:
        return "cupy"

    @property
    def device_info(self) -> GPUInfo:
        return self._info

    # ── probing ──────────────────────────────────────────────────────

    @classmethod
    def probe(cls) -> bool:
        _ensure_nvidia_lib_path()
        try:
            import cupy as cp

            n_devices = cp.cuda.runtime.getDeviceCount()
            if n_devices < 1:
                return False
            # Sanity: try a tiny allocation to confirm the driver works
            _ = cp.zeros(1, dtype=cp.float64)
            return True
        except Exception:
            return False

    # ── device memory ────────────────────────────────────────────────

    def allocate(
        self,
        shape: tuple[int, ...],
        dtype: np.dtype = np.float64,  # type: ignore[assignment]
    ) -> object:
        return self._cp.empty(shape, dtype=dtype)

    def zeros(
        self,
        shape: tuple[int, ...],
        dtype: np.dtype = np.float64,  # type: ignore[assignment]
    ) -> object:
        return self._cp.zeros(shape, dtype=dtype)

    def to_device(self, host_array: NDArray[np.floating]) -> object:
        return self._cp.asarray(host_array)

    def to_host(self, device_array: object) -> NDArray[np.floating]:
        return self._cp.asnumpy(device_array)  # type: ignore[arg-type]

    # ── synchronisation ──────────────────────────────────────────────

    def synchronize(self) -> None:
        self._device.synchronize()

    # ── memory query (runtime, more accurate than static) ────────────

    def check_memory(self, required_bytes: int) -> bool:
        free, total = self._cp.cuda.runtime.memGetInfo()
        ok = required_bytes <= int(free * 0.9)
        if not ok:
            logger.warning(
                "GPU memory check failed: need %.1f MiB, "
                "%.1f MiB free / %.0f MiB total",
                required_bytes / (1024 * 1024),
                free / (1024 * 1024),
                total / (1024 * 1024),
            )
        return ok

    # ── internal ─────────────────────────────────────────────────────

    @staticmethod
    def _query_info(device_id: int) -> GPUInfo:
        import cupy as cp

        dev = cp.cuda.Device(device_id)
        attrs = dev.attributes
        props = cp.cuda.runtime.getDeviceProperties(device_id)
        name: str = props["name"].decode() if isinstance(props["name"], bytes) else props["name"]
        total_mem = props["totalGlobalMem"]
        cc_major = props["major"]
        cc_minor = props["minor"]
        driver_ver = cp.cuda.runtime.driverGetVersion()
        return GPUInfo(
            device_name=name,
            total_memory_mb=total_mem // (1024 * 1024),
            compute_capability=(cc_major, cc_minor),
            driver_version=str(driver_ver),
            device_id=device_id,
        )
