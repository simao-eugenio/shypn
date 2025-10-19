"""Fairness analyzer for Petri nets.

Fairness ensures that enabled transitions eventually get the opportunity to fire,
preventing starvation scenarios where some transitions are perpetually ignored.

Fairness Types:
- **Bounded Fairness**: Every transition fires at least once within k steps
- **Unconditional Fairness**: Every continuously enabled transition eventually fires
- **Impartial Fairness**: Transitions in conflict get equal firing opportunities
- **Just Fairness**: Every enabled transition fires infinitely often

Analysis approaches:
- Structural: Check for conflicts and resource competition
- Behavioral: Analyze firing sequences for fairness violations
- Stochastic: Assess probability of starvation

Mathematical Background:
- Best, E. (1987). "Fairness and conspiracies"
- Vogler, W. (1991). "Fairness and infinite behavior"
- Carstensen, H. (1987). "Fairness in Petri nets"

Implementation approach:
- Identify conflicting transitions (shared input places)
- Analyze transition priority relationships
- Detect potential starvation scenarios
- Classify fairness level (strong/weak/none)
"""

from typing import Any, Dict, List, Set, Optional, Tuple
import numpy as np

from shypn.topology.base.topology_analyzer import TopologyAnalyzer
from shypn.topology.base.analysis_result import AnalysisResult
from shypn.topology.base.exceptions import TopologyAnalysisError


class FairnessAnalyzer(TopologyAnalyzer):
    """Analyzer for checking fairness properties of Petri nets.
    
    Fairness prevents starvation by ensuring all enabled transitions
    eventually get the opportunity to fire.
    
    Example:
        >>> analyzer = FairnessAnalyzer(model)
        >>> result = analyzer.analyze()
        >>> if result.get('is_fair'):
        ...     print(f"Net has {result.get('fairness_level')} fairness")
    """
    
    def __init__(self, model: Any):
        """Initialize fairness analyzer.
        
        Args:
            model: Petri net model with places, transitions, and arcs attributes
        """
        super().__init__(model)
        self.name = "Fairness"
        self.description = "Check if transitions get fair firing opportunities"
    
    def analyze(
        self,
        check_conflicts: bool = True,
        check_starvation: bool = True,
        check_priorities: bool = True,
        classify_fairness: bool = True
    ) -> AnalysisResult:
        """Analyze fairness properties of the Petri net.
        
        Args:
            check_conflicts: Identify conflicting transitions
            check_starvation: Detect potential starvation scenarios
            check_priorities: Analyze transition priority relationships
            classify_fairness: Classify fairness level (strong/weak/none)
            
        Returns:
            AnalysisResult with:
            - is_fair: Boolean indicating if net has fairness guarantees
            - fairness_level: 'strong', 'weak', or 'none'
            - conflicting_transitions: Sets of transitions competing for resources
            - starvation_risk: Transitions at risk of starvation
            - priority_conflicts: Transitions with priority issues
            - fairness_violations: List of detected fairness violations
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
                    'is_fair': True,
                    'fairness_level': 'strong',
                    'conflicting_transitions': [],
                    'starvation_risk': [],
                    'priority_conflicts': [],
                    'fairness_violations': [],
                    'total_transitions': 0
                },
                metadata={'analysis_time': self._end_timer(start_time)}
            )
        
        try:
            # Find conflicting transitions
            conflicts = []
            if check_conflicts:
                conflicts = self._find_conflicts()
            
            # Check for starvation risk
            starvation_risk = []
            if check_starvation:
                starvation_risk = self._check_starvation_risk(conflicts)
            
            # Analyze priorities
            priority_conflicts = []
            if check_priorities:
                priority_conflicts = self._analyze_priorities(conflicts)
            
            # Classify fairness level
            fairness_level = 'none'
            fairness_violations = []
            
            if classify_fairness:
                fairness_level, fairness_violations = self._classify_fairness(
                    conflicts,
                    starvation_risk,
                    priority_conflicts
                )
            
            # Determine if net is fair
            is_fair = fairness_level in ['strong', 'weak']
            
            return AnalysisResult(
                success=True,
                data={
                    'is_fair': is_fair,
                    'fairness_level': fairness_level,
                    'conflicting_transitions': conflicts,
                    'starvation_risk': starvation_risk,
                    'priority_conflicts': priority_conflicts,
                    'fairness_violations': fairness_violations,
                    'total_transitions': len(self.model.transitions),
                    'total_conflicts': len(conflicts)
                },
                metadata={
                    'analysis_time': self._end_timer(start_time),
                    'checked_conflicts': check_conflicts,
                    'checked_starvation': check_starvation,
                    'checked_priorities': check_priorities
                }
            )
            
        except Exception as e:
            return AnalysisResult(
                success=False,
                errors=[f"Fairness analysis failed: {str(e)}"],
                metadata={'analysis_time': self._end_timer(start_time)}
            )
    
    def _find_conflicts(self) -> List[Dict[str, Any]]:
        """Find sets of transitions that conflict (share input places).
        
        Transitions conflict if they compete for tokens from the same place.
        
        Returns:
            List of conflict dictionaries with transition sets and shared places
        """
        conflicts = []
        
        # Build mapping of places to transitions that consume from them
        place_consumers = {}
        
        for arc in self.model.arcs:
            source_id = str(arc.source_id)
            target_id = str(arc.target_id)
            
            # Check if this is a place → transition arc
            if self._is_place(source_id) and self._is_transition(target_id):
                if source_id not in place_consumers:
                    place_consumers[source_id] = []
                place_consumers[source_id].append(target_id)
        
        # Find places with multiple consumers (conflict points)
        for place_id, consumers in place_consumers.items():
            if len(consumers) > 1:
                place_name = self._get_place_name(place_id)
                transition_names = [self._get_transition_name(tid) for tid in consumers]
                
                conflicts.append({
                    'place_id': place_id,
                    'place_name': place_name,
                    'transition_ids': consumers,
                    'transition_names': transition_names,
                    'conflict_size': len(consumers)
                })
        
        return conflicts
    
    def _check_starvation_risk(self, conflicts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Check for transitions at risk of starvation.
        
        A transition risks starvation if:
        - It conflicts with higher-priority or more frequently enabled transitions
        - Its input places have limited token supply
        - It competes in large conflict sets
        
        Args:
            conflicts: List of conflict sets
            
        Returns:
            List of transitions at risk with reasons
        """
        starvation_risk = []
        
        for conflict in conflicts:
            place_id = conflict['place_id']
            trans_ids = conflict['transition_ids']
            
            # Get place marking
            place = self._get_place_by_id(place_id)
            marking = getattr(place, 'marking', 0) if place else 0
            
            # Large conflict sets increase starvation risk
            if len(trans_ids) > 3:
                for trans_id in trans_ids:
                    trans_name = self._get_transition_name(trans_id)
                    starvation_risk.append({
                        'transition_id': trans_id,
                        'transition_name': trans_name,
                        'reason': f'Large conflict set ({len(trans_ids)} transitions) at place {conflict["place_name"]}',
                        'risk_level': 'high' if len(trans_ids) > 5 else 'medium'
                    })
            
            # Low token count with conflicts increases risk
            elif marking < len(trans_ids) and marking > 0:
                for trans_id in trans_ids:
                    trans_name = self._get_transition_name(trans_id)
                    starvation_risk.append({
                        'transition_id': trans_id,
                        'transition_name': trans_name,
                        'reason': f'Limited tokens ({marking}) for {len(trans_ids)} competing transitions',
                        'risk_level': 'medium'
                    })
        
        # Deduplicate by transition_id
        seen = set()
        unique_risks = []
        for risk in starvation_risk:
            tid = risk['transition_id']
            if tid not in seen:
                seen.add(tid)
                unique_risks.append(risk)
        
        return unique_risks
    
    def _analyze_priorities(self, conflicts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze priority relationships between conflicting transitions.
        
        Args:
            conflicts: List of conflict sets
            
        Returns:
            List of priority conflicts
        """
        priority_conflicts = []
        
        for conflict in conflicts:
            trans_ids = conflict['transition_ids']
            
            # Check if transitions have explicit priorities
            priorities = {}
            for trans_id in trans_ids:
                trans = self._get_transition_by_id(trans_id)
                if trans and hasattr(trans, 'priority'):
                    priorities[trans_id] = trans.priority
            
            # If priorities exist and differ, there's a priority-based conflict
            if priorities and len(set(priorities.values())) > 1:
                priority_conflicts.append({
                    'place_id': conflict['place_id'],
                    'place_name': conflict['place_name'],
                    'transitions': [
                        {
                            'id': tid,
                            'name': self._get_transition_name(tid),
                            'priority': priorities.get(tid, 0)
                        }
                        for tid in trans_ids
                    ],
                    'issue': 'Explicit priority differences may cause starvation'
                })
        
        return priority_conflicts
    
    def _classify_fairness(
        self,
        conflicts: List[Dict[str, Any]],
        starvation_risk: List[Dict[str, Any]],
        priority_conflicts: List[Dict[str, Any]]
    ) -> Tuple[str, List[str]]:
        """Classify the fairness level of the net.
        
        Args:
            conflicts: Conflict sets
            starvation_risk: Transitions at risk
            priority_conflicts: Priority-based conflicts
            
        Returns:
            (fairness_level, violations) tuple
        """
        violations = []
        
        # No conflicts = strong fairness (all transitions can fire without competition)
        if not conflicts:
            return 'strong', []
        
        # High starvation risk = no fairness
        high_risk_count = sum(1 for r in starvation_risk if r['risk_level'] == 'high')
        if high_risk_count > 0:
            violations.append(f'{high_risk_count} transition(s) at high starvation risk')
            return 'none', violations
        
        # Priority conflicts = potential unfairness
        if priority_conflicts:
            violations.append(f'{len(priority_conflicts)} priority conflict(s) detected')
            return 'weak', violations
        
        # Medium starvation risk = weak fairness
        if starvation_risk:
            violations.append(f'{len(starvation_risk)} transition(s) at medium starvation risk')
            return 'weak', violations
        
        # Conflicts exist but no severe issues = weak fairness
        if conflicts:
            return 'weak', []
        
        return 'strong', []
    
    def _is_place(self, element_id: str) -> bool:
        """Check if element ID corresponds to a place.
        
        Args:
            element_id: Element ID
            
        Returns:
            True if element is a place
        """
        return any(str(p.id) == element_id for p in self.model.places)
    
    def _is_transition(self, element_id: str) -> bool:
        """Check if element ID corresponds to a transition.
        
        Args:
            element_id: Element ID
            
        Returns:
            True if element is a transition
        """
        return any(str(t.id) == element_id for t in self.model.transitions)
    
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
    
    def _get_transition_by_id(self, trans_id: str) -> Optional[Any]:
        """Get transition object by ID.
        
        Args:
            trans_id: Transition ID
            
        Returns:
            Transition object or None
        """
        for transition in self.model.transitions:
            if str(transition.id) == trans_id:
                return transition
        return None
    
    def _get_place_name(self, place_id: str) -> str:
        """Get place name by ID.
        
        Args:
            place_id: Place ID
            
        Returns:
            Place name or ID if name not available
        """
        place = self._get_place_by_id(place_id)
        if place and hasattr(place, 'name') and place.name:
            return str(place.name)
        return place_id
    
    def _get_transition_name(self, trans_id: str) -> str:
        """Get transition name by ID.
        
        Args:
            trans_id: Transition ID
            
        Returns:
            Transition name or ID if name not available
        """
        trans = self._get_transition_by_id(trans_id)
        if trans and hasattr(trans, 'name') and trans.name:
            return str(trans.name)
        return trans_id
    
    def check_transition_fairness(self, transition_id: str) -> AnalysisResult:
        """Check fairness for a specific transition.
        
        Args:
            transition_id: ID of transition to check
            
        Returns:
            AnalysisResult with transition-specific fairness info
        """
        result = self.analyze()
        
        if not result.success:
            return result
        
        # Check if transition is in any conflict
        conflicts = result.get('conflicting_transitions', [])
        in_conflict = any(
            transition_id in c['transition_ids']
            for c in conflicts
        )
        
        # Check if transition has starvation risk
        starvation_risks = result.get('starvation_risk', [])
        has_risk = any(
            r['transition_id'] == transition_id
            for r in starvation_risks
        )
        
        risk_level = 'none'
        if has_risk:
            risk_obj = next(
                r for r in starvation_risks
                if r['transition_id'] == transition_id
            )
            risk_level = risk_obj.get('risk_level', 'unknown')
        
        return AnalysisResult(
            success=True,
            data={
                'transition_id': transition_id,
                'in_conflict': in_conflict,
                'has_starvation_risk': has_risk,
                'risk_level': risk_level,
                'is_fair': not has_risk or risk_level == 'low'
            },
            metadata=result.metadata
        )
