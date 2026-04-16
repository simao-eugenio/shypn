#!/usr/bin/env python3
"""
Re-simulate N-methylation series with corrected models.

After fixing passive diffusion formula bugs and rate field refactoring,
all CSV files need to be regenerated.

Usage:
  python resimulate_nme_series.py

Output:
  Generates corrected CSV files in workspace/projects/My_Project/drug_discovery/data/n_methylation/
  Filenames: sim_nme_{series}_{level}_enhanced_corrected.csv
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, 'src')

from shypn.document_model import DocumentModel
from shypn.engine.simulation.controller import SimulationController

# Configuration
MODEL_DIR = Path("workspace/projects/My_Project/drug_discovery/models/manuscript")
OUTPUT_DIR = Path("workspace/projects/My_Project/drug_discovery/data/n_methylation")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Simulation parameters
SIM_DURATION = 60.0  # seconds
TIME_STEP = 0.01     # 10 ms

# Models to simulate
MODELS = [
    # Normal series
    ("normal", 1), ("normal", 2), ("normal", 3), ("normal", 4),
    ("normal", 5), ("normal", 6), ("normal", 7),
    # Tumor series
    ("tumor", 1), ("tumor", 2), ("tumor", 3), ("tumor", 4),
    ("tumor", 5), ("tumor", 6), ("tumor", 7),
]

def simulate_model(series, nme_level):
    """Simulate a single N-methylation model."""
    model_file = MODEL_DIR / f"macrocycle_transport_{series}_nme_{nme_level}_enhanced.shy"
    output_file = OUTPUT_DIR / f"sim_nme_{series}_{nme_level}_enhanced_corrected.csv"
    
    print(f"\n{'='*80}")
    print(f"Simulating: {series.upper()} N-Me {nme_level}")
    print(f"{'='*80}")
    print(f"Model: {model_file.name}")
    print(f"Output: {output_file.name}")
    
    if not model_file.exists():
        print(f"⚠️  Model file not found: {model_file}")
        return False
    
    try:
        # Load model
        print(f"\n📂 Loading model...")
        doc_model = DocumentModel()
        doc_model.load_from_file(str(model_file))
        
        # Create simulation controller
        print(f"⚙️  Initializing simulation...")
        controller = SimulationController(doc_model.model)
        
        # Configure simulation
        controller.set_time_parameters(
            duration=SIM_DURATION,
            step=TIME_STEP
        )
        
        # Run simulation
        print(f"▶️  Running simulation (duration={SIM_DURATION}s, dt={TIME_STEP}s)...")
        success = controller.run_simulation()
        
        if not success:
            print(f"❌ Simulation failed")
            return False
        
        # Export results
        print(f"💾 Exporting to CSV...")
        controller.export_to_csv(str(output_file))
        
        # Get stats
        time_points = len(controller.time_series)
        print(f"\n✓ Success!")
        print(f"  Time points: {time_points}")
        print(f"  Final time: {controller.time_series[-1]:.2f}s")
        print(f"  Output size: {output_file.stat().st_size / 1024:.1f} KB")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error during simulation: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("="*80)
    print("RE-SIMULATE N-METHYLATION SERIES (CORRECTED MODELS)")
    print("="*80)
    print(f"\nModels directory: {MODEL_DIR}")
    print(f"Output directory: {OUTPUT_DIR}")
    print(f"Total models to simulate: {len(MODELS)}")
    print(f"\nSimulation parameters:")
    print(f"  Duration: {SIM_DURATION}s")
    print(f"  Time step: {TIME_STEP}s")
    print(f"  Expected time points: ~{int(SIM_DURATION/TIME_STEP)}")
    
    # Confirm
    response = input(f"\nProceed with {len(MODELS)} simulations? [y/N]: ")
    if response.lower() != 'y':
        print("Cancelled.")
        return
    
    # Run simulations
    results = []
    for series, level in MODELS:
        success = simulate_model(series, level)
        results.append((series, level, success))
    
    # Summary
    print(f"\n{'='*80}")
    print(f"SUMMARY")
    print(f"{'='*80}")
    
    successful = sum(1 for _, _, success in results if success)
    failed = len(results) - successful
    
    print(f"\nCompleted: {successful}/{len(results)}")
    if failed > 0:
        print(f"Failed: {failed}")
        print(f"\nFailed simulations:")
        for series, level, success in results:
            if not success:
                print(f"  • {series} N-Me {level}")
    
    if successful == len(results):
        print(f"\n✓ All simulations completed successfully!")
        print(f"✓ New CSV files ready for analysis")
        print(f"\nFiles generated in: {OUTPUT_DIR}")
    
    print(f"{'='*80}\n")

if __name__ == "__main__":
    main()
