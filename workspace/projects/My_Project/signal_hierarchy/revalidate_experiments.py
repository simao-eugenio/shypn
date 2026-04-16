#!/usr/bin/env python3
"""
Re-validate Signal Hierarchy Experiments after Bug Fix

CRITICAL BUG FIXED (Dec 27, 2025):
- Before: Normal arcs to signal places had READ-ONLY behavior (no token consumption)
- After: Normal arcs to signal places CONSUME tokens (normalized behavior)

This script re-runs the key experimental batches to validate that the paper's
conclusions remain intact after the bug fix.

Key Experiments to Re-run:
1. batch_20251225_235533 (100 UV enabled) - Information flow analysis
2. batch_20251226_010448 (100 NO UV) - Information flow analysis
3. batch_20251225_084841 (100 UV cycle) - UV cycle validation
4. batch_20251225_011804 (100 UV depleted) - Bistability baseline

Author: Eugénio Simão
Date: December 27, 2025
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / 'src'))

def backup_model(model_path):
    """Create timestamped backup of model before re-validation."""
    backup_path = model_path.parent / f"{model_path.stem}_PRE_BUGFIX_{datetime.now().strftime('%Y%m%d_%H%M%S')}.shy"
    import shutil
    shutil.copy2(model_path, backup_path)
    print(f"✓ Backed up model to: {backup_path}")
    return backup_path

def check_arc_types(model_path):
    """Verify arc types in model after bug fix."""
    with open(model_path, 'r') as f:
        model = json.load(f)
    
    signal_places = {p['id'] for p in model['places'] if p.get('is_signal_place', False)}
    
    print(f"\n=== Arc Type Analysis ===")
    print(f"Signal places: {len(signal_places)}")
    
    arc_types = {'normal': 0, 'signal_flow': 0, 'test': 0, 'inhibitor': 0}
    consuming_from_signal = []
    
    for arc in model['arcs']:
        arc_type = arc.get('arc_type', 'normal')
        arc_types[arc_type] = arc_types.get(arc_type, 0) + 1
        
        # Check if normal arc consumes from signal place
        if arc_type == 'normal' and arc['source_id'] in signal_places:
            # This is an OUTPUT arc (signal place is source) - will NOW consume
            consuming_from_signal.append({
                'id': arc['id'],
                'source': arc['source_id'],
                'target': arc['target_id'],
                'weight': arc.get('weight', 1)
            })
    
    print(f"\nArc type distribution:")
    for atype, count in arc_types.items():
        print(f"  {atype}: {count}")
    
    print(f"\n⚠️  CRITICAL: {len(consuming_from_signal)} normal arcs NOW CONSUME from signal places:")
    for arc in consuming_from_signal[:10]:  # Show first 10
        print(f"  {arc['id']}: {arc['source']} → {arc['target']} (weight={arc['weight']})")
    
    return len(consuming_from_signal) > 0

def run_batch_simulation(model_path, config, output_dir):
    """Run batch simulation with given configuration."""
    print(f"\n{'='*60}")
    print(f"Running: {config['name']}")
    print(f"{'='*60}")
    
    cmd = [
        sys.executable,
        'workspace/projects/My_Project/signal_hierarchy/run_batch_simulation.py',
        '--model', str(model_path),
        '--replicates', str(config['replicates']),
        '--duration', str(config['duration']),
        '--output', str(output_dir / config['batch_name']),
        '--condition', config['condition']
    ]
    
    if config.get('uv_enabled'):
        cmd.append('--uv-enabled')
    
    print(f"Command: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ FAILED: {result.stderr}")
        return False
    
    print(f"✓ Completed: {config['name']}")
    return True

def main():
    """Re-run critical experiments after bug fix."""
    print("="*70)
    print("SIGNAL HIERARCHY EXPERIMENT RE-VALIDATION")
    print("Bug Fix: Normal arcs now CONSUME from signal places")
    print("="*70)
    
    # Paths
    project_dir = Path(__file__).parent
    model_path = project_dir / 'models' / 'lambda_hierarchical_v3.shy'
    output_dir = project_dir / 'data' / 'results_AFTER_BUGFIX'
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Backup model
    backup_path = backup_model(model_path)
    
    # Check arc types
    has_consuming_arcs = check_arc_types(model_path)
    
    if not has_consuming_arcs:
        print("\n⚠️  WARNING: No consuming arcs found. Bug fix may not be applied to model!")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            print("Aborted.")
            return
    
    # Define experimental batches
    experiments = [
        {
            'name': 'Experiment 1: UV Enabled (Information Flow)',
            'batch_name': 'batch_UV_enabled',
            'replicates': 100,
            'duration': 5000,
            'condition': 'balanced',
            'uv_enabled': True,
            'original': 'batch_20251225_235533'
        },
        {
            'name': 'Experiment 2: NO UV (Information Flow)',
            'batch_name': 'batch_NO_UV',
            'replicates': 100,
            'duration': 5000,
            'condition': 'balanced',
            'uv_enabled': False,
            'original': 'batch_20251226_010448'
        },
        {
            'name': 'Experiment 3: UV Cycle Validation',
            'batch_name': 'batch_UV_cycle',
            'replicates': 100,
            'duration': 3000,
            'condition': 'zero',
            'uv_enabled': True,
            'original': 'batch_20251225_084841'
        },
        {
            'name': 'Experiment 4: Bistability Baseline',
            'batch_name': 'batch_baseline',
            'replicates': 100,
            'duration': 3000,
            'condition': 'zero',
            'uv_enabled': False,
            'original': 'batch_20251225_011804'
        }
    ]
    
    # Confirmation
    print(f"\n📋 Plan: Re-run {len(experiments)} experimental batches")
    print(f"   Total replicates: {sum(e['replicates'] for e in experiments)}")
    print(f"   Output directory: {output_dir}")
    print(f"\n⚠️  This will take significant computation time!")
    
    response = input("\nProceed with re-validation? (y/n): ")
    if response.lower() != 'y':
        print("Aborted.")
        return
    
    # Run experiments
    results = []
    for exp in experiments:
        success = run_batch_simulation(model_path, exp, output_dir)
        results.append({'experiment': exp['name'], 'success': success})
    
    # Summary
    print(f"\n{'='*70}")
    print("RE-VALIDATION COMPLETE")
    print(f"{'='*70}")
    
    for i, result in enumerate(results, 1):
        status = "✓ PASS" if result['success'] else "❌ FAIL"
        print(f"{i}. {result['experiment']}: {status}")
    
    # Next steps
    print(f"\n📊 Next Steps:")
    print(f"1. Run analyze_information_flow.py on new data")
    print(f"2. Compare results with original batches")
    print(f"3. Update paper if conclusions change")
    print(f"\n💾 Original model backed up to: {backup_path.name}")

if __name__ == '__main__':
    main()
