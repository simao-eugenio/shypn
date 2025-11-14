"""Level 2: Dependency analyzer - analyze inter-locality flow dependencies."""
from typing import List, Dict, Any, Set
from .base_analyzer import BaseAnalyzer
from ..investigation import Issue, Suggestion, Subnet, Dependency


class DependencyAnalyzer(BaseAnalyzer):
    """Analyze dependencies between localities in a subnet.
    
    Level 2 analysis focuses on how localities interact through shared places
    and how issues in one locality cascade to others.
    """
    
    def analyze(self, context: Dict[str, Any]) -> List[Issue]:
        """Perform dependency analysis.
        
        Args:
            context: Must contain:
                - 'subnet': Subnet object with dependencies
                - 'localities': List of Locality objects
                - 'kb': Knowledge base
                - 'sim_data': Optional simulation data dict (transition_id → data)
                
        Returns:
            List of Issue objects
        """
        self.clear()
        
        subnet = context.get('subnet')
        localities = context.get('localities')
        kb = context.get('kb')
        sim_data = context.get('sim_data', {})
        
        if not subnet or not localities or not kb:
            return []
        
        # Analyze dependency graph
        self.issues.extend(self._analyze_flow_balance(subnet, localities, kb, sim_data))
        self.issues.extend(self._analyze_bottlenecks(subnet, localities, kb, sim_data))
        self.issues.extend(self._analyze_cascading_issues(subnet, localities, kb))
        
        return self.issues
    
    def generate_suggestions(self, issues: List[Issue], context: Dict[str, Any]) -> List[Suggestion]:
        """Generate suggestions to fix dependency issues.
        
        Args:
            issues: List of issues to address
            context: Analysis context
            
        Returns:
            List of Suggestion objects
        """
        self.suggestions.clear()
        
        for issue in issues:
            if 'flow_mismatch' in issue.details:
                self.suggestions.extend(self._suggest_flow_fix(issue, context))
            elif 'bottleneck' in issue.details:
                self.suggestions.extend(self._suggest_bottleneck_fix(issue, context))
            elif 'cascade' in issue.details:
                self.suggestions.extend(self._suggest_cascade_fix(issue, context))
        
        return self.suggestions
    
    def _analyze_flow_balance(
        self, 
        subnet: Subnet, 
        localities: List[Any], 
        kb: Any, 
        sim_data: Dict
    ) -> List[Issue]:
        """Analyze flow balance through dependencies.
        
        Checks if production rate of source transition matches
        consumption rate of target transition.
        
        Args:
            subnet: Subnet object
            localities: List of localities
            kb: Knowledge base
            sim_data: Simulation data per transition
            
        Returns:
            List of flow balance issues
        """
        issues = []
        
        for dep in subnet.dependencies:
            source_data = sim_data.get(dep.source_transition_id, {})
            target_data = sim_data.get(dep.target_transition_id, {})
            
            source_rate = source_data.get('firing_count', 0) / source_data.get('duration', 60.0) if source_data else 0
            target_rate = target_data.get('firing_count', 0) / target_data.get('duration', 60.0) if target_data else 0
            
            # Check if rates are significantly different
            if source_rate > 0 and target_rate > 0:
                ratio = source_rate / target_rate if target_rate > 0 else float('inf')
                
                if ratio > 2.0:
                    place_name = self._get_human_readable_name(kb, dep.connecting_place_id, "place")
                    source_name = self._get_human_readable_name(kb, dep.source_transition_id, "transition")
                    target_name = self._get_human_readable_name(kb, dep.target_transition_id, "transition")
                    
                    issues.append(Issue(
                        category='dependency',
                        severity='warning',
                        message=f"Flow imbalance: {source_name} produces {place_name} faster than {target_name} consumes it",
                        element_id=dep.connecting_place_id,
                        details={
                            'flow_mismatch': True,
                            'source': dep.source_transition_id,
                            'target': dep.target_transition_id,
                            'place': dep.connecting_place_id,
                            'source_rate': source_rate,
                            'target_rate': target_rate,
                            'ratio': ratio
                        }
                    ))
                elif ratio < 0.5:
                    place_name = self._get_human_readable_name(kb, dep.connecting_place_id, "place")
                    source_name = self._get_human_readable_name(kb, dep.source_transition_id, "transition")
                    target_name = self._get_human_readable_name(kb, dep.target_transition_id, "transition")
                    
                    issues.append(Issue(
                        category='dependency',
                        severity='warning',
                        message=f"Flow imbalance: {target_name} consumes {place_name} faster than {source_name} produces it",
                        element_id=dep.connecting_place_id,
                        details={
                            'flow_mismatch': True,
                            'source': dep.source_transition_id,
                            'target': dep.target_transition_id,
                            'place': dep.connecting_place_id,
                            'source_rate': source_rate,
                            'target_rate': target_rate,
                            'ratio': ratio
                        }
                    ))
        
        return issues
    
    def _analyze_bottlenecks(
        self, 
        subnet: Subnet, 
        localities: List[Any], 
        kb: Any, 
        sim_data: Dict
    ) -> List[Issue]:
        """Identify bottleneck transitions in subnet.
        
        A bottleneck is a transition that limits flow through the subnet.
        
        Args:
            subnet: Subnet object
            localities: List of localities
            kb: Knowledge base
            sim_data: Simulation data per transition
            
        Returns:
            List of bottleneck issues
        """
        issues = []
        
        # Calculate firing rates
        rates = {}
        for trans_obj in subnet.transitions:
            trans_id = trans_obj.id  # Extract ID from object
            data = sim_data.get(trans_id, {})
            rate = data.get('firing_count', 0) / data.get('duration', 60.0) if data else 0
            rates[trans_id] = rate
        
        if not rates:
            return issues
        
        # Find transitions with significantly lower rates
        avg_rate = sum(rates.values()) / len(rates) if rates else 0
        
        for trans_id, rate in rates.items():
            if rate < avg_rate * 0.3 and rate < 1.0:  # Less than 30% of average and < 1 firing/s
                trans_name = self._get_human_readable_name(kb, trans_id, "transition")
                
                issues.append(Issue(
                    category='dependency',
                    severity='error',
                    message=f"{trans_name} is a bottleneck (rate: {rate:.3f}/s, avg: {avg_rate:.3f}/s)",
                    element_id=trans_id,
                    details={
                        'bottleneck': True,
                        'rate': rate,
                        'avg_rate': avg_rate,
                        'ratio': rate / avg_rate if avg_rate > 0 else 0
                    }
                ))
        
        return issues
    
    def _analyze_cascading_issues(
        self, 
        subnet: Subnet, 
        localities: List[Any], 
        kb: Any
    ) -> List[Issue]:
        """Detect issues that cascade through dependencies.
        
        E.g., if transition A has no rate and feeds transition B,
        then B will also have problems.
        
        Args:
            subnet: Subnet object
            localities: List of localities
            kb: Knowledge base
            
        Returns:
            List of cascading issues
        """
        issues = []
        
        # Build map of transition → locality
        trans_to_loc = {loc.transition.id: loc for loc in localities}
        
        # Check each dependency for potential cascades
        for dep in subnet.dependencies:
            source_loc = trans_to_loc.get(dep.source_transition_id)
            target_loc = trans_to_loc.get(dep.target_transition_id)
            
            if not source_loc or not target_loc:
                continue
            
            source_trans = source_loc.transition
            target_trans = target_loc.transition
            
            # Check if source has no rate → will affect target
            if hasattr(source_trans, 'rate') and (source_trans.rate is None or source_trans.rate == 0):
                place_name = self._get_human_readable_name(kb, dep.connecting_place_id, "place")
                source_name = self._get_human_readable_name(kb, dep.source_transition_id, "transition")
                target_name = self._get_human_readable_name(kb, dep.target_transition_id, "transition")
                
                issues.append(Issue(
                    category='dependency',
                    severity='warning',
                    message=f"Cascading issue: {source_name} has no rate, will starve {target_name}",
                    element_id=dep.source_transition_id,
                    details={
                        'cascade': True,
                        'source': dep.source_transition_id,
                        'target': dep.target_transition_id,
                        'place': dep.connecting_place_id,
                        'issue_type': 'no_rate'
                    }
                ))
        
        return issues
    
    def _suggest_flow_fix(self, issue: Issue, context: Dict[str, Any]) -> List[Suggestion]:
        """Suggest fixes for flow imbalances."""
        suggestions = []
        
        source_id = issue.details.get('source')
        target_id = issue.details.get('target')
        ratio = issue.details.get('ratio', 1.0)
        
        if ratio > 2.0:
            # Source too fast
            suggestions.append(Suggestion(
                category='dependency',
                action='adjust_rate',
                message=f"Slow down {source_id} or speed up {target_id} to balance flow",
                parameters={
                    'source_transition': source_id,
                    'target_transition': target_id,
                    'suggested_action': 'reduce_source_rate' if ratio > 5.0 else 'increase_target_rate'
                },
                impact=f"Will balance production/consumption through {issue.details.get('place')}"
            ))
        elif ratio < 0.5:
            # Target too fast (source too slow)
            suggestions.append(Suggestion(
                category='dependency',
                action='adjust_rate',
                message=f"Speed up {source_id} or slow down {target_id} to balance flow",
                parameters={
                    'source_transition': source_id,
                    'target_transition': target_id,
                    'suggested_action': 'increase_source_rate' if ratio < 0.2 else 'reduce_target_rate'
                },
                impact=f"Will prevent starvation of {target_id}"
            ))
        
        return suggestions
    
    def _suggest_bottleneck_fix(self, issue: Issue, context: Dict[str, Any]) -> List[Suggestion]:
        """Suggest fixes for bottlenecks."""
        suggestions = []
        
        trans_id = issue.element_id
        rate = issue.details.get('rate', 0)
        avg_rate = issue.details.get('avg_rate', 1.0)
        
        suggestions.append(Suggestion(
            category='dependency',
            action='increase_rate',
            message=f"Increase rate of {trans_id} from {rate:.3f} to ~{avg_rate:.3f} to remove bottleneck",
            parameters={
                'transition_id': trans_id,
                'current_rate': rate,
                'suggested_rate': avg_rate
            },
            impact="Will improve overall subnet throughput"
        ))
        
        suggestions.append(Suggestion(
            category='dependency',
            action='investigate_enablement',
            message=f"Check if {trans_id} has sufficient input tokens",
            parameters={'transition_id': trans_id}
        ))
        
        return suggestions
    
    def _suggest_cascade_fix(self, issue: Issue, context: Dict[str, Any]) -> List[Suggestion]:
        """Suggest fixes for cascading issues."""
        suggestions = []
        
        source_id = issue.details.get('source')
        target_id = issue.details.get('target')
        
        if issue.details.get('issue_type') == 'no_rate':
            suggestions.append(Suggestion(
                category='dependency',
                action='set_rate',
                message=f"Set firing rate for {source_id} to enable {target_id}",
                parameters={
                    'transition_id': source_id,
                    'affected_transitions': [target_id]
                },
                impact=f"Fixing {source_id} will also fix {target_id}",
                dependencies=[]  # Should be fixed first
            ))
        
        return suggestions
