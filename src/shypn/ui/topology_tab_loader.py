"""Topology tab loaders for property dialogs.

This module provides UI loaders for topology analysis tabs, decoupling
UI definitions (GTK .ui files) from business logic (topology analyzers).

Architecture:
- UI definitions: /ui/topology_tab_*.ui (GTK XML files)
- UI loaders: /src/shypn/ui/topology_tab_loader.py (this file)
- Business logic: /src/shypn/topology/* (analyzer implementations)

This design ensures:
1. Clean separation of concerns
2. Reusable UI components
3. Testable business logic
4. Wayland compatibility (proper widget lifecycle)
5. Easy SwissKnifePalette integration

Author: Simão Eugénio
Date: 2025-10-19
"""

import os
from typing import Optional, Dict, Any
from abc import ABC, abstractmethod

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk


class TopologyTabLoader(ABC):
    """Base class for topology tab loaders.
    
    Handles loading GTK UI files and populating topology information
    in property dialogs. Subclasses implement element-specific analysis
    (places, transitions, arcs).
    
    Attributes:
        builder: GTK Builder for loading UI file
        root_widget: Root container widget from UI file
        model: Petri net model for topology analysis
        element_id: ID of the element being analyzed
        ui_file: Path to GTK UI file
        highlighting_manager: Optional manager for canvas highlighting
    """
    
    def __init__(
        self,
        model,
        element_id: str,
        ui_dir: Optional[str] = None,
        highlighting_manager=None
    ):
        """Initialize topology tab loader.
        
        Args:
            model: Petri net model containing the element
            element_id: ID of the element to analyze
            ui_dir: Directory containing UI files (defaults to /ui)
            highlighting_manager: Optional HighlightingManager for canvas integration
        """
        self.model = model
        self.element_id = element_id
        self.highlighting_manager = highlighting_manager
        
        # Determine UI directory
        if ui_dir is None:
            # Default to /ui directory at project root
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
            ui_dir = os.path.join(project_root, 'ui')
        
        self.ui_dir = ui_dir
        self.ui_file = os.path.join(ui_dir, self._get_ui_filename())
        
        # GTK builder and widgets
        self.builder = None
        self.root_widget = None
        
        # Widget references (set by subclasses)
        self.cycles_label = None
        self.paths_label = None
        self.hub_label = None
        self.p_inv_label = None
        self.t_inv_label = None
        self.arc_info_label = None
        self.critical_label = None
        
        # Action buttons
        self.highlight_button = None
        self.export_button = None
        
        # Load UI
        self._load_ui()
        self._setup_widgets()
        self._connect_signals()
    
    @abstractmethod
    def _get_ui_filename(self) -> str:
        """Get the UI filename for this loader type.
        
        Returns:
            UI filename (e.g., 'topology_tab_place.ui')
        """
        pass
    
    @abstractmethod
    def _get_root_widget_id(self) -> str:
        """Get the root widget ID from the UI file.
        
        Returns:
            Root widget ID (e.g., 'place_topology_tab_root')
        """
        pass
    
    def _load_ui(self):
        """Load GTK UI file.
        
        Raises:
            FileNotFoundError: If UI file doesn't exist
            RuntimeError: If UI loading fails
        """
        if not os.path.exists(self.ui_file):
            raise FileNotFoundError(f"UI file not found: {self.ui_file}")
        
        try:
            self.builder = Gtk.Builder()
            self.builder.add_from_file(self.ui_file)
            self.root_widget = self.builder.get_object(self._get_root_widget_id())
            
            if self.root_widget is None:
                raise RuntimeError(
                    f"Root widget '{self._get_root_widget_id()}' not found in {self.ui_file}"
                )
        except Exception as e:
            raise RuntimeError(f"Failed to load UI file {self.ui_file}: {e}")
    
    def _setup_widgets(self):
        """Setup widget references from builder.
        
        Subclasses override to get element-specific widgets.
        """
        # Common widgets (may not exist in all UI files)
        self.cycles_label = self.builder.get_object('topology_cycles_label')
        self.paths_label = self.builder.get_object('topology_paths_label')
        self.hub_label = self.builder.get_object('topology_hub_label')
        self.p_inv_label = self.builder.get_object('topology_p_invariants_label')
        self.t_inv_label = self.builder.get_object('topology_t_invariants_label')
        self.arc_info_label = self.builder.get_object('topology_arc_info_label')
        self.critical_label = self.builder.get_object('topology_critical_label')
        
        # Action buttons
        self.highlight_button = self.builder.get_object('highlight_button')
        self.export_button = self.builder.get_object('export_button')
    
    def _connect_signals(self):
        """Connect signal handlers for buttons.
        
        Wayland-compatible signal connection with proper cleanup.
        """
        if self.highlight_button:
            self.highlight_button.connect('clicked', self._on_highlight_clicked)
        
        if self.export_button:
            self.export_button.connect('clicked', self._on_export_clicked)
    
    def _on_highlight_clicked(self, button):
        """Handle highlight button click.
        
        Delegates to highlighting manager if available.
        
        Args:
            button: GTK button that was clicked
        """
        if self.highlighting_manager:
            self.highlighting_manager.highlight_element_topology(
                self.element_id,
                self._get_element_type()
            )
        else:
            # Show info dialog if highlighting not available
            dialog = Gtk.MessageDialog(
                transient_for=button.get_toplevel(),
                flags=0,
                message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.OK,
                text="Highlighting not available"
            )
            dialog.format_secondary_text(
                "Canvas highlighting will be available in a future version."
            )
            dialog.run()
            dialog.destroy()
    
    def _on_export_clicked(self, button):
        """Handle export button click.
        
        Opens file chooser and exports topology analysis.
        
        Args:
            button: GTK button that was clicked
        """
        dialog = Gtk.FileChooserDialog(
            title="Export Topology Analysis",
            parent=button.get_toplevel(),
            action=Gtk.FileChooserAction.SAVE
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_SAVE, Gtk.ResponseType.OK
        )
        
        # Add file filters
        filter_text = Gtk.FileFilter()
        filter_text.set_name("Text files")
        filter_text.add_mime_type("text/plain")
        dialog.add_filter(filter_text)
        
        filter_json = Gtk.FileFilter()
        filter_json.set_name("JSON files")
        filter_json.add_mime_type("application/json")
        dialog.add_filter(filter_json)
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            filename = dialog.get_filename()
            self._export_topology_data(filename)
        
        dialog.destroy()
    
    @abstractmethod
    def _get_element_type(self) -> str:
        """Get element type for highlighting.
        
        Returns:
            Element type ('place', 'transition', or 'arc')
        """
        pass
    
    def _export_topology_data(self, filename: str):
        """Export topology analysis data to file.
        
        Args:
            filename: Output filename
        """
        # Placeholder - implement in Phase 5
        with open(filename, 'w') as f:
            f.write(f"Topology Analysis for {self._get_element_type()} {self.element_id}\n")
            f.write("=" * 60 + "\n\n")
            f.write("Export functionality coming in Phase 5\n")
    
    @abstractmethod
    def populate(self):
        """Populate topology information in the UI.
        
        Runs topology analyzers and updates labels with results.
        Subclasses implement element-specific analysis.
        """
        pass
    
    def get_root_widget(self) -> Gtk.Widget:
        """Get the root widget for embedding in dialogs.
        
        Returns:
            Root GTK widget (usually a GtkBox)
        """
        return self.root_widget
    
    def destroy(self):
        """Clean up resources and widgets.
        
        Ensures proper widget lifecycle for Wayland compatibility.
        Prevents orphaned widgets that can cause focus issues.
        """
        # Clear widget references
        self.cycles_label = None
        self.paths_label = None
        self.hub_label = None
        self.p_inv_label = None
        self.t_inv_label = None
        self.arc_info_label = None
        self.critical_label = None
        self.highlight_button = None
        self.export_button = None
        
        # Clear builder (this releases all widgets)
        if self.builder:
            self.builder = None
        
        # Clear root widget
        if self.root_widget:
            self.root_widget = None
        
        # Clear model reference
        self.model = None
        self.highlighting_manager = None


class PlaceTopologyTabLoader(TopologyTabLoader):
    """Topology tab loader for places (metabolites).
    
    Displays:
    - Cycles containing the place
    - P-invariants (conservation laws) involving the place
    - Paths passing through the place
    - Hub status (degree, centrality)
    """
    
    def _get_ui_filename(self) -> str:
        return 'topology_tab_place.ui'
    
    def _get_root_widget_id(self) -> str:
        return 'place_topology_tab_root'
    
    def _get_element_type(self) -> str:
        return 'place'
    
    def populate(self):
        """Populate place topology information."""
        if not self.model:
            return
        
        try:
            from shypn.topology.graph import CycleAnalyzer, PathAnalyzer
            from shypn.topology.structural import PInvariantAnalyzer
            from shypn.topology.network import HubAnalyzer
            
            # Analyze cycles
            if self.cycles_label:
                try:
                    cycle_analyzer = CycleAnalyzer(self.model)
                    cycles = cycle_analyzer.find_cycles_containing_node(self.element_id)
                    
                    if cycles:
                        text = f"Part of {len(cycles)} cycle(s):\n\n"
                        for i, cycle in enumerate(cycles[:5], 1):
                            names = ' → '.join(cycle['names'][:10])
                            if len(cycle['names']) > 10:
                                names += ' ...'
                            text += f"{i}. {names}\n"
                            text += f"   Length: {cycle['length']}, Type: {cycle['type']}\n\n"
                        if len(cycles) > 5:
                            text += f"... and {len(cycles) - 5} more cycle(s)\n"
                        self.cycles_label.set_text(text.strip())
                    else:
                        self.cycles_label.set_text("Not part of any cycles")
                except Exception as e:
                    self.cycles_label.set_text(f"Analysis error: {str(e)}")
            
            # Analyze P-invariants
            if self.p_inv_label:
                try:
                    p_inv_analyzer = PInvariantAnalyzer(self.model)
                    invariants = p_inv_analyzer.find_invariants_containing_place(self.element_id)
                    
                    if invariants:
                        text = f"In {len(invariants)} P-invariant(s):\n\n"
                        for i, inv in enumerate(invariants[:5], 1):
                            text += f"{i}. {inv['sum_expression']}\n"
                            text += f"   Conserved value: {inv['conserved_value']}\n\n"
                        if len(invariants) > 5:
                            text += f"... and {len(invariants) - 5} more invariant(s)\n"
                        self.p_inv_label.set_text(text.strip())
                    else:
                        self.p_inv_label.set_text("Not in any P-invariants")
                except Exception as e:
                    self.p_inv_label.set_text(f"Analysis error: {str(e)}")
            
            # Analyze paths
            if self.paths_label:
                try:
                    path_analyzer = PathAnalyzer(self.model)
                    path_result = path_analyzer.find_paths_through_node(self.element_id, max_paths=50)
                    
                    if path_result.success and path_result.data.get('paths'):
                        paths = path_result.data['paths']
                        path_count = len(paths)
                        if path_count >= 50:
                            text = f"≥50 paths pass through this place\n(limited to first 50)"
                        else:
                            avg_length = sum(len(p) for p in paths) / len(paths) if paths else 0
                            text = f"{path_count} path(s) pass through this place\n"
                            text += f"Average path length: {avg_length:.1f} nodes"
                        self.paths_label.set_text(text)
                    else:
                        self.paths_label.set_text("Not in any paths")
                except Exception as e:
                    self.paths_label.set_text(f"Analysis error: {str(e)}")
            
            # Analyze hub status
            if self.hub_label:
                try:
                    hub_analyzer = HubAnalyzer(self.model)
                    hub_result = hub_analyzer.get_node_degree_info(self.element_id)
                    
                    if hub_result.success:
                        hub_data = hub_result.data
                        is_hub = hub_data.get('is_hub', False)
                        degree = hub_data.get('degree', 0)
                        in_deg = hub_data.get('in_degree', 0)
                        out_deg = hub_data.get('out_degree', 0)
                        
                        if is_hub:
                            text = f"⭐ HUB (degree {degree})\n"
                            text += f"Incoming: {in_deg} arcs, Outgoing: {out_deg} arcs"
                        else:
                            text = f"Regular place (degree {degree})\n"
                            text += f"Incoming: {in_deg} arcs, Outgoing: {out_deg} arcs"
                        self.hub_label.set_text(text)
                    else:
                        self.hub_label.set_text("Unable to analyze hub status")
                except Exception as e:
                    self.hub_label.set_text(f"Analysis error: {str(e)}")
        
        except ImportError:
            # Topology module not available
            pass


class TransitionTopologyTabLoader(TopologyTabLoader):
    """Topology tab loader for transitions (reactions).
    
    Displays:
    - Cycles containing the transition
    - T-invariants (reproducible sequences) involving the transition
    - Paths passing through the transition
    - Hub status (degree, centrality)
    """
    
    def _get_ui_filename(self) -> str:
        return 'topology_tab_transition.ui'
    
    def _get_root_widget_id(self) -> str:
        return 'transition_topology_tab_root'
    
    def _get_element_type(self) -> str:
        return 'transition'
    
    def populate(self):
        """Populate transition topology information."""
        if not self.model:
            return
        
        try:
            from shypn.topology.graph import CycleAnalyzer, PathAnalyzer
            from shypn.topology.network import HubAnalyzer
            
            # Analyze cycles (same as places)
            if self.cycles_label:
                try:
                    cycle_analyzer = CycleAnalyzer(self.model)
                    cycles = cycle_analyzer.find_cycles_containing_node(self.element_id)
                    
                    if cycles:
                        text = f"Part of {len(cycles)} cycle(s):\n\n"
                        for i, cycle in enumerate(cycles[:5], 1):
                            names = ' → '.join(cycle['names'][:10])
                            if len(cycle['names']) > 10:
                                names += ' ...'
                            text += f"{i}. {names}\n"
                            text += f"   Length: {cycle['length']}, Type: {cycle['type']}\n\n"
                        if len(cycles) > 5:
                            text += f"... and {len(cycles) - 5} more cycle(s)\n"
                        self.cycles_label.set_text(text.strip())
                    else:
                        self.cycles_label.set_text("Not part of any cycles")
                except Exception as e:
                    self.cycles_label.set_text(f"Analysis error: {str(e)}")
            
            # T-invariants (placeholder for Tier 2)
            if self.t_inv_label:
                self.t_inv_label.set_text("T-invariants not yet implemented (Tier 2)")
            
            # Analyze paths
            if self.paths_label:
                try:
                    path_analyzer = PathAnalyzer(self.model)
                    path_result = path_analyzer.find_paths_through_node(self.element_id, max_paths=50)
                    
                    if path_result.success and path_result.data.get('paths'):
                        paths = path_result.data['paths']
                        path_count = len(paths)
                        if path_count >= 50:
                            text = f"≥50 paths pass through this transition\n(limited to first 50)"
                        else:
                            avg_length = sum(len(p) for p in paths) / len(paths) if paths else 0
                            text = f"{path_count} path(s) pass through this transition\n"
                            text += f"Average path length: {avg_length:.1f} nodes"
                        self.paths_label.set_text(text)
                    else:
                        self.paths_label.set_text("Not in any paths")
                except Exception as e:
                    self.paths_label.set_text(f"Analysis error: {str(e)}")
            
            # Analyze hub status
            if self.hub_label:
                try:
                    hub_analyzer = HubAnalyzer(self.model)
                    hub_result = hub_analyzer.get_node_degree_info(self.element_id)
                    
                    if hub_result.success:
                        hub_data = hub_result.data
                        is_hub = hub_data.get('is_hub', False)
                        degree = hub_data.get('degree', 0)
                        in_deg = hub_data.get('in_degree', 0)
                        out_deg = hub_data.get('out_degree', 0)
                        
                        if is_hub:
                            text = f"⭐ HUB (degree {degree})\n"
                            text += f"Incoming: {in_deg} arcs, Outgoing: {out_deg} arcs"
                        else:
                            text = f"Regular transition (degree {degree})\n"
                            text += f"Incoming: {in_deg} arcs, Outgoing: {out_deg} arcs"
                        self.hub_label.set_text(text)
                    else:
                        self.hub_label.set_text("Unable to analyze hub status")
                except Exception as e:
                    self.hub_label.set_text(f"Analysis error: {str(e)}")
        
        except ImportError:
            pass


class ArcTopologyTabLoader(TopologyTabLoader):
    """Topology tab loader for arcs (connections).
    
    Displays:
    - Arc endpoint information (source → target)
    - Cycles containing the arc
    - Paths using the arc
    - Critical edge analysis (removal impact)
    """
    
    def _get_ui_filename(self) -> str:
        return 'topology_tab_arc.ui'
    
    def _get_root_widget_id(self) -> str:
        return 'arc_topology_tab_root'
    
    def _get_element_type(self) -> str:
        return 'arc'
    
    def populate(self):
        """Populate arc topology information."""
        if not self.model:
            return
        
        try:
            from shypn.topology.graph import CycleAnalyzer, PathAnalyzer
            
            # Arc endpoint info
            if self.arc_info_label:
                # Try to find arc in model's elements
                arc = None
                if hasattr(self.model, 'arcs'):
                    for a in self.model.arcs:
                        if hasattr(a, 'id') and a.id == self.element_id:
                            arc = a
                            break
                
                if arc:
                    source_name = arc.source.name if hasattr(arc, 'source') and arc.source else 'Unknown'
                    target_name = arc.target.name if hasattr(arc, 'target') and arc.target else 'Unknown'
                    weight = arc.weight if hasattr(arc, 'weight') else 1
                    
                    text = f"Connection: {source_name} → {target_name}\n"
                    text += f"Weight: {weight}"
                    self.arc_info_label.set_text(text)
                else:
                    self.arc_info_label.set_text("Arc information not available")
            
            # Cycles containing this arc
            if self.cycles_label:
                # Note: Need to check if arc is part of cycle
                # This requires checking if source and target are in same cycle
                self.cycles_label.set_text("Arc-level cycle analysis not yet implemented")
            
            # Paths using this arc
            if self.paths_label:
                self.paths_label.set_text("Arc-level path analysis not yet implemented")
            
            # Critical edge analysis
            if self.critical_label:
                self.critical_label.set_text("Critical edge analysis not yet implemented (Tier 3)")
        
        except Exception as e:
            # Handle any errors gracefully
            if self.arc_info_label:
                self.arc_info_label.set_text(f"Error loading arc info: {str(e)}")


def create_place_topology_tab(model, place_id: str, ui_dir: Optional[str] = None, highlighting_manager=None):
    """Factory function to create a place topology tab loader.
    
    Args:
        model: Petri net model
        place_id: Place ID to analyze
        ui_dir: Optional UI directory (defaults to /ui)
        highlighting_manager: Optional HighlightingManager
    
    Returns:
        PlaceTopologyTabLoader instance
    """
    return PlaceTopologyTabLoader(model, place_id, ui_dir, highlighting_manager)


def create_transition_topology_tab(model, transition_id: str, ui_dir: Optional[str] = None, highlighting_manager=None):
    """Factory function to create a transition topology tab loader.
    
    Args:
        model: Petri net model
        transition_id: Transition ID to analyze
        ui_dir: Optional UI directory (defaults to /ui)
        highlighting_manager: Optional HighlightingManager
    
    Returns:
        TransitionTopologyTabLoader instance
    """
    return TransitionTopologyTabLoader(model, transition_id, ui_dir, highlighting_manager)


def create_arc_topology_tab(model, arc_id: str, ui_dir: Optional[str] = None, highlighting_manager=None):
    """Factory function to create an arc topology tab loader.
    
    Args:
        model: Petri net model
        arc_id: Arc ID to analyze
        ui_dir: Optional UI directory (defaults to /ui)
        highlighting_manager: Optional HighlightingManager
    
    Returns:
        ArcTopologyTabLoader instance
    """
    return ArcTopologyTabLoader(model, arc_id, ui_dir, highlighting_manager)
