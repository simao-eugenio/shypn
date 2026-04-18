"""Numba CUDA-based GPU backend.

Requires ``numba`` with CUDA support (``numba.cuda``).  All CUDA
imports are deferred to :meth:`probe` / :meth:`__init__` so that the
module can be imported safely on CPU-only machines or when numba is
installed without CUDA toolkit access.
"""

from __future__ import annotations

import logging
from typing import Optional

import numpy as np
from numpy.typing import NDArray

from .base import GPUBackend, GPUInfo

logger = logging.getLogger(__name__)


class NumbaCudaBackend(GPUBackend):
    """GPU backend implemented with Numba CUDA.

    Numba CUDA provides JIT-compiled CUDA kernels written in Python
    syntax, plus device array management.  Preferred when CuPy is not
    installed but numba is already available (common in scientific
    Python environments).
    """

    def __init__(self, device_id: int = 0) -> None:
        from numba import cuda  # deferred

        self._cuda = cuda
        self._device = cuda.gpus[device_id]
        self._device_id = device_id
        with self._device:
            self._info = self._query_info(device_id)
        logger.info("NumbaCudaBackend initialised: %s", self._info.device_name)

    # ── identification ───────────────────────────────────────────────

    @property
    def name(self) -> str:
        return "numba_cuda"

    @property
    def device_info(self) -> GPUInfo:
        return self._info

    # ── probing ──────────────────────────────────────────────────────

    @classmethod
    def probe(cls) -> bool:
        try:
            from numba import cuda

            if not cuda.is_available():
                return False
            # Ensure at least one device is usable
            gpus = cuda.gpus
            if len(gpus) < 1:
                return False
            return True
        except Exception:
            return False

    # ── device memory ────────────────────────────────────────────────

    def allocate(
        self,
        shape: tuple[int, ...],
        dtype: np.dtype = np.float64,  # type: ignore[assignment]
    ) -> object:
        return self._cuda.device_array(shape, dtype=dtype)

    def zeros(
        self,
        shape: tuple[int, ...],
        dtype: np.dtype = np.float64,  # type: ignore[assignment]
    ) -> object:
        arr = self._cuda.device_array(shape, dtype=dtype)
        # Numba doesn't have a direct zeros — upload a host zeros array
        arr.copy_to_device(np.zeros(shape, dtype=dtype))
        return arr

    def to_device(self, host_array: NDArray[np.floating]) -> object:
        return self._cuda.to_device(host_array)

    def to_host(self, device_array: object) -> NDArray[np.floating]:
        return device_array.copy_to_host()  # type: ignore[union-attr]

    # ── synchronisation ──────────────────────────────────────────────

    def synchronize(self) -> None:
        self._cuda.synchronize()

    # ── internal ─────────────────────────────────────────────────────

    @staticmethod
    def _query_info(device_id: int) -> GPUInfo:
        from numba import cuda

        dev = cuda.gpus[device_id]
        with dev:
            ctx = cuda.current_context()
            cc = dev.compute_capability
            name = dev.name
            # Numba exposes TOTAL_MEMORY via the device attrs
            mem_info = ctx.get_memory_info()
            total_mem = mem_info.total
            driver_ver = str(cuda.runtime.get_version())
        return GPUInfo(
            device_name=name if isinstance(name, str) else name.decode(),
            total_memory_mb=total_mem // (1024 * 1024),
            compute_capability=(cc[0], cc[1]),
            driver_version=driver_ver,
            device_id=device_id,
        )
