#!/usr/bin/env python3
"""Viability Assistant Panel - Intelligent Model Improvement Suggester.

This panel is an INTELLIGENT ASSISTANT that helps users improve their models by:
1. Learning patterns from the Knowledge Base (KB)
2. Generating actionable suggestions based on multi-domain analysis
3. Providing Apply/Preview/Undo functionality for suggested changes

MODES:
- Interactive Mode: Analyze specific transition locality when selected
- Batch Mode: Analyze entire model and suggest all improvements

CATEGORIES:
1. Structural Suggestions (topology-based: add arcs, adjust stoichiometry)
2. Biological Suggestions (semantic: map compounds, balance reactions)
3. Kinetic Suggestions (BRENDA-based: query rates, set parameters)
4. Diagnosis & Repair (multi-domain integrated suggestions)

KEY DIFFERENCE FROM REPORT PANEL:
- Report Panel: Shows PROBLEMS (read-only)
- Viability Panel: Suggests SOLUTIONS (actionable)

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
    """Viability Assistant Panel - Suggests model improvements.
    
    Architecture:
    - Observer learns from KB (not just detects issues)
    - Categories show actionable suggestions (not just problems)
    - Interactive mode: Analyze locality when transition selected
    - Batch mode: Analyze entire model with one button
    - Apply/Preview/Undo functionality
    """
    
    def __init__(self, model=None, model_canvas=None):
        """Initialize viability assistant panel.
        
        Args:
            model: ShypnModel instance (optional, can be set later)
            model_canvas: ModelCanvas instance for accessing current model and KB
        """
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        self.model = model
        self.model_canvas = model_canvas
        self.topology_panel = None  # Will be set via set_topology_panel()
        self.analyses_panel = None  # For locality access
        
        # Create intelligent observer (learns patterns and generates suggestions)
        self.observer = ViabilityObserver()
        
        # Track selected locality for interactive mode
        self.selected_transition = None
        self.selected_locality = None
        
        # Build panel header with Analyze All button
        self._build_header()
        
        # Build main content with categories
        self._build_content()
        
        # Show all widgets
        self.show_all()
    
    def _build_header(self):
        """Build panel header with Analyze All button."""
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        header_box.set_size_request(-1, 48)  # Fixed 48px height
        header_box.set_margin_start(10)
        header_box.set_margin_end(10)
        
        # Title label (left)
        header_label = Gtk.Label()
        header_label.set_markup("<b>VIABILITY</b>")
        header_label.set_halign(Gtk.Align.START)
        header_label.set_valign(Gtk.Align.CENTER)
        header_label.set_tooltip_text("Model viability analysis and suggestions")
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
            return
        
        # Expand diagnosis category if collapsed
        if not self.diagnosis_category.category_frame.is_expanded():
            self.diagnosis_category.category_frame.set_expanded(True)
        
        # Set the locality and trigger scan
        self.diagnosis_category.set_selected_locality(
            transition_id=transition_id,
            auto_scan=True
        )
        
    
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
        print(f"[VIABILITY_PANEL] ========== set_model_canvas() CALLED ==========")
        print(f"[VIABILITY_PANEL] model_canvas: {model_canvas}")
        
        self.model_canvas = model_canvas
        
        # Propagate to all categories (CRITICAL!)
        for category in self.categories:
            category.model_canvas = model_canvas
        
        print(f"[VIABILITY_PANEL] About to feed observer with KB data...")
        # Feed initial KB data to observer
        self._feed_observer_with_kb_data()
        print(f"[VIABILITY_PANEL] KB data fed to observer")
    
    def set_drawing_area(self, drawing_area):
        """Set the drawing area this panel is associated with.
        
        Args:
            drawing_area: Gtk.DrawingArea widget for this document
        """
        self.drawing_area = drawing_area
        print(f"[VIABILITY] Set drawing_area: {id(drawing_area)}")
    
    def on_transition_selected(self, transition, locality):
        """INTERACTIVE MODE: Analyze specific transition locality.
        
        Called when user right-clicks transition and selects "Suggest Improvements".
        
        Args:
            transition: Transition object selected by user
            locality: Locality object with input/output places and arcs
        """
        print(f"[VIABILITY] ========== INTERACTIVE MODE ==========")
        print(f"[VIABILITY] Analyzing locality for transition: {transition.id}")
        
        # Store selection
        self.selected_transition = transition
        self.selected_locality = locality
        
        # Get KB
        kb = self.model_canvas.get_current_knowledge_base() if self.model_canvas else None
        if not kb:
            print(f"[VIABILITY] ⚠️ No KB available")
            return
        
        # Build locality-specific knowledge
        locality_knowledge = {
            'mode': 'interactive',
            'transition': transition,
            'transition_id': transition.id,
            'input_places': locality.input_places if locality else [],
            'output_places': locality.output_places if locality else [],
            'input_arcs': locality.input_arcs if locality else [],
            'output_arcs': locality.output_arcs if locality else [],
            'kb': kb
        }
        
        # Add simulation data if available
        if hasattr(self, 'drawing_area') and self.drawing_area:
            controller = self.model_canvas.simulation_controllers.get(self.drawing_area)
            if controller:
                data_collector = getattr(controller, 'data_collector', None)
                if data_collector and data_collector.has_data():
                    time_points, firing_counts = data_collector.get_transition_series(transition.id)
                    locality_knowledge['simulation_data'] = {
                        'transition_firings': firing_counts[-1] if firing_counts else 0,
                        'time_points': len(time_points),
                        'has_data': True
                    }
        
        # Ask observer to generate suggestions for THIS locality
        print(f"[VIABILITY] Requesting suggestions from observer...")
        suggestions = self.observer.generate_suggestions_for_locality(locality_knowledge)
        print(f"[VIABILITY] Received {len(suggestions)} total suggestions")
        
        # Distribute suggestions by category
        structural = [s for s in suggestions if s.get('category') == 'structural']
        biological = [s for s in suggestions if s.get('category') == 'biological']
        kinetic = [s for s in suggestions if s.get('category') == 'kinetic']
        diagnosis = [s for s in suggestions if s.get('category') == 'diagnosis']
        
        print(f"[VIABILITY]   Structural: {len(structural)}")
        print(f"[VIABILITY]   Biological: {len(biological)}")
        print(f"[VIABILITY]   Kinetic: {len(kinetic)}")
        print(f"[VIABILITY]   Diagnosis: {len(diagnosis)}")
        
        # Update categories and expand those with suggestions
        if structural:
            self.structural_category.category_frame.set_expanded(True)
            self.structural_category._on_observer_update(structural)
        
        if biological:
            self.biological_category.category_frame.set_expanded(True)
            self.biological_category._on_observer_update(biological)
        
        if kinetic:
            self.kinetic_category.category_frame.set_expanded(True)
            self.kinetic_category._on_observer_update(kinetic)
        
        if diagnosis:
            self.diagnosis_category.category_frame.set_expanded(True)
            self.diagnosis_category._on_observer_update(diagnosis)
    
    def on_analyze_all(self, button):
        """BATCH MODE: Analyze entire model and suggest all improvements.
        
        Args:
            button: Button that triggered this action
        """
        print(f"[VIABILITY] ========== BATCH MODE ==========")
        print(f"[VIABILITY] Analyzing entire model...")
        
        # Get KB
        kb = self.model_canvas.get_current_knowledge_base() if self.model_canvas else None
        if not kb:
            print(f"[VIABILITY] ⚠️ No KB available")
            return
        
        # Get simulation data if available
        simulation_data = None
        if hasattr(self, 'drawing_area') and self.drawing_area:
            controller = self.model_canvas.simulation_controllers.get(self.drawing_area)
            if controller:
                data_collector = getattr(controller, 'data_collector', None)
                if data_collector and data_collector.has_data():
                    simulation_data = {
                        'has_data': True,
                        'transitions': {},
                        'places': {}
                    }
                    # Collect data for all transitions
                    for trans_id in kb.transitions.keys():
                        time_points, firing_counts = data_collector.get_transition_series(trans_id)
                        simulation_data['transitions'][trans_id] = {
                            'firings': firing_counts[-1] if firing_counts else 0
                        }
        
        # Ask observer to generate ALL suggestions
        print(f"[VIABILITY] Requesting all suggestions from observer...")
        all_suggestions = self.observer.generate_all_suggestions(kb, simulation_data)
        
        # all_suggestions is dict: {'structural': [...], 'biological': [...], ...}
        total = sum(len(suggestions) for suggestions in all_suggestions.values())
        print(f"[VIABILITY] Generated {total} total suggestions")
        
        # Distribute to categories
        for category_name, suggestions in all_suggestions.items():
            print(f"[VIABILITY]   {category_name}: {len(suggestions)} suggestions")
            category = self._get_category_by_name(category_name)
            if category and suggestions:
                # Expand BEFORE updating so the UI update happens
                category.category_frame.set_expanded(True)
                category._on_observer_update(suggestions)
    
    def _get_category_by_name(self, name):
        """Get category instance by name.
        
        Args:
            name: Category name ('structural', 'biological', 'kinetic', 'diagnosis')
            
        Returns:
            Category instance or None
        """
        category_map = {
            'structural': self.structural_category,
            'biological': self.biological_category,
            'kinetic': self.kinetic_category,
            'diagnosis': self.diagnosis_category
        }
        return category_map.get(name)
    
    def on_simulation_complete(self):
        """Called when simulation completes.
        
        Simply records simulation data in observer for future suggestion generation.
        Does NOT automatically generate suggestions (user must click Analyze All or select transition).
        """
        print(f"[VIABILITY] ========== on_simulation_complete() CALLED ==========")
        
        if not self.model_canvas:
            print(f"[VIABILITY] ⚠️ No model_canvas")
            return
        
        try:
            # Get the correct controller for this panel's drawing_area
            if not hasattr(self, 'drawing_area') or not self.drawing_area:
                print(f"[VIABILITY] ⚠️ No drawing_area set")
                return
            
            # Get controller from model_canvas.simulation_controllers
            controller = self.model_canvas.simulation_controllers.get(self.drawing_area)
            print(f"[VIABILITY] controller: {controller}")
            if not controller:
                print(f"[VIABILITY] ⚠️ No controller for this drawing_area")
                return
            
            data_collector = getattr(controller, 'data_collector', None)
            print(f"[VIABILITY] data_collector: {data_collector}")
            if not data_collector or not data_collector.has_data():
                print(f"[VIABILITY] ⚠️ No data_collector or no data")
                return
            
            kb = self.model_canvas.get_current_knowledge_base()
            if not kb:
                print(f"[VIABILITY] ⚠️ No KB")
                return
            
            # Simply record that simulation data is available
            # Observer will use this when generating suggestions
            print(f"[VIABILITY] ✅ Simulation data available")
            print(f"[VIABILITY] Data points: {len(data_collector.time_points) if hasattr(data_collector, 'time_points') else 'unknown'}")
            print(f"[VIABILITY] → User can now click 'Analyze All' or select a transition for suggestions")
            
        except Exception as e:
            print(f"[ViabilityPanel] Error in on_simulation_complete: {e}")
            import traceback
            traceback.print_exc()
    
    def _feed_observer_with_kb_data(self):
        """Feed observer with current Knowledge Base data.
        
        This allows the observer to evaluate rules immediately instead of
        waiting for events to occur.
        """
        print(f"[VIABILITY_OBSERVER] ========== _feed_observer_with_kb_data() CALLED ==========")
        print(f"[VIABILITY_OBSERVER] model_canvas: {self.model_canvas}")
        
        if not self.model_canvas:
            print(f"[VIABILITY_OBSERVER] ⚠️ No model_canvas - cannot feed observer")
            return
        
        try:
            kb = self.model_canvas.get_current_knowledge_base()
            print(f"[VIABILITY_OBSERVER] KB: {kb}")
            if not kb:
                print(f"[VIABILITY_OBSERVER] ⚠️ No KB available")
                return
            
            print(f"[VIABILITY_OBSERVER] KB has:")
            print(f"[VIABILITY_OBSERVER]   places: {len(kb.places) if hasattr(kb, 'places') else 0}")
            print(f"[VIABILITY_OBSERVER]   transitions: {len(kb.transitions) if hasattr(kb, 'transitions') else 0}")
            print(f"[VIABILITY_OBSERVER]   arcs: {len(kb.arcs) if hasattr(kb, 'arcs') else 0}")
            print(f"[VIABILITY_OBSERVER]   compounds: {len(kb.compounds) if hasattr(kb, 'compounds') else 0}")
            print(f"[VIABILITY_OBSERVER]   reactions: {len(kb.reactions) if hasattr(kb, 'reactions') else 0}")
            
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
            print(f"[VIABILITY_OBSERVER] ✅ Event recorded")
        except Exception as e:
            import traceback
            print(f"[VIABILITY_OBSERVER] ❌ Error feeding KB data to observer: {e}")
            traceback.print_exc()
    
    def refresh_all(self):
        """Refresh all categories.
        
        Called when model changes or KB updates.
        """
        print(f"[VIABILITY_PANEL] ========== refresh_all() CALLED ==========")
        
        # Re-feed observer with updated KB data
        self._feed_observer_with_kb_data()
        
        # Refresh expanded categories
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
    
    def add_object_for_analysis(self, obj):
        """Add a place or transition to viability analysis (from context menu).
        
        
        This method is called when user right-clicks an object and selects
        "Add to Viability Analysis".
        
        Args:
            obj: Place or Transition object to analyze
        """
        from shypn.netobjs import Place, Transition
        
        print(f"[VIABILITY_PANEL] add_object_for_analysis called with: {obj.id} (type: {type(obj).__name__})")
        
        # Determine which category to expand and highlight
        if isinstance(obj, Place):
            # Biological category handles places
            for category in self.categories:
                if hasattr(category, '__class__') and 'Biological' in category.__class__.__name__:
                    # Expand the category
                    category.category_frame.set_expanded(True)
                    print(f"[VIABILITY_PANEL] Added place {obj.id} to Biological category")
                    break
        
        elif isinstance(obj, Transition):
            # Structural and Kinetic categories handle transitions
            # Expand both and refresh
            for category in self.categories:
                if hasattr(category, '__class__'):
                    class_name = category.__class__.__name__
                    if 'Structural' in class_name or 'Kinetic' in class_name:
                        category.category_frame.set_expanded(True)
                        print(f"[VIABILITY_PANEL] Added transition {obj.id} to {class_name}")
                    # Also add to Diagnosis category's locality listbox
                    elif 'Diagnosis' in class_name:
                        category.category_frame.set_expanded(True)
                        print(f"[VIABILITY_PANEL] Found Diagnosis category, calling add_transition_for_analysis...")
                        # Add transition to the locality listbox and select it
                        if hasattr(category, 'add_transition_for_analysis'):
                            category.add_transition_for_analysis(obj)
                            print(f"[VIABILITY_PANEL] Successfully called add_transition_for_analysis for {obj.id}")
                        else:
                            print(f"[VIABILITY_PANEL] ERROR: Diagnosis category missing add_transition_for_analysis method!")
                        print(f"[VIABILITY_PANEL] Added transition {obj.id} to Diagnosis category listbox")


