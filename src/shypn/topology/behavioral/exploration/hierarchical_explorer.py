"""Hierarchical Explorer - Layer-by-layer state space exploration.

Implements Phase 3 of the weak independence partition plan, exploiting
signal hierarchy to decompose state space exploration into manageable layers.

Author: Simão Eugénio
Date: February 3, 2026
"""

from typing import Dict, List, Set, Tuple, Any, Optional
from collections import deque
import logging
import time

from .base_explorer import StateSpaceExplorer, WorkQueue
from .signal_layer_detector import SignalLayerDetector
from .transition_partitioner import TransitionPartitioner

logger = logging.getLogger(__name__)


class HierarchicalExplorer(StateSpaceExplorer):
    """Layer-by-layer state space exploration using signal hierarchy.
    
    Exploits biological hierarchy to partition exploration:
    - Layer 0 (ENERGY): ATP-gated baseline metabolism
    - Layer 1 (SPATIAL): Compartment-specific pathways
    - Layer 2 (QUORUM): Cell-cell communication
    - Layer 3 (REGULATORY): Gene expression decisions
    
    Key insight: Lower layers act as enabling conditions for higher layers,
    allowing compositional reasoning and dramatic state space reduction.
    
    Example:
        explorer = HierarchicalExplorer(model)
        result = explorer.explore(
            initial_marking, 
            max_states=100000,
            max_depth=100
        )
    """
    
    def __init__(self, model_or_analyzer: Any):
        """Initialize hierarchical explorer.
        
        Args:
            model_or_analyzer: Either Petri net model or ReachabilityAnalyzer
        """
        # Handle both direct model and analyzer wrapper
        if hasattr(model_or_analyzer, 'model'):
            # It's an analyzer
            super().__init__(model_or_analyzer)
        else:
            # It's a model - create minimal wrapper
            self.model = model_or_analyzer
            self.analyzer = None
        
        # Detect layers
        self.layer_detector = SignalLayerDetector(self.model)
        self.signal_layers = self.layer_detector.detect_layers()
        
        # Partition transitions
        self.partitioner = TransitionPartitioner(self.model, self.signal_layers)
        self.layer_groups = self.partitioner.partition_transitions()
        
        logger.info(
            f"Hierarchical explorer initialized: "
            f"{len(self.signal_layers)} signals, "
            f"{sum(len(ts) for ts in self.layer_groups.values())} transitions"
        )
    
    def explore(
        self,
        initial_marking: Dict[str, int],
        max_states: int = 10000,
        max_depth: int = 100,
        find_deadlocks: bool = True
    ) -> Dict[str, Any]:
        """Explore state space hierarchically.
        
        Strategy:
        1. Explore Layer 0 until stable states found
        2. For each stable Layer 0 state, explore Layer 1
        3. Continue layer-by-layer to Layer 3
        4. Exploit layer independence for state space reduction
        
        Args:
            initial_marking: Initial marking dict
            max_states: Maximum states to explore
            max_depth: Maximum depth to explore
            find_deadlocks: Whether to detect deadlock states
            
        Returns:
            Exploration result dict
        """
        start_time = time.time()
        
        # Initialize state tracking
        visited = {}  # marking_tuple → state_id
        states = {}   # state_id → marking dict
        transitions = []  # (from_id, to_id, trans_id)
        deadlocks = []
        
        state_counter = 0
        
        # Add initial state
        initial_tuple = self._dict_to_tuple(initial_marking)
        visited[initial_tuple] = state_counter
        states[state_counter] = initial_marking.copy()
        state_counter += 1
        
        # If no hierarchy detected, fall back to flat exploration
        if not self.layer_groups or len(self.layer_groups) == 1:
            logger.warning("No hierarchy detected - using flat exploration")
            return self._explore_flat(
                initial_marking,
                max_states,
                max_depth,
                find_deadlocks
            )
        
        # Hierarchical exploration by layer
        logger.info(f"Starting hierarchical exploration ({len(self.layer_groups)} layers)")
        
        # Phase 1: Explore Layer 0 (baseline metabolism)
        layer0_states = self._explore_layer(
            layer=0,
            initial_states=[initial_marking],
            visited=visited,
            states=states,
            transitions=transitions,
            deadlocks=deadlocks,
            state_counter=state_counter,
            max_states=max_states,
            max_depth=max_depth,
            find_deadlocks=find_deadlocks
        )
        
        state_counter = len(states)
        
        # Phase 2+: Explore higher layers from stable lower layer states
        for layer in range(1, max(self.layer_groups.keys()) + 1):
            if state_counter >= max_states:
                break
            
            # Get stable states from previous layer
            stable_states = self._find_stable_states(
                layer0_states if layer == 1 else layer_states,
                layer - 1
            )
            
            if not stable_states:
                logger.info(f"No stable states for layer {layer} - skipping")
                continue
            
            logger.info(
                f"Exploring layer {layer} from {len(stable_states)} stable states"
            )
            
            layer_states = self._explore_layer(
                layer=layer,
                initial_states=stable_states,
                visited=visited,
                states=states,
                transitions=transitions,
                deadlocks=deadlocks,
                state_counter=state_counter,
                max_states=max_states,
                max_depth=max_depth,
                find_deadlocks=find_deadlocks,
                frozen_layers=list(range(layer))
            )
            
            state_counter = len(states)
        
        elapsed = time.time() - start_time
        
        logger.info(
            f"Hierarchical exploration complete: "
            f"{len(states)} states, {len(transitions)} transitions, "
            f"{len(deadlocks)} deadlocks, {elapsed:.2f}s"
        )
        
        return {
            'states': states,
            'transitions': transitions,
            'deadlocks': deadlocks,
            'initial_state': 0,
            'total_states': len(states),
            'total_transitions': len(transitions),
            'elapsed_time': elapsed,
            'exploration_mode': 'hierarchical',
            'layer_count': len(self.layer_groups)
        }
    
    def _explore_layer(
        self,
        layer: int,
        initial_states: List[Dict[str, int]],
        visited: Dict[Tuple, int],
        states: Dict[int, Dict[str, int]],
        transitions: List[Tuple[int, int, str]],
        deadlocks: List[int],
        state_counter: int,
        max_states: int,
        max_depth: int,
        find_deadlocks: bool,
        frozen_layers: Optional[List[int]] = None
    ) -> List[Dict[str, int]]:
        """Explore a single layer.
        
        Args:
            layer: Layer number to explore
            initial_states: Starting states for this layer
            visited: Shared visited dict
            states: Shared states dict
            transitions: Shared transitions list
            deadlocks: Shared deadlocks list
            state_counter: Current state counter
            max_states: Maximum states
            max_depth: Maximum depth
            find_deadlocks: Whether to find deadlocks
            frozen_layers: Layers whose signals are frozen (lower layers)
            
        Returns:
            List of reachable states in this layer
        """
        frozen_layers = frozen_layers or []
        layer_transitions = self.layer_groups.get(layer, [])
        
        if not layer_transitions:
            logger.warning(f"Layer {layer} has no transitions")
            return initial_states
        
        logger.info(
            f"Exploring layer {layer}: {len(layer_transitions)} transitions, "
            f"{len(initial_states)} initial states"
        )
        
        layer_states = []
        work_queue = deque()
        
        # Initialize queue with initial states
        for marking in initial_states:
            marking_tuple = self._dict_to_tuple(marking)
            if marking_tuple in visited:
                state_id = visited[marking_tuple]
            else:
                state_id = state_counter
                visited[marking_tuple] = state_id
                states[state_id] = marking.copy()
                state_counter += 1
            
            work_queue.append((marking, 0, state_id))
            layer_states.append(marking)
        
        # BFS exploration
        while work_queue and len(states) < max_states:
            current_marking, depth, current_id = work_queue.popleft()
            
            if depth >= max_depth:
                continue
            
            # Get enabled transitions (only from current layer)
            enabled = self._get_enabled_layer_transitions(
                current_marking,
                layer_transitions
            )
            
            if not enabled and find_deadlocks:
                deadlocks.append(current_id)
            
            # Fire each enabled transition
            for trans in enabled:
                trans_id = str(trans.id)
                new_marking = self._fire_transition(current_marking, trans)
                new_tuple = self._dict_to_tuple(new_marking)
                
                # Check if new state
                if new_tuple not in visited:
                    new_state_id = state_counter
                    visited[new_tuple] = new_state_id
                    states[new_state_id] = new_marking.copy()
                    state_counter += 1
                    
                    work_queue.append((new_marking, depth + 1, new_state_id))
                    layer_states.append(new_marking)
                else:
                    new_state_id = visited[new_tuple]
                
                # Record transition
                transitions.append((current_id, new_state_id, trans_id))
        
        logger.info(f"Layer {layer} exploration: {len(layer_states)} reachable states")
        
        return layer_states
    
    def _get_enabled_layer_transitions(
        self,
        marking: Dict[str, int],
        layer_transitions: List[Any]
    ) -> List[Any]:
        """Get enabled transitions from specific layer.
        
        Args:
            marking: Current marking
            layer_transitions: Transitions in current layer
            
        Returns:
            List of enabled transitions
        """
        enabled = []
        
        for trans in layer_transitions:
            if self._is_transition_enabled(marking, trans):
                enabled.append(trans)
        
        return enabled
    
    def _find_stable_states(
        self,
        states: List[Dict[str, int]],
        layer: int
    ) -> List[Dict[str, int]]:
        """Find stable states for a layer.
        
        Stable state: No more transitions in this layer can fire.
        
        Args:
            states: List of states to check
            layer: Layer number
            
        Returns:
            List of stable states
        """
        layer_transitions = self.layer_groups.get(layer, [])
        stable = []
        
        for marking in states:
            # Check if any layer transitions are enabled
            enabled = self._get_enabled_layer_transitions(marking, layer_transitions)
            
            if not enabled:
                # No transitions enabled → stable state
                stable.append(marking)
        
        return stable
    
    # Helper methods
    
    def _dict_to_tuple(self, marking: Dict[str, int]) -> Tuple:
        """Convert marking dict to hashable tuple."""
        return tuple(sorted(marking.items()))
    
    def _tuple_to_dict(self, marking_tuple: Tuple) -> Dict[str, int]:
        """Convert marking tuple back to dict."""
        return dict(marking_tuple)
    
    def _is_transition_enabled(self, marking: Dict[str, int], transition: Any) -> bool:
        """Check if transition is enabled in given marking."""
        for place_id, weight in transition.inputs.items():
            if marking.get(place_id, 0) < weight:
                return False
        return True
    
    def _fire_transition(
        self,
        marking: Dict[str, int],
        transition: Any
    ) -> Dict[str, int]:
        """Fire transition and return new marking."""
        new_marking = marking.copy()
        
        # Consume inputs
        for place_id, weight in transition.inputs.items():
            new_marking[place_id] = new_marking.get(place_id, 0) - weight
        
        # Produce outputs
        for place_id, weight in transition.outputs.items():
            new_marking[place_id] = new_marking.get(place_id, 0) + weight
        
        return new_marking
    
    def _explore_flat(
        self,
        initial_marking: Dict[str, int],
        max_states: int,
        max_depth: int,
        find_deadlocks: bool
    ) -> Dict[str, Any]:
        """Fallback to flat BFS exploration if no hierarchy.
        
        Args:
            initial_marking: Initial marking
            max_states: Maximum states
            max_depth: Maximum depth
            find_deadlocks: Whether to find deadlocks
            
        Returns:
            Exploration result dict
        """
        from .sequential_explorer import SequentialExplorer
        
        logger.info("Using flat exploration (no hierarchy)")
        # SequentialExplorer also expects analyzer, need to wrap
        if self.analyzer:
            flat_explorer = SequentialExplorer(self.analyzer)
        else:
            # Create minimal mock analyzer
            class MockAnalyzer:
                def __init__(self, model):
                    self.model = model
            flat_explorer = SequentialExplorer(MockAnalyzer(self.model))
        
        return flat_explorer.explore(
            initial_marking,
            max_states,
            max_depth,
            compute_graph=True,
            find_deadlocks=find_deadlocks
        )
