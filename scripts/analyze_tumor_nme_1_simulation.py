#!/usr/bin/env python3
"""
Comprehensive analysis of N-Me 1 tumor simulation data - first N-methylation.
Analyzes macrocycle transport dynamics with single N-methyl group in tumor microenvironment.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Configuration
DATA_FILE = Path("workspace/projects/My_Project/drug_discovery/data/n_methylation/sim_nme_tumor_1_enhanced.csv")
OUTPUT_STATS = Path("tumor_nme_1_summary_statistics.csv")
OUTPUT_PLOT = Path("tumor_nme_1_comprehensive_analysis.png")

def load_simulation_data(filepath):
    """Load and validate simulation CSV data."""
    df = pd.read_csv(filepath)
    print(f"Loaded {len(df)} timepoints from {filepath.name}")
    print(f"Columns: {list(df.columns)}")
    print(f"Time range: {df['Time (s)'].min():.3f}s to {df['Time (s)'].max():.3f}s")
    return df

def calculate_metrics(df):
    """Calculate key transport and energetic metrics."""
    metrics = {}
    
    # Extracellular transport dynamics
    initial_extracellular = df['Drug_ext (mM)'].iloc[0]
    final_extracellular = df['Drug_ext (mM)'].iloc[-1]
    metrics['drug_transported_in'] = initial_extracellular - final_extracellular
    metrics['transport_efficiency_percent'] = (metrics['drug_transported_in'] / initial_extracellular) * 100
    
    # Intracellular accumulation
    initial_intracellular = df['Drug_intracellular (mM)'].iloc[0]
    final_intracellular = df['Drug_intracellular (mM)'].iloc[-1]
    metrics['intracellular_gain'] = final_intracellular - initial_intracellular
    
    # Conformational dynamics (extended vs compact)
    metrics['initial_extended'] = df['Drug_extended (mM)'].iloc[0]
    metrics['final_extended'] = df['Drug_extended (mM)'].iloc[-1]
    initial_compact = df['Drug_compact (mM)'].iloc[0]
    final_compact = df['Drug_compact (mM)'].iloc[-1]
    metrics['initial_compact'] = initial_compact
    metrics['final_compact'] = final_compact
    metrics['compact_gain'] = final_compact - initial_compact
    metrics['conformational_conversion_percent'] = (metrics['compact_gain'] / metrics['initial_extended']) * 100
    metrics['extended_to_compact_ratio'] = df['Drug_extended (mM)'].iloc[-1] / (final_compact + 1e-10)
    
    # ATP/ADP dynamics
    metrics['initial_ATP'] = df['ATP_pool (mM)'].iloc[0]
    metrics['final_ATP'] = df['ATP_pool (mM)'].iloc[-1]
    metrics['initial_ADP'] = df['ADP_pool (mM)'].iloc[0]
    metrics['final_ADP'] = df['ADP_pool (mM)'].iloc[-1]
    metrics['ATP_depletion_percent'] = ((metrics['initial_ATP'] - metrics['final_ATP']) / metrics['initial_ATP']) * 100
    metrics['ADP_accumulation'] = metrics['final_ADP'] - metrics['initial_ADP']
    
    # Energy ratio dynamics
    metrics['initial_ATP_ADP_ratio'] = metrics['initial_ATP'] / (metrics['initial_ADP'] + 1e-10)
    metrics['final_ATP_ADP_ratio'] = metrics['final_ATP'] / (metrics['final_ADP'] + 1e-10)
    
    # Pi (phosphate) depletion time - critical for energy coupling
    pi_threshold = df['Pi_pool (mM)'].iloc[0] * 0.5  # 50% depletion
    pi_depleted = df[df['Pi_pool (mM)'] < pi_threshold]
    metrics['pi_depletion_time'] = pi_depleted['Time (s)'].iloc[0] if len(pi_depleted) > 0 else df['Time (s)'].iloc[-1]
    
    # Conformational transition events (count significant changes)
    extended_diff = df['Drug_extended (mM)'].diff().abs()
    metrics['conformational_transitions'] = len(extended_diff[extended_diff > 0.01])
    
    # Mass conservation check
    total_drug = df['Drug_extended (mM)'] + df['Drug_compact (mM)']
    metrics['mass_conservation_percent'] = (total_drug.iloc[-1] / total_drug.iloc[0]) * 100
    
    # Gradient utilization
    metrics['initial_out_gradient'] = df['Membrane_potential (mM)'].iloc[0]
    metrics['final_out_gradient'] = df['Membrane_potential (mM)'].iloc[-1]
    metrics['gradient_consumption'] = metrics['initial_out_gradient'] - metrics['final_out_gradient']
    
    return metrics

def create_comprehensive_plot(df, metrics):
    """Generate 6-panel comprehensive analysis visualization."""
    fig, axes = plt.subplots(3, 2, figsize=(15, 12))
    fig.suptitle('N-Me 1 (First N-Methyl) Tumor Simulation - Comprehensive Analysis', 
                 fontsize=14, fontweight='bold')
    
    time = df['Time (s)']
    
    # Panel 1: Drug conformational states
    ax1 = axes[0, 0]
    ax1.plot(time, df['Drug_extended (mM)'], label='Extended', linewidth=2, color='#2E86AB')
    ax1.plot(time, df['Drug_compact (mM)'], label='Compact (accumulated)', linewidth=2, color='#A23B72')
    ax1.set_xlabel('Time (s)', fontsize=10)
    ax1.set_ylabel('Concentration (molecules)', fontsize=10)
    ax1.set_title(f'Drug Conformational Dynamics\nCompact Gain: {metrics["compact_gain"]:.1f} mM ({metrics["conformational_conversion_percent"]:.1f}% conversion)', 
                  fontsize=11, fontweight='bold')
    ax1.legend(fontsize=9)
    ax1.grid(True, alpha=0.3)
    
    # Panel 2: ATP/ADP energy dynamics
    ax2 = axes[0, 1]
    ax2.plot(time, df['ATP_pool (mM)'], label='ATP', linewidth=2, color='#F18F01')
    ax2.plot(time, df['ADP_pool (mM)'], label='ADP', linewidth=2, color='#C73E1D')
    ax2.set_xlabel('Time (s)', fontsize=10)
    ax2.set_ylabel('Concentration (molecules)', fontsize=10)
    ax2.set_title(f'Energy Metabolism\nATP Depletion: {metrics["ATP_depletion_percent"]:.2f}%', 
                  fontsize=11, fontweight='bold')
    ax2.legend(fontsize=9)
    ax2.grid(True, alpha=0.3)
    
    # Panel 3: Phosphate (Pi) dynamics
    ax3 = axes[1, 0]
    ax3.plot(time, df['Pi_pool (mM)'], linewidth=2, color='#6A994E')
    ax3.axhline(y=df['Pi_pool (mM)'].iloc[0] * 0.5, color='red', linestyle='--', 
                label='50% threshold', alpha=0.7)
    ax3.axvline(x=metrics['pi_depletion_time'], color='red', linestyle=':', 
                label=f'Depletion time: {metrics["pi_depletion_time"]:.2f}s', alpha=0.7)
    ax3.set_xlabel('Time (s)', fontsize=10)
    ax3.set_ylabel('Pi Concentration', fontsize=10)
    ax3.set_title('Phosphate Dynamics (Energy Coupling)', fontsize=11, fontweight='bold')
    ax3.legend(fontsize=9)
    ax3.grid(True, alpha=0.3)
    
    # Panel 4: ATP/ADP ratio over time
    ax4 = axes[1, 1]
    atp_adp_ratio = df['ATP_pool (mM)'] / (df['ADP_pool (mM)'] + 1e-10)
    ax4.plot(time, atp_adp_ratio, linewidth=2, color='#BC4B51')
    ax4.set_xlabel('Time (s)', fontsize=10)
    ax4.set_ylabel('ATP/ADP Ratio', fontsize=10)
    ax4.set_title(f'Energy Status\nInitial: {metrics["initial_ATP_ADP_ratio"]:.2f} → Final: {metrics["final_ATP_ADP_ratio"]:.2f}', 
                  fontsize=11, fontweight='bold')
    ax4.grid(True, alpha=0.3)
    
    # Panel 5: Mass conservation check
    ax5 = axes[2, 0]
    total_drug = df['Drug_extended (mM)'] + df['Drug_compact (mM)']
    ax5.plot(time, total_drug, linewidth=2, color='#5E60CE')
    ax5.axhline(y=total_drug.iloc[0], color='black', linestyle='--', 
                label=f'Initial: {total_drug.iloc[0]:.1f}', alpha=0.7)
    ax5.set_xlabel('Time (s)', fontsize=10)
    ax5.set_ylabel('Total Drug (molecules)', fontsize=10)
    ax5.set_title(f'Mass Conservation Check\n{metrics["mass_conservation_percent"]:.2f}% retained', 
                  fontsize=11, fontweight='bold')
    ax5.legend(fontsize=9)
    ax5.grid(True, alpha=0.3)
    
    # Panel 6: Gradient consumption
    ax6 = axes[2, 1]
    ax6.plot(time, df['Membrane_potential (mM)'], label='Membrane potential', linewidth=2, color='#7209B7')
    ax6.plot(time, df['pH_gradient (mM)'], label='pH gradient', linewidth=2, color='#F72585')
    ax6.set_xlabel('Time (s)', fontsize=10)
    ax6.set_ylabel('Gradient Strength', fontsize=10)
    ax6.set_title(f'Electrochemical Gradients\nConsumption: {metrics["gradient_consumption"]:.2e}', 
                  fontsize=11, fontweight='bold')
    ax6.legend(fontsize=9)
    ax6.grid(True, alpha=0.3)
    
    plt.tight_layout()
    return fig

def main():
    """Main analysis workflow."""
    print("=" * 80)
    print("N-Me 1 (First N-Methyl) TUMOR Simulation Analysis")
    print("=" * 80)
    
    # Load data
    df = load_simulation_data(DATA_FILE)
    
    # Calculate metrics
    print("\nCalculating transport and energetic metrics...")
    metrics = calculate_metrics(df)
    
    # Display key findings
    print("\n" + "=" * 80)
    print("KEY FINDINGS - TUMOR MICROENVIRONMENT")
    print("=" * 80)
    print(f"\n🎯 Drug Transport & Accumulation:")
    print(f"   Transported in: {metrics['drug_transported_in']:.1f} mM ({metrics['transport_efficiency_percent']:.1f}% of extracellular)")
    print(f"   Intracellular gain: {metrics['intracellular_gain']:.1f} mM")
    print(f"   Conformational conversion: {metrics['initial_extended']:.1f}→{metrics['final_extended']:.1f} mM extended")
    print(f"   Compact accumulation: {metrics['initial_compact']:.1f}→{metrics['final_compact']:.1f} mM (+{metrics['compact_gain']:.1f} mM)")
    
    print(f"\n⚡ Energy Metabolism:")
    print(f"   ATP depletion: {metrics['ATP_depletion_percent']:.2f}%")
    print(f"   Initial ATP: {metrics['initial_ATP']:.1f} → Final: {metrics['final_ATP']:.1f}")
    print(f"   Initial ADP: {metrics['initial_ADP']:.1f} → Final: {metrics['final_ADP']:.1f}")
    print(f"   ATP/ADP ratio: {metrics['initial_ATP_ADP_ratio']:.3f} → {metrics['final_ATP_ADP_ratio']:.3f}")
    
    print(f"\n🔄 Conformational Dynamics:")
    print(f"   Pi depletion time: {metrics['pi_depletion_time']:.2f}s")
    print(f"   Transition events: {metrics['conformational_transitions']}")
    print(f"   Extended/Compact ratio: {metrics['extended_to_compact_ratio']:.4f}")
    
    print(f"\n📊 System Integrity:")
    print(f"   Mass conservation: {metrics['mass_conservation_percent']:.2f}%")
    print(f"   Gradient consumption: {metrics['gradient_consumption']:.2e}")
    
    # Save metrics to CSV
    metrics_df = pd.DataFrame([metrics])
    metrics_df.to_csv(OUTPUT_STATS, index=False)
    print(f"\n✅ Summary statistics saved to: {OUTPUT_STATS}")
    
    # Generate comprehensive plot
    print("\nGenerating comprehensive visualization...")
    fig = create_comprehensive_plot(df, metrics)
    fig.savefig(OUTPUT_PLOT, dpi=300, bbox_inches='tight')
    print(f"✅ Visualization saved to: {OUTPUT_PLOT}")
    
    plt.close()
    
    print("\n" + "=" * 80)
    print("Analysis complete!")
    print("=" * 80)

if __name__ == "__main__":
    main()
