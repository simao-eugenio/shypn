"""PlaceBuilder - Fluent interface for Place construction.

Provides clean, readable API for constructing Place objects with all properties
including Signal Hierarchical Petri Net (SHPN) extensions.

Features:
- Fluent method chaining API
- Signal place designation (Ψ ⊆ P in SHPN formalism)
- Hierarchical layer assignment (λ: Ψ → ℕ₀)
- Spatial properties (compartment, volume, diffusion)
- Validation and error checking
- Sensible defaults

Example - Simple place:
    place = (PlaceBuilder("glucose")
             .with_tokens(10)
             .at_position(100, 150)
             .build())

Example - Signal place with SHPN properties:
    atp = (PlaceBuilder("ATP")
           .with_tokens(100)
           .at_position(150, 200)
           .as_signal_place("ENERGY")  # Mark as Ψ (signal place)
           .with_layer(0)              # λ(ATP) = 0 (metabolic layer)
           .with_label("ATP Pool")
           .with_spatial_properties(
               compartment="mitochondria",
               volume=0.5,  # fL
               diffusion_coefficient=300.0  # μm²/s
           )
           .build())

Example - Regulatory gene locus:
    gene = (PlaceBuilder("spo0A_gene")
            .with_tokens(1)  # 1 copy per cell
            .at_position(200, 100)
            .as_regulatory_place()
            .with_label("spo0A locus")
            .build())

See doc/PHASE_3_QUALITY_PLAN.md for design rationale.
See doc/SIGNAL_HIERARCHICAL_FORMALISM.md for SHPN theoretical foundations.
"""

from typing import Optional, Tuple, Dict, Any
from shypn.netobjs.place import Place, BoundaryType
from shypn.netobjs.signal_type import SignalType


class PlaceBuilder:
    """Fluent builder for Place objects.
    
    Simplifies place construction with method chaining and validation.
    Supports all Place properties including SHPN extensions.
    
    Attributes:
        All internal attributes are prefixed with _ to indicate builder state.
        Use build() to construct the final Place object.
    """
    
    def __init__(self, id: str = None, *, id_manager=None):
        """Initialize builder with place ID.
        
        Args:
            id: Unique place identifier (e.g., "P1", "ATP", "glucose"), auto-generated if None
            id_manager: IDManager instance from document (keyword-only, if None creates standalone)
        """
        # Required properties
        self._id = id
        self._id_manager = id_manager
        self._name = id if id else None  # Default name = id
        
        # Position and styling
        self._x = 0.0
        self._y = 0.0
        self._radius = None  # Use Place.DEFAULT_RADIUS if not set
        self._label = ""
        self._color = None  # Use ColorSchemaManager default if not set
        
        # State
        self._tokens = 0
        self._initial_marking = None  # Defaults to _tokens if not set
        self._capacity = float('inf')
        
        # SHPN - Signal place properties (Ψ ⊆ P)
        self._is_signal_place = False
        self._signal_type: Optional[str] = None  # ENERGY, SPATIAL, QUORUM, REGULATORY
        self._signal_scope = []
        self._layer: Optional[int] = None  # λ(p) - hierarchical layer (0=metabolism, 1=sensing, 2=integration, 3=execution)
        
        # Regulatory place properties
        self._is_regulatory_place = False
        
        # Module assignment
        self._module_id: Optional[str] = None
        self._is_compartment_place = False
        
        # Spatial properties (for SPATIAL signal places)
        self._diffusion_coefficient: Optional[float] = None
        self._boundary_type: Optional[BoundaryType] = None
        self._gradient_vector: Optional[Tuple[float, float, float]] = None
        self._compartment_volume: Optional[float] = None
        self._neighbor_compartments = []
        self._spatial_position: Optional[Tuple[float, float, float]] = None
        
        # Additional properties and metadata
        self._properties: Dict[str, Any] = {}
        self._metadata: Dict[str, Any] = {}
    
    # ========== Required Properties ==========
    
    def with_name(self, name: str) -> 'PlaceBuilder':
        """Set place name (defaults to ID if not called).
        
        Args:
            name: Place name (e.g., "P1", "ATP_pool")
        
        Returns:
            Self for method chaining
        """
        self._name = name
        return self
    
    # ========== Position and Styling ==========
    
    def at_position(self, x: float, y: float) -> 'PlaceBuilder':
        """Set canvas position.
        
        Args:
            x: X coordinate in world space
            y: Y coordinate in world space
        
        Returns:
            Self for method chaining
        
        Example:
            .at_position(150, 200)
        """
        self._x = float(x)
        self._y = float(y)
        return self
    
    def with_radius(self, radius: float) -> 'PlaceBuilder':
        """Set circle radius (default: Place.DEFAULT_RADIUS = 40.0).
        
        Args:
            radius: Circle radius in pixels
        
        Returns:
            Self for method chaining
        
        Example:
            .with_radius(50)  # Larger place
        """
        self._radius = float(radius)
        return self
    
    def with_label(self, label: str) -> 'PlaceBuilder':
        """Set display label (shown on canvas).
        
        Args:
            label: User-visible text label
        
        Returns:
            Self for method chaining
        
        Example:
            .with_label("ATP Pool")
        """
        self._label = label
        return self
    
    def with_color(self, r: float, g: float, b: float) -> 'PlaceBuilder':
        """Set border color (RGB 0.0-1.0).
        
        Note: Signal places automatically get blue border via ColorSchemaManager.
        This method overrides the automatic color.
        
        Args:
            r: Red component (0.0-1.0)
            g: Green component (0.0-1.0)
            b: Blue component (0.0-1.0)
        
        Returns:
            Self for method chaining
        
        Example:
            .with_color(1.0, 0.0, 0.0)  # Red border
        """
        self._color = (float(r), float(g), float(b))
        return self
    
    # ========== State ==========
    
    def with_tokens(self, tokens: int) -> 'PlaceBuilder':
        """Set initial token count.
        
        Args:
            tokens: Number of tokens (non-negative)
        
        Returns:
            Self for method chaining
        
        Raises:
            ValueError: If tokens < 0
        
        Example:
            .with_tokens(100)  # Start with 100 ATP molecules
        """
        if tokens < 0:
            raise ValueError(f"Token count must be non-negative, got {tokens}")
        self._tokens = int(tokens)
        return self
    
    def with_initial_marking(self, marking: int) -> 'PlaceBuilder':
        """Set initial marking (for simulation reset, defaults to tokens).
        
        Args:
            marking: Initial marking value
        
        Returns:
            Self for method chaining
        
        Example:
            .with_tokens(50).with_initial_marking(100)  # Reset to 100
        """
        self._initial_marking = int(marking)
        return self
    
    def with_capacity(self, capacity: float) -> 'PlaceBuilder':
        """Set maximum token capacity (default: infinite).
        
        Args:
            capacity: Maximum tokens (use float('inf') for unbounded)
        
        Returns:
            Self for method chaining
        
        Example:
            .with_capacity(1000)  # Cap at 1000 molecules
        """
        self._capacity = float(capacity)
        return self
    
    # ========== SHPN - Signal Place Properties ==========
    
    def as_signal_place(self, signal_type: Optional[str] = None) -> 'PlaceBuilder':
        """Mark as signal place (Ψ ⊆ P in SHPN formalism).
        
        Signal places participate in both:
        - Normal arcs (horizontal mass transfer at Layer 0)
        - Signal flow arcs (vertical information broadcast to higher layers)
        
        Dual arc semantics enable metabolites to function simultaneously as:
        - Biochemical substrates (e.g., ATP in glycolysis)
        - Regulatory signals (e.g., ATP gating sporulation commitment)
        
        Args:
            signal_type: Optional classification:
                - "ENERGY": ATP, GTP, NADH, NAD+ (metabolic energy carriers)
                - "SPATIAL": Ca²⁺, IP₃, DAG (spatial gradients and diffusion)
                - "QUORUM": cAMP, autoinducers, pheromones (cell-cell communication)
                - "REGULATORY": Transcription factors, kinases, phosphorylated species
                - None: Generic signal place (type determined later)
        
        Returns:
            Self for method chaining
        
        Example - ATP as energy signal:
            .as_signal_place("ENERGY")
        
        Example - cAMP as quorum signal:
            .as_signal_place("QUORUM")
        
        See:
            doc/SIGNAL_HIERARCHICAL_FORMALISM.md - Section "Signal Places"
        """
        self._is_signal_place = True
        if signal_type:
            # Validate signal type
            valid_types = {"ENERGY", "SPATIAL", "QUORUM", "REGULATORY"}
            if signal_type.upper() not in valid_types:
                raise ValueError(
                    f"Invalid signal_type '{signal_type}'. "
                    f"Must be one of: {', '.join(sorted(valid_types))}"
                )
            self._signal_type = signal_type.upper()
        return self
    
    def with_layer(self, layer: int) -> 'PlaceBuilder':
        """Set hierarchical layer λ(p) for SHPN signal places.
        
        Layer function λ: Ψ → ℕ₀ assigns hierarchical depth via topological sort:
        - Layer 0: Metabolism (ATP, NADH production)
        - Layer 1: Sensing (metabolite sensors CodY, CcpA)
        - Layer 2: Integration (phosphorelay Spo0A~P)
        - Layer 3: Execution (sigma factors σ^F, σ^E)
        
        If not set, PetriNetBuilder.compute_layers() will assign via topological sort
        on signal flow graph G_s = (Ψ, F_s).
        
        Args:
            layer: Hierarchical depth (0, 1, 2, ...) where:
                   λ(pᵢ) < λ(pⱼ) for all signal paths pᵢ → t → pⱼ
        
        Returns:
            Self for method chaining
        
        Raises:
            ValueError: If layer < 0
        
        Example - ATP at metabolic layer:
            .as_signal_place("ENERGY").with_layer(0)
        
        Example - Sigma factor at execution layer:
            .as_signal_place("REGULATORY").with_layer(3)
        
        See:
            doc/SIGNAL_HIERARCHICAL_FORMALISM.md - Section "Hierarchical Layers"
        """
        if layer < 0:
            raise ValueError(f"Layer must be non-negative, got {layer}")
        self._layer = int(layer)
        return self
    
    def with_signal_scope(self, *module_ids: str) -> 'PlaceBuilder':
        """Set signal visibility scope (which modules can read this signal).
        
        Args:
            *module_ids: Module IDs that can read signal (empty = global scope)
        
        Returns:
            Self for method chaining
        
        Example:
            .with_signal_scope("M_cytoplasm", "M_nucleus")
        """
        self._signal_scope = list(module_ids)
        return self
    
    # ========== Regulatory Place ==========
    
    def as_regulatory_place(self) -> 'PlaceBuilder':
        """Mark as regulatory place (gene locus or constant resource).
        
        Regulatory places represent:
        - Gene loci (DNA templates for transcription)
        - Constant resource pools
        - Abstract regulatory states
        
        Returns:
            Self for method chaining
        
        Example:
            .as_regulatory_place().with_tokens(1)  # 1 gene copy
        """
        self._is_regulatory_place = True
        return self
    
    # ========== Module and Compartment ==========
    
    def with_module(self, module_id: str) -> 'PlaceBuilder':
        """Assign to module (for modular Bio-PN architecture).
        
        Args:
            module_id: Module identifier (e.g., "M_cytoplasm", "M_mitochondria")
        
        Returns:
            Self for method chaining
        
        Example:
            .with_module("M_mitochondria")
        """
        self._module_id = module_id
        return self
    
    def in_compartment(self, compartment: bool = True) -> 'PlaceBuilder':
        """Mark as non-default compartment place.
        
        Args:
            compartment: True if in special compartment (e.g., extracellular)
        
        Returns:
            Self for method chaining
        
        Example:
            .in_compartment()  # Marks as compartment place
        """
        self._is_compartment_place = compartment
        return self
    
    # ========== Spatial Properties (for SPATIAL signal places) ==========
    
    def with_spatial_properties(self, 
                                compartment: Optional[str] = None,
                                volume: Optional[float] = None,
                                diffusion_coefficient: Optional[float] = None,
                                boundary_type: Optional[str] = None,
                                position: Optional[Tuple[float, float, float]] = None,
                                **kwargs) -> 'PlaceBuilder':
        """Set spatial properties for SPATIAL signal places.
        
        Args:
            compartment: Compartment name (e.g., "mitochondria", "cytoplasm")
            volume: Compartment volume in femtoliters (fL)
            diffusion_coefficient: Diffusion rate in μm²/s
            boundary_type: Permeability ("permeable", "selective", "impermeable")
            position: 3D position tuple (x, y, z) in μm
            **kwargs: Additional spatial properties
        
        Returns:
            Self for method chaining
        
        Example - Calcium signal with diffusion:
            .as_signal_place("SPATIAL")
            .with_spatial_properties(
                compartment="cytoplasm",
                volume=1.5,  # fL
                diffusion_coefficient=220.0,  # μm²/s (Ca²⁺ typical)
                boundary_type="selective"
            )
        
        See:
            doc/SIGNAL_HIERARCHICAL_FORMALISM.md - "Signal Types" section
        """
        if compartment:
            self._properties['compartment'] = compartment
        
        if volume is not None:
            self._compartment_volume = float(volume)
        
        if diffusion_coefficient is not None:
            self._diffusion_coefficient = float(diffusion_coefficient)
        
        if boundary_type:
            # Parse boundary type string to enum
            try:
                self._boundary_type = BoundaryType[boundary_type.upper()]
            except KeyError:
                valid = [bt.value for bt in BoundaryType]
                raise ValueError(
                    f"Invalid boundary_type '{boundary_type}'. "
                    f"Must be one of: {', '.join(valid)}"
                )
        
        if position:
            if len(position) != 3:
                raise ValueError(f"Position must be (x, y, z) tuple, got {position}")
            self._spatial_position = tuple(float(v) for v in position)
        
        # Store additional spatial properties
        for key, value in kwargs.items():
            self._properties[key] = value
        
        return self
    
    def with_gradient(self, dx: float, dy: float, dz: float) -> 'PlaceBuilder':
        """Set concentration gradient vector for spatial signals.
        
        Args:
            dx: X-direction gradient component
            dy: Y-direction gradient component
            dz: Z-direction gradient component
        
        Returns:
            Self for method chaining
        
        Example:
            .with_gradient(1.0, 0.0, 0.0)  # Gradient in +X direction
        """
        self._gradient_vector = (float(dx), float(dy), float(dz))
        return self
    
    def with_neighbors(self, *compartment_ids: str) -> 'PlaceBuilder':
        """Set adjacent compartments for diffusion.
        
        Args:
            *compartment_ids: IDs of neighboring compartments
        
        Returns:
            Self for method chaining
        
        Example:
            .with_neighbors("C_left", "C_right", "C_top")
        """
        self._neighbor_compartments = list(compartment_ids)
        return self
    
    # ========== Custom Properties and Metadata ==========
    
    def with_property(self, key: str, value: Any) -> 'PlaceBuilder':
        """Set custom property.
        
        Args:
            key: Property key
            value: Property value
        
        Returns:
            Self for method chaining
        
        Example:
            .with_property("enzyme_km", 5.0)
        """
        self._properties[key] = value
        return self
    
    def with_metadata(self, **kwargs) -> 'PlaceBuilder':
        """Set metadata (annotations, provenance).
        
        Args:
            **kwargs: Metadata key-value pairs
        
        Returns:
            Self for method chaining
        
        Example:
            .with_metadata(
                source="KEGG",
                kegg_id="C00002",
                description="Adenosine triphosphate"
            )
        """
        self._metadata.update(kwargs)
        return self
    
    # ========== Build ==========
    
    def build(self) -> Place:
        """Construct the Place object with all configured properties.
        
        Returns:
            Configured Place instance
        
        Raises:
            ValueError: If configuration is invalid
        
        Example:
            place = PlaceBuilder("ATP").with_tokens(100).build()
        """
        # Generate ID if not provided
        if self._id is None:
            if self._id_manager is None:
                # Standalone builder - create temporary id_manager
                from shypn.data.canvas.id_manager import IDManager
                self._id_manager = IDManager()
            self._id = self._id_manager.generate_place_id()
        
        # Generate name if not provided
        if self._name is None:
            self._name = self._id
        
        # Create place with required parameters
        place = Place(
            x=self._x,
            y=self._y,
            id=self._id,
            name=self._name,
            radius=self._radius,
            label=self._label
        )
        
        # Set state
        place.tokens = self._tokens
        place.initial_marking = self._initial_marking if self._initial_marking is not None else self._tokens
        place.capacity = self._capacity
        
        # Set optional color (if specified, overrides ColorSchemaManager default)
        if self._color:
            place.border_color = self._color
        
        # SHPN - Signal place properties
        if self._is_signal_place:
            place.is_signal_place = True
            
            if self._signal_type:
                # Convert string to SignalType enum
                place.signal_type = SignalType[self._signal_type]
            
            # Layer is only meaningful for signal places (λ: Ψ → ℕ₀)
            if self._layer is not None:
                place.layer = self._layer
            
            if self._signal_scope:
                place.signal_scope = self._signal_scope.copy()
        
        # Regulatory place
        if self._is_regulatory_place:
            place.is_regulatory_place = True
        
        # Module and compartment
        if self._module_id:
            place.module_id = self._module_id
        
        if self._is_compartment_place:
            place.is_compartment_place = True
        
        # Spatial properties
        if self._diffusion_coefficient is not None:
            place.diffusion_coefficient = self._diffusion_coefficient
        
        if self._boundary_type is not None:
            place.boundary_type = self._boundary_type
        
        if self._gradient_vector is not None:
            place.gradient_vector = self._gradient_vector
        
        if self._compartment_volume is not None:
            place.compartment_volume = self._compartment_volume
        
        if self._neighbor_compartments:
            place.neighbor_compartments = self._neighbor_compartments.copy()
        
        if self._spatial_position is not None:
            place.spatial_position = self._spatial_position
        
        # Custom properties and metadata
        if self._properties:
            place.properties.update(self._properties)
        
        if self._metadata:
            place.metadata.update(self._metadata)
        
        # Lifecycle tracking (Week 2 - Phase 4)
        # Register object with IDManager for lifecycle observation
        if self._id_manager and hasattr(self._id_manager, 'register_object'):
            try:
                self._id_manager.register_object(place, obj_type='place')
            except (AttributeError, TypeError, RuntimeError) as e:
                # Lifecycle tracking optional, don't break build
                from shypn.utils.logging import get_logger
                logger = get_logger(__name__)
                logger.debug(f"Failed to register place with lifecycle ID manager: {e}")
        
        return place
    
    # ========== Convenience Methods ==========
    
    def __repr__(self) -> str:
        """String representation for debugging.
        
        Returns:
            Descriptive string
        """
        signal_info = f", signal={self._signal_type}" if self._is_signal_place else ""
        layer_info = f", layer={self._layer}" if self._layer is not None else ""
        return (f"PlaceBuilder(id={self._id!r}, tokens={self._tokens}, "
                f"pos=({self._x}, {self._y}){signal_info}{layer_info})")

