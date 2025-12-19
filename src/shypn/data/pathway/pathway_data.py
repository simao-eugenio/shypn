"""
Pathway Data Classes

Data structures for representing biochemical pathway information
before conversion to Petri nets.

Coordinate System Note:
- Position data stored as (x, y) tuples use graphics coordinates
- Origin at top-left, Y increases downward (standard Cairo/GTK)
- Conceptually represents Cartesian space (see doc/COORDINATE_SYSTEM.md)
- Higher Y values = further descended in pathway hierarchy
"""

from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Any


@dataclass
class Annotation:
    """
    MIRIAM-compliant annotation for species/reactions.
    
    Stores database cross-references following MIRIAM guidelines:
    - identifiers.org URIs
    - Biological database IDs (ChEBI, KEGG, UniProt, etc.)
    - SBO (Systems Biology Ontology) terms
    
    Attributes:
        identifiers: Dict mapping database names to IDs
                    Example: {'chebi': 'CHEBI:15422', 'kegg': 'C00002'}
        uris: List of full identifiers.org URIs
             Example: ['http://identifiers.org/chebi/CHEBI:15422']
        sbo_term: Systems Biology Ontology term
                 Example: "SBO:0000247" (simple chemical)
        notes: Free-text notes from SBML
    """
    identifiers: Dict[str, str] = field(default_factory=dict)
    uris: List[str] = field(default_factory=list)
    sbo_term: Optional[str] = None
    notes: Optional[str] = None
    
    def get_uri(self, database: str) -> Optional[str]:
        """
        Get identifiers.org URI for a specific database.
        
        Args:
            database: Database name (e.g., 'chebi', 'kegg')
            
        Returns:
            Full URI or None if database not found
        """
        if database in self.identifiers:
            db_id = self.identifiers[database]
            return f"http://identifiers.org/{database}/{db_id}"
        return None
    
    def __repr__(self) -> str:
        dbs = ', '.join(self.identifiers.keys())
        return f"Annotation(databases=[{dbs}], sbo={self.sbo_term})"


@dataclass
class Compartment:
    """
    Cellular compartment with volume information.
    
    Enhanced from simple string mapping to full object representation.
    Enables proper amount ↔ concentration conversion in multi-compartment models.
    
    Attributes:
        id: Unique identifier (e.g., "cytosol", "mitochondria")
        name: Human-readable name
        size: Volume (default unit: liters)
        spatial_dimensions: Dimensionality (3D by default)
        units: Volume units (optional)
        constant: True if volume doesn't change over time
        metadata: Additional properties
    """
    id: str
    name: str
    size: float = 1.0
    spatial_dimensions: int = 3
    units: Optional[str] = None
    constant: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __repr__(self) -> str:
        return f"Compartment(id={self.id!r}, name={self.name!r}, size={self.size})"


@dataclass
class Event:
    """
    SBML Event representation (14th tuple component).
    
    Events enable experimental perturbations and environmental changes:
    - Time-based triggers (e.g., t > 100)
    - State-based triggers (e.g., [Glucose] < 0.1)
    - Discrete assignments to species/parameters
    
    Used for modeling:
    - Drug addition
    - Nutrient depletion
    - Temperature changes
    - Protocol steps
    
    Attributes:
        id: Unique identifier
        name: Human-readable name
        trigger: Mathematical expression for trigger condition
        delay: Delay before executing assignments (time units)
        use_values_from_trigger_time: Use values at trigger time or execution time
        priority: Priority for simultaneous events (higher = first)
        assignments: Dict mapping variable IDs to assignment expressions
        trigger_compiled: Compiled trigger for simulation (set during simulation init)
        metadata: Additional properties
    """
    id: str
    name: Optional[str] = None
    trigger: str = ""
    delay: float = 0.0
    use_values_from_trigger_time: bool = True
    priority: int = 0
    assignments: Dict[str, str] = field(default_factory=dict)
    trigger_compiled: Optional[Any] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __repr__(self) -> str:
        return f"Event(id={self.id!r}, trigger={self.trigger!r}, assignments={len(self.assignments)})"


@dataclass
class UnitDefinition:
    """
    SBML unit definition for consistent parameter interpretation.
    
    Stores custom units and conversion factors to base SI units.
    Enables proper unit normalization during SBML import.
    
    Attributes:
        id: Unit identifier (e.g., "mM", "per_second")
        name: Human-readable name
        base_units: List of base unit components
                   Each tuple: (kind, exponent, scale, multiplier)
                   Example for mM: [('mole', 1, -3, 1.0), ('litre', -1, 0, 1.0)]
        si_conversion_factor: Multiplicative factor to convert to SI base units
    """
    id: str
    name: Optional[str] = None
    base_units: List[Tuple[str, int, int, float]] = field(default_factory=list)
    si_conversion_factor: float = 1.0
    
    def __repr__(self) -> str:
        return f"UnitDefinition(id={self.id!r}, si_factor={self.si_conversion_factor})"


@dataclass
class Species:
    """
    Represents a biochemical species (metabolite/compound).
    
    Will be converted to a Place in the Petri net.
    
    Attributes:
        id: Unique identifier (e.g., "C00031" for glucose)
        name: Human-readable name (e.g., "Glucose")
        compartment: Cellular location (e.g., "cytosol")
        initial_concentration: Initial amount (default unit: mM - millimolar)
        initial_tokens: Token count after unit normalization
        formula: Chemical formula (e.g., "C6H12O6")
        charge: Electrical charge
        chebi_id: ChEBI database ID
        kegg_id: KEGG database ID
        metadata: Additional properties
        
    Notes:
        - Default concentration scale: mM (millimolar, 10^-3 M)
        - Typical cellular metabolite range: 0.01 - 10 mM
        - Default value when unspecified: 1.0 mM (physiological assumption)
    """
    id: str
    name: Optional[str] = None
    compartment: Optional[str] = None
    initial_concentration: float = 0.0  # Default unit: mM (millimolar)
    initial_tokens: int = 0
    formula: Optional[str] = None
    charge: Optional[int] = None
    compartment_volume: float = 1.0  # For unit conversion
    
    # Database cross-references
    chebi_id: Optional[str] = None
    kegg_id: Optional[str] = None
    
    # Phase 1 additions: SBML Compliance
    annotation: Optional[Annotation] = None
    compartment_ref: Optional[Compartment] = None  # Reference to Compartment object
    substance_units: Optional[str] = None
    has_only_substance_units: bool = False  # True = amount, False = concentration
    
    # Additional properties
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __repr__(self) -> str:
        return f"Species(id={self.id!r}, name={self.name!r}, tokens={self.initial_tokens})"


@dataclass
class KineticLaw:
    """
    Represents kinetic rate law for a reaction.
    
    Will be converted to transition rate in the Petri net.
    
    Attributes:
        formula: Mathematical expression (e.g., "Vmax * S / (Km + S)")
        rate_type: Type of kinetics (e.g., "mass_action", "michaelis_menten")
        parameters: Parameter values (e.g., {"Vmax": 10.0, "Km": 0.5})
    """
    formula: str
    rate_type: Optional[str] = None  # "mass_action", "michaelis_menten", "custom"
    parameters: Dict[str, float] = field(default_factory=dict)
    
    def __repr__(self) -> str:
        return f"KineticLaw(type={self.rate_type!r}, formula={self.formula!r})"


@dataclass
class Reaction:
    """
    Represents a biochemical reaction.
    
    Will be converted to a Transition in the Petri net.
    
    Attributes:
        id: Unique identifier (e.g., "R00001")
        name: Human-readable name (e.g., "Hexokinase")
        reactants: List of (species_id, stoichiometry) tuples for inputs
        products: List of (species_id, stoichiometry) tuples for outputs
        modifiers: List of species_ids that act as catalysts/modulators
        kinetic_law: Rate law (optional)
        reversible: Whether reaction can go both directions
        enzyme: Enzyme catalyst name (optional, legacy)
        metadata: Additional properties
    """
    id: str
    name: Optional[str] = None
    reactants: List[Tuple[str, float]] = field(default_factory=list)  # [(species_id, stoich), ...]
    products: List[Tuple[str, float]] = field(default_factory=list)   # [(species_id, stoich), ...]
    modifiers: List[str] = field(default_factory=list)  # [species_id, ...] - catalysts/enzymes
    kinetic_law: Optional[KineticLaw] = None
    reversible: bool = False
    enzyme: Optional[str] = None  # Legacy field for enzyme name
    
    # Phase 1 additions: SBML Compliance
    annotation: Optional[Annotation] = None
    sbo_term: Optional[str] = None
    
    # Additional properties
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __repr__(self) -> str:
        n_reactants = len(self.reactants)
        n_products = len(self.products)
        return f"Reaction(id={self.id!r}, name={self.name!r}, {n_reactants}→{n_products})"


@dataclass
class PathwayData:
    """
    Container for raw pathway data after SBML parsing.
    
    This is the output of Phase 2 (Parsing) and input to Phase 3 (Validation).
    
    Attributes:
        species: List of all species (metabolites)
        reactions: List of all reactions
        compartments: Dict mapping compartment IDs to names (legacy, for backward compatibility)
        parameters: Global parameters
        metadata: Pathway-level information (name, source, etc.)
        
    Phase 1 additions (SBML Compliance):
        events: List of SBML events (14th tuple component)
        compartments_enhanced: Dict mapping compartment IDs to Compartment objects
        unit_definitions: Dict mapping unit IDs to UnitDefinition objects
    """
    species: List[Species] = field(default_factory=list)
    reactions: List[Reaction] = field(default_factory=list)
    compartments: Dict[str, str] = field(default_factory=dict)  # {id: name} - legacy
    parameters: Dict[str, float] = field(default_factory=dict)
    
    # Phase 1 additions: SBML Compliance
    events: List[Event] = field(default_factory=list)
    compartments_enhanced: Dict[str, Compartment] = field(default_factory=dict)
    unit_definitions: Dict[str, UnitDefinition] = field(default_factory=dict)
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __repr__(self) -> str:
        return (f"PathwayData("
                f"species={len(self.species)}, "
                f"reactions={len(self.reactions)})")
    
    def get_species_by_id(self, species_id: str) -> Optional[Species]:
        """Get species by ID."""
        for species in self.species:
            if species.id == species_id:
                return species
        return None
    
    def get_reaction_by_id(self, reaction_id: str) -> Optional[Reaction]:
        """Get reaction by ID."""
        for reaction in self.reactions:
            if reaction.id == reaction_id:
                return reaction
        return None


@dataclass
class ProcessedPathwayData:
    """
    Container for enriched pathway data after post-processing.
    
    This is the output of Phase 4 (Post-Processing) and input to Phase 5 (Conversion).
    
    Includes everything from PathwayData plus:
        - Calculated positions (x, y coordinates)
        - Assigned colors (by compartment)
        - Normalized units (tokens instead of concentrations)
        - Resolved names (from IDs to readable names)
        - Compartment grouping
    
    Attributes:
        species: List of species (with tokens set)
        reactions: List of reactions
        positions: Dict mapping IDs to (x, y) coordinates
        colors: Dict mapping species IDs to hex colors
        compartment_groups: Dict mapping compartment to species IDs
        metadata: Enriched metadata
    """
    species: List[Species] = field(default_factory=list)
    reactions: List[Reaction] = field(default_factory=list)
    positions: Dict[str, Tuple[float, float]] = field(default_factory=dict)  # {id: (x, y)}
    colors: Dict[str, str] = field(default_factory=dict)  # {species_id: "#RRGGBB"}
    compartment_groups: Dict[str, List[str]] = field(default_factory=dict)  # {compartment: [species_ids]}
    
    # Original data preserved
    compartments: Dict[str, str] = field(default_factory=dict)
    compartments_enhanced: Dict[str, 'Compartment'] = field(default_factory=dict)  # Phase 1: Enhanced
    parameters: Dict[str, float] = field(default_factory=dict)
    
    # Enriched metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __repr__(self) -> str:
        return (f"ProcessedPathwayData("
                f"species={len(self.species)}, "
                f"reactions={len(self.reactions)}, "
                f"positioned={len(self.positions)})")
    
    def get_position(self, element_id: str) -> Optional[Tuple[float, float]]:
        """Get position for species or reaction by ID."""
        return self.positions.get(element_id)
    
    def get_color(self, species_id: str) -> Optional[str]:
        """Get color for species by ID."""
        return self.colors.get(species_id)


@dataclass
class ValidationResult:
    """
    Result of pathway validation.
    
    Attributes:
        is_valid: True if no errors found
        errors: List of error messages (prevent conversion)
        warnings: List of warning messages (allow conversion but notify)
    """
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def __repr__(self) -> str:
        status = "VALID" if self.is_valid else "INVALID"
        return f"ValidationResult({status}, errors={len(self.errors)}, warnings={len(self.warnings)})"
    
    def add_error(self, message: str) -> None:
        """Add an error message (makes validation invalid)."""
        self.errors.append(message)
        self.is_valid = False
    
    def add_warning(self, message: str) -> None:
        """Add a warning message (doesn't affect validity)."""
        self.warnings.append(message)


# Example usage:
if __name__ == "__main__":
    # Create example species
    glucose = Species(
        id="C00031",
        name="Glucose",
        compartment="cytosol",
        initial_concentration=5.0,  # mM
        formula="C6H12O6",
        kegg_id="C00031"
    )
    
    atp = Species(
        id="C00002",
        name="ATP",
        compartment="cytosol",
        initial_concentration=2.5,  # mM
        formula="C10H16N5O13P3",
        kegg_id="C00002"
    )
    
    g6p = Species(
        id="C00092",
        name="Glucose-6-phosphate",
        compartment="cytosol",
        initial_concentration=0.0,
        formula="C6H13O9P",
        kegg_id="C00092"
    )
    
    # Create example reaction
    hexokinase = Reaction(
        id="R00001",
        name="Hexokinase",
        reactants=[("C00031", 1.0), ("C00002", 1.0)],  # Glucose + ATP
        products=[("C00092", 1.0)],                     # → G6P
        enzyme="Hexokinase",
        kinetic_law=KineticLaw(
            formula="Vmax * [Glucose] / (Km + [Glucose])",
            rate_type="michaelis_menten",
            parameters={"Vmax": 10.0, "Km": 0.1}
        )
    )
    
    # Create pathway
    pathway = PathwayData(
        species=[glucose, atp, g6p],
        reactions=[hexokinase],
        compartments={"cytosol": "Cytoplasm"},
        metadata={"name": "Glycolysis (partial)", "organism": "Homo sapiens"}
    )
    
