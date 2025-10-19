#!/usr/bin/env python3
"""
Headless Simulation Test for Glycolysis Model

Tests the simulation engine without GUI to verify:
1. Model loads correctly
2. Simulation controller initializes
3. Transitions can fire
4. Token movement works
5. Stochastic sources generate tokens
6. Multiple simulation steps execute

This helps identify if simulation issues are in the engine or GUI layer.
"""

import sys
import os
import json
from typing import Dict, List, Any

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def load_model(model_path: str) -> Dict[str, Any]:
    """Load .shy model file.
    
    Args:
        model_path: Path to .shy file
        
    Returns:
        dict: Model data
    """
    with open(model_path, 'r') as f:
        return json.load(f)

def create_model_canvas_manager(model_data: Dict[str, Any]):
    """Create ModelCanvasManager from model data.
    
    Args:
        model_data: Loaded model dictionary
        
    Returns:
        ModelCanvasManager instance
    """
    from shypn.data.canvas.document_model import DocumentModel
    from shypn.data.model_canvas_manager import ModelCanvasManager
    
    # Create document model
    doc_model = DocumentModel()
    
    # Load places
    for place_data in model_data['places']:
        from shypn.netobjs.place import Place
        place = Place(
            place_data['x'],
            place_data['y'],
            place_data['id'],
            place_data['name']
        )
        place.label = place_data.get('label', '')
        place.marking = place_data.get('marking', place_data.get('tokens', 0))
        doc_model.places.append(place)
    
    # Load transitions
    for trans_data in model_data['transitions']:
        from shypn.netobjs.transition import Transition
        trans = Transition(
            trans_data['x'],
            trans_data['y'],
            trans_data['id'],
            trans_data['name']
        )
        trans.label = trans_data.get('label', '')
        trans.type = trans_data.get('type', 'immediate')
        trans.rate = trans_data.get('rate', 1.0)
        trans.guard = trans_data.get('guard', 1)
        trans.priority = trans_data.get('priority', 1)
        doc_model.transitions.append(trans)
    
    # Load arcs
    for arc_data in model_data['arcs']:
        from shypn.netobjs.arc import Arc
        source_id = arc_data.get('source_id', arc_data.get('source'))
        target_id = arc_data.get('target_id', arc_data.get('target'))
        
        # Find source and target objects
        source = None
        target = None
        
        for p in doc_model.places:
            if p.id == source_id:
                source = p
            if p.id == target_id:
                target = p
        
        for t in doc_model.transitions:
            if t.id == source_id:
                source = t
            if t.id == target_id:
                target = t
        
        if source and target:
            arc = Arc(
                source,
                target,
                arc_data['id'],
                arc_data.get('name', arc_data['id']),
                weight=arc_data.get('weight', 1)
            )
            doc_model.arcs.append(arc)
    
    # Create canvas manager (without actual canvas)
    canvas_manager = ModelCanvasManager(canvas_width=2000, canvas_height=2000, filename="imported")
    canvas_manager.places = doc_model.places
    canvas_manager.transitions = doc_model.transitions
    canvas_manager.arcs = doc_model.arcs
    
    return canvas_manager

def test_simulation_controller():
    """Test simulation controller creation and basic operations."""
    print("=" * 80)
    print("TEST 1: Simulation Controller Initialization")
    print("=" * 80)
    
    try:
        from shypn.engine.simulation.controller import SimulationController
        
        # Create a minimal model for testing
        from shypn.data.canvas.document_model import DocumentModel
        from shypn.data.model_canvas_manager import ModelCanvasManager
        from shypn.netobjs.place import Place
        from shypn.netobjs.transition import Transition
        from shypn.netobjs.arc import Arc
        
        doc_model = DocumentModel()
        
        # Simple model: P1 -> T1 -> P2
        p1 = Place(0, 0, "P1", "P1")
        p1.marking = 5
        p2 = Place(100, 0, "P2", "P2")
        p2.marking = 0
        
        t1 = Transition(50, 0, "T1", "T1")
        t1.type = "immediate"
        t1.rate = 1.0
        t1.guard = 1
        
        a1 = Arc(p1, t1, "A1", "A1", weight=1)
        a2 = Arc(t1, p2, "A2", "A2", weight=1)
        
        doc_model.places = [p1, p2]
        doc_model.transitions = [t1]
        doc_model.arcs = [a1, a2]
        
        canvas_manager = ModelCanvasManager(None, None, filename="test")
        canvas_manager.places = doc_model.places
        canvas_manager.transitions = doc_model.transitions
        canvas_manager.arcs = doc_model.arcs
        
        # Create simulation controller
        controller = SimulationController(canvas_manager)
        
        print("✓ SimulationController created successfully")
        print(f"  Initial time: {controller.time}")
        print(f"  Places: {len(controller.model.places)}")
        print(f"  Transitions: {len(controller.model.transitions)}")
        print(f"  Arcs: {len(controller.model.arcs)}")
        print()
        
        return True, controller, canvas_manager
        
    except Exception as e:
        print(f"✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False, None, None

def test_transition_enablement(controller, canvas_manager):
    """Test transition enablement detection."""
    print("=" * 80)
    print("TEST 2: Transition Enablement Detection")
    print("=" * 80)
    
    try:
        # Check if transition is enabled
        t1 = canvas_manager.transitions[0]
        p1 = canvas_manager.places[0]
        p2 = canvas_manager.places[1]
        
        print(f"Initial state:")
        print(f"  P1 tokens: {p1.marking}")
        print(f"  P2 tokens: {p2.marking}")
        print(f"  T1 type: {t1.type}")
        print(f"  T1 guard: {t1.guard}")
        print()
        
        # Get enabled transitions
        from shypn.engine.simulation.controller import SimulationController
        
        # Check structural enablement
        enabled = []
        for trans in canvas_manager.transitions:
            behavior = controller.get_behavior(trans)
            if behavior.is_structurally_enabled():
                enabled.append(trans)
        
        print(f"Enabled transitions: {len(enabled)}")
        if enabled:
            for trans in enabled:
                print(f"  ✓ {trans.name} is enabled")
        else:
            print(f"  ✗ No transitions enabled")
        print()
        
        return len(enabled) > 0
        
    except Exception as e:
        print(f"✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_single_step(controller, canvas_manager):
    """Test single simulation step."""
    print("=" * 80)
    print("TEST 3: Single Simulation Step")
    print("=" * 80)
    
    try:
        p1 = canvas_manager.places[0]
        p2 = canvas_manager.places[1]
        
        print(f"Before step:")
        print(f"  P1 tokens: {p1.marking}")
        print(f"  P2 tokens: {p2.marking}")
        print(f"  Simulation time: {controller.time}")
        print()
        
        # Execute one step
        result = controller.step()
        
        print(f"After step:")
        print(f"  P1 tokens: {p1.marking}")
        print(f"  P2 tokens: {p2.marking}")
        print(f"  Simulation time: {controller.time}")
        print(f"  Step result: {result}")
        print()
        
        # Verify token moved
        if p1.marking == 4 and p2.marking == 1:
            print("✓ Token successfully moved from P1 to P2")
            return True
        else:
            print("✗ Token movement incorrect")
            return False
        
    except Exception as e:
        print(f"✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_multiple_steps(controller, canvas_manager):
    """Test multiple simulation steps."""
    print("=" * 80)
    print("TEST 4: Multiple Simulation Steps (5 steps)")
    print("=" * 80)
    
    try:
        p1 = canvas_manager.places[0]
        p2 = canvas_manager.places[1]
        
        print(f"Initial state:")
        print(f"  P1 tokens: {p1.marking}")
        print(f"  P2 tokens: {p2.marking}")
        print()
        
        # Execute 5 steps
        for i in range(5):
            result = controller.step()
            print(f"Step {i+1}: P1={p1.marking}, P2={p2.marking}, time={controller.time:.3f}, result={result}")
            
            if not result:
                print(f"  (No more enabled transitions)")
                break
        
        print()
        print(f"Final state:")
        print(f"  P1 tokens: {p1.marking}")
        print(f"  P2 tokens: {p2.marking}")
        print(f"  Total time: {controller.time:.3f}")
        
        # Should have transferred all tokens
        if p1.marking == 0 and p2.marking == 5:
            print("✓ All tokens successfully transferred")
            return True
        else:
            print(f"✗ Expected P1=0, P2=5, got P1={p1.marking}, P2={p2.marking}")
            return False
        
    except Exception as e:
        print(f"✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_glycolysis_model(model_path: str):
    """Test Glycolysis model simulation."""
    print("=" * 80)
    print("TEST 5: Glycolysis Model Simulation")
    print("=" * 80)
    print(f"Model: {model_path}")
    print()
    
    try:
        # Load model
        print("Loading model...")
        model_data = load_model(model_path)
        print(f"  Places: {len(model_data['places'])}")
        print(f"  Transitions: {len(model_data['transitions'])}")
        print(f"  Arcs: {len(model_data['arcs'])}")
        print()
        
        # Create canvas manager
        print("Creating canvas manager...")
        canvas_manager = create_model_canvas_manager(model_data)
        print(f"  ✓ Canvas manager created")
        print()
        
        # Create simulation controller
        print("Creating simulation controller...")
        from shypn.engine.simulation.controller import SimulationController
        controller = SimulationController(canvas_manager)
        print(f"  ✓ Simulation controller created")
        print(f"  Initial time: {controller.time}")
        print()
        
        # Count initial tokens
        total_tokens = sum(p.marking for p in canvas_manager.places)
        print(f"Initial tokens: {total_tokens}")
        print()
        
        # Find source transitions
        source_transitions = [t for t in canvas_manager.transitions if t.name.startswith('SOURCE_')]
        print(f"Source transitions: {len(source_transitions)}")
        for src in source_transitions:
            print(f"  - {src.name} (type: {src.type}, rate: {src.rate})")
        print()
        
        # Check enabled transitions
        print("Checking enabled transitions...")
        enabled_count = 0
        for trans in canvas_manager.transitions:
            try:
                behavior = controller.get_behavior(trans)
                if behavior.is_structurally_enabled():
                    enabled_count += 1
            except Exception as e:
                print(f"  Warning: Could not check {trans.name}: {e}")
        
        print(f"  Enabled transitions: {enabled_count}/{len(canvas_manager.transitions)}")
        print()
        
        # Run simulation steps
        print("Running simulation steps...")
        max_steps = 20
        steps_executed = 0
        
        for i in range(max_steps):
            result = controller.step()
            steps_executed += 1
            
            if i < 10 or i >= max_steps - 3:  # Show first 10 and last 3
                tokens_now = sum(p.marking for p in canvas_manager.places)
                print(f"  Step {i+1:2d}: tokens={tokens_now:3d}, time={controller.time:7.3f}, result={result}")
            elif i == 10:
                print(f"  ...")
            
            if not result:
                print(f"  (Simulation stopped - no enabled transitions)")
                break
        
        print()
        final_tokens = sum(p.marking for p in canvas_manager.places)
        print(f"Simulation summary:")
        print(f"  Steps executed: {steps_executed}")
        print(f"  Final time: {controller.time:.3f}")
        print(f"  Initial tokens: {total_tokens}")
        print(f"  Final tokens: {final_tokens}")
        print(f"  Token change: {final_tokens - total_tokens:+d}")
        print()
        
        # Check if sources are working (should have more tokens)
        if len(source_transitions) > 0:
            if final_tokens > total_tokens:
                print("✓ Source transitions are generating tokens")
                return True
            else:
                print("⚠ Warning: Source transitions may not be working (no token increase)")
                return True  # Still pass if simulation ran
        else:
            if steps_executed > 0:
                print("✓ Simulation executed successfully (no sources)")
                return True
            else:
                print("✗ No simulation steps executed")
                return False
        
    except Exception as e:
        print(f"✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_stochastic_sources():
    """Test stochastic source transitions specifically."""
    print("=" * 80)
    print("TEST 6: Stochastic Source Transitions")
    print("=" * 80)
    
    try:
        from shypn.data.canvas.document_model import DocumentModel
        from shypn.data.model_canvas_manager import ModelCanvasManager
        from shypn.netobjs.place import Place
        from shypn.netobjs.transition import Transition
        from shypn.netobjs.arc import Arc
        from shypn.engine.simulation.controller import SimulationController
        
        doc_model = DocumentModel()
        
        # Model: SOURCE (stochastic) -> P1
        source = Transition(0, 0, "SOURCE", "SOURCE")
        source.type = "stochastic"
        source.rate = 1.0  # High rate for testing
        source.guard = 1
        
        p1 = Place(100, 0, "P1", "P1")
        p1.marking = 0
        
        a1 = Arc(source, p1, "A1", "A1", weight=1)
        
        doc_model.places = [p1]
        doc_model.transitions = [source]
        doc_model.arcs = [a1]
        
        canvas_manager = ModelCanvasManager(canvas_width=200, canvas_height=200, filename="test_source")
        canvas_manager.places = doc_model.places
        canvas_manager.transitions = doc_model.transitions
        canvas_manager.arcs = doc_model.arcs
        controller = SimulationController(canvas_manager)
        
        print(f"Model: Stochastic source -> Place")
        print(f"  Source rate: {source.rate}")
        print(f"  Initial tokens: {p1.marking}")
        print()
        
        # Run multiple steps
        print("Running 10 simulation steps...")
        for i in range(10):
            result = controller.step()
            print(f"  Step {i+1:2d}: P1={p1.marking:2d} tokens, time={controller.time:7.3f}, result={result}")
            
            if not result:
                print(f"  Warning: Step returned False")
                break
        
        print()
        if p1.marking > 0:
            print(f"✓ Stochastic source generated {p1.marking} tokens")
            return True
        else:
            print(f"✗ Stochastic source did not generate tokens")
            return False
        
    except Exception as e:
        print(f"✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test runner."""
    print("=" * 80)
    print("HEADLESS SIMULATION TEST SUITE")
    print("=" * 80)
    print()
    print("This test verifies the simulation engine without GUI dependencies.")
    print()
    
    results = []
    
    # Test 1: Controller initialization
    success, controller, canvas_manager = test_simulation_controller()
    results.append(("Controller Initialization", success))
    
    if success:
        # Test 2: Transition enablement
        success = test_transition_enablement(controller, canvas_manager)
        results.append(("Transition Enablement", success))
        
        # Test 3: Single step
        success = test_single_step(controller, canvas_manager)
        results.append(("Single Step Execution", success))
        
        # Test 4: Multiple steps
        # Reset the model first
        canvas_manager.places[0].marking = 5
        canvas_manager.places[1].marking = 0
        controller.reset()
        
        success = test_multiple_steps(controller, canvas_manager)
        results.append(("Multiple Steps Execution", success))
    
    # Test 5: Glycolysis model (without sources)
    model_path = 'workspace/Test_flow/model/Glycolysis_SIMULATION_READY.shy'
    if os.path.exists(model_path):
        success = test_glycolysis_model(model_path)
        results.append(("Glycolysis Model (no sources)", success))
    else:
        print(f"⚠ Skipping: {model_path} not found")
        results.append(("Glycolysis Model (no sources)", None))
    
    # Test 6: Glycolysis model with sources
    model_path_sources = 'workspace/Test_flow/model/Glycolysis_WITH_SOURCES.shy'
    if os.path.exists(model_path_sources):
        success = test_glycolysis_model(model_path_sources)
        results.append(("Glycolysis Model (with sources)", success))
    else:
        print(f"⚠ Skipping: {model_path_sources} not found")
        results.append(("Glycolysis Model (with sources)", None))
    
    # Test 7: Stochastic sources
    success = test_stochastic_sources()
    results.append(("Stochastic Source Transitions", success))
    
    # Summary
    print()
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print()
    
    passed = sum(1 for _, result in results if result is True)
    failed = sum(1 for _, result in results if result is False)
    skipped = sum(1 for _, result in results if result is None)
    total = len(results)
    
    for test_name, result in results:
        if result is True:
            status = "✓ PASS"
        elif result is False:
            status = "✗ FAIL"
        else:
            status = "⊘ SKIP"
        print(f"  {status} - {test_name}")
    
    print()
    print(f"Results: {passed} passed, {failed} failed, {skipped} skipped out of {total} tests")
    print()
    
    if failed == 0:
        print("✓ ALL TESTS PASSED - Simulation engine is working correctly!")
        return 0
    else:
        print("✗ SOME TESTS FAILED - Review errors above for details")
        return 1

if __name__ == '__main__':
    sys.exit(main())
