#!/usr/bin/env python3
"""Test if long arcs are selectable.

This script tests the contains_point() method on long arcs.
"""

import sys
sys.path.insert(0, 'src')

from shypn.netobjs import Place, Transition, Arc

# Create a simple test: long arc (600px)
p1 = Place(100, 100, 1, "P1")
t1 = Transition(700, 105, 1, "T1")  # 600px away

arc = Arc(p1, t1, "A1", "")

print("=" * 80)
print("LONG ARC HIT DETECTION TEST")
print("=" * 80)
print(f"Arc: {p1.label} ({p1.x}, {p1.y}) → {t1.label} ({t1.x}, {t1.y})")
print(f"Distance: {((t1.x - p1.x)**2 + (t1.y - p1.y)**2)**0.5:.1f}px")
print()

# Test points along the arc
test_points = [
    (100, 100, "Start (source)"),
    (200, 101, "25%"),
    (400, 102.5, "50% (midpoint)"),
    (600, 104, "75%"),
    (700, 105, "End (target)"),
    (400, 112.5, "50% + 10px above (should hit)"),
    (400, 92.5, "50% + 10px below (should hit)"),
    (400, 125, "50% + 22px above (should NOT hit)"),
]

print("Testing hit detection:")
for x, y, label in test_points:
    result = arc.contains_point(x, y)
    status = "✓ HIT" if result else "✗ MISS"
    print(f"  {status}: ({x:.1f}, {y:.1f}) - {label}")

print()
print("=" * 80)
print("If long arcs show '✓ HIT' for midpoint, then hit detection works.")
print("If they show '✗ MISS', there's a bug in contains_point().")
print("=" * 80)
