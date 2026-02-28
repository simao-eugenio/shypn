"""Coverability analyzer for Petri nets.

This module provides analysis of coverability graphs/trees for Petri nets,
particularly useful for unbounded nets where the reachability graph is infinite.
Uses omega (ω) symbols to represent unbounded places.
"""

from typing import Dict, List, Set, Tuple, Optional, Any
from dataclasses import dataclass
import logging

from shypn.topology.base.topology_analyzer import TopologyAnalyzer
from shypn.topology.base.analysis_result import AnalysisResult

logger = logging.getLogger(__name__)

# Special value representing unbounded token count
OMEGA = float('inf')


@dataclass
class CoverabilityNode:
    """Represents a node in the coverability graph."""
    marking: Tuple[int, ...]  # Can contain OMEGA
    node_id: int
    is_duplicate: bool = False
    parent_id: Optional[int] = None
    transition: Optional[str] = None
    
    def __hash__(self):
        return hash(self.marking)
    
    def __eq__(self, other):
        if not isinstance(other, CoverabilityNode):
            return False
        return self.marking == other.marking


class CoverabilityAnalyzer(TopologyAnalyzer):
    """Analyzer for computing coverability graphs of Petri nets.
    
    The coverability graph is a finite representation of potentially infinite
    reachability graphs. It uses omega (ω) to represent places that can grow
    unboundedly. This is essential for analyzing unbounded Petri nets.
    
    Key capabilities:
    - Construct coverability tree/graph
    - Identify unbounded places
    - Detect coverable markings
    - Find dead markings
    - Compute graph statistics
    
    Example:
        analyzer = CoverabilityAnalyzer(model)
        result = analyzer.analyze(max_nodes=1000)
        if result.success:
            unbounded = result.data['unbounded_places']
            print(f"Unbounded places: {unbounded}")
    """
    
    def __init__(self, model):
        """Initialize the coverability analyzer.
        
        Args:
            model: The Petri net model to analyze
        """
        super().__init__(model)
        self._nodes: List[CoverabilityNode] = []
        self._edges: List[Tuple[int, int, str]] = []
        self._node_counter = 0
        self._marking_to_node: Dict[Tuple, int] = {}
        
    def analyze(  # type: ignore[override]
        self,
        initial_marking: Optional[Dict[str, int]] = None,
        max_nodes: int = 10000,
        max_omega: int = 1000
    ) -> AnalysisResult:
        """Compute the coverability graph for the Petri net.
        
        Args:
            initial_marking: Initial marking (uses model's initial if None)
            max_nodes: Maximum nodes to explore (prevents infinite computation)
            max_omega: Token threshold for introducing omega
            
        Returns:
            AnalysisResult containing:
                - nodes: List of coverability nodes
                - edges: List of transitions between nodes
                - unbounded_places: Places that reach omega
                - coverable_markings: Set of all coverable markings
                - dead_nodes: Nodes with no enabled transitions
                - statistics: Graph statistics
                - summary: Text summary
        """
        try:
            self._validate_model()
            start_time = self._start_timer()
            
            # Clear previous analysis
            self._nodes.clear()
            self._edges.clear()
            self._node_counter = 0
            self._marking_to_node.clear()
            
            # Get initial marking
            if initial_marking is None:
                initial_marking = self._get_initial_marking()
            
            # Build coverability graph
            marking_tuple = self._dict_to_tuple(initial_marking)
            root = CoverabilityNode(marking_tuple, self._node_counter, False)
            self._nodes.append(root)
            self._marking_to_node[marking_tuple] = self._node_counter
            self._node_counter += 1
            
            # BFS exploration
            queue = [0]  # Node IDs to explore
            
            while queue and len(self._nodes) < max_nodes:
                current_id = queue.pop(0)
                current_node = self._nodes[current_id]
                
                if current_node.is_duplicate:
                    continue
                
                current_marking_dict = self._tuple_to_dict(current_node.marking)
                
                # Try each transition
                enabled = self._get_enabled_transitions(current_marking_dict)
                
                for trans_id in enabled:
                    # Fire transition
                    new_marking_dict = self._fire_transition(
                        current_marking_dict, trans_id
                    )
                    
                    # Check for omega introduction along path
                    new_marking_tuple = self._introduce_omega(
                        new_marking_dict,
                        current_node,
                        max_omega
                    )
                    
                    # Check if marking already exists
                    if new_marking_tuple in self._marking_to_node:
                        # Duplicate - add edge but don't explore
                        existing_id = self._marking_to_node[new_marking_tuple]
                        self._edges.append((current_id, existing_id, trans_id))
                    else:
                        # New marking
                        new_node = CoverabilityNode(
                            new_marking_tuple,
                            self._node_counter,
                            False,
                            current_id,
                            trans_id
                        )
                        self._nodes.append(new_node)
                        self._marking_to_node[new_marking_tuple] = self._node_counter
                        self._edges.append((current_id, self._node_counter, trans_id))
                        queue.append(self._node_counter)
                        self._node_counter += 1
            
            elapsed = self._end_timer(start_time)
            
            # Analyze results
            unbounded_places = self._find_unbounded_places()
            dead_nodes = self._find_dead_nodes()
            statistics = self._compute_statistics()
            
            # Build result
            nodes_data = [
                {
                    'id': node.node_id,
                    'marking': self._tuple_to_dict(node.marking),
                    'is_duplicate': node.is_duplicate,
                    'parent_id': node.parent_id,
                    'transition': node.transition
                }
                for node in self._nodes
            ]
            
            edges_data = [
                {
                    'from': src,
                    'to': dst,
                    'transition': trans
                }
                for src, dst, trans in self._edges
            ]
            
            data = {
                'nodes': nodes_data,
                'edges': edges_data,
                'unbounded_places': list(unbounded_places),
                'dead_nodes': dead_nodes,
                'statistics': statistics,
                'is_bounded': len(unbounded_places) == 0,
                'is_complete': len(self._nodes) < max_nodes
            }
            
            summary = self._create_summary(
                len(self._nodes),
                len(self._edges),
                unbounded_places,
                dead_nodes,
                len(self._nodes) >= max_nodes
            )
            
            warnings = []
            if len(self._nodes) >= max_nodes:
                warnings.append(
                    f"Reached maximum node limit ({max_nodes}). "
                    "Graph may be incomplete."
                )
            
            return AnalysisResult(
                success=True,
                data=data,
                summary=summary,
                warnings=warnings,
                metadata={
                    'analyzer': 'coverability',
                    'computation_time': elapsed,
                    'nodes_explored': len(self._nodes),
                    'edges_found': len(self._edges),
                    'max_nodes': max_nodes,
                    'max_omega': max_omega
                }
            )
            
        except (ValueError, AttributeError, KeyError, MemoryError) as e:
            logger.error(f"Coverability analysis failed: {e}", exc_info=True)
            return AnalysisResult(
                success=False,
                errors=[str(e)],
                summary="Coverability analysis failed"
            )
    
    def is_coverable(
        self,
        target_marking: Dict[str, int]
    ) -> bool:
        """Check if a marking is coverable from the initial marking.
        
        A marking M' is coverable from M if there exists a reachable marking M''
        such that M''(p) >= M'(p) for all places p.
        
        Args:
            target_marking: The marking to check
            
        Returns:
            True if the marking is coverable
        """
        if not self._nodes:
            raise RuntimeError("Must run analyze() before checking coverability")
        
        target_tuple = self._dict_to_tuple(target_marking)
        
        for node in self._nodes:
            if self._covers(node.marking, target_tuple):
                return True
        
        return False
    
    def get_unbounded_places(self) -> List[str]:
        """Get list of places that are unbounded.
        
        Returns:
            List of place IDs that reach omega
        """
        if not self._nodes:
            raise RuntimeError("Must run analyze() before getting unbounded places")
        
        return self._find_unbounded_places()
    
    def _get_initial_marking(self) -> Dict[str, int]:
        """Get initial marking from the model."""
        marking = {}
        # Handle both dict and list formats
        if hasattr(self.model.places, 'items'):
            # Dict format
            for place_id, place in self.model.places.items():
                marking[place_id] = place.tokens
        else:
            # List format (DocumentModel)
            for place in self.model.places:
                marking[place.id] = place.tokens
        return marking
    
    def _dict_to_tuple(self, marking: Dict[str, int]) -> Tuple:
        """Convert marking dict to ordered tuple."""
        # Handle both dict and list formats
        if hasattr(self.model.places, 'keys'):
            place_ids = sorted(self.model.places.keys())
        else:
            place_ids = sorted(p.id for p in self.model.places)
        return tuple(marking.get(p, 0) for p in place_ids)
    
    def _tuple_to_dict(self, marking: Tuple) -> Dict[str, int]:
        """Convert marking tuple to dict."""
        # Handle both dict and list formats
        if hasattr(self.model.places, 'keys'):
            place_ids = sorted(self.model.places.keys())
        else:
            place_ids = sorted(p.id for p in self.model.places)
        result = {}
        for i, place_id in enumerate(place_ids):
            tokens = marking[i]
            # Handle omega
            if tokens == OMEGA:
                result[place_id] = OMEGA
            else:
                result[place_id] = int(tokens)
        return result  # type: ignore[return-value]
    
    def _get_enabled_transitions(self, marking: Dict[str, int]) -> List[str]:
        """Get list of enabled transitions for a marking."""
        enabled = []
        
        # Handle both dict and list formats
        if hasattr(self.model.transitions, 'items'):
            transitions_iter = self.model.transitions.items()
        else:
            transitions_iter = [(t.id, t) for t in self.model.transitions]
        
        arcs = self.model.arcs.values() if hasattr(self.model.arcs, 'values') else self.model.arcs
        
        for trans_id, transition in transitions_iter:
            # Check if all input places have enough tokens
            can_fire = True
            
            for arc in arcs:
                arc_target = arc.target.id if hasattr(arc.target, 'id') else arc.target
                arc_source = arc.source.id if hasattr(arc.source, 'id') else arc.source
                
                if arc_target == trans_id:  # Input arc
                    tokens = marking.get(arc_source, 0)
                    # Omega can always provide tokens
                    if tokens != OMEGA and tokens < arc.weight:
                        can_fire = False
                        break
            
            if can_fire:
                enabled.append(trans_id)
        
        return enabled
    
    def _fire_transition(
        self,
        marking: Dict[str, int],
        trans_id: str
    ) -> Dict[str, int]:
        """Fire a transition and return the new marking."""
        new_marking = marking.copy()
        
        # Handle both dict and list formats for arcs
        arcs = self.model.arcs.values() if hasattr(self.model.arcs, 'values') else self.model.arcs
        
        # Remove tokens from input places
        for arc in arcs:
            arc_target = arc.target.id if hasattr(arc.target, 'id') else arc.target
            arc_source = arc.source.id if hasattr(arc.source, 'id') else arc.source
            
            if arc_target == trans_id:
                place_id = arc_source
                current = new_marking.get(place_id, 0)
                if current != OMEGA:
                    new_marking[place_id] = max(0, current - arc.weight)
        
        # Add tokens to output places
        for arc in arcs:
            arc_target = arc.target.id if hasattr(arc.target, 'id') else arc.target
            arc_source = arc.source.id if hasattr(arc.source, 'id') else arc.source
            
            if arc_source == trans_id:
                place_id = arc_target
                current = new_marking.get(place_id, 0)
                if current == OMEGA:
                    new_marking[place_id] = OMEGA  # type: ignore[assignment]
                else:
                    new_marking[place_id] = current + arc.weight
        
        return new_marking
    
    def _introduce_omega(
        self,
        marking: Dict[str, int],
        current_node: CoverabilityNode,
        max_omega: int
    ) -> Tuple:
        """Introduce omega for unbounded places along the path.
        
        Omega introduction rule: If marking M' > M on some place along the path
        to M, then introduce omega for all places where M' > M.
        """
        # Check ancestors for strictly smaller markings
        ancestor = current_node
        marking_copy = marking.copy()
        
        while ancestor is not None:
            ancestor_marking_dict = self._tuple_to_dict(ancestor.marking)
            
            # Check if current marking is strictly greater than ancestor
            # Need to check if at least one place is strictly greater
            # and no place is strictly less (monotonic increase)
            has_greater = False
            all_ge = True
            
            for place_id in marking_copy:
                current_val = marking_copy[place_id]
                ancestor_val = ancestor_marking_dict.get(place_id, 0)
                
                # Skip if already omega
                if current_val == OMEGA or ancestor_val == OMEGA:
                    continue
                
                if current_val > ancestor_val:
                    has_greater = True
                elif current_val < ancestor_val:
                    all_ge = False
                    break
            
            # If monotonic increase detected (M' >= M and M' > M in at least one place)
            if has_greater and all_ge:
                # Introduce omega for all places where current > ancestor
                for place_id in marking_copy:
                    current_val = marking_copy[place_id]
                    ancestor_val = ancestor_marking_dict.get(place_id, 0)
                    
                    if current_val == OMEGA or ancestor_val == OMEGA:
                        continue
                    
                    if current_val > ancestor_val:
                        marking_copy[place_id] = OMEGA  # type: ignore[assignment]
            
            # Also check max_omega threshold
            for place_id in marking_copy:
                if marking_copy[place_id] != OMEGA and marking_copy[place_id] >= max_omega:
                    marking_copy[place_id] = OMEGA  # type: ignore[assignment]
            
            # Move to parent
            if ancestor.parent_id is not None:
                ancestor = self._nodes[ancestor.parent_id]
            else:
                ancestor = None  # type: ignore[assignment]
        
        return self._dict_to_tuple(marking_copy)
    
    def _covers(self, marking1: Tuple, marking2: Tuple) -> bool:
        """Check if marking1 covers marking2."""
        if len(marking1) != len(marking2):
            return False
        
        for m1, m2 in zip(marking1, marking2):
            # Omega covers anything
            if m1 == OMEGA:
                continue
            # Regular token count must be >= target
            if m1 < m2:
                return False
        
        return True
    
    def _find_unbounded_places(self) -> List[str]:
        """Find all places that reach omega in any node."""
        unbounded = set()
        # Handle both dict and list formats
        if hasattr(self.model.places, 'keys'):
            place_ids = sorted(self.model.places.keys())
        else:
            place_ids = sorted(p.id for p in self.model.places)
        
        for node in self._nodes:
            for i, tokens in enumerate(node.marking):
                if tokens == OMEGA:
                    unbounded.add(place_ids[i])
        
        return sorted(unbounded)
    
    def _find_dead_nodes(self) -> List[int]:
        """Find nodes with no outgoing transitions (dead markings)."""
        # Get nodes that have outgoing edges
        nodes_with_out_edges = set(src for src, _, _ in self._edges)
        
        # Dead nodes are those without outgoing edges and not duplicates
        dead = [
            node.node_id
            for node in self._nodes
            if node.node_id not in nodes_with_out_edges and not node.is_duplicate
        ]
        
        return dead
    
    def _compute_statistics(self) -> Dict[str, Any]:
        """Compute graph statistics."""
        # Count omega occurrences
        omega_count = 0
        for node in self._nodes:
            for tokens in node.marking:
                if tokens == OMEGA:
                    omega_count += 1
        
        # Compute depth (longest path from root)
        depths = {0: 0}
        for node in self._nodes[1:]:
            if node.parent_id is not None:
                depths[node.node_id] = depths.get(node.parent_id, 0) + 1
            else:
                depths[node.node_id] = 0
        
        max_depth = max(depths.values()) if depths else 0
        
        # Count duplicate nodes
        duplicates = sum(1 for node in self._nodes if node.is_duplicate)
        
        return {
            'total_nodes': len(self._nodes),
            'total_edges': len(self._edges),
            'omega_occurrences': omega_count,
            'max_depth': max_depth,
            'duplicate_nodes': duplicates,
            'average_branching': (
                len(self._edges) / max(1, len(self._nodes) - duplicates)
            )
        }
    
    def _create_summary(
        self,
        num_nodes: int,
        num_edges: int,
        unbounded_places: List[str],
        dead_nodes: List[int],
        truncated: bool
    ) -> str:
        """Create a human-readable summary."""
        lines = [f"Coverability graph: {num_nodes} nodes, {num_edges} edges"]
        
        if unbounded_places:
            lines.append(
                f"Unbounded: {len(unbounded_places)} places "
                f"({', '.join(unbounded_places[:3])}"
                f"{'...' if len(unbounded_places) > 3 else ''})"
            )
        else:
            lines.append("Net is bounded")
        
        if dead_nodes:
            lines.append(f"Dead markings: {len(dead_nodes)}")
        
        if truncated:
            lines.append("⚠ Graph truncated (max nodes reached)")
        
        return " | ".join(lines)
    
    def clear_cache(self) -> None:
        """Clear cached analysis results."""
        super().clear_cache()
        self._nodes.clear()
        self._edges.clear()
        self._node_counter = 0
        self._marking_to_node.clear()
