"""Cycle detection for Petri nets."""

from typing import List, Dict, Any, Optional, Tuple
import networkx as nx

from ..base.topology_analyzer import TopologyAnalyzer
from ..base.analysis_result import AnalysisResult
from ..base.exceptions import TopologyAnalysisError


class CycleAnalyzer(TopologyAnalyzer):
    """Analyzer for detecting cycles in Petri nets.
    
    This analyzer finds all elementary cycles (simple cycles) in the Petri net
    graph using Johnson's algorithm. Elementary cycles are cycles with no
    repeated nodes (except the start/end node).
    
    For biochemical networks, cycles represent:
    - Metabolic loops (e.g., TCA cycle, Calvin cycle)
    - Feedback regulation loops
    - Substrate recycling pathways
    - Conservation cycles
    
    Attributes:
        model: PetriNetModel instance to analyze
        
    Example:
        analyzer = CycleAnalyzer(model)
        result = analyzer.analyze(max_cycles=100)
        
        if result.success:
            for cycle_info in result.get('cycles', []):
                print(f"Cycle length {cycle_info['length']}: {cycle_info['names']}")
                print(f"  Type: {cycle_info['type']}")
                print(f"  Places: {cycle_info['place_count']}, Transitions: {cycle_info['transition_count']}")
        else:
            print("Analysis failed:", result.errors)
    """
    
    def analyze(self, max_cycles: int = 100, min_length: int = 2) -> AnalysisResult:
        """Find all elementary cycles in the Petri net.
        
        Args:
            max_cycles: Maximum number of cycles to return (prevents huge results)
            min_length: Minimum cycle length to report (default 2 = self-loops)
            
        Returns:
            AnalysisResult with:
                - cycles: List of cycle info dicts (nodes, length, names, types)
                - count: Total number of cycles found
                - truncated: Whether results were truncated
                - longest_length: Length of longest cycle
                - longest_cycle: Node IDs of longest cycle
                - summary: Human-readable summary
                - metadata: Analysis parameters and timing
                
        Raises:
            TopologyAnalysisError: If cycle detection fails
        """
        start_time = self._start_timer()
        
        try:
            # Validate model
            self._validate_model()
            
            # Build directed graph
            graph = self._build_graph()
            
            # Find elementary cycles using NetworkX (Johnson's algorithm)
            all_cycles = list(nx.simple_cycles(graph))
            
            # Filter by minimum length
            all_cycles = [c for c in all_cycles if len(c) >= min_length]
            
            # Check if we need to truncate
            total_count = len(all_cycles)
            truncated = total_count > max_cycles
            
            if truncated:
                # Keep longest cycles first
                all_cycles.sort(key=len, reverse=True)
                cycles_to_analyze = all_cycles[:max_cycles]
            else:
                cycles_to_analyze = all_cycles
            
            # Analyze each cycle
            cycle_data = []
            for cycle_nodes in cycles_to_analyze:
                cycle_info = self._analyze_cycle(cycle_nodes)
                cycle_data.append(cycle_info)
            
            # Find longest cycle
            longest = max(all_cycles, key=len) if all_cycles else []
            longest_length = len(longest)
            
            # Create summary
            summary = self._create_summary(total_count, longest_length, truncated)
            
            # Compute timing
            duration = self._end_timer(start_time)
            
            # Build result
            result = AnalysisResult(
                success=True,
                data={
                    'cycles': cycle_data,
                    'count': total_count,
                    'truncated': truncated,
                    'longest_length': longest_length,
                    'longest_cycle': longest,
                },
                summary=summary,
                metadata={
                    'max_cycles': max_cycles,
                    'min_length': min_length,
                    'analysis_time': duration,
                    'graph_nodes': graph.number_of_nodes(),
                    'graph_edges': graph.number_of_edges(),
                }
            )
            
            if truncated:
                result.add_warning(
                    f"Results truncated to {max_cycles} cycles (found {total_count} total)"
                )
            
            return result
        
        except Exception as e:
            return AnalysisResult(
                success=False,
                errors=[f"Cycle analysis failed: {str(e)}"],
                metadata={'analysis_time': self._end_timer(start_time)}
            )
    
    def _build_graph(self) -> nx.DiGraph:
        """Build directed graph from Petri net.
        
        Creates a NetworkX DiGraph where:
        - Nodes are places and transitions (identified by ID)
        - Edges are arcs (source → target)
        - Node attributes include type ('place' or 'transition') and object reference
        - Edge attributes include arc object reference
        
        Returns:
            NetworkX DiGraph representation of the Petri net
        """
        graph = nx.DiGraph()
        
        # Add place nodes
        for place in self.model.places:
            graph.add_node(
                place.id,
                type='place',
                obj=place,
                name=getattr(place, 'name', f'P{place.id}')
            )
        
        # Add transition nodes
        for transition in self.model.transitions:
            graph.add_node(
                transition.id,
                type='transition',
                obj=transition,
                name=getattr(transition, 'name', f'T{transition.id}')
            )
        
        # Add arc edges
        for arc in self.model.arcs:
            graph.add_edge(
                arc.source_id,
                arc.target_id,
                obj=arc,
                weight=getattr(arc, 'weight', 1)
            )
        
        return graph
    
    def _analyze_cycle(self, cycle_nodes: List[int]) -> Dict[str, Any]:
        """Analyze a single cycle.
        
        Extracts detailed information about a cycle including:
        - Node IDs and objects
        - Node names
        - Place/transition counts
        - Cycle type classification
        
        Args:
            cycle_nodes: List of node IDs forming the cycle
            
        Returns:
            Dictionary with cycle information:
                - nodes: List of node IDs
                - length: Number of nodes in cycle
                - names: List of node names
                - objects: List of Petri net objects
                - place_count: Number of places in cycle
                - transition_count: Number of transitions in cycle
                - type: Cycle type classification
        """
        # Get objects for each node
        objects = []
        names = []
        
        for node_id in cycle_nodes:
            obj = self._get_object_by_id(node_id)
            objects.append(obj)
            
            # Get name
            if obj:
                name = getattr(obj, 'name', None)
                if not name or name.strip() == "":
                    # Generate default name based on type
                    if hasattr(obj, 'tokens'):  # Place
                        name = f"P{obj.id}"
                    elif hasattr(obj, 'transition_type'):  # Transition
                        name = f"T{obj.id}"
                    else:
                        name = f"N{obj.id}"
                names.append(name)
            else:
                names.append(f"ID{node_id}")
        
        # Classify nodes
        places = [obj for obj in objects if obj and hasattr(obj, 'tokens')]
        transitions = [obj for obj in objects if obj and hasattr(obj, 'transition_type')]
        
        # Classify cycle type
        cycle_type = self._classify_cycle_type(places, transitions)
        
        return {
            'nodes': cycle_nodes,
            'length': len(cycle_nodes),
            'names': names,
            'objects': objects,
            'place_count': len(places),
            'transition_count': len(transitions),
            'type': cycle_type,
        }
    
    def _classify_cycle_type(self, places: List[Any], transitions: List[Any]) -> str:
        """Classify cycle type based on composition.
        
        Args:
            places: List of place objects in cycle
            transitions: List of transition objects in cycle
            
        Returns:
            Cycle type string:
                - 'self-loop': Single transition cycle
                - 'balanced': Equal places and transitions (typical metabolic cycle)
                - 'place-heavy': More places than transitions
                - 'transition-heavy': More transitions than places
        """
        place_count = len(places)
        transition_count = len(transitions)
        
        if transition_count == 1 and place_count == 1:
            return 'self-loop'
        elif place_count == transition_count:
            return 'balanced'
        elif place_count > transition_count:
            return 'place-heavy'
        else:
            return 'transition-heavy'
    
    def _create_summary(self, count: int, longest_length: int, truncated: bool) -> str:
        """Create human-readable summary.
        
        Args:
            count: Total number of cycles found
            longest_length: Length of longest cycle
            truncated: Whether results were truncated
            
        Returns:
            Summary string
        """
        if count == 0:
            return "No cycles found (network is a DAG)"
        
        summary_parts = [f"Found {count} cycle(s)"]
        
        if truncated:
            summary_parts.append("(results truncated)")
        
        if longest_length > 0:
            summary_parts.append(f"• Longest: {longest_length} nodes")
        
        return "\n".join(summary_parts)
    
    def _get_object_by_id(self, obj_id: int) -> Optional[Any]:
        """Get Petri net object by ID.
        
        Args:
            obj_id: Object ID to find
            
        Returns:
            Petri net object (Place or Transition), or None if not found
        """
        # Try places
        for place in self.model.places:
            if place.id == obj_id:
                return place
        
        # Try transitions
        for transition in self.model.transitions:
            if transition.id == obj_id:
                return transition
        
        return None
    
    def find_cycles_containing_node(self, node_id: int, max_cycles: int = 100) -> List[Dict[str, Any]]:
        """Find all cycles that contain a specific node.
        
        This is a convenience method for property dialogs that want to show
        which cycles contain a particular place or transition.
        
        Args:
            node_id: ID of the place or transition to find
            max_cycles: Maximum number of cycles to analyze
            
        Returns:
            List of cycle info dicts that contain the specified node
            
        Example:
            # Find cycles containing place with ID 5
            place_cycles = analyzer.find_cycles_containing_node(5)
            print(f"Place 5 is in {len(place_cycles)} cycle(s)")
        """
        result = self.analyze(max_cycles=max_cycles)
        
        if not result.success:
            return []
        
        cycles = result.get('cycles', [])
        return [c for c in cycles if node_id in c['nodes']]
