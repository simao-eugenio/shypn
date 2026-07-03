"""Signal hierarchy base — abstract interface and value objects.

Defines the algorithm-agnostic contract that hierarchy implementations
must satisfy, and the :class:`LambdaViolation` value object shared by
all implementations.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass(frozen=True)
class LambdaViolation:
    """One λ-ordering violation in the signal-flow DAG G_s.

    A violation exists when a G_s edge ``p_source → t → p_target``
    has ``λ(p_source) ≥ λ(p_target)``, breaking the strict-order
    requirement ``λ(p_source) < λ(p_target)`` for every edge in G_s
    (SHyPN formalism §3.3).

    Attributes:
        arc_id:          ID of the signal-flow arc that introduced the edge.
        source_place_id: ID of the upstream signal place.
        target_place_id: ID of the downstream signal place.
        lambda_source:   λ value of the source place.
        lambda_target:   λ value of the target place.
    """

    arc_id: str
    source_place_id: str
    target_place_id: str
    lambda_source: int
    lambda_target: int

    def __str__(self) -> str:
        return (
            f"λ-violation: arc {self.arc_id}: "
            f"λ({self.source_place_id})={self.lambda_source} "
            f"≥ λ({self.target_place_id})={self.lambda_target}"
        )


class SignalHierarchyBase(ABC):
    """Abstract base for signal-hierarchy computation strategies.

    Concrete subclasses provide a specific graph-traversal algorithm
    for computing λ and validating a given λ assignment against the
    model topology.

    Current concrete subclass: :class:`~kahn.KahnSignalHierarchy`.
    """

    @abstractmethod
    def compute_lambda_map(self, model: Any) -> Dict[str, int]:
        """Compute λ: Ψ_biological → ℕ₀ layer assignments.

        Args:
            model: Any object exposing ``.places`` (iterable or dict)
                   and ``.arcs`` (iterable or dict).

        Returns:
            ``{place_id: λ}`` for all non-SPATIAL signal places.
            Non-signal places and SPATIAL signal places are absent.

        Raises:
            ValueError: If G_s contains a directed cycle.
        """

    @abstractmethod
    def validate_topology(
        self,
        model: Any,
        lambda_map: Dict[str, int],
    ) -> List[LambdaViolation]:
        """Validate that every G_s edge satisfies λ(source) < λ(target).

        Args:
            model:      Same model object passed to :meth:`compute_lambda_map`.
            lambda_map: A λ assignment — may be freshly computed or loaded
                        from stored ``place.layer`` values in a ``.shy`` file.

        Returns:
            List of :class:`LambdaViolation` instances.
            Returns an empty list when the topology is well-formed.
        """
