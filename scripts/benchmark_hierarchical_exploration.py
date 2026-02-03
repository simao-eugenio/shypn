#!/usr/bin/env python3
"""Benchmark suite for hierarchical exploration performance.

Compares Phase 1 (parallel basic), Phase 2 (maximal sets), and Phase 3 
(hierarchical) exploration strategies on biological models of varying sizes.

Usage:
    python scripts/benchmark_hierarchical_exploration.py [--model MODEL] [--max-states N]

Author: Simão Eugénio
Date: February 3, 2026
"""

import sys
import os
import time
import argparse
import json
from pathlib import Path
from typing import Dict, Any, List
import logging

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BenchmarkResult:
    """Container for benchmark results."""
    
    def __init__(
        self,
        strategy: str,
        model_name: str,
        num_places: int,
        num_transitions: int,
        execution_time: float,
        states_explored: int,
        transitions_fired: int,
        deadlocks_found: int,
        memory_mb: float = 0.0,
        extra_metrics: Dict[str, Any] = None
    ):
        self.strategy = strategy
        self.model_name = model_name
        self.num_places = num_places
        self.num_transitions = num_transitions
        self.execution_time = execution_time
        self.states_explored = states_explored
        self.transitions_fired = transitions_fired
        self.deadlocks_found = deadlocks_found
        self.memory_mb = memory_mb
        self.extra_metrics = extra_metrics or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'strategy': self.strategy,
            'model_name': self.model_name,
            'model_size': {
                'places': self.num_places,
                'transitions': self.num_transitions
            },
            'performance': {
                'execution_time_s': self.execution_time,
                'states_explored': self.states_explored,
                'transitions_fired': self.transitions_fired,
                'deadlocks_found': self.deadlocks_found,
                'memory_mb': self.memory_mb
            },
            'extra_metrics': self.extra_metrics
        }
    
    def __repr__(self) -> str:
        return (
            f"BenchmarkResult({self.strategy}, {self.model_name}: "
            f"{self.states_explored} states in {self.execution_time:.3f}s)"
        )


class HierarchicalBenchmark:
    """Benchmark runner for hierarchical exploration."""
    
    def __init__(self, output_dir: str = "benchmark_results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.results: List[BenchmarkResult] = []
    
    def benchmark_hierarchical(
        self,
        model: Any,
        model_name: str,
        initial_marking: Dict[str, int],
        max_states: int = 10000,
        max_depth: int = 100,
        use_parallel: bool = False,
        num_workers: int = 4
    ) -> BenchmarkResult:
        """Benchmark Phase 3 hierarchical exploration.
        
        Args:
            model: Petri net model
            model_name: Name for reporting
            initial_marking: Initial marking
            max_states: Maximum states to explore
            max_depth: Maximum depth
            use_parallel: Enable parallel exploration
            num_workers: Number of worker processes
            
        Returns:
            BenchmarkResult with performance metrics
        """
        from shypn.topology.behavioral.exploration import HierarchicalExplorer
        import tracemalloc
        
        mode_str = f"parallel ({num_workers} workers)" if use_parallel else "sequential"
        logger.info(f"Benchmarking hierarchical exploration ({mode_str}) on {model_name}...")
        
        # Track memory
        tracemalloc.start()
        
        # Create explorer
        explorer = HierarchicalExplorer(model)
        
        # Run exploration
        start_time = time.time()
        result = explorer.explore(
            initial_marking,
            max_states=max_states,
            max_depth=max_depth,
            find_deadlocks=True,
            use_parallel=use_parallel,
            num_workers=num_workers
        )
        execution_time = time.time() - start_time
        
        # Get memory usage
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        memory_mb = peak / 1024 / 1024
        
        # Extract metrics
        strategy_name = f"Phase 3: Hierarchical ({mode_str})"
        benchmark_result = BenchmarkResult(
            strategy=strategy_name,
            model_name=model_name,
            num_places=len(model.places) if hasattr(model, 'places') else 0,
            num_transitions=len(model.transitions) if hasattr(model, 'transitions') else 0,
            execution_time=execution_time,
            states_explored=result['total_states'],
            transitions_fired=result['total_transitions'],
            deadlocks_found=len(result['deadlocks']),
            memory_mb=memory_mb,
            extra_metrics={
                'layer_count': result.get('layer_count', 0),
                'exploration_mode': result.get('exploration_mode', 'unknown'),
                'parallel': use_parallel,
                'num_workers': num_workers if use_parallel else 0
            }
        )
        
        logger.info(
            f"  ✓ {benchmark_result.states_explored} states, "
            f"{benchmark_result.execution_time:.3f}s, "
            f"{benchmark_result.memory_mb:.1f}MB"
        )
        
        self.results.append(benchmark_result)
        return benchmark_result
    
    def compare_strategies(
        self,
        model: Any,
        model_name: str,
        initial_marking: Dict[str, int],
        max_states: int = 10000
    ) -> Dict[str, BenchmarkResult]:
        """Compare all exploration strategies.
        
        Args:
            model: Petri net model
            model_name: Name for reporting
            initial_marking: Initial marking
            max_states: Maximum states to explore
            
        Returns:
            Dict mapping strategy name to BenchmarkResult
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"Comparing strategies on {model_name}")
        logger.info(f"{'='*60}\n")
        
        results = {}
        
        # Benchmark Phase 3 (hierarchical) - Sequential
        results['hierarchical_seq'] = self.benchmark_hierarchical(
            model, model_name, initial_marking, max_states,
            use_parallel=False
        )
        
        # Benchmark Phase 3 (hierarchical) - Parallel
        results['hierarchical_par'] = self.benchmark_hierarchical(
            model, model_name, initial_marking, max_states,
            use_parallel=True, num_workers=4
        )
        
        # TODO: Add Phase 1 and Phase 2 benchmarks when integrated
        # results['parallel_basic'] = self.benchmark_parallel_basic(...)
        # results['maximal_sets'] = self.benchmark_maximal_sets(...)
        
        return results
    
    def generate_report(self, output_file: str = "benchmark_report.json"):
        """Generate benchmark report.
        
        Args:
            output_file: Output filename
        """
        report = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'results': [r.to_dict() for r in self.results],
            'summary': self._compute_summary()
        }
        
        output_path = self.output_dir / output_file
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"\n📊 Benchmark report saved to {output_path}")
        self._print_summary()
    
    def _compute_summary(self) -> Dict[str, Any]:
        """Compute summary statistics."""
        if not self.results:
            return {}
        
        total_time = sum(r.execution_time for r in self.results)
        total_states = sum(r.states_explored for r in self.results)
        avg_time = total_time / len(self.results)
        
        return {
            'total_benchmarks': len(self.results),
            'total_time': total_time,
            'total_states_explored': total_states,
            'average_time': avg_time,
            'strategies': list(set(r.strategy for r in self.results))
        }
    
    def _print_summary(self):
        """Print summary to console."""
        summary = self._compute_summary()
        
        logger.info("\n" + "="*60)
        logger.info("BENCHMARK SUMMARY")
        logger.info("="*60)
        logger.info(f"Total benchmarks: {summary.get('total_benchmarks', 0)}")
        logger.info(f"Total execution time: {summary.get('total_time', 0):.2f}s")
        logger.info(f"Total states explored: {summary.get('total_states_explored', 0):,}")
        logger.info(f"Average time per benchmark: {summary.get('average_time', 0):.2f}s")
        logger.info(f"Strategies tested: {', '.join(summary.get('strategies', []))}")
        
        logger.info("\n" + "-"*60)
        logger.info("DETAILED RESULTS")
        logger.info("-"*60)
        
        for result in self.results:
            logger.info(f"\n{result.model_name} ({result.strategy}):")
            logger.info(f"  Model size: {result.num_places} places, {result.num_transitions} transitions")
            logger.info(f"  Execution time: {result.execution_time:.3f}s")
            logger.info(f"  States explored: {result.states_explored:,}")
            logger.info(f"  Transitions fired: {result.transitions_fired:,}")
            logger.info(f"  Deadlocks found: {result.deadlocks_found}")
            logger.info(f"  Memory usage: {result.memory_mb:.1f}MB")
            
            if result.extra_metrics:
                logger.info(f"  Extra metrics: {result.extra_metrics}")
        
        logger.info("\n" + "="*60)


def create_test_model():
    """Create a test model for benchmarking.
    
    Returns:
        Mock model object
    """
    class MockPlace:
        def __init__(self, id, name, is_signal=False, signal_type=None):
            self.id = id
            self.name = name
            self.is_signal_place = is_signal
            self.signal_type = signal_type
    
    class MockTransition:
        def __init__(self, id, name, inputs, outputs):
            self.id = id
            self.name = name
            self.inputs = inputs
            self.outputs = outputs
    
    class MockArc:
        def __init__(self, source, target, arc_type='normal'):
            self.source = source
            self.target = target
            self.arc_type = arc_type
            self.weight = 1
    
    class MockModel:
        def __init__(self):
            # Energy layer (Layer 0)
            self.places = {
                'ATP': MockPlace('ATP', 'ATP', True, 'ENERGY'),
                'ADP': MockPlace('ADP', 'ADP', True, 'ENERGY'),
                'Pi': MockPlace('Pi', 'Phosphate', True, 'ENERGY'),
                'Glucose': MockPlace('Glucose', 'Glucose', False),
                'G6P': MockPlace('G6P', 'Glucose-6-P', False),
                'F6P': MockPlace('F6P', 'Fructose-6-P', False),
                'FBP': MockPlace('FBP', 'Fructose-1,6-BP', False),
                'Pyruvate': MockPlace('Pyruvate', 'Pyruvate', False),
                # Quorum layer (Layer 2)
                'AI': MockPlace('AI', 'Autoinducer', True, 'QUORUM'),
                'AHL': MockPlace('AHL', 'AHL', True, 'QUORUM'),
                # Regulatory layer (Layer 3)
                'LuxR': MockPlace('LuxR', 'LuxR TF', True, 'REGULATORY'),
                'CRP': MockPlace('CRP', 'CRP TF', True, 'REGULATORY'),
                'GeneA': MockPlace('GeneA', 'Gene A', False),
                'GeneB': MockPlace('GeneB', 'Gene B', False)
            }
            
            # Energy transitions (Layer 0)
            self.transitions = [
                MockTransition('T1', 'Glucose phosphorylation',
                              {'Glucose': 1, 'ATP': 1},
                              {'G6P': 1, 'ADP': 1}),
                MockTransition('T2', 'G6P isomerization',
                              {'G6P': 1},
                              {'F6P': 1}),
                MockTransition('T3', 'F6P phosphorylation',
                              {'F6P': 1, 'ATP': 1},
                              {'FBP': 1, 'ADP': 1}),
                MockTransition('T4', 'Glycolysis',
                              {'FBP': 1, 'ADP': 2, 'Pi': 2},
                              {'Pyruvate': 2, 'ATP': 2}),
                # Quorum transitions (Layer 2)
                MockTransition('T5', 'AI synthesis',
                              {'ATP': 1},
                              {'AI': 1, 'ADP': 1}),
                MockTransition('T6', 'AHL production',
                              {'AI': 1, 'ATP': 1},
                              {'AHL': 1, 'ADP': 1}),
                # Regulatory transitions (Layer 3)
                MockTransition('T7', 'LuxR activation',
                              {'AHL': 1, 'ATP': 1},
                              {'LuxR': 1, 'ADP': 1}),
                MockTransition('T8', 'Gene A expression',
                              {'LuxR': 1, 'CRP': 1, 'ATP': 1},
                              {'GeneA': 1, 'LuxR': 1, 'CRP': 1, 'ADP': 1}),
                MockTransition('T9', 'Gene B expression',
                              {'CRP': 1, 'ATP': 1},
                              {'GeneB': 1, 'CRP': 1, 'ADP': 1})
            ]
            
            # Create arcs
            self.arcs = []
            for trans in self.transitions:
                for place_id in trans.inputs:
                    self.arcs.append(MockArc(place_id, trans.id))
                for place_id in trans.outputs:
                    self.arcs.append(MockArc(trans.id, place_id))
            
            # Add signal flow arcs
            self.arcs.extend([
                MockArc('ATP', 'T1', 'signal_flow'),
                MockArc('ATP', 'T3', 'signal_flow'),
                MockArc('ATP', 'T5', 'signal_flow'),
                MockArc('AI', 'T6', 'signal_flow'),
                MockArc('AHL', 'T7', 'signal_flow'),
                MockArc('LuxR', 'T8', 'signal_flow'),
                MockArc('CRP', 'T8', 'signal_flow'),
                MockArc('CRP', 'T9', 'signal_flow')
            ])
    
    return MockModel()


def main():
    """Run benchmark suite."""
    parser = argparse.ArgumentParser(description='Benchmark hierarchical exploration')
    parser.add_argument('--model', type=str, help='Path to model file (optional)')
    parser.add_argument('--max-states', type=int, default=10000, help='Maximum states')
    parser.add_argument('--output-dir', type=str, default='benchmark_results', help='Output directory')
    args = parser.parse_args()
    
    # Create benchmark runner
    benchmark = HierarchicalBenchmark(output_dir=args.output_dir)
    
    # Create test model
    logger.info("Creating test model...")
    model = create_test_model()
    
    # Initial marking
    initial_marking = {
        'ATP': 20,
        'ADP': 0,
        'Pi': 10,
        'Glucose': 10,
        'G6P': 0,
        'F6P': 0,
        'FBP': 0,
        'Pyruvate': 0,
        'AI': 0,
        'AHL': 0,
        'LuxR': 0,
        'CRP': 3,
        'GeneA': 0,
        'GeneB': 0
    }
    
    # Run benchmarks
    benchmark.compare_strategies(
        model,
        'Glycolysis + Quorum + Gene Regulation',
        initial_marking,
        max_states=args.max_states
    )
    
    # Generate report
    benchmark.generate_report()
    
    logger.info("\n✅ Benchmark complete!")


if __name__ == '__main__':
    main()
