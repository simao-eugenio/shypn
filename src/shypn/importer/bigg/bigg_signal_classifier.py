"""Signal classifier for BiGG models.

Identifies and classifies signal places (energy metabolites, regulatory genes)
in BiGG-imported models.
"""

import logging
from typing import List

from shypn.netobjs.place import Place
from shypn.netobjs.signal_type import SignalType
from .bigg_namespace_parser import BiGGNamespaceParser


class BiGGSignalClassifier:
    """Service for classifying signal places in BiGG models.
    
    Automatically detects energy metabolites and assigns appropriate
    signal types and hierarchy layers according to signal hierarchy theory.
    """
    
    def __init__(self):
        """Initialize signal classifier."""
        self.logger = logging.getLogger(self.__class__.__name__)
        self.parser = BiGGNamespaceParser()
    
    def classify_energy_signals(self, places: List[Place]) -> List[Place]:
        """Classify energy metabolites as signal places.
        
        Identifies common energy metabolites (ATP, NAD, CoA, etc.) and
        marks them as ENERGY signal places with hierarchy layer 0.
        
        Args:
            places: List of places from BiGG import
            
        Returns:
            Same list with signal classification applied
        """
        classified_count = 0
        
        self.logger.debug(f"Classifying {len(places)} places for energy signals")
        
        for place in places:
            # Get BiGG ID from metadata (SBML parser stores original ID)
            bigg_id = place.metadata.get('original_species_id', '')
            if not bigg_id:
                bigg_id = place.metadata.get('bigg_id', '')
            if not bigg_id:
                # Try using place name if neither field exists
                bigg_id = place.name or place.label or ''
            
            self.logger.debug(f"Checking place: {place.label}, bigg_id={bigg_id}")
            
            # Parse metabolite ID and compartment
            metabolite_id, compartment = self.parser.parse_species_id(bigg_id)
            
            # Check if it's an energy metabolite
            if self.parser.is_energy_metabolite(metabolite_id):
                place.is_signal_place = True
                place.signal_type = SignalType.ENERGY
                
                # Apply color schema (blue border for signal places)
                from shypn.utils.color_schema_manager import ColorSchemaManager
                ColorSchemaManager.reset_place_color(place)
                
                # Set hierarchy layer (Layer 0 for energy)
                place.metadata['hierarchy_layer'] = 0
                place.metadata['layer_name'] = 'Layer 0 (Energy)'
                place.metadata['signal_rationale'] = f'Energy metabolite: {metabolite_id}'
                
                # Store compartment info
                if compartment:
                    place.metadata['bigg_compartment'] = compartment
                    place.metadata['bigg_compartment_name'] = self.parser.get_compartment_name(compartment)
                
                classified_count += 1
                self.logger.debug(
                    f"Classified {place.label or place.name} as ENERGY signal "
                    f"(metabolite: {metabolite_id}, compartment: {compartment or 'none'})"
                )
        
        self.logger.info(f"Classified {classified_count} energy signals")
        return places
    
    def classify_regulatory_genes(self, places: List[Place]) -> List[Place]:
        """Classify gene-associated places as regulatory signals.
        
        Marks places representing genes or gene products as REGULATORY
        signal places with appropriate hierarchy layer.
        
        Args:
            places: List of places from BiGG import
            
        Returns:
            Same list with gene classification applied
        """
        classified_count = 0
        
        for place in places:
            # Check if place represents a gene
            is_gene = (
                place.metadata.get('is_gene', False) or
                place.metadata.get('gene_id', None) is not None or
                place.metadata.get('locus_tag', None) is not None
            )
            
            if is_gene:
                place.is_signal_place = True
                place.signal_type = SignalType.REGULATORY
                
                # Set hierarchy layer (Layer 3 for regulatory)
                place.metadata['hierarchy_layer'] = 3
                place.metadata['layer_name'] = 'Layer 3 (Regulatory)'
                place.metadata['signal_rationale'] = 'Gene regulation'
                
                classified_count += 1
                self.logger.debug(
                    f"Classified {place.label or place.name} as REGULATORY signal (gene)"
                )
        
        self.logger.info(f"Classified {classified_count} regulatory gene signals")
        return places
    
    def classify_all(self, places: List[Place]) -> List[Place]:
        """Apply all classification rules.
        
        Convenience method that applies both energy and regulatory
        classification.
        
        Args:
            places: List of places from BiGG import
            
        Returns:
            Same list with all classifications applied
        """
        self.classify_energy_signals(places)
        self.classify_regulatory_genes(places)
        return places
