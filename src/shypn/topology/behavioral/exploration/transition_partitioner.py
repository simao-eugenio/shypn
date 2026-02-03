"""Transition Partitioner - Group transitions by controlling signal layer.

Partitions transitions into layer groups based on their signal dependencies
to enable hierarchical state space exploration.

Author: Simão Eugénio
Date: February 3, 2026
"""

from typing import Dict, List, Set, Any
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class TransitionPartitioner:
    """Partition transitions by controlling signal layer.
    
    Assigns each transition to the highest signal layer it depends on,
    enabling layer-by-layer exploration where lower layers act as
    enabling conditions for higher layers.
    
    Example:
        partitioner = TransitionPartitioner(model, layer_assignment)
        layer_groups = partitioner.partition_transitions()
        # {0: [t1, t2], 1: [t3], 2: [t4, t5], 3: [t6]}
    """
    
    def __init__(self, model: Any, signal_layer_assignment: Dict[str, int]):
        """Initialize partitioner.
        
        Args:
            model: Petri net model
            signal_layer_assignment: Dict mapping signal_place_id → layer
        """
        self.model = model
        self.signal_layers = signal_layer_assignment
        self._signal_place_ids = set(signal_layer_assignment.keys())
    
    def partition_transitions(self) -> Dict[int, List[Any]]:
        """Partition transitions into layer groups.
        
        Rules:
        1. Transition with no signal inputs → Layer 0 (baseline metabolism)
        2. Transition with signal inputs → Max layer of input signals
        3. Signal flow arcs determine signal dependencies
        
        Returns:
            Dict mapping layer_number → list of Transition objects
        """
        layer_groups = defaultdict(list)
        
        # Get all transitions
        transitions = (self.model.transitions.values() 
                      if hasattr(self.model.transitions, 'values') 
                      else self.model.transitions)
        
        for transition in transitions:
            layer = self._determine_transition_layer(transition)
            layer_groups[layer].append(transition)
        
        # Convert to regular dict and sort
        result = {}
        for layer in sorted(layer_groups.keys()):
            result[layer] = layer_groups[layer]
        
        logger.info(
            f"Partitioned {sum(len(ts) for ts in result.values())} transitions: "
            f"L0={len(result.get(0, []))}, "
            f"L1={len(result.get(1, []))}, "
            f"L2={len(result.get(2, []))}, "
            f"L3={len(result.get(3, []))}"
        )
        
        return result
    
    def _determine_transition_layer(self, transition: Any) -> int:
        """Determine which layer a transition belongs to.
        
        Args:
            transition: Transition object
            
        Returns:
            Layer number (0-3)
        """
        trans_id = str(transition.id)
        
        # Find signal inputs via signal flow arcs
        signal_inputs = self._get_signal_inputs(trans_id)
        
        if not signal_inputs:
            # No signal dependencies → Layer 0 (baseline)
            return 0
        
        # Max layer of input signals
        max_layer = max(self.signal_layers[sig] for sig in signal_inputs)
        return max_layer
    
    def _get_signal_inputs(self, trans_id: str) -> Set[str]:
        """Get signal places that influence this transition.
        
        Args:
            trans_id: Transition ID
            
        Returns:
            Set of signal place IDs connected via signal flow arcs
        """
        signal_inputs = set()
        
        # Get all arcs
        arcs = (self.model.arcs.values() 
               if hasattr(self.model.arcs, 'values') 
               else self.model.arcs)
        
        for arc in arcs:
            source_id = str(arc.source.id if hasattr(arc.source, 'id') else arc.source)
            target_id = str(arc.target.id if hasattr(arc.target, 'id') else arc.target)
            
            # Check if this is a signal flow arc to our transition
            is_signal_flow = getattr(arc, 'arc_type', 'normal') == 'signal_flow'
            
            if is_signal_flow and target_id == trans_id:
                # Signal place → Transition
                if source_id in self._signal_place_ids:
                    signal_inputs.add(source_id)
        
        return signal_inputs
    
    def get_partition_statistics(
        self, 
        layer_groups: Dict[int, List[Any]]
    ) -> Dict[str, Any]:
        """Compute statistics about partition.
        
        Args:
            layer_groups: Result from partition_transitions()
            
        Returns:
            Dict with statistics
        """
        total_transitions = sum(len(ts) for ts in layer_groups.values())
        
        return {
            'total_transitions': total_transitions,
            'layer_0_count': len(layer_groups.get(0, [])),
            'layer_1_count': len(layer_groups.get(1, [])),
            'layer_2_count': len(layer_groups.get(2, [])),
            'layer_3_count': len(layer_groups.get(3, [])),
            'max_layer': max(layer_groups.keys()) if layer_groups else 0,
            'layer_distribution': {
                layer: len(transitions) 
                for layer, transitions in layer_groups.items()
            }
        }
    
    def get_transition_dependencies(
        self,
        layer_groups: Dict[int, List[Any]]
    ) -> Dict[int, Set[int]]:
        """Compute layer dependencies.
        
        Layer L depends on layer L' if any transition in L has
        signal input from layer L'.
        
        Args:
            layer_groups: Result from partition_transitions()
            
        Returns:
            Dict mapping layer → set of layers it depends on
        """
        dependencies = defaultdict(set)
        
        for layer, transitions in layer_groups.items():
            for transition in transitions:
                trans_id = str(transition.id)
                signal_inputs = self._get_signal_inputs(trans_id)
                
                for sig_id in signal_inputs:
                    sig_layer = self.signal_layers[sig_id]
                    if sig_layer != layer:
                        dependencies[layer].add(sig_layer)
        
        return dict(dependencies)
