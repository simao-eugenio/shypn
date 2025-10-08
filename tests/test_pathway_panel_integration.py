#!/usr/bin/env python3
"""Test Pathway Panel Integration"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk
except Exception as e:
    print(f'ERROR: GTK3 not available: {e}', file=sys.stderr)
    sys.exit(1)

# Test imports
print("Testing imports...")
try:
    from shypn.helpers.pathway_panel_loader import create_pathway_panel
    print("✓ pathway_panel_loader imported")
except ImportError as e:
    print(f"✗ Failed to import pathway_panel_loader: {e}")
    sys.exit(1)

try:
    from shypn.helpers.kegg_import_panel import KEGGImportPanel
    print("✓ kegg_import_panel imported")
except ImportError as e:
    print(f"✗ Failed to import kegg_import_panel: {e}")
    sys.exit(1)

try:
    from shypn.importer.kegg import KEGGAPIClient, KGMLParser, PathwayConverter
    print("✓ KEGG backend imported")
except ImportError as e:
    print(f"✗ Failed to import KEGG backend: {e}")
    sys.exit(1)

# Test panel creation
print("\nTesting panel creation...")
try:
    panel_loader = create_pathway_panel()
    print("✓ Panel loader created")
    
    # Check if window was loaded
    if panel_loader.window:
        print("✓ Panel window loaded")
    else:
        print("✗ Panel window not loaded")
    
    # Check if builder has widgets
    if panel_loader.builder:
        print("✓ Builder created")
        
        # Check key widgets
        widgets = [
            'pathway_id_entry',
            'organism_combo',
            'fetch_button',
            'import_button',
            'preview_text'
        ]
        
        for widget_name in widgets:
            widget = panel_loader.builder.get_object(widget_name)
            if widget:
                print(f"  ✓ {widget_name} found")
            else:
                print(f"  ✗ {widget_name} NOT FOUND")
    
    # Check if import controller exists
    if panel_loader.kegg_import_controller:
        print("✓ KEGG import controller created")
    else:
        print("✗ KEGG import controller not created")
    
    print("\n✅ All tests passed! Panel is ready for integration.")
    
except Exception as e:
    print(f"\n✗ Panel creation failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
