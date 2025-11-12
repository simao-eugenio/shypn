"""Level 4: Conservation analyzer - analyze subnet conservation laws."""
from typing import List, Dict, Any, Set
from .base_analyzer import BaseAnalyzer
from ..investigation import Issue, Suggestion, Subnet, ConservationAnalysis


class ConservationAnalyzer(BaseAnalyzer):
    """Analyze conservation properties within subnet.
    
    Level 4 analysis checks P-invariants, mass balance, and
    conservation laws within the subnet.
    """
    
    def analyze(self, context: Dict[str, Any]) -> List[Issue]:
        """Perform conservation analysis.
        
        Args:
            context: Must contain:
                - 'subnet': Subnet object
                - 'kb': Knowledge base with p_invariants
                - 'sim_data': Optional simulation data
                
        Returns:
            List of Issue objects
        """
        self.clear()
        
        subnet = context.get('subnet')
        kb = context.get('kb')
        sim_data = context.get('sim_data', {})
        
        if not subnet or not kb:
            return []
        
        # Analyze different conservation aspects
        self.issues.extend(self._analyze_p_invariants(subnet, kb, sim_data))
        self.issues.extend(self._analyze_mass_balance(subnet, kb))
        self.issues.extend(self._analyze_conservation_leaks(subnet, kb, sim_data))
        
        return self.issues
    
    def generate_suggestions(self, issues: List[Issue], context: Dict[str, Any]) -> List[Suggestion]:
        """Generate suggestions to fix conservation issues.
        
        Args:
            issues: List of issues to address
            context: Analysis context
            
        Returns:
            List of Suggestion objects
        """
        self.suggestions.clear()
        
        for issue in issues:
            if 'invariant_violation' in issue.details:
                self.suggestions.extend(self._suggest_invariant_fix(issue, context))
            elif 'mass_imbalance' in issue.details:
                self.suggestions.extend(self._suggest_mass_fix(issue, context))
            elif 'leak' in issue.details:
                self.suggestions.extend(self._suggest_leak_fix(issue, context))
        
        return self.suggestions
    
    def _analyze_p_invariants(self, subnet: Subnet, kb: Any, sim_data: Dict) -> List[Issue]:
        """Check P-invariants within subnet.
        
        P-invariants represent conservation laws. Check if they hold
        during simulation.
        
        Args:
            subnet: Subnet object
            kb: Knowledge base with p_invariants
            sim_data: Simulation data
            
        Returns:
            List of P-invariant violation issues
        """
        issues = []
        
        if not hasattr(kb, 'p_invariants') or not kb.p_invariants:
            return issues
        
        place_data = sim_data.get('places', {})
        
        # Check each P-invariant
        for invariant in kb.p_invariants:
            # Get places involved in this invariant
            inv_places = set(invariant.get('places', []))
            
            # Only check invariants that involve subnet places
            subnet_inv_places = inv_places & subnet.places
            if not subnet_inv_places:
                continue
            
            # Check if invariant is conserved over time
            violated = False
            invariant_name = invariant.get('name', 'Unknown')
            
            # Simple check: sum of tokens should be constant
            if len(subnet_inv_places) >= 2:
                time_series = []
                for place_id in subnet_inv_places:
                    history = place_data.get(place_id, {})
                    tokens = history.get('tokens', [])
                    if tokens:
                        time_series.append(tokens)
                
                if time_series and len(time_series) >= 2:
                    # Calculate sum at each time point
                    min_len = min(len(ts) for ts in time_series)
                    sums = [sum(ts[i] for ts in time_series) for i in range(min_len)]
                    
                    if sums:
                        initial_sum = sums[0]
                        final_sum = sums[-1]
                        
                        # Check if sum changed significantly (> 10%)
                        if abs(final_sum - initial_sum) > initial_sum * 0.1:
                            violated = True
                            
                            issues.append(Issue(
                                category='conservation',
                                severity='error',
                                message=f"P-invariant '{invariant_name}' violated in subnet ({initial_sum:.1f} → {final_sum:.1f})",
                                element_id=None,
                                details={
                                    'invariant_violation': True,
                                    'invariant_name': invariant_name,
                                    'places': list(subnet_inv_places),
                                    'initial_sum': initial_sum,
                                    'final_sum': final_sum,
                                    'change': final_sum - initial_sum
                                }
                            ))
        
        return issues
    
    def _analyze_mass_balance(self, subnet: Subnet, kb: Any) -> List[Issue]:
        """Check mass balance in subnet transitions.
        
        For each transition, check if input mass equals output mass
        based on compound formulas.
        
        Args:
            subnet: Subnet object
            kb: Knowledge base with compound data
            
        Returns:
            List of mass balance issues
        """
        issues = []
        
        # This is a simplified check - full implementation would require
        # compound formulas and atomic mass calculations
        
        if not hasattr(kb, 'compounds'):
            return issues
        
        # For now, just check if reactions have compound mappings
        for trans_id in subnet.transitions:
            trans = kb.transitions.get(trans_id)
            if not trans:
                continue
            
            # Check if transition has reaction metadata
            if not hasattr(trans, 'reaction_id') or not trans.reaction_id:
                trans_name = self._get_human_readable_name(kb, trans_id, "transition")
                
                issues.append(Issue(
                    category='conservation',
                    severity='warning',
                    message=f"{trans_name} lacks reaction metadata for mass balance check",
                    element_id=trans_id,
                    details={
                        'mass_imbalance': True,
                        'reason': 'no_reaction_metadata'
                    }
                ))
        
        return issues
    
    def _analyze_conservation_leaks(self, subnet: Subnet, kb: Any, sim_data: Dict) -> List[Issue]:
        """Detect conservation leaks in subnet.
        
        A leak occurs when material disappears or appears without
        accounting for it in the model.
        
        Args:
            subnet: Subnet object
            kb: Knowledge base
            sim_data: Simulation data
            
        Returns:
            List of leak issues
        """
        issues = []
        
        # Skip if no simulation data
        if not sim_data:
            return issues
        
        place_data = sim_data.get('places', {})
        
        # Calculate total tokens in internal places over time
        internal_totals = []
        
        for place_id in subnet.internal_places:
            history = place_data.get(place_id, {})
            tokens = history.get('tokens', [])
            if tokens:
                internal_totals.append(tokens)
        
        if not internal_totals:
            return issues
        
        # Calculate sum at each time point
        min_len = min(len(ts) for ts in internal_totals) if internal_totals else 0
        if min_len < 2:
            return issues
        
        sums = [sum(ts[i] for ts in internal_totals) for i in range(min_len)]
        initial_sum = sums[0]
        final_sum = sums[-1]
        
        # Check for unexplained changes in internal places
        # (boundary flow is expected, but internal should follow conservation)
        if initial_sum > 0:
            change_percent = abs(final_sum - initial_sum) / initial_sum
            
            if change_percent > 0.5:  # More than 50% change
                issues.append(Issue(
                    category='conservation',
                    severity='warning',
                    message=f"Possible conservation leak in subnet: internal places changed {change_percent*100:.1f}%",
                    element_id=None,
                    details={
                        'leak': True,
                        'initial_total': initial_sum,
                        'final_total': final_sum,
                        'change_percent': change_percent,
                        'internal_places': list(subnet.internal_places)
                    }
                ))
        
        return issues
    
    def create_conservation_analysis(self, subnet: Subnet, kb: Any, sim_data: Dict) -> ConservationAnalysis:
        """Create ConservationAnalysis summary object.
        
        Args:
            subnet: Subnet object
            kb: Knowledge base
            sim_data: Simulation data
            
        Returns:
            ConservationAnalysis object
        """
        analysis = ConservationAnalysis()
        
        # Check P-invariants
        if hasattr(kb, 'p_invariants') and kb.p_invariants:
            place_data = sim_data.get('places', {})
            
            for invariant in kb.p_invariants:
                inv_places = set(invariant.get('places', []))
                subnet_inv_places = inv_places & subnet.places
                
                if not subnet_inv_places or len(subnet_inv_places) < 2:
                    continue
                
                invariant_name = invariant.get('name', 'Unknown')
                
                # Check if conserved
                time_series = []
                for place_id in subnet_inv_places:
                    history = place_data.get(place_id, {})
                    tokens = history.get('tokens', [])
                    if tokens:
                        time_series.append(tokens)
                
                if time_series and len(time_series) >= 2:
                    min_len = min(len(ts) for ts in time_series)
                    sums = [sum(ts[i] for ts in time_series) for i in range(min_len)]
                    
                    if sums:
                        initial_sum = sums[0]
                        final_sum = sums[-1]
                        
                        if abs(final_sum - initial_sum) <= initial_sum * 0.1:
                            analysis.conserved_invariants.append(invariant_name)
                        else:
                            analysis.violated_invariants.append(invariant_name)
        
        # Check for leaks
        place_data = sim_data.get('places', {})
        internal_totals = []
        
        for place_id in subnet.internal_places:
            history = place_data.get(place_id, {})
            tokens = history.get('tokens', [])
            if tokens:
                internal_totals.append(tokens)
        
        if internal_totals:
            min_len = min(len(ts) for ts in internal_totals)
            if min_len >= 2:
                sums = [sum(ts[i] for ts in internal_totals) for i in range(min_len)]
                initial_sum = sums[0]
                final_sum = sums[-1]
                
                if initial_sum > 0:
                    change_percent = abs(final_sum - initial_sum) / initial_sum
                    if change_percent > 0.5:
                        analysis.detected_leaks.append("internal_places_change")
                        analysis.mass_balance_ok = False
        
        return analysis
    
    def _suggest_invariant_fix(self, issue: Issue, context: Dict[str, Any]) -> List[Suggestion]:
        """Suggest fixes for P-invariant violations."""
        suggestions = []
        
        invariant_name = issue.details.get('invariant_name')
        places = issue.details.get('places', [])
        change = issue.details.get('change', 0)
        
        if change > 0:
            suggestions.append(Suggestion(
                category='conservation',
                action='add_sink',
                message=f"P-invariant '{invariant_name}' gains tokens: add sink or fix stoichiometry",
                parameters={
                    'invariant': invariant_name,
                    'places': places,
                    'excess': change
                },
                impact="Will restore conservation law"
            ))
        else:
            suggestions.append(Suggestion(
                category='conservation',
                action='add_source',
                message=f"P-invariant '{invariant_name}' loses tokens: add source or fix stoichiometry",
                parameters={
                    'invariant': invariant_name,
                    'places': places,
                    'deficit': abs(change)
                },
                impact="Will restore conservation law"
            ))
        
        return suggestions
    
    def _suggest_mass_fix(self, issue: Issue, context: Dict[str, Any]) -> List[Suggestion]:
        """Suggest fixes for mass balance issues."""
        suggestions = []
        
        trans_id = issue.element_id
        
        if issue.details.get('reason') == 'no_reaction_metadata':
            suggestions.append(Suggestion(
                category='conservation',
                action='map_reaction',
                message=f"Map {trans_id} to KEGG reaction for mass balance validation",
                parameters={'transition_id': trans_id},
                impact="Enables automatic mass balance checking"
            ))
        
        return suggestions
    
    def _suggest_leak_fix(self, issue: Issue, context: Dict[str, Any]) -> List[Suggestion]:
        """Suggest fixes for conservation leaks."""
        suggestions = []
        
        change_percent = issue.details.get('change_percent', 0) * 100
        
        suggestions.append(Suggestion(
            category='conservation',
            action='review_stoichiometry',
            message=f"Review stoichiometry: {change_percent:.1f}% change in internal places",
            parameters={
                'internal_places': issue.details.get('internal_places', [])
            },
            impact="Identify source of conservation violation"
        ))
        
        suggestions.append(Suggestion(
            category='conservation',
            action='check_arcs',
            message="Verify all input/output arcs have correct weights",
            parameters={},
            impact="Incorrect arc weights can violate conservation"
        ))
        
        return suggestions
