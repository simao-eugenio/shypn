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
            condition=lambda data: 'simulation_state' in data and data['simulation_state'].get('has_data', False) and len(data['simulation_state'].get('dead_transitions', [])) > 0,
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
            condition=lambda data: 'simulation_state' in data and data['simulation_state'].get('has_data', False) and len(data['simulation_state'].get('zero_firing_transitions', [])) > 0,
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
            condition=lambda data: 'simulation_state' in data and data['simulation_state'].get('has_data', False) and len(data['simulation_state'].get('inactive_places', [])) > 0,
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
        print(f"[OBSERVER] ========== record_event() CALLED ==========")
        print(f"[OBSERVER] event_type: {event_type}")
        print(f"[OBSERVER] source: {source}")
        print(f"[OBSERVER] data keys: {list(data.keys())}")
        
        event = ObservationEvent(
            event_type=event_type,
            timestamp=datetime.now(),
            data=data,
            source=source
        )
        self.events.append(event)
        print(f"[OBSERVER] Event appended, total events: {len(self.events)}")
        
        # Update knowledge based on event
        self._update_knowledge(event)
        print(f"[OBSERVER] Knowledge updated")
        
        # Trigger rule evaluation
        print(f"[OBSERVER] About to evaluate rules...")
        self._evaluate_rules()
        print(f"[OBSERVER] Rules evaluated")
    
    def _update_knowledge(self, event: ObservationEvent):
        """Update accumulated knowledge from event.
        
        Args:
            event: Observation event
        """
        if event.event_type == "topology_complete":
            self.knowledge['topology_state'].update(event.data)
        
        elif event.event_type == "simulation_step":
            self.knowledge['simulation_state'].update(event.data)
        
        elif event.event_type == "simulation_complete":
            # Extract simulation data
            sim_data = event.data.get('simulation_data', {})
            
            print(f"[OBSERVER_DEBUG] ========== SIMULATION_COMPLETE EVENT ==========")
            print(f"[OBSERVER_DEBUG] sim_data type: {type(sim_data)}")
            print(f"[OBSERVER_DEBUG] sim_data keys: {list(sim_data.keys())}")
            print(f"[OBSERVER_DEBUG] dead_transitions type: {type(sim_data.get('dead_transitions', []))}")
            print(f"[OBSERVER_DEBUG] dead_transitions length: {len(sim_data.get('dead_transitions', []))}")
            if sim_data.get('dead_transitions'):
                dt_list = sim_data.get('dead_transitions', [])
                print(f"[OBSERVER_DEBUG] First 3 dead_transitions:")
                for i, dt in enumerate(dt_list[:3]):
                    print(f"[OBSERVER_DEBUG]   [{i}] type={type(dt)}, repr={repr(dt)}")
            
            self.knowledge['simulation_state'].update(sim_data)
            
            # Update biological state
            if 'places' in event.data:
                if 'places' not in self.knowledge['biological_state']:
                    self.knowledge['biological_state']['places'] = {}
                for place_id, place_obj in event.data['places'].items():
                    self.knowledge['biological_state']['places'][place_id] = {
                        'compound_id': getattr(place_obj, 'compound_id', None)
                    }
            
            if 'compounds' in event.data:
                self.knowledge['biological_state']['compounds'] = event.data['compounds']
            
            if 'arcs' in event.data:
                self.knowledge['biological_state']['arcs'] = event.data['arcs']
            
            if 'reactions' in event.data:
                self.knowledge['biological_state']['reactions'] = event.data['reactions']
            
            # Update kinetic state
            if 'transitions' in event.data:
                if 'transitions' not in self.knowledge['kinetic_state']:
                    self.knowledge['kinetic_state']['transitions'] = {}
                for trans_id, trans_obj in event.data['transitions'].items():
                    self.knowledge['kinetic_state']['transitions'][trans_id] = {
                        'rate': getattr(trans_obj, 'rate', 0.0)
                    }
            
            if 'kinetic_parameters' in event.data:
                self.knowledge['kinetic_state']['parameters'] = event.data['kinetic_parameters']
        
        elif event.event_type == "kb_updated":
            # Update topology state
            if 'liveness_status' in event.data:
                self.knowledge['topology_state']['liveness_status'] = event.data['liveness_status']
            if 'siphons' in event.data:
                self.knowledge['topology_state']['siphons'] = event.data['siphons']
            
            # Update biological state
            if 'compounds' in event.data:
                self.knowledge['biological_state']['compounds'] = event.data['compounds']
            if 'places' in event.data:
                if 'places' not in self.knowledge['biological_state']:
                    self.knowledge['biological_state']['places'] = {}
                for place_id, place_obj in event.data['places'].items():
                    self.knowledge['biological_state']['places'][place_id] = {
                        'compound_id': getattr(place_obj, 'compound_id', None)
                    }
            
            # Update kinetic state
            if 'kinetic_parameters' in event.data:
                self.knowledge['kinetic_state']['parameters'] = event.data['kinetic_parameters']
            if 'transitions' in event.data:
                if 'transitions' not in self.knowledge['kinetic_state']:
                    self.knowledge['kinetic_state']['transitions'] = {}
                for trans_id, trans_obj in event.data['transitions'].items():
                    self.knowledge['kinetic_state']['transitions'][trans_id] = {
                        'rate': getattr(trans_obj, 'rate', 0.0)
                    }
    
    def _evaluate_rules(self):
        """Evaluate all rules against current knowledge.
        
        This is the core of the intelligent analysis - it NEVER stops
        at the first failure. It evaluates ALL rules and gathers ALL
        applicable suggestions.
        """
        print(f"[OBSERVER] ========== _evaluate_rules() START ==========")
        print(f"[OBSERVER] Total rules: {len(self.rules)}")
        print(f"[OBSERVER] Knowledge keys: {list(self.knowledge.keys())}")
        
        suggestions_by_category = {
            'structural': [],
            'biological': [],
            'kinetic': [],
            'diagnosis': []
        }
        
        # Sort rules by priority
        sorted_rules = sorted(self.rules.values(), key=lambda r: r.priority)
        print(f"[OBSERVER] Sorted {len(sorted_rules)} rules by priority")
        print(f"[OBSERVER] knowledge keys: {list(self.knowledge.keys())}")
        print(f"[OBSERVER] simulation_state keys: {list(self.knowledge.get('simulation_state', {}).keys())}")
        print(f"[OBSERVER] simulation_state dead_transitions: {self.knowledge.get('simulation_state', {}).get('dead_transitions', 'NOT_FOUND')}")
        
        # Evaluate EVERY rule (never stop early)
        rules_evaluated = 0
        rules_triggered = 0
        for rule in sorted_rules:
            if not rule.enabled:
                continue
            
            rules_evaluated += 1
            try:
                # Check if rule applies
                applies = rule.condition(self.knowledge)
                print(f"[OBSERVER] Rule '{rule.rule_id}' (category={rule.category}): condition={applies}")
                
                if applies:
                    # Generate suggestions
                    issues = rule.action(self.knowledge)
                    if issues:
                        rules_triggered += 1
                        suggestions_by_category[rule.category].extend(issues)
                        print(f"[OBSERVER]   → Generated {len(issues)} issues")
            except Exception as e:
                import traceback
                print(f"[OBSERVER] ❌ Error evaluating rule {rule.rule_id}: {e}")
                traceback.print_exc()
                # Continue to next rule (never stop!)
                continue
        
        print(f"[OBSERVER] Evaluated {rules_evaluated} rules, {rules_triggered} triggered")
        print(f"[OBSERVER] Suggestions by category:")
        for cat, issues in suggestions_by_category.items():
            print(f"[OBSERVER]   {cat}: {len(issues)} issues")
        
        # Notify subscribers of updates
        for category, issues in suggestions_by_category.items():
            if issues:
                print(f"[OBSERVER] Notifying subscribers for category '{category}'...")
                self._notify_subscribers(category, issues)
        
        print(f"[OBSERVER] ========== _evaluate_rules() END ==========")
    
    def _notify_subscribers(self, category: str, issues: List[Any]):
        """Notify subscribers of updated suggestions.
        
        Args:
            category: Category name
            issues: List of issues/suggestions
        """
        print(f"[OBSERVER] _notify_subscribers for category '{category}' with {len(issues)} issues")
        print(f"[OBSERVER] Subscribers for '{category}': {len(self.subscribers.get(category, []))}")
        
        if category in self.subscribers:
            for i, callback in enumerate(self.subscribers[category]):
                try:
                    print(f"[OBSERVER] Calling subscriber {i+1}/{len(self.subscribers[category])} for '{category}'...")
                    callback(issues)
                    print(f"[OBSERVER]   ✅ Subscriber {i+1} called successfully")
                except Exception as e:
                    import traceback
                    print(f"[OBSERVER]   ❌ Error notifying subscriber {i+1}: {e}")
                    traceback.print_exc()
    
    def subscribe(self, category: str, callback: Callable[[List[Any]], None]):
        """Subscribe to suggestion updates for a category.
        
        Args:
            category: Category to subscribe to
            callback: Function to call with updated issues
        """
        if category not in self.subscribers:
            self.subscribers[category] = []
        self.subscribers[category].append(callback)
        print(f"[OBSERVER] ✅ Subscribed to category '{category}', total subscribers: {len(self.subscribers[category])}")
    
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
    
    def generate_suggestions_for_locality(self, locality_knowledge: Dict) -> List[Dict]:
        """Generate improvement suggestions for a specific transition locality.
        
        INTERACTIVE MODE: Called when user selects a transition.
        
        Args:
            locality_knowledge: Dict with transition, places, arcs, KB, simulation data
            
        Returns:
            List of suggestion dicts with category, title, description, action
        """
        print(f"[OBSERVER] ========== generate_suggestions_for_locality() ==========")
        suggestions = []
        
        transition_id = locality_knowledge.get('transition_id')
        transition = locality_knowledge.get('transition')
        kb = locality_knowledge.get('kb')
        sim_data = locality_knowledge.get('simulation_data', {})
        
        print(f"[OBSERVER] Transition: {transition_id}")
        print(f"[OBSERVER] Has simulation data: {sim_data.get('has_data', False)}")
        
        # STRUCTURAL SUGGESTIONS
        # Check if transition never fires
        if sim_data.get('transition_firings', -1) == 0:
            # Suggest: Check input places for tokens
            input_places = locality_knowledge.get('input_places', [])
            if input_places:
                suggestion = {
                    'category': 'structural',
                    'title': f'Add initial tokens to input places of {transition_id}',
                    'description': f'Transition {transition_id} never fired. Input places may need initial marking.',
                    'reasoning': f'Input places: {", ".join([p.id for p in input_places])}',
                    'confidence': 0.8,
                    'action_type': 'add_initial_marking',
                    'target_places': [p.id for p in input_places]
                }
                suggestions.append(suggestion)
        
        # KINETIC SUGGESTIONS
        # Check if transition has rate set
        if transition and hasattr(transition, 'rate'):
            if transition.rate == 0:
                suggestion = {
                    'category': 'kinetic',
                    'title': f'Query BRENDA for firing rate of {transition_id}',
                    'description': f'Transition {transition_id} has rate=0. Search BRENDA database for kinetic parameters.',
                    'reasoning': f'Reaction: {transition.label if hasattr(transition, "label") else "unknown"}',
                    'confidence': 0.7,
                    'action_type': 'query_brenda',
                    'target_transition': transition_id,
                    'reaction_id': getattr(transition, 'label', None)
                }
                suggestions.append(suggestion)
        
        # BIOLOGICAL SUGGESTIONS  
        # Check if places have compound mappings
        input_places = locality_knowledge.get('input_places', [])
        for place in input_places:
            if not hasattr(place, 'compound_id') or not place.compound_id:
                suggestion = {
                    'category': 'biological',
                    'title': f'Map place {place.id} to compound database',
                    'description': f'Place {place.id} is not mapped to a biological compound.',
                    'reasoning': 'Mapping enables pathway analysis and stoichiometry validation',
                    'confidence': 0.6,
                    'action_type': 'map_compound',
                    'target_place': place.id
                }
                suggestions.append(suggestion)
        
        print(f"[OBSERVER] Generated {len(suggestions)} suggestions for locality")
        return suggestions
    
    def generate_all_suggestions(self, kb, simulation_data=None) -> Dict[str, List[Dict]]:
        """Generate ALL improvement suggestions for entire model.
        
        BATCH MODE: Called when user clicks "Analyze All".
        
        Args:
            kb: ModelKnowledgeBase instance
            simulation_data: Optional dict with simulation results
            
        Returns:
            Dict mapping category names to lists of suggestions
        """
        print(f"[OBSERVER] ========== generate_all_suggestions() ==========")
        print(f"[OBSERVER] KB transitions: {len(kb.transitions) if kb else 0}")
        print(f"[OBSERVER] Has simulation data: {simulation_data is not None}")
        
        all_suggestions = {
            'structural': [],
            'biological': [],
            'kinetic': [],
            'diagnosis': []
        }
        
        if not kb:
            return all_suggestions
        
        # STRUCTURAL SUGGESTIONS - for all dead transitions
        if simulation_data and 'transitions' in simulation_data:
            for trans_id, trans_data in simulation_data['transitions'].items():
                if trans_data.get('firings', -1) == 0:
                    suggestion = {
                        'category': 'structural',
                        'title': f'Enable transition {trans_id} to fire',
                        'description': f'Transition {trans_id} never fired during simulation.',
                        'reasoning': 'Check input place tokens and arc weights',
                        'confidence': 0.8,
                        'action_type': 'fix_dead_transition',
                        'target_transition': trans_id
                    }
                    all_suggestions['structural'].append(suggestion)
        
        # KINETIC SUGGESTIONS - for transitions without rates
        for trans_id, trans_obj in kb.transitions.items():
            if hasattr(trans_obj, 'rate') and trans_obj.rate == 0:
                suggestion = {
                    'category': 'kinetic',
                    'title': f'Set firing rate for {trans_id}',
                    'description': f'Transition {trans_id} has rate=0.',
                    'reasoning': f'Query BRENDA for {getattr(trans_obj, "label", "reaction")}',
                    'confidence': 0.7,
                    'action_type': 'query_brenda',
                    'target_transition': trans_id
                }
                all_suggestions['kinetic'].append(suggestion)
        
        # BIOLOGICAL SUGGESTIONS - for unmapped places
        for place_id, place_obj in kb.places.items():
            if not hasattr(place_obj, 'compound_id') or not place_obj.compound_id:
                suggestion = {
                    'category': 'biological',
                    'title': f'Map place {place_id} to compound',
                    'description': f'Place {place_id} lacks compound mapping.',
                    'reasoning': 'Enable pathway analysis and validation',
                    'confidence': 0.6,
                    'action_type': 'map_compound',
                    'target_place': place_id
                }
                all_suggestions['biological'].append(suggestion)
        
        # DIAGNOSIS - summary of all issues
        total_suggestions = sum(len(s) for s in all_suggestions.values())
        if total_suggestions > 0:
            suggestion = {
                'category': 'diagnosis',
                'title': f'Model needs {total_suggestions} improvements',
                'description': f'Found {len(all_suggestions["structural"])} structural, '
                              f'{len(all_suggestions["kinetic"])} kinetic, and '
                              f'{len(all_suggestions["biological"])} biological suggestions.',
                'reasoning': 'Review each category for details',
                'confidence': 1.0,
                'action_type': 'summary'
            }
            all_suggestions['diagnosis'].append(suggestion)
        
        print(f"[OBSERVER] Generated {total_suggestions} total suggestions:")
        for cat, suggs in all_suggestions.items():
            print(f"[OBSERVER]   {cat}: {len(suggs)}")
        
        return all_suggestions
    
    # Rule action implementations
    def _analyze_dead_transitions_liveness(self, knowledge: Dict) -> List:
        """Analyze dead transitions from liveness analyzer.
        
        Uses topology analysis to identify structurally dead transitions.
        """
        from .viability_dataclasses import Issue
        issues = []
        
        liveness_status = knowledge.get('topology_state', {}).get('liveness_status', {})
        for trans_id, status in liveness_status.items():
            if status == 'dead':
                issue = Issue(
                    id=f"dead_transition_liveness_{trans_id}",
                    category="structural",
                    severity="critical",
                    title=f"Dead Transition (Topology): {trans_id}",
                    description=f"Transition {trans_id} is structurally dead and can never fire. "
                                "This indicates a modeling error or missing preconditions.",
                    element_id=trans_id,
                    element_type="transition",
                    metadata={'source': 'liveness_analyzer', 'status': status}
                )
                issues.append(issue)
        
        return issues
    
    def _analyze_dead_transitions_simulation(self, knowledge: Dict) -> List:
        """Analyze dead transitions from simulation data.
        
        Uses actual simulation results to identify transitions that never fired.
        """
        from .viability_dataclasses import Issue
        issues = []
        
        sim_data = knowledge.get('simulation_state', {})
        dead_transitions = sim_data.get('dead_transitions', [])
        
        for trans_id in dead_transitions:
            issue = Issue(
                id=f"dead_transition_simulation_{trans_id}",
                category="structural",
                severity="critical",
                title=f"Dead Transition (Simulation): {trans_id}",
                description=f"Transition {trans_id} never fired during simulation. "
                            "Check preconditions, rates, or initial marking.",
                element_id=trans_id,
                element_type="transition",
                metadata={'source': 'simulation', 'firings': 0}
            )
            issues.append(issue)
        
        return issues
    
    def _analyze_siphons(self, knowledge: Dict) -> List:
        """Analyze empty siphons.
        
        Empty siphons indicate places that will become permanently empty,
        blocking dependent transitions.
        """
        from .viability_dataclasses import Issue
        issues = []
        
        siphons = knowledge.get('topology_state', {}).get('siphons', [])
        for siphon in siphons:
            # Each siphon is a list of place IDs
            if isinstance(siphon, list) and len(siphon) > 0:
                place_ids = ', '.join(siphon)
                issue = Issue(
                    id=f"empty_siphon_{hash(tuple(siphon))}",
                    category="structural",
                    severity="warning",
                    title=f"Empty Siphon Detected",
                    description=f"Siphon containing places {place_ids} may become permanently empty, "
                                "causing deadlock. Add initial tokens or rework structure.",
                    element_id=siphon[0],  # Use first place as representative
                    element_type="place",
                    metadata={'source': 'topology', 'siphon': siphon}
                )
                issues.append(issue)
        
        return issues
    
    def _analyze_missing_rates(self, knowledge: Dict) -> List:
        """Analyze missing firing rates.
        
        Identifies transitions without kinetic parameters.
        """
        from .viability_dataclasses import Issue
        issues = []
        
        # This needs KB access - will be populated when KB is fed to observer
        transitions = knowledge.get('kinetic_state', {}).get('transitions', {})
        
        for trans_id, trans_data in transitions.items():
            rate = trans_data.get('rate', 0.0)
            if rate == 0.0 or rate is None:
                issue = Issue(
                    id=f"missing_rate_{trans_id}",
                    category="kinetic",
                    severity="warning",
                    title=f"Missing Rate: {trans_id}",
                    description=f"Transition {trans_id} has no firing rate. "
                                "Assign a rate from literature or experimental data.",
                    element_id=trans_id,
                    element_type="transition",
                    metadata={'source': 'kb', 'rate': rate}
                )
                issues.append(issue)
        
        return issues
    
    def _analyze_zero_firings(self, knowledge: Dict) -> List:
        """Analyze transitions that never fired.
        
        Uses simulation statistics to find inactive transitions.
        """
        from .viability_dataclasses import Issue
        issues = []
        
        sim_data = knowledge.get('simulation_state', {})
        zero_firing = sim_data.get('zero_firing_transitions', [])
        
        for trans_id in zero_firing:
            total_firings = sim_data.get('total_firings', {}).get(trans_id, 0)
            issue = Issue(
                id=f"zero_firing_{trans_id}",
                category="kinetic",
                severity="warning",
                title=f"Zero Firings: {trans_id}",
                description=f"Transition {trans_id} never fired (0 firings). "
                            "Check if rate is too low or preconditions are never met.",
                element_id=trans_id,
                element_type="transition",
                metadata={'source': 'simulation', 'firings': total_firings}
            )
            issues.append(issue)
        
        return issues
    
    def _analyze_rate_confidence(self, knowledge: Dict) -> List:
        """Analyze rate confidence levels.
        
        Identifies rates with low confidence from BRENDA or other sources.
        """
        from .viability_dataclasses import Issue
        issues = []
        
        kinetic_params = knowledge.get('kinetic_state', {}).get('parameters', {})
        
        for trans_id, params in kinetic_params.items():
            confidence = params.get('confidence', 1.0)
            if confidence < 0.5:  # Low confidence threshold
                issue = Issue(
                    id=f"low_confidence_{trans_id}",
                    category="kinetic",
                    severity="info",
                    title=f"Low Confidence Rate: {trans_id}",
                    description=f"Transition {trans_id} has low-confidence rate (confidence: {confidence:.0%}). "
                                "Consider querying BRENDA for better values.",
                    element_id=trans_id,
                    element_type="transition",
                    metadata={'source': 'brenda', 'confidence': confidence}
                )
                issues.append(issue)
        
        return issues
    
    def _analyze_compound_mapping(self, knowledge: Dict) -> List:
        """Analyze compound mappings.
        
        Identifies places not mapped to known compounds.
        """
        from .viability_dataclasses import Issue
        issues = []
        
        places = knowledge.get('biological_state', {}).get('places', {})
        compounds = knowledge.get('biological_state', {}).get('compounds', {})
        
        for place_id, place_data in places.items():
            compound_id = place_data.get('compound_id')
            if not compound_id or compound_id not in compounds:
                issue = Issue(
                    id=f"unmapped_compound_{place_id}",
                    category="biological",
                    severity="info",
                    title=f"Unmapped Compound: {place_id}",
                    description=f"Place {place_id} is not mapped to a known compound. "
                                "Map to KEGG/ChEBI for biological context.",
                    element_id=place_id,
                    element_type="place",
                    metadata={'source': 'kb', 'compound_id': compound_id}
                )
                issues.append(issue)
        
        return issues
    
    def _analyze_stoichiometry(self, knowledge: Dict) -> List:
        """Analyze stoichiometry mismatches.
        
        Checks if arc weights match known reaction stoichiometry.
        """
        from .viability_dataclasses import Issue
        issues = []
        
        arcs = knowledge.get('biological_state', {}).get('arcs', {})
        reactions = knowledge.get('biological_state', {}).get('reactions', {})
        
        for arc_id, arc_data in arcs.items():
            expected_weight = arc_data.get('expected_weight')
            actual_weight = arc_data.get('actual_weight', 1)
            
            if expected_weight and expected_weight != actual_weight:
                issue = Issue(
                    id=f"stoichiometry_mismatch_{arc_id}",
                    category="biological",
                    severity="warning",
                    title=f"Stoichiometry Mismatch: {arc_id}",
                    description=f"Arc {arc_id} has weight {actual_weight} but expected {expected_weight} "
                                "from biological database. Adjust weight to match reaction.",
                    element_id=arc_id,
                    element_type="arc",
                    metadata={'source': 'kegg', 'expected': expected_weight, 'actual': actual_weight}
                )
                issues.append(issue)
        
        return issues
    
    def _analyze_compound_activity(self, knowledge: Dict) -> List:
        """Analyze compound activity from simulation.
        
        Identifies places that never changed token count during simulation.
        """
        from .viability_dataclasses import Issue
        issues = []
        
        sim_data = knowledge.get('simulation_state', {})
        inactive_places = sim_data.get('inactive_places', [])
        
        for place_id in inactive_places:
            issue = Issue(
                id=f"inactive_compound_{place_id}",
                category="biological",
                severity="info",
                title=f"Inactive Compound: {place_id}",
                description=f"Place {place_id} tokens never changed during simulation. "
                            "Check if this compound should be involved in reactions.",
                element_id=place_id,
                element_type="place",
                metadata={'source': 'simulation', 'activity': 'none'}
            )
            issues.append(issue)
        
        return issues
