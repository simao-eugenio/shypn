#!/usr/bin/env python3
"""Topology Panel - Main panel class.

Assembles 4 topology analysis categories:
1. Structural Analysis (P-Invariants, T-Invariants, Siphons, Traps)
2. Graph & Network Analysis (Cycles, Paths, Hubs)
3. Behavioral Analysis (Reachability, Boundedness, Liveness, Deadlocks, Fairness)
4. Biological Analysis (Dependency & Coupling, Regulatory Structure) - For Bio-PNs

Uses CategoryFrame expanders with exclusive expansion between categories.

Author: Simão Eugénio
Date: 2025-10-29
Updated: October 31, 2025 - Added Biological Analysis category
"""
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from shypn.ui.panels.topology.structural_category import StructuralCategory
from shypn.ui.panels.topology.graph_network_category import GraphNetworkCategory
from shypn.ui.panels.topology.behavioral_category import BehavioralCategory
from shypn.ui.panels.topology.biological_category import BiologicalCategory


class TopologyPanel(Gtk.Box):
    """Topology analysis panel with 4 categories.
    
    Architecture:
    - Each category is a CategoryFrame expander
    - Categories can expand/collapse independently
    - Each category contains Analysis Summary + individual analyzer expanders
    - Analyzers run on expansion (with caching)
    - Biological category appears for SBML models and models with test arcs
    """
    
    def __init__(self, model=None, model_canvas=None):
        """Initialize topology panel.
        
        Args:
            model: ShypnModel instance (optional, can be set later)
            model_canvas: ModelCanvas instance for accessing current model
        """
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        self.model = model
        self.model_canvas = model_canvas
        self.knowledge_base = None  # Will be retrieved from model_canvas when needed
        
        # Panel title header (matches other panels: REPORT, EXPLORER, etc.)
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        header_box.set_size_request(-1, 48)  # Fixed 48px height
        header_box.set_margin_start(10)
        header_box.set_margin_end(10)
        
        header_label = Gtk.Label()
        header_label.set_markup("<b>TOPOLOGY</b>")
        header_label.set_halign(Gtk.Align.START)
        header_label.set_valign(Gtk.Align.CENTER)
        header_box.pack_start(header_label, True, True, 0)
        
        # Float button on the far right (icon only)
        self.float_button = Gtk.ToggleButton()
        self.float_button.set_label("⬈")
        self.float_button.set_tooltip_text("Detach panel to floating window")
        self.float_button.set_relief(Gtk.ReliefStyle.NONE)  # Flat button
        self.float_button.set_valign(Gtk.Align.CENTER)
        header_box.pack_end(self.float_button, False, False, 0)
        
        self.pack_start(header_box, False, False, 0)
        
        # Separator
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        self.pack_start(separator, False, False, 0)
        
        # Create scrolled window for all categories
        self.scrolled_window = Gtk.ScrolledWindow()
        self.scrolled_window.set_policy(
            Gtk.PolicyType.AUTOMATIC,
            Gtk.PolicyType.AUTOMATIC
        )
        self.scrolled_window.set_hexpand(True)
        self.scrolled_window.set_vexpand(True)
        
        # Main container for categories
        self.categories_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.categories_box.set_margin_start(5)
        self.categories_box.set_margin_end(5)
        self.categories_box.set_margin_top(5)
        self.categories_box.set_margin_bottom(5)
        
        # Create 4 categories with grouped tables enabled
        self.structural_category = StructuralCategory(
            model_canvas=model_canvas,
            expanded=False,
            use_grouped_table=True  # Enable grouped table mode
        )
        
        self.graph_network_category = GraphNetworkCategory(
            model_canvas=model_canvas,
            expanded=False,
            use_grouped_table=True  # Enable grouped table mode
        )
        
        self.behavioral_category = BehavioralCategory(
            model_canvas=model_canvas,
            expanded=False,
            use_grouped_table=True  # Enable grouped table mode
        )
        
        self.biological_category = BiologicalCategory(
            model_canvas=model_canvas,
            expanded=False,
            use_grouped_table=True  # Enable grouped table mode
        )
        
        # Store categories in list for easy iteration
        self.categories = [
            self.structural_category,
            self.graph_network_category,
            self.behavioral_category,
            self.biological_category,
        ]
        
        # Report panel callback (will be set by report panel)
        self._report_refresh_callback = None
        
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
        
        # Setup exclusive expansion (optional - categories can be independent)
        # Uncomment if you want only one category open at a time:
        # self._setup_exclusive_expansion()
        
        # Show all child widgets (but let parent control panel visibility)
        self.categories_box.show_all()
        self.scrolled_window.show_all()
    
    def _setup_exclusive_expansion(self):
        """Setup exclusive expansion between categories.
        
        When one category is expanded, others are collapsed.
        This is optional - comment out if you want independent expansion.
        """
        # Connect to category frame expansion events
        for category in self.categories:
            category_frame = category.get_widget()
            category_frame._title_event_box.connect(
                'button-press-event',
                self._on_category_clicked,
                category
            )
    
    def _on_category_clicked(self, event_box, event, clicked_category):
        """Handle category expansion/collapse for exclusive expansion.
        
        Args:
            event_box: The EventBox that was clicked
            event: The button press event
            clicked_category: The category that was clicked
        """
        clicked_frame = clicked_category.get_widget()
        
        # If clicking to expand, collapse others
        if not clicked_frame.expanded:
            for category in self.categories:
                if category != clicked_category:
                    category_frame = category.get_widget()
                    if category_frame.expanded:
                        category_frame.set_expanded(False)
        
        return False  # Let default handler also run
    
    def set_model_canvas(self, model_canvas):
        """Set model canvas for all categories.
        
        Args:
            model_canvas: ModelCanvas instance
        """
        self.model_canvas = model_canvas
        
        # Update all categories
        for category in self.categories:
            category.set_model_canvas(model_canvas)
    
    def refresh(self):
        """Refresh all categories.
        
        Called when model changes or tab switches.
        """
        for category in self.categories:
            category.refresh()
    
    def auto_run_all_analyzers(self):
        """Auto-run all analyzers in background when model is loaded.
        
        This triggers all analyzers to run without requiring user to expand them.
        Results are cached and will be displayed instantly when expanders are opened.
        """
        for category in self.categories:
            if hasattr(category, 'auto_run_all_analyzers'):
                category.auto_run_all_analyzers()
    
    def get_knowledge_base(self):
        """Get the knowledge base for the current model.
        
        Returns:
            ModelKnowledgeBase or None: Knowledge base instance
        """
        if self.model_canvas and hasattr(self.model_canvas, 'get_current_knowledge_base'):
            return self.model_canvas.get_current_knowledge_base()
        return None
    
    def get_widget(self):
        """Get the panel widget.
        
        Returns:
            Gtk.Box: This panel (for compatibility)
        """
        return self
    
    def set_report_refresh_callback(self, callback):
        """Set callback to refresh report panel when analyses complete.
        
        Args:
            callback: Function to call when topology analyses update
        """
        self._report_refresh_callback = callback
    
    def notify_report_panel(self):
        """Notify report panel that topology analyses have been updated."""
        if self._report_refresh_callback:
            try:
                self._report_refresh_callback()
            except Exception as e:
                print(f"Warning: Could not refresh report panel: {e}")
    
    def get_all_results(self):
        """Get all analyzer results from all categories.
        
        Returns:
            Dict of {analyzer_name: AnalysisResult} for all 12 analyzers
        """
        all_results = {}
        
        # Get current drawing area
        drawing_area = None
        if self.model_canvas:
            if hasattr(self.model_canvas, 'get_current_document'):
                drawing_area = self.model_canvas.get_current_document()
            elif hasattr(self.model_canvas, 'current_document'):
                drawing_area = self.model_canvas.current_document
        
        if not drawing_area:
            return all_results
        
        # Collect results from all categories
        for category in self.categories:
            if hasattr(category, 'results_cache'):
                category_results = category.results_cache.get(drawing_area, {})
                all_results.update(category_results)
        
        return all_results
    
    def generate_summary_for_report_panel(self):
        """Generate lightweight summary for Report Panel.
        
        Returns:
            Dict with:
            - category: 'Topology'
            - status: 'complete'/'partial'/'error'
            - summary_lines: List of short summary strings
            - statistics: Dict of key metrics
            - formatted_text: Formatted text for display
        """
        from shypn.topology.reporting import TopologySummaryGenerator
        
        # Get all analyzer results
        all_results = self.get_all_results()
        
        if not all_results:
            return {
                'category': 'Topology',
                'status': 'not_analyzed',
                'summary_lines': ['No topology analysis performed yet'],
                'statistics': {},
                'formatted_text': 'ℹ️  No topology analysis performed yet\n\nExpand analyzers in Topology Panel to run analysis.'
            }
        
        # Generate summary
        generator = TopologySummaryGenerator()
        summary = generator.generate_summary(all_results)
        
        # Add formatted text for direct display
        summary['formatted_text'] = generator.format_for_report_panel(summary)
        
        return summary
