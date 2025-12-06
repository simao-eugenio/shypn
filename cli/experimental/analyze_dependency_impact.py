#!/usr/bin/env python3
"""Analyze Dependency Impact - Measure how dependency detection affects performance"""
import argparse, sys, json
from pathlib import Path
from shypn.engine.simulation.replicate_runner import ReplicateRunner
from shypn.data.pathway.sbml_parser import SBMLParser
from shypn.data.pathway.pathway_converter import PathwayConverter

def analyze_dependencies(model):
    """Analyze model dependency structure."""
    # Count transition dependencies
    total_transitions = len(model.transitions)
    independent_count = 0
    dependent_count = 0
    
    for t in model.transitions:
        # A transition is independent if it doesn't share places with others
        shared = False
        for other in model.transitions:
            if t == other:
                continue
            # Check for shared places in pre/post conditions
            t_places = set(t.pre_conditions.keys()) | set(t.post_conditions.keys())
            other_places = set(other.pre_conditions.keys()) | set(other.post_conditions.keys())
            if t_places & other_places:
                shared = True
                break
        
        if shared:
            dependent_count += 1
        else:
            independent_count += 1
    
    independence_ratio = independent_count / total_transitions if total_transitions > 0 else 0.0
    
    return {
        'total_transitions': total_transitions,
        'independent': independent_count,
        'dependent': dependent_count,
        'independence_ratio': float(independence_ratio)
    }

def main():
    parser = argparse.ArgumentParser(description='Analyze dependency impact on performance')
    parser.add_argument('model', help='SBML model file')
    parser.add_argument('-n', '--replicates', type=int, default=50)
    parser.add_argument('-d', '--duration', type=float, default=100.0)
    parser.add_argument('-o', '--output', default='dependency_analysis')
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
        print(f"  Model: {len(model.places)} places, {len(model.transitions)} transitions")
        
        # Analyze dependencies
        print("\nAnalyzing dependency structure...")
        dep_analysis = analyze_dependencies(model)
        print(f"  Independent transitions: {dep_analysis['independent']}")
        print(f"  Dependent transitions: {dep_analysis['dependent']}")
        print(f"  Independence ratio: {dep_analysis['independence_ratio']:.2%}")
        
        # Run simulation to see impact
        print(f"\nRunning simulations ({args.replicates} replicates)...")
        runner = ReplicateRunner(model)
        results = runner.run_replicates(
            n=args.replicates,
            use_tau_leaping=True,
            duration=args.duration,
            verbose=False
        )
        
        successful = sum(1 for r in results if 'error' not in r)
        success_rate = successful / len(results)
        
        # Compile full analysis
        analysis = {
            'model_info': {
                'name': model_path.name,
                'places': len(model.places),
                'transitions': len(model.transitions)
            },
            'dependency_structure': dep_analysis,
            'simulation_results': {
                'n_replicates': args.replicates,
                'successful': successful,
                'success_rate': float(success_rate)
            },
            'performance_insight': {
                'parallelization_potential': dep_analysis['independence_ratio'],
                'recommendation': 'HIGH' if dep_analysis['independence_ratio'] > 0.5 else 'MODERATE' if dep_analysis['independence_ratio'] > 0.2 else 'LOW'
            }
        }
        
        # Export
        results_file = output_dir / 'dependency_analysis.json'
        with open(results_file, 'w') as f:
            json.dump(analysis, f, indent=2)
        
        print(f"\n{'='*60}")
        print(f"Parallelization Potential: {analysis['performance_insight']['recommendation']}")
        print(f"Independence Ratio: {dep_analysis['independence_ratio']:.2%}")
        print(f"{'='*60}")
        print(f"\n✓ Results saved to: {results_file}")
        
    except Exception as e:
        sys.exit(f"ERROR: {e}")

if __name__ == '__main__':
    main()
