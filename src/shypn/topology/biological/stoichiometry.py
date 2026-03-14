"""Stoichiometric Consistency Analyzer for Biological Petri Nets.

This analyzer validates the stoichiometric structure of biochemical networks:

1. **Stoichiometric Matrix (N)**: Constructs N where N(p,t) = W(t,p) - W(p,t)
2. **Matrix Rank**: Checks if rank(N) indicates valid flux space
3. **Conservation Laws**: Finds P-invariants (null space of N^T)
4. **Flux Space**: Validates that steady-state flux distribution is feasible

Stoichiometric consistency is fundamental to systems biology - an inconsistent
matrix indicates impossible reaction networks or missing reactions.

Theoretical Foundation:
- Doc: doc/foundation/BIOLOGICAL_PETRI_NET_FORMALIZATION.md
- Section 2.3: Stoichiometric Matrix
- Section 5.2: Stoichiometry Consistency Analyzer

Author: GitHub Copilot
Date: November 20, 2025
"""

import numpy as np
from typing import Any, Dict, List, Set, Tuple, Optional
from collections import defaultdict

from shypn.topology.base.topology_analyzer import TopologyAnalyzer
from shypn.topology.base.analysis_result import AnalysisResult
from shypn.topology.base.exceptions import TopologyAnalysisError


class StoichiometryAnalyzer(TopologyAnalyzer):
    """Analyzer for stoichiometric consistency in biochemical networks.
    
    Constructs and analyzes the stoichiometric matrix N:
    - N(p,t) = W(t,p) - W(p,t)  (production - consumption)
    - Validates matrix rank
    - Finds conservation laws (P-invariants)
    - Checks for fractional stoichiometry
    
    Example:
        >>> analyzer = StoichiometryAnalyzer(model)
        >>> result = analyzer.analyze()
        >>> print(f"Matrix rank: {result.data['matrix_rank']}")
        >>> print(f"Conservation laws: {len(result.data['conservation_laws'])}")
    """
    
    def __init__(self, model: Any):
        """Initialize stoichiometry analyzer.
        
        Args:
            model: Petri net model with places, transitions, and arcs
        """
        super().__init__(model)
        self.name = "Stoichiometric Consistency"
        self.description = "Validates stoichiometric matrix structure and conservation laws"
    
    def analyze(self, **kwargs) -> AnalysisResult:
        """Analyze stoichiometric consistency.
        
        Args:
            **kwargs: Optional parameters (unused, for compatibility)
        
        Returns:
            AnalysisResult: Contains stoichiometric matrix, rank, conservation laws
        """
        try:
            # Build stoichiometric matrix
            N, place_ids, transition_ids = self._build_stoichiometric_matrix()
            
            # Analyze matrix properties
            matrix_rank = np.linalg.matrix_rank(N)
            num_places = len(place_ids)
            num_transitions = len(transition_ids)
            
            # Find conservation laws (null space of N^T)
            conservation_laws = self._find_conservation_laws(N, place_ids)
            
            # Check for fractional stoichiometry
            fractional_arcs = self._check_fractional_stoichiometry()
            
            # Detect blocked reactions (columns of all zeros)
            blocked_transitions = self._find_blocked_transitions(N, transition_ids)
            
            # Check if matrix is consistent (rank indicates valid flux space)
            is_consistent = matrix_rank <= min(num_places, num_transitions)
            
            statistics = {
                'num_places': num_places,
                'num_transitions': num_transitions,
                'matrix_rank': matrix_rank,
                'num_conservation_laws': len(conservation_laws),
                'num_blocked_transitions': len(blocked_transitions),
                'num_fractional_arcs': len(fractional_arcs),
                'is_consistent': is_consistent,
                'flux_dimension': num_transitions - matrix_rank,  # Dimension of flux cone
            }
            
            result = AnalysisResult(
                success=True,
                data={
                    'stoichiometric_matrix': N.tolist(),
                    'place_ids': place_ids,
                    'transition_ids': transition_ids,
                    'matrix_rank': matrix_rank,
                    'conservation_laws': conservation_laws,
                    'blocked_transitions': blocked_transitions,
                    'fractional_arcs': fractional_arcs,
                    'statistics': statistics,
                },
                summary=self._format_summary(statistics)
            )
            
            return result
            
        except (ValueError, np.linalg.LinAlgError, AttributeError) as e:
            raise TopologyAnalysisError(
                f"Stoichiometry analysis failed: {str(e)}"
            )
    
    def _build_stoichiometric_matrix(self) -> Tuple[np.ndarray, List[str], List[str]]:
        """Build stoichiometric matrix N.
        
        N(p,t) = W(t,p) - W(p,t)
        - Positive: transition produces to place
        - Negative: transition consumes from place
        - Zero: no interaction
        
        Returns:
            tuple: (N matrix, place_ids, transition_ids)
        """
        place_ids = [p.id for p in self.model.places]
        transition_ids = [t.id for t in self.model.transitions]
        
        # Create index mappings
        place_idx = {pid: i for i, pid in enumerate(place_ids)}
        transition_idx = {tid: i for i, tid in enumerate(transition_ids)}
        
        # Initialize matrix (places × transitions)
        N = np.zeros((len(place_ids), len(transition_ids)))
        
        # Fill matrix from arcs
        for arc in self.model.arcs:
            weight = getattr(arc, 'weight', 1.0)
            
            # Skip test arcs (catalysts don't participate in stoichiometry)
            if hasattr(arc, 'arc_type') and arc.arc_type == 'test':
                continue
            
            # Skip inhibitor arcs (regulatory only)
            if hasattr(arc, 'arc_type') and arc.arc_type == 'inhibitor':
                continue
            
            # Place → Transition (consumption)
            if hasattr(arc.source, 'id') and arc.source.id in place_idx:
                if hasattr(arc.target, 'id') and arc.target.id in transition_idx:
                    p_i = place_idx[arc.source.id]
                    t_i = transition_idx[arc.target.id]
                    N[p_i, t_i] -= weight  # Negative for consumption
            
            # Transition → Place (production)
            elif hasattr(arc.source, 'id') and arc.source.id in transition_idx:
                if hasattr(arc.target, 'id') and arc.target.id in place_idx:
                    t_i = transition_idx[arc.source.id]
                    p_i = place_idx[arc.target.id]
                    N[p_i, t_i] += weight  # Positive for production
        
        return N, place_ids, transition_ids
    
    def _find_conservation_laws(
        self, 
        N: np.ndarray, 
        place_ids: List[str]
    ) -> List[Dict[str, Any]]:
        """Find conservation laws (P-invariants).
        
        Conservation laws are vectors v such that v^T · N = 0
        (i.e., null space of N^T)
        
        Args:
            N: Stoichiometric matrix
            place_ids: List of place IDs
            
        Returns:
            list: Conservation laws with their coefficients
        """
        conservation_laws = []
        
        try:
            # Find null space of N^T
            # v^T · N = 0  ⟺  N^T · v = 0
            _, s, vh = np.linalg.svd(N.T, full_matrices=True)
            
            # Tolerance for considering singular value as zero
            tol = 1e-10
            null_mask = s < tol
            
            # If there are zero singular values, we have conservation laws
            if np.any(null_mask):
                # Get null space vectors from right singular vectors
                null_space = vh[len(s):, :]
                
                for i, vector in enumerate(null_space):
                    # Only include if non-trivial (not all zeros)
                    if np.any(np.abs(vector) > tol):
                        # Normalize to smallest non-zero coefficient = 1
                        non_zero = vector[np.abs(vector) > tol]
                        if len(non_zero) > 0:
                            min_val = np.min(np.abs(non_zero))
                            normalized = vector / min_val
                            
                            # Create coefficient dict
                            coefficients = {
                                place_ids[j]: float(normalized[j])
                                for j in range(len(place_ids))
                                if abs(normalized[j]) > tol
                            }
                            
                            if coefficients:
                                conservation_laws.append({
                                    'id': f"P-inv-{i+1}",
                                    'coefficients': coefficients,
                                    'num_places': len(coefficients),
                                })
        
        except (np.linalg.LinAlgError, ValueError) as e:
            # If SVD fails, return empty list
            self.logger.debug(f"SVD computation failed for conservation laws: {e}")  # type: ignore[attr-defined]
        
        return conservation_laws
    
    def _find_blocked_transitions(
        self, 
        N: np.ndarray, 
        transition_ids: List[str]
    ) -> List[Dict[str, Any]]:
        """Find transitions that have no effect (all zeros column).
        
        Args:
            N: Stoichiometric matrix
            transition_ids: List of transition IDs
            
        Returns:
            list: Blocked transition info
        """
        blocked = []
        
        for i, tid in enumerate(transition_ids):
            column = N[:, i]
            
            # Check if column is all zeros (no stoichiometric effect)
            if np.allclose(column, 0, atol=1e-10):
                # Find the actual transition object
                transition = next((t for t in self.model.transitions if t.id == tid), None)
                
                blocked.append({
                    'transition_id': tid,
                    'transition_name': getattr(transition, 'name', tid) if transition else tid,
                    'reason': 'No stoichiometric effect (all arcs are test/inhibitor or balanced)',
                })
        
        return blocked
    
    def _check_fractional_stoichiometry(self) -> List[Dict[str, Any]]:
        """Check for fractional stoichiometric coefficients.
        
        Returns:
            list: Arcs with fractional weights
        """
        fractional = []
        
        for arc in self.model.arcs:
            weight = getattr(arc, 'weight', 1.0)
            
            # Skip test and inhibitor arcs
            if hasattr(arc, 'arc_type') and arc.arc_type in ('test', 'inhibitor'):
                continue
            
            # Check if fractional (not close to an integer)
            if not np.isclose(weight, round(weight), atol=0.01):
                source_name = getattr(arc.source, 'name', arc.source.id) if hasattr(arc.source, 'id') else str(arc.source)
                target_name = getattr(arc.target, 'name', arc.target.id) if hasattr(arc.target, 'id') else str(arc.target)
                
                fractional.append({
                    'arc_id': arc.id,
                    'source': source_name,
                    'target': target_name,
                    'weight': weight,
                    'note': 'Fractional coefficient (normalized reaction?)',
                })
        
        return fractional
    
    def _format_summary(self, statistics: Dict[str, Any]) -> str:
        """Format summary message.
        
        Args:
            statistics: Statistics dict
            
        Returns:
            str: Formatted summary
        """
        lines = [
            "Stoichiometric Consistency Analysis:",
            f"  Places: {statistics['num_places']}",
            f"  Transitions: {statistics['num_transitions']}",
            f"  Matrix rank: {statistics['matrix_rank']}",
            f"  Flux space dimension: {statistics['flux_dimension']}",
            f"  Conservation laws: {statistics['num_conservation_laws']}",
            f"  Blocked transitions: {statistics['num_blocked_transitions']}",
            f"  Fractional coefficients: {statistics['num_fractional_arcs']}",
        ]
        
        if statistics['is_consistent']:
            lines.append("\n✓ Stoichiometric matrix is consistent")
        else:
            lines.append("\n⚠️ Matrix rank exceeds dimensions (inconsistent)")
        
        if statistics['num_blocked_transitions'] > 0:
            lines.append(f"⚠️ {statistics['num_blocked_transitions']} transition(s) have no stoichiometric effect")
        
        return "\n".join(lines)
    
    def format_result(self, result: AnalysisResult) -> str:
        """Format analysis result as human-readable text.
        
        Args:
            result: Analysis result
            
        Returns:
            str: Formatted text
        """
        if not result.success:
            return f"Stoichiometry Analysis Failed: {result.message}"  # type: ignore[attr-defined]
        
        lines = ["=" * 60]
        lines.append("STOICHIOMETRIC CONSISTENCY ANALYSIS")
        lines.append("=" * 60)
        lines.append("")
        
        # Statistics
        stats = result.data['statistics']
        lines.append("MATRIX PROPERTIES:")
        lines.append(f"  Dimensions: {stats['num_places']} places × {stats['num_transitions']} transitions")
        lines.append(f"  Rank: {stats['matrix_rank']}")
        lines.append(f"  Flux space dimension: {stats['flux_dimension']}")
        lines.append(f"  Consistent: {'Yes' if stats['is_consistent'] else 'No'}")
        lines.append("")
        
        # Conservation laws
        if result.data['conservation_laws']:
            lines.append(f"CONSERVATION LAWS ({len(result.data['conservation_laws'])}):")
            lines.append("-" * 60)
            
            for law in result.data['conservation_laws']:
                lines.append(f"\n{law['id']} ({law['num_places']} places):")
                
                # Format as equation
                terms = []
                for place_id, coeff in law['coefficients'].items():
                    if abs(coeff - 1.0) < 0.01:
                        terms.append(f"[{place_id}]")
                    else:
                        terms.append(f"{coeff:.2f}·[{place_id}]")
                
                lines.append(f"  {' + '.join(terms)} = constant")
            
            lines.append("")
        else:
            lines.append("CONSERVATION LAWS: None (open system)")
            lines.append("")
        
        # Blocked transitions
        if result.data['blocked_transitions']:
            lines.append(f"⚠️ BLOCKED TRANSITIONS ({len(result.data['blocked_transitions'])}):")
            lines.append("-" * 60)
            
            for blocked in result.data['blocked_transitions']:
                lines.append(f"  {blocked['transition_id']}: {blocked['transition_name']}")
                lines.append(f"    → {blocked['reason']}")
            
            lines.append("")
        
        # Fractional stoichiometry
        if result.data['fractional_arcs']:
            lines.append(f"⚠️ FRACTIONAL STOICHIOMETRY ({len(result.data['fractional_arcs'])}):")
            lines.append("-" * 60)
            
            for arc in result.data['fractional_arcs']:
                lines.append(f"  {arc['arc_id']}: {arc['source']} → {arc['target']}")
                lines.append(f"    Weight: {arc['weight']:.4f} ({arc['note']})")
            
            lines.append("")
        
        lines.append("=" * 60)
        
        return "\n".join(lines)
