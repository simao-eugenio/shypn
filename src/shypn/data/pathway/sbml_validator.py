"""SBML Validator - Detects unsupported features and validates model semantics.

This module performs comprehensive validation of SBML models before conversion:
1. Detects unsupported SBML features (assignment rules, rate rules, constraints, etc.)
2. Validates parameter ranges (checks for extreme values)
3. Validates initial conditions (species amounts/concentrations)
4. Checks for algebraic dependencies that require special handling
5. Warns about potential simulation issues

Design Philosophy:
- Fail fast: Detect problems during import, not during simulation
- Clear guidance: Explain what's unsupported and suggest alternatives
- Defensive: Assume SBML models may have edge cases
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

try:
    import libsbml
except ImportError:
    libsbml = None


class ValidationSeverity(Enum):
    """Severity levels for validation issues."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ValidationIssue:
    """A single validation issue found in the SBML model."""
    severity: ValidationSeverity
    category: str  # e.g., "assignment_rules", "extreme_values", "unsupported_feature"
    message: str
    element_id: Optional[str] = None
    suggestion: Optional[str] = None


class SBMLValidator:
    """Validates SBML models for compatibility with the import pipeline.
    
    Checks for:
    - Unsupported SBML features (assignment rules, rate rules, constraints)
    - Extreme parameter values that may cause numerical issues
    - Missing initial conditions
    - Algebraic dependencies between species
    - Invalid kinetic law formulas
    """
    
    # Numerical limits for validation
    MAX_SAFE_VALUE = 1e15  # Values above this may cause numerical issues
    MIN_SAFE_VALUE = 1e-15  # Values below this (but > 0) may cause underflow
    
    def __init__(self, model, logger=None):
        """Initialize validator with SBML model.
        
        Args:
            model: libsbml.Model object
            logger: Optional logger instance
        """
        self.model = model
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        self.issues: List[ValidationIssue] = []
    
    def validate(self) -> Tuple[bool, List[ValidationIssue]]:
        """Run all validation checks.
        
        Returns:
            Tuple of (is_valid, issues_list)
            is_valid: True if no critical/error issues found
            issues_list: List of all validation issues
        """
        self.issues = []
        
        # Check for unsupported SBML features
        self._check_assignment_rules()
        self._check_rate_rules()
        self._check_algebraic_rules()
        self._check_constraints()
        self._check_initial_assignments()
        self._check_events_complexity()
        
        # Validate numerical values
        self._validate_parameters()
        self._validate_species_initial_values()
        self._validate_compartment_sizes()
        
        # Check formula validity and stochastic compatibility
        self._check_reversible_formulas_stochastic_risk()
        self._check_formula_dependencies()
        
        # Determine if model is valid (no errors or critical issues)
        is_valid = not any(
            issue.severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL]
            for issue in self.issues
        )
        
        return is_valid, self.issues
    
    def _check_assignment_rules(self):
        """Check for assignment rules (may be incompatible with stochastic simulation).
        
        Assignment rules define algebraic constraints that should be maintained throughout
        the simulation. SBML distinguishes between:
        - Assignment rules for SPECIES: Problematic in stochastic (not re-evaluated)
        - Assignment rules for PARAMETERS: Usually fine (computed constants)
        - Initial assignments: Safe (only evaluated at t=0)
        """
        num_rules = self.model.getNumRules()
        assignment_rules_species = []
        assignment_rules_parameters = []
        
        for i in range(num_rules):
            rule = self.model.getRule(i)
            if rule.isAssignment():
                variable = rule.getVariable()
                formula = libsbml.formulaToL3String(rule.getMath())
                
                # Check what type of entity this rule targets
                species = self.model.getSpecies(variable)
                parameter = self.model.getParameter(variable)
                
                if species is not None:
                    # Assignment rule for a species
                    # Check if it's a boundary species (external reservoir)
                    is_boundary = species.getBoundaryCondition()
                    
                    if not is_boundary:
                        # Non-boundary species with assignment rule = PROBLEMATIC
                        assignment_rules_species.append((variable, formula, "internal species"))
                    else:
                        # Boundary species with assignment rule = usually fine
                        self.logger.debug(f"Assignment rule for boundary species '{variable}' (acceptable)")
                elif parameter is not None:
                    # Assignment rule for a parameter (computed constant)
                    # This is generally fine - just a derived parameter
                    assignment_rules_parameters.append((variable, formula))
                else:
                    # Unknown target - could be compartment size, etc.
                    self.logger.debug(f"Assignment rule for '{variable}' (unknown entity type)")
        
        # Only warn about assignment rules on internal (non-boundary) species
        if assignment_rules_species:
            variables = ", ".join([var for var, _, _ in assignment_rules_species[:3]])
            if len(assignment_rules_species) > 3:
                variables += f", ... (+{len(assignment_rules_species)-3} more)"
            
            # Store detailed rule information for UI display
            rules_detail = "\n".join([f"  • {var} ({vtype}): {formula[:50]}{'...' if len(formula) > 50 else ''}" 
                                      for var, formula, vtype in assignment_rules_species[:5]])
            if len(assignment_rules_species) > 5:
                rules_detail += f"\n  ... and {len(assignment_rules_species)-5} more"
            
            self.issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category="assignment_rules",
                message=f"Assignment rules on species detected ({len(assignment_rules_species)} rules): {variables}",
                suggestion=(
                    "⚠️  STOCHASTIC SIMULATION RISK:\n"
                    "Assignment rules on internal species are evaluated ONCE at t=0 but NOT\n"
                    "re-evaluated during stochastic simulation. This causes species values to\n"
                    "become stale, leading to:\n"
                    "  • Incorrect reaction rates (uses outdated species values)\n"
                    "  • Extreme propensities (>1e17) → simulation failure\n"
                    "\n"
                    "RECOMMENDATIONS:\n"
                    "  ✓ Use CONTINUOUS mode (re-evaluates formulas at each timestep)\n"
                    "  ✓ Use HYBRID mode (continuous for reactions using rule-defined species)\n"
                    "  ✗ Avoid STOCHASTIC mode (will likely fail)\n"
                    "\n"
                    f"Affected species:\n{rules_detail}\n"
                    "\n"
                    "NOTE: Assignment rules on parameters or boundary species are acceptable."
                )
            ))
        
        # Log parameter assignment rules as INFO (not problematic)
        if assignment_rules_parameters:
            self.logger.info(
                f"Found {len(assignment_rules_parameters)} assignment rule(s) on parameters "
                f"(acceptable - computed constants)"
            )
    
    def _check_rate_rules(self):
        """Check for rate rules (currently unsupported)."""
        num_rules = self.model.getNumRules()
        rate_rules = []
        
        for i in range(num_rules):
            rule = self.model.getRule(i)
            if rule.isRate():
                variable = rule.getVariable()
                rate_rules.append(variable)
        
        if rate_rules:
            self.issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category="rate_rules",
                message=f"Model contains {len(rate_rules)} rate rule(s): {', '.join(rate_rules)}",
                suggestion=(
                    "Rate rules (dX/dt = f(...)) are not yet fully supported. "
                    "They require ODE integration which may not execute correctly."
                )
            ))
    
    def _check_algebraic_rules(self):
        """Check for algebraic rules (currently unsupported)."""
        num_rules = self.model.getNumRules()
        algebraic_rules = 0
        
        for i in range(num_rules):
            rule = self.model.getRule(i)
            if rule.isAlgebraic():
                algebraic_rules += 1
        
        if algebraic_rules > 0:
            self.issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category="algebraic_rules",
                message=f"Model contains {algebraic_rules} algebraic rule(s)",
                suggestion="Algebraic rules are not supported and will be ignored."
            ))
    
    def _check_constraints(self):
        """Check for constraints (informational only)."""
        num_constraints = self.model.getNumConstraints()
        
        if num_constraints > 0:
            self.issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category="constraints",
                message=f"Model contains {num_constraints} constraint(s)",
                suggestion="Constraints are for validation only and will not be enforced during simulation."
            ))
    
    def _check_initial_assignments(self):
        """Check for initial assignments (may need special handling)."""
        num_initial = self.model.getNumInitialAssignments()
        
        if num_initial > 0:
            assignments = []
            for i in range(num_initial):
                ia = self.model.getInitialAssignment(i)
                symbol = ia.getSymbol()
                assignments.append(symbol)
            
            self.issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category="initial_assignments",
                message=f"Model contains {num_initial} initial assignment(s): {', '.join(assignments)}",
                suggestion=(
                    "Initial assignments will be evaluated once at t=0. "
                    "If they depend on other assignments, order matters."
                )
            ))
    
    def _check_events_complexity(self):
        """Check if events have complex features."""
        num_events = self.model.getNumEvents()
        complex_events = []
        
        for i in range(num_events):
            event = self.model.getEvent(i)
            
            # Check for priority (affects event ordering)
            if event.isSetPriority():
                complex_events.append(f"{event.getId()} (has priority)")
            
            # Check for delay (requires time-shifted execution)
            if event.isSetDelay():
                complex_events.append(f"{event.getId()} (has delay)")
            
            # Check for persistent triggers
            trigger = event.getTrigger()
            if trigger and not trigger.getPersistent():
                complex_events.append(f"{event.getId()} (non-persistent trigger)")
        
        if complex_events:
            self.issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category="events_complex",
                message=f"Events with complex features: {', '.join(complex_events)}",
                suggestion="Event priorities, delays, and non-persistent triggers may not be fully supported."
            ))
    
    def _validate_parameters(self):
        """Check parameter values for extreme numbers."""
        num_params = self.model.getNumParameters()
        extreme_params = []
        
        for i in range(num_params):
            param = self.model.getParameter(i)
            param_id = param.getId()
            value = param.getValue()
            
            if abs(value) > self.MAX_SAFE_VALUE:
                extreme_params.append((param_id, value, "too large"))
            elif 0 < abs(value) < self.MIN_SAFE_VALUE:
                extreme_params.append((param_id, value, "too small"))
        
        if extreme_params:
            summary = ", ".join([f"{pid}={val:.2e}" for pid, val, _ in extreme_params[:3]])
            if len(extreme_params) > 3:
                summary += f" (+{len(extreme_params)-3} more)"
            
            self.issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category="extreme_values",
                message=f"Parameters with extreme values: {summary}",
                suggestion=(
                    "Extreme parameter values may cause numerical instability. "
                    "Consider rescaling the model to use values in range [1e-15, 1e15]."
                )
            ))
    
    def _validate_species_initial_values(self):
        """Check species initial amounts/concentrations for extreme values."""
        num_species = self.model.getNumSpecies()
        extreme_species = []
        missing_initial = []
        
        for i in range(num_species):
            species = self.model.getSpecies(i)
            spec_id = species.getId()
            
            # Check if initial value is set
            has_initial = species.isSetInitialAmount() or species.isSetInitialConcentration()
            
            if not has_initial:
                # Check if there's an assignment rule or initial assignment
                has_rule = self.model.getRuleByVariable(spec_id) is not None
                has_init_assign = self.model.getInitialAssignment(spec_id) is not None
                
                if not has_rule and not has_init_assign:
                    missing_initial.append(spec_id)
            else:
                # Get the value
                if species.isSetInitialAmount():
                    value = species.getInitialAmount()
                else:
                    value = species.getInitialConcentration()
                
                if abs(value) > self.MAX_SAFE_VALUE:
                    extreme_species.append((spec_id, value, "too large"))
                elif 0 < abs(value) < self.MIN_SAFE_VALUE:
                    extreme_species.append((spec_id, value, "too small"))
        
        if extreme_species:
            summary = ", ".join([f"{sid}={val:.2e}" for sid, val, _ in extreme_species[:3]])
            if len(extreme_species) > 3:
                summary += f" (+{len(extreme_species)-3} more)"
            
            self.issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category="extreme_values",
                message=f"Species with extreme initial values: {summary}",
                suggestion="Extreme initial values may cause simulation instability."
            ))
        
        if missing_initial:
            summary = ", ".join(missing_initial[:5])
            if len(missing_initial) > 5:
                summary += f" (+{len(missing_initial)-5} more)"
            
            self.issues.append(ValidationIssue(
                severity=ValidationSeverity.INFO,
                category="missing_initial",
                message=f"Species without explicit initial values: {summary}",
                suggestion="These species default to 0. Verify this matches model intent."
            ))
    
    def _validate_compartment_sizes(self):
        """Check compartment sizes for extreme values."""
        num_comps = self.model.getNumCompartments()
        extreme_comps = []
        
        for i in range(num_comps):
            comp = self.model.getCompartment(i)
            comp_id = comp.getId()
            size = comp.getSize()
            
            if size > self.MAX_SAFE_VALUE:
                extreme_comps.append((comp_id, size, "too large"))
            elif 0 < size < self.MIN_SAFE_VALUE:
                extreme_comps.append((comp_id, size, "too small"))
        
        if extreme_comps:
            summary = ", ".join([f"{cid}={size:.2e}" for cid, size, _ in extreme_comps])
            
            self.issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category="extreme_values",
                message=f"Compartments with extreme sizes: {summary}",
                suggestion="Extreme compartment sizes may cause numerical issues in rate calculations."
            ))
    
    def _check_reversible_formulas_stochastic_risk(self):
        """Inform about reversible reaction formulas and Skellam distribution support.
        
        Reversible reactions with net rate formulas (k_f*A - k_r*B) produce difference
        of Poisson random variables, which follows a Skellam distribution. The τ-leaping
        engine automatically detects these patterns and uses Skellam sampling.
        """
        reversible_reactions = []
        
        for i in range(self.model.getNumReactions()):
            reaction = self.model.getReaction(i)
            kinetic_law = reaction.getKineticLaw()
            
            if kinetic_law is None:
                continue
            
            # Get formula as string
            math_ast = kinetic_law.getMath()
            if math_ast is None:
                continue
            
            formula = libsbml.formulaToL3String(math_ast)
            
            # Detect reversible patterns
            has_subtraction = ' - ' in formula
            has_reverse_keywords = any(keyword in formula.lower() 
                                      for keyword in ['k_r', 'kr_', 'k_rev', 'krev', 'k_backward'])
            
            if has_subtraction or has_reverse_keywords:
                reaction_id = reaction.getId()
                reaction_name = reaction.getName() or reaction_id
                reversible_reactions.append((reaction_name, formula))
        
        if reversible_reactions:
            reactions_list = ", ".join([name for name, _ in reversible_reactions[:3]])
            if len(reversible_reactions) > 3:
                reactions_list += f", ... (+{len(reversible_reactions)-3} more)"
            
            # Detailed list for UI display
            reactions_detail = "\n".join([f"  • {name}: {formula[:60]}{'...' if len(formula) > 60 else ''}" 
                                          for name, formula in reversible_reactions[:5]])
            if len(reversible_reactions) > 5:
                reactions_detail += f"\n  ... and {len(reversible_reactions)-5} more"
            
            self.issues.append(ValidationIssue(
                severity=ValidationSeverity.INFO,
                category="reversible_formulas",
                message=f"Reversible reaction formulas detected ({len(reversible_reactions)} reactions): {reactions_list}",
                suggestion=(
                    "ℹ️  REVERSIBLE REACTIONS WITH SKELLAM DISTRIBUTION:\n"
                    "Reversible reactions with net rate formulas (e.g., k_f*A - k_r*B) are now\n"
                    "FULLY SUPPORTED in stochastic simulation using the Skellam distribution.\n"
                    "\n"
                    "The τ-leaping engine automatically:\n"
                    "  ✓ Detects reversible reaction patterns (formulas with subtraction)\n"
                    "  ✓ Uses Skellam sampling: X ~ Poisson(λ_forward) - Poisson(λ_reverse)\n"
                    "  ✓ Handles net reverse flux correctly (negative Δn values)\n"
                    "  ✓ Maintains thermodynamic consistency\n"
                    "\n"
                    "SIMULATION MODE RECOMMENDATIONS:\n"
                    "  ✓ STOCHASTIC with τ-leaping: Automatically uses Skellam (recommended)\n"
                    "  ✓ CONTINUOUS mode: Alternative for very fast reactions\n"
                    "  ✓ HYBRID mode: Combines both approaches\n"
                    "\n"
                    f"Reactions with reversible patterns:\n{reactions_detail}"
                )
            ))
            
            self.logger.info(
                f"Detected {len(reversible_reactions)} reactions with reversible formulas (Skellam distribution will be used)"
            )
    
    def _check_formula_dependencies(self):
        """Check if reaction formulas reference species defined by assignment rules."""
        num_rules = self.model.getNumRules()
        rule_variables = set()
        
        # Collect all variables defined by rules
        for i in range(num_rules):
            rule = self.model.getRule(i)
            if rule.isAssignment():
                rule_variables.add(rule.getVariable())
        
        if not rule_variables:
            return
        
        # Check if any reaction references these variables
        num_reactions = self.model.getNumReactions()
        problematic_reactions = []
        
        for i in range(num_reactions):
            reaction = self.model.getReaction(i)
            kl = reaction.getKineticLaw()
            if kl and kl.isSetMath():
                formula = libsbml.formulaToL3String(kl.getMath())
                
                # Check if formula contains any rule-defined variables
                for var in rule_variables:
                    if var in formula:
                        problematic_reactions.append((reaction.getId(), var))
                        break
        
        if problematic_reactions:
            summary = ", ".join([f"{rid}→{var}" for rid, var in problematic_reactions[:3]])
            if len(problematic_reactions) > 3:
                summary += f" (+{len(problematic_reactions)-3} more)"
            
            self.issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category="rule_dependencies",
                message=f"Reactions reference rule-defined variables: {summary}",
                suggestion=(
                    "Kinetic laws reference species defined by assignment rules. "
                    "Rules are evaluated at t=0 but not updated during simulation, "
                    "which may cause incorrect propensity calculations. "
                    "Monitor for extreme propensity values during simulation."
                )
            ))


def format_validation_report(issues: List[ValidationIssue]) -> str:
    """Format validation issues into a human-readable report.
    
    Args:
        issues: List of ValidationIssue objects
        
    Returns:
        Formatted string report
    """
    if not issues:
        return "✓ No validation issues found"
    
    # Group by severity
    by_severity: Dict[ValidationSeverity, List[Any]] = {
        ValidationSeverity.CRITICAL: [],
        ValidationSeverity.ERROR: [],
        ValidationSeverity.WARNING: [],
        ValidationSeverity.INFO: []
    }
    
    for issue in issues:
        by_severity[issue.severity].append(issue)
    
    lines: List[str] = []
    # Validation report commented out to reduce console noise
    # Only errors/critical issues will be shown via logger
    # lines.append("=" * 80)
    # lines.append("SBML VALIDATION REPORT")
    # lines.append("=" * 80)
    return ""  # Return early to skip verbose report
    
    # Show critical issues first
    for severity in [ValidationSeverity.CRITICAL, ValidationSeverity.ERROR, 
                     ValidationSeverity.WARNING, ValidationSeverity.INFO]:
        severity_issues = by_severity[severity]
        if not severity_issues:
            continue
        
        icon = {"critical": "🔴", "error": "❌", "warning": "⚠️", "info": "ℹ️"}[severity.value]
        lines.append(f"\n{icon} {severity.value.upper()}: {len(severity_issues)} issue(s)")
        lines.append("-" * 80)
        
        for issue in severity_issues:
            lines.append(f"\n[{issue.category}] {issue.message}")
            if issue.suggestion:
                lines.append(f"  → {issue.suggestion}")
    
    lines.append("\n" + "=" * 80)
    
    return "\n".join(lines)
