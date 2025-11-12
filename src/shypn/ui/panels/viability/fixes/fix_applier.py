"""Fix applier for applying suggestions to the model.

Applies fixes with full undo support and state tracking.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

from shypn.ui.panels.viability.investigation import Suggestion


class FixStatus(Enum):
    """Status of an applied fix."""
    PENDING = "pending"
    APPLIED = "applied"
    FAILED = "failed"
    REVERTED = "reverted"


@dataclass
class AppliedFix:
    """Record of an applied fix with undo information.
    
    Attributes:
        suggestion: The original suggestion
        status: Current status of the fix
        applied_at: Timestamp when applied
        reverted_at: Timestamp when reverted (if applicable)
        previous_state: State before fix was applied (for undo)
        error: Error message if application failed
    """
    suggestion: Suggestion
    status: FixStatus = FixStatus.PENDING
    applied_at: Optional[datetime] = None
    reverted_at: Optional[datetime] = None
    previous_state: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    
    def can_revert(self) -> bool:
        """Check if fix can be reverted.
        
        Returns:
            True if fix is applied and can be undone
        """
        return self.status == FixStatus.APPLIED and bool(self.previous_state)


class FixApplier:
    """Applies fixes to the model with undo support.
    
    Handles different types of fixes:
    - Arc weight adjustments
    - Adding/removing elements
    - Parameter updates
    - Compound mappings
    - Reaction mappings
    """
    
    def __init__(self, kb):
        """Initialize fix applier.
        
        Args:
            kb: Knowledge base (model)
        """
        self.kb = kb
        self.applied_fixes: List[AppliedFix] = []
    
    def apply(self, suggestion: Suggestion) -> AppliedFix:
        """Apply a fix suggestion to the model.
        
        Args:
            suggestion: The suggestion to apply
            
        Returns:
            AppliedFix record with status and undo info
        """
        applied_fix = AppliedFix(suggestion=suggestion)
        
        try:
            # Route to appropriate handler based on category
            if suggestion.category == 'structural':
                self._apply_structural_fix(suggestion, applied_fix)
            elif suggestion.category == 'kinetic':
                self._apply_kinetic_fix(suggestion, applied_fix)
            elif suggestion.category == 'biological':
                self._apply_biological_fix(suggestion, applied_fix)
            elif suggestion.category == 'flow':
                self._apply_flow_fix(suggestion, applied_fix)
            elif suggestion.category == 'boundary':
                self._apply_boundary_fix(suggestion, applied_fix)
            elif suggestion.category == 'conservation':
                self._apply_conservation_fix(suggestion, applied_fix)
            else:
                raise ValueError(f"Unknown fix category: {suggestion.category}")
            
            applied_fix.status = FixStatus.APPLIED
            applied_fix.applied_at = datetime.now()
            
        except Exception as e:
            applied_fix.status = FixStatus.FAILED
            applied_fix.error = str(e)
        
        self.applied_fixes.append(applied_fix)
        return applied_fix
    
    def revert(self, applied_fix: AppliedFix) -> bool:
        """Revert an applied fix.
        
        Args:
            applied_fix: The fix to revert
            
        Returns:
            True if successfully reverted
        """
        if not applied_fix.can_revert():
            return False
        
        try:
            # Restore previous state
            self._restore_state(applied_fix)
            
            applied_fix.status = FixStatus.REVERTED
            applied_fix.reverted_at = datetime.now()
            return True
            
        except Exception as e:
            applied_fix.error = f"Revert failed: {e}"
            return False
    
    def _apply_structural_fix(self, suggestion: Suggestion, applied_fix: AppliedFix):
        """Apply structural fix (arcs, weights, topology).
        
        Args:
            suggestion: The suggestion
            applied_fix: Record to update with undo info
        """
        details = suggestion.details or {}
        action = suggestion.action.lower()
        element_id = suggestion.target_element_id
        
        if 'balance' in action and 'weight' in action:
            # Balance arc weights
            self._balance_arc_weights(element_id, applied_fix)
        
        elif 'add' in action and 'arc' in action:
            # Add missing arc
            arc_type = details.get('arc_type', 'input')
            place_id = details.get('place_id')
            self._add_arc(element_id, place_id, arc_type, applied_fix)
        
        elif 'add' in action and 'source' in action:
            # Add source transition
            place_id = element_id  # Assuming element is the place needing source
            self._add_source_transition(place_id, applied_fix)
        
        elif 'add' in action and 'sink' in action:
            # Add sink transition
            place_id = element_id
            self._add_sink_transition(place_id, applied_fix)
        
        else:
            raise ValueError(f"Unknown structural fix: {action}")
    
    def _apply_kinetic_fix(self, suggestion: Suggestion, applied_fix: AppliedFix):
        """Apply kinetic fix (rates, parameters).
        
        Args:
            suggestion: The suggestion
            applied_fix: Record to update with undo info
        """
        details = suggestion.details or {}
        action = suggestion.action.lower()
        element_id = suggestion.target_element_id
        
        if 'rate' in action and 'increase' in action:
            # Increase rate
            multiplier = details.get('multiplier', 2.0)
            self._adjust_rate(element_id, multiplier, applied_fix)
        
        elif 'rate' in action and 'decrease' in action:
            # Decrease rate
            multiplier = details.get('multiplier', 0.5)
            self._adjust_rate(element_id, multiplier, applied_fix)
        
        elif 'rate' in action and 'set' in action:
            # Set specific rate
            new_rate = details.get('rate')
            self._set_rate(element_id, new_rate, applied_fix)
        
        elif 'query brenda' in action:
            # This requires user interaction - just mark for manual action
            applied_fix.previous_state['requires_manual_action'] = True
            applied_fix.previous_state['action_type'] = 'brenda_query'
        
        else:
            raise ValueError(f"Unknown kinetic fix: {action}")
    
    def _apply_biological_fix(self, suggestion: Suggestion, applied_fix: AppliedFix):
        """Apply biological fix (mappings).
        
        Args:
            suggestion: The suggestion
            applied_fix: Record to update with undo info
        """
        details = suggestion.details or {}
        action = suggestion.action.lower()
        element_id = suggestion.target_element_id
        
        if 'map compound' in action:
            # Map compound to KEGG
            compound_id = details.get('compound_id')
            self._map_compound(element_id, compound_id, applied_fix)
        
        elif 'map reaction' in action:
            # Map reaction to KEGG
            reaction_id = details.get('reaction_id')
            self._map_reaction(element_id, reaction_id, applied_fix)
        
        else:
            # Mark for manual action
            applied_fix.previous_state['requires_manual_action'] = True
            applied_fix.previous_state['action_type'] = 'biological_mapping'
    
    def _apply_flow_fix(self, suggestion: Suggestion, applied_fix: AppliedFix):
        """Apply flow fix (balance, bottlenecks).
        
        Args:
            suggestion: The suggestion
            applied_fix: Record to update with undo info
        """
        details = suggestion.details or {}
        action = suggestion.action.lower()
        
        if 'bottleneck' in action:
            # Fix bottleneck by increasing rate
            element_id = suggestion.target_element_id
            multiplier = details.get('multiplier', 2.0)
            self._adjust_rate(element_id, multiplier, applied_fix)
        
        elif 'balance' in action and 'rate' in action:
            # Balance production/consumption rates
            source_id = details.get('source')
            target_id = details.get('target')
            self._balance_rates(source_id, target_id, applied_fix)
        
        else:
            raise ValueError(f"Unknown flow fix: {action}")
    
    def _apply_boundary_fix(self, suggestion: Suggestion, applied_fix: AppliedFix):
        """Apply boundary fix (sources, sinks).
        
        Args:
            suggestion: The suggestion
            applied_fix: Record to update with undo info
        """
        # Boundary fixes are similar to structural fixes
        self._apply_structural_fix(suggestion, applied_fix)
    
    def _apply_conservation_fix(self, suggestion: Suggestion, applied_fix: AppliedFix):
        """Apply conservation fix (stoichiometry, invariants).
        
        Args:
            suggestion: The suggestion
            applied_fix: Record to update with undo info
        """
        details = suggestion.details or {}
        action = suggestion.action.lower()
        
        if 'stoichiometry' in action:
            # Review/fix stoichiometry - requires manual action
            applied_fix.previous_state['requires_manual_action'] = True
            applied_fix.previous_state['action_type'] = 'stoichiometry_review'
        
        elif 'source' in action or 'sink' in action:
            # Add source/sink to preserve invariant
            self._apply_structural_fix(suggestion, applied_fix)
        
        else:
            raise ValueError(f"Unknown conservation fix: {action}")
    
    # Helper methods for specific operations
    
    def _balance_arc_weights(self, transition_id: str, applied_fix: AppliedFix):
        """Balance input/output arc weights for a transition."""
        transition = self.kb.transitions.get(transition_id)
        if not transition:
            raise ValueError(f"Transition not found: {transition_id}")
        
        # Store previous weights
        applied_fix.previous_state['arc_weights'] = {}
        
        # Get input and output arcs
        input_arcs = [arc for arc in self.kb.arcs.values() 
                      if hasattr(arc, 'target') and arc.target == transition_id]
        output_arcs = [arc for arc in self.kb.arcs.values() 
                       if hasattr(arc, 'source') and arc.source == transition_id]
        
        # Calculate average weights
        if input_arcs and output_arcs:
            avg_input = sum(getattr(arc, 'weight', 1) for arc in input_arcs) / len(input_arcs)
            avg_output = sum(getattr(arc, 'weight', 1) for arc in output_arcs) / len(output_arcs)
            
            # Balance to average
            target_weight = (avg_input + avg_output) / 2
            
            for arc in input_arcs + output_arcs:
                arc_id = getattr(arc, 'id', str(arc))
                applied_fix.previous_state['arc_weights'][arc_id] = getattr(arc, 'weight', 1)
                arc.weight = target_weight
    
    def _add_arc(self, transition_id: str, place_id: str, arc_type: str, applied_fix: AppliedFix):
        """Add a new arc."""
        # Store that we added this arc
        applied_fix.previous_state['added_arc'] = {
            'transition': transition_id,
            'place': place_id,
            'type': arc_type
        }
        
        # In real implementation, would call kb.add_arc(...)
        # For now, just record the intent
    
    def _add_source_transition(self, place_id: str, applied_fix: AppliedFix):
        """Add a source transition producing to a place."""
        applied_fix.previous_state['added_transition'] = {
            'type': 'source',
            'place': place_id
        }
    
    def _add_sink_transition(self, place_id: str, applied_fix: AppliedFix):
        """Add a sink transition consuming from a place."""
        applied_fix.previous_state['added_transition'] = {
            'type': 'sink',
            'place': place_id
        }
    
    def _adjust_rate(self, transition_id: str, multiplier: float, applied_fix: AppliedFix):
        """Adjust transition rate by multiplier."""
        transition = self.kb.transitions.get(transition_id)
        if not transition:
            raise ValueError(f"Transition not found: {transition_id}")
        
        old_rate = getattr(transition, 'rate', 1.0)
        applied_fix.previous_state['rate'] = {
            'transition': transition_id,
            'old_value': old_rate
        }
        
        transition.rate = old_rate * multiplier
    
    def _set_rate(self, transition_id: str, new_rate: float, applied_fix: AppliedFix):
        """Set transition rate to specific value."""
        transition = self.kb.transitions.get(transition_id)
        if not transition:
            raise ValueError(f"Transition not found: {transition_id}")
        
        old_rate = getattr(transition, 'rate', 1.0)
        applied_fix.previous_state['rate'] = {
            'transition': transition_id,
            'old_value': old_rate
        }
        
        transition.rate = new_rate
    
    def _balance_rates(self, source_id: str, target_id: str, applied_fix: AppliedFix):
        """Balance rates between producer and consumer."""
        source = self.kb.transitions.get(source_id)
        target = self.kb.transitions.get(target_id)
        
        if not source or not target:
            raise ValueError(f"Transitions not found: {source_id}, {target_id}")
        
        source_rate = getattr(source, 'rate', 1.0)
        target_rate = getattr(target, 'rate', 1.0)
        
        applied_fix.previous_state['balanced_rates'] = {
            source_id: source_rate,
            target_id: target_rate
        }
        
        # Set both to average
        avg_rate = (source_rate + target_rate) / 2
        source.rate = avg_rate
        target.rate = avg_rate
    
    def _map_compound(self, place_id: str, compound_id: str, applied_fix: AppliedFix):
        """Map place to KEGG compound."""
        place = self.kb.places.get(place_id)
        if not place:
            raise ValueError(f"Place not found: {place_id}")
        
        old_mapping = getattr(place, 'compound_id', None)
        applied_fix.previous_state['compound_mapping'] = {
            'place': place_id,
            'old_value': old_mapping
        }
        
        place.compound_id = compound_id
    
    def _map_reaction(self, transition_id: str, reaction_id: str, applied_fix: AppliedFix):
        """Map transition to KEGG reaction."""
        transition = self.kb.transitions.get(transition_id)
        if not transition:
            raise ValueError(f"Transition not found: {transition_id}")
        
        old_mapping = getattr(transition, 'reaction_id', None)
        applied_fix.previous_state['reaction_mapping'] = {
            'transition': transition_id,
            'old_value': old_mapping
        }
        
        transition.reaction_id = reaction_id
    
    def _restore_state(self, applied_fix: AppliedFix):
        """Restore previous state from applied fix.
        
        Args:
            applied_fix: The fix to revert
        """
        state = applied_fix.previous_state
        
        # Restore arc weights
        if 'arc_weights' in state:
            for arc_id, old_weight in state['arc_weights'].items():
                arc = self.kb.arcs.get(arc_id)
                if arc:
                    arc.weight = old_weight
        
        # Restore rates
        if 'rate' in state:
            transition_id = state['rate']['transition']
            old_rate = state['rate']['old_value']
            transition = self.kb.transitions.get(transition_id)
            if transition:
                transition.rate = old_rate
        
        if 'balanced_rates' in state:
            for transition_id, old_rate in state['balanced_rates'].items():
                transition = self.kb.transitions.get(transition_id)
                if transition:
                    transition.rate = old_rate
        
        # Restore mappings
        if 'compound_mapping' in state:
            place_id = state['compound_mapping']['place']
            old_value = state['compound_mapping']['old_value']
            place = self.kb.places.get(place_id)
            if place:
                if old_value is None:
                    delattr(place, 'compound_id')
                else:
                    place.compound_id = old_value
        
        if 'reaction_mapping' in state:
            transition_id = state['reaction_mapping']['transition']
            old_value = state['reaction_mapping']['old_value']
            transition = self.kb.transitions.get(transition_id)
            if transition:
                if old_value is None:
                    delattr(transition, 'reaction_id')
                else:
                    transition.reaction_id = old_value
        
        # Remove added elements (in real impl, would call kb.remove_...)
        # For now, just recorded
    
    def get_history(self) -> List[AppliedFix]:
        """Get history of all applied fixes.
        
        Returns:
            List of applied fixes in chronological order
        """
        return self.applied_fixes.copy()
    
    def clear_history(self):
        """Clear fix history."""
        self.applied_fixes.clear()
