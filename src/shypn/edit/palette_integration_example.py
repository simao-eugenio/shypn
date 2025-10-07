#!/usr/bin/env python3
"""Example: How to integrate the new OOP palette system into model_canvas_loader.py

This shows the pattern for using PaletteManager with the refactored palettes.
"""

from gi.repository import Gtk
from shypn.edit.palette_manager import PaletteManager
from shypn.edit.tools_palette_new import ToolsPalette
from shypn.edit.operations_palette_new import OperationsPalette


def example_setup_palettes_in_canvas(overlay_widget, canvas_manager):
    """Example of how to set up palettes in model_canvas_loader.py
    
    Args:
        overlay_widget: GtkOverlay containing the canvas
        canvas_manager: ModelCanvasManager instance
    """
    
    # Step 1: Create PaletteManager
    palette_manager = PaletteManager(overlay_widget)
    
    # Step 2: Create ToolsPalette (pure Python - no UI file!)
    tools_palette = ToolsPalette()
    
    # Step 3: Register tools palette with position
    # Position: Center horizontally, End (bottom) vertically
    palette_manager.register_palette(
        tools_palette,
        position=(Gtk.Align.CENTER, Gtk.Align.END)
    )
    
    # Step 4: Create OperationsPalette
    ops_palette = OperationsPalette()
    
    # Step 5: Register operations palette with different position
    # Position: Start (left) horizontally, End (bottom) vertically
    palette_manager.register_palette(
        ops_palette,
        position=(Gtk.Align.START, Gtk.Align.END)
    )
    
    # Step 6: Connect signals to canvas manager
    
    # Tools palette signal
    def on_tool_selected(palette, tool_name):
        """Handle tool selection."""
        if tool_name:
            print(f"Tool selected: {tool_name}")
            # Set tool in canvas manager
            if hasattr(canvas_manager, 'set_tool'):
                canvas_manager.set_tool(tool_name)
        else:
            print("Tool cleared")
            if hasattr(canvas_manager, 'clear_tool'):
                canvas_manager.clear_tool()
    
    tools_palette.connect('tool-selected', on_tool_selected)
    
    # Operations palette signal
    def on_operation_triggered(palette, operation):
        """Handle operation trigger."""
        print(f"Operation triggered: {operation}")
        
        if operation == 'select':
            # Activate selection mode
            if hasattr(canvas_manager, 'set_selection_mode'):
                canvas_manager.set_selection_mode(True)
        
        elif operation == 'select-off':
            # Deactivate selection mode
            if hasattr(canvas_manager, 'set_selection_mode'):
                canvas_manager.set_selection_mode(False)
        
        elif operation == 'lasso':
            # Trigger lasso selection
            if hasattr(canvas_manager, 'start_lasso_selection'):
                canvas_manager.start_lasso_selection()
        
        elif operation == 'undo':
            # Trigger undo
            if hasattr(canvas_manager, 'undo'):
                canvas_manager.undo()
        
        elif operation == 'redo':
            # Trigger redo
            if hasattr(canvas_manager, 'redo'):
                canvas_manager.redo()
    
    ops_palette.connect('operation-triggered', on_operation_triggered)
    
    # Step 7: Store references in canvas manager for later access
    canvas_manager.palette_manager = palette_manager
    canvas_manager.tools_palette = tools_palette
    canvas_manager.ops_palette = ops_palette
    
    # Step 8: Show palettes (optional - they start hidden)
    # palette_manager.show_palette('tools')
    # palette_manager.show_palette('operations')
    
    print("[Example] Palette system integrated successfully!")
    
    return palette_manager


def example_update_undo_redo_state(canvas_manager, can_undo, can_redo):
    """Example of updating undo/redo button states.
    
    Call this after operations that affect undo/redo availability.
    
    Args:
        canvas_manager: ModelCanvasManager with palette references
        can_undo: Whether undo is available
        can_redo: Whether redo is available
    """
    if hasattr(canvas_manager, 'ops_palette'):
        canvas_manager.ops_palette.update_undo_redo_state(can_undo, can_redo)


def example_show_hide_palettes(canvas_manager):
    """Example of showing/hiding palettes programmatically.
    
    Args:
        canvas_manager: ModelCanvasManager with palette_manager reference
    """
    if hasattr(canvas_manager, 'palette_manager'):
        pm = canvas_manager.palette_manager
        
        # Show specific palette
        pm.show_palette('tools')
        
        # Hide specific palette
        pm.hide_palette('operations')
        
        # Toggle palette
        pm.toggle_palette('tools')
        
        # Show all palettes
        pm.show_all()
        
        # Hide all palettes
        pm.hide_all()


def example_keyboard_shortcuts(window, canvas_manager):
    """Example of wiring keyboard shortcuts to palette operations.
    
    Args:
        window: Main window to attach key-press-event
        canvas_manager: ModelCanvasManager with palette references
    """
    
    def on_key_press(widget, event):
        """Handle keyboard shortcuts."""
        from gi.repository import Gdk
        
        ctrl = event.state & Gdk.ModifierType.CONTROL_MASK
        shift = event.state & Gdk.ModifierType.SHIFT_MASK
        
        # Ctrl+P: Place tool
        if ctrl and event.keyval == Gdk.KEY_p:
            if hasattr(canvas_manager, 'tools_palette'):
                canvas_manager.tools_palette.set_tool('place')
            return True
        
        # Ctrl+T: Transition tool
        elif ctrl and event.keyval == Gdk.KEY_t:
            if hasattr(canvas_manager, 'tools_palette'):
                canvas_manager.tools_palette.set_tool('transition')
            return True
        
        # Ctrl+A: Arc tool
        elif ctrl and event.keyval == Gdk.KEY_a:
            if hasattr(canvas_manager, 'tools_palette'):
                canvas_manager.tools_palette.set_tool('arc')
            return True
        
        # Ctrl+S: Select mode
        elif ctrl and event.keyval == Gdk.KEY_s:
            if hasattr(canvas_manager, 'ops_palette'):
                current = canvas_manager.ops_palette.is_selection_mode()
                canvas_manager.ops_palette.set_selection_mode(not current)
            return True
        
        # Ctrl+Z: Undo
        elif ctrl and not shift and event.keyval == Gdk.KEY_z:
            if hasattr(canvas_manager, 'undo'):
                canvas_manager.undo()
            return True
        
        # Ctrl+Shift+Z: Redo
        elif ctrl and shift and event.keyval == Gdk.KEY_z:
            if hasattr(canvas_manager, 'redo'):
                canvas_manager.redo()
            return True
        
        return False
    
    window.connect('key-press-event', on_key_press)


# ==================== ACTUAL INTEGRATION CODE FOR model_canvas_loader.py ====================

"""
To integrate into your actual model_canvas_loader.py, add this to _setup_canvas_manager():

def _setup_canvas_manager(self, drawing_area, overlay_box=None, overlay_widget=None):
    # ... existing setup code ...
    
    # Create and setup palettes if overlay exists
    if overlay_widget:
        from shypn.edit.palette_manager import PaletteManager
        from shypn.edit.tools_palette_new import ToolsPalette
        from shypn.edit.operations_palette_new import OperationsPalette
        
        # Create palette manager
        palette_manager = PaletteManager(overlay_widget)
        
        # Create and register tools palette
        tools_palette = ToolsPalette()
        palette_manager.register_palette(
            tools_palette,
            position=(Gtk.Align.CENTER, Gtk.Align.END)
        )
        
        # Create and register operations palette
        ops_palette = OperationsPalette()
        palette_manager.register_palette(
            ops_palette,
            position=(Gtk.Align.START, Gtk.Align.END)
        )
        
        # Wire signals
        tools_palette.connect('tool-selected', self._on_tool_selected, manager)
        ops_palette.connect('operation-triggered', self._on_operation_triggered, manager)
        
        # Store references
        manager.palette_manager = palette_manager
        manager.tools_palette = tools_palette
        manager.ops_palette = ops_palette
        
        print("[ModelCanvasLoader] Palettes integrated")
    
    # ... rest of setup code ...

# Add signal handlers:

def _on_tool_selected(self, palette, tool_name, manager):
    '''Handle tool selection from palette.'''
    if tool_name:
        manager.set_tool(tool_name)
    else:
        manager.clear_tool()

def _on_operation_triggered(self, palette, operation, manager):
    '''Handle operation trigger from palette.'''
    if operation == 'undo':
        manager.undo()
    elif operation == 'redo':
        manager.redo()
    # ... handle other operations ...
"""
