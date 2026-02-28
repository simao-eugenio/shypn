"""Sequential state-space exploration using BFS.

This module implements the classic breadth-first search algorithm
for reachability analysis. Used as baseline and fallback strategy.
"""

from typing import Any, Dict, List
from collections import deque

from .base_explorer import StateSpaceExplorer


class SequentialExplorer(StateSpaceExplorer):
    """Sequential BFS exploration (baseline implementation)."""
    
    def explore(
        self,
        initial_marking: Dict[str, int],
        max_states: int,
        max_depth: int,
        compute_graph: bool,
        find_deadlocks: bool
    ) -> Dict[str, Any]:
        """Explore reachable states using sequential BFS.
        
        This is the baseline implementation from ReachabilityAnalyzer,
        extracted for modularity.
        """
        # Initialize exploration
        visited = set()
        queue = deque([(initial_marking, 0)])  # (marking, depth)
        visited.add(self._marking_to_tuple(initial_marking))
        
        states = [initial_marking]
        transitions_fired = 0
        max_depth_reached = 0
        
        # Graph structure
        graph = {'nodes': [], 'edges': []} if compute_graph else None  # type: ignore[var-annotated]
        if compute_graph:
            graph['nodes'].append({  # type: ignore[index]
                'id': 0,
                'marking': initial_marking.copy(),
                'depth': 0
            })
        
        state_index = {self._marking_to_tuple(initial_marking): 0}
        next_state_id = 1
        
        # BFS exploration
        while queue and len(visited) < max_states:
            current_marking, depth = queue.popleft()
            
            if depth > max_depth:
                continue
            
            max_depth_reached = max(max_depth_reached, depth)
            
            # Find enabled transitions
            enabled = self._get_enabled_transitions(current_marking)
            
            # Fire each enabled transition
            for trans_id in enabled:
                new_marking = self._fire_transition(current_marking, trans_id)
                marking_tuple = self._marking_to_tuple(new_marking)
                
                transitions_fired += 1
                
                # Check if new state
                if marking_tuple not in visited:
                    visited.add(marking_tuple)
                    states.append(new_marking)
                    queue.append((new_marking, depth + 1))
                    
                    if compute_graph:
                        state_index[marking_tuple] = next_state_id
                        graph['nodes'].append({  # type: ignore[index]
                            'id': next_state_id,
                            'marking': new_marking.copy(),
                            'depth': depth + 1
                        })
                        next_state_id += 1
                
                # Add edge to graph
                if compute_graph:
                    source_id = state_index[self._marking_to_tuple(current_marking)]
                    target_id = state_index[marking_tuple]
                    graph['edges'].append({  # type: ignore[index]
                        'source': source_id,
                        'target': target_id,
                        'transition': trans_id,
                        'transition_name': self.analyzer._get_transition_name(trans_id)
                    })
        
        # Find deadlocks if requested
        deadlock_states = []
        if find_deadlocks:
            for i, state in enumerate(states):
                if self._is_deadlock(state):
                    deadlock_states.append({
                        'state_id': i,
                        'marking': state,
                        'enabled_transitions': []
                    })
        
        return {
            'total_states': len(visited),
            'total_transitions': transitions_fired,
            'max_depth': max_depth_reached,
            'states': states,
            'graph': graph,
            'deadlock_states': deadlock_states,
            'exploration_stats': {
                'strategy': 'sequential',
                'mode': 'single-threaded',
                'num_workers': 1
            }
        }
