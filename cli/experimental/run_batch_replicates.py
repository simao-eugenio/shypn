#!/usr/bin/env python3
"""Run Batch Replicates - Process multiple models with replicates"""
import _fix_imports  # Add src to path
import argparse, sys
from pathlib import Path
from shypn.data.batch import BatchProcessor
from shypn.engine.simulation.replicate_runner import ReplicateRunner
from _sbml_loader import load_sbml_model


def process_model(model_id, model_path, config):
    """Process single model with replicates."""
    parser = SBMLParser()
    pathway = parser.parse_file(model_path)
    converter = PathwayConverter()
    model = converter.convert(pathway)
    
    runner = ReplicateRunner(model)
    results = runner.run_replicates(
        n=config['replicates'],
        use_tau_leaping=not config['no_tau_leaping'],
        duration=config['duration'],
        verbose=False
    )
    stats = runner.compute_statistics(results)
    
    return {
        'model_id': model_id,
        'n_species': len(model.places),
        'n_reactions': len(model.transitions),
        'statistics': stats['species_statistics']
    }

def main():
    parser = argparse.ArgumentParser(description='Run replicates for batch of models')
    parser.add_argument('batch_csv', help='Batch CSV with model_id,model_path')
    parser.add_argument('-n', '--replicates', type=int, default=100)
    parser.add_argument('-d', '--duration', type=float, default=100.0)
    parser.add_argument('--no-tau-leaping', action='store_true')
    parser.add_argument('--parallel', action='store_true', help='Process models in parallel')
    parser.add_argument('-o', '--output', default='batch_results')
    parser.add_argument('-v', '--verbose', action='store_true')
    args = parser.parse_args()
    
    try:
        batch_path = Path(args.batch_csv)
        if not batch_path.exists():
            sys.exit(f"ERROR: Batch CSV not found: {batch_path}")
        
        output_dir = Path(args.output)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        processor = BatchProcessor(verbose=args.verbose)
        models = processor.load_from_csv(batch_path)
        print(f"✓ Loaded {len(models)} models")
        
        config = {
            'replicates': args.replicates,
            'duration': args.duration,
            'no_tau_leaping': args.no_tau_leaping
        }
        
        print(f"\nProcessing {len(models)} models with {args.replicates} replicates each...")
        
        def wrapped_processor(model_id, model_path):
            return process_model(model_id, model_path, config)
        
        results = processor.process_batch(models, wrapped_processor, parallel=args.parallel)
        processor.export_results(results, output_dir, include_details=True)
        
        success_rate = results['n_successful'] / results['n_total'] if results['n_total'] > 0 else 0
        print(f"\n✅ Batch complete: {results['n_successful']}/{results['n_total']} successful ({100*success_rate:.1f}%)")
        print(f"Results saved to: {output_dir.absolute()}")
        
    except Exception as e:
        sys.exit(f"ERROR: {e}")

if __name__ == '__main__':
    main()
