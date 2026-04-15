#!/usr/bin/env python3
"""
Quick validation test - First 10 BioModels

Fast test to verify the testing infrastructure is working correctly
before running the full 100-model suite.

Usage:
    python tests/thesis/test_quick_validation.py

Expected duration: ~5-10 minutes
Expected results: 9-10 successful imports (90%+ success rate)
"""

import sys
from pathlib import Path

# Add src to path
repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root / 'src'))

from test_100_biomodels import BioModels100TestSuite


def main():
    """Run quick validation with first 10 models."""
    
    print("=" * 70)
    print("QUICK VALIDATION TEST - First 10 BioModels")
    print("=" * 70)
    print()
    print("This test validates the testing infrastructure by importing")
    print("the first 10 models from the catalog.")
    print()
    print("Expected duration: ~5-10 minutes")
    print("Expected success rate: 90%+")
    print()
    
    # Use default output directory
    output_dir = repo_root / 'doc' / 'thesis' / 'sbml_models'
    
    print(f"Output directory: {output_dir}")
    print()
    
    # Create test suite
    suite = BioModels100TestSuite(output_dir=output_dir)
    
    try:
        # Run with limit of 10 models
        suite.run_all_tests(limit=10)
        
        # Quick summary
        successful = sum(1 for r in suite.results if r.success)
        total = len(suite.results)
        
        print()
        print("=" * 70)
        print("QUICK VALIDATION COMPLETE")
        print("=" * 70)
        print()
        
        if successful >= 9:
            print("✅ VALIDATION PASSED")
            print(f"   Success rate: {successful}/{total} ({(successful/total)*100:.0f}%)")
            print()
            print("The testing infrastructure is working correctly.")
            print("You can now run the full test suite:")
            print()
            print("  python tests/thesis/test_100_biomodels.py")
            print()
            return 0
        else:
            print("⚠️  VALIDATION WARNING")
            print(f"   Success rate: {successful}/{total} ({(successful/total)*100:.0f}%)")
            print()
            print("Success rate is lower than expected.")
            print("Check the detailed results in:")
            print(f"  {output_dir}/test_results_report.md")
            print()
            return 1
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        return 1
    except Exception as e:
        print(f"\n\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
