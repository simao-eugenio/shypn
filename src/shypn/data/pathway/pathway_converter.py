"""
Pathway Converter

Converts processed pathway data to DocumentModel (Petri net).

Maps biological concepts to Petri net elements:
- Species → Places (with initial tokens from concentration)
- Reactions → Transitions (with kinetic properties)
- Stoichiometry → Arc weights
- Compartments → Visual grouping (colors, positions)

Uses clean OOP architecture:
- BaseConverter: Abstract base for all converters
- Specialized converters: Each handles one type of mapping
- PathwayConverter: Minimal coordinator

Author: Shypn Development Team
Date: October 2025
"""

from typing import Dict, List, Optional
import logging

from .pathway_data import ProcessedPathwayData, Species, Reaction
from shypn.data.canvas.document_model import DocumentModel
from shypn.netobjs.place import Place
from shypn.netobjs.transition import Transition
from shypn.netobjs.arc import Arc


class BaseConverter:
    """
    Abstract base class for all converters.
    
    All specialized converters inherit from this class and implement
    the convert() method.
    """
    
    def __init__(self, pathway: ProcessedPathwayData, document: DocumentModel):
        """
        Initialize converter.
        
        Args:
            pathway: The processed pathway data to convert
            document: The DocumentModel to populate
        """
        self.pathway = pathway
        self.document = document
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def convert(self) -> Dict:
        """
        Convert pathway elements to document model.
        
        Returns:
            Dictionary with mapping information (species_id → Place, etc.)
        """
        raise NotImplementedError("Subclasses must implement convert()")


class SpeciesConverter(BaseConverter):
    """
    Converts species to places.
    
    Maps:
    - Species ID → Place name/label
    - Initial tokens → Place marking
    - Position → Place position
    - Compartment color → Place border color
    """
    
    def convert(self) -> Dict[str, Place]:
        """
        Convert all species to places.
        
        Returns:
            Dictionary mapping species ID to Place object
        """
        species_to_place = {}
        
        for species in self.pathway.species:
            # Get position (from post-processor)
            x, y = self.pathway.positions.get(species.id, (100.0, 100.0))
            
            # Get compartment color (from post-processor)
            compartment = species.compartment or "default"
            color_hex = self.pathway.colors.get(compartment, "#E8F4F8")
            
            # Convert hex color to RGB tuple
            border_color = self._hex_to_rgb(color_hex)
            
            # Create place
            place = self.document.create_place(
                x=x,
                y=y,
                label=species.name or species.id
            )
            
            # Set initial marking (from normalized tokens)
            place.set_tokens(species.initial_tokens)
            place.set_initial_marking(species.initial_tokens)
            
            # Set visual properties
            place.border_color = border_color
            
            # Store metadata for traceability
            if not hasattr(place, 'metadata'):
                place.metadata = {}
            place.metadata['species_id'] = species.id
            place.metadata['concentration'] = species.initial_concentration
            place.metadata['compartment'] = species.compartment
            
            species_to_place[species.id] = place
            self.logger.debug(
                f"Converted species '{species.id}' to place '{place.name}' "
                f"with {place.tokens} tokens"
            )
        
        self.logger.info(f"Converted {len(species_to_place)} species to places")
        return species_to_place
    
    @staticmethod
    def _hex_to_rgb(hex_color: str) -> tuple:
        """Convert hex color to RGB tuple.
        
        Args:
            hex_color: Hex color string (e.g., "#E8F4F8")
            
        Returns:
            RGB tuple with values 0.0-1.0 (e.g., (0.91, 0.96, 0.97))
        """
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) / 255.0 for i in (0, 2, 4))


class ReactionConverter(BaseConverter):
    """
    Converts reactions to transitions.
    
    Maps:
    - Reaction ID → Transition name/label
    - Position → Transition position
    - Kinetic properties → Transition type and rate
    - Reversibility → Could create reverse arcs (not implemented yet)
    """
    
    def convert(self) -> Dict[str, Transition]:
        """
        Convert all reactions to transitions.
        
        Returns:
            Dictionary mapping reaction ID to Transition object
        """
        reaction_to_transition = {}
        
        for reaction in self.pathway.reactions:
            # Get position (from post-processor)
            x, y = self.pathway.positions.get(reaction.id, (200.0, 200.0))
            
            # Create transition
            transition = self.document.create_transition(
                x=x,
                y=y,
                label=reaction.name or reaction.id
            )
            
            # Set kinetic properties
            if reaction.kinetic_law:
                # Map kinetic law type to transition type
                if reaction.kinetic_law.rate_type == "michaelis_menten":
                    transition.transition_type = "continuous"
                    # Extract Vmax as rate if available
                    if "Vmax" in reaction.kinetic_law.parameters:
                        transition.rate = reaction.kinetic_law.parameters["Vmax"]
                elif reaction.kinetic_law.rate_type == "mass_action":
                    transition.transition_type = "stochastic"
                    # Extract rate constant
                    if "k" in reaction.kinetic_law.parameters:
                        transition.rate = reaction.kinetic_law.parameters["k"]
                else:
                    transition.transition_type = "timed"
                    transition.rate = 1.0
            else:
                # Default: immediate transition
                transition.transition_type = "immediate"
                transition.rate = 1.0
            
            # Store metadata for traceability
            if not hasattr(transition, 'metadata'):
                transition.metadata = {}
            transition.metadata['reaction_id'] = reaction.id
            transition.metadata['reversible'] = reaction.reversible
            if reaction.kinetic_law:
                transition.metadata['kinetic_formula'] = reaction.kinetic_law.formula
                transition.metadata['kinetic_parameters'] = reaction.kinetic_law.parameters
            
            reaction_to_transition[reaction.id] = transition
            self.logger.debug(
                f"Converted reaction '{reaction.id}' to transition '{transition.name}' "
                f"(type: {transition.transition_type}, rate: {transition.rate})"
            )
        
        self.logger.info(f"Converted {len(reaction_to_transition)} reactions to transitions")
        return reaction_to_transition


class ArcConverter(BaseConverter):
    """
    Converts stoichiometric relationships to arcs.
    
    Maps:
    - Reactants → Arcs from Place to Transition (weight = stoichiometry)
    - Products → Arcs from Transition to Place (weight = stoichiometry)
    """
    
    def __init__(self, pathway: ProcessedPathwayData, document: DocumentModel,
                 species_to_place: Dict[str, Place],
                 reaction_to_transition: Dict[str, Transition]):
        """
        Initialize arc converter.
        
        Args:
            pathway: The processed pathway data
            document: The DocumentModel to populate
            species_to_place: Mapping from species ID to Place
            reaction_to_transition: Mapping from reaction ID to Transition
        """
        super().__init__(pathway, document)
        self.species_to_place = species_to_place
        self.reaction_to_transition = reaction_to_transition
    
    def convert(self) -> List[Arc]:
        """
        Convert all stoichiometric relationships to arcs.
        
        Returns:
            List of created Arc objects
        """
        arcs = []
        
        for reaction in self.pathway.reactions:
            transition = self.reaction_to_transition.get(reaction.id)
            if not transition:
                self.logger.warning(f"Transition not found for reaction '{reaction.id}'")
                continue
            
            # Create input arcs (reactants → transition)
            for species_id, stoichiometry in reaction.reactants:
                place = self.species_to_place.get(species_id)
                if not place:
                    self.logger.warning(
                        f"Place not found for reactant species '{species_id}' "
                        f"in reaction '{reaction.id}'"
                    )
                    continue
                
                # Create arc from place to transition
                weight = max(1, round(stoichiometry))  # Convert to integer
                arc = self.document.create_arc(
                    source=place,
                    target=transition,
                    weight=weight
                )
                
                if arc:
                    arcs.append(arc)
                    self.logger.debug(
                        f"Created input arc: {place.name} → {transition.name} (weight: {weight})"
                    )
            
            # Create output arcs (transition → products)
            for species_id, stoichiometry in reaction.products:
                place = self.species_to_place.get(species_id)
                if not place:
                    self.logger.warning(
                        f"Place not found for product species '{species_id}' "
                        f"in reaction '{reaction.id}'"
                    )
                    continue
                
                # Create arc from transition to place
                weight = max(1, round(stoichiometry))  # Convert to integer
                arc = self.document.create_arc(
                    source=transition,
                    target=place,
                    weight=weight
                )
                
                if arc:
                    arcs.append(arc)
                    self.logger.debug(
                        f"Created output arc: {transition.name} → {place.name} (weight: {weight})"
                    )
        
        self.logger.info(f"Created {len(arcs)} arcs")
        return arcs


class PathwayConverter:
    """
    Main pathway converter coordinator.
    
    Converts ProcessedPathwayData to DocumentModel:
    - Creates DocumentModel instance
    - Delegates to specialized converters
    - Returns complete document ready for simulation
    
    Minimal coordinator pattern - most logic is in specialized converters.
    """
    
    def __init__(self):
        """Initialize pathway converter."""
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def convert(self, pathway: ProcessedPathwayData) -> DocumentModel:
        """
        Convert processed pathway to DocumentModel.
        
        Args:
            pathway: The processed pathway data (with layout, colors, tokens, etc.)
        
        Returns:
            DocumentModel with all Petri net objects created
        """
        self.logger.info(f"Converting pathway: {pathway.metadata.get('name', 'Unknown')}")
        
        # Create empty document
        document = DocumentModel()
        
        # Store pathway metadata in document
        document.metadata = {
            "source": "biochemical_pathway",
            "pathway_name": pathway.metadata.get('name', 'Unknown'),
            "species_count": len(pathway.species),
            "reactions_count": len(pathway.reactions),
            "compartments": list(pathway.compartments.keys())
        }
        
        # Convert species to places
        species_converter = SpeciesConverter(pathway, document)
        species_to_place = species_converter.convert()
        
        # Convert reactions to transitions
        reaction_converter = ReactionConverter(pathway, document)
        reaction_to_transition = reaction_converter.convert()
        
        # Convert stoichiometry to arcs
        arc_converter = ArcConverter(
            pathway, document,
            species_to_place, reaction_to_transition
        )
        arcs = arc_converter.convert()
        
        # Log summary
        place_count, transition_count, arc_count = document.get_object_count()
        self.logger.info(
            f"Conversion complete: {place_count} places, "
            f"{transition_count} transitions, {arc_count} arcs"
        )
        
        return document


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 70)
    print("PATHWAY CONVERTER")
    print("=" * 70)
    
    # Example: Load and convert pathway
    from .pathway_data import Species, Reaction, KineticLaw, PathwayData
    from .pathway_postprocessor import PathwayPostProcessor
    
    # Create example pathway
    glucose = Species(
        id="glucose",
        name="Glucose",
        compartment="cytosol",
        initial_concentration=5.0
    )
    
    atp = Species(
        id="atp",
        name="ATP",
        compartment="cytosol",
        initial_concentration=2.5
    )
    
    g6p = Species(
        id="g6p",
        name="Glucose-6-phosphate",
        compartment="cytosol",
        initial_concentration=0.0
    )
    
    hexokinase = Reaction(
        id="hexokinase",
        name="Hexokinase",
        reactants=[("glucose", 1.0), ("atp", 1.0)],
        products=[("g6p", 1.0)],
        kinetic_law=KineticLaw(
            formula="Vmax * glucose / (Km + glucose)",
            rate_type="michaelis_menten",
            parameters={"Vmax": 10.0, "Km": 0.1}
        )
    )
    
    pathway = PathwayData(
        species=[glucose, atp, g6p],
        reactions=[hexokinase],
        compartments={"cytosol": "Cytoplasm"},
        metadata={"name": "Simple Glycolysis"}
    )
    
    # Post-process
    postprocessor = PathwayPostProcessor(spacing=150.0, scale_factor=2.0)
    processed = postprocessor.process(pathway)
    
    print(f"\nProcessed pathway:")
    print(f"  Species: {len(processed.species)}")
    print(f"  Reactions: {len(processed.reactions)}")
    print(f"  Positions: {len(processed.positions)}")
    
    # Convert to DocumentModel
    converter = PathwayConverter()
    document = converter.convert(processed)
    
    print(f"\nDocument model:")
    place_count, transition_count, arc_count = document.get_object_count()
    print(f"  Places: {place_count}")
    print(f"  Transitions: {transition_count}")
    print(f"  Arcs: {arc_count}")
    
    print(f"\nPlace details:")
    for place in document.places:
        print(f"  {place.label}: {place.tokens} tokens at ({place.x:.1f}, {place.y:.1f})")
    
    print(f"\nTransition details:")
    for transition in document.transitions:
        print(f"  {transition.label}: {transition.transition_type}, rate={transition.rate}")
    
    print(f"\nArc details:")
    for arc in document.arcs:
        source_label = arc.source.label if hasattr(arc.source, 'label') else arc.source.name
        target_label = arc.target.label if hasattr(arc.target, 'label') else arc.target.name
        print(f"  {source_label} → {target_label} (weight: {arc.weight})")
    
    print("\n" + "=" * 70)
    print("Converter ready for use!")
    print("=" * 70)
