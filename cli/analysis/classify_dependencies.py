#!/usr/bin/env python3
"""
Classify Transition Dependencies (Algorithm 1)

Runs dependency classification on 100 BioModels to generate Table 3 data.

Usage:
    python classify_all_dependencies.py \
        --models ../experimental_data/biomodels_dataset/model_list.csv \
        --sbml-dir ../experimental_data/biomodels_dataset/sbml_files \
        --output ../experimental_data/dependency_distribution/classification_results.csv

Author: Eugênio Simão
Date: 2025-12-04
"""

import argparse
import csv
import sys
from pathlib import Path

# Add SHYpn to path
sys.path.insert(0, str(Path(__file__).parents[4] / 'src'))

try:
    from shypn.data.pathway.sbml_parser import SBMLParser
    from shypn.data.pathway.pathway_postprocessor import PathwayPostProcessor
    from shypn.data.pathway.pathway_converter import PathwayConverter
    from shypn.topology.biological.dependency_coupling import DependencyAndCouplingAnalyzer
except ImportError as e:
    print(f"Error importing SHYpn modules: {e}", file=sys.stderr)
    print("Make sure SHYpn is installed: pip install -e /home/simao/projetos/shypn", file=sys.stderr)
    sys.exit(1)


def classify_model_dependencies(model_id: str, sbml_path: Path) -> dict:
    """Classify dependencies for a single model.
    
    Args:
        model_id: BioModels ID
        sbml_path: Path to SBML file
    
    Returns:
        Dict with classification results
    """
    try:
        # Parse SBML
        parser = SBMLParser()
        pathway = parser.parse_file(str(sbml_path))
        
        # Post-process pathway (add layout, positions, etc.)
        postprocessor = PathwayPostProcessor(scale_factor=1.0)
        processed_pathway = postprocessor.process(pathway)
        
        # Convert to Petri net (DocumentModel)
        converter = PathwayConverter()
        doc_model = converter.convert(processed_pathway)
        
        # Run dependency analysis
        analyzer = DependencyAndCouplingAnalyzer(doc_model)
        result = analyzer.analyze()
        
        if not result.success:
            raise Exception(f"Analysis failed: {result.errors}")
        
        stats = result.data.get('statistics', {})
        
        return {
            'model_id': model_id,
            'total_pairs': stats.get('total_pairs', 0),
            'strong_independent': stats.get('strongly_independent_count', 0),
            'convergent': stats.get('convergent_count', 0),
            'regulatory': stats.get('regulatory_count', 0),
            'competitive': stats.get('competitive_count', 0),
            'weakly_independent_pct': stats.get('weakly_independent_pct', 0.0),
            'status': 'success'
        }
        
    except Exception as e:
        print(f"  ❌ Error classifying {model_id}: {e}")
        return {
            'model_id': model_id,
            'total_pairs': 0,
            'strong_independent': 0,
            'convergent': 0,
            'regulatory': 0,
            'competitive': 0,
            'weakly_independent_pct': 0.0,
            'status': f'error: {str(e)}'
        }


def main():
    parser = argparse.ArgumentParser(description='Classify transition dependencies')
    parser.add_argument('--models', type=str, required=True,
                       help='CSV file with model list')
    parser.add_argument('--sbml-dir', type=str, required=True,
                       help='Directory containing SBML files')
    parser.add_argument('--output', type=str, required=True,
                       help='Output CSV file')
    
    args = parser.parse_args()
    
    models_file = Path(args.models)
    sbml_dir = Path(args.sbml_dir)
    output_file = Path(args.output)
    
    # Validate inputs
    if not models_file.exists():
        print(f"Error: Models file not found: {models_file}", file=sys.stderr)
        sys.exit(1)
    
    if not sbml_dir.exists():
        print(f"Error: SBML directory not found: {sbml_dir}", file=sys.stderr)
        sys.exit(1)
    
    # Create output directory
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Read model list
    model_ids = []
    with open(models_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['model_id'] and not row['model_id'].startswith('#'):
                model_ids.append(row['model_id'])
    
    print(f"Classifying dependencies for {len(model_ids)} models...")
    print(f"Using Algorithm 1 (Dependency Classification)")
    
    # Classify all models
    results = []
    for i, model_id in enumerate(model_ids, 1):
        print(f"\n[{i}/{len(model_ids)}] Classifying {model_id}...")
        
        # Find SBML file
        sbml_path = None
        for ext in ['.xml', '.sbml']:
            candidate = sbml_dir / f"{model_id}{ext}"
            if candidate.exists():
                sbml_path = candidate
                break
        
        if sbml_path is None:
            print(f"  ⚠️  SBML file not found: {model_id}")
            results.append({
                'model_id': model_id,
                'total_pairs': 0,
                'strong_independent': 0,
                'convergent': 0,
                'regulatory': 0,
                'competitive': 0,
                'weakly_independent_pct': 0.0,
                'status': 'file_not_found'
            })
            continue
        
        result = classify_model_dependencies(model_id, sbml_path)
        results.append(result)
        
        if result['status'] == 'success':
            print(f"  ✅ Total pairs: {result['total_pairs']}, Weakly independent: {result['weakly_independent_pct']:.1f}%")
    
    # Write results
    print(f"\nWriting results to {output_file}...")
    
    with open(output_file, 'w', newline='') as f:
        fieldnames = ['model_id', 'total_pairs', 'strong_independent', 'convergent',
                      'regulatory', 'competitive', 'weakly_independent_pct', 'status']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    
    # Calculate aggregated statistics
    successful = [r for r in results if r['status'] == 'success']
    
    if not successful:
        print("\n❌ No successful classifications!")
        sys.exit(1)
    
    total_pairs = sum(r['total_pairs'] for r in successful)
    total_strong = sum(r['strong_independent'] for r in successful)
    total_convergent = sum(r['convergent'] for r in successful)
    total_regulatory = sum(r['regulatory'] for r in successful)
    total_competitive = sum(r['competitive'] for r in successful)
    
    pct_strong = (total_strong / total_pairs * 100) if total_pairs > 0 else 0
    pct_convergent = (total_convergent / total_pairs * 100) if total_pairs > 0 else 0
    pct_regulatory = (total_regulatory / total_pairs * 100) if total_pairs > 0 else 0
    pct_competitive = (total_competitive / total_pairs * 100) if total_pairs > 0 else 0
    pct_weakly_indep = pct_strong + pct_convergent + pct_regulatory
    
    print("\n" + "="*60)
    print("SUMMARY (Aggregated across all models)")
    print("="*60)
    print(f"Total models classified: {len(successful)}")
    print(f"Total transition pairs: {total_pairs}")
    print(f"\nDependency classification:")
    print(f"  Strong Independent: {total_strong} ({pct_strong:.1f}%)")
    print(f"  Convergent:         {total_convergent} ({pct_convergent:.1f}%)")
    print(f"  Regulatory:         {total_regulatory} ({pct_regulatory:.1f}%)")
    print(f"  Competitive:        {total_competitive} ({pct_competitive:.1f}%)")
    print(f"  ────────────────────────────────────")
    print(f"  Weakly Independent: {total_strong + total_convergent + total_regulatory} ({pct_weakly_indep:.1f}%)")
    print(f"\n✅ Results saved to: {output_file}")
    
    # Expected values from paper (Table 3)
    print("\n" + "="*60)
    print("VERIFICATION (compare with paper Table 3):")
    print("="*60)
    print(f"Strong Independent (expected: 15.3%): {pct_strong:.1f}%")
    print(f"Convergent (expected: 52.7%):         {pct_convergent:.1f}%")
    print(f"Regulatory (expected: 12.5%):         {pct_regulatory:.1f}%")
    print(f"Competitive (expected: 19.5%):        {pct_competitive:.1f}%")
    print(f"Weakly Independent (expected: 65.2%): {pct_weakly_indep:.1f}%")


if __name__ == '__main__':
    main()
