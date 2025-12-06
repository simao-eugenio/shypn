#!/usr/bin/env python3
"""Plot Speedup Analysis - Visualize performance benchmark results"""
import _fix_imports  # Add src to path
import argparse, sys, json
from pathlib import Path

def plot_speedup(benchmark_data, output_path):
    """Generate speedup plot from benchmark data."""
    try:
        import matplotlib.pyplot as plt
        import numpy as np
        
        # Extract data
        tau = benchmark_data.get('tau_leaping', {})
        gill = benchmark_data.get('gillespie', {})
        speedup = benchmark_data.get('speedup', 1.0)
        
        if not tau or not gill:
            print("WARNING: Missing algorithm data, cannot generate comparison plot")
            return
        
        # Create figure with two subplots
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        
        # Plot 1: Execution time comparison
        algorithms = ['τ-leaping', 'Gillespie SSA']
        times = [tau['total_time'], gill['total_time']]
        colors = ['#2E86AB', '#A23B72']
        
        bars = ax1.bar(algorithms, times, color=colors, alpha=0.8)
        ax1.set_ylabel('Total Time (seconds)', fontsize=11)
        ax1.set_title('Execution Time Comparison', fontsize=12, fontweight='bold')
        ax1.grid(axis='y', alpha=0.3)
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.2f}s',
                    ha='center', va='bottom', fontsize=10)
        
        # Plot 2: Speedup factor
        ax2.barh(['Speedup'], [speedup], color='#F18F01', alpha=0.8, height=0.5)
        ax2.set_xlabel('Speedup Factor', fontsize=11)
        ax2.set_title(f'τ-leaping Speedup: {speedup:.2f}x', fontsize=12, fontweight='bold')
        ax2.grid(axis='x', alpha=0.3)
        
        # Add speedup annotation
        ax2.text(speedup, 0, f'  {speedup:.2f}x', va='center', fontsize=12, fontweight='bold')
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        print(f"✓ Plot saved: {output_path}")
        
    except ImportError:
        print("ERROR: matplotlib not installed. Install with: pip install matplotlib")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description='Plot speedup analysis results')
    parser.add_argument('benchmark_file', help='Path to benchmark_results.json')
    parser.add_argument('-o', '--output', default='speedup_analysis.png')
    args = parser.parse_args()
    
    try:
        benchmark_path = Path(args.benchmark_file)
        if not benchmark_path.exists():
            sys.exit(f"ERROR: Benchmark file not found: {benchmark_path}")
        
        # Load benchmark data
        with open(benchmark_path, 'r') as f:
            data = json.load(f)
        
        # Validate data
        if 'tau_leaping' not in data:
            sys.exit("ERROR: Missing 'tau_leaping' data in benchmark file")
        
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        print(f"Generating speedup plot...")
        plot_speedup(data, output_path)
        
    except json.JSONDecodeError:
        sys.exit(f"ERROR: Invalid JSON in {args.benchmark_file}")
    except Exception as e:
        sys.exit(f"ERROR: {e}")

if __name__ == '__main__':
    main()
