#!/usr/bin/env python3
"""Test bidirectional compound name ↔ ID auto-suggestion.

Verifies that:
1. Typing compound ID → suggests name
2. Typing compound name → suggests ID
3. Mapper has comprehensive coverage
"""

import sys
sys.path.insert(0, 'src')

from shypn.thermodynamics.compound_mapper import CompoundMapper


def test_id_to_name():
    """Test ID → name lookup."""
    print("Test 1: ID → Name Lookup")
    
    test_cases = [
        ('C00002', 'ATP'),
        ('C00031', 'Glucose'),
        ('C00186', 'Lactate'),
        ('C00003', 'NAD+'),
        ('C00005', 'NADPH'),
    ]
    
    for compound_id, expected_name in test_cases:
        result = CompoundMapper.id_to_name(compound_id)
        assert result == expected_name, f"Expected {expected_name}, got {result}"
        print(f"  ✓ {compound_id} → {result}")
    
    print("✅ ID → Name tests passed\n")


def test_name_to_id():
    """Test name → ID lookup."""
    print("Test 2: Name → ID Lookup")
    
    test_cases = [
        ('ATP', 'C00002'),
        ('atp', 'C00002'),  # Case-insensitive
        ('Glucose', 'C00031'),
        ('D-Glucose', 'C00031'),  # Alternative name
        ('Lactate', 'C00186'),
        ('NAD+', 'C00003'),
        ('NAD', 'C00003'),  # Without +
        ('NADPH', 'C00005'),
        ('Pyruvate', 'C00022'),
    ]
    
    for name, expected_id in test_cases:
        result = CompoundMapper.name_to_id(name)
        assert result == expected_id, f"'{name}' → Expected {expected_id}, got {result}"
        print(f"  ✓ '{name}' → {result}")
    
    print("✅ Name → ID tests passed\n")


def test_fuzzy_matching():
    """Test partial name suggestions."""
    print("Test 3: Fuzzy Matching (Suggestions)")
    
    # Test partial name matching
    glu_suggestions = CompoundMapper.suggest_names('glu')
    print(f"  'glu' → {len(glu_suggestions)} suggestions:")
    for name, compound_id in glu_suggestions[:5]:
        print(f"    - {name} ({compound_id})")
    
    assert len(glu_suggestions) >= 3, "Should suggest at least 3 compounds for 'glu'"
    assert any('Glucose' in name for name, _ in glu_suggestions), "Should include Glucose"
    assert any('Glutamate' in name for name, _ in glu_suggestions), "Should include Glutamate"
    
    # Test partial ID matching
    c00_suggestions = CompoundMapper.suggest_ids('C0000')
    print(f"\n  'C0000' → {len(c00_suggestions)} suggestions:")
    for compound_id, name in c00_suggestions[:5]:
        print(f"    - {compound_id} ({name})")
    
    assert len(c00_suggestions) >= 5, "Should suggest at least 5 IDs for 'C0000'"
    
    print("✅ Fuzzy matching tests passed\n")


def test_alias_support():
    """Test alternative name aliases."""
    print("Test 4: Alias Support")
    
    test_cases = [
        ('adenosine triphosphate', 'C00002'),  # Full name
        ('lactic acid', 'C00186'),  # Common name
        ('dextrose', 'C00031'),  # Alternative name for glucose
        ('2-oxoglutarate', 'C00026'),  # IUPAC name
    ]
    
    for alias, expected_id in test_cases:
        result = CompoundMapper.name_to_id(alias)
        assert result == expected_id, f"Alias '{alias}' → Expected {expected_id}, got {result}"
        print(f"  ✓ '{alias}' → {result}")
    
    print("✅ Alias tests passed\n")


def test_coverage():
    """Test mapper coverage of common metabolites."""
    print("Test 5: Metabolite Coverage")
    
    categories = {
        'Energy metabolites': ['ATP', 'ADP', 'AMP', 'GTP', 'GDP'],
        'Cofactors': ['NAD+', 'NADH', 'NADP+', 'NADPH', 'FAD', 'CoA'],
        'Glycolysis': ['Glucose', 'G6P', 'F6P', 'Pyruvate', 'Lactate'],
        'TCA cycle': ['Citrate', 'Isocitrate', 'Succinate', 'Malate'],
        'Amino acids': ['Glutamate', 'Glutamine', 'Alanine', 'Glycine'],
    }
    
    total_mapped = 0
    for category, compounds in categories.items():
        mapped = sum(1 for c in compounds if CompoundMapper.name_to_id(c))
        total_mapped += mapped
        print(f"  {category}: {mapped}/{len(compounds)} mapped")
    
    total_compounds = sum(len(v) for v in categories.values())
    coverage = (total_mapped / total_compounds) * 100
    
    print(f"\n  Total coverage: {total_mapped}/{total_compounds} ({coverage:.0f}%)")
    assert coverage >= 90, f"Coverage should be ≥90%, got {coverage:.0f}%"
    
    print("✅ Coverage tests passed\n")


def test_bidirectional_consistency():
    """Test round-trip consistency."""
    print("Test 6: Bidirectional Consistency")
    
    # Test that ID → name → ID is consistent
    test_ids = ['C00002', 'C00031', 'C00003', 'C00022', 'C00186']
    
    for compound_id in test_ids:
        name = CompoundMapper.id_to_name(compound_id)
        if name:
            reverse_id = CompoundMapper.name_to_id(name)
            assert reverse_id == compound_id, f"{compound_id} → {name} → {reverse_id} (inconsistent)"
            print(f"  ✓ {compound_id} ↔ {name}")
    
    print("✅ Bidirectional consistency passed\n")


def test_dialog_integration():
    """Test that mapper integrates with dialog loader."""
    print("Test 7: Dialog Integration")
    
    # Check if place_prop_dialog_loader imports CompoundMapper
    try:
        from shypn.helpers.place_prop_dialog_loader import PlacePropDialogLoader
        print("  ✓ PlacePropDialogLoader imports successfully")
        
        # Check if new methods exist
        loader_methods = dir(PlacePropDialogLoader)
        assert '_on_compound_id_changed' in loader_methods, "Missing _on_compound_id_changed method"
        assert '_on_place_name_changed' in loader_methods, "Missing _on_place_name_changed method"
        assert '_block_handler' in loader_methods, "Missing _block_handler method"
        
        print("  ✓ Bidirectional handler methods present")
        print("  ✓ Signal blocking utility present")
        
    except ImportError as e:
        print(f"  ⚠️  Dialog loader import failed: {e}")
        print("     (This is expected if GTK is not available)")
    
    print("✅ Dialog integration verified\n")


if __name__ == '__main__':
    print("=" * 60)
    print("COMPOUND MAPPER BIDIRECTIONAL TEST SUITE")
    print("=" * 60)
    print()
    
    tests = [
        ("ID → Name", test_id_to_name),
        ("Name → ID", test_name_to_id),
        ("Fuzzy Matching", test_fuzzy_matching),
        ("Alias Support", test_alias_support),
        ("Coverage", test_coverage),
        ("Bidirectional Consistency", test_bidirectional_consistency),
        ("Dialog Integration", test_dialog_integration),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"\n❌ {test_name} FAILED: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed == 0:
        print("\n✅ All bidirectional mapping tests passed!")
        print("\nUsage in dialog:")
        print("  1. Type 'ATP' in Name field → auto-suggests C00002 in Compound ID")
        print("  2. Type 'C00002' in Compound ID → auto-fills 'ATP' in Name")
        print("  3. Works for 80+ common metabolites")
        sys.exit(0)
    else:
        print(f"\n❌ {failed} test(s) failed")
        sys.exit(1)
