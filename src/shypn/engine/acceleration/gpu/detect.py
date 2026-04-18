"""GPU detection facade.

Probes available CUDA backends in preference order and returns the
first usable one.  The result is cached for the process lifetime so
repeated calls are free.

Preference order:
    1. **CuPy** — richer NumPy-compatible API, cuRAND, cuBLAS.
    2. **Numba CUDA** — lighter dependency, already installed in many
       scientific Python environments.

Usage::

    from shypn.engine.acceleration.gpu import detect_gpu

    backend = detect_gpu()
    if backend is not None:
        print(backend.device_info)
"""

from __future__ import annotations

import logging
from typing import Optional, Sequence, Type

from .base import GPUBackend

logger = logging.getLogger(__name__)

# Cached singleton — ``None`` means "not probed yet"; ``False`` means
# "probed and no GPU found".  A :class:`GPUBackend` instance means
# "probed and ready".
_cached: Optional[GPUBackend | bool] = None


def _backend_classes() -> Sequence[Type[GPUBackend]]:
    """Return concrete backend classes in preference order.

    Imports are done inside the function so that missing packages
    (cupy, numba) never cause import-time errors.
    """
    classes: list[Type[GPUBackend]] = []
    try:
        from .cupy_backend import CuPyBackend
        classes.append(CuPyBackend)
    except Exception:
        pass
    try:
        from .numba_cuda_backend import NumbaCudaBackend
        classes.append(NumbaCudaBackend)
    except Exception:
        pass
    return classes


def detect_gpu(*, force_reprobe: bool = False) -> Optional[GPUBackend]:
    """Probe the system for a usable CUDA GPU and return a backend.

    Parameters
    ----------
    force_reprobe:
        Bypass the process-lifetime cache and re-probe (useful after
        installing a new package at runtime).

    Returns
    -------
    GPUBackend or None
        The first backend whose ``probe()`` succeeds, fully
        initialised and ready to use.  ``None`` if no usable GPU
        is found.
    """
    global _cached

    if not force_reprobe and _cached is not None:
        return _cached if isinstance(_cached, GPUBackend) else None

    logger.info("GPU detection: probing available backends…")
    for cls in _backend_classes():
        cls_name = cls.__name__
        logger.debug("  trying %s …", cls_name)
        try:
            if cls.probe():
                backend = cls()
                info = backend.device_info
                logger.info(
                    "GPU detected via %s: %s (%d MiB, CC %s)",
                    cls_name,
                    info.device_name,
                    info.total_memory_mb,
                    info.compute_capability_str,
                )
                _cached = backend
                return backend
            logger.debug("  %s: probe returned False", cls_name)
        except Exception as exc:
            logger.debug("  %s: probe failed (%s)", cls_name, exc)

    logger.info("GPU detection: no usable GPU found — CPU path will be used")
    _cached = False  # type: ignore[assignment]
    return None
