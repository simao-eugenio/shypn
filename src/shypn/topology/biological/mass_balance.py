"""Mass Balance Analyzer for Biological Petri Nets.

This analyzer validates atom conservation (C, H, O, N, P, S) across biochemical
reactions, ensuring that chemical reactions are stoichiometrically balanced at
the atomic level.

Key Concepts:
1. **Atom Conservation**: Total atoms in reactants = total atoms in products
2. **Chemical Formulas**: Parse molecular formulas (e.g., C6H12O6 for glucose)
3. **Reaction Balancing**: Check each transition for atom balance
4. **Mass Conservation**: Law of conservation of mass (atoms cannot be created/destroyed)

This is fundamental to validating biological models - unbalanced reactions
indicate modeling errors or missing cofactors.

Example:
    Glucose → 2 Pyruvate
    C6H12O6 → 2(C3H4O3)
    C: 6 = 6 ✓, H: 12 ≠ 8 ✗, O: 6 = 6 ✓
    → UNBALANCED (missing H, likely needs NAD+/NADH)

Theoretical Foundation:
- Doc: doc/foundation/BIOLOGICAL_PETRI_NET_FORMALIZATION.md
- Section 5.2: Analyzer Specifications - Mass Balance Analyzer

Author: GitHub Copilot
Date: November 20, 2025
"""

import re
from typing import Any, Dict, List, Set, Tuple, Optional
from collections import defaultdict

from shypn.topology.base.topology_analyzer import TopologyAnalyzer
from shypn.topology.base.analysis_result import AnalysisResult
from shypn.topology.base.exceptions import TopologyAnalysisError


class MassBalanceAnalyzer(TopologyAnalyzer):
    """Analyzer for atom conservation in biochemical reactions.
    
    Validates that each transition conserves atoms (C, H, O, N, P, S).
    Reports unbalanced reactions that violate conservation laws.
    
    Example:
        >>> analyzer = MassBalanceAnalyzer(model)
        >>> result = analyzer.analyze()
        >>> print(f"Balanced reactions: {result.data['statistics']['balanced']}")
        >>> print(f"Unbalanced reactions: {result.data['statistics']['unbalanced']}")
    """
    
    def __init__(self, model: Any):
        """Initialize mass balance analyzer.
        
        Args:
            model: Petri net model with places, transitions, and arcs
        """
        super().__init__(model)
        self.name = "Mass Balance"
        self.description = "Validates atom conservation (C, H, O, N, P, S) across reactions"
    
    def analyze(self, **kwargs) -> AnalysisResult:
        """Analyze mass balance for all transitions.
        
        Args:
            **kwargs: Optional parameters (unused, for compatibility)
        
        Returns:
            AnalysisResult: Contains balanced/unbalanced/incomplete transitions, atom counts
        """
        try:
            # Parse chemical formulas for all places
            place_formulas = self._parse_place_formulas()
            
            # Check each transition for mass balance
            balanced_transitions = []
            unbalanced_transitions = []
            incomplete_transitions = []
            
            for transition in self.model.transitions:
                balance_check = self._check_transition_balance(
                    transition, place_formulas
                )
                
                if balance_check['incomplete']:
                    incomplete_transitions.append(balance_check)
                elif balance_check['balanced']:
                    balanced_transitions.append(balance_check)
                else:
                    unbalanced_transitions.append(balance_check)
            
            # Compile statistics
            statistics = {
                'total_transitions': len(self.model.transitions),
                'balanced': len(balanced_transitions),
                'unbalanced': len(unbalanced_transitions),
                'incomplete': len(incomplete_transitions),
                'balance_rate': len(balanced_transitions) / len(self.model.transitions) if self.model.transitions else 0,
                'places_with_formulas': len(place_formulas),
                'places_without_formulas': len(self.model.places) - len(place_formulas),
            }
            
            # Create result
            result = AnalysisResult(
                success=True,
                data={
                    'balanced_transitions': balanced_transitions,
                    'unbalanced_transitions': unbalanced_transitions,
                    'incomplete_transitions': incomplete_transitions,
                    'place_formulas': place_formulas,
                    'statistics': statistics,
                },
                summary=self._format_summary(statistics)
            )
            
            return result
            
        except Exception as e:
            raise TopologyAnalysisError(
                f"Mass balance analysis failed: {str(e)}"
            )
    
    def _parse_place_formulas(self) -> Dict[str, Dict[str, int]]:
        """Parse chemical formulas from place names or metadata.
        
        Tries multiple strategies:
        1. Metadata field 'formula' or 'chemical_formula'
        2. Parse from name (e.g., 'Glucose_C6H12O6')
        3. Common biochemical abbreviations (ATP, NADH, etc.)
        
        Returns:
            dict: {place_id: {element: count}} e.g., {'P1': {'C': 6, 'H': 12, 'O': 6}}
        """
        formulas = {}
        
        for place in self.model.places:
            formula = None
            
            # Strategy 1: Check metadata
            if hasattr(place, 'metadata') and place.metadata:
                formula = place.metadata.get('formula') or place.metadata.get('chemical_formula')
            
            # Strategy 2: Parse from name
            if not formula and hasattr(place, 'name'):
                formula = self._extract_formula_from_name(place.name)
            
            # Strategy 3: Common abbreviations
            if not formula and hasattr(place, 'name'):
                formula = self._get_common_formula(place.name)
            
            if formula:
                parsed = self._parse_chemical_formula(formula)
                if parsed:
                    formulas[place.id] = parsed
        
        return formulas
    
    def _extract_formula_from_name(self, name: str) -> Optional[str]:
        """Extract chemical formula from place name.
        
        Examples:
            'Glucose_C6H12O6' → 'C6H12O6'
            'ATP (C10H16N5O13P3)' → 'C10H16N5O13P3'
            'G6P' → None (no formula in name)
            'C00293' → None (KEGG ID, not a formula)
            'C000469' → None (KEGG ID variation)
        
        Args:
            name: Place name
            
        Returns:
            str or None: Chemical formula if found
        """
        # CRITICAL: Filter out KEGG compound IDs (C00001-C99999 and variations)
        # Pattern: C followed by 3-6 digits (with or without leading zeros)
        if re.match(r'^C0*\d{1,6}$', name):
            return None
        
        # Pattern: letters followed by numbers (chemical formula)
        # Look for patterns like C6H12O6, C10H16N5O13P3
        match = re.search(r'[_\s(]([A-Z][a-z]?\d+(?:[A-Z][a-z]?\d+)*)[_\s)]', name)
        if match:
            candidate = match.group(1)
            # Double-check it's not a KEGG ID
            if not re.match(r'^C0*\d{1,6}$', candidate):
                return candidate
        
        # Also check if entire name is a formula
        if re.match(r'^[A-Z][a-z]?\d+(?:[A-Z][a-z]?\d+)*$', name):
            # Must have at least 2 different elements to be a valid formula
            # E.g., C6H12O6 is valid, but C293 (single element) is likely garbage
            elements = re.findall(r'[A-Z][a-z]?', name)
            if len(set(elements)) >= 2:  # At least 2 different elements
                return name
        
        return None
    
    def _get_common_formula(self, name: str) -> Optional[str]:
        """Get formula for common biochemical abbreviations.
        
        Args:
            name: Place name (e.g., 'ATP', 'NADH', 'Glucose')
            
        Returns:
            str or None: Chemical formula
        """
        # Common metabolites
        common_formulas = {
            # Nucleotides
            'ATP': 'C10H16N5O13P3',
            'ADP': 'C10H15N5O10P2',
            'AMP': 'C10H14N5O7P',
            'GTP': 'C10H16N5O14P3',
            'GDP': 'C10H15N5O11P2',
            'CTP': 'C9H16N3O14P3',
            'UTP': 'C9H15N2O15P3',
            
            # Cofactors
            'NAD': 'C21H27N7O14P2',
            'NADH': 'C21H29N7O14P2',
            'NADP': 'C21H28N7O17P3',
            'NADPH': 'C21H30N7O17P3',
            'FAD': 'C27H33N9O15P2',
            'FADH2': 'C27H35N9O15P2',
            'CoA': 'C21H36N7O16P3S',
            
            # Sugars
            'Glucose': 'C6H12O6',
            'G6P': 'C6H13O9P',
            'F6P': 'C6H13O9P',
            'FBP': 'C6H14O12P2',
            'GAP': 'C3H7O6P',
            'DHAP': 'C3H7O6P',
            'Pyruvate': 'C3H4O3',
            'Lactate': 'C3H6O3',
            
            # TCA Cycle
            'AcetylCoA': 'C23H38N7O17P3S',
            'Citrate': 'C6H8O7',
            'Isocitrate': 'C6H8O7',
            'AlphaKetoglutarate': 'C5H6O5',
            'Succinate': 'C4H6O4',
            'Fumarate': 'C4H4O4',
            'Malate': 'C4H6O5',
            'Oxaloacetate': 'C4H4O5',
            
            # Other
            'Pi': 'HO4P',  # Inorganic phosphate
            'PPi': 'H4O7P2',  # Pyrophosphate
            'H2O': 'H2O',
            'CO2': 'CO2',
            'O2': 'O2',
            'NH3': 'NH3',
        }
        
        # Try exact match (case-insensitive)
        name_upper = name.upper()
        for abbrev, formula in common_formulas.items():
            if name_upper == abbrev.upper() or name_upper.replace('_', '').replace('-', '') == abbrev.upper():
                return formula
        
        # Try partial match
        for abbrev, formula in common_formulas.items():
            if abbrev.upper() in name_upper:
                return formula
        
        return None
    
    def _parse_chemical_formula(self, formula: str) -> Optional[Dict[str, int]]:
        """Parse chemical formula into element counts.
        
        Examples:
            'C6H12O6' → {'C': 6, 'H': 12, 'O': 6}
            'C10H16N5O13P3' → {'C': 10, 'H': 16, 'N': 5, 'O': 13, 'P': 3}
        
        Args:
            formula: Chemical formula string
            
        Returns:
            dict: {element: count} or None if parse fails
        """
        try:
            atoms: Dict[str, int] = {}
            
            # Pattern: Element (capital + optional lowercase) followed by optional number
            # Examples: C6, H12, O, Na2, Cl
            pattern = r'([A-Z][a-z]?)(\d*)'
            
            for match in re.finditer(pattern, formula):
                element = match.group(1)
                count_str = match.group(2)
                count = int(count_str) if count_str else 1
                
                if element:  # Valid element symbol
                    atoms[element] = atoms.get(element, 0) + count
            
            return atoms if atoms else None
            
        except Exception:
            return None
    
    def _check_transition_balance(
        self, 
        transition: Any, 
        place_formulas: Dict[str, Dict[str, int]]
    ) -> Dict[str, Any]:
        """Check if transition conserves atoms.
        
        Args:
            transition: Transition to check
            place_formulas: Dict of place formulas
            
        Returns:
            dict: Balance check result with 'balanced', 'incomplete', or 'unbalanced' status
        """
        # Get input and output places
        input_atoms: Dict[str, float] = defaultdict(float)
        output_atoms: Dict[str, float] = defaultdict(float)
        
        input_places = []
        output_places = []
        input_places_with_formula = 0
        output_places_with_formula = 0
        total_input_places = 0
        total_output_places = 0
        
        # Count atoms from inputs
        for arc in self.model.arcs:
            if arc.target == transition:
                total_input_places += 1
                if arc.source.id in place_formulas:
                    # This is an input arc WITH formula
                    input_places_with_formula += 1
                    weight = getattr(arc, 'weight', 1.0)
                    formula = place_formulas[arc.source.id]
                    
                    for element, count in formula.items():
                        input_atoms[element] += count * weight
                    
                    input_places.append({
                        'id': arc.source.id,
                        'name': getattr(arc.source, 'name', arc.source.id),
                        'formula': formula,
                        'weight': weight
                    })
        
        # Count atoms from outputs
        for arc in self.model.arcs:
            if arc.source == transition:
                total_output_places += 1
                if arc.target.id in place_formulas:
                    # This is an output arc WITH formula
                    output_places_with_formula += 1
                    weight = getattr(arc, 'weight', 1.0)
                    formula = place_formulas[arc.target.id]
                    
                    for element, count in formula.items():
                        output_atoms[element] += count * weight
                    
                    output_places.append({
                        'id': arc.target.id,
                        'name': getattr(arc.target, 'name', arc.target.id),
                        'formula': formula,
                        'weight': weight
                    })
        
        # Check if we have complete information
        has_complete_info = (
            input_places_with_formula == total_input_places and
            output_places_with_formula == total_output_places and
            total_input_places > 0 and
            total_output_places > 0
        )
        
        # Check balance for each element
        all_elements = set(input_atoms.keys()) | set(output_atoms.keys())
        imbalances = {}
        balanced = True
        
        for element in all_elements:
            input_count = input_atoms.get(element, 0)
            output_count = output_atoms.get(element, 0)
            
            # Allow small floating point errors (0.001 tolerance)
            if abs(input_count - output_count) > 0.001:
                balanced = False
                imbalances[element] = {
                    'input': input_count,
                    'output': output_count,
                    'difference': output_count - input_count
                }
        
        return {
            'transition_id': transition.id,
            'transition_name': getattr(transition, 'name', transition.id),
            'balanced': balanced and has_complete_info,
            'incomplete': not has_complete_info,
            'input_places': input_places,
            'output_places': output_places,
            'input_atoms': dict(input_atoms),
            'output_atoms': dict(output_atoms),
            'imbalances': imbalances if has_complete_info else {},
            'total_input_places': total_input_places,
            'input_places_with_formula': input_places_with_formula,
            'total_output_places': total_output_places,
            'output_places_with_formula': output_places_with_formula,
        }
    
    def _format_summary(self, statistics: Dict[str, Any]) -> str:
        """Format summary message.
        
        Args:
            statistics: Statistics dict
            
        Returns:
            str: Formatted summary
        """
        total = statistics['total_transitions']
        balanced = statistics['balanced']
        unbalanced = statistics['unbalanced']
        incomplete = statistics.get('incomplete', 0)
        rate = statistics['balance_rate'] * 100
        
        lines = [
            f"Mass Balance Analysis Summary:",
            f"  Total transitions: {total}",
            f"  Balanced: {balanced} ({rate:.1f}%)",
            f"  Unbalanced: {unbalanced}",
            f"  Incomplete data: {incomplete}",
            f"  Places with formulas: {statistics['places_with_formulas']}",
            f"  Places without formulas: {statistics['places_without_formulas']}",
        ]
        
        if unbalanced > 0:
            lines.append(f"\n❌ {unbalanced} reaction(s) violate atom conservation!")
        elif incomplete > 0:
            lines.append(f"\n⚠️ {incomplete} reaction(s) cannot be verified (missing formulas)")
        else:
            lines.append(f"\n✓ All reactions are balanced")
        
        return "\n".join(lines)
    
    def format_result(self, result: AnalysisResult) -> str:
        """Format analysis result as human-readable text.
        
        Args:
            result: Analysis result
            
        Returns:
            str: Formatted text
        """
        if not result.success:
            return f"Mass Balance Analysis Failed: {result.message}"  # type: ignore[attr-defined]
        
        lines = ["=" * 60]
        lines.append("MASS BALANCE ANALYSIS")
        lines.append("=" * 60)
        lines.append("")
        
        # Statistics
        stats = result.data['statistics']
        lines.append("STATISTICS:")
        lines.append(f"  Total Transitions: {stats['total_transitions']}")
        lines.append(f"  Balanced: {stats['balanced']} ({stats['balance_rate']*100:.1f}%)")
        lines.append(f"  Unbalanced: {stats['unbalanced']}")
        lines.append(f"  Places with formulas: {stats['places_with_formulas']}")
        lines.append(f"  Places without formulas: {stats['places_without_formulas']}")
        lines.append("")
        
        # Unbalanced transitions (detailed)
        if result.data['unbalanced_transitions']:
            lines.append("UNBALANCED REACTIONS:")
            lines.append("-" * 60)
            
            for check in result.data['unbalanced_transitions']:
                lines.append(f"\n❌ {check['transition_id']}: {check['transition_name']}")
                
                # Show reactants
                if check['input_places']:
                    lines.append("  Reactants:")
                    for p in check['input_places']:
                        formula_str = ''.join(f"{e}{c}" for e, c in p['formula'].items())
                        lines.append(f"    {p['weight']} × {p['name']} ({formula_str})")
                
                # Show products
                if check['output_places']:
                    lines.append("  Products:")
                    for p in check['output_places']:
                        formula_str = ''.join(f"{e}{c}" for e, c in p['formula'].items())
                        lines.append(f"    {p['weight']} × {p['name']} ({formula_str})")
                
                # Show imbalances
                lines.append("  Imbalances:")
                for element, data in check['imbalances'].items():
                    diff = data['difference']
                    sign = '+' if diff > 0 else ''
                    lines.append(
                        f"    {element}: {data['input']} → {data['output']} "
                        f"(Δ = {sign}{diff:.2f})"
                    )
            
            lines.append("")
        
        # Balanced transitions (summary)
        if result.data['balanced_transitions']:
            lines.append(f"BALANCED REACTIONS: ({len(result.data['balanced_transitions'])})")
            lines.append("-" * 60)
            for check in result.data['balanced_transitions']:
                lines.append(f"✓ {check['transition_id']}: {check['transition_name']}")
            lines.append("")
        
        lines.append("=" * 60)
        
        return "\n".join(lines)
