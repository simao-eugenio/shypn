"""Deadlock detection analyzer for Petri nets.

A deadlock is a state where no transition can fire, causing the system to halt.
Deadlocks can be:
1. **Structural deadlocks**: Inevitable due to net structure (empty siphons)
2. **Behavioral deadlocks**: Depend on current marking and can be avoided

Detection approaches:
- Structural: Check for empty siphons (if siphon is empty, it stays empty)
- Behavioral: Check if any transition is enabled in current marking
- Reachability: Check if deadlock states are reachable

Mathematical Background:
- Commoner, F. et al. (1971). "Marked directed graphs"
- Ezpeleta, J. et al. (1995). "A Petri net based deadlock prevention policy"
- Li, Z. & Zhou, M. (2008). "Deadlock resolution in automated manufacturing systems"

Implementation approach:
- Leverage siphon analysis for structural deadlock detection
- Check enablement of all transitions for behavioral deadlock
- Classify deadlock severity and provide recovery suggestions
"""

from typing import Any, Dict, List, Set, Optional
import numpy as np

from shypn.topology.base.topology_analyzer import TopologyAnalyzer
from shypn.topology.base.analysis_result import AnalysisResult
from shypn.topology.base.exceptions import TopologyAnalysisError


class DeadlockAnalyzer(TopologyAnalyzer):
    """Analyzer for detecting deadlocks in Petri nets.
    
    A deadlock occurs when no transition can fire, halting the system.
    This analyzer detects both structural and behavioral deadlocks.
    
    Structural deadlocks: Due to empty siphons (inevitable)
    Behavioral deadlocks: Due to current marking (potentially avoidable)
    
    Example:
        >>> analyzer = DeadlockAnalyzer(model)
        >>> result = analyzer.analyze(check_siphons=True)
        >>> if result.get('has_deadlock'):
        ...     print(f"Deadlock detected: {result.get('deadlock_type')}")
    """
    
    def __init__(self, model: Any):
        """Initialize deadlock analyzer.
        
        Args:
            model: Petri net model with places, transitions, and arcs attributes
        """
        super().__init__(model)
        self.name = "Deadlocks"
        self.description = "Detect structural and behavioral deadlocks"
    
    def analyze(
        self,
        check_siphons: bool = True,
        check_enablement: bool = True,
        suggest_recovery: bool = True
    ) -> AnalysisResult:
        """Analyze the Petri net for deadlocks.
        
        Args:
            check_siphons: Whether to check for structural deadlocks (empty siphons)
            check_enablement: Whether to check current marking for behavioral deadlocks
            suggest_recovery: Whether to suggest recovery actions
            
        Returns:
            AnalysisResult with:
            - has_deadlock: Boolean indicating if deadlock exists
            - deadlock_type: Type of deadlock (structural, behavioral, none)
            - empty_siphons: List of empty siphons (structural cause)
            - disabled_transitions: List of all disabled transitions
            - deadlock_places: Places involved in deadlock
            - severity: Severity level (critical, high, medium, low, none)
            - recovery_suggestions: List of suggested recovery actions
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
        if not self.model.places or not self.model.transitions:
            return AnalysisResult(
                success=True,
                data={
                    'has_deadlock': True,  # No transitions = deadlock
                    'deadlock_type': 'structural',
                    'empty_siphons': [],
                    'disabled_transitions': [],
                    'deadlock_places': [],
                    'severity': 'critical',
                    'recovery_suggestions': ['Add transitions to the model']
                },
                metadata={'analysis_time': self._end_timer(start_time)}
            )
        
        try:
            # Check for structural deadlocks (empty siphons)
            empty_siphons = []
            structural_deadlock = False
            
            if check_siphons:
                empty_siphons = self._find_empty_siphons()
                structural_deadlock = len(empty_siphons) > 0
            
            # Check for behavioral deadlocks (no enabled transitions)
            disabled_transitions = []
            behavioral_deadlock = False
            
            if check_enablement:
                disabled_transitions = self._find_disabled_transitions()
                behavioral_deadlock = len(disabled_transitions) == len(self.model.transitions)
            
            # Determine deadlock status
            has_deadlock = structural_deadlock or behavioral_deadlock
            
            if structural_deadlock:
                deadlock_type = 'structural'
            elif behavioral_deadlock:
                deadlock_type = 'behavioral'
            else:
                deadlock_type = 'none'
            
            # Find places involved in deadlock
            deadlock_places = self._identify_deadlock_places(
                empty_siphons,
                disabled_transitions
            )
            
            # Classify severity
            severity = self._classify_deadlock_severity(
                deadlock_type,
                len(empty_siphons),
                len(disabled_transitions),
                len(deadlock_places)
            )
            
            # Generate recovery suggestions
            recovery_suggestions = []
            if suggest_recovery and has_deadlock:
                recovery_suggestions = self._generate_recovery_suggestions(
                    deadlock_type,
                    empty_siphons,
                    disabled_transitions,
                    deadlock_places
                )
            
            return AnalysisResult(
                success=True,
                data={
                    'has_deadlock': has_deadlock,
                    'deadlock_type': deadlock_type,
                    'empty_siphons': empty_siphons,
                    'disabled_transitions': disabled_transitions,
                    'deadlock_places': deadlock_places,
                    'severity': severity,
                    'recovery_suggestions': recovery_suggestions,
                    'total_transitions': len(self.model.transitions),
                    'enabled_transitions': len(self.model.transitions) - len(disabled_transitions)
                },
                metadata={
                    'analysis_time': self._end_timer(start_time),
                    'checked_siphons': check_siphons,
                    'checked_enablement': check_enablement
                }
            )
            
        except Exception as e:
            return AnalysisResult(
                success=False,
                errors=[f"Deadlock analysis failed: {str(e)}"],
                metadata={'analysis_time': self._end_timer(start_time)}
            )
    
    def _find_empty_siphons(self) -> List[Dict[str, Any]]:
        """Find all empty siphons (structural deadlock indicators).
        
        Returns:
            List of empty siphon dictionaries
        """
        try:
            from shypn.topology.structural.siphons import SiphonAnalyzer
            
            siphon_analyzer = SiphonAnalyzer(self.model)
            result = siphon_analyzer.analyze(check_marking=True)
            
            if not result.success:
                return []
            
            siphons = result.get('siphons', [])
            return [s for s in siphons if s.get('is_empty', False)]
            
        except Exception:
            return []
    
    def _find_disabled_transitions(self) -> List[Dict[str, Any]]:
        """Find all transitions that cannot fire with current marking.
        
        Returns:
            List of disabled transition dictionaries
        """
        disabled = []
        
        # Build place marking map
        place_marking = {
            str(p.id): getattr(p, 'marking', 0)
            for p in self.model.places
        }
        
        # Check each transition
        for transition in self.model.transitions:
            trans_id = str(transition.id)
            trans_name = str(transition.name) if hasattr(transition, 'name') and transition.name else trans_id
            
            # Find input arcs (place → transition)
            input_arcs = [
                arc for arc in self.model.arcs
                if str(arc.target_id) == trans_id
            ]
            
            # Check if all input places have enough tokens
            is_enabled = True
            required_tokens = {}
            
            for arc in input_arcs:
                place_id = str(arc.source_id)
                weight = getattr(arc, 'weight', 1)
                required_tokens[place_id] = weight
                
                if place_marking.get(place_id, 0) < weight:
                    is_enabled = False
            
            if not is_enabled:
                disabled.append({
                    'id': trans_id,
                    'name': trans_name,
                    'required_tokens': required_tokens,
                    'reason': 'Insufficient tokens in input places'
                })
        
        return disabled
    
    def _identify_deadlock_places(
        self,
        empty_siphons: List[Dict[str, Any]],
        disabled_transitions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Identify places involved in deadlock.
        
        Args:
            empty_siphons: List of empty siphon dictionaries
            disabled_transitions: List of disabled transition dictionaries
            
        Returns:
            List of place dictionaries involved in deadlock
        """
        deadlock_place_ids = set()
        
        # Add places from empty siphons
        for siphon in empty_siphons:
            deadlock_place_ids.update(siphon.get('place_ids', []))
        
        # Add places that prevent transitions from firing
        for trans in disabled_transitions:
            required_tokens = trans.get('required_tokens', {})
            deadlock_place_ids.update(required_tokens.keys())
        
        # Build place info
        place_map = {str(p.id): p for p in self.model.places}
        deadlock_places = []
        
        for place_id in deadlock_place_ids:
            if place_id in place_map:
                place = place_map[place_id]
                deadlock_places.append({
                    'id': place_id,
                    'name': str(place.name) if hasattr(place, 'name') and place.name else place_id,
                    'marking': getattr(place, 'marking', 0)
                })
        
        return deadlock_places
    
    def _classify_deadlock_severity(
        self,
        deadlock_type: str,
        num_empty_siphons: int,
        num_disabled_transitions: int,
        num_deadlock_places: int
    ) -> str:
        """Classify deadlock severity.
        
        Args:
            deadlock_type: Type of deadlock (structural, behavioral, none)
            num_empty_siphons: Number of empty siphons
            num_disabled_transitions: Number of disabled transitions
            num_deadlock_places: Number of places involved
            
        Returns:
            Severity level string
        """
        if deadlock_type == 'none':
            return 'none'
        
        if deadlock_type == 'structural':
            # Structural deadlocks are always critical (inevitable)
            return 'critical'
        
        # Behavioral deadlock severity depends on scale
        if num_disabled_transitions == len(self.model.transitions):
            # All transitions disabled = critical
            return 'critical'
        elif num_disabled_transitions > len(self.model.transitions) * 0.75:
            # >75% disabled = high
            return 'high'
        elif num_disabled_transitions > len(self.model.transitions) * 0.5:
            # >50% disabled = medium
            return 'medium'
        else:
            # Otherwise = low
            return 'low'
    
    def _generate_recovery_suggestions(
        self,
        deadlock_type: str,
        empty_siphons: List[Dict[str, Any]],
        disabled_transitions: List[Dict[str, Any]],
        deadlock_places: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate recovery suggestions for deadlock.
        
        Args:
            deadlock_type: Type of deadlock
            empty_siphons: List of empty siphons
            disabled_transitions: List of disabled transitions
            deadlock_places: List of places involved
            
        Returns:
            List of recovery suggestion strings
        """
        suggestions = []
        
        if deadlock_type == 'structural':
            suggestions.append("STRUCTURAL DEADLOCK: Requires net redesign")
            
            for siphon in empty_siphons:
                place_names = ', '.join(siphon.get('place_names', []))
                suggestions.append(f"Add control place to prevent siphon {{{place_names}}} from emptying")
            
            suggestions.append("Consider adding monitor places or resource allocation policies")
        
        elif deadlock_type == 'behavioral':
            suggestions.append("BEHAVIORAL DEADLOCK: Add tokens to enable transitions")
            
            # Suggest adding tokens to specific places
            for place in deadlock_places:
                if place.get('marking', 0) == 0:
                    suggestions.append(f"Add tokens to place '{place['name']}' ({place['id']})")
            
            suggestions.append("Or reset the system to a safe initial marking")
        
        return suggestions
    
    def check_for_deadlock_freedom(self) -> AnalysisResult:
        """Check if the net is deadlock-free (no structural deadlocks).
        
        Returns:
            AnalysisResult indicating if net is structurally deadlock-free
        """
        result = self.analyze(check_siphons=True, check_enablement=False)
        
        if not result.success:
            return result
        
        is_deadlock_free = result.get('deadlock_type') == 'none'
        
        return AnalysisResult(
            success=True,
            data={
                'is_deadlock_free': is_deadlock_free,
                'empty_siphons': result.get('empty_siphons', []),
                'can_deadlock': not is_deadlock_free
            },
            metadata=result.metadata
        )
