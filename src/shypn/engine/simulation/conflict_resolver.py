"""Conflict resolver for maximal-step Petri net execution.

This module provides:
- ``AbstractConflictResolver`` (ABC) — typed public contract.
- ``ConflictResolver`` (concrete) — full implementation of the three-phase
  maximal-step algorithm extracted from ``SimulationController``.

The three phases are:

Phase 1 — Locality Independence Detection
    Computes which transitions share places (conflict graph).

Phase 2 — Maximal Concurrent Set Computation
    Finds maximal sets of mutually independent (non-conflicting) transitions
    using a hybrid greedy strategy with O(k·n²) complexity.

Phase 3 — Atomic Maximal Step Execution
    Selects and atomically fires a maximal concurrent set with full rollback
    guarantee on failure (snapshot → commit → restore pattern).
"""
from __future__ import annotations

import logging
import random
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Set, Tuple

logger = logging.getLogger(__name__)


# ============================================================================
# Abstract base class
# ============================================================================

class AbstractConflictResolver(ABC):
    """Abstract contract for conflict-resolution in maximal-step semantics.

    Implementors must provide:
    - A way to determine which transitions conflict (share places).
    - A way to enumerate maximal concurrent sets.
    - A way to atomically execute a selected set (with rollback).
    """

    # ------------------------------------------------------------------ #
    # Phase 1 — Conflict graph                                             #
    # ------------------------------------------------------------------ #

    @abstractmethod
    def are_independent(self, t1: Any, t2: Any) -> bool:
        """Return True if *t1* and *t2* share no places."""
        ...

    @abstractmethod
    def compute_conflict_sets(self, transitions: List[Any]) -> Dict[Any, Set[Any]]:
        """Return a mapping ``transition_id → set_of_conflicting_ids``."""
        ...

    @abstractmethod
    def get_independent_groups(self, transitions: List[Any]) -> List[List[Any]]:
        """Partition *transitions* into mutually-independent groups."""
        ...

    # ------------------------------------------------------------------ #
    # Phase 2 — Maximal concurrent sets                                    #
    # ------------------------------------------------------------------ #

    @abstractmethod
    def find_maximal_concurrent_sets(
        self, enabled: List[Any], max_sets: int = 5
    ) -> List[List[Any]]:
        """Return up to *max_sets* maximal concurrent sets from *enabled*."""
        ...

    @abstractmethod
    def is_concurrent_set_maximal(
        self,
        concurrent_set: List[Any],
        all_enabled: List[Any],
        conflict_sets: Dict[Any, Set[Any]],
    ) -> bool:
        """Return True if *concurrent_set* cannot be extended."""
        ...

    # ------------------------------------------------------------------ #
    # Phase 3 — Atomic execution                                          #
    # ------------------------------------------------------------------ #

    @abstractmethod
    def select_maximal_set(
        self, maximal_sets: List[List[Any]], strategy: str = "largest"
    ) -> List[Any]:
        """Select which maximal set to execute according to *strategy*."""
        ...

    @abstractmethod
    def validate_all_can_fire(self, transition_set: List[Any]) -> bool:
        """Return True only if every transition in *transition_set* is enabled."""
        ...

    @abstractmethod
    def execute_maximal_step(
        self, transition_set: List[Any]
    ) -> Tuple[bool, List[Any], str]:
        """Atomically fire *transition_set*.

        Returns:
            ``(success, fired_transitions, error_message)``
        """
        ...


# ============================================================================
# Concrete implementation
# ============================================================================

class ConflictResolver(AbstractConflictResolver):
    """Concrete conflict resolver for maximal-step Petri net execution.

    Extracted from ``SimulationController`` (lines 1 711–2 363).  All
    algorithmic logic lives here; the controller holds only a thin
    delegation wrapper.

    Args:
        model: The Petri net model (must expose ``.places`` and ``.arcs``).
        viability_checker: Object with ``validate_all(transitions) -> bool``.
        get_places_fn: Callable ``(transition) -> set`` returning the set of
            place IDs in a transition's neighbourhood (input ∪ output).
            Typically ``SimulationController._get_all_places_for_transition``.
    """

    def __init__(
        self,
        model: Any,
        viability_checker: Any,
        get_places_fn: Callable[[Any], Set[Any]],
    ) -> None:
        self._model = model
        self._viability_checker = viability_checker
        self._get_places = get_places_fn

    # ------------------------------------------------------------------ #
    # Phase 1 — Conflict graph                                             #
    # ------------------------------------------------------------------ #

    def are_independent(self, t1: Any, t2: Any) -> bool:
        """Return True if *t1* and *t2* share no places.

        Two transitions are independent when:
            (•t1 ∪ t1•) ∩ (•t2 ∪ t2•) = ∅
        """
        places_t1: Set[Any] = self._get_places(t1)
        places_t2: Set[Any] = self._get_places(t2)
        return len(places_t1 & places_t2) == 0

    def compute_conflict_sets(self, transitions: List[Any]) -> Dict[Any, Set[Any]]:
        """Build conflict graph: ``transition_id → set_of_conflicting_ids``.

        Args:
            transitions: Transition objects to analyse.

        Returns:
            Dictionary mapping each transition ID to the IDs of all
            transitions it conflicts with (shares at least one place).

        Example::

            {
                'T1': {'T2'},   # T1 and T2 share P1
                'T2': {'T1'},
                'T3': set(),    # T3 has no conflicts
            }
        """
        conflict_sets: Dict[Any, Set[Any]] = {t.id: set() for t in transitions}
        for i, t1 in enumerate(transitions):
            for t2 in transitions[i + 1 :]:
                if not self.are_independent(t1, t2):
                    conflict_sets[t1.id].add(t2.id)
                    conflict_sets[t2.id].add(t1.id)
        return conflict_sets

    def get_independent_groups(self, transitions: List[Any]) -> List[List[Any]]:
        """Partition *transitions* into mutually-independent groups.

        Transitions within each group are pairwise non-conflicting.
        Used for debugging and locality-visualisation.
        """
        if not transitions:
            return []

        conflict_sets = self.compute_conflict_sets(transitions)
        groups: List[List[Any]] = []
        remaining: Set[Any] = {t.id for t in transitions}
        by_id: Dict[Any, Any] = {t.id: t for t in transitions}

        while remaining:
            first_id = next(iter(remaining))
            group = [by_id[first_id]]
            remaining.remove(first_id)

            for tid in list(remaining):
                if all(tid not in conflict_sets[gt.id] for gt in group):
                    group.append(by_id[tid])
                    remaining.remove(tid)

            groups.append(group)

        return groups

    # ------------------------------------------------------------------ #
    # Phase 2 — Maximal concurrent sets                                    #
    # ------------------------------------------------------------------ #

    def find_maximal_concurrent_sets(
        self, enabled: List[Any], max_sets: int = 5
    ) -> List[List[Any]]:
        """Find up to *max_sets* maximal concurrent sets from *enabled*.

        A maximal concurrent set is a set of transitions that are:
        1. Mutually independent (no shared places).
        2. Cannot be extended without introducing a conflict.

        Uses four greedy strategies to explore diverse sets without
        exponential complexity (O(k·n²), k = max_sets, n = |enabled|).
        """
        if not enabled:
            return []
        if len(enabled) == 1:
            return [[enabled[0]]]

        conflict_sets = self.compute_conflict_sets(enabled)
        maximal: List[List[Any]] = []
        seen: Set[frozenset[Any]] = set()

        def _try_add(candidate: List[Any]) -> None:
            if candidate:
                key = frozenset(t.id for t in candidate)
                if key not in seen:
                    seen.add(key)
                    maximal.append(candidate)

        # Strategy 1: natural order
        _try_add(self._greedy_maximal_set(enabled, conflict_sets, start_index=0))

        # Strategy 2: rotated starting points
        for start in range(1, min(len(enabled), max_sets)):
            if len(maximal) >= max_sets:
                break
            _try_add(self._greedy_maximal_set(enabled, conflict_sets, start_index=start))

        # Strategy 3: most-conflicts first (handle constrained transitions first)
        if len(maximal) < max_sets:
            ordered = self._sort_by_conflict_degree(enabled, conflict_sets, ascending=False)
            _try_add(self._greedy_maximal_set(ordered, conflict_sets, start_index=0))

        # Strategy 4: least-conflicts first (maximise set size)
        if len(maximal) < max_sets:
            ordered = self._sort_by_conflict_degree(enabled, conflict_sets, ascending=True)
            _try_add(self._greedy_maximal_set(ordered, conflict_sets, start_index=0))

        return maximal

    def _greedy_maximal_set(
        self,
        transitions: List[Any],
        conflict_sets: Dict[Any, Set[Any]],
        start_index: int = 0,
    ) -> List[Any]:
        """Build one maximal concurrent set by greedy selection.

        Starting at *start_index*, adds each transition that is independent
        of all transitions already in the set (O(n²)).
        """
        if not transitions:
            return []
        ordered = transitions[start_index:] + transitions[:start_index]
        result = [ordered[0]]
        result_ids: Set[Any] = {ordered[0].id}
        for t in ordered[1:]:
            if all(t.id not in conflict_sets[tid] for tid in result_ids):
                result.append(t)
                result_ids.add(t.id)
        return result

    def _sort_by_conflict_degree(
        self,
        transitions: List[Any],
        conflict_sets: Dict[Any, Set[Any]],
        ascending: bool = True,
    ) -> List[Any]:
        """Sort *transitions* by number of conflicts (ascending or descending)."""
        return sorted(
            transitions,
            key=lambda t: len(conflict_sets.get(t.id, set())),
            reverse=not ascending,
        )

    def is_concurrent_set_maximal(
        self,
        concurrent_set: List[Any],
        all_enabled: List[Any],
        conflict_sets: Dict[Any, Set[Any]],
    ) -> bool:
        """Return True if *concurrent_set* cannot be extended."""
        set_ids: Set[Any] = {t.id for t in concurrent_set}
        for t in all_enabled:
            if t.id in set_ids:
                continue
            if all(t.id not in conflict_sets[tid] for tid in set_ids):
                return False  # Found a transition we could add
        return True

    # ------------------------------------------------------------------ #
    # Phase 3 — Atomic execution                                          #
    # ------------------------------------------------------------------ #

    def select_maximal_set(
        self, maximal_sets: List[List[Any]], strategy: str = "largest"
    ) -> List[Any]:
        """Select which maximal set to fire.

        Strategies:
            ``'largest'``  — maximise parallelism (default).
            ``'priority'`` — maximise sum of transition priorities.
            ``'random'``   — random choice (for exploration).
            ``'first'``    — first set in list (deterministic).
        """
        if not maximal_sets:
            return []
        if strategy == "largest":
            return max(maximal_sets, key=len)
        if strategy == "priority":
            return max(maximal_sets, key=lambda s: sum(getattr(t, "priority", 0) for t in s))
        if strategy == "random":
            return random.choice(maximal_sets)
        # "first" or unknown → deterministic fallback
        return maximal_sets[0]

    def validate_all_can_fire(self, transition_set: List[Any]) -> bool:
        """Return True only if every transition in *transition_set* is enabled.

        Delegates to the injected viability checker.
        """
        return self._viability_checker.validate_all(transition_set)  # type: ignore[no-any-return]

    def _snapshot_marking(self) -> Dict[Any, int]:
        """Snapshot current token counts for rollback.

        Returns:
            ``{place_id: token_count}`` for all places in the model.
        """
        places = self._model.places if hasattr(self._model, "places") else []
        if isinstance(places, dict):
            return {p.id: p.tokens for p in places.values()}
        return {p.id: p.tokens for p in places}

    def _restore_marking(self, snapshot: Dict[Any, int]) -> None:
        """Restore token counts from *snapshot* (rollback).

        Args:
            snapshot: Dict previously produced by :meth:`_snapshot_marking`.
        """
        places = self._model.places if hasattr(self._model, "places") else []
        if isinstance(places, dict):
            places = places.values()
        for place in places:
            if place.id in snapshot:
                place.tokens = snapshot[place.id]

    def execute_maximal_step(
        self, transition_set: List[Any]
    ) -> Tuple[bool, List[Any], str]:
        """Atomically fire all transitions in *transition_set*.

        Uses a three-phase commit protocol:

        1. **Validate** — pre-flight check for all transitions.
        2. **Prepare** — snapshot current marking.
        3. **Commit** — fire all transitions; rollback on any failure.

        Returns:
            ``(success, fired_transitions, error_message)``

            On failure the net state is rolled back to the pre-attempt marking.
        """
        if not transition_set:
            return (False, [], "Empty transition set")

        # Phase 1: Validate
        if not self.validate_all_can_fire(transition_set):
            return (False, [], "Pre-condition failed: Not all transitions enabled")

        # Phase 2: Prepare
        snapshot = self._snapshot_marking()

        try:
            fired: List[Any] = []

            # Deterministic execution order: descending priority then ID
            sorted_set = sorted(
                transition_set,
                key=lambda t: (getattr(t, "priority", 0), t.id),
                reverse=True,
            )

            for transition in sorted_set:
                # Consume input tokens
                for arc in self._model.arcs:
                    if arc.target is not transition:
                        continue
                    arc_type = getattr(arc, "arc_type", "normal")
                    if arc_type == "test":
                        continue  # Read arc — no consumption
                    place = arc.source
                    tokens_consumed: int = getattr(arc, "weight", 1)
                    if place.tokens < tokens_consumed:
                        raise RuntimeError(
                            f"{transition.id} cannot fire: {place.id} has "
                            f"{place.tokens} < {tokens_consumed} tokens"
                        )
                    place.tokens -= tokens_consumed

                # Execute optional transition behaviour
                behavior = getattr(transition, "behavior", None)
                if behavior is not None:
                    try:
                        behavior.execute()
                    except (AttributeError, TypeError, ValueError) as exc:
                        raise RuntimeError(
                            f"{transition.id} behavior failed: {exc}"
                        ) from exc

                # Produce output tokens
                for arc in self._model.arcs:
                    if arc.source is not transition:
                        continue
                    place = arc.target
                    place.tokens += getattr(arc, "weight", 1)

                fired.append(transition)

            return (True, fired, "")

        except Exception as exc:
            logger.error("Transition firing failed: %s", exc)
            self._restore_marking(snapshot)
            return (False, [], f"Execution failed: {exc}, rolled back")
