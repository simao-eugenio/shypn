#!/usr/bin/env python3
"""
Test script to demonstrate debug logging of arc type behavior during simulation.

Run with: python test_arc_debug_logging.py

This will show detailed traces of:
- Arc type detection during enablement checks
- Token consumption decisions (skip vs consume)
- Actual token consumption amounts
"""

import sys
sys.path.insert(0, 'src')

import logging

# Configure logging to show DEBUG messages
logging.basicConfig(
    level=logging.DEBUG,
    format='%(levelname)s [%(name)s] %(message)s'
)

from shypn.data.canvas.document_model import DocumentModel
from shypn.netobjs import Place, Transition, Arc
from shypn.netobjs.test_arc import TestArc
from shypn.netobjs.inhibitor_arc import InhibitorArc
from shypn.engine.immediate_behavior import ImmediateBehavior

print("=" * 80)
print("ARC TYPE DEBUG LOGGING TEST")
print("=" * 80)

# ============================================================================
# TEST 1: Normal Arc (should consume)
# ============================================================================
print("\n" + "=" * 80)
print("TEST 1: Normal Arc (should consume tokens)")
print("=" * 80)

doc1 = DocumentModel()
p1 = Place(id='P1', name='P1', x=100, y=100)
p1.tokens = 10
p2 = Place(id='P2', name='P2', x=300, y=100)
p2.tokens = 0
t1 = Transition(id='T1', name='T1', x=200, y=100)
t1.transition_type = 'immediate'

arc_normal_in = Arc(source=p1, target=t1, id='A1', name='NormalArc', weight=3)
arc_normal_out = Arc(source=t1, target=p2, id='A2', name='Output', weight=1)

doc1.arcs = [arc_normal_in, arc_normal_out]
doc1.places = [p1, p2]
doc1.transitions = [t1]

print(f"\nInitial: P1={p1.tokens}, P2={p2.tokens}")
print(f"Arc: {type(arc_normal_in).__name__}, weight={arc_normal_in.weight}")

behavior1 = ImmediateBehavior(t1, doc1)

print("\n--- Checking Enablement ---")
enabled, reason = behavior1.can_fire()
print(f"Enabled: {enabled}, Reason: {reason}")

print("\n--- Firing Transition ---")
success, result = behavior1.fire(behavior1.get_input_arcs(), behavior1.get_output_arcs())

print(f"\nFinal: P1={p1.tokens}, P2={p2.tokens}")
print(f"Expected: P1=7 (10-3), P2=1")

# ============================================================================
# TEST 2: Test Arc (should NOT consume)
# ============================================================================
print("\n" + "=" * 80)
print("TEST 2: Test Arc (should NOT consume tokens)")
print("=" * 80)

doc2 = DocumentModel()
p3 = Place(id='P3', name='P3', x=100, y=100)
p3.tokens = 10
p4 = Place(id='P4', name='P4', x=300, y=100)
p4.tokens = 0
t2 = Transition(id='T2', name='T2', x=200, y=100)
t2.transition_type = 'immediate'

arc_test_in = TestArc(source=p3, target=t2, id='A3', name='TestArc', weight=3)
arc_test_out = Arc(source=t2, target=p4, id='A4', name='Output', weight=1)

doc2.arcs = [arc_test_in, arc_test_out]
doc2.places = [p3, p4]
doc2.transitions = [t2]

print(f"\nInitial: P3={p3.tokens}, P4={p4.tokens}")
print(f"Arc: {type(arc_test_in).__name__}, weight={arc_test_in.weight}")

behavior2 = ImmediateBehavior(t2, doc2)

print("\n--- Checking Enablement ---")
enabled, reason = behavior2.can_fire()
print(f"Enabled: {enabled}, Reason: {reason}")

print("\n--- Firing Transition ---")
success, result = behavior2.fire(behavior2.get_input_arcs(), behavior2.get_output_arcs())

print(f"\nFinal: P3={p3.tokens}, P4={p4.tokens}")
print(f"Expected: P3=10 (unchanged), P4=1")

# ============================================================================
# TEST 3: Inhibitor Arc (should NOT consume)
# ============================================================================
print("\n" + "=" * 80)
print("TEST 3: Inhibitor Arc (should NOT consume tokens)")
print("=" * 80)

doc3 = DocumentModel()
p5 = Place(id='P5', name='P5', x=100, y=100)
p5.tokens = 2  # Below threshold
p6 = Place(id='P6', name='P6', x=300, y=100)
p6.tokens = 0
t3 = Transition(id='T3', name='T3', x=200, y=100)
t3.transition_type = 'immediate'

arc_inh_in = InhibitorArc(source=p5, target=t3, id='A5', name='InhibitorArc', weight=5)
arc_inh_out = Arc(source=t3, target=p6, id='A6', name='Output', weight=1)

doc3.arcs = [arc_inh_in, arc_inh_out]
doc3.places = [p5, p6]
doc3.transitions = [t3]

print(f"\nInitial: P5={p5.tokens}, P6={p6.tokens}")
print(f"Arc: {type(arc_inh_in).__name__}, threshold={arc_inh_in.weight}")
print(f"Note: Inhibitor fires when tokens < threshold (2 < 5, so enabled)")

behavior3 = ImmediateBehavior(t3, doc3)

print("\n--- Checking Enablement ---")
enabled, reason = behavior3.can_fire()
print(f"Enabled: {enabled}, Reason: {reason}")

print("\n--- Firing Transition ---")
success, result = behavior3.fire(behavior3.get_input_arcs(), behavior3.get_output_arcs())

print(f"\nFinal: P5={p5.tokens}, P6={p6.tokens}")
print(f"Expected: P5=2 (unchanged), P6=1")

# ============================================================================
# TEST 4: Mixed Arcs (Normal + Test)
# ============================================================================
print("\n" + "=" * 80)
print("TEST 4: Mixed Arcs (Normal arc + Test arc)")
print("=" * 80)

doc4 = DocumentModel()
p7 = Place(id='P7', name='Substrate', x=50, y=100)
p7.tokens = 10
p8 = Place(id='P8', name='Enzyme', x=150, y=50)
p8.tokens = 5
p9 = Place(id='P9', name='Product', x=300, y=100)
p9.tokens = 0
t4 = Transition(id='T4', name='Reaction', x=200, y=100)
t4.transition_type = 'immediate'

arc_substrate = Arc(source=p7, target=t4, id='A7', name='Substrate', weight=2)  # Normal - consumes
arc_enzyme = TestArc(source=p8, target=t4, id='A8', name='Enzyme', weight=1)  # Test - catalyst
arc_product = Arc(source=t4, target=p9, id='A9', name='Product', weight=1)

doc4.arcs = [arc_substrate, arc_enzyme, arc_product]
doc4.places = [p7, p8, p9]
doc4.transitions = [t4]

print(f"\nInitial: Substrate={p7.tokens}, Enzyme={p8.tokens}, Product={p9.tokens}")
print(f"Substrate arc: {type(arc_substrate).__name__}, weight={arc_substrate.weight}")
print(f"Enzyme arc: {type(arc_enzyme).__name__}, weight={arc_enzyme.weight}")

behavior4 = ImmediateBehavior(t4, doc4)

print("\n--- Checking Enablement ---")
enabled, reason = behavior4.can_fire()
print(f"Enabled: {enabled}, Reason: {reason}")

print("\n--- Firing Transition ---")
success, result = behavior4.fire(behavior4.get_input_arcs(), behavior4.get_output_arcs())

print(f"\nFinal: Substrate={p7.tokens}, Enzyme={p8.tokens}, Product={p9.tokens}")
print(f"Expected: Substrate=8 (10-2), Enzyme=5 (unchanged), Product=1")

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "=" * 80)
print("DEBUG LOGGING SUMMARY")
print("=" * 80)
print("""
The debug logs show:
1. [ENABLEMENT] - Arc type detection during enablement checks
2. [IMMEDIATE FIRE] - Arc type detection during token consumption
3. → SKIP consumption - When test/inhibitor arcs are skipped
4. → CONSUMED - Actual token consumption with amounts

To enable debug logging in your application:
    import logging
    logging.basicConfig(level=logging.DEBUG)

To filter only arc-related logs:
    logging.getLogger('shypn.engine').setLevel(logging.DEBUG)
""")
