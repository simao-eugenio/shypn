"""
Test KEGG enzyme-to-test-arc conversion.

Verifies that KEGG enzyme entries (type="gene"/"enzyme"/"ortholog") 
with reaction attributes are automatically converted to test arcs
(Biological Petri Net catalysts) when create_enzyme_places=True.

NOTE: By default, KEGG imports do NOT create enzyme places (for clean layout).
Set create_enzyme_places=True to enable Biological PN with test arcs.
"""

import pytest
from pathlib import Path
from shypn.importer.kegg import parse_kgml, convert_pathway
from shypn.netobjs.test_arc import TestArc


def test_kegg_enzyme_creates_test_arcs():
    """Test that KEGG enzyme entries create test arcs when create_enzyme_places=True."""
    
    # Create minimal KGML with enzyme entry
    kgml = """<?xml version="1.0"?>
<!DOCTYPE pathway SYSTEM "https://www.kegg.jp/kegg/xml/KGML_v0.7.2_.dtd">
<pathway name="path:test00010" org="test" number="00010">
    <!-- Compound entries -->
    <entry id="1" name="cpd:C00031" type="compound">
        <graphics name="C00031" x="100" y="100" type="circle"/>
    </entry>
    <entry id="2" name="cpd:C00068" type="compound">
        <graphics name="C00068" x="200" y="100" type="circle"/>
    </entry>
    
    <!-- Enzyme entry that catalyzes the reaction -->
    <entry id="3" name="gene:12345" type="gene" reaction="rn:R00710">
        <graphics name="Enzyme XYZ" x="150" y="50" type="rectangle"/>
    </entry>
    
    <!-- Reaction -->
    <reaction id="4" name="rn:R00710" type="irreversible">
        <substrate id="1" name="cpd:C00031"/>
        <product id="2" name="cpd:C00068"/>
    </reaction>
</pathway>"""
    
    # Parse and convert WITH enzyme places enabled
    pathway = parse_kgml(kgml)
    document = convert_pathway(pathway, create_enzyme_places=True)
    
    # Verify structure
    assert len(document.places) >= 2, "Should have at least 2 places (substrates/products)"
    assert len(document.transitions) == 1, "Should have 1 transition (reaction)"
    
    # Check for test arcs
    test_arcs = [arc for arc in document.arcs if isinstance(arc, TestArc)]
    assert len(test_arcs) == 1, "Should have 1 test arc (enzyme)"
    
    # Verify test arc properties
    test_arc = test_arcs[0]
    assert test_arc.consumes_tokens() is False, "Test arc should not consume tokens"
    
    # Verify test arc connects enzyme place to reaction transition
    # The enzyme entry should become a place, connected via test arc to transition
    assert test_arc.target == document.transitions[0], \
        "Test arc should target the reaction transition"
    
    # Verify metadata
    assert test_arc.metadata.get('catalyst_type') == 'enzyme'
    assert test_arc.metadata.get('kegg_reaction') == 'rn:R00710'
    assert test_arc.metadata.get('source') == 'kegg_enzyme'
    
    # Verify document is marked as Biological Petri Net
    assert document.metadata.get('has_test_arcs') is True
    assert document.metadata.get('model_type') == 'Biological Petri Net'
    assert document.metadata.get('source') == 'kegg'
    
    print("✓ KEGG enzyme creates test arc")
    print(f"✓ Test arc: {test_arc.source.label} → {test_arc.target.label}")
    print(f"✓ Document marked as: {document.metadata.get('model_type')}")


def test_kegg_multiple_enzymes():
    """Test that multiple enzyme entries create multiple test arcs."""
    
    kgml = """<?xml version="1.0"?>
<!DOCTYPE pathway SYSTEM "https://www.kegg.jp/kegg/xml/KGML_v0.7.2_.dtd">
<pathway name="path:test00020" org="test" number="00020">
    <!-- Compounds -->
    <entry id="1" name="cpd:C00031" type="compound">
        <graphics name="C00031" x="100" y="100" type="circle"/>
    </entry>
    <entry id="2" name="cpd:C00068" type="compound">
        <graphics name="C00068" x="200" y="100" type="circle"/>
    </entry>
    <entry id="3" name="cpd:C00088" type="compound">
        <graphics name="C00088" x="300" y="100" type="circle"/>
    </entry>
    
    <!-- Two enzyme entries for different reactions -->
    <entry id="4" name="gene:11111" type="gene" reaction="rn:R00710">
        <graphics name="Enzyme A" x="150" y="50" type="rectangle"/>
    </entry>
    <entry id="5" name="gene:22222" type="enzyme" reaction="rn:R00720">
        <graphics name="Enzyme B" x="250" y="50" type="rectangle"/>
    </entry>
    
    <!-- Two reactions -->
    <reaction id="6" name="rn:R00710" type="irreversible">
        <substrate id="1" name="cpd:C00031"/>
        <product id="2" name="cpd:C00068"/>
    </reaction>
    <reaction id="7" name="rn:R00720" type="irreversible">
        <substrate id="2" name="cpd:C00068"/>
        <product id="3" name="cpd:C00088"/>
    </reaction>
</pathway>"""
    
    # Parse and convert WITH enzyme places enabled
    pathway = parse_kgml(kgml)
    document = convert_pathway(pathway, create_enzyme_places=True)
    
    # Verify structure
    assert len(document.places) >= 3, "Should have at least 3 places"
    assert len(document.transitions) == 2, "Should have 2 transitions"
    
    # Check for test arcs
    test_arcs = [arc for arc in document.arcs if isinstance(arc, TestArc)]
    assert len(test_arcs) == 2, "Should have 2 test arcs (2 enzymes)"
    
    # Verify all test arcs are non-consuming
    for test_arc in test_arcs:
        assert test_arc.consumes_tokens() is False
        assert test_arc.metadata.get('source') == 'kegg_enzyme'
    
    # Verify metadata count
    assert document.metadata.get('test_arc_count') == 2
    
    print("✓ Multiple enzymes create multiple test arcs")
    print(f"✓ Created {len(test_arcs)} test arcs from 2 enzyme entries")


def test_kegg_enzyme_without_reaction_attribute():
    """Test that enzyme entries without reaction attribute don't create test arcs."""
    
    kgml = """<?xml version="1.0"?>
<!DOCTYPE pathway SYSTEM "https://www.kegg.jp/kegg/xml/KGML_v0.7.2_.dtd">
<pathway name="path:test00030" org="test" number="00030">
    <!-- Compounds -->
    <entry id="1" name="cpd:C00031" type="compound">
        <graphics name="C00031" x="100" y="100" type="circle"/>
    </entry>
    <entry id="2" name="cpd:C00068" type="compound">
        <graphics name="C00068" x="200" y="100" type="circle"/>
    </entry>
    
    <!-- Enzyme entry WITHOUT reaction attribute -->
    <entry id="3" name="gene:12345" type="gene">
        <graphics name="Enzyme XYZ" x="150" y="50" type="rectangle"/>
    </entry>
    
    <!-- Reaction -->
    <reaction id="4" name="rn:R00710" type="irreversible">
        <substrate id="1" name="cpd:C00031"/>
        <product id="2" name="cpd:C00068"/>
    </reaction>
</pathway>"""
    
    # Parse and convert WITH enzyme places enabled (but enzyme has no reaction attribute)
    pathway = parse_kgml(kgml)
    document = convert_pathway(pathway, create_enzyme_places=True)
    
    # Check for test arcs
    test_arcs = [arc for arc in document.arcs if isinstance(arc, TestArc)]
    assert len(test_arcs) == 0, "Should have 0 test arcs (enzyme has no reaction attribute)"
    
    # Document should NOT be marked as Biological Petri Net
    if hasattr(document, 'metadata') and document.metadata:
        assert document.metadata.get('has_test_arcs') is not True
    
    print("✓ Enzyme without reaction attribute doesn't create test arc")


def test_kegg_compound_entries_not_converted_to_test_arcs():
    """Test that compound entries are not converted to test arcs."""
    
    kgml = """<?xml version="1.0"?>
<!DOCTYPE pathway SYSTEM "https://www.kegg.jp/kegg/xml/KGML_v0.7.2_.dtd">
<pathway name="path:test00040" org="test" number="00040">
    <!-- Compounds (should not become test arcs) -->
    <entry id="1" name="cpd:C00031" type="compound">
        <graphics name="C00031" x="100" y="100" type="circle"/>
    </entry>
    <entry id="2" name="cpd:C00068" type="compound">
        <graphics name="C00068" x="200" y="100" type="circle"/>
    </entry>
    
    <!-- Reaction -->
    <reaction id="3" name="rn:R00710" type="irreversible">
        <substrate id="1" name="cpd:C00031"/>
        <product id="2" name="cpd:C00068"/>
    </reaction>
</pathway>"""
    
    # Parse and convert WITHOUT enzyme places (default)
    pathway = parse_kgml(kgml)
    document = convert_pathway(pathway, create_enzyme_places=False)
    
    # Check for test arcs
    test_arcs = [arc for arc in document.arcs if isinstance(arc, TestArc)]
    assert len(test_arcs) == 0, "Compounds should not create test arcs"
    
    print("✓ Compound entries correctly excluded from test arc conversion")


def test_kegg_ortholog_entry_creates_test_arc():
    """Test that ortholog entries (another enzyme type) create test arcs."""
    
    kgml = """<?xml version="1.0"?>
<!DOCTYPE pathway SYSTEM "https://www.kegg.jp/kegg/xml/KGML_v0.7.2_.dtd">
<pathway name="path:test00050" org="test" number="00050">
    <!-- Compounds -->
    <entry id="1" name="cpd:C00031" type="compound">
        <graphics name="C00031" x="100" y="100" type="circle"/>
    </entry>
    <entry id="2" name="cpd:C00068" type="compound">
        <graphics name="C00068" x="200" y="100" type="circle"/>
    </entry>
    
    <!-- Ortholog entry (enzyme type) -->
    <entry id="3" name="ko:K00001" type="ortholog" reaction="rn:R00710">
        <graphics name="Ortholog ABC" x="150" y="50" type="rectangle"/>
    </entry>
    
    <!-- Reaction -->
    <reaction id="4" name="rn:R00710" type="irreversible">
        <substrate id="1" name="cpd:C00031"/>
        <product id="2" name="cpd:C00068"/>
    </reaction>
</pathway>"""
    
    # Parse and convert WITH enzyme places enabled
    pathway = parse_kgml(kgml)
    document = convert_pathway(pathway, create_enzyme_places=True)
    
    # Check for test arcs
    test_arcs = [arc for arc in document.arcs if isinstance(arc, TestArc)]
    assert len(test_arcs) == 1, "Ortholog should create test arc"
    
    # Verify metadata
    test_arc = test_arcs[0]
    assert test_arc.metadata.get('kegg_entry_type') == 'ortholog'
    assert test_arc.metadata.get('catalyst_type') == 'enzyme'
    
    print("✓ Ortholog entry creates test arc")


def test_kegg_default_behavior_no_enzyme_places():
    """Test that default behavior (create_enzyme_places=False) produces clean layout."""
    
    kgml = """<?xml version="1.0"?>
<!DOCTYPE pathway SYSTEM "https://www.kegg.jp/kegg/xml/KGML_v0.7.2_.dtd">
<pathway name="path:test00060" org="test" number="00060">
    <!-- Compounds -->
    <entry id="1" name="cpd:C00031" type="compound">
        <graphics name="C00031" x="100" y="100" type="circle"/>
    </entry>
    <entry id="2" name="cpd:C00068" type="compound">
        <graphics name="C00068" x="200" y="100" type="circle"/>
    </entry>
    
    <!-- Enzyme entry (should NOT create place by default) -->
    <entry id="3" name="gene:12345" type="gene" reaction="rn:R00710">
        <graphics name="Hexokinase" x="150" y="50" type="rectangle"/>
    </entry>
    
    <!-- Reaction -->
    <reaction id="4" name="rn:R00710" type="irreversible">
        <substrate id="1" name="cpd:C00031"/>
        <product id="2" name="cpd:C00068"/>
    </reaction>
</pathway>"""
    
    # Parse and convert with DEFAULT options (create_enzyme_places=False)
    pathway = parse_kgml(kgml)
    document = convert_pathway(pathway)  # Default: no enzyme places
    
    # Verify: Only compound places created (clean layout)
    assert len(document.places) == 2, "Should only have 2 places (compounds only)"
    assert len(document.transitions) == 1, "Should have 1 transition"
    
    # Verify: No test arcs (enzymes are implicit)
    test_arcs = [arc for arc in document.arcs if isinstance(arc, TestArc)]
    assert len(test_arcs) == 0, "Should have 0 test arcs (enzymes implicit)"
    
    # Verify: Normal arcs only (substrate → transition → product)
    assert len(document.arcs) == 2, "Should have 2 arcs (input + output)"
    
    # Verify: NOT marked as Biological PN
    if hasattr(document, 'metadata') and document.metadata:
        assert document.metadata.get('has_test_arcs') is not True
        assert document.metadata.get('model_type') != 'Biological Petri Net'
    
    # Verify all places are compounds
    for place in document.places:
        assert place.metadata.get('is_enzyme') is not True, \
            "No enzyme places should exist in default mode"
    
    print("✓ Default behavior: Clean layout without enzyme places")
    print(f"  Places: {len(document.places)} (compounds only)")
    print(f"  Test arcs: {len(test_arcs)} (enzymes implicit)")


if __name__ == '__main__':
    print("Testing KEGG enzyme-to-test-arc conversion...")
    print()
    
    test_kegg_enzyme_creates_test_arcs()
    print()
    
    test_kegg_multiple_enzymes()
    print()
    
    test_kegg_enzyme_without_reaction_attribute()
    print()
    
    test_kegg_compound_entries_not_converted_to_test_arcs()
    print()
    
    test_kegg_ortholog_entry_creates_test_arc()
    print()
    
    test_kegg_default_behavior_no_enzyme_places()
    print()
    
    print("=" * 60)
    print("All KEGG catalyst import tests passed! ✓")
    print("=" * 60)
