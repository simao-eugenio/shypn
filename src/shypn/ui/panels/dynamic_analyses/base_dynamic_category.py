#!/usr/bin/env python3
"""Base class for dynamic analysis categories.

All dynamic analysis categories inherit from BaseDynamicCategory and implement
the _build_content() method to populate their specific visualization views.

Each category contains:
1. Search functionality (for Transitions/Places categories)
2. Matplotlib canvas or metrics display
3. Real-time updates from data collector

Author: Simão Eugénio
Date: 2025-10-29
"""
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

from shypn.ui.category_frame import CategoryFrame


class BaseDynamicCategory:
    """Base class for dynamic analysis category controllers.
    
    Each category is responsible for:
    1. Building its content view (plots, metrics, etc.)
    2. Handling search functionality (if applicable)
    3. Updating visualizations from data collector
    4. Managing canvas/widget lifecycle
    5. Registering with model for cleanup
    
    Subclasses must implement:
    - _build_content(): Create and return the content widget
    - refresh(): Update display when data changes
    """
    
    def __init__(self, title, model=None, data_collector=None, expanded=False):
        """Initialize base dynamic category.
        
        Args:
            title: Category title displayed in expander
            model: ModelCanvasManager for search/cleanup (optional)
            data_collector: SimulationDataCollector for plots (optional)
            expanded: Whether category starts expanded
        """
        self.title = title
        self.model = model
        self.data_collector = data_collector
        self.expanded = expanded
        self.parent_panel = None  # Will be set by DynamicAnalysesPanel
        
        # Widgets
        self.search_entry = None
        self.search_button = None
        self.result_label = None
        self.canvas_container = None
        
        # Panel reference (PlaceRatePanel, TransitionRatePanel, DiagnosticsPanel)
        self.panel = None
        
        # Create category frame
        self.category_frame = CategoryFrame(
            title=self.title,
            expanded=self.expanded
        )
        
        # Build content (implemented by subclasses)
        content_widget = self._build_content()
        if content_widget:
            content_widget.show_all()
            self.category_frame.set_content(content_widget)
    
    def _build_content(self):
        """Build and return the content widget.
        
        Must be implemented by subclasses.
        
        Returns:
            Gtk.Widget: The content to display in this category
        """
        raise NotImplementedError("Subclasses must implement _build_content()")
    
    def _create_search_box(self):
        """Create search controls (entry + button + result label).
        
        Returns:
            Gtk.Box: Container with search controls
        """
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        
        # Search entry + button
        search_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        
        self.search_entry = Gtk.Entry()
        self.search_entry.set_placeholder_text(f"Search {self.title.lower()}...")
        self.search_entry.set_hexpand(True)
        self.search_entry.connect('activate', self._on_search_activated)
        search_box.pack_start(self.search_entry, True, True, 0)
        
        self.search_button = Gtk.Button(label="Search")
        self.search_button.connect('clicked', self._on_search_clicked)
        search_box.pack_start(self.search_button, False, False, 0)
        
        box.pack_start(search_box, False, False, 0)
        
        # Result label
        self.result_label = Gtk.Label()
        self.result_label.set_xalign(0)
        self.result_label.set_selectable(True)
        self.result_label.set_ellipsize(3)  # PANGO_ELLIPSIZE_END
        self.result_label.get_style_context().add_class('dim-label')
        box.pack_start(self.result_label, False, False, 0)
        
        return box
    
    def _on_search_activated(self, entry):
        """Handle Enter key in search entry."""
        self._perform_search()
    
    def _on_search_clicked(self, button):
        """Handle search button click."""
        self._perform_search()
    
    def _perform_search(self):
        """Perform search (implemented by subclasses)."""
        pass
    
    def get_widget(self):
        """Get the category frame widget.
        
        Returns:
            CategoryFrame: The category frame containing this category
        """
        return self.category_frame
    
    def set_model(self, model):
        """Set model and register with it.
        
        Args:
            model: ModelCanvasManager instance
        """
        self.model = model
        
        # Register panel with model if applicable
        if self.panel and hasattr(self.panel, 'register_with_model'):
            self.panel.register_with_model(model)
    
    def set_data_collector(self, data_collector):
        """Set data collector for real-time updates.
        
        Args:
            data_collector: SimulationDataCollector instance
        """
        print(f"[CATEGORY] {self.__class__.__name__}.set_data_collector() called")
        print(f"[CATEGORY]   data_collector={data_collector} (id={id(data_collector)})")
        self.data_collector = data_collector
        
        # Update panel's data collector if applicable
        if self.panel and hasattr(self.panel, 'set_data_collector'):
            print(f"[CATEGORY]   Setting panel.data_collector (panel={self.panel.__class__.__name__})")
            self.panel.set_data_collector(data_collector)
        elif self.panel:
            print(f"[CATEGORY]   Panel {self.panel.__class__.__name__} has no set_data_collector method")
            print(f"[CATEGORY]   Setting panel.data_collector directly")
            self.panel.data_collector = data_collector
        else:
            print(f"[CATEGORY]   WARNING: No panel to update!")
    
    def refresh(self):
        """Refresh the category content.
        
        Should be implemented by subclasses to update their displays.
        Called when data changes.
        """
        pass
    
    def clear_plot(self):
        """Clear plot data and reset display.
        
        Called when simulation is reset to clear old data from plots.
        Delegates to the panel's clear_plot method if available.
        """
        if self.panel and hasattr(self.panel, 'clear_plot'):
            try:
                self.panel.clear_plot()
            except Exception as e:
                print(f"Warning: Could not clear plot in {self.panel.__class__.__name__}: {e}")
    
    def _get_current_drawing_area(self):
        """Get the current drawing area from model.
        
        Returns:
            DrawingArea or None
        """
        if not self.model:
            return None
        
        if hasattr(self.model, 'get_current_document'):
            return self.model.get_current_document()
        elif hasattr(self.model, 'current_document'):
            return self.model.current_document
        
        return None
