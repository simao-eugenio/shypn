#!/usr/bin/env python3
"""Behavioral Topology Analysis Category.

Manages behavioral property analyzers:
1. Reachability - What markings are reachable
2. Boundedness - Whether places have bounded tokens
3. Liveness - Whether transitions can always fire
4. Deadlocks - Detection of deadlock states
5. Fairness - Fair firing of transitions

Author: Simão Eugénio
Date: 2025-10-29
"""
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from shypn.ui.panels.topology.base_topology_category import BaseTopologyCategory
from shypn.topology.behavioral.reachability import ReachabilityAnalyzer
from shypn.topology.behavioral.boundedness import BoundednessAnalyzer
from shypn.topology.behavioral.liveness import LivenessAnalyzer
from shypn.topology.behavioral.deadlocks import DeadlockAnalyzer
from shypn.topology.behavioral.fairness import FairnessAnalyzer


class BehavioralCategory(BaseTopologyCategory):
    """Behavioral analysis category for Topology Panel.
    
    Contains:
    - Analysis Summary section
    - Reachability analyzer
    - Boundedness analyzer
    - Liveness analyzer
    - Deadlocks analyzer
    - Fairness analyzer
    """
    
    def __init__(self, model_canvas=None, expanded=False):
        """Initialize behavioral category.
        
        Args:
            model_canvas: ModelCanvas instance (optional)
            expanded: Whether category starts expanded
        """
        super().__init__(
            title="Behavioral Analysis",
            model_canvas=model_canvas,
            expanded=expanded
        )
    
    def _get_analyzers(self):
        """Get dict of analyzer name -> AnalyzerClass.
        
        Returns:
            dict: {analyzer_name: AnalyzerClass}
        """
        return {
            'reachability': ReachabilityAnalyzer,
            'boundedness': BoundednessAnalyzer,
            'liveness': LivenessAnalyzer,
            'deadlocks': DeadlockAnalyzer,
            'fairness': FairnessAnalyzer,
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
