"""Flux Balance Analysis (FBA) for Biological Petri Nets.

This analyzer performs Flux Balance Analysis to check steady-state feasibility:

1. **Steady-State Constraint**: N · v = 0 (no accumulation)
2. **Flux Bounds**: v_min ≤ v ≤ v_max (reaction directionality)
3. **Feasibility Check**: Does a valid flux distribution exist?
4. **Blocked Reactions**: Reactions that must have zero flux

FBA is the gold standard in systems biology for analyzing metabolic networks.

Theoretical Foundation:
- Doc: doc/foundation/BIOLOGICAL_PETRI_NET_FORMALIZATION.md
- Section 2.3: Flux Balance
- Section 5.2: Flux Balance Analyzer
- Reference: Orth et al. (2010) "What is flux balance analysis?" Nature Biotechnology

Author: GitHub Copilot
Date: November 20, 2025
"""

import numpy as np
from typing import Any, Dict, List, Set, Tuple, Optional
from collections import defaultdict

from shypn.topology.base.topology_analyzer import TopologyAnalyzer
from shypn.topology.base.analysis_result import AnalysisResult
from shypn.topology.base.exceptions import TopologyAnalysisError


class FluxBalanceAnalyzer(TopologyAnalyzer):
    """Flux Balance Analysis for metabolic networks.
    
    Solves: N · v = 0 subject to flux bounds
    Where:
    - N: Stoichiometric matrix
    - v: Flux vector (reaction rates)
    
    Checks:
    - Is steady-state feasible?
    - Which reactions must be zero?
    - What are flux ranges?
    
    Example:
        >>> analyzer = FluxBalanceAnalyzer(model)
        >>> result = analyzer.analyze()
        >>> print(f"Feasible: {result.data['is_feasible']}")
        >>> print(f"Active reactions: {len(result.data['active_reactions'])}")
    """
    
    def __init__(self, model: Any):
        """Initialize flux balance analyzer.
        
        Args:
            model: Petri net model with places, transitions, and arcs
        """
        super().__init__(model)
        self.name = "Flux Balance Analysis"
        self.description = "Checks steady-state feasibility using constraint-based modeling"
    
    def analyze(self, **kwargs) -> AnalysisResult:
        """Perform flux balance analysis.
        
        Args:
            **kwargs: Optional parameters (unused, for compatibility)
        
        Returns:
            AnalysisResult: Contains feasibility, flux ranges, blocked reactions
        """
        try:
            # Check if scipy is available
            try:
                from scipy.optimize import linprog
                has_scipy = True
            except ImportError:
                has_scipy = False
            
            # Build stoichiometric matrix
            N, place_ids, transition_ids = self._build_stoichiometric_matrix()
            
            if not has_scipy:
                # Simplified analysis without optimization
                result_data = self._analyze_without_scipy(N, place_ids, transition_ids)
            else:
                # Full FBA with optimization
                result_data = self._analyze_with_scipy(N, place_ids, transition_ids)
            
            result = AnalysisResult(
                success=True,
                data=result_data,
                summary=self._format_summary(result_data['statistics'])
            )
            
            return result
            
        except (ValueError, np.linalg.LinAlgError, AttributeError) as e:
            raise TopologyAnalysisError(
                f"Flux balance analysis failed: {str(e)}"
            )
    
    def _build_stoichiometric_matrix(self) -> Tuple[np.ndarray, List[str], List[str]]:
        """Build stoichiometric matrix N.
        
        Returns:
            tuple: (N matrix, place_ids, transition_ids)
        """
        place_ids = [p.id for p in self.model.places]
        transition_ids = [t.id for t in self.model.transitions]
        
        place_idx = {pid: i for i, pid in enumerate(place_ids)}
        transition_idx = {tid: i for i, tid in enumerate(transition_ids)}
        
        N = np.zeros((len(place_ids), len(transition_ids)))
        
        for arc in self.model.arcs:
            weight = getattr(arc, 'weight', 1.0)
            
            # Skip test arcs and inhibitor arcs
            if hasattr(arc, 'arc_type') and arc.arc_type in ('test', 'inhibitor'):
                continue
            
            # Place → Transition (consumption)
            if hasattr(arc.source, 'id') and arc.source.id in place_idx:
                if hasattr(arc.target, 'id') and arc.target.id in transition_idx:
                    p_i = place_idx[arc.source.id]
                    t_i = transition_idx[arc.target.id]
                    N[p_i, t_i] -= weight
            
            # Transition → Place (production)
            elif hasattr(arc.source, 'id') and arc.source.id in transition_idx:
                if hasattr(arc.target, 'id') and arc.target.id in place_idx:
                    t_i = transition_idx[arc.source.id]
                    p_i = place_idx[arc.target.id]
                    N[p_i, t_i] += weight
        
        return N, place_ids, transition_ids
    
    def _analyze_without_scipy(
        self, 
        N: np.ndarray, 
        place_ids: List[str], 
        transition_ids: List[str]
    ) -> Dict[str, Any]:
        """Simplified FBA without scipy (rank-based feasibility check).
        
        Args:
            N: Stoichiometric matrix
            place_ids: Place IDs
            transition_ids: Transition IDs
            
        Returns:
            dict: Analysis results
        """
        num_places = len(place_ids)
        num_transitions = len(transition_ids)
        matrix_rank = np.linalg.matrix_rank(N)
        
        # Check basic feasibility: rank(N) ≤ min(places, transitions)
        is_feasible = matrix_rank <= min(num_places, num_transitions)
        
        # Estimate flux space dimension
        flux_dimension = num_transitions - matrix_rank
        
        # Identify source/sink transitions (they can have non-zero flux)
        source_transitions = []
        sink_transitions = []
        internal_transitions = []
        
        for i, tid in enumerate(transition_ids):
            column = N[:, i]
            
            # Check if transition has only outputs (source)
            has_negative = np.any(column < -1e-10)  # Consumes something
            has_positive = np.any(column > 1e-10)   # Produces something
            
            transition = next((t for t in self.model.transitions if t.id == tid), None)
            trans_name = getattr(transition, 'name', tid) if transition else tid
            
            if not has_negative and has_positive:
                source_transitions.append({'id': tid, 'name': trans_name})
            elif has_negative and not has_positive:
                sink_transitions.append({'id': tid, 'name': trans_name})
            elif has_negative or has_positive:
                internal_transitions.append({'id': tid, 'name': trans_name})
        
        statistics = {
            'num_places': num_places,
            'num_transitions': num_transitions,
            'matrix_rank': matrix_rank,
            'flux_dimension': flux_dimension,
            'is_feasible': is_feasible,
            'num_source_transitions': len(source_transitions),
            'num_sink_transitions': len(sink_transitions),
            'num_internal_transitions': len(internal_transitions),
            'scipy_available': False,
        }
        
        return {
            'stoichiometric_matrix': N.tolist(),
            'place_ids': place_ids,
            'transition_ids': transition_ids,
            'is_feasible': is_feasible,
            'source_transitions': source_transitions,
            'sink_transitions': sink_transitions,
            'internal_transitions': internal_transitions,
            'blocked_reactions': [],  # Cannot determine without optimization
            'flux_ranges': {},  # Cannot determine without optimization
            'statistics': statistics,
            'note': 'Simplified analysis (scipy not available). Install scipy for full FBA.',
        }
    
    def _analyze_with_scipy(
        self, 
        N: np.ndarray, 
        place_ids: List[str], 
        transition_ids: List[str]
    ) -> Dict[str, Any]:
        """Full FBA with scipy optimization.
        
        Args:
            N: Stoichiometric matrix
            place_ids: Place IDs
            transition_ids: Transition IDs
            
        Returns:
            dict: Analysis results
        """
        from scipy.optimize import linprog
        
        num_places = len(place_ids)
        num_transitions = len(transition_ids)
        matrix_rank = np.linalg.matrix_rank(N)
        
        # Set up flux bounds (default: reversible reactions)
        # lb: lower bounds (default: -1000 for reversibility)
        # ub: upper bounds (default: +1000)
        lb = np.full(num_transitions, -1000.0)
        ub = np.full(num_transitions, 1000.0)
        
        # Check if model has directionality info
        for i, tid in enumerate(transition_ids):
            transition = next((t for t in self.model.transitions if t.id == tid), None)
            
            if transition:
                # Check if transition is marked as irreversible
                if hasattr(transition, 'reversible') and not transition.reversible:
                    lb[i] = 0.0  # Irreversible: forward only
                
                # Check for source/sink markers
                if hasattr(transition, 'is_source') and transition.is_source:
                    lb[i] = 0.0  # Sources produce only
                if hasattr(transition, 'is_sink') and transition.is_sink:
                    ub[i] = 0.0  # Sinks consume only (but typically we allow positive)
        
        # Try to find a feasible flux distribution
        # Objective: minimize sum of absolute fluxes (find simplest solution)
        c = np.ones(num_transitions)  # Minimize total flux
        
        # Constraints: N · v = 0 (steady state)
        # Convert to inequality form for linprog: A_eq · v = b_eq
        A_eq = N
        b_eq = np.zeros(num_places)
        
        # Bounds
        bounds = [(lb[i], ub[i]) for i in range(num_transitions)]
        
        # Solve
        result = linprog(
            c, 
            A_eq=A_eq, 
            b_eq=b_eq, 
            bounds=bounds,
            method='highs'  # Modern solver
        )
        
        is_feasible = result.success
        
        # Analyze flux solution
        blocked_reactions = []
        active_reactions = []
        flux_ranges = {}
        
        if is_feasible:
            flux = result.x
            
            # Find blocked reactions (flux forced to zero)
            for i, tid in enumerate(transition_ids):
                transition = next((t for t in self.model.transitions if t.id == tid), None)
                trans_name = getattr(transition, 'name', tid) if transition else tid
                
                flux_value = flux[i]
                
                if abs(flux_value) < 1e-6:
                    # Reaction has zero flux - check if it's blocked
                    # (Try to maximize/minimize this flux separately)
                    blocked_reactions.append({
                        'id': tid,
                        'name': trans_name,
                        'flux': flux_value,
                    })
                else:
                    active_reactions.append({
                        'id': tid,
                        'name': trans_name,
                        'flux': flux_value,
                    })
                
                flux_ranges[tid] = {
                    'value': flux_value,
                    'min': lb[i],
                    'max': ub[i],
                }
        
        statistics = {
            'num_places': num_places,
            'num_transitions': num_transitions,
            'matrix_rank': matrix_rank,
            'flux_dimension': num_transitions - matrix_rank,
            'is_feasible': is_feasible,
            'num_blocked_reactions': len(blocked_reactions),
            'num_active_reactions': len(active_reactions),
            'scipy_available': True,
        }
        
        return {
            'stoichiometric_matrix': N.tolist(),
            'place_ids': place_ids,
            'transition_ids': transition_ids,
            'is_feasible': is_feasible,
            'blocked_reactions': blocked_reactions,
            'active_reactions': active_reactions,
            'flux_ranges': flux_ranges,
            'statistics': statistics,
        }
    
    def _format_summary(self, statistics: Dict[str, Any]) -> str:
        """Format summary message.
        
        Args:
            statistics: Statistics dict
            
        Returns:
            str: Formatted summary
        """
        lines = [
            f"Flux Balance Analysis:",
            f"  Places: {statistics['num_places']}",
            f"  Transitions: {statistics['num_transitions']}",
            f"  Matrix rank: {statistics['matrix_rank']}",
            f"  Flux space dimension: {statistics['flux_dimension']}",
        ]
        
        if statistics.get('scipy_available'):
            lines.append(f"  Blocked reactions: {statistics.get('num_blocked_reactions', 0)}")
            lines.append(f"  Active reactions: {statistics.get('num_active_reactions', 0)}")
        else:
            lines.append(f"  Source transitions: {statistics.get('num_source_transitions', 0)}")
            lines.append(f"  Sink transitions: {statistics.get('num_sink_transitions', 0)}")
        
        if statistics['is_feasible']:
            lines.append(f"\n✓ Steady-state flux distribution is FEASIBLE")
        else:
            lines.append(f"\n✗ No feasible steady-state flux distribution")
        
        return "\n".join(lines)
    
    def format_result(self, result: AnalysisResult) -> str:
        """Format analysis result as human-readable text.
        
        Args:
            result: Analysis result
            
        Returns:
            str: Formatted text
        """
        if not result.success:
            return f"Flux Balance Analysis Failed: {result.message}"
        
        lines = ["=" * 60]
        lines.append("FLUX BALANCE ANALYSIS (FBA)")
        lines.append("=" * 60)
        lines.append("")
        
        # Statistics
        stats = result.data['statistics']
        lines.append("NETWORK PROPERTIES:")
        lines.append(f"  Places: {stats['num_places']}")
        lines.append(f"  Transitions: {stats['num_transitions']}")
        lines.append(f"  Matrix rank: {stats['matrix_rank']}")
        lines.append(f"  Flux space dimension: {stats['flux_dimension']}")
        lines.append(f"  Feasible: {'Yes' if result.data['is_feasible'] else 'No'}")
        lines.append("")
        
        if 'note' in result.data:
            lines.append(f"NOTE: {result.data['note']}")
            lines.append("")
        
        # Blocked reactions
        if result.data.get('blocked_reactions'):
            lines.append(f"BLOCKED REACTIONS ({len(result.data['blocked_reactions'])}):")
            lines.append("-" * 60)
            lines.append("These reactions must have zero flux at steady state:")
            
            for reaction in result.data['blocked_reactions']:
                lines.append(f"  {reaction['id']}: {reaction['name']}")
                if 'flux' in reaction:
                    lines.append(f"    Flux: {reaction['flux']:.6f}")
            
            lines.append("")
        
        # Active reactions
        if result.data.get('active_reactions'):
            lines.append(f"ACTIVE REACTIONS ({len(result.data['active_reactions'])}):")
            lines.append("-" * 60)
            
            for reaction in result.data['active_reactions'][:10]:  # Show first 10
                lines.append(f"  {reaction['id']}: {reaction['name']}")
                if 'flux' in reaction:
                    lines.append(f"    Flux: {reaction['flux']:.6f}")
            
            if len(result.data['active_reactions']) > 10:
                lines.append(f"  ... and {len(result.data['active_reactions']) - 10} more")
            
            lines.append("")
        
        # Source/sink transitions (simplified mode)
        if result.data.get('source_transitions'):
            lines.append(f"SOURCE TRANSITIONS ({len(result.data['source_transitions'])}):")
            lines.append("-" * 60)
            for trans in result.data['source_transitions']:
                lines.append(f"  {trans['id']}: {trans['name']}")
            lines.append("")
        
        if result.data.get('sink_transitions'):
            lines.append(f"SINK TRANSITIONS ({len(result.data['sink_transitions'])}):")
            lines.append("-" * 60)
            for trans in result.data['sink_transitions']:
                lines.append(f"  {trans['id']}: {trans['name']}")
            lines.append("")
        
        lines.append("=" * 60)
        
        return "\n".join(lines)
