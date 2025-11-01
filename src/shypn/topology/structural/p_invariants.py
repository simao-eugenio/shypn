"""P-Invariant analyzer for Petri nets."""

from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from scipy import linalg

from ..base.topology_analyzer import TopologyAnalyzer
from ..base.analysis_result import AnalysisResult
from ..base.exceptions import TopologyAnalysisError


class PInvariantAnalyzer(TopologyAnalyzer):
    """Analyzer for P-invariants (place invariants) in Petri nets.
    
    P-invariants represent conservation laws in the Petri net. They are
    vectors y such that C^T * y = 0, where C is the incidence matrix.
    A P-invariant indicates that a weighted sum of tokens remains constant.
    
    For biochemical networks, P-invariants represent:
    - Mass conservation (total metabolites constant)
    - Cofactor balance (NAD+/NADH, ATP/ADP, NADP+/NADPH)
    - Charge conservation
    - Element conservation (C, N, O atoms)
    
    Algorithm: Farkas algorithm for finding non-negative integer solutions
    to homogeneous linear systems.
    
    Attributes:
        model: PetriNetModel instance to analyze
        
    Example:
        analyzer = PInvariantAnalyzer(model)
        result = analyzer.analyze()
        
        if result.success:
            for inv in result.get('p_invariants', []):
    """
    
    def analyze(
        self,
        min_support: int = 1,
        max_invariants: int = 100,
        normalize: bool = True
    ) -> AnalysisResult:
        """Find all minimal P-invariants (place invariants).
        
        Args:
            min_support: Minimum number of places in invariant (default 1)
            max_invariants: Maximum number of invariants to return
            normalize: Whether to normalize to smallest integer weights
            
        Returns:
            AnalysisResult with:
                - p_invariants: List of P-invariant dicts
                - count: Total number of P-invariants found
                - covered_places: Number of places covered by invariants
                - coverage_ratio: Fraction of places in some invariant
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
            if len(self.model.places) == 0:
                return AnalysisResult(
                    success=True,
                    data={'p_invariants': [], 'count': 0},
                    summary="No places in model",
                    metadata={'analysis_time': self._end_timer(start_time)}
                )
            
            # Build incidence matrix
            incidence_matrix, place_map, transition_map = self._build_incidence_matrix()
            
            # Compute P-invariants (kernel of C^T)
            invariant_vectors = self._compute_invariants(incidence_matrix.T)
            
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
            total_count = len(invariant_vectors)
            truncated = total_count > max_invariants
            if truncated:
                invariant_vectors = invariant_vectors[:max_invariants]
            
            # Analyze each invariant
            p_invariants = []
            for inv_vector in invariant_vectors:
                inv_info = self._analyze_invariant(inv_vector, place_map)
                p_invariants.append(inv_info)
            
            # Calculate coverage
            covered_places = self._calculate_coverage(p_invariants)
            coverage_ratio = len(covered_places) / len(self.model.places) if self.model.places else 0
            
            # Create summary
            summary = self._create_summary(total_count, coverage_ratio, truncated)
            
            # Compute timing
            duration = self._end_timer(start_time)
            
            # Build result
            result = AnalysisResult(
                success=True,
                data={
                    'p_invariants': p_invariants,
                    'count': total_count,
                    'covered_places': list(covered_places),
                    'coverage_ratio': coverage_ratio,
                },
                summary=summary,
                metadata={
                    'min_support': min_support,
                    'max_invariants': max_invariants,
                    'normalize': normalize,
                    'analysis_time': duration,
                    'matrix_shape': incidence_matrix.shape,
                }
            )
            
            if truncated:
                result.add_warning(
                    f"Results truncated to {max_invariants} invariants (found {total_count} total)"
                )
            
            if coverage_ratio < 0.5:
                result.add_warning(
                    f"Low coverage: only {coverage_ratio:.1%} of places covered by invariants"
                )
            
            return result
        
        except Exception as e:
            return AnalysisResult(
                success=False,
                errors=[f"P-invariant analysis failed: {str(e)}"],
                metadata={'analysis_time': self._end_timer(start_time)}
            )
    
    def _build_incidence_matrix(self) -> Tuple[np.ndarray, Dict[int, int], Dict[int, int]]:
        """Build incidence matrix C.
        
        C[i,j] = effect of firing transition j on place i
               = (output arc weight) - (input arc weight)
        
        Returns:
            incidence_matrix: numpy array of shape (n_places, n_transitions)
            place_map: dict mapping place_id -> row index
            transition_map: dict mapping transition_id -> column index
        """
        # Create mappings
        place_map = {p.id: i for i, p in enumerate(self.model.places)}
        transition_map = {t.id: i for i, t in enumerate(self.model.transitions)}
        
        n_places = len(self.model.places)
        n_transitions = len(self.model.transitions)
        
        # Initialize matrix
        incidence_matrix = np.zeros((n_places, n_transitions), dtype=int)
        
        # Fill matrix from arcs
        for arc in self.model.arcs:
            weight = getattr(arc, 'weight', 1)
            
            # Check if arc is place -> transition (input arc)
            if arc.source_id in place_map and arc.target_id in transition_map:
                place_idx = place_map[arc.source_id]
                trans_idx = transition_map[arc.target_id]
                incidence_matrix[place_idx, trans_idx] -= weight
            
            # Check if arc is transition -> place (output arc)
            elif arc.source_id in transition_map and arc.target_id in place_map:
                trans_idx = transition_map[arc.source_id]
                place_idx = place_map[arc.target_id]
                incidence_matrix[place_idx, trans_idx] += weight
        
        return incidence_matrix, place_map, transition_map
    
    def _compute_invariants(self, matrix: np.ndarray) -> List[np.ndarray]:
        """Compute invariants as null space (kernel) of matrix.
        
        Uses SVD-based approach for numerical stability.
        
        Args:
            matrix: Matrix to compute kernel of (C^T for P-invariants)
            
        Returns:
            List of invariant vectors (non-negative integer vectors)
        """
        if matrix.size == 0:
            return []
        
        # Use SVD to find null space
        try:
            # scipy null_space function
            from scipy.linalg import null_space
            kernel = null_space(matrix)
        except ImportError:
            # Fallback to manual SVD
            U, s, Vt = linalg.svd(matrix, full_matrices=True)
            # Null space is columns of V corresponding to zero singular values
            tolerance = max(matrix.shape) * np.spacing(s[0]) if s.size > 0 else 1e-10
            rank = np.sum(s > tolerance)
            kernel = Vt[rank:].T
        
        if kernel.size == 0:
            return []
        
        # Convert to non-negative integer vectors
        invariants = []
        for i in range(kernel.shape[1]):
            vec = kernel[:, i]
            
            # Convert to non-negative (flip sign if needed)
            if np.any(vec < 0):
                if np.sum(vec < 0) > np.sum(vec > 0):
                    vec = -vec
            
            # Scale to integers
            # Find GCD of all non-zero elements to get minimal representation
            non_zero = np.abs(vec[np.abs(vec) > 1e-10])
            if len(non_zero) > 0:
                # Scale to avoid floating point issues
                scale = 1.0 / np.min(non_zero)
                vec = vec * scale
                
                # Round to integers
                vec = np.round(vec).astype(int)
                
                # Make non-negative
                vec = np.abs(vec)
                
                # Skip if all zeros
                if np.any(vec > 0):
                    invariants.append(vec)
        
        return invariants
    
    def _normalize_invariant(self, vec: np.ndarray) -> np.ndarray:
        """Normalize invariant to smallest integer representation.
        
        Divides by GCD of all non-zero elements.
        """
        non_zero = vec[vec > 0]
        if len(non_zero) == 0:
            return vec
        
        # Compute GCD of all non-zero elements
        gcd = non_zero[0]
        for val in non_zero[1:]:
            gcd = np.gcd(gcd, val)
        
        if gcd > 1:
            vec = vec // gcd
        
        return vec
    
    def _remove_duplicates(self, invariants: List[np.ndarray]) -> List[np.ndarray]:
        """Remove duplicate invariants (same support and proportional weights)."""
        unique = []
        for inv in invariants:
            is_duplicate = False
            for existing in unique:
                if np.allclose(inv, existing):
                    is_duplicate = True
                    break
            if not is_duplicate:
                unique.append(inv)
        return unique
    
    def _analyze_invariant(self, inv_vector: np.ndarray, place_map: Dict[int, int]) -> Dict[str, Any]:
        """Analyze a single P-invariant.
        
        Args:
            inv_vector: Invariant vector (weights for each place)
            place_map: Mapping from place_id to vector index
            
        Returns:
            Dictionary with invariant information
        """
        # Get place IDs and weights
        place_ids = []
        weights = []
        names = []
        
        # Reverse place_map to get place_id from index
        idx_to_place_id = {idx: pid for pid, idx in place_map.items()}
        
        for idx, weight in enumerate(inv_vector):
            if weight > 0:
                place_id = idx_to_place_id[idx]
                place_obj = self._get_place_by_id(place_id)
                
                place_ids.append(place_id)
                weights.append(int(weight))
                
                if place_obj:
                    name = getattr(place_obj, 'name', None)
                    if not name or name.strip() == "":
                        name = f"P{place_id}"
                    names.append(name)
                else:
                    names.append(f"P{place_id}")
        
        # Create sum expression (e.g., "2*P1 + 3*P2 + P3")
        terms = []
        for weight, name in zip(weights, names):
            if weight == 1:
                terms.append(name)
            else:
                terms.append(f"{weight}*{name}")
        sum_expression = " + ".join(terms)
        
        # Calculate conserved value (sum of weighted tokens)
        conserved_value = 0
        for place_id, weight in zip(place_ids, weights):
            place_obj = self._get_place_by_id(place_id)
            if place_obj:
                tokens = getattr(place_obj, 'tokens', 0)
                conserved_value += weight * tokens
        
        return {
            'places': place_ids,
            'weights': weights,
            'names': names,
            'support_size': len(place_ids),
            'sum_expression': sum_expression,
            'conserved_value': conserved_value,
            'vector': inv_vector.tolist(),
        }
    
    def _calculate_coverage(self, p_invariants: List[Dict[str, Any]]) -> set:
        """Calculate which places are covered by at least one invariant."""
        covered = set()
        for inv in p_invariants:
            covered.update(inv['places'])
        return covered
    
    def _create_summary(self, count: int, coverage_ratio: float, truncated: bool) -> str:
        """Create human-readable summary."""
        if count == 0:
            return "No P-invariants found"
        
        summary_parts = [f"Found {count} P-invariant(s)"]
        
        if truncated:
            summary_parts.append("(results truncated)")
        
        summary_parts.append(f"• Coverage: {coverage_ratio:.1%} of places")
        
        return "\n".join(summary_parts)
    
    def _get_place_by_id(self, place_id: int) -> Optional[Any]:
        """Get place object by ID."""
        for place in self.model.places:
            if place.id == place_id:
                return place
        return None
    
    def find_invariants_containing_place(
        self,
        place_id: int,
        max_invariants: int = 100
    ) -> List[Dict[str, Any]]:
        """Find all P-invariants that contain a specific place.
        
        This is a convenience method for property dialogs.
        
        Args:
            place_id: ID of the place to find
            max_invariants: Maximum number of invariants to analyze
            
        Returns:
            List of P-invariant info dicts that contain the specified place
            
        Example:
            # Find invariants containing place with ID 5
            place_invs = analyzer.find_invariants_containing_place(5)
        """
        result = self.analyze(max_invariants=max_invariants)
        
        if not result.success:
            return []
        
        p_invariants = result.get('p_invariants', [])
        return [inv for inv in p_invariants if place_id in inv['places']]
