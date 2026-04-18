"""GPU acceleration sub-package.

Provides runtime GPU detection with a backend abstraction layer
so that different CUDA toolkits (CuPy, Numba CUDA) can be used
interchangeably by the simulation engine.

Public API
----------
``detect_gpu``
    Probe the system and return a ready-to-use :class:`GPUBackend`
    (or ``None`` if no usable GPU is found).

``GPUBackend``
    Abstract base class — type-annotation target for downstream code.

``GPUInfo``
    Immutable data class with device properties (name, VRAM, compute
    capability, driver version).

Usage::

    from shypn.engine.acceleration.gpu import detect_gpu

    backend = detect_gpu()          # None on CPU-only machines
    if backend is not None:
        info = backend.device_info
        print(f"Using {backend.name} on {info.device_name}")
"""

from .base import GPUBackend, GPUInfo
from .detect import detect_gpu

__all__ = ["GPUBackend", "GPUInfo", "detect_gpu"]
