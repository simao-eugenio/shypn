"""Base class for Topology Panel.

Clean OOP architecture:
- Base class handles UI lifecycle and Wayland safety
- Controller subclass handles analyzer coordination
- Minimal code in loader (wrapper only)

Author: Simão Eugénio
Date: 2025-10-20
"""

import sys
from abc import ABC, abstractmethod
from pathlib import Path

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib


class TopologyPanelBase(ABC):
    """Base class for Topology Panel.
    
    Responsibilities:
    - Load UI from XML
    - Manage widget lifecycle (Wayland safe)
    - Handle attach/detach/float operations
    - Coordinate with master palette
    
    NOT responsible for:
    - Analyzer logic (handled by controller subclass)
    - Business logic (handled by analyzers themselves)
    """
    
    def __init__(self, ui_path=None):
        """Initialize topology panel base.
        
        Args:
            ui_path: Optional path to UI file (defaults to ui/panels/topology_panel.ui)
        """
        # Determine UI path
        if ui_path is None:
            current_dir = Path(__file__).parent
            project_root = current_dir.parent.parent.parent
            ui_path = project_root / 'ui' / 'panels' / 'topology_panel.ui'
        
        self.ui_path = Path(ui_path)
        
        # GTK components
        self.builder = Gtk.Builder()
        self.window = None  # Floating window
        self.content = None  # Content widget (shared between window and attached)
        self.float_button = None
        
        # State tracking
        self.is_attached = False
        self.parent_container = None
        self.parent_window = None
        
        # Callbacks
        self.on_float_callback = None
        self.on_attach_callback = None
        
        # Internal state
        self._updating_button = False
    
    def load(self):
        """Load UI from XML file.
        
        WAYLAND SAFE: Proper widget initialization order.
        """
        if not self.ui_path.exists():
            raise FileNotFoundError(f"UI file not found: {self.ui_path}")
        
        try:
            # Load UI file
            self.builder.add_from_file(str(self.ui_path))
            
            # Get main widgets
            self.window = self.builder.get_object('topology_window')
            self.content = self.builder.get_object('topology_content')
            self.float_button = self.builder.get_object('topology_float_button')
            
            if not self.window or not self.content:
                raise RuntimeError("Required widgets not found in UI file")
            
            # Connect float button
            if self.float_button:
                self.float_button.connect('toggled', self._on_float_button_toggled)
            
            # Connect window delete event
            self.window.connect('delete-event', self._on_window_delete)
            
            # Initialize subclass-specific widgets
            self._init_widgets()
            
            # Connect signals
            self._connect_signals()
            
        except Exception as e:
            print(f"Error loading topology panel UI: {e}", file=sys.stderr)
            raise
    
    @abstractmethod
    def _init_widgets(self):
        """Initialize subclass-specific widgets.
        
        Called after base widgets are loaded.
        Subclasses should override to get widget references.
        """
        pass
    
    @abstractmethod
    def _connect_signals(self):
        """Connect subclass-specific signals.
        
        Called after widgets are initialized.
        Subclasses should override to connect button signals, etc.
        """
        pass
    
    def attach_to(self, container, parent_window=None):
        """Attach panel to container.
        
        WAYLAND SAFE: Uses idle callback for deferred reparenting.
        
        Args:
            container: Gtk.Box or other container to embed content
            parent_window: Optional parent window reference
        """
        if self.window is None:
            self.load()
        
        # WAYLAND FIX: Prevent redundant attach
        if self.is_attached and self.parent_container == container:
            print(f"[ATTACH] TopologyPanel already attached, ensuring visibility", file=sys.stderr)
            # Check if content was removed by hide() - if so, re-add it
            if self.content.get_parent() != container:
                print(f"[ATTACH] TopologyPanel content was removed, re-adding to container", file=sys.stderr)
                container.add(self.content)
            container.set_visible(True)
            self.content.set_visible(True)
            self.content.show_all()  # Ensure all children are visible
            return
        
        print(f"[ATTACH] TopologyPanel attach_to() called, is_attached={self.is_attached}", file=sys.stderr)
        
        # Store references
        if parent_window:
            self.parent_window = parent_window
        self.parent_container = container
        
        def _do_attach():
            """Deferred attach operation for Wayland safety."""
            print(f"[ATTACH] TopologyPanel _do_attach() executing", file=sys.stderr)
            try:
                # Extract content from window
                current_parent = self.content.get_parent()
                if current_parent == self.window:
                    self.window.remove(self.content)
                elif current_parent and current_parent != container:
                    current_parent.remove(self.content)
                
                # WAYLAND FIX: Hide window BEFORE reparenting
                if self.window:
                    self.window.hide()
                
                # Add to container
                if self.content.get_parent() != container:
                    container.add(self.content)
                
                # Show container and content
                container.set_visible(True)
                self.content.set_visible(True)
                
                print(f"[ATTACH] TopologyPanel attached successfully, content visible", file=sys.stderr)
                
                # Update float button state
                if self.float_button and self.float_button.get_active():
                    self._updating_button = True
                    self.float_button.set_active(False)
                    self._updating_button = False
                
                self.is_attached = True
                
                # Notify callback
                if self.on_attach_callback:
                    self.on_attach_callback()
                    
            except Exception as e:
                print(f"Warning: Error during topology panel attach: {e}", file=sys.stderr)
            
            return False  # Don't repeat
        
        # WAYLAND FIX: Defer reparenting
        GLib.idle_add(_do_attach)
    
    def float(self, parent_window=None):
        """Float panel as separate window.
        
        WAYLAND SAFE: Uses idle callback for deferred operations.
        
        Args:
            parent_window: Optional parent window to set as transient
        """
        if self.window is None:
            self.load()
        
        # Store parent reference
        if parent_window:
            self.parent_window = parent_window
        
        def _do_float():
            """Deferred float operation for Wayland safety."""
            try:
                # If attached, unattach first
                if self.is_attached:
                    # Remove from container
                    if self.parent_container and self.content.get_parent() == self.parent_container:
                        self.parent_container.remove(self.content)
                    
                    # Return content to window
                    if self.content.get_parent() != self.window:
                        self.window.add(self.content)
                    
                    self.is_attached = False
                    
                    # Hide container
                    if self.parent_container:
                        self.parent_container.set_visible(False)
                
                # WAYLAND FIX: Set transient parent
                parent = parent_window if parent_window else self.parent_window
                if parent:
                    self.window.set_transient_for(parent)
                
                # Update float button state
                if self.float_button and not self.float_button.get_active():
                    self._updating_button = True
                    self.float_button.set_active(True)
                    self._updating_button = False
                
                # Notify callback
                if self.on_float_callback:
                    self.on_float_callback()
                
                # WAYLAND FIX: Ensure content visible before showing window
                self.content.set_visible(True)
                self.window.show_all()
                
            except Exception as e:
                print(f"Warning: Error during topology panel float: {e}", file=sys.stderr)
            
            return False  # Don't repeat
        
        # WAYLAND FIX: Defer float operation
        GLib.idle_add(_do_float)
    
    def hide(self):
        """Hide panel (both attached and floating states).
        
        WAYLAND SAFE: Uses idle callback for deferred operations.
        """
        print(f"[HIDE] TopologyPanel hide() called, is_attached={self.is_attached}", file=sys.stderr)
        
        def _do_hide():
            """Deferred hide operation for Wayland safety."""
            print(f"[HIDE] TopologyPanel _do_hide() executing", file=sys.stderr)
            try:
                if self.is_attached:
                    # CRITICAL: Remove content from container instead of hiding container
                    # All panels share left_dock_area, so hiding container prevents other panels from showing
                    if self.content and self.parent_container:
                        current_parent = self.content.get_parent()
                        if current_parent == self.parent_container:
                            print(f"[HIDE] TopologyPanel removing content from container", file=sys.stderr)
                            self.parent_container.remove(self.content)
                        self.content.set_visible(False)
                        # Don't hide container - other panels might use it
                    print(f"[HIDE] TopologyPanel hidden (attached mode)", file=sys.stderr)
                elif self.window:
                    # Hide floating window
                    self.window.hide()
                    print(f"[HIDE] TopologyPanel hidden (floating mode)", file=sys.stderr)
            except Exception as e:
                print(f"[ERROR] Error during topology panel hide: {e}", file=sys.stderr)
            
            return False  # Don't repeat
        
        # WAYLAND FIX: Defer hide operation
        GLib.idle_add(_do_hide)
    
    def show(self):
        """Show panel in current state (attached or floating)."""
        if self.is_attached:
            if self.parent_container:
                self.parent_container.set_visible(True)
            if self.content:
                self.content.set_visible(True)
        elif self.window:
            self.window.show_all()
    
    def _on_float_button_toggled(self, button):
        """Handle float button toggle.
        
        Args:
            button: The toggle button that was clicked
        """
        if self._updating_button:
            return  # Ignore programmatic changes
        
        is_active = button.get_active()
        
        if is_active:
            # Float the panel
            self.float(self.parent_window)
        else:
            # Attach the panel back
            if self.parent_container and self.parent_window:
                self.attach_to(self.parent_container, self.parent_window)
    
    def _on_window_delete(self, window, event):
        """Handle window close button.
        
        Instead of destroying, we hide and update button state.
        
        Args:
            window: The window being closed
            event: The delete event
            
        Returns:
            True to prevent destruction
        """
        # Hide window
        window.hide()
        
        # Update float button
        if self.float_button and self.float_button.get_active():
            self._updating_button = True
            self.float_button.set_active(False)
            self._updating_button = False
        
        # Notify callback
        if self.on_float_callback:
            self.on_float_callback()
        
        # Prevent destruction
        return True


__all__ = ['TopologyPanelBase']
