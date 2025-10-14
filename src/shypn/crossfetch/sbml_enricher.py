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
        """Extract KEGG pathway ID from SBML annotations.
        
        Searches for KEGG pathway IDs in:
        1. Model-level annotations (direct pathway reference)
        2. Species annotations (finds most common pathway with organism awareness)
        3. Reaction annotations
        
        IMPORTANT: Returns organism-specific pathway ID (e.g., sce00010 for yeast)
        NOT a generic reference pathway (map00010)
        
        Args:
            sbml_string: SBML as string
            
        Returns:
            KEGG pathway ID with organism code (e.g., "sce00010") or None
        """
        import re
        from collections import Counter
        
        document = libsbml.readSBMLFromString(sbml_string)
        model = document.getModel()
        
        if not model:
            return None
        
        # Try to extract KEGG pathway from model annotations
        model_annotation = model.getAnnotationString()
        if model_annotation:
            kegg_match = re.search(r'kegg\.pathway[:/]([a-z]{2,4}\d{5})', model_annotation, re.IGNORECASE)
            if kegg_match:
                pathway_id = kegg_match.group(1).lower()
                logger.info(f"Found KEGG pathway in model annotations: {pathway_id}")
                return pathway_id
        
        # Try to infer organism from model metadata
        organism_code = self._infer_organism_from_model(model)
        logger.info(f"Inferred organism code: {organism_code or 'unknown'}")
        
        # Collect KEGG pathway IDs from species and reactions
        pathway_votes = Counter()
        
        # Check species annotations for KEGG compound IDs
        for i in range(model.getNumSpecies()):
            species = model.getSpecies(i)
            annotation = species.getAnnotationString()
            
            if not annotation:
                continue
            
            # Look for KEGG compound IDs (e.g., C00031, C00002)
            kegg_compound = re.search(r'kegg\.compound[:/]([C]\d{5})', annotation, re.IGNORECASE)
            if kegg_compound:
                compound_id = kegg_compound.group(1).upper()
                
                # Query KEGG for pathways containing this compound
                pathways = self._query_kegg_pathways_for_compound(compound_id, organism_code)
                pathway_votes.update(pathways)
        
        # Check reaction annotations for KEGG reaction IDs
        for i in range(model.getNumReactions()):
            reaction = model.getReaction(i)
            annotation = reaction.getAnnotationString()
            
            if not annotation:
                continue
            
            # Look for KEGG reaction IDs (e.g., R00001)
            kegg_reaction = re.search(r'kegg\.reaction[:/]([R]\d{5})', annotation, re.IGNORECASE)
            if kegg_reaction:
                reaction_id = kegg_reaction.group(1).upper()
                
                # Query KEGG for pathways containing this reaction
                pathways = self._query_kegg_pathways_for_reaction(reaction_id, organism_code)
                pathway_votes.update(pathways)
        
        # Filter and return most common ORGANISM-SPECIFIC pathway (not map)
        if pathway_votes:
            # Remove generic "map" pathways, prefer organism-specific
            organism_pathways = {k: v for k, v in pathway_votes.items() if not k.startswith('map')}
            
            if organism_pathways:
                most_common = Counter(organism_pathways).most_common(1)[0]
                pathway_id, count = most_common
                logger.info(f"Found KEGG pathway by voting: {pathway_id} ({count} references)")
                return pathway_id
            else:
                # Fallback to map pathway if that's all we have
                most_common = pathway_votes.most_common(1)[0]
                pathway_id, count = most_common
                logger.warning(f"Only found generic map pathway: {pathway_id}, may not have coordinates")
                return pathway_id
        
        logger.debug("No KEGG pathway ID found in SBML annotations")
        return None
    
    def _infer_organism_from_model(self, model) -> Optional[str]:
        """Infer organism code from SBML model metadata.
        
        Checks:
        - Model name for organism keywords
        - Model annotations for taxonomy
        - Species names for organism-specific terms
        
        Args:
            model: libsbml Model object
            
        Returns:
            KEGG organism code (e.g., "hsa", "sce", "eco") or None
        """
        import re
        
        # Common organism mappings
        organism_map = {
            'human': 'hsa',
            'homo sapiens': 'hsa',
            'sapiens': 'hsa',
            'yeast': 'sce',
            'saccharomyces cerevisiae': 'sce',
            'cerevisiae': 'sce',
            's. cerevisiae': 'sce',
            'e. coli': 'eco',
            'escherichia coli': 'eco',
            'coli': 'eco',
            'mouse': 'mmu',
            'mus musculus': 'mmu',
            'rat': 'rno',
            'rattus norvegicus': 'rno',
        }
        
        # Check model name
        model_name = model.getName() if model.isSetName() else model.getId()
        if model_name:
            model_name_lower = model_name.lower()
            for keyword, code in organism_map.items():
                if keyword in model_name_lower:
                    logger.debug(f"Inferred organism from model name: {code}")
                    return code
        
        # Check model annotations for taxonomy
        model_annotation = model.getAnnotationString()
        if model_annotation:
            # Look for taxonomy IDs or organism names
            for keyword, code in organism_map.items():
                if keyword in model_annotation.lower():
                    logger.debug(f"Inferred organism from annotations: {code}")
                    return code
        
        # Default to human if nothing found
        logger.debug("Could not infer organism, defaulting to human (hsa)")
        return 'hsa'
    
    def _query_kegg_pathways_for_compound(self, compound_id: str, organism_code: Optional[str] = None) -> List[str]:
        """Query KEGG for pathways containing a compound.
        
        Args:
            compound_id: KEGG compound ID (e.g., "C00031")
            organism_code: Preferred organism code (e.g., "hsa", "sce")
            
        Returns:
            List of pathway IDs, prioritizing organism-specific pathways
        """
        try:
            import urllib.request
            
            url = f"https://rest.kegg.jp/link/pathway/{compound_id}"
            with urllib.request.urlopen(url, timeout=5) as response:
                data = response.read().decode('utf-8')
            
            # Parse response: "cpd:C00031\tpath:hsa00010"
            pathways = []
            for line in data.strip().split('\n'):
                if '\t' in line:
                    _, pathway_ref = line.split('\t')
                    pathway_id = pathway_ref.replace('path:', '')
                    
                    # Prioritize organism-specific pathways
                    if organism_code and pathway_id.startswith(organism_code):
                        pathways.insert(0, pathway_id)  # Add to front
                    else:
                        pathways.append(pathway_id)
            
            return pathways
        except Exception as e:
            logger.debug(f"Failed to query pathways for {compound_id}: {e}")
            return []
    
    def _query_kegg_pathways_for_reaction(self, reaction_id: str, organism_code: Optional[str] = None) -> List[str]:
        """Query KEGG for pathways containing a reaction.
        
        Args:
            reaction_id: KEGG reaction ID (e.g., "R00001")
            organism_code: Preferred organism code (e.g., "hsa", "sce")
            
        Returns:
            List of pathway IDs, prioritizing organism-specific pathways
        """
        try:
            import urllib.request
            
            url = f"https://rest.kegg.jp/link/pathway/{reaction_id}"
            with urllib.request.urlopen(url, timeout=5) as response:
                data = response.read().decode('utf-8')
            
            # Parse response
            pathways = []
            for line in data.strip().split('\n'):
                if '\t' in line:
                    _, pathway_ref = line.split('\t')
                    pathway_id = pathway_ref.replace('path:', '')
                    
                    # Prioritize organism-specific pathways
                    if organism_code and pathway_id.startswith(organism_code):
                        pathways.insert(0, pathway_id)
                    else:
                        pathways.append(pathway_id)
            
            return pathways
        except Exception as e:
            logger.debug(f"Failed to query pathways for {reaction_id}: {e}")
            return []
    
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
