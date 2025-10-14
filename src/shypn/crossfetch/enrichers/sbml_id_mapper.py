"""
SBML ID Mapper

Maps identifiers between different database formats (KEGG, SBML, etc.).
Handles flexible matching strategies for cross-referencing.

Author: Shypn Development Team  
Date: October 2025
"""

import logging
from typing import Dict, List, Optional


class SBMLIDMapper:
    """Maps external database IDs (e.g., KEGG) to SBML species/reaction IDs.
    
    Uses multiple strategies for flexible matching:
    1. Exact ID match
    2. Name-based match (case-insensitive)
    3. Partial/substring match
    4. Annotation-based match (MIRIAM identifiers)
    """
    
    def __init__(self):
        """Initialize ID mapper."""
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def map_species_ids(
        self,
        model,
        external_data: List[Dict]
    ) -> Dict[str, Dict]:
        """Map external species IDs to SBML species IDs.
        
        Args:
            model: SBML Model object (from libsbml)
            external_data: List of species data with IDs and coordinates
                Format: [{'kegg_id': 'cpd:C00031', 'name': 'Glucose', ...}, ...]
        
        Returns:
            Mapping: {sbml_species_id: external_data_dict}
        """
        mapping = {}
        
        # Build reverse lookups for fast matching
        id_lookup = {}
        name_lookup = {}
        
        for data in external_data:
            external_id = data.get('kegg_id', data.get('external_id', ''))
            name = data.get('name', '')
            
            # Store with full ID
            id_lookup[external_id] = data
            
            # Store with bare ID (without prefix)
            if ':' in external_id:
                bare_id = external_id.split(':', 1)[1]
                id_lookup[bare_id] = data
            
            # Store by name (case-insensitive)
            if name:
                name_lookup[name.lower()] = data
        
        # Map each SBML species
        for i in range(model.getNumSpecies()):
            species = model.getSpecies(i)
            sbml_id = species.getId()
            sbml_name = species.getName()
            
            # Strategy 1: Exact ID match
            if sbml_id in id_lookup:
                mapping[sbml_id] = id_lookup[sbml_id]
                self.logger.debug(f"Mapped species {sbml_id} by exact ID")
                continue
            
            # Strategy 2: Name match
            if sbml_name and sbml_name.lower() in name_lookup:
                mapping[sbml_id] = name_lookup[sbml_name.lower()]
                self.logger.debug(f"Mapped species {sbml_id} by name: {sbml_name}")
                continue
            
            # Strategy 3: Partial match
            matched = False
            for ext_id, data in id_lookup.items():
                if ext_id in sbml_id or sbml_id in ext_id:
                    mapping[sbml_id] = data
                    self.logger.debug(f"Mapped species {sbml_id} by partial match with {ext_id}")
                    matched = True
                    break
            
            if matched:
                continue
            
            # Strategy 4: Annotation match (future enhancement)
            # TODO: Parse SBML annotations for KEGG/ChEBI identifiers
        
        self.logger.info(
            f"Mapped {len(mapping)}/{model.getNumSpecies()} species IDs"
        )
        
        return mapping
    
    def map_reaction_ids(
        self,
        model,
        external_data: List[Dict]
    ) -> Dict[str, Dict]:
        """Map external reaction IDs to SBML reaction IDs.
        
        Args:
            model: SBML Model object
            external_data: List of reaction data with IDs
                Format: [{'kegg_id': 'rn:R00299', 'name': 'Hexokinase', ...}, ...]
        
        Returns:
            Mapping: {sbml_reaction_id: external_data_dict}
        """
        mapping = {}
        
        # Build reverse lookup
        id_lookup = {}
        for data in external_data:
            external_id = data.get('kegg_id', data.get('external_id', ''))
            id_lookup[external_id] = data
            
            # Also store without prefix
            if ':' in external_id:
                bare_id = external_id.split(':', 1)[1]
                id_lookup[bare_id] = data
        
        # Map each SBML reaction
        for i in range(model.getNumReactions()):
            reaction = model.getReaction(i)
            sbml_id = reaction.getId()
            
            # Try exact match
            if sbml_id in id_lookup:
                mapping[sbml_id] = id_lookup[sbml_id]
                self.logger.debug(f"Mapped reaction {sbml_id}")
                continue
            
            # Try partial match
            for ext_id, data in id_lookup.items():
                if ext_id in sbml_id or sbml_id in ext_id:
                    mapping[sbml_id] = data
                    self.logger.debug(f"Mapped reaction {sbml_id} by partial match")
                    break
        
        self.logger.info(
            f"Mapped {len(mapping)}/{model.getNumReactions()} reaction IDs"
        )
        
        return mapping
