#!/usr/bin/env python3
"""Generate Experiment Report - Compile comprehensive analysis report"""
import _fix_imports  # Add src to path
import argparse, sys, json
from pathlib import Path
from datetime import datetime

def load_json(path):
    """Load JSON file with error handling."""
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"WARNING: Could not load {path}: {e}")
        return None

def generate_markdown_report(data, output_path):
    """Generate markdown report from collected data."""
    
    lines = [
        "# Tau-Leaping Validation Report",
        f"\n**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "\n---\n"
    ]
    
    # Model information
    if 'validation' in data and data['validation']:
        lines.append("## Model Information\n")
        model_name = data['validation'].get('model_name', 'Unknown')
        n_replicates = data['validation'].get('n_replicates', 0)
        lines.append(f"- **Model:** `{model_name}`")
        lines.append(f"- **Replicates:** {n_replicates}\n")
    
    # Validation results
    if 'validation' in data and data['validation']:
        lines.append("## Validation Results\n")
        val = data['validation']
        summary = val.get('summary', {})
        verdict = val.get('verdict', 'UNKNOWN')
        
        n_species = summary.get('n_species', 0)
        n_equiv = summary.get('n_equivalent', 0)
        equiv_rate = summary.get('equivalence_rate', 0.0)
        
        lines.append(f"**Verdict:** {verdict}")
        lines.append(f"- Equivalent species: {n_equiv}/{n_species} ({equiv_rate:.1%})")
        lines.append(f"- Tolerance threshold: 5%\n")
        
        # Species comparison table
        if 'species_comparison' in val:
            lines.append("### Species Comparison\n")
            lines.append("| Species | τ-leaping | Gillespie | Rel. Diff | Equivalent |")
            lines.append("|---------|-----------|-----------|-----------|------------|")
            
            for species, comp in val['species_comparison'].items():
                tau_mean = comp['tau_mean']
                ssa_mean = comp['ssa_mean']
                rel_diff = comp['rel_diff'] * 100
                equiv = '✓' if comp['equivalent'] else '✗'
                lines.append(f"| {species} | {tau_mean:.2f} | {ssa_mean:.2f} | {rel_diff:.2f}% | {equiv} |")
            lines.append("")
    
    # Benchmark results
    if 'benchmark' in data and data['benchmark']:
        lines.append("## Performance Benchmark\n")
        bench = data['benchmark']
        
        if 'tau_leaping' in bench:
            tau = bench['tau_leaping']
            lines.append(f"**τ-leaping:**")
            lines.append(f"- Total time: {tau['total_time']:.2f}s")
            lines.append(f"- Per replicate: {tau['time_per_replicate']*1000:.1f}ms\n")
        
        if 'gillespie' in bench:
            gill = bench['gillespie']
            lines.append(f"**Gillespie SSA:**")
            lines.append(f"- Total time: {gill['total_time']:.2f}s")
            lines.append(f"- Per replicate: {gill['time_per_replicate']*1000:.1f}ms\n")
        
        if 'speedup' in bench:
            speedup = bench['speedup']
            lines.append(f"**Speedup:** {speedup:.2f}x (τ-leaping is {speedup:.2f}x faster)\n")
    
    # Dependency analysis
    if 'dependency' in data and data['dependency']:
        lines.append("## Dependency Analysis\n")
        dep = data['dependency'].get('dependency_structure', {})
        perf = data['dependency'].get('performance_insight', {})
        
        lines.append(f"- Independent transitions: {dep.get('independent', 0)}")
        lines.append(f"- Dependent transitions: {dep.get('dependent', 0)}")
        lines.append(f"- Independence ratio: {dep.get('independence_ratio', 0.0):.2%}")
        lines.append(f"- Parallelization potential: **{perf.get('recommendation', 'UNKNOWN')}**\n")
    
    # Conclusions
    lines.append("## Conclusions\n")
    
    if 'validation' in data and data['validation']:
        verdict = data['validation'].get('verdict', '')
        if 'PASSED' in verdict:
            lines.append("✅ **Validation passed:** τ-leaping produces equivalent results to Gillespie SSA.")
        elif 'WARNING' in verdict:
            lines.append("⚠️ **Validation warning:** Some species show non-negligible differences.")
        else:
            lines.append("❌ **Validation failed:** Significant differences detected between algorithms.")
    
    if 'benchmark' in data and data['benchmark'] and 'speedup' in data['benchmark']:
        speedup = data['benchmark']['speedup']
        if speedup > 2.0:
            lines.append(f"🚀 **Performance gain:** Substantial speedup ({speedup:.2f}x) demonstrates practical benefit.")
        elif speedup > 1.2:
            lines.append(f"⚡ **Performance gain:** Moderate speedup ({speedup:.2f}x) observed.")
        else:
            lines.append(f"⏱️ **Performance:** Limited speedup ({speedup:.2f}x) for this model.")
    
    lines.append("\n---\n")
    lines.append("*Report generated by ShyPN experimental CLI*")
    
    # Write report
    with open(output_path, 'w') as f:
        f.write('\n'.join(lines))

def main():
    parser = argparse.ArgumentParser(description='Generate comprehensive experiment report')
    parser.add_argument('--validation', help='Path to validation_results.json')
    parser.add_argument('--benchmark', help='Path to benchmark_results.json')
    parser.add_argument('--dependency', help='Path to dependency_analysis.json')
    parser.add_argument('-o', '--output', default='experiment_report.md')
    args = parser.parse_args()
    
    try:
        # Collect all data
        data = {
            'validation': load_json(args.validation) if args.validation else None,
            'benchmark': load_json(args.benchmark) if args.benchmark else None,
            'dependency': load_json(args.dependency) if args.dependency else None
        }
        
        # Check if we have any data
        if not any(data.values()):
            sys.exit("ERROR: No input files provided. Use --validation, --benchmark, and/or --dependency")
        
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        print("Generating experiment report...")
        generate_markdown_report(data, output_path)
        print(f"✓ Report saved: {output_path}")
        
    except Exception as e:
        sys.exit(f"ERROR: {e}")

if __name__ == '__main__':
    main()
