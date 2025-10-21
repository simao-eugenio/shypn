"""Topology Panel Controller - Expander Design (NO BUTTONS).

Ultra-clean architecture:
- NO analyze buttons → Expanding = Auto-analyze
- NO highlight buttons → Use Switch Palette
- NO detail buttons → Full report in expander
- Just 12 expanders with automatic analysis

Author: Simão Eugénio  
Date: 2025-10-20
"""

import sys
import threading
from typing import Dict, Optional

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

# Import all 12 analyzers
from shypn.topology.structural.p_invariants import PInvariantAnalyzer
from shypn.topology.structural.t_invariants import TInvariantAnalyzer
from shypn.topology.structural.siphons import SiphonAnalyzer
from shypn.topology.structural.traps import TrapAnalyzer
from shypn.topology.graph.cycles import CycleAnalyzer
from shypn.topology.graph.paths import PathAnalyzer
from shypn.topology.network.hubs import HubAnalyzer
from shypn.topology.behavioral.reachability import ReachabilityAnalyzer
from shypn.topology.behavioral.boundedness import BoundednessAnalyzer
from shypn.topology.behavioral.liveness import LivenessAnalyzer
from shypn.topology.behavioral.deadlocks import DeadlockAnalyzer
from shypn.topology.behavioral.fairness import FairnessAnalyzer


class TopologyPanelController:
    """Controller for Topology Panel (Expander Design).
    
    Responsibilities:
    - Initialize all 12 analyzers
    - Handle expander expand/collapse events
    - Run analysis when expander is expanded (first time)
    - Cache results (re-expand shows cached results instantly)
    - Show spinner during analysis
    - Format and display reports
    
    NOT responsible for:
    - Highlighting (handled by Switch Palette)
    - UI loading (handled by loader)
    - Widget lifecycle (handled by base)
    """
    
    def __init__(
        self,
        model,
        expanders: Dict[str, Gtk.Expander],
        scrolled_windows: Dict[str, Gtk.ScrolledWindow],
        report_labels: Dict[str, Gtk.Label],
    ):
        """Initialize controller.
        
        Args:
            model: ShypnModel instance (can be None - will be fetched at analysis time)
            expanders: Dict mapping analyzer name → GtkExpander widget
            scrolled_windows: Dict mapping analyzer name → GtkScrolledWindow widget
            report_labels: Dict mapping analyzer name → GtkLabel widget (for reports)
        """
        self.model = model
        self.model_canvas_loader = None  # Set externally to access current model
        self.expanders = expanders
        self.scrolled_windows = scrolled_windows
        self.report_labels = report_labels
        
        # Cache for analysis results (PER-TAB: keyed by drawing_area)
        # Format: {drawing_area: {analyzer_name: result}}
        # This prevents showing wrong results when switching tabs
        self.results = {}
        
        # Track which analyzers are currently analyzing (PER-TAB)
        # Format: {drawing_area: set(analyzer_names)}
        self.analyzing = {}
        
        # Track initial state (pre-expanded expanders on first load)
        self.initial_state_handled = set()
        
        # Track last seen drawing_area to detect tab switches
        self._last_drawing_area = None
        
        # Initialize all 12 analyzers
        self._init_analyzers()
        
        # Handle initial pre-expanded state (P-Invariants)
        self._handle_initial_state()
    
    def _init_analyzers(self):
        """Initialize all 12 analyzer classes."""
        self.analyzers = {
            'p_invariants': PInvariantAnalyzer,
            't_invariants': TInvariantAnalyzer,
            'siphons': SiphonAnalyzer,
            'traps': TrapAnalyzer,
            'cycles': CycleAnalyzer,
            'paths': PathAnalyzer,
            'hubs': HubAnalyzer,
            'reachability': ReachabilityAnalyzer,
            'boundedness': BoundednessAnalyzer,
            'liveness': LivenessAnalyzer,
            'deadlocks': DeadlockAnalyzer,
            'fairness': FairnessAnalyzer,
        }
        
        # Map analyzers to their tabs for exclusive expansion
        self.tab_groups = {
            'structural': ['p_invariants', 't_invariants', 'siphons', 'traps'],
            'graph_network': ['cycles', 'paths', 'hubs'],
            'behavioral': ['reachability', 'boundedness', 'liveness', 'deadlocks', 'fairness'],
        }
    
    def _handle_initial_state(self):
        """Handle pre-expanded expanders (p_invariants is expanded by default in UI)."""
        for analyzer_name, expander in self.expanders.items():
            if expander.get_expanded():
                self.initial_state_handled.add(analyzer_name)
                # P-Invariants is pre-expanded but not yet analyzed
                label = self.report_labels.get(analyzer_name)
                if label:
                    label.set_markup(
                        "<b>Not yet analyzed.</b>\n\n"
                        "Collapse and expand again to run analysis."
                    )
    
    def _collapse_other_expanders(self, active_analyzer: str):
        """Collapse all other expanders in the same tab group (exclusive expansion).
        
        Also manages vexpand property: only the active analyzer's scrolled window
        gets vexpand=True to fill available space, all others get vexpand=False.
        
        Args:
            active_analyzer: Name of the analyzer being expanded
        """
        # Find which tab group this analyzer belongs to
        active_group = None
        for group_name, analyzers in self.tab_groups.items():
            if active_analyzer in analyzers:
                active_group = analyzers
                break
        
        if not active_group:
            return  # Unknown analyzer, skip
        
        # Collapse all other expanders in the same group
        for analyzer_name in active_group:
            expander = self.expanders.get(analyzer_name)
            scrolled = self.scrolled_windows.get(analyzer_name)
            
            if analyzer_name != active_analyzer:
                # Collapse and disable vexpand for inactive expanders
                if expander and expander.get_expanded():
                    # Temporarily block signal to avoid recursive toggling
                    expander.handler_block_by_func(self.on_expander_toggled)
                    expander.set_expanded(False)
                    expander.handler_unblock_by_func(self.on_expander_toggled)
                
                # Disable vexpand (don't fill space)
                if scrolled:
                    scrolled.set_vexpand(False)
            else:
                # Enable vexpand for active expander (fill ALL available space)
                if scrolled:
                    scrolled.set_vexpand(True)
                    # Force layout recalculation
                    parent = scrolled.get_parent()
                    while parent and not isinstance(parent, Gtk.ScrolledWindow):
                        parent.queue_resize()
                        parent = parent.get_parent()
    
    def on_expander_toggled(self, expander: Gtk.Expander, param, analyzer_name: str):
        """Handle expander expand/collapse.
        
        Args:
            expander: The GtkExpander widget
            param: GParamSpec (GTK parameter, not used)
            analyzer_name: Name of the analyzer (e.g., 'p_invariants')
        """
        is_expanded = expander.get_expanded()
        
        # User collapsed → Disable vexpand so other expanders move back to top
        if not is_expanded:
            scrolled = self.scrolled_windows.get(analyzer_name)
            if scrolled:
                scrolled.set_vexpand(False)
                # Force layout recalculation to move expanders back up
                parent = scrolled.get_parent()
                while parent and not isinstance(parent, Gtk.ScrolledWindow):
                    parent.queue_resize()
                    parent = parent.get_parent()
            return
        
        # User expanded → Collapse all other expanders in the same tab (exclusive behavior)
        self._collapse_other_expanders(analyzer_name)
        
        # Get current drawing area (identifies which tab/model)
        if not self.model_canvas_loader:
            self._show_error(analyzer_name, "No canvas loader available")
            return
        
        drawing_area = self.model_canvas_loader.get_current_document()
        if not drawing_area:
            self._show_error(analyzer_name, "No model loaded. Please create or open a model first.")
            return
        
        # Detect tab switch and clear visible state if needed
        if self._last_drawing_area != drawing_area:
            self._on_tab_switched(drawing_area)
            self._last_drawing_area = drawing_area
        
        # User expanded → Check if we need to analyze
        
        # Handle initial pre-expanded state (don't auto-analyze)
        if analyzer_name in self.initial_state_handled:
            self.initial_state_handled.discard(analyzer_name)
            # Already showing "not yet analyzed" message
            return
        
        # Initialize cache for this tab if needed
        if drawing_area not in self.results:
            self.results[drawing_area] = {}
        if drawing_area not in self.analyzing:
            self.analyzing[drawing_area] = set()
        
        # Already analyzed FOR THIS TAB → Show cached results
        if analyzer_name in self.results[drawing_area]:
            return  # Label already has the cached markup
        
        # First time expanding ON THIS TAB → Run analysis
        if analyzer_name not in self.analyzing[drawing_area]:
            self._trigger_analysis(analyzer_name, drawing_area)
    
    def _trigger_analysis(self, analyzer_name: str, drawing_area):
        """Trigger analysis in background thread and show spinner.
        
        Args:
            analyzer_name: Name of the analyzer to run
            drawing_area: GtkDrawingArea identifying the tab/model
        """
        self.analyzing[drawing_area].add(analyzer_name)
        
        # Show spinner immediately
        label = self.report_labels.get(analyzer_name)
        if label:
            display_name = self._get_display_name(analyzer_name)
            label.set_markup(
                f"<b>🔄 Analyzing {display_name}...</b>\n\n"
                f"This may take a few seconds for large models."
            )
        
        # Run analysis in background thread (keep UI responsive)
        def analyze_thread():
            try:
                result = self._run_analysis(analyzer_name, drawing_area)
                # Update UI in main thread
                GLib.idle_add(self._on_analysis_complete, analyzer_name, drawing_area, result)
            except Exception as e:
                # Show error in main thread
                GLib.idle_add(self._on_analysis_error, analyzer_name, drawing_area, str(e))
        
        threading.Thread(target=analyze_thread, daemon=True).start()
    
    def _run_analysis(self, analyzer_name: str, drawing_area):
        """Run the actual analysis (called in background thread).
        
        Args:
            analyzer_name: Name of the analyzer to run
            drawing_area: GtkDrawingArea identifying the tab/model
            
        Returns:
            Analysis result
            
        Raises:
            Exception: If model not loaded or analysis fails
        """
        # Get model for THIS specific tab
        if not self.model_canvas_loader:
            raise Exception("No canvas loader available")
        
        canvas_manager = self.model_canvas_loader.get_canvas_manager(drawing_area)
        if canvas_manager is None:
            raise Exception("No model loaded. Please create or open a model first.")
        
        # Get analyzer class and instantiate with canvas manager as model
        analyzer_class = self.analyzers.get(analyzer_name)
        if not analyzer_class:
            raise Exception(f"Unknown analyzer: {analyzer_name}")
        
        # Canvas manager IS the model (has places, transitions, arcs)
        analyzer = analyzer_class(canvas_manager)
        
        # Run analysis
        result = analyzer.analyze()
        
        return result
    
    def _on_analysis_complete(self, analyzer_name: str, drawing_area, result):
        """Handle successful analysis completion (called in main thread).
        
        Args:
            analyzer_name: Name of the analyzer
            drawing_area: GtkDrawingArea identifying the tab/model
            result: Analysis result
        """
        # Remove from analyzing set
        if drawing_area in self.analyzing:
            self.analyzing[drawing_area].discard(analyzer_name)
        
        # Cache result FOR THIS TAB
        if drawing_area not in self.results:
            self.results[drawing_area] = {}
        self.results[drawing_area][analyzer_name] = result
        
        # Format and display report (only if still on same tab)
        current_drawing_area = self.model_canvas_loader.get_current_document()
        if current_drawing_area == drawing_area:
            report_markup = self._format_report(analyzer_name, result)
            label = self.report_labels.get(analyzer_name)
            if label:
                label.set_markup(report_markup)
    
    def _on_analysis_error(self, analyzer_name: str, drawing_area, error_message: str):
        """Handle analysis error (called in main thread).
        
        Args:
            analyzer_name: Name of the analyzer
            drawing_area: GtkDrawingArea identifying the tab/model
            error_message: Error message string
        """
        # Remove from analyzing set
        if drawing_area in self.analyzing:
            self.analyzing[drawing_area].discard(analyzer_name)
        
        # Show error in report area (only if still on same tab)
        current_drawing_area = self.model_canvas_loader.get_current_document()
        if current_drawing_area == drawing_area:
            display_name = self._get_display_name(analyzer_name)
            label = self.report_labels.get(analyzer_name)
            if label:
                label.set_markup(
                    f"<b>⚠ Analysis Failed</b>\n\n"
                    f"<b>Analyzer:</b> {display_name}\n"
                    f"<b>Error:</b> {error_message}\n\n"
                    f"<i>Please check that a model is loaded and try again.</i>"
                )
    
    def _show_error(self, analyzer_name: str, error_message: str):
        """Show error message in analyzer's report label.
        
        Args:
            analyzer_name: Name of the analyzer
            error_message: Error message to display
        """
        display_name = self._get_display_name(analyzer_name)
        label = self.report_labels.get(analyzer_name)
        if label:
            label.set_markup(
                f"<b>⚠ Error</b>\n\n"
                f"<b>Analyzer:</b> {display_name}\n"
                f"<b>Error:</b> {error_message}\n\n"
                f"<i>Please check the console for details.</i>"
            )
    
    # ==================== MODEL LIFECYCLE EVENT HANDLERS ====================
    
    def on_tab_switched(self, drawing_area):
        """PUBLIC: Called when user switches tabs.
        
        Handles scenario: User creates/opens multiple models and switches between them.
        Updates UI to show cached results for the new tab, or "not yet analyzed".
        
        Args:
            drawing_area: The newly active drawing area
        """
        self._on_tab_switched(drawing_area)
    
    def _on_tab_switched(self, drawing_area):
        """Internal: Handle tab switch.
        
        Args:
            drawing_area: The newly active drawing area
        """
        # Update all expander labels to show correct state for THIS tab
        for analyzer_name, label in self.report_labels.items():
            if drawing_area in self.results and analyzer_name in self.results[drawing_area]:
                # This tab has cached results - restore them
                result = self.results[drawing_area][analyzer_name]
                report_markup = self._format_report(analyzer_name, result)
                label.set_markup(report_markup)
            elif drawing_area in self.analyzing and analyzer_name in self.analyzing[drawing_area]:
                # Analysis is running for this tab
                display_name = self._get_display_name(analyzer_name)
                label.set_markup(
                    f"<b>🔄 Analyzing {display_name}...</b>\n\n"
                    f"This may take a few seconds for large models."
                )
            else:
                # Not yet analyzed for this tab
                label.set_markup(
                    "<b>Not yet analyzed.</b>\n\n"
                    "Expand to run analysis."
                )
    
    def on_file_opened(self, drawing_area):
        """PUBLIC: Called when user opens a .shy file.
        
        Handles scenario: User opens existing Petri net file while topology panel is visible.
        Clears cache for the tab where file was loaded.
        
        Args:
            drawing_area: The drawing area where file was loaded
        """
        self.invalidate_cache(drawing_area)
    
    def on_pathway_imported(self, drawing_area):
        """PUBLIC: Called when KEGG or SBML pathway is imported.
        
        Handles scenario: User imports pathway into existing or new tab.
        Clears cache because model has completely changed.
        
        Args:
            drawing_area: The drawing area where pathway was imported
        """
        self.invalidate_cache(drawing_area)
    
    def on_model_modified(self, drawing_area):
        """PUBLIC: Called when model is modified (place/transition/arc added/removed).
        
        Handles scenario: User interactively designs model by adding/removing elements.
        Clears cache because topology has changed.
        
        Args:
            drawing_area: The drawing area where model was modified
        """
        self.invalidate_cache(drawing_area)
    
    def invalidate_cache(self, drawing_area):
        """Clear cached results for a specific tab.
        
        Args:
            drawing_area: The drawing area whose cache should be cleared
        """
        if drawing_area in self.results:
            del self.results[drawing_area]
        if drawing_area in self.analyzing:
            # Don't stop running analyses, just clear the set for next time
            pass
        
        # Update UI if this is the current tab
        if self.model_canvas_loader:
            current = self.model_canvas_loader.get_current_document()
            if current == drawing_area:
                # Refresh all labels to show "not yet analyzed"
                for analyzer_name, label in self.report_labels.items():
                    expander = self.expanders.get(analyzer_name)
                    if expander and expander.get_expanded():
                        # Expanded but no cache - show prompt to re-analyze
                        label.set_markup(
                            "<b>⚠ Model Changed</b>\n\n"
                            "Model was modified since last analysis.\n"
                            "Collapse and expand again to re-analyze."
                        )
                    else:
                        # Collapsed - just show default message
                        label.set_markup(
                            "<b>Not yet analyzed.</b>\n\n"
                            "Expand to run analysis."
                        )
    
    def invalidate_all_caches(self):
        """Clear ALL cached results for ALL tabs.
        
        Use when something global changes (e.g., analyzer settings).
        """
        self.results.clear()
        self.analyzing.clear()
        
        # Update UI
        for analyzer_name, label in self.report_labels.items():
            label.set_markup(
                "<b>Not yet analyzed.</b>\n\n"
                "Expand to run analysis."
            )
    
    def _get_display_name(self, analyzer_name: str) -> str:
        """Get display name for analyzer.
        
        Args:
            analyzer_name: Internal analyzer name (e.g., 'p_invariants')
            
        Returns:
            Display name (e.g., 'P-Invariants')
        """
        display_names = {
            'p_invariants': 'P-Invariants',
            't_invariants': 'T-Invariants',
            'siphons': 'Siphons',
            'traps': 'Traps',
            'cycles': 'Elementary Cycles',
            'paths': 'Critical Paths',
            'hubs': 'Network Hubs',
            'reachability': 'Reachability Analysis',
            'boundedness': 'Boundedness Analysis',
            'liveness': 'Liveness Analysis',
            'deadlocks': 'Deadlock Detection',
            'fairness': 'Fairness Analysis',
        }
        return display_names.get(analyzer_name, analyzer_name.replace('_', ' ').title())
    
    def _format_report(self, analyzer_name: str, result) -> str:
        """Format analysis results as Pango markup.
        
        Args:
            analyzer_name: Name of the analyzer
            result: Analysis result
            
        Returns:
            Pango markup string
        """
        # Route to appropriate formatter
        if analyzer_name == 'p_invariants':
            return self._format_p_invariants_report(result)
        elif analyzer_name == 't_invariants':
            return self._format_t_invariants_report(result)
        elif analyzer_name == 'siphons':
            return self._format_siphons_report(result)
        elif analyzer_name == 'traps':
            return self._format_traps_report(result)
        elif analyzer_name == 'cycles':
            return self._format_cycles_report(result)
        elif analyzer_name == 'paths':
            return self._format_paths_report(result)
        elif analyzer_name == 'hubs':
            return self._format_hubs_report(result)
        elif analyzer_name == 'reachability':
            return self._format_reachability_report(result)
        elif analyzer_name == 'boundedness':
            return self._format_boundedness_report(result)
        elif analyzer_name == 'liveness':
            return self._format_liveness_report(result)
        elif analyzer_name == 'deadlocks':
            return self._format_deadlocks_report(result)
        elif analyzer_name == 'fairness':
            return self._format_fairness_report(result)
        else:
            return f"<b>Unknown analyzer: {analyzer_name}</b>"
    
    # ==================== REPORT FORMATTERS ====================
    
    def _format_p_invariants_report(self, result) -> str:
        """Format P-Invariants analysis report."""
        if not result or not result.success:
            return "<b>P-Invariants Analysis</b>\n\n<i>Analysis failed or no data.</i>"
        
        invariants = result.get('invariants', [])
        count = len(invariants)
        
        lines = [f"<b>P-Invariants Analysis Results</b>\n"]
        lines.append(f"Found: <b>{count}</b> invariant{'s' if count != 1 else ''}\n")
        
        if count > 0:
            lines.append("\n<b>Invariants:</b>")
            for i, inv in enumerate(invariants[:10], 1):  # Show first 10
                places = inv.get('places', [])
                weights = inv.get('weights', [])
                lines.append(f"\n<b>Invariant {i}:</b>")
                for j, (place, weight) in enumerate(zip(places[:20], weights[:20])):  # Show first 20 places
                    lines.append(f"  • {place} (weight: {weight})")
                if len(places) > 20:
                    lines.append(f"  <i>... and {len(places) - 20} more places</i>")
            
            if count > 10:
                lines.append(f"\n<i>... and {count - 10} more invariants</i>")
        
        return '\n'.join(lines)
    
    def _format_t_invariants_report(self, result) -> str:
        """Format T-Invariants analysis report."""
        if not result or not result.success:
            return "<b>T-Invariants Analysis</b>\n\n<i>Analysis failed or no data.</i>"
        
        invariants = result.get('invariants', [])
        count = len(invariants)
        
        lines = [f"<b>T-Invariants Analysis Results</b>\n"]
        lines.append(f"Found: <b>{count}</b> invariant{'s' if count != 1 else ''}\n")
        
        if count > 0:
            lines.append("\n<b>Invariants:</b>")
            for i, inv in enumerate(invariants[:10], 1):
                transitions = inv.get('transitions', [])
                weights = inv.get('weights', [])
                lines.append(f"\n<b>Invariant {i}:</b>")
                for j, (trans, weight) in enumerate(zip(transitions[:20], weights[:20])):
                    lines.append(f"  • {trans} (weight: {weight})")
                if len(transitions) > 20:
                    lines.append(f"  <i>... and {len(transitions) - 20} more transitions</i>")
            
            if count > 10:
                lines.append(f"\n<i>... and {count - 10} more invariants</i>")
        
        return '\n'.join(lines)
    
    def _format_siphons_report(self, result) -> str:
        """Format Siphons analysis report."""
        if not result or not result.success:
            return "<b>Siphons Analysis</b>\n\n<i>Analysis failed or no data.</i>"
        
        siphons = result.get('siphons', [])
        count = len(siphons)
        
        lines = [f"<b>Siphons Analysis Results</b>\n"]
        lines.append(f"Found: <b>{count}</b> siphon{'s' if count != 1 else ''}\n")
        
        if count > 0:
            lines.append("\n<b>Siphons:</b>")
            for i, siphon in enumerate(siphons[:10], 1):
                places = siphon.get('places', [])
                lines.append(f"\n<b>Siphon {i}:</b>")
                lines.append(f"  Places: {', '.join(places[:15])}")
                if len(places) > 15:
                    lines.append(f"  <i>... and {len(places) - 15} more places</i>")
            
            if count > 10:
                lines.append(f"\n<i>... and {count - 10} more siphons</i>")
        
        return '\n'.join(lines)
    
    def _format_traps_report(self, result) -> str:
        """Format Traps analysis report."""
        if not result or not result.success:
            return "<b>Traps Analysis</b>\n\n<i>Analysis failed or no data.</i>"
        
        traps = result.get('traps', [])
        count = len(traps)
        
        lines = [f"<b>Traps Analysis Results</b>\n"]
        lines.append(f"Found: <b>{count}</b> trap{'s' if count != 1 else ''}\n")
        
        if count > 0:
            lines.append("\n<b>Traps:</b>")
            for i, trap in enumerate(traps[:10], 1):
                places = trap.get('places', [])
                lines.append(f"\n<b>Trap {i}:</b>")
                lines.append(f"  Places: {', '.join(places[:15])}")
                if len(places) > 15:
                    lines.append(f"  <i>... and {len(places) - 15} more places</i>")
            
            if count > 10:
                lines.append(f"\n<i>... and {count - 10} more traps</i>")
        
        return '\n'.join(lines)
    
    def _format_cycles_report(self, result) -> str:
        """Format Elementary Cycles analysis report."""
        if not result or not result.success:
            return "<b>Elementary Cycles Analysis</b>\n\n<i>Analysis failed or no data.</i>"
        
        cycles = result.get('cycles', [])
        count = result.get('count', len(cycles))
        longest_length = result.get('longest_length', 0)
        truncated = result.get('truncated', False)
        
        lines = [f"<b>Elementary Cycles Analysis Results</b>\n"]
        lines.append(f"Found: <b>{count}</b> cycle{'s' if count != 1 else ''}")
        if longest_length > 0:
            lines.append(f"Longest: <b>{longest_length}</b> nodes")
        if truncated:
            lines.append("<i>(results truncated)</i>")
        lines.append("")
        
        if cycles:
            lines.append("\n<b>Cycles:</b>")
            for i, cycle in enumerate(cycles[:10], 1):
                names = cycle.get('names', [])
                length = cycle.get('length', len(names))
                cycle_type = cycle.get('type', 'unknown')
                place_count = cycle.get('place_count', 0)
                trans_count = cycle.get('transition_count', 0)
                
                lines.append(f"\n<b>Cycle {i}:</b> ({length} nodes, {cycle_type})")
                lines.append(f"  Places: {place_count}, Transitions: {trans_count}")
                if names:
                    path = " → ".join(names[:10])
                    if len(names) > 10:
                        path += f" ... (+{len(names) - 10} more)"
                    lines.append(f"  Path: {path}")
            
            if count > 10:
                lines.append(f"\n<i>... and {count - 10} more cycles</i>")
        
        return '\n'.join(lines)
    
    def _format_paths_report(self, result) -> str:
        """Format Critical Paths analysis report."""
        if not result or not result.success:
            return "<b>Critical Paths Analysis</b>\n\n<i>Analysis failed or no data.</i>"
        
        # Check if this is a specific path query or general analysis
        path = result.get('path')
        if path:
            # Specific path between source and target
            length = result.get('length', 0)
            exists = result.get('exists', True)
            
            lines = [f"<b>Path Analysis Results</b>\n"]
            if exists:
                names = path.get('names', [])
                place_count = path.get('place_count', 0)
                trans_count = path.get('transition_count', 0)
                
                lines.append(f"Path found: <b>{length}</b> step{'s' if length != 1 else ''}")
                lines.append(f"Places: {place_count}, Transitions: {trans_count}\n")
                
                if names:
                    path_str = " → ".join(names)
                    lines.append(f"<b>Route:</b>\n{path_str}")
            else:
                lines.append("<i>No path exists between specified nodes.</i>")
        else:
            # General path analysis
            paths = result.get('paths', [])
            count = result.get('count', len(paths))
            
            lines = [f"<b>Path Analysis Results</b>\n"]
            lines.append(f"Found: <b>{count}</b> path{'s' if count != 1 else ''}\n")
            
            if paths:
                lines.append("\n<b>Paths:</b>")
                for i, p in enumerate(paths[:8], 1):
                    names = p.get('names', [])
                    length = p.get('length', 0)
                    lines.append(f"\n<b>Path {i}:</b> ({length} steps)")
                    if names:
                        route = " → ".join(names[:8])
                        if len(names) > 8:
                            route += f" ... (+{len(names) - 8} more)"
                        lines.append(f"  {route}")
                
                if count > 8:
                    lines.append(f"\n<i>... and {count - 8} more paths</i>")
        
        return '\n'.join(lines)
    
    def _format_hubs_report(self, result) -> str:
        """Format Network Hubs analysis report."""
        if not result or not result.success:
            return "<b>Network Hubs Analysis</b>\n\n<i>Analysis failed or no data.</i>"
        
        hubs = result.get('hubs', [])
        count = result.get('count', len(hubs))
        max_degree = result.get('max_degree', 0)
        avg_degree = result.get('avg_degree', 0)
        
        lines = [f"<b>Network Hubs Analysis Results</b>\n"]
        lines.append(f"Found: <b>{count}</b> hub{'s' if count != 1 else ''}")
        lines.append(f"Max degree: <b>{max_degree}</b>")
        lines.append(f"Avg degree: <b>{avg_degree:.1f}</b>\n")
        
        if hubs:
            lines.append("\n<b>Top Hubs:</b>")
            for i, hub in enumerate(hubs[:12], 1):
                name = hub.get('name', 'Unknown')
                degree = hub.get('degree', 0)
                in_deg = hub.get('in_degree', 0)
                out_deg = hub.get('out_degree', 0)
                node_type = hub.get('type', 'unknown')
                
                lines.append(f"\n<b>{i}. {name}</b> ({node_type})")
                lines.append(f"  Degree: {degree} (in: {in_deg}, out: {out_deg})")
            
            if count > 12:
                lines.append(f"\n<i>... and {count - 12} more hubs</i>")
        
        return '\n'.join(lines)
    
    def _format_reachability_report(self, result) -> str:
        """Format Reachability Analysis report."""
        if not result or not result.success:
            return "<b>Reachability Analysis</b>\n\n<i>Analysis failed or no data.</i>"
        
        total_states = result.get('total_states', 0)
        total_transitions = result.get('total_transitions', 0)
        max_depth = result.get('max_depth_reached', 0)
        is_bounded = result.get('is_bounded', True)
        deadlock_states = result.get('deadlock_states', [])
        
        lines = [f"<b>Reachability Analysis Results</b>\n"]
        lines.append(f"Reachable states: <b>{total_states}</b>")
        lines.append(f"State transitions: <b>{total_transitions}</b>")
        lines.append(f"Max depth: <b>{max_depth}</b>")
        lines.append(f"Bounded: <b>{'Yes' if is_bounded else 'No'}</b>\n")
        
        if deadlock_states:
            lines.append(f"\n<b>⚠ Deadlock States Found: {len(deadlock_states)}</b>")
            for i, state in enumerate(deadlock_states[:5], 1):
                marking = state.get('marking', {})
                if marking:
                    # Show first few places with tokens
                    tokens_str = ", ".join([f"{k}: {v}" for k, v in list(marking.items())[:5]])
                    if len(marking) > 5:
                        tokens_str += "..."
                    lines.append(f"  State {i}: [{tokens_str}]")
            
            if len(deadlock_states) > 5:
                lines.append(f"  <i>... and {len(deadlock_states) - 5} more deadlock states</i>")
        else:
            lines.append("\n<b>✓ No deadlock states detected</b>")
        
        return '\n'.join(lines)
    
    def _format_boundedness_report(self, result) -> str:
        """Format Boundedness Analysis report."""
        if not result or not result.success:
            return "<b>Boundedness Analysis</b>\n\n<i>Analysis failed or no data.</i>"
        
        is_bounded = result.get('is_bounded', False)
        boundedness_level = result.get('boundedness_level', 0)
        is_safe = result.get('is_safe', False)
        is_conservative = result.get('is_conservative', False)
        unbounded_places = result.get('unbounded_places', [])
        place_bounds = result.get('place_bounds', {})
        overflow_risk = result.get('overflow_risk', False)
        
        lines = [f"<b>Boundedness Analysis Results</b>\n"]
        
        if is_bounded:
            if is_safe:
                lines.append("<b>✓ Net is SAFE (1-bounded)</b>")
            else:
                lines.append(f"<b>✓ Net is {boundedness_level}-BOUNDED</b>")
        else:
            lines.append("<b>⚠ Net is UNBOUNDED</b>")
        
        lines.append(f"Conservative: <b>{'Yes' if is_conservative else 'No'}</b>")
        lines.append(f"Overflow risk: <b>{'Yes' if overflow_risk else 'No'}</b>\n")
        
        if unbounded_places:
            lines.append(f"\n<b>⚠ Unbounded Places ({len(unbounded_places)}):</b>")
            for place_info in unbounded_places[:10]:
                if isinstance(place_info, dict):
                    name = place_info.get('name', 'Unknown')
                    lines.append(f"  • {name}")
                else:
                    lines.append(f"  • {place_info}")
            
            if len(unbounded_places) > 10:
                lines.append(f"  <i>... and {len(unbounded_places) - 10} more</i>")
        
        if place_bounds and is_bounded:
            max_bound = max(place_bounds.values()) if place_bounds else 0
            lines.append(f"\n<b>Place Bounds:</b>")
            lines.append(f"Maximum tokens: <b>{max_bound}</b>")
            
            # Show places with highest bounds
            sorted_places = sorted(place_bounds.items(), key=lambda x: x[1], reverse=True)
            for place_id, bound in sorted_places[:8]:
                lines.append(f"  • Place {place_id}: {bound} tokens")
            
            if len(place_bounds) > 8:
                lines.append(f"  <i>... and {len(place_bounds) - 8} more places</i>")
        
        return '\n'.join(lines)
    
    def _format_liveness_report(self, result) -> str:
        """Format Liveness Analysis report."""
        if not result or not result.success:
            return "<b>Liveness Analysis</b>\n\n<i>Analysis failed or no data.</i>"
        
        is_live = result.get('is_live', False)
        liveness_levels = result.get('liveness_levels', {})
        dead_transitions = result.get('dead_transitions', [])
        live_transitions = result.get('live_transitions', [])
        total_transitions = result.get('total_transitions', 0)
        
        lines = [f"<b>Liveness Analysis Results</b>\n"]
        
        if is_live:
            lines.append("<b>✓ Net is LIVE</b>")
            lines.append("<i>All transitions can fire infinitely often.</i>\n")
        else:
            lines.append("<b>⚠ Net is NOT LIVE</b>")
            if dead_transitions:
                lines.append(f"<i>{len(dead_transitions)} dead transition(s) detected.</i>\n")
        
        lines.append(f"Total transitions: <b>{total_transitions}</b>")
        lines.append(f"Live transitions: <b>{len(live_transitions)}</b>")
        lines.append(f"Dead transitions: <b>{len(dead_transitions)}</b>\n")
        
        if dead_transitions:
            lines.append("\n<b>⚠ Dead Transitions (L0):</b>")
            for trans_info in dead_transitions[:10]:
                if isinstance(trans_info, dict):
                    name = trans_info.get('name', 'Unknown')
                    reason = trans_info.get('reason', 'Cannot fire')
                    lines.append(f"  • {name}: {reason}")
                else:
                    lines.append(f"  • {trans_info}")
            
            if len(dead_transitions) > 10:
                lines.append(f"  <i>... and {len(dead_transitions) - 10} more</i>")
        
        # Show liveness level distribution
        if liveness_levels:
            level_counts = {'L0': 0, 'L1': 0, 'L2': 0, 'L3': 0, 'L4': 0}
            for level in liveness_levels.values():
                if level in level_counts:
                    level_counts[level] += 1
            
            if any(level_counts.values()):
                lines.append("\n<b>Liveness Levels:</b>")
                for level, count in level_counts.items():
                    if count > 0:
                        lines.append(f"  {level}: {count} transition(s)")
        
        return '\n'.join(lines)
    
    def _format_deadlocks_report(self, result) -> str:
        """Format Deadlock Detection report."""
        if not result or not result.success:
            return "<b>Deadlock Detection</b>\n\n<i>Analysis failed or no data.</i>"
        
        has_deadlock = result.get('has_deadlock', False)
        deadlock_type = result.get('deadlock_type', 'none')
        empty_siphons = result.get('empty_siphons', [])
        disabled_transitions = result.get('disabled_transitions', [])
        deadlock_places = result.get('deadlock_places', [])
        severity = result.get('severity', 'none')
        recovery_suggestions = result.get('recovery_suggestions', [])
        
        lines = [f"<b>Deadlock Detection Results</b>\n"]
        
        if has_deadlock:
            lines.append(f"<b>⚠ DEADLOCK DETECTED</b>")
            lines.append(f"Type: <b>{deadlock_type.upper()}</b>")
            lines.append(f"Severity: <b>{severity.upper()}</b>\n")
        else:
            lines.append("<b>✓ NO DEADLOCK DETECTED</b>")
            lines.append("<i>All transitions can be enabled.</i>\n")
        
        if empty_siphons:
            lines.append(f"\n<b>Empty Siphons ({len(empty_siphons)}):</b>")
            lines.append("<i>Structural deadlock - once empty, stays empty</i>")
            for siphon in empty_siphons[:5]:
                if isinstance(siphon, dict):
                    places = siphon.get('places', [])
                    lines.append(f"  • Siphon with {len(places)} places")
                else:
                    lines.append(f"  • {siphon}")
            
            if len(empty_siphons) > 5:
                lines.append(f"  <i>... and {len(empty_siphons) - 5} more</i>")
        
        if disabled_transitions:
            lines.append(f"\n<b>Disabled Transitions ({len(disabled_transitions)}):</b>")
            for trans in disabled_transitions[:10]:
                if isinstance(trans, dict):
                    name = trans.get('name', 'Unknown')
                    reason = trans.get('reason', 'Not enabled')
                    lines.append(f"  • {name}: {reason}")
                else:
                    lines.append(f"  • {trans}")
            
            if len(disabled_transitions) > 10:
                lines.append(f"  <i>... and {len(disabled_transitions) - 10} more</i>")
        
        if deadlock_places:
            lines.append(f"\n<b>Deadlock Places ({len(deadlock_places)}):</b>")
            for place in deadlock_places[:10]:
                lines.append(f"  • {place}")
            
            if len(deadlock_places) > 10:
                lines.append(f"  <i>... and {len(deadlock_places) - 10} more</i>")
        
        if recovery_suggestions:
            lines.append("\n<b>Recovery Suggestions:</b>")
            for suggestion in recovery_suggestions[:5]:
                lines.append(f"  • {suggestion}")
        
        return '\n'.join(lines)
    
    def _format_fairness_report(self, result) -> str:
        """Format Fairness Analysis report."""
        if not result or not result.success:
            return "<b>Fairness Analysis</b>\n\n<i>Analysis failed or no data.</i>"
        
        is_fair = result.get('is_fair', False)
        fairness_level = result.get('fairness_level', 'none')
        conflicting_transitions = result.get('conflicting_transitions', [])
        starvation_risk = result.get('starvation_risk', [])
        priority_conflicts = result.get('priority_conflicts', [])
        fairness_violations = result.get('fairness_violations', [])
        total_transitions = result.get('total_transitions', 0)
        
        lines = [f"<b>Fairness Analysis Results</b>\n"]
        
        if is_fair:
            lines.append(f"<b>✓ Net has {fairness_level.upper()} FAIRNESS</b>")
            lines.append("<i>Transitions get fair firing opportunities.</i>\n")
        else:
            lines.append("<b>⚠ Net lacks FAIRNESS guarantees</b>")
            lines.append("<i>Some transitions may be starved.</i>\n")
        
        lines.append(f"Fairness level: <b>{fairness_level}</b>")
        lines.append(f"Total transitions: <b>{total_transitions}</b>\n")
        
        if conflicting_transitions:
            lines.append(f"\n<b>Conflicting Transition Sets ({len(conflicting_transitions)}):</b>")
            for i, conflict in enumerate(conflicting_transitions[:8], 1):
                if isinstance(conflict, dict):
                    transitions = conflict.get('transitions', [])
                    place = conflict.get('place', 'Unknown')
                    lines.append(f"  {i}. Conflict at {place}: {len(transitions)} transitions")
                elif isinstance(conflict, (list, set)):
                    lines.append(f"  {i}. Conflict: {len(conflict)} transitions")
                else:
                    lines.append(f"  {i}. {conflict}")
            
            if len(conflicting_transitions) > 8:
                lines.append(f"  <i>... and {len(conflicting_transitions) - 8} more conflicts</i>")
        
        if starvation_risk:
            lines.append(f"\n<b>⚠ Starvation Risk ({len(starvation_risk)}):</b>")
            for trans in starvation_risk[:10]:
                if isinstance(trans, dict):
                    name = trans.get('name', 'Unknown')
                    reason = trans.get('reason', 'Low priority')
                    lines.append(f"  • {name}: {reason}")
                else:
                    lines.append(f"  • {trans}")
            
            if len(starvation_risk) > 10:
                lines.append(f"  <i>... and {len(starvation_risk) - 10} more</i>")
        
        if fairness_violations:
            lines.append(f"\n<b>Fairness Violations ({len(fairness_violations)}):</b>")
            for violation in fairness_violations[:5]:
                lines.append(f"  • {violation}")
            
            if len(fairness_violations) > 5:
                lines.append(f"  <i>... and {len(fairness_violations) - 5} more</i>")
        
        if priority_conflicts:
            lines.append(f"\n<b>Priority Conflicts ({len(priority_conflicts)}):</b>")
            for conflict in priority_conflicts[:5]:
                if isinstance(conflict, dict):
                    trans1 = conflict.get('transition1', 'T1')
                    trans2 = conflict.get('transition2', 'T2')
                    lines.append(f"  • {trans1} vs {trans2}")
                else:
                    lines.append(f"  • {conflict}")
            
            if len(priority_conflicts) > 5:
                lines.append(f"  <i>... and {len(priority_conflicts) - 5} more</i>")
        
        return '\n'.join(lines)


# Module exports
__all__ = ['TopologyPanelController']
