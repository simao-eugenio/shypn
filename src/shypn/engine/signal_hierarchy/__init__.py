"""Signal hierarchy computation for the SHyPN 13-tuple formalism.

λ: Ψ_biological → ℕ₀ assigns each non-SPATIAL signal place to a
topological layer in the signal-flow DAG G_s.  The computation is
used at runtime to (a) validate model topology and (b) annotate
preemption-blocked messages in ``_check_preemption()``.

Public API
----------
``compute_lambda_map(model)`` → ``Dict[str, int]``
    Module-level convenience function (uses :class:`KahnSignalHierarchy`).

``validate_lambda_topology(model, lambda_map)`` → ``List[LambdaViolation]``
    Module-level convenience function (uses :class:`KahnSignalHierarchy`).

Classes
-------
:class:`LambdaViolation`
    Frozen dataclass representing one λ-ordering violation.
:class:`SignalHierarchyBase`
    Abstract base class — algorithm-agnostic interface.
:class:`KahnSignalHierarchy`
    Concrete Kahn-topo-sort implementation.
"""
from __future__ import annotations

from typing import Any, Dict, List

from .base import LambdaViolation, SignalHierarchyBase
from .kahn import KahnSignalHierarchy

__all__: List[str] = [
    "LambdaViolation",
    "SignalHierarchyBase",
    "KahnSignalHierarchy",
    "compute_lambda_map",
    "validate_lambda_topology",
]

_default: KahnSignalHierarchy | None = None


def _get_default() -> KahnSignalHierarchy:
    global _default
    if _default is None:
        _default = KahnSignalHierarchy()
    return _default


def compute_lambda_map(model: Any) -> Dict[str, int]:
    """Compute λ: Ψ_biological → ℕ₀ using the Kahn algorithm.

    Convenience wrapper — equivalent to
    ``KahnSignalHierarchy().compute_lambda_map(model)``.

    Args:
        model: Any object exposing ``.places`` and ``.arcs``.

    Returns:
        ``{place_id: λ}`` for all non-SPATIAL signal places.

    Raises:
        ValueError: If G_s contains a directed cycle.
    """
    return _get_default().compute_lambda_map(model)


def validate_lambda_topology(
    model: Any,
    lambda_map: Dict[str, int],
) -> List[LambdaViolation]:
    """Validate that every G_s edge satisfies λ(source) < λ(target).

    Convenience wrapper — equivalent to
    ``KahnSignalHierarchy().validate_topology(model, lambda_map)``.

    Args:
        model: Same model object as passed to :func:`compute_lambda_map`.
        lambda_map: A λ assignment (computed or loaded from a ``.shy`` file).

    Returns:
        List of :class:`LambdaViolation` instances — empty when well-formed.
    """
    return _get_default().validate_topology(model, lambda_map)
