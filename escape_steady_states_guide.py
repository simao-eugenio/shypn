#!/usr/bin/env python3
"""Demonstrate strategies to escape steady states in continuous transitions."""

print("=" * 80)
print("ESCAPING STEADY STATES IN CONTINUOUS PETRI NETS")
print("=" * 80)
print()

print("When continuous transitions reach equilibrium (e.g., P1=0.9, P2=0.1),")
print("the system becomes 'stuck' because inflow = outflow at every place.")
print()
print("Here are 7 strategies to perturb the system and restore dynamics:")
print()

strategies = [
    {
        'rank': 1,
        'name': 'Add Stochastic Noise (Wiener Process)',
        'confidence': 0.95,
        'formula': 'rate * (1 + 0.1 * wiener(t))',
        'description': [
            'Add Brownian motion noise to continuous rates',
            '±10% fluctuation around base rate',
            'Represents molecular noise from finite molecule numbers',
            'Example: rate=1.0 → values between 0.9-1.1 continuously'
        ],
        'biological': 'Stochastic gene expression, finite molecule fluctuations',
        'implementation': 'Use dW = sqrt(dt) * N(0,1) for Wiener increments'
    },
    {
        'rank': 2,
        'name': 'Threshold-Based Switching (Piecewise Functions)',
        'confidence': 0.90,
        'formula': 'if(P1 > 0.5, rate*2, rate*0.5)',
        'description': [
            'Change rate based on substrate concentration thresholds',
            'Double rate above threshold, halve below',
            'Creates non-linear dynamics preventing steady states',
            'Can implement Hill functions for cooperativity'
        ],
        'biological': 'Allosteric regulation, feedback inhibition, ultrasensitivity',
        'implementation': 'Use if/else in rate function: if(place > threshold, high_rate, low_rate)'
    },
    {
        'rank': 3,
        'name': 'Periodic Forcing (Circadian Rhythms)',
        'confidence': 0.85,
        'formula': 'rate * (1 + 0.2 * sin(2*pi*t/24))',
        'description': [
            'Add sinusoidal oscillation with 24-hour period',
            '±20% amplitude variation',
            'Continuously changes parameters preventing equilibrium',
            'Can use different periods (circadian, ultradian, cell cycle)'
        ],
        'biological': 'Circadian clock, cell cycle, metabolic rhythms',
        'implementation': 'Add sin(2*pi*t/period) term to rate function'
    },
    {
        'rank': 4,
        'name': 'Substrate Inhibition (Product Feedback)',
        'confidence': 0.80,
        'formula': 'vmax * S / (km + S + S^2/ki)',
        'description': [
            'High substrate concentration inhibits the reaction',
            'S^2/ki term reduces rate at high [S]',
            'Prevents unlimited accumulation',
            'Can generate oscillations or limit cycles'
        ],
        'biological': 'Phosphofructokinase, hexokinase, many metabolic enzymes',
        'implementation': 'Add S^2/ki term to denominator of Michaelis-Menten'
    },
    {
        'rank': 5,
        'name': 'Time Delays (Transcription Lag)',
        'confidence': 0.75,
        'formula': 'rate * P1(t-delay)',
        'description': [
            'Rate depends on past substrate concentrations',
            'Creates phase lags between cause and effect',
            'Delays can generate oscillations (Hopf bifurcation)',
            'Typical delays: seconds (signaling) to hours (gene expression)'
        ],
        'biological': 'Gene transcription/translation (20min-2hr), transport delays',
        'implementation': 'Store history buffer, lookup P(t-delay)'
    },
    {
        'rank': 6,
        'name': 'Hybrid Modeling (Discrete + Continuous)',
        'confidence': 0.70,
        'formula': 'Mix stochastic (discrete) with continuous',
        'description': [
            'Convert some transitions to stochastic (discrete bursts)',
            'Keep others continuous (smooth flow)',
            'Discrete jumps break perfect balance',
            'Accurate for low-copy-number molecules'
        ],
        'biological': 'Transcription factors (discrete), metabolites (continuous)',
        'implementation': 'Change transition_type from continuous to stochastic'
    },
    {
        'rank': 7,
        'name': 'Pulse Perturbations (External Stimuli)',
        'confidence': 0.65,
        'formula': 'Add tokens periodically or stochastically',
        'description': [
            'Inject token pulses every N time units',
            'Simulates external perturbations',
            'Can be periodic (feeding) or stochastic (stress)',
            'System must accommodate sudden changes'
        ],
        'biological': 'Hormone pulses (insulin, GnRH), feeding cycles, stress',
        'implementation': 'Add pulse source transitions or scheduled token injection'
    }
]

for strat in strategies:
    print(f"#{strat['rank']}. {strat['name']}")
    print(f"   Confidence: {strat['confidence']}")
    print(f"   Formula: {strat['formula']}")
    print()
    print("   How it works:")
    for desc in strat['description']:
        print(f"     • {desc}")
    print()
    print(f"   Biological basis: {strat['biological']}")
    print(f"   Implementation: {strat['implementation']}")
    print()
    print("-" * 80)
    print()

print("=" * 80)
print("RECOMMENDATION FOR YOUR MODEL (test.shy)")
print("=" * 80)
print()
print("For T1 and T2 continuous transitions in a cycle:")
print()
print("BEST APPROACH: Strategy #1 (Stochastic Noise)")
print("  T1 rate: 1.0 * (1 + 0.1 * wiener(t))")
print("  T2 rate: 1.0 * (1 + 0.15 * wiener(t))  # Slightly different noise")
print()
print("This will:")
print("  ✓ Break the exact steady state (P1=0.9, P2=0.1)")
print("  ✓ Create fluctuating dynamics around equilibrium")
print("  ✓ Maintain biological realism (molecular noise)")
print("  ✓ Prevent synchronization (different noise amplitudes)")
print()
print("Alternative: Strategy #3 (Periodic Forcing)")
print("  T1 rate: 1.0 * (1 + 0.2 * sin(2*pi*t/10))")
print("  T2 rate: 1.0 * (1 + 0.2 * sin(2*pi*t/10 + pi/2))  # 90° phase shift")
print()
print("This creates oscillating behavior with a 10-second period.")
print()
