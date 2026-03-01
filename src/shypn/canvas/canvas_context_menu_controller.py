"""Concrete canvas context-menu controller.

Sprint 22 — Phase 7 OOP refactor.
Extracted from :class:`~shypn.helpers.model_canvas_loader.ModelCanvasLoader`.

All Petri-net object editing callbacks (on_object_properties, on_arc_convert_*,
on_transition_type_change, …) still live in MCL and are reached via the
*loader* back-reference so that the editing logic stays close to its data.
"""

from __future__ import annotations

__all__ = ["CanvasContextMenuController"]

import logging
from typing import Any

from shypn.canvas.abstract_context_menu_controller import AbstractContextMenuController

logger = logging.getLogger(__name__)

try:
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk
except Exception:  # pragma: no cover
    Gtk = None  # type: ignore[assignment]

try:
    from shypn.netobjs import Place, Transition, Arc
except Exception:  # pragma: no cover
    Place = Transition = Arc = None  # type: ignore[assignment]


class CanvasContextMenuController(AbstractContextMenuController):
    """Builds, shows and manages all canvas / object context menus.

    Args:
        loader: The :class:`~shypn.helpers.model_canvas_loader.ModelCanvasLoader`
            that owns this controller.  Used to reach object-editing callbacks
            and shared state such as ``persistency`` and ``context_menu_handler``.
    """

    __slots__ = ("_loader", "_canvas_context_menus", "_active_canvas_menu")

    def __init__(self, loader: Any) -> None:
        self._loader = loader
        self._canvas_context_menus: dict = {}
        self._active_canvas_menu: Any = None

    # ------------------------------------------------------------------
    # AbstractContextMenuController interface
    # ------------------------------------------------------------------

    def setup_for_drawing_area(self, drawing_area: Any, manager: Any) -> None:
        """Build and register the Gtk.Menu for *drawing_area*.  Sprint 22."""
        if Gtk is None:
            return
        menu = Gtk.Menu()
        menu_items = [
            ('Reset Zoom (100%)', lambda: self._on_reset_zoom_clicked(menu, drawing_area, manager)),
            ('Zoom In',           lambda: self._on_zoom_in_clicked(menu, drawing_area, manager)),
            ('Zoom Out',          lambda: self._on_zoom_out_clicked(menu, drawing_area, manager)),
            ('Fit to Window',     lambda: self._on_fit_to_window_clicked(menu, drawing_area, manager)),
            None,
            ('Rotate 90° CW',     lambda: self._on_rotate_90_cw_clicked(menu, drawing_area, manager)),
            ('Rotate 90° CCW',    lambda: self._on_rotate_90_ccw_clicked(menu, drawing_area, manager)),
            ('Rotate 180°',       lambda: self._on_rotate_180_clicked(menu, drawing_area, manager)),
            ('Reset Rotation',    lambda: self._on_reset_rotation_clicked(menu, drawing_area, manager)),
            None,
            ('Grid: Line Style',  lambda: self._on_grid_line_clicked(menu, drawing_area, manager)),
            ('Grid: Dot Style',   lambda: self._on_grid_dot_clicked(menu, drawing_area, manager)),
            ('Grid: Cross Style', lambda: self._on_grid_cross_clicked(menu, drawing_area, manager)),
            None,
            ('Center View',       lambda: self._on_center_view_clicked(menu, drawing_area, manager)),
            ('Clear Canvas',      lambda: self._on_clear_canvas_clicked(menu, drawing_area, manager)),
            None,
            ('🎯 Create Center Marker', lambda: self._on_create_center_marker_clicked(menu, drawing_area, manager)),
        ]
        for item_data in menu_items:
            if item_data is None:
                menu_item = Gtk.SeparatorMenuItem()
            else:
                label, cb = item_data
                menu_item = Gtk.MenuItem(label=label)
                menu_item.connect('activate', lambda _w, _cb=cb: _cb())
            menu_item.show()
            menu.append(menu_item)
        self._active_canvas_menu = menu
        self._canvas_context_menus[drawing_area] = menu

    def show_canvas_menu(self, x: float, y: float, drawing_area: Any) -> None:
        """Pop up the canvas-level menu (Wayland-safe).  Sprint 22."""
        menu = self._canvas_context_menus.get(drawing_area)
        if menu:
            menu.popup_at_pointer(None)

    def show_object_menu(
        self,
        x: float,
        y: float,
        drawing_area: Any,
        manager: Any,
        obj: Any,
    ) -> None:
        """Build and pop up the per-object context menu.  Sprint 22."""
        if Gtk is None or Place is None:
            return
        _loader = self._loader
        menu = Gtk.Menu()
        _TYPE_LABELS = {Place: 'Place', Transition: 'Transition', Arc: 'Arc'}
        obj_type = next(
            (lbl for cls, lbl in _TYPE_LABELS.items() if isinstance(obj, cls)),
            'Object',
        )
        title_label = (
            f'{obj_type}: {obj.id} - {obj.name}'
            if isinstance(obj, Arc)
            else f'{obj_type}: {obj.name}'
        )
        title_item = Gtk.MenuItem(label=title_label)
        title_item.set_sensitive(False)
        title_item.show()
        menu.append(title_item)
        sep = Gtk.SeparatorMenuItem()
        sep.show()
        menu.append(sep)

        is_parallel_arc = False
        if isinstance(obj, Arc):
            parallels = manager.detect_parallel_arcs(obj)
            is_parallel_arc = len(parallels) > 0

        if is_parallel_arc:
            menu_items: list = [
                ('Edit Properties...', lambda: _loader._on_object_properties(obj, manager, drawing_area)),
                None,
                ('Delete', lambda: _loader._on_object_delete(obj, manager, drawing_area)),
            ]
        else:
            menu_items = [
                ('Edit Properties...', lambda: _loader._on_object_properties(obj, manager, drawing_area)),
                ('Edit Mode (Double-click)', lambda: _loader._on_object_edit_mode(obj, manager, drawing_area)),
                None,
                ('Delete', lambda: _loader._on_object_delete(obj, manager, drawing_area)),
            ]

        for obj_cls, builder in [
            (Place,      self._add_place_context_items),
            (Transition, self._add_transition_context_items),
            (Arc,        self._add_arc_context_items),
        ]:
            if isinstance(obj, obj_cls):
                builder(obj, menu_items, manager, drawing_area)
                break

        for item_data in menu_items:
            if item_data is None:
                mi = Gtk.SeparatorMenuItem()
            elif item_data[0] == '__SUBMENU__':
                mi = item_data[1]
            else:
                label, cb = item_data
                mi = Gtk.MenuItem(label=label)
                mi.connect('activate', lambda _w, _cb=cb: _cb())
                mi.show()
            menu.append(mi)

        if _loader.context_menu_handler:
            _loader.context_menu_handler.add_analysis_menu_items(menu, obj)

        if isinstance(obj, (Place, Transition)):
            sep2 = Gtk.SeparatorMenuItem()
            sep2.show()
            menu.append(sep2)
            is_recorded = False
            if hasattr(manager, 'simulation_settings'):
                settings = manager.simulation_settings
                if settings and hasattr(settings, 'is_object_recorded'):
                    is_recorded = settings.is_object_recorded(obj.id)
            record_label = (
                '✓ Mark for Recording (Batch Mode)'
                if is_recorded
                else '📊 Mark for Recording (Batch Mode)'
            )
            record_item = Gtk.MenuItem(label=record_label)
            record_item.connect(
                'activate',
                lambda _w: _loader._on_toggle_recording(obj, manager, drawing_area),
            )
            record_item.show()
            menu.append(record_item)

        self._active_canvas_menu = menu
        # Wayland-safe: no attach_to_widget(); popup_at_pointer() handles parent
        menu.popup_at_pointer(None)

    def popdown_canvas_menu(self) -> bool:
        """Dismiss the active canvas menu.  Sprint 22."""
        if self._active_canvas_menu and isinstance(self._active_canvas_menu, Gtk.Menu):
            self._active_canvas_menu.popdown()
            return True
        return False

    # ------------------------------------------------------------------
    # Type-specific menu-item builders
    # ------------------------------------------------------------------

    def _add_place_context_items(
        self, obj: Any, menu_items: list, manager: Any, drawing_area: Any
    ) -> None:
        """Append Place-specific items."""
        _loader = self._loader
        is_signal = getattr(obj, 'is_signal_place', False)
        if is_signal:
            menu_items.insert(
                2,
                (
                    'Remove Signal Designation',
                    lambda: _loader._on_remove_signal_designation(obj, manager, drawing_area),
                ),
            )
        else:
            signal_submenu_item = Gtk.MenuItem(label='Convert to Signal Place ►')
            signal_submenu = Gtk.Menu()
            for type_value, type_label in [
                ('energy',     'Ψₑ - Energy/Metabolic State'),
                ('regulatory', 'Ψᵣ - Regulatory/Gene Expression'),
                ('quorum',     'Ψq - Quorum/Cell Communication'),
                ('spatial',    'Ψₛ - Spatial/Compartment Sensing'),
            ]:
                signal_item = Gtk.MenuItem(label=type_label)
                signal_item.connect(
                    'activate',
                    lambda _w, t=type_value: _loader._on_convert_to_signal(obj, t, manager, drawing_area),
                )
                signal_item.show()
                signal_submenu.append(signal_item)
            signal_submenu_item.set_submenu(signal_submenu)
            signal_submenu_item.show()
            menu_items.insert(2, ('__SUBMENU__', signal_submenu_item))
        menu_items.insert(3, None)

    def _add_transition_context_items(
        self, obj: Any, menu_items: list, manager: Any, drawing_area: Any
    ) -> None:
        """Append Transition-specific items."""
        _loader = self._loader
        type_submenu_item = Gtk.MenuItem(label='Change Type ►')
        type_submenu = Gtk.Menu()
        current_type = getattr(obj, 'transition_type', 'continuous')
        for type_value, type_label in [
            ('immediate',  'Immediate (zero delay)'),
            ('timed',      'Timed (TPN)'),
            ('stochastic', 'Stochastic (GSPN)'),
            ('continuous', 'Continuous (SHPN)'),
        ]:
            label = (
                f'✓ {type_label}' if type_value == current_type else f'   {type_label}'
            )
            ti = Gtk.MenuItem(label=label)
            ti.connect(
                'activate',
                lambda _w, t=type_value: _loader._on_transition_type_change(
                    obj, t, manager, drawing_area
                ),
            )
            ti.show()
            type_submenu.append(ti)
        type_submenu_item.set_submenu(type_submenu)
        type_submenu_item.show()
        menu_items.insert(2, ('__SUBMENU__', type_submenu_item))
        menu_items.insert(
            3,
            (
                'Flip Orientation',
                lambda: _loader._on_transition_flip_orientation(obj, manager, drawing_area),
            ),
        )

    def _add_arc_context_items(
        self, obj: Any, menu_items: list, manager: Any, drawing_area: Any
    ) -> None:
        """Append Arc-specific items."""
        from shypn.utils.arc_transform import is_straight, is_curved, is_signal_flow
        from shypn.netobjs.place import Place as _Place
        from shypn.netobjs.transition import Transition as _Transition
        from shypn.netobjs.test_arc import TestArc
        from shypn.netobjs.inhibitor_arc import InhibitorArc

        _loader = self._loader
        can_be_directional = isinstance(obj.source, _Place) and isinstance(obj.target, _Transition)
        is_test = isinstance(obj, TestArc)
        is_inhibitor_arc = isinstance(obj, InhibitorArc)
        is_signal = is_signal_flow(obj)
        is_normal_arc = not is_test and not is_inhibitor_arc and not is_signal

        menu_items.insert(2, ('Edit Weight...', lambda: _loader._on_arc_edit_weight(obj, manager, drawing_area)))
        menu_items.insert(3, None)

        if is_curved(obj):
            menu_items.insert(4, ('Transform to Straight', lambda: _loader._on_arc_make_straight(obj, manager, drawing_area)))
        elif is_straight(obj):
            menu_items.insert(4, ('Transform to Curved', lambda: _loader._on_arc_make_curved(obj, manager, drawing_area)))

        if can_be_directional:
            if not is_normal_arc:
                menu_items.insert(5, ('Convert to Normal Arc', lambda: _loader._on_arc_convert_to_normal(obj, manager, drawing_area)))
            if not is_test:
                menu_items.insert(5, ('Convert to Test Arc (Catalyst)', lambda: _loader._on_arc_convert_to_test(obj, manager, drawing_area)))
            if not is_inhibitor_arc:
                menu_items.insert(5, ('Convert to Inhibitor Arc', lambda: _loader._on_arc_convert_to_inhibitor(obj, manager, drawing_area)))

        if not is_signal:
            menu_items.insert(5, ('Convert to Signal Flow Arc', lambda: _loader._on_arc_convert_to_signal_flow(obj, manager, drawing_area)))

    # ------------------------------------------------------------------
    # Viewport / grid / canvas action handlers (Wayland-safe, no parent)
    # ------------------------------------------------------------------

    def _on_zoom_in_clicked(self, _menu: Any, drawing_area: Any, manager: Any) -> None:
        manager.zoom_in(manager.pointer_x, manager.pointer_y)
        drawing_area.queue_draw()

    def _on_zoom_out_clicked(self, _menu: Any, drawing_area: Any, manager: Any) -> None:
        manager.zoom_out(manager.pointer_x, manager.pointer_y)
        drawing_area.queue_draw()

    def _on_fit_to_window_clicked(self, _menu: Any, drawing_area: Any, manager: Any) -> None:
        manager.fit_to_page(padding_percent=10)
        drawing_area.queue_draw()

    def _on_rotate_90_cw_clicked(self, _menu: Any, drawing_area: Any, manager: Any) -> None:
        manager.rotate_canvas_90_cw()
        drawing_area.queue_draw()

    def _on_rotate_90_ccw_clicked(self, _menu: Any, drawing_area: Any, manager: Any) -> None:
        manager.rotate_canvas_90_ccw()
        drawing_area.queue_draw()

    def _on_rotate_180_clicked(self, _menu: Any, drawing_area: Any, manager: Any) -> None:
        manager.rotate_canvas_180()
        drawing_area.queue_draw()

    def _on_reset_rotation_clicked(self, _menu: Any, drawing_area: Any, manager: Any) -> None:
        manager.reset_canvas_rotation()
        drawing_area.queue_draw()

    def _on_grid_line_clicked(self, _menu: Any, drawing_area: Any, manager: Any) -> None:
        manager.set_grid_style('line')
        drawing_area.queue_draw()

    def _on_grid_dot_clicked(self, _menu: Any, drawing_area: Any, manager: Any) -> None:
        manager.set_grid_style('dot')
        drawing_area.queue_draw()

    def _on_grid_cross_clicked(self, _menu: Any, drawing_area: Any, manager: Any) -> None:
        manager.set_grid_style('cross')
        drawing_area.queue_draw()

    def _on_clear_canvas_clicked(self, _menu: Any, drawing_area: Any, manager: Any) -> None:
        """Clear canvas, prompting for unsaved-changes confirmation."""
        persistency = getattr(self._loader, 'persistency', None)
        if persistency:
            if not persistency.check_unsaved_changes():
                return
            persistency.new_document()
        manager.clear_all_objects()
        drawing_area.queue_draw()

    def _on_create_center_marker_clicked(self, _menu: Any, drawing_area: Any, manager: Any) -> None:
        manager.create_test_objects()
        drawing_area.queue_draw()

    def _on_reset_zoom_clicked(self, _menu: Any, drawing_area: Any, manager: Any) -> None:
        manager.set_zoom(1.0, manager.viewport_width / 2, manager.viewport_height / 2)
        drawing_area.queue_draw()

    def _on_center_view_clicked(self, _menu: Any, drawing_area: Any, manager: Any) -> None:
        manager.pan_x = 0
        manager.pan_y = 0
        drawing_area.queue_draw()
