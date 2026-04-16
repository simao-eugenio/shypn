#!/usr/bin/env python3
"""
Quick Test: Fresh Glycolysis Import
====================================

Tests the freshly imported Glycolysis model to verify that our serialization
fixes (object_type vs type, transition_type property) work correctly.

This should NOT have the corrupted 'transition_type=transition' data that the
old saved models had.
"""

import os
import sys
from pathlib import Path

# Add src to path (go up 3 levels: headless -> validate -> tests -> project_root)
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / 'src'))

def test_fresh_glycolysis():
    """Test freshly imported Glycolysis model."""
    
    print("=" * 80)
    print("FRESH GLYCOLYSIS MODEL TEST")
    print("=" * 80)
    print()
    
    model_path = 'workspace/projects/Flow_Test/models/Glycolysis_fresh_WITH_SOURCES.shy'
    
    if not os.path.exists(model_path):
        print(f"✗ Model not found: {model_path}")
        return False
    
    print(f"Model: {model_path}")
    print()
    
    try:
        # Load model
        print("Loading model...")
        from shypn.data.canvas.document_model import DocumentModel
        document = DocumentModel.load_from_file(model_path)
        
        print(f"  ✓ Loaded successfully")
        print(f"  Places: {len(document.places)}")
        print(f"  Transitions: {len(document.transitions)}")
        print(f"  Arcs: {len(document.arcs)}")
        print()
        
        # Check transition types
        print("Checking transition types...")
        transition_types = {}
        corrupted = []
        
        for t in document.transitions:
            ttype = getattr(t, 'transition_type', 'MISSING')
            if ttype == 'MISSING':
                corrupted.append(f"{t.name}: no transition_type attribute")
            elif ttype == 'transition':
                corrupted.append(f"{t.name}: corrupted value 'transition'")
            else:
                transition_types[ttype] = transition_types.get(ttype, 0) + 1
        
        if corrupted:
            print(f"  ✗ Found {len(corrupted)} corrupted transitions:")
            for msg in corrupted[:5]:  # Show first 5
                print(f"      {msg}")
            if len(corrupted) > 5:
                print(f"      ... and {len(corrupted) - 5} more")
            print()
            return False
        else:
            print(f"  ✓ All transitions have valid transition_type!")
            for ttype, count in sorted(transition_types.items()):
                print(f"      {ttype}: {count}")
            print()
        
        # Create canvas manager
        print("Creating canvas manager...")
        from shypn.data.model_canvas_manager import ModelCanvasManager
        from shypn.core.controllers.document_controller import DocumentController
        
        doc_controller = DocumentController()
        canvas_manager = ModelCanvasManager(doc_controller)
        
        # Load objects into canvas manager (this triggers observer registration)
        canvas_manager.load_objects(document.places, document.transitions, document.arcs)
        
        print(f"  ✓ Canvas manager created")
        print(f"  Places: {len(canvas_manager.places)}")
        print(f"  Transitions: {len(canvas_manager.transitions)}")
        print(f"  Arcs: {len(canvas_manager.arcs)}")
        print()
        
        # Create simulation controller
        print("Creating simulation controller...")
        from shypn.engine.simulation.controller import SimulationController
        controller = SimulationController(canvas_manager)
        print(f"  ✓ Simulation controller created")
        print(f"  Initial time: {controller.time}")
        print()
        
        # Check if behaviors can be created
        print("Checking transition behaviors...")
        behavior_types = {}
        behavior_errors = []
        
        for t in canvas_manager.transitions:
            try:
                behavior = controller._get_behavior(t)
                btype = type(behavior).__name__
                behavior_types[btype] = behavior_types.get(btype, 0) + 1
            except Exception as e:
                behavior_errors.append(f"{t.name}: {e}")
        
        if behavior_errors:
            print(f"  ✗ Found {len(behavior_errors)} behavior errors:")
            for msg in behavior_errors[:5]:
                print(f"      {msg}")
            if len(behavior_errors) > 5:
                print(f"      ... and {len(behavior_errors) - 5} more")
            print()
            return False
        else:
            print(f"  ✓ All transitions have valid behaviors!")
            for btype, count in sorted(behavior_types.items()):
                print(f"      {btype}: {count}")
            print()
        
        # Count source transitions
        source_transitions = [t for t in canvas_manager.transitions 
                            if t.is_source or (hasattr(t, 'name') and 'SOURCE_' in str(t.name))]
        print(f"Source transitions: {len(source_transitions)}")
        for src in source_transitions[:5]:  # Show first 5
            print(f"  - {src.name} (type: {src.transition_type}, rate: {src.rate})")
        print()
        
        # Try simulation steps
        print("Testing simulation (20 steps)...")
        initial_tokens = sum(p.tokens for p in canvas_manager.places)
        print(f"  Initial tokens: {initial_tokens}")
        
        for step in range(20):
            result = controller.step()
            if step < 3 or step >= 17:  # Show first 3 and last 3
                tokens_now = sum(p.tokens for p in canvas_manager.places)
                print(f"  Step {step+1:2d}: tokens={tokens_now:7.2f}, time={controller.time:7.3f}, result={result}")
            elif step == 3:
                print("  ...")
            
            if not result:
                print(f"  (Stopped - no enabled transitions)")
                break
        
        final_tokens = sum(p.tokens for p in canvas_manager.places)
        print(f"  Final tokens: {final_tokens:.2f}")
        token_change = final_tokens - initial_tokens
        print(f"  Token change: {token_change:+.2f}")
        print()
        
        if token_change > 0:
            print("  ✓ Tokens generated - sources are working!")
        elif token_change == 0:
            print("  ⚠ No token change (sources might not be firing)")
        else:
            print("  ⚠ Tokens decreased (unexpected for source transitions)")
        print()
        
        print("=" * 80)
        print("✓ FRESH GLYCOLYSIS MODEL TEST PASSED!")
        print("=" * 80)
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = test_fresh_glycolysis()
    sys.exit(0 if success else 1)
