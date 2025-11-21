#!/usr/bin/env python3
"""Biological Topology Analysis Category.

Manages biological property analyzers for Biological Petri Nets:
1. Dependency & Coupling - Classifies transition dependencies:
   - Strongly Independent (no shared places)
   - Competitive (shared inputs → conflict)
   - Convergent (shared outputs → valid coupling)
   - Regulatory (shared catalysts → valid coupling)
2. Regulatory Structure - Detects test arcs (catalysts) and implicit regulation

This category validates the refined locality theory: most "dependencies" in
biological models are actually VALID COUPLINGS (convergent production or
shared enzymes), not true conflicts.

Author: GitHub Copilot
Date: October 31, 2025
"""
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from shypn.ui.panels.topology.base_topology_category import BaseTopologyCategory
from shypn.topology.biological.dependency_coupling import DependencyAndCouplingAnalyzer
from shypn.topology.biological.regulatory_structure import RegulatoryStructureAnalyzer
from shypn.topology.biological.mass_balance import MassBalanceAnalyzer
from shypn.topology.biological.stoichiometry import StoichiometryAnalyzer
from shypn.topology.biological.flux_balance import FluxBalanceAnalyzer
from shypn.topology.biological.thermodynamics import ThermodynamicAnalyzer
from shypn.topology.biological.thermodynamics import ThermodynamicAnalyzer


class BiologicalCategory(BaseTopologyCategory):
    """Biological analysis category for Topology Panel.
    
    Contains:
    - Analysis Summary section
    - Dependency & Coupling analyzer (validates refined locality theory)
    - Regulatory Structure analyzer (detects catalysts and implicit regulation)
    
    This category is particularly relevant for:
    - SBML imported models (biological pathways)
    - Models with test arcs (catalysts/enzymes)
    - Metabolic networks with convergent pathways
    """
    
    def __init__(self, model_canvas=None, expanded=False, use_grouped_table=False):
        """Initialize biological category.
        
        Args:
            model_canvas: ModelCanvas instance (optional)
            expanded: Whether category starts expanded
            use_grouped_table: If True, use grouped table instead of expanders
        """
        super().__init__(
            title="BIOLOGICAL ANALYSIS",
            model_canvas=model_canvas,
            expanded=expanded,
            use_grouped_table=use_grouped_table
        )
    
    def _get_analyzers(self):
        """Get dict of analyzer name -> AnalyzerClass.
        
        Returns:
            dict: {analyzer_name: AnalyzerClass}
        """
        return {
            'mass_balance': MassBalanceAnalyzer,
            'stoichiometry': StoichiometryAnalyzer,
            'flux_balance': FluxBalanceAnalyzer,
            'dependency_coupling': DependencyAndCouplingAnalyzer,
            'regulatory_structure': RegulatoryStructureAnalyzer,
            'thermodynamics': ThermodynamicAnalyzer,
        }
    
    def _build_content(self):
        """Build and return the content widget.
        
        Returns:
            Gtk.Box: The content to display in this category
        """
        if self.use_grouped_table:
            return self._build_grouped_table()
        
        # Default: individual expanders (old mode)
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        # 1. Analysis Summary section
        summary_section = self._build_summary_section()
        main_box.pack_start(summary_section, False, False, 0)
        
        # 2. Individual analyzer expanders
        analyzer_expanders = self._build_analyzer_expanders()
        main_box.pack_start(analyzer_expanders, True, True, 0)
        
        return main_box
    
    def _define_table_columns(self):
        """Define columns for biological dependencies grouped table.
        
        Returns:
            list: List of (column_name, column_type) tuples
        """
        return [
            ('Type', str),                # Competitive, Convergent, Regulatory, Independent, Catalyst
            ('Transition Pair', str),     # (t1, t2) or single transition
            ('Shared Elements', str),     # Places that cause relationship
            ('Conflict Score', float),    # 0.0-1.0
            ('Classification', str),      # True Conflict, Valid Coupling, etc.
            ('Notes', str),               # Biological interpretation
        ]
    
    def _format_analyzer_row(self, analyzer_name, result):
        """Format biological analyzer result as table rows.
        
        Args:
            analyzer_name: Name of analyzer
            result: Analysis result data
        
        Returns:
            list: List of row tuples
        """
        rows = []
        
        if analyzer_name == 'mass_balance':
            # Result format: {'balanced_transitions': [...], 'unbalanced_transitions': [...], 'statistics': {...}}
            statistics = result.get('statistics', {})
            unbalanced = result.get('unbalanced_transitions', [])
            
            if unbalanced:
                for trans_info in unbalanced:
                    trans_name = trans_info.get('transition_name', trans_info.get('transition_id', 'Unknown'))
                    imbalances = trans_info.get('imbalances', {})
                    
                    # imbalances format: {element: {'input': X, 'output': Y, 'difference': Z}}
                    imbalance_str = ', '.join([f"{elem}: {data.get('difference', 0):+.2f}" 
                                               for elem, data in imbalances.items() 
                                               if isinstance(data, dict)])
                    
                    rows.append((
                        'Imbalanced',
                        trans_name,
                        imbalance_str,
                        1.0,  # High severity
                        '❌ Mass Error',
                        'Atoms not conserved'
                    ))
            else:
                # All balanced - show summary
                num_balanced = statistics.get('num_balanced', 0)
                if num_balanced > 0:
                    rows.append((
                        'Mass Balance',
                        'All Transitions',
                        f'{num_balanced} reaction(s)',
                        0.0,
                        '✓ Balanced',
                        'All atoms conserved'
                    ))
        
        elif analyzer_name == 'stoichiometry':
            # Result format: {'stoichiometric_matrix': [...], 'conservation_laws': [...], 'blocked_transitions': [...]}
            statistics = result.get('statistics', {})
            blocked = result.get('blocked_transitions', [])
            conservation_laws = result.get('conservation_laws', [])
            
            if blocked:
                for trans_id in blocked:
                    rows.append((
                        'Blocked',
                        trans_id,
                        'No substrates or products',
                        1.0,
                        '❌ Blocked',
                        'Cannot fire'
                    ))
            
            if conservation_laws:
                for law in conservation_laws[:5]:  # Show first 5
                    place_str = ', '.join([f"{pid}×{coef:.2f}" for pid, coef in law.items() if coef != 0])
                    rows.append((
                        'Conservation Law',
                        'Invariant',
                        place_str,
                        0.0,
                        '✓ Conserved',
                        'Token/mass invariant'
                    ))
            
            if not blocked and conservation_laws:
                rows.append((
                    'Stoichiometry',
                    'Summary',
                    f'{len(conservation_laws)} conservation law(s)',
                    0.0,
                    '✓ Consistent',
                    'Matrix rank OK'
                ))
        
        elif analyzer_name == 'flux_balance':
            # Result format: {'feasible_transitions': [...], 'infeasible_transitions': [...], 'statistics': {...}}
            statistics = result.get('statistics', {})
            infeasible = result.get('infeasible_transitions', [])
            feasible = result.get('feasible_transitions', [])
            
            if infeasible:
                for trans_info in infeasible:
                    trans_name = trans_info.get('transition_name', trans_info.get('transition_id', 'Unknown'))
                    reason = trans_info.get('reason', 'Unknown')
                    
                    rows.append((
                        'Infeasible',
                        trans_name,
                        reason,
                        1.0,
                        '❌ No Flux',
                        'Cannot maintain steady state'
                    ))
            elif feasible:
                rows.append((
                    'Flux Balance',
                    'All Transitions',
                    f'{len(feasible)} reaction(s)',
                    0.0,
                    '✓ Feasible',
                    'Steady state possible'
                ))
        
        elif analyzer_name == 'thermodynamics':
            # Result format: {'issues': [...], 'statistics': {...}}
            issues = result.get('issues', [])
            statistics = result.get('statistics', {})
            
            if issues:
                for issue in issues[:10]:  # Show first 10
                    trans_name = issue.get('transition_id', 'Unknown')
                    severity = issue.get('severity', 'warning')
                    description = issue.get('description', '')
                    issue_type = issue.get('type', 'unknown')
                    
                    severity_icon = '❌' if severity == 'error' else '⚠️'
                    
                    rows.append((
                        f'{severity_icon} {issue_type.replace("_", " ").title()}',
                        trans_name,
                        description[:60],
                        1.0 if severity == 'error' else 0.5,
                        severity.title(),
                        issue.get('suggestion', '')[:40]
                    ))
            else:
                total_transitions = statistics.get('total_transitions', 0)
                if total_transitions > 0:
                    rows.append((
                        'Thermodynamics',
                        'All Transitions',
                        f'{total_transitions} reaction(s)',
                        0.0,
                        '✓ Feasible',
                        'Thermodynamically valid'
                    ))
        
        elif analyzer_name == 'dependency_coupling':
            # Result format: {'classifications': {'competitive': [...], 'convergent': [...], ...}}
            classifications = result.get('classifications', {})
            
            # Process competitive pairs (conflicts)
            for t1_id, t2_id, details in classifications.get('competitive', []):
                shared_inputs = details.get('shared_inputs', [])
                shared_outputs = details.get('shared_outputs', [])
                shared_reg = details.get('shared_regulatory', [])
                
                all_shared = shared_inputs + shared_outputs + shared_reg
                
                rows.append((
                    'Competitive',
                    f'({t1_id}, {t2_id})',
                    ', '.join(map(str, all_shared)) if all_shared else '-',
                    1.0,  # High conflict score
                    'True Conflict',
                    'Mutually exclusive firing (input competition)'
                ))
            
            # Process convergent pairs (valid coupling)
            for t1_id, t2_id, details in classifications.get('convergent', []):
                shared_outputs = details.get('shared_outputs', [])
                
                rows.append((
                    'Convergent',
                    f'({t1_id}, {t2_id})',
                    ', '.join(map(str, shared_outputs)) if shared_outputs else '-',
                    0.0,  # No conflict
                    'Valid Coupling',
                    'Both produce same metabolite'
                ))
            
            # Process regulatory pairs (valid coupling)
            for t1_id, t2_id, details in classifications.get('regulatory', []):
                shared_reg = details.get('shared_regulatory', [])
                
                rows.append((
                    'Regulatory',
                    f'({t1_id}, {t2_id})',
                    ', '.join(map(str, shared_reg)) if shared_reg else '-',
                    0.0,  # No conflict
                    'Valid Coupling',
                    'Share enzyme, no conflict'
                ))
            
            # Process strongly independent pairs
            for t1_id, t2_id, details in classifications.get('strongly_independent', []):
                rows.append((
                    'Independent',
                    f'({t1_id}, {t2_id})',
                    '-',
                    0.0,
                    'No Coupling',
                    'No shared places (parallel or sequential)'
                ))
        
        elif analyzer_name == 'regulatory_structure':
            # Result format: {'test_arcs': [...], 'inhibitor_arcs': [...], 'catalyst_map': {...}, 'inhibitor_map': {...}}
            test_arcs = result.get('test_arcs', [])
            inhibitor_arcs = result.get('inhibitor_arcs', [])
            catalyst_map = result.get('catalyst_map', {})
            inhibitor_map = result.get('inhibitor_map', {})
            
            # Show each test arc (catalyst)
            for arc_info in test_arcs:
                # Test arc structure: source (catalyst place) -> target (transition)
                catalyst_place_id = arc_info.get('source_id', '')
                catalyst_place_name = arc_info.get('source_name', str(catalyst_place_id))
                transition_id = arc_info.get('target_id', '')
                transition_name = arc_info.get('target_name', str(transition_id))
                
                # Get how many transitions use this catalyst
                catalyst_usage = len(catalyst_map.get(catalyst_place_id, []))
                
                rows.append((
                    'Catalyst',
                    transition_name,
                    f'{catalyst_place_name} (test arc)',
                    0.0,
                    'Enzymatic',
                    f'Enzyme used by {catalyst_usage} transition(s)'
                ))
            
            # Show each inhibitor arc
            for arc_info in inhibitor_arcs:
                # Inhibitor arc structure: source (inhibitor place) -> target (transition)
                inhibitor_place_id = arc_info.get('source_id', '')
                inhibitor_place_name = arc_info.get('source_name', str(inhibitor_place_id))
                transition_id = arc_info.get('target_id', '')
                transition_name = arc_info.get('target_name', str(transition_id))
                
                # Get how many transitions this inhibitor affects
                inhibitor_usage = len(inhibitor_map.get(inhibitor_place_id, []))
                
                rows.append((
                    'Inhibitor',
                    transition_name,
                    f'{inhibitor_place_name} (inhibitor arc)',
                    0.0,
                    'Negative Feedback',
                    f'Inhibits {inhibitor_usage} transition(s)'
                ))
        
        return rows
    
    def _format_error_row(self, analyzer_name, error_message):
        """Format error message as table row matching biological table structure.
        
        Overrides base class to return 6 columns instead of 3.
        
        Args:
            analyzer_name: Name of analyzer
            error_message: Error message
            
        Returns:
            tuple: Row with 6 columns
        """
        title = self._format_analyzer_title(analyzer_name)
        message = f"❌ Error: {error_message[:100]}"
        return (
            'Error',           # Type
            title,             # Transition Pair (analyzer name)
            message,           # Shared Elements (error message)
            0.0,               # Conflict Score
            '⚠️ ERROR',        # Classification
            ''                 # Notes
        )
    
    def _format_timeout_row(self, analyzer_name, timeout_seconds, complexity):
        """Format timeout message as table row matching biological table structure.
        
        Overrides base class to return 6 columns instead of 3.
        
        Args:
            analyzer_name: Name of analyzer
            timeout_seconds: Timeout value
            complexity: Algorithm complexity
            
        Returns:
            tuple: Row with 6 columns
        """
        title = self._format_analyzer_title(analyzer_name)
        message = f"⏱️ Timeout ({timeout_seconds}s) - Model too complex for {complexity} algorithm"
        return (
            'Timeout',         # Type
            title,             # Transition Pair (analyzer name)
            message,           # Shared Elements (timeout message)
            0.0,               # Conflict Score
            '⚠️ TIMEOUT',      # Classification
            ''                 # Notes
        )

