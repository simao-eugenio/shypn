"""
SBML Parser Module

Parses SBML (Systems Biology Markup Language) files and extracts
pathway information into PathwayData objects.

Architecture (Phase 1 - Refactored):
- SBMLParser: Thin orchestrator (delegates to specialized extractors)
- Extractors: Specialized classes in extractors/ subpackage
- Converters: Unit and concentration conversion utilities

Legacy extractor classes moved to extractors/ subpackage for modularity.
"""

from typing import Optional, Dict, List
from pathlib import Path
import logging

try:
    import libsbml
except ImportError:
    libsbml = None
    logging.warning("libsbml not available. SBML parsing will not work.")

from .converters import UnitConverter, ConcentrationCalculator


class SBMLParser:
    """
    Main SBML parser - thin orchestrator pattern.
    
    Delegates extraction to specialized classes in extractors/ subpackage.
    Coordinates the extraction pipeline and applies post-processing.
    
    Design Principles:
    - Minimal logic in parser (delegates to extractors)
    - Extensible (add new extractors without modifying parser)
    - Clear separation of concerns
    
    Example:
        parser = SBMLParser()
        pathway = parser.parse_file('glycolysis.sbml')
    """
    """
    Main SBML parser class.
    
    Coordinates the extraction of pathway data from SBML files.
    Uses specialized extractor classes for different element types.
    
    Example:
        parser = SBMLParser()
        pathway = parser.parse_file('glycolysis.sbml')
    """
    
    def __init__(self):
        """Initialize SBML parser."""
        self.logger = logging.getLogger(self.__class__.__name__)
        
        if libsbml is None:
            raise ImportError(
                "python-libsbml is not installed. "
                "Install with: pip3 install --user python-libsbml"
            )
    
    def parse_file(self, filepath: str, filter_isolated_species: bool = False) -> PathwayData:
        """
        Parse SBML file and extract pathway data.
        
        Args:
            filepath: Path to SBML file (.sbml or .xml)
            filter_isolated_species: If True, exclude species with no connections (default: False)
                                    WARNING: Filtering may break simulations if isolated species
                                    are referenced in rate equations. Keep False unless you're sure.
            
        Returns:
            PathwayData object with parsed information
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If SBML file is invalid
        """
        filepath = Path(filepath)
        
        if not filepath.exists():
            raise FileNotFoundError(f"SBML file not found: {filepath}")
        
        self.logger.info(f"Parsing SBML file: {filepath.name}")
        
        # Read SBML file
        document = libsbml.readSBML(str(filepath))
        
        # Check for errors
        if document.getNumErrors() > 0:
            errors = []
            for i in range(document.getNumErrors()):
                error = document.getError(i)
                errors.append(f"  - {error.getMessage()}")
            raise ValueError(f"SBML parsing errors:\n" + "\n".join(errors))
        
        # Get model
        model = document.getModel()
        if model is None:
            raise ValueError("SBML file contains no model")
        
        # Extract all elements using specialized extractors
        pathway_data = self._extract_pathway_data(model, filepath, filter_isolated_species)
        
        self.logger.info(
            f"Successfully parsed: "
            f"{len(pathway_data.species)} species, "
            f"{len(pathway_data.reactions)} reactions"
        )
        
        return pathway_data
    
    def _extract_pathway_data(
        self,
        model,
        filepath: Path,
        filter_isolated_species: bool = True
    ) -> PathwayData:
        """
        Extract all pathway data from SBML model.
        
        Phase 1 Refactor: Uses modular extractors + converters.
        
        Args:
            model: libsbml Model object
            filepath: Path to original file
            filter_isolated_species: If True, exclude species not used in reactions
            
        Returns:
            PathwayData object with Phase 1 enhancements
        """
        # Step 1: Create all extractors
        logger = self.logger
        
        compartment_extractor = CompartmentExtractor(model, logger)
        unit_extractor = UnitExtractor(model, logger)
        parameter_extractor = ParameterExtractor(model, logger)
        species_extractor = SpeciesExtractor(model, logger)
        reaction_extractor = ReactionExtractor(model, logger)
        event_extractor = EventExtractor(model, logger)
        annotation_extractor = AnnotationExtractor(model, logger)
        
        # Step 2: Extract all elements (in dependency order)
        compartments_enhanced = compartment_extractor.extract()
        compartments_legacy = compartment_extractor.extract_legacy()
        unit_defs = unit_extractor.extract()
        parameters = parameter_extractor.extract()
        all_species = species_extractor.extract()
        reactions = reaction_extractor.extract()
        events = event_extractor.extract()
        annotations = annotation_extractor.extract()
        
        # Step 3: Apply annotations to species/reactions
        self._apply_annotations(all_species, reactions, annotations)
        
        # Step 4: Link species to compartment objects
        self._link_compartments(all_species, compartments_enhanced)
        
        # Step 5: Filter isolated species if requested
        if filter_isolated_species:
            species = self._filter_isolated_species(all_species, reactions)
        else:
            species = all_species
            self.logger.debug("Including all species (no filtering)")
        
        # Step 6: Merge compartment sizes into parameters (for kinetic formulas)
        for comp_id, comp in compartments_enhanced.items():
            parameters[comp_id] = comp.size
        self.logger.debug(f"Merged {len(compartments_enhanced)} compartment sizes into parameters")
        
        # Step 7: Create metadata
        metadata = self._create_metadata(model, filepath)
        
        # Step 8: Assemble PathwayData
        pathway_data = PathwayData(
            species=species,
            reactions=reactions,
            compartments=compartments_legacy,  # Legacy for compatibility
            compartments_enhanced=compartments_enhanced,  # Phase 1: Enhanced
            parameters=parameters,
            events=events,  # Phase 1: Events
            unit_definitions=unit_defs,  # Phase 1: Unit definitions
            metadata=metadata
        )
        
        # Step 9: Post-processing (unit conversion, concentration calculation)
        # TODO: Implement in future PR when simulation integration is ready
        # pathway_data = self._postprocess(pathway_data)
        
        return pathway_data
    
    def _apply_annotations(self, 
                          species: List[Species],
                          reactions: List[Reaction],
                          annotations: Dict[str, 'Annotation']) -> None:
        """
        Apply annotations to species and reactions.
        
        Args:
            species: List of Species objects
            reactions: List of Reaction objects
            annotations: Dict mapping element IDs to Annotation objects
        """
        for s in species:
            if s.id in annotations:
                s.annotation = annotations[s.id]
        
        for r in reactions:
            if r.id in annotations:
                r.annotation = annotations[r.id]
    
    def _link_compartments(self,
                           species: List[Species],
                           compartments: Dict[str, 'Compartment']) -> None:
        """
        Link species to Compartment objects.
        
        Args:
            species: List of Species objects
            compartments: Dict mapping compartment IDs to Compartment objects
        """
        for s in species:
            if s.compartment and s.compartment in compartments:
                s.compartment_ref = compartments[s.compartment]
    
    def _filter_isolated_species(self,
                                  all_species: List[Species],
                                  reactions: List[Reaction]) -> List[Species]:
        """
        Filter out species not used in any reactions.
        
        Args:
            all_species: All extracted species
            reactions: All extracted reactions
            
        Returns:
            Filtered list of species
        """
        # Build set of species IDs that are actually used in reactions
        used_species_ids = set()
        for reaction in reactions:
            # Add reactants
            for species_id, _ in reaction.reactants:
                used_species_ids.add(species_id)
            # Add products
            for species_id, _ in reaction.products:
                used_species_ids.add(species_id)
            # Add modifiers (catalysts)
            for modifier_id in reaction.modifiers:
                used_species_ids.add(modifier_id)
        
        # Filter species to only include those used in reactions
        species = [s for s in all_species if s.id in used_species_ids]
        
        # Log filtering results
        num_filtered = len(all_species) - len(species)
        if num_filtered > 0:
            filtered_ids = [s.id for s in all_species if s.id not in used_species_ids]
            self.logger.info(
                f"Filtered {num_filtered} isolated species not used in reactions: "
                f"{', '.join(filtered_ids[:5])}"
                + ("..." if len(filtered_ids) > 5 else "")
            )
        
        return species
    
    def _create_metadata(self, model, filepath: Path) -> Dict:
        """
        Create metadata dictionary from SBML model.
        
        Args:
            model: libsbml Model object
            filepath: Path to source file
            
        Returns:
            Metadata dictionary
        """
        metadata = {
            'source_file': str(filepath),
            'model_id': model.getId(),
            'name': model.getName() or model.getId(),  # Primary name key
            'model_name': model.getName() or model.getId(),  # Kept for compatibility
            'sbml_level': model.getLevel(),
            'sbml_version': model.getVersion(),
        }
        
        # Add notes if available
        if model.isSetNotes():
            # Extract plain text from notes (simplified)
            notes = model.getNotesString()
            if notes:
                # Ensure notes is a string and truncate
                try:
                    notes_str = str(notes) if not isinstance(notes, str) else notes
                    metadata['notes'] = notes_str[:500]  # Truncate to 500 chars
                except Exception as e:
                    self.logger.warning(f"Could not process notes: {e}")
                    metadata['notes'] = "Notes unavailable"
        
        return metadata
    
    def parse_string(self, sbml_string: str, filter_isolated_species: bool = False) -> PathwayData:
        """
        Parse SBML from string.
        
        Args:
            sbml_string: SBML XML as string
            filter_isolated_species: If True, exclude species with no connections (default: False)
            
        Returns:
            PathwayData object
            
        Raises:
            ValueError: If SBML is invalid
        """
        self.logger.info("Parsing SBML from string")
        
        document = libsbml.readSBMLFromString(sbml_string)
        
        if document.getNumErrors() > 0:
            errors = []
            for i in range(document.getNumErrors()):
                error = document.getError(i)
                errors.append(f"  - {error.getMessage()}")
            raise ValueError(f"SBML parsing errors:\n" + "\n".join(errors))
        
        model = document.getModel()
        if model is None:
            raise ValueError("SBML contains no model")
        
        return self._extract_pathway_data(model, Path("(string)"), filter_isolated_species)


# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(name)s - %(levelname)s - %(message)s'
    )
    
    # Example: Parse SBML file
    pass  # Implementation examples removed for brevity
