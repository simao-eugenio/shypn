#!/usr/bin/env python3
"""Test script to verify property dialogs work correctly."""

import sys
sys.path.insert(0, '/home/simao/projetos/shypn/src')

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from unittest.mock import Mock

def test_place_dialog():
    """Test place property dialog."""
    print("Testing Place Property Dialog...")
    try:
        from shypn.helpers.place_prop_dialog_loader import PlacePropDialogLoader
        
        # Create mock place
        place = Mock()
        place.id = 'p1'
        place.name = 'Place 1'
        place.tokens = 5
        place.radius = 20.0
        place.capacity = float('inf')
        place.border_width = 2.0
        place.border_color = (0.0, 0.0, 0.0)
        place.label = 'Test place'
        
        # Create mock model
        model = Mock()
        model.places = [place]
        model.transitions = []
        model.arcs = []
        
        # Create dialog
        loader = PlacePropDialogLoader(place, model=model)
        print("  ✓ Place dialog created successfully")
        
        # Clean up
        loader.destroy()
        print("  ✓ Place dialog destroyed successfully")
        return True
        
    except Exception as e:
        print(f"  ✗ Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_transition_dialog():
    """Test transition property dialog."""
    print("\nTesting Transition Property Dialog...")
    try:
        from shypn.helpers.transition_prop_dialog_loader import TransitionPropDialogLoader
        
        # Create mock transition
        transition = Mock()
        transition.id = 't1'
        transition.name = 'Transition 1'
        transition.width = 30.0
        transition.height = 10.0
        transition.border_width = 2.0
        transition.border_color = (0.0, 0.0, 0.0)
        transition.fill_color = (1.0, 1.0, 1.0)
        transition.label = 'Test transition'
        transition.priority = 1
        transition.guard = ''
        
        # Create mock model
        model = Mock()
        model.places = []
        model.transitions = [transition]
        model.arcs = []
        
        # Create dialog
        loader = TransitionPropDialogLoader(transition, model=model)
        print("  ✓ Transition dialog created successfully")
        
        # Clean up
        loader.destroy()
        print("  ✓ Transition dialog destroyed successfully")
        return True
        
    except Exception as e:
        print(f"  ✗ Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_arc_dialog():
    """Test arc property dialog."""
    print("\nTesting Arc Property Dialog...")
    try:
        from shypn.helpers.arc_prop_dialog_loader import ArcPropDialogLoader
        
        # Create mock place and transition
        place = Mock()
        place.id = 'p1'
        place.name = 'Place 1'
        
        transition = Mock()
        transition.id = 't1'
        transition.name = 'Transition 1'
        
        # Create mock arc
        arc = Mock()
        arc.id = 'a1'
        arc.source = place
        arc.target = transition
        arc.weight = 1
        arc.width = 2.0  # Add width attribute
        arc.source_id = 'p1'
        arc.target_id = 't1'
        arc.border_width = 2.0
        arc.color = (0.0, 0.0, 0.0)  # Use 'color' not 'border_color' for arcs
        arc.arc_type = 'normal'
        
        # Create mock model
        model = Mock()
        model.places = [place]
        model.transitions = [transition]
        model.arcs = [arc]
        
        # Create dialog
        loader = ArcPropDialogLoader(arc, model=model)
        print("  ✓ Arc dialog created successfully")
        
        # Clean up
        loader.destroy()
        print("  ✓ Arc dialog destroyed successfully")
        return True
        
    except Exception as e:
        print(f"  ✗ Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    print("=" * 60)
    print("Property Dialog Test Suite")
    print("=" * 60)
    
    results = []
    results.append(('Place Dialog', test_place_dialog()))
    results.append(('Transition Dialog', test_transition_dialog()))
    results.append(('Arc Dialog', test_arc_dialog()))
    
    print("\n" + "=" * 60)
    print("Test Results:")
    print("=" * 60)
    
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{name:30s} {status}")
    
    all_passed = all(r[1] for r in results)
    
    print("\n" + "=" * 60)
    if all_passed:
        print("ALL TESTS PASSED ✓")
        sys.exit(0)
    else:
        print("SOME TESTS FAILED ✗")
        sys.exit(1)
