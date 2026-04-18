"""Abstract base class for GPU backends and device info data class.

All concrete backends (CuPy, Numba CUDA, …) inherit from
:class:`GPUBackend` and implement the abstract interface so that
the simulation engine can consume GPU services without coupling
to a specific toolkit.
"""

from __future__ import annotations

import abc
import logging
from dataclasses import dataclass
from typing import Optional

import numpy as np
from numpy.typing import NDArray

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# Device information (immutable value object)
# ------------------------------------------------------------------

@dataclass(frozen=True)
class GPUInfo:
    """Immutable snapshot of a CUDA device's properties.

    Attributes:
        device_name:        Marketing name (e.g. "GeForce RTX 5060 Ti").
        total_memory_mb:    Total VRAM in MiB.
        compute_capability: ``(major, minor)`` tuple.
        driver_version:     Driver string reported by the toolkit.
        device_id:          CUDA device ordinal (default 0).
    """

    device_name: str
    total_memory_mb: int
    compute_capability: tuple[int, int]
    driver_version: str
    device_id: int = 0

    @property
    def compute_capability_str(self) -> str:
        """Human-readable compute capability, e.g. ``'12.0'``."""
        return f"{self.compute_capability[0]}.{self.compute_capability[1]}"


# ------------------------------------------------------------------
# Abstract backend
# ------------------------------------------------------------------

class GPUBackend(abc.ABC):
    """Abstract interface that every GPU backend must implement.

    The simulation engine programmes against this contract and never
    imports CuPy or Numba CUDA directly — keeping those dependencies
    optional and swappable.

    Subclass contract
    -----------------
    * ``probe()`` — **class method**, returns ``True`` when the toolkit
      is importable AND a usable CUDA device is present.
    * ``device_info`` — property returning a :class:`GPUInfo`.
    * ``allocate(shape, dtype)`` — allocate a device array.
    * ``to_device(host_array)`` — upload a numpy array.
    * ``to_host(device_array)`` — download to numpy.
    * ``synchronize()`` — block until all queued work completes.
    """

    # ── identification ───────────────────────────────────────────────

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Short human-readable backend name (e.g. ``'cupy'``)."""

    @property
    @abc.abstractmethod
    def device_info(self) -> GPUInfo:
        """Return device properties for the active CUDA device."""

    # ── probing (class-level) ────────────────────────────────────────

    @classmethod
    @abc.abstractmethod
    def probe(cls) -> bool:
        """Return ``True`` if this backend is usable on the current host.

        Must **not** raise — return ``False`` on any import or runtime
        error so the detection loop can move to the next candidate.
        """

    # ── device memory ────────────────────────────────────────────────

    @abc.abstractmethod
    def allocate(
        self,
        shape: tuple[int, ...],
        dtype: np.dtype = np.float64,  # type: ignore[assignment]
    ) -> object:
        """Allocate an uninitialised device array.

        Returns a backend-specific device array object.
        """

    @abc.abstractmethod
    def zeros(
        self,
        shape: tuple[int, ...],
        dtype: np.dtype = np.float64,  # type: ignore[assignment]
    ) -> object:
        """Allocate a zero-initialised device array."""

    @abc.abstractmethod
    def to_device(self, host_array: NDArray[np.floating]) -> object:
        """Upload a host (numpy) array to device memory.

        Returns a backend-specific device array.
        """

    @abc.abstractmethod
    def to_host(self, device_array: object) -> NDArray[np.floating]:
        """Download a device array to host (numpy) memory."""

    # ── synchronisation ──────────────────────────────────────────────

    @abc.abstractmethod
    def synchronize(self) -> None:
        """Block until all enqueued GPU work has completed."""

    # ── convenience ──────────────────────────────────────────────────

    def check_memory(self, required_bytes: int) -> bool:
        """Return ``True`` if ``required_bytes`` fits in device VRAM.

        Default implementation uses :attr:`device_info.total_memory_mb`
        with a 90 % safety margin.  Subclasses may override with a
        runtime free-memory query.
        """
        available = self.device_info.total_memory_mb * 1024 * 1024 * 0.9
        ok = required_bytes <= available
        if not ok:
            logger.warning(
                "GPU memory check failed: need %.1f MiB, have ~%.0f MiB free",
                required_bytes / (1024 * 1024),
                available / (1024 * 1024),
            )
        return ok

    def __repr__(self) -> str:
        info = self.device_info
        return (
            f"<{type(self).__name__} device={info.device_name!r} "
            f"vram={info.total_memory_mb} MiB "
            f"cc={info.compute_capability_str}>"
        )
