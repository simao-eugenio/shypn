#!/usr/bin/env python3
"""Test Example 07 equilibrium behavior for PGI reaction."""

import json
import sys
sys.path.insert(0, '/home/simao/projetos/shypn/src')

from shypn.netobjs.model import Model

# Load Example 07
model_path = '/home/simao/projetos/shypn/workspace/projects/Biochemical-Examples/07_Upper_Glycolysis_Pathway/model.shy'
with open(model_path, 'r') as f:
    data = json.load(f)

model = Model.from_dict(data)

# Get initial state
print("=== Initial State ===")
for place in model.places:
    if place.id in ['P1', 'P2', 'P3', 'P4']:
        print(f"{place.name} ({place.id}): {place.marking:.4f} mM")

print("\n=== Transition T2 (PGI) ===")
t2 = model.get_transition('T2')
print(f"Type: {t2.transition_type}")
print(f"Rate forward: {getattr(t2, 'rate_forward', 'NOT SET')}")
print(f"Rate reverse: {getattr(t2, 'rate_reverse', 'NOT SET')}")
print(f"Regular rate: {getattr(t2, 'rate', 'NOT SET')}")

# Check the behavior
from shypn.engine.continuous_behavior import ContinuousBehavior
behavior = ContinuousBehavior(t2, model)

print(f"\nUse directional rates: {behavior.use_directional_rates}")

# Test rate calculation at initial state
places_dict = {p.name: p.marking for p in model.places}
print(f"\nPlaces dict: {places_dict}")

rate_fwd = behavior.rate_forward_function(places_dict, 0)
rate_rev = behavior.rate_reverse_function(places_dict, 0)
net_rate = behavior.rate_function(places_dict, 0)

print(f"\nRate forward (0.41 * G6P): {rate_fwd:.6f}")
print(f"Rate reverse (0.14 * F6P): {rate_rev:.6f}")
print(f"Net rate (fwd - rev): {net_rate:.6f}")

# Calculate expected equilibrium
# At equilibrium: rate_fwd = rate_rev
# 0.41 * G6P = 0.14 * F6P
# G6P / F6P = 0.14 / 0.41 = 0.341
# Expected: F6P / G6P = 0.41 / 0.14 = 2.93
print(f"\n=== Expected Equilibrium ===")
print(f"F6P / G6P should reach: {0.41 / 0.14:.3f}")
print(f"Current F6P / G6P: {places_dict['F6P'] / places_dict['G6P']:.3f}")

# Simulate for a while
print("\n=== Running Simulation ===")
from shypn.engine.simulation_engine import SimulationEngine

engine = SimulationEngine(model)
engine.reset()

# Run to steady state
times = [0, 10, 20, 50, 100, 200]
for t in times:
    engine.run_until(t)
    p2 = model.get_place('P2').marking
    p3 = model.get_place('P3').marking
    ratio = p3 / p2 if p2 > 0 else 0
    print(f"t={t:3.0f}s: G6P={p2:.6f}, F6P={p3:.6f}, F6P/G6P={ratio:.3f}")
