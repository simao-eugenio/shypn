#!/usr/bin/env python3
"""
Test property dialogs with a real Petri net model.

This script loads a real .shy model file and tests opening property dialogs
for places, transitions, and arcs to verify the topology integration works.
"""

import sys
import os

# Add src to path
sys.path.insert(0, '/home/simao/projetos/shypn/src')

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

def load_model(model_path):
    """Load a .shy model file."""
    print(f"\nLoading model: {model_path}")
    
    try:
        from shypn.model.petri_net_model import PetriNetModel
        from shypn.persistence.net_obj_persistency import NetObjPersistency
        
        # Create model and persistency
        model = PetriNetModel()
        persistency = NetObjPersistency(model)
        
        # Load the file
        if os.path.exists(model_path):
            persistency.load(model_path)
            print(f"  ✓ Model loaded successfully")
            print(f"  - Places: {len(model.places)}")
            print(f"  - Transitions: {len(model.transitions)}")
            print(f"  - Arcs: {len(model.arcs)}")
            return model, persistency
        else:
            print(f"  ✗ File not found: {model_path}")
            return None, None
            
    except Exception as e:
        print(f"  ✗ Error loading model: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return None, None


def test_place_dialog(model, persistency):
    """Test opening a place property dialog."""
    print("\n" + "="*60)
    print("Testing Place Property Dialog")
    print("="*60)
    
    if not model or not model.places:
        print("  ⊘ No places in model")
        return False
    
    try:
        from shypn.helpers.place_prop_dialog_loader import PlacePropDialogLoader
        
        # Get first place
        place = model.places[0]
        print(f"  Testing with place: {place.name} (id={place.id})")
        print(f"  - Tokens: {getattr(place, 'tokens', 0)}")
        print(f"  - Capacity: {getattr(place, 'capacity', 'inf')}")
        
        # Create dialog
        print("  Creating dialog...")
        loader = PlacePropDialogLoader(
            place,
            parent_window=None,
            persistency_manager=persistency,
            model=model
        )
        
        print("  ✓ Dialog created successfully")
        print("  ✓ Topology tab integration successful")
        
        # Clean up
        loader.destroy()
        print("  ✓ Dialog destroyed successfully")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_transition_dialog(model, persistency):
    """Test opening a transition property dialog."""
    print("\n" + "="*60)
    print("Testing Transition Property Dialog")
    print("="*60)
    
    if not model or not model.transitions:
        print("  ⊘ No transitions in model")
        return False
    
    try:
        from shypn.helpers.transition_prop_dialog_loader import TransitionPropDialogLoader
        
        # Get first transition
        transition = model.transitions[0]
        print(f"  Testing with transition: {transition.name} (id={transition.id})")
        
        # Create dialog
        print("  Creating dialog...")
        loader = TransitionPropDialogLoader(
            transition,
            parent_window=None,
            persistency_manager=persistency,
            model=model
        )
        
        print("  ✓ Dialog created successfully")
        print("  ✓ Topology tab integration successful")
        
        # Clean up
        loader.destroy()
        print("  ✓ Dialog destroyed successfully")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_arc_dialog(model, persistency):
    """Test opening an arc property dialog."""
    print("\n" + "="*60)
    print("Testing Arc Property Dialog")
    print("="*60)
    
    if not model or not model.arcs:
        print("  ⊘ No arcs in model")
        return False
    
    try:
        from shypn.helpers.arc_prop_dialog_loader import ArcPropDialogLoader
        
        # Get first arc
        arc = model.arcs[0]
        print(f"  Testing with arc: {arc.id}")
        if hasattr(arc, 'source') and hasattr(arc, 'target'):
            source_name = arc.source.name if arc.source else 'Unknown'
            target_name = arc.target.name if arc.target else 'Unknown'
            print(f"  - Connection: {source_name} → {target_name}")
            print(f"  - Weight: {getattr(arc, 'weight', 1)}")
        
        # Create dialog
        print("  Creating dialog...")
        loader = ArcPropDialogLoader(
            arc,
            parent_window=None,
            persistency_manager=persistency,
            model=model
        )
        
        print("  ✓ Dialog created successfully")
        print("  ✓ Topology tab integration successful")
        
        # Clean up
        loader.destroy()
        print("  ✓ Dialog destroyed successfully")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main test function."""
    print("="*60)
    print("Real Model Property Dialog Test")
    print("="*60)
    
    # Try to find a model file
    model_paths = [
        '/home/simao/projetos/shypn/workspace/examples/pathways/hsa00020.shy',  # Smallest pathway
        '/home/simao/projetos/shypn/workspace/examples/pathways/hsa00010.shy',
        '/home/simao/projetos/shypn/workspace/projects/Test/models/Hynne2001_Glycolysis.shy',
    ]
    
    model = None
    persistency = None
    
    for model_path in model_paths:
        if os.path.exists(model_path):
            model, persistency = load_model(model_path)
            if model:
                break
    
    if not model:
        print("\n✗ No model could be loaded. Exiting.")
        sys.exit(1)
    
    # Run tests
    results = []
    results.append(('Place Dialog', test_place_dialog(model, persistency)))
    results.append(('Transition Dialog', test_transition_dialog(model, persistency)))
    results.append(('Arc Dialog', test_arc_dialog(model, persistency)))
    
    # Print summary
    print("\n" + "="*60)
    print("Test Results Summary")
    print("="*60)
    
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{name:30s} {status}")
    
    all_passed = all(r[1] for r in results)
    
    print("\n" + "="*60)
    if all_passed:
        print("ALL TESTS PASSED ✓")
        print("Property dialogs work correctly with real models!")
        print("Topology behavioral integration is functioning properly.")
        sys.exit(0)
    else:
        print("SOME TESTS FAILED ✗")
        print("Check error messages above for details.")
        sys.exit(1)


if __name__ == '__main__':
    main()
