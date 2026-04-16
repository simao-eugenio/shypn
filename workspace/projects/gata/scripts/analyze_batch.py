#!/usr/bin/env python3
"""
Analyze batch simulation results for GATA1/PU.1 bistability project.

This script processes 100 replicate simulations to:
1. Determine final fate (ERYTHROID vs MYELOID) for each replicate
2. Calculate commitment times
3. Generate distribution plots
4. Compute statistics and validate bistability
"""

import os
import sys
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Dict, List, Tuple

# === PARAMETERS ===
RATIO_THRESHOLD = 2.5  # GATA1/PU1 ratio for fate classification
COMMITMENT_THRESHOLD = 2.5  # Same threshold for commitment detection
MIN_COMMITMENT_TIME = 10.0  # seconds (ignore very early noise)

class BatchAnalyzer:
    def __init__(self, batch_dir: str):
        self.batch_dir = Path(batch_dir)
        self.results = []
        
    def load_config(self):
        """Load batch configuration."""
        config_path = self.batch_dir / "config.json"
        with open(config_path, 'r') as f:
            return json.load(f)
    
    def analyze_single_run(self, run_file: Path) -> Dict:
        """Analyze a single replicate."""
        # Read CSV, skipping comment lines
        df = pd.read_csv(run_file, comment='#')
        
        # Extract protein concentrations (P3=GATA1_Protein, P6=PU1_Protein)
        time = df['time'].values
        gata1 = df['P3'].values  # GATA1_Protein
        pu1 = df['P6'].values    # PU1_Protein
        
        # Calculate ratio trajectory
        ratio = gata1 / (pu1 + 1e-9)  # Add epsilon to avoid division by zero
        
        # Determine final fate
        final_gata1 = gata1[-1]
        final_pu1 = pu1[-1]
        final_ratio = final_gata1 / (final_pu1 + 1e-9)
        
        if final_ratio > RATIO_THRESHOLD:
            fate = "ERYTHROID"
        elif final_ratio < 1.0 / RATIO_THRESHOLD:
            fate = "MYELOID"
        else:
            fate = "UNCOMMITTED"
        
        # Find commitment time (when ratio first crosses threshold and stays there)
        commitment_time = None
        if fate == "ERYTHROID":
            # Find when ratio > COMMITMENT_THRESHOLD
            committed_indices = np.where((ratio > COMMITMENT_THRESHOLD) & (time > MIN_COMMITMENT_TIME))[0]
            if len(committed_indices) > 0:
                # Check if it stays committed (doesn't cross back)
                first_commit_idx = committed_indices[0]
                if np.all(ratio[first_commit_idx:] > COMMITMENT_THRESHOLD):
                    commitment_time = time[first_commit_idx]
        
        elif fate == "MYELOID":
            # Find when ratio < 1/COMMITMENT_THRESHOLD
            committed_indices = np.where((ratio < 1.0/COMMITMENT_THRESHOLD) & (time > MIN_COMMITMENT_TIME))[0]
            if len(committed_indices) > 0:
                first_commit_idx = committed_indices[0]
                if np.all(ratio[first_commit_idx:] < 1.0/COMMITMENT_THRESHOLD):
                    commitment_time = time[first_commit_idx]
        
        return {
            'run_file': run_file.name,
            'fate': fate,
            'final_gata1': final_gata1,
            'final_pu1': final_pu1,
            'final_ratio': final_ratio,
            'commitment_time': commitment_time,
            'trajectory': {
                'time': time,
                'gata1': gata1,
                'pu1': pu1,
                'ratio': ratio
            }
        }
    
    def analyze_all_runs(self):
        """Analyze all replicates in batch."""
        run_files = sorted(self.batch_dir.glob("run_*.csv"))
        
        print(f"Analyzing {len(run_files)} replicates...")
        
        for i, run_file in enumerate(run_files, 1):
            if i % 10 == 0:
                print(f"  Processed {i}/{len(run_files)} runs...")
            
            result = self.analyze_single_run(run_file)
            self.results.append(result)
        
        print(f"✓ Completed analysis of {len(self.results)} replicates")
    
    def compute_statistics(self) -> Dict:
        """Compute summary statistics."""
        fates = [r['fate'] for r in self.results]
        n_erythroid = fates.count("ERYTHROID")
        n_myeloid = fates.count("MYELOID")
        n_uncommitted = fates.count("UNCOMMITTED")
        n_total = len(fates)
        
        # Commitment times (excluding None)
        erythroid_times = [r['commitment_time'] for r in self.results 
                          if r['fate'] == "ERYTHROID" and r['commitment_time'] is not None]
        myeloid_times = [r['commitment_time'] for r in self.results 
                        if r['fate'] == "MYELOID" and r['commitment_time'] is not None]
        
        all_commit_times = erythroid_times + myeloid_times
        
        # Final ratios
        erythroid_ratios = [r['final_ratio'] for r in self.results if r['fate'] == "ERYTHROID"]
        myeloid_ratios = [r['final_ratio'] for r in self.results if r['fate'] == "MYELOID"]
        
        stats = {
            'n_total': n_total,
            'n_erythroid': n_erythroid,
            'n_myeloid': n_myeloid,
            'n_uncommitted': n_uncommitted,
            'pct_erythroid': 100.0 * n_erythroid / n_total,
            'pct_myeloid': 100.0 * n_myeloid / n_total,
            'pct_uncommitted': 100.0 * n_uncommitted / n_total,
            'erythroid_mean_time': np.mean(erythroid_times) if erythroid_times else None,
            'erythroid_std_time': np.std(erythroid_times) if erythroid_times else None,
            'myeloid_mean_time': np.mean(myeloid_times) if myeloid_times else None,
            'myeloid_std_time': np.std(myeloid_times) if myeloid_times else None,
            'overall_mean_time': np.mean(all_commit_times) if all_commit_times else None,
            'overall_std_time': np.std(all_commit_times) if all_commit_times else None,
            'erythroid_mean_ratio': np.mean(erythroid_ratios) if erythroid_ratios else None,
            'erythroid_std_ratio': np.std(erythroid_ratios) if erythroid_ratios else None,
            'myeloid_mean_ratio': np.mean(myeloid_ratios) if myeloid_ratios else None,
            'myeloid_std_ratio': np.std(myeloid_ratios) if myeloid_ratios else None,
        }
        
        return stats
    
    def validate_bistability(self, stats: Dict) -> Dict:
        """Validate bistability against Lambda Phage benchmark."""
        checks = {}
        
        # Check 1: Bimodal distribution (both fates present)
        checks['bimodal'] = (stats['n_erythroid'] > 10 and stats['n_myeloid'] > 10)
        
        # Check 2: Balanced fates (30:70 to 70:30 range, Lambda Phage is 42:48)
        balance_ratio = stats['n_erythroid'] / (stats['n_myeloid'] + 1e-9)
        checks['balanced'] = (0.43 <= balance_ratio <= 2.33)  # 30:70 to 70:30
        
        # Check 3: Strong separation (ratios clearly distinct)
        if stats['erythroid_mean_ratio'] and stats['myeloid_mean_ratio']:
            separation = stats['erythroid_mean_ratio'] / (stats['myeloid_mean_ratio'] + 1e-9)
            checks['separated'] = (separation > 10.0)  # >10x difference
        else:
            checks['separated'] = False
        
        # Check 4: Reasonable commitment times (10-500 seconds)
        if stats['overall_mean_time']:
            checks['timing'] = (10.0 <= stats['overall_mean_time'] <= 500.0)
        else:
            checks['timing'] = False
        
        # Check 5: Low uncommitted fraction (<5%)
        checks['decisive'] = (stats['pct_uncommitted'] < 5.0)
        
        checks['all_passed'] = all(checks.values())
        
        return checks
    
    def plot_results(self, stats: Dict, checks: Dict):
        """Generate comprehensive visualization."""
        fig = plt.figure(figsize=(16, 10))
        gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
        
        # === Panel 1: Fate distribution (pie chart) ===
        ax1 = fig.add_subplot(gs[0, 0])
        fates = [stats['n_erythroid'], stats['n_myeloid'], stats['n_uncommitted']]
        labels = [f"ERYTHROID\n({stats['pct_erythroid']:.1f}%)",
                 f"MYELOID\n({stats['pct_myeloid']:.1f}%)",
                 f"UNCOMMITTED\n({stats['pct_uncommitted']:.1f}%)"]
        colors = ['#e74c3c', '#3498db', '#95a5a6']
        ax1.pie(fates, labels=labels, colors=colors, autopct='%d', startangle=90)
        ax1.set_title('Fate Distribution (n=100)', fontweight='bold')
        
        # === Panel 2: Final ratio histogram ===
        ax2 = fig.add_subplot(gs[0, 1])
        erythroid_ratios = [r['final_ratio'] for r in self.results if r['fate'] == "ERYTHROID"]
        myeloid_ratios = [r['final_ratio'] for r in self.results if r['fate'] == "MYELOID"]
        
        # Log scale for better visualization
        if erythroid_ratios:
            ax2.hist(np.log10(erythroid_ratios), bins=20, alpha=0.6, color='#e74c3c', label='ERYTHROID')
        if myeloid_ratios:
            ax2.hist(np.log10(myeloid_ratios), bins=20, alpha=0.6, color='#3498db', label='MYELOID')
        
        ax2.axvline(np.log10(RATIO_THRESHOLD), color='black', linestyle='--', linewidth=1.5, label='Threshold')
        ax2.axvline(np.log10(1.0/RATIO_THRESHOLD), color='black', linestyle='--', linewidth=1.5)
        ax2.set_xlabel('log₁₀(GATA1/PU1 Ratio)', fontweight='bold')
        ax2.set_ylabel('Frequency', fontweight='bold')
        ax2.set_title('Bimodal Distribution', fontweight='bold')
        ax2.legend()
        ax2.grid(alpha=0.3)
        
        # === Panel 3: Commitment time distribution ===
        ax3 = fig.add_subplot(gs[0, 2])
        erythroid_times = [r['commitment_time'] for r in self.results 
                          if r['fate'] == "ERYTHROID" and r['commitment_time'] is not None]
        myeloid_times = [r['commitment_time'] for r in self.results 
                        if r['fate'] == "MYELOID" and r['commitment_time'] is not None]
        
        if erythroid_times:
            ax3.hist(erythroid_times, bins=30, alpha=0.6, color='#e74c3c', label='ERYTHROID')
        if myeloid_times:
            ax3.hist(myeloid_times, bins=30, alpha=0.6, color='#3498db', label='MYELOID')
        
        ax3.set_xlabel('Commitment Time (seconds)', fontweight='bold')
        ax3.set_ylabel('Frequency', fontweight='bold')
        ax3.set_title('Commitment Timing', fontweight='bold')
        ax3.legend()
        ax3.grid(alpha=0.3)
        
        # === Panel 4: Sample trajectories (protein levels) ===
        ax4 = fig.add_subplot(gs[1, :2])
        
        # Plot 5 random ERYTHROID and 5 random MYELOID trajectories
        erythroid_results = [r for r in self.results if r['fate'] == "ERYTHROID"]
        myeloid_results = [r for r in self.results if r['fate'] == "MYELOID"]
        
        np.random.seed(42)
        sample_erythroid = np.random.choice(erythroid_results, min(5, len(erythroid_results)), replace=False)
        sample_myeloid = np.random.choice(myeloid_results, min(5, len(myeloid_results)), replace=False)
        
        for r in sample_erythroid:
            ax4.plot(r['trajectory']['time'], r['trajectory']['gata1'], 
                    color='#e74c3c', alpha=0.4, linewidth=1)
            ax4.plot(r['trajectory']['time'], r['trajectory']['pu1'], 
                    color='#3498db', alpha=0.4, linewidth=1)
        
        for r in sample_myeloid:
            ax4.plot(r['trajectory']['time'], r['trajectory']['gata1'], 
                    color='#e74c3c', alpha=0.4, linewidth=1)
            ax4.plot(r['trajectory']['time'], r['trajectory']['pu1'], 
                    color='#3498db', alpha=0.4, linewidth=1)
        
        # Add dummy lines for legend
        ax4.plot([], [], color='#e74c3c', linewidth=2, label='GATA1')
        ax4.plot([], [], color='#3498db', linewidth=2, label='PU.1')
        
        ax4.set_xlabel('Time (seconds)', fontweight='bold')
        ax4.set_ylabel('Protein (µM)', fontweight='bold')
        ax4.set_title('Sample Trajectories (10 runs)', fontweight='bold')
        ax4.legend()
        ax4.grid(alpha=0.3)
        
        # === Panel 5: Phase portrait overlay ===
        ax5 = fig.add_subplot(gs[1, 2])
        
        for r in sample_erythroid:
            ax5.plot(r['trajectory']['gata1'], r['trajectory']['pu1'], 
                    color='#e74c3c', alpha=0.5, linewidth=1)
        
        for r in sample_myeloid:
            ax5.plot(r['trajectory']['gata1'], r['trajectory']['pu1'], 
                    color='#3498db', alpha=0.5, linewidth=1)
        
        # Add diagonal threshold line
        max_val = 150
        ax5.plot([0, max_val], [0, max_val/RATIO_THRESHOLD], 'k--', linewidth=1.5, label='Threshold')
        ax5.plot([0, max_val], [0, max_val*RATIO_THRESHOLD], 'k--', linewidth=1.5)
        
        ax5.set_xlabel('GATA1 (µM)', fontweight='bold')
        ax5.set_ylabel('PU.1 (µM)', fontweight='bold')
        ax5.set_title('Phase Portrait', fontweight='bold')
        ax5.set_xlim(0, max_val)
        ax5.set_ylim(0, max_val)
        ax5.legend()
        ax5.grid(alpha=0.3)
        
        # === Panel 6: Statistics table ===
        ax6 = fig.add_subplot(gs[2, :])
        ax6.axis('off')
        
        # Create statistics text
        stats_text = f"""
BATCH ANALYSIS SUMMARY (n={stats['n_total']} replicates)

FATE DISTRIBUTION:
  • ERYTHROID: {stats['n_erythroid']} ({stats['pct_erythroid']:.1f}%)
  • MYELOID: {stats['n_myeloid']} ({stats['pct_myeloid']:.1f}%)
  • UNCOMMITTED: {stats['n_uncommitted']} ({stats['pct_uncommitted']:.1f}%)
  • Balance Ratio: {stats['n_erythroid']/(stats['n_myeloid']+1e-9):.2f}:1 (Lambda Phage benchmark: 0.88:1)

COMMITMENT TIMING:"""
        
        if stats['erythroid_mean_time'] is not None:
            stats_text += f"""
  • ERYTHROID: {stats['erythroid_mean_time']:.1f} ± {stats['erythroid_std_time']:.1f} sec (n={len([r for r in self.results if r['fate']=="ERYTHROID" and r['commitment_time']])})"""
        
        if stats['myeloid_mean_time'] is not None:
            stats_text += f"""
  • MYELOID: {stats['myeloid_mean_time']:.1f} ± {stats['myeloid_std_time']:.1f} sec (n={len([r for r in self.results if r['fate']=="MYELOID" and r['commitment_time']])})"""
        
        if stats['overall_mean_time'] is not None:
            stats_text += f"""
  • Overall: {stats['overall_mean_time']:.1f} ± {stats['overall_std_time']:.1f} sec"""
        
        stats_text += """

FINAL STATE SEPARATION:"""
        
        if stats['erythroid_mean_ratio'] is not None:
            stats_text += f"""
  • ERYTHROID ratio: {stats['erythroid_mean_ratio']:.1f} ± {stats['erythroid_std_ratio']:.1f}"""
        
        if stats['myeloid_mean_ratio'] is not None:
            stats_text += f"""
  • MYELOID ratio: {stats['myeloid_mean_ratio']:.3f} ± {stats['myeloid_std_ratio']:.3f}"""
        
        if stats['erythroid_mean_ratio'] is not None and stats['myeloid_mean_ratio'] is not None:
            stats_text += f"""
  • Separation factor: {stats['erythroid_mean_ratio']/(stats['myeloid_mean_ratio']+1e-9):.1f}×"""
        
        stats_text += f"""

VALIDATION CHECKS:
  ✓ Bimodal: {checks['bimodal']} (both fates present)
  ✓ Balanced: {checks['balanced']} (30:70 to 70:30 range)
  ✓ Separated: {checks['separated']} (>10× ratio difference)
  ✓ Timing: {checks['timing']} (10-500 sec range)
  ✓ Decisive: {checks['decisive']} (<5% uncommitted)
  
  OVERALL: {'✓ PASSED' if checks['all_passed'] else '✗ FAILED'}
"""
        
        ax6.text(0.05, 0.5, stats_text, transform=ax6.transAxes, 
                fontfamily='monospace', fontsize=10, verticalalignment='center')
        
        plt.suptitle('GATA1/PU.1 Bistability - Batch Analysis', 
                     fontsize=16, fontweight='bold', y=0.995)
        
        return fig
    
    def save_results(self, stats: Dict, checks: Dict):
        """Save analysis results to JSON."""
        # Convert numpy types and bools to native Python types for JSON serialization
        def convert_to_json_serializable(obj):
            if isinstance(obj, (np.integer, np.floating)):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, (bool, np.bool_)):
                return bool(obj)
            elif obj is None:
                return None
            else:
                return obj
        
        # Deep convert all values
        stats_serializable = {k: convert_to_json_serializable(v) for k, v in stats.items()}
        checks_serializable = {k: convert_to_json_serializable(v) for k, v in checks.items()}
        
        output = {
            'statistics': stats_serializable,
            'validation': checks_serializable,
            'replicates': [
                {
                    'run_file': r['run_file'],
                    'fate': r['fate'],
                    'final_gata1': float(r['final_gata1']),
                    'final_pu1': float(r['final_pu1']),
                    'final_ratio': float(r['final_ratio']),
                    'commitment_time': float(r['commitment_time']) if r['commitment_time'] is not None else None
                }
                for r in self.results
            ]
        }
        
        output_path = self.batch_dir / "batch_analysis.json"
        with open(output_path, 'w') as f:
            json.dump(output, f, indent=2)
        
        print(f"✓ Saved analysis to {output_path}")
        
        return output_path


def main():
    if len(sys.argv) < 2:
        print("Usage: python analyze_batch.py <batch_directory>")
        sys.exit(1)
    
    batch_dir = sys.argv[1]
    
    if not os.path.exists(batch_dir):
        print(f"Error: Directory not found: {batch_dir}")
        sys.exit(1)
    
    print("=" * 70)
    print("GATA1/PU.1 BATCH ANALYSIS")
    print("=" * 70)
    print()
    
    # Create analyzer
    analyzer = BatchAnalyzer(batch_dir)
    
    # Load configuration
    config = analyzer.load_config()
    print(f"Batch: {config['timestamp']}")
    print(f"Replicates: {config['n_replicates']}")
    print(f"Duration: {config['settings']['duration']} seconds")
    print()
    
    # Analyze all runs
    analyzer.analyze_all_runs()
    print()
    
    # Compute statistics
    stats = analyzer.compute_statistics()
    
    # Validate bistability
    checks = analyzer.validate_bistability(stats)
    
    # Display summary
    print("=" * 70)
    print("SUMMARY STATISTICS")
    print("=" * 70)
    print()
    print(f"Fate Distribution:")
    print(f"  ERYTHROID: {stats['n_erythroid']:3d} ({stats['pct_erythroid']:5.1f}%)")
    print(f"  MYELOID:   {stats['n_myeloid']:3d} ({stats['pct_myeloid']:5.1f}%)")
    print(f"  UNCOMMIT:  {stats['n_uncommitted']:3d} ({stats['pct_uncommitted']:5.1f}%)")
    print()
    print(f"Balance: {stats['n_erythroid']}:{stats['n_myeloid']} "
          f"({stats['n_erythroid']/(stats['n_myeloid']+1e-9):.2f}:1)")
    print(f"Lambda Phage benchmark: 42:48 (0.88:1)")
    print()
    
    if stats['overall_mean_time']:
        print(f"Commitment Time: {stats['overall_mean_time']:.1f} ± {stats['overall_std_time']:.1f} sec")
        print()
    
    print("Validation Checks:")
    for check_name, passed in checks.items():
        status = "✓" if passed else "✗"
        print(f"  {status} {check_name}")
    print()
    
    if checks['all_passed']:
        print("✓ BISTABILITY VALIDATED!")
    else:
        print("✗ Some validation checks failed")
    print()
    
    # Generate plots
    print("Generating plots...")
    fig = analyzer.plot_results(stats, checks)
    
    plot_path = Path(batch_dir) / "batch_analysis.png"
    fig.savefig(plot_path, dpi=300, bbox_inches='tight')
    print(f"✓ Saved plot to {plot_path}")
    print()
    
    # Save results
    analyzer.save_results(stats, checks)
    
    print("=" * 70)
    print("ANALYSIS COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()