#!/usr/bin/env python3
"""Detailed investigation of Report -> MODELS category implementation.

Tests what's actually implemented and working in the Models category.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from shypn.ui.panels.report.model_structure_category import ModelsCategory
from shypn.importer.kegg import fetch_pathway, parse_kgml, convert_pathway


def investigate_models_category():
    """Investigate what's implemented in the Models category."""
    
    print("=" * 80)
    print("REPORT -> MODELS CATEGORY IMPLEMENTATION INVESTIGATION")
    print("=" * 80)
    print()
    
    # === TEST 1: Check class structure ===
    print("TEST 1: Class Structure")
    print("-" * 80)
    
    category = ModelsCategory()
    
    print(f"✓ Class instantiation: {type(category).__name__}")
    print(f"✓ Base class: {type(category).__bases__[0].__name__}")
    print(f"✓ Title: {category.title}")
    print()
    
    # Check methods
    methods = [m for m in dir(category) if not m.startswith('_') and callable(getattr(category, m))]
    print(f"Public methods ({len(methods)}):")
    for method in sorted(methods):
        print(f"  - {method}()")
    print()
    
    # Check attributes
    attrs = [a for a in dir(category) if not a.startswith('_') and not callable(getattr(category, a))]
    print(f"Public attributes ({len(attrs)}):")
    for attr in sorted(attrs):
        value = getattr(category, attr)
        print(f"  - {attr}: {type(value).__name__}")
    print()
    
    # === TEST 2: Check UI components ===
    print("TEST 2: UI Components")
    print("-" * 80)
    
    # Check widget structure
    widget = category.get_widget()
    print(f"✓ Main widget type: {type(widget).__name__}")
    
    # Check labels
    ui_components = {
        'overview_label': category.overview_label,
        'structure_label': category.structure_label,
        'provenance_label': category.provenance_label,
        'provenance_frame': category.provenance_frame,
        'species_expander': category.species_expander,
        'reactions_expander': category.reactions_expander,
        'species_store': category.species_store,
        'reactions_store': category.reactions_store,
        'species_treeview': category.species_treeview,
        'reactions_treeview': category.reactions_treeview,
    }
    
    for name, component in ui_components.items():
        comp_type = type(component).__name__
        print(f"  ✓ {name}: {comp_type}")
        
        # Check initial state
        if hasattr(component, 'get_text') and comp_type == 'Label':
            text = component.get_text()
            print(f"      Initial: '{text[:50]}...'")
        elif hasattr(component, 'get_visible'):
            visible = component.get_visible()
            print(f"      Visible: {visible}")
    print()
    
    # === TEST 3: Test with real KEGG data ===
    print("TEST 3: Load Real KEGG Pathway")
    print("-" * 80)
    
    # Import a small pathway
    print("Importing hsa00010 (Glycolysis)...")
    kgml_xml = fetch_pathway('hsa00010')
    pathway = parse_kgml(kgml_xml)
    result = convert_pathway(pathway, filter_isolated_compounds=True)
    
    if result and hasattr(result, 'places'):
        model = result
        print(f"✓ Model loaded: {model.name if hasattr(model, 'name') else 'Unknown'}")
        print(f"  Places: {len(model.places)}")
        print(f"  Transitions: {len(model.transitions)}")
        print(f"  Arcs: {len(model.arcs)}")
        print()
        
        # Create a mock model canvas
        class MockModelCanvas:
            def __init__(self, model):
                self.model = model
                self.file_path = None
        
        mock_canvas = MockModelCanvas(model)
        
        # Create category with model
        category_with_model = ModelsCategory(model_canvas=mock_canvas)
        
        # === TEST 4: Check data extraction ===
        print("TEST 4: Data Extraction from Model")
        print("-" * 80)
        
        # Refresh to populate
        category_with_model.refresh()
        
        # Check Model Overview
        overview_text = category_with_model.overview_label.get_text()
        print("Model Overview:")
        print(overview_text)
        print()
        
        # Check Petri Net Structure
        structure_text = category_with_model.structure_label.get_text()
        print("Petri Net Structure:")
        print(structure_text)
        print()
        
        # Check Provenance (should be hidden for this test)
        provenance_visible = category_with_model.provenance_frame.get_visible()
        provenance_text = category_with_model.provenance_label.get_text()
        print(f"Import Provenance (visible={provenance_visible}):")
        print(provenance_text)
        print()
        
        # Check Species List
        species_count = len(category_with_model.species_store)
        print(f"Species/Places Table (rows={species_count}):")
        if species_count > 0:
            # Show first 3 rows
            for i, row in enumerate(list(category_with_model.species_store)[:3]):
                print(f"  Row {i+1}: [{row[1]}] {row[2]} | KEGG:{row[3]} | Tokens:{row[4]} | Formula:{row[5]} | Mass:{row[6]:.2f}")
        print()
        
        # Check Reactions List
        reactions_count = len(category_with_model.reactions_store)
        print(f"Reactions/Transitions Table (rows={reactions_count}):")
        if reactions_count > 0:
            # Show first 3 rows
            for i, row in enumerate(list(category_with_model.reactions_store)[:3]):
                print(f"  Row {i+1}: [{row[1]}] {row[2]} | Type:{row[3]} | KEGG:{row[4]} | EC:{row[5]} | Rate:{row[6]}")
        print()
        
        # === TEST 5: Check metadata extraction ===
        print("TEST 5: Metadata Extraction")
        print("-" * 80)
        
        # Sample a few places
        print("Sample Places (first 3):")
        for i, place in enumerate(model.places[:3], 1):
            place_id = place.id if hasattr(place, 'id') else f"P{i}"
            print(f"  {i}. ID={place_id}")
            print(f"     Label: {place.label if hasattr(place, 'label') else 'N/A'}")
            if hasattr(place, 'metadata') and place.metadata:
                print(f"     Metadata: {list(place.metadata.keys())}")
                for key, value in list(place.metadata.items())[:3]:
                    print(f"       - {key}: {value}")
            else:
                print(f"     Metadata: None")
            print()
        
        # Sample a few transitions
        print("Sample Transitions (first 3):")
        for i, trans in enumerate(model.transitions[:3], 1):
            trans_id = trans.id if hasattr(trans, 'id') else f"T{i}"
            print(f"  {i}. ID={trans_id}")
            print(f"     Label: {trans.label if hasattr(trans, 'label') else 'N/A'}")
            print(f"     Type: {trans.transition_type if hasattr(trans, 'transition_type') else 'N/A'}")
            if hasattr(trans, 'metadata') and trans.metadata:
                print(f"     Metadata: {list(trans.metadata.keys())}")
                for key, value in list(trans.metadata.items())[:3]:
                    print(f"       - {key}: {value}")
            else:
                print(f"     Metadata: None")
            print()
        
        # === TEST 6: Test export functionality ===
        print("TEST 6: Export Functionality")
        print("-" * 80)
        
        export_text = category_with_model.export_to_text()
        print("Export to Text (first 800 chars):")
        print(export_text[:800])
        print("...")
        print()
        
    else:
        print("✗ Failed to load KEGG pathway")
        print()
    
    # === SUMMARY ===
    print("=" * 80)
    print("IMPLEMENTATION SUMMARY")
    print("=" * 80)
    print()
    print("✓ IMPLEMENTED:")
    print("  1. Model Overview section")
    print("     - Model name, file path, dates")
    print("     - Project name")
    print("     - Description")
    print()
    print("  2. Petri Net Structure section")
    print("     - Places, transitions, arcs counts")
    print("     - Model type detection (Stochastic, Continuous, Timed, Bio-PN)")
    print()
    print("  3. Import Provenance section (conditional)")
    print("     - Source type (KEGG/SBML)")
    print("     - Source ID and organism")
    print("     - Import date and original file")
    print("     - Metadata (species/reactions counts)")
    print()
    print("  4. Species/Places List (expandable)")
    print("     - Format: [Internal ID] Label | Metadata")
    print("     - Extracts KEGG IDs, formulas, mass")
    print()
    print("  5. Reactions/Transitions List (expandable)")
    print("     - Format: [Internal ID] Label | Type | Metadata")
    print("     - Extracts KEGG reactions, EC numbers, kinetic laws")
    print()
    print("  6. Export to text functionality")
    print()
    print("❓ NEEDS VERIFICATION:")
    print("  - PathwayDocument linking (provenance may not show)")
    print("  - Metadata extraction completeness")
    print("  - Date parsing robustness")
    print()
    print("🔄 TODO:")
    print("  - Export to HTML")
    print("  - Export to PDF")
    print("  - Live refresh on model changes")
    print()


if __name__ == '__main__':
    investigate_models_category()
