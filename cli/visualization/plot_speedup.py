#!/usr/bin/env python3
"""
Plot Speedup Distribution (Figure 3)

Generates scatter plot of weak independence vs parallel speedup.

Usage:
    python plot_speedup.py \
        --input ../experimental_data/simulation_performance/speedup_data.csv \
        --output ../figures/speedup_plot.pdf

Author: Eugênio Simão
Date: 2025-12-04
"""

import argparse
import csv
import sys
from pathlib import Path

try:
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
except ImportError:
    print("Error: matplotlib not installed. Install with: pip install matplotlib", file=sys.stderr)
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description='Plot speedup distribution')
    parser.add_argument('--input', type=str, required=True,
                       help='Input CSV file with speedup data')
    parser.add_argument('--output', type=str, required=True,
                       help='Output PDF file')
    parser.add_argument('--title', type=str, default='Parallel Simulation Speedup',
                       help='Plot title')
    
    args = parser.parse_args()
    
    input_file = Path(args.input)
    output_file = Path(args.output)
    
    # Validate input
    if not input_file.exists():
        print(f"Error: Input file not found: {input_file}", file=sys.stderr)
        sys.exit(1)
    
    # Create output directory
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Read data
    print(f"Reading data from {input_file}...")
    
    data_by_category = {
        'Metabolic': {'x': [], 'y': []},
        'Signaling': {'x': [], 'y': []},
        'Regulatory': {'x': [], 'y': []},
        'Unknown': {'x': [], 'y': []}
    }
    
    with open(input_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['status'] != 'success':
                continue
            
            weak_indep = float(row['weakly_independent_pct'])
            speedup = float(row['speedup'])
            category = row.get('category', 'Unknown')
            
            if category not in data_by_category:
                category = 'Unknown'
            
            data_by_category[category]['x'].append(weak_indep)
            data_by_category[category]['y'].append(speedup)
    
    # Calculate statistics
    all_speedups = []
    for cat_data in data_by_category.values():
        all_speedups.extend(cat_data['y'])
    
    if not all_speedups:
        print("Error: No valid data points to plot", file=sys.stderr)
        sys.exit(1)
    
    mean_speedup = sum(all_speedups) / len(all_speedups)
    
    # Create plot
    print(f"Creating plot...")
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Color scheme
    colors = {
        'Metabolic': '#2E86AB',    # Blue
        'Signaling': '#A23B72',    # Purple
        'Regulatory': '#F18F01',   # Orange
        'Unknown': '#C73E1D'       # Red
    }
    
    # Plot each category
    for category, cat_data in data_by_category.items():
        if cat_data['x']:
            ax.scatter(cat_data['x'], cat_data['y'], 
                      c=colors[category], 
                      label=category,
                      s=50, 
                      alpha=0.7,
                      edgecolors='white',
                      linewidth=0.5)
    
    # Mean line
    ax.axhline(y=mean_speedup, color='black', linestyle='--', linewidth=1.5,
               label=f'Mean: {mean_speedup:.2f}×', alpha=0.7)
    
    # Formatting
    ax.set_xlabel('Weak Independence (%)', fontsize=12)
    ax.set_ylabel('Speedup (×)', fontsize=12)
    ax.set_title(args.title, fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3, linestyle=':')
    ax.legend(loc='upper left', framealpha=0.9)
    
    # Set axis limits
    ax.set_xlim(0, 100)
    ax.set_ylim(0, max(all_speedups) * 1.1)
    
    # Save
    print(f"Saving plot to {output_file}...")
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"\n✅ Plot saved to: {output_file}")
    print(f"   Data points: {len(all_speedups)}")
    print(f"   Mean speedup: {mean_speedup:.2f}×")
    print(f"   Max speedup: {max(all_speedups):.2f}×")


if __name__ == '__main__':
    main()
