#!/usr/bin/env python3
"""Behavioral Topology Analysis Category.

Manages behavioral property analyzers with prioritized execution:

PRIORITY ORDER (fast to slow):
1. Boundedness (Priority 1) - O(n) - Simple token counting (<0.5s)
2. Fairness (Priority 1) - O(n+e) - Conflict analysis (<0.5s)
3. Throughput (Priority 2) - O(n*k) - Simulation-based (2-5s)
4. ResponseTime (Priority 2) - O(n*k) - Simulation-based (2-5s)
5. Coverability (Priority 3) - O(k^n) - Graph construction (5-30s)
6. Deadlocks (Priority 3) - O(2^n) - Siphon detection (5-30s)
7. Liveness (Priority 3) - O(k^n) - Depends on reachability (5-30s)
8. Reachability (Priority 3) - O(k^n) - State explosion (5-30s)

Fast analyzers run first to provide instant feedback,
while expensive analyzers run last.

Author: Simão Eugénio
Date: 2025-10-29
Updated: 2025-11-09 - Added algorithm prioritization
Updated: 2026-02-03 - Added coverability, throughput, response_time
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
from shypn.topology.behavioral.coverability import CoverabilityAnalyzer
from shypn.topology.behavioral.throughput import ThroughputAnalyzer
from shypn.topology.behavioral.response_time import ResponseTimeAnalyzer


class BehavioralCategory(BaseTopologyCategory):
    """Behavioral analysis category for Topology Panel.
    
    Contains:
    - Analysis Summary section
    - Boundedness analyzer
    - Fairness analyzer
    - Throughput analyzer
    - Response Time analyzer
    - Coverability analyzer
    - Deadlocks analyzer
    - Liveness analyzer
    - Reachability analyzer
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
            
            # MODERATE - Priority 2 (1-5s)
            ('throughput', ThroughputAnalyzer),     # O(n*k) - simulation-based
            ('response_time', ResponseTimeAnalyzer), # O(n*k) - simulation-based
            
            # SLOW - Priority 3 (5-30s)
            ('coverability', CoverabilityAnalyzer), # O(k^n) - graph construction
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
        """Create transposed properties matrix table with analyzers as rows.
        
        Shows each analyzer in its own row with detailed results across multiple columns.
        Rows are ordered by algorithm execution priority.
        
        Returns:
            Gtk.TreeView: Properties matrix
        """
        # Columns: Analyzer Name | Status | Result | Details | Time
        self.properties_table_store = Gtk.ListStore(str, str, str, str, str)
        
        # Add rows for each analyzer (IN PRIORITY ORDER)
        analyzers = [
            ('Boundedness', 'boundedness'),
            ('Fairness', 'fairness'),
            ('Throughput', 'throughput'),
            ('Response Time', 'response_time'),
            ('Coverability', 'coverability'),
            ('Deadlocks', 'deadlocks'),
            ('Liveness', 'liveness'),
            ('Reachability', 'reachability')
        ]
        
        for display_name, internal_name in analyzers:
            self.properties_table_store.append([
                display_name,      # Analyzer name
                'Not analyzed',    # Status
                '',                # Result
                '',                # Details
                ''                 # Time
            ])
        
        treeview = Gtk.TreeView(model=self.properties_table_store)
        treeview.set_grid_lines(Gtk.TreeViewGridLines.BOTH)
        
        # Column 0: Analyzer Name (bold)
        renderer = Gtk.CellRendererText()
        renderer.set_property('weight', 700)  # Bold
        column = Gtk.TreeViewColumn('Analyzer', renderer, text=0)
        column.set_resizable(True)
        column.set_min_width(120)
        treeview.append_column(column)
        
        # Column 1: Status (⏳, ✓, ✗, ⚠, ⏱️, ❌)
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn('Status', renderer, text=1)
        column.set_resizable(True)
        column.set_min_width(100)
        treeview.append_column(column)
        
        # Column 2: Result (main finding)
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn('Result', renderer, text=2)
        column.set_resizable(True)
        column.set_min_width(120)
        treeview.append_column(column)
        
        # Column 3: Details (additional info)
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn('Details', renderer, text=3)
        column.set_resizable(True)
        column.set_min_width(150)
        treeview.append_column(column)
        
        # Column 4: Time (computation time)
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn('Time', renderer, text=4)
        column.set_resizable(True)
        column.set_min_width(80)
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
                return False  # Stop GLib.idle_add from repeating
            result_data = result.data if hasattr(result, 'data') else {}
        else:
            result_data = result
        
        # Get current drawing area to track all results
        drawing_area = self._get_current_drawing_area()
        if not drawing_area:
            return False  # Stop GLib.idle_add from repeating
        
        # Wait until all analyzers have run, then update properties matrix
        analyzed_set = self.analyzed.get(drawing_area, set())
        
        # Update properties matrix when each analyzer completes
        self._update_properties_matrix()
        
        # If deadlocks analyzer, populate deadlocks table
        if analyzer_name == 'deadlocks' and result_data:
            self._update_deadlocks_table(result_data)
        
        # Return False to stop GLib.idle_add from repeating
        return False
    
    def _on_analyzer_start(self, analyzer_name):
        """Called when an analyzer starts running.
        
        Updates the properties matrix to show "Analyzing..." for the active analyzer.
        
        Args:
            analyzer_name: Name of analyzer that started
        """
        # Update matrix to show "Analyzing..." status
        self._update_properties_matrix()
        
        # Return False to stop GLib.idle_add from repeating
        return False
    
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
        
        # Return False to stop GLib.idle_add from repeating
        return False
    
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
        
        # Return False to stop GLib.idle_add from repeating
        return False
    
    def _update_properties_matrix(self):
        """Update the properties matrix based on cached results.
        
        Updates each analyzer's row with status, result, details, and computation time.
        Rows are in PRIORITY ORDER so results populate top-to-bottom as fast algorithms complete first.
        """
        drawing_area = self._get_current_drawing_area()
        if not drawing_area:
            return
        
        results = self.results_cache.get(drawing_area, {})
        
        # Analyzer order (matches row order in table)
        analyzers_list = [
            ('Boundedness', 'boundedness'),
            ('Fairness', 'fairness'),
            ('Throughput', 'throughput'),
            ('Response Time', 'response_time'),
            ('Coverability', 'coverability'),
            ('Deadlocks', 'deadlocks'),
            ('Liveness', 'liveness'),
            ('Reachability', 'reachability')
        ]
        
        # Update each row
        for row_idx, (display_name, analyzer_name) in enumerate(analyzers_list):
            if analyzer_name in self.analyzing:
                # Currently running
                status = '⏳ Analyzing'
                result_text = ''
                details = ''
                time_text = ''
            elif analyzer_name in results:
                # Completed - get formatted result
                result_obj = results[analyzer_name]
                status, result_text, details, time_text = self._format_analyzer_row(analyzer_name, result_obj)
            else:
                # Not started yet
                status = 'Not analyzed'
                result_text = ''
                details = ''
                time_text = ''
            
            # Update row
            iter = self.properties_table_store.get_iter(row_idx)
            self.properties_table_store.set(iter,
                0, display_name,
                1, status,
                2, result_text,
                3, details,
                4, time_text
            )
    
    def _format_analyzer_row(self, analyzer_name, result):
        """Format analyzer result into table row (status, result, details, time).
        
        Args:
            analyzer_name: Name of analyzer
            result: Analysis result object or dict
            
        Returns:
            Tuple of (status, result_text, details, time_text)
        """
        # Check for timeout
        if isinstance(result, dict) and result.get('timeout'):
            timeout = result.get('timeout_seconds', '?')
            return ('⏱️ Timeout', f'{timeout}s exceeded', '', '')
        
        # Check for error
        if isinstance(result, dict) and result.get('error'):
            error_msg = result.get('error_message', 'Unknown error')
            return ('❌ Error', error_msg[:50], '', '')
        
        # Check if analysis failed (AnalysisResult with success=False)
        if hasattr(result, 'success') and not result.success:
            errors = result.errors if hasattr(result, 'errors') else []
            error_text = errors[0] if errors else 'Analysis failed'
            return ('❌ Failed', error_text[:50], '', '')
        
        # Get result data and metadata
        data = result.data if hasattr(result, 'data') else result
        metadata = result.metadata if hasattr(result, 'metadata') else {}
        comp_time = metadata.get('computation_time', 0)
        time_text = f'{comp_time:.3f}s' if comp_time else ''
        
        # Call specific formatter
        if analyzer_name == 'reachability':
            return self._format_reachability_row(data, time_text)
        elif analyzer_name == 'boundedness':
            return self._format_boundedness_row(data, time_text)
        elif analyzer_name == 'liveness':
            return self._format_liveness_row(data, time_text)
        elif analyzer_name == 'deadlocks':
            return self._format_deadlocks_row(data, time_text)
        elif analyzer_name == 'fairness':
            return self._format_fairness_row(data, time_text)
        elif analyzer_name == 'throughput':
            return self._format_throughput_row(data, time_text)
        elif analyzer_name == 'response_time':
            return self._format_response_time_row(data, time_text)
        elif analyzer_name == 'coverability':
            return self._format_coverability_row(data, time_text)
        else:
            return ('✓ Complete', '', '', time_text)
    
    def _format_reachability_row(self, data, time_text):
        """Format reachability result as table row."""
        state_count = data.get('total_states', 0)
        trans_count = data.get('total_transitions', 0)
        max_depth = data.get('max_depth_reached', 0)
        exploration_complete = data.get('exploration_complete', False)
        
        if state_count > 0:
            if exploration_complete:
                status = '✓ Complete'
            else:
                status = '⚠ Partial'
            result = f'{state_count} states'
            details = f'{trans_count} transitions, depth {max_depth}'
        else:
            status = '⚠ Empty'
            result = 'No states found'
            details = f'Check model (got {state_count} states)'
        
        return (status, result, details, time_text)
    
    def _format_boundedness_row(self, data, time_text):
        """Format boundedness result as table row."""
        is_bounded = data.get('bounded', False)
        bound = data.get('k', 0)
        unbounded_places = data.get('unbounded_places', [])
        
        if is_bounded:
            status = '✓ Bounded'
            result = f'k = {bound}'
            details = f'All places ≤ {bound} tokens'
        else:
            status = '✗ Unbounded'
            result = f'{len(unbounded_places)} places'
            details = ', '.join(unbounded_places[:3])
            if len(unbounded_places) > 3:
                details += f', ... (+{len(unbounded_places) - 3} more)'
        
        return (status, result, details, time_text)
    
    def _format_liveness_row(self, data, time_text):
        """Format liveness result as table row."""
        is_live = data.get('live', False)
        percentage = data.get('percentage', 0)
        live_count = data.get('live_transitions', 0)
        total_count = data.get('total_transitions', 0)
        
        if is_live:
            status = '✓ Live'
            result = '100% transitions'
            details = f'{total_count}/{total_count} live'
        elif percentage > 0:
            status = '⚠ Quasi-Live'
            result = f'{percentage}% transitions'
            details = f'{live_count}/{total_count} live'
        else:
            status = '✗ Not Live'
            result = '0% transitions'
            details = 'No live transitions'
        
        return (status, result, details, time_text)
    
    def _format_deadlocks_row(self, data, time_text):
        """Format deadlocks result as table row."""
        has_deadlock = data.get('has_deadlock', False)
        deadlock_count = data.get('deadlock_count', 0)
        deadlock_type = data.get('deadlock_type', 'unknown')
        
        if has_deadlock:
            status = '✗ Found'
            result = f'{deadlock_count} deadlock(s)'
            details = f'Type: {deadlock_type}'
        else:
            status = '✓ None'
            result = 'No deadlocks'
            details = 'All states reachable'
        
        return (status, result, details, time_text)
    
    def _format_fairness_row(self, data, time_text):
        """Format fairness result as table row."""
        is_fair = data.get('is_fair', False)
        fairness_level = data.get('fairness_level', 'unknown')
        unfair_count = data.get('unfair_transitions', 0)
        
        if is_fair:
            status = '✓ Fair'
            result = 'All transitions'
            details = 'Bounded waiting times'
        elif fairness_level != 'unknown':
            status = f'⚠ {fairness_level}'
            result = f'{unfair_count} unfair'
            details = 'Some unbounded waiting'
        else:
            status = '✗ Unfair'
            result = 'Not analyzed'
            details = ''
        
        return (status, result, details, time_text)
    
    def _format_throughput_row(self, data, time_text):
        """Format throughput result as table row."""
        throughput = data.get('throughput', 0.0)
        bottlenecks = data.get('bottlenecks', [])
        steps = data.get('statistics', {}).get('total_steps', 0)
        firings = data.get('statistics', {}).get('total_firings', 0)
        
        if bottlenecks:
            status = '⚠ Bottlenecks'
            result = f'{throughput:.2f} fires/step'
            details = f'{len(bottlenecks)} bottleneck(s) detected'
        else:
            status = '✓ Good'
            result = f'{throughput:.2f} fires/step'
            details = f'{firings} firings in {steps} steps'
        
        return (status, result, details, time_text)
    
    def _format_response_time_row(self, data, time_text):
        """Format response time result as table row."""
        avg_times = data.get('inter_firing_times', {})
        steps = data.get('statistics', {}).get('total_steps', 0)
        
        if avg_times:
            # Calculate overall average
            overall_avg = sum(avg_times.values()) / len(avg_times) if avg_times else 0
            max_avg = max(avg_times.values()) if avg_times else 0
            
            if max_avg > 100:
                status = '⚠ Slow'
                result = f'avg: {overall_avg:.1f} steps'
                details = f'max: {max_avg:.1f} steps'
            else:
                status = '✓ Fast'
                result = f'avg: {overall_avg:.1f} steps'
                details = f'max: {max_avg:.1f} steps'
        else:
            status = '✓ Complete'
            result = f'{steps} steps'
            details = 'No inter-firing data'
        
        return (status, result, details, time_text)
    
    def _format_coverability_row(self, data, time_text):
        """Format coverability result as table row."""
        node_count = data.get('statistics', {}).get('total_nodes', 0)
        unbounded = data.get('unbounded_places', [])
        
        if unbounded:
            status = '⚠ Unbounded'
            result = f'{len(unbounded)} place(s)'
            details = ', '.join(unbounded[:3])
            if len(unbounded) > 3:
                details += f', ... (+{len(unbounded) - 3} more)'
        else:
            status = '✓ Bounded'
            result = f'{node_count} nodes'
            details = 'All places bounded'
        
        return (status, result, details, time_text)
    
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
