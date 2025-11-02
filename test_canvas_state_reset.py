#!/usr/bin/env python3
"""
Test that canvas interaction states are properly reset when loading models.

This test verifies the fix for canvas state corruption issues where:
- Context menus stopped working after loading a model
- Panning/zooming became stuck
- Arc drawing mode was broken
- Double-click detection failed

The bug occurred because interaction states (_drag_state, _arc_state, etc.)
were only initialized once when the canvas was created, but never reset
when loading new documents into the same tab.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk

from shypn.helpers.model_canvas_loader import ModelCanvasLoader
from shypn.data.model_canvas_manager import ModelCanvasManager


def test_canvas_state_reset():
    """Test that canvas interaction states are reset when loading models."""
    
    print("=" * 80)
    print("TEST: Canvas State Reset on Model Load")
    print("=" * 80)
    
    # Create loader and a mock canvas
    loader = ModelCanvasLoader()
    
    # Create a drawing area (simulating a tab)
    drawing_area = Gtk.DrawingArea()
    
    # Create manager
    manager = ModelCanvasManager(drawing_area)
    
    # Register the manager with the loader (this is done when creating a tab)
    if not hasattr(loader, 'managers'):
        loader.managers = {}
    loader.managers[drawing_area] = manager
    
    print("\n1. Initial canvas setup:")
    print(f"   Manager created: {manager is not None}")
    print(f"   Manager registered with loader: {drawing_area in loader.managers}")
    
    # Simulate initial state setup (like what happens on tab creation)
    if not hasattr(loader, '_drag_state'):
        loader._drag_state = {}
    loader._drag_state[drawing_area] = {
        'active': True,  # Simulate stuck drag
        'button': 1,
        'start_x': 100,
        'start_y': 200,
        'is_panning': True,  # Simulate stuck panning
        'is_rect_selecting': False,
        'is_transforming': False
    }
    
    if not hasattr(loader, '_arc_state'):
        loader._arc_state = {}
    loader._arc_state[drawing_area] = {
        'source': "STUCK_OBJECT",  # Simulate stuck arc source
        'cursor_pos': (100, 200),
        'target_valid': None,
        'hovered_target': "STUCK_TARGET",
        'ignore_next_release': True  # Simulate stuck flag
    }
    
    if not hasattr(loader, '_click_state'):
        loader._click_state = {}
    loader._click_state[drawing_area] = {
        'last_click_time': 999.0,  # Simulate stuck timestamp
        'last_click_obj': "STUCK_OBJ",
        'double_click_threshold': 0.3,
        'pending_timeout': 12345,  # Simulate stuck timeout
        'pending_click_data': {"stuck": "data"}
    }
    
    if not hasattr(loader, '_lasso_state'):
        loader._lasso_state = {}
    loader._lasso_state[drawing_area] = {
        'active': True,  # Simulate stuck lasso
        'selector': None  # Would be a selector object
    }
    
    print("\n2. Simulated corrupted states:")
    print(f"   Drag state active: {loader._drag_state[drawing_area]['active']}")
    print(f"   Drag state is_panning: {loader._drag_state[drawing_area]['is_panning']}")
    print(f"   Arc state source: {loader._arc_state[drawing_area]['source']}")
    print(f"   Arc state ignore_next_release: {loader._arc_state[drawing_area]['ignore_next_release']}")
    print(f"   Click state pending_timeout: {loader._click_state[drawing_area]['pending_timeout']}")
    print(f"   Lasso state active: {loader._lasso_state[drawing_area]['active']}")
    
    # Call the reset method (this is what happens when loading a model)
    print("\n3. Calling _reset_manager_for_load()...")
    loader._reset_manager_for_load(manager, "test_model")
    
    # Verify states are reset
    print("\n4. Verifying states after reset:")
    
    success = True
    
    # Check drag state
    drag_state = loader._drag_state[drawing_area]
    if drag_state['active'] != False:
        print(f"   ❌ FAIL: Drag state active should be False, got {drag_state['active']}")
        success = False
    elif drag_state['is_panning'] != False:
        print(f"   ❌ FAIL: Drag state is_panning should be False, got {drag_state['is_panning']}")
        success = False
    else:
        print(f"   ✓ Drag state reset correctly")
    
    # Check arc state
    arc_state = loader._arc_state[drawing_area]
    if arc_state['source'] is not None:
        print(f"   ❌ FAIL: Arc state source should be None, got {arc_state['source']}")
        success = False
    elif arc_state['ignore_next_release'] != False:
        print(f"   ❌ FAIL: Arc state ignore_next_release should be False, got {arc_state['ignore_next_release']}")
        success = False
    else:
        print(f"   ✓ Arc state reset correctly")
    
    # Check click state
    click_state = loader._click_state[drawing_area]
    if click_state['pending_timeout'] is not None:
        print(f"   ❌ FAIL: Click state pending_timeout should be None, got {click_state['pending_timeout']}")
        success = False
    elif click_state['pending_click_data'] is not None:
        print(f"   ❌ FAIL: Click state pending_click_data should be None, got {click_state['pending_click_data']}")
        success = False
    else:
        print(f"   ✓ Click state reset correctly")
    
    # Check lasso state
    lasso_state = loader._lasso_state[drawing_area]
    if lasso_state['active'] != False:
        print(f"   ❌ FAIL: Lasso state active should be False, got {lasso_state['active']}")
        success = False
    else:
        print(f"   ✓ Lasso state reset correctly")
    
    # Check manager state
    if manager.zoom != 1.0:
        print(f"   ❌ FAIL: Manager zoom should be 1.0, got {manager.zoom}")
        success = False
    elif manager.pan_x != 0.0 or manager.pan_y != 0.0:
        print(f"   ❌ FAIL: Manager pan should be (0,0), got ({manager.pan_x}, {manager.pan_y})")
        success = False
    elif manager._suppress_callbacks:
        print(f"   ❌ FAIL: Manager callbacks should be enabled")
        success = False
    else:
        print(f"   ✓ Manager state reset correctly")
    
    if success:
        print(f"\n✅ TEST PASSED!")
        print(f"   All canvas interaction states correctly reset")
        print(f"   Canvas will work properly after model load")
        print(f"\nBenefits:")
        print(f"   - Context menus will work")
        print(f"   - Panning/zooming will work")
        print(f"   - Arc drawing will work")
        print(f"   - Double-click detection will work")
    else:
        print(f"\n❌ TEST FAILED!")
        print(f"   Some states were not properly reset")
    
    return success


if __name__ == '__main__':
    success = test_canvas_state_reset()
    sys.exit(0 if success else 1)
