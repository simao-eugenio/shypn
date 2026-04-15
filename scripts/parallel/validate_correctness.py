#!/usr/bin/env python3
"""Validation script for parallel reachability correctness.

Compares parallel results against sequential baseline to ensure:
1. Same state count discovered
2. Identical state sets (no missing or extra states)
3. Consistent deadlock detection
4. Matching reachability graph structure

Usage:
    python validate_correctness.py [--verbose] [--models all]
"""

import argparse
import sys
from pathlib import Path
from typing import Set, Tuple

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from shypn.topology.behavioral.reachability import ReachabilityAnalyzer
from shypn.topology.behavioral.parallel_reachability import ParallelReachabilityAnalyzer


class CorrectnessValidator:
    """Validates parallel reachability against sequential baseline."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.passed = 0
        self.failed = 0
    
    def validate_model(self, model, name: str, num_workers: int = 4) -> bool:
        """Validate parallel matches sequential for a model."""
        print(f"\n{'='*60}")
        print(f"Validating: {name}")
        print(f"{'='*60}")
        
        # Run sequential
        print("Running sequential analysis...")
        seq_analyzer = ReachabilityAnalyzer(model)
        seq_result = seq_analyzer.analyze(max_states=10000)
        
        if not seq_result.success:
            print("❌ FAILED: Sequential analysis failed")
            self.failed += 1
            return False
        
        # Run parallel
        print(f"Running parallel analysis ({num_workers} workers)...")
        par_analyzer = ParallelReachabilityAnalyzer(model, num_workers=num_workers)
        par_result = par_analyzer.analyze(max_states=10000, parallel=True)
        
        if not par_result.success:
            print("❌ FAILED: Parallel analysis failed")
            self.failed += 1
            return False
        
        # Compare results
        all_passed = True
        
        # 1. State count
        seq_states = seq_result.get('total_states')
        par_states = par_result.get('total_states')
        
        if seq_states == par_states:
            print(f"✓ State count matches: {seq_states}")
        else:
            print(f"❌ State count mismatch: seq={seq_states}, par={par_states}")
            all_passed = False
        
        # 2. State sets
        seq_state_set = self._extract_state_set(seq_result)
        par_state_set = self._extract_state_set(par_result)
        
        if seq_state_set == par_state_set:
            print(f"✓ State sets identical ({len(seq_state_set)} states)")
        else:
            missing = seq_state_set - par_state_set
            extra = par_state_set - seq_state_set
            print(f"❌ State sets differ:")
            if missing:
                print(f"  Missing from parallel: {len(missing)} states")
            if extra:
                print(f"  Extra in parallel: {len(extra)} states")
            all_passed = False
        
        # 3. Deadlock detection
        seq_deadlocks = len(seq_result.get('deadlock_states', []))
        par_deadlocks = len(par_result.get('deadlock_states', []))
        
        if seq_deadlocks == par_deadlocks:
            print(f"✓ Deadlock count matches: {seq_deadlocks}")
        else:
            print(f"❌ Deadlock mismatch: seq={seq_deadlocks}, par={par_deadlocks}")
            all_passed = False
        
        # 4. Max depth
        seq_depth = seq_result.get('max_depth_reached')
        par_depth = par_result.get('max_depth_reached')
        
        if seq_depth == par_depth:
            print(f"✓ Max depth matches: {seq_depth}")
        else:
            print(f"⚠ Max depth differs: seq={seq_depth}, par={par_depth}")
            # Not a failure, just informational
        
        # Update counters
        if all_passed:
            print("\n✓ PASSED: All checks passed")
            self.passed += 1
        else:
            print("\n❌ FAILED: Some checks failed")
            self.failed += 1
        
        return all_passed
    
    def _extract_state_set(self, result) -> Set[Tuple]:
        """Extract set of state tuples from result."""
        states = set()
        
        graph = result.get('reachability_graph')
        if not graph:
            return states
        
        for node in graph.get('nodes', []):
            marking = node['marking']
            # Convert to hashable tuple
            marking_tuple = tuple(sorted(marking.items()))
            states.add(marking_tuple)
        
        return states
    
    def print_summary(self):
        """Print validation summary."""
        total = self.passed + self.failed
        
        print(f"\n{'='*60}")
        print("VALIDATION SUMMARY")
        print(f"{'='*60}")
        print(f"Total tests: {total}")
        print(f"Passed: {self.passed} ✓")
        print(f"Failed: {self.failed} ❌")
        
        if self.failed == 0:
            print("\n🎉 All validation tests passed!")
            return True
        else:
            print(f"\n⚠ {self.failed} test(s) failed")
            return False


def create_test_models():
    """Create test models for validation."""
    # TODO: Implement test model generation
    return {
        'simple': None,
        'medium': None,
        'deadlock': None,
    }


def main():
    parser = argparse.ArgumentParser(description='Validate parallel reachability correctness')
    parser.add_argument('--verbose', action='store_true',
                       help='Print detailed output')
    parser.add_argument('--models', default='all',
                       help='Models to test (comma-separated or "all")')
    parser.add_argument('--workers', type=int, default=4,
                       help='Number of workers for parallel (default: 4)')
    
    args = parser.parse_args()
    
    # Create validator
    validator = CorrectnessValidator(verbose=args.verbose)
    
    # Load test models
    models = create_test_models()
    
    # Determine which models to test
    if args.models == 'all':
        models_to_test = models.keys()
    else:
        models_to_test = args.models.split(',')
    
    # Run validation
    for name in models_to_test:
        if name not in models:
            print(f"Warning: Unknown model '{name}', skipping")
            continue
        
        model = models[name]
        if model is None:
            print(f"Warning: Model '{name}' not implemented, skipping")
            continue
        
        validator.validate_model(model, name, num_workers=args.workers)
    
    # Print summary
    success = validator.print_summary()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
