"""Traps analyzer for Petri nets.

A trap is a set of places that, once marked, stays marked forever.
Formally: S ⊆ P is a trap if ∀p ∈ S: S• ⊆ •p

This means all output transitions from places in S also input to places in S.
If S has at least one token, it will always have tokens.

Traps are the dual concept to siphons:
- Siphon: Once empty, stays empty (•S ⊆ S•)
- Trap: Once marked, stays marked (S• ⊆ •S)

Traps are critical for:
- Safety analysis (tokens accumulate here)
- Buffer overflow detection (unbounded growth)
- Resource accumulation points
- Liveness verification (marked traps ensure progress)

Mathematical Background:
- Commoner, F. et al. (1971). "Marked directed graphs"
- Lautenbach, K. (1987). "Linear algebraic calculation of deadlocks and traps"
- Murata, T. (1989). "Petri nets: Properties, analysis and applications"

Implementation approach:
- Use graph-based enumeration (same as siphons but dual condition)
- Check trap property for place subsets
- Filter to minimal traps (not contained in others)
- Complexity: Exponential in worst case, but practical for small nets
"""

from typing import Any, Dict, List, Set, Optional
from itertools import combinations
import numpy as np

from shypn.topology.base.topology_analyzer import TopologyAnalyzer
from shypn.topology.base.analysis_result import AnalysisResult
from shypn.topology.base.exceptions import TopologyAnalysisError


class TrapAnalyzer(TopologyAnalyzer):
    """Analyzer for finding traps in Petri nets.
    
    A trap is a set of places that, once marked, cannot become empty.
    Formal definition: S ⊆ P is a trap if ∀p ∈ S: S• ⊆ •S
    
    This means: all transitions that output from S also input to S.
    
    Example:
        >>> analyzer = TrapAnalyzer(model)
        >>> result = analyzer.analyze(min_size=2, max_size=5)
        >>> traps = result.get('traps', [])
        >>> for trap in traps:
        ...     print(f"Trap: {trap['place_ids']}")
    """
    
    def __init__(self, model: Any):
        """Initialize trap analyzer.
        
        Args:
            model: Petri net model with places, transitions, and arcs attributes
        """
        super().__init__(model)
        self.name = "Traps"
        self.description = "Find traps (place sets that stay marked once marked)"
    
    def analyze(
        self,
        min_size: int = 1,
        max_size: Optional[int] = None,
        max_traps: int = 100,
        check_marking: bool = True
    ) -> AnalysisResult:
        """Find all traps in the Petri net.
        
        Args:
            min_size: Minimum number of places in trap (default 1)
            max_size: Maximum number of places to check (None = all)
            max_traps: Maximum number of traps to return
            check_marking: Whether to check current marking status
            
        Returns:
            AnalysisResult with:
            - traps: List of trap dictionaries
            - count: Number of traps found
            - has_marked_traps: Boolean indicating if any trap is marked
            - accumulation_risk: Boolean indicating potential unbounded growth
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
                    'traps': [],
                    'count': 0,
                    'has_marked_traps': False,
                    'accumulation_risk': False
                },
                metadata={
                    'analysis_time': self._end_timer(start_time),
                    'min_size': min_size,
                    'max_size': max_size
                }
            )
        
        try:
            # Build connectivity maps
            place_presets, place_postsets = self._build_place_connectivity()
            
            # Find all traps
            all_traps = self._find_traps(
                place_presets,
                place_postsets,
                min_size,
                max_size
            )
            
            # Filter to minimal traps
            minimal_traps = self._filter_minimal_traps(all_traps)
            
            # Limit number of results
            if len(minimal_traps) > max_traps:
                minimal_traps = minimal_traps[:max_traps]
            
            # Analyze each trap
            trap_data = []
            has_marked = False
            
            for trap_places in minimal_traps:
                trap_info = self._analyze_trap(
                    trap_places,
                    place_presets,
                    place_postsets,
                    check_marking
                )
                trap_data.append(trap_info)
                
                if check_marking and trap_info.get('is_marked', False):
                    has_marked = True
            
            # Determine accumulation risk (marked traps can accumulate tokens)
            accumulation_risk = has_marked
            
            return AnalysisResult(
                success=True,
                data={
                    'traps': trap_data,
                    'count': len(trap_data),
                    'has_marked_traps': has_marked,
                    'accumulation_risk': accumulation_risk
                },
                metadata={
                    'analysis_time': self._end_timer(start_time),
                    'min_size': min_size,
                    'max_size': max_size or len(self.model.places),
                    'total_places': len(self.model.places),
                    'checked_combinations': self._checked_count if hasattr(self, '_checked_count') else 0
                }
            )
            
        except Exception as e:
            return AnalysisResult(
                success=False,
                errors=[f"Trap analysis failed: {str(e)}"],
                metadata={'analysis_time': self._end_timer(start_time)}
            )
    
    def _build_place_connectivity(self) -> tuple:
        """Build preset and postset maps for places.
        
        Returns:
            (place_presets, place_postsets) where:
            - place_presets[place_id] = set of transition IDs that input to place
            - place_postsets[place_id] = set of transition IDs that output from place
        """
        place_presets = {str(p.id): set() for p in self.model.places}
        place_postsets = {str(p.id): set() for p in self.model.places}
        
        for arc in self.model.arcs:
            source_id = str(arc.source_id)
            target_id = str(arc.target_id)
            
            # Transition → Place arc (place is in postset of transition)
            if target_id in place_presets:
                place_presets[target_id].add(source_id)
            
            # Place → Transition arc (place is in preset of transition)
            if source_id in place_postsets:
                place_postsets[source_id].add(target_id)
        
        return place_presets, place_postsets
    
    def _find_traps(
        self,
        place_presets: Dict[str, Set[str]],
        place_postsets: Dict[str, Set[str]],
        min_size: int,
        max_size: Optional[int]
    ) -> List[Set[str]]:
        """Find all traps by checking subsets of places.
        
        Args:
            place_presets: Map of place ID → set of input transition IDs
            place_postsets: Map of place ID → set of output transition IDs
            min_size: Minimum trap size
            max_size: Maximum trap size (None = all places)
            
        Returns:
            List of trap place ID sets
        """
        place_ids = list(place_presets.keys())
        n_places = len(place_ids)
        
        if max_size is None:
            max_size = n_places
        
        traps = []
        self._checked_count = 0
        
        # Check subsets of increasing size
        for size in range(min_size, min(max_size + 1, n_places + 1)):
            for place_subset in combinations(place_ids, size):
                self._checked_count += 1
                
                if self._is_trap(set(place_subset), place_presets, place_postsets):
                    traps.append(set(place_subset))
        
        return traps
    
    def _is_trap(
        self,
        place_set: Set[str],
        place_presets: Dict[str, Set[str]],
        place_postsets: Dict[str, Set[str]]
    ) -> bool:
        """Check if a set of places is a trap.
        
        A set S is a trap if: ∀p ∈ S: S• ⊆ •S
        Meaning: All transitions that output from S also input to S.
        
        This is the DUAL of the siphon property:
        - Siphon: •S ⊆ S• (once empty, stays empty)
        - Trap:   S• ⊆ •S (once marked, stays marked)
        
        Args:
            place_set: Set of place IDs to check
            place_presets: Map of place ID → set of input transition IDs
            place_postsets: Map of place ID → set of output transition IDs
            
        Returns:
            True if place_set is a trap
        """
        # Compute S• (all transitions that output from any place in S)
        postset_S = set()
        for place_id in place_set:
            postset_S.update(place_postsets[place_id])
        
        # Compute •S (all transitions that input to any place in S)
        preset_S = set()
        for place_id in place_set:
            preset_S.update(place_presets[place_id])
        
        # Check trap property: S• ⊆ •S
        return postset_S.issubset(preset_S)
    
    def _filter_minimal_traps(self, traps: List[Set[str]]) -> List[Set[str]]:
        """Filter to minimal traps (not contained in other traps).
        
        Args:
            traps: List of trap place ID sets
            
        Returns:
            List of minimal trap place ID sets
        """
        minimal = []
        
        # Sort by size (smallest first)
        sorted_traps = sorted(traps, key=len)
        
        for trap in sorted_traps:
            is_minimal = True
            
            # Check if this trap is contained in any existing minimal trap
            for existing in minimal:
                if trap.issubset(existing):
                    is_minimal = False
                    break
            
            if is_minimal:
                # Remove any existing minimal traps that contain this one
                minimal = [t for t in minimal if not trap.issubset(t)]
                minimal.append(trap)
        
        return minimal
    
    def _analyze_trap(
        self,
        trap_places: Set[str],
        place_presets: Dict[str, Set[str]],
        place_postsets: Dict[str, Set[str]],
        check_marking: bool
    ) -> Dict[str, Any]:
        """Analyze a single trap.
        
        Args:
            trap_places: Set of place IDs in trap
            place_presets: Map of place ID → set of input transition IDs
            place_postsets: Map of place ID → set of output transition IDs
            check_marking: Whether to check current marking
            
        Returns:
            Dictionary with trap information
        """
        # Get place objects
        place_map = {str(p.id): p for p in self.model.places}
        places = [place_map[pid] for pid in trap_places]
        
        # Get place info
        place_ids = [str(p.id) for p in places]
        place_names = [str(p.name) if hasattr(p, 'name') and p.name else str(p.id) for p in places]
        
        # Compute preset and postset
        preset = set()
        postset = set()
        for pid in trap_places:
            preset.update(place_presets[pid])
            postset.update(place_postsets[pid])
        
        # Check marking if requested
        is_marked = False
        marking_info = {}
        total_tokens = 0
        
        if check_marking:
            is_marked = any(
                getattr(p, 'marking', 0) > 0
                for p in places
            )
            
            marking_info = {
                str(p.id): getattr(p, 'marking', 0)
                for p in places
            }
            
            total_tokens = sum(marking_info.values())
        
        # Classify risk level
        risk_level = self._classify_trap_risk(
            len(trap_places),
            is_marked if check_marking else None,
            total_tokens if check_marking else None
        )
        
        return {
            'place_ids': place_ids,
            'place_names': place_names,
            'size': len(place_ids),
            'preset_transitions': sorted(list(preset)),
            'postset_transitions': sorted(list(postset)),
            'is_marked': is_marked,
            'marking': marking_info,
            'total_tokens': total_tokens,
            'risk_level': risk_level,
            'accumulation_risk': is_marked if check_marking else None
        }
    
    def _classify_trap_risk(
        self,
        size: int,
        is_marked: Optional[bool],
        total_tokens: Optional[int]
    ) -> str:
        """Classify trap risk level.
        
        Args:
            size: Number of places in trap
            is_marked: Whether trap is currently marked (None if not checked)
            total_tokens: Total tokens in trap (None if not checked)
            
        Returns:
            Risk level string
        """
        if is_marked:
            # Marked traps accumulate tokens - risk increases with size
            if total_tokens is not None and total_tokens > 100:
                return "HIGH"
            elif size >= 5:
                return "HIGH"
            elif size >= 3:
                return "medium"
            else:
                return "low"
        elif is_marked is False:
            # Empty traps are not a problem
            return "none"
        else:
            # Marking not checked - estimate by size
            if size >= 5:
                return "medium"
            else:
                return "low"
    
    def find_traps_containing_place(self, place_id: str) -> List[Dict[str, Any]]:
        """Find all traps containing a specific place.
        
        Args:
            place_id: Place ID to search for
            
        Returns:
            List of trap dictionaries containing the place
        """
        result = self.analyze()
        
        if not result.success:
            return []
        
        traps = result.get('traps', [])
        return [
            trap for trap in traps
            if place_id in trap['place_ids']
        ]
