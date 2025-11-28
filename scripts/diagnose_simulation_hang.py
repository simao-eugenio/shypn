"""Diagnose simulation hang after parameter application.

This script helps identify why simulations hang after applying heuristic parameters.
It performs step-by-step validation of:
1. Model loading
2. Parameter application
3. Rate function evaluation
4. Simulation initialization
5. Simulation stepping

Usage:
    python scripts/diagnose_simulation_hang.py path/to/model.shy
    
    # With verbose output
    LOGLEVEL=DEBUG python scripts/diagnose_simulation_hang.py path/to/model.shy
"""

import sys
import logging
import traceback
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from shypn.data.model_canvas_manager import ModelCanvasManager
from shypn.crossfetch.controllers.heuristic_parameters_controller import HeuristicParametersController
from shypn.engine.simulation.controller import SimulationController

# Setup logging
log_level = logging.DEBUG if 'DEBUG' in str(sys.argv) else logging.INFO
logging.basicConfig(
    level=log_level,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


def diagnose_hang(model_path):
    """Diagnose simulation hang after parameter application.
    
    Args:
        model_path: Path to .shy model file
    """
    print("\n" + "="*70)
    print("SIMULATION HANG DIAGNOSTIC")
    print("="*70)
    print(f"Model: {model_path}\n")
    
    # Step 1: Load model
    print("STEP 1: Loading model...")
    try:
        manager = ModelCanvasManager.load_from_file(model_path)
        doc = manager.document_controller
        print(f"  ✓ Model loaded successfully")
        print(f"    Places: {len(list(doc.places))}")
        print(f"    Transitions: {len(list(doc.transitions))}")
        print(f"    Arcs: {len(list(doc.arcs))}")
    except Exception as e:
        print(f"  ✗ FAILED to load model: {e}")
        traceback.print_exc()
        return False
    
    # Step 2: Apply heuristic parameters
    print("\nSTEP 2: Applying heuristic parameters...")
    try:
        controller = HeuristicParametersController(manager)
        results = controller.infer_all_parameters()
        print(f"  ✓ Parameters applied")
        print(f"    Inferred: {results.get('inferred', 0)} transitions")
        print(f"    Failed: {results.get('failed', 0)} transitions")
    except Exception as e:
        print(f"  ✗ FAILED to apply parameters: {e}")
        traceback.print_exc()
        return False
    
    # Step 3: Validate all transitions
    print("\nSTEP 3: Validating transition configurations...")
    validation_errors = []
    
    for trans in doc.transitions:
        trans_id = trans.id
        trans_type = getattr(trans, 'transition_type', 'immediate')
        rate_func = trans.properties.get('rate_function', '')
        
        print(f"\n  Transition: {trans_id}")
        print(f"    Type: {trans_type}")
        print(f"    Rate: {rate_func}")
        
        # Check for missing rate function
        if trans_type in ['continuous', 'stochastic'] and not rate_func:
            error = f"Missing rate function for {trans_type} transition"
            print(f"    ✗ {error}")
            validation_errors.append((trans_id, error))
            continue
        
        # Check for invalid Km/Vmax
        km = trans.properties.get('km')
        vmax = trans.properties.get('vmax')
        
        if km is not None:
            print(f"    Km: {km}")
            if km <= 0:
                error = f"Invalid Km={km} (must be > 0)"
                print(f"    ✗ {error}")
                validation_errors.append((trans_id, error))
        
        if vmax is not None:
            print(f"    Vmax: {vmax}")
            if vmax <= 0:
                error = f"Invalid Vmax={vmax} (must be > 0)"
                print(f"    ✗ {error}")
                validation_errors.append((trans_id, error))
        
        # Try to compile rate function
        if rate_func:
            try:
                compile(rate_func, '<string>', 'eval')
                print(f"    ✓ Rate function syntax OK")
            except SyntaxError as e:
                error = f"Invalid rate function syntax: {e}"
                print(f"    ✗ {error}")
                validation_errors.append((trans_id, error))
        
        # Check input arcs
        input_arcs = [arc for arc in doc.arcs if arc.target == trans]
        print(f"    Input arcs: {len(input_arcs)}")
        for arc in input_arcs:
            source_place = arc.source
            print(f"      {source_place.id} -> {trans_id} (weight={arc.weight})")
    
    if validation_errors:
        print(f"\n  ✗ Found {len(validation_errors)} validation errors!")
        for trans_id, error in validation_errors:
            print(f"    - {trans_id}: {error}")
    else:
        print("\n  ✓ All transitions validated successfully")
    
    # Step 4: Check simulation controller initialization
    print("\nSTEP 4: Initializing simulation controller...")
    try:
        sim = SimulationController(manager)
        print(f"  ✓ Simulation controller initialized")
        print(f"    Current time: {sim.current_time}")
        print(f"    State: {getattr(sim, 'state', 'unknown')}")
    except Exception as e:
        print(f"  ✗ FAILED to initialize simulation: {e}")
        traceback.print_exc()
        return False
    
    # Step 5: Try reset
    print("\nSTEP 5: Testing simulation reset...")
    try:
        sim.reset()
        print(f"  ✓ Reset successful")
        print(f"    Current time after reset: {sim.current_time}")
    except Exception as e:
        print(f"  ✗ FAILED to reset: {e}")
        traceback.print_exc()
        return False
    
    # Step 6: Try simulation steps
    print("\nSTEP 6: Testing simulation steps...")
    print(f"  Attempting 10 steps with dt=0.1...")
    
    try:
        for i in range(10):
            print(f"    Step {i+1}/10...", end=' ', flush=True)
            
            # Check enabled transitions before step
            enabled_count = 0
            for trans in doc.transitions:
                if hasattr(trans, 'is_enabled') and trans.is_enabled():
                    enabled_count += 1
            
            print(f"({enabled_count} enabled)", end=' ', flush=True)
            
            # Perform step
            sim.step(time_step=0.1)
            
            print(f"✓ time={sim.current_time:.2f}")
        
        print(f"\n  ✓ All steps completed successfully!")
        print(f"    Final time: {sim.current_time}")
        
    except Exception as e:
        print(f"\n  ✗ HANG/ERROR at step {i+1}: {e}")
        print(f"    Time when failed: {sim.current_time}")
        traceback.print_exc()
        
        # Additional diagnostics
        print("\n  Additional diagnostics:")
        print(f"    Enabled transitions at failure:")
        for trans in doc.transitions:
            if hasattr(trans, 'is_enabled'):
                try:
                    enabled = trans.is_enabled()
                    if enabled:
                        print(f"      - {trans.id} (enabled)")
                except Exception as trans_e:
                    print(f"      - {trans.id} (error checking: {trans_e})")
        
        return False
    
    # Step 7: Summary
    print("\n" + "="*70)
    print("DIAGNOSTIC SUMMARY")
    print("="*70)
    
    if validation_errors:
        print(f"⚠️  VALIDATION WARNINGS: {len(validation_errors)} issues found")
        print("   These may cause simulation problems:")
        for trans_id, error in validation_errors:
            print(f"     • {trans_id}: {error}")
    else:
        print("✅ NO ISSUES DETECTED - Simulation works correctly!")
        print("   If you're experiencing hangs, it may be UI-related.")
        print("   Try running from command line without GUI.")
    
    print("="*70 + "\n")
    return len(validation_errors) == 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/diagnose_simulation_hang.py path/to/model.shy")
        print("\nOptions:")
        print("  Add 'DEBUG' anywhere in args for verbose output")
        print("\nExample:")
        print("  python scripts/diagnose_simulation_hang.py workspace/projects/models/hsa00010.shy")
        sys.exit(1)
    
    model_path = sys.argv[1]
    if not Path(model_path).exists():
        print(f"Error: Model file not found: {model_path}")
        sys.exit(1)
    
    success = diagnose_hang(model_path)
    sys.exit(0 if success else 1)
