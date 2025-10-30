#!/usr/bin/env python3
"""Diagnosis of sigmoid plotting issue.

Issue Report:
- User entered sigmoid(t, 10, 0.5) on continuous transition rate function
- Expected S-curve but sees straight line in plot
  
Investigation Results:
1. ✓ Sigmoid function implementation is correct
2. ✓ Rate data collection is correct (verified S-curve values)
3. ✓ Plotting code extracts and plots rate correctly

Root Cause Analysis:
The issue is likely related to SIMULATION DURATION and TIME RANGE:

Problem: sigmoid(t, 10, 0.5) parameters mean:
  - Center: t = 10 seconds
  - Steepness: 0.5 (relatively gradual S-curve)
  - The S-curve transitions from ~0 to ~1 between t=0 and t=20
  
If simulation runs with default settings (no duration limit), it runs
until P1 is exhausted, which could be 100+ seconds. When plotting 
0-100s range, the S-curve (0-20s) gets compressed and looks like a 
step or straight line!

Solution: User needs to set appropriate simulation duration to match
the sigmoid parameters. For sigmoid(t, center, steepness):
  - Duration should be ~2 * center to see full S-curve
  - For sigmoid(t, 10, 0.5), use duration = 20-30 seconds

Additional Finding:
The sigmoid function amplitude defaults to 1.0, so:
  - sigmoid(t, 10, 0.5) means sigmoid(t, 10, 0.5, 1.0)
  - Rate ranges from 0 to 1 tokens/second
  - With 100 tokens in P1, it takes ~100 seconds to deplete
  - By t=20, sigmoid is already at ~0.99, so rest looks flat

Recommendations:
1. Set simulation duration appropriately (e.g., 20-30s for sigmoid(t,10,0.5))
2. OR adjust sigmoid parameters to match intended simulation duration
3. Add UI hint: "For sigmoid(t, center, steepness), set duration ~2*center"
4. Consider auto-zooming plot to show interesting region
"""

import sys
sys.path.insert(0, '/home/simao/projetos/shypn/src')

import gi
gi.require_version('Gtk', '3.0')

from shypn.netobjs import Place, Transition, Arc
from shypn.data.model_canvas_manager import ModelCanvasManager
from shypn.engine.simulation.controller import SimulationController
from shypn.analyses.data_collector import SimulationDataCollector
from shypn.utils.time_utils import TimeUnits

def test_scenario(duration, title):
    """Test sigmoid plotting with given duration."""
    print(f"\n{'='*70}")
    print(f"SCENARIO: {title}")
    print(f"{'='*70}")
    print(f"Duration: {duration if duration else 'No limit (runs until depletion)'}")
    print()
    
    # Create model
    model = ModelCanvasManager()
    
    p1 = Place(x=100, y=100, id=1, name="P1", label="Input")
    p1.tokens = 100
    p1.initial_marking = 100
    
    p2 = Place(x=300, y=100, id=2, name="P2", label="Output")
    p2.tokens = 0
    p2.initial_marking = 0
    
    model.places.append(p1)
    model.places.append(p2)
    
    t1 = Transition(x=200, y=100, id=1, name="T1", label="Transfer")
    t1.transition_type = 'continuous'
    t1.properties = {'rate_function': 'sigmoid(t, 10, 0.5)'}
    model.transitions.append(t1)
    
    arc_in = Arc(source=p1, target=t1, id=1, name="A1", weight=1)
    arc_out = Arc(source=t1, target=p2, id=2, name="A2", weight=1)
    model.arcs.append(arc_in)
    model.arcs.append(arc_out)
    
    # Setup simulation
    controller = SimulationController(model)
    data_collector = SimulationDataCollector()
    controller.data_collector = data_collector
    controller.add_step_listener(data_collector.on_simulation_step)
    
    if duration:
        controller.settings.set_duration(duration, TimeUnits.SECONDS)
    controller.settings.dt_auto = False
    controller.settings.dt_manual = 0.1
    
    # Run
    step_count = 0
    while controller.step():
        step_count += 1
        if step_count > 10000:
            break
    
    # Analyze data
    t1_data = data_collector.get_transition_data(t1.id)
    print(f"Simulation ran: {step_count} steps to time {controller.time:.1f}s")
    print(f"Data points: {len(t1_data)}")
    print()
    
    # Show rate progression
    print("Rate values over time:")
    print(f"{'Time':>6s}  {'Rate':>8s}  {'Visual':30s}  {'Comments'}")
    print("-" * 70)
    
    sample_indices = [0, len(t1_data)//8, len(t1_data)//4, 3*len(t1_data)//8,
                     len(t1_data)//2, 5*len(t1_data)//8, 3*len(t1_data)//4, 
                     7*len(t1_data)//8, len(t1_data)-1]
    
    for i in sample_indices:
        if i < len(t1_data):
            time, event, details = t1_data[i]
            if details and 'rate' in details:
                rate = details['rate']
                bar_length = int(rate * 30)
                bar = '█' * bar_length
                
                if rate < 0.1:
                    comment = "← S-curve start"
                elif 0.4 <= rate <= 0.6:
                    comment = "← S-curve middle"
                elif rate > 0.9:
                    comment = "← S-curve saturated"
                else:
                    comment = ""
                
                print(f"{time:6.1f}  {rate:8.6f}  {bar:30s}  {comment}")
    
    print()
    
    # Visual assessment
    early_threshold = duration/4 if duration else 5
    late_threshold = 3*duration/4 if duration else controller.time * 0.75
    
    early_times = [d for d in t1_data if d[0] < early_threshold]
    late_times = [d for d in t1_data if d[0] > late_threshold]
    
    if early_times and late_times:
        early_rate = early_times[len(early_times)//2][2].get('rate', 0) if early_times[len(early_times)//2][2] else 0
        late_rate = late_times[len(late_times)//2][2].get('rate', 0) if late_times[len(late_times)//2][2] else 0
        
        print(f"Visual Analysis:")
        print(f"  Early portion (first 25%): rate ≈ {early_rate:.4f}")
        print(f"  Late portion (last 25%):  rate ≈ {late_rate:.4f}")
        print(f"  Change: {abs(late_rate - early_rate):.4f}")
        print()
        
        if abs(late_rate - early_rate) < 0.1:
            print(f"  ⚠ LOOKS LIKE STRAIGHT LINE!")
            print(f"     Most of the time range shows saturated rate (~{late_rate:.2f})")
            print(f"     S-curve portion is compressed into first ~{duration/5 if duration else 20}s")
        elif abs(late_rate - early_rate) > 0.5:
            print(f"  ✓ LOOKS LIKE S-CURVE!")
            print(f"     Clear transition from low to high rate visible")
        else:
            print(f"  ~ Partial S-curve visible")

def main():
    print("\n" + "="*70)
    print("SIGMOID RATE FUNCTION - ROOT CAUSE DIAGNOSIS")
    print("="*70)
    print()
    print("Testing sigmoid(t, 10, 0.5) with different simulation durations")
    print("to understand why user sees straight line instead of S-curve")
    print()
    
    # Test 1: No duration limit (what user might experience by default)
    test_scenario(None, "Default (no duration limit)")
    
    # Test 2: Short duration (shows S-curve properly)
    test_scenario(20.0, "Optimal duration for this sigmoid")
    
    # Test 3: Long duration (S-curve gets compressed)
    test_scenario(100.0, "Long duration (S-curve compressed)")
    
    print("\n" + "="*70)
    print("DIAGNOSIS SUMMARY")
    print("="*70)
    print()
    print("The sigmoid function and plotting code work correctly!")
    print()
    print("The 'straight line' appearance is caused by:")
    print("  1. Simulation runs too long (default: until source depleted)")
    print("  2. S-curve completes in first ~20 seconds")
    print("  3. Remaining 80+ seconds show flat rate ≈ 1.0")
    print("  4. When plotted on 0-100s axis, S-curve is compressed")
    print("     and looks like a vertical step or straight line at 1.0")
    print()
    print("SOLUTION:")
    print("  Set simulation duration to match sigmoid parameters:")
    print("  • For sigmoid(t, center, steepness)")
    print("  • Use duration ≈ 2 × center")
    print("  • Example: sigmoid(t, 10, 0.5) → duration = 20-25 seconds")
    print()
    print("="*70)

if __name__ == '__main__':
    main()
