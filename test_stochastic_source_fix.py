#!/usr/bin/env python3
"""
Test script to verify stochastic source transition fixes.

This script creates a minimal Petri net with a stochastic source transition
and verifies that it fires continuously as expected (Poisson process).

Test net structure:
    [Source] ---> (P1)
    
Where [Source] is a stochastic transition with:
- is_source = True (no input places)
- rate = 2.0 (λ = 2.0 events/sec)
- Expected: ~2 firings per second on average
- Expected: Inter-arrival times follow Exp(2.0) distribution

Test verifies:
1. Source fires multiple times (not just once)
2. Tokens accumulate in P1 over time
3. Average firing rate ≈ 2.0 firings/sec
4. Inter-arrival times roughly match exponential distribution
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))

from shypn.netobjs.place import Place
from shypn.netobjs.transition import Transition
from shypn.netobjs.arc import Arc
from shypn.data.model_canvas_manager import ModelCanvasManager
from shypn.engine.simulation.controller import SimulationController
from shypn.engine.simulation.settings import SimulationSettings
import statistics


def create_test_net():
    """Create a simple stochastic source transition test net."""
    # Create canvas manager (no canvas needed for headless test)
    manager = ModelCanvasManager(canvas_width=400, canvas_height=400, filename="test_source")
    
    # Create place to receive tokens
    p1 = manager.add_place(x=200, y=100)
    p1.tokens = 0  # Start empty
    
    # Create source transition (stochastic)
    t_source = manager.add_transition(x=100, y=100)
    t_source.is_source = True
    t_source.transition_type = 'stochastic'
    
    # Create output arc (Source -> P1)
    manager.add_arc(t_source, p1)
    
    return manager


def run_test(duration=10.0, rate=2.0):
    """Run the stochastic source test.
    
    Args:
        duration: Simulation duration in seconds
        rate: Stochastic rate parameter (λ)
        
    Returns:
        dict with test results
    """
    print("=" * 70)
    print("STOCHASTIC SOURCE TRANSITION FIX TEST")
    print("=" * 70)
    print(f"\nTest Parameters:")
    print(f"  Duration: {duration} seconds")
    print(f"  Rate (λ): {rate} events/sec")
    print(f"  Expected firings: ~{duration * rate} (±{(duration * rate)**0.5:.1f} stdev)")
    print(f"  Expected inter-arrival: ~{1/rate:.3f} sec")
    print()
    
    # Create test net
    manager = create_test_net()
    
    # Get objects directly from manager
    p1 = manager.places[0]  # First place
    t_source = manager.transitions[0]  # First transition
    
    # Create controller
    controller = SimulationController(manager)
    
    # Configure simulation settings
    controller.settings.duration = duration
    controller.settings.dt_mode = 'automatic'  # dt = duration / 1000
    
    # Set rate directly on transition
    t_source.rate = rate
    
    # Track firing times
    firing_times = []
    last_tokens = 0
    
    print("Running simulation...")
    print(f"Time: 0.0s | P1 tokens: 0 | Firings: 0")
    
    # Run simulation with callbacks to track firings
    step_count = 0
    while controller.time < duration:
        # Execute one simulation step
        controller.step()
        step_count += 1
        
        # Check if tokens increased (transition fired)
        current_tokens = p1.tokens
        
        if current_tokens > last_tokens:
            # Transition fired!
            firing_times.append(controller.time)
            if len(firing_times) <= 10 or len(firing_times) % 5 == 0:
                print(f"Time: {controller.time:.3f}s | P1 tokens: {current_tokens} | Firings: {len(firing_times)}")
            last_tokens = current_tokens
    
    # Final results
    final_tokens = p1.tokens
    num_firings = len(firing_times)
    
    print(f"\n{'=' * 70}")
    print("TEST RESULTS")
    print(f"{'=' * 70}")
    print(f"\nSimulation completed:")
    print(f"  Duration: {duration} seconds")
    print(f"  Steps executed: {step_count}")
    print(f"  Final time: {controller.time:.3f} seconds")
    print()
    print(f"Firing statistics:")
    print(f"  Total firings: {num_firings}")
    print(f"  Final tokens in P1: {final_tokens}")
    print(f"  Average firing rate: {num_firings / duration:.2f} events/sec")
    print(f"  Expected rate (λ): {rate} events/sec")
    print(f"  Deviation: {abs(num_firings / duration - rate) / rate * 100:.1f}%")
    print()
    
    # Calculate inter-arrival times
    if len(firing_times) >= 2:
        inter_arrivals = [firing_times[i] - firing_times[i-1] 
                         for i in range(1, len(firing_times))]
        mean_interval = statistics.mean(inter_arrivals)
        expected_interval = 1.0 / rate
        
        print(f"Inter-arrival time statistics:")
        print(f"  Mean: {mean_interval:.3f} seconds")
        print(f"  Expected (1/λ): {expected_interval:.3f} seconds")
        print(f"  Deviation: {abs(mean_interval - expected_interval) / expected_interval * 100:.1f}%")
        print(f"  Min: {min(inter_arrivals):.3f} seconds")
        print(f"  Max: {max(inter_arrivals):.3f} seconds")
        if len(inter_arrivals) >= 3:
            print(f"  Std dev: {statistics.stdev(inter_arrivals):.3f} seconds")
        print()
    
    # Test verdict
    print(f"{'=' * 70}")
    print("TEST VERDICT")
    print(f"{'=' * 70}")
    
    passed = True
    issues = []
    
    # Check 1: Multiple firings
    if num_firings < 2:
        passed = False
        issues.append(f"❌ FAIL: Only {num_firings} firing(s) - source not continuous!")
    else:
        print(f"✅ PASS: Multiple firings ({num_firings}) - source is continuous")
    
    # Check 2: Token accumulation
    if final_tokens != num_firings:
        passed = False
        issues.append(f"❌ FAIL: Token mismatch (tokens={final_tokens}, firings={num_firings})")
    else:
        print(f"✅ PASS: Token accumulation matches firings ({final_tokens})")
    
    # Check 3: Firing rate within 30% of expected (allowing for stochastic variance)
    actual_rate = num_firings / duration
    rate_error = abs(actual_rate - rate) / rate
    if rate_error > 0.3:  # 30% tolerance
        passed = False
        issues.append(f"❌ FAIL: Firing rate deviation too large ({rate_error*100:.1f}%)")
    else:
        print(f"✅ PASS: Firing rate within tolerance ({rate_error*100:.1f}% deviation)")
    
    # Check 4: Inter-arrival time reasonable
    if len(inter_arrivals) >= 2:
        interval_error = abs(mean_interval - expected_interval) / expected_interval
        if interval_error > 0.3:  # 30% tolerance
            passed = False
            issues.append(f"❌ FAIL: Inter-arrival time deviation too large ({interval_error*100:.1f}%)")
        else:
            print(f"✅ PASS: Inter-arrival time within tolerance ({interval_error*100:.1f}% deviation)")
    
    print()
    if passed:
        print("🎉 ALL TESTS PASSED - Stochastic source transitions working correctly!")
    else:
        print("❌ TESTS FAILED:")
        for issue in issues:
            print(f"   {issue}")
    
    print(f"{'=' * 70}\n")
    
    return {
        'passed': passed,
        'num_firings': num_firings,
        'final_tokens': final_tokens,
        'firing_rate': actual_rate,
        'expected_rate': rate,
        'firing_times': firing_times,
        'issues': issues
    }


if __name__ == '__main__':
    # Run test with default parameters
    result = run_test(duration=10.0, rate=2.0)
    
    # Exit with appropriate code
    sys.exit(0 if result['passed'] else 1)
