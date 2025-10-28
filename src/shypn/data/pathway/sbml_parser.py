"""
SBML Parser Module

Parses SBML (Systems Biology Markup Language) files and extracts
pathway information into PathwayData objects.

Architecture:
- SBMLParser: Main parser class (coordinates parsing)
- SpeciesExtractor: Extracts species/metabolites
- ReactionExtractor: Extracts reactions
- KineticsExtractor: Extracts kinetic laws
- CompartmentExtractor: Extracts compartments
"""

from typing import Optional, Dict, List, Any
from pathlib import Path
import logging

try:
    import libsbml
except ImportError:
    libsbml = None
    logging.warning("libsbml not available. SBML parsing will not work.")

from .pathway_data import (
    PathwayData,
    Species,
    Reaction,
    KineticLaw,
)


# Base extractor class
class BaseExtractor:
    """
    Base class for SBML element extractors.
    
    Each extractor handles a specific type of SBML element
    (species, reactions, compartments, etc.)
    """
    
    def __init__(self, sbml_model):
        """
        Initialize extractor with SBML model.
        
        Args:
            sbml_model: libsbml Model object
        """
        self.model = sbml_model
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def extract(self) -> Any:
        """
        Extract elements from SBML model.
        
        Must be implemented by subclasses.
        
        Returns:
            Extracted data (type depends on subclass)
        """
        raise NotImplementedError("Subclasses must implement extract()")


class SpeciesExtractor(BaseExtractor):
    """
    Extracts species (metabolites/compounds) from SBML model.
    
    Converts SBML species to Species data objects.
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
            initial_concentration = 0.0
        
        # Extract annotation data (ChEBI, KEGG IDs)
        metadata = self._extract_species_annotations(sbml_species)
        chebi_id = metadata.get('chebi_id')
        kegg_id = metadata.get('kegg_id')
        
        # Get compartment volume for unit conversion
        compartment_obj = self.model.getCompartment(compartment)
        compartment_volume = compartment_obj.getSize() if compartment_obj else 1.0
        
        return Species(
            id=species_id,
            name=name,
            compartment=compartment,
            initial_concentration=initial_concentration,
            compartment_volume=compartment_volume,
            chebi_id=chebi_id,
            kegg_id=kegg_id,
            metadata=metadata
        )
    
    def _extract_species_annotations(self, sbml_species) -> Dict[str, Any]:
        """
        Extract annotation data from SBML species.
        
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
            # (In production, use proper XML parsing)
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


class ReactionExtractor(BaseExtractor):
    """
    Extracts reactions from SBML model.
    
    Converts SBML reactions to Reaction data objects.
    """
    
    def extract(self) -> List[Reaction]:
        """
        Extract all reactions from SBML model.
        
        Returns:
            List of Reaction objects
        """
        reaction_list = []
        
        num_reactions = self.model.getNumReactions()
        self.logger.info(f"Extracting {num_reactions} reactions...")
        
        for i in range(num_reactions):
            sbml_reaction = self.model.getReaction(i)
            reaction = self._convert_reaction(sbml_reaction)
            reaction_list.append(reaction)
            self.logger.debug(f"  - {reaction.id}: {reaction.name}")
        
        return reaction_list
    
    def _convert_reaction(self, sbml_reaction) -> Reaction:
        """
        Convert SBML reaction to Reaction object.
        
        Args:
            sbml_reaction: libsbml Reaction object
            
        Returns:
            Reaction object
        """
        # Extract basic info
        reaction_id = sbml_reaction.getId()
        name = sbml_reaction.getName() or reaction_id
        reversible = sbml_reaction.getReversible()
        
        # Extract reactants (inputs)
        reactants = []
        for i in range(sbml_reaction.getNumReactants()):
            species_ref = sbml_reaction.getReactant(i)
            species_id = species_ref.getSpecies()
            stoichiometry = species_ref.getStoichiometry()
            reactants.append((species_id, stoichiometry))
        
        # Extract products (outputs)
        products = []
        for i in range(sbml_reaction.getNumProducts()):
            species_ref = sbml_reaction.getProduct(i)
            species_id = species_ref.getSpecies()
            stoichiometry = species_ref.getStoichiometry()
            products.append((species_id, stoichiometry))
        
        # Extract kinetic law
        kinetic_law = None
        if sbml_reaction.isSetKineticLaw():
            kinetic_law = self._extract_kinetic_law(
                sbml_reaction.getKineticLaw(),
                sbml_reaction=sbml_reaction
            )
        
        return Reaction(
            id=reaction_id,
            name=name,
            reactants=reactants,
            products=products,
            kinetic_law=kinetic_law,
            reversible=reversible
        )
    
    def _extract_kinetic_law(self, sbml_kinetic_law, sbml_reaction=None) -> Optional[KineticLaw]:
        """
        Extract kinetic law from SBML.
        
        Args:
            sbml_kinetic_law: libsbml KineticLaw object
            sbml_reaction: libsbml Reaction object (for metadata)
            
        Returns:
            KineticLaw object or None
        """
        if not sbml_kinetic_law.isSetMath():
            return None
        
        # Get formula as string
        math_ast = sbml_kinetic_law.getMath()
        formula = libsbml.formulaToL3String(math_ast)
        
        # Extract parameters
        parameters = {}
        for i in range(sbml_kinetic_law.getNumParameters()):
            param = sbml_kinetic_law.getParameter(i)
            param_id = param.getId()
            param_value = param.getValue()
            parameters[param_id] = param_value
        
        # Try to detect kinetic law type
        rate_type = self._detect_rate_type(formula)
        
        # Store SBML-specific metadata for later metadata creation
        # This will be used by the converter to create SBMLKineticMetadata
        sbml_metadata = {}
        if sbml_reaction:
            sbml_metadata['sbml_reaction_id'] = sbml_reaction.getId()
            sbml_metadata['sbml_level'] = self.model.getLevel()
            sbml_metadata['sbml_version'] = self.model.getVersion()
            sbml_metadata['sbml_model_id'] = self.model.getId()
        
        kinetic_law = KineticLaw(
            formula=formula,
            rate_type=rate_type,
            parameters=parameters
        )
        
        # Attach SBML metadata to kinetic law for converter to use
        kinetic_law.sbml_metadata = sbml_metadata
        
        return kinetic_law
    
    def _detect_rate_type(self, formula: str) -> str:
        """
        Detect type of kinetic law from formula.
        
        Args:
            formula: Mathematical formula string
            
        Returns:
            Rate type string
        """
        formula_lower = formula.lower()
        
        # Simple heuristics
        if 'vmax' in formula_lower and 'km' in formula_lower:
            return 'michaelis_menten'
        elif '*' in formula and '/' not in formula:
            return 'mass_action'
        else:
            return 'custom'


class CompartmentExtractor(BaseExtractor):
    """
    Extracts compartments (cellular locations) from SBML model.
    """
    
    def extract(self) -> Dict[str, str]:
        """
        Extract all compartments from SBML model.
        
        Returns:
            Dict mapping compartment IDs to names
        """
        compartments = {}
        
        num_compartments = self.model.getNumCompartments()
        self.logger.info(f"Extracting {num_compartments} compartments...")
        
        for i in range(num_compartments):
            sbml_compartment = self.model.getCompartment(i)
            comp_id = sbml_compartment.getId()
            comp_name = sbml_compartment.getName() or comp_id
            compartments[comp_id] = comp_name
            self.logger.debug(f"  - {comp_id}: {comp_name}")
        
        return compartments


class ParameterExtractor(BaseExtractor):
    """
    Extracts global parameters from SBML model.
    """
    
    def extract(self) -> Dict[str, float]:
        """
        Extract all global parameters from SBML model.
        
        Returns:
            Dict mapping parameter IDs to values
        """
        parameters = {}
        
        num_parameters = self.model.getNumParameters()
        self.logger.info(f"Extracting {num_parameters} parameters...")
        
        for i in range(num_parameters):
            sbml_parameter = self.model.getParameter(i)
            param_id = sbml_parameter.getId()
            param_value = sbml_parameter.getValue()
            parameters[param_id] = param_value
            self.logger.debug(f"  - {param_id}: {param_value}")
        
        return parameters


# Main parser class
class SBMLParser:
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
    
    def parse_file(self, filepath: str) -> PathwayData:
        """
        Parse SBML file and extract pathway data.
        
        Args:
            filepath: Path to SBML file (.sbml or .xml)
            
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
        pathway_data = self._extract_pathway_data(model, filepath)
        
        self.logger.info(
            f"Successfully parsed: "
            f"{len(pathway_data.species)} species, "
            f"{len(pathway_data.reactions)} reactions"
        )
        
        return pathway_data
    
    def _extract_pathway_data(
        self,
        model,
        filepath: Path
    ) -> PathwayData:
        """
        Extract all pathway data from SBML model.
        
        Uses specialized extractor classes for different element types.
        
        Args:
            model: libsbml Model object
            filepath: Path to original file
            
        Returns:
            PathwayData object
        """
        # Create extractors
        species_extractor = SpeciesExtractor(model)
        reaction_extractor = ReactionExtractor(model)
        compartment_extractor = CompartmentExtractor(model)
        parameter_extractor = ParameterExtractor(model)
        
        # Extract all elements
        species = species_extractor.extract()
        reactions = reaction_extractor.extract()
        compartments = compartment_extractor.extract()
        parameters = parameter_extractor.extract()
        
        # Create metadata
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
        
        return PathwayData(
            species=species,
            reactions=reactions,
            compartments=compartments,
            parameters=parameters,
            metadata=metadata
        )
    
    def parse_string(self, sbml_string: str) -> PathwayData:
        """
        Parse SBML from string.
        
        Args:
            sbml_string: SBML XML as string
            
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
        
        return self._extract_pathway_data(model, Path("(string)"))


# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(name)s - %(levelname)s - %(message)s'
    )
    
    # Example: Parse SBML file
    
    # Check if libsbml is available
    if libsbml is None:
        pass  # libsbml not available
    else:
        pass  # libsbml available
