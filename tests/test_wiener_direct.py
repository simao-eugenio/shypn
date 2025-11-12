#!/usr/bin/env python3
"""Direct test of wiener() in rate expression evaluation."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from shypn.engine.function_catalog import wiener, reset_wiener, FUNCTION_CATALOG

print("=" * 70)
print("WIENER FUNCTION - DIRECT RATE EVALUATION TEST")
print("=" * 70)
print()

# Check wiener is in catalog
if 'wiener' in FUNCTION_CATALOG:
    print("✓ wiener found in FUNCTION_CATALOG")
else:
    print("✗ wiener NOT in FUNCTION_CATALOG!")
    sys.exit(1)

print()
print("Test 1: Direct function calls")
print("-" * 70)

reset_wiener()
for i in range(10):
    t = i * 0.1
    w = wiener(t, amplitude=1.0, dt=0.1)
    print(f"wiener({t:.1f}) = {w:+.6f}")

print()
print("Test 2: Evaluate expression with wiener(time)")
print("-" * 70)

reset_wiener()

# Simulate what continuous_behavior.py does
expr = "1.0 * (1 + 0.1 * wiener(time))"

for i in range(10):
    time_value = i * 0.1
    
    # Build context like continuous_behavior.py does
    context = {
        'time': time_value,
        't': time_value,
    }
    context.update(FUNCTION_CATALOG)
    
    # Evaluate
    try:
        result = eval(expr, {"__builtins__": {}}, context)
        print(f"time={time_value:.1f}  expr={expr}  result={result:.6f}")
    except Exception as e:
        print(f"ERROR at time={time_value:.1f}: {e}")
        break

print()
print("Test 3: Check if results vary")
print("-" * 70)

reset_wiener()
results = []
for i in range(20):
    time_value = i * 0.1
    context = {
        'time': time_value,
    }
    context.update(FUNCTION_CATALOG)
    result = eval("1.0 * (1 + 0.1 * wiener(time))", {"__builtins__": {}}, context)
    results.append(result)

import statistics
mean = statistics.mean(results)
std = statistics.stdev(results)
min_val = min(results)
max_val = max(results)

print(f"Mean: {mean:.6f}")
print(f"Std:  {std:.6f}")
print(f"Min:  {min_val:.6f}")
print(f"Max:  {max_val:.6f}")
print(f"Range: {max_val - min_val:.6f}")

if std > 0.01:
    print("\n✓ wiener() produces variable results")
else:
    print("\n✗ wiener() is NOT producing variation!")

print()
print("=" * 70)
print("TEST COMPLETE")
print("=" * 70)
