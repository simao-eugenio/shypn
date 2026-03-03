"""Locality Controller — subnet model assembly service.

Extracts the pure-model (GTK-free) portion of locality management from
``ViabilityPanel``:

* Detecting places referenced in transition rate formulas
* Extracting place-ID sets from formula strings via regex
* Augmenting subnet place sets with formula-referenced places
* Assembling a ``DocumentModel`` from a set of selected localities

All dependencies are injected via callables at construction time so this
module has no import-time coupling to ``ViabilityPanel`` or GTK.

Architecture follows the Phase-6 ABC + concrete pattern:

    AbstractLocalityController (ABC)
        └── LocalityController            ← concrete implementation
"""
from __future__ import annotations

import re
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, Set


class AbstractLocalityController(ABC):
    """Public contract for subnet-model assembly operations."""

    @abstractmethod
    def detect_formula_referenced_places(self, transition_obj: Any) -> List[Any]:
        """Return Place objects referenced in *transition_obj*'s rate formula
        that are NOT already members of its locality.

        Args:
            transition_obj: Transition model object.

        Returns:
            List of Place objects (may be empty).
        """

    @abstractmethod
    def extract_place_ids_from_formula(
        self,
        formula: str,
        model: Any,
        selected_localities: Optional[Dict[str, Any]] = None,
        transition_id: Optional[str] = None,
    ) -> List[Any]:
        """Return Place objects whose IDs appear in *formula* but are not
        already in the locality of *transition_id*.

        Args:
            formula: Rate-formula string to parse.
            model: Model whose place list is searched.
            selected_localities: Panel's ``selected_localities`` dict — used to
                look up the locality when *transition_id* is given.  Pass
                ``None`` to skip locality filtering.
            transition_id: Transition whose locality provides the exclusion
                list.  Ignored when ``None``.

        Returns:
            List of Place objects referenced by *formula* that are outside the
            existing locality.
        """

    @abstractmethod
    def add_formula_referenced_places(
        self, transitions: Any, places_set: Set[Any]
    ) -> None:
        """Augment *places_set* in-place with places referenced in the rate
        formulas of every transition in *transitions*.

        Args:
            transitions: Iterable of Transition objects.
            places_set: Mutable set of Place objects (modified in-place).
        """

    @abstractmethod
    def create_subnet_model(
        self, selected_localities: Dict[str, Any]
    ) -> Any:
        """Build and return a ``DocumentModel`` from *selected_localities*.

        Uses direct object references (no deep-copy) so edits made via the
        panel's parameter tables update the live canvas objects.

        Args:
            selected_localities: Panel's ``selected_localities`` dict mapping
                ``transition_id -> {'locality': ..., 'formula_places': [...],
                ...}``.

        Returns:
            Populated ``DocumentModel`` instance.
        """


class LocalityController(AbstractLocalityController):
    """Concrete locality-controller implementation.

    Injected dependencies
    ---------------------
    get_canvas_manager : callable () -> CanvasManager | None
        Returns the currently active canvas manager (may return ``None``).
    get_current_model : callable () -> DocumentModel | None
        Returns the currently active document model (may return ``None``).
    """

    def __init__(
        self,
        get_canvas_manager: Callable[[], Any],
        get_current_model: Callable[[], Any],
    ) -> None:
        self._get_canvas_manager = get_canvas_manager
        self._get_current_model = get_current_model

    # ── public API ────────────────────────────────────────────────────────────

    def detect_formula_referenced_places(self, transition_obj: Any) -> List[Any]:
        """Return places referenced in *transition_obj*'s formula but outside
        its locality."""
        canvas_mgr = self._get_canvas_manager()
        if not canvas_mgr or not canvas_mgr._document_model:
            return []

        all_places: Dict[str, Any] = {
            p.id: p for p in canvas_mgr._document_model.places
        }

        # Resolve formula — priority: properties dict > string rate attribute
        formula: Optional[str] = None
        if (
            hasattr(transition_obj, 'properties')
            and isinstance(transition_obj.properties, dict)
        ):
            formula = (
                transition_obj.properties.get('rate_function')
                or transition_obj.properties.get('rate_function_display')
            )
        if not formula:
            rate_attr = getattr(transition_obj, 'rate', None)
            if rate_attr and isinstance(rate_attr, str) and rate_attr.strip():
                formula = rate_attr
        if not formula:
            return []

        # Extract identifier tokens
        referenced_place_ids: Set[str] = set()
        for match in re.findall(r'\b([A-Za-z_][A-Za-z0-9_]*)\b', formula):
            if match in all_places:
                referenced_place_ids.add(match)

        # Determine which place IDs are already in the locality
        model = self._get_current_model()
        if not model:
            return []

        try:
            from shypn.diagnostic import LocalityDetector
            locality_detector = LocalityDetector(model)
            locality = locality_detector.get_locality_for_transition(transition_obj)
            locality_place_ids: Set[str] = set()
            for p in locality.input_places:
                locality_place_ids.add(p.id)
            for p in locality.output_places:
                locality_place_ids.add(p.id)
            for p in locality.catalyst_places:
                locality_place_ids.add(p.id)
        except Exception:
            locality_place_ids = set()

        return [
            all_places[pid]
            for pid in referenced_place_ids
            if pid not in locality_place_ids and pid in all_places
        ]

    def extract_place_ids_from_formula(
        self,
        formula: str,
        model: Any,
        selected_localities: Optional[Dict[str, Any]] = None,
        transition_id: Optional[str] = None,
    ) -> List[Any]:
        """Return Place objects whose IDs appear in *formula* but are not in
        the locality of *transition_id*."""
        if not formula or not model:
            return []

        all_places: Dict[str, Any] = {p.id: p for p in model.places}

        # Build exclusion set from existing locality
        locality_place_ids: Set[str] = set()
        if transition_id and selected_localities and transition_id in selected_localities:
            locality = selected_localities[transition_id].get('locality')
            if locality:
                locality_place_ids.update(p.id for p in locality.input_places)
                locality_place_ids.update(p.id for p in locality.output_places)
                locality_place_ids.update(p.id for p in locality.catalyst_places)

        referenced: List[Any] = []
        for match in re.findall(r'\b([A-Za-z_][A-Za-z0-9_]*)\b', formula):
            if match in all_places and match not in locality_place_ids:
                referenced.append(all_places[match])
        return referenced

    def add_formula_referenced_places(
        self, transitions: Any, places_set: Set[Any]
    ) -> None:
        """Augment *places_set* in-place with places referenced in any
        transition's rate formula that are not already present."""
        canvas_mgr = self._get_canvas_manager()
        if not canvas_mgr or not canvas_mgr._document_model:
            return

        all_places: Dict[str, Any] = {
            p.id: p for p in canvas_mgr._document_model.places
        }

        for transition in transitions:
            formula: Optional[str] = None
            if (
                hasattr(transition, 'properties')
                and isinstance(transition.properties, dict)
            ):
                formula = (
                    transition.properties.get('rate_function')
                    or transition.properties.get('rate_function_display')
                )
            if not formula and hasattr(transition, 'formula') and transition.formula:
                formula = transition.formula
            if not formula and isinstance(getattr(transition, 'rate', None), str):
                formula = transition.rate
            if not formula:
                continue

            current_ids: Set[str] = {p.id for p in places_set}
            for match in re.findall(r'\b([A-Za-z_][A-Za-z0-9_]*)\b', formula):
                if match in all_places and match not in current_ids:
                    places_set.add(all_places[match])
                    current_ids.add(match)
                    print(
                        f"[SUBNET] Added place '{match}' referenced in formula "
                        f"for transition '{transition.id}'"
                    )

    def create_subnet_model(
        self, selected_localities: Dict[str, Any]
    ) -> Any:
        """Build a ``DocumentModel`` from *selected_localities*.

        Uses direct object references — no deep-copy — so inline edits in the
        panel's parameter table update the actual canvas objects.
        """
        from shypn.data.canvas.document_model import DocumentModel

        subnet_places: Set[Any] = set()
        subnet_transitions: Set[Any] = set()
        subnet_arcs: Set[Any] = set()

        for _tid, data in selected_localities.items():
            locality = data.get('locality')
            if not locality:
                continue
            subnet_transitions.add(locality.transition)
            subnet_places.update(locality.input_places)
            subnet_places.update(locality.output_places)
            subnet_places.update(locality.catalyst_places)
            subnet_places.update(data.get('formula_places', []))
            subnet_arcs.update(locality.input_arcs)
            subnet_arcs.update(locality.output_arcs)
            subnet_arcs.update(locality.catalyst_arcs)

        # Augment with any additional formula-referenced places
        self.add_formula_referenced_places(subnet_transitions, subnet_places)

        model = DocumentModel()
        model.places = list(subnet_places)
        model.transitions = list(subnet_transitions)
        model.arcs = list(subnet_arcs)
        return model
