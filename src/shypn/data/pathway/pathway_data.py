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
class Species:
    """
    Represents a biochemical species (metabolite/compound).
    
    Will be converted to a Place in the Petri net.
    
    Attributes:
        id: Unique identifier (e.g., "C00031" for glucose)
        name: Human-readable name (e.g., "Glucose")
        compartment: Cellular location (e.g., "cytosol")
        initial_concentration: Initial amount (mM, molecules, etc.)
        initial_tokens: Token count after unit normalization
        formula: Chemical formula (e.g., "C6H12O6")
        charge: Electrical charge
        chebi_id: ChEBI database ID
        kegg_id: KEGG database ID
        metadata: Additional properties
    """
    id: str
    name: Optional[str] = None
    compartment: Optional[str] = None
    initial_concentration: float = 0.0
    initial_tokens: int = 0
    formula: Optional[str] = None
    charge: Optional[int] = None
    compartment_volume: float = 1.0  # For unit conversion
    
    # Database cross-references
    chebi_id: Optional[str] = None
    kegg_id: Optional[str] = None
    
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
        kinetic_law: Rate law (optional)
        reversible: Whether reaction can go both directions
        enzyme: Enzyme catalyst name (optional)
        metadata: Additional properties
    """
    id: str
    name: Optional[str] = None
    reactants: List[Tuple[str, float]] = field(default_factory=list)  # [(species_id, stoich), ...]
    products: List[Tuple[str, float]] = field(default_factory=list)   # [(species_id, stoich), ...]
    kinetic_law: Optional[KineticLaw] = None
    reversible: bool = False
    enzyme: Optional[str] = None
    
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
        compartments: Dict mapping compartment IDs to names
        parameters: Global parameters
        metadata: Pathway-level information (name, source, etc.)
    """
    species: List[Species] = field(default_factory=list)
    reactions: List[Reaction] = field(default_factory=list)
    compartments: Dict[str, str] = field(default_factory=dict)  # {id: name}
    parameters: Dict[str, float] = field(default_factory=dict)
    
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
    
