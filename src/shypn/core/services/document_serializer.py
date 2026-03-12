"""DocumentSerializer — concrete document serialization service.

Sprint 20 — Phase 7: implementation of
:class:`~shypn.core.services.abstract_document_serializer.AbstractDocumentSerializer`
extracted from ``ModelCanvasManager``.

Usage (inside ModelCanvasManager)::

    from shypn.core.services.document_serializer import DocumentSerializer
    _serializer = DocumentSerializer()   # shared singleton, stateless

    # Then MCM methods become one-liners:
    def to_document_model(self):
        return _serializer.to_document_model(self)
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List, Optional, cast

from shypn.core.services.abstract_document_serializer import AbstractDocumentSerializer

__all__ = ["DocumentSerializer"]

logger = logging.getLogger(__name__)

# Module-level singleton — DocumentSerializer is stateless; one instance is enough.
_default_serializer: Optional["DocumentSerializer"] = None


def get_serializer() -> "DocumentSerializer":
    """Return the module-level shared :class:`DocumentSerializer` instance."""
    global _default_serializer
    if _default_serializer is None:
        _default_serializer = DocumentSerializer()
    return _default_serializer


class DocumentSerializer(AbstractDocumentSerializer):  # type: ignore[misc]
    """Stateless serializer for *ModelCanvasManager* documents.

    All public methods accept ``manager`` (a :class:`~shypn.data.model_canvas_manager.ModelCanvasManager`
    instance) as their first positional argument and operate purely on
    the data exposed by that object.  No internal state is stored — the
    same instance can safely be used for multiple documents.
    """

    # ------------------------------------------------------------------
    # Primary serialization
    # ------------------------------------------------------------------

    def to_document_model(self, manager: Any) -> Any:
        """Build a ``DocumentModel`` from *manager*'s Petri net objects.

        Colour-reset/restore cycle ensures analysis colours are not
        persisted: original visualisation colours are saved before the
        model is built, defaults are written into the model, then the live
        canvas is restored.
        """
        from shypn.data.canvas import DocumentModel

        original_colors = self._reset_analysis_colors_for_save(manager)

        document = DocumentModel()
        self._populate_document_objects(document, manager)
        self._sync_id_counters(document, manager)
        self._sync_view_state(document, manager)

        self._restore_analysis_colors(original_colors, manager)

        return document

    # ------------------------------------------------------------------
    # View-state persistence
    # ------------------------------------------------------------------

    def get_view_state(self, manager: Any) -> Dict[str, Any]:
        """Return a JSON-serialisable view-state dict."""
        return {
            "pan_x": manager.pan_x,
            "pan_y": manager.pan_y,
            "zoom": manager.zoom,
            "transformations": manager.transformation_manager.to_dict(),
        }

    def set_view_state(
        self, manager: Any, view_state: Optional[Dict[str, Any]]
    ) -> None:
        """Restore *manager*'s view from *view_state*."""
        if not view_state:
            return

        manager.pan_x = view_state.get("pan_x", 0.0)
        manager.pan_y = view_state.get("pan_y", 0.0)
        manager.zoom = view_state.get("zoom", 1.0)

        # Clamp zoom to manager's valid range
        manager.zoom = max(manager.MIN_ZOOM, min(manager.MAX_ZOOM, manager.zoom))

        # Sync viewport_controller BEFORE clamping pan
        vc = getattr(manager, "viewport_controller", None)
        if vc is not None:
            vc.pan_x = manager.pan_x
            vc.pan_y = manager.pan_y
            vc.zoom = manager.zoom
            vc._initial_pan_set = True  # suppress auto-centering

        manager.clamp_pan()

        # Sync back post-clamp
        if vc is not None:
            manager.pan_x = vc.pan_x
            manager.pan_y = vc.pan_y

        if "transformations" in view_state:
            manager.transformation_manager.from_dict(view_state["transformations"])

        manager._initial_pan_set = True
        manager.mark_dirty()
        manager.mark_needs_redraw()

    def save_view_state_to_file(
        self, manager: Any, filepath: Optional[str] = None
    ) -> bool:
        """Persist the view state to *filepath* (default: ``~/.shypn/<name>_view.json``)."""
        if filepath is None:
            filepath = self._default_view_state_path(manager)

        try:
            view_state = self.get_view_state(manager)
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, "w") as fh:
                json.dump(view_state, fh, indent=2)
            return True
        except (OSError, IOError, PermissionError, TypeError) as exc:
            logger.debug("DocumentSerializer.save_view_state_to_file failed: %s", exc)
            return False

    def load_view_state_from_file(
        self, manager: Any, filepath: Optional[str] = None
    ) -> bool:
        """Load and apply view state from *filepath*.

        Calls :meth:`~ModelCanvasManager.center_view_on_content` as fallback
        when the file does not exist.
        """
        if filepath is None:
            filepath = self._default_view_state_path(manager)

        if not os.path.exists(filepath):
            manager.center_view_on_content()
            return False

        try:
            with open(filepath, "r") as fh:
                view_state = json.load(fh)
            self.set_view_state(manager, view_state)
            return True
        except Exception as exc:
            logger.debug("DocumentSerializer.load_view_state_from_file failed: %s", exc)
            manager.center_view_on_content()
            return False

    # ------------------------------------------------------------------
    # Document metadata snapshot
    # ------------------------------------------------------------------

    def get_document_state(self, manager: Any) -> Dict[str, Any]:
        """Return a snapshot dict of metadata about the current document."""
        created_at = getattr(manager, "created_at", None)
        modified_at = getattr(manager, "modified_at", None)
        return {
            "filename": manager.filename,
            "modified": manager.modified,
            "created_at": created_at.isoformat() if created_at else None,
            "modified_at": modified_at.isoformat() if modified_at else None,
            "canvas": {
                "width": manager.canvas_width,
                "height": manager.canvas_height,
                "zoom": manager.zoom,
                "pan_x": manager.pan_x,
                "pan_y": manager.pan_y,
                "grid_style": manager.grid_style,
            },
            "viewport": {
                "width": manager.viewport_width,
                "height": manager.viewport_height,
            },
        }

    # ------------------------------------------------------------------
    # Private helpers — colour-reset cluster
    # ------------------------------------------------------------------

    @staticmethod
    def _should_preserve_transition_color(transition: Any) -> bool:
        return cast(bool, transition.is_source or transition.is_sink)

    @staticmethod
    def _should_preserve_place_color(place: Any) -> bool:
        from shypn.utils.color_schema_manager import ColorSchemaManager
        return cast(bool, ColorSchemaManager.is_semantic_place_color(place))

    @staticmethod
    def _should_preserve_arc_color(arc: Any) -> bool:
        from shypn.netobjs.arc import Arc
        return cast(bool, arc.color != Arc.DEFAULT_COLOR)

    def _reset_transition_colors_to_default(self, manager: Any) -> None:
        from shypn.netobjs import Transition
        for t in manager.transitions:
            if self._should_preserve_transition_color(t):
                continue
            t.border_color = Transition.DEFAULT_BORDER_COLOR
            t.fill_color = Transition.DEFAULT_COLOR

    def _reset_place_colors_to_default(self, manager: Any) -> None:
        from shypn.netobjs import Place
        for p in manager.places:
            if self._should_preserve_place_color(p):
                continue
            p.border_color = Place.DEFAULT_BORDER_COLOR

    def _reset_arc_colors_to_default(self, manager: Any) -> None:
        from shypn.netobjs.arc import Arc
        from shypn.netobjs.signal_flow_arc import SignalFlowArc
        for arc in manager.arcs:
            if self._should_preserve_arc_color(arc):
                continue
            if isinstance(arc, SignalFlowArc):
                arc.color = SignalFlowArc.DEFAULT_COLOR
            else:
                arc.color = Arc.DEFAULT_COLOR

    def _store_and_reset_transition_colors(self, manager: Any) -> List[Any]:
        from shypn.netobjs import Transition
        original: List[Any] = []
        for t in manager.transitions:
            if self._should_preserve_transition_color(t):
                original.append(None)
                continue
            original.append((t.border_color, t.fill_color))
            t.border_color = Transition.DEFAULT_BORDER_COLOR
            t.fill_color = Transition.DEFAULT_COLOR
        return original

    def _store_and_reset_place_colors(self, manager: Any) -> List[Any]:
        from shypn.netobjs import Place
        original: List[Any] = []
        for p in manager.places:
            if self._should_preserve_place_color(p):
                original.append(None)
                continue
            original.append(p.border_color)
            p.border_color = Place.DEFAULT_BORDER_COLOR
        return original

    def _store_and_reset_arc_colors(self, manager: Any) -> List[Any]:
        from shypn.netobjs.arc import Arc
        from shypn.netobjs.signal_flow_arc import SignalFlowArc
        original: List[Any] = []
        for arc in manager.arcs:
            if isinstance(arc, SignalFlowArc):
                if arc.color != SignalFlowArc.DEFAULT_COLOR:
                    original.append(None)
                    continue
                original.append(arc.color)
                arc.color = SignalFlowArc.DEFAULT_COLOR
            else:
                if arc.color != Arc.DEFAULT_COLOR:
                    original.append(None)
                    continue
                original.append(arc.color)
                arc.color = Arc.DEFAULT_COLOR
        return original

    def _reset_analysis_colors_for_save(self, manager: Any) -> Dict[str, List[Any]]:
        return {
            "transitions": self._store_and_reset_transition_colors(manager),
            "places": self._store_and_reset_place_colors(manager),
            "arcs": self._store_and_reset_arc_colors(manager),
        }

    @staticmethod
    def _restore_analysis_colors(
        original_colors: Dict[str, List[Any]], manager: Any
    ) -> None:
        for i, t in enumerate(manager.transitions):
            if i < len(original_colors["transitions"]) and original_colors["transitions"][i] is not None:
                t.border_color, t.fill_color = original_colors["transitions"][i]
        for i, p in enumerate(manager.places):
            if i < len(original_colors["places"]) and original_colors["places"][i] is not None:
                p.border_color = original_colors["places"][i]
        for i, arc in enumerate(manager.arcs):
            if i < len(original_colors["arcs"]) and original_colors["arcs"][i] is not None:
                arc.color = original_colors["arcs"][i]

    # ------------------------------------------------------------------
    # Private helpers — document population
    # ------------------------------------------------------------------

    @staticmethod
    def _populate_document_objects(document: Any, manager: Any) -> None:
        document.places = list(manager.places)
        document.transitions = list(manager.transitions)
        document.arcs = list(manager.arcs)
        if (
            hasattr(manager, "document_controller")
            and hasattr(manager.document_controller, "modules")
            and manager.document_controller.modules
        ):
            document.modules = dict(manager.document_controller.modules)
        # Sync environment events
        if hasattr(manager, 'events'):
            document.events = list(manager.events)

    @staticmethod
    def _sync_id_counters(document: Any, manager: Any) -> None:
        place_id, trans_id, arc_id, module_id = (
            manager.document_controller.id_manager.get_state()
        )
        document.id_manager.set_state(place_id, trans_id, arc_id, module_id)

    @staticmethod
    def _sync_view_state(document: Any, manager: Any) -> None:
        document.view_state = {
            "zoom": manager.zoom,
            "pan_x": manager.pan_x,
            "pan_y": manager.pan_y,
            "transformations": manager.transformation_manager.to_dict(),
        }

    # ------------------------------------------------------------------
    # Private helpers — path utilities
    # ------------------------------------------------------------------

    @staticmethod
    def _default_view_state_path(manager: Any) -> str:
        config_dir = os.path.expanduser("~/.shypn")
        filename = getattr(manager, "filename", None) or "default"
        return os.path.join(config_dir, f"{filename}_view.json")
