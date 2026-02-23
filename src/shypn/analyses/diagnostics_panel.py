#!/usr/bin/env python3
"""Diagnostics Panel - Real-time runtime diagnostics for selected transitions.

This panel displays runtime execution metrics during simulation, including:
- Locality structure and analysis
- Recent firing events
- Throughput calculations  
- Dynamic enablement state
- Token flow visualization

Unlike the static transition properties dialog, this panel updates in real-time
during simulation and is always accessible in the right panel.

Example:
    # In right_panel_loader
    panel = DiagnosticsPanel(model, data_collector)
    panel.set_transition(transition)
    # Panel now shows real-time diagnostics
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, Pango

from shypn.diagnostic import (
    LocalityDetector,
    LocalityAnalyzer, 
    LocalityRuntimeAnalyzer
)


class DiagnosticsPanel:
    """Panel for displaying real-time runtime diagnostics.
    
    This panel provides:
    - Locality structure detection
    - Static analysis (tokens, weights, balance)
    - Runtime metrics (events, throughput, enablement)
    - Automatic updates during simulation
    
    The panel is designed to be embedded in the right panel's notebook
    and updates continuously while simulation is running.
    
    Attributes:
        model: PetriNetModel instance
        data_collector: SimulationDataCollector for runtime data
        container: GTK Box container from UI
        detector: LocalityDetector for structure detection
        analyzer: LocalityAnalyzer for static analysis
        runtime_analyzer: LocalityRuntimeAnalyzer for runtime metrics
        current_transition: Currently selected transition
        update_timer: GLib timeout ID for periodic updates
    
    Example:
        panel = DiagnosticsPanel(model, data_collector)
        container = builder.get_object('diagnostics_content_container')
        panel.setup(container)
        panel.set_transition(transition)
    """
    
    def __init__(self, model, data_collector):
        """Initialize diagnostics panel.
        
        Args:
            model: PetriNetModel instance
            data_collector: SimulationDataCollector instance
        """
        self.model = model
        self.data_collector = data_collector
        self.container = None
        
        # Analysis components
        if model:
            self.detector = LocalityDetector(model)
            self.analyzer = LocalityAnalyzer(model)
            self.runtime_analyzer = LocalityRuntimeAnalyzer(model, data_collector) if data_collector else None
        else:
            self.detector = None
            self.analyzer = None
            self.runtime_analyzer = None
        
        # State
        self.current_transition = None
        self.locality = None
        self.update_timer = None
        self.auto_tracking_enabled = False  # Track if auto-tracking is active
        
        # Cache for change detection (Phase 1)
        self._last_diagnostics_hash = None
        self._cached_sections = {
            'header': '',
            'structure': '',
            'static': '',
            'runtime': ''
        }
        
        # Widgets
        self.selection_label = None
        self.textview = None
        self.placeholder_label = None
    
    def setup(self, container, selection_label=None, placeholder_label=None):
        """Setup panel with GTK container from UI.
        
        Args:
            container: GtkBox container for diagnostics content
            selection_label: Optional GtkLabel for showing selection info
            placeholder_label: Optional GtkLabel placeholder to remove
        """
        self.container = container
        self.selection_label = selection_label
        self.placeholder_label = placeholder_label
        
        # Remove placeholder if present
        if placeholder_label:
            parent = placeholder_label.get_parent()
            if parent:
                parent.remove(placeholder_label)
        
        # Find the existing TextView in the container (created by category)
        # Look for a ScrolledWindow that contains a TextView
        self.textview = None
        for child in container.get_children():
            if isinstance(child, Gtk.ScrolledWindow):
                # Check if it has a TextView child
                scrolled_child = child.get_child()
                if isinstance(scrolled_child, Gtk.TextView):
                    self.textview = scrolled_child
                    break
        
        # If no TextView found, create one (fallback)
        if not self.textview:
            self.textview = Gtk.TextView()
            self.textview.set_editable(False)
            self.textview.set_cursor_visible(False)
            self.textview.set_wrap_mode(Gtk.WrapMode.WORD)
            self.textview.set_left_margin(10)
            self.textview.set_right_margin(10)
            self.textview.set_top_margin(0)
            self.textview.set_bottom_margin(10)
            
            # Monospace font for better alignment
            font_desc = Pango.FontDescription("Monospace 10")
            self.textview.override_font(font_desc)
            
            # Add to container
            self.container.pack_start(self.textview, True, True, 0)
        else:
            # Use existing TextView but update its properties
            self.textview.set_left_margin(10)
            self.textview.set_right_margin(10)
            self.textview.set_top_margin(0)
            self.textview.set_bottom_margin(10)
            
            # Update font
            font_desc = Pango.FontDescription("Monospace 10")
            self.textview.override_font(font_desc)
        
        self.container.show_all()
        
        # Show initial message and enable auto-tracking
        self._show_auto_tracking_message()
        self.enable_auto_tracking()
    
    def set_transition(self, transition):
        """Set transition to display diagnostics for.
        
        Args:
            transition: Transition object to analyze
        """
        if transition is None:
            self.current_transition = None
            self.locality = None
            self._show_no_transition()
            self._stop_updates()
            self.auto_tracking_enabled = False  # Disable auto-tracking when cleared
            self._last_diagnostics_hash = None  # Reset hash
            return
        
        self.current_transition = transition
        self.auto_tracking_enabled = False  # Manual selection disables auto-tracking
        self._last_diagnostics_hash = None  # Reset hash to force initial update
        
        # Clear cached sections for fresh display
        self._cached_sections = {
            'header': '',
            'structure': '',
            'static': '',
            'runtime': ''
        }
        
        # Update selection label if available
        if self.selection_label:
            transition_name = getattr(transition, 'name', f'T{transition.id}')
            self.selection_label.set_markup(
                f"<b>Diagnostics for:</b> {transition_name}"
            )
        
        # Detect locality
        if self.detector:
            self.locality = self.detector.get_locality_for_transition(transition)
        
        # Initial update
        self._update_display()
        
        # Start periodic updates (every 500ms) - only if not already running
        if not self.update_timer:
            self._start_updates()
    
    def _update_display(self):
        """Update diagnostics display with differential updates (Phase 2)."""
        if not self.current_transition:
            self._show_no_transition()
            return
        
        if not self.locality or not self.locality.is_valid:
            self._show_invalid_locality()
            return
        
        # Generate sections separately
        new_sections = {
            'header': self._generate_header_section(),
            'structure': self._generate_structure_section(),
            'static': self._generate_static_section(),
            'runtime': self._generate_runtime_section()
        }
        
        # Check if any section changed and update differentially
        has_changes = False
        for section_name, new_content in new_sections.items():
            if new_content != self._cached_sections[section_name]:
                has_changes = True
                self._cached_sections[section_name] = new_content
        
        # Only update text if something changed
        if has_changes:
            # Combine all sections
            full_text = '\n'.join(new_sections.values())
            self._update_text_preserve_scroll(full_text)
    
    def _generate_header_section(self):
        """Generate header section text."""
        transition_name = getattr(self.current_transition, 'name', f'T{self.current_transition.id}')
        transition_type = getattr(self.current_transition, 'transition_type', 'unknown')
        
        lines = []
        lines.append("╔" + "═" * 58 + "╗")
        lines.append(f"║ Diagnostics: {transition_name:<45} ║")
        lines.append(f"║ Type: {transition_type:<50} ║")
        lines.append("╚" + "═" * 58 + "╝")
        lines.append("")
        if self.auto_tracking_enabled:
            lines.append("ℹ Auto-tracking: Showing most recently fired transition")
        lines.append("")
        
        return '\n'.join(lines)
    
    def _generate_structure_section(self):
        """Generate locality structure section text."""
        if not self.locality:
            return ""
        
        lines = []
        lines.append("━━━ Locality Structure ━━━")
        lines.append(self.locality.get_summary())
        lines.append("")
        
        return '\n'.join(lines)
    
    def _generate_static_section(self):
        """Generate static analysis section text."""
        if not self.analyzer or not self.locality:
            return ""
        
        analysis = self.analyzer.analyze_locality(self.locality)
        
        lines = []
        lines.append("━━━ Static Analysis ━━━")
        lines.append(f"  Places:           {analysis['place_count']} ({analysis['input_count']} in, {analysis['output_count']} out)")
        lines.append(f"  Arcs:             {analysis['arc_count']}")
        lines.append(f"  Arc Weight:       {analysis['total_weight']:.1f}")
        lines.append("")
        lines.append(f"  Input Tokens:     {analysis['input_tokens']}")
        lines.append(f"  Output Tokens:    {analysis['output_tokens']}")
        lines.append(f"  Token Balance:    {analysis['token_balance']:+.0f}")
        lines.append("")
        
        can_fire = analysis['can_fire']
        fire_icon = "✓" if can_fire else "✗"
        fire_status = "Yes" if can_fire else "No (insufficient tokens)"
        lines.append(f"  Can Fire (static): {fire_icon} {fire_status}")
        lines.append("")
        
        return '\n'.join(lines)
    
    def _generate_runtime_section(self):
        """Generate runtime diagnostics section text."""
        lines = []
        lines.append("━━━ Runtime Diagnostics ━━━")
        
        if not self.runtime_analyzer:
            lines.append("  No data collector available")
            return '\n'.join(lines)
        
        try:
            # Pass the full transition object, not just the ID
            diag = self.runtime_analyzer.get_transition_diagnostics(
                self.current_transition,
                window=10
            )
            
            # Event statistics
            total = diag.get('total_events', 0)
            lines.append(f"  Total Events:     {total}")
            
            if total > 0:
                last_time = diag.get('last_event_time', 0.0)
                lines.append(f"  Last Event:       t={last_time:.2f}s")
                lines.append(f"  Throughput:       {diag['throughput']:.3f} fires/sec")
            else:
                lines.append("  Status:           No firing events recorded")
            
            lines.append("")
            
            # Recent events list
            if diag.get('recent_events'):
                lines.append("━━━ Recent Events (last 5) ━━━")
                for i, event in enumerate(diag['recent_events'][-5:], 1):
                    time_val = event.get('time', 0.0)
                    event_type = event.get('type', 'unknown')
                    lines.append(f"  {i}. t={time_val:6.2f}s  {event_type}")
                
                if len(diag['recent_events']) > 5:
                    lines.append(f"  ... and {len(diag['recent_events']) - 5} more")
        
        except Exception as e:
            lines.append(f"  Error: {str(e)}")
        
        return '\n'.join(lines)
    
    def _update_text_preserve_scroll(self, text):
        """Update TextView text while preserving scroll position.
        
        Args:
            text: New text to display
        """
        if not self.textview:
            return
        
        # Get the parent ScrolledWindow
        parent = self.textview.get_parent()
        if not isinstance(parent, Gtk.ScrolledWindow):
            # Fallback: just update text without preserving scroll
            buffer = self.textview.get_buffer()
            buffer.set_text(text)
            return
        
        # Get current scroll position
        vadjustment = parent.get_vadjustment()
        old_value = vadjustment.get_value()
        old_upper = vadjustment.get_upper()
        
        # Update text
        buffer = self.textview.get_buffer()
        buffer.set_text(text)
        
        # Wait for text to be laid out, then restore scroll position
        def restore_scroll():
            new_upper = vadjustment.get_upper()
            
            # If we were at the bottom before, stay at the bottom
            # (allows auto-scrolling for new content)
            if old_value >= old_upper - vadjustment.get_page_size() - 1:
                vadjustment.set_value(new_upper - vadjustment.get_page_size())
            else:
                # Otherwise preserve the old position
                vadjustment.set_value(old_value)
            
            return False  # Don't repeat
        
        # Schedule scroll restoration after layout
        GLib.idle_add(restore_scroll)
    
    def _show_no_transition(self):
        """Show message when no transition selected."""
        if self.selection_label:
            self.selection_label.set_text("No transition selected")
        
        if self.textview:
            buffer = self.textview.get_buffer()
            buffer.set_text("Select a transition to view diagnostics.\n\nYou can:\n  • Search for a transition in the Transitions tab\n  • Right-click a transition and select 'Add to Analysis'\n  • Click on a transition in the canvas")
    
    def _show_invalid_locality(self):
        """Show message for invalid locality."""
        transition_name = getattr(self.current_transition, 'name', f'T{self.current_transition.id}')
        
        if self.selection_label:
            self.selection_label.set_markup(f"<b>Diagnostics for:</b> {transition_name}")
        
        if self.textview:
            text = []
            text.append(f"Transition: {transition_name}")
            text.append("")
            text.append("⚠ This transition does not form a valid locality.")
            text.append("")
            text.append("A valid locality requires:")
            text.append("  • At least 1 input place")
            text.append("  • At least 1 output place")
            text.append("")
            
            if self.locality:
                text.append("Current state:")
                text.append(f"  • Input places:  {len(self.locality.input_places)}")
                text.append(f"  • Output places: {len(self.locality.output_places)}")
            
            buffer = self.textview.get_buffer()
            buffer.set_text("\n".join(text))
    
    def _start_updates(self):
        """Start periodic display updates."""
        self._stop_updates()
        # Update every 500ms (2 times per second)
        self.update_timer = GLib.timeout_add(500, self._on_update_timer)
    
    def enable_auto_tracking(self):
        """Enable automatic tracking of active transitions.
        
        When enabled, the panel will automatically switch to show
        diagnostics for the most recently fired transition.
        """
        self.auto_tracking_enabled = True
        if not self.update_timer:
            self._start_updates()
        if not self.current_transition:
            self._show_auto_tracking_message()
    
    def _show_auto_tracking_message(self):
        """Show message that auto-tracking is active."""
        if self.selection_label:
            self.selection_label.set_markup(
                "<b>Auto-tracking:</b> Waiting for transition activity..."
            )
        
        if self.textview:
            buffer = self.textview.get_buffer()
            buffer.set_text(
                "Auto-tracking enabled.\n\n"
                "The diagnostics panel will automatically show metrics for\n"
                "the most recently fired transition during simulation.\n\n"
                "Or you can:\n"
                "  • Right-click a transition and select 'Add to Analysis'\n"
                "  • Search for a transition in the Transitions tab\n\n"
                "Waiting for simulation activity..."
            )
    
    def _stop_updates(self):
        """Stop periodic display updates."""
        if self.update_timer:
            GLib.source_remove(self.update_timer)
            self.update_timer = None
    
    def _compute_diagnostics_hash(self):
        """Compute hash of current diagnostic data for change detection.
        
        Returns:
            int: Hash of relevant diagnostic fields, or None if no data
        """
        if not self.runtime_analyzer or not self.current_transition:
            # Hash static data if available
            if self.locality:
                return hash((
                    self.current_transition.id,
                    len(self.locality.input_places),
                    len(self.locality.output_places),
                    len(self.locality.catalyst_places)
                ))
            return None
        
        try:
            diag = self.runtime_analyzer.get_transition_diagnostics(
                self.current_transition,
                window=10
            )
            
            # Hash relevant runtime fields
            recent_times = tuple(
                e.get('time', 0) 
                for e in diag.get('recent_events', [])[-5:]
            )
            
            return hash((
                diag.get('total_events', 0),
                round(diag.get('last_event_time', 0), 3),  # Round to avoid float precision issues
                round(diag.get('throughput', 0), 3),
                recent_times
            ))
        except Exception:
            # If error computing hash, return None to force update
            return None
    
    def _on_update_timer(self):
        """Timer callback for periodic updates with change detection.
        
        Returns:
            bool: True to continue timer, False to stop
        """
        if self.current_transition:
            # Only auto-update if auto-tracking is enabled
            if self.auto_tracking_enabled:
                self._auto_update_active_transition()
            
            # Phase 1: Only update if data actually changed
            new_hash = self._compute_diagnostics_hash()
            if new_hash != self._last_diagnostics_hash:
                self._update_display()
                self._last_diagnostics_hash = new_hash
            
            return True  # Continue timer
        else:
            # Try to auto-select a transition if auto-tracking is enabled
            if self.auto_tracking_enabled:
                self._auto_select_transition()
            return True  # Continue checking
    
    def _auto_update_active_transition(self):
        """Auto-update to the most recently fired transition if available.
        
        This checks all transitions being plotted and switches to show
        diagnostics for the most recently active one.
        """
        if not self.runtime_analyzer or not self.model:
            return
        
        try:
            # Get all transitions from the model
            transitions = getattr(self.model, 'transitions', [])
            if not transitions:
                return
            
            # Find the most recently fired transition
            most_recent_time = -1
            most_recent_transition = None
            
            for transition in transitions:
                try:
                    diag = self.runtime_analyzer.get_transition_diagnostics(transition, window=1)
                    if diag.get('last_fired') is not None:
                        if diag['last_fired'] > most_recent_time:
                            most_recent_time = diag['last_fired']
                            most_recent_transition = transition
                except Exception:
                    continue
            
            # If we found a more recently fired transition, switch to it
            if most_recent_transition and most_recent_transition != self.current_transition:
                # Check if it fired in the last 2 seconds (active now)
                current_time = self.runtime_analyzer._get_logical_time()
                time_diff = current_time - most_recent_time
                
                if time_diff < 2.0:
                    self.current_transition = most_recent_transition
                    if self.selection_label:
                        transition_name = getattr(most_recent_transition, 'name', f'T{most_recent_transition.id}')
                        self.selection_label.set_markup(
                            f"<b>Active:</b> {transition_name} (auto-tracking)"
                        )
                    # Update locality
                    if self.detector:
                        self.locality = self.detector.get_locality_for_transition(most_recent_transition)
        except Exception:
            # Silently fail - don't disrupt updates
            pass
    
    def _auto_select_transition(self):
        """Auto-select a transition if none is currently selected.
        
        Looks for any transition that has fired recently and selects it.
        """
        if not self.model or not self.runtime_analyzer:
            return
        
        try:
            transitions = getattr(self.model, 'transitions', [])
            if not transitions:
                return
            
            # Find any transition that has fired
            found_any = False
            for transition in transitions:
                try:
                    transition_name = getattr(transition, 'name', f'T{transition.id}')
                    diag = self.runtime_analyzer.get_transition_diagnostics(transition, window=1)
                    if diag.get('last_fired') is not None:
                        # Found a transition with activity, select it
                        found_any = True
                        transition_name = getattr(transition, 'name', f'T{transition.id}')
                        
                        # Set transition directly without calling set_transition()
                        # to avoid disabling auto-tracking
                        self.current_transition = transition
                        if self.detector:
                            self.locality = self.detector.get_locality_for_transition(transition)
                        if self.selection_label:
                            self.selection_label.set_markup(
                                f"<b>Active:</b> {transition_name} (auto-tracking)"
                            )
                        break
                except Exception as e:
                    import traceback
                    traceback.print_exc()
                    continue
            
            if not found_any and len(transitions) > 0:
                pass  # No activity found yet
        except (AttributeError, TypeError, KeyError) as e:
            self.logger.debug(f"Failed to search for transition activity in diagnostics panel: {e}")
    
    def clear(self):
        """Clear diagnostics display."""
        self.set_transition(None)
    
    def set_model(self, model):
        """Update model reference.
        
        Args:
            model: New PetriNetModel instance
        """
        self.model = model
        if model:
            self.detector = LocalityDetector(model)
            self.analyzer = LocalityAnalyzer(model)
            if self.data_collector:
                self.runtime_analyzer = LocalityRuntimeAnalyzer(model, self.data_collector)
        else:
            self.detector = None
            self.analyzer = None
            self.runtime_analyzer = None
        
        # Refresh display if we have a transition
        if self.current_transition:
            self.set_transition(self.current_transition)
    
    def set_data_collector(self, data_collector):
        """Update data collector reference.
        
        Args:
            data_collector: New SimulationDataCollector instance
        """
        self.data_collector = data_collector
        if self.model and data_collector:
            self.runtime_analyzer = LocalityRuntimeAnalyzer(self.model, data_collector)
        else:
            self.runtime_analyzer = None
        
        # Refresh display if we have a transition
        if self.current_transition:
            self._update_display()


__all__ = ['DiagnosticsPanel']
