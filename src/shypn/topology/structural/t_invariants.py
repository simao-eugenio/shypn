"""T-Invariant analyzer for Petri nets."""

from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from scipy import linalg

from ..base.topology_analyzer import TopologyAnalyzer
from ..base.analysis_result import AnalysisResult
from ..base.exceptions import TopologyAnalysisError


class TInvariantAnalyzer(TopologyAnalyzer):
    """Analyzer for T-invariants (transition invariants) in Petri nets.
    
    T-invariants represent reproducible firing sequences that return the net
    to its initial marking. They are vectors x such that C * x = 0, where C
    is the incidence matrix. A T-invariant indicates a cyclic behavior.
    
    For biochemical networks, T-invariants represent:
    - Metabolic cycles (TCA cycle, Calvin cycle)
    - Reproducible pathways that maintain homeostasis
    - Reaction sequences with no net change in metabolites
    - Balanced processes (production = consumption)
    
    Algorithm: Farkas algorithm for finding non-negative integer solutions
    to homogeneous linear systems (applied to C, not C^T like P-invariants).
    
    Attributes:
        model: PetriNetModel instance to analyze
        
    Example:
        analyzer = TInvariantAnalyzer(model)
        result = analyzer.analyze()
        
        if result.success:
            for inv in result.get('t_invariants', []):
    """
    
    def analyze(
        self,
        min_support: int = 1,
        max_invariants: int = 100,
        normalize: bool = True,
        classify: bool = True
    ) -> AnalysisResult:
        """Find all minimal T-invariants (transition invariants).
        
        Args:
            min_support: Minimum number of transitions in invariant (default 1)
            max_invariants: Maximum number of invariants to return
            normalize: Whether to normalize to smallest integer weights
            classify: Whether to classify invariant types
            
        Returns:
            AnalysisResult with:
                - t_invariants: List of T-invariant dicts
                - count: Total number of T-invariants found
                - covered_transitions: Number of transitions covered
                - coverage_ratio: Fraction of transitions in some invariant
                - summary: Human-readable summary
                - metadata: Analysis parameters and timing
                
        Raises:
            TopologyAnalysisError: If analysis fails
        """
        start_time = self._start_timer()
        
        try:
            # Validate model
            self._validate_model()
            
            # Check for empty model
            if len(self.model.transitions) == 0:
                return AnalysisResult(
                    success=True,
                    data={'t_invariants': [], 'count': 0},
                    summary="No transitions in model",
                    metadata={'analysis_time': self._end_timer(start_time)}
                )
            
            # Build incidence matrix
            incidence_matrix, place_map, transition_map = self._build_incidence_matrix()
            
            # Compute T-invariants (kernel of C, not C^T)
            invariant_vectors = self._compute_invariants(incidence_matrix)
            
            # Filter by support size
            invariant_vectors = [
                v for v in invariant_vectors 
                if np.count_nonzero(v) >= min_support
            ]
            
            # Normalize if requested
            if normalize:
                invariant_vectors = [self._normalize_invariant(v) for v in invariant_vectors]
            
            # Remove duplicates
            invariant_vectors = self._remove_duplicates(invariant_vectors)
            
            # Limit results
            if len(invariant_vectors) > max_invariants:
                invariant_vectors = invariant_vectors[:max_invariants]
                truncated = True
            else:
                truncated = False
            
            # Convert to invariant information dicts
            invariants = []
            for vec in invariant_vectors:
                inv_info = self._analyze_invariant(
                    vec, 
                    transition_map,
                    classify=classify
                )
                invariants.append(inv_info)
            
            # Calculate coverage statistics
            covered_transitions = set()
            for inv in invariants:
                covered_transitions.update(inv['transition_ids'])
            
            coverage_ratio = len(covered_transitions) / len(self.model.transitions) if self.model.transitions else 0
            
            # Create summary
            summary = self._create_summary(
                len(invariants),
                len(covered_transitions),
                coverage_ratio,
                truncated
            )
            
            return AnalysisResult(
                success=True,
                data={
                    't_invariants': invariants,
                    'count': len(invariants),
                    'covered_transitions': len(covered_transitions),
                    'coverage_ratio': coverage_ratio,
                    'truncated': truncated
                },
                summary=summary,
                warnings=self._generate_warnings(invariants, truncated),
                metadata={
                    'analysis_time': self._end_timer(start_time),
                    'min_support': min_support,
                    'max_invariants': max_invariants,
                    'normalize': normalize,
                    'classify': classify
                }
            )
            
        except Exception as e:
            return AnalysisResult(
                success=False,
                errors=[f"T-invariant analysis failed: {str(e)}"],
                metadata={'analysis_time': self._end_timer(start_time)}
            )
    
    def _build_incidence_matrix(self) -> Tuple[np.ndarray, Dict[int, Any], Dict[int, Any]]:
        """Build incidence matrix C.
        
        C[i,j] = effect of firing transition j on place i
               = (output arc weight) - (input arc weight)
        
        Returns:
            incidence_matrix: numpy array of shape (n_places, n_transitions)
            place_map: dict mapping index -> place object
            transition_map: dict mapping index -> transition object
        """
        # Create mappings
        place_index_map = {p.id: i for i, p in enumerate(self.model.places)}
        transition_index_map = {t.id: i for i, t in enumerate(self.model.transitions)}
        
        # Create reverse mappings (index -> object)
        place_map = {i: p for i, p in enumerate(self.model.places)}
        transition_map = {i: t for i, t in enumerate(self.model.transitions)}
        
        n_places = len(self.model.places)
        n_transitions = len(self.model.transitions)
        
        # Initialize matrix
        incidence_matrix = np.zeros((n_places, n_transitions), dtype=int)
        
        # Fill matrix from arcs
        for arc in self.model.arcs:
            weight = getattr(arc, 'weight', 1)
            
            # Check if arc is place -> transition (input arc)
            if arc.source_id in place_index_map and arc.target_id in transition_index_map:
                place_idx = place_index_map[arc.source_id]
                trans_idx = transition_index_map[arc.target_id]
                incidence_matrix[place_idx, trans_idx] -= weight
            
            # Check if arc is transition -> place (output arc)
            elif arc.source_id in transition_index_map and arc.target_id in place_index_map:
                trans_idx = transition_index_map[arc.source_id]
                place_idx = place_index_map[arc.target_id]
                incidence_matrix[place_idx, trans_idx] += weight
        
        return incidence_matrix, place_map, transition_map
    
    def _compute_invariants(self, matrix: np.ndarray) -> List[np.ndarray]:
        """Compute invariants using null space computation.
        
        Args:
            matrix: Incidence matrix (for T-invariants, use C not C^T)
            
        Returns:
            List of invariant vectors (non-negative integer solutions)
        """
        # Compute null space
        try:
            null_space = linalg.null_space(matrix, rcond=1e-10)
        except Exception as e:
            raise TopologyAnalysisError(f"Failed to compute null space: {e}")
        
        if null_space.shape[1] == 0:
            return []  # No invariants
        
        # Convert to non-negative integer vectors
        invariants = self._convert_to_nonnegative_integers(null_space)
        
        return invariants
    
    def _convert_to_nonnegative_integers(
        self, 
        null_space: np.ndarray,
        tolerance: float = 1e-6
    ) -> List[np.ndarray]:
        """Convert null space basis to non-negative integer vectors.
        
        Uses a simplified Farkas-like algorithm: scale basis vectors to integers,
        then enumerate integer linear combinations systematically.
        
        Args:
            null_space: Null space basis matrix (columns are basis vectors)
            tolerance: Tolerance for considering values as zero
            
        Returns:
            List of non-negative integer invariant vectors
        """
        if null_space.shape[1] == 0:
            return []
        
        # Scale each basis vector to integers
        scaled_basis = []
        for i in range(null_space.shape[1]):
            vec = null_space[:, i]
            # Find scaling factor to make all components near-integers
            # Use LCM-like approach: scale by product of denominators
            max_val = np.max(np.abs(vec))
            if max_val < tolerance:
                continue
            vec_scaled = vec / max_val * 100  # Scale to ~100 for precision
            vec_int = np.round(vec_scaled).astype(int)
            scaled_basis.append(vec_int)
        
        if not scaled_basis:
            return []
        
        invariants = []
        seen = set()
        
        # Try systematic combinations of scaled basis vectors
        n_basis = len(scaled_basis)
        max_coef = 20  # Increased for better coverage
        
        for coefs in self._generate_coefficient_combinations(n_basis, max_coef):
            # Compute linear combination
            vec = np.zeros(null_space.shape[0], dtype=int)
            for i, coef in enumerate(coefs):
                vec += coef * scaled_basis[i]
            
            # Check if non-negative
            if np.all(vec >= 0) and np.any(vec > 0):
                # Normalize by GCD
                vec_normalized = self._normalize_invariant(vec)
                
                # Check for duplicates using tuple representation
                vec_tuple = tuple(vec_normalized)
                if vec_tuple not in seen:
                    seen.add(vec_tuple)
                    invariants.append(vec_normalized)
        
        return invariants
    
    def _generate_coefficient_combinations(self, n_basis: int, max_coef: int):
        """Generate coefficient combinations for linear combinations.
        
        Args:
            n_basis: Number of basis vectors
            max_coef: Maximum absolute coefficient value
            
        Yields:
            Lists of coefficients
        """
        # Try each basis vector alone (both directions)
        for i in range(n_basis):
            for sign in [1, -1]:
                coefs = [0] * n_basis
                coefs[i] = sign
                yield coefs
        
        # Try all pairwise combinations with small coefficients
        if n_basis >= 2:
            for i in range(n_basis):
                for j in range(i + 1, n_basis):
                    # Only try small coefficients to avoid explosion
                    for ci in range(-max_coef, max_coef + 1):
                        if ci == 0:
                            continue
                        for cj in range(-max_coef, max_coef + 1):
                            if cj == 0:
                                continue
                            coefs = [0] * n_basis
                            coefs[i] = ci
                            coefs[j] = cj
                            yield coefs
    
    def _scale_to_integers(
        self, 
        vec: np.ndarray, 
        tolerance: float = 1e-6
    ) -> Optional[np.ndarray]:
        """Scale vector to smallest positive integers.
        
        Args:
            vec: Vector to scale
            tolerance: Tolerance for zero values
            
        Returns:
            Integer-scaled vector or None if not possible
        """
        # Remove near-zero values
        vec = vec.copy()
        vec[np.abs(vec) < tolerance] = 0
        
        if np.all(vec == 0):
            return None
        
        # Find GCD of non-zero values to scale to integers
        non_zero = vec[vec > tolerance]
        if len(non_zero) == 0:
            return None
        
        # Scale to make smallest non-zero value close to 1
        min_val = np.min(non_zero)
        vec = vec / min_val
        
        # Round to integers
        vec_int = np.round(vec).astype(int)
        
        # Verify it's still close to original (within tolerance)
        if np.linalg.norm(vec - vec_int) < tolerance * len(vec):
            # Reduce by GCD
            gcd = np.gcd.reduce(vec_int[vec_int > 0])
            if gcd > 0:
                vec_int = vec_int // gcd
            return vec_int
        
        return None
    
    def _normalize_invariant(self, vec: np.ndarray) -> np.ndarray:
        """Normalize invariant to smallest positive integers.
        
        Args:
            vec: Invariant vector
            
        Returns:
            Normalized vector
        """
        vec_int = vec.astype(int)
        non_zero = vec_int[vec_int > 0]
        
        if len(non_zero) == 0:
            return vec_int
        
        gcd = np.gcd.reduce(non_zero)
        if gcd > 1:
            vec_int = vec_int // gcd
        
        return vec_int
    
    def _remove_duplicates(self, vectors: List[np.ndarray]) -> List[np.ndarray]:
        """Remove duplicate invariants.
        
        Args:
            vectors: List of invariant vectors
            
        Returns:
            List without duplicates
        """
        unique = []
        
        for vec in vectors:
            is_duplicate = False
            for existing in unique:
                if np.array_equal(vec, existing):
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique.append(vec)
        
        return unique
    
    def _analyze_invariant(
        self,
        vec: np.ndarray,
        transition_map: Dict[int, Any],
        classify: bool = True
    ) -> Dict[str, Any]:
        """Analyze a single T-invariant.
        
        Args:
            vec: Invariant vector
            transition_map: Map from index to transition object
            classify: Whether to classify invariant type
            
        Returns:
            Dictionary with invariant information
        """
        # Get transitions with non-zero coefficients
        transition_ids = []
        transition_names = []
        weights = []
        
        for idx, weight in enumerate(vec):
            if weight > 0:
                trans = transition_map[idx]
                # Handle both string IDs and Mock objects
                trans_id = str(trans.id) if hasattr(trans, 'id') else str(trans)
                trans_name = str(trans.name) if hasattr(trans, 'name') and trans.name else trans_id
                
                transition_ids.append(trans_id)
                transition_names.append(trans_name)
                weights.append(int(weight))
        
        # Create firing sequence string
        firing_sequence = ' → '.join([
            f"{w}×{name}" if w > 1 else name
            for w, name in zip(weights, transition_names)
        ])
        
        # Classify invariant type
        inv_type = "cycle"
        if classify:
            inv_type = self._classify_invariant(vec, transition_map)
        
        return {
            'transition_ids': transition_ids,
            'transition_names': transition_names,
            'weights': weights,
            'firing_sequence': firing_sequence,
            'size': len(transition_ids),
            'type': inv_type,
            'total_firings': sum(weights)
        }
    
    def _classify_invariant(
        self,
        vec: np.ndarray,
        transition_map: Dict[int, Any]
    ) -> str:
        """Classify the type of T-invariant.
        
        Args:
            vec: Invariant vector
            transition_map: Map from index to transition
            
        Returns:
            Classification string
        """
        size = np.count_nonzero(vec)
        
        if size == 1:
            return "self-loop"
        elif size == 2:
            return "simple-cycle"
        elif size <= 5:
            return "small-cycle"
        elif size <= 10:
            return "medium-cycle"
        else:
            return "large-cycle"
    
    def _create_summary(
        self,
        count: int,
        covered: int,
        coverage: float,
        truncated: bool
    ) -> str:
        """Create human-readable summary.
        
        Args:
            count: Number of T-invariants
            covered: Number of transitions covered
            coverage: Coverage ratio
            truncated: Whether results were truncated
            
        Returns:
            Summary string
        """
        if count == 0:
            return "No T-invariants found (network may not have reproducible behaviors)"
        
        summary = f"Found {count} T-invariant(s)"
        if truncated:
            summary += " (truncated)"
        
        summary += f"\nCovered transitions: {covered} ({coverage:.1%})"
        
        if coverage < 0.5:
            summary += "\n⚠ Low coverage - many transitions not in any invariant"
        
        return summary
    
    def _generate_warnings(
        self,
        invariants: List[Dict[str, Any]],
        truncated: bool
    ) -> List[str]:
        """Generate analysis warnings.
        
        Args:
            invariants: List of invariant dicts
            truncated: Whether results were truncated
            
        Returns:
            List of warning messages
        """
        warnings = []
        
        if truncated:
            warnings.append("Results truncated - increase max_invariants to see all")
        
        if len(invariants) == 0:
            warnings.append(
                "No T-invariants found. Network may not have reproducible behaviors "
                "or may be acyclic (DAG)."
            )
        
        return warnings
    
    def find_invariants_containing_transition(
        self,
        transition_id: str,
        max_invariants: int = 10
    ) -> AnalysisResult:
        """Find T-invariants containing a specific transition.
        
        Args:
            transition_id: ID of transition to find
            max_invariants: Maximum number of invariants to return
            
        Returns:
            AnalysisResult with filtered invariants
        """
        # Run full analysis
        result = self.analyze(max_invariants=max_invariants * 10)
        
        if not result.success:
            return result
        
        # Filter invariants
        all_invariants = result.get('t_invariants', [])
        filtered = [
            inv for inv in all_invariants
            if transition_id in inv['transition_ids']
        ]
        
        # Limit results
        if len(filtered) > max_invariants:
            filtered = filtered[:max_invariants]
            truncated = True
        else:
            truncated = False
        
        return AnalysisResult(
            success=True,
            data={
                't_invariants': filtered,
                'count': len(filtered),
                'transition_id': transition_id,
                'truncated': truncated
            },
            summary=f"Found {len(filtered)} T-invariant(s) containing transition {transition_id}",
            metadata={'query_type': 'transition_filter'}
        )
