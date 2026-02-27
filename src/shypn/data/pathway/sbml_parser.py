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
import math
from shypn.utils.safe_eval import safe_eval_numeric

try:
    import libsbml
except ImportError:
    libsbml = None
    logging.warning("libsbml not available. SBML parsing will not work.")

from .converters import UnitConverter, ConcentrationCalculator
from .extractors import (
    SpeciesExtractor,
    ReactionExtractor,
    CompartmentExtractor,
    ParameterExtractor,
    EventExtractor,
    AnnotationExtractor,
    UnitExtractor,
    FunctionDefinitionExtractor,
    FunctionDefinition
)
from .sbml_validator import SBMLValidator, format_validation_report
from .pathway_data import (
    PathwayData, 
    Species, 
    Reaction,
    Event,
    Annotation,
    Compartment,
    UnitDefinition
)


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
        
        # Validate SBML model for compatibility (NEW)
        self.logger.info("Validating SBML model...")
        validator = SBMLValidator(model, self.logger)
        is_valid, issues = validator.validate()
        
        # Store issues for later inclusion in metadata
        self._validation_issues = issues
        
        # Print validation report
        report = format_validation_report(issues)
        print(report)
        
        # Only block on truly critical structural issues (none currently defined)
        # Most issues are warnings that allow import to proceed
        critical_issues = [i for i in issues if i.severity.value == "critical"]
        error_issues = [i for i in issues if i.severity.value == "error"]
        
        if critical_issues:
            raise ValueError(
                f"Cannot import SBML model: {len(critical_issues)} critical issue(s) found.\n"
                "These represent structural problems that will cause immediate failure.\n"
                "See validation report above for details."
            )
        
        # Show warning but allow import to proceed
        if error_issues:
            print("\n" + "=" * 80)
            print(f"⚠️  WARNING: {len(error_issues)} error(s) found but import will proceed.")
            print("Simulation may fail or produce incorrect results.")
            print("=" * 80 + "\n")
        
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
        function_extractor = FunctionDefinitionExtractor(model, logger)
        species_extractor = SpeciesExtractor(model, logger)
        reaction_extractor = ReactionExtractor(model, logger)
        event_extractor = EventExtractor(model, logger)
        annotation_extractor = AnnotationExtractor(model, logger)
        
        # Step 2: Extract all elements (in dependency order)
        compartments_enhanced = compartment_extractor.extract()
        compartments_legacy = compartment_extractor.extract_legacy()
        unit_defs = unit_extractor.extract()
        parameters = parameter_extractor.extract()
        functions = function_extractor.extract()  # NEW: Extract function definitions
        all_species = species_extractor.extract()
        reactions = reaction_extractor.extract()
        events = event_extractor.extract()
        annotations = annotation_extractor.extract()
        
        # Step 3: Expand function calls in reaction formulas
        if functions:
            self._expand_function_calls(reactions, functions)
        
        # Step 4: Apply annotations to species/reactions
        self._apply_annotations(all_species, reactions, annotations)
        
        # Step 5: Link species to compartment objects
        self._link_compartments(all_species, compartments_enhanced)
        
        # Step 6: Filter isolated species if requested
        if filter_isolated_species:
            species = self._filter_isolated_species(all_species, reactions)
        else:
            species = all_species
            self.logger.debug("Including all species (no filtering)")
        
        # Step 6.5: Evaluate assignment rules at t=0 and store for runtime (NEW)
        assignment_rule_info = self._evaluate_assignment_rules(model, species, parameters)
        
        # Step 7: Merge compartment sizes into parameters (for kinetic formulas)
        for comp_id, comp in compartments_enhanced.items():
            parameters[comp_id] = comp.size
        self.logger.debug(f"Merged {len(compartments_enhanced)} compartment sizes into parameters")
        
        # Step 8: Create metadata
        metadata = self._create_metadata(model, filepath)
        
        # Store assignment rule metadata (NEW)
        if assignment_rule_info and assignment_rule_info['count'] > 0:
            metadata['assignment_rules'] = assignment_rule_info
            self.logger.info(
                f"Stored {len(assignment_rule_info['species_rules'])} species assignment rules, "
                f"{len(assignment_rule_info['parameter_rules'])} parameter rules"
            )
        
        # Store validation issues in metadata (NEW)
        if hasattr(self, '_validation_issues'):
            metadata['validation_issues'] = [
                {
                    'severity': issue.severity.value,
                    'category': issue.category,
                    'message': issue.message,
                    'suggestion': issue.suggestion
                }
                for issue in self._validation_issues
            ]
        
        # Step 8.5: Add function definition metadata
        if functions:
            metadata['function_definitions_count'] = len(functions)
            metadata['function_definitions'] = [f"{func_id}({', '.join(func.arguments)})" 
                                               for func_id, func in functions.items()]
        
        # Step 9: Assemble PathwayData
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
        
        # Step 10: Validate formulas for undeclared variables
        self._validate_formula_variables(pathway_data)
        
        # Step 11: Post-processing (unit conversion, concentration calculation)
        # TODO: Implement in future PR when simulation integration is ready
        # pathway_data = self._postprocess(pathway_data)
        
        return pathway_data
    
    def _expand_function_calls(self,
                               reactions: List[Reaction],
                               functions: Dict[str, FunctionDefinition]) -> None:
        """
        Expand user-defined function calls in reaction formulas.
        
        Replaces function calls like R_PFK(x, y, z) with their expanded definitions.
        Uses regex to find and replace function calls with actual argument substitution.
        
        Args:
            reactions: List of Reaction objects to process
            functions: Dict of FunctionDefinition objects
            
        Example:
            Formula: "Vmax * R_PFK(ATP, F6P, 0.5)"
            Function: R_PFK(x, y, z) = x * y / (z + x)
            Result:  "Vmax * ((ATP) * (F6P) / ((0.5) + (ATP)))"
        """
        if not functions:
            return
        
        import re
        
        self.logger.info(f"Expanding {len(functions)} function definitions in formulas...")
        
        expanded_count = 0
        
        for reaction in reactions:
            if not reaction.kinetic_law or not reaction.kinetic_law.formula:
                continue
            
            formula = reaction.kinetic_law.formula
            original_formula = formula
            
            # Expand each function that appears in the formula
            for func_id, func_def in functions.items():
                # Pattern: function_name(args...)
                # Matches: R_PFK(ATP, F6P, gR) or R_PFK( ATP , F6P , gR )
                pattern = rf'\b{re.escape(func_id)}\s*\((.*?)\)'
                
                def replace_call(match):
                    """Replace a single function call with expanded definition."""
                    args_str = match.group(1)
                    
                    # Split arguments, handling nested parentheses
                    args = self._split_function_args(args_str)
                    
                    try:
                        expanded = func_def.expand(args)
                        return f"({expanded})"
                    except ValueError as e:
                        self.logger.warning(
                            f"Failed to expand {func_id} in reaction {reaction.id}: {e}"
                        )
                        return match.group(0)  # Keep original if expansion fails
                
                # Replace all occurrences of this function
                formula = re.sub(pattern, replace_call, formula)
            
            # Update formula if changed
            if formula != original_formula:
                reaction.kinetic_law.formula = formula
                expanded_count += 1
                self.logger.debug(
                    f"  {reaction.id}: Expanded function calls\n"
                    f"    Before: {original_formula[:100]}...\n"
                    f"    After:  {formula[:100]}..."
                )
        
        self.logger.info(f"Expanded functions in {expanded_count} reaction formulas")
    
    def _split_function_args(self, args_str: str) -> List[str]:
        """Split function arguments, respecting nested parentheses.
        
        Args:
            args_str: Comma-separated argument string
            
        Returns:
            List of argument strings
            
        Example:
            "ATP, F6P, (Km + S)"  →  ["ATP", "F6P", "(Km + S)"]
        """
        args = []
        current = []
        depth = 0
        
        for char in args_str:
            if char == ',' and depth == 0:
                args.append(''.join(current).strip())
                current = []
            else:
                if char == '(':
                    depth += 1
                elif char == ')':
                    depth -= 1
                current.append(char)
        
        # Add last argument
        if current:
            args.append(''.join(current).strip())
        
        return args
    
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
    
    def _evaluate_assignment_rules(self,
                                   model,
                                   species: List[Species],
                                   parameters: Dict[str, float]) -> None:
        """
        Evaluate assignment rules at t=0 to set initial values.
        
        Assignment rules define algebraic relationships like:
            ATP = (P - ADP) / 2
        
        This method evaluates them once at initialization to get correct
        starting values. NOTE: Rules are NOT re-evaluated during simulation,
        which may cause incorrect results.
        
        Args:
            model: libsbml Model object
            species: List of Species objects to update
            parameters: Dict of parameters
        """
        num_rules = model.getNumRules()
        if num_rules == 0:
            return {'count': 0, 'species_rules': [], 'parameter_rules': [], 'evaluated': [], 'unevaluated': []}
        
        assignment_rules = []
        for i in range(num_rules):
            rule = model.getRule(i)
            if rule.isAssignment():
                variable = rule.getVariable()
                math_ast = rule.getMath()
                assignment_rules.append((variable, math_ast))
        
        if not assignment_rules:
            return {'count': 0, 'species_rules': [], 'parameter_rules': [], 'evaluated': [], 'unevaluated': []}
        
        self.logger.info(f"Evaluating {len(assignment_rules)} assignment rule(s) at t=0...")
        
        # Build evaluation context
        context = {}
        
        # Add all species initial values
        species_dict = {s.id: s for s in species}
        for s in species:
            context[s.id] = s.initial_concentration or 0.0
        
        # Add all parameters
        context.update(parameters)
        
        # Add compartment sizes
        for i in range(model.getNumCompartments()):
            comp = model.getCompartment(i)
            context[comp.getId()] = comp.getSize()
        
        # Evaluate rules in order (handle dependencies)
        max_iterations = 10  # Prevent infinite loops
        evaluated = set()
        
        for iteration in range(max_iterations):
            made_progress = False
            
            for variable, math_ast in assignment_rules:
                if variable in evaluated:
                    continue
                
                try:
                    # Convert MathML to Python expression
                    formula = libsbml.formulaToL3String(math_ast)
                    
                    # Replace SBML power operator (^) with Python power (**)
                    formula = formula.replace('^', '**')
                    
                    # Try to evaluate
                    import math
                    import numpy as np
                    safe_context = {
                        "__builtins__": {},
                        "sqrt": math.sqrt,
                        "pow": pow,
                        "exp": math.exp,
                        "log": math.log,
                        "log10": math.log10,
                        "sin": math.sin,
                        "cos": math.cos,
                        "tan": math.tan,
                        "abs": abs,
                        "min": min,
                        "max": max,
                    }
                    safe_context.update(context)
                    
                    # Safely evaluate assignment rule (replaces eval() for security)
                    value = safe_eval_numeric(formula, safe_context, allow_math=True)
                    
                    # Update context and species/parameter
                    context[variable] = value
                    
                    # Update the actual species or parameter
                    if variable in species_dict:
                        spec = species_dict[variable]
                        spec.initial_concentration = value
                        # Store the assignment rule formula for potential runtime re-evaluation
                        spec.assignment_rule = formula
                        spec.metadata['has_assignment_rule'] = True
                        self.logger.debug(f"  Rule: {variable} = {value:.6g} (formula stored)")
                    elif variable in parameters:
                        parameters[variable] = value
                        self.logger.debug(f"  Rule: {variable} = {value:.6g}")
                    
                    evaluated.add(variable)
                    made_progress = True
                    
                except Exception as e:
                    # Can't evaluate yet (may depend on other rules not yet evaluated)
                    # This is expected during iterative evaluation - silently skip
                    self.logger.debug("Rule %r deferred (not yet evaluable): %s", variable, e)
            
            if not made_progress:
                break
        
        # Warn about unevaluated rules
        unevaluated = set(var for var, _ in assignment_rules) - evaluated
        if unevaluated:
            self.logger.warning(
                f"Could not evaluate assignment rules for: {', '.join(unevaluated)}. "
                f"These may have circular dependencies or use unsupported functions."
            )
        else:
            self.logger.info(f"✓ Evaluated all {len(assignment_rules)} assignment rules")
        
        # Collect metadata about assignment rules
        species_dict = {s.id: s for s in species}
        species_rules = [
            {'variable': var, 'formula': libsbml.formulaToL3String(math_ast)}
            for var, math_ast in assignment_rules
            if var in species_dict
        ]
        parameter_rules = [
            {'variable': var, 'formula': libsbml.formulaToL3String(math_ast)}
            for var, math_ast in assignment_rules
            if var in parameters
        ]
        
        return {
            'count': len(assignment_rules),
            'species_rules': species_rules,
            'parameter_rules': parameter_rules,
            'evaluated': list(evaluated),
            'unevaluated': list(unevaluated)
        }
    
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
                except (ValueError, TypeError) as e:
                    self.logger.debug(f"Failed to process SBML notes: {e}")
        
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
    
    def _validate_formula_variables(self, pathway_data: PathwayData) -> None:
        """
        Validate that all variables in rate formulas are declared.
        
        Checks that every variable in a formula is one of:
        - Species ID (place)
        - Global parameter
        - Local kinetic law parameter
        - Compartment ID
        - Mathematical function (sin, cos, exp, log, etc.)
        
        Args:
            pathway_data: PathwayData to validate
            
        Raises:
            ValueError: If undeclared variables found
        """
        import re
        
        # Build set of all valid identifiers
        valid_ids = set()
        
        # Add species IDs
        valid_ids.update(s.id for s in pathway_data.species)
        
        # Add global parameters
        valid_ids.update(pathway_data.parameters.keys())
        
        # Add compartment IDs
        valid_ids.update(pathway_data.compartments_enhanced.keys())
        
        # Add common math functions (don't flag these as undeclared)
        math_functions = {
            'sin', 'cos', 'tan', 'exp', 'log', 'log10', 'sqrt', 'abs', 
            'ceil', 'floor', 'pow', 'min', 'max', 'sum', 'product',
            'pi', 'e', 'inf', 'nan', 'time', 't'  # time is simulation time
        }
        valid_ids.update(math_functions)
        
        # Check each reaction's formula
        undeclared_vars = []
        
        for reaction in pathway_data.reactions:
            if not reaction.kinetic_law or not reaction.kinetic_law.formula:
                continue
            
            formula = reaction.kinetic_law.formula
            
            # Add local parameters for this reaction
            local_params = set(reaction.kinetic_law.parameters.keys()) if reaction.kinetic_law.parameters else set()
            reaction_valid_ids = valid_ids | local_params
            
            # Extract all identifiers from formula (alphanumeric + underscore)
            identifiers = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', formula)
            
            # Check each identifier
            for identifier in identifiers:
                if identifier not in reaction_valid_ids:
                    undeclared_vars.append((reaction.id, identifier, formula))
        
        # Report errors
        if undeclared_vars:
            parts = ["Undeclared variables in rate formulas:\n"]
            for reaction_id, var_name, formula in undeclared_vars:
                parts.append(f"  Reaction '{reaction_id}': '{var_name}' not found\n")
                parts.append(f"    Formula: {formula}\n")
            parts += [
                "\nValid identifiers:\n",
                f"  Species: {sorted([s.id for s in pathway_data.species])}\n",
                f"  Parameters: {sorted(pathway_data.parameters.keys())}\n",
                f"  Compartments: {sorted(pathway_data.compartments_enhanced.keys())}\n",
            ]
            error_msg = "".join(parts)
            
            self.logger.error(error_msg)
            raise ValueError(error_msg)
        
        self.logger.info("Formula validation passed - all variables declared")


# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(name)s - %(levelname)s - %(message)s'
    )
    
    # Example: Parse SBML file
    pass  # Implementation examples removed for brevity
