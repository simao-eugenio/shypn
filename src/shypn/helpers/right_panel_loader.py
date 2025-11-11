#!/usr/bin/env python3
"""Right Panel Loader/Controller.

This module is responsible for loading and managing the right Dynamic Analyses panel.
The panel uses a modern OOP architecture with CategoryFrame expanders instead of tabs.

The panel can exist in two states:
  - Detached: standalone floating window
  - Attached: content embedded in main window container (extreme right)
"""
import os
import sys

try:
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk, GLib
except Exception as e:
    print('ERROR: GTK3 not available in right_panel loader:', e, file=sys.stderr)
    sys.exit(1)

from shypn.ui.panels.dynamic_analyses import DynamicAnalysesPanel


class RightPanelLoader:
    """Loader and controller for the right Dynamic Analyses panel (attachable window)."""
    
    def __init__(self, ui_path=None, data_collector=None):
        """Initialize the right panel loader.
        
        Args:
            ui_path: Optional path to right_panel.ui (deprecated - panel is now code-based)
            data_collector: Optional SimulationDataCollector for plotting panels
        """
        self.ui_path = ui_path  # Kept for compatibility but no longer used
        self.data_collector = data_collector
        self.model = None  # ModelCanvasManager for search functionality
        
        # Window and content
        self.window = None
        self.content = None
        self.float_button = None
        
        # State management
        self.is_hanged = False  # Simple state flag (skeleton pattern)
        self.parent_container = None
        self.parent_window = None  # Track parent window for float button
        self._updating_button = False  # Flag to prevent recursive toggle events
        self.on_float_callback = None  # Callback to notify when panel floats
        self.on_attach_callback = None  # Callback to notify when panel attaches
        
        # Dynamic analyses panel (OOP architecture)
        self.dynamic_analyses_panel = None
        
        # Convenience accessors for backward compatibility
        self.place_panel = None
        self.transition_panel = None
        self.diagnostics_panel = None
        self.context_menu_handler = None
    
    def load(self):
        """Load the panel and return the window.
        
        Returns:
            Gtk.Window: The right panel window.
        """
        # Create window
        self.window = Gtk.Window(title="Dynamic Analyses")
        self.window.set_default_size(400, 600)
        try:
            from gi.repository import Gdk
            self.window.set_type_hint(Gdk.WindowTypeHint.UTILITY)
        except:
            pass  # Not critical if type hint fails
        
        # Create main container (replaces right_panel_content from UI)
        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        # Create header box with title and float button
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        header_box.set_margin_top(8)
        header_box.set_margin_bottom(8)
        header_box.set_margin_start(12)
        header_box.set_margin_end(12)
        
        # Title label on the left
        title_label = Gtk.Label()
        title_label.set_markup('<b>DYNAMIC ANALYSES</b>')
        title_label.set_halign(Gtk.Align.START)
        header_box.pack_start(title_label, True, True, 0)
        
        # Float button on the right (icon only)
        self.float_button = Gtk.ToggleButton()
        self.float_button.set_label("⬈")
        self.float_button.set_tooltip_text("Detach panel to floating window")
        self.float_button.connect('toggled', self._on_float_toggled)
        self.float_button.set_relief(Gtk.ReliefStyle.NONE)  # Flat button
        header_box.pack_end(self.float_button, False, False, 0)
        
        self.content.pack_start(header_box, False, False, 0)
        
        # Add separator
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        self.content.pack_start(separator, False, False, 0)
        
        # Create dynamic analyses panel
        self._setup_dynamic_analyses_panel()
        
        # Add panel to content
        self.content.pack_start(self.dynamic_analyses_panel, True, True, 0)
        
        # Add content to window
        
        # Hide window by default (will be shown when toggled)
        self.window.set_visible(False)
        
        return self.window
    
    def _setup_dynamic_analyses_panel(self):
        """Set up the dynamic analyses panel with CategoryFrame architecture.
        
        Creates the panel with None data_collector initially. The data_collector
        will be set later via set_data_collector() when simulation controller is ready.
        """
        # Create dynamic analyses panel
        self.dynamic_analyses_panel = DynamicAnalysesPanel(
            model=self.model,
            data_collector=self.data_collector
        )
        
        # Set up convenience accessors for backward compatibility
        self.place_panel = self.dynamic_analyses_panel.places_category.panel
        self.transition_panel = self.dynamic_analyses_panel.transitions_category.panel
        self.diagnostics_panel = self.dynamic_analyses_panel.diagnostics_category.panel
        
        # Context menu handler will be created later in recreate_context_menu_handler()
        # after model_canvas_loader is set. This ensures viability panel support.
        self.context_menu_handler = None
        print("[RightPanelLoader] Context menu handler will be created after model_canvas_loader is set")
        
        # Register panels with model if available
        if self.model:
            if hasattr(self.place_panel, 'register_with_model'):
                self.place_panel.register_with_model(self.model)
            if hasattr(self.transition_panel, 'register_with_model'):
                self.transition_panel.register_with_model(self.model)
    
    def recreate_context_menu_handler(self):
        """Recreate context menu handler with current configuration.
        
        Call this after model_canvas_loader is set to enable viability panel support.
        """
        if not hasattr(self, 'model_canvas_loader') or not self.model_canvas_loader:
            print("[RightPanelLoader] Cannot recreate context menu handler - model_canvas_loader not set")
            return
        
        from shypn.analyses import ContextMenuHandler
        self.context_menu_handler = ContextMenuHandler(
            place_panel=self.place_panel,
            transition_panel=self.transition_panel,
            model=self.model,
            diagnostics_panel=self.diagnostics_panel,
            model_canvas_loader=self.model_canvas_loader
        )
        print(f"[RightPanelLoader] Recreated context menu handler with model_canvas_loader: {self.model_canvas_loader}")
        
        # Update the panel's reference too for consistency
        if self.dynamic_analyses_panel:
            self.dynamic_analyses_panel.context_menu_handler = self.context_menu_handler
    
    def set_data_collector(self, data_collector):
        """Set or update the data collector for plotting panels.
        
        This allows setting the data collector after initialization,
        useful when the right panel is created before the simulation controller.
        
        Args:
            data_collector: SimulationDataCollector instance
        """
        self.data_collector = data_collector
        
        # Update dynamic analyses panel
        if self.dynamic_analyses_panel:
            self.dynamic_analyses_panel.set_data_collector(data_collector)
    
    def set_model(self, model):
        """Set the model for search functionality.
        
        This allows setting the model after initialization,
        useful when the right panel is created before the canvas loader.
        
        Args:
            model: ModelCanvasManager instance for searching places/transitions
        """
        self.model = model
        
        # Update dynamic analyses panel
        if self.dynamic_analyses_panel:
            self.dynamic_analyses_panel.set_model(model)
            
            # Update convenience accessor (panel may have recreated handler)
            self.context_menu_handler = self.dynamic_analyses_panel.context_menu_handler
        
        # Also update the handler directly if it exists
        if self.context_menu_handler:
            self.context_menu_handler.set_model(model)
    
    def _on_float_toggled(self, button):
        """Internal callback when float toggle button is clicked."""
        # Prevent recursive calls when we update the button state programmatically
        if self._updating_button:
            return
            
        is_active = button.get_active()
        if is_active:
            # Button is now active → detach the panel (float)
            self.detach()
        else:
            # Button is now inactive → attach the panel back
            if self.parent_container:
                self.hang_on(self.parent_container)
    
    def detach(self):
        """Detach from container and restore as independent window (skeleton pattern)."""
        
        if not self.is_hanged:
            return
        
        # Remove from container
        if self.parent_container:
            self.parent_container.remove(self.content)
            # Hide the container after unattaching
            self.parent_container.set_visible(False)
        
        # Hide the stack if this was the active panel
        if hasattr(self, '_stack') and self._stack:
            self._stack.set_visible(False)
        
        # Return content to independent window
        self.window.add(self.content)
        
        # Set transient for main window if available
        if self.parent_window:
            self.window.set_transient_for(self.parent_window)
        
        # Update state
        self.is_hanged = False
        
        # Update float button state
        if self.float_button and not self.float_button.get_active():
            self._updating_button = True
            self.float_button.set_active(True)
            self._updating_button = False
        
        # Notify that panel is floating
        if self.on_float_callback:
            self.on_float_callback()
        
        # Show window
        self.window.show_all()
        
    
    def float(self, parent_window=None):
        """Float panel as a separate window (alias for detach for backward compatibility).
        
        Args:
            parent_window: Optional parent window to set as transient.
        """
        if parent_window:
            self.parent_window = parent_window
        self.detach()
    
    def hang_on(self, container):
        """Hang this panel on a container (attach - skeleton pattern).
        
        Args:
            container: Gtk.Box or other container to embed content into.
        """
        
        if self.is_hanged:
            if not self.content.get_visible():
                self.content.show_all()
            # Make sure container is visible when re-showing
            if not container.get_visible():
                container.set_visible(True)
            return
        
        # Hide independent window
        self.window.hide()
        
        # Remove content from window
        self.window.remove(self.content)
        
        # Hang content on container
        container.pack_start(self.content, True, True, 0)
        self.content.show_all()
        
        # Make container visible (it was hidden when detached)
        container.set_visible(True)
        
        self.is_hanged = True
        self.parent_container = container
        
        # Update float button state
        if self.float_button and self.float_button.get_active():
            self._updating_button = True
            self.float_button.set_active(False)
            self._updating_button = False
        
        # Show the stack if available
        if hasattr(self, '_stack') and self._stack:
            self._stack.set_visible(True)
            if hasattr(self, '_stack_panel_name'):
                self._stack.set_visible_child_name(self._stack_panel_name)
        
        # Notify that panel is attached
        if self.on_attach_callback:
            self.on_attach_callback()
        
    
    def attach_to(self, container, parent_window=None):
        """Attach panel to container (alias for hang_on for backward compatibility).
        
        Args:
            container: Gtk.Box or other container to embed content into.
            parent_window: Optional parent window (stored for float button).
        """
        if parent_window:
            self.parent_window = parent_window
        
        self.hang_on(container)
        
    
    def unattach(self):
        """Unattach panel from container (alias for detach for backward compatibility)."""
        self.detach()
    
    def hide(self):
        """Hide the panel (keep hanged but invisible - skeleton pattern)."""
        
        if self.is_hanged and self.parent_container:
            # Hide content while keeping it hanged
            self.content.set_no_show_all(True)  # Prevent show_all from revealing it
            self.content.hide()
        else:
            # Hide floating window
            self.window.hide()
    
    def show(self):
        """Show the panel (reveal if hanged, show window if floating - skeleton pattern)."""
        
        if self.is_hanged and self.parent_container:
            # Re-enable show_all and show content (reveal)
            self.content.set_no_show_all(False)
            self.content.show_all()
        else:
            # Show floating window
            self.window.show_all()
        
        # WAYLAND FIX: Use idle callback to defer hide operation
        GLib.idle_add(_do_hide)
    
    # ========================================================================
    # PHASE 4: GtkStack Integration Methods
    # New architecture: Panels live in GtkStack, controlled by Master Palette
    # ========================================================================
    
    def add_to_stack(self, stack, container, panel_name='analyses'):
        """Add panel content to a GtkStack container (Phase 4: new architecture).
        
        WAYLAND FIX: Don't create window in stack mode - load content directly.
        
        Args:
            stack: GtkStack widget that will contain all panels
            container: GtkBox container within the stack for this panel
            panel_name: Name identifier for this panel in the stack ('analyses')
        """
        
        # Create content if not already created
        if self.content is None:
            # Create main container
            self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
            
            # Create header box with title and float button
            header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
            header_box.set_margin_top(8)
            header_box.set_margin_bottom(8)
            header_box.set_margin_start(12)
            header_box.set_margin_end(12)
            
            # Title label on the left
            title_label = Gtk.Label()
            title_label.set_markup('<b>DYNAMIC ANALYSES</b>')
            title_label.set_halign(Gtk.Align.START)
            header_box.pack_start(title_label, True, True, 0)
            
            # Float button on the right (icon only)
            self.float_button = Gtk.ToggleButton()
            self.float_button.set_label("⬈")
            self.float_button.set_tooltip_text("Detach panel to floating window")
            self.float_button.connect('toggled', self._on_float_toggled)
            self.float_button.set_relief(Gtk.ReliefStyle.NONE)  # Flat button
            header_box.pack_end(self.float_button, False, False, 0)
            
            self.content.pack_start(header_box, False, False, 0)
            
            # Add separator
            separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
            self.content.pack_start(separator, False, False, 0)
            
            # Create dynamic analyses panel
            self._setup_dynamic_analyses_panel()
            
            # Add panel to content
            self.content.pack_start(self.dynamic_analyses_panel, True, True, 0)
        
        # Add content directly to stack container
        if self.content.get_parent() != container:
            current_parent = self.content.get_parent()
            if current_parent:
                current_parent.remove(self.content)
            container.pack_start(self.content, True, True, 0)
        
        # Show all widgets (matching topology panel pattern)
        self.content.show_all()
        
        # Mark as hanged in stack mode
        self.is_hanged = True
        self.parent_container = container
        self._stack = stack
        self._stack_panel_name = panel_name
        
    
    def show_in_stack(self):
        """Show this panel in the GtkStack (Phase 4: Master Palette control)."""
        
        if not hasattr(self, '_stack') or not self._stack:
            return
        
        # Make stack visible
        if not self._stack.get_visible():
            self._stack.set_visible(True)
        
        # Set this panel as active child
        self._stack.set_visible_child_name(self._stack_panel_name)
        
        # Show the container
        if self.parent_container:
            self.parent_container.set_visible(True)
        
        # Show the widget and all children
        if self.content:
            self.content.set_no_show_all(False)
            self.content.show_all()  # Ensure all children are shown
        
    
    def hide_in_stack(self):
        """Hide this panel in the GtkStack (Phase 4: Master Palette control)."""
        
        # Hide the content using no_show_all to prevent show_all from revealing it
        if self.content:
            self.content.set_no_show_all(True)
            self.content.hide()
        
        # Hide container too
        if self.parent_container:
            self.parent_container.set_visible(False)

        


def create_right_panel(ui_path=None, data_collector=None):
    """Convenience function to create and load the right panel loader.
    
    Args:
        ui_path: Optional path to right_panel.ui.
        data_collector: Optional SimulationDataCollector for plotting panels.
        
    Returns:
        RightPanelLoader: The loaded right panel loader instance.
        
    Example:
        # With data collector for plotting
        loader = create_right_panel(data_collector=collector)
        loader.detach(main_window)  # Show as floating
        # or
        loader.attach_to(container)  # Attach to extreme right
    """
    loader = RightPanelLoader(ui_path, data_collector)
    loader.load()
    return loader
