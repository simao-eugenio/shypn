#!/usr/bin/env python3
"""Viability Panel Observer System.

Continuously monitors application events and updates suggestions dynamically.

Events monitored:
1. Topology analysis complete → Update structural rules
2. Simulation step → Update kinetic statistics
3. Token change → Update biological activity
4. Arc modified → Update stoichiometry validation
5. Transition fired → Update rate analysis
6. File loaded → Full rescan
7. KB updated → Refresh knowledge

The observer never stops at first failure - it gathers data from ALL sources
and combines them intelligently.

Author: Simão Eugénio
Date: November 10, 2025
"""

from dataclasses import dataclass, field
from typing import Dict, List, Set, Callable, Any, Optional
from datetime import datetime


@dataclass
class ObservationEvent:
    """Event captured by the observer.
    
    Attributes:
        event_type: Type of event (topology_complete, simulation_step, etc.)
        timestamp: When the event occurred
        data: Event-specific data
        source: Source component that triggered the event
    """
    event_type: str
    timestamp: datetime
    data: Dict[str, Any]
    source: str


@dataclass
class ObservationRule:
    """Rule for analyzing observations.
    
    Attributes:
        rule_id: Unique rule identifier
        category: Category (structural, biological, kinetic)
        condition: Function that checks if rule applies
        action: Function that generates suggestions
        priority: Rule priority (1=high, 3=low)
        enabled: Whether rule is active
    """
    rule_id: str
    category: str
    condition: Callable[[Dict[str, Any]], bool]
    action: Callable[[Dict[str, Any]], List[Any]]  # Returns Issue list
    priority: int = 2
    enabled: bool = True


class ViabilityObserver:
    """Intelligent observer that monitors application events.
    
    The observer continuously gathers data from multiple sources and
    applies rules to generate dynamic suggestions. Never stops at first
    failure - analyzes all available data.
    
    Architecture:
    1. Event Stream: Captures events from throughout the application
    2. Rule Engine: Applies rules to generate suggestions
    3. Knowledge Accumulation: Builds understanding over time
    4. Dynamic Update: Notifies categories when suggestions change
    """
    
    def __init__(self):
        """Initialize the observer."""
        self.events: List[ObservationEvent] = []
        self.rules: Dict[str, ObservationRule] = {}
        self.knowledge: Dict[str, Any] = {
            'topology_state': {},
            'simulation_state': {},
            'biological_state': {},
            'kinetic_state': {}
        }
        self.subscribers: Dict[str, List[Callable]] = {
            'structural': [],
            'biological': [],
            'kinetic': [],
            'diagnosis': []
        }
        self._register_default_rules()
    
    def _register_default_rules(self):
        """Register default observation rules."""
        # STRUCTURAL RULES
        self.add_rule(ObservationRule(
            rule_id="dead_transitions_from_liveness",
            category="structural",
            condition=lambda data: 'liveness_status' in data and len(data['liveness_status']) > 0,
            action=self._analyze_dead_transitions_liveness,
            priority=1
        ))
        
        self.add_rule(ObservationRule(
            rule_id="dead_transitions_from_simulation",
            category="structural",
            condition=lambda data: 'simulation_data' in data and data['simulation_data'].get('has_data', False),
            action=self._analyze_dead_transitions_simulation,
            priority=1
        ))
        
        self.add_rule(ObservationRule(
            rule_id="empty_siphons",
            category="structural",
            condition=lambda data: 'siphons' in data and len(data['siphons']) > 0,
            action=self._analyze_siphons,
            priority=2
        ))
        
        # KINETIC RULES
        self.add_rule(ObservationRule(
            rule_id="missing_firing_rates",
            category="kinetic",
            condition=lambda data: 'transitions' in data,
            action=self._analyze_missing_rates,
            priority=1
        ))
        
        self.add_rule(ObservationRule(
            rule_id="zero_firing_transitions",
            category="kinetic",
            condition=lambda data: 'simulation_data' in data and data['simulation_data'].get('has_data', False),
            action=self._analyze_zero_firings,
            priority=1
        ))
        
        self.add_rule(ObservationRule(
            rule_id="low_confidence_rates",
            category="kinetic",
            condition=lambda data: 'kinetic_parameters' in data,
            action=self._analyze_rate_confidence,
            priority=3
        ))
        
        # BIOLOGICAL RULES
        self.add_rule(ObservationRule(
            rule_id="unmapped_compounds",
            category="biological",
            condition=lambda data: 'places' in data and 'compounds' in data,
            action=self._analyze_compound_mapping,
            priority=2
        ))
        
        self.add_rule(ObservationRule(
            rule_id="stoichiometry_mismatches",
            category="biological",
            condition=lambda data: 'arcs' in data and 'reactions' in data,
            action=self._analyze_stoichiometry,
            priority=1
        ))
        
        self.add_rule(ObservationRule(
            rule_id="inactive_compounds",
            category="biological",
            condition=lambda data: 'simulation_data' in data and data['simulation_data'].get('has_data', False),
            action=self._analyze_compound_activity,
            priority=2
        ))
    
    def add_rule(self, rule: ObservationRule):
        """Add observation rule.
        
        Args:
            rule: Rule to add
        """
        self.rules[rule.rule_id] = rule
    
    def remove_rule(self, rule_id: str):
        """Remove observation rule.
        
        Args:
            rule_id: Rule identifier
        """
        if rule_id in self.rules:
            del self.rules[rule_id]
    
    def record_event(self, event_type: str, data: Dict[str, Any], source: str = "unknown"):
        """Record an observation event.
        
        Args:
            event_type: Type of event
            data: Event data
            source: Source component
        """
        event = ObservationEvent(
            event_type=event_type,
            timestamp=datetime.now(),
            data=data,
            source=source
        )
        self.events.append(event)
        
        # Update knowledge based on event
        self._update_knowledge(event)
        
        # Trigger rule evaluation
        self._evaluate_rules()
    
    def _update_knowledge(self, event: ObservationEvent):
        """Update accumulated knowledge from event.
        
        Args:
            event: Observation event
        """
        if event.event_type == "topology_complete":
            self.knowledge['topology_state'].update(event.data)
        elif event.event_type == "simulation_step":
            self.knowledge['simulation_state'].update(event.data)
        elif event.event_type == "kb_updated":
            # Update all knowledge domains
            if 'liveness_status' in event.data:
                self.knowledge['topology_state']['liveness_status'] = event.data['liveness_status']
            if 'simulation_data' in event.data:
                self.knowledge['simulation_state'].update(event.data['simulation_data'])
            if 'compounds' in event.data:
                self.knowledge['biological_state']['compounds'] = event.data['compounds']
            if 'kinetic_parameters' in event.data:
                self.knowledge['kinetic_state']['parameters'] = event.data['kinetic_parameters']
    
    def _evaluate_rules(self):
        """Evaluate all rules against current knowledge.
        
        This is the core of the intelligent analysis - it NEVER stops
        at the first failure. It evaluates ALL rules and gathers ALL
        applicable suggestions.
        """
        suggestions_by_category = {
            'structural': [],
            'biological': [],
            'kinetic': [],
            'diagnosis': []
        }
        
        # Sort rules by priority
        sorted_rules = sorted(self.rules.values(), key=lambda r: r.priority)
        
        # Evaluate EVERY rule (never stop early)
        for rule in sorted_rules:
            if not rule.enabled:
                continue
            
            try:
                # Check if rule applies
                if rule.condition(self.knowledge):
                    # Generate suggestions
                    issues = rule.action(self.knowledge)
                    if issues:
                        suggestions_by_category[rule.category].extend(issues)
            except Exception as e:
                print(f"[OBSERVER] Error evaluating rule {rule.rule_id}: {e}")
                # Continue to next rule (never stop!)
                continue
        
        # Notify subscribers of updates
        for category, issues in suggestions_by_category.items():
            if issues:
                self._notify_subscribers(category, issues)
    
    def _notify_subscribers(self, category: str, issues: List[Any]):
        """Notify subscribers of updated suggestions.
        
        Args:
            category: Category name
            issues: List of issues/suggestions
        """
        if category in self.subscribers:
            for callback in self.subscribers[category]:
                try:
                    callback(issues)
                except Exception as e:
                    print(f"[OBSERVER] Error notifying subscriber: {e}")
    
    def subscribe(self, category: str, callback: Callable[[List[Any]], None]):
        """Subscribe to suggestion updates for a category.
        
        Args:
            category: Category to subscribe to
            callback: Function to call with updated issues
        """
        if category not in self.subscribers:
            self.subscribers[category] = []
        self.subscribers[category].append(callback)
    
    def get_current_suggestions(self, category: str) -> List[Any]:
        """Get current suggestions for a category.
        
        Args:
            category: Category name
            
        Returns:
            List of current issues/suggestions
        """
        # Evaluate rules for this category only
        suggestions = []
        for rule in self.rules.values():
            if rule.category == category and rule.enabled:
                try:
                    if rule.condition(self.knowledge):
                        issues = rule.action(self.knowledge)
                        if issues:
                            suggestions.extend(issues)
                except:
                    continue
        return suggestions
    
    # Rule action implementations
    def _analyze_dead_transitions_liveness(self, knowledge: Dict) -> List:
        """Analyze dead transitions from liveness analyzer."""
        # Implementation in next step
        return []
    
    def _analyze_dead_transitions_simulation(self, knowledge: Dict) -> List:
        """Analyze dead transitions from simulation data."""
        return []
    
    def _analyze_siphons(self, knowledge: Dict) -> List:
        """Analyze empty siphons."""
        return []
    
    def _analyze_missing_rates(self, knowledge: Dict) -> List:
        """Analyze missing firing rates."""
        return []
    
    def _analyze_zero_firings(self, knowledge: Dict) -> List:
        """Analyze transitions that never fired."""
        return []
    
    def _analyze_rate_confidence(self, knowledge: Dict) -> List:
        """Analyze rate confidence levels."""
        return []
    
    def _analyze_compound_mapping(self, knowledge: Dict) -> List:
        """Analyze compound mappings."""
        return []
    
    def _analyze_stoichiometry(self, knowledge: Dict) -> List:
        """Analyze stoichiometry mismatches."""
        return []
    
    def _analyze_compound_activity(self, knowledge: Dict) -> List:
        """Analyze compound activity from simulation."""
        return []
