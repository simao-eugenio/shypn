"""Siphons analyzer for Petri nets.

A siphon is a set of places that, once empty, stays empty forever.
Formally: S ⊆ P is a siphon if ∀p ∈ S: •p ⊆ S•

This means all input transitions to places in S also output to places in S.
If S becomes empty, no transition can put tokens back into S.

Siphons are critical for:
- Deadlock detection (empty siphon → potential deadlock)
- Resource starvation analysis
- Liveness verification (siphons must stay marked)

Mathematical Background:
- Commoner, F. et al. (1971). "Marked directed graphs"
- Lautenbach, K. (1987). "Linear algebraic calculation of deadlocks and traps"
- Murata, T. (1989). "Petri nets: Properties, analysis and applications"

Implementation approach:
- Use graph-based enumeration
- Check siphon property for place subsets
- Filter to minimal siphons (not contained in others)
- Complexity: Exponential in worst case, but practical for small nets
"""

from typing import Any, Dict, List, Set, Optional
from itertools import combinations

from shypn.topology.base.topology_analyzer import TopologyAnalyzer
from shypn.topology.base.analysis_result import AnalysisResult
from shypn.topology.base.exceptions import TopologyAnalysisError


class SiphonAnalyzer(TopologyAnalyzer):
    """Analyzer for finding siphons in Petri nets.
    
    A siphon is a set of places that, once empty, cannot receive tokens again.
    Formal definition: S ⊆ P is a siphon if ∀p ∈ S: •p ⊆ S•
    
    This means: all transitions that input to S also output to S.
    
    Example:
        >>> analyzer = SiphonAnalyzer(model)
        >>> result = analyzer.analyze(min_size=2, max_size=5)
        >>> siphons = result.get('siphons', [])
        >>> for siphon in siphons:
        ...     print(f"Siphon: {siphon['place_ids']}")
    """
    
    def __init__(self, model: Any):
        """Initialize siphon analyzer.
        
        Args:
            model: Petri net model with places, transitions, and arcs attributes
        """
        super().__init__(model)
        self.name = "Siphons"
        self.description = "Find siphons (place sets that stay empty once emptied)"
    
    def analyze(  # type: ignore[override]
        self,
        min_size: int = 1,
        max_size: Optional[int] = None,
        max_siphons: int = 100,
        check_marking: bool = True,
        parallel: bool = False,
        num_workers: Optional[int] = None
    ) -> AnalysisResult:
        """Find all siphons in the Petri net.
        
        Args:
            min_size: Minimum number of places in siphon (default 1)
            max_size: Maximum number of places to check (None = all)
            max_siphons: Maximum number of siphons to return
            check_marking: Whether to check current marking status
            parallel: Use parallel processing for siphon detection
            num_workers: Number of worker processes (None = CPU count)
            
        Returns:
            AnalysisResult with:
            - siphons: List of siphon dictionaries
            - count: Number of siphons found
            - has_empty_siphons: Boolean indicating if any siphon is empty
            - deadlock_risk: Boolean indicating potential deadlock
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
        
        # ========================================================================
        # SIZE GUARD: Check model size to prevent exponential computation freeze
        # ========================================================================
        try:
            n_places = len(self.model.places)
        except Exception as e:
            return AnalysisResult(
                success=False,
                errors=[f"Model places is not iterable: {e}"],
                metadata={'analysis_time': self._end_timer(start_time)}
            )
        
        # Siphon analysis has O(2^n) complexity - exponential in number of places
        # Checking all subsets becomes impractical beyond ~20 places
        MAX_PLACES_SAFE = 20  # Conservative limit for interactive use
        
        if n_places > MAX_PLACES_SAFE:
            estimated_combinations = sum(
                1 for r in range(min_size, min(max_size or n_places, n_places) + 1)
                for _ in range(1)  # Just count ranges
            )
            
            return AnalysisResult(
                success=False,
                errors=[
                    "⛔ Model too large for siphon analysis",
                    f"   Places: {n_places} (maximum: {MAX_PLACES_SAFE})",
                    f"   Estimated operations: > 10^{int(n_places * 0.3)} (exponential)",
                    "",
                    "⚠️  This analysis would take hours or days to complete",
                    "    and could freeze your system."
                ],
                warnings=[
                    "Options to analyze this model:",
                    "• Extract a smaller subnetwork for analysis",
                    "• Use batch analysis mode (overnight processing)",
                    "• Increase max_size limit if you only need small siphons",
                    f"  Current max_size: {max_size or n_places}"
                ],
                metadata={
                    'analysis_time': self._end_timer(start_time),
                    'blocked': True,
                    'block_reason': 'model_too_large',
                    'max_places_limit': MAX_PLACES_SAFE,
                    'actual_places': n_places,
                    'complexity': 'O(2^n) - Exponential'
                }
            )
        
        # Handle empty model
        if not self.model.places or not self.model.transitions:
            return AnalysisResult(
                success=True,
                data={
                    'siphons': [],
                    'count': 0,
                    'has_empty_siphons': False,
                    'deadlock_risk': False
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
            
            # Find all siphons (parallel or sequential)
            if parallel and len(self.model.places) >= 8:
                all_siphons = self._find_siphons_parallel(
                    place_presets,
                    place_postsets,
                    min_size,
                    max_size,
                    num_workers
                )
            else:
                all_siphons = self._find_siphons(
                    place_presets,
                    place_postsets,
                    min_size,
                    max_size
                )
            
            # Filter to minimal siphons
            minimal_siphons = self._filter_minimal_siphons(all_siphons)
            
            # Limit number of results
            if len(minimal_siphons) > max_siphons:
                minimal_siphons = minimal_siphons[:max_siphons]
            
            # Analyze each siphon
            siphon_data = []
            has_empty = False
            
            for siphon_places in minimal_siphons:
                siphon_info = self._analyze_siphon(
                    siphon_places,
                    place_presets,
                    place_postsets,
                    check_marking
                )
                siphon_data.append(siphon_info)
                
                if check_marking and siphon_info.get('is_empty', False):
                    has_empty = True
            
            # Determine deadlock risk
            deadlock_risk = has_empty
            
            return AnalysisResult(
                success=True,
                data={
                    'siphons': siphon_data,
                    'count': len(siphon_data),
                    'has_empty_siphons': has_empty,
                    'deadlock_risk': deadlock_risk
                },
                metadata={
                    'analysis_time': self._end_timer(start_time),
                    'min_size': min_size,
                    'max_size': max_size or len(self.model.places),
                    'total_places': len(self.model.places),
                    'checked_combinations': self._checked_count if hasattr(self, '_checked_count') else 0
                }
            )
            
        except (ValueError, AttributeError, KeyError) as e:
            return AnalysisResult(
                success=False,
                errors=[f"Siphon analysis failed: {str(e)}"],
                metadata={'analysis_time': self._end_timer(start_time)}
            )
    
    def _find_siphons_parallel(
        self,
        place_presets: Dict[str, Set[str]],
        place_postsets: Dict[str, Set[str]],
        min_size: int,
        max_size: Optional[int],
        num_workers: Optional[int]
    ) -> List[Set[str]]:
        """Find siphons in parallel by partitioning subset checks.
        
        Args:
            place_presets: Map of place_id -> input transitions
            place_postsets: Map of place_id -> output transitions
            min_size: Minimum siphon size
            max_size: Maximum siphon size
            num_workers: Number of worker processes
            
        Returns:
            List of siphon sets (place IDs)
        """
        from multiprocessing import Pool, cpu_count
        from itertools import combinations
        
        workers = num_workers if num_workers else cpu_count()
        place_ids = list(place_presets.keys())
        n_places = len(place_ids)
        max_size = min(max_size or n_places, n_places)
        
        # Collect all combinations to check (partitioned by size)
        all_combinations = []
        for size in range(min_size, max_size + 1):
            combos = list(combinations(place_ids, size))
            all_combinations.extend(combos)
        
        # Partition work among workers
        chunk_size = max(1, len(all_combinations) // workers)
        work_chunks = [
            all_combinations[i:i + chunk_size]
            for i in range(0, len(all_combinations), chunk_size)
        ]
        
        # Parallel siphon checking
        with Pool(workers) as pool:
            results = pool.starmap(
                self._check_siphons_worker,
                [(chunk, place_presets, place_postsets) for chunk in work_chunks]
            )
        
        # Flatten results
        siphons = []
        for chunk_siphons in results:
            siphons.extend(chunk_siphons)
        
        return siphons
    
    @staticmethod
    def _check_siphons_worker(
        combinations_to_check: List[tuple],
        place_presets: Dict[str, Set[str]],
        place_postsets: Dict[str, Set[str]]
    ) -> List[Set[str]]:
        """Worker function to check if place subsets are siphons (static for pickling).
        
        Args:
            combinations_to_check: List of place ID tuples to check
            place_presets: Map of place_id -> input transitions
            place_postsets: Map of place_id -> output transitions
            
        Returns:
            List of confirmed siphon sets
        """
        siphons = []
        
        for combo in combinations_to_check:
            place_set = set(combo)
            
            # Check siphon property: ∀p ∈ S: •p ⊆ S•
            is_siphon = True
            
            # Collect all input transitions to S
            input_transitions = set()
            for place_id in place_set:
                input_transitions.update(place_presets.get(place_id, set()))
            
            # Collect all output transitions from S
            output_transitions = set()
            for place_id in place_set:
                output_transitions.update(place_postsets.get(place_id, set()))
            
            # Check if input ⊆ output (siphon property)
            if not input_transitions.issubset(output_transitions):
                is_siphon = False
            
            if is_siphon:
                siphons.append(place_set)
        
        return siphons
    
    def _find_siphons(
        self,
        place_presets: Dict[str, Set[str]],
        place_postsets: Dict[str, Set[str]],
        min_size: int,
        max_size: Optional[int]
    ) -> List[Set[str]]:
        """Find all siphons by checking subsets of places.
        
        Args:
            place_presets: Map of place ID → set of input transition IDs
            place_postsets: Map of place ID → set of output transition IDs
            min_size: Minimum siphon size
            max_size: Maximum siphon size (None = all places)
            
        Returns:
            List of siphon place ID sets
        """
        place_ids = list(place_presets.keys())
        n_places = len(place_ids)
        
        if max_size is None:
            max_size = n_places
        
        siphons = []
        self._checked_count = 0
        
        # Check subsets of increasing size
        for size in range(min_size, min(max_size + 1, n_places + 1)):
            for place_subset in combinations(place_ids, size):
                self._checked_count += 1
                
                if self._is_siphon(set(place_subset), place_presets, place_postsets):
                    siphons.append(set(place_subset))
        
        return siphons
    
    def _is_siphon(
        self,
        place_set: Set[str],
        place_presets: Dict[str, Set[str]],
        place_postsets: Dict[str, Set[str]]
    ) -> bool:
        """Check if a set of places is a siphon.
        
        A set S is a siphon if: ∀p ∈ S: •p ⊆ S•
        Meaning: All transitions that input to S also output to S.
        
        Args:
            place_set: Set of place IDs to check
            place_presets: Map of place ID → set of input transition IDs
            place_postsets: Map of place ID → set of output transition IDs
            
        Returns:
            True if place_set is a siphon
        """
        # Compute •S (all transitions that input to any place in S)
        preset_S = set()
        for place_id in place_set:
            preset_S.update(place_presets[place_id])
        
        # Compute S• (all transitions that output from any place in S)
        postset_S = set()
        for place_id in place_set:
            postset_S.update(place_postsets[place_id])
        
        # Check siphon property: •S ⊆ S•
        return preset_S.issubset(postset_S)
    
    def _filter_minimal_siphons(self, siphons: List[Set[str]]) -> List[Set[str]]:
        """Filter to minimal siphons (not contained in other siphons).
        
        Args:
            siphons: List of siphon place ID sets
            
        Returns:
            List of minimal siphon place ID sets
        """
        minimal: List[Any] = []
        
        # Sort by size (smallest first)
        sorted_siphons = sorted(siphons, key=len)
        
        for siphon in sorted_siphons:
            is_minimal = True
            
            # Check if this siphon is contained in any existing minimal siphon
            for existing in minimal:
                if siphon.issubset(existing):
                    is_minimal = False
                    break
            
            if is_minimal:
                # Remove any existing minimal siphons that contain this one
                minimal = [s for s in minimal if not siphon.issubset(s)]
                minimal.append(siphon)
        
        return minimal
    
    def _analyze_siphon(
        self,
        siphon_places: Set[str],
        place_presets: Dict[str, Set[str]],
        place_postsets: Dict[str, Set[str]],
        check_marking: bool
    ) -> Dict[str, Any]:
        """Analyze a single siphon.
        
        Args:
            siphon_places: Set of place IDs in siphon
            place_presets: Map of place ID → set of input transition IDs
            place_postsets: Map of place ID → set of output transition IDs
            check_marking: Whether to check current marking
            
        Returns:
            Dictionary with siphon information
        """
        # Get place objects
        place_map = {str(p.id): p for p in self.model.places}
        places = [place_map[pid] for pid in siphon_places]
        
        # Get place info
        place_ids = [str(p.id) for p in places]
        place_names = [str(p.name) if hasattr(p, 'name') and p.name else str(p.id) for p in places]
        
        # Compute preset and postset
        preset = set()
        postset = set()
        for pid in siphon_places:
            preset.update(place_presets[pid])
            postset.update(place_postsets[pid])
        
        # Check marking if requested
        is_empty = False
        marking_info = {}
        
        if check_marking:
            is_empty = all(
                getattr(p, 'marking', 0) == 0
                for p in places
            )
            
            marking_info = {
                str(p.id): getattr(p, 'marking', 0)
                for p in places
            }
        
        # Classify criticality
        criticality = self._classify_siphon_criticality(
            len(siphon_places),
            is_empty if check_marking else None,
            len(preset)
        )
        
        return {
            'place_ids': place_ids,
            'place_names': place_names,
            'size': len(place_ids),
            'preset_transitions': sorted(list(preset)),
            'postset_transitions': sorted(list(postset)),
            'is_empty': is_empty,
            'marking': marking_info,
            'criticality': criticality,
            'deadlock_risk': is_empty if check_marking else None
        }
    
    def _classify_siphon_criticality(
        self,
        size: int,
        is_empty: Optional[bool],
        preset_size: int
    ) -> str:
        """Classify siphon criticality level.
        
        Args:
            size: Number of places in siphon
            is_empty: Whether siphon is currently empty (None if not checked)
            preset_size: Number of input transitions
            
        Returns:
            Criticality level string
        """
        if is_empty:
            return "CRITICAL"
        elif is_empty is False:
            if size == 1:
                return "low"
            elif size <= 3:
                return "medium"
            else:
                return "high"
        else:
            # Marking not checked
            if size == 1:
                return "low"
            elif size <= 3:
                return "medium"
            else:
                return "high"
    
    def find_siphons_containing_place(self, place_id: str) -> List[Dict[str, Any]]:
        """Find all siphons containing a specific place.
        
        Args:
            place_id: Place ID to search for
            
        Returns:
            List of siphon dictionaries containing the place
        """
        result = self.analyze()
        
        if not result.success:
            return []
        
        siphons = result.get('siphons', [])
        return [
            siphon for siphon in siphons
            if place_id in siphon['place_ids']
        ]
