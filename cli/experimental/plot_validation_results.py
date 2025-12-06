#!/usr/bin/env python3
"""Plot Validation Results - Visualize algorithm equivalence results"""
import argparse, sys, json
from pathlib import Path

def plot_validation(validation_data, output_path):
    """Generate validation comparison plot."""
    try:
        import matplotlib.pyplot as plt
        import numpy as np
        
        species_data = validation_data.get('species_comparison', {})
        summary = validation_data.get('summary', {})
        
        if not species_data:
            sys.exit("ERROR: No species comparison data found")
        
        # Extract data
        species = list(species_data.keys())
        tau_means = [species_data[s]['tau_mean'] for s in species]
        ssa_means = [species_data[s]['ssa_mean'] for s in species]
        rel_diffs = [species_data[s]['rel_diff'] * 100 for s in species]
        equivalent = [species_data[s]['equivalent'] for s in species]
        
        # Create figure with two subplots
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
        
        # Plot 1: Mean comparison
        x = np.arange(len(species))
        width = 0.35
        
        bars1 = ax1.bar(x - width/2, tau_means, width, label='τ-leaping', color='#2E86AB', alpha=0.8)
        bars2 = ax1.bar(x + width/2, ssa_means, width, label='Gillespie SSA', color='#A23B72', alpha=0.8)
        
        ax1.set_ylabel('Final Mean Abundance', fontsize=11)
        ax1.set_title('Algorithm Comparison: Final Means', fontsize=12, fontweight='bold')
        ax1.set_xticks(x)
        ax1.set_xticklabels(species, rotation=45, ha='right')
        ax1.legend()
        ax1.grid(axis='y', alpha=0.3)
        
        # Plot 2: Relative differences
        colors = ['#27AE60' if eq else '#E74C3C' for eq in equivalent]
        bars = ax2.bar(species, rel_diffs, color=colors, alpha=0.8)
        
        ax2.axhline(y=5, color='gray', linestyle='--', linewidth=1, alpha=0.5, label='5% threshold')
        ax2.set_ylabel('Relative Difference (%)', fontsize=11)
        ax2.set_title('Equivalence Analysis (5% tolerance)', fontsize=12, fontweight='bold')
        ax2.set_xticklabels(species, rotation=45, ha='right')
        ax2.legend()
        ax2.grid(axis='y', alpha=0.3)
        
        # Add summary text
        equiv_rate = summary.get('equivalence_rate', 0.0)
        n_equiv = summary.get('n_equivalent', 0)
        n_species = summary.get('n_species', 0)
        
        fig.text(0.5, 0.02, f'Equivalence: {n_equiv}/{n_species} species ({equiv_rate:.1%})',
                ha='center', fontsize=11, fontweight='bold',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))
        
        plt.tight_layout()
        plt.subplots_adjust(bottom=0.1)
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        print(f"✓ Plot saved: {output_path}")
        
    except ImportError:
        print("ERROR: matplotlib not installed. Install with: pip install matplotlib")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description='Plot validation results')
    parser.add_argument('validation_file', help='Path to validation_results.json')
    parser.add_argument('-o', '--output', default='validation_results.png')
    args = parser.parse_args()
    
    try:
        validation_path = Path(args.validation_file)
        if not validation_path.exists():
            sys.exit(f"ERROR: Validation file not found: {validation_path}")
        
        # Load validation data
        with open(validation_path, 'r') as f:
            data = json.load(f)
        
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        print(f"Generating validation plot...")
        plot_validation(data, output_path)
        
    except json.JSONDecodeError:
        sys.exit(f"ERROR: Invalid JSON in {args.validation_file}")
    except Exception as e:
        sys.exit(f"ERROR: {e}")

if __name__ == '__main__':
    main()
