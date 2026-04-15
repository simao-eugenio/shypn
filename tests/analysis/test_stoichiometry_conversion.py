"""Tests for stoichiometry support in KEGG pathway conversion.

This test module verifies that stoichiometric coefficients are correctly:
1. Parsed from KGML XML
2. Stored in data models
3. Applied as arc weights in Petri nets
4. Preserved in metadata for traceability
"""

import pytest
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from shypn.importer.kegg.kgml_parser import parse_kgml
from shypn.importer.kegg.pathway_converter import convert_pathway
from shypn.importer.kegg.models import KEGGSubstrate, KEGGProduct


class TestStoichiometryDataModels:
    """Test stoichiometry in data models."""
    
    def test_substrate_default_stoichiometry(self):
        """Test substrate has default stoichiometry of 1."""
        substrate = KEGGSubstrate(id="1", name="cpd:C00031")
        assert substrate.stoichiometry == 1
    
    def test_substrate_explicit_stoichiometry(self):
        """Test substrate with explicit stoichiometry."""
        substrate = KEGGSubstrate(id="1", name="cpd:C00027", stoichiometry=2)
        assert substrate.stoichiometry == 2
    
    def test_product_default_stoichiometry(self):
        """Test product has default stoichiometry of 1."""
        product = KEGGProduct(id="1", name="cpd:C00668")
        assert product.stoichiometry == 1
    
    def test_product_explicit_stoichiometry(self):
        """Test product with explicit stoichiometry."""
        product = KEGGProduct(id="1", name="cpd:C00001", stoichiometry=2)
        assert product.stoichiometry == 2


class TestStoichiometryParsing:
    """Test stoichiometry parsing from KGML."""
    
    def test_parse_reaction_without_stoichiometry(self):
        """Test parsing reaction with implicit 1:1 stoichiometry."""
        kgml = """<?xml version="1.0"?>
        <pathway name="test" org="hsa" number="00010" title="Test Pathway">
            <entry id="1" name="cpd:C00031" type="compound">
                <graphics name="Glucose" x="100" y="100"/>
            </entry>
            <entry id="2" name="cpd:C00668" type="compound">
                <graphics name="G6P" x="200" y="100"/>
            </entry>
            <reaction id="1" name="rn:R01068" type="irreversible">
                <substrate id="1" name="cpd:C00031"/>
                <product id="2" name="cpd:C00668"/>
            </reaction>
        </pathway>
        """
        
        pathway = parse_kgml(kgml)
        assert pathway is not None
        assert len(pathway.reactions) == 1
        
        reaction = pathway.reactions[0]
        
        # Verify default stoichiometry
        assert len(reaction.substrates) == 1
        assert reaction.substrates[0].stoichiometry == 1
        assert len(reaction.products) == 1
        assert reaction.products[0].stoichiometry == 1
    
    def test_parse_reaction_with_stoichiometry(self):
        """Test parsing reaction with explicit stoichiometry (2 H2O2 → 2 H2O + O2)."""
        kgml = """<?xml version="1.0"?>
        <pathway name="test" org="hsa" number="00010" title="Test Pathway">
            <entry id="1" name="cpd:C00027" type="compound">
                <graphics name="H2O2" x="100" y="100"/>
            </entry>
            <entry id="2" name="cpd:C00001" type="compound">
                <graphics name="H2O" x="200" y="100"/>
            </entry>
            <entry id="3" name="cpd:C00007" type="compound">
                <graphics name="O2" x="300" y="100"/>
            </entry>
            <reaction id="1" name="rn:R00959" type="irreversible">
                <substrate id="1" name="cpd:C00027" stoichiometry="2"/>
                <product id="2" name="cpd:C00001" stoichiometry="2"/>
                <product id="3" name="cpd:C00007" stoichiometry="1"/>
            </reaction>
        </pathway>
        """
        
        pathway = parse_kgml(kgml)
        assert pathway is not None
        
        reaction = pathway.reactions[0]
        
        # Verify explicit stoichiometry
        assert len(reaction.substrates) == 1
        assert reaction.substrates[0].stoichiometry == 2
        assert len(reaction.products) == 2
        assert reaction.products[0].stoichiometry == 2  # H2O
        assert reaction.products[1].stoichiometry == 1  # O2
    
    def test_parse_invalid_stoichiometry(self):
        """Test parsing handles invalid stoichiometry gracefully."""
        kgml = """<?xml version="1.0"?>
        <pathway name="test" org="hsa" number="00010" title="Test Pathway">
            <entry id="1" name="cpd:C00031" type="compound">
                <graphics name="Glucose" x="100" y="100"/>
            </entry>
            <entry id="2" name="cpd:C00668" type="compound">
                <graphics name="G6P" x="200" y="100"/>
            </entry>
            <reaction id="1" name="rn:R01068" type="irreversible">
                <substrate id="1" name="cpd:C00031" stoichiometry="invalid"/>
                <product id="2" name="cpd:C00668" stoichiometry="3.14"/>
            </reaction>
        </pathway>
        """
        
        pathway = parse_kgml(kgml)
        reaction = pathway.reactions[0]
        
        # Should default to 1 for invalid values
        assert reaction.substrates[0].stoichiometry == 1  # Invalid string
        assert reaction.products[0].stoichiometry == 1    # Float defaults to 1 (int() raises ValueError)


class TestStoichiometryConversion:
    """Test stoichiometry in Petri net conversion."""
    
    def test_convert_simple_reaction(self):
        """Test 1:1 reaction converts with weight 1."""
        kgml = """<?xml version="1.0"?>
        <pathway name="test" org="hsa" number="00010" title="Test Pathway">
            <entry id="1" name="cpd:C00031" type="compound">
                <graphics name="Glucose" x="100" y="100"/>
            </entry>
            <entry id="2" name="cpd:C00668" type="compound">
                <graphics name="G6P" x="200" y="100"/>
            </entry>
            <reaction id="1" name="rn:R01068" type="irreversible">
                <substrate id="1" name="cpd:C00031"/>
                <product id="2" name="cpd:C00668"/>
            </reaction>
        </pathway>
        """
        
        pathway = parse_kgml(kgml)
        document = convert_pathway(pathway)
        
        # Verify conversion
        assert len(document.places) == 2
        assert len(document.transitions) == 1
        assert len(document.arcs) == 2
        
        # Check arc weights (all should be 1)
        for arc in document.arcs:
            assert arc.weight == 1
    
    def test_convert_stoichiometric_reaction(self):
        """Test 2:2:1 reaction (2 H2O2 → 2 H2O + O2) converts with correct weights."""
        kgml = """<?xml version="1.0"?>
        <pathway name="test" org="hsa" number="00010" title="Test Pathway">
            <entry id="1" name="cpd:C00027" type="compound">
                <graphics name="H2O2" x="100" y="100"/>
            </entry>
            <entry id="2" name="cpd:C00001" type="compound">
                <graphics name="H2O" x="200" y="100"/>
            </entry>
            <entry id="3" name="cpd:C00007" type="compound">
                <graphics name="O2" x="300" y="100"/>
            </entry>
            <reaction id="1" name="rn:R00959" type="irreversible">
                <substrate id="1" name="cpd:C00027" stoichiometry="2"/>
                <product id="2" name="cpd:C00001" stoichiometry="2"/>
                <product id="3" name="cpd:C00007" stoichiometry="1"/>
            </reaction>
        </pathway>
        """
        
        pathway = parse_kgml(kgml)
        document = convert_pathway(pathway)
        
        # Verify conversion
        assert len(document.places) == 3
        assert len(document.transitions) == 1
        assert len(document.arcs) == 3  # 1 input, 2 outputs
        
        # Find arcs by checking their connections
        transition = document.transitions[0]
        
        # Check input arc (H2O2 → transition)
        input_arcs = [a for a in document.arcs if a.target == transition]
        assert len(input_arcs) == 1
        assert input_arcs[0].weight == 2
        
        # Check output arcs (transition → H2O, transition → O2)
        output_arcs = [a for a in document.arcs if a.source == transition]
        assert len(output_arcs) == 2
        
        # One should have weight 2 (H2O), one should have weight 1 (O2)
        weights = sorted([arc.weight for arc in output_arcs])
        assert weights == [1, 2]
    
    def test_arc_metadata_contains_stoichiometry(self):
        """Test arc metadata includes stoichiometry value."""
        kgml = """<?xml version="1.0"?>
        <pathway name="test" org="hsa" number="00010" title="Test Pathway">
            <entry id="1" name="cpd:C00027" type="compound">
                <graphics name="H2O2" x="100" y="100"/>
            </entry>
            <entry id="2" name="cpd:C00001" type="compound">
                <graphics name="H2O" x="200" y="100"/>
            </entry>
            <reaction id="1" name="rn:R00959" type="irreversible">
                <substrate id="1" name="cpd:C00027" stoichiometry="2"/>
                <product id="2" name="cpd:C00001" stoichiometry="2"/>
            </reaction>
        </pathway>
        """
        
        pathway = parse_kgml(kgml)
        document = convert_pathway(pathway)
        
        # Check metadata
        for arc in document.arcs:
            assert hasattr(arc, 'metadata')
            assert 'stoichiometry' in arc.metadata
            assert arc.metadata['stoichiometry'] == 2
            assert arc.metadata['source'] == 'KEGG'
            assert 'direction' in arc.metadata
    
    def test_backward_compatibility(self):
        """Test that pathways without stoichiometry still work (backward compatibility)."""
        kgml = """<?xml version="1.0"?>
        <pathway name="test" org="hsa" number="00010" title="Test Pathway">
            <entry id="1" name="cpd:C00031" type="compound">
                <graphics name="Glucose" x="100" y="100"/>
            </entry>
            <entry id="2" name="cpd:C00002" type="compound">
                <graphics name="ATP" x="150" y="50"/>
            </entry>
            <entry id="3" name="cpd:C00668" type="compound">
                <graphics name="G6P" x="200" y="100"/>
            </entry>
            <entry id="4" name="cpd:C00008" type="compound">
                <graphics name="ADP" x="150" y="150"/>
            </entry>
            <reaction id="1" name="rn:R01068" type="irreversible">
                <substrate id="1" name="cpd:C00031"/>
                <substrate id="2" name="cpd:C00002"/>
                <product id="3" name="cpd:C00668"/>
                <product id="4" name="cpd:C00008"/>
            </reaction>
        </pathway>
        """
        
        pathway = parse_kgml(kgml)
        document = convert_pathway(pathway, include_cofactors=True)
        
        # Should work without errors
        assert len(document.places) == 4
        assert len(document.transitions) == 1
        assert len(document.arcs) == 4
        
        # All arcs should have weight 1 (default)
        for arc in document.arcs:
            assert arc.weight == 1
            assert arc.metadata['stoichiometry'] == 1


class TestComplexStoichiometry:
    """Test complex stoichiometry scenarios."""
    
    def test_multiple_reactions_with_different_stoichiometry(self):
        """Test pathway with multiple reactions having different stoichiometry."""
        kgml = """<?xml version="1.0"?>
        <pathway name="test" org="hsa" number="00010" title="Test Pathway">
            <entry id="1" name="cpd:C00031" type="compound">
                <graphics name="Glucose" x="100" y="100"/>
            </entry>
            <entry id="2" name="cpd:C00668" type="compound">
                <graphics name="G6P" x="200" y="100"/>
            </entry>
            <entry id="3" name="cpd:C00027" type="compound">
                <graphics name="H2O2" x="100" y="200"/>
            </entry>
            <entry id="4" name="cpd:C00001" type="compound">
                <graphics name="H2O" x="200" y="200"/>
            </entry>
            <entry id="5" name="cpd:C00007" type="compound">
                <graphics name="O2" x="300" y="200"/>
            </entry>
            <reaction id="1" name="rn:R01068" type="irreversible">
                <substrate id="1" name="cpd:C00031"/>
                <product id="2" name="cpd:C00668"/>
            </reaction>
            <reaction id="2" name="rn:R00959" type="irreversible">
                <substrate id="3" name="cpd:C00027" stoichiometry="2"/>
                <product id="4" name="cpd:C00001" stoichiometry="2"/>
                <product id="5" name="cpd:C00007" stoichiometry="1"/>
            </reaction>
        </pathway>
        """
        
        pathway = parse_kgml(kgml)
        document = convert_pathway(pathway)
        
        # Verify conversion
        assert len(document.places) == 5
        assert len(document.transitions) == 2
        assert len(document.arcs) == 5  # 2 for reaction 1, 3 for reaction 2
        
        # Check that we have both weight=1 and weight=2 arcs
        weights = [arc.weight for arc in document.arcs]
        assert 1 in weights
        assert 2 in weights


# Run tests
if __name__ == '__main__':
    pytest.main([__file__, '-v'])
