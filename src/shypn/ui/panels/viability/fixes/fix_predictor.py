"""Fix predictor for predicting impact before applying fixes.

Analyzes what will change and predicts cascading effects.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Any
from enum import Enum

from shypn.ui.panels.viability.investigation import Suggestion


class ChangeType(Enum):
    """Type of change predicted."""
    ARC_WEIGHT = "arc_weight"
    RATE = "rate"
    ADD_ELEMENT = "add_element"
    REMOVE_ELEMENT = "remove_element"
    MAPPING = "mapping"
    TOPOLOGY = "topology"


class ImpactLevel(Enum):
    """Level of predicted impact."""
    LOW = "low"          # Affects only target element
    MEDIUM = "medium"    # Affects nearby elements
    HIGH = "high"        # Affects subnet or multiple localities
    CRITICAL = "critical"  # Affects entire model


@dataclass
class PredictedChange:
    """A predicted change from applying a fix.
    
    Attributes:
        element_id: ID of affected element
        change_type: Type of change
        old_value: Current value (if applicable)
        new_value: Predicted new value (if applicable)
        description: Human-readable description
    """
    element_id: str
    change_type: ChangeType
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None
    description: str = ""


@dataclass
class FixPrediction:
    """Complete prediction of fix impact.
    
    Attributes:
        suggestion: The suggestion being predicted
        direct_changes: Changes directly made by the fix
        cascade_changes: Changes that cascade from the fix
        affected_elements: Set of all affected element IDs
        impact_level: Overall impact level
        risk_level: Risk assessment (low/medium/high)
        warnings: List of warnings about potential issues
    """
    suggestion: Suggestion
    direct_changes: List[PredictedChange] = field(default_factory=list)
    cascade_changes: List[PredictedChange] = field(default_factory=list)
    affected_elements: Set[str] = field(default_factory=set)
    impact_level: ImpactLevel = ImpactLevel.LOW
    risk_level: str = "low"
    warnings: List[str] = field(default_factory=list)
    
    def get_all_changes(self) -> List[PredictedChange]:
        """Get all changes (direct + cascade).
        
        Returns:
            Combined list of changes
        """
        return self.direct_changes + self.cascade_changes
    
    def has_warnings(self) -> bool:
        """Check if prediction has warnings.
        
        Returns:
            True if warnings exist
        """
        return len(self.warnings) > 0


class FixPredictor:
    """Predicts impact of applying fixes.
    
    Analyzes:
    1. Direct changes to target element
    2. Cascading changes to connected elements
    3. Overall impact level
    4. Potential risks and warnings
    """
    
    def __init__(self, kb):
        """Initialize fix predictor.
        
        Args:
            kb: Knowledge base (model)
        """
        self.kb = kb
    
    def predict(self, suggestion: Suggestion) -> FixPrediction:
        """Predict impact of applying a suggestion.
        
        Args:
            suggestion: The suggestion to predict
            
        Returns:
            FixPrediction with complete impact analysis
        """
        prediction = FixPrediction(suggestion=suggestion)
        
        # Predict direct changes
        self._predict_direct_changes(suggestion, prediction)
        
        # Predict cascade effects
        self._predict_cascade_effects(suggestion, prediction)
        
        # Compute affected elements
        prediction.affected_elements = self._compute_affected_elements(prediction)
        
        # Assess impact level
        prediction.impact_level = self._assess_impact_level(prediction)
        
        # Assess risk
        prediction.risk_level = self._assess_risk(prediction)
        
        # Generate warnings
        prediction.warnings = self._generate_warnings(prediction)
        
        return prediction
    
    def _predict_direct_changes(self, suggestion: Suggestion, prediction: FixPrediction):
        """Predict direct changes from the fix.
        
        Args:
            suggestion: The suggestion
            prediction: Prediction to populate
        """
        category = suggestion.category
        action = suggestion.action.lower()
        element_id = suggestion.target_element_id
        details = suggestion.details or {}
        
        if category == 'structural':
            self._predict_structural_changes(element_id, action, details, prediction)
        
        elif category == 'kinetic':
            self._predict_kinetic_changes(element_id, action, details, prediction)
        
        elif category == 'biological':
            self._predict_biological_changes(element_id, action, details, prediction)
        
        elif category in ['flow', 'boundary', 'conservation']:
            # These often involve multiple elements
            self._predict_multi_element_changes(suggestion, prediction)
    
    def _predict_structural_changes(self, element_id: str, action: str, 
                                    details: Dict, prediction: FixPrediction):
        """Predict structural changes."""
        if 'balance' in action and 'weight' in action:
            # Arc weight balancing
            transition = self.kb.transitions.get(element_id)
            if transition:
                # Predict weight changes for all arcs
                input_arcs = self._get_input_arcs(element_id)
                output_arcs = self._get_output_arcs(element_id)
                
                for arc in input_arcs + output_arcs:
                    arc_id = getattr(arc, 'id', str(arc))
                    old_weight = getattr(arc, 'weight', 1.0)
                    new_weight = details.get('target_weight', 1.0)
                    
                    change = PredictedChange(
                        element_id=arc_id,
                        change_type=ChangeType.ARC_WEIGHT,
                        old_value=old_weight,
                        new_value=new_weight,
                        description=f"Arc weight: {old_weight} → {new_weight}"
                    )
                    prediction.direct_changes.append(change)
        
        elif 'add' in action:
            # Adding element
            if 'arc' in action:
                change = PredictedChange(
                    element_id=element_id,
                    change_type=ChangeType.ADD_ELEMENT,
                    description=f"Add arc to/from {element_id}"
                )
            elif 'source' in action or 'sink' in action:
                element_type = 'source' if 'source' in action else 'sink'
                change = PredictedChange(
                    element_id=f"new_{element_type}",
                    change_type=ChangeType.ADD_ELEMENT,
                    description=f"Add {element_type} transition for {element_id}"
                )
            else:
                change = PredictedChange(
                    element_id=element_id,
                    change_type=ChangeType.ADD_ELEMENT,
                    description=f"Add element: {element_id}"
                )
            
            prediction.direct_changes.append(change)
    
    def _predict_kinetic_changes(self, element_id: str, action: str,
                                 details: Dict, prediction: FixPrediction):
        """Predict kinetic changes."""
        transition = self.kb.transitions.get(element_id)
        if not transition:
            return
        
        old_rate = getattr(transition, 'rate', 1.0)
        
        if 'increase' in action:
            multiplier = details.get('multiplier', 2.0)
            new_rate = old_rate * multiplier
        elif 'decrease' in action:
            multiplier = details.get('multiplier', 0.5)
            new_rate = old_rate * multiplier
        elif 'set' in action:
            new_rate = details.get('rate', 1.0)
        else:
            new_rate = old_rate
        
        change = PredictedChange(
            element_id=element_id,
            change_type=ChangeType.RATE,
            old_value=old_rate,
            new_value=new_rate,
            description=f"Rate: {old_rate:.2f} → {new_rate:.2f}"
        )
        prediction.direct_changes.append(change)
    
    def _predict_biological_changes(self, element_id: str, action: str,
                                    details: Dict, prediction: FixPrediction):
        """Predict biological changes."""
        if 'map compound' in action:
            compound_id = details.get('compound_id', 'unknown')
            change = PredictedChange(
                element_id=element_id,
                change_type=ChangeType.MAPPING,
                old_value=None,
                new_value=compound_id,
                description=f"Map to compound {compound_id}"
            )
            prediction.direct_changes.append(change)
        
        elif 'map reaction' in action:
            reaction_id = details.get('reaction_id', 'unknown')
            change = PredictedChange(
                element_id=element_id,
                change_type=ChangeType.MAPPING,
                old_value=None,
                new_value=reaction_id,
                description=f"Map to reaction {reaction_id}"
            )
            prediction.direct_changes.append(change)
    
    def _predict_multi_element_changes(self, suggestion: Suggestion, prediction: FixPrediction):
        """Predict changes affecting multiple elements."""
        details = suggestion.details or {}
        
        # Flow fixes often affect both producer and consumer
        if suggestion.category == 'flow':
            source_id = details.get('source')
            target_id = details.get('target')
            
            if source_id:
                source = self.kb.transitions.get(source_id)
                if source:
                    change = PredictedChange(
                        element_id=source_id,
                        change_type=ChangeType.RATE,
                        old_value=getattr(source, 'rate', 1.0),
                        new_value=getattr(source, 'rate', 1.0) * 1.5,
                        description=f"Adjust producer rate"
                    )
                    prediction.direct_changes.append(change)
            
            if target_id:
                target = self.kb.transitions.get(target_id)
                if target:
                    change = PredictedChange(
                        element_id=target_id,
                        change_type=ChangeType.RATE,
                        old_value=getattr(target, 'rate', 1.0),
                        new_value=getattr(target, 'rate', 1.0) * 1.5,
                        description=f"Adjust consumer rate"
                    )
                    prediction.direct_changes.append(change)
    
    def _predict_cascade_effects(self, suggestion: Suggestion, prediction: FixPrediction):
        """Predict cascading effects from the fix.
        
        Args:
            suggestion: The suggestion
            prediction: Prediction to populate
        """
        element_id = suggestion.target_element_id
        
        # Rate changes cascade through dependencies
        if suggestion.category == 'kinetic' or suggestion.category == 'flow':
            downstream = self._get_downstream_transitions(element_id)
            
            for trans_id in downstream:
                change = PredictedChange(
                    element_id=trans_id,
                    change_type=ChangeType.RATE,
                    description=f"May affect downstream transition {trans_id}"
                )
                prediction.cascade_changes.append(change)
        
        # Topology changes affect connected elements
        if suggestion.category == 'structural':
            action = suggestion.action.lower()
            if 'add' in action or 'remove' in action:
                connected = self._get_connected_elements(element_id)
                
                for conn_id in connected:
                    change = PredictedChange(
                        element_id=conn_id,
                        change_type=ChangeType.TOPOLOGY,
                        description=f"Topology change affects {conn_id}"
                    )
                    prediction.cascade_changes.append(change)
    
    def _compute_affected_elements(self, prediction: FixPrediction) -> Set[str]:
        """Compute set of all affected elements.
        
        Args:
            prediction: The prediction
            
        Returns:
            Set of element IDs
        """
        affected = set()
        
        for change in prediction.get_all_changes():
            affected.add(change.element_id)
        
        # Also add target element
        affected.add(prediction.suggestion.target_element_id)
        
        return affected
    
    def _assess_impact_level(self, prediction: FixPrediction) -> ImpactLevel:
        """Assess overall impact level.
        
        Args:
            prediction: The prediction
            
        Returns:
            Impact level
        """
        num_affected = len(prediction.affected_elements)
        num_cascades = len(prediction.cascade_changes)
        
        if num_affected == 1 and num_cascades == 0:
            return ImpactLevel.LOW
        elif num_affected <= 3 and num_cascades <= 2:
            return ImpactLevel.MEDIUM
        elif num_affected <= 10:
            return ImpactLevel.HIGH
        else:
            return ImpactLevel.CRITICAL
    
    def _assess_risk(self, prediction: FixPrediction) -> str:
        """Assess risk level of applying fix.
        
        Args:
            prediction: The prediction
            
        Returns:
            Risk level: 'low', 'medium', 'high'
        """
        risk_score = 0
        
        # More affected elements = higher risk
        risk_score += len(prediction.affected_elements) * 0.1
        
        # Cascade effects = higher risk
        risk_score += len(prediction.cascade_changes) * 0.2
        
        # Topology changes = higher risk
        for change in prediction.direct_changes:
            if change.change_type in [ChangeType.ADD_ELEMENT, ChangeType.REMOVE_ELEMENT, 
                                     ChangeType.TOPOLOGY]:
                risk_score += 0.5
        
        if risk_score < 1.0:
            return "low"
        elif risk_score < 3.0:
            return "medium"
        else:
            return "high"
    
    def _generate_warnings(self, prediction: FixPrediction) -> List[str]:
        """Generate warnings about potential issues.
        
        Args:
            prediction: The prediction
            
        Returns:
            List of warning messages
        """
        warnings = []
        
        # Warn about high impact
        if prediction.impact_level in [ImpactLevel.HIGH, ImpactLevel.CRITICAL]:
            warnings.append(f"⚠️  {prediction.impact_level.value.upper()} impact: "
                          f"affects {len(prediction.affected_elements)} elements")
        
        # Warn about cascade effects
        if len(prediction.cascade_changes) > 5:
            warnings.append(f"⚠️  Large cascade: {len(prediction.cascade_changes)} "
                          f"downstream changes predicted")
        
        # Warn about topology changes
        topology_changes = [c for c in prediction.direct_changes 
                           if c.change_type in [ChangeType.ADD_ELEMENT, 
                                               ChangeType.REMOVE_ELEMENT,
                                               ChangeType.TOPOLOGY]]
        if topology_changes:
            warnings.append(f"⚠️  Topology change: affects model structure")
        
        # Warn about high risk
        if prediction.risk_level == "high":
            warnings.append(f"⚠️  HIGH RISK: consider testing in isolation first")
        
        return warnings
    
    # Helper methods for graph traversal
    
    def _get_input_arcs(self, transition_id: str) -> List:
        """Get input arcs for a transition."""
        if not hasattr(self.kb, 'arcs'):
            return []
        
        return [arc for arc in self.kb.arcs.values()
                if hasattr(arc, 'target') and arc.target == transition_id]
    
    def _get_output_arcs(self, transition_id: str) -> List:
        """Get output arcs for a transition."""
        if not hasattr(self.kb, 'arcs'):
            return []
        
        return [arc for arc in self.kb.arcs.values()
                if hasattr(arc, 'source') and arc.source == transition_id]
    
    def _get_downstream_transitions(self, transition_id: str) -> List[str]:
        """Get transitions downstream of given transition.
        
        Uses simple BFS to find connected transitions.
        """
        if not hasattr(self.kb, 'arcs') or not hasattr(self.kb, 'transitions'):
            return []
        
        downstream = []
        visited = {transition_id}
        queue = [transition_id]
        
        while queue and len(downstream) < 10:  # Limit depth
            current = queue.pop(0)
            
            # Get output places
            output_arcs = self._get_output_arcs(current)
            for arc in output_arcs:
                place_id = getattr(arc, 'target', None)
                if not place_id:
                    continue
                
                # Get transitions consuming from this place
                consuming_arcs = [a for a in self.kb.arcs.values()
                                 if hasattr(a, 'source') and a.source == place_id]
                
                for cons_arc in consuming_arcs:
                    trans_id = getattr(cons_arc, 'target', None)
                    if trans_id and trans_id not in visited:
                        downstream.append(trans_id)
                        visited.add(trans_id)
                        queue.append(trans_id)
        
        return downstream[:10]  # Return max 10
    
    def _get_connected_elements(self, element_id: str) -> List[str]:
        """Get elements directly connected to given element."""
        if not hasattr(self.kb, 'arcs'):
            return []
        
        connected = []
        
        # If element is transition, get connected places
        if element_id in self.kb.transitions:
            input_arcs = self._get_input_arcs(element_id)
            output_arcs = self._get_output_arcs(element_id)
            
            for arc in input_arcs:
                if hasattr(arc, 'source'):
                    connected.append(arc.source)
            
            for arc in output_arcs:
                if hasattr(arc, 'target'):
                    connected.append(arc.target)
        
        # If element is place, get connected transitions
        elif element_id in self.kb.places:
            for arc in self.kb.arcs.values():
                if hasattr(arc, 'source') and arc.source == element_id:
                    if hasattr(arc, 'target'):
                        connected.append(arc.target)
                elif hasattr(arc, 'target') and arc.target == element_id:
                    if hasattr(arc, 'source'):
                        connected.append(arc.source)
        
        return connected
