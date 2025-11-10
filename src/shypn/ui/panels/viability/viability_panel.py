#!/usr/bin/env python3
"""Viability Panel - Intelligent Model Repair Assistant.

Organizes inference suggestions into 4 categories:
1. Structural Inference (topology-based: siphons, liveness, P-invariants)
2. Biological Inference (semantic: stoichiometry, compounds, conservation)
3. Kinetic Inference (BRENDA-based: firing rates, Km/Vmax/Kcat)
4. Diagnosis & Repair (multi-domain + locality-aware analysis)

Follows the same architecture as Topology and Report panels:
- Each category is an expandable frame
- Categories can expand/collapse independently
- Supports locality filtering for focused analysis
- Multi-domain suggestions combine all knowledge layers

Author: Simão Eugénio
Date: November 10, 2025
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from .structural_category import StructuralCategory
from .biological_category import BiologicalCategory
from .kinetic_category import KineticCategory
from .diagnosis_category import DiagnosisCategory


class ViabilityPanel(Gtk.Box):
    """Viability analysis panel with 4 inference categories.
    
    Architecture:
    - Each category is a collapsible frame (like Topology panel)
    - Categories scan for issues and suggest fixes
    - Diagnosis category integrates all domains
    - Supports locality filtering from Analyses panel
    """
    
    def __init__(self, model=None, model_canvas=None):
        """Initialize viability panel.
        
        Args:
            model: ShypnModel instance (optional, can be set later)
            model_canvas: ModelCanvas instance for accessing current model and KB
        """
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        self.model = model
        self.model_canvas = model_canvas
        self.topology_panel = None  # Will be set via set_topology_panel()
        self.analyses_panel = None  # For locality access
        
        # Build panel header
        self._build_header()
        
        # Build main content with categories
        self._build_content()
        
        # Show all widgets
        self.show_all()
    
    def _build_header(self):
        """Build panel header (matches REPORT, TOPOLOGY, etc.)."""
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        header_box.set_size_request(-1, 48)  # Fixed 48px height
        header_box.set_margin_start(10)
        header_box.set_margin_end(10)
        
        # Title label (left)
        header_label = Gtk.Label()
        header_label.set_markup("<b>VIABILITY</b>")
        header_label.set_halign(Gtk.Align.START)
        header_label.set_valign(Gtk.Align.CENTER)
        header_box.pack_start(header_label, True, True, 0)
        
        # Float button (right)
        self.float_button = Gtk.ToggleButton()
        self.float_button.set_label("⬈")
        self.float_button.set_tooltip_text("Detach panel to floating window")
        self.float_button.set_relief(Gtk.ReliefStyle.NONE)
        self.float_button.set_valign(Gtk.Align.CENTER)
        header_box.pack_end(self.float_button, False, False, 0)
        
        self.pack_start(header_box, False, False, 0)
        
        # Separator
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        self.pack_start(separator, False, False, 0)
    
    def _build_content(self):
        """Build main content area with categories."""
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
        
        # Create 4 inference categories
        self.structural_category = StructuralCategory(
            model_canvas=self.model_canvas,
            expanded=False
        )
        
        self.biological_category = BiologicalCategory(
            model_canvas=self.model_canvas,
            expanded=False
        )
        
        self.kinetic_category = KineticCategory(
            model_canvas=self.model_canvas,
            expanded=False
        )
        
        # Diagnosis category starts expanded (it's the main one)
        self.diagnosis_category = DiagnosisCategory(
            model_canvas=self.model_canvas,
            expanded=True
        )
        
        # Store categories in list for easy iteration
        self.categories = [
            self.diagnosis_category,     # Main category first
            self.structural_category,
            self.biological_category,
            self.kinetic_category,
        ]
        
        # Set parent panel reference for all categories
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
    
    def set_topology_panel(self, topology_panel):
        """Set reference to topology panel.
        
        Args:
            topology_panel: TopologyPanel instance
        """
        self.topology_panel = topology_panel
        
        # Propagate to categories if needed
        for category in self.categories:
            if hasattr(category, 'set_topology_panel'):
                category.set_topology_panel(topology_panel)
    
    def set_analyses_panel(self, analyses_panel):
        """Set reference to analyses panel (for locality access).
        
        Args:
            analyses_panel: AnalysesPanel instance
        """
        self.analyses_panel = analyses_panel
        
        # Propagate to diagnosis category (it uses localities)
        if hasattr(self.diagnosis_category, 'set_analyses_panel'):
            self.diagnosis_category.set_analyses_panel(analyses_panel)
    
    def set_model(self, model):
        """Update model reference.
        
        Args:
            model: ShypnModel instance
        """
        self.model = model
        
        # Propagate to categories
        for category in self.categories:
            if hasattr(category, 'set_model'):
                category.set_model(model)
    
    def refresh_all(self):
        """Refresh all categories.
        
        Called when model changes or KB updates.
        """
        for category in self.categories:
            if hasattr(category, 'refresh') and category.expander.get_expanded():
                category.refresh()
    
    def get_knowledge_base(self):
        """Get the knowledge base for the current model.
        
        Returns:
            ModelKnowledgeBase: The knowledge base, or None
        """
        if self.model_canvas and hasattr(self.model_canvas, 'get_current_knowledge_base'):
            return self.model_canvas.get_current_knowledge_base()
        return None
