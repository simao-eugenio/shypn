"""Level 1: Locality analyzer - analyze single locality issues."""
from typing import List, Dict, Any, Optional
from .base_analyzer import BaseAnalyzer
from ..investigation import Issue, Suggestion


class LocalityAnalyzer(BaseAnalyzer):
    """Analyze single locality for structural, biological, and kinetic issues.
    
    Level 1 analysis focuses on a single transition and its immediate
    input/output places and arcs.
    """
    
    def analyze(self, context: Dict[str, Any]) -> List[Issue]:
        """Perform locality analysis.
        
        Args:
            context: Must contain:
                - 'transition': Transition object
                - 'locality': Locality object
                - 'kb': Knowledge base
                - 'sim_data': Optional simulation data
                
        Returns:
            List of Issue objects
        """
        self.clear()
        
        transition = context.get('transition')
        locality = context.get('locality')
        kb = context.get('kb')
        sim_data = context.get('sim_data')
        
        if not transition or not locality or not kb:
            return []
        
        # Analyze different aspects
        self.issues.extend(self._analyze_structural(transition, locality, kb))
        self.issues.extend(self._analyze_biological(transition, locality, kb))
        
        if sim_data:
            self.issues.extend(self._analyze_kinetic(transition, locality, kb, sim_data))
        
        return self.issues
    
    def generate_suggestions(self, issues: List[Issue], context: Dict[str, Any]) -> List[Suggestion]:
        """Generate suggestions to fix locality issues.
        
        Args:
            issues: List of issues to address
            context: Analysis context
            
        Returns:
            List of Suggestion objects
        """
        self.suggestions.clear()
        
        for issue in issues:
            if issue.category == 'structural':
                self.suggestions.extend(self._suggest_structural_fix(issue, context))
            elif issue.category == 'biological':
                self.suggestions.extend(self._suggest_biological_fix(issue, context))
            elif issue.category == 'kinetic':
                self.suggestions.extend(self._suggest_kinetic_fix(issue, context))
        
        return self.suggestions
    
    def _analyze_structural(self, transition: Any, locality: Any, kb: Any) -> List[Issue]:
        """Analyze structural issues (topology).
        
        Checks:
        - Missing input/output arcs
        - Deadlock potential (no inputs/outputs)
        - Arc weight consistency
        
        Args:
            transition: Transition object
            locality: Locality object
            kb: Knowledge base
            
        Returns:
            List of structural issues
        """
        issues = []
        trans_name = self._get_human_readable_name(kb, transition.transition_id, "transition")
        
        # Check if transition has no inputs (source transition)
        if not locality.input_places:
            issues.append(Issue(
                category='structural',
                severity='warning',
                message=f"{trans_name} has no input places (source transition)",
                element_id=transition.transition_id,
                details={'is_source': True}
            ))
        
        # Check if transition has no outputs (sink transition)
        if not locality.output_places:
            issues.append(Issue(
                category='structural',
                severity='warning',
                message=f"{trans_name} has no output places (sink transition)",
                element_id=transition.transition_id,
                details={'is_sink': True}
            ))
        
        # Check for unbalanced arc weights (basic check)
        input_weight_sum = 0
        output_weight_sum = 0
        
        for arc_id in locality.input_arcs:
            arc = kb.arcs.get(arc_id)
            if arc and hasattr(arc, 'current_weight'):
                input_weight_sum += arc.current_weight
        
        for arc_id in locality.output_arcs:
            arc = kb.arcs.get(arc_id)
            if arc and hasattr(arc, 'current_weight'):
                output_weight_sum += arc.current_weight
        
        if input_weight_sum > 0 and output_weight_sum > 0 and input_weight_sum != output_weight_sum:
            issues.append(Issue(
                category='structural',
                severity='info',
                message=f"{trans_name} has unbalanced arc weights (in:{input_weight_sum}, out:{output_weight_sum})",
                element_id=transition.transition_id,
                details={'input_sum': input_weight_sum, 'output_sum': output_weight_sum}
            ))
        
        return issues
    
    def _analyze_biological(self, transition: Any, locality: Any, kb: Any) -> List[Issue]:
        """Analyze biological issues (semantics).
        
        Checks:
        - Missing compound mappings
        - Stoichiometry vs KEGG reaction
        - Conservation violations
        
        Args:
            transition: Transition object
            locality: Locality object
            kb: Knowledge base
            
        Returns:
            List of biological issues
        """
        issues = []
        trans_name = self._get_human_readable_name(kb, transition.transition_id, "transition")
        
        # Check for unmapped compounds
        unmapped_places = []
        for place_obj in locality.input_places + locality.output_places:
            # Place is already an object (not an ID)
            if not hasattr(place_obj, 'compound_id') or not place_obj.compound_id:
                place_name = self._get_human_readable_name(kb, place_obj.id, "place")
                unmapped_places.append(place_name)
        
        if unmapped_places:
            issues.append(Issue(
                category='biological',
                severity='warning',
                message=f"{trans_name} has {len(unmapped_places)} unmapped places: {', '.join(unmapped_places[:3])}",
                element_id=transition.transition_id,
                details={'unmapped_places': unmapped_places}
            ))
        
        # Check if transition has reaction metadata
        if not hasattr(transition, 'reaction_id') or not transition.reaction_id:
            issues.append(Issue(
                category='biological',
                severity='info',
                message=f"{trans_name} not mapped to KEGG reaction",
                element_id=transition.transition_id,
                details={'needs_reaction_mapping': True}
            ))
        
        return issues
    
    def _analyze_kinetic(self, transition: Any, locality: Any, kb: Any, sim_data: Dict) -> List[Issue]:
        """Analyze kinetic issues (rates, simulation behavior).
        
        Checks:
        - Transition never fired
        - Very low firing rate
        - No kinetic parameters
        
        Args:
            transition: Transition object
            locality: Locality object
            kb: Knowledge base
            sim_data: Simulation data
            
        Returns:
            List of kinetic issues
        """
        issues = []
        trans_name = self._get_human_readable_name(kb, transition.transition_id, "transition")
        
        # Check firing count from simulation
        firing_count = sim_data.get('firing_count', 0)
        duration = sim_data.get('duration', 60.0)
        
        if firing_count == 0:
            issues.append(Issue(
                category='kinetic',
                severity='error',
                message=f"{trans_name} never fired during simulation",
                element_id=transition.transition_id,
                details={'firing_count': 0, 'duration': duration}
            ))
        elif firing_count / duration < 0.1:
            issues.append(Issue(
                category='kinetic',
                severity='warning',
                message=f"{trans_name} has very low firing rate ({firing_count / duration:.3f} firings/s)",
                element_id=transition.transition_id,
                details={'firing_count': firing_count, 'rate': firing_count / duration}
            ))
        
        # Check if transition has rate parameter
        if not hasattr(transition, 'rate') or transition.rate is None or transition.rate == 0:
            issues.append(Issue(
                category='kinetic',
                severity='warning',
                message=f"{trans_name} has no firing rate set",
                element_id=transition.transition_id,
                details={'needs_rate': True}
            ))
        
        return issues
    
    def _suggest_structural_fix(self, issue: Issue, context: Dict[str, Any]) -> List[Suggestion]:
        """Suggest structural fixes."""
        suggestions = []
        
        if issue.details.get('is_source'):
            suggestions.append(Suggestion(
                category='structural',
                action='review',
                message=f"Review if {issue.element_id} should be a source transition",
                parameters={'transition_id': issue.element_id}
            ))
        
        if issue.details.get('is_sink'):
            suggestions.append(Suggestion(
                category='structural',
                action='review',
                message=f"Review if {issue.element_id} should be a sink transition",
                parameters={'transition_id': issue.element_id}
            ))
        
        if 'input_sum' in issue.details and 'output_sum' in issue.details:
            suggestions.append(Suggestion(
                category='structural',
                action='balance_weights',
                message=f"Consider balancing arc weights for {issue.element_id}",
                parameters={
                    'transition_id': issue.element_id,
                    'current_in': issue.details['input_sum'],
                    'current_out': issue.details['output_sum']
                }
            ))
        
        return suggestions
    
    def _suggest_biological_fix(self, issue: Issue, context: Dict[str, Any]) -> List[Suggestion]:
        """Suggest biological fixes."""
        suggestions = []
        
        if issue.details.get('unmapped_places'):
            suggestions.append(Suggestion(
                category='biological',
                action='map_compounds',
                message=f"Map compounds for unmapped places in {issue.element_id}",
                parameters={
                    'transition_id': issue.element_id,
                    'unmapped_places': issue.details['unmapped_places']
                }
            ))
        
        if issue.details.get('needs_reaction_mapping'):
            suggestions.append(Suggestion(
                category='biological',
                action='map_reaction',
                message=f"Map {issue.element_id} to KEGG reaction",
                parameters={'transition_id': issue.element_id}
            ))
        
        return suggestions
    
    def _suggest_kinetic_fix(self, issue: Issue, context: Dict[str, Any]) -> List[Suggestion]:
        """Suggest kinetic fixes."""
        suggestions = []
        
        if issue.details.get('firing_count') == 0:
            suggestions.append(Suggestion(
                category='kinetic',
                action='investigate_enablement',
                message=f"Investigate why {issue.element_id} never fires (check input tokens)",
                parameters={'transition_id': issue.element_id}
            ))
        
        if issue.details.get('needs_rate'):
            suggestions.append(Suggestion(
                category='kinetic',
                action='query_brenda',
                message=f"Query BRENDA for kinetic parameters for {issue.element_id}",
                parameters={'transition_id': issue.element_id}
            ))
        
        if 'rate' in issue.details:
            suggestions.append(Suggestion(
                category='kinetic',
                action='adjust_rate',
                message=f"Consider increasing firing rate for {issue.element_id}",
                parameters={
                    'transition_id': issue.element_id,
                    'current_rate': issue.details.get('rate', 0)
                }
            ))
        
        return suggestions
