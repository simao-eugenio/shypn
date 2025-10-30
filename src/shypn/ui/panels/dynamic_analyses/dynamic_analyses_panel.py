#!/usr/bin/env python3
"""Dynamic Analyses Panel - Main container for real-time visualization.

This panel contains three categories:
1. Transitions - Real-time transition firing rate plots
2. Places - Real-time place token evolution plots
3. Diagnostics - Runtime performance metrics

Author: Simão Eugénio
Date: 2025-10-29
"""
import sys
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from .transitions_category import TransitionsCategory
from .places_category import PlacesCategory
from .diagnostics_category import DiagnosticsCategory


class DynamicAnalysesPanel(Gtk.Box):
    """Main dynamic analyses panel with three categories.
    
    Organizes real-time visualization into categories:
    - Transitions: Firing rate plots with search
    - Places: Token evolution plots with search
    - Diagnostics: Performance metrics
    
    Each category is collapsible and can be expanded independently.
    """
    
    def __init__(self, model=None, data_collector=None):
        """Initialize dynamic analyses panel.
        
        Args:
            model: ModelCanvasManager instance (optional)
            data_collector: SimulationDataCollector instance (optional)
        """
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        self.model = model
        self.data_collector = data_collector
        
        # Report panel callback (will be set by report panel)
        self._report_refresh_callback = None
        
        # Context menu handler (will be set after categories are created)
        self.context_menu_handler = None
        
        # Build UI
        self._build_ui()
    
    def _build_ui(self):
        """Build panel UI with scrolled window and categories."""
        # Scrolled window for categories
        self.scrolled_window = Gtk.ScrolledWindow()
        self.scrolled_window.set_policy(
            Gtk.PolicyType.NEVER,
            Gtk.PolicyType.AUTOMATIC
        )
        
        # Container for categories
        self.categories_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=0
        )
        
        # Create categories
        # Create places category first (needed for transitions locality plotting)
        self.places_category = PlacesCategory(
            model=self.model,
            data_collector=self.data_collector,
            expanded=True  # Expanded by default
        )
        
        # Create transitions category with place panel reference for locality plotting
        self.transitions_category = TransitionsCategory(
            model=self.model,
            data_collector=self.data_collector,
            expanded=True,  # Expanded by default
            place_panel=self.places_category.panel  # Wire place panel for locality
        )
        
        self.diagnostics_category = DiagnosticsCategory(
            model=self.model,
            data_collector=self.data_collector,
            expanded=True  # Expanded by default
        )
        
        # Store categories in list for easy iteration
        self.categories = [
            self.transitions_category,
            self.places_category,
            self.diagnostics_category,
        ]
        
        # Set parent panel reference for all categories (for report notifications)
        for category in self.categories:
            category.parent_panel = self
        
        # Add categories to container
        for category in self.categories:
            self.categories_box.pack_start(
                category.get_widget(),
                False,  # Don't expand to fill
                False,  # Don't fill
                0
            )
        
        # Add container to scrolled window
        self.scrolled_window.add(self.categories_box)
        
        # Add scrolled window to panel
        self.pack_start(self.scrolled_window, True, True, 0)
        
        # Show all child widgets immediately
        for category in self.categories:
            category.get_widget().show_all()
        self.categories_box.show_all()
        self.scrolled_window.show_all()
        
        # Show the panel itself
        self.show_all()
        
        # Create context menu handler after categories exist
        self._setup_context_menu()
    
    def _setup_context_menu(self):
        """Set up context menu handler for plot interactions."""
        try:
            from shypn.analyses import ContextMenuHandler
            
            # Get panel references from categories
            place_panel = self.places_category.panel if self.places_category else None
            transition_panel = self.transitions_category.panel if self.transitions_category else None
            diagnostics_panel = self.diagnostics_category.panel if self.diagnostics_category else None
            
            if place_panel and transition_panel:
                self.context_menu_handler = ContextMenuHandler(
                    place_panel=place_panel,
                    transition_panel=transition_panel,
                    model=self.model,
                    diagnostics_panel=diagnostics_panel
                )
                print(f"[DYNAMIC_ANALYSES] Context menu handler created successfully", file=sys.stderr)
            else:
                print(f"[DYNAMIC_ANALYSES] Warning: Cannot create context menu handler - panels not ready", file=sys.stderr)
        except Exception as e:
            import traceback
            print(f"[DYNAMIC_ANALYSES] Warning: Could not create context menu handler: {e}", file=sys.stderr)
            traceback.print_exc()
    
    def set_model(self, model):
        """Set model for all categories.
        
        Args:
            model: ModelCanvasManager instance
        """
        self.model = model
        
        # Update all categories
        for category in self.categories:
            category.set_model(model)
        
        # Update or create context menu handler
        if self.context_menu_handler:
            self.context_menu_handler.set_model(model)
        else:
            # Context menu handler doesn't exist yet, create it
            self._setup_context_menu()
    
    def set_data_collector(self, data_collector):
        """Set data collector for all categories.
        
        Args:
            data_collector: SimulationDataCollector instance
        """
        self.data_collector = data_collector
        
        # Update all categories
        for category in self.categories:
            category.set_data_collector(data_collector)
    
    def refresh(self):
        """Refresh all categories.
        
        Called when model changes or tab switches.
        """
        for category in self.categories:
            category.refresh()
    
    def get_widget(self):
        """Get the panel widget.
        
        Returns:
            Gtk.Box: This panel (for compatibility)
        """
        return self
    
    def set_report_refresh_callback(self, callback):
        """Set callback to refresh report panel when analyses update.
        
        Args:
            callback: Function to call when dynamic analyses update
        """
        self._report_refresh_callback = callback
    
    def notify_report_panel(self):
        """Notify report panel that dynamic analyses have been updated."""
        if self._report_refresh_callback:
            try:
                self._report_refresh_callback()
            except Exception as e:
                print(f"Warning: Could not refresh report panel: {e}")
    
    def generate_summary_for_report_panel(self):
        """Generate lightweight summary for Report Panel.
        
        Returns:
            Dict with:
            - category: 'Dynamic Analyses'
            - status: 'active'/'idle'/'not_initialized'
            - summary_lines: List of short summary strings
            - statistics: Dict of key metrics
            - formatted_text: Formatted text for display
        """
        status = 'not_initialized'
        summary_lines = []
        statistics = {}
        
        if not self.data_collector:
            summary_lines = ['No simulation data collector initialized']
            status = 'not_initialized'
        else:
            # Check if simulation is running
            # TODO: Add proper status checking when data collector exposes state
            status = 'idle'
            
            # Collect basic statistics
            transitions_count = 0
            places_count = 0
            
            if self.transitions_category.panel:
                # Get number of plotted transitions
                transitions_count = len(getattr(self.transitions_category.panel, 'selected_transitions', []))
            
            if self.places_category.panel:
                # Get number of plotted places
                places_count = len(getattr(self.places_category.panel, 'selected_places', []))
            
            if transitions_count > 0 or places_count > 0:
                summary_lines.append(f'📊 Monitoring {transitions_count} transitions, {places_count} places')
                status = 'active'
            else:
                summary_lines.append('No elements selected for monitoring')
            
            statistics['transitions_count'] = transitions_count
            statistics['places_count'] = places_count
        
        # Format text
        formatted_text = '\n'.join(summary_lines) if summary_lines else 'No dynamic analyses data'
        
        return {
            'category': 'Dynamic Analyses',
            'status': status,
            'summary_lines': summary_lines,
            'statistics': statistics,
            'formatted_text': formatted_text
        }
