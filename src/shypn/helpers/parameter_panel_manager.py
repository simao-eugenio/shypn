#!/usr/bin/env python3
"""Parameter Panel Manager - Universal parameter panel lifecycle management.

Phase 3: Universal Parameter Panel Architecture
================================================

Manages parameter panels that slide UP above sub-palettes in the Swiss Knife Palette.
This solves the variable height problem while providing extensible parameter UI.

ARCHITECTURE:
- Parameter panels slide UP from above the sub-palette area
- Main palette stays CONSTANT 114px height (50px sub-palette + 64px buttons)
- Multiple parameter panels can be registered (per category/tool)
- Only one panel visible at a time (auto-hide previous when switching)

USAGE:
    manager = ParameterPanelManager(main_container, sub_palette_area)
    
    # Register parameter panel factory
    manager.register_parameter_panel('simulate', simulate_loader.create_settings_panel)
    
    # Show panel (slides up with animation)
    manager.show_panel('simulate')
    
    # Hide panel (slides down with animation)
    manager.hide_panel('simulate')
    
    # Toggle panel
    manager.toggle_panel('simulate')

WAYLAND SAFETY:
- No widget reparenting (panels created in place)
- No compositor-breaking operations
- Revealer animations are Wayland-safe
"""

from gi.repository import Gtk, GLib


class ParameterPanelManager:
    """Manages parameter panels that slide above sub-palettes.
    
    Provides universal pattern for tool/category-specific parameter UIs
    while maintaining constant main palette height.
    """
    
    def __init__(self, main_container, sub_palette_area):
        """Initialize parameter panel manager.
        
        Args:
            main_container: Main Swiss Knife palette container (Gtk.Box VERTICAL)
            sub_palette_area: Sub-palette area widget (50px constant height)
        """
        self.main_container = main_container
        self.sub_palette_area = sub_palette_area
        
        # Registry: cat_id -> factory function that returns Gtk.Widget
        self.panel_factories = {}
        
        # Active panels: cat_id -> {'revealer': GtkRevealer, 'widget': panel_widget}
        self.active_panels = {}
        
        # Currently visible panel
        self.current_panel_id = None
        
        # Create parameter panel revealer (sits ABOVE sub_palette_area)
        self._create_parameter_panel_revealer()
    
    def _create_parameter_panel_revealer(self):
        """Create the main parameter panel revealer container.
        
        This revealer sits at the TOP of main_container (above sub_palette_area).
        It holds the currently active parameter panel and slides UP/DOWN.
        """
        # Main revealer for parameter panels (SLIDE_UP animation)
        self.parameter_revealer = Gtk.Revealer()
        self.parameter_revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_UP)
        self.parameter_revealer.set_transition_duration(600)  # Match sub-palette animation
        self.parameter_revealer.set_reveal_child(False)
        self.parameter_revealer.set_visible(True)
        
        # Stack to hold multiple parameter panels (only one visible at a time)
        self.parameter_stack = Gtk.Stack()
        self.parameter_stack.set_transition_type(Gtk.StackTransitionType.NONE)  # Instant switch
        self.parameter_stack.set_hexpand(False)  # Don't expand horizontally
        self.parameter_stack.set_halign(Gtk.Align.CENTER)  # Center the stack
        self.parameter_revealer.add(self.parameter_stack)
        
        # Insert parameter revealer at TOP of main_container (index 0)
        # Order: [parameter_revealer] [sub_palette_area] [category_buttons]
        self.main_container.pack_start(self.parameter_revealer, False, False, 0)
        self.main_container.reorder_child(self.parameter_revealer, 0)
    
    def register_parameter_panel(self, panel_id, factory_function):
        """Register a parameter panel factory.
        
        Factory function should return a Gtk.Widget (typically a revealer or container).
        The widget is created on-demand when first shown.
        
        Args:
            panel_id: Unique identifier for this panel (typically category ID)
            factory_function: Callable that returns Gtk.Widget (panel content)
        """
        self.panel_factories[panel_id] = factory_function
    
    def _ensure_panel_created(self, panel_id):
        """Ensure panel widget is created and added to stack.
        
        Creates panel on-demand using registered factory function.
        
        Args:
            panel_id: Panel identifier
            
        Returns:
            bool: True if panel exists/created, False if factory not registered
        """
        # Already created
        if panel_id in self.active_panels:
            return True
        
        # Check if factory registered
        factory = self.panel_factories.get(panel_id)
        if not factory:
            return False
        
        # Create panel widget
        panel_widget = factory()
        if not panel_widget:
            return False
        
        # Add to stack
        self.parameter_stack.add_named(panel_widget, panel_id)
        panel_widget.show_all()
        
        # Store in active panels
        self.active_panels[panel_id] = {
            'widget': panel_widget
        }
        
        return True
    
    def show_panel(self, panel_id, callback=None):
        """Show parameter panel with slide-up animation.
        
        If another panel is currently visible, it will be hidden first
        (instant switch in stack, then reveal animation).
        
        Args:
            panel_id: Panel identifier to show
            callback: Optional callback(panel_id) called after animation completes
        """
        # Ensure panel is created
        if not self._ensure_panel_created(panel_id):
            if callback:
                callback(panel_id)
            return
        
        # Switch stack to this panel (instant)
        self.parameter_stack.set_visible_child_name(panel_id)
        
        # Reveal with animation
        self.parameter_revealer.set_reveal_child(True)
        self.current_panel_id = panel_id
        
        # Call callback after animation
        if callback:
            GLib.timeout_add(650, lambda: (callback(panel_id), False)[1])
    
    def hide_panel(self, panel_id=None, callback=None):
        """Hide parameter panel with slide-down animation.
        
        Args:
            panel_id: Panel identifier to hide (if None, hides current panel)
            callback: Optional callback(panel_id) called after animation completes
        """
        if panel_id is None:
            panel_id = self.current_panel_id
        
        if not panel_id:
            if callback:
                callback(None)
            return
        
        # Hide with animation
        self.parameter_revealer.set_reveal_child(False)
        
        # Clear current panel IMMEDIATELY (don't wait for animation)
        # This ensures is_panel_visible() returns False right away
        self.current_panel_id = None
        
        # Call callback after animation completes
        if callback:
            GLib.timeout_add(650, lambda: (callback(panel_id), False)[1])
    
    def toggle_panel(self, panel_id, callback=None):
        """Toggle parameter panel visibility.
        
        Args:
            panel_id: Panel identifier to toggle
            callback: Optional callback(panel_id, visible) called after animation
        """
        # If this panel is currently visible, hide it
        if self.current_panel_id == panel_id:
            def on_hide(pid):
                if callback:
                    callback(pid, False)
            self.hide_panel(panel_id, on_hide)
        else:
            # If different panel visible, hide it first (instant)
            if self.current_panel_id:
                self.parameter_revealer.set_reveal_child(False)
            
            # Show new panel
            def on_show(pid):
                if callback:
                    callback(pid, True)
            self.show_panel(panel_id, on_show)
    
    def is_panel_visible(self, panel_id=None):
        """Check if parameter panel is currently visible.
        
        Args:
            panel_id: Panel identifier (if None, checks any panel visible)
            
        Returns:
            bool: True if panel is visible, False otherwise
        """
        if panel_id is None:
            return self.parameter_revealer.get_reveal_child()
        
        return (self.current_panel_id == panel_id and 
                self.parameter_revealer.get_reveal_child())
    
    def hide_all_panels(self, callback=None):
        """Hide all parameter panels (for mode switches, etc.).
        
        Args:
            callback: Optional callback() called after animation completes
        """
        self.hide_panel(callback=callback)


__all__ = ['ParameterPanelManager']
