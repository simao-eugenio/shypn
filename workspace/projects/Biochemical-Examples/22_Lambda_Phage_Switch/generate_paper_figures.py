#!/usr/bin/env python3
"""
Generate publication-quality figures for Lambda Phage Bistable Switch paper.

Usage:
    python generate_paper_figures.py

Generates:
    - Figure 1: Outcome distribution histograms (3 conditions)
    - Figure 2: Final concentration scatter plots
    - Figure 3: Time course examples (lysogenic and lytic)
    - Figure 4: Rate function symmetry demonstration
    - Figure 5: Summary comparison bars
"""

import csv
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from matplotlib.patches import Rectangle

# Publication settings
plt.rcParams['font.size'] = 10
plt.rcParams['font.family'] = 'Arial'
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['savefig.bbox'] = 'tight'

OUTPUT_DIR = Path('figures')
OUTPUT_DIR.mkdir(exist_ok=True)

def load_batch_results(batch_dir):
    """Load all replicate results from a batch directory."""
    batch_path = Path(batch_dir)
    results = []
    
    for csv_file in sorted(batch_path.glob('run_*.csv')):
        with open(csv_file, 'r') as f:
            data = list(csv.DictReader(f))
        
        if not data:
            continue
        
        final = data[-1]
        ci = float(final.get('P7', 0))
        cro = float(final.get('P8', 0))
        
        results.append({
            'ci': ci,
            'cro': cro,
            'time_points': len(data)
        })
    
    return results

def classify_outcome(ci, cro):
    """Classify outcome as lysogenic or lytic."""
    if ci > 50 and cro < 30:
        return 'lysogenic'
    elif cro > 50 and ci < 30:
        return 'lytic'
    else:
        return 'intermediate'

def figure1_outcome_distributions():
    """Figure 1: Three-panel histogram of outcome distributions."""
    fig, axes = plt.subplots(1, 3, figsize=(12, 4))
    
    batches = [
        ('batch_results/zero_no_uv', 'ZERO, no UV', 'A'),
        ('batch_results/zero_with_uv', 'ZERO + UV', 'B'),
        ('batch_results/balanced_with_uv', 'BALANCED + UV', 'C'),
    ]
    
    for ax, (batch_dir, title, panel) in zip(axes, batches):
        results = load_batch_results(batch_dir)
        
        ci_vals = [r['ci'] for r in results]
        cro_vals = [r['cro'] for r in results]
        
        # 2D histogram
        h = ax.hist2d(ci_vals, cro_vals, bins=30, cmap='YlOrRd', 
                     range=[[0, 100], [0, 100]], cmin=1)
        
        # Add attractor regions
        ax.add_patch(Rectangle((70, 0), 30, 30, fill=False, 
                               edgecolor='blue', linewidth=2, linestyle='--',
                               label='Lysogenic'))
        ax.add_patch(Rectangle((0, 70), 30, 30, fill=False, 
                               edgecolor='red', linewidth=2, linestyle='--',
                               label='Lytic'))
        
        ax.set_xlabel('CI Dimer (mM)')
        ax.set_ylabel('Cro Dimer (mM)')
        ax.set_title(f'{panel}. {title}')
        ax.set_xlim(0, 100)
        ax.set_ylim(0, 100)
        ax.set_aspect('equal')
        
        # Count outcomes
        lysogenic = sum(1 for r in results if classify_outcome(r['ci'], r['cro']) == 'lysogenic')
        lytic = sum(1 for r in results if classify_outcome(r['ci'], r['cro']) == 'lytic')
        
        ax.text(0.05, 0.95, f'Lys: {lysogenic}\nLyt: {lytic}', 
               transform=ax.transAxes, verticalalignment='top',
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        
        if ax == axes[0]:
            ax.legend(loc='upper right', fontsize=8)
        
        plt.colorbar(h[3], ax=ax, label='Count')
    
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'figure1_outcome_distributions.png')
    plt.savefig(OUTPUT_DIR / 'figure1_outcome_distributions.pdf')
    print(f"✓ Saved Figure 1: {OUTPUT_DIR / 'figure1_outcome_distributions.png'}")
    plt.close()

def figure2_scatter_plots():
    """Figure 2: Scatter plots showing attractor separation."""
    fig, axes = plt.subplots(1, 3, figsize=(12, 4), sharey=True)
    
    batches = [
        ('batch_results/zero_no_uv', 'ZERO, no UV', 'A'),
        ('batch_results/zero_with_uv', 'ZERO + UV', 'B'),
        ('batch_results/balanced_with_uv', 'BALANCED + UV', 'C'),
    ]
    
    for ax, (batch_dir, title, panel) in zip(axes, batches):
        results = load_batch_results(batch_dir)
        
        ci_vals = [r['ci'] for r in results]
        cro_vals = [r['cro'] for r in results]
        outcomes = [classify_outcome(r['ci'], r['cro']) for r in results]
        
        # Color by outcome
        colors = {'lysogenic': 'blue', 'lytic': 'red', 'intermediate': 'gray'}
        for outcome in ['lysogenic', 'lytic', 'intermediate']:
            mask = [o == outcome for o in outcomes]
            ci_subset = [ci for ci, m in zip(ci_vals, mask) if m]
            cro_subset = [cro for cro, m in zip(cro_vals, mask) if m]
            ax.scatter(ci_subset, cro_subset, c=colors[outcome], 
                      alpha=0.6, s=30, label=outcome.capitalize())
        
        # Diagonal line
        ax.plot([0, 100], [0, 100], 'k--', alpha=0.3, linewidth=1)
        
        ax.set_xlabel('CI Dimer (mM)')
        if ax == axes[0]:
            ax.set_ylabel('Cro Dimer (mM)')
        ax.set_title(f'{panel}. {title}')
        ax.set_xlim(-5, 105)
        ax.set_ylim(-5, 105)
        ax.set_aspect('equal')
        ax.grid(True, alpha=0.3)
        ax.legend(loc='upper left', fontsize=8)
    
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'figure2_scatter_plots.png')
    plt.savefig(OUTPUT_DIR / 'figure2_scatter_plots.pdf')
    print(f"✓ Saved Figure 2: {OUTPUT_DIR / 'figure2_scatter_plots.png'}")
    plt.close()

def figure3_time_courses():
    """Figure 3: Example time course trajectories."""
    fig, axes = plt.subplots(2, 2, figsize=(10, 8))
    
    # Find example lysogenic and lytic trajectories
    batch_dir = Path('batch_results/zero_no_uv')
    
    lysogenic_file = None
    lytic_file = None
    
    for csv_file in sorted(batch_dir.glob('run_*.csv')):
        with open(csv_file, 'r') as f:
            data = list(csv.DictReader(f))
        
        if not data:
            continue
        
        final = data[-1]
        ci = float(final['P7'])
        cro = float(final['P8'])
        outcome = classify_outcome(ci, cro)
        
        if outcome == 'lysogenic' and lysogenic_file is None:
            lysogenic_file = csv_file
        elif outcome == 'lytic' and lytic_file is None:
            lytic_file = csv_file
        
        if lysogenic_file and lytic_file:
            break
    
    # Plot lysogenic example
    if lysogenic_file:
        with open(lysogenic_file, 'r') as f:
            data = list(csv.DictReader(f))
        
        times = [float(row['time']) for row in data]
        ci_vals = [float(row['P7']) for row in data]
        cro_vals = [float(row['P8']) for row in data]
        
        axes[0, 0].plot(times, ci_vals, 'b-', linewidth=2, label='CI Dimer')
        axes[0, 0].plot(times, cro_vals, 'r-', linewidth=2, label='Cro Dimer')
        axes[0, 0].set_ylabel('Concentration (mM)')
        axes[0, 0].set_title('A. Lysogenic Outcome (CI wins)')
        axes[0, 0].legend()
        axes[0, 0].grid(True, alpha=0.3)
        
        axes[1, 0].plot(ci_vals, cro_vals, 'g-', linewidth=1, alpha=0.6)
        axes[1, 0].scatter([ci_vals[0]], [cro_vals[0]], c='green', s=100, 
                          marker='o', label='Start', zorder=5)
        axes[1, 0].scatter([ci_vals[-1]], [cro_vals[-1]], c='blue', s=100, 
                          marker='*', label='End (Lysogenic)', zorder=5)
        axes[1, 0].set_xlabel('CI Dimer (mM)')
        axes[1, 0].set_ylabel('Cro Dimer (mM)')
        axes[1, 0].set_title('C. Phase Portrait (Lysogenic)')
        axes[1, 0].legend()
        axes[1, 0].grid(True, alpha=0.3)
        axes[1, 0].set_aspect('equal')
    
    # Plot lytic example
    if lytic_file:
        with open(lytic_file, 'r') as f:
            data = list(csv.DictReader(f))
        
        times = [float(row['time']) for row in data]
        ci_vals = [float(row['P7']) for row in data]
        cro_vals = [float(row['P8']) for row in data]
        
        axes[0, 1].plot(times, ci_vals, 'b-', linewidth=2, label='CI Dimer')
        axes[0, 1].plot(times, cro_vals, 'r-', linewidth=2, label='Cro Dimer')
        axes[0, 1].set_ylabel('Concentration (mM)')
        axes[0, 1].set_title('B. Lytic Outcome (Cro wins)')
        axes[0, 1].legend()
        axes[0, 1].grid(True, alpha=0.3)
        
        axes[1, 1].plot(ci_vals, cro_vals, 'g-', linewidth=1, alpha=0.6)
        axes[1, 1].scatter([ci_vals[0]], [cro_vals[0]], c='green', s=100, 
                          marker='o', label='Start', zorder=5)
        axes[1, 1].scatter([ci_vals[-1]], [cro_vals[-1]], c='red', s=100, 
                          marker='*', label='End (Lytic)', zorder=5)
        axes[1, 1].set_xlabel('CI Dimer (mM)')
        axes[1, 1].set_ylabel('Cro Dimer (mM)')
        axes[1, 1].set_title('D. Phase Portrait (Lytic)')
        axes[1, 1].legend()
        axes[1, 1].grid(True, alpha=0.3)
        axes[1, 1].set_aspect('equal')
    
    for ax in axes.flat:
        ax.set_xlabel('Time (s)' if 'Phase' not in ax.get_title() else ax.get_xlabel())
    
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'figure3_time_courses.png')
    plt.savefig(OUTPUT_DIR / 'figure3_time_courses.pdf')
    print(f"✓ Saved Figure 3: {OUTPUT_DIR / 'figure3_time_courses.png'}")
    plt.close()

def figure4_rate_symmetry():
    """Figure 4: Demonstrate symmetric rate functions."""
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    
    # Parameter space
    protein_range = np.linspace(0, 100, 200)
    
    # T1: CI transcription repressed by Cro
    def t1_rate(ci_dimer, cro_dimer):
        return 2.0 * (1 + 0.5 * ci_dimer / (5 + ci_dimer)) / (1 + (cro_dimer / 15)**2)
    
    # T6: Cro transcription repressed by CI
    def t6_rate(cro_dimer, ci_dimer):
        return 2.0 * (1 + 0.5 * cro_dimer / (5 + cro_dimer)) / (1 + (ci_dimer / 15)**2)
    
    # Plot 1: Effect of self-activation
    ax = axes[0]
    for repressor in [0, 10, 30]:
        rates_ci = [t1_rate(ci, repressor) for ci in protein_range]
        rates_cro = [t6_rate(cro, repressor) for cro in protein_range]
        
        ax.plot(protein_range, rates_ci, 'b-', linewidth=2, 
               label=f'T1 (CI), Cro={repressor}' if repressor == 0 else '', alpha=0.7)
        ax.plot(protein_range, rates_cro, 'r--', linewidth=2, 
               label=f'T6 (Cro), CI={repressor}' if repressor == 0 else '', alpha=0.7)
    
    ax.set_xlabel('Self Protein Dimer (mM)')
    ax.set_ylabel('Transcription Rate (mM/s)')
    ax.set_title('A. Positive Feedback (saturating)')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Plot 2: Effect of repression
    ax = axes[1]
    for self_protein in [0, 50]:
        rates_ci = [t1_rate(self_protein, cro) for cro in protein_range]
        rates_cro = [t6_rate(self_protein, ci) for ci in protein_range]
        
        label_ci = f'T1, CI={self_protein}' if self_protein in [0, 50] else ''
        label_cro = f'T6, Cro={self_protein}' if self_protein in [0, 50] else ''
        
        ax.plot(protein_range, rates_ci, 'b-', linewidth=2, 
               label=label_ci, alpha=0.7)
        ax.plot(protein_range, rates_cro, 'r--', linewidth=2, 
               label=label_cro, alpha=0.7)
    
    ax.set_xlabel('Repressor Dimer (mM)')
    ax.set_ylabel('Transcription Rate (mM/s)')
    ax.set_title('B. Mutual Repression (Hill n=2, Ki=15)')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'figure4_rate_symmetry.png')
    plt.savefig(OUTPUT_DIR / 'figure4_rate_symmetry.pdf')
    print(f"✓ Saved Figure 4: {OUTPUT_DIR / 'figure4_rate_symmetry.png'}")
    plt.close()

def figure5_summary_bars():
    """Figure 5: Summary bar chart comparing all conditions."""
    fig, ax = plt.subplots(1, 1, figsize=(10, 6))
    
    batches = [
        ('batch_results/zero_no_uv', 'ZERO\nno UV'),
        ('batch_results/zero_with_uv', 'ZERO\n+ UV'),
        ('batch_results/balanced_with_uv', 'BALANCED\n+ UV'),
    ]
    
    lysogenic_counts = []
    lytic_counts = []
    intermediate_counts = []
    
    for batch_dir, _ in batches:
        results = load_batch_results(batch_dir)
        
        lysogenic = sum(1 for r in results if classify_outcome(r['ci'], r['cro']) == 'lysogenic')
        lytic = sum(1 for r in results if classify_outcome(r['ci'], r['cro']) == 'lytic')
        intermediate = sum(1 for r in results if classify_outcome(r['ci'], r['cro']) == 'intermediate')
        
        lysogenic_counts.append(lysogenic)
        lytic_counts.append(lytic)
        intermediate_counts.append(intermediate)
    
    x = np.arange(len(batches))
    width = 0.25
    
    ax.bar(x - width, lysogenic_counts, width, label='Lysogenic', color='blue', alpha=0.8)
    ax.bar(x, lytic_counts, width, label='Lytic', color='red', alpha=0.8)
    ax.bar(x + width, intermediate_counts, width, label='Intermediate', color='gray', alpha=0.8)
    
    ax.set_xlabel('Condition')
    ax.set_ylabel('Number of Replicates (out of 100)')
    ax.set_title('Lambda Phage Decision Outcomes Across Conditions')
    ax.set_xticks(x)
    ax.set_xticklabels([label for _, label in batches])
    ax.legend()
    ax.grid(True, axis='y', alpha=0.3)
    
    # Add percentage labels
    for i, (lys, lyt, inter) in enumerate(zip(lysogenic_counts, lytic_counts, intermediate_counts)):
        total = lys + lyt + inter
        if total > 0:
            ax.text(i - width, lys + 2, f'{100*lys/total:.0f}%', 
                   ha='center', va='bottom', fontsize=9)
            ax.text(i, lyt + 2, f'{100*lyt/total:.0f}%', 
                   ha='center', va='bottom', fontsize=9)
            if inter > 0:
                ax.text(i + width, inter + 2, f'{100*inter/total:.0f}%', 
                       ha='center', va='bottom', fontsize=9)
    
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'figure5_summary_bars.png')
    plt.savefig(OUTPUT_DIR / 'figure5_summary_bars.pdf')
    print(f"✓ Saved Figure 5: {OUTPUT_DIR / 'figure5_summary_bars.png'}")
    plt.close()

def main():
    """Generate all figures."""
    print("=" * 80)
    print("Generating Publication Figures for Lambda Phage Bistable Switch")
    print("=" * 80)
    
    print("\nGenerating figures...")
    
    try:
        figure1_outcome_distributions()
        figure2_scatter_plots()
        figure3_time_courses()
        figure4_rate_symmetry()
        figure5_summary_bars()
        
        print("\n" + "=" * 80)
        print("✓ All figures generated successfully!")
        print(f"✓ Output directory: {OUTPUT_DIR.absolute()}")
        print("=" * 80)
        
        print("\nFigure descriptions:")
        print("  Figure 1: 2D histograms showing final CI vs Cro distributions")
        print("  Figure 2: Scatter plots with outcome classification")
        print("  Figure 3: Time course examples (lysogenic and lytic)")
        print("  Figure 4: Rate function symmetry demonstration")
        print("  Figure 5: Summary bar chart of outcomes")
        
    except Exception as e:
        print(f"\n❌ Error generating figures: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
