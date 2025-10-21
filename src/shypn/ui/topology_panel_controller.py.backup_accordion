"""Topology Panel Controller - Business Logic.

Clean OOP architecture:
- Separated from UI loader
- Coordinates 12 analyzers
- Manages results cache
- Updates UI with results

Author: Simão Eugénio
Date: 2025-10-20
"""

import sys
from typing import Dict, Optional

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

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
    """Controller for Topology Panel.
    
    Responsibilities:
    - Initialize all 12 analyzers
    - Run analysis on button click
    - Cache results
    - Update UI labels
    - Coordinate highlighting
    
    NOT responsible for:
    - UI loading (handled by loader)
    - Widget lifecycle (handled by base)
    - Wayland safety (handled by base)
    """
    
    def __init__(
        self,
        model,
        analyze_buttons: Dict[str, Gtk.Button],
        highlight_buttons: Dict[str, Gtk.Button],
        result_labels: Dict[str, Gtk.Label],
        expand_buttons: Optional[Dict[str, Gtk.ToggleButton]] = None,
        expand_icons: Optional[Dict[str, Gtk.Image]] = None,
        detail_revealers: Optional[Dict[str, Gtk.Revealer]] = None,
        detail_labels: Optional[Dict[str, Gtk.Label]] = None,
    ):
        """Initialize controller.
        
        Args:
            model: ShypnModel instance (can be None - will be fetched at analysis time)
            analyze_buttons: Dict mapping analyzer name → analyze button
            highlight_buttons: Dict mapping analyzer name → highlight button
            result_labels: Dict mapping analyzer name → result label (summary)
            expand_buttons: Dict mapping analyzer name → expand toggle button ([V]/[^])
            expand_icons: Dict mapping analyzer name → expand icon widget
            detail_revealers: Dict mapping analyzer name → GtkRevealer widget
            detail_labels: Dict mapping analyzer name → detail report label
        """
        self.model = model
        self.model_canvas_loader = None  # Set externally to access current model
        self.analyze_buttons = analyze_buttons
        self.highlight_buttons = highlight_buttons
        self.result_labels = result_labels
        
        # Accordion widgets
        self.expand_buttons = expand_buttons or {}
        self.expand_icons = expand_icons or {}
        self.detail_revealers = detail_revealers or {}
        self.detail_labels = detail_labels or {}
        
        # Results cache (analyzer name → result dict)
        self.results = {}
        
        # Analyzer classes (will instantiate on-demand with current model)
        self.analyzer_classes = {
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
        
        print(f"✓ Topology panel controller initialized with {len(self.analyzer_classes)} analyzer classes")
    
    def on_analyze_clicked(self, button: Gtk.Button, analyzer_name: str):
        """Handle analyze button click.
        
        Args:
            button: The button that was clicked
            analyzer_name: Name of the analyzer to run
        """
        if analyzer_name not in self.analyzer_classes:
            print(f"Unknown analyzer: {analyzer_name}", file=sys.stderr)
            return
        
        # Get analyzer class
        analyzer_class = self.analyzer_classes[analyzer_name]
        
        # Get result label
        result_label = self.result_labels.get(analyzer_name)
        if not result_label:
            print(f"No result label for: {analyzer_name}", file=sys.stderr)
            return
        
        # Get current model from model_canvas_loader
        model = None
        if self.model_canvas_loader and hasattr(self.model_canvas_loader, 'current_document'):
            current_doc = self.model_canvas_loader.current_document
            if current_doc and hasattr(current_doc, 'model'):
                model = current_doc.model
        
        if not model:
            result_label.set_text("Error: No model loaded")
            return
        
        try:
            # Show analyzing message
            result_label.set_text("Analyzing...")
            
            # Create analyzer instance with current model
            analyzer = analyzer_class(model)
            
            # Run analysis
            result = analyzer.analyze()
            
            # Cache result
            self.results[analyzer_name] = result
            
            # Update UI with result
            self._update_result_label(analyzer_name, result)
            
            # Enable highlight button
            highlight_btn = self.highlight_buttons.get(analyzer_name)
            if highlight_btn:
                highlight_btn.set_sensitive(True)
            
            # Auto-expand the detail section to show results
            expand_btn = self.expand_buttons.get(analyzer_name)
            if expand_btn and not expand_btn.get_active():
                expand_btn.set_active(True)  # This will trigger on_expand_clicked
                
        except Exception as e:
            # Show error
            result_label.set_text(f"Error: {e}")
            print(f"Error analyzing {analyzer_name}: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
    
    def on_highlight_clicked(self, button: Gtk.Button, analyzer_name: str):
        """Handle highlight button click.
        
        Args:
            button: The button that was clicked
            analyzer_name: Name of the analyzer whose results to highlight
        """
        # Get cached result
        result = self.results.get(analyzer_name)
        if not result:
            print(f"No cached result for: {analyzer_name}", file=sys.stderr)
            return
        
        # TODO: Implement highlighting (Day 3)
        # For now, just print
        print(f"TODO: Highlight {analyzer_name} results: {result}")
    
    def _update_result_label(self, analyzer_name: str, result):
        """Update result label with analysis results.
        
        Args:
            analyzer_name: Name of the analyzer
            result: AnalysisResult object from analyzer
        """
        result_label = self.result_labels.get(analyzer_name)
        if not result_label:
            return
        
        # Check if analysis succeeded
        if not result.success:
            error_msg = "Analysis failed"
            if result.errors:
                error_msg += f": {result.errors[0]}"
            result_label.set_text(error_msg)
            return
        
        # Get data from result
        data = result.data if hasattr(result, 'data') else {}
        
        # Format result based on analyzer type
        # This is a simple implementation - can be refined
        
        if analyzer_name == 'p_invariants':
            invariants = data.get('p_invariants', [])
            count = len(invariants)
            if count == 0:
                text = "No P-invariants found"
            else:
                text = f"Found {count} P-invariant(s)"
                if count <= 3:
                    # Show details for small counts
                    details = []
                    for inv in invariants[:3]:
                        places = inv.get('places', [])
                        details.append(f"  • {len(places)} places")
                    text += "\n" + "\n".join(details)
            result_label.set_text(text)
        
        elif analyzer_name == 't_invariants':
            invariants = data.get('t_invariants', [])
            count = len(invariants)
            if count == 0:
                text = "No T-invariants found"
            else:
                text = f"Found {count} T-invariant(s)"
                if count <= 3:
                    details = []
                    for inv in invariants[:3]:
                        transitions = inv.get('transitions', [])
                        details.append(f"  • {len(transitions)} transitions")
                    text += "\n" + "\n".join(details)
            result_label.set_text(text)
        
        elif analyzer_name == 'siphons':
            siphons = data.get('siphons', [])
            count = len(siphons)
            if count == 0:
                text = "No siphons found (good - no deadlock potential)"
            else:
                text = f"⚠ Found {count} siphon(s) - potential deadlocks"
                if count <= 3:
                    details = []
                    for siphon in siphons[:3]:
                        places = siphon.get('places', [])
                        details.append(f"  • {len(places)} places")
                    text += "\n" + "\n".join(details)
            result_label.set_text(text)
        
        elif analyzer_name == 'traps':
            traps = data.get('traps', [])
            count = len(traps)
            if count == 0:
                text = "No traps found"
            else:
                text = f"Found {count} trap(s)"
                if count <= 3:
                    details = []
                    for trap in traps[:3]:
                        places = trap.get('places', [])
                        details.append(f"  • {len(places)} places")
                    text += "\n" + "\n".join(details)
            result_label.set_text(text)
        
        elif analyzer_name == 'cycles':
            cycles = data.get('cycles', [])
            count = len(cycles)
            if count == 0:
                text = "No cycles found"
            else:
                text = f"Found {count} cycle(s) - feedback loops"
                if count <= 3:
                    details = []
                    for cycle in cycles[:3]:
                        length = len(cycle.get('path', []))
                        details.append(f"  • Length {length}")
                    text += "\n" + "\n".join(details)
            result_label.set_text(text)
        
        elif analyzer_name == 'paths':
            paths = data.get('paths', [])
            count = len(paths)
            if count == 0:
                text = "No paths found"
            else:
                text = f"Found {count} metabolic path(s)"
                if count <= 3:
                    details = []
                    for path in paths[:3]:
                        length = len(path.get('transitions', []))
                        details.append(f"  • {length} transitions")
                    text += "\n" + "\n".join(details)
            result_label.set_text(text)
        
        elif analyzer_name == 'hubs':
            hubs = data.get('hubs', [])
            count = len(hubs)
            if count == 0:
                text = "No hubs found"
            else:
                text = f"Found {count} hub(s) - central metabolites"
                if count <= 5:
                    details = []
                    for hub in hubs[:5]:
                        name = hub.get('name', 'Unknown')
                        degree = hub.get('degree', 0)
                        details.append(f"  • {name}: {degree} connections")
                    text += "\n" + "\n".join(details)
            result_label.set_text(text)
        
        elif analyzer_name == 'reachability':
            is_reachable = data.get('is_reachable', False)
            states_count = data.get('states_explored', 0)
            if is_reachable:
                text = f"✓ Network is reachable\n({states_count} states explored)"
            else:
                text = f"✗ Network has unreachable states\n({states_count} states explored)"
            result_label.set_text(text)
        
        elif analyzer_name == 'boundedness':
            is_bounded = data.get('is_bounded', False)
            max_tokens = data.get('max_tokens', 0)
            if is_bounded:
                text = f"✓ Network is bounded\n(max {max_tokens} tokens per place)"
            else:
                text = f"✗ Network is unbounded\n(tokens can grow infinitely)"
            result_label.set_text(text)
        
        elif analyzer_name == 'liveness':
            is_live = data.get('is_live', False)
            liveness_level = data.get('liveness_level', 0)
            if is_live:
                text = f"✓ Network is live (L{liveness_level})\n(all transitions can fire)"
            else:
                text = f"✗ Network is not live\n(some transitions may be blocked)"
            result_label.set_text(text)
        
        elif analyzer_name == 'deadlocks':
            has_deadlocks = data.get('has_deadlocks', False)
            deadlock_states = data.get('deadlock_states', [])
            count = len(deadlock_states)
            if has_deadlocks:
                text = f"✗ Found {count} deadlock state(s)\n(network can get stuck)"
            else:
                text = f"✓ No deadlocks found\n(network cannot get stuck)"
            result_label.set_text(text)
        
        elif analyzer_name == 'fairness':
            is_fair = data.get('is_fair', False)
            conflicts = data.get('conflicts', [])
            if is_fair:
                text = f"✓ Network is fair\n(conflicts resolved fairly)"
            else:
                text = f"✗ Network has unfair conflicts\n({len(conflicts)} conflict(s) found)"
            result_label.set_text(text)
        
        else:
            # Generic fallback - use summary if available
            if hasattr(result, 'summary') and result.summary:
                result_label.set_text(result.summary)
            else:
                result_label.set_text(f"Analysis complete")
    
    def on_expand_clicked(self, toggle_button: Gtk.ToggleButton, analyzer_name: str):
        """Handle expand/collapse toggle button click.
        
        Args:
            toggle_button: The toggle button that was clicked ([V] or [^])
            analyzer_name: Name of the analyzer to expand/collapse
        """
        is_expanded = toggle_button.get_active()
        
        # Get revealer widget
        revealer = self.detail_revealers.get(analyzer_name)
        if not revealer:
            print(f"No revealer found for: {analyzer_name}", file=sys.stderr)
            return
        
        # Get expand icon to update
        expand_icon = self.expand_icons.get(analyzer_name)
        
        # Animate expand/collapse
        revealer.set_reveal_child(is_expanded)
        
        # Update icon: down arrow when collapsed, up arrow when expanded
        if expand_icon:
            if is_expanded:
                expand_icon.set_from_icon_name('pan-up-symbolic', Gtk.IconSize.BUTTON)
            else:
                expand_icon.set_from_icon_name('pan-down-symbolic', Gtk.IconSize.BUTTON)
        
        # If expanding and we have cached results, populate detail report
        if is_expanded and analyzer_name in self.results:
            self._populate_detail_report(analyzer_name)
    
    def _populate_detail_report(self, analyzer_name: str):
        """Generate and display detailed report for an analyzer.
        
        Args:
            analyzer_name: Name of the analyzer
        """
        result = self.results.get(analyzer_name)
        if not result:
            return
        
        detail_label = self.detail_labels.get(analyzer_name)
        if not detail_label:
            return
        
        # Generate detailed markup based on analyzer type
        try:
            if analyzer_name == 'p_invariants':
                markup = self._format_p_invariants_detail(result)
            elif analyzer_name == 't_invariants':
                markup = self._format_t_invariants_detail(result)
            elif analyzer_name == 'siphons':
                markup = self._format_siphons_detail(result)
            elif analyzer_name == 'traps':
                markup = self._format_traps_detail(result)
            elif analyzer_name == 'cycles':
                markup = self._format_cycles_detail(result)
            elif analyzer_name == 'paths':
                markup = self._format_paths_detail(result)
            elif analyzer_name == 'hubs':
                markup = self._format_hubs_detail(result)
            elif analyzer_name == 'reachability':
                markup = self._format_reachability_detail(result)
            elif analyzer_name == 'boundedness':
                markup = self._format_boundedness_detail(result)
            elif analyzer_name == 'liveness':
                markup = self._format_liveness_detail(result)
            elif analyzer_name == 'deadlocks':
                markup = self._format_deadlocks_detail(result)
            elif analyzer_name == 'fairness':
                markup = self._format_fairness_detail(result)
            else:
                markup = "<b>Detailed report not available</b>"
            
            detail_label.set_markup(markup)
        except Exception as e:
            print(f"Error formatting detail report for {analyzer_name}: {e}", file=sys.stderr)
            detail_label.set_markup(f"<b>Error generating report:</b> {e}")
    
    # Detail formatters (one per analyzer) - Placeholder implementations for now
    
    def _format_p_invariants_detail(self, result) -> str:
        """Format detailed report for P-Invariants."""
        data = result.data if hasattr(result, 'data') else {}
        invariants = data.get('invariants', [])
        
        if not invariants:
            return "<b>No P-Invariants found</b>"
        
        lines = [f"<b>P-Invariants Detailed Report</b>\n"]
        lines.append(f"Total: {len(invariants)} invariant(s) found\n")
        
        for i, inv in enumerate(invariants[:10], 1):  # Show first 10
            places = inv.get('places', [])
            lines.append(f"\n<b>P-Invariant #{i}</b>")
            lines.append(f"  Places ({len(places)}):")
            for place in places[:20]:  # Show first 20 places
                weight = place.get('weight', 1)
                name = place.get('name', 'Unknown')
                lines.append(f"    • {name} (weight: {weight})")
            if len(places) > 20:
                lines.append(f"    ... and {len(places) - 20} more places")
        
        if len(invariants) > 10:
            lines.append(f"\n... and {len(invariants) - 10} more invariants")
        
        return '\n'.join(lines)
    
    def _format_t_invariants_detail(self, result) -> str:
        """Format detailed report for T-Invariants."""
        data = result.data if hasattr(result, 'data') else {}
        invariants = data.get('invariants', [])
        
        if not invariants:
            return "<b>No T-Invariants found</b>"
        
        lines = [f"<b>T-Invariants Detailed Report</b>\n"]
        lines.append(f"Total: {len(invariants)} invariant(s) found\n")
        
        for i, inv in enumerate(invariants[:10], 1):
            transitions = inv.get('transitions', [])
            lines.append(f"\n<b>T-Invariant #{i}</b>")
            lines.append(f"  Transitions ({len(transitions)}):")
            for trans in transitions[:20]:
                weight = trans.get('weight', 1)
                name = trans.get('name', 'Unknown')
                lines.append(f"    • {name} (weight: {weight})")
            if len(transitions) > 20:
                lines.append(f"    ... and {len(transitions) - 20} more transitions")
        
        if len(invariants) > 10:
            lines.append(f"\n... and {len(invariants) - 10} more invariants")
        
        return '\n'.join(lines)
    
    def _format_siphons_detail(self, result) -> str:
        """Format detailed report for Siphons."""
        data = result.data if hasattr(result, 'data') else {}
        siphons = data.get('siphons', [])
        
        if not siphons:
            return "<b>No siphons found</b>\n\n✓ Network has no deadlock-prone structures"
        
        lines = [f"<b>Siphons Detailed Report</b>\n"]
        lines.append(f"Total: {len(siphons)} siphon(s) found\n")
        
        for i, siphon in enumerate(siphons[:10], 1):
            places = siphon.get('places', [])
            lines.append(f"\n<b>Siphon #{i}</b>")
            lines.append(f"  Places ({len(places)}):")
            for place in places[:15]:
                lines.append(f"    • {place}")
            if len(places) > 15:
                lines.append(f"    ... and {len(places) - 15} more places")
        
        if len(siphons) > 10:
            lines.append(f"\n... and {len(siphons) - 10} more siphons")
        
        return '\n'.join(lines)
    
    def _format_traps_detail(self, result) -> str:
        """Format detailed report for Traps."""
        data = result.data if hasattr(result, 'data') else {}
        traps = data.get('traps', [])
        
        if not traps:
            return "<b>No traps found</b>"
        
        lines = [f"<b>Traps Detailed Report</b>\n"]
        lines.append(f"Total: {len(traps)} trap(s) found\n")
        
        for i, trap in enumerate(traps[:10], 1):
            places = trap.get('places', [])
            lines.append(f"\n<b>Trap #{i}</b>")
            lines.append(f"  Places ({len(places)}):")
            for place in places[:15]:
                lines.append(f"    • {place}")
            if len(places) > 15:
                lines.append(f"    ... and {len(places) - 15} more places")
        
        if len(traps) > 10:
            lines.append(f"\n... and {len(traps) - 10} more traps")
        
        return '\n'.join(lines)
    
    # Simplified placeholders for other analyzers
    def _format_cycles_detail(self, result) -> str:
        return "<b>Cycles Detailed Report</b>\n\n(Full implementation pending)"
    
    def _format_paths_detail(self, result) -> str:
        return "<b>Paths Detailed Report</b>\n\n(Full implementation pending)"
    
    def _format_hubs_detail(self, result) -> str:
        return "<b>Hubs Detailed Report</b>\n\n(Full implementation pending)"
    
    def _format_reachability_detail(self, result) -> str:
        return "<b>Reachability Detailed Report</b>\n\n(Full implementation pending)"
    
    def _format_boundedness_detail(self, result) -> str:
        return "<b>Boundedness Detailed Report</b>\n\n(Full implementation pending)"
    
    def _format_liveness_detail(self, result) -> str:
        return "<b>Liveness Detailed Report</b>\n\n(Full implementation pending)"
    
    def _format_deadlocks_detail(self, result) -> str:
        return "<b>Deadlocks Detailed Report</b>\n\n(Full implementation pending)"
    
    def _format_fairness_detail(self, result) -> str:
        return "<b>Fairness Detailed Report</b>\n\n(Full implementation pending)"

