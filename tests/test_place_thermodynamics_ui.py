#!/usr/bin/env python3
"""
Test Place Properties Dialog - Thermodynamics Tab

Verifies that the thermodynamics tab correctly displays and saves
thermodynamic properties for places.
"""
import sys
import os

# Add src to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(current_dir, 'src'))

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from shypn.netobjs.place import Place
from shypn.helpers.place_prop_dialog_loader import PlacePropDialogLoader


def test_thermodynamics_tab_display():
    """Test that thermodynamics tab displays existing properties."""
    print("Testing thermodynamics tab display...")
    
    # Create a place with thermodynamic properties
    place = Place(id="P1", x=100, y=100, name="ATP")
    place.properties = {
        'compound_id': 'C00002',
        'compound_name': 'Adenosine 5\'-triphosphate',
        'delta_g_formation': -2292.2,
        'delta_g_uncertainty': 5.0,
        'thermodynamic_source': 'eQuilibrator',
        'thermodynamic_conditions': {
            'pH': 7.0,
            'temperature': 298.15,
            'ionic_strength': 0.1
        }
    }
    
    # Create dialog (don't run it, just verify it loads)
    try:
        dialog_loader = PlacePropDialogLoader(place)
        
        # Verify thermodynamic widgets were populated
        compound_id_entry = dialog_loader.builder.get_object('compound_id_entry')
        assert compound_id_entry is not None, "compound_id_entry not found"
        assert compound_id_entry.get_text() == 'C00002', f"Expected 'C00002', got '{compound_id_entry.get_text()}'"
        
        compound_name_entry = dialog_loader.builder.get_object('compound_name_entry')
        assert compound_name_entry is not None, "compound_name_entry not found"
        assert compound_name_entry.get_text() == 'Adenosine 5\'-triphosphate', f"Compound name mismatch"
        
        delta_g_entry = dialog_loader.builder.get_object('delta_g_formation_entry')
        assert delta_g_entry is not None, "delta_g_formation_entry not found"
        assert delta_g_entry.get_text() == '-2292.2', f"Expected '-2292.2', got '{delta_g_entry.get_text()}'"
        
        uncertainty_entry = dialog_loader.builder.get_object('delta_g_uncertainty_entry')
        assert uncertainty_entry is not None, "delta_g_uncertainty_entry not found"
        assert uncertainty_entry.get_text() == '5.0', f"Expected '5.0', got '{uncertainty_entry.get_text()}'"
        
        source_entry = dialog_loader.builder.get_object('thermodynamic_source_entry')
        assert source_entry is not None, "thermodynamic_source_entry not found"
        assert source_entry.get_text() == 'eQuilibrator', f"Expected 'eQuilibrator', got '{source_entry.get_text()}'"
        
        conditions_display = dialog_loader.builder.get_object('conditions_display')
        assert conditions_display is not None, "conditions_display not found"
        conditions_text = conditions_display.get_text()
        assert 'pH: 7.0' in conditions_text, f"pH not found in conditions: '{conditions_text}'"
        assert 'Temperature: 298.15' in conditions_text, f"Temperature not found in conditions"
        assert 'Ionic Strength: 0.1' in conditions_text, f"Ionic strength not found in conditions"
        
        print("✓ Thermodynamics tab display test passed!")
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_thermodynamics_tab_save():
    """Test that thermodynamics tab saves edited properties."""
    print("\nTesting thermodynamics tab save...")
    
    # Create a place with minimal properties
    place = Place(id="P2", x=100, y=100, name="Glucose")
    place.properties = {
        'compound_id': 'C00031',
        'delta_g_formation': -915.9
    }
    
    try:
        dialog_loader = PlacePropDialogLoader(place)
        
        # Simulate user editing values
        compound_id_entry = dialog_loader.builder.get_object('compound_id_entry')
        compound_id_entry.set_text('C00031')
        
        delta_g_entry = dialog_loader.builder.get_object('delta_g_formation_entry')
        delta_g_entry.set_text('-920.5')  # Modified value
        
        uncertainty_entry = dialog_loader.builder.get_object('delta_g_uncertainty_entry')
        uncertainty_entry.set_text('3.5')  # New value
        
        # Save properties
        dialog_loader._save_thermodynamics()
        
        # Verify properties were saved
        assert place.properties['compound_id'] == 'C00031', "Compound ID not saved"
        assert place.properties['delta_g_formation'] == -920.5, f"Expected -920.5, got {place.properties['delta_g_formation']}"
        assert place.properties['delta_g_uncertainty'] == 3.5, f"Expected 3.5, got {place.properties['delta_g_uncertainty']}"
        
        print("✓ Thermodynamics tab save test passed!")
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_empty_place_thermodynamics():
    """Test that empty place doesn't crash when showing thermodynamics tab."""
    print("\nTesting empty place thermodynamics...")
    
    # Create a place without thermodynamic properties
    place = Place(id="P3", x=100, y=100, name="Unknown")
    
    try:
        dialog_loader = PlacePropDialogLoader(place)
        
        # Verify widgets exist but are empty
        compound_id_entry = dialog_loader.builder.get_object('compound_id_entry')
        assert compound_id_entry is not None, "compound_id_entry not found"
        assert compound_id_entry.get_text() == '', "Expected empty compound_id"
        
        delta_g_entry = dialog_loader.builder.get_object('delta_g_formation_entry')
        assert delta_g_entry is not None, "delta_g_formation_entry not found"
        assert delta_g_entry.get_text() == '', "Expected empty delta_g"
        
        print("✓ Empty place thermodynamics test passed!")
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    print("=" * 60)
    print("Place Properties Dialog - Thermodynamics Tab Tests")
    print("=" * 60)
    
    results = []
    results.append(test_thermodynamics_tab_display())
    results.append(test_thermodynamics_tab_save())
    results.append(test_empty_place_thermodynamics())
    
    print("\n" + "=" * 60)
    if all(results):
        print("✓ ALL TESTS PASSED!")
        print("=" * 60)
        sys.exit(0)
    else:
        print("✗ SOME TESTS FAILED!")
        print("=" * 60)
        sys.exit(1)
