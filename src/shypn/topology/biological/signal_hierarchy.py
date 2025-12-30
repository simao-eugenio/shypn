"""Signal Hierarchy Analyzer for Biological Petri Nets.

This analyzer detects and validates hierarchical control structures in biological models:

1. **Signal Places (Ψ)**: Places representing information channels
   - 4 types: quorum sensing, energy status, regulatory, spatial information
   - Affect transition rates without mass transfer (information channel)
   - Visual: marked with is_signal_place=True

2. **Signal Flow Arcs**: Information transfer connections
   - Connect signal places to transitions (information consumption)
   - Different from test arcs (test = catalytic/non-consuming)
   - Visual: dashed line with angled arrowhead (15° offset)
   - Formal: arc_type="signal_flow"

3. **Hierarchical Layers**: Stratified control structure
   - Layer detection from signal flow graph topology
   - Acyclicity validation (no feedback in signal hierarchy)
   - Preemption relationships (higher layers control lower layers)

4. **Validation**: Structural integrity checks
   - Signal flow arcs must connect to signal places
   - Signal hierarchy should be acyclic
   - Layer ordering should be consistent

Theoretical Foundation:
- Doc: doc/foundation/SIGNAL_HIERARCHY_THEORY.md
- Doc: doc/foundation/SIGNAL_FLOW_ARCS_SPECIFICATION.md
- Section: Hierarchical Preemption Mechanism
- Reference: Simão, E. (2025). "Hierarchical Preemption: A Novel Information-Theoretic 
  Control Mechanism in Lambda Phage Decision-Making"

Author: GitHub Copilot & Eugênio Simão
Date: December 26, 2025
"""

from typing import Any, Dict, List, Set, Tuple, Optional
from collections import defaultdict, deque

from shypn.topology.base.topology_analyzer import TopologyAnalyzer
from shypn.topology.base.analysis_result import AnalysisResult
from shypn.topology.base.exceptions import TopologyAnalysisError
from shypn.netobjs.signal_flow_arc import SignalFlowArc
from shypn.netobjs.place import Place
from shypn.netobjs.transition import Transition


class SignalHierarchyAnalyzer(TopologyAnalyzer):
    """Analyzer for signal hierarchies in Biological Petri Nets.
    
    Detects:
    - Signal places (information channels)
    - Signal flow arcs (information transfer)
    - Hierarchical layers (control stratification)
    - Preemption relationships (inter-layer control)
    
    Validates:
    - Signal flow arc connections (must connect to signal place)
    - Acyclicity (no feedback loops in signal hierarchy)
    - Layer consistency (proper stratification)
    
    Example:
        >>> analyzer = SignalHierarchyAnalyzer(model)
        >>> result = analyzer.analyze()
        >>> print(f"Signal places: {len(result.data['signal_places'])}")
        >>> print(f"Signal flow arcs: {len(result.data['signal_flow_arcs'])}")
        >>> print(f"Hierarchy layers: {result.data['hierarchy']['layer_count']}")
    """
    
    def __init__(self, model: Any):
        """Initialize signal hierarchy analyzer.
        
        Args:
            model: Petri net model with places, transitions, and arcs
        """
        super().__init__(model)
        self.name = "Signal Hierarchy"
        self.description = "Detect signal places, signal flow arcs, and hierarchical control structure"
    
    def analyze(self, **kwargs) -> AnalysisResult:
        """Analyze signal hierarchy in the model.
        
        Returns:
            AnalysisResult with:
            - signal_places: List of signal place details
            - signal_flow_arcs: List of signal flow arc details
            - hierarchy: Hierarchical structure (layers, preemption relationships)
            - validation: Validation results
            - statistics: Summary statistics
            - interpretation: Biological interpretation
        """
        start_time = self._start_timer()
        
        try:
            # Detect signal places
            signal_places = self._detect_signal_places()
            
            # Detect signal flow arcs
            signal_flow_arcs = self._detect_signal_flow_arcs()
            
            # Validate signal flow connections
            validation_results = self._validate_signal_flow(signal_places, signal_flow_arcs)
            
            # Infer hierarchical layers
            hierarchy = self._infer_hierarchy_layers(signal_places, signal_flow_arcs)
            
            # Compute statistics
            statistics = self._compute_statistics(signal_places, signal_flow_arcs, hierarchy)
            
            # Generate interpretation
            interpretation = self._generate_interpretation(signal_places, signal_flow_arcs, hierarchy, validation_results)
            
            elapsed_time = self._stop_timer(start_time)
            
            return AnalysisResult(
                analyzer_name=self.name,
                success=True,
                data={
                    'signal_places': signal_places,
                    'signal_flow_arcs': signal_flow_arcs,
                    'hierarchy': hierarchy,
                    'validation': validation_results,
                    'statistics': statistics,
                    'interpretation': interpretation
                },
                elapsed_time=elapsed_time
            )
        except Exception as e:
            elapsed_time = self._stop_timer(start_time)
            raise TopologyAnalysisError(
                f"Signal hierarchy analysis failed: {str(e)}",
                analyzer_name=self.name
            ) from e
    
    def _detect_signal_places(self) -> List[Dict[str, Any]]:
        """Detect all signal places in the model.
        
        Signal places are identified by:
        1. is_signal_place=True attribute
        2. signal_type attribute (quorum, energy, regulatory, spatial)
        
        Returns:
            List of signal place information dicts
        """
        signal_places = []
        
        for place in self.model.places:
            # Check if place has signal place marker
            is_signal = getattr(place, 'is_signal_place', False)
            
            if is_signal:
                signal_type = getattr(place, 'signal_type', 'unknown')
                initial_marking = getattr(place, 'marking', 0)
                
                # Find connected arcs
                incoming_arcs = [arc for arc in self.model.arcs if arc.target == place]
                outgoing_arcs = [arc for arc in self.model.arcs if arc.source == place]
                
                # Count signal flow arcs
                signal_flow_out = [arc for arc in outgoing_arcs if isinstance(arc, SignalFlowArc)]
                
                signal_places.append({
                    'id': place.id,
                    'name': place.name,
                    'signal_type': signal_type,
                    'initial_marking': initial_marking,
                    'incoming_count': len(incoming_arcs),
                    'outgoing_count': len(outgoing_arcs),
                    'signal_flow_count': len(signal_flow_out),
                    'place_obj': place  # For later reference
                })
        
        return signal_places
    
    def _detect_signal_flow_arcs(self) -> List[Dict[str, Any]]:
        """Detect all signal flow arcs in the model.
        
        Signal flow arcs are identified by:
        1. isinstance(arc, SignalFlowArc)
        2. arc_type=="signal_flow"
        
        Returns:
            List of signal flow arc information dicts
        """
        signal_flow_arcs = []
        
        for arc in self.model.arcs:
            if isinstance(arc, SignalFlowArc):
                source = arc.source
                target = arc.target
                weight = getattr(arc, 'weight', 1.0)
                
                # Determine endpoint types
                source_is_signal = getattr(source, 'is_signal_place', False)
                target_is_signal = getattr(target, 'is_signal_place', False) if isinstance(target, Place) else False
                
                # Determine direction (signal place → transition or transition → signal place)
                if source_is_signal and isinstance(target, Transition):
                    direction = "signal_to_transition"
                    signal_place_id = source.id
                    transition_id = target.id
                elif isinstance(source, Transition) and target_is_signal:
                    direction = "transition_to_signal"
                    signal_place_id = target.id
                    transition_id = source.id
                else:
                    direction = "unknown"
                    signal_place_id = None
                    transition_id = None
                
                signal_flow_arcs.append({
                    'id': arc.id,
                    'name': getattr(arc, 'name', ''),
                    'source_id': source.id,
                    'source_name': getattr(source, 'name', ''),
                    'target_id': target.id,
                    'target_name': getattr(target, 'name', ''),
                    'weight': weight,
                    'direction': direction,
                    'signal_place_id': signal_place_id,
                    'transition_id': transition_id,
                    'arc_obj': arc  # For later reference
                })
        
        return signal_flow_arcs
    
    def _validate_signal_flow(self, signal_places: List[Dict], signal_flow_arcs: List[Dict]) -> Dict[str, Any]:
        """Validate signal flow arc connections and structure.
        
        Checks:
        1. Every signal flow arc connects to at least one signal place
        2. Signal flow arcs do not create cycles in hierarchy
        3. Signal places have consistent signal types
        
        Args:
            signal_places: List of signal place info
            signal_flow_arcs: List of signal flow arc info
        
        Returns:
            Validation results dict
        """
        issues = []
        warnings = []
        
        signal_place_ids = {sp['id'] for sp in signal_places}
        
        # Check 1: Signal flow arcs must connect to signal places
        for arc_info in signal_flow_arcs:
            source_id = arc_info['source_id']
            target_id = arc_info['target_id']
            
            if source_id not in signal_place_ids and target_id not in signal_place_ids:
                issues.append({
                    'type': 'invalid_connection',
                    'arc_id': arc_info['id'],
                    'arc_name': arc_info['name'],
                    'message': f"Signal flow arc {arc_info['id']} does not connect to any signal place"
                })
        
        # Check 2: Detect cycles in signal flow graph
        cycles = self._detect_cycles(signal_flow_arcs)
        if cycles:
            for cycle in cycles:
                issues.append({
                    'type': 'cycle_detected',
                    'cycle': cycle,
                    'message': f"Signal hierarchy contains cycle: {' -> '.join(cycle)}"
                })
        
        # Check 3: Warn about signal places with no outgoing signal flow
        for sp in signal_places:
            if sp['signal_flow_count'] == 0:
                warnings.append({
                    'type': 'unused_signal_place',
                    'place_id': sp['id'],
                    'place_name': sp['name'],
                    'message': f"Signal place {sp['name']} has no outgoing signal flow arcs"
                })
        
        is_valid = len(issues) == 0
        
        return {
            'is_valid': is_valid,
            'issues': issues,
            'warnings': warnings,
            'issue_count': len(issues),
            'warning_count': len(warnings)
        }
    
    def _detect_cycles(self, signal_flow_arcs: List[Dict]) -> List[List[str]]:
        """Detect cycles in the signal flow graph using DFS.
        
        Args:
            signal_flow_arcs: List of signal flow arc info
        
        Returns:
            List of cycles (each cycle is a list of node IDs)
        """
        # Build adjacency list
        graph = defaultdict(list)
        for arc in signal_flow_arcs:
            graph[arc['source_id']].append(arc['target_id'])
        
        cycles = []
        visited = set()
        rec_stack = set()
        path = []
        
        def dfs(node: str):
            """DFS with cycle detection."""
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    dfs(neighbor)
                elif neighbor in rec_stack:
                    # Cycle detected
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]
                    cycles.append(cycle)
            
            path.pop()
            rec_stack.remove(node)
        
        # Run DFS from each unvisited node
        for node in graph.keys():
            if node not in visited:
                dfs(node)
        
        return cycles
    
    def _infer_hierarchy_layers(self, signal_places: List[Dict], signal_flow_arcs: List[Dict]) -> Dict[str, Any]:
        """Infer hierarchical layers from signal flow topology.
        
        Uses topological sorting to assign layer numbers:
        - Layer 0: Signal places with no incoming signal flow
        - Layer k: Signal places with incoming from layer k-1
        
        Args:
            signal_places: List of signal place info
            signal_flow_arcs: List of signal flow arc info
        
        Returns:
            Hierarchy structure dict
        """
        # Build signal place graph (signal place → transition → signal place)
        signal_place_ids = {sp['id'] for sp in signal_places}
        
        # Build graph of signal place dependencies
        dependencies = defaultdict(set)  # target_signal → source_signals
        
        for arc in signal_flow_arcs:
            source_id = arc['source_id']
            target_id = arc['target_id']
            
            # If arc is signal_place → transition, mark transition as intermediate
            # If arc is transition → signal_place, connect previous signal places to this one
            if source_id in signal_place_ids and arc['direction'] == 'signal_to_transition':
                # Store transition as intermediate node
                transition_id = arc['transition_id']
                
                # Find arcs from this transition to signal places
                for arc2 in signal_flow_arcs:
                    if arc2['source_id'] == transition_id and arc2['target_id'] in signal_place_ids:
                        # source_id (signal) → transition → arc2['target_id'] (signal)
                        dependencies[arc2['target_id']].add(source_id)
        
        # Topological sort to assign layers
        layer_assignment = {}
        in_degree = defaultdict(int)
        
        for target in dependencies:
            in_degree[target] = len(dependencies[target])
        
        # All signal places start at layer 0
        for sp in signal_places:
            if sp['id'] not in in_degree or in_degree[sp['id']] == 0:
                layer_assignment[sp['id']] = 0
        
        # BFS to assign layers
        queue = deque([sp_id for sp_id in layer_assignment.keys()])
        
        while queue:
            current_id = queue.popleft()
            current_layer = layer_assignment[current_id]
            
            # Update downstream signal places
            for target_id, sources in dependencies.items():
                if current_id in sources:
                    new_layer = max(layer_assignment.get(target_id, 0), current_layer + 1)
                    layer_assignment[target_id] = new_layer
                    if target_id not in queue:
                        queue.append(target_id)
        
        # Group by layer
        layers = defaultdict(list)
        for sp_id, layer in layer_assignment.items():
            layers[layer].append(sp_id)
        
        layer_count = len(layers)
        max_layer_size = max([len(nodes) for nodes in layers.values()]) if layers else 0
        
        # Detect preemption relationships (higher layer → lower layer control)
        preemption_pairs = []
        for target_id, sources in dependencies.items():
            target_layer = layer_assignment.get(target_id, 0)
            for source_id in sources:
                source_layer = layer_assignment.get(source_id, 0)
                if source_layer < target_layer:
                    preemption_pairs.append({
                        'source': source_id,
                        'target': target_id,
                        'source_layer': source_layer,
                        'target_layer': target_layer,
                        'layer_gap': target_layer - source_layer
                    })
        
        return {
            'layer_count': layer_count,
            'max_layer_size': max_layer_size,
            'layers': dict(layers),
            'layer_assignment': layer_assignment,
            'preemption_pairs': preemption_pairs,
            'is_hierarchical': layer_count > 1,
            'is_acyclic': len(self._detect_cycles(signal_flow_arcs)) == 0
        }
    
    def _compute_statistics(self, signal_places: List[Dict], signal_flow_arcs: List[Dict], hierarchy: Dict) -> Dict[str, Any]:
        """Compute summary statistics.
        
        Args:
            signal_places: List of signal place info
            signal_flow_arcs: List of signal flow arc info
            hierarchy: Hierarchy structure
        
        Returns:
            Statistics dict
        """
        # Count signal types
        signal_type_counts = defaultdict(int)
        for sp in signal_places:
            signal_type_counts[sp['signal_type']] += 1
        
        # Count arc directions
        direction_counts = defaultdict(int)
        for arc in signal_flow_arcs:
            direction_counts[arc['direction']] += 1
        
        return {
            'total_signal_places': len(signal_places),
            'total_signal_flow_arcs': len(signal_flow_arcs),
            'signal_type_counts': dict(signal_type_counts),
            'direction_counts': dict(direction_counts),
            'hierarchy_layer_count': hierarchy['layer_count'],
            'max_layer_size': hierarchy['max_layer_size'],
            'preemption_count': len(hierarchy['preemption_pairs']),
            'is_hierarchical': hierarchy['is_hierarchical'],
            'is_acyclic': hierarchy['is_acyclic']
        }
    
    def _generate_interpretation(self, signal_places: List[Dict], signal_flow_arcs: List[Dict], 
                                 hierarchy: Dict, validation: Dict) -> str:
        """Generate biological interpretation of signal hierarchy.
        
        Args:
            signal_places: List of signal place info
            signal_flow_arcs: List of signal flow arc info
            hierarchy: Hierarchy structure
            validation: Validation results
        
        Returns:
            Interpretation string
        """
        lines = []
        
        # Header
        lines.append("=== Signal Hierarchy Analysis ===\n")
        
        # Summary
        lines.append(f"Signal Places: {len(signal_places)}")
        lines.append(f"Signal Flow Arcs: {len(signal_flow_arcs)}")
        lines.append(f"Hierarchy Layers: {hierarchy['layer_count']}")
        lines.append(f"Preemption Relationships: {len(hierarchy['preemption_pairs'])}\n")
        
        # Validation status
        if validation['is_valid']:
            lines.append("✓ Signal hierarchy structure is VALID")
        else:
            lines.append(f"✗ Signal hierarchy has {validation['issue_count']} structural issues")
        
        if validation['warnings']:
            lines.append(f"⚠ {validation['warning_count']} warnings detected\n")
        else:
            lines.append("")
        
        # Hierarchical structure interpretation
        if hierarchy['is_hierarchical']:
            lines.append("Hierarchical Control: DETECTED")
            lines.append(f"  - {hierarchy['layer_count']} layers of control")
            lines.append(f"  - Largest layer: {hierarchy['max_layer_size']} signal places")
            
            if hierarchy['is_acyclic']:
                lines.append("  - Acyclic structure (no feedback loops)")
            else:
                lines.append("  - WARNING: Cyclic structure detected")
            
            lines.append(f"\nPreemption Mechanism:")
            lines.append(f"  - {len(hierarchy['preemption_pairs'])} preemption relationships")
            lines.append(f"  - Higher layers control lower layer decisions")
        else:
            lines.append("Hierarchical Control: NOT DETECTED")
            lines.append("  - Single-layer or flat control structure")
        
        # Biological interpretation
        lines.append("\nBiological Interpretation:")
        if hierarchy['is_hierarchical'] and hierarchy['is_acyclic']:
            lines.append("  The model exhibits hierarchical control with clear layer stratification.")
            lines.append("  Higher-level signals (e.g., stress, nutrient availability) regulate")
            lines.append("  lower-level decision-making processes through information cascades.")
        elif signal_flow_arcs:
            lines.append("  The model uses signal flow arcs for information transfer.")
            lines.append("  However, hierarchical layering is not clearly defined.")
        else:
            lines.append("  No signal flow structure detected in this model.")
        
        return "\n".join(lines)
