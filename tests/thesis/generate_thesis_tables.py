#!/usr/bin/env python3
"""
Generate LaTeX tables and figures from test results

This script processes test results and generates publication-ready
LaTeX tables and figures for inclusion in thesis/paper.

Usage:
    python tests/thesis/generate_thesis_tables.py
    
Input:
    doc/thesis/sbml_models/test_results_complete.json
    
Output:
    doc/thesis/sbml_models/tables/*.tex
    doc/thesis/sbml_models/figures/*.pdf
"""

import sys
import json
from pathlib import Path
from typing import Dict, List

repo_root = Path(__file__).parent.parent.parent


def load_results() -> Dict:
    """Load test results from JSON."""
    results_file = repo_root / 'doc' / 'thesis' / 'sbml_models' / 'test_results_complete.json'
    
    if not results_file.exists():
        print(f"❌ Results file not found: {results_file}")
        print()
        print("Please run the test suite first:")
        print("  python tests/thesis/test_100_biomodels.py")
        sys.exit(1)
    
    with open(results_file, 'r') as f:
        return json.load(f)


def generate_summary_table(results: Dict, output_dir: Path):
    """Generate summary statistics table."""
    
    table = r"""\begin{table}[htbp]
\centering
\caption{SBML Import Validation Summary (100 BioModels)}
\label{tab:sbml-import-summary}
\begin{tabular}{lrr}
\toprule
\textbf{Metric} & \textbf{Count} & \textbf{Percentage} \\
\midrule
Models Tested & """ + str(results['test_metadata']['total_models_tested']) + r""" & 100\% \\
Successful Imports & """ + str(results['summary_statistics']['models_successful']) + r""" & """ + results['summary_statistics']['success_rate'] + r""" \\
Failed Imports & """ + str(results['summary_statistics']['models_failed']) + r""" & """ + f"{(results['summary_statistics']['models_failed']/results['test_metadata']['total_models_tested'])*100:.1f}" + r"""\% \\
\midrule
Parse Success & """ + str(results['test_metadata']['total_models_tested']) + r""" & """ + results['summary_statistics']['parse_success_rate'] + r""" \\
Layout Generated & """ + str(results['test_metadata']['total_models_tested']) + r""" & """ + results['summary_statistics']['layout_success_rate'] + r""" \\
\bottomrule
\end{tabular}
\end{table}
"""
    
    output_file = output_dir / 'summary_statistics.tex'
    with open(output_file, 'w') as f:
        f.write(table)
    
    print(f"✓ Generated: {output_file}")


def generate_conversion_table(results: Dict, output_dir: Path):
    """Generate conversion accuracy table."""
    
    conv = results['conversion_statistics']
    
    table = r"""\begin{table}[htbp]
\centering
\caption{SBML to Petri Net Conversion Statistics}
\label{tab:conversion-stats}
\begin{tabular}{lrr}
\toprule
\textbf{SBML Element} & \textbf{Count} & \textbf{Petri Net Element} & \textbf{Count} \\
\midrule
Species & """ + str(conv['total_species']) + r""" & Places & """ + str(conv['total_places_created']) + r""" \\
Reactions & """ + str(conv['total_reactions']) + r""" & Transitions & """ + str(conv['total_transitions_created']) + r""" \\
\midrule
\multicolumn{2}{l}{\textit{Arc Types}} & & \\
& & Normal Arcs & """ + str(conv['total_normal_arcs']) + r""" \\
& & Test Arcs (Catalysts) & """ + str(conv['total_test_arcs']) + r""" \\
& & Inhibitor Arcs & """ + str(conv['total_inhibitor_arcs']) + r""" \\
\midrule
\multicolumn{2}{l}{\textbf{Total Arcs}} & & \textbf{""" + str(conv['total_normal_arcs'] + conv['total_test_arcs'] + conv['total_inhibitor_arcs']) + r"""} \\
\bottomrule
\end{tabular}
\end{table}
"""
    
    output_file = output_dir / 'conversion_statistics.tex'
    with open(output_file, 'w') as f:
        f.write(table)
    
    print(f"✓ Generated: {output_file}")


def generate_kinetics_table(results: Dict, output_dir: Path):
    """Generate kinetics analysis table."""
    
    kin = results['kinetics_statistics']
    
    table = r"""\begin{table}[htbp]
\centering
\caption{Kinetic Parameter Analysis}
\label{tab:kinetics-stats}
\begin{tabular}{lrr}
\toprule
\textbf{Category} & \textbf{Count} & \textbf{Percentage} \\
\midrule
Models with Kinetic Laws & """ + str(kin['models_with_kinetics']) + r""" & """ + kin['percentage_with_kinetics'] + r""" \\
Models without Kinetics & """ + str(results['test_metadata']['total_models_tested'] - kin['models_with_kinetics']) + r""" & """ + f"{((results['test_metadata']['total_models_tested'] - kin['models_with_kinetics'])/results['test_metadata']['total_models_tested'])*100:.1f}" + r"""\% \\
\midrule
Continuous Transitions & """ + str(kin['total_continuous_transitions']) + r""" & """ + kin['continuous_ratio'] + r""" \\
Stochastic Transitions & """ + str(kin['total_stochastic_transitions']) + r""" & """ + f"{(kin['total_stochastic_transitions']/(kin['total_continuous_transitions']+kin['total_stochastic_transitions']))*100:.1f}" + r"""\% \\
\bottomrule
\end{tabular}
\end{table}
"""
    
    output_file = output_dir / 'kinetics_statistics.tex'
    with open(output_file, 'w') as f:
        f.write(table)
    
    print(f"✓ Generated: {output_file}")


def generate_complexity_analysis(results: Dict, output_dir: Path):
    """Generate analysis by model complexity."""
    
    # Group results by complexity
    complexity_stats = {
        'simple': {'total': 0, 'success': 0, 'species': [], 'reactions': []},
        'medium': {'total': 0, 'success': 0, 'species': [], 'reactions': []},
        'complex': {'total': 0, 'success': 0, 'species': [], 'reactions': []},
        'very_complex': {'total': 0, 'success': 0, 'species': [], 'reactions': []}
    }
    
    # Note: We'd need to store complexity in results to properly categorize
    # For now, use simple heuristics based on species count
    for result in results['detailed_results']:
        species = result['species_count']
        
        if species <= 20:
            cat = 'simple'
        elif species <= 50:
            cat = 'medium'
        elif species <= 100:
            cat = 'complex'
        else:
            cat = 'very_complex'
        
        complexity_stats[cat]['total'] += 1
        if result['success']:
            complexity_stats[cat]['success'] += 1
        complexity_stats[cat]['species'].append(result['species_count'])
        complexity_stats[cat]['reactions'].append(result['reactions_count'])
    
    # Generate table
    table = r"""\begin{table}[htbp]
\centering
\caption{Import Success by Model Complexity}
\label{tab:complexity-analysis}
\begin{tabular}{lrrrrr}
\toprule
\textbf{Complexity} & \textbf{Models} & \textbf{Success} & \textbf{Rate} & \textbf{Avg Species} & \textbf{Avg Reactions} \\
\midrule
"""
    
    for cat in ['simple', 'medium', 'complex', 'very_complex']:
        stats = complexity_stats[cat]
        if stats['total'] > 0:
            success_rate = (stats['success'] / stats['total']) * 100
            avg_species = sum(stats['species']) / len(stats['species'])
            avg_reactions = sum(stats['reactions']) / len(stats['reactions'])
            
            cat_name = cat.replace('_', ' ').title()
            table += f"{cat_name} & {stats['total']} & {stats['success']} & {success_rate:.1f}\\% & {avg_species:.1f} & {avg_reactions:.1f} \\\\\n"
    
    table += r"""\bottomrule
\end{tabular}
\end{table}
"""
    
    output_file = output_dir / 'complexity_analysis.tex'
    with open(output_file, 'w') as f:
        f.write(table)
    
    print(f"✓ Generated: {output_file}")


def generate_averages_table(results: Dict, output_dir: Path):
    """Generate table with average metrics per model."""
    
    conv = results['conversion_statistics']
    
    table = r"""\begin{table}[htbp]
\centering
\caption{Average Metrics per Model}
\label{tab:average-metrics}
\begin{tabular}{lr}
\toprule
\textbf{Metric} & \textbf{Average Value} \\
\midrule
Species per Model & """ + f"{conv['avg_species_per_model']:.1f}" + r""" \\
Reactions per Model & """ + f"{conv['avg_reactions_per_model']:.1f}" + r""" \\
Places per Model & """ + f"{conv['avg_places_per_model']:.1f}" + r""" \\
Transitions per Model & """ + f"{conv['avg_transitions_per_model']:.1f}" + r""" \\
\midrule
Species/Reactions Ratio & """ + f"{conv['avg_species_per_model']/conv['avg_reactions_per_model']:.2f}" + r""" \\
Places/Transitions Ratio & """ + f"{conv['avg_places_per_model']/conv['avg_transitions_per_model']:.2f}" + r""" \\
\bottomrule
\end{tabular}
\end{table}
"""
    
    output_file = output_dir / 'average_metrics.tex'
    with open(output_file, 'w') as f:
        f.write(table)
    
    print(f"✓ Generated: {output_file}")


def main():
    """Main entry point."""
    
    print("=" * 70)
    print("LaTeX Table Generator for Thesis")
    print("=" * 70)
    print()
    
    # Load results
    print("Loading test results...")
    results = load_results()
    print(f"✓ Loaded results for {results['test_metadata']['total_models_tested']} models")
    print()
    
    # Create output directories
    tables_dir = repo_root / 'doc' / 'thesis' / 'sbml_models' / 'tables'
    tables_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate tables
    print("Generating LaTeX tables...")
    generate_summary_table(results, tables_dir)
    generate_conversion_table(results, tables_dir)
    generate_kinetics_table(results, tables_dir)
    generate_complexity_analysis(results, tables_dir)
    generate_averages_table(results, tables_dir)
    
    print()
    print("=" * 70)
    print("TABLE GENERATION COMPLETE")
    print("=" * 70)
    print()
    print("Generated files:")
    print(f"  📄 {tables_dir}/summary_statistics.tex")
    print(f"  📄 {tables_dir}/conversion_statistics.tex")
    print(f"  📄 {tables_dir}/kinetics_statistics.tex")
    print(f"  📄 {tables_dir}/complexity_analysis.tex")
    print(f"  📄 {tables_dir}/average_metrics.tex")
    print()
    print("Use in thesis LaTeX:")
    print(r"  \input{doc/thesis/sbml_models/tables/summary_statistics.tex}")
    print()


if __name__ == '__main__':
    main()
