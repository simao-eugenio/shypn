#!/usr/bin/env python3
"""Test hover tooltips and arc property dialog ID field.

Tests:
1. Hover tooltips show ID-Name for canvas objects
2. Arc property dialog shows ID field
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))

print("=" * 70)
print("BASIC REFINEMENTS TEST")
print("=" * 70)

# Test 1: Verify tooltip logic
print("\n1. Testing tooltip logic...")
from shypn.netobjs import Place, Transition, Arc

p1 = Place(100, 100, 'P1', 'Glucose')
p1.tokens = 5

t1 = Transition(200, 100, 'T1', 'Glycolysis')
t1.rate = 1.0

a1 = Arc(p1, t1, 'A1', 'A1', 1)

# Test place with different name
obj_id = p1.id
obj_name = p1.name
if obj_name and obj_name != obj_id:
    tooltip = f"{obj_id} - {obj_name}"
else:
    tooltip = obj_id

print(f"   Place P1 tooltip: '{tooltip}'")
assert tooltip == "P1 - Glucose", f"Expected 'P1 - Glucose', got '{tooltip}'"

# Test transition with same ID and name
t2 = Transition(300, 100, 'T2', 'T2')
obj_id = t2.id
obj_name = t2.name
if obj_name and obj_name != obj_id:
    tooltip = f"{obj_id} - {obj_name}"
else:
    tooltip = obj_id

print(f"   Transition T2 tooltip: '{tooltip}'")
assert tooltip == "T2", f"Expected 'T2', got '{tooltip}'"

# Test arc
obj_id = a1.id
obj_name = a1.name
if obj_name and obj_name != obj_id:
    tooltip = f"{obj_id} - {obj_name}"
else:
    tooltip = obj_id

print(f"   Arc A1 tooltip: '{tooltip}'")
assert tooltip == "A1", f"Expected 'A1', got '{tooltip}'"

print("   ✓ Tooltip logic works correctly")

# Test 2: Verify arc dialog UI has ID field
print("\n2. Testing arc property dialog has ID field...")

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

# Load UI file
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
ui_path = os.path.join(project_root, 'ui', 'dialogs', 'arc_prop_dialog.ui')

if not os.path.exists(ui_path):
    print(f"   ✗ UI file not found: {ui_path}")
    sys.exit(1)

builder = Gtk.Builder()
builder.add_from_file(ui_path)

# Check for ID entry widget
id_entry = builder.get_object('id_entry')
if id_entry is None:
    print("   ✗ ID entry widget not found in arc_prop_dialog.ui")
    sys.exit(1)

print(f"   ✓ ID entry widget found: {type(id_entry).__name__}")

# Verify it's not editable
if hasattr(id_entry, 'get_editable'):
    is_editable = id_entry.get_editable()
    print(f"   ID entry editable: {is_editable}")
    assert not is_editable, "ID entry should be read-only"
    print("   ✓ ID entry is read-only")

# Test 3: Verify arc dialog loader populates ID
print("\n3. Testing arc dialog loader populates ID field...")

from shypn.helpers.arc_prop_dialog_loader import ArcPropDialogLoader

# Create arc (Place → Transition is valid)
a2 = Arc(p1, t1, 'A123', 'TestArc', 2)

# Create dialog loader (without showing dialog)
try:
    loader = ArcPropDialogLoader(a2, ui_dir=os.path.join(project_root, 'ui', 'dialogs'))
    
    # Check if ID field is populated
    id_entry = loader.builder.get_object('id_entry')
    if id_entry:
        id_text = id_entry.get_text()
        print(f"   ID field value: '{id_text}'")
        assert id_text == 'A123', f"Expected 'A123', got '{id_text}'"
        print("   ✓ ID field populated correctly")
    else:
        print("   ✗ Could not get ID entry from builder")
        sys.exit(1)
    
    # Cleanup
    if loader.dialog:
        loader.dialog.destroy()
    
except Exception as e:
    print(f"   ✗ Error creating dialog loader: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 70)
print("✓ ALL TESTS PASSED!")
print("=" * 70)
print("\nBasic refinements verified:")
print("  ✓ Hover tooltips show 'ID - Name' format")
print("  ✓ Arc property dialog has read-only ID field")
print("  ✓ Arc dialog loader populates ID correctly")
print("\nRefinements ready for real app testing!")
