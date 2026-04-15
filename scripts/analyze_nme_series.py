#!/usr/bin/env python3
"""
Analyze N-methylation effects on drug transport across the series (N_Me 0-6).

Compares:
- Drug accumulation rates (intracellular, extended, compact conformations)
- ATP consumption patterns and energy charge
- Transport efficiency and metabolic costs
- Permeability effects from N-methylation
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import seaborn as sns

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (14, 10)
plt.rcParams['font.size'] = 10

# Data directory
DATA_DIR = Path("workspace/projects/My_Project/drug_discovery/data/n_methylation")
OUTPUT_DIR = Path("workspace/projects/My_Project/drug_discovery/analysis/nme_series")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def load_simulation_data(nme_level):
    """Load CSV data for a specific N-methylation level."""
    csv_file = DATA_DIR / f"sim_nme_normal_{nme_level}_enhanced.csv"
    
    if not csv_file.exists():
        print(f"⚠️  Warning: {csv_file} not found")
        return None
    
    df = pd.read_csv(csv_file)
    
    # Rename columns for easier access
    df = df.rename(columns={
        'Time (s)': 'time',
        'Drug_ext (mM)': 'Drug_ext',
        'Drug_intracellular (mM)': 'Drug_intracellular',
        'Drug_extended (mM)': 'Drug_extended',
        'Drug_compact (mM)': 'Drug_compact',
        'Drug_degraded (mM)': 'Drug_degraded',
        'ATP_pool (mM)': 'ATP_pool',
        'ADP_pool (mM)': 'ADP_pool',
        'Pi_pool (mM)': 'Pi_pool',
    })
    
    print(f"✓ Loaded N_Me {nme_level}: {len(df)} time points, {df['time'].max():.1f}s duration")
    return df

def calculate_metrics(df, nme_level):
    """Calculate key metrics from simulation data."""
    if df is None or df.empty:
        return None
    
    # Get final values (last 10% of simulation for steady-state)
    steady_state = df[df['time'] >= df['time'].max() * 0.9]
    
    # Drug compartments
    drug_external = steady_state['Drug_ext'].mean()
    drug_intracellular = steady_state['Drug_intracellular'].mean()
    drug_extended = steady_state['Drug_extended'].mean()
    drug_compact = steady_state['Drug_compact'].mean()
    drug_degraded = steady_state['Drug_degraded'].mean()
    
    # Total drug accumulation (intracellular + conformations)
    total_internal = drug_intracellular + drug_extended + drug_compact
    
    # Energy pools
    atp = steady_state['ATP_pool'].mean()
    adp = steady_state['ADP_pool'].mean()
    energy_charge = atp / (atp + adp) if (atp + adp) > 0 else 0
    
    # ATP consumption (initial - final)
    atp_initial = df['ATP_pool'].iloc[0]
    atp_consumed = atp_initial - atp
    
    # Transport efficiency (drug accumulated per ATP consumed)
    transport_efficiency = total_internal / atp_consumed if atp_consumed > 0 else 0
    
    # Accumulation rate (slope in first 50s)
    early_phase = df[df['time'] <= 50]
    if len(early_phase) > 10:
        time = early_phase['time'].values
        drug = early_phase['Drug_intracellular'].values
        accumulation_rate = np.polyfit(time, drug, 1)[0]  # Linear fit slope
    else:
        accumulation_rate = 0
    
    return {
        'N_Me': nme_level,
        'Drug_external': drug_external,
        'Drug_intracellular': drug_intracellular,
        'Drug_extended': drug_extended,
        'Drug_compact': drug_compact,
        'Drug_degraded': drug_degraded,
        'Total_internal': total_internal,
        'ATP_pool': atp,
        'ADP_pool': adp,
        'Energy_charge': energy_charge,
        'ATP_consumed': atp_consumed,
        'Transport_efficiency': transport_efficiency,
        'Accumulation_rate': accumulation_rate,
    }

def plot_time_series(data_dict, metrics_df):
    """Generate time series plots comparing all N-methylation levels."""
    
    fig, axes = plt.subplots(3, 2, figsize=(16, 12))
    fig.suptitle('N-Methylation Series: Time Course Comparison', fontsize=16, fontweight='bold')
    
    colors = plt.cm.viridis(np.linspace(0, 1, 7))
    
    # Plot 1: Intracellular drug accumulation
    ax = axes[0, 0]
    for nme, df in data_dict.items():
        if df is not None:
            ax.plot(df['time'], df['Drug_intracellular'], 
                   label=f'N_Me {nme}', color=colors[nme], linewidth=2)
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Drug Intracellular (molecules)')
    ax.set_title('Intracellular Drug Accumulation')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Plot 2: ATP pool depletion
    ax = axes[0, 1]
    for nme, df in data_dict.items():
        if df is not None:
            ax.plot(df['time'], df['ATP_pool'], 
                   label=f'N_Me {nme}', color=colors[nme], linewidth=2)
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('ATP Pool (molecules)')
    ax.set_title('ATP Consumption Over Time')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Plot 3: Energy charge
    ax = axes[1, 0]
    for nme, df in data_dict.items():
        if df is not None:
            energy_charge = df['ATP_pool'] / (df['ATP_pool'] + df['ADP_pool'])
            ax.plot(df['time'], energy_charge, 
                   label=f'N_Me {nme}', color=colors[nme], linewidth=2)
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Energy Charge (ATP/(ATP+ADP))')
    ax.set_title('Cellular Energy Charge')
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.axhline(y=0.8, color='red', linestyle='--', alpha=0.5, label='Healthy threshold')
    
    # Plot 4: Drug conformations (N_Me 6 example)
    ax = axes[1, 1]
    if 6 in data_dict and data_dict[6] is not None:
        df = data_dict[6]
        ax.plot(df['time'], df['Drug_intracellular'], label='Intracellular', linewidth=2)
        ax.plot(df['time'], df['Drug_extended'], label='Extended', linewidth=2)
        ax.plot(df['time'], df['Drug_compact'], label='Compact', linewidth=2)
        ax.set_xlabel('Time (s)')
        ax.set_ylabel('Drug Amount (molecules)')
        ax.set_title('Drug Conformations (N_Me 6 Example)')
        ax.legend()
        ax.grid(True, alpha=0.3)
    
    # Plot 5: External drug depletion
    ax = axes[2, 0]
    for nme, df in data_dict.items():
        if df is not None:
            ax.plot(df['time'], df['Drug_ext'], 
                   label=f'N_Me {nme}', color=colors[nme], linewidth=2)
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Drug External (molecules)')
    ax.set_title('External Drug Depletion')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Plot 6: Degraded drug
    ax = axes[2, 1]
    for nme, df in data_dict.items():
        if df is not None:
            ax.plot(df['time'], df['Drug_degraded'], 
                   label=f'N_Me {nme}', color=colors[nme], linewidth=2)
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Drug Degraded (molecules)')
    ax.set_title('Drug Degradation Over Time')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    output_file = OUTPUT_DIR / "nme_series_timecourse.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✓ Saved time series plot: {output_file}")
    plt.close()

def plot_nme_effects(metrics_df):
    """Plot N-methylation effects on key metrics."""
    
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    fig.suptitle('N-Methylation Effects on Drug Transport and Energy Metabolism', 
                 fontsize=16, fontweight='bold')
    
    nme_levels = metrics_df['N_Me'].values
    
    # Plot 1: Total internal drug accumulation
    ax = axes[0, 0]
    ax.bar(nme_levels, metrics_df['Total_internal'], color='steelblue', alpha=0.7)
    ax.set_xlabel('N-Methylation Level')
    ax.set_ylabel('Total Internal Drug (molecules)')
    ax.set_title('Drug Accumulation vs N-Methylation')
    ax.grid(True, alpha=0.3, axis='y')
    
    # Plot 2: Accumulation rate
    ax = axes[0, 1]
    ax.bar(nme_levels, metrics_df['Accumulation_rate'], color='coral', alpha=0.7)
    ax.set_xlabel('N-Methylation Level')
    ax.set_ylabel('Accumulation Rate (molecules/s)')
    ax.set_title('Initial Accumulation Rate')
    ax.grid(True, alpha=0.3, axis='y')
    
    # Plot 3: ATP consumed
    ax = axes[0, 2]
    ax.bar(nme_levels, metrics_df['ATP_consumed'], color='crimson', alpha=0.7)
    ax.set_xlabel('N-Methylation Level')
    ax.set_ylabel('ATP Consumed (molecules)')
    ax.set_title('Total ATP Consumption')
    ax.grid(True, alpha=0.3, axis='y')
    
    # Plot 4: Energy charge
    ax = axes[1, 0]
    ax.bar(nme_levels, metrics_df['Energy_charge'], color='forestgreen', alpha=0.7)
    ax.set_xlabel('N-Methylation Level')
    ax.set_ylabel('Energy Charge')
    ax.set_title('Final Energy Charge')
    ax.axhline(y=0.8, color='red', linestyle='--', linewidth=2, label='Healthy threshold')
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')
    ax.set_ylim([0, 1])
    
    # Plot 5: Transport efficiency
    ax = axes[1, 1]
    ax.bar(nme_levels, metrics_df['Transport_efficiency'], color='purple', alpha=0.7)
    ax.set_xlabel('N-Methylation Level')
    ax.set_ylabel('Transport Efficiency (drug/ATP)')
    ax.set_title('Metabolic Efficiency of Transport')
    ax.grid(True, alpha=0.3, axis='y')
    
    # Plot 6: Drug distribution
    ax = axes[1, 2]
    width = 0.25
    x = np.arange(len(nme_levels))
    ax.bar(x - width, metrics_df['Drug_intracellular'], width, label='Intracellular', alpha=0.7)
    ax.bar(x, metrics_df['Drug_extended'], width, label='Extended', alpha=0.7)
    ax.bar(x + width, metrics_df['Drug_compact'], width, label='Compact', alpha=0.7)
    ax.set_xlabel('N-Methylation Level')
    ax.set_ylabel('Drug Amount (molecules)')
    ax.set_title('Drug Conformation Distribution')
    ax.set_xticks(x)
    ax.set_xticklabels(nme_levels)
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    output_file = OUTPUT_DIR / "nme_effects_summary.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✓ Saved N-methylation effects plot: {output_file}")
    plt.close()

def plot_correlations(metrics_df):
    """Plot correlations between N-methylation and key metrics."""
    
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle('N-Methylation Correlations', fontsize=16, fontweight='bold')
    
    nme = metrics_df['N_Me'].values
    
    # Correlation 1: N-methylation vs Drug accumulation
    ax = axes[0]
    ax.scatter(nme, metrics_df['Total_internal'], s=100, alpha=0.7, color='steelblue')
    z = np.polyfit(nme, metrics_df['Total_internal'], 1)
    p = np.poly1d(z)
    ax.plot(nme, p(nme), "r--", alpha=0.8, linewidth=2)
    correlation = np.corrcoef(nme, metrics_df['Total_internal'])[0, 1]
    ax.set_xlabel('N-Methylation Level')
    ax.set_ylabel('Total Internal Drug (molecules)')
    ax.set_title(f'Drug Accumulation vs N-Methylation\n(r = {correlation:.3f})')
    ax.grid(True, alpha=0.3)
    
    # Correlation 2: Drug accumulation vs ATP consumption
    ax = axes[1]
    scatter = ax.scatter(metrics_df['ATP_consumed'], metrics_df['Total_internal'], 
               s=100, alpha=0.7, c=nme, cmap='viridis')
    z = np.polyfit(metrics_df['ATP_consumed'], metrics_df['Total_internal'], 1)
    p = np.poly1d(z)
    ax.plot(metrics_df['ATP_consumed'], p(metrics_df['ATP_consumed']), 
            "r--", alpha=0.8, linewidth=2)
    correlation = np.corrcoef(metrics_df['ATP_consumed'], metrics_df['Total_internal'])[0, 1]
    ax.set_xlabel('ATP Consumed (molecules)')
    ax.set_ylabel('Total Internal Drug (molecules)')
    ax.set_title(f'Drug vs Energy Cost\n(r = {correlation:.3f})')
    ax.grid(True, alpha=0.3)
    cbar = plt.colorbar(scatter, ax=ax)
    cbar.set_label('N-Methylation Level')
    
    plt.tight_layout()
    output_file = OUTPUT_DIR / "nme_correlations.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✓ Saved correlation plot: {output_file}")
    plt.close()

def main():
    """Main analysis pipeline."""
    print("=" * 80)
    print("N-METHYLATION SERIES ANALYSIS")
    print("=" * 80)
    print()
    
    # Load all simulation data
    print("Loading simulation data...")
    data_dict = {}
    for nme in range(7):
        data_dict[nme] = load_simulation_data(nme)
    print()
    
    # Calculate metrics for each N-methylation level
    print("Calculating metrics...")
    metrics_list = []
    for nme in range(7):
        metrics = calculate_metrics(data_dict[nme], nme)
        if metrics:
            metrics_list.append(metrics)
    
    metrics_df = pd.DataFrame(metrics_list)
    print("✓ Metrics calculated for all N-methylation levels")
    print()
    
    # Save metrics to CSV
    metrics_file = OUTPUT_DIR / "nme_series_metrics.csv"
    metrics_df.to_csv(metrics_file, index=False, float_format='%.4f')
    print(f"✓ Saved metrics: {metrics_file}")
    print()
    
    # Display summary table
    print("METRICS SUMMARY:")
    print("=" * 80)
    pd.set_option('display.width', 120)
    pd.set_option('display.max_columns', None)
    print(metrics_df.to_string(index=False))
    print()
    
    # Generate plots
    print("Generating plots...")
    plot_time_series(data_dict, metrics_df)
    plot_nme_effects(metrics_df)
    plot_correlations(metrics_df)
    print()
    
    # Key findings
    print("KEY FINDINGS:")
    print("=" * 80)
    
    # N-methylation effect on accumulation
    nme_correlation = np.corrcoef(metrics_df['N_Me'], metrics_df['Total_internal'])[0, 1]
    print(f"1. N-methylation vs Drug Accumulation: r = {nme_correlation:.3f}")
    if abs(nme_correlation) > 0.7:
        trend = "positive" if nme_correlation > 0 else "negative"
        print(f"   → Strong {trend} correlation detected")
    
    # Energy efficiency
    max_efficiency_idx = metrics_df['Transport_efficiency'].idxmax()
    max_efficiency_nme = metrics_df.loc[max_efficiency_idx, 'N_Me']
    max_efficiency_val = metrics_df.loc[max_efficiency_idx, 'Transport_efficiency']
    print(f"\n2. Most Efficient N-Methylation: N_Me {int(max_efficiency_nme)}")
    print(f"   → Transport efficiency: {max_efficiency_val:.4f} drug molecules/ATP")
    
    # Energy depletion
    min_energy = metrics_df['Energy_charge'].min()
    max_energy = metrics_df['Energy_charge'].max()
    print(f"\n3. Energy Charge Range: {min_energy:.3f} - {max_energy:.3f}")
    if min_energy < 0.8:
        print(f"   ⚠️  Some models fall below healthy threshold (0.8)")
    
    # Accumulation rate
    fastest_rate_idx = metrics_df['Accumulation_rate'].idxmax()
    fastest_nme = metrics_df.loc[fastest_rate_idx, 'N_Me']
    fastest_rate = metrics_df.loc[fastest_rate_idx, 'Accumulation_rate']
    print(f"\n4. Fastest Accumulation Rate: N_Me {int(fastest_nme)}")
    print(f"   → {fastest_rate:.4f} molecules/s (first 50s)")
    
    print()
    print("=" * 80)
    print(f"✅ ANALYSIS COMPLETE")
    print(f"   Output directory: {OUTPUT_DIR}")
    print(f"   Generated files:")
    print(f"     - nme_series_metrics.csv (numerical summary)")
    print(f"     - nme_series_timecourse.png (time series plots)")
    print(f"     - nme_effects_summary.png (bar charts)")
    print(f"     - nme_correlations.png (scatter plots)")
    print("=" * 80)

if __name__ == "__main__":
    main()
