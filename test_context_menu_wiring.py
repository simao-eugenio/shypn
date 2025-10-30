#!/usr/bin/env python3
"""Test context menu handler wiring after refactoring."""
import sys
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

# Add src to path
sys.path.insert(0, '/home/simao/projetos/shypn/src')

from shypn.helpers.right_panel_loader import RightPanelLoader

def test_context_menu_wiring():
    """Test that context menu handler is properly wired."""
    
    print("\n" + "="*70)
    print("TEST: Context Menu Handler Wiring After Refactoring")
    print("="*70 + "\n")
    
    # Step 1: Create right panel without model/data_collector
    print("Step 1: Creating right panel (no model, no data_collector)...")
    right_panel = RightPanelLoader()
    right_panel.load()
    
    # Check if context menu handler exists
    if right_panel.context_menu_handler:
        print("  ✓ context_menu_handler exists:", right_panel.context_menu_handler)
        print(f"    - place_panel: {right_panel.context_menu_handler.place_panel}")
        print(f"    - transition_panel: {right_panel.context_menu_handler.transition_panel}")
        print(f"    - model: {right_panel.context_menu_handler.model}")
        print(f"    - locality_detector: {right_panel.context_menu_handler.locality_detector}")
    else:
        print("  ✗ context_menu_handler is None!")
        return False
    
    print()
    
    # Step 2: Check panel references
    print("Step 2: Checking panel references...")
    if right_panel.place_panel:
        print(f"  ✓ place_panel exists: {right_panel.place_panel}")
    else:
        print("  ✗ place_panel is None!")
        return False
    
    if right_panel.transition_panel:
        print(f"  ✓ transition_panel exists: {right_panel.transition_panel}")
    else:
        print("  ✗ transition_panel is None!")
        return False
    
    if right_panel.diagnostics_panel:
        print(f"  ✓ diagnostics_panel exists: {right_panel.diagnostics_panel}")
    else:
        print("  ✗ diagnostics_panel is None!")
        return False
    
    print()
    
    # Step 3: Verify handler has correct panel references
    print("Step 3: Verifying handler has correct panel references...")
    if right_panel.context_menu_handler.place_panel is right_panel.place_panel:
        print("  ✓ Handler's place_panel matches")
    else:
        print("  ✗ Handler's place_panel MISMATCH!")
        return False
    
    if right_panel.context_menu_handler.transition_panel is right_panel.transition_panel:
        print("  ✓ Handler's transition_panel matches")
    else:
        print("  ✗ Handler's transition_panel MISMATCH!")
        return False
    
    print()
    
    # Step 4: Simulate setting model (like in main app)
    print("Step 4: Simulating set_model() call...")
    
    class MockModel:
        def __init__(self):
            self.places = {}
            self.transitions = {}
            self._observers = []
        
        def mark_needs_redraw(self):
            pass
        
        def register_observer(self, callback):
            """Register observer for model changes."""
            self._observers.append(callback)
        
        def unregister_observer(self, callback):
            """Unregister observer."""
            if callback in self._observers:
                self._observers.remove(callback)
    
    mock_model = MockModel()
    right_panel.set_model(mock_model)
    
    if right_panel.context_menu_handler.model is mock_model:
        print(f"  ✓ Handler's model updated: {right_panel.context_menu_handler.model}")
    else:
        print("  ✗ Handler's model NOT updated!")
        return False
    
    if right_panel.context_menu_handler.locality_detector:
        print(f"  ✓ Locality detector created: {right_panel.context_menu_handler.locality_detector}")
    else:
        print("  ✗ Locality detector NOT created!")
        return False
    
    print()
    
    # Step 5: Test add_analysis_menu_items method
    print("Step 5: Testing add_analysis_menu_items method...")
    
    # Import actual Transition class
    from shypn.netobjs import Transition
    
    menu = Gtk.Menu()
    mock_transition = Transition(100, 100, "T1", "T1", label="Test Transition")  # x, y, id, name
    
    try:
        right_panel.context_menu_handler.add_analysis_menu_items(menu, mock_transition)
        menu_items = menu.get_children()
        
        if len(menu_items) > 0:
            print(f"  ✓ Menu items added: {len(menu_items)} items")
            for item in menu_items:
                if isinstance(item, Gtk.SeparatorMenuItem):
                    print(f"    - Separator")
                elif isinstance(item, Gtk.MenuItem):
                    print(f"    - MenuItem: {item.get_label()}")
        else:
            print("  ✗ No menu items added!")
            return False
    except Exception as e:
        print(f"  ✗ Error adding menu items: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print()
    print("="*70)
    print("✓ ALL TESTS PASSED - Context menu handler is properly wired!")
    print("="*70)
    
    return True

if __name__ == '__main__':
    success = test_context_menu_wiring()
    sys.exit(0 if success else 1)
