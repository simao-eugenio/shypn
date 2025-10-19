"""Canvas highlighting manager for topology visualization.

This module provides the HighlightingManager class for visually highlighting
topology features (cycles, paths, hubs) on the Petri net canvas.

Architecture:
- Highlighting manager: Coordinates visual feedback
- Canvas integration: Works with existing canvas drawing code
- SwissKnifePalette: Future palette integration for highlighting controls

Features:
- Highlight cycles on canvas
- Highlight paths (metabolic routes)
- Highlight hubs (central metabolites)
- Highlight node neighborhoods
- Multiple highlight layers (cycle + hub, etc.)
- Clear highlighting
- Export highlighted view

Author: Simão Eugénio
Date: 2025-10-19
"""

from typing import List, Dict, Optional, Set, Tuple
from enum import Enum


class HighlightType(Enum):
    """Types of highlighting available."""
    CYCLE = 'cycle'
    PATH = 'path'
    HUB = 'hub'
    P_INVARIANT = 'p_invariant'
    T_INVARIANT = 't_invariant'
    NEIGHBORHOOD = 'neighborhood'
    CUSTOM = 'custom'


class HighlightStyle:
    """Visual style for highlighted elements.
    
    Attributes:
        color: RGB tuple (0-1 range) for highlight color
        alpha: Opacity (0-1)
        line_width: Width for highlighted arcs
        glow: Whether to apply glow effect
        pulse: Whether to animate with pulsing
    """
    
    def __init__(
        self,
        color: Tuple[float, float, float] = (1.0, 0.0, 0.0),
        alpha: float = 0.7,
        line_width: float = 3.0,
        glow: bool = True,
        pulse: bool = False
    ):
        """Initialize highlight style.
        
        Args:
            color: RGB color tuple (0-1 range), default red
            alpha: Opacity 0-1, default 0.7
            line_width: Line width for arcs, default 3.0
            glow: Apply glow effect, default True
            pulse: Animate with pulsing, default False
        """
        self.color = color
        self.alpha = alpha
        self.line_width = line_width
        self.glow = glow
        self.pulse = pulse


# Predefined styles
STYLE_CYCLE = HighlightStyle(color=(0.0, 0.5, 1.0), alpha=0.6, glow=True)  # Blue
STYLE_PATH = HighlightStyle(color=(0.0, 0.8, 0.2), alpha=0.6, glow=True)   # Green
STYLE_HUB = HighlightStyle(color=(1.0, 0.8, 0.0), alpha=0.7, glow=True, pulse=True)  # Gold
STYLE_P_INV = HighlightStyle(color=(0.8, 0.0, 0.8), alpha=0.6)  # Purple
STYLE_T_INV = HighlightStyle(color=(0.8, 0.4, 0.0), alpha=0.6)  # Orange


class HighlightLayer:
    """A layer of highlighted elements.
    
    Supports multiple overlapping highlights (e.g., cycle + hub).
    
    Attributes:
        name: Layer name
        highlight_type: Type of highlighting
        style: Visual style
        nodes: Set of node IDs to highlight
        edges: Set of edge/arc IDs to highlight
        visible: Whether layer is visible
    """
    
    def __init__(
        self,
        name: str,
        highlight_type: HighlightType,
        style: HighlightStyle,
        nodes: Optional[Set[str]] = None,
        edges: Optional[Set[str]] = None
    ):
        """Initialize highlight layer.
        
        Args:
            name: Layer name (e.g., 'TCA Cycle', 'ATP Hub')
            highlight_type: Type of highlighting
            style: Visual style to apply
            nodes: Set of node IDs to highlight
            edges: Set of edge IDs to highlight
        """
        self.name = name
        self.highlight_type = highlight_type
        self.style = style
        self.nodes = nodes or set()
        self.edges = edges or set()
        self.visible = True
    
    def add_node(self, node_id: str):
        """Add a node to this layer."""
        self.nodes.add(node_id)
    
    def add_edge(self, edge_id: str):
        """Add an edge to this layer."""
        self.edges.add(edge_id)
    
    def remove_node(self, node_id: str):
        """Remove a node from this layer."""
        self.nodes.discard(node_id)
    
    def remove_edge(self, edge_id: str):
        """Remove an edge from this layer."""
        self.edges.discard(edge_id)
    
    def clear(self):
        """Clear all highlighted elements in this layer."""
        self.nodes.clear()
        self.edges.clear()
    
    def show(self):
        """Make this layer visible."""
        self.visible = True
    
    def hide(self):
        """Hide this layer."""
        self.visible = False


class HighlightingManager:
    """Manager for canvas highlighting.
    
    Coordinates visual highlighting of topology features on the Petri net canvas.
    Supports multiple overlapping highlight layers with different styles.
    
    Attributes:
        canvas: Canvas widget to highlight on
        model: Petri net model
        layers: Dictionary of highlight layers by name
        active: Whether highlighting is active
    """
    
    def __init__(self, canvas=None, model=None):
        """Initialize highlighting manager.
        
        Args:
            canvas: Canvas widget (DrawingArea or similar)
            model: Petri net model
        """
        self.canvas = canvas
        self.model = model
        self.layers: Dict[str, HighlightLayer] = {}
        self.active = True
    
    def create_layer(
        self,
        name: str,
        highlight_type: HighlightType,
        style: Optional[HighlightStyle] = None
    ) -> HighlightLayer:
        """Create a new highlight layer.
        
        Args:
            name: Layer name
            highlight_type: Type of highlighting
            style: Optional custom style (uses default if None)
        
        Returns:
            Created HighlightLayer
        """
        if style is None:
            # Use default style for type
            style_map = {
                HighlightType.CYCLE: STYLE_CYCLE,
                HighlightType.PATH: STYLE_PATH,
                HighlightType.HUB: STYLE_HUB,
                HighlightType.P_INVARIANT: STYLE_P_INV,
                HighlightType.T_INVARIANT: STYLE_T_INV,
            }
            style = style_map.get(highlight_type, HighlightStyle())
        
        layer = HighlightLayer(name, highlight_type, style)
        self.layers[name] = layer
        return layer
    
    def get_layer(self, name: str) -> Optional[HighlightLayer]:
        """Get a layer by name.
        
        Args:
            name: Layer name
        
        Returns:
            HighlightLayer or None if not found
        """
        return self.layers.get(name)
    
    def remove_layer(self, name: str):
        """Remove a layer.
        
        Args:
            name: Layer name
        """
        if name in self.layers:
            del self.layers[name]
            self._redraw_canvas()
    
    def clear_all_layers(self):
        """Clear all highlight layers."""
        self.layers.clear()
        self._redraw_canvas()
    
    def highlight_cycle(self, cycle_nodes: List[str], layer_name: Optional[str] = None):
        """Highlight a cycle on the canvas.
        
        Args:
            cycle_nodes: List of node IDs in the cycle
            layer_name: Optional layer name (auto-generated if None)
        """
        if not layer_name:
            layer_name = f"Cycle {len(self.layers) + 1}"
        
        layer = self.create_layer(layer_name, HighlightType.CYCLE)
        
        # Add nodes
        for node_id in cycle_nodes:
            layer.add_node(node_id)
        
        # Add edges between consecutive nodes
        for i in range(len(cycle_nodes)):
            source = cycle_nodes[i]
            target = cycle_nodes[(i + 1) % len(cycle_nodes)]
            edge_id = self._find_edge(source, target)
            if edge_id:
                layer.add_edge(edge_id)
        
        self._redraw_canvas()
    
    def highlight_path(self, path_nodes: List[str], layer_name: Optional[str] = None):
        """Highlight a path on the canvas.
        
        Args:
            path_nodes: List of node IDs in the path
            layer_name: Optional layer name
        """
        if not layer_name:
            layer_name = f"Path {len(self.layers) + 1}"
        
        layer = self.create_layer(layer_name, HighlightType.PATH)
        
        # Add nodes
        for node_id in path_nodes:
            layer.add_node(node_id)
        
        # Add edges between consecutive nodes
        for i in range(len(path_nodes) - 1):
            source = path_nodes[i]
            target = path_nodes[i + 1]
            edge_id = self._find_edge(source, target)
            if edge_id:
                layer.add_edge(edge_id)
        
        self._redraw_canvas()
    
    def highlight_hub(self, hub_id: str, layer_name: Optional[str] = None):
        """Highlight a hub and its connections.
        
        Args:
            hub_id: Hub node ID
            layer_name: Optional layer name
        """
        if not layer_name:
            layer_name = f"Hub: {hub_id}"
        
        layer = self.create_layer(layer_name, HighlightType.HUB)
        
        # Add hub node
        layer.add_node(hub_id)
        
        # Add all connected edges
        if self.model:
            # Get incoming arcs
            for arc in self._get_incoming_arcs(hub_id):
                layer.add_edge(arc.id if hasattr(arc, 'id') else str(arc))
            
            # Get outgoing arcs
            for arc in self._get_outgoing_arcs(hub_id):
                layer.add_edge(arc.id if hasattr(arc, 'id') else str(arc))
        
        self._redraw_canvas()
    
    def highlight_element_topology(self, element_id: str, element_type: str):
        """Highlight all topology features for an element.
        
        Called from topology tab "Highlight on Canvas" button.
        
        Args:
            element_id: Element ID
            element_type: Element type ('place', 'transition', 'arc')
        """
        # Clear existing highlights
        self.clear_all_layers()
        
        # Highlight the element itself
        layer = self.create_layer(f"{element_type.capitalize()}: {element_id}", HighlightType.CUSTOM)
        layer.add_node(element_id)
        
        # Add neighborhood
        if self.model:
            # Highlight connected nodes
            for arc in self._get_incoming_arcs(element_id):
                source_id = arc.source.id if hasattr(arc.source, 'id') else None
                if source_id:
                    layer.add_node(source_id)
                    layer.add_edge(arc.id if hasattr(arc, 'id') else str(arc))
            
            for arc in self._get_outgoing_arcs(element_id):
                target_id = arc.target.id if hasattr(arc.target, 'id') else None
                if target_id:
                    layer.add_node(target_id)
                    layer.add_edge(arc.id if hasattr(arc, 'id') else str(arc))
        
        self._redraw_canvas()
    
    def _find_edge(self, source_id: str, target_id: str) -> Optional[str]:
        """Find edge ID between two nodes.
        
        Args:
            source_id: Source node ID
            target_id: Target node ID
        
        Returns:
            Edge ID or None
        """
        if not self.model:
            return None
        
        # Search for arc connecting these nodes
        # Implementation depends on model API
        # Placeholder for now
        return f"{source_id}_to_{target_id}"
    
    def _get_incoming_arcs(self, node_id: str) -> List:
        """Get incoming arcs for a node.
        
        Args:
            node_id: Node ID
        
        Returns:
            List of arc objects
        """
        if not self.model:
            return []
        
        # Placeholder - implement based on model API
        return []
    
    def _get_outgoing_arcs(self, node_id: str) -> List:
        """Get outgoing arcs for a node.
        
        Args:
            node_id: Node ID
        
        Returns:
            List of arc objects
        """
        if not self.model:
            return []
        
        # Placeholder - implement based on model API
        return []
    
    def _redraw_canvas(self):
        """Request canvas redraw.
        
        Triggers canvas widget to redraw with current highlights.
        """
        if self.canvas and hasattr(self.canvas, 'queue_draw'):
            self.canvas.queue_draw()
    
    def get_highlighted_nodes(self) -> Set[str]:
        """Get all currently highlighted node IDs.
        
        Returns:
            Set of node IDs across all visible layers
        """
        nodes = set()
        for layer in self.layers.values():
            if layer.visible:
                nodes.update(layer.nodes)
        return nodes
    
    def get_highlighted_edges(self) -> Set[str]:
        """Get all currently highlighted edge IDs.
        
        Returns:
            Set of edge IDs across all visible layers
        """
        edges = set()
        for layer in self.layers.values():
            if layer.visible:
                edges.update(layer.edges)
        return edges
    
    def is_node_highlighted(self, node_id: str) -> bool:
        """Check if a node is currently highlighted.
        
        Args:
            node_id: Node ID
        
        Returns:
            True if highlighted in any visible layer
        """
        for layer in self.layers.values():
            if layer.visible and node_id in layer.nodes:
                return True
        return False
    
    def is_edge_highlighted(self, edge_id: str) -> bool:
        """Check if an edge is currently highlighted.
        
        Args:
            edge_id: Edge ID
        
        Returns:
            True if highlighted in any visible layer
        """
        for layer in self.layers.values():
            if layer.visible and edge_id in layer.edges:
                return True
        return False
    
    def get_node_highlight_style(self, node_id: str) -> Optional[HighlightStyle]:
        """Get the highlight style for a node.
        
        If node is in multiple layers, returns the top-most layer's style.
        
        Args:
            node_id: Node ID
        
        Returns:
            HighlightStyle or None if not highlighted
        """
        for layer in self.layers.values():
            if layer.visible and node_id in layer.nodes:
                return layer.style
        return None
    
    def get_edge_highlight_style(self, edge_id: str) -> Optional[HighlightStyle]:
        """Get the highlight style for an edge.
        
        If edge is in multiple layers, returns the top-most layer's style.
        
        Args:
            edge_id: Edge ID
        
        Returns:
            HighlightStyle or None if not highlighted
        """
        for layer in self.layers.values():
            if layer.visible and edge_id in layer.edges:
                return layer.style
        return None
    
    def enable(self):
        """Enable highlighting."""
        self.active = True
        self._redraw_canvas()
    
    def disable(self):
        """Disable highlighting (but keep layers)."""
        self.active = False
        self._redraw_canvas()
    
    def export_highlighted_view(self, filename: str):
        """Export current highlighted view to image file.
        
        Args:
            filename: Output filename (PNG, SVG, etc.)
        """
        # Placeholder for Phase 5
        pass


def create_highlighting_manager(canvas=None, model=None) -> HighlightingManager:
    """Factory function to create a highlighting manager.
    
    Args:
        canvas: Canvas widget
        model: Petri net model
    
    Returns:
        HighlightingManager instance
    """
    return HighlightingManager(canvas, model)
