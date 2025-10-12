"""
Pathway Validator Module

Validates parsed pathway data to ensure integrity before conversion
to Petri nets.

Architecture:
- BaseValidator: Abstract base class for all validators
- SpeciesReferenceValidator: Validates species references
- StoichiometryValidator: Validates stoichiometry coefficients
- KineticsValidator: Validates kinetic formulas
- CompartmentValidator: Validates compartments
- PathwayValidator: Main validator class (coordinates validation)
"""

from typing import List, Set
import logging
import re

from .pathway_data import (
    PathwayData,
    ValidationResult,
    Species,
    Reaction,
)


# Base validator class
class BaseValidator:
    """
    Base class for pathway data validators.
    
    Each validator handles validation of a specific aspect
    of pathway data.
    """
    
    def __init__(self, pathway: PathwayData):
        """
        Initialize validator with pathway data.
        
        Args:
            pathway: PathwayData object to validate
        """
        self.pathway = pathway
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def validate(self, result: ValidationResult) -> None:
        """
        Perform validation and update result.
        
        Must be implemented by subclasses.
        
        Args:
            result: ValidationResult to update with errors/warnings
        """
        raise NotImplementedError("Subclasses must implement validate()")


class SpeciesReferenceValidator(BaseValidator):
    """
    Validates that all species references in reactions exist.
    
    Ensures no orphaned or dangling references.
    """
    
    def validate(self, result: ValidationResult) -> None:
        """
        Validate species references in all reactions.
        
        Args:
            result: ValidationResult to update
        """
        self.logger.info("Validating species references...")
        
        # Build set of valid species IDs
        valid_species_ids = {species.id for species in self.pathway.species}
        
        if not valid_species_ids:
            result.add_error("No species defined in pathway")
            return
        
        # Check each reaction
        for reaction in self.pathway.reactions:
            # Check reactants
            for species_id, _ in reaction.reactants:
                if species_id not in valid_species_ids:
                    result.add_error(
                        f"Reaction '{reaction.name}' ({reaction.id}): "
                        f"Unknown reactant species '{species_id}'"
                    )
            
            # Check products
            for species_id, _ in reaction.products:
                if species_id not in valid_species_ids:
                    result.add_error(
                        f"Reaction '{reaction.name}' ({reaction.id}): "
                        f"Unknown product species '{species_id}'"
                    )
        
        self.logger.info(f"  Checked {len(self.pathway.reactions)} reactions")


class StoichiometryValidator(BaseValidator):
    """
    Validates stoichiometry coefficients in reactions.
    
    Ensures all coefficients are positive and reasonable.
    """
    
    def validate(self, result: ValidationResult) -> None:
        """
        Validate stoichiometry coefficients.
        
        Args:
            result: ValidationResult to update
        """
        self.logger.info("Validating stoichiometry...")
        
        for reaction in self.pathway.reactions:
            # Check reactants
            for species_id, stoich in reaction.reactants:
                if stoich <= 0:
                    result.add_error(
                        f"Reaction '{reaction.name}' ({reaction.id}): "
                        f"Invalid stoichiometry {stoich} for reactant '{species_id}' "
                        f"(must be positive)"
                    )
                elif stoich > 100:
                    result.add_warning(
                        f"Reaction '{reaction.name}' ({reaction.id}): "
                        f"Very large stoichiometry {stoich} for reactant '{species_id}' "
                        f"(unusual)"
                    )
            
            # Check products
            for species_id, stoich in reaction.products:
                if stoich <= 0:
                    result.add_error(
                        f"Reaction '{reaction.name}' ({reaction.id}): "
                        f"Invalid stoichiometry {stoich} for product '{species_id}' "
                        f"(must be positive)"
                    )
                elif stoich > 100:
                    result.add_warning(
                        f"Reaction '{reaction.name}' ({reaction.id}): "
                        f"Very large stoichiometry {stoich} for product '{species_id}' "
                        f"(unusual)"
                    )
            
            # Check for empty reactions
            if not reaction.reactants and not reaction.products:
                result.add_error(
                    f"Reaction '{reaction.name}' ({reaction.id}): "
                    f"No reactants or products defined"
                )


class KineticsValidator(BaseValidator):
    """
    Validates kinetic laws and formulas.
    
    Checks formula syntax and parameter consistency.
    """
    
    def validate(self, result: ValidationResult) -> None:
        """
        Validate kinetic laws.
        
        Args:
            result: ValidationResult to update
        """
        self.logger.info("Validating kinetics...")
        
        reactions_without_kinetics = 0
        
        for reaction in self.pathway.reactions:
            if not reaction.kinetic_law:
                reactions_without_kinetics += 1
                continue
            
            kinetic_law = reaction.kinetic_law
            
            # Check for empty formula
            if not kinetic_law.formula or not kinetic_law.formula.strip():
                result.add_warning(
                    f"Reaction '{reaction.name}' ({reaction.id}): "
                    f"Empty kinetic formula"
                )
                continue
            
            # Check for suspicious patterns (very basic syntax check)
            formula = kinetic_law.formula
            
            # Check for balanced parentheses
            if formula.count('(') != formula.count(')'):
                result.add_error(
                    f"Reaction '{reaction.name}' ({reaction.id}): "
                    f"Unbalanced parentheses in kinetic formula: {formula}"
                )
            
            # Check for division by zero patterns
            if '/0' in formula.replace(' ', '') or '/ 0' in formula:
                result.add_error(
                    f"Reaction '{reaction.name}' ({reaction.id}): "
                    f"Division by zero in kinetic formula: {formula}"
                )
            
            # Check for consecutive operators
            if re.search(r'[+\-*/]{2,}', formula.replace('**', '')):
                result.add_warning(
                    f"Reaction '{reaction.name}' ({reaction.id}): "
                    f"Consecutive operators in kinetic formula: {formula}"
                )
        
        # Warn if many reactions lack kinetics
        if reactions_without_kinetics > 0:
            percentage = (reactions_without_kinetics / len(self.pathway.reactions)) * 100
            if percentage > 50:
                result.add_warning(
                    f"{reactions_without_kinetics}/{len(self.pathway.reactions)} reactions "
                    f"({percentage:.0f}%) have no kinetic laws defined"
                )


class CompartmentValidator(BaseValidator):
    """
    Validates compartments and their usage.
    
    Ensures all referenced compartments are defined.
    """
    
    def validate(self, result: ValidationResult) -> None:
        """
        Validate compartments.
        
        Args:
            result: ValidationResult to update
        """
        self.logger.info("Validating compartments...")
        
        # Check if any compartments are defined
        if not self.pathway.compartments:
            result.add_warning("No compartments defined in pathway")
            return
        
        # Check for species with undefined compartments
        defined_compartments = set(self.pathway.compartments.keys())
        
        for species in self.pathway.species:
            if species.compartment and species.compartment not in defined_compartments:
                result.add_error(
                    f"Species '{species.name}' ({species.id}): "
                    f"References undefined compartment '{species.compartment}'"
                )


class StructureValidator(BaseValidator):
    """
    Validates overall pathway structure.
    
    Checks for orphaned species, disconnected components, etc.
    """
    
    def validate(self, result: ValidationResult) -> None:
        """
        Validate pathway structure.
        
        Args:
            result: ValidationResult to update
        """
        self.logger.info("Validating pathway structure...")
        
        # Check for minimum elements
        if len(self.pathway.species) == 0:
            result.add_error("Pathway has no species defined")
            return
        
        if len(self.pathway.reactions) == 0:
            result.add_error("Pathway has no reactions defined")
            return
        
        # Find species that appear in reactions
        species_in_reactions: Set[str] = set()
        
        for reaction in self.pathway.reactions:
            for species_id, _ in reaction.reactants:
                species_in_reactions.add(species_id)
            for species_id, _ in reaction.products:
                species_in_reactions.add(species_id)
        
        # Check for orphaned species (not in any reaction)
        orphaned_species = []
        for species in self.pathway.species:
            if species.id not in species_in_reactions:
                orphaned_species.append(f"{species.name} ({species.id})")
        
        if orphaned_species:
            result.add_warning(
                f"{len(orphaned_species)} orphaned species (not in any reaction): "
                f"{', '.join(orphaned_species[:5])}"
                + (f" and {len(orphaned_species) - 5} more" if len(orphaned_species) > 5 else "")
            )


class ConcentrationValidator(BaseValidator):
    """
    Validates species concentrations.
    
    Checks for negative or unreasonable concentrations.
    """
    
    def validate(self, result: ValidationResult) -> None:
        """
        Validate species concentrations.
        
        Args:
            result: ValidationResult to update
        """
        self.logger.info("Validating concentrations...")
        
        for species in self.pathway.species:
            if species.initial_concentration < 0:
                result.add_error(
                    f"Species '{species.name}' ({species.id}): "
                    f"Negative initial concentration {species.initial_concentration}"
                )
            elif species.initial_concentration > 1000:
                result.add_warning(
                    f"Species '{species.name}' ({species.id}): "
                    f"Very large initial concentration {species.initial_concentration} "
                    f"(unusual, may cause numerical issues)"
                )


# Main validator class
class PathwayValidator:
    """
    Main pathway validator class.
    
    Coordinates validation using specialized validator classes.
    Ensures pathway data is valid before conversion to Petri nets.
    
    Example:
        validator = PathwayValidator()
        result = validator.validate(pathway_data)
        if result.is_valid:
            print("✅ Pathway is valid")
        else:
            print("❌ Validation errors:")
            for error in result.errors:
                print(f"  - {error}")
    """
    
    def __init__(self):
        """Initialize pathway validator."""
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def validate(self, pathway: PathwayData) -> ValidationResult:
        """
        Validate pathway data using all validators.
        
        Args:
            pathway: PathwayData object to validate
            
        Returns:
            ValidationResult with errors and warnings
        """
        self.logger.info("Starting pathway validation...")
        
        # Create result object
        result = ValidationResult(is_valid=True)
        
        # Create all validators
        validators = [
            SpeciesReferenceValidator(pathway),
            StoichiometryValidator(pathway),
            KineticsValidator(pathway),
            CompartmentValidator(pathway),
            StructureValidator(pathway),
            ConcentrationValidator(pathway),
        ]
        
        # Run all validators
        for validator in validators:
            try:
                validator.validate(result)
            except Exception as e:
                self.logger.error(f"Validator {validator.__class__.__name__} failed: {e}")
                result.add_error(f"Validator error: {e}")
        
        # Log summary
        if result.is_valid:
            if result.warnings:
                self.logger.warning(
                    f"Validation passed with {len(result.warnings)} warning(s)"
                )
            else:
                self.logger.info("Validation passed with no warnings")
        else:
            self.logger.error(
                f"Validation failed with {len(result.errors)} error(s)"
            )
        
        return result
    
    def validate_quick(self, pathway: PathwayData) -> bool:
        """
        Quick validation (only checks critical errors).
        
        Args:
            pathway: PathwayData object to validate
            
        Returns:
            True if valid, False otherwise
        """
        result = self.validate(pathway)
        return result.is_valid


# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(name)s - %(levelname)s - %(message)s'
    )
    
    print("Pathway Validator Example")
    print("=" * 50)
    print()
    print("To validate pathway data:")
    print("  validator = PathwayValidator()")
    print("  result = validator.validate(pathway_data)")
    print("  if result.is_valid:")
    print("      print('✅ Valid')")
    print("  else:")
    print("      for error in result.errors:")
    print("          print(f'❌ {error}')")
