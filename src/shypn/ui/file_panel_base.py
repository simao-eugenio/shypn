#!/usr/bin/env python3
"""File Panel Base - Abstract base class for file panel.

Provides common UI loading and widget management infrastructure.
Follows the same pattern as TopologyPanelBase for consistency.

Author: Simão Eugénio
Date: 2025-10-22
"""

import sys
from abc import ABC, abstractmethod
from pathlib import Path

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk


class FilePanelBase(ABC):
    """Abstract base class for File Panel.
    
    Provides:
    - UI file loading (skeleton pattern)
    - Widget reference management
    - Window and content separation
    - Float/detach support
    - GtkStack integration
    
    Subclasses must implement:
    - _init_widgets(): Get widget references from builder
    - _connect_signals(): Connect widget signals to handlers
    """
    
    def __init__(self, ui_path=None):
        """Initialize file panel base.
        
        Args:
            ui_path: Optional path to UI file (defaults to ui/panels/file_panel_v2.ui)
        """
        # Determine UI path
        if ui_path is None:
            current_dir = Path(__file__).parent
            project_root = current_dir.parent.parent.parent
            ui_path = project_root / 'ui' / 'panels' / 'file_panel_v3.ui'
        
        self.ui_path = Path(ui_path)
        
        # GTK components
        self.builder = Gtk.Builder()
        self.window = None  # Panel window
        self.content = None  # Content widget
        self.main_window = None  # Reference to main window
        self.palette_widget = None  # Reference to Master Palette widget
        
        # State tracking
        self.is_loaded = False  # Track if load() has been called
    
    def load(self):
        """Load UI from XML file - panel stays in its own window.
        
        SIMPLIFIED ARCHITECTURE:
        - Panel content stays in panel window (no reparenting initially)
        - Panel responds to show/hide signals from main app
        - No premature widget tree modifications = No Error 71!
        """
        if not self.ui_path.exists():
            raise FileNotFoundError(f"UI file not found: {self.ui_path}")
        
        try:
            # Load UI file
            self.builder.add_from_file(str(self.ui_path))
            
            # Get main widgets
            self.window = self.builder.get_object('file_panel_window')
            self.content = self.builder.get_object('file_panel_content')
            
            if not self.window or not self.content:
                raise RuntimeError("Required widgets not found in UI file")
            
            # Panel content stays in its own window - no reparenting
            print(f"[LOAD] File Panel loaded (content stays in panel window)", file=sys.stderr)
            
            # Connect window delete event
            self.window.connect('delete-event', self._on_window_delete)
            
            # Initialize subclass-specific widgets
            self._init_widgets()
            
            # Connect signals
            self._connect_signals()
            
            # Hide window by default (will be shown when toggled)
            self.window.set_visible(False)
            
            # Mark as loaded
            self.is_loaded = True
            print(f"[LOAD] File Panel load() complete, is_loaded=True", file=sys.stderr)
            
        except Exception as e:
            print(f"Error loading file panel UI: {e}", file=sys.stderr)
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
    
    # ===============================
    # Panel Control Methods
    # ===============================
    
    def set_palette_parent(self, palette_widget):
        """Set the Master Palette widget as parent for positioning.
        
        Args:
            palette_widget: The Master Palette container widget
        """
        self.palette_widget = palette_widget
        
        # Get the toplevel window containing the palette
        if palette_widget:
            self.main_window = palette_widget.get_toplevel()
    
    def _on_window_delete(self, window, event):
        """Handle window delete event - hide instead of destroy.
        
        Args:
            window: The window being closed
            event: The delete event
            
        Returns:
            True to prevent window destruction
        """
        # Just hide the window instead of destroying it
        # This prevents Error 71 and allows re-showing later
        window.hide()
        return True  # Prevent destruction
    
    # ========================================================================
    # PHASE 4: GtkStack Integration Methods
    # New architecture: Panels live in GtkStack, controlled by Master Palette
    # ========================================================================
    
    def add_to_stack(self, stack, container, panel_name='files'):
        """Add panel content to a GtkStack container (Phase 4: new architecture).
        
        Args:
            stack: GtkStack widget that will contain all panels
            container: GtkBox container within the stack for this panel
            panel_name: Name identifier for this panel in the stack ('files')
        """
        if self.window is None:
            self.load()
        
        # Extract content from window
        current_parent = self.content.get_parent()
        if current_parent == self.window:
            self.window.remove(self.content)
        elif current_parent and current_parent != container:
            current_parent.remove(self.content)
        
        # Add content to stack container
        if self.content.get_parent() != container:
            container.add(self.content)
        
        # Mark as hanged in stack mode (skeleton pattern)
        self.is_hanged = True
        self.parent_container = container
        self._stack = stack
        self._stack_panel_name = panel_name
        
        # Hide window (not needed in stack mode)
        if self.window:
            self.window.hide()
        
        print(f"[STACK] FilePanel content added to stack container '{panel_name}'", file=sys.stderr)
    
    def show_in_stack(self):
        """Show this panel in the GtkStack (Phase 4: Master Palette control).
        
        WAYLAND FIX: Don't use show_all() - it causes Error 71 (Protocol error).
        Instead, explicitly show widgets that need to be visible.
        """
        print(f"[STACK] FilePanel show_in_stack() called", file=sys.stderr)
        
        if not hasattr(self, '_stack') or not self._stack:
            print(f"[STACK] WARNING: FilePanel not added to stack yet", file=sys.stderr)
            return
        
        # Make stack visible
        if not self._stack.get_visible():
            self._stack.set_visible(True)
        
        # Set this panel as active child
        self._stack.set_visible_child_name(self._stack_panel_name)
        
        # WAYLAND FIX: Use show() instead of show_all()
        if self.content:
            self.content.set_no_show_all(False)  # Re-enable show_all
            self.content.show()  # Show just the container (not show_all!)
        
        # Make container visible too
        if self.parent_container:
            self.parent_container.set_visible(True)
        
        print(f"[STACK] FilePanel now visible in stack", file=sys.stderr)
    
    def hide_in_stack(self):
        """Hide this panel in the GtkStack (Phase 4: Master Palette control)."""
        print(f"[STACK] FilePanel hide_in_stack() called", file=sys.stderr)
        
        # Hide the content using no_show_all to prevent show_all from revealing it
        if self.content:
            self.content.set_no_show_all(True)
            self.content.hide()
        
        # Hide container too
        if self.parent_container:
            self.parent_container.set_visible(False)
        
        print(f"[STACK] FilePanel hidden in stack (content remains for fast re-show)", file=sys.stderr)
    
    # ========================================================================
    # Float/Detach Support (Skeleton Pattern)
    # ========================================================================
    
    def detach(self):
        """Detach panel from container and show as floating window.
        
        Skeleton pattern: synchronous, simple state flag.
        """
        
        if not hasattr(self, 'is_hanged') or not self.is_hanged:
            pass
            return
        
        # Remove content from container
        if self.parent_container:
            self.parent_container.remove(self.content)
            self.parent_container.set_visible(False)  # Hide empty container
        
        # Hide the stack if this was the active panel
        if hasattr(self, '_stack') and self._stack:
            self._stack.set_visible(False)
        
        # Add content to window
        self.window.add(self.content)
        
        # Update state
        self.is_hanged = False
        
        # Update float button state (if it exists)
        if hasattr(self, 'float_button') and self.float_button:
            self._updating_button = True
            self.float_button.set_active(True)
            self._updating_button = False
        
        # Show floating window
        self.window.show_all()
        
    
    def float(self):
        """Alias for detach() - make panel float as separate window."""
        self.detach()
    
    def hang_on(self, container):
        """Attach panel to container (opposite of detach).
        
        Args:
            container: GtkBox or container to attach to
        """
        
        if hasattr(self, 'is_hanged') and self.is_hanged:
            pass
            return
        
        # Hide floating window
        self.window.hide()
        
        # Remove content from window
        self.window.remove(self.content)
        
        # Add content to container
        container.pack_start(self.content, True, True, 0)
        container.set_visible(True)  # Show container with content
        
        # Update state and references
        self.is_hanged = True
        self.parent_container = container
        
        # Update float button state (if it exists)
        if hasattr(self, 'float_button') and self.float_button:
            self._updating_button = True
            self.float_button.set_active(False)
            self._updating_button = False
        
        # Show the stack if available
        if hasattr(self, '_stack') and self._stack:
            self._stack.set_visible(True)
            if hasattr(self, '_stack_panel_name'):
                self._stack.set_visible_child_name(self._stack_panel_name)
        
    
    def attach_to(self, container):
        """Alias for hang_on() - attach panel to container."""
        self.hang_on(container)


__all__ = ['FilePanelBase']
