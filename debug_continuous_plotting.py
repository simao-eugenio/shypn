#!/usr/bin/env python3
"""Debug script to test continuous transition plotting.

This script simulates the data flow for continuous transitions
to identify where the plotting issue occurs.
"""

# Simulate data collection for continuous transitions
print("=" * 60)
print("DEBUG: Continuous Transition Plotting")
print("=" * 60)

# Scenario: P1 --[T1:continuous]--> P2
# P1 starts with 100 tokens
# T1 has rate = 10.0 tokens/second
# Time step = 0.1s
# Expected: P1 loses 1.0 tokens/step, P2 gains 1.0 tokens/step

place_data = {
    1: [],  # P1 (source)
    2: []   # P2 (target)
}

time = 0.0
p1_tokens = 100.0
p2_tokens = 0.0
dt = 0.1
rate = 10.0

print(f"\nInitial State:")
print(f"  P1: {p1_tokens} tokens")
print(f"  P2: {p2_tokens} tokens")
print(f"  Rate: {rate} tokens/s")
print(f"  Time step: {dt}s")
print(f"  Expected flow per step: {rate * dt} tokens\n")

# Simulate 10 steps
for step in range(10):
    # Continuous transition integrates
    flow = rate * dt
    p1_tokens -= flow
    p2_tokens += flow
    time += dt
    
    # Data collector records place tokens
    place_data[1].append((time, p1_tokens))
    place_data[2].append((time, p2_tokens))
    
    print(f"Step {step+1} (t={time:.1f}s): P1={p1_tokens:.1f}, P2={p2_tokens:.1f}, flow={flow}")

print(f"\nCollected Data:")
print(f"  P1 data points: {len(place_data[1])}")
print(f"  P2 data points: {len(place_data[2])}")

# Now simulate rate calculation
print(f"\nRate Calculation (time_window=0.1s):")

for place_id, data in place_data.items():
    if len(data) < 2:
        continue
    
    place_name = f"P{place_id}"
    print(f"\n{place_name} rates:")
    
    for i in range(1, len(data)):
        current_time = data[i][0]
        
        # Find points within time window
        time_window = 0.1
        recent = [(t, tokens) for t, tokens in data if current_time - t <= time_window]
        
        if len(recent) < 2:
            continue
        
        # Calculate rate
        dt_calc = recent[-1][0] - recent[0][0]
        dtokens = recent[-1][1] - recent[0][1]
        rate_calc = dtokens / dt_calc if dt_calc > 0 else 0.0
        
        print(f"  t={current_time:.1f}s: rate={rate_calc:.2f} tokens/s (Δtokens={dtokens:.2f}, Δt={dt_calc:.2f})")

print(f"\n" + "=" * 60)
print("Expected Results:")
print("  P1 rate: -10.0 tokens/s (consumption)")
print("  P2 rate: +10.0 tokens/s (production)")
print("=" * 60)
