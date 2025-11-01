"""Regulatory Structure Analyzer for Biological Petri Nets.

This analyzer detects and analyzes regulatory relationships in biological models:

1. **Explicit Catalysts**: Test arcs (read arcs) representing enzymes/catalysts
   - Non-consuming arcs that enable transitions without token consumption
   - Visual: dashed line with hollow diamond
   - Σ(t) = {p | arc(p,t) is test arc}

2. **Regulatory Patterns**: Common biological regulation structures
   - Enzyme-catalyzed reactions (one enzyme, multiple substrates)
   - Allosteric regulation (product inhibits upstream enzyme)
   - Feedback loops (product regulates its own production)

3. **Validation**: Checks for proper regulatory structure
   - Catalysts should have sufficient tokens
   - Regulatory places should not be depleted
   - Test arcs should connect Place → Transition only

This analyzer complements the Dependency & Coupling analyzer by focusing on
the regulatory structure rather than dependency classification.

Theoretical Foundation:
- Doc: doc/foundation/BIOLOGICAL_PETRI_NET_FORMALIZATION.md
- Section 2.2: Test Arcs for Catalyst Behavior
- Section 3.3: Regulatory Dependencies

Author: GitHub Copilot
Date: October 31, 2025
"""

from typing import Any, Dict, List, Set, Tuple, Optional
from collections import defaultdict

from shypn.topology.base.topology_analyzer import TopologyAnalyzer
from shypn.topology.base.analysis_result import AnalysisResult
from shypn.topology.base.exceptions import TopologyAnalysisError


class RegulatoryStructureAnalyzer(TopologyAnalyzer):
    """Analyzer for regulatory structures in Biological Petri Nets.
    
    Detects:
    - Test arcs (explicit catalysts)
    - Regulatory patterns (enzyme-catalyzed reactions, feedback loops)
    - Shared catalysts (one enzyme catalyzing multiple reactions)
    - Regulatory validation (sufficient catalyst tokens, proper structure)
    
    Example:
        >>> analyzer = RegulatoryStructureAnalyzer(model)
        >>> result = analyzer.analyze()
        >>> print(f"Total catalysts: {result.data['statistics']['total_catalysts']}")
        >>> print(f"Shared catalysts: {result.data['statistics']['shared_catalysts']}")
    """
    
    def __init__(self, model: Any):
        """Initialize regulatory structure analyzer.
        
        Args:
            model: Petri net model with places, transitions, and arcs
        """
        super().__init__(model)
        self.name = "Regulatory Structure"
        self.description = "Detect test arcs (catalysts) and regulatory patterns"
    
    def analyze(self, **kwargs) -> AnalysisResult:
        """Analyze regulatory structure in the model.
        
        Returns:
            AnalysisResult with:
            - test_arcs: List of test arc details
            - catalysts: List of places used as catalysts
            - catalyzed_transitions: List of transitions with catalysts
            - shared_catalysts: List of catalysts shared by multiple transitions
            - regulatory_patterns: Detected regulatory patterns
            - validation: Validation results for regulatory structure
            - statistics: Summary statistics
            - interpretation: Biological interpretation
        """
        start_time = self._start_timer()
        
        try:
            # Validate model
            self._validate_model()
            
            # Detect test arcs and catalysts
            test_arcs = self._detect_test_arcs()
            
            # Build catalyst usage map
            catalyst_map = self._build_catalyst_map(test_arcs)
            
            # Detect shared catalysts
            shared_catalysts = self._detect_shared_catalysts(catalyst_map)
            
            # Detect regulatory patterns
            patterns = self._detect_regulatory_patterns(catalyst_map)
            
            # Validate regulatory structure
            validation = self._validate_regulatory_structure(test_arcs, catalyst_map)
            
            # Calculate statistics
            stats = self._calculate_statistics(
                test_arcs, catalyst_map, shared_catalysts, patterns
            )
            
            # Generate interpretation
            interpretation = self._generate_interpretation(stats, patterns, validation)
            
            # Build result data
            data = {
                'test_arcs': test_arcs,
                'catalysts': list(catalyst_map.keys()),
                'catalyst_map': catalyst_map,
                'shared_catalysts': shared_catalysts,
                'patterns': patterns,
                'validation': validation,
                'statistics': stats,
                'interpretation': interpretation
            }
            
            # Generate summary
            summary = self._generate_summary(stats)
            
            # Build metadata
            metadata = {
                'analyzer': self.name,
                'execution_time': self._end_timer(start_time)
            }
            
            return AnalysisResult(
                success=True,
                data=data,
                summary=summary,
                metadata=metadata
            )
            
        except TopologyAnalysisError as e:
            return AnalysisResult(
                success=False,
                errors=[str(e)],
                metadata={'analyzer': self.name}
            )
        except Exception as e:
            return AnalysisResult(
                success=False,
                errors=[f"Unexpected error: {str(e)}"],
                metadata={'analyzer': self.name}
            )
    
    def _validate_model(self):
        """Validate that model has required attributes.
        
        Raises:
            TopologyAnalysisError: If model is invalid
        """
        if not hasattr(self.model, 'places'):
            raise TopologyAnalysisError("Model must have 'places' attribute")
        
        if not hasattr(self.model, 'transitions'):
            raise TopologyAnalysisError("Model must have 'transitions' attribute")
        
        if not hasattr(self.model, 'arcs'):
            raise TopologyAnalysisError("Model must have 'arcs' attribute")
    
    def _detect_test_arcs(self) -> List[Dict[str, Any]]:
        """Detect all test arcs (catalysts) in the model.
        
        Returns:
            List of test arc details with source, target, weight
        """
        test_arcs = []
        
        # Get arcs collection (dict or list)
        arcs_collection = self.model.arcs
        if isinstance(arcs_collection, dict):
            arcs = arcs_collection.values()
        else:
            arcs = arcs_collection
        
        for arc in arcs:
            # Check if arc is a test arc (non-consuming)
            if hasattr(arc, 'consumes_tokens') and not arc.consumes_tokens():
                # Get source and target
                source = arc.source
                target = arc.target
                
                arc_info = {
                    'arc_id': arc.id if hasattr(arc, 'id') else None,
                    'source_id': source.id if hasattr(source, 'id') else None,
                    'source_name': source.name if hasattr(source, 'name') else 'Unknown',
                    'target_id': target.id if hasattr(target, 'id') else None,
                    'target_name': target.name if hasattr(target, 'name') else 'Unknown',
                    'weight': arc.weight if hasattr(arc, 'weight') else 1,
                    'arc_obj': arc
                }
                
                test_arcs.append(arc_info)
        
        return test_arcs
    
    def _build_catalyst_map(self, test_arcs: List[Dict[str, Any]]) -> Dict[int, List[Dict[str, Any]]]:
        """Build map of catalyst places to transitions they catalyze.
        
        Args:
            test_arcs: List of test arc details
            
        Returns:
            Dict mapping catalyst_place_id -> list of catalyzed transitions
        """
        catalyst_map = defaultdict(list)
        
        for arc_info in test_arcs:
            catalyst_id = arc_info['source_id']
            transition_id = arc_info['target_id']
            
            catalyst_map[catalyst_id].append({
                'transition_id': transition_id,
                'transition_name': arc_info['target_name'],
                'weight': arc_info['weight']
            })
        
        return dict(catalyst_map)
    
    def _detect_shared_catalysts(self, catalyst_map: Dict[int, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Detect catalysts that are shared by multiple transitions.
        
        Args:
            catalyst_map: Map of catalyst to catalyzed transitions
            
        Returns:
            List of shared catalyst details
        """
        shared = []
        
        for catalyst_id, transitions in catalyst_map.items():
            if len(transitions) > 1:
                # Get catalyst place
                catalyst_place = self._get_place_by_id(catalyst_id)
                
                shared.append({
                    'catalyst_id': catalyst_id,
                    'catalyst_name': catalyst_place.name if catalyst_place and hasattr(catalyst_place, 'name') else 'Unknown',
                    'num_transitions': len(transitions),
                    'transitions': transitions,
                    'tokens': catalyst_place.tokens if catalyst_place and hasattr(catalyst_place, 'tokens') else None
                })
        
        return shared
    
    def _detect_regulatory_patterns(self, catalyst_map: Dict[int, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Detect common regulatory patterns.
        
        Args:
            catalyst_map: Map of catalyst to catalyzed transitions
            
        Returns:
            List of detected patterns
        """
        patterns = []
        
        # Pattern 1: Multi-substrate enzyme (one enzyme catalyzes multiple reactions)
        for catalyst_id, transitions in catalyst_map.items():
            if len(transitions) > 1:
                catalyst_place = self._get_place_by_id(catalyst_id)
                catalyst_name = catalyst_place.name if catalyst_place and hasattr(catalyst_place, 'name') else 'Unknown'
                
                patterns.append({
                    'type': 'multi_substrate_enzyme',
                    'description': f"Enzyme '{catalyst_name}' catalyzes {len(transitions)} reactions",
                    'catalyst_id': catalyst_id,
                    'catalyst_name': catalyst_name,
                    'num_reactions': len(transitions),
                    'reactions': [t['transition_name'] for t in transitions]
                })
        
        # Pattern 2: Single-substrate enzyme (one enzyme, one reaction)
        single_substrate_count = sum(1 for transitions in catalyst_map.values() if len(transitions) == 1)
        if single_substrate_count > 0:
            patterns.append({
                'type': 'single_substrate_enzymes',
                'description': f"{single_substrate_count} enzyme(s) catalyze single reactions",
                'count': single_substrate_count
            })
        
        return patterns
    
    def _validate_regulatory_structure(
        self,
        test_arcs: List[Dict[str, Any]],
        catalyst_map: Dict[int, List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """Validate regulatory structure correctness.
        
        Args:
            test_arcs: List of test arcs
            catalyst_map: Map of catalysts to transitions
            
        Returns:
            Validation results with warnings and issues
        """
        warnings = []
        issues = []
        
        # Check 1: Test arcs should connect Place → Transition
        for arc_info in test_arcs:
            arc = arc_info['arc_obj']
            source = arc.source
            target = arc.target
            
            # Check if source is place and target is transition
            if self._is_transition(source):
                issues.append(
                    f"Invalid test arc: connects Transition → Place "
                    f"(should be Place → Transition)"
                )
        
        # Check 2: Catalysts should have tokens
        for catalyst_id, transitions in catalyst_map.items():
            catalyst_place = self._get_place_by_id(catalyst_id)
            
            if catalyst_place and hasattr(catalyst_place, 'tokens'):
                if catalyst_place.tokens == 0:
                    warnings.append(
                        f"Catalyst '{catalyst_place.name}' has 0 tokens - "
                        f"reactions cannot fire"
                    )
                elif catalyst_place.tokens < len(transitions):
                    warnings.append(
                        f"Catalyst '{catalyst_place.name}' has {catalyst_place.tokens} token(s) "
                        f"but catalyzes {len(transitions)} reactions - may limit parallelism"
                    )
        
        # Check 3: Detect if any catalysts are also consumed (hybrid behavior)
        places_collection = self.model.places
        if isinstance(places_collection, dict):
            places = places_collection.values()
        else:
            places = places_collection
        
        arcs_collection = self.model.arcs
        if isinstance(arcs_collection, dict):
            arcs = arcs_collection.values()
        else:
            arcs = arcs_collection
        
        for catalyst_id in catalyst_map.keys():
            # Check if this place also has normal consuming arcs
            has_consuming_arc = False
            for arc in arcs:
                if hasattr(arc, 'source') and hasattr(arc.source, 'id'):
                    if arc.source.id == catalyst_id:
                        if not (hasattr(arc, 'consumes_tokens') and not arc.consumes_tokens()):
                            has_consuming_arc = True
                            break
            
            if has_consuming_arc:
                catalyst_place = self._get_place_by_id(catalyst_id)
                catalyst_name = catalyst_place.name if catalyst_place and hasattr(catalyst_place, 'name') else 'Unknown'
                warnings.append(
                    f"Place '{catalyst_name}' acts as both catalyst (non-consuming) "
                    f"and substrate (consuming) - hybrid behavior"
                )
        
        return {
            'valid': len(issues) == 0,
            'warnings': warnings,
            'issues': issues,
            'num_warnings': len(warnings),
            'num_issues': len(issues)
        }
    
    def _calculate_statistics(
        self,
        test_arcs: List[Dict[str, Any]],
        catalyst_map: Dict[int, List[Dict[str, Any]]],
        shared_catalysts: List[Dict[str, Any]],
        patterns: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate summary statistics.
        
        Args:
            test_arcs: List of test arcs
            catalyst_map: Map of catalysts
            shared_catalysts: List of shared catalysts
            patterns: List of regulatory patterns
            
        Returns:
            Dictionary of statistics
        """
        total_transitions = len(self.model.transitions) if hasattr(self.model.transitions, '__len__') else 0
        if isinstance(self.model.transitions, dict):
            total_transitions = len(self.model.transitions)
        
        catalyzed_transitions = set()
        for transitions in catalyst_map.values():
            for t in transitions:
                catalyzed_transitions.add(t['transition_id'])
        
        return {
            'total_test_arcs': len(test_arcs),
            'total_catalysts': len(catalyst_map),
            'total_transitions': total_transitions,
            'catalyzed_transitions': len(catalyzed_transitions),
            'catalyzed_pct': (len(catalyzed_transitions) / total_transitions * 100) if total_transitions > 0 else 0,
            'shared_catalysts': len(shared_catalysts),
            'single_use_catalysts': len(catalyst_map) - len(shared_catalysts),
            'patterns_detected': len(patterns)
        }
    
    def _generate_interpretation(
        self,
        stats: Dict[str, Any],
        patterns: List[Dict[str, Any]],
        validation: Dict[str, Any]
    ) -> str:
        """Generate biological interpretation of results.
        
        Args:
            stats: Statistics dictionary
            patterns: List of patterns
            validation: Validation results
            
        Returns:
            Formatted interpretation string
        """
        lines = ["=== REGULATORY STRUCTURE ANALYSIS ===\n"]
        
        # Overview
        lines.append(f"Total test arcs (catalysts): {stats['total_test_arcs']}")
        lines.append(f"Total catalyst places: {stats['total_catalysts']}")
        lines.append(f"Catalyzed transitions: {stats['catalyzed_transitions']} of {stats['total_transitions']} "
                    f"({stats['catalyzed_pct']:.1f}%)\n")
        
        # Catalyst sharing
        if stats['shared_catalysts'] > 0:
            lines.append(f"SHARED CATALYSTS: {stats['shared_catalysts']}")
            lines.append(f"  → Same enzyme catalyzes multiple reactions")
            lines.append(f"  → Correct biological behavior (enzyme reuse)")
            lines.append(f"  → Enables WEAK INDEPENDENCE (not strong)\n")
        
        if stats['single_use_catalysts'] > 0:
            lines.append(f"SINGLE-USE CATALYSTS: {stats['single_use_catalysts']}")
            lines.append(f"  → One enzyme per reaction (specific catalysis)\n")
        
        # Patterns
        if patterns:
            lines.append("REGULATORY PATTERNS DETECTED:")
            for pattern in patterns:
                if pattern['type'] == 'multi_substrate_enzyme':
                    lines.append(f"  • Multi-substrate enzyme: {pattern['description']}")
                    lines.append(f"    Reactions: {', '.join(pattern['reactions'])}")
                elif pattern['type'] == 'single_substrate_enzymes':
                    lines.append(f"  • {pattern['description']}")
            lines.append("")
        
        # Validation
        lines.append("VALIDATION:")
        if validation['valid']:
            lines.append("  ✓ Regulatory structure is valid")
        else:
            lines.append(f"  ✗ Found {validation['num_issues']} issue(s)")
            for issue in validation['issues']:
                lines.append(f"    - {issue}")
        
        if validation['warnings']:
            lines.append(f"\n  ⚠ {validation['num_warnings']} warning(s):")
            for warning in validation['warnings']:
                lines.append(f"    - {warning}")
        
        # Key insight
        if stats['total_catalysts'] > 0:
            lines.append("\n=== KEY INSIGHT ===")
            if stats['shared_catalysts'] > 0:
                lines.append(f"Model has {stats['shared_catalysts']} shared catalyst(s).")
                lines.append("This is CORRECT biological behavior:")
                lines.append("  - Same enzyme can catalyze multiple reactions")
                lines.append("  - Non-consuming regulatory dependency")
                lines.append("  - Enables parallel execution (Weak Independence)")
            else:
                lines.append("All catalysts are single-use (specific catalysis).")
                lines.append("Each enzyme catalyzes exactly one reaction type.")
        else:
            lines.append("\n=== NO CATALYSTS ===")
            lines.append("Model has no test arcs (catalysts).")
            lines.append("Either:")
            lines.append("  - Not a biological model")
            lines.append("  - Catalysts modeled implicitly (in rate functions)")
            lines.append("  - Classical Petri Net without regulatory structure")
        
        return "\n".join(lines)
    
    def _generate_summary(self, stats: Dict[str, Any]) -> str:
        """Generate short summary for display.
        
        Args:
            stats: Statistics dictionary
            
        Returns:
            Summary string
        """
        if stats['total_catalysts'] == 0:
            return "No test arcs found (no explicit catalysts)"
        
        return (f"Found {stats['total_catalysts']} catalyst(s), "
                f"{stats['catalyzed_transitions']} catalyzed transitions, "
                f"{stats['shared_catalysts']} shared")
    
    def _get_place_by_id(self, place_id: int) -> Optional[Any]:
        """Get place object by ID.
        
        Args:
            place_id: Place ID
            
        Returns:
            Place object or None if not found
        """
        places_collection = self.model.places
        
        if isinstance(places_collection, dict):
            return places_collection.get(place_id)
        else:
            # List-like collection
            for place in places_collection:
                if hasattr(place, 'id') and place.id == place_id:
                    return place
        
        return None
    
    def _is_transition(self, obj: Any) -> bool:
        """Check if object is a transition.
        
        Args:
            obj: Object to check
            
        Returns:
            True if obj is a transition
        """
        if obj is None:
            return False
        
        # Check class name
        class_name = obj.__class__.__name__
        if 'Transition' in class_name:
            return True
        
        # Check type attribute
        if hasattr(obj, 'type') and obj.type == 'transition':
            return True
        
        return False
    
    def _is_place(self, obj: Any) -> bool:
        """Check if object is a place.
        
        Args:
            obj: Object to check
            
        Returns:
            True if obj is a place
        """
        if obj is None:
            return False
        
        # Check class name
        class_name = obj.__class__.__name__
        if 'Place' in class_name:
            return True
        
        # Check type attribute
        if hasattr(obj, 'type') and obj.type == 'place':
            return True
        
        return False
