"""Transform topology analysis results into per-element properties.

This module aggregates results from multiple analyzers and organizes them
by model element (place/transition) instead of by analyzer.

Example transformation:
    FROM (analyzer-centric):
        P-Invariants: [{places: [P1, P2], ...}, ...]
        Siphons: [{places: [P1, P3], ...}, ...]
    
    TO (element-centric):
        P1: {p_invariants: [...], in_siphons: [...], ...}
        P2: {p_invariants: [...], ...}
        P3: {in_siphons: [...], ...}

Author: Simão Eugénio
Date: 2025-10-29
"""

from typing import Dict, List, Any, Optional
from collections import defaultdict


class TopologyResultAggregator:
    """Aggregate topology analysis results into per-element properties.
    
    This class takes results from all 12 topology analyzers and transforms
    them into a per-element view, making it easy to see all properties of
    each place or transition in one place.
    
    Example:
        aggregator = TopologyResultAggregator()
        element_data = aggregator.aggregate(all_results)
        
        # Access place properties
        atp_properties = element_data['places']['P1']
        
        # Access transition properties
        hexokinase = element_data['transitions']['T1']
    """
    
    def aggregate(self, all_results: Dict[str, Any]) -> Dict[str, Dict]:
        """Aggregate all analysis results into per-element view.
        
        Args:
            all_results: Dict of {analyzer_name: AnalysisResult object or data dict}
                Can handle both AnalysisResult objects and raw data dicts
        
        Returns:
            Dict with structure:
            {
                'places': {
                    'place_id': {
                        'name': 'Place Name',
                        'id': place_id,
                        'p_invariants': [...],
                        'in_siphons': [...],
                        'in_traps': [...],
                        'boundedness': 'bounded/unbounded',
                        ...
                    },
                    ...
                },
                'transitions': {
                    'transition_id': {
                        'name': 'Transition Name',
                        'id': transition_id,
                        't_invariants': [...],
                        'is_hub': True/False,
                        'hub_degree': int,
                        'in_cycles': [...],
                        'liveness_level': 'L0/L1/L2/L3/L4',
                        ...
                    },
                    ...
                }
            }
        """
        places = defaultdict(lambda: {
            'name': '',
            'id': None,
            'p_invariants': [],
            'in_siphons': [],
            'in_traps': [],
            'boundedness': 'unknown',
            'can_deadlock': False
        })
        
        transitions = defaultdict(lambda: {
            'name': '',
            'id': None,
            't_invariants': [],
            'is_hub': False,
            'hub_degree': 0,
            'in_cycles': [],
            'in_paths': [],
            'liveness_level': 'unknown',
            'liveness_description': '',
            'can_deadlock': False,
            'fairness': 'unknown'
        })
        
        # Process each analyzer's results
        for analyzer_name, result in all_results.items():
            # Extract data from AnalysisResult object or use raw dict
            if hasattr(result, 'success'):
                if not result.success:
                    continue  # Skip failed/blocked analyses
                data = result.data if hasattr(result, 'data') else {}
            else:
                data = result
            
            # Route to appropriate processor
            if analyzer_name == 'p_invariants':
                self._process_p_invariants(data, places)
            elif analyzer_name == 't_invariants':
                self._process_t_invariants(data, transitions)
            elif analyzer_name == 'siphons':
                self._process_siphons(data, places)
            elif analyzer_name == 'traps':
                self._process_traps(data, places)
            elif analyzer_name == 'cycles':
                self._process_cycles(data, transitions)
            elif analyzer_name == 'paths':
                self._process_paths(data, transitions)
            elif analyzer_name == 'hubs':
                self._process_hubs(data, transitions)
            elif analyzer_name == 'boundedness':
                self._process_boundedness(data, places)
            elif analyzer_name == 'reachability':
                self._process_reachability(data, places, transitions)
            elif analyzer_name == 'liveness':
                self._process_liveness(data, transitions)
            elif analyzer_name == 'deadlocks':
                self._process_deadlocks(data, places, transitions)
            elif analyzer_name == 'fairness':
                self._process_fairness(data, transitions)
        
        return {
            'places': dict(places),
            'transitions': dict(transitions)
        }
    
    def _process_p_invariants(self, data: Dict, places: Dict):
        """Process P-Invariant results into place properties."""
        invariants = data.get('p_invariants', [])
        
        for inv_id, inv in enumerate(invariants, 1):
            place_ids = inv.get('places', [])
            weights = inv.get('weights', [])
            expression = inv.get('sum_expression', '')
            names = inv.get('names', [])
            
            for i, place_id in enumerate(place_ids):
                place_id_str = str(place_id)
                weight = weights[i] if i < len(weights) else 1
                name = names[i] if i < len(names) else f"P{place_id}"
                
                places[place_id_str]['id'] = place_id
                if not places[place_id_str]['name']:
                    places[place_id_str]['name'] = name
                
                places[place_id_str]['p_invariants'].append({
                    'invariant_id': inv_id,
                    'weight': weight,
                    'expression': expression
                })
    
    def _process_t_invariants(self, data: Dict, transitions: Dict):
        """Process T-Invariant results into transition properties."""
        invariants = data.get('t_invariants', [])
        
        for inv_id, inv in enumerate(invariants, 1):
            trans_ids = inv.get('transition_ids', [])
            weights = inv.get('weights', [])
            sequence = inv.get('firing_sequence', '')
            trans_names = inv.get('transition_names', [])
            
            for i, trans_id in enumerate(trans_ids):
                trans_id_str = str(trans_id)
                weight = weights[i] if i < len(weights) else 1
                name = trans_names[i] if i < len(trans_names) else f"T{trans_id}"
                
                transitions[trans_id_str]['id'] = trans_id
                if not transitions[trans_id_str]['name']:
                    transitions[trans_id_str]['name'] = name
                
                transitions[trans_id_str]['t_invariants'].append({
                    'invariant_id': inv_id,
                    'weight': weight,
                    'sequence': sequence
                })
    
    def _process_siphons(self, data: Dict, places: Dict):
        """Process Siphon results into place properties."""
        siphons = data.get('siphons', [])
        
        for siphon_id, siphon in enumerate(siphons, 1):
            place_ids = siphon.get('place_ids', [])
            is_empty = siphon.get('is_empty', False)
            
            for place_id in place_ids:
                place_id_str = str(place_id)
                places[place_id_str]['in_siphons'].append({
                    'siphon_id': siphon_id,
                    'is_empty': is_empty,
                    'size': len(place_ids)
                })
                
                if is_empty:
                    places[place_id_str]['can_deadlock'] = True
    
    def _process_traps(self, data: Dict, places: Dict):
        """Process Trap results into place properties."""
        traps = data.get('traps', [])
        
        for trap_id, trap in enumerate(traps, 1):
            place_ids = trap.get('place_ids', [])
            is_marked = trap.get('is_marked', False)
            
            for place_id in place_ids:
                place_id_str = str(place_id)
                places[place_id_str]['in_traps'].append({
                    'trap_id': trap_id,
                    'is_marked': is_marked,
                    'size': len(place_ids)
                })
    
    def _process_cycles(self, data: Dict, transitions: Dict):
        """Process Cycle results into transition properties."""
        cycles = data.get('cycles', [])
        
        for cycle_id, cycle in enumerate(cycles, 1):
            nodes = cycle.get('nodes', [])
            length = cycle.get('length', len(nodes))
            cycle_type = cycle.get('type', 'unknown')
            
            # Extract transition IDs from cycle nodes
            # (cycles contain both places and transitions)
            for node in nodes:
                node_str = str(node)
                # Simple heuristic: if it starts with 'T' or is numeric (trans ID)
                if isinstance(node, int) or (isinstance(node, str) and (node.startswith('T') or node.isdigit())):
                    transitions[node_str]['in_cycles'].append({
                        'cycle_id': cycle_id,
                        'length': length,
                        'type': cycle_type,
                        'nodes': nodes
                    })
    
    def _process_paths(self, data: Dict, transitions: Dict):
        """Process Path results into transition properties."""
        paths = data.get('paths', [])
        
        for path_id, path in enumerate(paths, 1):
            nodes = path.get('nodes', [])
            
            for node in nodes:
                node_str = str(node)
                if isinstance(node, int) or (isinstance(node, str) and (node.startswith('T') or node.isdigit())):
                    transitions[node_str]['in_paths'].append({
                        'path_id': path_id,
                        'length': len(nodes),
                        'nodes': nodes
                    })
    
    def _process_hubs(self, data: Dict, transitions: Dict):
        """Process Hub results into transition properties."""
        hubs = data.get('hubs', [])
        
        for hub in hubs:
            trans_id = hub.get('id') or hub.get('transition_id')
            if trans_id is None:
                continue
            
            trans_id_str = str(trans_id)
            transitions[trans_id_str]['is_hub'] = True
            transitions[trans_id_str]['hub_degree'] = hub.get('degree', 0)
            transitions[trans_id_str]['connected_to'] = hub.get('neighbors', [])
    
    def _process_boundedness(self, data: Dict, places: Dict):
        """Process Boundedness results into place properties."""
        is_bounded = data.get('is_bounded', True)
        unbounded_places = data.get('unbounded_places', [])
        
        for place_id in unbounded_places:
            place_id_str = str(place_id)
            places[place_id_str]['boundedness'] = 'unbounded'
        
        # Mark all others as bounded if globally bounded
        if is_bounded:
            for place_id_str in places.keys():
                if places[place_id_str]['boundedness'] == 'unknown':
                    places[place_id_str]['boundedness'] = 'bounded'
    
    def _process_reachability(self, data: Dict, places: Dict, transitions: Dict):
        """Process Reachability results (affects both places and transitions)."""
        # This is complex - for now just store basic info
        total_states = data.get('total_states', 0)
        deadlock_states = data.get('deadlock_states', [])
        
        # Could mark transitions that are never enabled, etc.
        pass
    
    def _process_liveness(self, data: Dict, transitions: Dict):
        """Process Liveness results into transition properties."""
        liveness_levels = data.get('liveness_levels', {})
        dead_transitions = data.get('dead_transitions', [])
        live_transitions = data.get('live_transitions', [])
        
        for trans_id, level in liveness_levels.items():
            trans_id_str = str(trans_id)
            transitions[trans_id_str]['liveness_level'] = level
            
            # Add description
            level_descriptions = {
                'L0': 'Dead - cannot fire',
                'L1': 'Potentially firable',
                'L2': 'Potentially live',
                'L3': 'Live - can fire infinitely',
                'L4': 'Strictly live'
            }
            transitions[trans_id_str]['liveness_description'] = level_descriptions.get(level, level)
    
    def _process_deadlocks(self, data: Dict, places: Dict, transitions: Dict):
        """Process Deadlock results into place/transition properties."""
        has_deadlock = data.get('has_deadlock', False)
        empty_siphons = data.get('empty_siphons', [])
        deadlock_places = data.get('deadlock_places', [])
        
        for place_id in deadlock_places:
            place_id_str = str(place_id)
            places[place_id_str]['can_deadlock'] = True
    
    def _process_fairness(self, data: Dict, transitions: Dict):
        """Process Fairness results into transition properties."""
        is_fair = data.get('is_fair', True)
        unfair_transitions = data.get('unfair_transitions', [])
        
        for trans_id in unfair_transitions:
            trans_id_str = str(trans_id)
            transitions[trans_id_str]['fairness'] = 'unfair'
        
        # Mark others as fair
        if is_fair:
            for trans_id_str in transitions.keys():
                if transitions[trans_id_str]['fairness'] == 'unknown':
                    transitions[trans_id_str]['fairness'] = 'fair'
    
    def to_table_format(self, element_data: Dict[str, Dict], element_type: str = 'places') -> List[Dict]:
        """Convert element-centric data to table format for display.
        
        Args:
            element_data: Result from aggregate() method
            element_type: 'places' or 'transitions'
        
        Returns:
            List of dicts suitable for table display, one row per element
        """
        elements = element_data.get(element_type, {})
        table_rows = []
        
        if element_type == 'places':
            for place_id, props in elements.items():
                row = {
                    'ID': place_id,
                    'Name': props.get('name', ''),
                    'P-Invariants': len(props.get('p_invariants', [])),
                    'Siphons': len(props.get('in_siphons', [])),
                    'Traps': len(props.get('in_traps', [])),
                    'Boundedness': props.get('boundedness', 'unknown'),
                    'Deadlock Risk': '⚠️' if props.get('can_deadlock', False) else '✓'
                }
                table_rows.append(row)
        
        elif element_type == 'transitions':
            for trans_id, props in elements.items():
                row = {
                    'ID': trans_id,
                    'Name': props.get('name', ''),
                    'T-Invariants': len(props.get('t_invariants', [])),
                    'Hub': '✓' if props.get('is_hub', False) else '',
                    'Degree': props.get('hub_degree', 0) if props.get('is_hub') else '',
                    'Cycles': len(props.get('in_cycles', [])),
                    'Liveness': props.get('liveness_level', 'unknown'),
                    'Fairness': props.get('fairness', 'unknown')
                }
                table_rows.append(row)
        
        return table_rows
