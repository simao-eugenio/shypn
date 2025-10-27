#!/usr/bin/env python3
"""Pathway builder for converting fetched data to Shypn models.

This module converts FetchResult data from external sources (KEGG, BioModels, Reactome)
into Shypn Petri net objects (Place, Transition, Arc).

The mapping strategy:
- Species/Compounds → Places (with initial marking from concentrations)
- Reactions → Transitions (with kinetic parameters)
- Interactions → Arcs (with weights)

The builder maintains ID counters and naming conventions (P1, P2, T1, T2, A1, A2).
"""

import logging
from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass

from shypn.netobjs.place import Place
from shypn.netobjs.transition import Transition
from shypn.netobjs.arc import Arc
from shypn.crossfetch.models.fetch_result import FetchResult

logger = logging.getLogger(__name__)


@dataclass
class BuildResult:
    """Result of building a pathway from fetched data.
    
    Contains all created Petri net objects organized by type.
    
    Attributes:
        places: Dictionary mapping place ID to Place object
        transitions: Dictionary mapping transition ID to Transition object
        arcs: Dictionary mapping arc ID to Arc object
        metadata: Dictionary containing pathway metadata (name, source, etc.)
        warnings: List of warning messages generated during build
    """
    places: Dict[int, Place]
    transitions: Dict[int, Transition]
    arcs: Dict[int, Arc]
    metadata: Dict[str, any]
    warnings: List[str]
    
    def __str__(self) -> str:
        """String representation showing counts."""
        return (f"BuildResult(places={len(self.places)}, "
                f"transitions={len(self.transitions)}, "
                f"arcs={len(self.arcs)})")


class PathwayBuilder:
    """Converts FetchResult data to Shypn Petri net objects.
    
    This builder handles the conversion of pathway data from external sources
    (KEGG, BioModels, Reactome) into Shypn's native Place/Transition/Arc objects.
    
    The builder maintains:
    - ID counters for unique object IDs
    - Name counters for unique object names (P1, T1, A1)
    - Position layout for visual arrangement
    - Mapping from external IDs to internal objects
    
    Example:
        >>> from shypn.crossfetch.core.enrichment_pipeline import EnrichmentPipeline
        >>> pipeline = EnrichmentPipeline()
        >>> results = pipeline.fetch_and_select("hsa00010")  # Glycolysis
        >>> 
        >>> builder = PathwayBuilder()
        >>> build_result = builder.build_from_fetch_results(results)
        >>> 
        >>> print(f"Created {len(build_result.places)} places")
        >>> print(f"Created {len(build_result.transitions)} transitions")
        >>> print(f"Created {len(build_result.arcs)} arcs")
    """
    
    # Layout constants (for automatic positioning)
    PLACE_SPACING_X = 150.0  # Horizontal spacing between places
    PLACE_SPACING_Y = 100.0  # Vertical spacing between rows
    TRANSITION_OFFSET_Y = 50.0  # Offset transitions below places
    
    def __init__(self):
        """Initialize pathway builder."""
        # ID counters (start from 1)
        self._next_place_id = 1
        self._next_transition_id = 1
        self._next_arc_id = 1
        
        # Name counters (P1, P2, T1, T2, A1, A2)
        self._next_place_name = 1
        self._next_transition_name = 1
        self._next_arc_name = 1
        
        # Mapping from external IDs to internal objects
        self._species_to_place: Dict[str, Place] = {}
        self._reaction_to_transition: Dict[str, Transition] = {}
        
        # Created objects
        self._places: Dict[int, Place] = {}
        self._transitions: Dict[int, Transition] = {}
        self._arcs: Dict[int, Arc] = {}
        
        # Build warnings
        self._warnings: List[str] = []
        
        logger.info("PathwayBuilder initialized")
    
    def build_from_fetch_results(self, fetch_results: List[FetchResult]) -> BuildResult:
        """Build Petri net from fetched pathway data.
        
        This is the main entry point. It processes a list of FetchResult objects
        and converts them into Place/Transition/Arc objects.
        
        The build process:
        1. Extract all species/compounds → create Places
        2. Extract all reactions → create Transitions
        3. Extract all interactions → create Arcs
        4. Apply concentrations to Place initial markings
        5. Apply kinetic parameters to Transitions
        6. Layout objects in grid formation
        
        Args:
            fetch_results: List of FetchResult objects from pipeline
            
        Returns:
            BuildResult: Contains all created objects and metadata
            
        Raises:
            ValueError: If fetch_results is empty or invalid
        """
        if not fetch_results:
            raise ValueError("Cannot build pathway: fetch_results is empty")
        
        logger.info(f"Building pathway from {len(fetch_results)} fetch results")
        
        # Reset state for new build
        self._reset()
        
        # Collect all species and reactions from all results
        all_species = set()
        all_reactions = []
        all_interactions = []
        concentrations = {}
        kinetics = {}
        
        # Extract pathway metadata from first result
        metadata = {
            'pathway_id': fetch_results[0].pathway_id,
            'pathway_name': fetch_results[0].data.get('name', 'Imported Pathway'),
            'source': fetch_results[0].source,
            'data_types': [r.data_type for r in fetch_results]
        }
        
        # Process each fetch result
        for result in fetch_results:
            data = result.data
            
            # Extract species (as strings, not Place objects)
            if 'species' in data:
                # Species can be list of dicts or list of strings
                for species in data['species']:
                    if isinstance(species, dict):
                        species_id = species.get('id') or species.get('name')
                    else:
                        species_id = str(species)
                    if species_id:
                        all_species.add(species_id)
            
            # Extract compounds (KEGG format)
            if 'compounds' in data:
                for compound in data['compounds']:
                    if isinstance(compound, dict):
                        compound_id = compound.get('id') or compound.get('name')
                    else:
                        compound_id = str(compound)
                    if compound_id:
                        all_species.add(compound_id)
            
            # Extract reactions
            if 'reactions' in data:
                reactions = data['reactions']
                if isinstance(reactions, list):
                    all_reactions.extend(reactions)
                elif isinstance(reactions, dict):
                    all_reactions.extend(reactions.values())
            
            # Extract interactions
            if 'interactions' in data:
                interactions = data['interactions']
                if isinstance(interactions, list):
                    all_interactions.extend(interactions)
            
            # Extract concentrations
            if 'concentrations' in data:
                conc_data = data['concentrations']
                if isinstance(conc_data, dict):
                    concentrations.update(conc_data)
            
            # Extract kinetics
            if 'kinetics' in data:
                kinetic_data = data['kinetics']
                if isinstance(kinetic_data, dict):
                    kinetics.update(kinetic_data)
        
        logger.info(f"Extracted: {len(all_species)} species, {len(all_reactions)} reactions, "
                   f"{len(all_interactions)} interactions")
        
        # Step 1: Create Places from species/compounds
        self._create_places_from_species(all_species)
        
        # Step 2: Create Transitions from reactions
        self._create_transitions_from_reactions(all_reactions)
        
        # Step 3: Create Arcs from interactions
        self._create_arcs_from_interactions(all_interactions)
        
        # Step 4: Apply concentrations to Places
        self._apply_concentrations(concentrations)
        
        # Step 5: Apply kinetics to Transitions
        self._apply_kinetics(kinetics)
        
        # Step 6: Layout objects (if not already positioned)
        self._auto_layout()
        
        # Create result
        result = BuildResult(
            places=self._places.copy(),
            transitions=self._transitions.copy(),
            arcs=self._arcs.copy(),
            metadata=metadata,
            warnings=self._warnings.copy()
        )
        
        logger.info(f"Build complete: {result}")
        if self._warnings:
            logger.warning(f"Build generated {len(self._warnings)} warnings")
        
        return result
    
    def _reset(self):
        """Reset builder state for new build."""
        self._next_place_id = 1
        self._next_transition_id = 1
        self._next_arc_id = 1
        self._next_place_name = 1
        self._next_transition_name = 1
        self._next_arc_name = 1
        
        self._species_to_place.clear()
        self._reaction_to_transition.clear()
        self._places.clear()
        self._transitions.clear()
        self._arcs.clear()
        self._warnings.clear()
    
    def _create_places_from_species(self, species: Set[str]):
        """Create Place objects from species IDs.
        
        Args:
            species: Set of species ID strings
        """
        for species_id in sorted(species):  # Sort for deterministic order
            place_id = self._next_place_id
            place_name = f"P{self._next_place_name}"
            
            # Create place at origin (will be positioned later)
            place = Place(
                x=0.0,
                y=0.0,
                id=place_id,
                name=place_name,
                label=species_id  # Use species ID as label
            )
            
            self._places[place_id] = place
            self._species_to_place[species_id] = place
            
            self._next_place_id += 1
            self._next_place_name += 1
        
        logger.debug(f"Created {len(self._places)} places")
    
    def _create_transitions_from_reactions(self, reactions: List[Dict]):
        """Create Transition objects from reaction data.
        
        Args:
            reactions: List of reaction dictionaries
        """
        for reaction in reactions:
            if not isinstance(reaction, dict):
                self._warnings.append(f"Skipping non-dict reaction: {reaction}")
                continue
            
            reaction_id = reaction.get('id') or reaction.get('name', f'R{self._next_transition_name}')
            
            transition_id = self._next_transition_id
            transition_name = f"T{self._next_transition_name}"
            
            # Create transition at origin (will be positioned later)
            transition = Transition(
                x=0.0,
                y=0.0,
                id=transition_id,
                name=transition_name,
                label=reaction_id  # Use reaction ID as label
            )
            
            # Set transition properties if available
            if 'reversible' in reaction:
                transition.properties = {'reversible': reaction['reversible']}
            
            self._transitions[transition_id] = transition
            self._reaction_to_transition[reaction_id] = transition
            
            self._next_transition_id += 1
            self._next_transition_name += 1
            
            # Create arcs from substrates to transition
            substrates = reaction.get('substrates', []) or reaction.get('reactants', [])
            for substrate in substrates:
                substrate_id = substrate if isinstance(substrate, str) else substrate.get('id') or substrate.get('name')
                if substrate_id in self._species_to_place:
                    source_place = self._species_to_place[substrate_id]
                    self._create_arc(source_place, transition, weight=1)
                else:
                    self._warnings.append(f"Substrate '{substrate_id}' not found in species")
            
            # Create arcs from transition to products
            products = reaction.get('products', [])
            for product in products:
                product_id = product if isinstance(product, str) else product.get('id') or product.get('name')
                if product_id in self._species_to_place:
                    target_place = self._species_to_place[product_id]
                    self._create_arc(transition, target_place, weight=1)
                else:
                    self._warnings.append(f"Product '{product_id}' not found in species")
        
        logger.debug(f"Created {len(self._transitions)} transitions")
    
    def _create_arcs_from_interactions(self, interactions: List[Dict]):
        """Create Arc objects from interaction data.
        
        This handles explicit interaction data (e.g., from protein-protein interactions).
        Reaction-based arcs are created in _create_transitions_from_reactions.
        
        Args:
            interactions: List of interaction dictionaries
        """
        for interaction in interactions:
            if not isinstance(interaction, dict):
                continue
            
            source_id = interaction.get('source')
            target_id = interaction.get('target')
            interaction_type = interaction.get('type', 'unknown')
            
            if not source_id or not target_id:
                self._warnings.append(f"Skipping interaction with missing source/target: {interaction}")
                continue
            
            # Look up source and target objects
            source_obj = self._species_to_place.get(source_id) or self._reaction_to_transition.get(source_id)
            target_obj = self._species_to_place.get(target_id) or self._reaction_to_transition.get(target_id)
            
            if not source_obj or not target_obj:
                self._warnings.append(f"Cannot create arc: source '{source_id}' or target '{target_id}' not found")
                continue
            
            # Create arc (will validate bipartite constraint)
            try:
                weight = interaction.get('stoichiometry', 1)
                self._create_arc(source_obj, target_obj, weight=weight)
            except ValueError as e:
                self._warnings.append(f"Cannot create arc for interaction: {e}")
        
        logger.debug(f"Created {len(self._arcs)} total arcs")
    
    def _create_arc(self, source, target, weight: int = 1) -> Optional[Arc]:
        """Create an Arc object between source and target.
        
        Args:
            source: Source Place or Transition
            target: Target Place or Transition
            weight: Arc weight (multiplicity)
            
        Returns:
            Arc object if created, None if validation failed
        """
        try:
            arc_id = self._next_arc_id
            arc_name = f"A{self._next_arc_name}"
            
            arc = Arc(
                source=source,
                target=target,
                id=arc_id,
                name=arc_name,
                weight=weight
            )
            
            self._arcs[arc_id] = arc
            self._next_arc_id += 1
            self._next_arc_name += 1
            
            return arc
        except ValueError as e:
            # Arc validation failed (e.g., Place→Place)
            logger.debug(f"Arc creation failed: {e}")
            return None
    
    def _apply_concentrations(self, concentrations: Dict[str, any]):
        """Apply concentration data to Place initial markings.
        
        Converts concentration values to token counts using simple scaling.
        
        Args:
            concentrations: Dictionary mapping species ID to concentration data
        """
        if not concentrations:
            return
        
        for species_id, conc_data in concentrations.items():
            place = self._species_to_place.get(species_id)
            if not place:
                continue
            
            # Extract concentration value
            if isinstance(conc_data, dict):
                value = conc_data.get('value', 0.0)
                unit = conc_data.get('unit', 'M')
            else:
                value = float(conc_data)
                unit = 'M'
            
            # Simple conversion: assume 1 token = 1 mM
            # This is a placeholder - real conversion depends on volume, etc.
            if unit == 'M':
                tokens = int(value * 1000)  # M → mM
            elif unit == 'mM':
                tokens = int(value)
            elif unit == 'µM' or unit == 'uM':
                tokens = int(value / 1000)  # µM → mM
            else:
                tokens = int(value)
            
            place.set_initial_marking(max(1, tokens))
            place.set_tokens(place.initial_marking)
            
            logger.debug(f"Set {place.name} initial marking to {tokens} (from {value} {unit})")
    
    def _apply_kinetics(self, kinetics: Dict[str, any]):
        """Apply kinetic parameters to Transitions.
        
        Args:
            kinetics: Dictionary mapping reaction ID to kinetic data
        """
        if not kinetics:
            return
        
        for reaction_id, kinetic_data in kinetics.items():
            transition = self._reaction_to_transition.get(reaction_id)
            if not transition:
                continue
            
            # Extract kinetic parameters
            if isinstance(kinetic_data, dict):
                # Set rate constant
                if 'rate_constant' in kinetic_data:
                    transition.rate = float(kinetic_data['rate_constant'])
                elif 'k' in kinetic_data:
                    transition.rate = float(kinetic_data['k'])
                
                # Set transition type
                if 'law_type' in kinetic_data:
                    law_type = kinetic_data['law_type'].lower()
                    if 'mass_action' in law_type:
                        # Mass action is STOCHASTIC (scientific basis: Gillespie 1977)
                        # Molecular collisions are probabilistic (Brownian motion)
                        # Exponential time distribution, NOT deterministic fixed delay
                        transition.transition_type = 'stochastic'
                    elif 'michaelis' in law_type or 'enzymatic' in law_type:
                        transition.transition_type = 'continuous'
                    elif 'stochastic' in law_type:
                        transition.transition_type = 'stochastic'
                
                # Store full kinetic data in properties
                if not hasattr(transition, 'properties'):
                    transition.properties = {}
                transition.properties['kinetics'] = kinetic_data
            
            logger.debug(f"Applied kinetics to {transition.name}: rate={transition.rate}")
    
    def _auto_layout(self):
        """Automatically position objects in a grid layout.
        
        Simple layout strategy:
        - Places in rows (grid formation)
        - Transitions positioned below their reactant places
        - Arcs automatically connect based on source/target positions
        """
        # Position places in grid
        places_per_row = 5
        for i, place in enumerate(self._places.values()):
            row = i // places_per_row
            col = i % places_per_row
            
            place.x = col * self.PLACE_SPACING_X + 100
            place.y = row * self.PLACE_SPACING_Y + 100
        
        # Position transitions below their input places
        for transition in self._transitions.values():
            # Find input places (arcs from places to this transition)
            input_places = []
            for arc in self._arcs.values():
                if arc.target == transition and isinstance(arc.source, Place):
                    input_places.append(arc.source)
            
            if input_places:
                # Position transition at average of input place positions, offset downward
                avg_x = sum(p.x for p in input_places) / len(input_places)
                avg_y = sum(p.y for p in input_places) / len(input_places)
                transition.x = avg_x
                transition.y = avg_y + self.TRANSITION_OFFSET_Y
            else:
                # No inputs: position at grid position
                transition.x = 200.0
                transition.y = 200.0
        
        logger.debug("Auto-layout complete")
