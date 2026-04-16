#!/usr/bin/env python3
"""
Test MAPK Oscillations with Timed Transition Delays
Adds explicit delays to negative feedback loop to test if phase separation enables oscillations
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from shypn.core.model import SHPNModel
import matplotlib.pyplot as plt
import numpy as np

# Load base oscillation model
model_path = Path(__file__).parent / "models" / "erk_cascade_oscillation.shy"
model = SHPNModel.load(str(model_path))

print(f"Loaded model: {model.name}")
print(f"Places: {len(model.places)}")
print(f"Transitions: {len(model.transitions)}")

# Find MKP synthesis transition
mkp_synthesis = None
for t in model.transitions:
    if "MKP" in t.name and ("syn" in t.name.lower() or "prod" in t.name.lower()):
        mkp_synthesis = t
        print(f"\nFound MKP synthesis transition: {t.name}")
        break

if not mkp_synthesis:
    print("\nSearching for any MKP-related transition...")
    for t in model.transitions:
        if "MKP" in t.name:
            print(f"  - {t.name}")
            mkp_synthesis = t
            break

if mkp_synthesis:
    # Add explicit delay to MKP synthesis (10-30 seconds to create phase shift)
    print(f"\nOriginal transition type: {mkp_synthesis.transition_type}")
    
    # Try different delay values
    delays = [10.0, 20.0, 30.0]
    
    for delay in delays:
        print(f"\n{'='*60}")
        print(f"Testing with {delay}s delay in MKP synthesis")
        print(f"{'='*60}")
        
        # Set timed transition with delay
        mkp_synthesis.transition_type = "timed"
        mkp_synthesis.delay = delay
        
        # Run simulation
        print(f"Running simulation for 300s...")
        result = model.simulate(
            duration=300.0,
            dt=0.1,
            method="rk4"
        )
        
        # Extract ERK-PP trajectory
        erk_pp_idx = None
        for i, place in enumerate(model.places):
            if "ERK" in place.name and "PP" in place.name or place.name == "ERK_PP":
                erk_pp_idx = i
                break
        
        if erk_pp_idx is not None:
            erk_pp = result[:, erk_pp_idx]
            time = np.arange(0, len(erk_pp) * 0.1, 0.1)[:len(erk_pp)]
            
            # Check for oscillations using FFT
            from scipy.fft import fft, fftfreq
            
            # Remove DC component and compute FFT
            erk_pp_ac = erk_pp - np.mean(erk_pp)
            fft_vals = np.abs(fft(erk_pp_ac))
            freqs = fftfreq(len(erk_pp_ac), 0.1)
            
            # Find dominant frequency (excluding DC)
            positive_freqs = freqs[1:len(freqs)//2]
            positive_fft = fft_vals[1:len(fft_vals)//2]
            
            if len(positive_fft) > 0:
                peak_idx = np.argmax(positive_fft)
                peak_freq = positive_freqs[peak_idx]
                peak_power = positive_fft[peak_idx]
                
                # Check if peak is significant
                mean_power = np.mean(positive_fft)
                snr = peak_power / mean_power if mean_power > 0 else 0
                
                print(f"  Peak frequency: {peak_freq:.4f} Hz (period: {1/peak_freq:.1f}s)")
                print(f"  Peak power: {peak_power:.2f}")
                print(f"  SNR: {snr:.2f}x")
                print(f"  ERK-PP range: [{erk_pp.min():.2f}, {erk_pp.max():.2f}] nM")
                
                if snr > 3.0:  # Significant oscillation
                    print(f"  ✓ OSCILLATIONS DETECTED!")
                    
                    # Plot result
                    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
                    
                    ax1.plot(time, erk_pp, linewidth=2, color='#2E86AB')
                    ax1.set_xlabel('Time (s)')
                    ax1.set_ylabel('ERK-PP (nM)')
                    ax1.set_title(f'MAPK Oscillations with {delay}s MKP Synthesis Delay')
                    ax1.grid(True, alpha=0.3)
                    
                    ax2.plot(positive_freqs, positive_fft, linewidth=2, color='#E63946')
                    ax2.set_xlabel('Frequency (Hz)')
                    ax2.set_ylabel('FFT Magnitude')
                    ax2.set_title('Frequency Spectrum')
                    ax2.axvline(peak_freq, color='gray', linestyle='--', alpha=0.5)
                    ax2.grid(True, alpha=0.3)
                    
                    plt.tight_layout()
                    output_path = Path(__file__).parent / "figures" / f"oscillations_delay_{int(delay)}s.pdf"
                    output_path.parent.mkdir(exist_ok=True)
                    plt.savefig(output_path, dpi=300, bbox_inches='tight')
                    print(f"  Saved figure: {output_path}")
                    plt.close()
                else:
                    print(f"  ✗ No significant oscillations (SNR < 3.0)")
            else:
                print("  Could not analyze frequency spectrum")
        else:
            print("  Could not find ERK-PP in results")
else:
    print("\nERROR: Could not find MKP synthesis transition in model")
    print("Available transitions:")
    for t in model.transitions:
        print(f"  - {t.name}")
