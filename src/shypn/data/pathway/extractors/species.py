"""
Species Extractor

Extracts species (metabolites/compounds) from SBML model.
"""

from typing import List, Dict, Any

try:
    import libsbml
except ImportError:
    libsbml = None

from ..pathway_data import Species
from .base import BaseExtractor


class SpeciesExtractor(BaseExtractor[List[Species]]):
    """
    Extracts species (metabolites/compounds) from SBML model.
    
    Converts SBML species to Species data objects with:
    - Basic properties (ID, name, compartment)
    - Initial concentration/amount
    - Database cross-references (ChEBI, KEGG)
    - Compartment volume for unit conversion
    """
    
    def extract(self) -> List[Species]:
        """
        Extract all species from SBML model.
        
        Returns:
            List of Species objects
        """
        species_list = []
        
        num_species = self.model.getNumSpecies()
        self.logger.info(f"Extracting {num_species} species...")
        
        for i in range(num_species):
            sbml_species = self.model.getSpecies(i)
            species = self._convert_species(sbml_species)
            if species:
                species_list.append(species)
                self.logger.debug(f"  - {species.id}: {species.name}")
        
        return species_list
    
    def _convert_species(self, sbml_species) -> Species:
        """
        Convert SBML species to Species object.
        
        Args:
            sbml_species: libsbml Species object
            
        Returns:
            Species object
        """
        # Extract basic info
        species_id = sbml_species.getId()
        name = sbml_species.getName() or species_id
        compartment = sbml_species.getCompartment()
        
        # Extract initial amount/concentration
        if sbml_species.isSetInitialConcentration():
            initial_concentration = sbml_species.getInitialConcentration()
        elif sbml_species.isSetInitialAmount():
            initial_concentration = sbml_species.getInitialAmount()
        else:
            # No initial value specified - use physiological default
            # Assumption: mM scale (millimolar, typical for cellular metabolites)
            # Default: 1.0 mM (reasonable for most metabolites)
            initial_concentration = 1.0
            self.logger.debug(
                f"Species '{species_id}' has no initial concentration, "
                f"using default 1.0 mM (physiological scale)"
            )
        
        # Extract annotation data (ChEBI, KEGG IDs)
        metadata = self._extract_species_annotations(sbml_species)
        chebi_id = metadata.get('chebi_id')
        kegg_id = metadata.get('kegg_id')
        
        # Mark as SBML import (so converter knows to preserve original names)
        metadata['data_source'] = 'sbml_import'
        
        # Extract boundary condition (for signal places)
        # Boundary species = constant external sources/sinks (infinite reservoirs)
        if sbml_species.getBoundaryCondition():
            metadata['boundary_condition'] = True
            self.logger.debug(
                f"Species '{species_id}' is a boundary species (constant source/sink)"
            )
        
        # Get compartment volume for unit conversion
        compartment_obj = self.model.getCompartment(compartment)
        compartment_volume = compartment_obj.getSize() if compartment_obj else 1.0
        
        # Extract substance units (Phase 1 addition)
        substance_units = None
        if sbml_species.isSetSubstanceUnits():
            substance_units = sbml_species.getSubstanceUnits()
        
        has_only_substance_units = sbml_species.getHasOnlySubstanceUnits()
        
        return Species(
            id=species_id,
            name=name,
            compartment=compartment,
            initial_concentration=initial_concentration,
            compartment_volume=compartment_volume,
            chebi_id=chebi_id,
            kegg_id=kegg_id,
            substance_units=substance_units,
            has_only_substance_units=has_only_substance_units,
            metadata=metadata
        )
    
    def _extract_species_annotations(self, sbml_species) -> Dict[str, Any]:
        """
        Extract annotation data from SBML species.
        
        Simple extraction for backward compatibility.
        Full annotation extraction done by AnnotationExtractor.
        
        Args:
            sbml_species: libsbml Species object
            
        Returns:
            Dictionary with annotation data
        """
        metadata = {}
        
        # Try to extract database cross-references from annotation
        if sbml_species.isSetAnnotation():
            annotation = sbml_species.getAnnotationString()
            
            # Simple parsing for common databases
            # (Full RDF parsing done by AnnotationExtractor)
            if 'chebi/CHEBI:' in annotation:
                start = annotation.find('chebi/CHEBI:') + len('chebi/CHEBI:')
                end = annotation.find('"', start)
                if end > start:
                    metadata['chebi_id'] = f"CHEBI:{annotation[start:end]}"
            
            if 'kegg.compound/' in annotation:
                start = annotation.find('kegg.compound/') + len('kegg.compound/')
                end = annotation.find('"', start)
                if end > start:
                    metadata['kegg_id'] = annotation[start:end]
        
        return metadata
