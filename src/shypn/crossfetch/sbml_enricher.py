#!/usr/bin/env python3
"""SBML Enricher - Pre-processes SBML files with external data.

This module enriches SBML files BEFORE they are parsed into Shypn models.
It fills in missing data (concentrations, kinetics, annotations) from external
sources like KEGG, Reactome, and other databases.

Architecture:
    User enters pathway ID
         ↓
    Fetch SBML from BioModels (primary source)
         ↓
    CrossFetch enrichment (PRE-PROCESSING) ← THIS MODULE
         - Fetch missing concentrations from KEGG
         - Fetch missing kinetics from KEGG/Reactome
         - Fetch missing annotations from multiple sources
         ↓
    Enriched SBML
         ↓
    Existing flow: SBMLParser → PathwayConverter → PostProcessor
         ↓
    Shypn Petri Net Model

This is the PRE-processor that enhances SBML before conversion.
"""

import logging
from typing import Optional, Dict, List, Any
from pathlib import Path

try:
    import libsbml
except ImportError:
    libsbml = None
    logging.warning("libsbml not available. SBML enrichment will not work.")

from shypn.crossfetch.core.enrichment_pipeline import EnrichmentPipeline
from shypn.crossfetch.models.fetch_result import FetchResult

logger = logging.getLogger(__name__)


class SBMLEnricher:
    """Enriches SBML files with data from external sources.
    
    This class implements the PRE-PROCESSING step in the import workflow:
    1. Load existing SBML file (from BioModels or local file)
    2. Identify missing data (concentrations, kinetics, annotations)
    3. Fetch missing data from KEGG, Reactome, etc. using CrossFetch
    4. Merge fetched data into SBML structure
    5. Return enriched SBML string
    
    The enriched SBML then goes through the existing post-processing pipeline.
    
    Example:
        >>> enricher = SBMLEnricher()
        >>> 
        >>> # Enrich by pathway ID (fetches SBML from BioModels)
        >>> enriched_sbml = enricher.enrich_by_pathway_id("BIOMD0000000002")
        >>> 
        >>> # Or enrich existing SBML file
        >>> enriched_sbml = enricher.enrich_sbml_file("pathway.xml")
        >>> 
        >>> # Then pass to existing parser
        >>> from shypn.data.pathway.sbml_parser import SBMLParser
        >>> parser = SBMLParser()
        >>> pathway_data = parser.parse_sbml_string(enriched_sbml)
    """
    
    def __init__(self, 
                 fetch_sources: Optional[List[str]] = None,
                 enrich_concentrations: bool = True,
                 enrich_kinetics: bool = True,
                 enrich_annotations: bool = True,
                 enrich_coordinates: bool = True):
        """Initialize SBML enricher.
        
        Args:
            fetch_sources: Sources to fetch from (default: ["KEGG", "Reactome"])
            enrich_concentrations: Whether to enrich concentration data
            enrich_kinetics: Whether to enrich kinetic parameters
            enrich_annotations: Whether to enrich annotations
            enrich_coordinates: Whether to enrich layout coordinates
        """
        self.pipeline = EnrichmentPipeline()
        self.fetch_sources = fetch_sources or ["KEGG", "Reactome"]
        self.enrich_concentrations = enrich_concentrations
        self.enrich_kinetics = enrich_kinetics
        self.enrich_annotations = enrich_annotations
        self.enrich_coordinates = enrich_coordinates
        
        logger.info(f"SBMLEnricher initialized with sources: {self.fetch_sources}")
    
    def enrich_by_pathway_id(self, pathway_id: str) -> str:
        """Enrich SBML by pathway ID (fetches from BioModels first).
        
        This is the main entry point for enriching pathways by ID.
        
        Workflow:
        1. Fetch SBML from BioModels using pathway ID
        2. Parse SBML to identify what's missing
        3. Fetch missing data from other sources (KEGG, Reactome)
        4. Merge data into SBML
        5. Return enriched SBML string
        
        Args:
            pathway_id: Pathway ID (e.g., "BIOMD0000000002" or "hsa00010")
            
        Returns:
            Enriched SBML as string
            
        Raises:
            ValueError: If pathway_id is invalid or SBML fetch fails
        """
        logger.info(f"Enriching pathway by ID: {pathway_id}")
        
        if not libsbml:
            raise RuntimeError("libsbml not available. Cannot enrich SBML.")
        
        # Step 1: Fetch base SBML from BioModels
        logger.info("Step 1: Fetching base SBML from BioModels...")
        base_sbml = self._fetch_sbml_from_biomodels(pathway_id)
        
        if not base_sbml:
            raise ValueError(f"Failed to fetch SBML for pathway: {pathway_id}")
        
        # Step 2: Parse SBML to identify missing data
        logger.info("Step 2: Analyzing SBML for missing data...")
        document = libsbml.readSBMLFromString(base_sbml)
        model = document.getModel()
        
        if not model:
            raise ValueError("Invalid SBML: no model found")
        
        missing_data = self._identify_missing_data(model)
        logger.info(f"Missing data: {list(missing_data.keys())}")
        
        # Step 3: Fetch missing data from external sources
        logger.info("Step 3: Fetching missing data from external sources...")
        external_data = self._fetch_external_data(pathway_id, missing_data)
        
        # Step 4: Merge external data into SBML
        logger.info("Step 4: Merging external data into SBML...")
        enriched_sbml = self._merge_data_into_sbml(base_sbml, external_data)
        
        logger.info("SBML enrichment complete")
        return enriched_sbml
    
    def enrich_sbml_file(self, sbml_path: Path) -> str:
        """Enrich existing SBML file.
        
        Args:
            sbml_path: Path to SBML file
            
        Returns:
            Enriched SBML as string
        """
        logger.info(f"Enriching SBML file: {sbml_path}")
        
        # Read SBML file
        with open(sbml_path, 'r') as f:
            base_sbml = f.read()
        
        # Try to extract pathway ID from SBML annotations
        pathway_id = self._extract_pathway_id_from_sbml(base_sbml)
        
        if not pathway_id:
            logger.warning("Could not extract pathway ID from SBML. Enrichment may be limited.")
            return base_sbml
        
        # Follow same enrichment flow
        return self.enrich_by_pathway_id(pathway_id)
    
    def _fetch_sbml_from_biomodels(self, pathway_id: str) -> Optional[str]:
        """Fetch SBML from BioModels database.
        
        Args:
            pathway_id: Pathway ID
            
        Returns:
            SBML string or None if fetch failed
        """
        # Use BioModels fetcher to get SBML
        # Note: This might already be implemented in BioModelsFetcher
        from shypn.crossfetch.fetchers.biomodels_fetcher import BioModelsFetcher
        
        fetcher = BioModelsFetcher()
        
        try:
            # Fetch pathway data (should include SBML)
            result = fetcher.fetch(pathway_id, "pathway")
            
            if result.is_usable() and 'sbml' in result.data:
                return result.data['sbml']
            
            logger.warning(f"BioModels fetch did not return SBML for {pathway_id}")
            return None
            
        except Exception as e:
            logger.error(f"Failed to fetch SBML from BioModels: {e}")
            return None
    
    def _identify_missing_data(self, model) -> Dict[str, List[str]]:
        """Identify what data is missing from SBML model.
        
        Args:
            model: libsbml Model object
            
        Returns:
            Dictionary mapping data type to list of missing elements
        """
        missing = {}
        
        # Check species for missing initial concentrations
        if self.enrich_concentrations:
            species_without_conc = []
            for i in range(model.getNumSpecies()):
                species = model.getSpecies(i)
                if not species.isSetInitialConcentration() and not species.isSetInitialAmount():
                    species_without_conc.append(species.getId())
            
            if species_without_conc:
                missing['concentrations'] = species_without_conc
        
        # Check reactions for missing kinetics
        if self.enrich_kinetics:
            reactions_without_kinetics = []
            for i in range(model.getNumReactions()):
                reaction = model.getReaction(i)
                if not reaction.isSetKineticLaw():
                    reactions_without_kinetics.append(reaction.getId())
            
            if reactions_without_kinetics:
                missing['kinetics'] = reactions_without_kinetics
        
        # Check for missing annotations
        if self.enrich_annotations:
            elements_without_annotations = []
            
            # Check species annotations
            for i in range(model.getNumSpecies()):
                species = model.getSpecies(i)
                if not species.isSetAnnotation():
                    elements_without_annotations.append(('species', species.getId()))
            
            # Check reaction annotations
            for i in range(model.getNumReactions()):
                reaction = model.getReaction(i)
                if not reaction.isSetAnnotation():
                    elements_without_annotations.append(('reaction', reaction.getId()))
            
            if elements_without_annotations:
                missing['annotations'] = elements_without_annotations
        
        # Check for missing layout coordinates
        if self.enrich_coordinates:
            # Check if SBML already has Layout extension
            has_layout = False
            try:
                mplugin = model.getPlugin('layout')
                if mplugin and mplugin.getNumLayouts() > 0:
                    has_layout = True
            except:
                pass
            
            if not has_layout:
                # Request coordinates for all species and reactions
                missing['coordinates'] = {
                    'species': [model.getSpecies(i).getId() for i in range(model.getNumSpecies())],
                    'reactions': [model.getReaction(i).getId() for i in range(model.getNumReactions())]
                }
        
        return missing
    
    def _fetch_external_data(self, 
                            pathway_id: str, 
                            missing_data: Dict[str, List]) -> Dict[str, Any]:
        """Fetch missing data from external sources.
        
        Args:
            pathway_id: Pathway ID
            missing_data: Dictionary of missing data types
            
        Returns:
            Dictionary of fetched data organized by type
        """
        external_data = {}
        
        # Determine which data types to fetch
        data_types = []
        if 'concentrations' in missing_data:
            data_types.append('concentrations')
        if 'kinetics' in missing_data:
            data_types.append('kinetics')
        if 'annotations' in missing_data:
            data_types.append('annotations')
        if 'coordinates' in missing_data:
            data_types.append('coordinates')
        
        if not data_types:
            logger.info("No missing data to fetch")
            return external_data
        
        # Fetch from pipeline
        try:
            fetch_results = self.pipeline.fetch(
                pathway_id=pathway_id,
                preferred_sources=self.fetch_sources,
                data_types=data_types
            )
            
            # Organize results by data type
            for result in fetch_results:
                external_data[result.data_type] = result.data
                logger.info(f"Fetched {result.data_type} from {result.source}")
            
        except Exception as e:
            logger.error(f"Failed to fetch external data: {e}", exc_info=True)
        
        return external_data
    
    def _merge_data_into_sbml(self, base_sbml: str, external_data: Dict[str, Any]) -> str:
        """Merge external data into SBML structure.
        
        Args:
            base_sbml: Original SBML string
            external_data: Fetched external data
            
        Returns:
            Enriched SBML string
        """
        if not external_data:
            logger.info("No external data to merge")
            return base_sbml
        
        # Parse SBML
        document = libsbml.readSBMLFromString(base_sbml)
        model = document.getModel()
        
        # Merge concentrations
        if 'concentrations' in external_data:
            self._merge_concentrations(model, external_data['concentrations'])
        
        # Merge kinetics
        if 'kinetics' in external_data:
            self._merge_kinetics(model, external_data['kinetics'])
        
        # Merge annotations
        if 'annotations' in external_data:
            self._merge_annotations(model, external_data['annotations'])
        
        # Merge coordinates (via CoordinateEnricher)
        if 'coordinates' in external_data:
            self._merge_coordinates(model, external_data['coordinates'])
        
        # Convert back to string
        enriched_sbml = libsbml.writeSBMLToString(document)
        return enriched_sbml
    
    def _merge_concentrations(self, model, concentration_data: Dict[str, Any]):
        """Merge concentration data into SBML species.
        
        Args:
            model: libsbml Model object
            concentration_data: Dictionary of concentration data
        """
        logger.info("Merging concentration data...")
        
        merged_count = 0
        for species_id, conc_info in concentration_data.items():
            species = model.getSpecies(species_id)
            if not species:
                continue
            
            # Extract concentration value
            if isinstance(conc_info, dict):
                value = conc_info.get('value', 0.0)
            else:
                value = float(conc_info)
            
            # Set initial concentration if not already set
            if not species.isSetInitialConcentration():
                species.setInitialConcentration(value)
                merged_count += 1
        
        logger.info(f"Merged {merged_count} concentration values")
    
    def _merge_kinetics(self, model, kinetic_data: Dict[str, Any]):
        """Merge kinetic data into SBML reactions.
        
        Args:
            model: libsbml Model object
            kinetic_data: Dictionary of kinetic data
        """
        logger.info("Merging kinetic data...")
        
        merged_count = 0
        for reaction_id, kinetic_info in kinetic_data.items():
            reaction = model.getReaction(reaction_id)
            if not reaction:
                continue
            
            # Create kinetic law if not present
            if not reaction.isSetKineticLaw():
                kinetic_law = reaction.createKineticLaw()
                
                # Add rate constant parameter
                if isinstance(kinetic_info, dict) and 'rate_constant' in kinetic_info:
                    param = kinetic_law.createParameter()
                    param.setId('k')
                    param.setValue(float(kinetic_info['rate_constant']))
                    
                    # Set formula (simple mass action)
                    kinetic_law.setFormula(f"k * {reaction.getReactant(0).getSpecies()}")
                    merged_count += 1
        
        logger.info(f"Merged {merged_count} kinetic laws")
    
    def _merge_annotations(self, model, annotation_data: Dict[str, Any]):
        """Merge annotation data into SBML elements.
        
        Args:
            model: libsbml Model object
            annotation_data: Dictionary of annotation data
        """
        logger.info("Merging annotation data...")
        
        # Annotations are complex and would need proper RDF/XML formatting
        # For now, just log that we would merge them
        logger.info(f"Would merge {len(annotation_data)} annotations (not yet implemented)")
    
    def _extract_pathway_id_from_sbml(self, sbml_string: str) -> Optional[str]:
        """Extract pathway ID from SBML annotations.
        
        Args:
            sbml_string: SBML as string
            
        Returns:
            Pathway ID or None
        """
        # Parse SBML and look for pathway ID in annotations
        # This is a simplified implementation
        document = libsbml.readSBMLFromString(sbml_string)
        model = document.getModel()
        
        if not model:
            return None
        
        # Try to get from model ID
        model_id = model.getId()
        if model_id:
            return model_id
        
        # Could also check annotations for BioModels/KEGG IDs
        # TODO: Implement more sophisticated ID extraction
        
        return None
    
    def _merge_coordinates(self, model, coordinate_data: Dict[str, Any]):
        """Merge coordinate data into SBML Layout extension.
        
        Uses the CoordinateEnricher to apply coordinate data to the SBML model.
        The coordinates are transformed from screen coordinates to Cartesian
        (first quadrant, origin at bottom-left) as required by Shypn.
        
        Args:
            model: libsbml Model object
            coordinate_data: Dictionary with 'species' and 'reactions' coordinate data
        """
        logger.info("Merging coordinate data...")
        
        try:
            from shypn.crossfetch.enrichers import CoordinateEnricher
            from shypn.crossfetch.models import FetchResult
            
            # Create a CoordinateEnricher instance
            enricher = CoordinateEnricher()
            
            # Wrap coordinate data in FetchResult format
            fetch_result = FetchResult(
                source='KEGG',
                data_type='coordinates',
                pathway_id=model.getId() or 'unknown',
                success=True,
                data=coordinate_data
            )
            
            # Create a simple pathway wrapper with the model
            class PathwayWrapper:
                def __init__(self, sbml_model):
                    self.model = sbml_model
            
            pathway = PathwayWrapper(model)
            
            # Validate data before applying
            is_valid, warnings = enricher.validate(pathway, fetch_result)
            
            if not is_valid:
                logger.warning(f"Coordinate data validation failed: {warnings}")
                return
            
            if warnings:
                for warning in warnings:
                    logger.warning(f"Coordinate validation warning: {warning}")
            
            # Apply coordinate enrichment
            result = enricher.apply(pathway, fetch_result)
            
            if result.success:
                logger.info(
                    f"Successfully merged coordinates: "
                    f"{result.statistics.get('species_glyphs', 0)} species, "
                    f"{result.statistics.get('reaction_glyphs', 0)} reactions"
                )
            else:
                logger.error(f"Failed to merge coordinates: {result.message}")
                
        except Exception as e:
            logger.error(f"Failed to merge coordinate data: {e}", exc_info=True)
