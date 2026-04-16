#!/usr/bin/env python3
"""
Generate excitability figure showing all-or-nothing MAPK cascade dynamics.
Uses pre-simulated data files for different GF doses.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from pathlib import Path

def load_excitability_data():
    """Load simulation data for different GF doses."""
    data_dir = Path(__file__).parent.parent / "data" / "manuscript"
    
    # Map dose to data file
    dose_files = {
        0: "simulation_data_basal_tunned.csv",  # basal
        5: "simulation_data_subthreshold_50nM.csv",  # subthreshold
        20: "simulation_data_dose_20nM_tuned.csv",
        40: "simulation_data_dose_40nM_tuned.csv",
        60: "simulation_data_dose_60nM_tuned.csv",
        80: "simulation_data_dose_80nM_tuned.csv",
    }
    
    results = {}
    peak_erk = []
    doses = []
    
    print("Loading excitability simulation data...")
    
    for dose, filename in sorted(dose_files.items()):
        filepath = data_dir / filename
        if not filepath.exists():
            print(f"  Warning: {filename} not found, skipping dose {dose} nM")
            continue
            
        print(f"  Loading GF = {dose} nM from {filename}...")
        df = pd.read_csv(filepath)
        
        time = df['Time (s)'].values
        
        # Try different column names for ERK-PP
        erk_cols = ['ERK_PP (mM)', 'ERK_PP (nM)', 'ERK_PP']
        erk_pp = None
        for col in erk_cols:
            if col in df.columns:
                erk_pp = df[col].values
                break
        
        if erk_pp is None:
            print(f"    Warning: Could not find ERK_PP column in {filename}")
            continue
        
        # Convert to nM if in mM
        if 'mM' in [c for c in df.columns if 'ERK_PP' in c][0]:
            erk_pp = erk_pp * 1000  # mM to nM
        
        results[dose] = {'time': time, 'ERK_PP': erk_pp}
        
        # Get peak ERK-PP
        peak = np.max(erk_pp)
        peak_erk.append(peak)
        doses.append(dose)
        print(f"    Peak ERK-PP = {peak:.1f} nM")
    
    return results, doses, peak_erk

def main():
    """Generate excitability figure."""
    results, doses, peak_erk = load_excitability_data()
    
    if not results:
        print("Error: No data loaded!")
        return
    
    # Create figure with 3 panels
    fig = plt.figure(figsize=(14, 5))
    gs = gridspec.GridSpec(1, 3, figure=fig, wspace=0.35)
    
    # Panel A: Time courses for selected doses
    ax1 = fig.add_subplot(gs[0, 0:2])
    
    # Plot available doses
    colors = ['#388E3C', '#FFA726', '#EF5350', '#C62828']
    plot_doses = [d for d in [0, 5, 20, 60, 80] if d in results]
    
    for i, dose in enumerate(plot_doses):
        time = results[dose]['time']
        erk_pp = results[dose]['ERK_PP']
        
        color = colors[min(i, len(colors)-1)]
        label = f'{dose} nM GF'
        
        if dose < 10:
            linestyle = '--'
            label += ' (subthreshold)'
        else:
            linestyle = '-'
            label += ' (suprathreshold)'
            
        ax1.plot(time, erk_pp, color=color, linewidth=2.5, 
                linestyle=linestyle, label=label, alpha=0.9)
    
    ax1.set_xlabel('Time (s)', fontsize=13, fontweight='bold')
    ax1.set_ylabel('ERK-PP (nM)', fontsize=13, fontweight='bold')
    ax1.set_title('Excitable MAPK Cascade Dynamics', fontsize=14, fontweight='bold', pad=10)
    ax1.legend(frameon=True, fontsize=11, loc='upper left')
    ax1.grid(True, alpha=0.3, linestyle=':', linewidth=0.5)
    ax1.tick_params(labelsize=11)
    
    # Panel B: Dose-response curve
    ax2 = fig.add_subplot(gs[0, 2])
    
    # Sort by dose
    sorted_data = sorted(zip(doses, peak_erk))
    sorted_doses, sorted_peaks = zip(*sorted_data)
    
    ax2.plot(sorted_doses, sorted_peaks, 'o-', color='#1565C0', linewidth=3, 
             markersize=10, markerfacecolor='white', markeredgewidth=2.5)
    
    # Mark threshold region (assuming ~10-15 nM)
    threshold = 10
    ax2.axvline(x=threshold, color='#D32F2F', linestyle='--', 
               alpha=0.6, linewidth=2.5)
    ax2.text(threshold + 2, max(sorted_peaks)*0.5, 'Threshold', 
             fontsize=11, color='#D32F2F', fontweight='bold', 
             rotation=0, va='center')
    
    ax2.set_xlabel('Growth Factor (nM)', fontsize=13, fontweight='bold')
    ax2.set_ylabel('Peak ERK-PP (nM)', fontsize=13, fontweight='bold')
    ax2.grid(True, alpha=0.3, linestyle=':', linewidth=0.5)
    ax2.tick_params(labelsize=11)
    
    # Add text labels for subthreshold vs suprathreshold
    if sorted_doses[0] < threshold:
        ax2.text(sorted_doses[0], sorted_peaks[0]*1.15, 'Subthreshold', 
                fontsize=9, ha='center', style='italic', color='#388E3C')
    
    suprathreshold_idx = [i for i, d in enumerate(sorted_doses) if d >= 20]
    if suprathreshold_idx:
        idx = suprathreshold_idx[-1]
        ax2.text(sorted_doses[idx], sorted_peaks[idx]*1.05, 'Saturated', 
                fontsize=9, ha='center', style='italic', color='#C62828')
    
    plt.tight_layout()
    
    # Save figure
    output_dir = Path(__file__).parent.parent / 'figures'
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / 'mapk_excitability.pdf'
    
    plt.savefig(output_path, format='pdf', dpi=300, bbox_inches='tight')
    print(f"\nFigure saved to: {output_path}")
    
    # Also save as PNG for preview
    png_path = output_path.with_suffix('.png')
    plt.savefig(png_path, format='png', dpi=150, bbox_inches='tight')
    print(f"PNG preview saved to: {png_path}")
    
    plt.close()
    
    # Print summary statistics
    print("\n=== Excitability Summary ===")
    subthreshold = [p for d, p in zip(sorted_doses, sorted_peaks) if d < threshold]
    suprathreshold = [p for d, p in zip(sorted_doses, sorted_peaks) if d >= threshold]
    
    if subthreshold:
        print(f"Subthreshold response (<{threshold} nM): {np.mean(subthreshold):.1f} nM")
    if suprathreshold:
        print(f"Suprathreshold response (≥{threshold} nM): {np.mean(suprathreshold):.1f} ± {np.std(suprathreshold):.1f} nM")
        if subthreshold:
            fold_amp = np.mean(suprathreshold) / np.mean(subthreshold)
            print(f"Fold amplification: {fold_amp:.0f}×")

if __name__ == '__main__':
    main()
