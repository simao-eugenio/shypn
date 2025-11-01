#!/usr/bin/env python3
"""Test sigmoid rate function plotting for continuous transitions."""
import sys
sys.path.insert(0, '/home/simao/projetos/shypn/src')

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from shypn.netobjs import Place, Transition, Arc
from shypn.data.model_canvas_manager import ModelCanvasManager
from shypn.engine.simulation.controller import SimulationController
from shypn.analyses.data_collector import SimulationDataCollector

def test_sigmoid_plotting():
    """Test sigmoid rate function evaluation and plotting data."""
    
    print("\n" + "="*70)
    print("TEST: Sigmoid Rate Function Plotting Data")
    print("="*70 + "\n")
    
    # Create simple P-T-P model
    print("Creating P1 --[T1]--> P2 model with sigmoid rate...")
    model = ModelCanvasManager()
    
    # Create places (x, y, id, name, radius, label)
    p1 = Place(x=100, y=100, id=1, name="P1", label="Input")
    p1.tokens = 100  # Lots of tokens
    p1.initial_marking = 100
    
    p2 = Place(x=300, y=100, id=2, name="P2", label="Output")
    p2.tokens = 0
    p2.initial_marking = 0
    
    # Add to model
    model.places.append(p1)
    model.places.append(p2)
    
    # Create transition with sigmoid rate function (x, y, id, name, width, height, label, horizontal)
    t1 = Transition(x=200, y=100, id=1, name="T1", label="Transfer")
    t1.transition_type = 'continuous'
    
    # Set sigmoid rate function: sigmoid(t, 10, 0.5)
    # This should produce S-curve centered at t=10 with steepness=0.5
    t1.properties = {
        'rate_function': 'sigmoid(t, 10, 0.5)'
    }
    
    model.transitions.append(t1)
    
    # Create arcs (source, target, id, name, weight)
    arc_in = Arc(source=p1, target=t1, id=1, name="A1", weight=1)
    arc_out = Arc(source=t1, target=p2, id=2, name="A2", weight=1)
    
    model.arcs.append(arc_in)
    model.arcs.append(arc_out)
    
    print(f"✓ Model created:")
    print(f"  P1[{p1.tokens}] --[T1: sigmoid(t, 10, 0.5)]--> P2[{p2.tokens}]")
    print()
    
    # Create simulation controller with data collector
    controller = SimulationController(model)
    data_collector = SimulationDataCollector()
    controller.data_collector = data_collector
    controller.add_step_listener(data_collector.on_simulation_step)
    
    # Set duration and time step using settings API
    from shypn.utils.time_utils import TimeUnits
    controller.settings.set_duration(20.0, TimeUnits.SECONDS)  # Run for 20 seconds
    controller.settings.dt_auto = False  # Disable auto time step
    controller.settings.dt_manual = 0.1  # Manual time step for smooth curve
    
    print(f"Simulation settings:")
    print(f"  Duration: {controller.settings.duration}s")
    print(f"  Time step: {controller.settings.dt_manual}s")
    print(f"  Expected steps: {int(controller.settings.duration / controller.settings.dt_manual)}")
    print()
    
    # Run simulation
    print("Running simulation...")
    step_count = 0
    while controller.step():
        step_count += 1
        if step_count > 10000:  # Safety limit
            print("  Warning: Stopped at 10000 steps")
            break
    
    print(f"✓ Simulation complete: {step_count} steps")
    print(f"  Final time: {controller.time:.2f}s")
    print()
    
    # Check collected data
    print("Checking collected transition data...")
    t1_data = data_collector.get_transition_data(t1.id)
    
    if not t1_data:
        print("  ✗ NO DATA COLLECTED!")
        return False
    
    print(f"  ✓ {len(t1_data)} data points collected")
    print()
    
    # Check if rate is in details
    has_rate = False
    rate_values = []
    
    for time, event_type, details in t1_data:
        if details and isinstance(details, dict) and 'rate' in details:
            has_rate = True
            rate = details['rate']
            rate_values.append((time, rate))
    
    if not has_rate:
        print("  ✗ NO RATE DATA IN DETAILS!")
        return False
    
    print(f"  ✓ Rate data found in {len(rate_values)} events")
    print()
    
    # Display rate progression (sample)
    print("Rate function values over time (sigmoid should show S-curve):")
    print("="*70)
    print(f"{'Time (s)':<10} {'Rate (tokens/s)':<20} {'Expected Pattern'}")
    print("-"*70)
    
    # Sample every ~2 seconds
    sample_times = [0, 2, 5, 8, 10, 12, 15, 18, 20]
    
    for sample_t in sample_times:
        # Find closest data point
        closest = min(rate_values, key=lambda x: abs(x[0] - sample_t), default=None)
        if closest:
            t, rate = closest
            
            # Determine expected pattern
            if t < 5:
                pattern = "Low (start of S)"
            elif t < 9:
                pattern = "Rising (S-curve)"
            elif 9 <= t <= 11:
                pattern = "Midpoint (~0.5)"
            elif 11 < t < 15:
                pattern = "Rising fast"
            else:
                pattern = "High (saturating)"
            
            print(f"{t:<10.2f} {rate:<20.6f} {pattern}")
    
    print("="*70)
    print()
    
    # Check if we see S-curve pattern
    print("Analyzing S-curve pattern...")
    
    # Get rates at key times
    early_rates = [r for t, r in rate_values if t < 5]
    mid_rates = [r for t, r in rate_values if 9 <= t <= 11]
    late_rates = [r for t, r in rate_values if t > 15]
    
    if early_rates and mid_rates and late_rates:
        early_avg = sum(early_rates) / len(early_rates)
        mid_avg = sum(mid_rates) / len(mid_rates)
        late_avg = sum(late_rates) / len(late_rates)
        
        print(f"  Early (t<5):    {early_avg:.6f} (should be ~0.0)")
        print(f"  Middle (t~10):  {mid_avg:.6f} (should be ~0.5)")
        print(f"  Late (t>15):    {late_avg:.6f} (should be ~1.0)")
        print()
        
        # Check if we have S-curve pattern
        if early_avg < 0.2 and 0.4 < mid_avg < 0.6 and late_avg > 0.8:
            print("  ✓ S-CURVE PATTERN DETECTED!")
            print("    Sigmoid function is working correctly!")
        else:
            print("  ✗ S-curve pattern NOT clear")
            print("    Expected: low → mid → high progression")
            print(f"    Got: {early_avg:.3f} → {mid_avg:.3f} → {late_avg:.3f}")
            return False
    else:
        print("  ✗ Insufficient data points to verify S-curve")
        return False
    
    print()
    print("="*70)
    print("✓ TEST PASSED - Sigmoid rate function produces S-curve data")
    print("="*70)
    
    return True

if __name__ == '__main__':
    success = test_sigmoid_plotting()
    sys.exit(0 if success else 1)
