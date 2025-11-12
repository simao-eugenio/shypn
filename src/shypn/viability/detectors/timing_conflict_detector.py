#!/usr/bin/env python3
"""Timing Conflict Detector - Detects mutual timing window interference.

This detector identifies situations where timed transitions with shared
input places interfere with each other's timing windows, causing livelock.

Pattern Detected:
    - Two or more timed transitions T1, T2, ...
    - T1 and T2 share input places
    - When T1 fires, it consumes tokens that T2 needs, resetting T2's timer
    - When T2 fires, it consumes tokens that T1 needs, resetting T1's timer
    - Neither transition can accumulate enough elapsed time to satisfy timing window
    - Results in permanent livelock despite sufficient tokens being available

Biological Context:
    In metabolic networks, this usually indicates that transitions should be
    continuous (enzyme-catalyzed reactions) rather than timed (scheduled events).
    Continuous transitions don't have timing windows and can fire whenever
    substrates are available.

Example:
    P1 + P4 → T1 → P2    (timed, [1.0, 1.0])
    P2 + P5 → T2 → P1    (timed, [1.0, 1.0])
    
    Both transitions need 1 second to fire, but they keep disabling each other
    by consuming shared metabolites, creating a livelock.

Repair Suggestions:
    1. Convert to continuous transitions (preserves biological semantics)
    2. Use immediate transitions (removes timing constraints)
    3. Separate token pools (remove shared inputs)
    4. Adjust timing windows (make them shorter or zero)
"""

from typing import List, Dict, Any, Set, Tuple
from ..issue import ViabilityIssue


class TimingConflictDetector:
    """Detects mutual timing window interference between timed transitions.
    
    This detector analyzes timed transitions to find patterns where they
    interfere with each other's timing windows by sharing input places.
    """
    
    def __init__(self):
        """Initialize the detector."""
        self.name = "Timing Conflict Detector"
        self.category = "structural"
    
    def detect(self, model, kb=None) -> List[ViabilityIssue]:
        """Detect timing conflicts in the model.
        
        Args:
            model: Petri net model with places, transitions, arcs
            kb: Knowledge base (optional, for enhanced analysis)
            
        Returns:
            List of detected timing conflict issues
        """
        issues = []
        
        # Get all timed transitions
        timed_transitions = [
            t for t in model.transitions 
            if t.transition_type == 'timed'
        ]
        
        if len(timed_transitions) < 2:
            # Need at least 2 timed transitions for conflict
            return issues
        
        # Build input place mapping for timed transitions
        # input_places[tid] = set of place IDs that transition tid consumes from
        input_places = {}
        for t in timed_transitions:
            places = set()
            for arc in model.arcs:
                if arc.target_id == t.id and arc.source_type == 'place':
                    places.add(arc.source_id)
            input_places[t.id] = places
        
        # Check for shared input places between timed transitions
        conflicts = []
        for i, t1 in enumerate(timed_transitions):
            for t2 in timed_transitions[i+1:]:
                shared = input_places[t1.id] & input_places[t2.id]
                if shared:
                    # Check if they also form a cycle (consume each other's outputs)
                    t1_outputs = set()
                    t2_outputs = set()
                    
                    for arc in model.arcs:
                        if arc.source_id == t1.id and arc.target_type == 'place':
                            t1_outputs.add(arc.target_id)
                        if arc.source_id == t2.id and arc.target_type == 'place':
                            t2_outputs.add(arc.target_id)
                    
                    # Check if outputs are inputs to the other
                    t1_feeds_t2 = bool(t1_outputs & input_places[t2.id])
                    t2_feeds_t1 = bool(t2_outputs & input_places[t1.id])
                    
                    conflicts.append({
                        't1': t1,
                        't2': t2,
                        'shared_inputs': shared,
                        'cyclic': t1_feeds_t2 or t2_feeds_t1,
                        't1_feeds_t2': t1_feeds_t2,
                        't2_feeds_t1': t2_feeds_t1
                    })
        
        # Create issues for detected conflicts
        for conflict in conflicts:
            t1 = conflict['t1']
            t2 = conflict['t2']
            shared = conflict['shared_inputs']
            cyclic = conflict['cyclic']
            
            # Get timing windows
            t1_window = self._get_timing_window(t1)
            t2_window = self._get_timing_window(t2)
            
            severity = 'high' if cyclic else 'medium'
            
            description = (
                f"Timing conflict between {t1.id} and {t2.id}: "
                f"shared input places {', '.join(sorted(shared))} cause mutual interference. "
            )
            
            if cyclic:
                description += (
                    "These transitions form a cycle where each consumes the other's outputs, "
                    "creating a livelock where neither can satisfy timing requirements. "
                )
            else:
                description += (
                    "When one transition fires, it may disable the other by consuming shared tokens, "
                    "resetting its timing window. "
                )
            
            description += (
                f"{t1.id} has timing window {t1_window}, "
                f"{t2.id} has timing window {t2_window}."
            )
            
            # Build repair suggestions
            repairs = []
            
            # Suggestion 1: Convert to continuous (best for biological models)
            repairs.append({
                'action': 'convert_to_continuous',
                'description': (
                    f"Convert {t1.id} and {t2.id} to continuous transitions. "
                    "This preserves biological semantics for enzyme-catalyzed reactions "
                    "that occur continuously when substrates are available."
                ),
                'confidence': 0.95,
                'transitions': [t1.id, t2.id],
                'new_type': 'continuous'
            })
            
            # Suggestion 2: Convert to immediate (removes timing)
            repairs.append({
                'action': 'convert_to_immediate',
                'description': (
                    f"Convert {t1.id} and {t2.id} to immediate transitions. "
                    "This removes timing constraints and allows firing as soon as enabled."
                ),
                'confidence': 0.7,
                'transitions': [t1.id, t2.id],
                'new_type': 'immediate'
            })
            
            # Suggestion 3: Adjust timing windows
            repairs.append({
                'action': 'adjust_timing_windows',
                'description': (
                    f"Set timing windows to [0.0, ∞] for {t1.id} and {t2.id}. "
                    "This allows them to fire immediately when enabled without waiting."
                ),
                'confidence': 0.6,
                'transitions': [t1.id, t2.id],
                'earliest': 0.0,
                'latest': float('inf')
            })
            
            # Suggestion 4: Add initial tokens (if cyclic)
            if cyclic:
                repairs.append({
                    'action': 'add_initial_tokens',
                    'description': (
                        f"Add initial tokens to places {', '.join(sorted(shared))} "
                        "to ensure at least one transition can complete its timing window."
                    ),
                    'confidence': 0.5,
                    'places': list(shared),
                    'initial_marking': 1
                })
            
            issue = ViabilityIssue(
                category='structural',
                severity=severity,
                title=f'Timing Conflict: {t1.id} ↔ {t2.id}',
                description=description,
                affected_elements=[t1.id, t2.id] + list(shared),
                repair_suggestions=repairs,
                detector_name=self.name
            )
            
            issues.append(issue)
        
        return issues
    
    def _get_timing_window(self, transition) -> str:
        """Get timing window description for a transition.
        
        Args:
            transition: Transition object
            
        Returns:
            String like "[1.0, 1.0]" or "[0.0, ∞]"
        """
        # Check if transition has explicit earliest/latest
        props = getattr(transition, 'properties', {})
        
        if 'earliest' in props or 'latest' in props:
            earliest = props.get('earliest', 0.0)
            latest = props.get('latest', float('inf'))
        else:
            # Use rate as timing window
            rate = getattr(transition, 'rate', None)
            if rate is not None:
                try:
                    delay = float(rate) if isinstance(rate, (int, float)) else 1.0
                    earliest = delay
                    latest = delay
                except:
                    earliest = 1.0
                    latest = 1.0
            else:
                earliest = 1.0
                latest = 1.0
        
        # Format for display
        latest_str = '∞' if latest == float('inf') else f'{latest:.1f}'
        return f'[{earliest:.1f}, {latest_str}]'
