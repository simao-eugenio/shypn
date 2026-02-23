"""PetriNetBuilder - Fluent interface for complete Petri net construction.

Provides a builder pattern for constructing complete Petri net models with:
- Places, transitions, and arcs
- Module/compartment organization
- SHPN signal hierarchy features
- Metadata and configuration
- Validation and integrity checking

Example:
    # Build complete model
    model = (PetriNetBuilder()
             .add_place(atp_place)
             .add_transition(commit_transition)
             .add_arc(signal_arc)
             .with_metadata(source="B. subtilis", pathway="sporulation")
             .validate_acyclicity()  # SHPN requirement
             .build())
    
    # Or use fluent construction with builders
    model = (PetriNetBuilder()
             .create_place().with_tokens(100).as_signal_place("ENERGY").done()
             .create_transition().as_immediate().with_priority(10).done()
             .connect_last_to_last(signal_weight=0.17)
             .build())
"""

from typing import List, Optional, Dict, Any, Tuple
from shypn.data.canvas.document_model import DocumentModel
from shypn.netobjs import Place, Transition, Arc
from shypn.builders.place_builder import PlaceBuilder
from shypn.builders.arc_builder import ArcBuilder
from shypn.builders.transition_builder import TransitionBuilder


class PetriNetBuilder:
    """Fluent builder for complete Petri net models.
    
    Supports two construction patterns:
    1. Adding pre-built objects: .add_place(place), .add_transition(t), .add_arc(a)
    2. Fluent nested construction: .create_place().with_tokens(5).done()
    
    SHPN Features:
    - .compute_layers(): Assign hierarchical layers λ via topological sort
    - .validate_acyclicity(): Verify signal flow graph is DAG
    - .compute_commitment_thresholds(): Calculate M_commit = θ + W_s for all signal transitions
    
    Validation:
    - .validate_integrity(): Check referential integrity (arcs connect existing objects)
    - .validate_model(): Run all validation checks
    
    Organization:
    - .create_module(name): Create compartment/module
    - .assign_to_module(obj, module_id): Assign object to module
    """
    
    def __init__(self, name: str = None):
        """Initialize PetriNetBuilder.
        
        Args:
            name: Optional model name (stored in metadata)
        """
        # Core model
        self._model = DocumentModel()
        
        # Model metadata
        self._name = name
        self._metadata = {}
        
        # For fluent nested construction
        self._current_place_builder: Optional[PlaceBuilder] = None
        self._current_transition_builder: Optional[TransitionBuilder] = None
        self._current_arc_builder: Optional[ArcBuilder] = None
        
        # Track last added objects for convenience methods
        self._last_place: Optional[Place] = None
        self._last_transition: Optional[Transition] = None
        self._last_arc: Optional[Arc] = None
    
    # ========== Object Addition (Pre-built) ==========
    
    def add_place(self, place: Place) -> 'PetriNetBuilder':
        """Add an existing place to the model.
        
        Args:
            place: Place object to add
        
        Returns:
            Self for method chaining
        """
        self._model.add_place(place)
        self._last_place = place
        return self
    
    def add_transition(self, transition: Transition) -> 'PetriNetBuilder':
        """Add an existing transition to the model.
        
        Args:
            transition: Transition object to add
        
        Returns:
            Self for method chaining
        """
        self._model.add_transition(transition)
        self._last_transition = transition
        return self
    
    def add_arc(self, arc: Arc) -> 'PetriNetBuilder':
        """Add an existing arc to the model.
        
        Args:
            arc: Arc object to add
        
        Returns:
            Self for method chaining
        """
        self._model.add_arc(arc)
        self._last_arc = arc
        return self
    
    def add_places(self, places: List[Place]) -> 'PetriNetBuilder':
        """Add multiple places at once.
        
        Args:
            places: List of Place objects
        
        Returns:
            Self for method chaining
        """
        for place in places:
            self._model.add_place(place)
            self._last_place = place
        return self
    
    def add_transitions(self, transitions: List[Transition]) -> 'PetriNetBuilder':
        """Add multiple transitions at once.
        
        Args:
            transitions: List of Transition objects
        
        Returns:
            Self for method chaining
        """
        for transition in transitions:
            self._model.add_transition(transition)
            self._last_transition = transition
        return self
    
    def add_arcs(self, arcs: List[Arc]) -> 'PetriNetBuilder':
        """Add multiple arcs at once.
        
        Args:
            arcs: List of Arc objects
        
        Returns:
            Self for method chaining
        """
        for arc in arcs:
            self._model.add_arc(arc)
            self._last_arc = arc
        return self
    
    # ========== Fluent Nested Construction ==========
    
    def create_place(self, name: str = None) -> PlaceBuilder:
        """Start creating a place with fluent builder.
        
        Args:
            name: Optional place name
        
        Returns:
            PlaceBuilder configured to return to this PetriNetBuilder
        
        Example:
            model = (PetriNetBuilder()
                     .create_place("ATP")
                         .with_tokens(100)
                         .as_signal_place("ENERGY")
                         .done()
                     .build())
        """
        # Use document's id_manager for consistent ID generation
        self._current_place_builder = PlaceBuilder(id=name, id_manager=self._model.id_manager)
        # Store reference back to this builder for .done()
        self._current_place_builder._parent_builder = self
        return self._current_place_builder
    
    def create_transition(self, name: str = None) -> TransitionBuilder:
        """Start creating a transition with fluent builder.
        
        Args:
            name: Optional transition name
        
        Returns:
            TransitionBuilder configured to return to this PetriNetBuilder
        
        Example:
            model = (PetriNetBuilder()
                     .create_transition("commit")
                         .as_immediate()
                         .with_priority(10)
                         .done()
                     .build())
        """
        # Use document's id_manager for consistent ID generation
        self._current_transition_builder = TransitionBuilder(name, id_manager=self._model.id_manager)
        self._current_transition_builder._parent_builder = self
        return self._current_transition_builder
    
    def create_arc(self) -> ArcBuilder:
        """Start creating an arc with fluent builder.
        
        Returns:
            ArcBuilder configured to return to this PetriNetBuilder
        
        Example:
            model = (PetriNetBuilder()
                     .create_arc()
                         .from_place("P1")
                         .to_transition("T1")
                         .with_weight(2)
                         .done()
                     .build())
        """
        self._current_arc_builder = ArcBuilder()
        self._current_arc_builder._parent_builder = self
        return self._current_arc_builder
    
    def done_place(self) -> 'PetriNetBuilder':
        """Complete nested place construction and return to builder.
        
        Returns:
            Self for method chaining
        """
        if self._current_place_builder is not None:
            place = self._current_place_builder.build()
            self.add_place(place)
            self._current_place_builder = None
        return self
    
    def done_transition(self) -> 'PetriNetBuilder':
        """Complete nested transition construction and return to builder.
        
        Returns:
            Self for method chaining
        """
        if self._current_transition_builder is not None:
            transition = self._current_transition_builder.build()
            self.add_transition(transition)
            self._current_transition_builder = None
        return self
    
    def done_arc(self) -> 'PetriNetBuilder':
        """Complete nested arc construction and return to builder.
        
        Returns:
            Self for method chaining
        """
        if self._current_arc_builder is not None:
            # Need to resolve references from model
            resolve_refs = self._build_resolve_dict()
            arc = self._current_arc_builder.build(resolve_refs)
            self.add_arc(arc)
            self._current_arc_builder = None
        return self
    
    def _build_resolve_dict(self) -> Dict[str, Any]:
        """Build ID→object mapping for arc resolution.
        
        Returns:
            Dictionary mapping IDs/names to objects
        """
        refs = {}
        for place in self._model.places:
            refs[place.id] = place
            refs[place.name] = place
        for transition in self._model.transitions:
            refs[transition.id] = transition
            refs[transition.name] = transition
        return refs
    
    # ========== Convenience Connection Methods ==========
    
    def connect(self, source_id: str, target_id: str, weight: float = 1.0, 
                arc_type: str = 'normal', **kwargs) -> 'PetriNetBuilder':
        """Create arc connecting two objects by ID.
        
        Args:
            source_id: Source object ID
            target_id: Target object ID
            weight: Arc weight (default 1.0)
            arc_type: Arc type ('normal', 'test', 'inhibitor', 'signal_flow', 'curved')
            **kwargs: Additional arc properties (e.g., signal_weight=0.17)
        
        Returns:
            Self for method chaining
        
        Example:
            .connect("ATP", "commit", arc_type="signal_flow", signal_weight=0.17)
        """
        refs = self._build_resolve_dict()
        source = refs.get(source_id)
        target = refs.get(target_id)
        
        if source is None or target is None:
            raise ValueError(f"Cannot resolve source '{source_id}' or target '{target_id}'")
        
        builder = (ArcBuilder()
                   .from_place(source) if isinstance(source, Place) else ArcBuilder().from_transition(source))
        builder = (builder.to_place(target) if isinstance(target, Place) else builder.to_transition(target))
        builder = builder.with_weight(weight)
        
        # Apply arc type
        if arc_type == 'test':
            builder = builder.as_test()
        elif arc_type == 'inhibitor':
            builder = builder.as_inhibitor()
        elif arc_type == 'signal_flow':
            builder = builder.as_signal_flow()
        elif arc_type == 'curved':
            builder = builder.as_curved()
        
        # Apply additional properties
        if 'signal_weight' in kwargs:
            builder = builder.with_signal_weight(kwargs['signal_weight'])
        if 'threshold' in kwargs:
            builder = builder.with_threshold(kwargs['threshold'])
        
        arc = builder.build()
        return self.add_arc(arc)
    
    def connect_last_to_last(self, weight: float = 1.0, signal_weight: float = None) -> 'PetriNetBuilder':
        """Connect last added place/transition to last added transition/place.
        
        Convenience method for sequential construction.
        
        Args:
            weight: Normal arc weight
            signal_weight: Signal weight (if signal flow arc)
        
        Returns:
            Self for method chaining
        """
        if self._last_place is None or self._last_transition is None:
            raise ValueError("Need both a place and transition to connect")
        
        # Determine direction (last added determines source)
        # If place was added last, connect Place → Transition
        places_index = self._model.places.index(self._last_place) if self._last_place in self._model.places else -1
        transitions_index = self._model.transitions.index(self._last_transition) if self._last_transition in self._model.transitions else -1
        
        if places_index > transitions_index:
            # Place added more recently → Place → Transition
            source, target = self._last_place, self._last_transition
        else:
            # Transition added more recently → Transition → Place
            source, target = self._last_transition, self._last_place
        
        builder = ArcBuilder()
        if isinstance(source, Place):
            builder = builder.from_place(source)
        else:
            builder = builder.from_transition(source)
        
        if isinstance(target, Place):
            builder = builder.to_place(target)
        else:
            builder = builder.to_transition(target)
        
        builder = builder.with_weight(weight)
        
        # Auto-detect signal flow
        if signal_weight is not None or getattr(source, 'is_signal_place', False) or getattr(target, 'is_signal_place', False):
            builder = builder.as_signal_flow()
            if signal_weight is not None:
                builder = builder.with_signal_weight(signal_weight)
        
        arc = builder.build()
        return self.add_arc(arc)
    
    # ========== Module/Compartment Management ==========
    
    def create_module(self, name: str, compartment_id: str = None) -> 'PetriNetBuilder':
        """Create a module/compartment.
        
        Args:
            name: Module display name (e.g., "Cytoplasm")
            compartment_id: SBML compartment ID (if mapping from SBML)
        
        Returns:
            Self for method chaining
        """
        self._model.create_module(name, compartment_id)
        return self
    
    def assign_to_module(self, obj, module_id: str) -> 'PetriNetBuilder':
        """Assign object to a module.
        
        Args:
            obj: Place or Transition object
            module_id: Module identifier
        
        Returns:
            Self for method chaining
        """
        if not isinstance(obj, (Place, Transition)):
            raise TypeError("Can only assign places and transitions to modules")
        
        module = self._model.get_module(module_id)
        if module is None:
            raise ValueError(f"Module '{module_id}' not found")
        
        obj.module_id = module_id
        if isinstance(obj, Place):
            module.places.add(obj)
        elif isinstance(obj, Transition):
            module.transitions.add(obj)
        
        return self
    
    # ========== SHPN Signal Hierarchy ==========
    
    def compute_layers(self) -> Dict[str, int]:
        """Compute hierarchical layers λ for signal places via topological sort.
        
        Algorithm:
        1. Build signal flow graph G_s = (Ψ, F_s)
        2. Topological sort to assign layers
        3. Layer 0: No incoming signal arcs (metabolism)
        4. Layer k: Max incoming layer + 1
        
        Returns:
            Dictionary mapping place_id → layer
        
        Raises:
            ValueError: If signal flow graph contains cycles
        
        Example:
            layers = builder.compute_layers()
            # {'ATP': 0, 'CodY': 1, 'Spo0A': 2}
        """
        from shypn.netobjs.signal_flow_arc import SignalFlowArc
        
        # Find all signal places
        signal_places = [p for p in self._model.places if getattr(p, 'is_signal_place', False)]
        
        if not signal_places:
            return {}  # No signal places
        
        # Build adjacency list for signal flow graph
        # Map: place → list of downstream signal places
        graph = {p.id: [] for p in signal_places}
        in_degree = {p.id: 0 for p in signal_places}
        
        # Build graph from signal flow arcs
        for arc in self._model.arcs:
            if not isinstance(arc, SignalFlowArc):
                continue
            
            # Signal flow arc connects signal place → transition or transition → signal place
            # We need to find signal place → transition → signal place paths
            
            if isinstance(arc.source, Place) and isinstance(arc.target, Transition):
                # Signal place → transition
                source_place = arc.source
                transition = arc.target
                
                if source_place.id not in graph:
                    continue
                
                # Find downstream signal places
                for out_arc in self._model.arcs:
                    if out_arc.source == transition and isinstance(out_arc.target, Place):
                        target_place = out_arc.target
                        if getattr(target_place, 'is_signal_place', False) and target_place.id in graph:
                            graph[source_place.id].append(target_place.id)
                            in_degree[target_place.id] += 1
            
            elif isinstance(arc.source, Transition) and isinstance(arc.target, Place):
                # Transition → signal place
                transition = arc.source
                target_place = arc.target
                
                if target_place.id not in graph:
                    continue
                
                # Find upstream signal places
                for in_arc in self._model.arcs:
                    if isinstance(in_arc, SignalFlowArc) and in_arc.target == transition and isinstance(in_arc.source, Place):
                        source_place = in_arc.source
                        if getattr(source_place, 'is_signal_place', False) and source_place.id in graph:
                            graph[source_place.id].append(target_place.id)
                            in_degree[target_place.id] += 1
        
        # Topological sort (Kahn's algorithm)
        layers = {}
        queue = [pid for pid in in_degree if in_degree[pid] == 0]
        
        for pid in queue:
            layers[pid] = 0  # Layer 0: no incoming arcs
        
        while queue:
            current = queue.pop(0)
            current_layer = layers[current]
            
            for neighbor in graph[current]:
                in_degree[neighbor] -= 1
                
                # Assign layer = max(incoming layers) + 1
                layers[neighbor] = max(layers.get(neighbor, 0), current_layer + 1)
                
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        # Check for cycles
        if len(layers) < len(signal_places):
            raise ValueError("Signal flow graph contains cycles (acyclicity requirement violated)")
        
        # Apply layers to places
        for place in signal_places:
            if hasattr(place, 'layer'):
                place.layer = layers.get(place.id, 0)
            else:
                # Store in properties if no layer attribute
                place.properties['layer'] = layers.get(place.id, 0)
        
        return layers
    
    def validate_acyclicity(self) -> bool:
        """Validate that signal flow graph is acyclic (DAG).
        
        SHPN requirement: Signal flow arcs must form a directed acyclic graph.
        
        Returns:
            True if acyclic, raises ValueError if cycle detected
        
        Raises:
            ValueError: If cycle detected in signal flow graph
        """
        try:
            self.compute_layers()
            return True
        except ValueError as e:
            if "cycles" in str(e):
                raise
            return True  # No signal places, trivially acyclic
    
    def compute_commitment_thresholds(self) -> Dict[Tuple[str, str], float]:
        """Compute commitment thresholds M_commit = θ(t) + W_s for signal transitions.
        
        Formula: M_commit(p_s, t) = θ(t) + W_s((p_s, t))
        
        Where:
        - p_s: Signal place
        - t: Transition
        - θ(t): Enablement threshold (from transition properties)
        - W_s: Signal arc weight (decision quota)
        
        Returns:
            Dictionary mapping (place_id, transition_id) → M_commit
        
        Example:
            thresholds = builder.compute_commitment_thresholds()
            # {('ATP', 'commit'): 2.38}  # θ=2.21 + W_s=0.17
        """
        from shypn.netobjs.signal_flow_arc import SignalFlowArc
        
        thresholds = {}
        
        for arc in self._model.arcs:
            if not isinstance(arc, SignalFlowArc):
                continue
            
            # Get signal place and transition
            if isinstance(arc.source, Place):
                signal_place = arc.source
                transition = arc.target
            else:
                signal_place = arc.target
                transition = arc.source
            
            # Get enablement threshold θ(t)
            theta = transition.properties.get('enablement_threshold', 0.0)
            
            # Get signal weight W_s
            w_s = arc.properties.get('signal_weight', 1.0)
            if hasattr(arc, 'signal_weight'):
                w_s = arc.signal_weight
            
            # Compute commitment threshold
            m_commit = theta + w_s
            
            thresholds[(signal_place.id, transition.id)] = m_commit
        
        return thresholds
    
    # ========== Validation ==========
    
    def validate_integrity(self) -> bool:
        """Validate referential integrity (arcs connect to existing objects).
        
        Returns:
            True if valid
        
        Raises:
            ValueError: If integrity violation found
        """
        for arc in self._model.arcs:
            if arc.source not in self._model.places and arc.source not in self._model.transitions:
                raise ValueError(f"Arc {arc.id} source not in model")
            if arc.target not in self._model.places and arc.target not in self._model.transitions:
                raise ValueError(f"Arc {arc.id} target not in model")
        return True
    
    def validate_model(self) -> bool:
        """Run all validation checks.
        
        Returns:
            True if all validations pass
        
        Raises:
            ValueError: If any validation fails
        """
        self.validate_integrity()
        # Note: acyclicity validation is optional (not all models are SHPN)
        return True
    
    # ========== Metadata and Configuration ==========
    
    def with_name(self, name: str) -> 'PetriNetBuilder':
        """Set model name.
        
        Args:
            name: Model name
        
        Returns:
            Self for method chaining
        """
        self._name = name
        return self
    
    def with_metadata(self, **kwargs) -> 'PetriNetBuilder':
        """Set model metadata.
        
        Args:
            **kwargs: Metadata key-value pairs
        
        Returns:
            Self for method chaining
        
        Example:
            .with_metadata(source="KEGG", pathway="Glycolysis", organism="E. coli")
        """
        self._metadata.update(kwargs)
        return self
    
    # REMOVED: with_simulation_settings() - Simulation parameters are session-specific,
    # set on controller.settings, not saved in model. This method would have required
    # model.simulation_settings which was removed to fix architecture. If you need to
    # set simulation parameters in tests, do so on the SimulationController.settings
    # after creating the model and controller.
    
    # ========== Build ==========
    
    def build(self) -> DocumentModel:
        """Construct final DocumentModel.
        
        Returns:
            DocumentModel with all configured objects and settings
        """
        # Apply metadata
        if self._name:
            self._model.metadata['name'] = self._name
        self._model.metadata.update(self._metadata)
        
        # Validate model
        self.validate_integrity()
        
        return self._model
    
    def __repr__(self) -> str:
        """Return string representation for debugging.
        
        Returns:
            str: Builder state summary
        """
        pc, tc, ac = len(self._model.places), len(self._model.transitions), len(self._model.arcs)
        return f"PetriNetBuilder(places={pc}, transitions={tc}, arcs={ac})"


# Monkey-patch builders to support .done() method returning to PetriNetBuilder
def _add_done_methods():
    """Add .done() methods to PlaceBuilder, TransitionBuilder, ArcBuilder."""
    
    def place_done(self) -> 'PetriNetBuilder':
        """Complete place and return to parent PetriNetBuilder."""
        if hasattr(self, '_parent_builder') and self._parent_builder is not None:
            return self._parent_builder.done_place()
        raise ValueError("No parent PetriNetBuilder")
    
    def transition_done(self) -> 'PetriNetBuilder':
        """Complete transition and return to parent PetriNetBuilder."""
        if hasattr(self, '_parent_builder') and self._parent_builder is not None:
            return self._parent_builder.done_transition()
        raise ValueError("No parent PetriNetBuilder")
    
    def arc_done(self) -> 'PetriNetBuilder':
        """Complete arc and return to parent PetriNetBuilder."""
        if hasattr(self, '_parent_builder') and self._parent_builder is not None:
            return self._parent_builder.done_arc()
        raise ValueError("No parent PetriNetBuilder")
    
    PlaceBuilder.done = place_done
    TransitionBuilder.done = transition_done
    ArcBuilder.done = arc_done

_add_done_methods()
