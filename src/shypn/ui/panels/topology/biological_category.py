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
            'dependency_coupling': DependencyAndCouplingAnalyzer,
            'regulatory_structure': RegulatoryStructureAnalyzer,
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
            analyzer_name: Name of analyzer (dependency_coupling, regulatory_structure)
            result: Analysis result data
        
        Returns:
            list: List of row tuples
        """
        rows = []
        
        if analyzer_name == 'dependency_coupling':
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
            
            # Process strongly independent pairs (optional - may create too many rows)
            # Uncomment if you want to see independent pairs
            # for t1_id, t2_id, details in classifications.get('strongly_independent', []):
            #     rows.append((
            #         'Independent',
            #         f'({t1_id}, {t2_id})',
            #         '-',
            #         0.0,
            #         'No Coupling',
            #         'No shared places'
            #     ))
        
        elif analyzer_name == 'regulatory_structure':
            # Result format: {'test_arcs': [...], 'catalyst_map': {...}, 'shared_catalysts': [...]}
            test_arcs = result.get('test_arcs', [])
            catalyst_map = result.get('catalyst_map', {})
            
            # Show each test arc (catalyst)
            for arc_info in test_arcs:
                catalyst_place_id = arc_info.get('catalyst_place_id', '')
                catalyst_place_name = arc_info.get('catalyst_place_name', str(catalyst_place_id))
                transition_id = arc_info.get('transition_id', '')
                transition_name = arc_info.get('transition_name', str(transition_id))
                
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
        
        return rows
