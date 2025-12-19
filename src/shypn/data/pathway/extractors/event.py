"""
Event Extractor

Extracts SBML events for experimental perturbations.
"""

from typing import List, Optional
import logging

try:
    import libsbml
except ImportError:
    libsbml = None

from ..pathway_data import Event
from .base import BaseExtractor


class EventExtractor(BaseExtractor[List[Event]]):
    """
    Extracts SBML events.
    
    Events enable experimental perturbations:
    - Time-based triggers (t > 100)
    - State-based triggers ([Glucose] < 0.1)
    - Discrete assignments to species/parameters
    
    Responsibilities:
    - Parse <event> elements
    - Extract trigger conditions (MathML)
    - Extract event assignments
    - Parse delays and priorities
    """
    
    def extract(self) -> List[Event]:
        """
        Extract all events from SBML model.
        
        Returns:
            List of Event objects
        """
        events = []
        
        num_events = self.model.getNumEvents()
        self.logger.info(f"Extracting {num_events} events...")
        
        for i in range(num_events):
            sbml_event = self.model.getEvent(i)
            event = self._convert_event(sbml_event)
            if event:
                events.append(event)
                self.logger.debug(f"  - {event.id}: {event.name or event.id}")
        
        return events
    
    def _convert_event(self, sbml_event) -> Optional[Event]:
        """
        Convert SBML event to Event object.
        
        Args:
            sbml_event: libsbml Event object
            
        Returns:
            Event object or None if extraction fails
        """
        try:
            event_id = sbml_event.getId()
            event_name = sbml_event.getName() or event_id
            
            # Extract trigger
            trigger_expr = ""
            if sbml_event.isSetTrigger():
                trigger = sbml_event.getTrigger()
                math = trigger.getMath()
                if math:
                    trigger_expr = libsbml.formulaToL3String(math)
            
            # Extract delay
            delay = 0.0
            if sbml_event.isSetDelay():
                delay_obj = sbml_event.getDelay()
                math = delay_obj.getMath()
                if math:
                    # Try to evaluate as constant, otherwise keep as expression
                    delay = self._evaluate_constant(math)
            
            # Extract assignments
            assignments = {}
            for j in range(sbml_event.getNumEventAssignments()):
                assignment = sbml_event.getEventAssignment(j)
                variable = assignment.getVariable()
                math = assignment.getMath()
                if math:
                    expr = libsbml.formulaToL3String(math)
                    assignments[variable] = expr
            
            # Priority
            priority = 0
            if sbml_event.isSetPriority():
                priority_obj = sbml_event.getPriority()
                math = priority_obj.getMath()
                if math:
                    priority = int(self._evaluate_constant(math))
            
            # Use values from trigger time
            use_trigger_time = sbml_event.getUseValuesFromTriggerTime()
            
            return Event(
                id=event_id,
                name=event_name,
                trigger=trigger_expr,
                delay=delay,
                use_values_from_trigger_time=use_trigger_time,
                priority=priority,
                assignments=assignments
            )
            
        except Exception as e:
            self.logger.error(f"Failed to extract event: {e}")
            self.add_error(f"Event extraction error: {e}")
            return None
    
    def _evaluate_constant(self, math_ast) -> float:
        """
        Try to evaluate MathML as constant.
        
        Args:
            math_ast: libsbml ASTNode
            
        Returns:
            Numeric value if constant, 0.0 otherwise
        """
        # Simple implementation - can be enhanced
        if math_ast.isNumber():
            return math_ast.getReal()
        return 0.0
