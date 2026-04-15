#!/usr/bin/env python3
"""
Quick test to verify the ATP sweep parameter bug fix.
Runs 3 experiments with ATP=[0, 100, 5000] and checks:
1. ~/sweep_debug.log shows correct parameter application
2. CSV files contain correct initial ATP values
"""

import os
import sys
import csv
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from shypn.ui.panels.viability.automation.batch_executor import BatchExecutor

def main():
    # Clean debug log
    debug_log = Path.home() / 'sweep_debug.log'
    if debug_log.exists():
        debug_log.unlink()
    
    print("🧪 Testing sweep parameter fix...")
    print(f"Debug log: {debug_log}")
    
    # Setup paths - use the enhanced model from manuscript
    model_path = Path.home() / 'projetos/shypn/workspace/projects/My_Project/drug_discovery/models/manuscript/macrocycle_transport_normal_nme_0_enhanced.shy'
    output_dir = Path.home() / 'projetos/shypn/workspace/projects/My_Project/sweep_test'
    output_dir.mkdir(exist_ok=True, parents=True)
    
    if not model_path.exists():
        print(f"❌ Model not found: {model_path}")
        print(f"\n Available models:")
        model_dir = model_path.parent
        if model_dir.exists():
            for f in sorted(model_dir.glob('*.shy')):
                print(f"   {f.name}")
        return 1
    
    # Run mini-sweep: ATP = [0, 100, 5000]
    executor = BatchExecutor(model_path, output_dir)
    
    # Configure sweep
    sweep_config = {
        'place_id': 'P7',  # ATP_pool
        'place_name': 'ATP_pool',
        'min_value': 0.0,
        'max_value': 5000.0,
        'num_experiments': 3,
        'distribution': 'linear'
    }
    
    print(f"\n📊 Running sweep: ATP = [0, 100, 5000]")
    print(f"   Model: {model_path.name}")
    print(f"   Output: {output_dir}")
    print(f"   Mode: parallel")
    
    # Run in parallel mode to test the fixed dict handling
    executor.run_sweep(
        sweep_config=sweep_config,
        parallel=True,
        num_workers=2
    )
    
    print("\n✅ Sweep complete!")
    
    # Verify results
    print("\n🔍 Verification:")
    
    # 1. Check debug log
    if debug_log.exists():
        print(f"\n📝 Debug log contents:")
        with open(debug_log) as f:
            log_contents = f.read()
            print(log_contents)
            
            # Check for swept parameter applications
            if '[WORKER] ✓ SWEPT PARAM: P7 = 5000' in log_contents:
                print("✅ Swept parameter application detected!")
            else:
                print("⚠️ No swept parameter application found")
    else:
        print(f"⚠️ Debug log not created")
    
    # 2. Check CSV files
    print(f"\n📊 CSV Initial Values:")
    csv_files = sorted(output_dir.glob('*.csv'))
    
    for csv_file in csv_files:
        try:
            with open(csv_file, 'r') as f:
                reader = csv.DictReader(f)
                headers = reader.fieldnames
                
                if 'ATP_pool' in headers:
                    first_row = next(reader)
                    initial_atp = float(first_row['ATP_pool'])
                    
                    # Find which experiment this is
                    exp_name = csv_file.stem
                    print(f"   {exp_name}: ATP_pool = {initial_atp} µM")
                    
                    # Check if it's NOT 5000 for the first experiment
                    if '0' in exp_name and initial_atp == 0.0:
                        print(f"      ✅ CORRECT (expected 0)")
                    elif 'P7_' in exp_name and initial_atp != 5000.0:
                        print(f"      ✅ SWEPT VALUE APPLIED")
                    elif initial_atp == 5000.0:
                        print(f"      ❌ Still baseline value (bug not fixed)")
        except Exception as e:
            print(f"   ⚠️ Error reading {csv_file.name}: {e}")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
