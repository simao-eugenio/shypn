"""Document Model - Core data structure for Petri net models.

This module defines the DocumentModel class, which represents a complete
Petri net model including places, transitions, arcs, modules, and metadata.
"""

import time
from typing import List, Dict, Optional, Any, Tuple
from shypn.events import EventBus
from shypn.netobjs import Place, Transition, Arc, PetriNetObject, Module
from .id_manager import IDManager, suspend_lifecycle_delegation


class DocumentModel:
    """Manages Petri net objects for a document.
    
    This class provides:
    - Object storage (places, transitions, arcs)
    - Spatial queries (objects at point, in rectangle)
    - Object lifecycle (add, remove)
    - Validation (arc connectivity rules)
    - Collection operations (get all, clear)
    
    The model is independent of viewport and rendering concerns.
    """
    
    def __init__(self):
        """Initialize empty document model."""
        self.places: List[Place] = []
        self.transitions: List[Transition] = []
        self.arcs: List[Arc] = []
        
        # Module collection (modular Bio-PN architecture)
        # Dict mapping module_id → Module object
        self.modules: Dict[str, Module] = {}
        
        # Centralized ID management
        self.id_manager = IDManager()
        
        # View state (zoom and pan position)
        self.view_state = {
            "zoom": 1.0,
            "pan_x": 0.0,
            "pan_y": 0.0
        }
        
        # Simulation settings (for batch mode and recording configuration)
        from shypn.engine.simulation.settings import SimulationSettings
        self.simulation_settings = SimulationSettings()
        
        # Thermodynamic settings (pH, temperature, validation parameters)
        self.thermodynamic_settings = self._get_default_thermodynamic_settings()
        
        # Compound mappings (place_id → compound_id for thermodynamic validation)
        # Format: {"P001": "C00002", "P002": "CHEBI:15422", ...}
        self.compound_mappings: Dict[str, str] = {}
        
        # Model metadata (source, creation date, model type, etc.)
        # Always initialized to ensure metadata is available for all models
        from datetime import datetime
        self.metadata: Dict[str, Any] = {
            "created": datetime.now().isoformat(),
            "source": "manual",  # Can be overwritten by import/load operations
            "model_type": "Petri Net"  # Can be updated based on object types
        }
    
    @staticmethod
    def _get_default_thermodynamic_settings() -> dict:
        """Get default thermodynamic settings (biochemical standard state).
        
        Returns:
            Dictionary with pH, temperature, ionic_strength, tolerance, enable_validation
        """
        return {
            "ph": 7.0,                      # Biochemical standard pH
            "temperature": 298.15,          # 25°C in Kelvin
            "ionic_strength": 0.1,          # 0.1 M (physiological)
            "tolerance": 0.5,               # ±50% (≈±1 order of magnitude)
            "enable_validation": True,      # Validate by default
            "preset": "biochemical_standard"  # Track which preset is active
        }
    
    # ============================================================================
    # Object Creation
    # ============================================================================
    
    def create_place(self, x: float, y: float, label: str = "", 
                     compound_id: Optional[str] = None,
                     auto_fetch_thermodynamics: bool = True) -> Place:
        """Create a new place at the given position.
        
        Args:
            x: X coordinate in world space
            y: Y coordinate in world space
            label: Optional label for the place
            compound_id: Optional KEGG/ChEBI ID for thermodynamic enrichment
            auto_fetch_thermodynamics: If True and compound_id provided, fetch
                                       thermodynamic properties from local database
            
        Returns:
            The created Place object with thermodynamic properties (if available)
            
        Example:
            >>> # Manual creation without enrichment
            >>> place = document.create_place(100, 100, "MyPlace")
            
            >>> # Creation with automatic thermodynamic enrichment
            >>> atp = document.create_place(200, 100, "ATP", compound_id="C00002")
            >>> print(atp.properties.get('delta_g_formation'))  # -2292.2 kJ/mol
        """
        place_id = self.id_manager.generate_place_id()
        place_name = place_id  # Name matches ID
        
        place = Place(x=x, y=y, id=place_id, name=place_name, label=label or place_name)
        # Apply default color schema
        from shypn.utils.color_schema_manager import ColorSchemaManager
        ColorSchemaManager.reset_place_color(place)
        
        # Auto-fetch thermodynamic properties if compound ID provided
        if compound_id and auto_fetch_thermodynamics:
            self.enrich_place_thermodynamics(place, compound_id)
        
        self.places.append(place)
        return place
    
    def create_transition(self, x: float, y: float, label: str = "") -> Transition:
        """Create a new transition at the given position.
        
        Args:
            x: X coordinate in world space
            y: Y coordinate in world space
            label: Optional label for the transition
            
        Returns:
            The created Transition object
        """
        transition_id = self.id_manager.generate_transition_id()
        transition_name = transition_id  # Name matches ID
        
        transition = Transition(x=x, y=y, id=transition_id, name=transition_name, label=label or transition_name)
        self.transitions.append(transition)
        return transition
    
    def create_arc(self, source: PetriNetObject, target: PetriNetObject, 
                   weight: int = 1, arc_type: str = 'normal') -> Optional[Arc]:
        """Create a new arc connecting source to target.
        
        Args:
            source: Source object (Place or Transition)
            target: Target object (must be different type from source)
            weight: Arc weight (default 1)
            arc_type: Type of arc ('normal', 'test', 'inhibitor', 'signal_flow', 'curved', 'curved_inhibitor_arc', 'curved_opposite_signal_flow')
            
        Returns:
            The created Arc object (proper subclass), or None if connection is invalid
        """
        # Validate connection (Place→Transition or Transition→Place)
        source_is_place = isinstance(source, Place)
        target_is_place = isinstance(target, Place)
        
        if source_is_place == target_is_place:
            # Both same type → invalid
            return None
        
        # AUTO-DETECT signal_flow arc: if connecting to/from signal place and arc_type is 'normal'
        if arc_type == 'normal':
            source_is_signal = (source_is_place and 
                               getattr(source, 'is_signal_place', False))
            target_is_signal = (target_is_place and 
                               getattr(target, 'is_signal_place', False))
            
            if source_is_signal or target_is_signal:
                # Automatically create signal_flow arc when connecting to signal places
                arc_type = 'signal_flow'
        
        arc_id = self.id_manager.generate_arc_id()
        arc_name = arc_id  # Name matches ID
        
        try:
            # Instantiate the appropriate arc subclass based on arc_type
            if arc_type == 'test':
                from shypn.netobjs.test_arc import TestArc
                arc = TestArc(source=source, target=target, id=arc_id, name=arc_name, weight=weight)
            elif arc_type == 'inhibitor':
                from shypn.netobjs.inhibitor_arc import InhibitorArc
                arc = InhibitorArc(source=source, target=target, id=arc_id, name=arc_name, weight=weight)
            elif arc_type == 'signal_flow':
                from shypn.netobjs.signal_flow_arc import SignalFlowArc
                arc = SignalFlowArc(source=source, target=target, id=arc_id, name=arc_name, weight=weight)
            elif arc_type == 'curved':
                from shypn.netobjs.curved_arc import CurvedArc
                arc = CurvedArc(source=source, target=target, id=arc_id, name=arc_name, weight=weight)
            elif arc_type == 'curved_inhibitor_arc':
                from shypn.netobjs.curved_inhibitor_arc import CurvedInhibitorArc
                arc = CurvedInhibitorArc(source=source, target=target, id=arc_id, name=arc_name, weight=weight)
            elif arc_type == 'curved_opposite_signal_flow':
                from shypn.netobjs.curved_signal_flow_arc import CurvedSignalFlowArc
                arc = CurvedSignalFlowArc(source=source, target=target, id=arc_id, name=arc_name, weight=weight)
            else:  # 'normal' or default
                arc = Arc(source=source, target=target, id=arc_id, name=arc_name, weight=weight)
            
            # Apply color schema to semantic arcs (TestArc, SignalFlowArc, InhibitorArc)
            from shypn.utils.color_schema_manager import ColorSchemaManager
            if ColorSchemaManager.is_semantic_arc_color(arc):
                ColorSchemaManager.reset_arc_color(arc)
            
            self.arcs.append(arc)
            return arc
        except ValueError:
            # Arc validation failed
            return None
    
    # ============================================================================
    # Object Addition (for loading existing objects)
    # ============================================================================
    
    def add_place(self, place: Place):
        """Add an existing place to the model.
        
        Args:
            place: Place object to add
        """
        if place not in self.places:
            self.places.append(place)
    
    def add_transition(self, transition: Transition):
        """Add an existing transition to the model.
        
        Args:
            transition: Transition object to add
        """
        if transition not in self.transitions:
            self.transitions.append(transition)
    
    def add_arc(self, arc: Arc):
        """Add an existing arc to the model.
        
        Args:
            arc: Arc object to add
        """
        if arc not in self.arcs:
            self.arcs.append(arc)
    
    # ============================================================================
    # Module Management (Modular Bio-PN Architecture)
    # ============================================================================
    
    def create_module(self, name: str, compartment_id: Optional[str] = None) -> Module:
        """Create a new module (interactive creation path).
        
        Args:
            name: Display name (e.g., "Cytoplasm", "Mitochondria")
            compartment_id: SBML compartment ID if mapping from SBML
            
        Returns:
            The created Module object
            
        Note:
            Supports both SBML auto-creation and manual interactive creation
        """
        module_id = self.id_manager.generate_module_id()
        module = Module(module_id=module_id, name=name, compartment_id=compartment_id)
        self.modules[module_id] = module
        return module
    
    def add_module(self, module: Module):
        """Add an existing module to the model (loading path).
        
        Args:
            module: Module object to add
            
        Note:
            Registers module ID to prevent duplicates
        """
        if module.module_id not in self.modules:
            self.modules[module.module_id] = module
            self.id_manager.register_module_id(module.module_id)
    
    def get_module(self, module_id: str) -> Optional[Module]:
        """Get module by ID.
        
        Args:
            module_id: Module identifier
            
        Returns:
            Module object or None if not found
        """
        return self.modules.get(module_id)
    
    def get_module_by_name(self, name: str) -> Optional[Module]:
        """Get module by name.
        
        Args:
            name: Module name
            
        Returns:
            First module with matching name, or None
        """
        for module in self.modules.values():
            if module.name == name:
                return module
        return None
    
    def get_module_by_compartment(self, compartment_id: str) -> Optional[Module]:
        """Get module by SBML compartment ID.
        
        Args:
            compartment_id: SBML compartment identifier
            
        Returns:
            Module object or None if not found
        """
        for module in self.modules.values():
            if module.compartment_id == compartment_id:
                return module
        return None
    
    def remove_module(self, module_id: str) -> bool:
        """Remove a module and clear object assignments.
        
        Args:
            module_id: Module identifier
            
        Returns:
            True if removed, False if not found
            
        Note:
            Clears module_id from all places/transitions in the module
        """
        if module_id not in self.modules:
            return False
        
        module = self.modules[module_id]
        
        # Clear module assignment from all objects
        for place in module.places:
            place.module_id = None
        for transition in module.transitions:
            transition.module_id = None
        
        # Remove from collection
        del self.modules[module_id]
        return True
    
    def get_modules_list(self) -> List[Module]:
        """Get list of all modules.
        
        Returns:
            List of Module objects
        """
        return list(self.modules.values())
    
    # ============================================================================
    # Object Removal
    # ============================================================================
    
    def remove_place(self, place: Place) -> bool:
        """Remove a place and all connected arcs.
        
        Args:
            place: Place to remove
            
        Returns:
            True if removed, False if not found
        """
        if place not in self.places:
            return False
        
        # Remove all arcs connected to this place
        self.arcs = [arc for arc in self.arcs 
                     if arc.source != place and arc.target != place]
        
        self.places.remove(place)
        return True
    
    def remove_transition(self, transition: Transition) -> bool:
        """Remove a transition and all connected arcs.
        
        Args:
            transition: Transition to remove
            
        Returns:
            True if removed, False if not found
        """
        if transition not in self.transitions:
            return False
        
        # Remove all arcs connected to this transition
        self.arcs = [arc for arc in self.arcs 
                     if arc.source != transition and arc.target != transition]
        
        self.transitions.remove(transition)
        return True
    
    def remove_arc(self, arc: Arc) -> bool:
        """Remove an arc.
        
        Args:
            arc: Arc to remove
            
        Returns:
            True if removed, False if not found
        """
        if arc in self.arcs:
            self.arcs.remove(arc)
            return True
        return False
    
    def remove_object(self, obj: PetriNetObject) -> bool:
        """Remove any Petri net object (place, transition, or arc).
        
        Args:
            obj: Object to remove
            
        Returns:
            True if removed, False if not found
        """
        if isinstance(obj, Place):
            return self.remove_place(obj)
        elif isinstance(obj, Transition):
            return self.remove_transition(obj)
        elif isinstance(obj, Arc):
            return self.remove_arc(obj)
        return False
    
    # ============================================================================
    # Spatial Queries
    # ============================================================================
    
    def get_object_at_point(self, x: float, y: float, 
                           tolerance: float = 5.0) -> Optional[PetriNetObject]:
        """Find object at the given point (world coordinates).
        
        Checks in order: Places, Transitions, Arcs
        Uses object-specific hit testing.
        
        Args:
            x: X coordinate in world space
            y: Y coordinate in world space
            tolerance: Hit test tolerance in world units
            
        Returns:
            The object at the point, or None if no object found
        """
        # Check places (circular hit test)
        for place in self.places:
            dx = x - place.x
            dy = y - place.y
            distance = (dx * dx + dy * dy) ** 0.5
            if distance <= place.radius + tolerance:
                return place
        
        # Check transitions (rectangular hit test)
        for transition in self.transitions:
            half_w = transition.width / 2
            half_h = transition.height / 2
            if (transition.x - half_w - tolerance <= x <= transition.x + half_w + tolerance and
                transition.y - half_h - tolerance <= y <= transition.y + half_h + tolerance):
                return transition
        
        # Check arcs (line hit test - simplified)
        for arc in self.arcs:
            if self._point_near_arc(x, y, arc, tolerance):
                return arc
        
        return None
    
    def _point_near_arc(self, x: float, y: float, arc: Arc, tolerance: float) -> bool:
        """Check if point is near an arc line.
        
        Simplified version - checks distance to line segment.
        """
        # Get arc endpoints
        sx, sy = arc.source.x, arc.source.y
        tx, ty = arc.target.x, arc.target.y
        
        # Vector from source to target
        dx = tx - sx
        dy = ty - sy
        length_sq = dx * dx + dy * dy
        
        if length_sq == 0:
            # Degenerate arc (source == target)
            return False
        
        # Project point onto line segment
        t = max(0, min(1, ((x - sx) * dx + (y - sy) * dy) / length_sq))
        
        # Closest point on segment
        closest_x = sx + t * dx
        closest_y = sy + t * dy
        
        # Distance from point to closest point
        dist_sq = (x - closest_x) ** 2 + (y - closest_y) ** 2
        
        return dist_sq <= (tolerance ** 2)
    
    def get_objects_in_rectangle(self, x1: float, y1: float, 
                                 x2: float, y2: float) -> List[PetriNetObject]:
        """Find all objects within a rectangle (world coordinates).
        
        Args:
            x1: Left edge
            y1: Top edge
            x2: Right edge
            y2: Bottom edge
            
        Returns:
            List of objects within the rectangle
        """
        min_x, max_x = min(x1, x2), max(x1, x2)
        min_y, max_y = min(y1, y2), max(y1, y2)
        
        objects = []
        
        # Check places
        for place in self.places:
            if (min_x <= place.x <= max_x and min_y <= place.y <= max_y):
                objects.append(place)
        
        # Check transitions
        for transition in self.transitions:
            if (min_x <= transition.x <= max_x and min_y <= transition.y <= max_y):
                objects.append(transition)
        
        # Note: Not including arcs in rectangle selection (common UX pattern)
        
        return objects
    
    # ============================================================================
    # Collection Operations
    # ============================================================================
    
    def get_all_objects(self) -> List[PetriNetObject]:
        """Get all objects in the model.
        
        Returns:
            List containing all places, transitions, and arcs
        """
        return self.places + self.transitions + self.arcs
    
    def get_connected_arcs(self, obj: PetriNetObject) -> List[Arc]:
        """Get all arcs connected to an object.
        
        Args:
            obj: Place or Transition to check
            
        Returns:
            List of connected arcs
        """
        return [arc for arc in self.arcs 
                if arc.source == obj or arc.target == obj]
    
    def clear(self):
        """Remove all objects from the model."""
        self.places.clear()
        self.transitions.clear()
        self.arcs.clear()
        self.id_manager.reset()
    
    # ============================================================================
    # Statistics
    # ============================================================================
    
    def get_object_count(self) -> Tuple[int, int, int]:
        """Get count of objects in the model.
        
        Returns:
            Tuple of (places_count, transitions_count, arcs_count)
        """
        return (len(self.places), len(self.transitions), len(self.arcs))
    
    def is_empty(self) -> bool:
        """Check if model has no objects.
        
        Returns:
            True if model is empty
        """
        return len(self.places) == 0 and len(self.transitions) == 0 and len(self.arcs) == 0
    
    # ============================================================================
    # Persistence (Serialization/Deserialization)
    # ============================================================================
    
    def to_dict(self) -> dict:
        """Serialize entire document to dictionary.
        
        Returns:
            Dictionary containing all document data in JSON-compatible format
        """
        from datetime import datetime
        
        # Build metadata - preserve existing metadata and add serialization info
        metadata = {}
        if hasattr(self, 'metadata') and self.metadata:
            metadata.update(self.metadata)  # Preserve existing metadata (source, has_test_arcs, etc.)
        
        # Add serialization metadata
        metadata["created"] = datetime.now().isoformat()
        metadata["object_counts"] = {
            "places": len(self.places),
            "transitions": len(self.transitions),
            "arcs": len(self.arcs),
            "modules": len(self.modules)
        }
        
        return {
            "version": "2.0",
            "metadata": metadata,
            "view_state": self.view_state,
            "thermodynamic_settings": self.thermodynamic_settings,
            "compound_mappings": self.compound_mappings,
            "places": [place.to_dict() for place in self.places],
            "transitions": [transition.to_dict() for transition in self.transitions],
            "arcs": [arc.to_dict() for arc in self.arcs],
            "modules": [module.to_dict() for module in self.modules.values()]
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'DocumentModel':
        """Deserialize document from dictionary.
        
        Args:
            data: Dictionary containing document data
            
        Returns:
            DocumentModel instance with all objects restored
            
        Raises:
            ValueError: If data format is invalid
        """
        # Create empty document
        document = cls()
        
        # Check version (for future compatibility)
        version = data.get("version", "1.0")
        if not version.startswith("2."):
            pass  # Version check - could add migration logic here
        
        # Restore places first (they have no dependencies)
        places_dict = {}
        for place_data in data.get("places", []):
            place = Place.from_dict(place_data)
            document.places.append(place)
            places_dict[place.id] = place  # Use string ID as dict key
            # Register ID to update counter (LOCAL ONLY to avoid scope contamination)
            with suspend_lifecycle_delegation():
                document.id_manager.register_place_id(place.id)
        
        # Restore transitions second (they have no dependencies)
        transitions_dict = {}
        for transition_data in data.get("transitions", []):
            transition = Transition.from_dict(transition_data)
            document.transitions.append(transition)
            transitions_dict[transition.id] = transition  # Use string ID as dict key
            # Register ID to update counter (LOCAL ONLY)
            with suspend_lifecycle_delegation():
                document.id_manager.register_transition_id(transition.id)
        
        # Restore arcs last (they depend on places and transitions)
        for arc_data in data.get("arcs", []):
            arc = Arc.from_dict(arc_data, places=places_dict, transitions=transitions_dict)
            document.arcs.append(arc)
            # Register ID to update counter (LOCAL ONLY)
            with suspend_lifecycle_delegation():
                document.id_manager.register_arc_id(arc.id)
        
        # Restore modules (if present)
        from shypn.netobjs.module import Module
        for module_data in data.get("modules", []):
            try:
                module = Module.from_dict(module_data, place_lookup=places_dict, transition_lookup=transitions_dict)
                document.add_module(module)
            except Exception as e:
                import traceback
                traceback.print_exc()
        
        # IMPORTANT: Reset all places to their initial marking
        # When loading a saved file, we want to start with the initial state,
        # not the simulation state that was active when the file was saved
        for place in document.places:
            if hasattr(place, 'initial_marking'):
                place.tokens = place.initial_marking
        
        # Restore view state if present
        if "view_state" in data:
            document.view_state = data["view_state"]
        
        # Restore thermodynamic settings if present, else use defaults
        if "thermodynamic_settings" in data:
            document.thermodynamic_settings = data["thermodynamic_settings"]
        else:
            # Legacy models get defaults
            document.thermodynamic_settings = cls._get_default_thermodynamic_settings()
        
        # Restore compound mappings if present, else use empty dict
        if "compound_mappings" in data:
            document.compound_mappings = data["compound_mappings"]
        else:
            # Legacy models get empty mappings
            document.compound_mappings = {}
        
        # Restore metadata if present (source, has_test_arcs, model_type, etc.)
        if "metadata" in data:
            # Filter out serialization-only metadata (created, object_counts)
            # and only restore application metadata
            metadata = {k: v for k, v in data["metadata"].items() 
                       if k not in ("created", "object_counts")}
            if metadata:
                document.metadata = metadata
        
        # POST-LOAD FIX: Convert regular Arcs to SignalFlowArcs if connecting to signal places
        # This fixes files saved before SignalFlowArc auto-detection was implemented
        from shypn.netobjs.signal_flow_arc import SignalFlowArc
        from shypn.utils.color_schema_manager import ColorSchemaManager
        
        arcs_to_convert = []
        for i, arc in enumerate(document.arcs):
            # Skip if already a SignalFlowArc or TestArc or InhibitorArc
            if not isinstance(arc, Arc) or arc.__class__ != Arc:
                continue
            
            # Check if arc connects to/from signal place
            source_is_signal = (isinstance(arc.source, Place) and 
                               getattr(arc.source, 'is_signal_place', False))
            target_is_signal = (isinstance(arc.target, Place) and 
                               getattr(arc.target, 'is_signal_place', False))
            
            if source_is_signal or target_is_signal:
                # Convert to SignalFlowArc
                signal_arc = SignalFlowArc(
                    source=arc.source,
                    target=arc.target,
                    id=arc.id,
                    name=arc.name,
                    weight=arc.weight
                )
                # Copy other properties
                signal_arc.label = arc.label
                signal_arc.width = arc.width
                signal_arc.control_points = arc.control_points.copy() if arc.control_points else []
                
                # Apply correct color
                ColorSchemaManager.reset_arc_color(signal_arc)
                
                arcs_to_convert.append((i, signal_arc))
        
        # Replace converted arcs
        for i, signal_arc in arcs_to_convert:
            document.arcs[i] = signal_arc
        
        return document
    
    # ============================================================================
    # Thermodynamic Data Management
    # ============================================================================
    
    def enrich_place_thermodynamics(self, place: Place, compound_id: str) -> bool:
        """Fetch and populate thermodynamic properties for a place.
        
        Queries local thermodynamic database and populates place.properties
        with ΔG°_f, uncertainty, and other compound data.
        
        Args:
            place: Place object to enrich
            compound_id: KEGG C-number (e.g., 'C00002') or ChEBI ID
            
        Returns:
            True if thermodynamic data found and populated, False otherwise
            
        Example:
            >>> place = document.create_place(100, 100, "ATP")
            >>> success = document.enrich_place_thermodynamics(place, "C00002")
            >>> if success:
            >>>     print(f"ΔG°_f = {place.properties['delta_g_formation']} kJ/mol")
        """
        try:
            # Lazy-load thermodynamic provider
            if not hasattr(self, '_thermo_provider'):
                from shypn.thermodynamics.database import MultiSourceProvider
                self._thermo_provider = MultiSourceProvider(
                    enable_cache=True,
                    enable_static=True,
                    enable_web=False  # Only use local data for interactive creation
                )
            
            # Get thermodynamic settings for query
            ph = self.thermodynamic_settings.get('ph', 7.0)
            temp = self.thermodynamic_settings.get('temperature', 298.15)
            ionic = self.thermodynamic_settings.get('ionic_strength', 0.1)
            
            # Query database
            compound_data = self._thermo_provider.get_compound(
                compound_id, ph=ph, temperature=temp, ionic_strength=ionic
            )
            
            if compound_data:
                # Populate place properties
                place.properties['compound_id'] = compound_data.compound_id
                place.properties['compound_name'] = compound_data.name
                place.properties['delta_g_formation'] = compound_data.delta_g_formation
                place.properties['delta_g_uncertainty'] = compound_data.uncertainty
                place.properties['thermodynamic_source'] = compound_data.source
                place.properties['thermodynamic_conditions'] = {
                    'pH': ph,
                    'temperature': temp,
                    'ionic_strength': ionic
                }
                
                # Update metadata for traceability
                if not hasattr(place, 'metadata'):
                    place.metadata = {}
                place.metadata['compound_id'] = compound_data.compound_id
                place.metadata['has_thermodynamic_data'] = True
                
                return True
            else:
                # Compound not found in database
                if not hasattr(place, 'metadata'):
                    place.metadata = {}
                place.metadata['compound_id'] = compound_id
                place.metadata['has_thermodynamic_data'] = False
                return False
                
        except Exception as e:
            import logging
            logging.getLogger('DocumentModel').warning(
                f"Failed to fetch thermodynamic data for {compound_id}: {e}"
            )
            return False
    
    def enrich_all_places_thermodynamics(self, id_mapping: Optional[Dict[str, str]] = None) -> Dict[str, bool]:
        """Batch enrich all places with thermodynamic data.
        
        Useful for post-import enrichment or updating existing models.
        
        Args:
            id_mapping: Optional mapping of place_id → compound_id.
                       If None, uses place.metadata['compound_id'] or place.metadata['kegg_id']
            
        Returns:
            Dictionary mapping place_id → enrichment_success (True/False)
            
        Example:
            >>> # Enrich all places that have KEGG IDs in metadata
            >>> results = document.enrich_all_places_thermodynamics()
            >>> enriched = sum(results.values())
            >>> print(f"Enriched {enriched}/{len(results)} places")
        """
        results = {}
        
        for place in self.places:
            # Determine compound ID
            compound_id = None
            
            if id_mapping and place.id in id_mapping:
                compound_id = id_mapping[place.id]
            elif hasattr(place, 'metadata'):
                # Try compound_id first, then kegg_id
                compound_id = place.metadata.get('compound_id') or place.metadata.get('kegg_id')
                # Clean KEGG ID if needed (remove 'cpd:' prefix)
                if compound_id and ':' in compound_id:
                    compound_id = compound_id.split(':')[-1]
            
            if compound_id:
                success = self.enrich_place_thermodynamics(place, compound_id)
                results[place.id] = success
            else:
                results[place.id] = False
        
        return results
    
    # ============================================================================
    # Thermodynamic Settings Management
    # ============================================================================
    
    @staticmethod
    def get_thermodynamic_presets() -> Dict[str, dict]:
        """Get available thermodynamic condition presets.
        
        Returns:
            Dictionary mapping preset_name → settings dict
        """
        return {
            "biochemical_standard": {
                "ph": 7.0,
                "temperature": 298.15,  # 25°C
                "ionic_strength": 0.1,
                "tolerance": 0.5,
                "enable_validation": True,
                "preset": "biochemical_standard",
                "description": "Biochemical standard state (pH 7.0, 25°C)"
            },
            "e_coli_cytoplasm": {
                "ph": 7.4,
                "temperature": 310.15,  # 37°C
                "ionic_strength": 0.15,
                "tolerance": 0.5,
                "enable_validation": True,
                "preset": "e_coli_cytoplasm",
                "description": "E. coli cytoplasm (pH 7.4, 37°C)"
            },
            "human_blood": {
                "ph": 7.4,
                "temperature": 310.15,  # 37°C
                "ionic_strength": 0.15,
                "tolerance": 0.5,
                "enable_validation": True,
                "preset": "human_blood",
                "description": "Human blood plasma (pH 7.4, 37°C)"
            },
            "thermophile": {
                "ph": 7.0,
                "temperature": 353.15,  # 80°C
                "ionic_strength": 0.1,
                "tolerance": 0.5,
                "enable_validation": True,
                "preset": "thermophile",
                "description": "Thermophilic organism (pH 7.0, 80°C)"
            },
            "acidophile": {
                "ph": 3.0,
                "temperature": 298.15,  # 25°C
                "ionic_strength": 0.1,
                "tolerance": 0.5,
                "enable_validation": True,
                "preset": "acidophile",
                "description": "Acidophilic organism (pH 3.0, 25°C)"
            },
            "alkaliphile": {
                "ph": 10.0,
                "temperature": 298.15,  # 25°C
                "ionic_strength": 0.1,
                "tolerance": 0.5,
                "enable_validation": True,
                "preset": "alkaliphile",
                "description": "Alkaliphilic organism (pH 10.0, 25°C)"
            }
        }
    
    def set_thermodynamic_preset(self, preset_name: str) -> None:
        """Apply a thermodynamic preset to this model.
        
        Args:
            preset_name: Name of preset from get_thermodynamic_presets()
            
        Raises:
            ValueError: If preset_name is not recognized
        """
        presets = self.get_thermodynamic_presets()
        if preset_name not in presets:
            raise ValueError(f"Unknown preset: {preset_name}. Available: {list(presets.keys())}")
        
        self.thermodynamic_settings = presets[preset_name].copy()
    
    def update_thermodynamic_settings(self, **kwargs) -> None:
        """Update specific thermodynamic settings.
        
        Args:
            **kwargs: Settings to update (ph, temperature, ionic_strength, tolerance, enable_validation)
            
        Example:
            >>> doc.update_thermodynamic_settings(ph=7.4, temperature=310.15)
        """
        # Update provided settings
        for key, value in kwargs.items():
            if key in self.thermodynamic_settings:
                self.thermodynamic_settings[key] = value
        
        # Mark as custom if not using a standard preset
        if any(kwargs):
            self.thermodynamic_settings["preset"] = "custom"
    
    def get_thermodynamic_setting(self, key: str, default=None):
        """Get a specific thermodynamic setting value.
        
        Args:
            key: Setting name (ph, temperature, ionic_strength, tolerance, enable_validation)
            default: Value to return if key not found
            
        Returns:
            Setting value or default
        """
        return self.thermodynamic_settings.get(key, default)
    
    def save_to_file(self, filepath: str) -> None:
        """Save document to JSON file.
        
        Args:
            filepath: Path to save file (should already have extension like .shy)
            
        Raises:
            IOError: If file cannot be written
        """
        import json
        import os
        
        # Reset all objects to color schema defaults before saving
        # This ensures recording colors (orange) don't get persisted
        from shypn.utils.color_schema_manager import ColorSchemaManager
        for place in self.places:
            ColorSchemaManager.reset_place_color(place)
        for transition in self.transitions:
            ColorSchemaManager.reset_transition_colors(transition)
        for arc in self.arcs:
            ColorSchemaManager.reset_arc_color(arc)
        
        # Don't modify filepath - it should already have the correct extension (.shy)
        # The .shy extension is used for SHYpn Petri net files (which are JSON internally)
        
        # Create directory if needed
        directory = os.path.dirname(filepath)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
        
        # Serialize and save
        data = self.to_dict()
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        # Emit file.saved event
        EventBus.emit('file.saved', {
            'filepath': filepath,
            'document': self,
            'timestamp': time.time(),
            'was_autosave': False  # Manual save
        })
    
    @classmethod
    def load_from_file(cls, filepath: str) -> 'DocumentModel':
        """Load document from JSON file.
        
        Args:
            filepath: Path to file to load
            
        Returns:
            DocumentModel instance loaded from file
            
        Raises:
            IOError: If file cannot be read
            ValueError: If file format is invalid
        """
        import json
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        document = cls.from_dict(data)
        
        # Emit file.opened event
        EventBus.emit('file.opened', {
            'filepath': filepath,
            'document': document,
            'timestamp': time.time()
        })
        
        return document
