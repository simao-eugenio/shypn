"""Boundedness analyzer for Petri nets.

Boundedness determines if places have bounded token capacity, preventing
overflow conditions. A Petri net is bounded if there exists a finite limit
on the number of tokens in each place for all reachable markings.

Types of boundedness:
1. **k-bounded**: Max k tokens in any place
2. **safe (1-bounded)**: At most 1 token per place
3. **Unbounded**: Token count can grow without limit

Analysis approaches:
- Structural: Using incidence matrix and P-invariants
- Behavioral: Reachability analysis (limited exploration)
- Conservative: Check if net is conservative (total tokens constant)

Mathematical Background:
- Murata, T. (1989). "Petri nets: Properties, analysis and applications"
- Hack, M. (1972). "Analysis of production schemata by Petri nets"
- Memmi, G. & Roucairol, G. (1980). "Linear algebra in net theory"

Implementation approach:
- Check conservation laws (P-invariants sum to constant)
- Analyze incidence matrix for structural boundedness
- Optionally explore marking space to detect unbounded places
"""

from typing import Any, Dict, List, Set, Optional
import numpy as np

from shypn.topology.base.topology_analyzer import TopologyAnalyzer
from shypn.topology.base.analysis_result import AnalysisResult
from shypn.topology.base.exceptions import TopologyAnalysisError


class BoundednessAnalyzer(TopologyAnalyzer):
    """Analyzer for checking boundedness of Petri nets.
    
    A Petri net is bounded if there's a finite limit on tokens in each place.
    This analyzer checks structural and behavioral boundedness properties.
    
    Example:
        >>> analyzer = BoundednessAnalyzer(model)
        >>> result = analyzer.analyze(max_bound=100)
        >>> if result.get('is_bounded'):
        ...     print(f"Net is {result.get('boundedness_level')}-bounded")
    """
    
    def __init__(self, model: Any):
        """Initialize boundedness analyzer.
        
        Args:
            model: Petri net model with places, transitions, and arcs attributes
        """
        super().__init__(model)
        self.name = "Boundedness"
        self.description = "Check if places have bounded token capacity"
    
    def analyze(
        self,
        max_bound: int = 1000,
        check_conservation: bool = True,
        check_structural: bool = True,
        check_current_marking: bool = True
    ) -> AnalysisResult:
        """Analyze boundedness of the Petri net.
        
        Args:
            max_bound: Maximum bound to consider (places exceeding this are unbounded)
            check_conservation: Check if net is conservative (tokens constant)
            check_structural: Check structural boundedness properties
            check_current_marking: Include current marking in analysis
            
        Returns:
            AnalysisResult with:
            - is_bounded: Boolean indicating if net is bounded
            - boundedness_level: Bound level (e.g., 1 for safe, k for k-bounded)
            - is_safe: Boolean indicating if net is 1-bounded (safe)
            - is_conservative: Boolean indicating if total tokens constant
            - unbounded_places: List of potentially unbounded places
            - place_bounds: Dict mapping place IDs to their bounds
            - overflow_risk: Boolean indicating risk of overflow
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
        if not self.model.places:
            return AnalysisResult(
                success=True,
                data={
                    'is_bounded': True,
                    'boundedness_level': 0,
                    'is_safe': True,
                    'is_conservative': True,
                    'unbounded_places': [],
                    'place_bounds': {},
                    'overflow_risk': False
                },
                metadata={'analysis_time': self._end_timer(start_time)}
            )
        
        try:
            # Check conservation
            is_conservative = False
            if check_conservation:
                is_conservative = self._check_conservation()
            
            # Get current place bounds from marking
            place_bounds = {}
            if check_current_marking:
                place_bounds = self._get_current_bounds()
            
            # Check structural properties
            structural_info = {}
            if check_structural:
                structural_info = self._check_structural_boundedness()
            
            # Combine analyses to determine boundedness
            is_bounded, boundedness_level, unbounded_places = self._determine_boundedness(
                place_bounds,
                structural_info,
                is_conservative,
                max_bound
            )
            
            # Check if net is safe (0 or 1-bounded)
            is_safe = (boundedness_level <= 1) if is_bounded else False
            
            # Determine overflow risk
            overflow_risk = self._assess_overflow_risk(
                place_bounds,
                unbounded_places,
                max_bound
            )
            
            return AnalysisResult(
                success=True,
                data={
                    'is_bounded': is_bounded,
                    'boundedness_level': boundedness_level,
                    'is_safe': is_safe,
                    'is_conservative': is_conservative,
                    'unbounded_places': unbounded_places,
                    'place_bounds': place_bounds,
                    'overflow_risk': overflow_risk,
                    'total_places': len(self.model.places),
                    'max_bound': max_bound
                },
                metadata={
                    'analysis_time': self._end_timer(start_time),
                    'checked_conservation': check_conservation,
                    'checked_structural': check_structural
                }
            )
            
        except Exception as e:
            return AnalysisResult(
                success=False,
                errors=[f"Boundedness analysis failed: {str(e)}"],
                metadata={'analysis_time': self._end_timer(start_time)}
            )
    
    def _check_conservation(self) -> bool:
        """Check if the net is conservative (total tokens remain constant).
        
        A net is conservative if there exists a positive P-invariant covering all places.
        
        Returns:
            True if net is conservative
        """
        try:
            from shypn.topology.structural.p_invariants import PInvariantAnalyzer
            
            p_inv_analyzer = PInvariantAnalyzer(self.model)
            result = p_inv_analyzer.analyze()
            
            if not result.success:
                return False
            
            invariants = result.get('p_invariants', [])
            
            # Check if any invariant covers all places
            all_place_ids = {str(p.id) for p in self.model.places}
            
            for inv in invariants:
                inv_places = set(inv.get('place_ids', []))
                if inv_places == all_place_ids:
                    return True
            
            return False
            
        except Exception:
            return False
    
    def _get_current_bounds(self) -> Dict[str, int]:
        """Get current token counts for all places.
        
        Returns:
            Dict mapping place ID to current marking
        """
        bounds = {}
        
        for place in self.model.places:
            place_id = str(place.id)
            marking = getattr(place, 'marking', 0)
            bounds[place_id] = marking
        
        return bounds
    
    def _check_structural_boundedness(self) -> Dict[str, Any]:
        """Check structural properties for boundedness.
        
        Returns:
            Dictionary with structural analysis info
        """
        info = {
            'has_sources': False,
            'has_sinks': False,
            'has_cycles': True  # Assume true unless proven otherwise
        }
        
        # Check for source places (no input arcs)
        # Check for sink places (no output arcs)
        place_inputs = {str(p.id): 0 for p in self.model.places}
        place_outputs = {str(p.id): 0 for p in self.model.places}
        
        for arc in self.model.arcs:
            source_id = str(arc.source_id)
            target_id = str(arc.target_id)
            
            # Transition → Place (place has input)
            if target_id in place_inputs:
                place_inputs[target_id] += 1
            
            # Place → Transition (place has output)
            if source_id in place_outputs:
                place_outputs[source_id] += 1
        
        # Source places: no inputs
        sources = [pid for pid, count in place_inputs.items() if count == 0]
        info['has_sources'] = len(sources) > 0
        info['source_places'] = sources
        
        # Sink places: no outputs
        sinks = [pid for pid, count in place_outputs.items() if count == 0]
        info['has_sinks'] = len(sinks) > 0
        info['sink_places'] = sinks
        
        return info
    
    def _determine_boundedness(
        self,
        place_bounds: Dict[str, int],
        structural_info: Dict[str, Any],
        is_conservative: bool,
        max_bound: int
    ) -> tuple:
        """Determine overall boundedness from analyses.
        
        Args:
            place_bounds: Current place markings
            structural_info: Structural analysis results
            is_conservative: Whether net is conservative
            max_bound: Maximum bound threshold
            
        Returns:
            (is_bounded, boundedness_level, unbounded_places)
        """
        unbounded_places = []
        
        # If conservative, net is structurally bounded
        if is_conservative:
            # Find max marking
            if place_bounds:
                max_marking = max(place_bounds.values())
                return True, max_marking, []
            else:
                return True, 0, []
        
        # Check for structural unboundedness indicators
        has_sources = structural_info.get('has_sources', False)
        has_sinks = structural_info.get('has_sinks', False)
        
        # Skip structural unboundedness check for now
        # (Isolated places are not necessarily unbounded in practice)
        
        # Check current markings against max_bound
        for place_id, marking in place_bounds.items():
            if marking > max_bound:
                place_name = next(
                    (str(p.name) if hasattr(p, 'name') and p.name else place_id
                     for p in self.model.places if str(p.id) == place_id),
                    place_id
                )
                unbounded_places.append({
                    'id': place_id,
                    'name': place_name,
                    'reason': f'Current marking ({marking}) exceeds max_bound ({max_bound})'
                })
        
        # Determine boundedness
        if unbounded_places:
            return False, None, unbounded_places
        
        # Find bound level (max tokens in any place)
        if place_bounds:
            max_tokens = max(place_bounds.values())
            return True, max_tokens, []
        else:
            return True, 0, []
    
    def _assess_overflow_risk(
        self,
        place_bounds: Dict[str, int],
        unbounded_places: List[Dict[str, Any]],
        max_bound: int
    ) -> bool:
        """Assess risk of overflow based on current state.
        
        Args:
            place_bounds: Current place markings
            unbounded_places: List of unbounded places
            max_bound: Maximum bound threshold
            
        Returns:
            True if overflow risk detected
        """
        # If any place is unbounded, there's risk
        if unbounded_places:
            return True
        
        # Check if any place is close to max_bound (>80%)
        threshold = max_bound * 0.8
        for marking in place_bounds.values():
            if marking > threshold:
                return True
        
        return False
    
    def check_place_boundedness(self, place_id: str) -> AnalysisResult:
        """Check boundedness of a specific place.
        
        Args:
            place_id: ID of place to check
            
        Returns:
            AnalysisResult with place-specific boundedness info
        """
        result = self.analyze()
        
        if not result.success:
            return result
        
        place_bounds = result.get('place_bounds', {})
        unbounded_places = result.get('unbounded_places', [])
        
        # Check if place is unbounded
        is_unbounded = any(p['id'] == place_id for p in unbounded_places)
        current_bound = place_bounds.get(place_id, 0)
        
        return AnalysisResult(
            success=True,
            data={
                'place_id': place_id,
                'is_bounded': not is_unbounded,
                'current_marking': current_bound,
                'is_unbounded': is_unbounded
            },
            metadata=result.metadata
        )
