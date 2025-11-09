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
    
    def __init__(self, model_canvas=None, expanded=False, use_grouped_table=False):
        """Initialize behavioral category.
        
        Args:
            model_canvas: ModelCanvas instance (optional)
            expanded: Whether category starts expanded
            use_grouped_table: If True, use grouped table instead of expanders
        """
        # Additional widgets for 2-table layout
        self.properties_table_store = None
        self.properties_table_view = None
        self.deadlocks_table_store = None
        self.deadlocks_table_view = None
        self.deadlocks_section = None
        
        super().__init__(
            title="BEHAVIORAL ANALYSIS",
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
        if self.use_grouped_table:
            return self._build_behavioral_tables()
        
        # Default: individual expanders (old mode)
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        # 1. Analysis Summary section
        summary_section = self._build_summary_section()
        main_box.pack_start(summary_section, False, False, 0)
        
        # 2. Individual analyzer expanders
        analyzer_expanders = self._build_analyzer_expanders()
        main_box.pack_start(analyzer_expanders, True, True, 0)
        
        return main_box
    
    def _build_behavioral_tables(self):
        """Build 2-table layout for behavioral analysis.
        
        Table 1: Properties Matrix (single-row, 5 columns)
        Table 2: Deadlock States (multi-row, conditional)
        
        Returns:
            Gtk.Box: Container with both tables
        """
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        main_box.set_margin_start(12)
        main_box.set_margin_end(12)
        main_box.set_margin_top(12)
        main_box.set_margin_bottom(12)
        
        # Toolbar with Run All button
        toolbar = self._build_grouped_toolbar()
        main_box.pack_start(toolbar, False, False, 0)
        
        # Table 1: Properties Matrix
        properties_frame = Gtk.Frame()
        properties_frame.set_label("Behavioral Properties")
        properties_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        properties_box.set_margin_start(6)
        properties_box.set_margin_end(6)
        properties_box.set_margin_top(6)
        properties_box.set_margin_bottom(6)
        
        self.properties_table_view = self._create_properties_matrix()
        properties_box.pack_start(self.properties_table_view, False, False, 0)
        properties_frame.add(properties_box)
        main_box.pack_start(properties_frame, False, False, 0)
        
        # Table 2: Deadlock States (initially hidden)
        self.deadlocks_section = Gtk.Frame()
        self.deadlocks_section.set_label("Deadlock States")
        deadlocks_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        deadlocks_box.set_margin_start(6)
        deadlocks_box.set_margin_end(6)
        deadlocks_box.set_margin_top(6)
        deadlocks_box.set_margin_bottom(6)
        
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_min_content_height(150)
        scrolled.set_max_content_height(300)
        
        self.deadlocks_table_view = self._create_deadlocks_table()
        scrolled.add(self.deadlocks_table_view)
        deadlocks_box.pack_start(scrolled, True, True, 0)
        self.deadlocks_section.add(deadlocks_box)
        
        self.deadlocks_section.set_no_show_all(True)
        self.deadlocks_section.hide()
        main_box.pack_start(self.deadlocks_section, True, True, 0)
        
        return main_box
    
    def _create_properties_matrix(self):
        """Create single-row properties matrix table.
        
        Returns:
            Gtk.TreeView: Properties matrix
        """
        # 5 columns for the 5 properties
        self.properties_table_store = Gtk.ListStore(str, str, str, str, str)
        
        # Add initial placeholder row
        self.properties_table_store.append([
            'Not analyzed',
            'Not analyzed',
            'Not analyzed',
            'Not analyzed',
            'Not analyzed'
        ])
        
        treeview = Gtk.TreeView(model=self.properties_table_store)
        treeview.set_grid_lines(Gtk.TreeViewGridLines.BOTH)
        
        # Column names
        column_names = ['Reachability', 'Boundedness', 'Liveness', 'Deadlocks', 'Fairness']
        
        for i, col_name in enumerate(column_names):
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(col_name, renderer, text=i)
            column.set_resizable(True)
            column.set_min_width(120)
            treeview.append_column(column)
        
        return treeview
    
    def _create_deadlocks_table(self):
        """Create deadlock states table.
        
        Returns:
            Gtk.TreeView: Deadlocks table
        """
        # 4 columns: Has Deadlock, Deadlock Type, Disabled Transitions, Deadlock Places
        self.deadlocks_table_store = Gtk.ListStore(str, str, str, str)
        
        treeview = Gtk.TreeView(model=self.deadlocks_table_store)
        treeview.set_grid_lines(Gtk.TreeViewGridLines.BOTH)
        
        column_names = ['Has Deadlock', 'Deadlock Type', 'Disabled Transitions', 'Deadlock Places']
        
        for i, col_name in enumerate(column_names):
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(col_name, renderer, text=i)
            column.set_resizable(True)
            treeview.append_column(column)
        
        return treeview
    
    def _add_result_to_grouped_table(self, analyzer_name, result):
        """Override to handle behavioral 2-table layout.
        
        Args:
            analyzer_name: Name of analyzer
            result: Analysis result
        """
        # Handle AnalysisResult objects
        if hasattr(result, 'success'):
            if not result.success:
                return
            result_data = result.data if hasattr(result, 'data') else {}
        else:
            result_data = result
        
        # Get current drawing area to track all results
        drawing_area = self._get_current_drawing_area()
        if not drawing_area:
            return
        
        # Wait until all analyzers have run, then update properties matrix
        analyzed_set = self.analyzed.get(drawing_area, set())
        
        # Update properties matrix when each analyzer completes
        self._update_properties_matrix()
        
        # If deadlocks analyzer, populate deadlocks table
        if analyzer_name == 'deadlocks' and result_data:
            self._update_deadlocks_table(result_data)
    
    def _update_properties_matrix(self):
        """Update the properties matrix based on cached results."""
        drawing_area = self._get_current_drawing_area()
        if not drawing_area:
            return
        
        results = self.results_cache.get(drawing_area, {})
        
        # Build properties row
        reachability_text = self._format_reachability(results.get('reachability'))
        boundedness_text = self._format_boundedness(results.get('boundedness'))
        liveness_text = self._format_liveness(results.get('liveness'))
        deadlocks_text = self._format_deadlocks(results.get('deadlocks'))
        fairness_text = self._format_fairness(results.get('fairness'))
        
        # Update table (clear and add new row)
        self.properties_table_store.clear()
        self.properties_table_store.append([
            reachability_text,
            boundedness_text,
            liveness_text,
            deadlocks_text,
            fairness_text
        ])
    
    def _format_reachability(self, result):
        """Format reachability result for matrix cell."""
        if not result:
            return 'Not analyzed'
        
        data = result.data if hasattr(result, 'data') else result
        state_count = data.get('state_count', 0)
        
        if state_count > 0:
            return f'✓ Yes\n{state_count} states'
        return '✗ No'
    
    def _format_boundedness(self, result):
        """Format boundedness result for matrix cell."""
        if not result:
            return 'Not analyzed'
        
        data = result.data if hasattr(result, 'data') else result
        is_bounded = data.get('bounded', False)
        bound = data.get('k', 0)
        
        if is_bounded:
            return f'✓ Yes\nk={bound}'
        return '✗ Unbounded'
    
    def _format_liveness(self, result):
        """Format liveness result for matrix cell."""
        if not result:
            return 'Not analyzed'
        
        data = result.data if hasattr(result, 'data') else result
        is_live = data.get('live', False)
        percentage = data.get('percentage', 0)
        
        if is_live:
            return '✓ Yes\n100%'
        elif percentage > 0:
            return f'⚠ Quasi-Live\n{percentage}%'
        return '✗ No'
    
    def _format_deadlocks(self, result):
        """Format deadlocks result for matrix cell."""
        if not result:
            return 'Not analyzed'
        
        data = result.data if hasattr(result, 'data') else result
        deadlocks = data.get('deadlocks', [])
        
        if deadlocks:
            return f'✗ Yes\n{len(deadlocks)} found'
        return '✓ No'
    
    def _format_fairness(self, result):
        """Format fairness result for matrix cell."""
        if not result:
            return 'Not analyzed'
        
        data = result.data if hasattr(result, 'data') else result
        is_fair = data.get('fair', False)
        
        if is_fair:
            return '✓ Yes'
        return '✗ No'
    
    def _update_deadlocks_table(self, result_data):
        """Update deadlocks table with detected deadlocks.
        
        Args:
            result_data: Deadlocks analysis result
        """
        deadlocks = result_data.get('deadlocks', [])
        
        if not deadlocks:
            # No deadlocks - hide table
            self.deadlocks_section.hide()
            return
        
        # Clear and populate deadlocks table
        self.deadlocks_table_store.clear()
        
        for deadlock in deadlocks:
            deadlock_type = deadlock.get('type', 'Total Deadlock')
            disabled_transitions = deadlock.get('disabled_transitions', [])
            places = deadlock.get('places', {})
            
            # Format places as "p1 (0 tokens), p2 (0 tokens)"
            places_str = ', '.join([f'{p} ({t} tokens)' for p, t in places.items()])
            
            self.deadlocks_table_store.append([
                'Yes',
                deadlock_type,
                ', '.join(disabled_transitions),
                places_str
            ])
        
        # Show deadlocks section
        self.deadlocks_section.show_all()
