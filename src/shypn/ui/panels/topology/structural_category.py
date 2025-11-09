#!/usr/bin/env python3
"""Structural Topology Analysis Category.

Manages structural property analyzers:
1. P-Invariants - Place invariants (conservation laws)
2. T-Invariants - Transition invariants (reproducible sequences)
3. Siphons - Places that once empty, stay empty
4. Traps - Places that once marked, stay marked

Author: Simão Eugénio
Date: 2025-10-29
"""
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from shypn.ui.panels.topology.base_topology_category import BaseTopologyCategory
from shypn.topology.structural.p_invariants import PInvariantAnalyzer
from shypn.topology.structural.t_invariants import TInvariantAnalyzer
from shypn.topology.structural.siphons import SiphonAnalyzer
from shypn.topology.structural.traps import TrapAnalyzer


class StructuralCategory(BaseTopologyCategory):
    """Structural analysis category for Topology Panel.
    
    Contains:
    - Analysis Summary section
    - P-Invariants analyzer
    - T-Invariants analyzer
    - Siphons analyzer
    - Traps analyzer
    """
    
    def __init__(self, model_canvas=None, expanded=False, use_grouped_table=False):
        """Initialize structural category.
        
        Args:
            model_canvas: ModelCanvas instance (optional)
            expanded: Whether category starts expanded
            use_grouped_table: If True, use grouped table instead of expanders
        """
        super().__init__(
            title="STRUCTURAL ANALYSIS",
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
            'p_invariants': PInvariantAnalyzer,
            't_invariants': TInvariantAnalyzer,
            'siphons': SiphonAnalyzer,
            'traps': TrapAnalyzer,
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
        """Define columns for structural properties grouped table.
        
        Returns:
            list: List of (column_name, column_type) tuples
        """
        return [
            ('Type', str),           # P-Invariant, T-Invariant, Siphon, Trap
            ('Name', str),           # P_Inv_1, T_Inv_1, etc.
            ('Size', int),           # Number of elements
            ('Elements', str),       # Comma-separated places/transitions
            ('Support', str),        # Support vector or "-"
            ('Properties', str),     # Minimal, Conservative, etc.
        ]
    
    def _format_analyzer_row(self, analyzer_name, result):
        """Format structural analyzer result as table rows.
        
        Args:
            analyzer_name: Name of analyzer (p_invariants, t_invariants, siphons, traps)
            result: Analysis result data
        
        Returns:
            list: List of row tuples
        """
        rows = []
        
        if analyzer_name == 'p_invariants':
            # Result format: {'p_invariants': [{places: [...], weights: [...], names: [...]}]}
            invariants = result.get('p_invariants', [])
            for i, inv in enumerate(invariants, 1):
                place_ids = inv.get('places', [])
                weights = inv.get('weights', [])
                names = inv.get('names', [])
                
                # Use names if available, otherwise IDs
                elements_str = ', '.join(names) if names else ', '.join(map(str, place_ids))
                
                # Format weights as support vector
                support_str = str(weights) if weights else '-'
                
                # Properties (minimal is implicit, check for conservation)
                conserved_value = inv.get('conserved_value', 0)
                properties = f'Conserved value: {conserved_value}'
                
                rows.append((
                    'P-Invariant',
                    f'P_Inv_{i}',
                    len(place_ids),
                    elements_str,
                    support_str,
                    properties
                ))
        
        elif analyzer_name == 't_invariants':
            # Result format: {'t_invariants': [{transition_ids: [...], transition_names: [...], weights: [...]}]}
            invariants = result.get('t_invariants', [])
            for i, inv in enumerate(invariants, 1):
                transition_ids = inv.get('transition_ids', [])
                transition_names = inv.get('transition_names', [])
                weights = inv.get('weights', [])
                inv_type = inv.get('type', 'cycle')
                
                # Use names if available, otherwise IDs
                elements_str = ', '.join(transition_names) if transition_names else ', '.join(map(str, transition_ids))
                
                # Format weights as support vector
                support_str = str(weights) if weights else '-'
                
                # Properties
                properties = f'Type: {inv_type}, Total firings: {sum(weights) if weights else 0}'
                
                rows.append((
                    'T-Invariant',
                    f'T_Inv_{i}',
                    len(transition_ids),
                    elements_str,
                    support_str,
                    properties
                ))
        
        elif analyzer_name == 'siphons':
            # Result format: {'siphons': [{place_ids: [...], place_names: [...], is_empty: bool, criticality: str}]}
            siphons = result.get('siphons', [])
            for i, siphon in enumerate(siphons, 1):
                place_ids = siphon.get('place_ids', [])
                place_names = siphon.get('place_names', [])
                is_empty = siphon.get('is_empty', False)
                criticality = siphon.get('criticality', 'unknown')
                
                # Use names if available, otherwise IDs
                elements_str = ', '.join(place_names) if place_names else ', '.join(map(str, place_ids))
                
                # Properties
                prop_list = ['Minimal']  # All returned siphons are minimal
                if is_empty:
                    prop_list.append('Empty')
                prop_list.append(f'Criticality: {criticality}')
                
                rows.append((
                    'Siphon',
                    f'Siphon_{i}',
                    len(place_ids),
                    elements_str,
                    '-',
                    ', '.join(prop_list)
                ))
        
        elif analyzer_name == 'traps':
            # Result format: {'traps': [{place_ids: [...], place_names: [...], is_marked: bool, criticality: str}]}
            traps = result.get('traps', [])
            for i, trap in enumerate(traps, 1):
                place_ids = trap.get('place_ids', [])
                place_names = trap.get('place_names', [])
                is_marked = trap.get('is_marked', False)
                criticality = trap.get('criticality', 'unknown')
                
                # Use names if available, otherwise IDs
                elements_str = ', '.join(place_names) if place_names else ', '.join(map(str, place_ids))
                
                # Properties
                prop_list = ['Minimal']  # All returned traps are minimal
                if is_marked:
                    prop_list.append('Marked')
                prop_list.append(f'Criticality: {criticality}')
                
                rows.append((
                    'Trap',
                    f'Trap_{i}',
                    len(place_ids),
                    elements_str,
                    '-',
                    ', '.join(prop_list)
                ))
        
        return rows
