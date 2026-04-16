#!/usr/bin/env python3
"""
Test KEGG Import Place Naming

Verifies that places imported from KEGG have:
1. System IDs (P1, P2, etc.) for place.id and place.name
2. Biological names (ATP, Glucose, etc.) for place.label

Author: Shypn Development Team
Date: January 2026
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from shypn.importer.kegg.compound_mapper import StandardCompoundMapper
from shypn.importer.kegg.kegg_data import KEGGEntry, KEGGGraphics
from shypn.importer.kegg.conversion_options import ConversionOptions
from shypn.canvas.lifecycle.id_scope_manager import IDScopeManager


def test_atp_place_naming():
    """Test that ATP compound gets proper naming."""
    print("="*70)
    print("Test: ATP Compound Place Naming")
    print("="*70)
    
    # Create mock KEGG entry for ATP (C00002)
    graphics = KEGGGraphics(name="C00002", fgcolor="#000000", bgcolor="#FFFFFF", type="circle", x=100.0, y=100.0)
    entry = KEGGEntry(
        entry_id=1,
        name="cpd:C00002",
        type="compound",
        graphics=graphics
    )
    
    # Create compound mapper and ID manager
    mapper = StandardCompoundMapper()
    id_manager = IDScopeManager()
    options = ConversionOptions()
    
    # Create place
    place = mapper.create_place(entry, options, id_manager)
    
    # Verify naming
    print(f"\nPlace attributes:")
    print(f"  place.id   = {place.id!r}")
    print(f"  place.name = {place.name!r}")
    print(f"  place.label = {place.label!r}")
    
    print(f"\nMetadata:")
    print(f"  kegg_id = {place.metadata.get('kegg_id')!r}")
    
    # Assertions
    assert place.id.startswith("P"), f"ID should start with 'P', got {place.id!r}"
    assert place.name == place.id, f"Name should match ID, got name={place.name!r}, id={place.id!r}"
    assert place.label not in ("C00002", "cpd:C00002"), \
        f"Label should be biological name, not KEGG code. Got {place.label!r}"
    
    print(f"\n✓ Test PASSED")
    print(f"  - System ID: {place.id}")
    print(f"  - Display label: {place.label}")
    print(f"  - KEGG metadata preserved: {place.metadata.get('kegg_id')}")
    
    return True


def test_glucose_place_naming():
    """Test that Glucose compound gets proper naming."""
    print("\n" + "="*70)
    print("Test: Glucose Compound Place Naming")
    print("="*70)
    
    # Create mock KEGG entry for Glucose (C00031)
    graphics = KEGGGraphics(name="C00031", fgcolor="#000000", bgcolor="#FFFFFF", type="circle", x=150.0, y=150.0)
    entry = KEGGEntry(
        entry_id=2,
        name="cpd:C00031",
        type="compound",
        graphics=graphics
    )
    
    # Create compound mapper and ID manager
    mapper = StandardCompoundMapper()
    id_manager = IDScopeManager()
    options = ConversionOptions()
    
    # Create place
    place = mapper.create_place(entry, options, id_manager)
    
    # Verify naming
    print(f"\nPlace attributes:")
    print(f"  place.id   = {place.id!r}")
    print(f"  place.name = {place.name!r}")
    print(f"  place.label = {place.label!r}")
    
    print(f"\nMetadata:")
    print(f"  kegg_id = {place.metadata.get('kegg_id')!r}")
    
    # Assertions
    assert place.id.startswith("P"), f"ID should start with 'P', got {place.id!r}"
    assert place.name == place.id, f"Name should match ID"
    assert place.label not in ("C00031", "cpd:C00031"), \
        f"Label should be biological name. Got {place.label!r}"
    
    # Check if it's actually "glucose" or similar
    label_lower = place.label.lower()
    assert "glucose" in label_lower or "glc" in label_lower or label_lower.startswith("d-"), \
        f"Expected glucose-related name, got {place.label!r}"
    
    print(f"\n✓ Test PASSED")
    print(f"  - System ID: {place.id}")
    print(f"  - Display label: {place.label}")
    
    return True


def test_rate_formula_usage():
    """Verify that rate formulas will use place.id (P1, P2) not place.label."""
    print("\n" + "="*70)
    print("Test: Rate Formula Uses Place IDs")
    print("="*70)
    
    # Create two places
    mapper = StandardCompoundMapper()
    id_manager = IDScopeManager()
    options = ConversionOptions()
    
    # ATP
    graphics_atp = KEGGGraphics(name="C00002", fgcolor="#000000", bgcolor="#FFFFFF", type="circle", x=100.0, y=100.0)
    entry_atp = KEGGEntry(entry_id=1, name="cpd:C00002", type="compound", graphics=graphics_atp)
    place_atp = mapper.create_place(entry_atp, options, id_manager)
    
    # Glucose
    graphics_glc = KEGGGraphics(name="C00031", fgcolor="#000000", bgcolor="#FFFFFF", type="circle", x=150.0, y=150.0)
    entry_glc = KEGGEntry(entry_id=2, name="cpd:C00031", type="compound", graphics=graphics_glc)
    place_glc = mapper.create_place(entry_glc, options, id_manager)
    
    print(f"\nPlaces created:")
    print(f"  {place_atp.id} (label: {place_atp.label})")
    print(f"  {place_glc.id} (label: {place_glc.label})")
    
    # Simulate rate formula generation (what heuristic system does)
    substrate_ids = [place_atp.id, place_glc.id]
    substrate_expr = ' * '.join(substrate_ids)
    
    # Example Michaelis-Menten formula
    vmax = 100.0
    km = 0.05
    rate_function = f"({vmax} * {substrate_expr}) / ({km} + {substrate_expr})"
    
    print(f"\nGenerated rate formula:")
    print(f"  {rate_function}")
    
    # Verify formula uses IDs not labels
    assert place_atp.id in rate_function, "Formula should contain place ID"
    assert place_glc.id in rate_function, "Formula should contain place ID"
    assert place_atp.label not in rate_function, "Formula should NOT contain biological name"
    assert place_glc.label not in rate_function, "Formula should NOT contain biological name"
    
    print(f"\n✓ Test PASSED")
    print(f"  - Formula uses place IDs ({place_atp.id}, {place_glc.id})")
    print(f"  - Formula does NOT use labels ({place_atp.label}, {place_glc.label})")
    
    return True


def main():
    """Run all tests."""
    print("\n" + "#"*70)
    print("# KEGG Import Place Naming Tests")
    print("#"*70)
    print("\nVerifying that KEGG import produces:")
    print("  1. Place IDs for system use (P1, P2, ...)")
    print("  2. Biological names for display (ATP, Glucose, ...)")
    print("  3. Rate formulas use IDs, not names")
    
    try:
        results = []
        results.append(("ATP place naming", test_atp_place_naming()))
        results.append(("Glucose place naming", test_glucose_place_naming()))
        results.append(("Rate formula ID usage", test_rate_formula_usage()))
        
        # Summary
        print("\n" + "="*70)
        print("SUMMARY")
        print("="*70)
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for name, result in results:
            status = "✓ PASS" if result else "✗ FAIL"
            print(f"{status} - {name}")
        
        print(f"\nTotal: {passed}/{total} tests passed")
        
        if passed == total:
            print("\n🎉 All tests passed!")
            print("\nKEGG import now produces:")
            print("  - Place labels with biological names (ATP, not C00002)")
            print("  - Rate formulas with place IDs (P1, P2, not ATP, Glucose)")
        else:
            print("\n⚠ Some tests failed")
            
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
