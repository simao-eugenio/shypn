#!/usr/bin/env python3
"""Thermodynamic Feasibility Analyzer for Biological Petri Nets.

This analyzer performs basic thermodynamic checks on biochemical reactions
to identify potentially unfavorable or problematic reaction directions.

CURRENT IMPLEMENTATION: Basic checks without chemical database integration
FUTURE ENHANCEMENT: Full ΔG°' calculations with compound database

Scientific Background:
- Gibbs Free Energy: ΔG = ΔG°' + RT ln(Q)
- Favorable reactions: ΔG < 0
- Unfavorable reactions: ΔG > 0 (need coupling)
- Equilibrium: ΔG = 0

Author: Simão Eugénio
Date: November 20, 2025
"""

from typing import Dict, List, Tuple, Optional, Set, Any
from dataclasses import dataclass
import re

from shypn.topology.base.topology_analyzer import TopologyAnalyzer
from shypn.topology.base.analysis_result import AnalysisResult
from shypn.topology.base.exceptions import TopologyAnalysisError


@dataclass
class ThermodynamicIssue:
    """Issue detected by thermodynamic analysis."""
    transition_id: str
    issue_type: str
    severity: str  # 'info', 'warning', 'error'
    description: str
    suggestion: Optional[str] = None


@dataclass
class ReactionThermodynamics:
    """Thermodynamic properties of a reaction."""
    transition_id: str
    reversible: bool
    likely_favorable: Optional[bool]  # None if unknown
    needs_coupling: bool
    equilibrium_likely: bool
    notes: List[str]


class ThermodynamicAnalyzer(TopologyAnalyzer):
    """Basic thermodynamic feasibility analyzer.
    
    CURRENT CAPABILITIES (Basic Implementation):
    - Detect reversibility inconsistencies
    - Identify reactions that should be coupled with ATP/GTP
    - Flag likely equilibrium states
    - Check for futile cycles
    - Validate reaction directionality
    
    FUTURE ENHANCEMENTS (Requires Chemical Database):
    - Calculate actual ΔG°' from compound databases (ChEBI, MetaCyc)
    - Compute concentration-dependent ΔG
    - pH and temperature corrections
    - Pseudoisomer handling (protonation states)
    - Group contribution estimation for missing data
    - Pathway-level thermodynamic analysis
    
    Example:
        >>> analyzer = ThermodynamicAnalyzer(model)
        >>> result = analyzer.analyze()
        >>> print(result.report)
    """
    
    def __init__(self, model: Any):
        """Initialize analyzer.
        
        Args:
            model: Petri net model to analyze
        """
        super().__init__(model)
        self.issues: List[ThermodynamicIssue] = []
        self.reaction_data: Dict[str, ReactionThermodynamics] = {}
        
        # FUTURE: Load from compound database
        self.high_energy_compounds = {
            'ATP', 'GTP', 'CTP', 'UTP',  # Nucleotide triphosphates
            'NADH', 'NADPH', 'FADH2',     # Reduced cofactors
            'Acetyl-CoA', 'AcetylCoA',    # High-energy thioesters
            'PEP',                         # Phosphoenolpyruvate
            '1,3-BPG', '1,3-Bisphosphoglycerate'  # High-energy phosphates
        }
        
        self.low_energy_compounds = {
            'ADP', 'GDP', 'CDP', 'UDP',   # Nucleotide diphosphates
            'AMP', 'GMP', 'CMP', 'UMP',   # Nucleotide monophosphates
            'NAD+', 'NADP+', 'FAD',       # Oxidized cofactors
            'CoA', 'CoASH',                # Free coenzyme A
            'Pi', 'PPi', 'Phosphate'      # Inorganic phosphate
        }
    
    def analyze(self, **kwargs) -> AnalysisResult:
        """Perform thermodynamic analysis.
        
        Args:
            **kwargs: Optional parameters (unused, for compatibility)
        
        Returns:
            AnalysisResult with formatted report
        """
        self.issues.clear()
        self.reaction_data.clear()
        
        # Run basic checks
        self._check_reversibility_consistency()
        self._check_atp_coupling()
        self._check_futile_cycles()
        self._check_equilibrium_states()
        self._analyze_energy_flow()
        
        report = self._format_report()
        
        return AnalysisResult(
            success=len([i for i in self.issues if i.severity == 'error']) == 0,
            summary=report,
            data={
                'issues': [
                    {
                        'transition_id': i.transition_id,
                        'type': i.issue_type,
                        'severity': i.severity,
                        'description': i.description,
                        'suggestion': i.suggestion
                    }
                    for i in self.issues
                ],
                'reaction_data': {
                    tid: {
                        'reversible': r.reversible,
                        'likely_favorable': r.likely_favorable,
                        'needs_coupling': r.needs_coupling,
                        'equilibrium_likely': r.equilibrium_likely,
                        'notes': r.notes
                    }
                    for tid, r in self.reaction_data.items()
                },
                'statistics': {
                    'total_transitions': len(self.model.transitions),
                    'errors': len([i for i in self.issues if i.severity == 'error']),
                    'warnings': len([i for i in self.issues if i.severity == 'warning']),
                    'info': len([i for i in self.issues if i.severity == 'info'])
                }
            }
        )
    
    def _check_reversibility_consistency(self):
        """Check if reversibility settings match likely thermodynamics.
        
        CURRENT: Heuristic-based on keywords and reaction patterns
        FUTURE: Calculate from ΔG°' database
        """
        for transition in self.model.transitions:
            is_reversible = self._is_reversible(transition)
            should_be_reversible = self._should_be_reversible(transition)
            
            notes = []
            
            # Check for mismatch
            if is_reversible and should_be_reversible is False:
                self.issues.append(ThermodynamicIssue(
                    transition_id=transition.id,
                    issue_type='reversibility_mismatch',
                    severity='warning',
                    description=f"Transition '{transition.label}' is reversible but appears highly exergonic (should be irreversible)",
                    suggestion="Consider making this transition irreversible if it's strongly favorable"
                ))
                notes.append("Marked reversible but likely irreversible")
            
            elif not is_reversible and should_be_reversible is True:
                self.issues.append(ThermodynamicIssue(
                    transition_id=transition.id,
                    issue_type='reversibility_mismatch',
                    severity='info',
                    description=f"Transition '{transition.label}' is irreversible but might be near equilibrium",
                    suggestion="Consider allowing reversibility if this reaction is near equilibrium"
                ))
                notes.append("Marked irreversible but possibly reversible")
            
            self.reaction_data[transition.id] = ReactionThermodynamics(
                transition_id=transition.id,
                reversible=is_reversible,
                likely_favorable=should_be_reversible is False,
                needs_coupling=False,  # Updated in _check_atp_coupling
                equilibrium_likely=should_be_reversible is True,
                notes=notes
            )
    
    def _check_atp_coupling(self):
        """Identify reactions that should be coupled with ATP hydrolysis.
        
        CURRENT: Pattern matching for biosynthetic reactions without ATP
        FUTURE: Calculate ΔG and determine coupling requirements
        """
        for transition in self.model.transitions:
            reactants = self._get_reactants(transition)
            products = self._get_products(transition)
            
            # Check if this is a biosynthetic reaction
            if self._is_biosynthetic(transition):
                # Check if ATP/GTP is involved
                has_energy_input = any(
                    self._matches_compound(r, self.high_energy_compounds)
                    for r in reactants
                )
                
                if not has_energy_input:
                    self.issues.append(ThermodynamicIssue(
                        transition_id=transition.id,
                        issue_type='missing_atp_coupling',
                        severity='warning',
                        description=f"Biosynthetic reaction '{transition.label}' lacks ATP/GTP coupling",
                        suggestion="Consider adding ATP → ADP coupling for unfavorable biosynthetic reactions"
                    ))
                    
                    if transition.id in self.reaction_data:
                        self.reaction_data[transition.id].needs_coupling = True
                        self.reaction_data[transition.id].notes.append("May need ATP coupling")
    
    def _check_futile_cycles(self):
        """Detect potential futile cycles (ATP-wasting loops).
        
        CURRENT: Simple cycle detection with ATP consumption
        FUTURE: Pathway-level thermodynamic analysis
        """
        # Find simple cycles in the network
        cycles = self._find_simple_cycles()
        
        for cycle in cycles:
            # Check if cycle consumes ATP but has no net output
            atp_consumed = False
            has_net_product = False
            
            for transition_id in cycle:
                # Find transition by ID
                transition = next((t for t in self.model.transitions if t.id == transition_id), None)
                if not transition:
                    continue
                
                reactants = self._get_reactants(transition)
                products = self._get_products(transition)
                
                # Check ATP consumption
                if any(self._matches_compound(r, {'ATP'}) for r in reactants):
                    atp_consumed = True
                
                # Check for products leaving the cycle
                for product in products:
                    if product not in cycle:
                        has_net_product = True
            
            if atp_consumed and not has_net_product:
                cycle_str = " → ".join(cycle)
                self.issues.append(ThermodynamicIssue(
                    transition_id=cycle[0],
                    issue_type='futile_cycle',
                    severity='warning',
                    description=f"Potential futile cycle detected: {cycle_str}",
                    suggestion="Verify this cycle has biological function (not just ATP waste)"
                ))
    
    def _check_equilibrium_states(self):
        """Identify reactions likely at equilibrium.
        
        CURRENT: Heuristic-based on isomerases and near-equilibrium reactions
        FUTURE: Calculate from K_eq and cellular concentrations
        """
        equilibrium_keywords = [
            'isomerase', 'mutase', 'epimerase',
            'equilibrium', 'reversible',
            'isomerization'
        ]
        
        for transition in self.model.transitions:
            label_lower = transition.label.lower()
            
            if any(keyword in label_lower for keyword in equilibrium_keywords):
                self.issues.append(ThermodynamicIssue(
                    transition_id=transition.id,
                    issue_type='equilibrium_state',
                    severity='info',
                    description=f"Reaction '{transition.label}' likely operates near equilibrium (ΔG ≈ 0)",
                    suggestion="Near-equilibrium reactions are normal, flux depends on substrate/product concentrations"
                ))
                
                if transition.id in self.reaction_data:
                    self.reaction_data[transition.id].equilibrium_likely = True
                    self.reaction_data[transition.id].notes.append("Near equilibrium")
    
    def _analyze_energy_flow(self):
        """Analyze overall energy flow in the network.
        
        CURRENT: Count ATP production/consumption
        FUTURE: Full pathway thermodynamic analysis with ΔG summation
        """
        atp_producers = []
        atp_consumers = []
        
        for transition in self.model.transitions:
            reactants = self._get_reactants(transition)
            products = self._get_products(transition)
            
            consumes_atp = any(self._matches_compound(r, {'ATP'}) for r in reactants)
            produces_atp = any(self._matches_compound(p, {'ATP'}) for p in products)
            
            if produces_atp:
                atp_producers.append(transition.id)
            if consumes_atp:
                atp_consumers.append(transition.id)
        
        # Check energy balance
        if atp_consumers and not atp_producers:
            self.issues.append(ThermodynamicIssue(
                transition_id='network',
                issue_type='energy_imbalance',
                severity='warning',
                description=f"Network consumes ATP ({len(atp_consumers)} reactions) but doesn't produce it",
                suggestion="Add ATP-generating reactions or mark as energy-consuming pathway"
            ))
        
        # Store energy flow info
        if atp_producers or atp_consumers:
            self.issues.append(ThermodynamicIssue(
                transition_id='network',
                issue_type='energy_flow',
                severity='info',
                description=f"Energy flow: {len(atp_producers)} ATP-producing, {len(atp_consumers)} ATP-consuming reactions"
            ))
    
    # Helper methods
    
    def _is_reversible(self, transition) -> bool:
        """Check if transition is configured as reversible.
        
        FUTURE: Also check if reverse transition exists in network
        """
        # Check if transition type suggests reversibility
        if hasattr(transition, 'transition_type'):
            if transition.transition_type == 'continuous':
                # Check if rate formula has subtraction (kf*A - kr*B)
                rate = getattr(transition, 'rate', None)
                if rate and isinstance(rate, str):
                    return '-' in rate
        
        # Check label for reversibility indicators
        label_lower = transition.label.lower()
        return '⇌' in transition.label or 'reversible' in label_lower
    
    def _should_be_reversible(self, transition) -> Optional[bool]:
        """Heuristic check if reaction should be reversible.
        
        Returns:
            True: Should be reversible (near equilibrium)
            False: Should be irreversible (highly favorable)
            None: Unknown
        
        FUTURE: Calculate from ΔG°' database
        """
        label_lower = transition.label.lower()
        
        # Highly favorable (should be irreversible)
        irreversible_keywords = [
            'kinase', 'synthase', 'carboxylase',
            'decarboxylase', 'hydrolysis',
            'atp → adp', 'gtp → gdp'
        ]
        
        # Near equilibrium (should be reversible)
        reversible_keywords = [
            'isomerase', 'mutase', 'epimerase',
            'dehydrogenase', 'transaminase'
        ]
        
        if any(kw in label_lower for kw in irreversible_keywords):
            return False
        
        if any(kw in label_lower for kw in reversible_keywords):
            return True
        
        return None
    
    def _is_biosynthetic(self, transition) -> bool:
        """Check if this is a biosynthetic reaction.
        
        FUTURE: Use reaction database classification
        """
        label_lower = transition.label.lower()
        biosynthetic_keywords = [
            'synthase', 'synthetase', 'ligase',
            'polymerase', 'synthesis', 'anabolism',
            'condensation', 'formation'
        ]
        return any(keyword in label_lower for keyword in biosynthetic_keywords)
    
    def _get_reactants(self, transition) -> List[str]:
        """Get reactant place IDs."""
        reactants = []
        for arc in self.model.arcs:
            if arc.target_id == transition.id:
                # Find place by ID
                place = next((p for p in self.model.places if p.id == arc.source_id), None)
                if place:
                    reactants.append(place.label)
        return reactants
    
    def _get_products(self, transition) -> List[str]:
        """Get product place IDs."""
        products = []
        for arc in self.model.arcs:
            if arc.source_id == transition.id:
                # Find place by ID
                place = next((p for p in self.model.places if p.id == arc.target_id), None)
                if place:
                    products.append(place.label)
        return products
    
    def _matches_compound(self, label: str, compound_set: Set[str]) -> bool:
        """Check if label matches any compound in set (fuzzy matching)."""
        label_clean = label.replace('-', '').replace(' ', '').lower()
        for compound in compound_set:
            compound_clean = compound.replace('-', '').replace(' ', '').lower()
            if compound_clean in label_clean or label_clean in compound_clean:
                return True
        return False
    
    def _find_simple_cycles(self) -> List[List[str]]:
        """Find simple cycles in the network.
        
        FUTURE: Use more sophisticated cycle detection
        """
        # Simplified cycle detection (only immediate loops)
        cycles = []
        
        for place in self.model.places:
            # Find transitions that consume this place
            consumers = [arc.target_id for arc in self.model.arcs 
                        if arc.source_id == place.id]
            
            # Find transitions that produce this place
            producers = [arc.source_id for arc in self.model.arcs 
                        if arc.target_id == place.id]
            
            # Check for immediate cycles (T1 → P → T2 → P)
            for consumer in consumers:
                for producer in producers:
                    if consumer != producer:
                        cycles.append([place.id, consumer, producer])
        
        return cycles
    
    def _format_report(self) -> str:
        """Format analysis results as readable report."""
        lines = []
        lines.append("=" * 70)
        lines.append("THERMODYNAMIC FEASIBILITY ANALYSIS")
        lines.append("=" * 70)
        lines.append("")
        lines.append("⚠️  BASIC IMPLEMENTATION - Heuristic checks only")
        lines.append("🔮 FUTURE: Full ΔG°' calculations with compound database")
        lines.append("")
        
        # Group issues by severity
        errors = [i for i in self.issues if i.severity == 'error']
        warnings = [i for i in self.issues if i.severity == 'warning']
        info = [i for i in self.issues if i.severity == 'info']
        
        # Summary
        lines.append("SUMMARY")
        lines.append("-" * 70)
        lines.append(f"Total transitions analyzed: {len(self.model.transitions)}")
        lines.append(f"Issues found: {len(errors)} errors, {len(warnings)} warnings, {len(info)} info")
        lines.append("")
        
        # Errors
        if errors:
            lines.append("❌ ERRORS (Thermodynamic violations)")
            lines.append("-" * 70)
            for issue in errors:
                lines.append(f"  • {issue.description}")
                if issue.suggestion:
                    lines.append(f"    → {issue.suggestion}")
            lines.append("")
        
        # Warnings
        if warnings:
            lines.append("⚠️  WARNINGS (Potential issues)")
            lines.append("-" * 70)
            for issue in warnings:
                lines.append(f"  • {issue.description}")
                if issue.suggestion:
                    lines.append(f"    → {issue.suggestion}")
            lines.append("")
        
        # Info
        if info:
            lines.append("ℹ️  INFORMATION")
            lines.append("-" * 70)
            for issue in info:
                lines.append(f"  • {issue.description}")
                if issue.suggestion:
                    lines.append(f"    → {issue.suggestion}")
            lines.append("")
        
        # Reaction details
        if self.reaction_data:
            lines.append("REACTION THERMODYNAMICS")
            lines.append("-" * 70)
            for reaction in self.reaction_data.values():
                lines.append(f"Transition {reaction.transition_id}:")
                lines.append(f"  Reversible: {reaction.reversible}")
                lines.append(f"  Likely favorable: {reaction.likely_favorable}")
                lines.append(f"  Needs coupling: {reaction.needs_coupling}")
                lines.append(f"  Equilibrium likely: {reaction.equilibrium_likely}")
                if reaction.notes:
                    lines.append(f"  Notes: {', '.join(reaction.notes)}")
                lines.append("")
        
        # Future enhancements
        lines.append("=" * 70)
        lines.append("FUTURE ENHANCEMENTS (Requires Chemical Database)")
        lines.append("=" * 70)
        lines.append("• Calculate ΔG°' from ChEBI/MetaCyc compound databases")
        lines.append("• Compute concentration-dependent ΔG = ΔG°' + RT ln(Q)")
        lines.append("• pH and temperature corrections (Alberty-Legendre transform)")
        lines.append("• Pseudoisomer handling (protonation states)")
        lines.append("• Group contribution estimation for missing compounds")
        lines.append("• Pathway-level thermodynamic analysis")
        lines.append("• Validate reaction coupling (ATP-driven reactions)")
        lines.append("• Identify thermodynamic bottlenecks")
        lines.append("")
        lines.append("Dependencies:")
        lines.append("  - equilibrator-api (eQuilibrator thermodynamics)")
        lines.append("  - ChEBI compound database")
        lines.append("  - MetaCyc/BioCyc reaction database")
        lines.append("  - Component contribution method (Noor et al. 2013)")
        lines.append("")
        
        return "\n".join(lines)
