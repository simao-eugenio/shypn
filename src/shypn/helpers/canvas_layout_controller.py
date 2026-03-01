"""Canvas Layout Sub-Controller.

Handles graph-layout application for the Petri Net drawing canvas.
This includes auto, hierarchical, force-directed, circular and orthogonal
layouts via the ``shypn.edit.graph_layout`` engine.

Extracted from ``ModelCanvasLoader`` to keep layout concerns isolated.
"""
import logging


class CanvasLayoutController:
    """Sub-controller responsible for applying graph layouts to a canvas document.

    Args:
        overlay_managers:  The shared ``overlay_managers`` dict from
                           ``ModelCanvasLoader`` (passed *by reference*).
        get_sbml_panel:    Zero-arg callable that returns the current SBML
                           panel (or ``None``).  Used as a fallback for layout
                           parameters when the SwissKnife panel has none.
    """

    def __init__(self, overlay_managers: dict, get_sbml_panel=None):
        self.logger = logging.getLogger(__name__)
        self._overlay_managers = overlay_managers
        self._get_sbml_panel = get_sbml_panel or (lambda: None)

    # ------------------------------------------------------------------
    # Layout entry-points
    # ------------------------------------------------------------------

    def _on_layout_auto_clicked(self, menu, drawing_area, manager):
        """Apply automatic layout (best algorithm for graph topology)."""
        try:
            from shypn.edit.graph_layout import LayoutEngine

            if not manager.places and not manager.transitions:
                self._show_layout_message("No objects to layout", drawing_area)
                return

            all_objs = list(manager.places) + list(manager.transitions)
            if all_objs:
                center_x = sum(obj.x for obj in all_objs) / len(all_objs)
                center_y = sum(obj.y for obj in all_objs) / len(all_objs)
            else:
                center_x = manager.canvas_width / 2
                center_y = manager.canvas_height / 2

            layout_params = {}
            try:
                if drawing_area in self._overlay_managers:
                    overlay_mgr = self._overlay_managers.get(drawing_area)
                    if overlay_mgr and hasattr(overlay_mgr, 'swissknife_palette'):
                        swissknife = overlay_mgr.swissknife_palette
                        if swissknife and hasattr(swissknife, 'layout_settings_loader'):
                            settings_loader = swissknife.layout_settings_loader
                            if settings_loader and hasattr(settings_loader, 'get_settings'):
                                all_settings = settings_loader.get_settings()
                                if all_settings:
                                    layout_params = {
                                        'layer_spacing': all_settings.get('layer_spacing', 150),
                                        'node_spacing':  all_settings.get('node_spacing', 100),
                                        'iterations':    all_settings.get('iterations', 500),
                                        'k_multiplier':  all_settings.get('k_multiplier', 1.5),
                                        'scale':         all_settings.get('scale', 2000.0),
                                    }
            except Exception as e:
                self.logger.warning("Could not get layout parameters: %s", e, exc_info=True)
                layout_params = {}

            engine = LayoutEngine(manager)
            result = engine.apply_layout('auto', **layout_params)

            all_objs = list(manager.places) + list(manager.transitions)
            if all_objs:
                new_center_x = sum(obj.x for obj in all_objs) / len(all_objs)
                new_center_y = sum(obj.y for obj in all_objs) / len(all_objs)
                offset_x = center_x - new_center_x
                offset_y = center_y - new_center_y
                for obj in all_objs:
                    obj.x += offset_x
                    obj.y += offset_y

            message = (
                f"Applied {result['algorithm']} layout\n"
                f"Moved {result['nodes_moved']} objects\n"
                f"Reason: {result['reason']}"
            )
            if layout_params and result.get('parameters'):
                message += f"\nParameters: {result['parameters']}"
            self._show_layout_message(message, drawing_area)
            drawing_area.queue_draw()

        except Exception as e:
            self.logger.error("Auto layout error: %s", e, exc_info=True)
            self._show_layout_message(f"Layout error: {str(e)}", drawing_area)

    def _on_layout_hierarchical_clicked(self, menu, drawing_area, manager):
        """Apply hierarchical (Sugiyama) layout."""
        self._apply_specific_layout(manager, drawing_area, 'hierarchical', 'Hierarchical (Sugiyama)')

    def _on_layout_force_clicked(self, menu, drawing_area, manager):
        """Apply force-directed (Fruchterman-Reingold) layout."""
        self._apply_specific_layout(manager, drawing_area, 'force_directed', 'Force-Directed')

    def _on_layout_circular_clicked(self, menu, drawing_area, manager):
        """Apply circular layout."""
        self._apply_specific_layout(manager, drawing_area, 'circular', 'Circular')

    def _on_layout_orthogonal_clicked(self, menu, drawing_area, manager):
        """Apply orthogonal (grid-aligned) layout."""
        self._apply_specific_layout(manager, drawing_area, 'orthogonal', 'Orthogonal')

    def _apply_specific_layout(self, manager, drawing_area, algorithm, algorithm_name):
        """Apply a specific layout algorithm.

        Args:
            manager:        ModelCanvasManager instance.
            drawing_area:   GtkDrawingArea widget.
            algorithm:      Algorithm name ('hierarchical', 'force_directed', …).
            algorithm_name: Human-readable name for messages.
        """
        try:
            from shypn.edit.graph_layout import LayoutEngine

            if not manager.places and not manager.transitions:
                self._show_layout_message("No objects to layout", drawing_area)
                return

            all_objs = list(manager.places) + list(manager.transitions)
            if all_objs:
                center_x = sum(obj.x for obj in all_objs) / len(all_objs)
                center_y = sum(obj.y for obj in all_objs) / len(all_objs)
            else:
                center_x = manager.canvas_width / 2
                center_y = manager.canvas_height / 2

            layout_params = {}
            try:
                if drawing_area in self._overlay_managers:
                    overlay_mgr = self._overlay_managers.get(drawing_area)
                    if overlay_mgr and hasattr(overlay_mgr, 'swissknife_palette'):
                        swissknife = overlay_mgr.swissknife_palette
                        if swissknife and hasattr(swissknife, 'layout_settings_loader'):
                            settings_loader = swissknife.layout_settings_loader
                            if settings_loader and hasattr(settings_loader, 'get_settings'):
                                all_settings = settings_loader.get_settings()
                                if all_settings:
                                    if algorithm == 'hierarchical':
                                        layout_params = {
                                            'layer_spacing': all_settings.get('layer_spacing', 150),
                                            'node_spacing':  all_settings.get('node_spacing', 100),
                                        }
                                    elif algorithm == 'force_directed':
                                        layout_params = {
                                            'iterations':   all_settings.get('iterations', 500),
                                            'k_multiplier': all_settings.get('k_multiplier', 1.5),
                                            'scale':        all_settings.get('scale', 2000.0),
                                        }

                sbml_panel = self._get_sbml_panel()
                if not layout_params and sbml_panel is not None:
                    layout_params = sbml_panel.get_layout_parameters_for_algorithm(algorithm) or {}
            except Exception as e:
                self.logger.warning("Could not get layout parameters: %s", e, exc_info=True)
                layout_params = {}

            engine = LayoutEngine(manager)
            result = engine.apply_layout(algorithm, **layout_params)

            all_objs = list(manager.places) + list(manager.transitions)
            if all_objs:
                new_center_x = sum(obj.x for obj in all_objs) / len(all_objs)
                new_center_y = sum(obj.y for obj in all_objs) / len(all_objs)
                offset_x = center_x - new_center_x
                offset_y = center_y - new_center_y
                for obj in all_objs:
                    obj.x += offset_x
                    obj.y += offset_y

            message = f"Applied {algorithm_name} layout\nMoved {result['nodes_moved']} objects"
            if layout_params:
                message += f"\nParameters: {layout_params}"
            self._show_layout_message(message, drawing_area)
            drawing_area.queue_draw()

        except Exception as e:
            self.logger.error("Layout error (%s): %s", algorithm, e, exc_info=True)
            self._show_layout_message(f"Layout error: {str(e)}", drawing_area)

    def _show_layout_message(self, message, drawing_area):
        """Show a temporary layout status message.

        Currently a stub — can be wired to a status bar in future.
        """
        pass
