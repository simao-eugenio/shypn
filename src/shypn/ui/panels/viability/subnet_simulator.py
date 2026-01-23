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
    """Execute subnet simulation using real SimulationController infrastructure.
    
    This ensures all viability panel simulations use the same engine as
    the main simulation and automation experiments, providing:
    - Consistent behavior across all simulation modes
    - Proper data collection for analyses panel plotting
    - Support for all transition types (continuous, stochastic, timed, immediate)
    - Tau-leaping and advanced simulation features
    """
    
    def __init__(self, viability_panel):
        """Initialize simulator.
        
        Args:
            viability_panel: ViabilityPanel instance
        """
        self.panel = viability_panel
        self.controller = None  # Real SimulationController
        self.subnet_model = None  # DocumentModel built from subnet
        self.initial_markings = {}  # Store for reset
        
    def is_initialized(self):
        """Check if simulator is ready.
        
        Returns:
            bool: True if initialized
        """
        return self.controller is not None
        
    @property
    def state(self):
        """Get current simulation state (compatibility property).
        
        Returns:
            SimulationState-like object with controller data
        """
        if not self.controller:
            return None
        
        # Create compatibility wrapper around controller state
        class ControllerStateWrapper:
            def __init__(self, controller, initial_markings):
                self.controller = controller
                self.initial_markings = initial_markings
                
            @property
            def time(self):
                return self.controller.time
            
            @property
            def current_markings(self):
                return {p.id: p.tokens for p in self.controller.model_adapter.places.values()}
            
            @property
            def firing_counts(self):
                return {t.id: getattr(t, 'firing_count', 0) 
                       for t in self.controller.model_adapter.transitions.values()}
            
            @property
            def step_count(self):
                # Approximate from data collector length
                if self.controller.data_collector.time_points:
                    return len(self.controller.data_collector.time_points)
                return 0
            
            @property  
            def trajectory(self):
                # Build from data collector
                if not self.controller.data_collector.time_points:
                    return []
                times = self.controller.data_collector.time_points
                # Get place data for first place as reference
                place_ids = list(self.controller.data_collector.place_data.keys())
                if not place_ids:
                    return []
                result = []
                for i, t in enumerate(times):
                    marking = {
                        pid: self.controller.data_collector.place_data[pid][i][1]  # Extract tokens from (time, tokens) tuple
                        for pid in place_ids
                    }
                    result.append((t, marking))
                return result
            
            @property
            def enabled_transitions(self):
                # Return list of currently enabled transitions
                enabled = []
                for trans in self.controller.model_adapter.transitions.values():
                    behavior = self.controller._get_behavior(trans)
                    can_fire, _ = behavior.can_fire()
                    if can_fire:
                        enabled.append(trans)
                return enabled
            
            @property
            def is_running(self):
                return self.controller.is_running if hasattr(self.controller, 'is_running') else False
            
            @property
            def is_paused(self):
                return self.controller.is_paused if hasattr(self.controller, 'is_paused') else False
        
        return ControllerStateWrapper(self.controller, self.initial_markings)
        
    def initialize_simulation(self):
        """Extract subnet and prepare simulation using real SimulationController.
        
        Returns:
            bool: True if initialization successful
        """
        # 1. Get base model
        base_model = self.panel._get_current_model()
        if not base_model:
            return False
        
        # 2. Extract subnet from selected localities
        subnet = self._extract_subnet()
        if not subnet or not subnet['transitions']:
            return False
        
        # 3. Read parameters from TreeViews and apply to subnet
        self._apply_parameters_from_treeviews(subnet)
        
        # 4. Build a complete DocumentModel from subnet
        from shypn.data.canvas.document_model import DocumentModel
        self.subnet_model = DocumentModel()
        
        # Copy subnet elements to new model
        self.subnet_model.places = subnet['places']
        self.subnet_model.transitions = subnet['transitions']
        self.subnet_model.arcs = subnet['arcs']
        
        # Store initial markings
        self.initial_markings = {}
        for place in self.subnet_model.places:
            marking = getattr(place, 'tokens', 0)
            self.initial_markings[place.id] = marking
        
        # Initialize transition firing counts to 0 (CRITICAL for transition plots)
        for transition in self.subnet_model.transitions:
            transition.firing_count = 0
        
        # 5. Create SimulationController with subnet model
        from shypn.engine.simulation.controller import SimulationController
        self.controller = SimulationController(self.subnet_model)
        
        # Configure controller settings (τ-leaping for performance)
        self.controller.settings.use_tau_leaping = True
        self.controller.settings.tau_epsilon = 0.03
        
        # Start data collection (CRITICAL: must start BEFORE recording initial state)
        self.controller.data_collector.start_collection()
        
        # Record initial state at t=0 (captures initial place tokens AND transition firing_count=0)
        self.controller.data_collector.record_state(0.0)
        
        # Initialize transition enablement states
        self.controller._update_enablement_states()
        
        print(f"✓ SubnetSimulator initialized: {len(self.subnet_model.places)} places, "
              f"{len(self.subnet_model.transitions)} transitions")
        
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
            
            # Get transition object (prefer object from locality if available)
            trans_obj = getattr(locality, 'transition', None)
            if not trans_obj:
                trans_obj = next((t for t in model.transitions if t.id == transition_id), None)
            if trans_obj and trans_obj not in subnet['transitions']:
                subnet['transitions'].append(trans_obj)
            
            # Get place objects (handle both object and ID forms)
            all_places = set(locality.input_places) | set(locality.output_places)
            for place in all_places:
                if hasattr(place, 'id'):
                    place_obj = place
                else:
                    place_obj = next((p for p in model.places if p.id == place), None)
                if place_obj and place_obj not in subnet['places']:
                    subnet['places'].append(place_obj)
            
            # Get arc objects (handle both object and ID forms)
            all_arcs = set(locality.input_arcs) | set(locality.output_arcs)
            for arc in all_arcs:
                if hasattr(arc, 'id'):
                    arc_obj = arc
                else:
                    arc_obj = next((a for a in model.arcs if a.id == arc), None)
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
                place_obj.tokens = marking  # Use .tokens not .marking
        
        # Update transition rates - prefer formulas from experiment_manager baseline
        for row in self.panel.transitions_store:
            trans_id = row[0]
            rate = row[2]  # Column 2: numeric rate
            formula = row[3]  # Column 3: formula string
            trans_obj = next((t for t in subnet['transitions'] if t.id == trans_id), None)
            if trans_obj:
                # Prefer formula over rate if available
                if formula and formula.strip():
                    trans_obj.rate = formula  # Assign formula string
                else:
                    trans_obj.rate = rate
        
        # Update arc weights from Arcs tab
        for row in self.panel.arcs_store:
            arc_id = row[0]
            weight = row[3]
            arc_obj = next((a for a in subnet['arcs'] if a.id == arc_id), None)
            if arc_obj:
                arc_obj.weight = weight
    
    def step(self):
        """Execute single simulation step using real SimulationController.
        
        Returns:
            dict or None: Step info with:
                - 'fired_transition': transition_id or None  
                - 'time_delta': dt
                - 'marking_changes': {place_id: (old, new)}
                - 'enabled_transitions': [trans_ids]
                - 'deadlocked': bool
        """
        if not self.controller:
            return None
        
        # Get markings and firing counts before step
        markings_before = {p.id: p.tokens for p in self.controller.model_adapter.places.values()}
        firing_counts_before = {
            t.id: getattr(t, 'firing_count', 0) 
            for t in self.controller.model_adapter.transitions.values()
        }
        time_before = self.controller.time
        
        # Execute one simulation step using real controller
        success = self.controller.step()
        
        # Get markings and firing counts after step
        markings_after = {p.id: p.tokens for p in self.controller.model_adapter.places.values()}
        firing_counts_after = {
            t.id: getattr(t, 'firing_count', 0) 
            for t in self.controller.model_adapter.transitions.values()
        }
        time_after = self.controller.time
        
        # Calculate marking changes
        marking_changes = {}
        for pid in markings_before:
            if markings_before[pid] != markings_after.get(pid, 0):
                marking_changes[pid] = (markings_before[pid], markings_after[pid])
        
        # Detect which transition(s) fired by checking firing_count changes
        fired_transitions = []
        for tid in firing_counts_before:
            count_before = firing_counts_before[tid]
            count_after = firing_counts_after.get(tid, 0)
            if count_after > count_before:
                fired_transitions.append(tid)
        
        # Get enabled transitions
        enabled_ids = []
        for trans in self.controller.model_adapter.transitions.values():
            behavior = self.controller._get_behavior(trans)
            can_fire, _ = behavior.can_fire()
            if can_fire:
                enabled_ids.append(trans.id)
        
        if not success:
            # Deadlock or simulation ended
            return {
                'fired_transition': None,
                'time_delta': 0.0,
                'marking_changes': {},
                'enabled_transitions': enabled_ids,
                'deadlocked': len(enabled_ids) == 0
            }
        
        # Report first fired transition (or None if none detected)
        fired_transition = fired_transitions[0] if fired_transitions else None
        
        return {
            'fired_transition': fired_transition,
            'time_delta': time_after - time_before,
            'marking_changes': marking_changes,
            'enabled_transitions': enabled_ids,
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
        """Run simulation until deadlock or limits using real SimulationController.
        
        Args:
            max_time: Maximum simulation time
            max_steps: Maximum firing events
            log_callback: Function to call with log messages
            
        Returns:
            SimulationResults: Complete outcomes
        """
        if not self.controller:
            if log_callback:
                log_callback("✗ Simulator not initialized")
            return SimulationResults()
        
        start_real_time = time.time()
        
        # Configure controller duration
        self.controller.settings.duration = max_time
        
        # Run simulation loop using controller.step()
        step_count = 0
        while step_count < max_steps and self.controller.time < max_time:
            # Check for enabled transitions (deadlock detection)
            has_enabled = False
            for trans in self.controller.model_adapter.transitions.values():
                behavior = self.controller._get_behavior(trans)
                can_fire, _ = behavior.can_fire()
                if can_fire:
                    has_enabled = True
                    break
            
            if not has_enabled:
                if log_callback:
                    log_callback("✗ Deadlock detected - no enabled transitions")
                break
            
            # Execute one controller step
            success = self.controller.step()
            step_count += 1
            
            if not success:
                if log_callback:
                    log_callback("✗ Simulation stopped")
                break
            
            # Log progress periodically
            if log_callback and (step_count % 100 == 0):
                markings_summary = ", ".join([
                    f"{p.id}={p.tokens}"
                    for p in list(self.controller.model_adapter.places.values())[:3]
                ])
                log_callback(f"Step {step_count}: t={self.controller.time:.2f}s | {markings_summary}...")
        
        # Check why we stopped
        if self.controller.time >= max_time:
            if log_callback:
                log_callback(f"⏱ Reached time limit ({max_time}s)")
        elif step_count >= max_steps:
            if log_callback:
                log_callback(f"⏱ Reached step limit ({max_steps} steps)")
        
        # Build results from controller state
        results = SimulationResults()
        results.final_markings = {p.id: p.tokens for p in self.controller.model_adapter.places.values()}
        results.firing_counts = {
            t.id: getattr(t, 'firing_count', 0)
            for t in self.controller.model_adapter.transitions.values()
        }
        results.execution_time = time.time() - start_real_time
        results.sim_time = self.controller.time
        results.step_count = step_count
        
        # Get trajectory from data collector
        if self.controller.data_collector.time_points:
            times = self.controller.data_collector.time_points
            place_ids = list(self.controller.data_collector.place_data.keys())
            for i, t in enumerate(times):
                marking = {
                    pid: self.controller.data_collector.place_data[pid][i][1]  # Extract tokens from (time, tokens) tuple
                    for pid in place_ids
                }
                results.trajectory.append((t, marking))
        
        # Check for deadlock
        results.deadlocked = not any(
            self.controller._get_behavior(t).can_fire()[0]
            for t in self.controller.model_adapter.transitions.values()
        )
        
        # Calculate fluxes (firings per unit time)
        if results.sim_time > 0:
            for trans_id, count in results.firing_counts.items():
                results.fluxes[trans_id] = count / results.sim_time
        
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
        if not self.controller or not self.initial_markings:
            return
        
        # Reset place markings to initial values
        for place in self.controller.model_adapter.places.values():
            if place.id in self.initial_markings:
                place.tokens = self.initial_markings[place.id]
        
        # Reset transition firing counts
        for trans in self.controller.model_adapter.transitions.values():
            if hasattr(trans, 'firing_count'):
                trans.firing_count = 0
        
        # Reset controller time
        self.controller.time = 0.0
        
        # Reset data collector
        self.controller.data_collector.clear()
        self.controller.data_collector.start_collection()
        self.controller.data_collector.record_state(0.0)
        
        # Re-initialize enablement states
        self.controller._update_enablement_states()
    
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
    
    def __repr__(self):
        status = "initialized" if self.is_initialized() else "uninitialized"
        return f"SubnetSimulator({status})"
