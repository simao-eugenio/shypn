#!/usr/bin/env python3
"""Run Simulation Replicates - Implemented CLI Tool"""
import argparse, sys
from pathlib import Path
from shypn.engine.simulation.replicate_runner import ReplicateRunner
from shypn.data.pathway.sbml_parser import SBMLParser
from shypn.data.pathway.pathway_converter import PathwayConverter

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
        parser_obj = SBMLParser()
        pathway = parser_obj.parse_file(model_path)
        converter = PathwayConverter()
        model = converter.convert(pathway)
        
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
