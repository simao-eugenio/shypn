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
from .viability_observer import ViabilityObserver


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
        
        print(f"[ViabilityPanel] __init__() called")
        print(f"  model_canvas: {model_canvas}")
        
        self.model = model
        self.model_canvas = model_canvas
        self.topology_panel = None  # Will be set via set_topology_panel()
        self.analyses_panel = None  # For locality access
        
        # Create intelligent observer (watches ALL application events)
        self.observer = ViabilityObserver()
        print("[ViabilityPanel] Observer created and ready to monitor events")
        
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
            
        # Subscribe categories to observer updates
        self.observer.subscribe('structural', self.structural_category._on_observer_update)
        self.observer.subscribe('biological', self.biological_category._on_observer_update)
        self.observer.subscribe('kinetic', self.kinetic_category._on_observer_update)
        self.observer.subscribe('diagnosis', self.diagnosis_category._on_observer_update)
        print("[ViabilityPanel] Categories subscribed to observer")
        
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
    
    def analyze_locality_for_transition(self, transition_id):
        """Analyze locality for a specific transition (called from context menu).
        
        This is the entry point for the canvas context menu action:
        "Analyze Locality". It switches the Viability panel to show the
        Diagnosis & Repair category focused on the selected transition's locality.
        
        Args:
            transition_id: ID of the transition to analyze
        """
        if not self.diagnosis_category:
            print("[Viability] Cannot analyze locality: Diagnosis category not initialized")
            return
        
        # Expand diagnosis category if collapsed
        if not self.diagnosis_category.category_frame.is_expanded():
            self.diagnosis_category.category_frame.set_expanded(True)
        
        # Set the locality and trigger scan
        self.diagnosis_category.set_selected_locality(
            transition_id=transition_id,
            auto_scan=True
        )
        
        print(f"[Viability] Analyzing locality for transition: {transition_id}")
    
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
    
    def set_model_canvas(self, model_canvas):
        """Update model_canvas reference.
        
        This is called after __init__ when the loader wires the model_canvas.
        We need to propagate it to all categories.
        
        Args:
            model_canvas: ModelCanvasLoader instance
        """
        print(f"[ViabilityPanel] set_model_canvas() called")
        print(f"  model_canvas: {model_canvas}")
        
        self.model_canvas = model_canvas
        
        # Propagate to all categories (CRITICAL!)
        for category in self.categories:
            category.model_canvas = model_canvas
            print(f"  ✓ Updated {category.__class__.__name__}.model_canvas")
        
        # Feed initial KB data to observer
        self._feed_observer_with_kb_data()
    
    def _feed_observer_with_kb_data(self):
        """Feed observer with current Knowledge Base data.
        
        This allows the observer to evaluate rules immediately instead of
        waiting for events to occur.
        """
        if not self.model_canvas:
            return
        
        try:
            kb = self.model_canvas.get_current_knowledge_base()
            if not kb:
                return
            
            # Record KB update event
            self.observer.record_event(
                event_type='kb_updated',
                data={
                    'places': kb.places,
                    'transitions': kb.transitions,
                    'arcs': kb.arcs,
                    'compounds': kb.compounds,
                    'reactions': kb.reactions,
                    'kinetic_parameters': kb.kinetic_parameters,
                    'p_invariants': kb.p_invariants,
                    't_invariants': kb.t_invariants,
                    'siphons': kb.siphons,
                    'liveness_status': kb.liveness_status
                },
                source='viability_panel'
            )
            print("[ViabilityPanel] Fed initial KB data to observer")
        except Exception as e:
            print(f"[ViabilityPanel] Error feeding KB data to observer: {e}")
    
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
