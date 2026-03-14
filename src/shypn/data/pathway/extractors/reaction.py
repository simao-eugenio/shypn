"""
Reaction Extractor

Extracts reactions from SBML model.
"""

from typing import List, Optional
import re

try:
    import libsbml
except ImportError:
    libsbml = None

from ..pathway_data import Reaction, KineticLaw
from .base import BaseExtractor


class ReactionExtractor(BaseExtractor[List[Reaction]]):
    """
    Extracts reactions from SBML model.
    
    Converts SBML reactions to Reaction data objects with:
    - Reactants and products with stoichiometry
    - Modifiers (catalysts, enzymes, inhibitors)
    - Kinetic laws with parameters
    - Reversibility information
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
            if reaction:
                reaction_list.append(reaction)
                self.logger.debug(f"  - {reaction.id}: {reaction.name}")
        
        return reaction_list
    
    def _convert_reaction(self, sbml_reaction) -> Reaction:
        """
        Convert SBML reaction to Reaction object.
        
        Args:
            sbml_reaction: libsbml Reaction object
            
        Returns:
            Reaction object with reactants, products, and modifiers
        """
        # Extract basic info
        reaction_id = sbml_reaction.getId()
        name = sbml_reaction.getName() or reaction_id
        reversible = sbml_reaction.getReversible()
        
        # Extract SBO term (Phase 1 addition)
        sbo_term = None
        if sbml_reaction.isSetSBOTerm():
            sbo_term = sbml_reaction.getSBOTermID()
        
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
        
        # Extract modifiers (catalysts/enzymes/inhibitors)
        # These will be converted to signal places (Ψ) in 13-tuple Bio-PN
        modifiers = []
        for i in range(sbml_reaction.getNumModifiers()):
            modifier_ref = sbml_reaction.getModifier(i)
            species_id = modifier_ref.getSpecies()
            modifiers.append(species_id)
            self.logger.debug(f"    Modifier: {species_id} (catalyst/enzyme)")
        
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
            modifiers=modifiers,
            kinetic_law=kinetic_law,
            reversible=reversible,
            sbo_term=sbo_term
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
        
        # Sanitize formula to replace hyphens with underscores in species IDs
        # This prevents Python syntax errors like "MOS-P" being parsed as "MOS - P"
        formula = self._sanitize_formula(formula)
        
        # Extract parameters
        parameters = {}
        for i in range(sbml_kinetic_law.getNumParameters()):
            param = sbml_kinetic_law.getParameter(i)
            param_id = param.getId()
            param_value = param.getValue()
            
            # Validate parameter has a valid numeric value
            if param_value is None or (isinstance(param_value, float) and not (param_value == param_value)):  # Check for NaN
                self.logger.warning(
                    f"Parameter '{param_id}' in reaction has invalid value: {param_value}"
                )
            
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
        kinetic_law.sbml_metadata = sbml_metadata  # type: ignore[attr-defined]
        
        return kinetic_law
    
    def _sanitize_formula(self, formula: str) -> str:
        """
        Sanitize formula by replacing hyphens with underscores in identifiers
        and fixing malformed scientific notation.
        
        This prevents Python syntax errors when:
        1. Species IDs contain hyphens (e.g., "MOS-P" → "MOS_P")
        2. Scientific notation has underscore instead of minus (libSBML bug)
           (e.g., "5.9e_4" → "5.9e-4")
        
        Args:
            formula: Original formula from SBML
            
        Returns:
            Sanitized formula with underscores and correct scientific notation
        """
        if not formula:
            return formula
        
        # Fix 1: Replace hyphens with underscores in identifiers
        # Match word characters followed by hyphen followed by word characters
        # This preserves mathematical operators like minus signs
        # Pattern: word boundary, alphanumeric+hyphen+alphanumeric, word boundary
        def replace_hyphen(match):
            return match.group(0).replace('-', '_')
        
        # Match identifiers with hyphens (e.g., MOS-P, Erk2-pp, Mek1-p)
        sanitized = re.sub(r'\b\w+(?:-\w+)+\b', replace_hyphen, formula)
        
        # Fix 2: Correct malformed scientific notation from libSBML
        # Some versions of libSBML convert <cn type="e-notation">5.9 <sep/> -4</cn>
        # to "5.9e_4" instead of "5.9e-4"
        # Pattern: digit followed by 'e_' followed by digit → replace 'e_' with 'e-'
        sanitized = re.sub(r'(\d)e_(\d)', r'\1e-\2', sanitized)
        
        return sanitized
    
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
