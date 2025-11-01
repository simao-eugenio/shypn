"""Dependency and Coupling Analyzer for Biological Petri Nets.

This analyzer implements the refined locality theory from the Biological Petri Net
formalization, distinguishing between:

1. **Strongly Independent**: No shared places at all
   - ∀t₁, t₂ ∈ T: (•t₁ ∪ t₁• ∪ Σ(t₁)) ∩ (•t₂ ∪ t₂• ∪ Σ(t₂)) = ∅
   - True parallelism, no interference

2. **Competitive (True Conflict)**: Shared input places
   - ∃p ∈ P: p ∈ •t₁ ∧ p ∈ •t₂ ∧ arc(p,t₁).consumes ∧ arc(p,t₂).consumes
   - Both consume from same source → resource competition
   - REQUIRES: Sequential execution or priority resolution

3. **Convergent (Valid Coupling)**: Shared output places only
   - (•t₁ ∩ •t₂) = ∅  (no input competition)
   - (t₁• ∩ t₂•) ≠ ∅  (share output targets)
   - Rates SUPERPOSE: dM/dt = r₁ + r₂ (Linear combination principle)
   - CORRECT BIOLOGICAL BEHAVIOR: Multiple pathways producing same metabolite

4. **Regulatory (Valid Coupling)**: Shared catalyst places (test arcs)
   - ∃p ∈ P: p ∈ Σ(t₁) ∧ p ∈ Σ(t₂)  (shared regulatory place)
   - Σ(t) = {p | arc(p,t) is test arc (read-only, non-consuming)}
   - Enzyme/catalyst shared between reactions
   - CORRECT BIOLOGICAL BEHAVIOR: Same enzyme catalyzes multiple reactions

This analyzer is KEY to validating the refined locality theory and showing that
~80% of "dependencies" in biological models are actually valid couplings, not conflicts.

Theoretical Foundation:
- Doc: doc/foundation/BIOLOGICAL_PETRI_NET_FORMALIZATION.md
- Section 3.1: Locality and Independence
- Section 2.2: Superposition Principle for Convergent Sharing

Author: GitHub Copilot (based on user's refined locality theory)
Date: October 31, 2025
"""

from typing import Any, Dict, List, Set, Tuple, Optional
from collections import defaultdict

from shypn.topology.base.topology_analyzer import TopologyAnalyzer
from shypn.topology.base.analysis_result import AnalysisResult
from shypn.topology.base.exceptions import TopologyAnalysisError


class DependencyAndCouplingAnalyzer(TopologyAnalyzer):
    """Analyzer for dependency and coupling relationships in Biological Petri Nets.
    
    Classifies transition pairs into four categories:
    1. Strongly Independent (no shared places)
    2. Competitive (shared inputs → conflict)
    3. Convergent (shared outputs → coupling OK)
    4. Regulatory (shared catalysts → coupling OK)
    
    This analyzer validates the refined locality theory: most "dependencies" in
    biological models are actually valid couplings, not true conflicts.
    
    Example:
        >>> analyzer = DependencyAndCouplingAnalyzer(model)
        >>> result = analyzer.analyze()
        >>> print(f"True conflicts: {result.data['competitive_count']}")
        >>> print(f"Valid couplings: {result.data['convergent_count'] + result.data['regulatory_count']}")
    """
    
    def __init__(self, model: Any):
        """Initialize dependency and coupling analyzer.
        
        Args:
            model: Petri net model with places, transitions, and arcs
        """
        super().__init__(model)
        self.name = "Dependency & Coupling"
        self.description = "Classify transition dependencies (Strong Independence vs Weak Independence)"
    
    def analyze(self, **kwargs) -> AnalysisResult:
        """Analyze dependency and coupling relationships.
        
        Returns:
            AnalysisResult with:
            - strongly_independent: List of (t1, t2) pairs with no shared places
            - competitive: List of (t1, t2) pairs with input competition
            - convergent: List of (t1, t2) pairs with output convergence only
            - regulatory: List of (t1, t2) pairs with shared catalysts only
            - statistics: Counts and percentages for each category
            - interpretation: Biological interpretation of results
        """
        start_time = self._start_timer()
        
        try:
            # Validate model
            self._validate_model()
            
            # Build place usage maps
            input_places, output_places, regulatory_places = self._build_place_usage_maps()
            
            # Classify all transition pairs
            classifications = self._classify_transition_pairs(
                input_places, output_places, regulatory_places
            )
            
            # Calculate statistics
            stats = self._calculate_statistics(classifications)
            
            # Generate interpretation
            interpretation = self._generate_interpretation(stats)
            
            # Prepare result
            return AnalysisResult(
                success=True,
                data={
                    'classifications': classifications,
                    'statistics': stats,
                    'interpretation': interpretation,
                    'input_places': {t_id: list(places) for t_id, places in input_places.items()},
                    'output_places': {t_id: list(places) for t_id, places in output_places.items()},
                    'regulatory_places': {t_id: list(places) for t_id, places in regulatory_places.items()},
                },
                summary=f"Analyzed {stats['total_pairs']} transition pairs: "
                       f"{stats['competitive_count']} conflicts, "
                       f"{stats['convergent_count'] + stats['regulatory_count']} valid couplings",
                metadata={
                    'analysis_time': self._end_timer(start_time),
                    'model_size': {
                        'places': len(self.model.places),
                        'transitions': len(self.model.transitions),
                        'arcs': len(self.model.arcs)
                    }
                }
            )
            
        except TopologyAnalysisError as e:
            return AnalysisResult(
                success=False,
                errors=[str(e)],
                metadata={'analysis_time': self._end_timer(start_time)}
            )
        except Exception as e:
            return AnalysisResult(
                success=False,
                errors=[f"Unexpected error: {str(e)}"],
                metadata={'analysis_time': self._end_timer(start_time)}
            )
    
    def _validate_model(self):
        """Validate that model has required attributes.
        
        Raises:
            TopologyAnalysisError: If model is invalid
        """
        if not hasattr(self.model, 'places'):
            raise TopologyAnalysisError("Model has no 'places' attribute")
        if not hasattr(self.model, 'transitions'):
            raise TopologyAnalysisError("Model has no 'transitions' attribute")
        if not hasattr(self.model, 'arcs'):
            raise TopologyAnalysisError("Model has no 'arcs' attribute")
        
        if len(self.model.transitions) == 0:
            raise TopologyAnalysisError("Model has no transitions")
    
    def _build_place_usage_maps(self) -> Tuple[Dict, Dict, Dict]:
        """Build maps of which places each transition uses as input/output/regulatory.
        
        Returns:
            Tuple of (input_places, output_places, regulatory_places)
            Each is a dict mapping transition_id → set of place_ids
        """
        input_places = defaultdict(set)  # •t: places consumed by transition
        output_places = defaultdict(set)  # t•: places produced by transition
        regulatory_places = defaultdict(set)  # Σ(t): places in test arcs (catalysts)
        
        # Handle both dict and list structures
        arcs = self.model.arcs.values() if hasattr(self.model.arcs, 'values') else self.model.arcs
        
        for arc in arcs:
            # Determine arc direction and type
            source_id = arc.source.id if hasattr(arc.source, 'id') else arc.source_id
            target_id = arc.target.id if hasattr(arc.target, 'id') else arc.target_id
            
            # Check if it's a test arc (non-consuming, regulatory)
            is_test_arc = hasattr(arc, 'consumes_tokens') and not arc.consumes_tokens()
            
            # Place → Transition (input or regulatory)
            if self._is_place(arc.source) and self._is_transition(arc.target):
                if is_test_arc:
                    regulatory_places[target_id].add(source_id)
                else:
                    input_places[target_id].add(source_id)
            
            # Transition → Place (output)
            elif self._is_transition(arc.source) and self._is_place(arc.target):
                output_places[source_id].add(target_id)
        
        return input_places, output_places, regulatory_places
    
    def _is_place(self, obj) -> bool:
        """Check if object is a Place."""
        from shypn.netobjs.place import Place
        return isinstance(obj, Place)
    
    def _is_transition(self, obj) -> bool:
        """Check if object is a Transition."""
        from shypn.netobjs.transition import Transition
        return isinstance(obj, Transition)
    
    def _classify_transition_pairs(
        self,
        input_places: Dict,
        output_places: Dict,
        regulatory_places: Dict
    ) -> Dict[str, List[Tuple[str, str, Dict]]]:
        """Classify all transition pairs by dependency type.
        
        Args:
            input_places: Map of transition_id → input place_ids
            output_places: Map of transition_id → output place_ids
            regulatory_places: Map of transition_id → regulatory place_ids
        
        Returns:
            Dict with keys: 'strongly_independent', 'competitive', 'convergent', 'regulatory'
            Each value is a list of (t1_id, t2_id, details_dict) tuples
        """
        classifications = {
            'strongly_independent': [],
            'competitive': [],
            'convergent': [],
            'regulatory': []
        }
        
        # Get all transitions
        transitions = self.model.transitions.values() if hasattr(self.model.transitions, 'values') else self.model.transitions
        transition_ids = [t.id for t in transitions]
        
        # Compare all pairs (only once: i < j)
        for i, t1_id in enumerate(transition_ids):
            for t2_id in transition_ids[i+1:]:
                # Get place sets for each transition
                t1_inputs = input_places.get(t1_id, set())
                t1_outputs = output_places.get(t1_id, set())
                t1_regulatory = regulatory_places.get(t1_id, set())
                
                t2_inputs = input_places.get(t2_id, set())
                t2_outputs = output_places.get(t2_id, set())
                t2_regulatory = regulatory_places.get(t2_id, set())
                
                # Calculate intersections
                shared_inputs = t1_inputs & t2_inputs
                shared_outputs = t1_outputs & t2_outputs
                shared_regulatory = t1_regulatory & t2_regulatory
                
                # Total shared places
                all_shared = shared_inputs | shared_outputs | shared_regulatory
                
                # Classification logic
                if len(all_shared) == 0:
                    # No shared places at all → Strongly Independent
                    classifications['strongly_independent'].append((
                        t1_id, t2_id,
                        {
                            'description': 'No shared places (true parallelism)',
                            'shared_places': []
                        }
                    ))
                
                elif len(shared_inputs) > 0:
                    # Shared input places → Competitive (conflict)
                    classifications['competitive'].append((
                        t1_id, t2_id,
                        {
                            'description': 'Shared input places (resource competition)',
                            'shared_inputs': list(shared_inputs),
                            'shared_outputs': list(shared_outputs),
                            'shared_regulatory': list(shared_regulatory),
                            'conflict_type': 'input_competition'
                        }
                    ))
                
                elif len(shared_outputs) > 0:
                    # Shared output places only → Convergent (valid coupling)
                    classifications['convergent'].append((
                        t1_id, t2_id,
                        {
                            'description': 'Shared output places (metabolite convergence - rates superpose)',
                            'shared_outputs': list(shared_outputs),
                            'shared_regulatory': list(shared_regulatory),
                            'coupling_type': 'convergent',
                            'biological_interpretation': 'Multiple pathways producing same metabolite'
                        }
                    ))
                
                elif len(shared_regulatory) > 0:
                    # Shared regulatory places only → Regulatory (valid coupling)
                    classifications['regulatory'].append((
                        t1_id, t2_id,
                        {
                            'description': 'Shared catalyst/enzyme (non-consuming regulatory coupling)',
                            'shared_regulatory': list(shared_regulatory),
                            'coupling_type': 'regulatory',
                            'biological_interpretation': 'Same enzyme catalyzes multiple reactions'
                        }
                    ))
        
        return classifications
    
    def _calculate_statistics(self, classifications: Dict) -> Dict:
        """Calculate statistics from classifications.
        
        Args:
            classifications: Dict with classified transition pairs
        
        Returns:
            Dict with counts, percentages, and summary statistics
        """
        strongly_independent_count = len(classifications['strongly_independent'])
        competitive_count = len(classifications['competitive'])
        convergent_count = len(classifications['convergent'])
        regulatory_count = len(classifications['regulatory'])
        
        total_pairs = (strongly_independent_count + competitive_count + 
                      convergent_count + regulatory_count)
        
        # Calculate percentages
        def percentage(count, total):
            return (count / total * 100) if total > 0 else 0.0
        
        # Valid couplings = convergent + regulatory
        valid_couplings_count = convergent_count + regulatory_count
        
        # Weakly independent = strongly independent + valid couplings
        weakly_independent_count = strongly_independent_count + valid_couplings_count
        
        return {
            'total_pairs': total_pairs,
            'strongly_independent_count': strongly_independent_count,
            'competitive_count': competitive_count,
            'convergent_count': convergent_count,
            'regulatory_count': regulatory_count,
            'valid_couplings_count': valid_couplings_count,
            'weakly_independent_count': weakly_independent_count,
            'strongly_independent_pct': percentage(strongly_independent_count, total_pairs),
            'competitive_pct': percentage(competitive_count, total_pairs),
            'convergent_pct': percentage(convergent_count, total_pairs),
            'regulatory_pct': percentage(regulatory_count, total_pairs),
            'valid_couplings_pct': percentage(valid_couplings_count, total_pairs),
            'weakly_independent_pct': percentage(weakly_independent_count, total_pairs),
        }
    
    def _generate_interpretation(self, stats: Dict) -> str:
        """Generate biological interpretation of results.
        
        Args:
            stats: Statistics dictionary
        
        Returns:
            Human-readable interpretation string
        """
        lines = []
        
        lines.append("=== DEPENDENCY & COUPLING ANALYSIS ===\n")
        
        # Summary
        total = stats['total_pairs']
        if total == 0:
            return "No transition pairs to analyze (model has ≤1 transition)."
        
        lines.append(f"Total transition pairs analyzed: {total}\n")
        
        # Strong Independence
        si_count = stats['strongly_independent_count']
        si_pct = stats['strongly_independent_pct']
        lines.append(f"1. STRONGLY INDEPENDENT: {si_count} ({si_pct:.1f}%)")
        lines.append("   → No shared places at all")
        lines.append("   → True parallelism, can execute simultaneously\n")
        
        # Competitive (True Conflicts)
        comp_count = stats['competitive_count']
        comp_pct = stats['competitive_pct']
        lines.append(f"2. COMPETITIVE (TRUE CONFLICTS): {comp_count} ({comp_pct:.1f}%)")
        lines.append("   → Shared input places (resource competition)")
        lines.append("   → REQUIRES: Sequential execution or priority resolution")
        lines.append("   → Classical PN conflict resolution applies\n")
        
        # Convergent (Valid Coupling)
        conv_count = stats['convergent_count']
        conv_pct = stats['convergent_pct']
        lines.append(f"3. CONVERGENT (VALID COUPLING): {conv_count} ({conv_pct:.1f}%)")
        lines.append("   → Shared output places only (no input competition)")
        lines.append("   → Multiple pathways producing same metabolite")
        lines.append("   → Rates SUPERPOSE: dM/dt = r₁ + r₂")
        lines.append("   → CORRECT BIOLOGICAL BEHAVIOR\n")
        
        # Regulatory (Valid Coupling)
        reg_count = stats['regulatory_count']
        reg_pct = stats['regulatory_pct']
        lines.append(f"4. REGULATORY (VALID COUPLING): {reg_count} ({reg_pct:.1f}%)")
        lines.append("   → Shared catalyst/enzyme places (test arcs)")
        lines.append("   → Same enzyme catalyzes multiple reactions")
        lines.append("   → Non-consuming regulatory dependency")
        lines.append("   → CORRECT BIOLOGICAL BEHAVIOR\n")
        
        # Key Insight
        valid_count = stats['valid_couplings_count']
        valid_pct = stats['valid_couplings_pct']
        lines.append("=== KEY INSIGHT ===")
        lines.append(f"Valid Couplings (Convergent + Regulatory): {valid_count} ({valid_pct:.1f}%)")
        lines.append(f"True Conflicts (Competitive): {comp_count} ({comp_pct:.1f}%)")
        
        if valid_count > comp_count:
            ratio = valid_count / comp_count if comp_count > 0 else float('inf')
            lines.append(f"\n✓ {ratio:.1f}x MORE valid couplings than true conflicts!")
            lines.append("  This validates the refined locality theory:")
            lines.append("  Most 'dependencies' in biological models are actually")
            lines.append("  CORRECT BIOLOGICAL COUPLINGS, not conflicts.\n")
        
        # Weak Independence Summary
        weak_count = stats['weakly_independent_count']
        weak_pct = stats['weakly_independent_pct']
        lines.append(f"Weakly Independent (Strong Independent + Valid Couplings): {weak_count} ({weak_pct:.1f}%)")
        lines.append("→ These transition pairs can execute in parallel without interference\n")
        
        return '\n'.join(lines)
    
    def _start_timer(self) -> float:
        """Start timing analysis."""
        import time
        return time.time()
    
    def _end_timer(self, start_time: float) -> float:
        """End timing and return elapsed seconds."""
        import time
        return time.time() - start_time
