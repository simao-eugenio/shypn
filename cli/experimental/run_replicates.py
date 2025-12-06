#!/usr/bin/env python3
"""Run Simulation Replicates - Implemented CLI Tool"""
import _fix_imports  # Add src to path
import argparse, sys
from pathlib import Path
from shypn.engine.simulation.replicate_runner import ReplicateRunner
from _sbml_loader import load_sbml_model


def main():
    parser = argparse.ArgumentParser(description='Run replicates with ReplicateRunner')
    parser.add_argument('model', help='SBML model file')
    parser.add_argument('-n', '--replicates', type=int, default=100)
    parser.add_argument('-d', '--duration', type=float, default=100.0)
    parser.add_argument('-o', '--output', default='.')
    parser.add_argument('-v', '--verbose', action='store_true')
    args = parser.parse_args()
    
    try:
        model_path = Path(args.model)
        if not model_path.exists():
            sys.exit(f"ERROR: Model not found: {model_path}")
        
        output_dir = Path(args.output)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"Loading {model_path.name}...")
        model = load_sbml_model(model_path)
        
        print(f"Running {args.replicates} replicates...")
        runner = ReplicateRunner(model)
        results = runner.run_replicates(n=args.replicates, duration=args.duration, verbose=args.verbose)
        stats = runner.compute_statistics(results)
        
        runner.export_trajectories_csv(results, output_dir / 'trajectories.csv')
        runner.export_statistics_json(stats, output_dir / 'statistics.json')
        
        print(f"✅ Complete! Saved to: {output_dir.absolute()}")
    except Exception as e:
        sys.exit(f"ERROR: {e}")

if __name__ == '__main__':
    main()
