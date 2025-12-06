#!/usr/bin/env python3
"""Summarize all experimental results"""
import _fix_imports
import json, sys
from pathlib import Path

def load_json(path):
    """Load JSON file safely."""
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except Exception as e:
        return None

def summarize_experiments(workspace_dir):
    """Summarize all experiments in workspace."""
    workspace = Path(workspace_dir)
    
    print("=" * 70)
    print("EXPERIMENTAL RESULTS SUMMARY")
    print("=" * 70)
    print()
    
    # Find all validation and benchmark results
    validation_files = list(workspace.glob("**/validation_results.json"))
    benchmark_files = list(workspace.glob("**/benchmark_results.json"))
    
    print(f"📊 Found {len(validation_files)} validation results")
    print(f"📊 Found {len(benchmark_files)} benchmark results")
    print()
    
    # Analyze validation results
    if validation_files:
        print("-" * 70)
        print("EQUIVALENCE VALIDATION")
        print("-" * 70)
        
        for vfile in sorted(validation_files):
            data = load_json(vfile)
            if not data:
                continue
            
            model_name = vfile.parent.name
            n_species = data.get('summary', {}).get('n_species', 0)
            n_equiv = data.get('summary', {}).get('n_equivalent', 0)
            equiv_rate = data.get('summary', {}).get('equivalence_rate', 0)
            verdict = data.get('verdict', 'UNKNOWN')
            
            status = "✅" if "PASSED" in verdict else "⚠️" if "WARNING" in verdict else "❌"
            print(f"{status} {model_name:20} {n_equiv:3}/{n_species:<3} species ({equiv_rate:>5.1%}) - {verdict}")
        
        print()
    
    # Analyze benchmark results
    if benchmark_files:
        print("-" * 70)
        print("PERFORMANCE BENCHMARKS")
        print("-" * 70)
        
        speedups = []
        for bfile in sorted(benchmark_files):
            data = load_json(bfile)
            if not data or 'speedup' not in data:
                continue
            
            model_name = bfile.parent.name
            speedup = data['speedup']
            speedups.append(speedup)
            
            tau_time = data.get('tau_leaping', {}).get('total_time', 0)
            ssa_time = data.get('gillespie', {}).get('total_time', 0)
            
            status = "🚀" if speedup > 1.5 else "⚡" if speedup > 1.0 else "⏱️"
            print(f"{status} {model_name:20} Speedup: {speedup:5.2f}x  "
                  f"(τ={tau_time:.3f}s, SSA={ssa_time:.3f}s)")
        
        if speedups:
            import numpy as np
            print()
            print(f"📈 Speedup Statistics:")
            print(f"   Min:    {min(speedups):.2f}x")
            print(f"   Max:    {max(speedups):.2f}x")
            print(f"   Mean:   {np.mean(speedups):.2f}x")
            print(f"   Median: {np.median(speedups):.2f}x")
        
        print()
    
    print("=" * 70)

def main():
    if len(sys.argv) < 2:
        workspace = "../../workspace"
    else:
        workspace = sys.argv[1]
    
    summarize_experiments(workspace)

if __name__ == '__main__':
    main()
