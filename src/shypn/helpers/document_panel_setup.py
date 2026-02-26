"""Per-document panel and palette setup, extracted from ModelCanvasLoader.

``DocumentPanelSetup`` owns the 8 per-document creation steps that used to
live as private methods on ``ModelCanvasLoader``.  It holds a back-reference
to the loader (``self._L``) so it can read/write loader-level attributes
(containers, panel loaders, etc.) without those attributes being moved.

Usage::

    setup = DocumentPanelSetup(loader, drawing_area, canvas_manager, overlay_manager)
    swissknife_palette, simulation_controller = setup.build(overlay_widget)
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

try:
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk
except Exception:  # pragma: no cover
    Gtk = None  # type: ignore[assignment]

try:
    from shypn.events import EventBus
except ImportError:
    EventBus = None  # type: ignore[assignment]

from shypn.core.document_id import doc_id
from shypn.engine.simulation.controller import SimulationController
from shypn.edit.palette_manager import PaletteManager
from shypn.edit.tools_palette_new import ToolsPalette
from shypn.edit.operations_palette_new import OperationsPalette
from shypn.helpers.swissknife_palette_new import SwissKnifePalette
from shypn.helpers.swissknife_tool_registry import ToolRegistry

if TYPE_CHECKING:
    from shypn.helpers.model_canvas_loader import ModelCanvasLoader

logger = logging.getLogger(__name__)


class DocumentPanelSetup:
    """Builds all per-document UI panels and palettes for one canvas tab.

    This class exists purely to reduce ``ModelCanvasLoader`` size.  It is a
    stateless helper: every public method delegates reads/writes back to the
    loader via ``self._L``.

    Args:
        loader:          The owning ``ModelCanvasLoader`` instance.
        drawing_area:    The ``GtkDrawingArea`` for this document tab.
        canvas_manager:  The ``ModelCanvasManager`` for this document tab.
        overlay_manager: The ``CanvasOverlayManager`` for this document tab.
    """

    __slots__ = ('_L', '_da', '_cm', '_om')

    def __init__(self, loader: "ModelCanvasLoader", drawing_area, canvas_manager, overlay_manager):
        self._L = loader
        self._da = drawing_area
        self._cm = canvas_manager
        self._om = overlay_manager

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def build(self, overlay_widget) -> tuple:
        """Run all 8 per-document setup steps in order.

        Returns:
            ``(swissknife_palette, simulation_controller)`` — both are needed
            by ``ModelCanvasLoader._setup_edit_palettes`` for
            ``DocumentSession`` registration.
        """
        swissknife = self._setup_swissknife_palette(overlay_widget)
        controller = self._setup_simulation_controller(swissknife)
        self._setup_document_report_panel(controller)
        self._setup_document_viability_panel(controller)
        self._setup_document_pathway_panel(controller)
        self._setup_document_analyses_panel()
        self._setup_document_topology_panel()
        palette_manager = self._L.palette_managers[self._da]
        self._wire_legacy_palettes(overlay_widget, palette_manager)
        return swissknife, controller

    # ------------------------------------------------------------------
    # Step 1 – SwissKnifePalette
    # ------------------------------------------------------------------

    def _setup_swissknife_palette(self, overlay_widget):
        """Create PaletteManager and SwissKnifePalette for this canvas.

        Returns the ``SwissKnifePalette`` instance (needed by step 2).
        """
        L, da, cm = self._L, self._da, self._cm

        # Create palette manager (kept for backward compatibility with old code)
        palette_manager = PaletteManager(overlay_widget, reference_widget=None)
        L.palette_managers[da] = palette_manager

        # Create tool registry and SwissKnifePalette
        tool_registry = ToolRegistry()
        swissknife_palette = SwissKnifePalette(
            mode='edit',
            model=cm,
            tool_registry=tool_registry
        )

        # Position widget
        swissknife_widget = swissknife_palette.get_widget()
        swissknife_widget.set_halign(Gtk.Align.CENTER)
        swissknife_widget.set_valign(Gtk.Align.END)
        swissknife_widget.set_margin_bottom(20)
        swissknife_widget.set_hexpand(False)
        swissknife_widget.set_vexpand(False)
        overlay_widget.add_overlay(swissknife_widget)

        # Wire signals
        swissknife_palette.connect('tool-activated', L._on_swissknife_tool_activated, cm, da)
        swissknife_palette.connect('mode-change-requested', L._on_swissknife_mode_change_requested, cm, da)
        swissknife_palette.connect('simulation-step-executed', L._on_simulation_step, da)
        swissknife_palette.connect('simulation-reset-executed', L._on_simulation_reset, da)
        swissknife_palette.connect('simulation-settings-changed', L._on_simulation_settings_changed, da)
        swissknife_palette.connect('float-toggled', L._on_swissknife_float_toggled, swissknife_widget, da)
        swissknife_palette.connect('position-changed', L._on_swissknife_position_changed, swissknife_widget, da)

        return swissknife_palette

    # ------------------------------------------------------------------
    # Step 2 – SimulationController
    # ------------------------------------------------------------------

    def _setup_simulation_controller(self, swissknife_palette):
        """Create ``SimulationController`` and register the canvas with the lifecycle adapter.

        Returns the ``SimulationController`` (needed by panel setup steps).
        """
        L, da, cm = self._L, self._da, self._cm

        simulation_controller = SimulationController(cm, document_id=doc_id(da))
        # Store drawing_area reference so Report Panel can find its document
        simulation_controller._drawing_area = da

        # Wire data_collector change callback so analyses panel updates on reset()
        def on_data_collector_changed(new_data_collector):
            if hasattr(L.overlay_managers[da], 'analyses_panel_loader'):
                analyses_loader = L.overlay_managers[da].analyses_panel_loader
                if analyses_loader and hasattr(analyses_loader, 'set_data_collector'):
                    analyses_loader.set_data_collector(new_data_collector)

        simulation_controller.data_collector_listeners.append(on_data_collector_changed)
        L.simulation_controllers[da] = simulation_controller

        # Store in overlay_manager for arc property dialog access
        if da in L.overlay_managers:
            L.overlay_managers[da].simulation_controller = simulation_controller

        # Notify existing report panel of controller replacement via EventBus (document-scoped)
        EventBus.emit('simulation.controller_ready',
                      {'controller': simulation_controller},
                      document_id=doc_id(da))

        # Register with lifecycle adapter
        if L.lifecycle_adapter:
            try:
                L.lifecycle_adapter.register_canvas(
                    da,
                    cm,
                    simulation_controller,
                    swissknife_palette
                )
            except Exception as e:
                L.logger.debug(f"Failed to register canvas with lifecycle adapter: {e}")

        # Store palette/controller references in overlay_manager
        if da not in L.overlay_managers:
            L.overlay_managers[da] = type('obj', (object,), {})()
        L.overlay_managers[da].swissknife_palette = swissknife_palette
        L.overlay_managers[da].simulation_controller = simulation_controller

        # Update existing analyses panel data_collector if it already exists
        if hasattr(L.overlay_managers[da], 'analyses_panel_loader'):
            analyses_loader = L.overlay_managers[da].analyses_panel_loader
            if analyses_loader and hasattr(analyses_loader, 'set_data_collector'):
                analyses_loader.set_data_collector(simulation_controller.data_collector)

        return simulation_controller

    # ------------------------------------------------------------------
    # Step 3 – Report Panel
    # ------------------------------------------------------------------

    def _setup_document_report_panel(self, simulation_controller):
        """Create (or rewire) the per-document Report Panel."""
        L, da = self._L, self._da

        # Create per-document report data container
        from shypn.ui.panels.report.document_report_data import DocumentReportData
        L.overlay_managers[da].report_data = DocumentReportData(drawing_area=da)

        if not hasattr(L.overlay_managers[da], 'report_panel_loader'):
            from shypn.helpers.report_panel_loader import ReportPanelLoader

            report_panel_loader = ReportPanelLoader(
                project=None,
                model_canvas_loader=L,
                document_id=doc_id(da),
                drawing_area=da
            )
            report_panel_loader.load()

            # Wire host callbacks
            if hasattr(L, 'on_report_float') and hasattr(L, 'on_report_attach'):
                report_panel_loader.on_float_callback = L.on_report_float
                report_panel_loader.on_attach_callback = L.on_report_attach
            if hasattr(L, 'main_window') and L.main_window:
                report_panel_loader.parent_window = L.main_window
            if hasattr(L, 'report_panel_container') and L.report_panel_container is not None:
                report_panel_loader.parent_container = L.report_panel_container
                report_panel_loader.is_hanged = True
            if hasattr(L, 'left_dock_stack') and L.left_dock_stack is not None:
                report_panel_loader._stack = L.left_dock_stack
                report_panel_loader._stack_panel_name = 'report'

            if hasattr(report_panel_loader, 'panel') and report_panel_loader.panel:
                report_panel_loader.panel.set_model_canvas(self._cm)

                model_manager = L.overlay_managers[da].canvas_manager
                if model_manager:
                    report_panel_loader.panel.set_model_canvas(model_manager)

                # Wire cross-panel references
                overlay_manager = L.overlay_managers[da]
                if hasattr(overlay_manager, 'pathway_panel_loader'):
                    pathway_loader = overlay_manager.pathway_panel_loader
                    if pathway_loader and hasattr(pathway_loader, 'panel') and pathway_loader.panel:
                        report_panel_loader.panel.set_pathway_operations_panel(pathway_loader.panel)

                if hasattr(overlay_manager, 'analyses_panel_loader'):
                    analyses_loader = overlay_manager.analyses_panel_loader
                    if analyses_loader and hasattr(analyses_loader, 'panel') and analyses_loader.panel:
                        report_panel_loader.panel.set_dynamic_analyses_panel(analyses_loader.panel)

                if hasattr(overlay_manager, 'topology_panel_loader'):
                    topology_loader = overlay_manager.topology_panel_loader
                    if topology_loader and hasattr(topology_loader, 'panel') and topology_loader.panel:
                        report_panel_loader.panel.set_topology_panel(topology_loader.panel)
                        report_panel_loader.panel.refresh_all()

                # Notify the new panel of its simulation controller via EventBus
                EventBus.emit('simulation.controller_ready',
                              {'controller': simulation_controller},
                              document_id=doc_id(da))

            L.overlay_managers[da].report_panel_loader = report_panel_loader
        else:
            # Rewire existing panel to new controller via EventBus
            report_panel_loader = L.overlay_managers[da].report_panel_loader
            if report_panel_loader and hasattr(report_panel_loader, 'panel') and report_panel_loader.panel:
                model_manager = L.overlay_managers[da].canvas_manager
                if model_manager:
                    report_panel_loader.panel.set_model_canvas(model_manager)
                EventBus.emit('simulation.controller_ready',
                              {'controller': simulation_controller},
                              document_id=doc_id(da))

    # ------------------------------------------------------------------
    # Step 4 – Viability Panel
    # ------------------------------------------------------------------

    def _setup_document_viability_panel(self, simulation_controller):
        """Create the per-document Viability Panel."""
        L, da = self._L, self._da

        if hasattr(L.overlay_managers[da], 'viability_panel_loader'):
            return

        from shypn.helpers.viability_panel_loader import ViabilityPanelLoader

        viability_panel_loader = ViabilityPanelLoader(
            model=None,
            document_id=doc_id(da),
            drawing_area=da
        )
        viability_panel_loader.set_model_canvas_loader(L)

        if hasattr(L, 'viability_panel_container') and L.viability_panel_container is not None:
            viability_panel_loader.parent_container = L.viability_panel_container
            viability_panel_loader.is_hanged = True
        if hasattr(L, 'left_dock_stack') and L.left_dock_stack is not None:
            viability_panel_loader._stack = L.left_dock_stack
            viability_panel_loader._stack_panel_name = 'viability'
        if hasattr(L, 'on_viability_float') and callable(getattr(L, 'on_viability_float')):
            viability_panel_loader.on_float_callback = L.on_viability_float
        if hasattr(L, 'on_viability_attach') and callable(getattr(L, 'on_viability_attach')):
            viability_panel_loader.on_attach_callback = L.on_viability_attach
        if hasattr(L, 'main_window') and L.main_window:
            viability_panel_loader.parent_window = L.main_window

        L.overlay_managers[da].viability_panel_loader = viability_panel_loader
        viability_panel_loader.initialize_eventbus()

        if viability_panel_loader.panel and L.viability_panel_container:
            parent = viability_panel_loader.widget.get_parent()
            if parent:
                parent.remove(viability_panel_loader.widget)
            L.viability_panel_container.pack_start(viability_panel_loader.widget, True, True, 0)
            viability_panel_loader.widget.show_all()

            viability_panel = viability_panel_loader.panel
            viability_panel.set_model_canvas(L)

            # Wire simulation complete callback (avoid wrapping if already viability callback)
            if hasattr(viability_panel, 'on_simulation_complete'):
                existing_callback = getattr(simulation_controller, 'on_simulation_complete', None)
                is_viability_callback = (
                    existing_callback and
                    hasattr(existing_callback, '__self__') and
                    existing_callback.__self__.__class__.__name__ == 'ViabilityPanel'
                )
                if not is_viability_callback:
                    def combined_callback():
                        if existing_callback and callable(existing_callback):
                            existing_callback()
                        viability_panel.on_simulation_complete()
                    simulation_controller.on_simulation_complete = combined_callback

            # Wire topology panel if already present
            overlay_manager = L.overlay_managers[da]
            if hasattr(overlay_manager, 'topology_panel_loader'):
                topology_loader = overlay_manager.topology_panel_loader
                if topology_loader and hasattr(topology_loader, 'panel') and topology_loader.panel:
                    viability_panel.set_topology_panel(topology_loader.panel)

    # ------------------------------------------------------------------
    # Step 5 – Pathway Panel
    # ------------------------------------------------------------------

    def _setup_document_pathway_panel(self, simulation_controller):
        """Create the per-document Pathway Operations Panel."""
        L, da, cm = self._L, self._da, self._cm

        if hasattr(L.overlay_managers[da], 'pathway_panel_loader'):
            return

        from shypn.helpers.pathway_panel_loader import PathwayPanelLoader

        canvas_manager = L.overlay_managers[da].canvas_manager
        pathway_panel_loader = PathwayPanelLoader(
            model=canvas_manager,
            parent_window=getattr(L, 'main_window', None),
            workspace_settings=L.workspace_settings,
            project=getattr(L, 'project', None),
            canvas_loader=L,
            document_id=doc_id(da),
            drawing_area=da
        )
        pathway_panel_loader.initialize()

        if hasattr(L, 'pathways_panel_container') and L.pathways_panel_container is not None:
            pathway_panel_loader.parent_container = L.pathways_panel_container
        if hasattr(L, 'left_dock_stack') and L.left_dock_stack is not None:
            pathway_panel_loader._stack = L.left_dock_stack
            pathway_panel_loader._stack_panel_name = 'pathways'

        L.overlay_managers[da].pathway_panel_loader = pathway_panel_loader

        if pathway_panel_loader.panel and L.pathways_panel_container:
            parent = pathway_panel_loader.widget.get_parent()
            if parent:
                parent.remove(pathway_panel_loader.widget)
            L.pathways_panel_container.pack_start(pathway_panel_loader.widget, True, True, 0)
            pathway_panel_loader.widget.show_all()

            if hasattr(pathway_panel_loader.panel, 'thermodynamics_category'):
                pathway_panel_loader.panel.thermodynamics_category.set_simulation_controller(simulation_controller)

    # ------------------------------------------------------------------
    # Step 6 – Analyses Panel + ContextMenuHandler
    # ------------------------------------------------------------------

    def _setup_document_analyses_panel(self):
        """Create the per-document Dynamic Analyses Panel and ContextMenuHandler."""
        L, da = self._L, self._da
        overlay_manager = self._om

        if hasattr(L.overlay_managers[da], 'analyses_panel_loader'):
            return

        analyses_panel_loader = None
        try:
            from shypn.helpers.analyses_panel_loader import AnalysesPanelLoader

            canvas_manager = L.overlay_managers[da].canvas_manager
            simulation_controller = L.overlay_managers[da].simulation_controller
            data_collector = getattr(simulation_controller, 'data_collector', None)

            analyses_panel_loader = AnalysesPanelLoader(
                model=canvas_manager,
                parent_window=getattr(L, 'main_window', None),
                data_collector=data_collector,
                document_id=doc_id(da),
                drawing_area=da
            )
            analyses_panel_loader.initialize()
            analyses_panel_loader.refresh()
        except Exception as e:
            import traceback
            L.logger.error(f"Failed to create analyses panel: {e}")
            traceback.print_exc()

        if analyses_panel_loader:
            if hasattr(L, 'analyses_panel_container') and L.analyses_panel_container is not None:
                analyses_panel_loader.parent_container = L.analyses_panel_container
            if hasattr(L, 'left_dock_stack') and L.left_dock_stack is not None:
                analyses_panel_loader._stack = L.left_dock_stack
                analyses_panel_loader._stack_panel_name = 'analyses'
            L.overlay_managers[da].analyses_panel_loader = analyses_panel_loader

            if analyses_panel_loader.panel and L.analyses_panel_container:
                parent = analyses_panel_loader.widget.get_parent()
                if parent:
                    parent.remove(analyses_panel_loader.widget)
                L.analyses_panel_container.pack_start(analyses_panel_loader.widget, True, True, 0)
        else:
            L.overlay_managers[da].analyses_panel_loader = None

        # Always create context menu handler — needed even if analyses panel failed
        if hasattr(L, 'model_canvas_loader') or hasattr(L, 'get_current_model'):
            from shypn.analyses import ContextMenuHandler

            canvas_manager = L.overlay_managers[da].canvas_manager
            place_panel = analyses_panel_loader.place_panel if analyses_panel_loader else None
            transition_panel = analyses_panel_loader.transition_panel if analyses_panel_loader else None
            plotting_panel = analyses_panel_loader.plotting_panel if analyses_panel_loader else None

            L.logger.debug(
                "[ANALYSES_INIT] Creating context menu handler: place_panel=%s, "
                "transition_panel=%s, plotting_panel=%s",
                place_panel is not None, transition_panel is not None, plotting_panel is not None
            )

            context_menu_handler = ContextMenuHandler(
                place_panel=place_panel,
                transition_panel=transition_panel,
                model=canvas_manager,
                diagnostics_panel=plotting_panel,
                model_canvas_loader=L
            )
            if analyses_panel_loader:
                analyses_panel_loader.set_context_menu_handler(context_menu_handler)

            overlay_manager.context_menu_handler = context_menu_handler
            L.set_context_menu_handler(context_menu_handler)

            if analyses_panel_loader:
                analyses_panel_loader.widget.show_all()

    # ------------------------------------------------------------------
    # Step 7 – Topology Panel
    # ------------------------------------------------------------------

    def _setup_document_topology_panel(self):
        """Create the per-document Topology Panel."""
        L, da = self._L, self._da

        if hasattr(L.overlay_managers[da], 'topology_panel_loader'):
            return

        from shypn.helpers.topology_panel_loader import TopologyPanelLoader

        canvas_manager = L.overlay_managers[da].canvas_manager
        topology_panel_loader = TopologyPanelLoader(
            model=canvas_manager,
            parent_window=getattr(L, 'main_window', None),
            document_id=doc_id(da),
            drawing_area=da
        )
        topology_panel_loader.initialize()
        topology_panel_loader.set_model_canvas_loader(L)

        if hasattr(L, 'topology_panel_container'):
            topology_panel_loader.parent_container = L.topology_panel_container
        if hasattr(L, 'left_dock_stack'):
            topology_panel_loader._stack = L.left_dock_stack
            topology_panel_loader._stack_panel_name = 'topology'
        if hasattr(L, 'topology_float_callback'):
            topology_panel_loader.on_float_callback = L.topology_float_callback
        if hasattr(L, 'topology_attach_callback'):
            topology_panel_loader.on_attach_callback = L.topology_attach_callback

        L.overlay_managers[da].topology_panel_loader = topology_panel_loader

        if topology_panel_loader.panel and L.topology_panel_container:
            parent = topology_panel_loader.widget.get_parent()
            if parent:
                parent.remove(topology_panel_loader.widget)
            L.topology_panel_container.pack_start(topology_panel_loader.widget, True, True, 0)
            topology_panel_loader.widget.show_all()

    # ------------------------------------------------------------------
    # Step 8 – Legacy palettes + final data_collector wiring
    # ------------------------------------------------------------------

    def _wire_legacy_palettes(self, overlay_widget, palette_manager):
        """Create hidden legacy ToolsPalette/OperationsPalette and wire final data_collector.

        The legacy palettes are kept hidden for backward compatibility during transition
        to SwissKnifePalette. The data_collector is wired here after all palettes exist.
        """
        L, da, cm = self._L, self._da, self._cm

        # ── Legacy palette objects (hidden, kept for backward compat) ──────────────
        tools_palette = ToolsPalette()
        palette_manager.register_palette(
            tools_palette,
            position=(Gtk.Align.CENTER, Gtk.Align.END)
        )
        tools_revealer = tools_palette.get_widget()
        tools_revealer.set_margin_bottom(68)
        tools_revealer.set_margin_end(194 + 80)
        tools_revealer.set_hexpand(False)
        tools_revealer.hide()

        operations_palette = OperationsPalette()
        palette_manager.register_palette(
            operations_palette,
            position=(Gtk.Align.CENTER, Gtk.Align.END)
        )
        operations_revealer = operations_palette.get_widget()
        operations_revealer.set_margin_bottom(68)
        operations_revealer.set_margin_start(148 + 80)
        operations_revealer.set_hexpand(False)
        operations_revealer.hide()

        tools_palette.connect('tool-selected', L._on_palette_tool_selected, cm, da)
        operations_palette.connect('operation-triggered', L._on_palette_operation_triggered, cm, da)

        # Wire undo/redo button state to legacy operations palette
        if hasattr(cm, 'undo_manager'):
            def update_undo_redo_buttons(can_undo, can_redo):
                operations_palette.update_undo_redo_state(can_undo, can_redo)
            cm.undo_manager.set_state_changed_callback(update_undo_redo_buttons)
            update_undo_redo_buttons(
                cm.undo_manager.can_undo(),
                cm.undo_manager.can_redo()
            )

        # ── Show overlay; hide simulate palette (shown only in simulate mode) ──────
        overlay_widget.show_all()
        if da in L.overlay_managers:
            overlay_mgr = L.overlay_managers[da]
            if overlay_mgr.simulate_palette:
                sim_widget = overlay_mgr.simulate_palette.get_widget()
                if sim_widget:
                    sim_widget.hide()

        # ── Wire initial data_collector to right panel ─────────────────────────────
        if L.right_panel_loader and da in L.overlay_managers:
            overlay_mgr = L.overlay_managers[da]
            if hasattr(overlay_mgr, 'swissknife_palette'):
                swissknife = overlay_mgr.swissknife_palette
                if hasattr(swissknife, 'widget_palette_instances'):
                    simulate_tools_palette = swissknife.widget_palette_instances.get('simulate')
                    if simulate_tools_palette and hasattr(simulate_tools_palette, 'data_collector'):
                        data_collector = simulate_tools_palette.data_collector
                        L.right_panel_loader.set_data_collector(data_collector)
