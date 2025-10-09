"""KEGG pathway data structures.

This module defines data classes for representing KEGG pathway elements
extracted from KGML (KEGG Markup Language) XML files.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple


@dataclass
class KEGGGraphics:
    """Graphics information for a KGML entry.
    
    Attributes:
        name: Display name (e.g., compound name, enzyme name)
        x: X coordinate in KEGG map (pixels)
        y: Y coordinate in KEGG map (pixels)
        width: Width in pixels
        height: Height in pixels
        fgcolor: Foreground color (hex)
        bgcolor: Background color (hex)
        type: Shape type (rectangle, circle, line, etc.)
    """
    name: str = ""
    x: float = 0.0
    y: float = 0.0
    width: float = 46.0
    height: float = 17.0
    fgcolor: str = "#000000"
    bgcolor: str = "#FFFFFF"
    type: str = "rectangle"


@dataclass
class KEGGEntry:
    """A node in the pathway graph.
    
    Types:
        - gene: Gene/protein product
        - enzyme: Enzyme (may be deprecated, use gene instead)
        - compound: Chemical compound (metabolite)
        - map: Link to another pathway map
        - group: Complex/group of entries
        - ortholog: KEGG Orthology (KO) entry
    
    Attributes:
        id: Entry ID (unique within pathway)
        name: KEGG identifier(s), space-separated (e.g., "hsa:226 hsa:229")
        type: Entry type
        reaction: Associated reaction ID (e.g., "rn:R01068")
        link: URL to KEGG database entry
        graphics: Visual representation data
        components: For groups, list of member entry IDs
    """
    id: str
    name: str
    type: str
    reaction: Optional[str] = None
    link: Optional[str] = None
    graphics: KEGGGraphics = field(default_factory=KEGGGraphics)
    components: List[str] = field(default_factory=list)
    
    def get_kegg_ids(self) -> List[str]:
        """Extract individual KEGG IDs from name field.
        
        Returns:
            List of KEGG identifiers (e.g., ["hsa:226", "hsa:229"])
        """
        return [id.strip() for id in self.name.split() if id.strip()]
    
    def is_compound(self) -> bool:
        """Check if this entry represents a compound."""
        return self.type == "compound"
    
    def is_gene(self) -> bool:
        """Check if this entry represents a gene/enzyme."""
        return self.type in ("gene", "enzyme", "ortholog")


@dataclass
class KEGGSubstrate:
    """Substrate (input) for a reaction.
    
    Attributes:
        id: Entry ID of the substrate compound
        name: KEGG compound ID (e.g., "cpd:C00031")
        stoichiometry: Stoichiometric coefficient (default: 1)
    """
    id: str
    name: str
    stoichiometry: int = 1


@dataclass
class KEGGProduct:
    """Product (output) of a reaction.
    
    Attributes:
        id: Entry ID of the product compound
        name: KEGG compound ID (e.g., "cpd:C00668")
        stoichiometry: Stoichiometric coefficient (default: 1)
    """
    id: str
    name: str
    stoichiometry: int = 1


@dataclass
class KEGGReaction:
    """A metabolic reaction.
    
    Attributes:
        id: Reaction entry ID (unique within pathway)
        name: KEGG reaction ID (e.g., "rn:R01068")
        type: Reaction type (reversible, irreversible)
        substrates: List of substrate compounds (inputs)
        products: List of product compounds (outputs)
    """
    id: str
    name: str
    type: str  # "reversible" or "irreversible"
    substrates: List[KEGGSubstrate] = field(default_factory=list)
    products: List[KEGGProduct] = field(default_factory=list)
    
    def is_reversible(self) -> bool:
        """Check if reaction is reversible."""
        return self.type == "reversible"


@dataclass
class KEGGRelationSubtype:
    """Subtype detail for a relation.
    
    Attributes:
        name: Subtype name (e.g., "activation", "inhibition", "compound")
        value: Associated entry ID or value
    """
    name: str
    value: str


@dataclass
class KEGGRelation:
    """A relationship between two entries (interaction, regulation).
    
    Types:
        - ECrel: Enzyme-enzyme relation
        - PPrel: Protein-protein interaction
        - GErel: Gene expression interaction
        - PCrel: Protein-compound interaction
        - maplink: Link between pathways
    
    Subtypes:
        - compound: Shared compound
        - activation: Positive regulation
        - inhibition: Negative regulation
        - expression: Gene expression
        - repression: Gene repression
        - indirect effect: Indirect effect
        - state change: State transition
        - binding/association: Physical binding
        - dissociation: Unbinding
        - missing interaction: Known missing link
        - phosphorylation: Phosphorylation
        - dephosphorylation: Dephosphorylation
        - glycosylation: Glycosylation
        - ubiquitination: Ubiquitination
        - methylation: Methylation
    
    Attributes:
        entry1: First entry ID
        entry2: Second entry ID
        type: Relation type
        subtypes: List of subtype details
    """
    entry1: str
    entry2: str
    type: str
    subtypes: List[KEGGRelationSubtype] = field(default_factory=list)
    
    def get_subtype_names(self) -> List[str]:
        """Get list of subtype names."""
        return [st.name for st in self.subtypes]
    
    def is_activation(self) -> bool:
        """Check if this is an activation relation."""
        return "activation" in self.get_subtype_names()
    
    def is_inhibition(self) -> bool:
        """Check if this is an inhibition relation."""
        return "inhibition" in self.get_subtype_names()


@dataclass
class KEGGPathway:
    """Complete KEGG pathway representation.
    
    Attributes:
        number: Pathway number (e.g., "00010")
        name: Full pathway name (e.g., "path:hsa00010")
        org: Organism code (e.g., "hsa" for human)
        title: Pathway title (e.g., "Glycolysis / Gluconeogenesis")
        image: URL to pathway image
        link: URL to pathway page
        entries: Dictionary of entries by ID
        reactions: List of reactions
        relations: List of relations
    """
    number: str
    name: str
    org: str
    title: str
    image: str = ""
    link: str = ""
    entries: Dict[str, KEGGEntry] = field(default_factory=dict)
    reactions: List[KEGGReaction] = field(default_factory=list)
    relations: List[KEGGRelation] = field(default_factory=list)
    
    def get_compounds(self) -> List[KEGGEntry]:
        """Get all compound entries."""
        return [e for e in self.entries.values() if e.is_compound()]
    
    def get_genes(self) -> List[KEGGEntry]:
        """Get all gene/enzyme entries."""
        return [e for e in self.entries.values() if e.is_gene()]
    
    def get_entry_by_id(self, entry_id: str) -> Optional[KEGGEntry]:
        """Get entry by ID.
        
        Args:
            entry_id: Entry ID to look up
            
        Returns:
            KEGGEntry or None if not found
        """
        return self.entries.get(entry_id)
