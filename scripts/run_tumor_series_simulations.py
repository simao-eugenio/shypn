#!/usr/bin/env python3
"""
Run tumor N-methylation series simulations (0-7).
Each simulation runs for 60 seconds with stochastic tau-leaping algorithm.
"""

import subprocess
import time
from pathlib import Path

def run_tumor_simulation(variant_num: int) -> tuple[bool, str, float]:
    """
    Run a single tumor simulation.
    
    Args:
        variant_num: N-methylation level (0-7)
    
    Returns:
        (success: bool, message: str, duration: float)
    """
    model_path = Path('workspace/projects/My_Project/drug_discovery/models/manuscript') / f'macrocycle_transport_tumor_nme_{variant_num}_enhanced.shy'
    output_dir = Path('workspace/projects/My_Project/drug_discovery/data/n_methylation')
    output_file = output_dir / f'tumor_nme_{variant_num}_simulation.csv'
    
    if not model_path.exists():
        return False, f"Model not found: {model_path}", 0.0
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n{'='*70}")
    print(f"RUNNING N-Me {variant_num} TUMOR SIMULATION")
    print(f"{'='*70}")
    print(f"Model: {model_path.name}")
    print(f"Output: {output_file.name}")
    print(f"Duration: 60 seconds (stochastic tau-leaping)")
    print(f"{'='*70}\n")
    
    start_time = time.time()
    
    try:
        # Run simulation using shypn CLI
        result = subprocess.run(
            [
                '.venv/bin/python', '-m', 'shypn',
                'simulate',
                str(model_path),
                '--duration', '60',
                '--algorithm', 'tau_leaping',
                '--output', str(output_file),
                '--quiet'
            ],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        duration = time.time() - start_time
        
        if result.returncode == 0:
            # Check if output file was created
            if output_file.exists():
                file_size = output_file.stat().st_size / 1024  # KB
                return True, f"Completed in {duration:.1f}s (output: {file_size:.1f} KB)", duration
            else:
                return False, f"Simulation completed but no output file generated", duration
        else:
            error_msg = result.stderr.strip() if result.stderr else "Unknown error"
            return False, f"Simulation failed: {error_msg}", duration
    
    except subprocess.TimeoutExpired:
        duration = time.time() - start_time
        return False, f"Simulation timed out after {duration:.1f}s", duration
    except Exception as e:
        duration = time.time() - start_time
        return False, f"Exception: {str(e)}", duration


def main():
    """Run all tumor simulations in the series."""
    print("=" * 70)
    print("TUMOR N-METHYLATION SERIES SIMULATIONS")
    print("=" * 70)
    print("\nRunning 8 tumor simulations (N-Me 0-7)...")
    print("Each simulation: 60 seconds, stochastic tau-leaping algorithm")
    print("=" * 70)
    
    results = []
    total_start = time.time()
    
    for i in range(8):
        success, message, duration = run_tumor_simulation(i)
        results.append((i, success, message, duration))
        
        # Brief pause between simulations
        if i < 7:
            time.sleep(1)
    
    total_duration = time.time() - total_start
    
    # Summary
    print("\n" + "=" * 70)
    print("SIMULATION SUMMARY")
    print("=" * 70)
    
    successes = 0
    failures = 0
    
    for variant_num, success, message, duration in results:
        status = "✓" if success else "✗"
        print(f"{status} N-Me {variant_num} (tumor): {message}")
        if success:
            successes += 1
        else:
            failures += 1
    
    print("\n" + "=" * 70)
    print(f"Total: {successes} succeeded, {failures} failed")
    print(f"Total time: {total_duration/60:.1f} minutes ({total_duration:.1f} seconds)")
    print("=" * 70)
    
    if failures == 0:
        print("\n✓ All tumor simulations completed successfully!")
        print("Next step: Analyze simulation data (analyze_tumor_nme_X_simulation.py)")
    else:
        print("\n⚠ Some simulations failed. Review error messages above.")


if __name__ == '__main__':
    main()
