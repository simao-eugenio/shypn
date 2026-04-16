#!/usr/bin/env python3
"""Benchmark script for parallel reachability analysis.

Measures speedup characteristics across different network sizes and worker counts.
Generates performance reports and scaling curves.

Usage:
    python benchmark_reachability.py [--workers 1,2,4,8] [--sizes small,medium,large]
    
Output:
    - Console report with speedup metrics
    - CSV file with detailed timing data
    - Performance plots (if matplotlib available)
"""

import argparse
import time
import csv
from pathlib import Path
from typing import Dict, List, Tuple
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from shypn.topology.behavioral.reachability import ReachabilityAnalyzer
from shypn.topology.behavioral.parallel_reachability import ParallelReachabilityAnalyzer


class ReachabilityBenchmark:
    """Benchmark harness for parallel reachability analysis."""
    
    def __init__(self, output_dir: Path = None):
        self.output_dir = output_dir or Path(__file__).parent / 'results'
        self.output_dir.mkdir(exist_ok=True)
        self.results = []
    
    def benchmark_model(self, model, name: str, worker_counts: List[int],
                       max_states: int = 10000) -> Dict:
        """Benchmark a model with varying worker counts."""
        print(f"\n{'='*60}")
        print(f"Benchmarking: {name}")
        print(f"{'='*60}")
        
        timings = {}
        
        # Sequential baseline
        print(f"\nRunning sequential baseline...")
        seq_analyzer = ReachabilityAnalyzer(model)
        start = time.time()
        seq_result = seq_analyzer.analyze(max_states=max_states)
        seq_time = time.time() - start
        timings[1] = seq_time
        
        total_states = seq_result.get('total_states', 0)
        print(f"  States explored: {total_states}")
        print(f"  Time: {seq_time:.3f}s")
        print(f"  Throughput: {total_states / seq_time:.0f} states/sec")
        
        # Parallel with varying workers
        for num_workers in worker_counts:
            if num_workers == 1:
                continue  # Already did sequential
            
            print(f"\nRunning parallel with {num_workers} workers...")
            par_analyzer = ParallelReachabilityAnalyzer(model, num_workers=num_workers)
            start = time.time()
            par_result = par_analyzer.analyze(max_states=max_states, parallel=True)
            par_time = time.time() - start
            timings[num_workers] = par_time
            
            speedup = seq_time / par_time
            efficiency = speedup / num_workers * 100
            
            print(f"  Time: {par_time:.3f}s")
            print(f"  Speedup: {speedup:.2f}×")
            print(f"  Efficiency: {efficiency:.1f}%")
            print(f"  Throughput: {total_states / par_time:.0f} states/sec")
            
            # Record result
            self.results.append({
                'model': name,
                'workers': num_workers,
                'time': par_time,
                'speedup': speedup,
                'efficiency': efficiency,
                'states': total_states,
                'throughput': total_states / par_time
            })
        
        return timings
    
    def generate_report(self):
        """Generate CSV report of benchmark results."""
        csv_path = self.output_dir / f'benchmark_{int(time.time())}.csv'
        
        with open(csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'model', 'workers', 'time', 'speedup', 'efficiency', 
                'states', 'throughput'
            ])
            writer.writeheader()
            writer.writerows(self.results)
        
        print(f"\n{'='*60}")
        print(f"Results saved to: {csv_path}")
        print(f"{'='*60}")
    
    def plot_results(self):
        """Generate performance plots (requires matplotlib)."""
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            print("matplotlib not available, skipping plots")
            return
        
        # Group by model
        models = {}
        for result in self.results:
            name = result['model']
            if name not in models:
                models[name] = {'workers': [], 'speedup': [], 'efficiency': []}
            models[name]['workers'].append(result['workers'])
            models[name]['speedup'].append(result['speedup'])
            models[name]['efficiency'].append(result['efficiency'])
        
        # Plot speedup curves
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        
        for name, data in models.items():
            ax1.plot(data['workers'], data['speedup'], marker='o', label=name)
            ax2.plot(data['workers'], data['efficiency'], marker='s', label=name)
        
        # Ideal speedup line
        max_workers = max(max(data['workers']) for data in models.values())
        ax1.plot([1, max_workers], [1, max_workers], 'k--', alpha=0.5, label='Ideal')
        
        ax1.set_xlabel('Number of Workers')
        ax1.set_ylabel('Speedup (×)')
        ax1.set_title('Parallel Speedup')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        ax2.set_xlabel('Number of Workers')
        ax2.set_ylabel('Efficiency (%)')
        ax2.set_title('Parallel Efficiency')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        ax2.axhline(y=100, color='k', linestyle='--', alpha=0.5)
        
        plt.tight_layout()
        plot_path = self.output_dir / f'speedup_{int(time.time())}.png'
        plt.savefig(plot_path, dpi=150)
        print(f"Plot saved to: {plot_path}")


def create_test_models():
    """Create test models for benchmarking."""
    # TODO: Implement test model generation
    # For now, return placeholder
    return {
        'small': None,   # 10 places, simple structure
        'medium': None,  # 50 places, moderate branching
        'large': None,   # 200 places, complex structure
    }


def main():
    parser = argparse.ArgumentParser(description='Benchmark parallel reachability')
    parser.add_argument('--workers', default='1,2,4,8',
                       help='Comma-separated worker counts (default: 1,2,4,8)')
    parser.add_argument('--sizes', default='small,medium,large',
                       help='Model sizes to test (default: small,medium,large)')
    parser.add_argument('--max-states', type=int, default=10000,
                       help='Maximum states to explore (default: 10000)')
    parser.add_argument('--output', type=Path, default=None,
                       help='Output directory for results')
    parser.add_argument('--plot', action='store_true',
                       help='Generate performance plots')
    
    args = parser.parse_args()
    
    # Parse arguments
    worker_counts = [int(w) for w in args.workers.split(',')]
    sizes = args.sizes.split(',')
    
    # Create benchmark harness
    benchmark = ReachabilityBenchmark(output_dir=args.output)
    
    # Load test models
    models = create_test_models()
    
    # Run benchmarks
    for size in sizes:
        if size not in models:
            print(f"Warning: Unknown model size '{size}', skipping")
            continue
        
        model = models[size]
        if model is None:
            print(f"Warning: Model '{size}' not implemented, skipping")
            continue
        
        benchmark.benchmark_model(
            model=model,
            name=size,
            worker_counts=worker_counts,
            max_states=args.max_states
        )
    
    # Generate report
    benchmark.generate_report()
    
    # Generate plots if requested
    if args.plot:
        benchmark.plot_results()


if __name__ == '__main__':
    main()
