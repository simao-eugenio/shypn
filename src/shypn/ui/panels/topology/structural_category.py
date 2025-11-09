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
            # Result format: {'invariants': [{places: [...], support: [...], properties: {...}}]}
            invariants = result.get('invariants', [])
            for i, inv in enumerate(invariants, 1):
                places = inv.get('places', [])
                support = inv.get('support', [])
                props = inv.get('properties', {})
                
                # Build properties string
                prop_list = []
                if props.get('minimal', False):
                    prop_list.append('Minimal')
                if props.get('conservative', False):
                    prop_list.append('Conservative')
                
                rows.append((
                    'P-Invariant',
                    f'P_Inv_{i}',
                    len(places),
                    ', '.join(places),
                    str(support),
                    ', '.join(prop_list) if prop_list else '-'
                ))
        
        elif analyzer_name == 't_invariants':
            # Result format: {'invariants': [{transitions: [...], support: [...], properties: {...}}]}
            invariants = result.get('invariants', [])
            for i, inv in enumerate(invariants, 1):
                transitions = inv.get('transitions', [])
                support = inv.get('support', [])
                props = inv.get('properties', {})
                
                prop_list = []
                if props.get('minimal', False):
                    prop_list.append('Minimal')
                if props.get('reproducible', False):
                    prop_list.append('Reproducible')
                
                rows.append((
                    'T-Invariant',
                    f'T_Inv_{i}',
                    len(transitions),
                    ', '.join(transitions),
                    str(support),
                    ', '.join(prop_list) if prop_list else '-'
                ))
        
        elif analyzer_name == 'siphons':
            # Result format: {'siphons': [{places: [...], properties: {...}}]}
            siphons = result.get('siphons', [])
            for i, siphon in enumerate(siphons, 1):
                places = siphon.get('places', [])
                props = siphon.get('properties', {})
                
                prop_list = []
                if props.get('minimal', False):
                    prop_list.append('Minimal')
                if props.get('is_trap', False):
                    prop_list.append('Also Trap')
                else:
                    prop_list.append('Not Trap')
                
                rows.append((
                    'Siphon',
                    f'Siphon_{i}',
                    len(places),
                    ', '.join(places),
                    '-',
                    ', '.join(prop_list) if prop_list else '-'
                ))
        
        elif analyzer_name == 'traps':
            # Result format: {'traps': [{places: [...], properties: {...}}]}
            traps = result.get('traps', [])
            for i, trap in enumerate(traps, 1):
                places = trap.get('places', [])
                props = trap.get('properties', {})
                
                prop_list = []
                if props.get('minimal', False):
                    prop_list.append('Minimal')
                if props.get('is_siphon', False):
                    prop_list.append('Also Siphon')
                else:
                    prop_list.append('Not Siphon')
                
                rows.append((
                    'Trap',
                    f'Trap_{i}',
                    len(places),
                    ', '.join(places),
                    '-',
                    ', '.join(prop_list) if prop_list else '-'
                ))
        
        return rows
