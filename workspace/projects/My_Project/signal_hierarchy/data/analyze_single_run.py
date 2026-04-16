#!/usr/bin/env python3
"""
Analyze a single simulation run from Lambda Phage model.
Plots time courses and phase portrait to assess bistability outcome.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

def analyze_single_run(csv_file):
    """Analyze a single simulation run."""
    
    csv_path = Path(csv_file)
    if not csv_path.exists():
        print(f"Error: File not found: {csv_file}")
        return
    
    print(f"Analyzing: {csv_file}")
    print("=" * 70)
    
    # Load data
    df = pd.read_csv(csv_file)
    
    # Display basic info
    print(f"Duration: {df['Time (s)'].min():.2f} - {df['Time (s)'].max():.2f} seconds")
    print(f"Time points: {len(df)}")
    print()
    
    # Extract key species
    time = df['Time (s)']
    ci_dimer = df['CI_Dimer (mM)']
    cro_dimer = df['Cro_Dimer (mM)']
    
    # Final state
    ci_final = ci_dimer.iloc[-1]
    cro_final = cro_dimer.iloc[-1]
    
    print("FINAL STATE (t=1000s)")
    print("-" * 70)
    print(f"CI_Dimer:  {ci_final:.2f} molecules")
    print(f"Cro_Dimer: {cro_final:.2f} molecules")
    print()
    
    # Classify outcome
    ci_threshold = 40
    cro_threshold = 40
    
    if ci_final > ci_threshold and cro_final < ci_threshold:
        outcome = "LYSOGENIC"
        outcome_desc = "CI repressor dominates (prophage integrated)"
    elif cro_final > cro_threshold and ci_final < ci_threshold:
        outcome = "LYTIC"
        outcome_desc = "Cro dominates (lytic pathway active)"
    else:
        outcome = "UNDECIDED"
        outcome_desc = "Both CI and Cro at intermediate levels"
    
    print(f"OUTCOME: {outcome}")
    print(f"  {outcome_desc}")
    print()
    
    # Statistics
    print("TIME COURSE STATISTICS")
    print("-" * 70)
    print(f"CI_Dimer:")
    print(f"  Mean ± SD: {ci_dimer.mean():.2f} ± {ci_dimer.std():.2f}")
    print(f"  Range: [{ci_dimer.min():.2f}, {ci_dimer.max():.2f}]")
    print()
    print(f"Cro_Dimer:")
    print(f"  Mean ± SD: {cro_dimer.mean():.2f} ± {cro_dimer.std():.2f}")
    print(f"  Range: [{cro_dimer.min():.2f}, {cro_dimer.max():.2f}]")
    print()
    
    # Check for other recorded species
    place_cols = [col for col in df.columns if col.endswith('(mM)') and 'CI_Dimer' not in col and 'Cro_Dimer' not in col]
    if place_cols:
        print("OTHER RECORDED SPECIES")
        print("-" * 70)
        for col in place_cols[:5]:  # Show first 5
            species_name = col.replace(' (mM)', '')
            final_val = df[col].iloc[-1]
            print(f"{species_name}: {final_val:.2f}")
        if len(place_cols) > 5:
            print(f"  ... and {len(place_cols) - 5} more")
        print()
    
    # Create visualization
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # 1. CI_Dimer time course
    ax = axes[0, 0]
    ax.plot(time, ci_dimer, 'g-', linewidth=1.5, label='CI_Dimer')
    ax.axhline(ci_threshold, color='gray', linestyle='--', alpha=0.5, label='Threshold')
    ax.set_xlabel('Time (seconds)', fontsize=11)
    ax.set_ylabel('CI_Dimer (molecules)', fontsize=11)
    ax.set_title('CI Repressor Time Course', fontsize=12, fontweight='bold')
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3)
    
    # 2. Cro_Dimer time course
    ax = axes[0, 1]
    ax.plot(time, cro_dimer, 'r-', linewidth=1.5, label='Cro_Dimer')
    ax.axhline(cro_threshold, color='gray', linestyle='--', alpha=0.5, label='Threshold')
    ax.set_xlabel('Time (seconds)', fontsize=11)
    ax.set_ylabel('Cro_Dimer (molecules)', fontsize=11)
    ax.set_title('Cro Repressor Time Course', fontsize=12, fontweight='bold')
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3)
    
    # 3. Both on same plot
    ax = axes[1, 0]
    ax.plot(time, ci_dimer, 'g-', linewidth=1.5, label='CI_Dimer', alpha=0.8)
    ax.plot(time, cro_dimer, 'r-', linewidth=1.5, label='Cro_Dimer', alpha=0.8)
    ax.axhline(40, color='gray', linestyle='--', alpha=0.3)
    ax.set_xlabel('Time (seconds)', fontsize=11)
    ax.set_ylabel('Molecules', fontsize=11)
    ax.set_title('Competition Dynamics (CI vs Cro)', fontsize=12, fontweight='bold')
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3)
    
    # 4. Phase portrait
    ax = axes[1, 1]
    
    # Color by time (early = blue, late = red)
    n_points = len(time)
    colors = plt.cm.viridis(np.linspace(0, 1, n_points))
    
    for i in range(n_points - 1):
        ax.plot(ci_dimer.iloc[i:i+2], cro_dimer.iloc[i:i+2], 
               color=colors[i], linewidth=0.5, alpha=0.6)
    
    # Mark start and end
    ax.scatter(ci_dimer.iloc[0], cro_dimer.iloc[0], 
              c='blue', s=100, marker='o', edgecolors='black', linewidths=2, 
              label='Start', zorder=5)
    ax.scatter(ci_dimer.iloc[-1], cro_dimer.iloc[-1], 
              c='red', s=100, marker='s', edgecolors='black', linewidths=2, 
              label='End', zorder=5)
    
    # Mark thresholds
    ax.axvline(ci_threshold, color='green', linestyle='--', alpha=0.3)
    ax.axhline(cro_threshold, color='red', linestyle='--', alpha=0.3)
    
    # Shade regions
    ax.axvspan(ci_threshold, ax.get_xlim()[1], alpha=0.1, color='green', label='Lysogenic region')
    ax.axhspan(cro_threshold, ax.get_ylim()[1], alpha=0.1, color='red', label='Lytic region')
    
    ax.set_xlabel('CI_Dimer (molecules)', fontsize=11)
    ax.set_ylabel('Cro_Dimer (molecules)', fontsize=11)
    ax.set_title(f'Phase Portrait (Outcome: {outcome})', fontsize=12, fontweight='bold')
    ax.legend(loc='best', fontsize=9)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Save figure
    output_file = csv_path.parent / f"{csv_path.stem}_analysis.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Figure saved: {output_file}")
    
    plt.show()
    
    return {
        'outcome': outcome,
        'ci_final': ci_final,
        'cro_final': cro_final,
        'duration': time.iloc[-1],
        'n_points': len(df)
    }

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python analyze_single_run.py <simulation_data.csv>")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    results = analyze_single_run(csv_file)
