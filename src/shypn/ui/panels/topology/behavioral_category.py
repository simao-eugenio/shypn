#!/usr/bin/env python3
"""Behavioral Topology Analysis Category.

Manages behavioral property analyzers with prioritized execution:

PRIORITY ORDER (fast to slow):
1. Boundedness (Priority 1) - O(n) - Simple token counting (<0.5s)
2. Fairness (Priority 1) - O(n+e) - Conflict analysis (<0.5s)
3. Deadlocks (Priority 3) - O(2^n) - Siphon detection (5-30s)
4. Liveness (Priority 3) - O(k^n) - Depends on reachability (5-30s)
5. Reachability (Priority 3) - O(k^n) - State explosion (5-30s)

Fast analyzers (Boundedness, Fairness) run first to provide instant feedback,
while expensive analyzers (Reachability, Liveness, Deadlocks) run last.

Author: Simão Eugénio
Date: 2025-10-29
Updated: 2025-11-09 - Added algorithm prioritization
"""
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from collections import OrderedDict

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
        """Get dict of analyzer name -> AnalyzerClass in PRIORITY ORDER.
        
        Analyzers are returned in execution priority order (fast to slow):
        1. Boundedness (Priority 1) - O(n) - Instant results (<0.5s)
        2. Fairness (Priority 1) - O(n+e) - Fast conflict check (<0.5s)
        3. Deadlocks (Priority 3) - O(2^n) - Moderate, siphon-based (5-30s)
        4. Liveness (Priority 3) - O(k^n) - Slow, depends on reachability (5-30s)
        5. Reachability (Priority 3) - O(k^n) - Slowest, state explosion (5-30s)
        
        Using OrderedDict ensures execution follows this priority when iterating.
        
        Returns:
            OrderedDict: {analyzer_name: AnalyzerClass} in priority order
        """
        # Return in PRIORITY ORDER (fastest first)
        return OrderedDict([
            # FAST - Priority 1 (< 0.5s)
            ('boundedness', BoundednessAnalyzer),  # O(n) - token counting
            ('fairness', FairnessAnalyzer),         # O(n+e) - conflict analysis
            
            # MODERATE/SLOW - Priority 3 (5-30s)
            ('deadlocks', DeadlockAnalyzer),        # O(2^n) - siphon detection
            ('liveness', LivenessAnalyzer),         # O(k^n) - depends on reachability
            ('reachability', ReachabilityAnalyzer), # O(k^n) - state space exploration
        ])
    
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
        """Create single-row properties matrix table with columns in priority order.
        
        Columns are ordered by algorithm execution priority:
        1. Boundedness (fastest)
        2. Fairness (fast)
        3. Deadlocks (moderate)
        4. Liveness (slow)
        5. Reachability (slowest)
        
        This matches the execution order, so results populate left-to-right.
        
        Returns:
            Gtk.TreeView: Properties matrix
        """
        # 5 columns for the 5 properties (IN PRIORITY ORDER)
        self.properties_table_store = Gtk.ListStore(str, str, str, str, str)
        
        # Add initial placeholder row
        self.properties_table_store.append([
            'Not analyzed',  # Boundedness
            'Not analyzed',  # Fairness
            'Not analyzed',  # Deadlocks
            'Not analyzed',  # Liveness
            'Not analyzed'   # Reachability
        ])
        
        treeview = Gtk.TreeView(model=self.properties_table_store)
        treeview.set_grid_lines(Gtk.TreeViewGridLines.BOTH)
        
        # Column names (IN PRIORITY ORDER - matches execution sequence)
        column_names = [
            'Boundedness',   # ⚡ Priority 1 - Results appear first
            'Fairness',      # ⚡ Priority 1 - Results appear second
            'Deadlocks',     # ⚠️ Priority 3 - Results appear third
            'Liveness',      # ⚠️ Priority 3 - Results appear fourth
            'Reachability'   # ⚠️ Priority 3 - Results appear last
        ]
        
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
    
    def _on_analyzer_start(self, analyzer_name):
        """Called when an analyzer starts running.
        
        Updates the properties matrix to show "Analyzing..." for the active analyzer.
        
        Args:
            analyzer_name: Name of analyzer that started
        """
        # Update matrix to show "Analyzing..." status
        self._update_properties_matrix()
    
    def _show_timeout_message(self, analyzer_name, timeout_seconds):
        """Override to show timeout in properties matrix.
        
        Args:
            analyzer_name: Name of analyzer that timed out
            timeout_seconds: Timeout value that was exceeded
        """
        # Mark as analyzed (so we don't show "Not analyzed")
        drawing_area = self._get_current_drawing_area()
        if drawing_area:
            if drawing_area not in self.analyzed:
                self.analyzed[drawing_area] = set()
            self.analyzed[drawing_area].add(analyzer_name)
            
            # Cache timeout result
            if drawing_area not in self.results_cache:
                self.results_cache[drawing_area] = {}
            
            # Create timeout marker
            self.results_cache[drawing_area][analyzer_name] = {
                'timeout': True,
                'timeout_seconds': timeout_seconds
            }
        
        # Update properties matrix to show timeout
        self._update_properties_matrix()
    
    def _show_error_message(self, analyzer_name, error_message):
        """Override to show error in properties matrix.
        
        Args:
            analyzer_name: Name of analyzer that failed
            error_message: Error message
        """
        # Mark as analyzed (so we don't show "Not analyzed")
        drawing_area = self._get_current_drawing_area()
        if drawing_area:
            if drawing_area not in self.analyzed:
                self.analyzed[drawing_area] = set()
            self.analyzed[drawing_area].add(analyzer_name)
            
            # Cache error result
            if drawing_area not in self.results_cache:
                self.results_cache[drawing_area] = {}
            
            # Create error marker
            self.results_cache[drawing_area][analyzer_name] = {
                'error': True,
                'error_message': error_message
            }
        
        # Update properties matrix to show error
        self._update_properties_matrix()
    
    def _update_properties_matrix(self):
        """Update the properties matrix based on cached results.
        
        Columns are in PRIORITY ORDER (Boundedness, Fairness, Deadlocks, Liveness, Reachability)
        so results populate left-to-right as fast algorithms complete first.
        
        Shows "Analyzing..." for algorithms currently running, "Not analyzed" for pending.
        """
        drawing_area = self._get_current_drawing_area()
        if not drawing_area:
            return
        
        results = self.results_cache.get(drawing_area, {})
        
        # Check which analyzers are currently running (in priority order)
        analyzers_list = ['boundedness', 'fairness', 'deadlocks', 'liveness', 'reachability']
        
        texts = []
        for analyzer_name in analyzers_list:
            if analyzer_name in self.analyzing:
                # Currently running - show spinner text
                texts.append('⏳ Analyzing...')
            elif analyzer_name in results:
                # Completed - show formatted result
                format_method = getattr(self, f'_format_{analyzer_name}')
                texts.append(format_method(results[analyzer_name]))
            else:
                # Not started yet
                texts.append('Not analyzed')
        
        # Update table (clear and add new row)
        self.properties_table_store.clear()
        self.properties_table_store.append(texts)
    
    def _format_reachability(self, result):
        """Format reachability result for matrix cell."""
        if not result:
            return 'Not analyzed'
        
        # Check for timeout
        if isinstance(result, dict) and result.get('timeout'):
            timeout = result.get('timeout_seconds', '?')
            return f'⏱️ Timeout\n({timeout}s)'
        
        # Check for error
        if isinstance(result, dict) and result.get('error'):
            return '❌ Error\n(see logs)'
        
        data = result.data if hasattr(result, 'data') else result
        state_count = data.get('state_count', 0)
        
        if state_count > 0:
            return f'✓ Yes\n{state_count} states'
        return '✗ No'
    
    def _format_boundedness(self, result):
        """Format boundedness result for matrix cell."""
        if not result:
            return 'Not analyzed'
        
        # Check for timeout
        if isinstance(result, dict) and result.get('timeout'):
            timeout = result.get('timeout_seconds', '?')
            return f'⏱️ Timeout\n({timeout}s)'
        
        # Check for error
        if isinstance(result, dict) and result.get('error'):
            return '❌ Error\n(see logs)'
        
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
        
        # Check for timeout
        if isinstance(result, dict) and result.get('timeout'):
            timeout = result.get('timeout_seconds', '?')
            return f'⏱️ Timeout\n({timeout}s)'
        
        # Check for error
        if isinstance(result, dict) and result.get('error'):
            return '❌ Error\n(see logs)'
        
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
        
        # Check for timeout
        if isinstance(result, dict) and result.get('timeout'):
            timeout = result.get('timeout_seconds', '?')
            return f'⏱️ Timeout\n({timeout}s)'
        
        # Check for error
        if isinstance(result, dict) and result.get('error'):
            return '❌ Error\n(see logs)'
        
        data = result.data if hasattr(result, 'data') else result
        has_deadlock = data.get('has_deadlock', False)
        deadlock_type = data.get('deadlock_type', 'unknown')
        
        if has_deadlock:
            return f'✗ Yes\n{deadlock_type}'
        return '✓ No'
    
    def _format_fairness(self, result):
        """Format fairness result for matrix cell."""
        if not result:
            return 'Not analyzed'
        
        # Check for timeout
        if isinstance(result, dict) and result.get('timeout'):
            timeout = result.get('timeout_seconds', '?')
            return f'⏱️ Timeout\n({timeout}s)'
        
        # Check for error
        if isinstance(result, dict) and result.get('error'):
            return '❌ Error\n(see logs)'
        
        data = result.data if hasattr(result, 'data') else result
        is_fair = data.get('is_fair', False)
        fairness_level = data.get('fairness_level', 'unknown')
        
        if is_fair:
            return '✓ Yes'
        elif fairness_level != 'unknown':
            return f'⚠ {fairness_level}'
        return '✗ No'
    
    def _create_deadlocks_table(self):
        """Create deadlocks detail table.
        
        Returns:
            Gtk.TreeView: Deadlocks table
        """
        # 4 columns for deadlock details
        self.deadlocks_table_store = Gtk.ListStore(str, str, str, str)
    
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
