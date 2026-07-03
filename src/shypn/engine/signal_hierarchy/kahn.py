"""Kahn-algorithm implementation of :class:`SignalHierarchyBase`.

Computes λ: Ψ_biological → ℕ₀ via Kahn topological sort over the
signal-flow graph G_s = (Ψ_biological, E_s).

Edge definition
~~~~~~~~~~~~~~~
An edge (p_i, p_j) ∈ E_s exists whenever there is a transition *t*
with a signal-flow arc from *p_i* into *t* AND a signal-flow arc
from *t* into *p_j*.

SPATIAL signal places are excluded: they are environmental scalars
(no PreemptionCheck, no POSet layer) and must not appear in λ.

Layer assignment
~~~~~~~~~~~~~~~~
Layer 0: no incoming edges in G_s (source signal places).
Layer k: ``max(λ(predecessors)) + 1``.

This ensures that when two G_s paths of different depth converge on
the same place the deeper path's layer propagates correctly.
"""
from __future__ import annotations

import logging
from collections import deque
from typing import Any, Dict, List, Set, Tuple

from .base import LambdaViolation, SignalHierarchyBase

logger = logging.getLogger(__name__)


class KahnSignalHierarchy(SignalHierarchyBase):
    """Kahn-topo-sort implementation of signal-hierarchy computation."""

    # ------------------------------------------------------------------ #
    # Public interface                                                      #
    # ------------------------------------------------------------------ #

    def compute_lambda_map(self, model: Any) -> Dict[str, int]:
        """Compute λ via Kahn topological sort on G_s.

        See :meth:`SignalHierarchyBase.compute_lambda_map` for contract.
        """
        bio_places = self._collect_biological_signal_places(model)
        if not bio_places:
            return {}

        bio_ids: Set[str] = {p.id for p in bio_places}
        triples = self._collect_gs_edge_triples(model, bio_ids)
        edges, in_degree = self._edges_from_triples(bio_ids, triples)
        layers = self._kahn_sort(bio_ids, edges, in_degree)

        if len(layers) < len(bio_ids):
            raise ValueError(
                "Signal-flow graph G_s contains a directed cycle "
                "(formalism acyclicity requirement violated)."
            )
        return layers

    def validate_topology(
        self,
        model: Any,
        lambda_map: Dict[str, int],
    ) -> List[LambdaViolation]:
        """Validate every G_s edge satisfies λ(source) < λ(target).

        See :meth:`SignalHierarchyBase.validate_topology` for contract.
        """
        bio_ids: Set[str] = set(lambda_map.keys())
        triples = self._collect_gs_edge_triples(model, bio_ids)
        violations: List[LambdaViolation] = []
        for arc_id, src_id, tgt_id in triples:
            lam_src = lambda_map.get(src_id, 0)
            lam_tgt = lambda_map.get(tgt_id, 0)
            if lam_src >= lam_tgt:
                violations.append(
                    LambdaViolation(
                        arc_id=arc_id,
                        source_place_id=src_id,
                        target_place_id=tgt_id,
                        lambda_source=lam_src,
                        lambda_target=lam_tgt,
                    )
                )
        return violations

    # ------------------------------------------------------------------ #
    # Private helpers — model traversal                                    #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _is_spatial(place: Any) -> bool:
        """Return True when *place* is a SPATIAL signal place."""
        try:
            from shypn.netobjs.signal_type import SignalType
            return (
                getattr(place, 'is_signal_place', False)
                and getattr(place, 'signal_type', None) == SignalType.SPATIAL
            )
        except ImportError:  # pragma: no cover — defensive
            return False

    def _collect_biological_signal_places(self, model: Any) -> List[Any]:
        """Return all non-SPATIAL signal places from *model.places*."""
        places = model.places
        if isinstance(places, dict):
            places = places.values()
        return [
            p for p in places
            if getattr(p, 'is_signal_place', False) and not self._is_spatial(p)
        ]

    @staticmethod
    def _iter_arcs(model: Any):
        """Yield all Arc objects from *model.arcs* (list or dict)."""
        arcs = model.arcs
        if isinstance(arcs, dict):
            yield from arcs.values()
        else:
            yield from arcs

    def _collect_gs_edge_triples(
        self,
        model: Any,
        bio_ids: Set[str],
    ) -> List[Tuple[str, str, str]]:
        """Return ``[(arc_id, src_place_id, tgt_place_id)]`` for all G_s edges.

        Duplicates (same src/tgt pair via different arcs) are collapsed —
        the first arc_id wins.  This preserves a stable set for
        ``validate_topology`` while keeping the graph structurally correct
        for ``compute_lambda_map``.
        """
        # group signal-flow arcs by the transition they touch
        t_in:  Dict[str, List[Tuple[str, str]]] = {}  # t_id → [(src_pid, arc_id)]
        t_out: Dict[str, List[str]]             = {}  # t_id → [tgt_pid]

        for arc in self._iter_arcs(model):
            if getattr(arc, 'arc_type', 'normal') != 'signal_flow':
                continue

            arc_id = str(getattr(arc, 'id', id(arc)))
            src    = getattr(arc, 'source', None)
            tgt    = getattr(arc, 'target', None)
            if src is None or tgt is None:
                continue

            src_id = getattr(src, 'id', None)
            tgt_id = getattr(tgt, 'id', None)

            # signal place → transition
            if src_id in bio_ids and hasattr(tgt, 'transition_type'):
                t_in.setdefault(tgt_id, []).append((src_id, arc_id))

            # transition → signal place
            elif tgt_id in bio_ids and hasattr(src, 'transition_type'):
                t_out.setdefault(src_id, []).append(tgt_id)

        # compose edges: every (in_place → t → out_place) triple
        triples: List[Tuple[str, str, str]] = []
        seen: Set[Tuple[str, str]] = set()
        for t_id, in_pairs in t_in.items():
            for tgt_pid in t_out.get(t_id, []):
                if tgt_pid not in bio_ids:
                    continue
                for src_pid, arc_id in in_pairs:
                    pair = (src_pid, tgt_pid)
                    if pair in seen:
                        continue
                    seen.add(pair)
                    triples.append((arc_id, src_pid, tgt_pid))

        return triples

    # ------------------------------------------------------------------ #
    # Private helpers — graph algorithm                                    #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _edges_from_triples(
        bio_ids: Set[str],
        triples: List[Tuple[str, str, str]],
    ) -> Tuple[Dict[str, List[str]], Dict[str, int]]:
        """Build adjacency list and in-degree map from edge triples."""
        edges:     Dict[str, List[str]] = {pid: [] for pid in bio_ids}
        in_degree: Dict[str, int]       = {pid: 0  for pid in bio_ids}
        for _, src_pid, tgt_pid in triples:
            edges[src_pid].append(tgt_pid)
            in_degree[tgt_pid] += 1
        return edges, in_degree

    @staticmethod
    def _kahn_sort(
        all_ids:   Set[str],
        edges:     Dict[str, List[str]],
        in_degree: Dict[str, int],
    ) -> Dict[str, int]:
        """Run Kahn topological sort; return ``{place_id: layer}``."""
        layers: Dict[str, int] = {}
        queue:  deque[str]     = deque(
            pid for pid in all_ids if in_degree[pid] == 0
        )
        for pid in queue:
            layers[pid] = 0

        while queue:
            current       = queue.popleft()
            current_layer = layers[current]
            for neighbor in edges.get(current, []):
                in_degree[neighbor] -= 1
                layers[neighbor] = max(
                    layers.get(neighbor, 0), current_layer + 1
                )
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        return layers
