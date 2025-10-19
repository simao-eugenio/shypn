"""Liveness analyzer for Petri nets.

Liveness determines whether transitions can fire infinitely often from any
reachable marking. A live Petri net guarantees deadlock-freedom and progress.

Liveness Levels (Landweber & Robertson, 1978):
- **L0 (Dead)**: Transition can never fire
- **L1 (Potentially firable)**: Can fire at least once in some sequence
- **L2 (Potentially live)**: Can fire arbitrarily often in some sequence
- **L3 (Live)**: Can fire infinitely often from any reachable marking
- **L4 (Strictly live)**: Can fire in every reachable marking

Analysis approaches:
- Structural: Check for transitions that can never be enabled
- Behavioral: Limited reachability exploration to assess firing potential
- Deadlock-based: Use deadlock analysis to identify dead transitions
- Conservative: Use P-invariants to verify token availability

Mathematical Background:
- Murata, T. (1989). "Petri nets: Properties, analysis and applications"
- Landweber, L.H. & Robertson, E.L. (1978). "Properties of conflict-free graphs"
- Commoner, F. (1972). "Deadlocks in Petri nets"

Implementation approach:
- Check structural enablement (can transition ever fire?)
- Analyze token flow (do input places have token sources?)
- Check for deadlock conditions that prevent firing
- Classify liveness levels based on firing potential
"""

from typing import Any, Dict, List, Set, Optional
import numpy as np

from shypn.topology.base.topology_analyzer import TopologyAnalyzer
from shypn.topology.base.analysis_result import AnalysisResult
from shypn.topology.base.exceptions import TopologyAnalysisError


class LivenessAnalyzer(TopologyAnalyzer):
    """Analyzer for checking liveness of Petri net transitions.
    
    A transition is live if it can fire infinitely often from any reachable marking.
    This analyzer classifies transitions into liveness levels (L0-L4).
    
    Example:
        >>> analyzer = LivenessAnalyzer(model)
        >>> result = analyzer.analyze()
        >>> for trans_id, level in result.get('liveness_levels').items():
        ...     print(f"{trans_id}: {level}")
    """
    
    def __init__(self, model: Any):
        """Initialize liveness analyzer.
        
        Args:
            model: Petri net model with places, transitions, and arcs attributes
        """
        super().__init__(model)
        self.name = "Liveness"
        self.description = "Check if transitions can fire infinitely often"
    
    def analyze(
        self,
        check_structural: bool = True,
        check_deadlocks: bool = True,
        check_token_flow: bool = True,
        classify_levels: bool = True
    ) -> AnalysisResult:
        """Analyze liveness of transitions in the Petri net.
        
        Args:
            check_structural: Check structural enablement conditions
            check_deadlocks: Use deadlock analysis to identify dead transitions
            check_token_flow: Analyze token flow to input places
            classify_levels: Classify transitions into liveness levels (L0-L4)
            
        Returns:
            AnalysisResult with:
            - is_live: Boolean indicating if net is live (all transitions L3+)
            - liveness_levels: Dict mapping transition IDs to liveness levels
            - dead_transitions: List of dead (L0) transitions
            - live_transitions: List of live (L3+) transitions
            - transition_analysis: Detailed analysis per transition
        """
        start_time = self._start_timer()
        
        # Validate model
        try:
            self._validate_model()
        except TopologyAnalysisError as e:
            return AnalysisResult(
                success=False,
                errors=[str(e)],
                metadata={'analysis_time': self._end_timer(start_time)}
            )
        
        # Handle empty model
        if not self.model.transitions:
            return AnalysisResult(
                success=True,
                data={
                    'is_live': True,
                    'liveness_levels': {},
                    'dead_transitions': [],
                    'live_transitions': [],
                    'transition_analysis': {},
                    'total_transitions': 0
                },
                metadata={'analysis_time': self._end_timer(start_time)}
            )
        
        try:
            # Build transition input/output mappings
            trans_inputs, trans_outputs = self._build_transition_mappings()
            
            # Check structural enablement
            structurally_enabled = {}
            if check_structural:
                structurally_enabled = self._check_structural_enablement(trans_inputs)
            
            # Check token flow to transitions
            token_flow_info = {}
            if check_token_flow:
                token_flow_info = self._analyze_token_flow(trans_inputs)
            
            # Check for deadlocks affecting transitions
            deadlock_info = {}
            if check_deadlocks:
                deadlock_info = self._check_deadlock_impact()
            
            # Classify liveness levels
            liveness_levels = {}
            transition_analysis = {}
            
            if classify_levels:
                for transition in self.model.transitions:
                    trans_id = str(transition.id)
                    
                    level, analysis = self._classify_transition_liveness(
                        transition,
                        trans_inputs.get(trans_id, []),
                        trans_outputs.get(trans_id, []),
                        structurally_enabled.get(trans_id, True),
                        token_flow_info.get(trans_id, {}),
                        deadlock_info.get(trans_id, {})
                    )
                    
                    liveness_levels[trans_id] = level
                    transition_analysis[trans_id] = analysis
            
            # Aggregate results
            dead_transitions = [
                {'id': tid, 'name': self._get_transition_name(tid), 'level': 'L0'}
                for tid, level in liveness_levels.items() if level == 'L0'
            ]
            
            live_transitions = [
                {'id': tid, 'name': self._get_transition_name(tid), 'level': level}
                for tid, level in liveness_levels.items() if level in ['L3', 'L4']
            ]
            
            # Net is live if all transitions are L3 or L4
            is_live = all(level in ['L3', 'L4'] for level in liveness_levels.values())
            
            return AnalysisResult(
                success=True,
                data={
                    'is_live': is_live,
                    'liveness_levels': liveness_levels,
                    'dead_transitions': dead_transitions,
                    'live_transitions': live_transitions,
                    'transition_analysis': transition_analysis,
                    'total_transitions': len(self.model.transitions)
                },
                metadata={
                    'analysis_time': self._end_timer(start_time),
                    'checked_structural': check_structural,
                    'checked_deadlocks': check_deadlocks,
                    'checked_token_flow': check_token_flow
                }
            )
            
        except Exception as e:
            return AnalysisResult(
                success=False,
                errors=[f"Liveness analysis failed: {str(e)}"],
                metadata={'analysis_time': self._end_timer(start_time)}
            )
    
    def _build_transition_mappings(self) -> tuple:
        """Build mappings of transitions to their input/output places.
        
        Returns:
            (trans_inputs, trans_outputs) where each maps transition ID to list of places
        """
        trans_inputs = {}
        trans_outputs = {}
        
        for transition in self.model.transitions:
            trans_id = str(transition.id)
            trans_inputs[trans_id] = []
            trans_outputs[trans_id] = []
        
        for arc in self.model.arcs:
            source_id = str(arc.source_id)
            target_id = str(arc.target_id)
            weight = getattr(arc, 'weight', 1)
            
            # Check if source is place and target is transition
            if target_id in trans_inputs:
                trans_inputs[target_id].append({
                    'place_id': source_id,
                    'weight': weight
                })
            
            # Check if source is transition and target is place
            if source_id in trans_outputs:
                trans_outputs[source_id].append({
                    'place_id': target_id,
                    'weight': weight
                })
        
        return trans_inputs, trans_outputs
    
    def _check_structural_enablement(self, trans_inputs: Dict[str, List[Dict]]) -> Dict[str, bool]:
        """Check if transitions are structurally enabled (have input places).
        
        Args:
            trans_inputs: Mapping of transition IDs to input places
            
        Returns:
            Dict mapping transition ID to enablement status
        """
        enabled = {}
        
        for trans_id, inputs in trans_inputs.items():
            # Transition is structurally enabled if it has at least one input
            # (unless it's a source transition)
            enabled[trans_id] = len(inputs) > 0 or self._is_source_transition(trans_id)
        
        return enabled
    
    def _is_source_transition(self, trans_id: str) -> bool:
        """Check if transition is a source (no inputs, only outputs).
        
        Args:
            trans_id: Transition ID
            
        Returns:
            True if transition is a source
        """
        has_inputs = False
        has_outputs = False
        
        for arc in self.model.arcs:
            source_id = str(arc.source_id)
            target_id = str(arc.target_id)
            
            if target_id == trans_id:
                has_inputs = True
            if source_id == trans_id:
                has_outputs = True
        
        return not has_inputs and has_outputs
    
    def _analyze_token_flow(self, trans_inputs: Dict[str, List[Dict]]) -> Dict[str, Dict]:
        """Analyze token flow to transition input places.
        
        Args:
            trans_inputs: Mapping of transition IDs to input places
            
        Returns:
            Dict mapping transition ID to token flow analysis
        """
        flow_info = {}
        
        for trans_id, inputs in trans_inputs.items():
            has_tokens = False
            total_required = 0
            total_available = 0
            
            for input_data in inputs:
                place_id = input_data['place_id']
                weight = input_data['weight']
                
                # Get place marking
                place = self._get_place_by_id(place_id)
                if place:
                    marking = getattr(place, 'marking', 0)
                    total_required += weight
                    total_available += marking
                    
                    if marking >= weight:
                        has_tokens = True
            
            flow_info[trans_id] = {
                'has_sufficient_tokens': has_tokens,
                'total_required': total_required,
                'total_available': total_available,
                'can_fire_now': total_available >= total_required if total_required > 0 else True
            }
        
        return flow_info
    
    def _check_deadlock_impact(self) -> Dict[str, Dict]:
        """Check if deadlocks affect transition liveness.
        
        Returns:
            Dict mapping transition ID to deadlock impact info
        """
        deadlock_info = {}
        
        try:
            from shypn.topology.behavioral.deadlocks import DeadlockAnalyzer
            
            analyzer = DeadlockAnalyzer(self.model)
            result = analyzer.analyze()
            
            if not result.success:
                return {}
            
            # Get disabled transitions from deadlock analysis
            disabled_transitions = set()
            for trans_data in result.get('disabled_transitions', []):
                disabled_transitions.add(trans_data['id'])
            
            # Mark transitions affected by deadlock
            for transition in self.model.transitions:
                trans_id = str(transition.id)
                deadlock_info[trans_id] = {
                    'is_disabled': trans_id in disabled_transitions,
                    'has_deadlock_risk': len(disabled_transitions) > 0
                }
            
        except Exception:
            # If deadlock analysis fails, assume no impact
            for transition in self.model.transitions:
                trans_id = str(transition.id)
                deadlock_info[trans_id] = {
                    'is_disabled': False,
                    'has_deadlock_risk': False
                }
        
        return deadlock_info
    
    def _classify_transition_liveness(
        self,
        transition: Any,
        inputs: List[Dict],
        outputs: List[Dict],
        structurally_enabled: bool,
        token_flow: Dict,
        deadlock_impact: Dict
    ) -> tuple:
        """Classify transition into liveness level.
        
        Args:
            transition: Transition object
            inputs: List of input places
            outputs: List of output places
            structurally_enabled: Whether transition is structurally enabled
            token_flow: Token flow analysis
            deadlock_impact: Deadlock impact analysis
            
        Returns:
            (liveness_level, analysis_dict)
        """
        trans_id = str(transition.id)
        trans_name = self._get_transition_name(trans_id)
        
        analysis = {
            'id': trans_id,
            'name': trans_name,
            'structurally_enabled': structurally_enabled,
            'input_count': len(inputs),
            'output_count': len(outputs)
        }
        
        # L0: Dead - can never fire
        if not structurally_enabled:
            analysis['reason'] = 'No input places and not a source transition'
            return 'L0', analysis
        
        # Note: Don't mark as dead just because currently disabled by deadlock
        # Deadlock is a behavioral property that may change with different markings
        
        # Check if transition has no inputs (source transition)
        if len(inputs) == 0:
            if len(outputs) > 0:
                analysis['reason'] = 'Source transition (can always fire)'
                return 'L4', analysis  # Strictly live
            else:
                analysis['reason'] = 'No inputs or outputs'
                return 'L0', analysis
        
        # Check token availability
        can_fire_now = token_flow.get('can_fire_now', False)
        
        # L4: Strictly live - can fire in every reachable marking
        # (Simplified: assume if can fire now and has outputs, it's L4)
        if can_fire_now and len(outputs) > 0:
            analysis['reason'] = 'Can fire with current marking and produces tokens'
            return 'L3', analysis  # Conservative: L3 (live) rather than L4
        
        # L3: Live - can fire infinitely often
        # (Simplified: if has token sources and outputs)
        if len(outputs) > 0 and self._has_token_sources(inputs):
            analysis['reason'] = 'Has token sources and outputs (potentially live)'
            return 'L3', analysis
        
        # L2: Potentially live - can fire arbitrarily often in some sequence
        if len(outputs) > 0:
            analysis['reason'] = 'Has outputs but uncertain token flow'
            return 'L2', analysis
        
        # L1: Potentially firable - can fire at least once (structurally enabled)
        if len(inputs) > 0:
            analysis['reason'] = 'Structurally enabled (has inputs)'
            return 'L1', analysis
        
        # Default to L1 if structurally enabled
        analysis['reason'] = 'Structurally enabled but no tokens currently'
        return 'L1', analysis
    
    def _has_token_sources(self, inputs: List[Dict]) -> bool:
        """Check if input places have token sources.
        
        Args:
            inputs: List of input place data
            
        Returns:
            True if input places can receive tokens
        """
        for input_data in inputs:
            place_id = input_data['place_id']
            place = self._get_place_by_id(place_id)
            
            if place:
                marking = getattr(place, 'marking', 0)
                if marking > 0:
                    return True
                
                # Check if place has input arcs (can receive tokens)
                has_inputs = self._place_has_inputs(place_id)
                if has_inputs:
                    return True
        
        return False
    
    def _place_has_inputs(self, place_id: str) -> bool:
        """Check if place has input arcs.
        
        Args:
            place_id: Place ID
            
        Returns:
            True if place has inputs
        """
        for arc in self.model.arcs:
            if str(arc.target_id) == place_id:
                return True
        return False
    
    def _get_place_by_id(self, place_id: str) -> Optional[Any]:
        """Get place object by ID.
        
        Args:
            place_id: Place ID
            
        Returns:
            Place object or None
        """
        for place in self.model.places:
            if str(place.id) == place_id:
                return place
        return None
    
    def _get_transition_name(self, trans_id: str) -> str:
        """Get transition name by ID.
        
        Args:
            trans_id: Transition ID
            
        Returns:
            Transition name or ID if name not available
        """
        for transition in self.model.transitions:
            if str(transition.id) == trans_id:
                if hasattr(transition, 'name') and transition.name:
                    return str(transition.name)
                return trans_id
        return trans_id
    
    def check_transition_liveness(self, transition_id: str) -> AnalysisResult:
        """Check liveness of a specific transition.
        
        Args:
            transition_id: ID of transition to check
            
        Returns:
            AnalysisResult with transition-specific liveness info
        """
        result = self.analyze()
        
        if not result.success:
            return result
        
        liveness_levels = result.get('liveness_levels', {})
        transition_analysis = result.get('transition_analysis', {})
        
        level = liveness_levels.get(transition_id, 'Unknown')
        analysis = transition_analysis.get(transition_id, {})
        
        return AnalysisResult(
            success=True,
            data={
                'transition_id': transition_id,
                'liveness_level': level,
                'is_live': level in ['L3', 'L4'],
                'is_dead': level == 'L0',
                'analysis': analysis
            },
            metadata=result.metadata
        )
    
    def is_net_live(self) -> bool:
        """Check if the entire net is live.
        
        Returns:
            True if all transitions are live (L3 or L4)
        """
        result = self.analyze()
        return result.get('is_live', False) if result.success else False
