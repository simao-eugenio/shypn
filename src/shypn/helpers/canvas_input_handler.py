"""Canvas input event handler for model canvas (GTK3).

Owns per-canvas interaction state (drag, arc, click, lasso contexts,
clipboard, pointer position) and implements all GDK event handlers.

All operations that require ModelCanvasLoader context (file I/O, tab
management, context-menus) are injected via *CanvasInputCallbacks* so
this class stays independent of the loader hierarchy.

Module structure:
    CanvasInputCallbacks        -- typed callback bundle (injected by MCL)
    AbstractCanvasInputHandler  -- ABC defining the public contract
    CanvasInputHandler          -- concrete implementation
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

try:
    import gi  # type: ignore[import-untyped]
    gi.require_version('Gtk', '3.0')
    gi.require_version('Gdk', '3.0')
    from gi.repository import Gdk, GLib, Gtk  # type: ignore[import-untyped]
except Exception:
    # Allow import without GTK for testing / headless environments.
    Gdk = None
    GLib = None
    Gtk = None

try:
    from shypn.netobjs import Arc, Place, Transition
except ImportError:
    Arc = Place = Transition = None

from shypn.helpers.canvas_interaction_context import CanvasInteractionContext


# ---------------------------------------------------------------------------
# Callback bundle
# ---------------------------------------------------------------------------

@dataclass
class CanvasInputCallbacks:
    """All external operations the handler delegates back to ModelCanvasLoader.

    Every field is a callable.  Use lambdas to capture the loader's ``self``
    lazily so the callbacks always see the latest attribute values.
    """

    #: (x, y, widget, manager, obj) -> None — show per-object context menu
    show_object_context_menu: Any
    #: (x, y, widget) -> None — show blank-canvas context menu
    show_canvas_context_menu: Any

    #: () -> None — trigger file save for the current document
    on_file_save: Any
    #: () -> None — trigger "save as" for the current document
    on_file_save_as: Any
    #: () -> None — open file-chooser dialog
    on_file_open: Any
    #: () -> None — open a new empty document tab
    on_add_document: Any
    #: (page_num: int) -> None — close the tab at *page_num*
    on_close_tab: Any
    #: (widget) -> int — return the notebook page index for *widget*'s tab
    get_page_num_for_widget: Any
    #: () -> Any — return the current GTK parent window (or None)
    get_parent_window: Any

    #: Shared reference to MCL's ``overlay_managers`` dict (always current)
    overlay_managers: Dict[Any, Any]

    #: Optional: () -> bool — pop down any open canvas context menu.
    #: Called during Escape handling.  May be None if not needed.
    canvas_context_menu_popdown: Any = field(default=None)


# ---------------------------------------------------------------------------
# Abstract base class
# ---------------------------------------------------------------------------

class AbstractCanvasInputHandler(ABC):
    """ABC defining the public contract for canvas input handling."""

    @abstractmethod
    def register_drawing_area(self, drawing_area: Any) -> None:
        """Create (or reset) the interaction context for *drawing_area*."""
        ...

    @abstractmethod
    def on_button_press(self, widget: Any, event: Any, manager: Any) -> bool:
        """GTK ``button-press-event`` handler."""
        ...

    @abstractmethod
    def on_button_release(self, widget: Any, event: Any, manager: Any) -> bool:
        """GTK ``button-release-event`` handler."""
        ...

    @abstractmethod
    def on_motion_notify(self, widget: Any, event: Any, manager: Any) -> bool:
        """GTK ``motion-notify-event`` handler."""
        ...

    @abstractmethod
    def on_scroll_event(self, widget: Any, event: Any, manager: Any) -> bool:
        """GTK ``scroll-event`` handler (zoom)."""
        ...

    @abstractmethod
    def on_key_press_event(self, widget: Any, event: Any, manager: Any) -> bool:
        """GTK ``key-press-event`` handler."""
        ...

    @abstractmethod
    def cut_selection(self, manager: Any, widget: Any) -> None:
        """Cut selected objects to the internal clipboard."""
        ...

    @abstractmethod
    def copy_selection(self, manager: Any) -> None:
        """Copy selected objects to the internal clipboard."""
        ...

    @abstractmethod
    def paste_selection(
        self,
        manager: Any,
        widget: Any,
        pointer_x: Optional[float] = None,
        pointer_y: Optional[float] = None,
    ) -> None:
        """Paste clipboard objects at *pointer_x/y* (world coords)."""
        ...

    @abstractmethod
    def delete_object(self, manager: Any, obj: Any) -> None:
        """Delete a single place / transition / arc from *manager*."""
        ...

    @property
    @abstractmethod
    def canvas_ctx(self) -> Dict[Any, CanvasInteractionContext]:
        """Per-widget interaction context registry."""
        ...

    @property
    @abstractmethod
    def clipboard(self) -> List[Any]:
        """Current clipboard contents (serialised model objects)."""
        ...

    @clipboard.setter
    @abstractmethod
    def clipboard(self, value: List[Any]) -> None: ...

    @property
    @abstractmethod
    def last_pointer_world_x(self) -> float:
        """Last known pointer world X (updated on every motion event)."""
        ...

    @property
    @abstractmethod
    def last_pointer_world_y(self) -> float:
        """Last known pointer world Y (updated on every motion event)."""
        ...


# ---------------------------------------------------------------------------
# Concrete implementation
# ---------------------------------------------------------------------------

class CanvasInputHandler(AbstractCanvasInputHandler):
    """Concrete GTK3 input handler for model canvases.

    Owns all per-canvas interaction state that was previously scattered
    across ``ModelCanvasLoader`` instance attributes:

    * ``_canvas_ctx``            — per-drawing-area :class:`CanvasInteractionContext`
    * ``_clipboard``             — copy/paste data
    * ``_last_pointer_world_x/y``— pointer world coordinates (paste-at-pointer)
    * ``_last_interaction_time`` — lightweight interaction tracking

    External operations use :class:`CanvasInputCallbacks` for loose coupling.
    """

    def __init__(
        self,
        callbacks: CanvasInputCallbacks,
        logger: Any,
    ) -> None:
        self.callbacks = callbacks
        self._logger: Any = logger

        # Per-canvas mutable state ----------------------------------------
        self._canvas_ctx: Dict[Any, CanvasInteractionContext] = {}
        self._clipboard: List[Any] = []
        self._last_pointer_world_x: float = 0.0
        self._last_pointer_world_y: float = 0.0
        self._last_interaction_time: float = 0.0

    # ------------------------------------------------------------------
    # ABC property implementations
    # ------------------------------------------------------------------

    @property
    def canvas_ctx(self) -> Dict[Any, CanvasInteractionContext]:
        return self._canvas_ctx

    @property
    def clipboard(self) -> List[Any]:
        return self._clipboard

    @clipboard.setter
    def clipboard(self, value: List[Any]) -> None:
        self._clipboard = value

    @property
    def last_pointer_world_x(self) -> float:
        return self._last_pointer_world_x

    @property
    def last_pointer_world_y(self) -> float:
        return self._last_pointer_world_y

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register_drawing_area(self, drawing_area: Any) -> None:
        """Create a fresh :class:`CanvasInteractionContext` for *drawing_area*."""
        self._canvas_ctx[drawing_area] = CanvasInteractionContext()

    # ------------------------------------------------------------------
    # Lightweight interaction tracking
    # ------------------------------------------------------------------

    def _mark_interaction(self, widget: Any) -> None:
        """Record a user interaction timestamp (no widget traversal)."""
        self._last_interaction_time = time.time()

    # ------------------------------------------------------------------
    # Button press
    # ------------------------------------------------------------------

    def on_button_press(self, widget: Any, event: Any, manager: Any) -> bool:
        """Handle button press events (GTK3)."""
        # Grab focus so keyboard shortcuts work
        if not widget.has_focus():
            widget.grab_focus()

        ctx = self._canvas_ctx[widget]
        state = ctx.drag
        arc_state = ctx.arc
        lasso_state = ctx.lasso

        # Check if lasso mode is active
        if lasso_state.get('active', False) and event.button == 1:
            world_x, world_y = manager.screen_to_world(event.x, event.y)
            is_ctrl = event.state & Gdk.ModifierType.CONTROL_MASK
            lasso_state['is_ctrl'] = is_ctrl
            lasso_state['selector'].start_lasso(world_x, world_y)
            widget.queue_draw()
            return True

        # Check if we should ignore this click (after dialog close)
        if arc_state.get('ignore_next_release', False):
            arc_state['ignore_next_release'] = False
            return True  # Consume the event without doing anything

        if event.button == 1 and manager.is_tool_active() and (manager.get_tool() == 'arc'):
            world_x, world_y = manager.screen_to_world(event.x, event.y)
            clicked_obj = manager.find_object_at_position(world_x, world_y)
            if clicked_obj is None:
                if arc_state['source'] is not None:
                    arc_state['source'] = None
                    widget.queue_draw()
                return True
            if arc_state['source'] is None:
                if isinstance(clicked_obj, (Place, Transition)):
                    arc_state['source'] = clicked_obj
                    widget.queue_draw()
                return True
            else:
                target = clicked_obj
                source = arc_state['source']
                if target == source:
                    return True
                try:
                    arc = manager.add_arc(source, target)
                    widget.queue_draw()
                except ValueError as e:
                    parent = self.callbacks.get_parent_window()
                    dialog = Gtk.MessageDialog(
                        transient_for=parent,
                        flags=0,
                        message_type=Gtk.MessageType.ERROR,
                        buttons=Gtk.ButtonsType.OK,
                        text="Cannot Create Arc"
                    )
                    dialog.set_keep_above(True)
                    dialog.format_secondary_text(str(e))
                    dialog.run()
                    dialog.destroy()
                finally:
                    arc_state['source'] = None
                    arc_state['target_valid'] = None
                    arc_state['hovered_target'] = None
                    widget.queue_draw()
                return True

        if event.button == 1 and manager.is_tool_active():
            tool = manager.get_tool()
            if tool in ('place', 'transition'):
                world_x, world_y = manager.screen_to_world(event.x, event.y)
                if tool == 'place':
                    place = manager.add_place(world_x, world_y)
                    widget.queue_draw()
                elif tool == 'transition':
                    transition = manager.add_transition(world_x, world_y)
                    widget.queue_draw()
                return True

        tool = manager.get_tool() if manager.is_tool_active() else None
        is_selection_mode = tool is None or tool == 'select'
        if event.button == 1 and is_selection_mode:
            world_x, world_y = manager.screen_to_world(event.x, event.y)

            # Check if clicking on a transform handle in edit mode
            if manager.selection_manager.is_edit_mode():
                edit_target = manager.selection_manager.get_edit_target()
                if edit_target:
                    handle = manager.editing_transforms.check_handle_at_position(
                        edit_target, world_x, world_y, manager.zoom
                    )
                    if handle:
                        if manager.editing_transforms.start_transformation(
                            edit_target, handle, world_x, world_y
                        ):
                            state['active'] = True
                            state['button'] = event.button
                            state['start_x'] = event.x
                            state['start_y'] = event.y
                            state['is_panning'] = False
                            state['is_rect_selecting'] = False
                            state['is_transforming'] = True
                            widget.queue_draw()
                            return True

            # Check for objects (places, transitions, arcs)
            clicked_obj = manager.find_object_at_position(world_x, world_y)
            is_ctrl = event.state & Gdk.ModifierType.CONTROL_MASK

            if clicked_obj is not None:
                click_state = ctx.click
                current_time = time.time()
                time_since_last = current_time - click_state['last_click_time']
                is_double_click = (
                    time_since_last < click_state['double_click_threshold']
                    and click_state['last_click_obj'] == clicked_obj
                )
                if click_state['pending_timeout'] is not None:
                    GLib.source_remove(click_state['pending_timeout'])
                    click_state['pending_timeout'] = None
                    click_state['pending_click_data'] = None

                if clicked_obj.selected and (not is_double_click):
                    if is_ctrl:
                        manager.selection_manager.deselect(clicked_obj)
                        widget.queue_draw()
                        click_state['last_click_time'] = current_time
                        click_state['last_click_obj'] = clicked_obj
                        return True
                    # Already selected (no Ctrl) — start drag immediately
                    manager.selection_manager.start_drag(clicked_obj, event.x, event.y, manager)
                    state['active'] = True
                    state['button'] = event.button
                    state['start_x'] = event.x
                    state['start_y'] = event.y
                    state['is_panning'] = False
                    state['is_rect_selecting'] = False
                    click_state['last_click_time'] = current_time
                    click_state['last_click_obj'] = clicked_obj
                elif not is_double_click:
                    if not is_ctrl:
                        manager.clear_all_selections()
                    clicked_obj.selected = True
                    manager.selection_manager.select(clicked_obj, multi=is_ctrl, manager=manager)
                    manager.selection_manager.start_drag(clicked_obj, event.x, event.y, manager)
                    state['active'] = True
                    state['button'] = event.button
                    state['start_x'] = event.x
                    state['start_y'] = event.y
                    state['is_panning'] = False
                    state['is_rect_selecting'] = False
                    widget.queue_draw()
                    click_state['last_click_time'] = current_time
                    click_state['last_click_obj'] = clicked_obj
                    return True

                if is_double_click:
                    if clicked_obj.selected:
                        manager.selection_manager.enter_edit_mode(clicked_obj, manager=manager)
                    else:
                        manager.selection_manager.toggle_selection(clicked_obj, multi=is_ctrl, manager=manager)
                        manager.selection_manager.enter_edit_mode(clicked_obj, manager=manager)
                    click_state['last_click_time'] = 0.0
                    click_state['last_click_obj'] = None
                    widget.queue_draw()
                    return True
            else:
                # Clicked on empty space
                if manager.selection_manager.is_edit_mode():
                    manager.selection_manager.exit_edit_mode()
                    widget.queue_draw()
                    return True
                # Start rectangle selection
                manager.rectangle_selection.start(world_x, world_y)
                state['active'] = True
                state['button'] = event.button
                state['start_x'] = event.x
                state['start_y'] = event.y
                state['is_panning'] = False
                state['is_rect_selecting'] = True
                if not is_ctrl:
                    manager.clear_all_selections()
                widget.grab_focus()
                return True

        state['active'] = True
        state['button'] = event.button
        state['start_x'] = event.x
        state['start_y'] = event.y
        state['start_pan_x'] = manager.pan_x
        state['start_pan_y'] = manager.pan_y
        state['is_panning'] = False
        state['is_rect_selecting'] = False
        widget.grab_focus()
        return True

    # ------------------------------------------------------------------
    # Button release
    # ------------------------------------------------------------------

    def on_button_release(self, widget: Any, event: Any, manager: Any) -> bool:
        """Handle button release events (GTK3)."""
        ctx = self._canvas_ctx[widget]
        state = ctx.drag
        lasso_state = ctx.lasso

        # Complete lasso selection if active
        if lasso_state.get('active', False) and lasso_state.get('selector'):
            if lasso_state['selector'].is_active and event.button == 1:
                is_ctrl = lasso_state.get('is_ctrl', False)
                lasso_state['selector'].finish_lasso(multi=is_ctrl)
                lasso_state['active'] = False
                lasso_state['is_ctrl'] = False
                widget.queue_draw()
                return True

        # End transformation if active
        if state.get('is_transforming', False):
            if manager.editing_transforms.end_transformation():
                widget.queue_draw()
            state['is_transforming'] = False
            state['active'] = False
            state['button'] = 0
            return True

        # Capture initial positions before ending drag (for undo)
        initial_positions = None
        if manager.selection_manager.is_dragging():
            initial_positions = manager.selection_manager.get_move_data_for_undo()

        # End drag
        if manager.selection_manager.end_drag():
            if initial_positions and hasattr(manager, 'undo_manager'):
                from shypn.edit.undo_operations import MoveOperation
                manager.undo_manager.push(MoveOperation(initial_positions, manager))
            state['active'] = False
            state['button'] = 0
            widget.queue_draw()
            return True

        if state.get('is_rect_selecting', False):
            is_ctrl = event.state & Gdk.ModifierType.CONTROL_MASK
            bounds = manager.rectangle_selection.finish()
            if bounds:
                count = manager.rectangle_selection.select_objects(manager, multi=is_ctrl)
            state['is_rect_selecting'] = False
            widget.queue_draw()

        if event.button == 3:
            dx = event.x - state['start_x']
            dy = event.y - state['start_y']
            distance = (dx * dx + dy * dy) ** 0.5
            if distance < 10:
                world_x, world_y = manager.screen_to_world(event.x, event.y)
                clicked_obj = manager.find_object_at_position(world_x, world_y)
                if clicked_obj:
                    self.callbacks.show_object_context_menu(event.x, event.y, widget, manager, clicked_obj)
                else:
                    self.callbacks.show_canvas_context_menu(event.x, event.y, widget)

        was_panning = state['is_panning']
        state['active'] = False
        state['button'] = 0
        state['is_panning'] = False
        if was_panning:
            manager.save_view_state_to_file()
        return True

    # ------------------------------------------------------------------
    # Motion notify
    # ------------------------------------------------------------------

    def on_motion_notify(self, widget: Any, event: Any, manager: Any) -> bool:
        """Handle motion events (GTK3)."""
        ctx = self._canvas_ctx[widget]
        state = ctx.drag
        arc_state = ctx.arc
        lasso_state = ctx.lasso

        manager.set_pointer_position(event.x, event.y)
        world_x, world_y = manager.screen_to_world(event.x, event.y)
        arc_state['cursor_pos'] = (world_x, world_y)

        # Track pointer position for paste-at-pointer functionality
        self._last_pointer_world_x = world_x
        self._last_pointer_world_y = world_y

        # Update hover tooltip (only when not actively dragging/panning)
        if not state['active']:
            hovered_obj = manager.find_object_at_position(world_x, world_y)
            if hovered_obj:
                from shypn.netobjs import Place, Transition, Arc
                if isinstance(hovered_obj, (Place, Transition, Arc)):
                    obj_id = hovered_obj.id if hasattr(hovered_obj, 'id') else "?"
                    obj_name = hovered_obj.name if hasattr(hovered_obj, 'name') else ""
                    if obj_name and obj_name != obj_id:
                        tooltip = f"{obj_id} - {obj_name}"
                    else:
                        tooltip = obj_id
                    widget.set_tooltip_text(tooltip)
            else:
                widget.set_tooltip_text(None)

        # Update lasso path if active
        if lasso_state.get('active', False) and lasso_state.get('selector'):
            if lasso_state['selector'].is_active:
                lasso_state['selector'].add_point(world_x, world_y)
                widget.queue_draw()
                return True

        # Update arc preview with target validation
        if manager.is_tool_active() and manager.get_tool() == 'arc' and (arc_state['source'] is not None):
            from shypn.netobjs import Place, Transition
            hovered = manager.find_object_at_position(world_x, world_y)
            if hovered and hovered != arc_state['source']:
                source = arc_state['source']
                is_valid = (
                    (isinstance(source, Place) and isinstance(hovered, Transition))
                    or (isinstance(source, Transition) and isinstance(hovered, Place))
                )
                arc_state['target_valid'] = is_valid
                arc_state['hovered_target'] = hovered
            else:
                arc_state['target_valid'] = None
                arc_state['hovered_target'] = None
            widget.queue_draw()

        if state['active'] and state['button'] > 0:
            # Handle transformation drag
            if state.get('is_transforming', False):
                manager.editing_transforms.update_transformation(world_x, world_y)
                widget.queue_draw()
                return True

            dx = event.x - state['start_x']
            dy = event.y - state['start_y']
            if not state['is_panning'] and (abs(dx) >= 2 or abs(dy) >= 2):
                state['is_panning'] = True

            if state.get('is_rect_selecting', False):
                world_x, world_y = manager.screen_to_world(event.x, event.y)
                manager.rectangle_selection.update(world_x, world_y)
                widget.queue_draw()
                return True

            if manager.selection_manager.update_drag(event.x, event.y, manager):
                self._mark_interaction(widget)
                click_state = ctx.click
                if click_state and click_state.get('pending_timeout'):
                    GLib.source_remove(click_state['pending_timeout'])
                    click_state['pending_timeout'] = None
                    click_state['pending_click_data'] = None
                widget.queue_draw()
                return True

            is_shift_pressed = event.state & Gdk.ModifierType.SHIFT_MASK
            should_pan = state['button'] in [2, 3] or (state['button'] == 1 and is_shift_pressed)
            if should_pan and state['is_panning']:
                self._mark_interaction(widget)
                dx = event.x - state['start_x']
                dy = event.y - state['start_y']
                # Reset pan to start position then apply delta
                manager.pan_x = state['start_pan_x']
                manager.pan_y = state['start_pan_y']
                manager.pan(dx, dy)
                widget.queue_draw()
        return True

    # ------------------------------------------------------------------
    # Scroll (zoom)
    # ------------------------------------------------------------------

    def on_scroll_event(self, widget: Any, event: Any, manager: Any) -> bool:
        """Handle scroll events for zoom (GTK3).

        Supports both discrete scroll wheels and smooth scrolling (trackpads).
        Zooms centred at cursor position (pointer-centred zoom).
        """
        direction = event.direction
        factor = None
        if direction == Gdk.ScrollDirection.SMOOTH:
            dy = event.delta_y
            if abs(dy) < 1e-06:
                return False
            factor = 1 / 1.1 if dy > 0 else 1.1
        elif direction == Gdk.ScrollDirection.UP:
            factor = 1.1
        elif direction == Gdk.ScrollDirection.DOWN:
            factor = 1 / 1.1
        if factor is None:
            return False

        self._mark_interaction(widget)
        manager.zoom_at_point(factor, event.x, event.y)
        manager.save_view_state_to_file()
        widget.queue_draw()
        return True

    # ------------------------------------------------------------------
    # Key press
    # ------------------------------------------------------------------

    def on_key_press_event(self, widget: Any, event: Any, manager: Any) -> bool:
        """Handle key press events (GTK3)."""
        ctx = self._canvas_ctx.get(widget)

        # Let the editing operations palette handle its shortcuts first
        if widget in self.callbacks.overlay_managers:
            overlay_manager = self.callbacks.overlay_managers[widget]
            editing_ops_palette = overlay_manager.get_palette('editing_operations')
            if editing_ops_palette and editing_ops_palette.handle_key_press(event):
                return True

        is_ctrl = event.state & Gdk.ModifierType.CONTROL_MASK
        is_shift = event.state & Gdk.ModifierType.SHIFT_MASK

        # Delete key — delete selected objects
        if event.keyval == Gdk.KEY_Delete or event.keyval == Gdk.KEY_KP_Delete:
            selected = manager.selection_manager.get_selected_objects(manager)
            if selected:
                if hasattr(manager, 'undo_manager'):
                    try:
                        from shypn.edit.snapshots import capture_delete_snapshots
                        from shypn.edit.undo_operations import DeleteOperation
                        snapshots = capture_delete_snapshots(manager, selected)
                        manager.undo_manager.push(DeleteOperation(snapshots))
                    except Exception:
                        try:
                            from shypn.edit.undo_operations import DeleteOperation
                            snapshots = self._capture_delete_snapshots_inline(manager, selected)
                            manager.undo_manager.push(DeleteOperation(snapshots))
                        except Exception:
                            self._logger.debug(
                                "Undo snapshot capture failed for delete (keyboard)",
                                exc_info=True,
                            )
                for obj in list(selected):
                    self.delete_object(manager, obj)
                widget.queue_draw()
                return True

        # Cut (Ctrl+X)
        if is_ctrl and not is_shift and (event.keyval == Gdk.KEY_x or event.keyval == Gdk.KEY_X):
            selected = manager.selection_manager.get_selected_objects(manager)
            if selected:
                self.cut_selection(manager, widget)
                return True

        # Copy (Ctrl+C)
        if is_ctrl and not is_shift and (event.keyval == Gdk.KEY_c or event.keyval == Gdk.KEY_C):
            selected = manager.selection_manager.get_selected_objects(manager)
            if selected:
                self.copy_selection(manager)
                return True

        # Paste (Ctrl+V)
        if is_ctrl and not is_shift and (event.keyval == Gdk.KEY_v or event.keyval == Gdk.KEY_V):
            if self._clipboard:
                self.paste_selection(
                    manager,
                    widget,
                    self._last_pointer_world_x,
                    self._last_pointer_world_y,
                )
                return True

        # Save (Ctrl+S)
        if is_ctrl and not is_shift and (event.keyval == Gdk.KEY_s or event.keyval == Gdk.KEY_S):
            self.callbacks.on_file_save()
            return True

        # Save As (Ctrl+Shift+S)
        if is_ctrl and is_shift and (event.keyval == Gdk.KEY_s or event.keyval == Gdk.KEY_S):
            self.callbacks.on_file_save_as()
            return True

        # Open (Ctrl+O)
        if is_ctrl and not is_shift and (event.keyval == Gdk.KEY_o or event.keyval == Gdk.KEY_O):
            self.callbacks.on_file_open()
            return True

        # Undo (Ctrl+Z)
        if is_ctrl and not is_shift and (event.keyval == Gdk.KEY_z or event.keyval == Gdk.KEY_Z):
            if hasattr(manager, 'undo_manager') and manager.undo_manager and manager.undo_manager.undo(manager):
                widget.queue_draw()
            return True

        # Redo (Ctrl+Shift+Z or Ctrl+Y)
        if (
            (is_ctrl and is_shift and (event.keyval == Gdk.KEY_z or event.keyval == Gdk.KEY_Z))
            or (is_ctrl and not is_shift and (event.keyval == Gdk.KEY_y or event.keyval == Gdk.KEY_Y))
        ):
            if hasattr(manager, 'undo_manager') and manager.undo_manager and manager.undo_manager.redo(manager):
                widget.queue_draw()
            return True

        # New document (Ctrl+N)
        if is_ctrl and not is_shift and (event.keyval == Gdk.KEY_n or event.keyval == Gdk.KEY_N):
            self.callbacks.on_add_document()
            return True

        # Close tab (Ctrl+W)
        if is_ctrl and not is_shift and (event.keyval == Gdk.KEY_w or event.keyval == Gdk.KEY_W):
            page_num = self.callbacks.get_page_num_for_widget(widget)
            if page_num >= 0:
                self.callbacks.on_close_tab(page_num)
            return True

        if event.keyval == Gdk.KEY_Escape:
            # Cancel lasso if active
            lasso_state = ctx.lasso if ctx else {}
            if lasso_state.get('active', False) and lasso_state.get('selector'):
                if lasso_state['selector'].is_active:
                    lasso_state['selector'].cancel_lasso()
                    lasso_state['active'] = False
                    widget.queue_draw()
                    return True

            # Cancel transformation if active
            if manager.editing_transforms.is_transforming():
                manager.editing_transforms.cancel_transformation()
                widget.queue_draw()
                return True

            # Cancel drag if active
            if manager.selection_manager.cancel_drag():
                widget.queue_draw()
                return True

            # Exit edit mode if active
            if manager.selection_manager.is_edit_mode():
                manager.selection_manager.exit_edit_mode()
                widget.queue_draw()
                return True

            # Close context menu if open
            if self.callbacks.canvas_context_menu_popdown:
                if self.callbacks.canvas_context_menu_popdown():
                    return True

            # Clear all selections if any exist
            if manager.selection_manager.has_selection():
                manager.clear_all_selections()
                widget.queue_draw()
                return True

        return False

    # ------------------------------------------------------------------
    # Clipboard operations
    # ------------------------------------------------------------------

    def cut_selection(self, manager: Any, widget: Any) -> None:
        """Cut selected objects to clipboard (copy then delete)."""
        self.copy_selection(manager)
        selected = manager.selection_manager.get_selected_objects(manager)
        if selected:
            if hasattr(manager, 'undo_manager'):
                try:
                    from shypn.edit.snapshots import capture_delete_snapshots
                    from shypn.edit.undo_operations import DeleteOperation
                    snapshots = capture_delete_snapshots(manager, selected)
                    manager.undo_manager.push(DeleteOperation(snapshots))
                except Exception:
                    try:
                        from shypn.edit.undo_operations import DeleteOperation
                        snapshots = self._capture_delete_snapshots_inline(manager, selected)
                        manager.undo_manager.push(DeleteOperation(snapshots))
                    except Exception:
                        self._logger.debug(
                            "Undo snapshot capture failed for delete (context menu)",
                            exc_info=True,
                        )
            for obj in list(selected):
                self.delete_object(manager, obj)
            widget.queue_draw()

    def copy_selection(self, manager: Any) -> None:
        """Copy selected objects to the internal clipboard."""
        from shypn.netobjs import Place, Transition, Arc
        selected = manager.selection_manager.get_selected_objects(manager)
        if not selected:
            return

        self._clipboard = []
        places = [obj for obj in selected if isinstance(obj, Place)]
        transitions = [obj for obj in selected if isinstance(obj, Transition)]
        arcs = [obj for obj in selected if isinstance(obj, Arc)]

        for place in places:
            self._clipboard.append({
                'type': 'place',
                'name': place.name,
                'x': place.x,
                'y': place.y,
                'radius': place.radius,
                'tokens': place.tokens,
                'capacity': getattr(place, 'capacity', float('inf')),
                'id': id(place),
            })
        for transition in transitions:
            self._clipboard.append({
                'type': 'transition',
                'name': transition.name,
                'x': transition.x,
                'y': transition.y,
                'width': transition.width,
                'height': transition.height,
                'horizontal': transition.horizontal,
                'transition_type': getattr(transition, 'transition_type', 'continuous'),
                'rate': getattr(transition, 'rate', 1.0),
                'delay': getattr(transition, 'delay', 0.0),
                'id': id(transition),
            })
        for arc in arcs:
            if arc.source in selected and arc.target in selected:
                arc_data: Dict[str, Any] = {
                    'type': 'arc',
                    'source_id': id(arc.source),
                    'target_id': id(arc.target),
                    'weight': arc.weight,
                    'arc_type': getattr(arc, 'arc_type', 'normal'),
                }
                if hasattr(arc, 'is_curved') and arc.is_curved:
                    arc_data['is_curved'] = True
                    arc_data['handle_x'] = arc.handle_x
                    arc_data['handle_y'] = arc.handle_y
                self._clipboard.append(arc_data)

    def paste_selection(
        self,
        manager: Any,
        widget: Any,
        pointer_x: Optional[float] = None,
        pointer_y: Optional[float] = None,
    ) -> None:
        """Paste clipboard objects centred at *pointer_x/y* (world coords)."""
        if not self._clipboard:
            return

        items_with_pos = [item for item in self._clipboard if 'x' in item and 'y' in item]
        if not items_with_pos:
            return

        clipboard_min_x = min(item['x'] for item in items_with_pos)
        clipboard_min_y = min(item['y'] for item in items_with_pos)
        clipboard_max_x = max(item['x'] for item in items_with_pos)
        clipboard_max_y = max(item['y'] for item in items_with_pos)
        clipboard_center_x = (clipboard_min_x + clipboard_max_x) / 2
        clipboard_center_y = (clipboard_min_y + clipboard_max_y) / 2

        if pointer_x is None or pointer_y is None:
            screen_center_x = manager.viewport_width / 2
            screen_center_y = manager.viewport_height / 2
            pointer_x, pointer_y = manager.screen_to_world(screen_center_x, screen_center_y)

        offset_x = pointer_x - clipboard_center_x
        offset_y = pointer_y - clipboard_center_y

        manager.clear_all_selections()
        id_map: Dict[int, Any] = {}

        # Create nodes first
        for item in self._clipboard:
            if item['type'] == 'place':
                place = manager.add_place(item['x'] + offset_x, item['y'] + offset_y)
                place.tokens = item['tokens']
                place.capacity = item.get('capacity', float('inf'))
                place.radius = item['radius']
                id_map[item['id']] = place
                place.selected = True
                manager.selection_manager.select(place, multi=True, manager=manager)
            elif item['type'] == 'transition':
                transition = manager.add_transition(item['x'] + offset_x, item['y'] + offset_y)
                transition.horizontal = item['horizontal']
                transition.width = item['width']
                transition.height = item['height']
                transition.transition_type = item.get('transition_type', 'continuous')
                transition.rate = item.get('rate', 1.0)
                transition.delay = item.get('delay', 0.0)
                id_map[item['id']] = transition
                transition.selected = True
                manager.selection_manager.select(transition, multi=True, manager=manager)

        # Then create arcs
        for item in self._clipboard:
            if item['type'] == 'arc':
                source = id_map.get(item['source_id'])
                target = id_map.get(item['target_id'])
                if source and target:
                    try:
                        arc = manager.add_arc(source, target)
                        arc.weight = item['weight']
                        arc_type = item.get('arc_type', 'normal')
                        if arc_type == 'inhibitor':
                            from shypn.utils.arc_transform import convert_to_inhibitor
                            new_arc = convert_to_inhibitor(arc)
                            manager.replace_arc(arc, new_arc)
                            arc = new_arc
                        elif arc_type == 'test':
                            from shypn.utils.arc_transform import convert_to_test
                            new_arc = convert_to_test(arc)
                            manager.replace_arc(arc, new_arc)
                            arc = new_arc
                        elif arc_type == 'signal_flow':
                            from shypn.utils.arc_transform import convert_to_signal_flow
                            try:
                                new_arc = convert_to_signal_flow(arc)
                                manager.replace_arc(arc, new_arc)
                                arc = new_arc
                            except ValueError:
                                pass
                        if item.get('is_curved'):
                            arc.is_curved = True
                            arc.handle_x = item['handle_x'] + offset_x
                            arc.handle_y = item['handle_y'] + offset_y
                    except ValueError:
                        pass
        widget.queue_draw()

    # ------------------------------------------------------------------
    # Delete helpers
    # ------------------------------------------------------------------

    def delete_object(self, manager: Any, obj: Any) -> None:
        """Delete a single place, transition, or arc from *manager*."""
        from shypn.netobjs import Place, Transition, Arc
        if isinstance(obj, Place):
            manager.remove_place(obj)
        elif isinstance(obj, Transition):
            manager.remove_transition(obj)
        elif isinstance(obj, Arc):
            manager.remove_arc(obj)

    def _capture_delete_snapshots_inline(self, manager: Any, targets: Any) -> List[Any]:
        """Inline snapshot capture (fallback when shypn.edit.snapshots unavailable)."""
        from shypn.netobjs import Place, Arc
        snaps: List[Any] = []
        recorded_arc_ids: Set[int] = set()

        def snap_arc(a: Any) -> Dict[str, Any]:
            return {
                'kind': 'arc',
                'id': getattr(a, 'id', None),
                'label': getattr(a, 'label', None),
                'source_id': getattr(a.source, 'id', None),
                'target_id': getattr(a.target, 'id', None),
            }

        for target in targets:
            if isinstance(target, Arc):
                s = snap_arc(target)
                if s['id'] and s['id'] not in recorded_arc_ids:
                    snaps.append(s)
                    recorded_arc_ids.add(s['id'])
                continue
            kind = 'place' if isinstance(target, Place) else 'transition'
            base: Dict[str, Any] = {
                'kind': kind,
                'id': getattr(target, 'id', None),
                'label': getattr(target, 'label', None),
                'x': getattr(target, 'x', 0.0),
                'y': getattr(target, 'y', 0.0),
            }
            if kind == 'place':
                base['radius'] = getattr(target, 'radius', None)
            else:
                base['width'] = getattr(target, 'width', None)
                base['height'] = getattr(target, 'height', None)
            incident: List[Any] = []
            connected_ids: List[Any] = []
            for a in manager.arcs:
                if a.source == target or a.target == target:
                    a_id = getattr(a, 'id', None)
                    if a_id and a_id not in recorded_arc_ids:
                        incident.append(snap_arc(a))
                        connected_ids.append(a_id)
                        recorded_arc_ids.add(a_id)
            base['connected_arc_ids'] = connected_ids
            base['arcs'] = incident
            snaps.append(base)
        return snaps
