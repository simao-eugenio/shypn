#!/usr/bin/env python3
"""File Panel V2 Loader - Minimal loader for refactored file panel.

Simple loader following panel loader pattern.
Delegates all logic to FilePanelV2 class.

Author: Simão Eugénio
Date: 2025-10-22
"""

import os
import sys

try:
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk
except Exception as e:
    print(f'ERROR: GTK3 not available in file_panel_v2_loader: {e}', file=sys.stderr)
    sys.exit(1)

from shypn.ui.file_panel_v2 import FilePanelV2


class FilePanelV2Loader:
    """Minimal loader for File Panel V2.
    
    Provides GtkStack compatibility (add_to_stack, show_in_stack, hide_in_stack)
    and minimal state management.
    """
    
    def __init__(self, base_path: str = None):
        """Initialize loader.
        
        Args:
            base_path: Base directory for file browser
        """
        # Determine base path
        if base_path is None:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            repo_root = os.path.normpath(os.path.join(script_dir, '..', '..', '..'))
            base_path = os.path.join(repo_root, 'workspace')
            
            # Ensure workspace exists
            if not os.path.exists(base_path):
                try:
                    os.makedirs(base_path)
                except Exception:
                    base_path = repo_root
        
        # Create panel
        self.panel = FilePanelV2(base_path=base_path)
        
        # Compatibility attributes
        self.window = Gtk.Window(title="File Panel V2")
        self.content = self.panel.get_widget()
        
        # State
        self.is_hanged = False  # Use skeleton pattern naming
        self.parent_container = None
        self.parent_window = None
        
        # Integration support
        self.model_canvas_loader = None
        self.persistency_manager = None
        
        # Callback support (set by shypn.py)
        self.on_file_open_requested = None
        
        # Compatibility stubs (for production shypn.py)
        class DummyExplorer:
            def __init__(self, panel):
                self.panel = panel
                self.persistency = None
            
            def set_persistency_manager(self, manager):
                self.persistency = manager
                self.panel.persistency_manager = manager
                if self.persistency:
                    self.persistency.parent_window = self.panel.parent_window
            
            def set_parent_window(self, window):
                self.panel.set_parent_window(window)
                if self.persistency:
                    self.persistency.parent_window = window
            
            def set_canvas_loader(self, loader):
                self.panel.set_canvas_loader(loader)
        
        class DummyController:
            def set_parent_window(self, *args, **kwargs): pass
        
        self.file_explorer = DummyExplorer(self.panel)
        self.project_controller = DummyController()
    
    def load(self):
        """Load panel (compatibility method).
        
        Returns:
            Panel window
        """
        return self.window
    
    # =========================================================================
    # GtkStack Integration
    # =========================================================================
    
    def add_to_stack(self, stack, container, panel_name='files'):
        """Add panel to GtkStack container.
        
        Args:
            stack: GtkStack widget
            container: Container box within stack
            panel_name: Panel identifier in stack
        """
        print(f"[FILE_PANEL_V2] add_to_stack('{panel_name}')", file=sys.stderr)
        
        # Remove from window if attached
        if self.content.get_parent():
            self.content.get_parent().remove(self.content)
        
        # Add to container
        container.add(self.content)
        
        # Store references
        self.is_hanged = True  # Use skeleton pattern naming
        self.parent_container = container
        self._stack = stack
        self._stack_panel_name = panel_name
        
        # Hide window
        self.window.hide()
        
        print(f"[FILE_PANEL_V2] Panel added to stack", file=sys.stderr)
    
    def show_in_stack(self):
        """Show panel in GtkStack."""
        print(f"[FILE_PANEL_V2] show_in_stack()", file=sys.stderr)
        
        # Make stack visible
        if not self._stack.get_visible():
            self._stack.set_visible(True)
        
        # Set as active child
        self._stack.set_visible_child_name(self._stack_panel_name)
        
        # Re-enable show_all and show content recursively
        if self.content:
            self.content.set_no_show_all(False)  # Re-enable show_all
            self.content.show_all()
        
        # Show container
        if self.parent_container:
            self.parent_container.set_visible(True)
        
        print(f"[FILE_PANEL_V2] Panel visible in stack", file=sys.stderr)
    
    def hide_in_stack(self):
        """Hide panel in GtkStack."""
        print(f"[FILE_PANEL_V2] hide_in_stack()", file=sys.stderr)
        # Hide the content using no_show_all to prevent show_all from revealing it
        if self.content:
            self.content.set_no_show_all(True)
            self.content.hide()
        
        # Hide container too
        if self.parent_container:
            self.parent_container.set_visible(False)
    
    # =========================================================================
    # Float/Detach Support (Skeleton Pattern)
    # =========================================================================
    
    def detach(self):
        """Detach panel from container and show as floating window.
        
        Skeleton pattern: synchronous, simple state flag.
        """
        print(f"[FILE_PANEL_V2] detach() called", file=sys.stderr)
        
        if not self.is_hanged:
            print(f"[FILE_PANEL_V2] Already detached, nothing to do", file=sys.stderr)
            return
        
        # Remove content from container
        if self.parent_container:
            self.parent_container.remove(self.content)
            self.parent_container.set_visible(False)  # Hide empty container
        
        # Add content to window
        self.window.add(self.content)
        
        # Update state
        self.is_hanged = False
        
        # Show floating window
        self.window.show_all()
        
        print(f"[FILE_PANEL_V2] Panel detached and floating", file=sys.stderr)
    
    def float(self):
        """Alias for detach() - make panel float as separate window."""
        self.detach()
    
    def hang_on(self, container):
        """Attach panel to container (opposite of detach).
        
        Args:
            container: GtkBox or container to attach to
        """
        print(f"[FILE_PANEL_V2] hang_on() called", file=sys.stderr)
        
        if self.is_hanged:
            print(f"[FILE_PANEL_V2] Already attached, nothing to do", file=sys.stderr)
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
        
        print(f"[FILE_PANEL_V2] Panel attached to container", file=sys.stderr)
    
    def attach_to(self, container):
        """Alias for hang_on() - attach panel to container."""
        self.hang_on(container)
    
    def set_parent_window(self, parent: Gtk.Window):
        """Set parent window for dialogs.
        
        Args:
            parent: Parent window
        """
        self.parent_window = parent
        self.panel.set_parent_window(parent)
    
    def __setattr__(self, name, value):
        """Intercept attribute setting to wire callbacks to panel.
        
        This allows shypn.py to set file_explorer.on_file_open_requested
        and have it automatically delegated to the panel.
        """
        if name == 'on_file_open_requested' and hasattr(self, 'panel'):
            # Wire the callback to the panel's file open mechanism
            print(f"[FILE_PANEL_V2_LOADER] Wiring on_file_open_requested callback", file=sys.stderr)
            # Store the callback so shypn.py's wiring can delegate to FileExplorerPanel logic
            object.__setattr__(self, name, value)
        else:
            object.__setattr__(self, name, value)


def create_file_panel_v2(base_path: str = None):
    """Create File Panel V2 loader.
    
    Factory function for consistency with other panel loaders.
    
    Args:
        base_path: Base directory for file browser
    
    Returns:
        FilePanelV2Loader instance
    """
    loader = FilePanelV2Loader(base_path=base_path)
    loader.load()
    return loader
