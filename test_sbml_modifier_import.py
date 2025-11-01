"""
Test SBML modifier-to-test-arc conversion.

Verifies that SBML modifiers (catalysts/enzymes) are automatically
converted to test arcs (Biological Petri Net).
"""

from shypn.data.pathway.sbml_parser import SBMLParser
from shypn.data.pathway.pathway_converter import PathwayConverter
from shypn.netobjs.test_arc import TestArc


def test_sbml_modifier_creates_test_arc():
    """Test that SBML modifiers create test arcs."""
    
    # Minimal SBML with modifier (catalyst/enzyme)
    sbml_str = """<?xml version="1.0" encoding="UTF-8"?>
<sbml xmlns="http://www.sbml.org/sbml/level3/version1/core" level="3" version="1">
  <model id="test_model" name="Test Model">
    <listOfCompartments>
      <compartment id="c" spatialDimensions="3" size="1" constant="true"/>
    </listOfCompartments>
    
    <listOfSpecies>
      <species id="S1" name="Substrate" compartment="c" initialAmount="10" hasOnlySubstanceUnits="false" boundaryCondition="false" constant="false"/>
      <species id="S2" name="Product" compartment="c" initialAmount="0" hasOnlySubstanceUnits="false" boundaryCondition="false" constant="false"/>
      <species id="E1" name="Enzyme" compartment="c" initialAmount="1" hasOnlySubstanceUnits="false" boundaryCondition="false" constant="false"/>
    </listOfSpecies>
    
    <listOfReactions>
      <reaction id="R1" name="Catalyzed Reaction" reversible="false" fast="false">
        <listOfReactants>
          <speciesReference species="S1" stoichiometry="1" constant="true"/>
        </listOfReactants>
        <listOfProducts>
          <speciesReference species="S2" stoichiometry="1" constant="true"/>
        </listOfProducts>
        <listOfModifiers>
          <modifierSpeciesReference species="E1"/>
        </listOfModifiers>
      </reaction>
    </listOfReactions>
  </model>
</sbml>"""
    
    # Parse SBML
    parser = SBMLParser()
    pathway = parser.parse_string(sbml_str)
    
    # Verify modifier was parsed
    assert len(pathway.reactions) == 1
    reaction = pathway.reactions[0]
    assert len(reaction.modifiers) == 1
    assert reaction.modifiers[0] == "E1"
    
    print(f"✓ SBML parser extracted modifier: {reaction.modifiers[0]}")
    
    # Convert to Petri net
    converter = PathwayConverter()
    document = converter.convert(pathway)
    
    # Verify structure
    assert len(document.places) == 3, "Should have 3 places (S1, S2, E1)"
    assert len(document.transitions) == 1, "Should have 1 transition"
    
    # Check for test arcs
    test_arcs = [arc for arc in document.arcs if isinstance(arc, TestArc)]
    assert len(test_arcs) == 1, f"Should have 1 test arc (enzyme), found {len(test_arcs)}"
    
    # Verify test arc properties
    test_arc = test_arcs[0]
    assert test_arc.consumes_tokens() is False, "Test arc should not consume tokens"
    assert test_arc.target == document.transitions[0], "Test arc should target the transition"
    
    # Find enzyme place
    enzyme_place = next((p for p in document.places if p.name == "E1"), None)
    assert enzyme_place is not None, "Enzyme place should exist"
    assert test_arc.source == enzyme_place, "Test arc should come from enzyme place"
    
    # Verify document metadata
    assert document.metadata.get('has_test_arcs') is True
    assert document.metadata.get('model_type') == 'Biological Petri Net'
    
    print(f"✓ Test arc created: {test_arc.source.name} → {test_arc.target.name}")
    print(f"✓ Document marked as: {document.metadata.get('model_type')}")
    print(f"✓ Test arc is non-consuming: {not test_arc.consumes_tokens()}")


def test_sbml_multiple_modifiers():
    """Test that multiple modifiers create multiple test arcs."""
    
    sbml_str = """<?xml version="1.0" encoding="UTF-8"?>
<sbml xmlns="http://www.sbml.org/sbml/level3/version1/core" level="3" version="1">
  <model id="test_model" name="Test Model">
    <listOfCompartments>
      <compartment id="c" spatialDimensions="3" size="1" constant="true"/>
    </listOfCompartments>
    
    <listOfSpecies>
      <species id="S1" name="Substrate" compartment="c" initialAmount="10" hasOnlySubstanceUnits="false" boundaryCondition="false" constant="false"/>
      <species id="S2" name="Product" compartment="c" initialAmount="0" hasOnlySubstanceUnits="false" boundaryCondition="false" constant="false"/>
      <species id="E1" name="Enzyme1" compartment="c" initialAmount="1" hasOnlySubstanceUnits="false" boundaryCondition="false" constant="false"/>
      <species id="E2" name="Enzyme2" compartment="c" initialAmount="1" hasOnlySubstanceUnits="false" boundaryCondition="false" constant="false"/>
    </listOfSpecies>
    
    <listOfReactions>
      <reaction id="R1" name="Multi-Enzyme Reaction" reversible="false" fast="false">
        <listOfReactants>
          <speciesReference species="S1" stoichiometry="1" constant="true"/>
        </listOfReactants>
        <listOfProducts>
          <speciesReference species="S2" stoichiometry="1" constant="true"/>
        </listOfProducts>
        <listOfModifiers>
          <modifierSpeciesReference species="E1"/>
          <modifierSpeciesReference species="E2"/>
        </listOfModifiers>
      </reaction>
    </listOfReactions>
  </model>
</sbml>"""
    
    # Parse and convert
    parser = SBMLParser()
    pathway = parser.parse_string(sbml_str)
    
    converter = PathwayConverter()
    document = converter.convert(pathway)
    
    # Check for test arcs
    test_arcs = [arc for arc in document.arcs if isinstance(arc, TestArc)]
    assert len(test_arcs) == 2, "Should have 2 test arcs (2 enzymes)"
    
    # Verify both are non-consuming
    for test_arc in test_arcs:
        assert test_arc.consumes_tokens() is False
    
    # Verify metadata
    assert document.metadata.get('test_arc_count') == 2
    
    print(f"✓ Multiple modifiers: {len(test_arcs)} test arcs created")


def test_sbml_no_modifiers():
    """Test that reactions without modifiers don't create test arcs."""
    
    sbml_str = """<?xml version="1.0" encoding="UTF-8"?>
<sbml xmlns="http://www.sbml.org/sbml/level3/version1/core" level="3" version="1">
  <model id="test_model" name="Test Model">
    <listOfCompartments>
      <compartment id="c" spatialDimensions="3" size="1" constant="true"/>
    </listOfCompartments>
    
    <listOfSpecies>
      <species id="S1" name="Substrate" compartment="c" initialAmount="10" hasOnlySubstanceUnits="false" boundaryCondition="false" constant="false"/>
      <species id="S2" name="Product" compartment="c" initialAmount="0" hasOnlySubstanceUnits="false" boundaryCondition="false" constant="false"/>
    </listOfSpecies>
    
    <listOfReactions>
      <reaction id="R1" name="Simple Reaction" reversible="false" fast="false">
        <listOfReactants>
          <speciesReference species="S1" stoichiometry="1" constant="true"/>
        </listOfReactants>
        <listOfProducts>
          <speciesReference species="S2" stoichiometry="1" constant="true"/>
        </listOfProducts>
        <!-- NO MODIFIERS -->
      </reaction>
    </listOfReactions>
  </model>
</sbml>"""
    
    # Parse and convert
    parser = SBMLParser()
    pathway = parser.parse_string(sbml_str)
    
    converter = PathwayConverter()
    document = converter.convert(pathway)
    
    # Check for test arcs
    test_arcs = [arc for arc in document.arcs if isinstance(arc, TestArc)]
    assert len(test_arcs) == 0, "Should have 0 test arcs (no modifiers)"
    
    # Should NOT be marked as Biological PN
    if hasattr(document, 'metadata') and document.metadata:
        assert document.metadata.get('has_test_arcs') is not True
    
    print(f"✓ No modifiers: No test arcs created (classical PN)")


if __name__ == '__main__':
    print("Testing SBML modifier-to-test-arc conversion...")
    print()
    
    test_sbml_modifier_creates_test_arc()
    print()
    
    test_sbml_multiple_modifiers()
    print()
    
    test_sbml_no_modifiers()
    print()
    
    print("=" * 60)
    print("All SBML modifier import tests passed! ✓")
    print("=" * 60)
