"""DocumentSession — per-document aggregate for the MDI architecture.

One session owns every object that belongs to a single open canvas tab:

    drawing_area          GtkDrawingArea widget (the stable identity key)
    canvas_manager        ModelCanvasManager  — places/transitions/arcs
    overlay_manager       CanvasOverlayManager — all panel loaders + swissknife
    simulation_controller SimulationController — execution engine
    knowledge_base        ModelKnowledgeBase or None

The session's :attr:`doc_id` reads the stable monotonic ID stamped on the
drawing_area widget by :func:`shypn.core.document_id.alloc_doc_id` when the
tab was first created (see ``model_canvas_loader.add_document``).

Panel loaders are proxied through ``overlay_manager`` so that
``session.report_panel_loader`` is always in sync with the overlay manager's
own attribute — no extra storage, no staleness.

Lifecycle
---------
* Created in :meth:`ModelCanvasLoader._setup_edit_palettes` after every
  per-document component has been initialised.
* Stored in ``ModelCanvasLoader.sessions[drawing_area]``.
* Destroyed (via :meth:`close`) inside ``ModelCanvasLoader.close_tab``,
  which calls ``EventBus.clear_document(self.doc_id)`` ensuring that no
  EventBus subscriptions survive the tab close.
"""

from __future__ import annotations

import logging
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from shypn.data.model_canvas_manager import ModelCanvasManager
    from shypn.canvas.canvas_overlay_manager import CanvasOverlayManager
    from shypn.engine.simulation.controller import SimulationController

logger = logging.getLogger(__name__)


class DocumentSession:
    """Aggregates every per-document component for one open MDI tab.

    Parameters
    ----------
    drawing_area:
        The GtkDrawingArea widget — the canonical key used everywhere in
        ModelCanvasLoader's four legacy dicts.
    canvas_manager:
        ModelCanvasManager instance for this tab.
    overlay_manager:
        CanvasOverlayManager that owns all panel loaders and the
        SwissKnifePalette for this tab.
    simulation_controller:
        SimulationController instance for this tab.
    knowledge_base:
        Optional ModelKnowledgeBase for model-repair support.
    """

    __slots__ = (
        'drawing_area',
        'canvas_manager',
        'overlay_manager',
        'simulation_controller',
        'knowledge_base',
    )

    def __init__(
        self,
        drawing_area,
        canvas_manager: 'ModelCanvasManager',
        overlay_manager: 'CanvasOverlayManager',
        simulation_controller: 'SimulationController',
        knowledge_base=None,
    ) -> None:
        self.drawing_area = drawing_area
        self.canvas_manager = canvas_manager
        self.overlay_manager = overlay_manager
        self.simulation_controller = simulation_controller
        self.knowledge_base = knowledge_base

    # ------------------------------------------------------------------
    # Identity helpers
    # ------------------------------------------------------------------

    @property
    def doc_id(self) -> int:
        """Stable monotonic document ID (never reused within a process).

        Reads ``drawing_area._shypn_doc_id`` stamped by
        :func:`shypn.core.document_id.alloc_doc_id` at tab-creation time.
        Falls back to ``id(drawing_area)`` for backward compatibility.
        """
        return getattr(self.drawing_area, '_shypn_doc_id', id(self.drawing_area))

    # ------------------------------------------------------------------
    # Panel-loader proxies through overlay_manager
    # ------------------------------------------------------------------

    @property
    def analyses_panel_loader(self):
        return getattr(self.overlay_manager, 'analyses_panel_loader', None)

    @property
    def report_panel_loader(self):
        return getattr(self.overlay_manager, 'report_panel_loader', None)

    @property
    def viability_panel_loader(self):
        return getattr(self.overlay_manager, 'viability_panel_loader', None)

    @property
    def pathway_panel_loader(self):
        return getattr(self.overlay_manager, 'pathway_panel_loader', None)

    @property
    def topology_panel_loader(self):
        return getattr(self.overlay_manager, 'topology_panel_loader', None)

    @property
    def swissknife_palette(self):
        return getattr(self.overlay_manager, 'swissknife_palette', None)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def close(self) -> None:
        """Release all EventBus subscriptions scoped to this document.

        Called from ``ModelCanvasLoader.close_tab`` BEFORE the GTK widget is
        destroyed and BEFORE the legacy dicts are cleaned up.  Calling this
        method is the canonical way to guarantee that no stale EventBus
        handler survives a tab close.

        Individual panel loaders may also call their own ``unsubscribe()``
        methods — that is fine; ``EventBus.clear_document`` is idempotent.
        """
        try:
            from shypn.events import EventBus
            removed = EventBus.clear_document(self.doc_id)
            logger.debug(
                "DocumentSession.close(): cleared %d EventBus subscriptions "
                "for doc_id=%d (drawing_area=%s)",
                removed, self.doc_id, self.drawing_area,
            )
        except Exception:
            logger.debug("DocumentSession.close(): EventBus.clear_document failed", exc_info=True)

    def __repr__(self) -> str:
        fname = getattr(self.canvas_manager, 'filename', '?')
        return f"DocumentSession(doc_id={self.doc_id}, filename={fname!r})"
