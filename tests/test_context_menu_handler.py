#!/usr/bin/env python3
"""Test that context menu handler is properly initialized."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from shypn.helpers.right_panel_loader import create_right_panel

print("=" * 70)
print("Testing Context Menu Handler Initialization")
print("=" * 70)

# Create right panel without data_collector (mimics actual app initialization)
print("\n1. Creating right panel WITHOUT data_collector...")
right_panel_loader = create_right_panel()

# Check if context_menu_handler exists
if hasattr(right_panel_loader, 'context_menu_handler'):
    if right_panel_loader.context_menu_handler is not None:
        print("   ✅ context_menu_handler exists!")
        print(f"      Type: {type(right_panel_loader.context_menu_handler)}")
        print(f"      place_panel: {right_panel_loader.context_menu_handler.place_panel}")
        print(f"      transition_panel: {right_panel_loader.context_menu_handler.transition_panel}")
    else:
        print("   ❌ context_menu_handler is None")
        sys.exit(1)
else:
    print("   ❌ context_menu_handler attribute doesn't exist")
    sys.exit(1)

print("\n2. Simulating data_collector set (happens on tab switch)...")
# Create a mock data_collector
class MockDataCollector:
    def __init__(self):
        self.places = []
        self.transitions = []

mock_collector = MockDataCollector()
right_panel_loader.set_data_collector(mock_collector)

# Check if panels were created and handler was updated
if right_panel_loader.place_panel and right_panel_loader.transition_panel:
    print("   ✅ Panels created successfully")
    if right_panel_loader.context_menu_handler.place_panel is not None:
        print("   ✅ context_menu_handler updated with place_panel")
    else:
        print("   ❌ context_menu_handler.place_panel is still None")
        sys.exit(1)
    
    if right_panel_loader.context_menu_handler.transition_panel is not None:
        print("   ✅ context_menu_handler updated with transition_panel")
    else:
        print("   ❌ context_menu_handler.transition_panel is still None")
        sys.exit(1)
else:
    print("   ❌ Panels not created")
    sys.exit(1)

print("\n" + "=" * 70)
print("✅ ALL TESTS PASSED")
print("=" * 70)
print("\nContext menu handler is properly initialized and will be available")
print("for 'Add to Analysis' menu items in object context menus.")
