#!/usr/bin/env python3
"""
Analyze Phase 2 Dose-Response Data

This script analyzes multiple batch simulations across EPO concentrations
to generate dose-response curves and calculate EC50.

Usage:
    python analyze_phase2_dose_response.py

Expected directory structure:
    data/results/
        dose_response_epo0/
        dose_response_epo5/
        dose_response_epo10/
        ...
"""

import os
import sys
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from scipy.optimize import curve_fit
from typing import Dict, List, Tuple

# Parameters
RATIO_THRESHOLD = 2.5
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "results"

def print_header(text):
    """Print formatted section header."""
    print("\n" + "=" * 70)
    print(text)
    print("=" * 70 + "\n")

def hill_equation(epo, ec50, hill_coef, baseline, amplitude):
    """
    Hill equation for dose-response curve.
    
    P(erythroid) = baseline + amplitude * [EPO]^n / (EC50^n + [EPO]^n)
    """
    return baseline + amplitude * (epo**hill_coef) / (ec50**hill_coef + epo**hill_coef)

def analyze_batch(batch_dir: Path) -> Dict:
    """Analyze single EPO level batch."""
    # Load batch analysis if it exists
    analysis_file = batch_dir / "batch_analysis.json"
    
    if not analysis_file.exists():
        print(f"  ⚠️  No analysis found, analyzing now...")
        # Run batch analysis
        from analyze_batch import BatchAnalyzer
        analyzer = BatchAnalyzer(batch_dir)
        analyzer.analyze_all_runs()
        stats = analyzer.compute_statistics()
        checks = analyzer.validate_bistability(stats)
        analyzer.save_results(stats, checks)
    
    # Load results
    with open(analysis_file, 'r') as f:
        data = json.load(f)
    
    stats = data['statistics']
    
    return {
        'n_total': stats['n_total'],
        'n_erythroid': stats['n_erythroid'],
        'n_myeloid': stats['n_myeloid'],
        'n_uncommitted': stats['n_uncommitted'],
        'pct_erythroid': stats['pct_erythroid'],
        'pct_myeloid': stats['pct_myeloid'],
        'pct_uncommitted': stats['pct_uncommitted']
    }

def find_dose_response_batches() -> List[Tuple[float, Path]]:
    """Find all dose-response batch directories."""
    batches = []
    
    for item in DATA_DIR.iterdir():
        if item.is_dir() and item.name.startswith('dose_response_epo'):
            # Extract EPO level from directory name
            try:
                epo_str = item.name.replace('dose_response_epo', '')
                epo_level = float(epo_str)
                batches.append((epo_level, item))
            except ValueError:
                continue
    
    # Sort by EPO level
    batches.sort(key=lambda x: x[0])
    return batches

def main():
    print_header("PHASE 2: DOSE-RESPONSE ANALYSIS")
    
    # Find batch directories
    batches = find_dose_response_batches()
    
    if not batches:
        print("❌ No dose-response batches found!")
        print(f"   Expected directories like: {DATA_DIR}/dose_response_epo0/")
        print()
        print("Run dose-response simulations first:")
        print("  python run_phase2_dose_response.py")
        return
    
    print(f"Found {len(batches)} EPO levels:")
    for epo, path in batches:
        print(f"  • EPO = {epo:5.1f} µM  ({path.name})")
    print()
    
    # Analyze each batch
    print_header("ANALYZING BATCHES")
    
    results = []
    for epo, batch_dir in batches:
        print(f"EPO = {epo:5.1f} µM...", end=' ')
        
        try:
            stats = analyze_batch(batch_dir)
            results.append({
                'epo': epo,
                **stats
            })
            print(f"✓ ({stats['pct_erythroid']:.1f}% ERY, "
                  f"{stats['pct_myeloid']:.1f}% MYE, "
                  f"{stats['pct_uncommitted']:.1f}% UNC)")
        except Exception as e:
            print(f"✗ Error: {e}")
    
    if not results:
        print("\n❌ No valid results!")
        return
    
    # Convert to DataFrame
    df = pd.DataFrame(results)
    
    print_header("DOSE-RESPONSE SUMMARY")
    
    print(df.to_string(index=False))
    print()
    
    # Fit Hill equation
    print_header("FITTING DOSE-RESPONSE CURVE")
    
    epo_values = df['epo'].values
    pct_ery = df['pct_erythroid'].values
    
    # Initial parameter guesses
    baseline_guess = pct_ery[0] if len(pct_ery) > 0 else 20
    amplitude_guess = 100 - baseline_guess
    ec50_guess = 25  # Middle of typical range
    hill_guess = 2
    
    try:
        # Fit Hill equation
        params, covariance = curve_fit(
            hill_equation,
            epo_values,
            pct_ery,
            p0=[ec50_guess, hill_guess, baseline_guess, amplitude_guess],
            bounds=([0, 0.1, 0, 0], [200, 10, 100, 100]),
            maxfev=10000
        )
        
        ec50, hill_coef, baseline, amplitude = params
        errors = np.sqrt(np.diag(covariance))
        
        print(f"Fitted parameters:")
        print(f"  EC50:       {ec50:.2f} ± {errors[0]:.2f} µM")
        print(f"  Hill coef:  {hill_coef:.2f} ± {errors[1]:.2f}")
        print(f"  Baseline:   {baseline:.1f} ± {errors[2]:.1f} %")
        print(f"  Amplitude:  {amplitude:.1f} ± {errors[3]:.1f} %")
        print()
        
        # Calculate R²
        y_pred = hill_equation(epo_values, ec50, hill_coef, baseline, amplitude)
        ss_res = np.sum((pct_ery - y_pred)**2)
        ss_tot = np.sum((pct_ery - np.mean(pct_ery))**2)
        r_squared = 1 - (ss_res / ss_tot)
        
        print(f"Goodness of fit:")
        print(f"  R² = {r_squared:.4f}")
        print()
        
        fit_success = True
        
    except Exception as e:
        print(f"⚠️  Curve fitting failed: {e}")
        print("   Proceeding with raw data only.")
        fit_success = False
        ec50, hill_coef, baseline, amplitude = None, None, None, None
    
    # Generate plots
    print_header("GENERATING PLOTS")
    
    fig = plt.figure(figsize=(16, 10))
    gs = fig.add_gridspec(2, 3, hspace=0.3, wspace=0.3)
    
    # === Panel 1: Dose-response curve (main) ===
    ax1 = fig.add_subplot(gs[0, :2])
    
    # Plot raw data
    ax1.scatter(df['epo'], df['pct_erythroid'], s=100, 
                color='#e74c3c', label='ERYTHROID', zorder=3, alpha=0.8)
    ax1.scatter(df['epo'], df['pct_myeloid'], s=100, 
                color='#3498db', label='MYELOID', zorder=3, alpha=0.8)
    ax1.scatter(df['epo'], df['pct_uncommitted'], s=100, 
                color='#95a5a6', label='UNCOMMITTED', zorder=3, alpha=0.8)
    
    # Plot fitted curve
    if fit_success:
        epo_fine = np.linspace(0, max(epo_values), 200)
        y_fit = hill_equation(epo_fine, ec50, hill_coef, baseline, amplitude)
        ax1.plot(epo_fine, y_fit, 'r--', linewidth=2, 
                label=f'Hill fit (EC50={ec50:.1f})', zorder=2)
        
        # Mark EC50
        ax1.axvline(ec50, color='black', linestyle=':', linewidth=1.5, alpha=0.5)
        ax1.axhline(baseline + amplitude/2, color='black', linestyle=':', 
                   linewidth=1.5, alpha=0.5)
        ax1.plot(ec50, baseline + amplitude/2, 'ko', markersize=10, zorder=4)
    
    ax1.set_xlabel('EPO Concentration (µM)', fontweight='bold', fontsize=12)
    ax1.set_ylabel('Fate Distribution (%)', fontweight='bold', fontsize=12)
    ax1.set_title('EPO Dose-Response Curve', fontweight='bold', fontsize=14)
    ax1.legend(loc='best')
    ax1.grid(alpha=0.3)
    ax1.set_ylim(-5, 105)
    
    # === Panel 2: Commitment efficiency ===
    ax2 = fig.add_subplot(gs[0, 2])
    
    pct_committed = 100 - df['pct_uncommitted']
    ax2.scatter(df['epo'], pct_committed, s=100, color='#2ecc71', alpha=0.8)
    ax2.plot(df['epo'], pct_committed, 'g--', linewidth=2, alpha=0.5)
    
    ax2.set_xlabel('EPO (µM)', fontweight='bold')
    ax2.set_ylabel('Committed (%)', fontweight='bold')
    ax2.set_title('Commitment Efficiency', fontweight='bold')
    ax2.grid(alpha=0.3)
    ax2.set_ylim(-5, 105)
    
    # === Panel 3: ERY vs MYE balance ===
    ax3 = fig.add_subplot(gs[1, 0])
    
    committed_df = df[df['pct_uncommitted'] < 95].copy()
    if len(committed_df) > 0:
        committed_df['ery_fraction'] = (
            committed_df['n_erythroid'] / 
            (committed_df['n_erythroid'] + committed_df['n_myeloid'] + 1e-9)
        )
        
        ax3.scatter(committed_df['epo'], committed_df['ery_fraction'] * 100, 
                   s=100, color='#9b59b6', alpha=0.8)
        ax3.plot(committed_df['epo'], committed_df['ery_fraction'] * 100, 
                'm--', linewidth=2, alpha=0.5)
        ax3.axhline(50, color='black', linestyle=':', linewidth=1.5, alpha=0.5)
    
    ax3.set_xlabel('EPO (µM)', fontweight='bold')
    ax3.set_ylabel('ERY Fraction (%)', fontweight='bold')
    ax3.set_title('Erythroid Bias (Among Committed)', fontweight='bold')
    ax3.grid(alpha=0.3)
    ax3.set_ylim(-5, 105)
    
    # === Panel 4: Raw counts ===
    ax4 = fig.add_subplot(gs[1, 1])
    
    x = np.arange(len(df))
    width = 0.25
    
    ax4.bar(x - width, df['n_erythroid'], width, label='ERY', color='#e74c3c', alpha=0.8)
    ax4.bar(x, df['n_myeloid'], width, label='MYE', color='#3498db', alpha=0.8)
    ax4.bar(x + width, df['n_uncommitted'], width, label='UNC', color='#95a5a6', alpha=0.8)
    
    ax4.set_xlabel('EPO Level', fontweight='bold')
    ax4.set_ylabel('Cell Count (n=100)', fontweight='bold')
    ax4.set_title('Absolute Counts', fontweight='bold')
    ax4.set_xticks(x)
    ax4.set_xticklabels([f'{e:.0f}' for e in df['epo']], rotation=45)
    ax4.legend()
    ax4.grid(alpha=0.3, axis='y')
    
    # === Panel 5: Statistics table ===
    ax5 = fig.add_subplot(gs[1, 2])
    ax5.axis('off')
    
    if fit_success:
        stats_text = f"""
DOSE-RESPONSE STATISTICS

Hill Equation Fit:
  EC50 = {ec50:.2f} ± {errors[0]:.2f} µM
  Hill coef = {hill_coef:.2f} ± {errors[1]:.2f}
  Baseline = {baseline:.1f} ± {errors[2]:.1f} %
  Amplitude = {amplitude:.1f} ± {errors[3]:.1f} %
  R² = {r_squared:.4f}

Interpretation:
  • {ec50:.1f} µM EPO gives 50% 
    erythroid commitment
  • Hill coefficient {hill_coef:.2f}
    indicates {"cooperative" if hill_coef > 1.5 else "graded"} response
  • Baseline {baseline:.1f}% reflects
    spontaneous commitment
  • Amplitude {amplitude:.1f}% is
    signal-driven increase

EPO Levels Tested: {len(df)}
Total Simulations: {len(df) * 100}
"""
    else:
        stats_text = f"""
DOSE-RESPONSE STATISTICS

Curve fitting unsuccessful.

Raw data summary:
  EPO levels: {len(df)}
  Total sims: {len(df) * 100}
  
  Min ERY: {df['pct_erythroid'].min():.1f}%
  Max ERY: {df['pct_erythroid'].max():.1f}%
  
  Min UNC: {df['pct_uncommitted'].min():.1f}%
  Max UNC: {df['pct_uncommitted'].max():.1f}%
"""
    
    ax5.text(0.05, 0.5, stats_text, transform=ax5.transAxes,
            fontfamily='monospace', fontsize=10, verticalalignment='center')
    
    plt.suptitle('Phase 2: EPO Dose-Response Analysis', 
                 fontsize=16, fontweight='bold', y=0.995)
    
    # Save plot
    output_path = DATA_DIR / "phase2_dose_response_analysis.png"
    fig.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✓ Saved plot: {output_path}")
    
    # Save results
    results_dict = {
        'dose_response_data': results,
        'fit_parameters': {
            'ec50': float(ec50) if ec50 else None,
            'hill_coefficient': float(hill_coef) if hill_coef else None,
            'baseline': float(baseline) if baseline else None,
            'amplitude': float(amplitude) if amplitude else None,
            'r_squared': float(r_squared) if fit_success else None
        } if fit_success else None,
        'summary': {
            'n_levels_tested': len(df),
            'total_simulations': len(df) * 100,
            'epo_range': [float(df['epo'].min()), float(df['epo'].max())]
        }
    }
    
    results_path = DATA_DIR / "phase2_dose_response_results.json"
    with open(results_path, 'w') as f:
        json.dump(results_dict, f, indent=2)
    print(f"✓ Saved results: {results_path}")
    
    print_header("ANALYSIS COMPLETE")
    
    if fit_success:
        print(f"Key Finding: EC50 = {ec50:.2f} µM")
        print()
        print(f"This means {ec50:.1f} µM EPO concentration produces")
        print(f"50% erythroid commitment (half-maximal response).")
        print()
        
        if ec50 < 10:
            print("⚠️  Very low EC50 - cells are highly sensitive to EPO")
        elif ec50 < 30:
            print("✓  Moderate EC50 - physiologically relevant sensitivity")
        else:
            print("⚠️  High EC50 - cells require strong EPO signal")
    
    print()
    print("Next steps:")
    print("  1. Review dose-response curve")
    print("  2. Test balanced signals (EPO=50, GCSF=50)")
    print("  3. Proceed to Phase 3 (stochastic vs instructive)")

if __name__ == "__main__":
    main()
