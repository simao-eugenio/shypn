"""DocumentSession — per-document aggregate for the MDI architecture.

One session owns every object that belongs to a single open canvas tab:

    drawing_area          GtkDrawingArea widget (the stable identity key)
    canvas_manager        ModelCanvasManager  — places/transitions/arcs
    overlay_manager       CanvasOverlayManager — all panel loaders + swissknife
    simulation_controller SimulationController — execution engine (may be None
                          briefly during construction; filled in by
                          DocumentPanelSetup._setup_simulation_controller)
    knowledge_base        ModelKnowledgeBase or None

Sprint 18 — Phase 7: ``DocumentSession`` is now created earlier (in
``_setup_canvas_manager``) with ``overlay_manager`` and
``simulation_controller`` as ``None``; they are populated moments later via
the :class:`~shypn.helpers.session_registry.SessionRegistry` proxy writes
inside ``_setup_canvas_manager`` and
:meth:`DocumentPanelSetup._setup_simulation_controller`.  ``__slots__`` type
annotations remain ``Optional`` to reflect this incremental construction
pattern.

The session's :attr:`doc_id` reads the stable monotonic ID stamped on the
drawing_area widget by :func:`shypn.core.document_id.alloc_doc_id` when the
tab was first created (see ``model_canvas_loader.add_document``).

Panel loaders are proxied through ``overlay_manager`` so that
``session.report_panel_loader`` is always in sync with the overlay manager's
own attribute — no extra storage, no staleness.

Lifecycle
---------
* Created in :meth:`ModelCanvasLoader._setup_canvas_manager` as soon as
  the canvas manager and knowledge base are available.
* Registered in :attr:`ModelCanvasLoader.sessions` (a
  :class:`~shypn.helpers.session_registry.SessionRegistry`) immediately.
* ``overlay_manager`` and ``simulation_controller`` are filled in within the
  same call stack, before the session is ever read by external code.
* Destroyed (via :meth:`teardown`) inside ``ModelCanvasLoader.close_tab``,
  which calls ``EventBus.clear_document(self.doc_id)`` ensuring that no
  EventBus subscriptions survive the tab close.
"""

from __future__ import annotations

import logging
from typing import Any, Optional, TYPE_CHECKING

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
        ModelCanvasLoader's SessionRegistry.
    canvas_manager:
        ModelCanvasManager instance for this tab.
    overlay_manager:
        CanvasOverlayManager that owns all panel loaders and the
        SwissKnifePalette for this tab.  May be ``None`` during incremental
        construction (filled in by :meth:`_setup_canvas_manager` immediately
        after this object is registered).
    simulation_controller:
        SimulationController instance for this tab.  May be ``None`` during
        incremental construction (filled in by
        :meth:`DocumentPanelSetup._setup_simulation_controller`).
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
        canvas_manager: "ModelCanvasManager",
        overlay_manager: "Optional[CanvasOverlayManager]" = None,
        simulation_controller: "Optional[SimulationController]" = None,
        knowledge_base: Optional[Any] = None,
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
    # Canvas-manager convenience proxies
    # ------------------------------------------------------------------

    @property
    def filepath(self) -> 'Optional[str]':
        """Absolute path of the saved file, or ``None`` for unsaved documents."""
        return getattr(self.canvas_manager, 'filepath', None)

    @property
    def display_name(self) -> str:
        """User-friendly tab name (filename without path, or default name)."""
        if hasattr(self.canvas_manager, 'get_display_name'):
            return self.canvas_manager.get_display_name()
        return getattr(self.canvas_manager, 'filename', '?')

    @property
    def is_dirty(self) -> bool:
        """``True`` if the document has unsaved changes."""
        return bool(getattr(self.canvas_manager, 'is_dirty', False)
                    or getattr(self.canvas_manager, 'modified', False))

    # ------------------------------------------------------------------
    # Simulation-controller convenience proxies
    # ------------------------------------------------------------------

    @property
    def data_collector(self):
        """The active :class:`DataCollector` for this document."""
        return getattr(self.simulation_controller, 'data_collector', None)

    @property
    def simulation_time(self) -> float:
        """Current simulation time for this document."""
        return getattr(self.simulation_controller, 'time', 0.0)

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

        Called from ``teardown()`` (and therefore from
        ``ModelCanvasLoader.close_tab``) BEFORE the GTK widget is destroyed.
        Individual panel loaders may also call their own ``unsubscribe()``
        methods — ``EventBus.clear_document`` is idempotent.
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

    def teardown(self) -> None:
        """Full resource teardown for this document session.

        Sequence guarantees:

        1. ``close()`` — EventBus.clear_document so no orphaned subscriptions
           survive.
        2. Panel-loader on_tab_closed hooks (topology, others in future).
        3. Report panel data cleared.
        4. ``overlay_manager.cleanup_overlays()`` — destroys GTK overlay
           widgets, palette references, step listeners.

        Called from ``ModelCanvasLoader.close_tab``.  Guards against ``None``
        ``overlay_manager`` and ``simulation_controller`` which can occur when
        tab setup fails very early (Sprint 18 incremental construction).
        """
        # Step 1 — release EventBus subscriptions
        self.close()

        if self.overlay_manager is None:
            logger.debug("DocumentSession.teardown(): overlay_manager is None — skipping panel hooks")
            return

        # Step 2 — panel-specific pre-destroy hooks
        try:
            tpl = getattr(self.overlay_manager, 'topology_panel_loader', None)
            if tpl and hasattr(tpl, 'on_tab_closed'):
                tpl.on_tab_closed(self.drawing_area)
        except Exception:
            logger.debug("topology_panel_loader.on_tab_closed failed", exc_info=True)

        # Step 3 — clear report panel data
        try:
            rpl = getattr(self.overlay_manager, 'report_panel_loader', None)
            if rpl:
                panel = getattr(rpl, 'panel', None)
                if panel and hasattr(panel, 'clear_all'):
                    panel.clear_all()
        except Exception:
            logger.debug("report_panel_loader.panel.clear_all failed", exc_info=True)

        # Step 4 — destroy overlay widgets and palette references
        try:
            self.overlay_manager.cleanup_overlays()
        except Exception:
            logger.debug("overlay_manager.cleanup_overlays failed", exc_info=True)


    def __repr__(self) -> str:
        fname = getattr(self.canvas_manager, 'filename', '?')
        return f"DocumentSession(doc_id={self.doc_id}, filename={fname!r})"
