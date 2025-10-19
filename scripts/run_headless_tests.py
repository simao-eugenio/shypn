#!/usr/bin/env python3
"""
Run Headless Validation Tests

Convenience script to run all headless simulation tests from the project root.

Usage:
    python3 run_headless_tests.py              # Run all tests
    python3 run_headless_tests.py --quick      # Run quick test only
    python3 run_headless_tests.py --full       # Run comprehensive test only
"""

import sys
import os
import subprocess
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / 'src'))

def run_test(test_file, description):
    """Run a single test file."""
    print()
    print("=" * 80)
    print(f"RUNNING: {description}")
    print("=" * 80)
    
    test_path = project_root / 'tests' / 'validate' / 'headless' / test_file
    
    if not test_path.exists():
        print(f"✗ Test file not found: {test_path}")
        return False
    
    result = subprocess.run(
        [sys.executable, str(test_path)],
        cwd=project_root,
        capture_output=False
    )
    
    return result.returncode == 0


def main():
    """Run headless validation tests."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run headless validation tests')
    parser.add_argument('--quick', action='store_true', 
                       help='Run only quick fresh glycolysis test')
    parser.add_argument('--full', action='store_true', 
                       help='Run only comprehensive simulation test')
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("HEADLESS SIMULATION VALIDATION TESTS")
    print("=" * 80)
    print()
    print(f"Project: {project_root}")
    print(f"Python: {sys.executable} (v{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro})")
    print()
    
    results = []
    
    # Determine which tests to run
    if args.quick:
        tests = [
            ('test_fresh_glycolysis.py', 'Fresh Glycolysis Import Validation (Quick)'),
        ]
    elif args.full:
        tests = [
            ('test_headless_simulation.py', 'Comprehensive Simulation Test Suite (7 tests)'),
        ]
    else:
        # Run both by default
        tests = [
            ('test_fresh_glycolysis.py', 'Fresh Glycolysis Import Validation (Quick)'),
            ('test_headless_simulation.py', 'Comprehensive Simulation Test Suite (7 tests)'),
        ]
    
    # Run tests
    for test_file, description in tests:
        success = run_test(test_file, description)
        results.append((description, success))
    
    # Summary
    print()
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    all_passed = True
    for description, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status}: {description}")
        if not success:
            all_passed = False
    
    print()
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        return 1


if __name__ == '__main__':
    sys.exit(main())
