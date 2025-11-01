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
    
    def __init__(self, model_canvas=None, expanded=False):
        """Initialize biological category.
        
        Args:
            model_canvas: ModelCanvas instance (optional)
            expanded: Whether category starts expanded
        """
        super().__init__(
            title="BIOLOGICAL ANALYSIS",
            model_canvas=model_canvas,
            expanded=expanded
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
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        # 1. Analysis Summary section
        summary_section = self._build_summary_section()
        main_box.pack_start(summary_section, False, False, 0)
        
        # 2. Individual analyzer expanders
        analyzer_expanders = self._build_analyzer_expanders()
        main_box.pack_start(analyzer_expanders, True, True, 0)
        
        return main_box
