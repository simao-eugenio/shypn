"""Level 3: Boundary analyzer - analyze subnet boundary flow."""
from typing import List, Dict, Any
from .base_analyzer import BaseAnalyzer
from ..investigation import Issue, Suggestion, Subnet, BoundaryAnalysis


class BoundaryAnalyzer(BaseAnalyzer):
    """Analyze subnet boundary inputs/outputs.
    
    Level 3 analysis focuses on places at the subnet boundary and
    checks for accumulation, depletion, and balance issues.
    """
    
    def analyze(self, context: Dict[str, Any]) -> List[Issue]:
        """Perform boundary analysis.
        
        Args:
            context: Must contain:
                - 'subnet': Subnet object
                - 'kb': Knowledge base
                - 'sim_data': Optional simulation data with place token histories
                
        Returns:
            List of Issue objects
        """
        self.clear()
        
        subnet = context.get('subnet')
        kb = context.get('kb')
        sim_data = context.get('sim_data', {})
        
        if not subnet or not kb:
            return []
        
        # Analyze boundary places
        self.issues.extend(self._analyze_accumulation(subnet, kb, sim_data))
        self.issues.extend(self._analyze_depletion(subnet, kb, sim_data))
        self.issues.extend(self._analyze_balance(subnet, kb, sim_data))
        
        return self.issues
    
    def generate_suggestions(self, issues: List[Issue], context: Dict[str, Any]) -> List[Suggestion]:
        """Generate suggestions to fix boundary issues.
        
        Args:
            issues: List of issues to address
            context: Analysis context
            
        Returns:
            List of Suggestion objects
        """
        self.suggestions.clear()
        
        for issue in issues:
            if 'accumulating' in issue.details:
                self.suggestions.extend(self._suggest_accumulation_fix(issue, context))
            elif 'depleting' in issue.details:
                self.suggestions.extend(self._suggest_depletion_fix(issue, context))
            elif 'unbalanced' in issue.details:
                self.suggestions.extend(self._suggest_balance_fix(issue, context))
        
        return self.suggestions
    
    def _analyze_accumulation(self, subnet: Subnet, kb: Any, sim_data: Dict) -> List[Issue]:
        """Detect boundary places that accumulate tokens.
        
        Accumulation happens when more tokens flow in than out.
        
        Args:
            subnet: Subnet object
            kb: Knowledge base
            sim_data: Simulation data with place histories
            
        Returns:
            List of accumulation issues
        """
        issues = []
        
        # Skip if no simulation data
        if not sim_data:
            return issues
        
        place_data = sim_data.get('places', {})
        
        for place_id in subnet.boundary_places:
            history = place_data.get(place_id, {})
            tokens_over_time = history.get('tokens', [])
            
            if len(tokens_over_time) < 2:
                continue
            
            initial = tokens_over_time[0]
            final = tokens_over_time[-1]
            
            # Check if tokens increased significantly
            if final > initial * 2 and final > 10:  # Doubled and > 10 tokens
                place_name = self._get_human_readable_name(kb, place_id, "place")
                
                issues.append(Issue(
                    category='boundary',
                    severity='warning',
                    message=f"{place_name} accumulates tokens ({initial:.1f} → {final:.1f})",
                    element_id=place_id,
                    details={
                        'accumulating': True,
                        'initial': initial,
                        'final': final,
                        'increase': final - initial
                    }
                ))
        
        return issues
    
    def _analyze_depletion(self, subnet: Subnet, kb: Any, sim_data: Dict) -> List[Issue]:
        """Detect boundary places that deplete tokens.
        
        Depletion happens when more tokens flow out than in.
        
        Args:
            subnet: Subnet object
            kb: Knowledge base
            sim_data: Simulation data with place histories
            
        Returns:
            List of depletion issues
        """
        issues = []
        
        # Skip if no simulation data
        if not sim_data:
            return issues
        
        place_data = sim_data.get('places', {})
        
        for place_id in subnet.boundary_places:
            history = place_data.get(place_id, {})
            tokens_over_time = history.get('tokens', [])
            
            if len(tokens_over_time) < 2:
                continue
            
            initial = tokens_over_time[0]
            final = tokens_over_time[-1]
            
            # Check if tokens decreased significantly
            if initial > 0 and final < initial * 0.5:  # More than 50% decrease
                place_name = self._get_human_readable_name(kb, place_id, "place")
                
                issues.append(Issue(
                    category='boundary',
                    severity='error' if final < 1.0 else 'warning',
                    message=f"{place_name} depletes tokens ({initial:.1f} → {final:.1f})",
                    element_id=place_id,
                    details={
                        'depleting': True,
                        'initial': initial,
                        'final': final,
                        'decrease': initial - final,
                        'near_empty': final < 1.0
                    }
                ))
        
        return issues
    
    def _analyze_balance(self, subnet: Subnet, kb: Any, sim_data: Dict) -> List[Issue]:
        """Analyze overall subnet boundary balance.
        
        Checks if total flow in approximately equals total flow out.
        
        Args:
            subnet: Subnet object
            kb: Knowledge base
            sim_data: Simulation data
            
        Returns:
            List of balance issues
        """
        issues = []
        
        place_data = sim_data.get('places', {})
        
        # Calculate net change for all boundary places
        total_increase = 0
        total_decrease = 0
        
        for place_id in subnet.boundary_places:
            history = place_data.get(place_id, {})
            tokens_over_time = history.get('tokens', [])
            
            if len(tokens_over_time) < 2:
                continue
            
            initial = tokens_over_time[0]
            final = tokens_over_time[-1]
            change = final - initial
            
            if change > 0:
                total_increase += change
            else:
                total_decrease += abs(change)
        
        # Check if significantly unbalanced
        if total_increase > 0 and total_decrease > 0:
            ratio = total_increase / total_decrease if total_decrease > 0 else float('inf')
            
            if ratio > 3.0:
                issues.append(Issue(
                    category='boundary',
                    severity='warning',
                    message=f"Subnet boundary unbalanced: more input than output ({total_increase:.1f} vs {total_decrease:.1f})",
                    element_id=None,
                    details={
                        'unbalanced': True,
                        'total_increase': total_increase,
                        'total_decrease': total_decrease,
                        'ratio': ratio,
                        'type': 'accumulating_subnet'
                    }
                ))
            elif ratio < 0.33:
                issues.append(Issue(
                    category='boundary',
                    severity='warning',
                    message=f"Subnet boundary unbalanced: more output than input ({total_increase:.1f} vs {total_decrease:.1f})",
                    element_id=None,
                    details={
                        'unbalanced': True,
                        'total_increase': total_increase,
                        'total_decrease': total_decrease,
                        'ratio': ratio,
                        'type': 'depleting_subnet'
                    }
                ))
        
        return issues
    
    def create_boundary_analysis(self, subnet: Subnet, kb: Any, sim_data: Dict) -> BoundaryAnalysis:
        """Create BoundaryAnalysis summary object.
        
        Args:
            subnet: Subnet object
            kb: Knowledge base
            sim_data: Simulation data
            
        Returns:
            BoundaryAnalysis object
        """
        analysis = BoundaryAnalysis()
        place_data = sim_data.get('places', {})
        
        for place_id in subnet.boundary_places:
            history = place_data.get(place_id, {})
            tokens_over_time = history.get('tokens', [])
            
            if len(tokens_over_time) < 2:
                continue
            
            initial = tokens_over_time[0]
            final = tokens_over_time[-1]
            change = final - initial
            
            if abs(change) < initial * 0.1:  # Less than 10% change
                analysis.balanced_places.append(place_id)
            elif change > 0:
                analysis.accumulating_places.append(place_id)
            else:
                analysis.depleting_places.append(place_id)
        
        return analysis
    
    def _suggest_accumulation_fix(self, issue: Issue, context: Dict[str, Any]) -> List[Suggestion]:
        """Suggest fixes for accumulating places."""
        suggestions = []
        
        place_id = issue.element_id
        final = issue.details.get('final', 0)
        
        suggestions.append(Suggestion(
            category='boundary',
            action='add_sink',
            message=f"Consider adding sink transition to consume {place_id}",
            parameters={
                'place_id': place_id,
                'accumulated_tokens': final
            },
            impact="Will prevent unbounded accumulation"
        ))
        
        suggestions.append(Suggestion(
            category='boundary',
            action='review',
            message=f"Review if {place_id} accumulation is intentional (storage)",
            parameters={'place_id': place_id}
        ))
        
        return suggestions
    
    def _suggest_depletion_fix(self, issue: Issue, context: Dict[str, Any]) -> List[Suggestion]:
        """Suggest fixes for depleting places."""
        suggestions = []
        
        place_id = issue.element_id
        near_empty = issue.details.get('near_empty', False)
        
        if near_empty:
            suggestions.append(Suggestion(
                category='boundary',
                action='add_source',
                message=f"Add source transition to replenish {place_id}",
                parameters={
                    'place_id': place_id,
                    'urgency': 'high'
                },
                impact="Critical: prevents subnet starvation"
            ))
        else:
            suggestions.append(Suggestion(
                category='boundary',
                action='increase_input',
                message=f"Increase input rate for {place_id}",
                parameters={'place_id': place_id},
                impact="Will prevent eventual depletion"
            ))
        
        return suggestions
    
    def _suggest_balance_fix(self, issue: Issue, context: Dict[str, Any]) -> List[Suggestion]:
        """Suggest fixes for boundary balance issues."""
        suggestions = []
        
        balance_type = issue.details.get('type')
        
        if balance_type == 'accumulating_subnet':
            suggestions.append(Suggestion(
                category='boundary',
                action='balance_flow',
                message="Subnet accumulates material: increase output or decrease input",
                parameters={
                    'total_increase': issue.details.get('total_increase'),
                    'total_decrease': issue.details.get('total_decrease')
                },
                impact="Will balance subnet material flow"
            ))
        elif balance_type == 'depleting_subnet':
            suggestions.append(Suggestion(
                category='boundary',
                action='balance_flow',
                message="Subnet depletes material: increase input or decrease output",
                parameters={
                    'total_increase': issue.details.get('total_increase'),
                    'total_decrease': issue.details.get('total_decrease')
                },
                impact="Will maintain subnet material balance"
            ))
        
        return suggestions
