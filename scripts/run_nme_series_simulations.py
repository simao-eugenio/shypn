#!/usr/bin/env python3
"""
Batch simulation script for N-methylation series (N_Me 0-6) using enhanced models.
Tests all enhanced models to verify they work with the bug fixes.

Supports parameter sweeps for testing different transport rates across all models.

NOTE: This script uses programmatic simulation. For interactive parameter sweeps
with the UI, use the Viability panel instead.
"""
import sys
import os
import argparse
from pathlib import Path
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from shypn.data.canvas.document_model import DocumentModel
from shypn.engine.simulation.controller import SimulationController

# Configuration
MODELS_DIR = Path("workspace/projects/My_Project/drug_discovery/models/manuscript")
DATA_DIR = Path("workspace/projects/My_Project/drug_discovery/data/n_methylation")
SIMULATION_TIME = 60  # seconds (default, can be overridden)
OUTPUT_INTERVAL = 0.05  # seconds

# Models to simulate
MODELS = [
    ("macrocycle_transport_normal_nme_0_enhanced.shy", "sim_nme_normal_0_enhanced.csv", 0),
    ("macrocycle_transport_normal_nme_1_enhanced.shy", "sim_nme_normal_1_enhanced.csv", 1),
    ("macrocycle_transport_normal_nme_2_enhanced.shy", "sim_nme_normal_2_enhanced.csv", 2),
    ("macrocycle_transport_normal_nme_3_enhanced.shy", "sim_nme_normal_3_enhanced.csv", 3),
    ("macrocycle_transport_normal_nme_4_enhanced.shy", "sim_nme_normal_4_enhanced.csv", 4),
    ("macrocycle_transport_normal_nme_5_enhanced.shy", "sim_nme_normal_5_enhanced.csv", 5),
    ("macrocycle_transport_normal_nme_6_enhanced.shy", "sim_nme_normal_6_enhanced.csv", 6),
]


def run_simulation(model_file, output_file, nme_level, duration=60, transport_rate=None):
    """Run a single simulation programmatically.
    
    Args:
        model_file: Model filename
        output_file: Output CSV filename
        nme_level: N-methylation level (0-6)
        duration: Simulation duration in seconds
        transport_rate: Optional transport rate multiplier (e.g., 0.8, 1.0, 1.5)
    """
    model_path = MODELS_DIR / model_file
    
    # Adjust output filename if transport_rate is specified
    if transport_rate is not None and transport_rate != 1.0:
        base_name = output_file.replace('.csv', '')
        output_file = f"{base_name}_rate{transport_rate}.csv"
    
    output_path = DATA_DIR / output_file
    
    print(f"\n{'='*80}")
    print(f"Simulating: {model_file}")
    print(f"N-methylation level: {nme_level}")
    if transport_rate is not None:
        print(f"Transport rate: {transport_rate}× baseline")
    print(f"Output: {output_file}")
    print(f"{'='*80}")
    
    if not model_path.exists():
        print(f"❌ ERROR: Model not found: {model_path}")
        return False
    
    # Ensure data directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        # Load model
        print(f"  Loading model...")
        model = DocumentModel.load_from_file(str(model_path))
        
        if not model:
            print(f"  ❌ ERROR: Failed to load model")
            return False
        
        print(f"  ✓ Model loaded: {len(model.places)} places, {len(model.transitions)} transitions")
        
        # Modify transport rate if specified
        if transport_rate is not None and transport_rate != 1.0:
            print(f"  ⚠️  WARNING: Transport rate modification ({transport_rate}×) not yet implemented")
            print(f"      Simulation will run with model's default rates")
            # TODO: Identify transport transition and scale its rate
            # for trans in model.transitions:
            #     if 'transport' in trans.name.lower():
            #         trans.rate *= transport_rate
        
        # Create simulation controller
        print(f"  Initializing simulation controller...")
        controller = SimulationController(model)
        controller.settings.use_tau_leaping = True
        controller.settings.tau_epsilon = 0.03
        controller.settings.duration = duration  # Set duration limit
        controller.settings.duration_unit = 'seconds'
        
        # Run simulation
        print(f"  Running simulation (duration={duration}s, method=adaptive-hybrid)...")
        start_time = datetime.now()
        
        controller.data_collector.start_collection()
        controller.data_collector.record_state(0.0)
        
        # Simulate using step() until duration reached
        step_count = 0
        while controller.time < duration and step_count < 1000000:  # Safety limit
            success = controller.step()
            if not success:
                break  # Deadlock or error
            step_count += 1
            
            # Record data periodically
            if step_count % 100 == 0:  # Record every 100 steps
                controller.data_collector.record_state(controller.time)
        
        # Final recording
        controller.data_collector.record_state(controller.time)
        
        elapsed = (datetime.now() - start_time).total_seconds()
        
        print(f"  Completed {step_count} simulation steps, final time={controller.time:.2f}s")
        
        # Export data
        print(f"  Exporting results to CSV...")
        controller.data_collector.export_csv(str(output_path))
        
        print(f"\n  ✅ SUCCESS (completed in {elapsed:.1f}s)")
        
        # Check output file
        if output_path.exists():
            size_kb = output_path.stat().st_size / 1024
            print(f"  Output file: {output_path}")
            print(f"  File size: {size_kb:.1f} KB")
            
            # Count lines
            with open(output_path, 'r') as f:
                line_count = sum(1 for _ in f)
            print(f"  Data points: {line_count - 1} (excluding header)")
            
            return True
        else:
            print(f"  ⚠️  WARNING: Output file not created")
            return False
            
    except Exception as e:
        print(f"\n  ❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all simulations."""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Batch simulation for N-methylation series (N_Me 0-6)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all models with default settings (60s)
  python run_nme_series_simulations.py
  
  # Run with longer duration
  python run_nme_series_simulations.py --duration 200
  
  # Test specific transport rates (sub-net sweep validation)
  python run_nme_series_simulations.py --transport-rates 0.8,1.0,1.5 --duration 200
  
  # Run specific N-methylation levels only
  python run_nme_series_simulations.py --models 0,3,6 --duration 100
        """
    )
    parser.add_argument(
        "--duration", 
        type=float, 
        default=60,
        help="Simulation duration in seconds (default: 60)"
    )
    parser.add_argument(
        "--transport-rates",
        type=str,
        default=None,
        help="Comma-separated transport rate multipliers to test (e.g., 0.8,1.0,1.5)"
    )
    parser.add_argument(
        "--models",
        type=str,
        default=None,
        help="Comma-separated N-methylation levels to run (e.g., 0,3,6). Default: all (0-6)"
    )
    
    args = parser.parse_args()
    
    # Parse transport rates
    transport_rates = None
    if args.transport_rates:
        try:
            transport_rates = [float(r.strip()) for r in args.transport_rates.split(',')]
            print(f"Testing transport rates: {transport_rates}")
        except ValueError:
            print(f"❌ ERROR: Invalid transport rates format: {args.transport_rates}")
            print(f"   Expected format: 0.8,1.0,1.5")
            return False
    
    # Parse model selection
    selected_models = None
    if args.models:
        try:
            selected_models = [int(m.strip()) for m in args.models.split(',')]
            print(f"Selected N-methylation levels: {selected_models}")
        except ValueError:
            print(f"❌ ERROR: Invalid model selection: {args.models}")
            print(f"   Expected format: 0,3,6")
            return False
    
    # Filter models if specific levels requested
    models_to_run = MODELS
    if selected_models is not None:
        models_to_run = [(m, o, n) for m, o, n in MODELS if n in selected_models]
        if not models_to_run:
            print(f"❌ ERROR: No models match selection: {selected_models}")
            return False
    
    print("="*80)
    print("BATCH SIMULATION: N-METHYLATION SERIES (Enhanced Models)")
    print("="*80)
    print(f"\nModels directory: {MODELS_DIR}")
    print(f"Output directory: {DATA_DIR}")
    print(f"Number of models: {len(models_to_run)}")
    print(f"Simulation time: {args.duration}s per model")
    print(f"Method: adaptive-hybrid")
    if transport_rates:
        print(f"Transport rate sweep: {transport_rates}")
    
    # Verify directories exist
    if not MODELS_DIR.exists():
        print(f"\n❌ ERROR: Models directory not found: {MODELS_DIR}")
        return False
    
    print(f"\n✓ Models directory found")
    
    # Run simulations
    start_time = datetime.now()
    results = []
    
    # Determine if we're doing a transport rate sweep
    if transport_rates:
        # Run each model at each transport rate
        for model_file, output_file, nme_level in models_to_run:
            for rate in transport_rates:
                success = run_simulation(
                    model_file, output_file, nme_level, 
                    duration=args.duration,
                    transport_rate=rate
                )
                results.append((f"{model_file} (rate={rate})", success))
    else:
        # Standard run: each model once
        for model_file, output_file, nme_level in models_to_run:
            success = run_simulation(
                model_file, output_file, nme_level,
                duration=args.duration,
                transport_rate=None
            )
            results.append((model_file, success))
    
    total_elapsed = (datetime.now() - start_time).total_seconds()
    
    # Summary
    print(f"\n{'='*80}")
    print(f"SIMULATION SUMMARY")
    print(f"{'='*80}")
    
    successful = sum(1 for _, success in results if success)
    failed = len(results) - successful
    
    print(f"\n  Total simulations: {len(results)}")
    print(f"  Successful: {successful}")
    print(f"  Failed: {failed}")
    print(f"  Total time: {total_elapsed:.1f}s ({total_elapsed/60:.1f} min)")
    print(f"  Average time: {total_elapsed/len(results):.1f}s per simulation")
    
    print(f"\n  Results:")
    for model_file, success in results:
        status = "✓" if success else "✗"
        print(f"    {status} {model_file}")
    
    if successful == len(results):
        print(f"\n  🎉 ALL SIMULATIONS SUCCESSFUL!")
        print(f"  Data ready for analysis in: {DATA_DIR}")
        print(f"\n  Next steps:")
        print(f"    1. Compare results across N-methylation series")
        print(f"    2. Validate against manuscript predictions")
        print(f"    3. Generate plots and statistical analysis")
    else:
        print(f"\n  ⚠️  Some simulations failed - check error messages above")
    
    print(f"\n{'='*80}")
    
    return successful == len(results)


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
