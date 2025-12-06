#!/usr/bin/env python3
"""Analyze Batch Results - Extract insights from batch experiments"""
import _fix_imports
import argparse, sys, json
from pathlib import Path
import numpy as np

def analyze_batch(batch_file):
    """Analyze batch experiment results."""
    with open(batch_file, 'r') as f:
        data = json.load(f)
    
    print("=" * 60)
    print("Batch Experiment Analysis")
    print("=" * 60)
    print(f"\n📊 Overview:")
    print(f"  Total models: {data['n_total']}")
    print(f"  Successful: {data['n_successful']}")
    print(f"  Failed: {data['n_failed']}")
    print(f"  Success rate: {data['success_rate']:.1%}")
    
    # Analyze model sizes
    species_counts = []
    reaction_counts = []
    
    for model_id, result in data['results'].items():
        species_counts.append(result['n_species'])
        reaction_counts.append(result['n_reactions'])
    
    print(f"\n📈 Model Size Distribution:")
    print(f"  Species: min={min(species_counts)}, max={max(species_counts)}, "
          f"mean={np.mean(species_counts):.1f}, median={np.median(species_counts):.0f}")
    print(f"  Reactions: min={min(reaction_counts)}, max={max(reaction_counts)}, "
          f"mean={np.mean(reaction_counts):.1f}, median={np.median(reaction_counts):.0f}")
    
    # Analyze replicate success
    print(f"\n🔬 Simulation Coverage:")
    print(f"  All {data['n_successful']} models simulated successfully")
    
    # Model details
    print(f"\n📋 Model Details:")
    print(f"  {'Model ID':<20} {'Species':<10} {'Reactions':<12}")
    print(f"  {'-'*20} {'-'*10} {'-'*12}")
    
    for model_id, result in sorted(data['results'].items()):
        print(f"  {model_id:<20} {result['n_species']:<10} {result['n_reactions']:<12}")
    
    print("\n" + "=" * 60)
    
    return data

def main():
    parser = argparse.ArgumentParser(description='Analyze batch experiment results')
    parser.add_argument('batch_file', help='Path to batch_summary.json')
    parser.add_argument('-o', '--output', help='Save analysis to file')
    args = parser.parse_args()
    
    try:
        batch_path = Path(args.batch_file)
        if not batch_path.exists():
            sys.exit(f"ERROR: Batch file not found: {batch_path}")
        
        data = analyze_batch(batch_path)
        
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save summary
            summary = {
                'n_total': data['n_total'],
                'n_successful': data['n_successful'],
                'success_rate': data['success_rate'],
                'models': [
                    {
                        'model_id': mid,
                        'n_species': r['n_species'],
                        'n_reactions': r['n_reactions']
                    }
                    for mid, r in data['results'].items()
                ]
            }
            
            with open(output_path, 'w') as f:
                json.dump(summary, f, indent=2)
            
            print(f"\n✓ Analysis saved to: {output_path}")
        
    except Exception as e:
        sys.exit(f"ERROR: {e}")

if __name__ == '__main__':
    main()
