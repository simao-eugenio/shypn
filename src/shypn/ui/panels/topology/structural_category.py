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
    
    def __init__(self, model_canvas=None, expanded=False):
        """Initialize structural category.
        
        Args:
            model_canvas: ModelCanvas instance (optional)
            expanded: Whether category starts expanded
        """
        super().__init__(
            title="STRUCTURAL ANALYSIS",
            model_canvas=model_canvas,
            expanded=expanded
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
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        # 1. Analysis Summary section
        summary_section = self._build_summary_section()
        main_box.pack_start(summary_section, False, False, 0)
        
        # 2. Individual analyzer expanders
        analyzer_expanders = self._build_analyzer_expanders()
        main_box.pack_start(analyzer_expanders, True, True, 0)
        
        return main_box
