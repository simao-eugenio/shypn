#!/usr/bin/env python3
"""Subnet simulation engine with step-by-step control.

Executes isolated subnet simulations with parameter values from
the viability panel's TreeViews. Supports step-by-step execution
for detailed observation and full runs to completion.

Author: Simão Eugénio
Date: November 13, 2025
"""

import random
import math
import time
from datetime import datetime


class SimulationState:
    """Current state of subnet simulation."""
    
    def __init__(self):
        self.current_markings = {}      # {place_id: tokens}
        self.firing_counts = {}          # {trans_id: count}
        self.time = 0.0                  # Simulation time
        self.step_count = 0              # Number of firings
        self.enabled_transitions = []    # Currently enabled transitions
        self.is_running = False
        self.is_paused = False
        self.trajectory = []             # List of (time, markings) tuples
        
    def __repr__(self):
        return f"SimulationState(t={self.time:.2f}, steps={self.step_count}, enabled={len(self.enabled_transitions)})"


class SimulationResults:
    """Complete simulation outcomes."""
    
    def __init__(self):
        self.final_markings = {}         # {place_id: tokens}
        self.firing_counts = {}          # {trans_id: count}
        self.fluxes = {}                 # {trans_id: firings/time}
        self.viability_status = "Unknown"  # ✓ Stable / ✗ Deadlock / ⚠ Unbounded
        self.execution_time = 0.0        # Real execution time (seconds)
        self.sim_time = 0.0              # Simulation time
        self.step_count = 0              # Total firing events
        self.trajectory = []             # Full time series
        self.deadlocked = False
        self.unbounded_places = []
        
    def __repr__(self):
        return f"SimulationResults({self.viability_status}, t={self.sim_time:.2f}, steps={self.step_count})"


class SubnetSimulator:
    """Execute subnet simulation with step control.
    
    Integrates with existing viability panel components:
    - SubnetBuilder (subnet extraction)
    - TreeViews (parameter source)
    - LocalityDetector (subnet identification)
    """
    
    def __init__(self, viability_panel):
        """Initialize simulator.
        
        Args:
            viability_panel: ViabilityPanel instance
        """
        self.panel = viability_panel
        self.state = None
        self.subnet = None
        self.initial_markings = {}  # Store for reset
        
    def initialize_simulation(self):
        """Extract subnet and prepare for simulation.
        
        Returns:
            bool: True if initialization successful
        """
        # 1. Get model
        model = self.panel._get_current_model()
        if not model:
            return False
        
        # 2. Extract subnet from selected localities
        subnet = self._extract_subnet()
        if not subnet or not subnet['transitions']:
            return False
        
        # 3. Read parameters from TreeViews
        self._apply_parameters_from_treeviews(subnet)
        
        # 4. Initialize state
        self.state = SimulationState()
        self.subnet = subnet
        
        # Copy initial markings
        for place in subnet['places']:
            marking = place.marking if hasattr(place, 'marking') else 0
            self.state.current_markings[place.id] = marking
            self.initial_markings[place.id] = marking
            
        for trans in subnet['transitions']:
            self.state.firing_counts[trans.id] = 0
        
        # Initial trajectory point
        self.state.trajectory = [(0.0, self.state.current_markings.copy())]
        
        return True
    
    def _extract_subnet(self):
        """Extract subnet from selected localities.
        
        Returns:
            dict: Subnet with 'places', 'transitions', 'arcs' lists
        """
        model = self.panel._get_current_model()
        if not model:
            return None
        
        subnet = {
            'places': [],
            'transitions': [],
            'arcs': []
        }
        
        # Collect all elements from selected localities
        for transition_id, data in self.panel.selected_localities.items():
            locality = data.get('locality')
            if not locality:
                continue
            
            # Get transition object
            trans_obj = next((t for t in model.transitions if t.id == transition_id), None)
            if trans_obj and trans_obj not in subnet['transitions']:
                subnet['transitions'].append(trans_obj)
            
            # Get place objects
            all_place_ids = set(locality.input_places) | set(locality.output_places)
            for place_id in all_place_ids:
                place_obj = next((p for p in model.places if p.id == place_id), None)
                if place_obj and place_obj not in subnet['places']:
                    subnet['places'].append(place_obj)
            
            # Get arc objects
            all_arc_ids = set(locality.input_arcs) | set(locality.output_arcs)
            for arc_id in all_arc_ids:
                arc_obj = next((a for a in model.arcs if a.id == arc_id), None)
                if arc_obj and arc_obj not in subnet['arcs']:
                    subnet['arcs'].append(arc_obj)
        
        return subnet
    
    def _apply_parameters_from_treeviews(self, subnet):
        """Read edited parameters from TreeViews and apply to subnet elements.
        
        Args:
            subnet: Subnet dict to update
        """
        # Update place markings from Places tab
        for row in self.panel.places_store:
            place_id = row[0]
            marking = row[2]
            place_obj = next((p for p in subnet['places'] if p.id == place_id), None)
            if place_obj:
                place_obj.marking = marking
        
        # Update transition rates from Transitions tab
        for row in self.panel.transitions_store:
            trans_id = row[0]
            rate = row[2]
            trans_obj = next((t for t in subnet['transitions'] if t.id == trans_id), None)
            if trans_obj:
                trans_obj.rate = rate
        
        # Update arc weights from Arcs tab
        for row in self.panel.arcs_store:
            arc_id = row[0]
            weight = row[3]
            arc_obj = next((a for a in subnet['arcs'] if a.id == arc_id), None)
            if arc_obj:
                arc_obj.weight = weight
    
    def step(self):
        """Execute single firing event.
        
        Returns:
            dict or None: Step info with:
                - 'fired_transition': transition_id or None
                - 'time_delta': dt
                - 'marking_changes': {place_id: (old, new)}
                - 'enabled_transitions': [trans_ids]
                - 'deadlocked': bool
        """
        if not self.state or not self.subnet:
            return None
        
        # 1. Check enabled transitions
        enabled = self._get_enabled_transitions()
        self.state.enabled_transitions = enabled
        
        if not enabled:
            # Deadlock
            return {
                'fired_transition': None,
                'time_delta': 0.0,
                'marking_changes': {},
                'enabled_transitions': [],
                'deadlocked': True
            }
        
        # 2. Select transition (random for stochastic, first for deterministic)
        selected_trans = random.choice(enabled)
        
        # 3. Calculate time delta
        dt = self._calculate_time_delta(enabled)
        
        # 4. Fire transition
        marking_changes = self._fire_transition(selected_trans)
        
        # 5. Update state
        self.state.time += dt
        self.state.step_count += 1
        self.state.firing_counts[selected_trans.id] += 1
        self.state.trajectory.append((self.state.time, self.state.current_markings.copy()))
        
        return {
            'fired_transition': selected_trans.id,
            'time_delta': dt,
            'marking_changes': marking_changes,
            'enabled_transitions': [t.id for t in enabled],
            'deadlocked': False
        }
    
    def _get_enabled_transitions(self):
        """Find transitions with sufficient input tokens.
        
        Returns:
            list: Enabled transition objects
        """
        enabled = []
        
        for trans in self.subnet['transitions']:
            # Check if all input places have enough tokens
            can_fire = True
            
            for arc in self.subnet['arcs']:
                # Input arc: place → transition
                if hasattr(arc, 'target') and arc.target == trans:
                    place = arc.source
                    required = arc.weight if hasattr(arc, 'weight') else 1
                    available = self.state.current_markings.get(place.id, 0)
                    
                    if available < required:
                        can_fire = False
                        break
            
            if can_fire:
                enabled.append(trans)
        
        return enabled
    
    def _fire_transition(self, transition):
        """Execute transition firing, update markings.
        
        Args:
            transition: Transition object to fire
            
        Returns:
            dict: {place_id: (old_marking, new_marking)}
        """
        changes = {}
        
        # Consume from input places (place → transition arcs)
        for arc in self.subnet['arcs']:
            if hasattr(arc, 'target') and arc.target == transition:
                place = arc.source
                weight = arc.weight if hasattr(arc, 'weight') else 1
                
                old_marking = self.state.current_markings.get(place.id, 0)
                new_marking = max(0, old_marking - weight)
                self.state.current_markings[place.id] = new_marking
                changes[place.id] = (old_marking, new_marking)
        
        # Produce to output places (transition → place arcs)
        for arc in self.subnet['arcs']:
            if hasattr(arc, 'source') and arc.source == transition:
                place = arc.target
                weight = arc.weight if hasattr(arc, 'weight') else 1
                
                old_marking = self.state.current_markings.get(place.id, 0)
                new_marking = old_marking + weight
                self.state.current_markings[place.id] = new_marking
                
                # Update change record
                if place.id in changes:
                    changes[place.id] = (changes[place.id][0], new_marking)
                else:
                    changes[place.id] = (old_marking, new_marking)
        
        return changes
    
    def _calculate_time_delta(self, enabled_transitions):
        """Calculate time until next event (Gillespie algorithm).
        
        Args:
            enabled_transitions: List of enabled transition objects
            
        Returns:
            float: Time delta
        """
        if not enabled_transitions:
            return 0.0
        
        # Sum of propensities (rates)
        total_rate = 0.0
        for trans in enabled_transitions:
            rate = trans.rate if hasattr(trans, 'rate') else 1.0
            total_rate += rate
        
        if total_rate == 0:
            return 0.01  # Small fixed step if no rates defined
        
        # Exponential waiting time (Gillespie)
        return -math.log(random.random()) / total_rate
    
    def run_to_completion(self, max_time=100, max_steps=1000, log_callback=None):
        """Run simulation until deadlock or limits reached.
        
        Args:
            max_time: Maximum simulation time
            max_steps: Maximum firing events
            log_callback: Function to call with log messages
            
        Returns:
            SimulationResults: Complete outcomes
        """
        start_real_time = time.time()
        
        self.state.is_running = True
        self.state.is_paused = False
        
        while self.state.is_running and not self.state.is_paused:
            # Check limits
            if self.state.time >= max_time:
                if log_callback:
                    log_callback(f"⏱ Reached time limit ({max_time}s)")
                break
            
            if self.state.step_count >= max_steps:
                if log_callback:
                    log_callback(f"⏱ Reached step limit ({max_steps} steps)")
                break
            
            # Execute step
            step_info = self.step()
            
            if step_info['deadlocked']:
                if log_callback:
                    log_callback("✗ Deadlock detected - no enabled transitions")
                break
            
            # Log step (throttle to avoid spam)
            if log_callback and (self.state.step_count <= 10 or self.state.step_count % 100 == 0):
                trans_id = step_info['fired_transition']
                changes_str = ", ".join([
                    f"{pid}: {old}→{new}"
                    for pid, (old, new) in step_info['marking_changes'].items()
                ])
                log_callback(f"Step {self.state.step_count}: {trans_id} fired ({changes_str})")
        
        self.state.is_running = False
        
        # Create results
        results = SimulationResults()
        results.final_markings = self.state.current_markings.copy()
        results.firing_counts = self.state.firing_counts.copy()
        results.execution_time = time.time() - start_real_time
        results.sim_time = self.state.time
        results.step_count = self.state.step_count
        results.trajectory = self.state.trajectory.copy()
        results.deadlocked = len(self._get_enabled_transitions()) == 0
        
        # Calculate fluxes (firings per unit time)
        if self.state.time > 0:
            for trans_id, count in self.state.firing_counts.items():
                results.fluxes[trans_id] = count / self.state.time
        
        # Determine viability status
        if results.deadlocked:
            results.viability_status = "✗ Deadlock"
        elif any(m > 10000 for m in results.final_markings.values()):
            results.viability_status = "⚠ Unbounded"
            results.unbounded_places = [
                pid for pid, m in results.final_markings.items() if m > 10000
            ]
        else:
            results.viability_status = "✓ Stable"
        
        return results
    
    def reset(self):
        """Reset simulation to initial state."""
        if self.subnet and self.initial_markings:
            # Restore initial markings
            self.state = SimulationState()
            
            for place_id, marking in self.initial_markings.items():
                self.state.current_markings[place_id] = marking
            
            for trans in self.subnet['transitions']:
                self.state.firing_counts[trans.id] = 0
            
            self.state.trajectory = [(0.0, self.state.current_markings.copy())]
    
    def pause(self):
        """Pause running simulation."""
        if self.state:
            self.state.is_paused = True
    
    def resume(self):
        """Resume paused simulation."""
        if self.state:
            self.state.is_paused = False
    
    def stop(self):
        """Stop running simulation."""
        if self.state:
            self.state.is_running = False
    
    def is_initialized(self):
        """Check if simulator is ready.
        
        Returns:
            bool: True if initialized
        """
        return self.state is not None and self.subnet is not None
    
    def __repr__(self):
        status = "initialized" if self.is_initialized() else "uninitialized"
        return f"SubnetSimulator({status})"
