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
        
        # DEBUG: Log first few positions from pathway data
        first_positions = list(self.pathway.positions.items())[:3]
        self.logger.warning(f"🔍 CONVERTER INPUT (pathway.positions):")
        for species_id, (x, y) in first_positions:
            self.logger.warning(f"   {species_id}: ({x:.1f}, {y:.1f})")
        
        for species in self.pathway.species:
            # Get position (from post-processor)
            if species.id not in self.pathway.positions:
                self.logger.warning(
                    f"Species '{species.id}' has no position, using fallback (100.0, 100.0)"
                )
            x, y = self.pathway.positions.get(species.id, (100.0, 100.0))
            
            # Get compartment color (from post-processor)
            compartment = species.compartment or "default"
            color_hex = self.pathway.colors.get(compartment, "#E8F4F8")
            
            # Convert hex color to RGB tuple (not used for now - colors too light)
            # border_color = self._hex_to_rgb(color_hex)
            
            # Create place
            place = self.document.create_place(
                x=x,
                y=y,
                label=species.name or species.id
            )
            
            # Set initial marking (from normalized tokens)
            place.set_tokens(species.initial_tokens)
            place.set_initial_marking(species.initial_tokens)
            
            # Keep default black border for visibility
            # TODO: Use compartment colors for fill instead of border
            # place.border_color = border_color
            
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
    
    Kinetic Law Handling:
    - michaelis_menten: Creates rate_function with michaelis_menten() call
    - mass_action: Sets transition to stochastic, uses k as lambda
    - Other: Keeps continuous with simple rate
    """
    
    def __init__(self, pathway: ProcessedPathwayData, document: DocumentModel,
                 species_to_place: Optional[Dict[str, Place]] = None):
        """
        Initialize reaction converter.
        
        Args:
            pathway: The processed pathway data
            document: The DocumentModel to populate
            species_to_place: Optional mapping from species ID to Place (for rate functions)
        """
        super().__init__(pathway, document)
        self.species_to_place = species_to_place or {}
    
    def convert(self) -> Dict[str, Transition]:
        """
        Convert all reactions to transitions.
        
        Returns:
            Dictionary mapping reaction ID to Transition object
        """
        reaction_to_transition = {}
        
        for reaction in self.pathway.reactions:
            # Get position (from post-processor)
            if reaction.id not in self.pathway.positions:
                self.logger.warning(
                    f"Reaction '{reaction.id}' has no position, using fallback (200.0, 200.0)"
                )
            x, y = self.pathway.positions.get(reaction.id, (200.0, 200.0))
            
            # Create transition
            transition = self.document.create_transition(
                x=x,
                y=y,
                label=reaction.name or reaction.id
            )
            
            # Initialize properties dict if not exists
            if not hasattr(transition, 'properties'):
                transition.properties = {}
            
            # Set kinetic properties based on kinetic law type
            self._configure_transition_kinetics(transition, reaction)
            
            # Store metadata for traceability
            if not hasattr(transition, 'metadata'):
                transition.metadata = {}
            transition.metadata['reaction_id'] = reaction.id
            transition.metadata['reversible'] = reaction.reversible
            if reaction.kinetic_law:
                transition.metadata['kinetic_formula'] = reaction.kinetic_law.formula
                transition.metadata['kinetic_parameters'] = reaction.kinetic_law.parameters
                transition.metadata['kinetic_type'] = reaction.kinetic_law.rate_type
            
            reaction_to_transition[reaction.id] = transition
            self.logger.debug(
                f"Converted reaction '{reaction.id}' to transition '{transition.name}' "
                f"(type: {transition.transition_type}, rate: {getattr(transition, 'rate', 'N/A')})"
            )
        
        self.logger.info(f"Converted {len(reaction_to_transition)} reactions to transitions")
        return reaction_to_transition
    
    def _configure_transition_kinetics(self, transition: Transition, reaction: Reaction) -> None:
        """
        Configure transition kinetics based on reaction kinetic law.
        
        Strategies:
        - michaelis_menten: Create rate_function with michaelis_menten(substrate, Vmax, Km)
        - mass_action: Set to stochastic with lambda rate
        - Other: Continuous with simple rate
        
        Args:
            transition: The transition to configure
            reaction: The reaction with kinetic law
        """
        if not reaction.kinetic_law:
            # No kinetic law - use default continuous
            transition.transition_type = "continuous"
            transition.rate = 1.0
            self.logger.debug(f"  No kinetic law, defaulting to continuous rate=1.0")
            return
        
        kinetic = reaction.kinetic_law
        
        # MICHAELIS-MENTEN: Create rate function
        if kinetic.rate_type == "michaelis_menten":
            self._setup_michaelis_menten(transition, reaction, kinetic)
        
        # MASS ACTION: Stochastic transition
        elif kinetic.rate_type == "mass_action":
            self._setup_mass_action(transition, reaction, kinetic)
        
        # OTHER: Continuous with simple rate
        else:
            transition.transition_type = "continuous"
            transition.rate = 1.0
            self.logger.debug(
                f"  Unknown kinetic type '{kinetic.rate_type}', defaulting to continuous"
            )
    
    def _setup_michaelis_menten(self, transition: Transition, reaction: Reaction, 
                                kinetic: 'KineticLaw') -> None:
        """
        Setup Michaelis-Menten kinetics with rate_function.
        
        For single substrate: michaelis_menten(S, Vmax, Km)
        For multiple substrates: Sequential Michaelis-Menten
          - michaelis_menten(S1, Vmax, Km1) * (S2/(Km2+S2)) * (S3/(Km3+S3)) * ...
        
        Args:
            transition: Transition to configure
            reaction: Reaction data
            kinetic: Kinetic law data
        """
        transition.transition_type = "continuous"
        
        # Extract parameters
        vmax = kinetic.parameters.get("Vmax", kinetic.parameters.get("vmax", 1.0))
        km = kinetic.parameters.get("Km", kinetic.parameters.get("km", 1.0))
        
        # Get all substrate places (use place objects, not names/IDs)
        substrate_places = []
        for species_id, stoich in reaction.reactants:
            place = self.species_to_place.get(species_id)
            if place:
                substrate_places.append(place)
        
        if not substrate_places:
            # No substrate places found, use simple rate
            transition.rate = vmax
            self.logger.warning(
                f"  Michaelis-Menten: Could not find substrate places, using Vmax={vmax} as rate"
            )
            return
        
        # Build rate function based on number of substrates
        # Use place.name for rate function string (this is acceptable - it's a formula string, not object reference)
        if len(substrate_places) == 1:
            # Single substrate - standard Michaelis-Menten
            rate_func = f"michaelis_menten({substrate_places[0].name}, {vmax}, {km})"
            self.logger.info(
                f"  Michaelis-Menten (single substrate): rate_function = '{rate_func}'"
            )
        else:
            # Multiple substrates - Sequential Michaelis-Menten
            # Primary substrate uses full MM, others use saturation terms
            # Formula: Vmax * [S1]/(Km+[S1]) * [S2]/(Km+[S2]) * ...
            
            # Primary substrate (first reactant)
            rate_func = f"michaelis_menten({substrate_places[0].name}, {vmax}, {km})"
            
            # Additional substrates as saturation terms
            for i, substrate_place in enumerate(substrate_places[1:], start=2):
                # Use same Km for all substrates (could be enhanced to use Km2, Km3, etc.)
                rate_func += f" * ({substrate_place.name} / ({km} + {substrate_place.name}))"
            
            self.logger.info(
                f"  Michaelis-Menten (sequential, {len(substrate_places)} substrates): "
                f"rate_function = '{rate_func}'"
            )
        
        transition.properties['rate_function'] = rate_func
        transition.rate = vmax  # Fallback for simple display
    
    def _setup_mass_action(self, transition: Transition, reaction: Reaction,
                          kinetic: 'KineticLaw') -> None:
        """
        Setup mass action kinetics (stochastic).
        
        Mass action is inherently stochastic for small molecule counts.
        Sets transition to stochastic with k as rate (lambda) parameter.
        
        Args:
            transition: Transition to configure
            reaction: Reaction data
            kinetic: Kinetic law data
        """
        # Mass action → Stochastic transition
        transition.transition_type = "stochastic"
        
        # Extract rate constant k
        k = kinetic.parameters.get("k", kinetic.parameters.get("rate_constant", 1.0))
        
        # For stochastic, rate attribute is the lambda parameter (used by StochasticBehavior)
        transition.rate = k
        
        self.logger.info(
            f"  Mass action: Set to stochastic with rate (lambda)={k}"
        )
        
        # Optional: Build rate function for multi-reactant mass action
        # Format: mass_action(reactant1, reactant2, rate_constant)
        if len(reaction.reactants) >= 2:
            reactant_places = []
            for species_id, _ in reaction.reactants[:2]:  # Up to 2 reactants
                place = self.species_to_place.get(species_id)
                if place:
                    reactant_places.append(place)
            
            if len(reactant_places) == 2:
                rate_func = f"mass_action({reactant_places[0].name}, {reactant_places[1].name}, {k})"
                transition.properties['rate_function'] = rate_func
                self.logger.info(f"    Rate function: '{rate_func}'")


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
            "compartments": list(pathway.compartments.keys()),
            "layout_type": pathway.metadata.get('layout_type', 'unknown')
        }
        
        # Convert species to places
        species_converter = SpeciesConverter(pathway, document)
        species_to_place = species_converter.convert()
        
        # Convert reactions to transitions (pass species_to_place for rate functions)
        reaction_converter = ReactionConverter(pathway, document, species_to_place)
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
    
    
    # Convert to DocumentModel
    converter = PathwayConverter()
    document = converter.convert(processed)
    
    place_count, transition_count, arc_count = document.get_object_count()
    
    for place in document.places:
        pass  # Process place
    
    for transition in document.transitions:
        pass  # Process transition
    
    for arc in document.arcs:
        source_label = arc.source.label if hasattr(arc.source, 'label') else arc.source.name
        target_label = arc.target.label if hasattr(arc.target, 'label') else arc.target.name
    
