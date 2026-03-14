#!/usr/bin/env python3
"""Base Panel Loader - Abstract base class for per-document panel instances.

This module defines the OOP architecture for per-document panel management.
All panel loaders inherit from PerDocumentPanelLoader to ensure consistent
behavior across the application.

Architecture:
  - Each document (DrawingArea) has its own panel instances
  - Panel instances are stored in OverlayManager per document
  - Tab switching swaps panel widget instances (no state rebuilding)
  - Complete data isolation between documents

Author: SHYPN Development Team
Date: 2026-01-06
"""
import sys
import logging
from abc import ABC, abstractmethod
from typing import Optional, Any

try:
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk
except Exception as e:
    print(f'ERROR: GTK3 not available in base_panel_loader: {e}', file=sys.stderr)
    sys.exit(1)


class PerDocumentPanelLoader(ABC):
    """Abstract base class for per-document panel loaders.
    
    This class defines the interface and common behavior for all panel loaders
    that follow the per-document instance pattern. Each document gets its own
    panel instance, ensuring complete state isolation.
    
    Design Pattern: Strategy + Factory
    - Strategy: Each panel type implements different behavior via subclasses
    - Factory: Subclasses provide factory methods for creating panel instances
    
    Attributes:
        panel: The GTK panel widget (Gtk.Box or custom widget)
        widget: The root widget to be packed into containers (usually same as panel)
        model: ModelCanvasManager instance for this document
        parent_window: Parent window for dialogs (Wayland-safe)
        logger: Logger instance for this panel
        
    Properties:
        is_attached: Whether panel is currently attached to main window
        is_visible: Whether panel is currently visible
        
    Abstract Methods:
        _create_panel(): Subclasses must implement panel creation logic
        get_panel_name(): Return human-readable panel name
        
    Template Methods:
        initialize(): Template method for panel initialization
        cleanup(): Template method for panel cleanup
        refresh(): Template method for panel refresh
    """
    
    def __init__(self, model: Any, parent_window: Optional[Gtk.Window] = None):
        """Initialize base panel loader.
        
        Args:
            model: ModelCanvasManager instance for this document
            parent_window: Optional parent window for dialogs (Wayland-safe)
        """
        self.model = model
        self.parent_window = parent_window
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Panel widget references (set by subclasses)
        self.panel: Optional[Gtk.Widget] = None
        self.widget: Optional[Gtk.Widget] = None
        
        # State tracking
        self._is_attached = True  # Assume attached by default
        self._is_visible = False
        
        # Initialize panel (template method)
        self.initialize()
    
    # =========================================================================
    # Abstract Methods (must be implemented by subclasses)
    # =========================================================================
    
    @abstractmethod
    def _create_panel(self) -> Gtk.Widget:
        """Create the panel widget.
        
        Subclasses must implement this method to create their specific panel.
        The returned widget should be a Gtk.Box or custom container with all
        UI elements properly configured.
        
        Returns:
            Gtk.Widget: The panel widget
            
        Example:
            ```python
            def _create_panel(self):
                panel = PathwayOperationsPanel(
                    workspace_settings=self.workspace_settings,
                    parent_window=self.parent_window,
                    model_canvas=self.model
                )
                return panel
            ```
        """
        pass
    
    @abstractmethod
    def get_panel_name(self) -> str:
        """Get human-readable panel name.
        
        Returns:
            str: Panel name (e.g., "Pathway Operations", "Dynamic Analyses")
        """
        pass
    
    # =========================================================================
    # Template Methods (can be overridden by subclasses)
    # =========================================================================
    
    def initialize(self) -> None:
        """Initialize the panel (template method).
        
        Default implementation:
        1. Create panel widget via _create_panel()
        2. Set self.widget to panel
        3. Wire float button if it exists
        4. Log initialization
        
        Subclasses can override to add custom initialization logic.
        """
        self.logger.debug(f"Initializing {self.get_panel_name()}")
        
        # Create panel widget
        self.panel = self._create_panel()
        self.widget = self.panel  # Default: widget is the panel itself
        
        # Wire float button if panel has one
        if self.panel and hasattr(self.panel, 'float_button'):
            self.panel.float_button.connect('toggled', self._on_float_toggled)
            self.logger.debug(f"{self.get_panel_name()} float button connected")
        
        # REMOVED: set_no_show_all(True) was preventing matplotlib canvas from showing!
        # The canvas widget inside panels needs show_all() to be realized properly.
        # Instead, we rely on explicit show()/hide() calls in docking logic.
        
        self.logger.debug(f"{self.get_panel_name()} initialized successfully")
    
    def cleanup(self) -> None:
        """Cleanup panel resources (template method).
        
        Called when document is closed. Default implementation destroys
        the panel widget. Subclasses can override to add custom cleanup.
        
        Example:
            ```python
            def cleanup(self):
                # Custom cleanup
                self.stop_background_tasks()
                # Call parent cleanup
                super().cleanup()
            ```
        """
        self.logger.debug(f"Cleaning up {self.get_panel_name()}")
        
        if self.widget:
            # Remove from parent if attached
            parent = self.widget.get_parent()
            if parent:
                parent.remove(self.widget)
            
            # Destroy widget (Wayland-safe)
            try:
                self.widget.destroy()
            except Exception as e:
                self.logger.warning(f"Error destroying widget: {e}")
            
            self.widget = None
            self.panel = None
        
        self.logger.debug(f"{self.get_panel_name()} cleaned up")
    
    def refresh(self) -> None:
        """Refresh panel data (template method).
        
        Called when panel should update its display to reflect current model state.
        Default implementation does nothing - subclasses should override if needed.
        
        Example:
            ```python
            def refresh(self):
                # Update tables, textviews, etc.
                self.panel.refresh_all()
            ```
        """
        pass  # Subclasses can override
    
    # =========================================================================
    # Properties
    # =========================================================================
    
    @property
    def is_attached(self) -> bool:
        """Whether panel is attached to main window (vs. floating)."""
        return self._is_attached
    
    @is_attached.setter
    def is_attached(self, value: bool) -> None:
        """Set attached state."""
        self._is_attached = value
    
    @property
    def is_hanged(self) -> bool:
        """Alias for is_attached (backward compatibility with legacy loaders).
        
        Returns same value as is_attached property.
        """
        return self._is_attached
    
    @is_hanged.setter
    def is_hanged(self, value: bool) -> None:
        """Set attached state via legacy property name."""
        self._is_attached = value
    
    @property
    def is_visible(self) -> bool:
        """Whether panel is currently visible."""
        return self._is_visible
    
    @is_visible.setter
    def is_visible(self, value: bool) -> None:
        """Set visible state."""
        self._is_visible = value
        if self.widget:
            if value:
                self.widget.show_all()
            else:
                self.widget.hide()
    
    # =========================================================================
    # Public Methods
    # =========================================================================
    
    def get_widget(self) -> Optional[Gtk.Widget]:
        """Get the panel widget for packing into containers.
        
        Returns:
            Gtk.Widget: The panel widget, or None if not initialized
        """
        return self.widget
    
    def set_model(self, model: Any) -> None:
        """Update the model reference.
        
        Called when model changes (though with per-document instances,
        this should rarely be needed since each panel has a fixed model).
        
        Args:
            model: New ModelCanvasManager instance
        """
        self.model = model
        self.logger.debug(f"{self.get_panel_name()} model updated")
    
    def show(self) -> None:
        """Show the panel (convenience method).
        
        Wayland-safe implementation that ensures proper widget visibility.
        """
        self.is_visible = True
    
    def hide(self) -> None:
        """Hide the panel (convenience method).
        
        Wayland-safe implementation that ensures proper widget hiding.
        """
        self.is_visible = False
    
    def show_in_stack(self) -> None:
        """Show this panel in the GtkStack (called by Master Palette toggle).
        
        Handles both docked and floating states:
        - If docked (is_hanged=True): Show in stack
        - If floating (is_hanged=False): Show window
        """
        if not hasattr(self, '_stack') or not self._stack:
            self.logger.warning(f"{self.get_panel_name()} has no stack reference")
            return
        
        # Check if panel is docked or floating
        is_docked = getattr(self, 'is_hanged', True)  # Default to docked if property doesn't exist
        
        if is_docked:
            # Panel is docked - show in stack
            if not self._stack.get_visible():
                self._stack.set_visible(True)
            
            if hasattr(self, '_stack_panel_name') and self._stack_panel_name:
                self._stack.set_visible_child_name(self._stack_panel_name)
            
            # Show panel content
            if self.panel:
                self.panel.set_no_show_all(False)
                self.panel.show_all()
            
            # Show parent container if it exists
            if hasattr(self, 'parent_container') and self.parent_container:
                self.parent_container.set_visible(True)
            
            self.logger.debug(f"{self.get_panel_name()} shown in stack")
        else:
            # Panel is floating - show window
            if hasattr(self, 'window') and self.window:
                self.window.show()
                self.logger.debug(f"{self.get_panel_name()} floating window shown")
    
    def hide_in_stack(self) -> None:
        """Hide this panel in the GtkStack (called by Master Palette toggle).
        
        Handles both docked and floating states:
        - If docked (is_hanged=True): Hide in stack
        - If floating (is_hanged=False): Hide window
        """
        # Check if panel is docked or floating
        is_docked = getattr(self, 'is_hanged', True)  # Default to docked if property doesn't exist
        
        if is_docked:
            # Panel is docked - hide content
            if self.panel:
                self.panel.set_no_show_all(True)
                self.panel.hide()
            
            # Hide parent container if it exists
            if hasattr(self, 'parent_container') and self.parent_container:
                self.parent_container.set_visible(False)
            
            self.logger.debug(f"{self.get_panel_name()} hidden in stack")
        else:
            # Panel is floating - hide window
            if hasattr(self, 'window') and self.window:
                self.window.hide()
                self.logger.debug(f"{self.get_panel_name()} floating window hidden")
    
    # =========================================================================
    # Float/Detach Support
    # =========================================================================
    
    def _on_float_toggled(self, button):
        """Handle float button toggle (internal callback).
        
        Args:
            button: Gtk.ToggleButton that was toggled
        """
        # Prevent recursive calls when we update button state programmatically
        if hasattr(self, '_updating_button') and self._updating_button:
            return
        
        is_active = button.get_active()
        if is_active:
            # Button activated → detach/float
            self.detach()
        else:
            # Button deactivated → attach/dock
            if hasattr(self, 'parent_container') and self.parent_container:
                self.hang_on(self.parent_container)
    
    def detach(self):
        """Detach from container and show as floating window.
        
        Creates a floating window if needed and moves panel content to it.
        """
        # Check if already floating
        is_docked = getattr(self, 'is_hanged', True)
        if not is_docked:
            return
        
        # Create window if it doesn't exist
        if not hasattr(self, 'window') or self.window is None:
            from gi.repository import Gdk
            self.window = Gtk.Window()
            self.window.set_title(self.get_panel_name())
            self.window.set_default_size(400, 700)
            self.window.connect('delete-event', self._on_delete_event)
            
            # Set window type hint to keep it visible (utility windows stay on top)
            try:
                self.window.set_type_hint(Gdk.WindowTypeHint.UTILITY)
            except (TypeError, AttributeError, RuntimeError) as e:
                self.logger.debug(f"GTK window type hint not supported on this compositor: {e}")
        
        # Remove from container
        if hasattr(self, 'parent_container') and self.parent_container:
            parent = self.widget.get_parent()
            if parent:
                parent.remove(self.widget)
            self.parent_container.set_visible(False)
        
        # Hide the stack itself when detaching to avoid showing empty container
        if hasattr(self, '_stack') and self._stack:
            self._stack.set_visible(False)
        
        # Add to window
        self.window.add(self.widget)
        
        # Set transient for main window (Wayland compatibility)
        if self.parent_window:
            self.window.set_transient_for(self.parent_window)
        
        # Update state
        self.is_hanged = False
        
        # Update float button state
        if self.panel and hasattr(self.panel, 'float_button'):
            if not self.panel.float_button.get_active():
                self._updating_button = True
                self.panel.float_button.set_active(True)
                self._updating_button = False
        
        # Show window and bring to front
        self.window.show_all()
        
        # Raise window to ensure visibility (works on X11 and some compositors)
        try:
            self.window.present()
        except (TypeError, AttributeError, RuntimeError) as e:
            self.logger.debug(f"GTK window.present() not supported by window manager: {e}")
        
        # Notify callback
        if hasattr(self, 'on_float_callback') and callable(self.on_float_callback):
            self.on_float_callback()
        
        self.logger.debug(f"{self.get_panel_name()} detached to floating window")
    
    def hang_on(self, container):
        """Attach panel to a container (dock).
        
        Args:
            container: Gtk.Container to attach panel to
        """
        # Check if already docked
        is_docked = getattr(self, 'is_hanged', True)
        if is_docked:
            return
        
        # Remove from window
        if hasattr(self, 'window') and self.window:
            self.window.remove(self.widget)
            self.window.hide()
        
        # Clear container first
        for child in container.get_children():
            container.remove(child)
        
        # Remove from current parent if any
        parent = self.widget.get_parent()
        if parent and parent != container:
            parent.remove(self.widget)
        
        # Add to container
        container.pack_start(self.widget, True, True, 0)
        container.set_visible(True)
        
        # Update state
        self.is_hanged = True
        self.parent_container = container
        
        # Update float button state
        if self.panel and hasattr(self.panel, 'float_button'):
            if self.panel.float_button.get_active():
                self._updating_button = True
                self.panel.float_button.set_active(False)
                self._updating_button = False
        
        # Show widget
        self.widget.show_all()
        
        # Notify callback
        if hasattr(self, 'on_attach_callback') and callable(self.on_attach_callback):
            self.on_attach_callback()
        
        self.logger.debug(f"{self.get_panel_name()} attached to container")
    
    def _on_delete_event(self, window, event):
        """Handle window close button (X) - hide and dock instead of destroy.
        
        Args:
            window: The Gtk.Window being closed
            event: The delete event
            
        Returns:
            bool: True to prevent window destruction
        """
        window.hide()
        
        # Dock back to container if available
        if hasattr(self, 'parent_container') and self.parent_container:
            self.hang_on(self.parent_container)
        
        return True  # Prevent destruction
    
    # =========================================================================
    # Protected Helper Methods
    # =========================================================================
    
    def _ensure_wayland_safe(self) -> None:
        """Ensure panel uses Wayland-safe GTK APIs.
        
        This method can be called by subclasses to verify they're not using
        deprecated or Wayland-incompatible APIs.
        
        Checks:
        - No Gtk.Window operations before realize
        - No deprecated Gtk.Stock icons
        - No GdkWindow operations before surface creation
        """
        # This is a placeholder for future checks
        # Subclasses can add specific Wayland safety checks
        pass
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        return (f"<{self.__class__.__name__} "
                f"panel={self.get_panel_name()} "
                f"model={id(self.model) if self.model else None} "
                f"attached={self.is_attached} "
                f"visible={self.is_visible}>")


class PanelLoaderFactory:
    """Factory for creating per-document panel loader instances.
    
    This factory provides a centralized way to create panel loaders with
    consistent configuration. Used by model_canvas_loader when creating
    new documents.
    
    Usage:
        ```python
        factory = PanelLoaderFactory(workspace_settings, parent_window)
        
        # Create panel for a new document
        pathway_loader = factory.create_pathway_panel(canvas_manager)
        analyses_loader = factory.create_analyses_panel(canvas_manager, data_collector)
        ```
    """
    
    def __init__(self, workspace_settings=None, parent_window: Optional[Gtk.Window] = None):
        """Initialize factory.
        
        Args:
            workspace_settings: Optional workspace settings for panels
            parent_window: Optional parent window for dialogs
        """
        self.workspace_settings = workspace_settings
        self.parent_window = parent_window
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def create_pathway_panel(self, model: Any) -> 'PathwayPanelLoader':
        """Create PathwayOperations panel loader.
        
        Args:
            model: ModelCanvasManager for this document
            
        Returns:
            PathwayPanelLoader: Configured panel loader
        """
        from .pathway_panel_loader import PathwayPanelLoader
        return PathwayPanelLoader(
            model=model,
            parent_window=self.parent_window,
            workspace_settings=self.workspace_settings
        )
    
    def create_analyses_panel(self, model: Any, data_collector: Any) -> 'AnalysesPanelLoader':
        """Create DynamicAnalyses panel loader.
        
        Args:
            model: ModelCanvasManager for this document
            data_collector: SimulationDataCollector for this document
            
        Returns:
            AnalysesPanelLoader: Configured panel loader
        """
        from .analyses_panel_loader import AnalysesPanelLoader
        return AnalysesPanelLoader(
            model=model,
            data_collector=data_collector,
            parent_window=self.parent_window
        )
    
    def create_topology_panel(self, model: Any) -> 'TopologyPanelLoader':
        """Create Topology panel loader.
        
        Args:
            model: ModelCanvasManager for this document
            
        Returns:
            TopologyPanelLoader: Configured panel loader
        """
        from .topology_panel_loader import TopologyPanelLoader
        return TopologyPanelLoader(
            model=model,
            parent_window=self.parent_window
        )
    
    def create_viability_panel(self, drawing_area: Any) -> 'ViabilityPanelLoader':
        """Create Viability panel loader.
        
        Args:
            drawing_area: DrawingArea for this document
            
        Returns:
            ViabilityPanelLoader: Configured panel loader
        """
        from .viability_panel_loader import ViabilityPanelLoader
        return ViabilityPanelLoader(drawing_area=drawing_area)
    
    def create_report_panel(self, model: Any, simulation_controller: Any) -> 'ReportPanelLoader':
        """Create Report panel loader.
        
        Args:
            model: ModelCanvasManager for this document
            simulation_controller: SimulationController for this document
            
        Returns:
            ReportPanelLoader: Configured panel loader
        """
        from .report_panel_loader import ReportPanelLoader
        return ReportPanelLoader(
            model=model,
            simulation_controller=simulation_controller
        )


__all__ = ['PerDocumentPanelLoader', 'PanelLoaderFactory']
