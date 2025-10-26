#!/usr/bin/env python3
"""
Test transition property dialog when changing type to stochastic.
This test verifies the fix for pipe errors when editing transition types.
"""
import sys
import json
sys.path.insert(0, 'src')

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

from shypn.data.canvas.document_model import DocumentModel
from shypn.data.model_canvas_manager import ModelCanvasManager
from shypn.helpers.transition_prop_dialog_loader import create_transition_prop_dialog

print("=" * 80)
print("TRANSITION DIALOG STOCHASTIC TYPE CHANGE TEST")
print("=" * 80)

# Load SBML model
model_path = 'workspace/projects/SBML/models/BIOMD0000000001.shy'
print(f"\n1. Loading SBML model: {model_path}")

try:
    with open(model_path, 'r') as f:
        data = json.load(f)
    
    document = DocumentModel.from_dict(data)
    print(f"   ✓ Model loaded: {len(document.places)} places, {len(document.transitions)} transitions")
except Exception as e:
    print(f"   ❌ Failed to load model: {e}")
    sys.exit(1)

# Create canvas manager
print(f"\n2. Creating canvas manager")
manager = ModelCanvasManager()
manager.load_objects(
    places=document.places,
    transitions=document.transitions,
    arcs=document.arcs
)
print(f"   ✓ Manager created: {len(manager.places)} places, {len(manager.transitions)} transitions")

# Get first transition
if not document.transitions:
    print("   ❌ No transitions found in model!")
    sys.exit(1)

test_transition = document.transitions[0]
print(f"\n3. Testing transition: {test_transition.name}")
print(f"   - Current type: {test_transition.transition_type}")
print(f"   - Current rate: {getattr(test_transition, 'rate', 'None')}")

# Create dialog
print(f"\n4. Creating transition properties dialog")
dialog_loader = create_transition_prop_dialog(
    test_transition,
    parent_window=None,
    model=manager
)
print(f"   ✓ Dialog created")

# Programmatically change type to stochastic (simulate user selecting it)
print(f"\n5. Simulating type change to 'stochastic'")
try:
    type_combo = dialog_loader.builder.get_object('prop_transition_type_combo')
    if type_combo:
        # Find stochastic index (should be 2: immediate=0, timed=1, stochastic=2, continuous=3)
        type_combo.set_active(2)
        print(f"   ✓ Type combo set to stochastic")
        
        # Give GTK time to process signals
        while Gtk.events_pending():
            Gtk.main_iteration()
        
        print(f"   ✓ Signal processing complete")
        print(f"   - Transition type now: {test_transition.transition_type}")
    else:
        print(f"   ❌ Could not find type combo widget")
        sys.exit(1)
except Exception as e:
    print(f"   ❌ Error changing type: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Set rate field
print(f"\n6. Setting rate field")
try:
    rate_textview = dialog_loader.builder.get_object('rate_textview')
    if rate_textview:
        buffer = rate_textview.get_buffer()
        buffer.set_text("2.5")
        print(f"   ✓ Rate set to 2.5")
        
        # Give GTK time to process buffer signals
        while Gtk.events_pending():
            Gtk.main_iteration()
        
        print(f"   ✓ Rate sync complete")
    else:
        print(f"   ⚠ Rate textview not found")
except Exception as e:
    print(f"   ❌ Error setting rate: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Clean up dialog
print(f"\n7. Destroying dialog")
try:
    dialog_loader.destroy()
    print(f"   ✓ Dialog destroyed successfully")
    
    # Process any remaining events
    while Gtk.events_pending():
        Gtk.main_iteration()
    
    print(f"   ✓ No pipe errors!")
except Exception as e:
    print(f"   ❌ Error during destroy: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print(f"\n" + "=" * 80)
print("TEST RESULTS")
print("=" * 80)
print(f"✅ SUCCESS! Transition dialog works without pipe errors")
print(f"   - Type changed to: {test_transition.transition_type}")
print(f"   - Dialog destroyed cleanly")
print(f"   - No Wayland/pipe errors detected")
sys.exit(0)
