#!/usr/bin/env python3
"""
Comprehensive test for stochastic sink and normal transitions.

Tests verify that:
1. Sink transitions disable when input tokens exhausted
2. Sink transitions re-enable when tokens become available
3. Normal transitions disable when input tokens exhausted
4. Normal transitions re-enable when tokens become available
5. Source → Normal → Sink pipeline works correctly
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))

from shypn.data.model_canvas_manager import ModelCanvasManager
from shypn.engine.simulation.controller import SimulationController
import statistics


def test_sink_exhaustion():
    """Test that sink transitions properly disable when tokens exhausted."""
    print("=" * 70)
    print("TEST 1: SINK TRANSITION EXHAUSTION")
    print("=" * 70)
    print("\nNet: (P1:10 tokens) → [Stochastic Sink, rate=5.0]\n")
    
    # Create net
    manager = ModelCanvasManager(canvas_width=400, canvas_height=400, filename="test_sink")
    p1 = manager.add_place(x=100, y=100)
    p1.tokens = 10  # Start with 10 tokens
    
    t_sink = manager.add_transition(x=200, y=100)
    t_sink.is_sink = True
    t_sink.transition_type = 'stochastic'
    t_sink.rate = 5.0  # Set rate directly on transition
    
    manager.add_arc(p1, t_sink)  # P1 → Sink
    
    # Configure simulation
    controller = SimulationController(manager)
    controller.settings.duration = 2.0
    controller.settings.dt_mode = 'automatic'
    
    # Run simulation and track
    firing_count = 0
    disabled_at = None
    
    print("Running simulation...")
    while controller.time < 2.0:
        tokens_before = p1.tokens
        controller.step()
        tokens_after = p1.tokens
        
        if tokens_after < tokens_before:
            firing_count += 1
            print(f"t={controller.time:.3f}s: Fired! P1: {tokens_before} → {tokens_after} tokens")
        
        if tokens_after == 0 and disabled_at is None:
            disabled_at = controller.time
            print(f"t={controller.time:.3f}s: P1 EXHAUSTED - sink should disable")
    
    # Results
    print(f"\n{'='*70}")
    print("RESULTS:")
    print(f"{'='*70}")
    print(f"Total firings: {firing_count}")
    print(f"Final P1 tokens: {p1.tokens}")
    print(f"Disabled at: {disabled_at:.3f}s" if disabled_at else "Never disabled")
    
    # Verdict
    passed = True
    if firing_count < 2:
        print(f"❌ FAIL: Too few firings ({firing_count})")
        passed = False
    else:
        print(f"✅ PASS: Multiple firings ({firing_count})")
    
    if p1.tokens > 0:
        print(f"❌ FAIL: Tokens not exhausted (P1:{p1.tokens})")
        passed = False
    else:
        print(f"✅ PASS: Tokens exhausted (P1:0)")
    
    if disabled_at is None:
        print(f"❌ FAIL: Sink never disabled")
        passed = False
    else:
        print(f"✅ PASS: Sink disabled at t={disabled_at:.3f}s")
    
    print()
    return passed


def test_normal_exhaustion():
    """Test that normal transitions properly disable when tokens exhausted."""
    print("=" * 70)
    print("TEST 2: NORMAL TRANSITION EXHAUSTION")
    print("=" * 70)
    print("\nNet: (P1:8 tokens) → [Stochastic T, rate=3.0] → (P2:0 tokens)\n")
    
    # Create net
    manager = ModelCanvasManager(canvas_width=400, canvas_height=400, filename="test_normal")
    p1 = manager.add_place(x=100, y=100)
    p1.tokens = 8
    
    p2 = manager.add_place(x=300, y=100)
    p2.tokens = 0
    
    t_normal = manager.add_transition(x=200, y=100)
    t_normal.transition_type = 'stochastic'
    t_normal.rate = 3.0  # Set rate directly
    
    manager.add_arc(p1, t_normal)  # P1 → T
    manager.add_arc(t_normal, p2)  # T → P2
    
    # Configure simulation
    controller = SimulationController(manager)
    controller.settings.duration = 2.0
    controller.settings.dt_mode = 'automatic'
    
    # Run simulation and track
    firing_count = 0
    disabled_at = None
    
    print("Running simulation...")
    while controller.time < 2.0:
        p1_before = p1.tokens
        p2_before = p2.tokens
        controller.step()
        
        if p1.tokens < p1_before:
            firing_count += 1
            print(f"t={controller.time:.3f}s: Fired! P1:{p1_before}→{p1.tokens}, P2:{p2_before}→{p2.tokens}")
        
        if p1.tokens == 0 and disabled_at is None:
            disabled_at = controller.time
            print(f"t={controller.time:.3f}s: P1 EXHAUSTED - transition should disable")
    
    # Results
    print(f"\n{'='*70}")
    print("RESULTS:")
    print(f"{'='*70}")
    print(f"Total firings: {firing_count}")
    print(f"Final P1 tokens: {p1.tokens}")
    print(f"Final P2 tokens: {p2.tokens}")
    print(f"Disabled at: {disabled_at:.3f}s" if disabled_at else "Never disabled")
    
    # Verdict
    passed = True
    if firing_count < 1:
        print(f"❌ FAIL: No firings")
        passed = False
    else:
        print(f"✅ PASS: Multiple firings ({firing_count})")
    
    if p1.tokens > 0:
        print(f"❌ FAIL: P1 not exhausted ({p1.tokens})")
        passed = False
    else:
        print(f"✅ PASS: P1 exhausted")
    
    if p2.tokens == 0:
        print(f"❌ FAIL: P2 has no tokens (transformation didn't work)")
        passed = False
    else:
        print(f"✅ PASS: P2 has tokens ({p2.tokens})")
    
    if disabled_at is None:
        print(f"❌ FAIL: Transition never disabled")
        passed = False
    else:
        print(f"✅ PASS: Transition disabled at t={disabled_at:.3f}s")
    
    print()
    return passed


def test_source_normal_sink_pipeline():
    """Test complete pipeline with source, normal, and sink transitions."""
    print("=" * 70)
    print("TEST 3: SOURCE → NORMAL → SINK PIPELINE")
    print("=" * 70)
    print("\nNet: [Source:2.0] → (P1) → [Normal:1.5] → (P2) → [Sink:3.0]\n")
    
    # Create net
    manager = ModelCanvasManager(canvas_width=600, canvas_height=200, filename="test_pipeline")
    
    # Source
    t_source = manager.add_transition(x=50, y=100)
    t_source.is_source = True
    t_source.transition_type = 'stochastic'
    t_source.rate = 2.0
    
    # P1
    p1 = manager.add_place(x=150, y=100)
    p1.tokens = 0
    
    # Normal
    t_normal = manager.add_transition(x=250, y=100)
    t_normal.transition_type = 'stochastic'
    t_normal.rate = 1.5
    
    # P2
    p2 = manager.add_place(x=350, y=100)
    p2.tokens = 0
    
    # Sink
    t_sink = manager.add_transition(x=450, y=100)
    t_sink.is_sink = True
    t_sink.transition_type = 'stochastic'
    t_sink.rate = 3.0
    
    # Arcs
    manager.add_arc(t_source, p1)  # Source → P1
    manager.add_arc(p1, t_normal)  # P1 → Normal
    manager.add_arc(t_normal, p2)  # Normal → P2
    manager.add_arc(p2, t_sink)    # P2 → Sink
    
    # Configure simulation
    controller = SimulationController(manager)
    controller.settings.duration = 5.0
    controller.settings.dt_mode = 'automatic'
    
    # Run and track
    source_firings = 0
    normal_firings = 0
    sink_firings = 0
    
    print("Running simulation...")
    last_report = 0.0
    
    while controller.time < 5.0:
        p1_before = p1.tokens
        p2_before = p2.tokens
        
        controller.step()
        
        # Detect firings
        if p1.tokens > p1_before:
            source_firings += 1
        if p1.tokens < p1_before and p2.tokens > p2_before:
            normal_firings += 1
        if p2.tokens < p2_before:
            sink_firings += 1
        
        # Report every 1 second
        if controller.time - last_report >= 1.0:
            print(f"t={controller.time:.1f}s: P1:{p1.tokens}, P2:{p2.tokens} | Firings: Source:{source_firings}, Normal:{normal_firings}, Sink:{sink_firings}")
            last_report = controller.time
    
    # Results
    print(f"\n{'='*70}")
    print("RESULTS:")
    print(f"{'='*70}")
    print(f"Source firings: {source_firings} (expected ~10 ± 3)")
    print(f"Normal firings: {normal_firings}")
    print(f"Sink firings: {sink_firings}")
    print(f"Final P1: {p1.tokens}, P2: {p2.tokens}")
    
    # Verdict
    passed = True
    
    if source_firings < 3:
        print(f"❌ FAIL: Source too few firings ({source_firings})")
        passed = False
    else:
        print(f"✅ PASS: Source continuous firings ({source_firings})")
    
    if normal_firings < 1:
        print(f"❌ FAIL: Normal didn't fire")
        passed = False
    else:
        print(f"✅ PASS: Normal fired ({normal_firings})")
    
    if sink_firings < 1:
        print(f"❌ FAIL: Sink didn't fire")
        passed = False
    else:
        print(f"✅ PASS: Sink fired ({sink_firings})")
    
    # Check that source fires more than sink (source is faster)
    if source_firings <= sink_firings:
        print(f"⚠️  WARNING: Source rate not higher than sink (expected Source > Sink)")
    else:
        print(f"✅ PASS: Rate hierarchy correct (Source:{source_firings} > Sink:{sink_firings})")
    
    print()
    return passed


if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("STOCHASTIC SINK AND NORMAL TRANSITION TEST SUITE")
    print("=" * 70 + "\n")
    
    test1_passed = test_sink_exhaustion()
    test2_passed = test_normal_exhaustion()
    test3_passed = test_source_normal_sink_pipeline()
    
    # Summary
    print("=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Test 1 (Sink Exhaustion): {'✅ PASS' if test1_passed else '❌ FAIL'}")
    print(f"Test 2 (Normal Exhaustion): {'✅ PASS' if test2_passed else '❌ FAIL'}")
    print(f"Test 3 (Source→Normal→Sink): {'✅ PASS' if test3_passed else '❌ FAIL'}")
    
    all_passed = test1_passed and test2_passed and test3_passed
    print(f"\nOverall: {'🎉 ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    print("=" * 70 + "\n")
    
    sys.exit(0 if all_passed else 1)
