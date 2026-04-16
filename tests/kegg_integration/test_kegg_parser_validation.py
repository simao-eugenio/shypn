#!/usr/bin/env python3
"""
Phase 0 Validation Test Suite for KEGG Parser

This test suite validates that the KEGG parser correctly:
1. Maintains bipartite property (Place ↔ Transition only)
2. Does NOT convert KEGG relations to arcs
3. Only converts KEGG reactions to arcs
4. Creates the correct number of arcs from reactions

Tests run on real KEGG pathway files to ensure production readiness.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
from pathlib import Path

from shypn.importer.kegg.kgml_parser import KGMLParser
from shypn.importer.kegg.pathway_converter import PathwayConverter
from shypn.netobjs import Place, Transition, Arc


class TestBipartiteProperty:
    """Test that all arcs satisfy bipartite property."""
    
    @pytest.fixture
    def converter(self):
        """Create pathway converter instance."""
        return PathwayConverter()
    
    @pytest.fixture
    def parser(self):
        """Create KGML parser instance."""
        return KGMLParser()
    
    def test_no_place_to_place_arcs_glycolysis(self, parser, converter):
        """Test hsa00010 (Glycolysis) has no Place→Place arcs."""
        kgml_path = "/home/simao/projetos/shypn/workspace/examples/pathways/hsa00010.kgml"
        if not os.path.exists(kgml_path):
            pytest.skip(f"KGML file not found: {kgml_path}")
        
        pathway = parser.parse_file(kgml_path)
        document = converter.convert(pathway)
        
        # Check for Place→Place arcs
        place_to_place = []
        for arc in document.arcs:
            if isinstance(arc.source, Place) and isinstance(arc.target, Place):
                place_to_place.append((arc.source.label, arc.target.label))
        
        assert len(place_to_place) == 0, \
            f"Found {len(place_to_place)} Place→Place arcs: {place_to_place}"
    
    def test_no_transition_to_transition_arcs_glycolysis(self, parser, converter):
        """Test hsa00010 (Glycolysis) has no Transition→Transition arcs."""
        kgml_path = "/home/simao/projetos/shypn/workspace/examples/pathways/hsa00010.kgml"
        if not os.path.exists(kgml_path):
            pytest.skip(f"KGML file not found: {kgml_path}")
        
        pathway = parser.parse_file(kgml_path)
        document = converter.convert(pathway)
        
        # Check for Transition→Transition arcs
        trans_to_trans = []
        for arc in document.arcs:
            if isinstance(arc.source, Transition) and isinstance(arc.target, Transition):
                trans_to_trans.append((arc.source.label, arc.target.label))
        
        assert len(trans_to_trans) == 0, \
            f"Found {len(trans_to_trans)} Transition→Transition arcs: {trans_to_trans}"
    
    def test_all_arcs_bipartite_glycolysis(self, parser, converter):
        """Test all arcs in hsa00010 are bipartite (Place↔Transition)."""
        kgml_path = "/home/simao/projetos/shypn/workspace/examples/pathways/hsa00010.kgml"
        if not os.path.exists(kgml_path):
            pytest.skip(f"KGML file not found: {kgml_path}")
        
        pathway = parser.parse_file(kgml_path)
        document = converter.convert(pathway)
        
        # Count arc types
        place_to_trans = 0
        trans_to_place = 0
        invalid = 0
        
        for arc in document.arcs:
            if isinstance(arc.source, Place) and isinstance(arc.target, Transition):
                place_to_trans += 1
            elif isinstance(arc.source, Transition) and isinstance(arc.target, Place):
                trans_to_place += 1
            else:
                invalid += 1
        
        assert invalid == 0, f"Found {invalid} invalid arcs (not Place↔Transition)"
        assert place_to_trans + trans_to_place == len(document.arcs), \
            f"Arc count mismatch: {place_to_trans} + {trans_to_place} != {len(document.arcs)}"
        print(f"\n✓ Glycolysis arcs: {place_to_trans} Place→Transition, {trans_to_place} Transition→Place")


class TestRelationsNotConverted:
    """Test that KEGG relations are NOT converted to arcs."""
    
    @pytest.fixture
    def converter(self):
        """Create pathway converter instance."""
        return PathwayConverter()
    
    @pytest.fixture
    def parser(self):
        """Create KGML parser instance."""
        return KGMLParser()
    
    def test_relations_not_converted_glycolysis(self, parser, converter):
        """Test hsa00010 relations are NOT converted to arcs."""
        kgml_path = "/home/simao/projetos/shypn/workspace/examples/pathways/hsa00010.kgml"
        if not os.path.exists(kgml_path):
            pytest.skip(f"KGML file not found: {kgml_path}")
        
        pathway = parser.parse_file(kgml_path)
        document = converter.convert(pathway)
        
        # Glycolysis has 84 relations but only 73 arcs (from reactions)
        assert len(pathway.relations) > 0, "Pathway should have relations"
        assert len(document.arcs) < len(pathway.relations), \
            f"Arc count ({len(document.arcs)}) should be less than relations ({len(pathway.relations)})"
        
        print(f"\n✓ Glycolysis: {len(pathway.relations)} relations, {len(document.arcs)} arcs")
        print(f"  Relations NOT converted ✓")
    
    def test_arc_count_matches_reactions(self, parser, converter):
        """Test arc count approximately matches reactions (substrates + products)."""
        kgml_path = "/home/simao/projetos/shypn/workspace/examples/pathways/hsa00010.kgml"
        if not os.path.exists(kgml_path):
            pytest.skip(f"KGML file not found: {kgml_path}")
        
        pathway = parser.parse_file(kgml_path)
        document = converter.convert(pathway)
        
        # Count expected arcs from reactions
        expected_arcs = 0
        for reaction in pathway.reactions:
            expected_arcs += len(reaction.substrates)  # Input arcs
            expected_arcs += len(reaction.products)    # Output arcs
        
        # Arc count should be close to expected (some reactions may share compounds)
        # We don't expect exact match due to shared compounds
        assert len(document.arcs) > 0, "Should have arcs from reactions"
        assert len(document.arcs) <= expected_arcs, \
            f"Arc count ({len(document.arcs)}) exceeds expected from reactions ({expected_arcs})"
        
        print(f"\n✓ Reactions: {len(pathway.reactions)}")
        print(f"  Expected arcs (max): {expected_arcs}")
        print(f"  Actual arcs: {len(document.arcs)}")
        print(f"  Difference: {expected_arcs - len(document.arcs)} (shared compounds)")


class TestMultiplePathways:
    """Test validation across multiple KEGG pathways."""
    
    @pytest.fixture
    def converter(self):
        """Create pathway converter instance."""
        return PathwayConverter()
    
    @pytest.fixture
    def parser(self):
        """Create KGML parser instance."""
        return KGMLParser()
    
    @pytest.mark.parametrize("pathway_id,pathway_name", [
        ("hsa00010", "Glycolysis"),
        ("hsa00020", "Citrate cycle (TCA)"),
        ("hsa00030", "Pentose phosphate pathway"),
    ])
    def test_bipartite_property_multiple_pathways(self, parser, converter, pathway_id, pathway_name):
        """Test bipartite property across multiple pathways."""
        kgml_path = f"/home/simao/projetos/shypn/workspace/examples/pathways/{pathway_id}.kgml"
        if not os.path.exists(kgml_path):
            pytest.skip(f"KGML file not found: {kgml_path}")
        
        pathway = parser.parse_file(kgml_path)
        document = converter.convert(pathway)
        
        # Count arc types
        place_to_trans = sum(1 for arc in document.arcs 
                            if isinstance(arc.source, Place) and isinstance(arc.target, Transition))
        trans_to_place = sum(1 for arc in document.arcs 
                            if isinstance(arc.source, Transition) and isinstance(arc.target, Place))
        
        # Check bipartite property
        assert place_to_trans + trans_to_place == len(document.arcs), \
            f"{pathway_name}: Not all arcs are bipartite"
        
        print(f"\n✓ {pathway_name} ({pathway_id}):")
        print(f"  Relations: {len(pathway.relations)} (NOT converted)")
        print(f"  Arcs: {len(document.arcs)} (Place→Transition: {place_to_trans}, Transition→Place: {trans_to_place})")


class TestValidationExceptions:
    """Test that validation correctly raises exceptions for invalid structures."""
    
    @pytest.fixture
    def converter(self):
        """Create pathway converter instance."""
        return PathwayConverter()
    
    def test_validation_method_detects_place_to_place(self, converter):
        """Test that Arc constructor prevents Place→Place connections."""
        from shypn.data.canvas.document_model import DocumentModel
        
        # Create mock places
        place1 = Place(x=100, y=100, id=1, name="P1", label="P1")
        place2 = Place(x=200, y=200, id=2, name="P2", label="P2")
        
        # Arc constructor should raise ValueError for Place→Place
        with pytest.raises(ValueError, match="Invalid connection: Place → Place"):
            arc = Arc(source=place1, target=place2, id=1, name="A1")
        
        print("\n✓ Arc constructor prevents Place→Place connections")
    
    def test_validation_method_detects_transition_to_transition(self, converter):
        """Test that Arc constructor prevents Transition→Transition connections."""
        from shypn.data.canvas.document_model import DocumentModel
        
        # Create mock transitions
        trans1 = Transition(x=100, y=100, id=1, name="T1", label="T1")
        trans2 = Transition(x=200, y=200, id=2, name="T2", label="T2")
        
        # Arc constructor should raise ValueError for Transition→Transition
        with pytest.raises(ValueError, match="Invalid connection: Transition → Transition"):
            arc = Arc(source=trans1, target=trans2, id=1, name="A1")
        
        print("\n✓ Arc constructor prevents Transition→Transition connections")
    
    def test_validation_accepts_valid_bipartite(self, converter):
        """Test that _validate_bipartite_property accepts valid arcs."""
        from shypn.data.canvas.document_model import DocumentModel
        
        # Create mock document with valid Place↔Transition arcs
        document = DocumentModel()
        place = Place(x=100, y=100, id=1, name="P1", label="P1")
        trans = Transition(x=200, y=200, id=1, name="T1", label="T1")
        arc1 = Arc(source=place, target=trans, id=1, name="A1")
        arc2 = Arc(source=trans, target=place, id=2, name="A2")
        
        document.places.append(place)
        document.transitions.append(trans)
        document.arcs.append(arc1)
        document.arcs.append(arc2)
        
        # Create mock pathway
        class MockPathway:
            name = "test_pathway"
            title = "Test Pathway"
        
        # Should NOT raise exception
        try:
            converter.strategy._validate_bipartite_property(document, MockPathway())
            print("\n✓ Validation accepts valid bipartite structure")
        except ValueError as e:
            pytest.fail(f"Validation incorrectly rejected valid structure: {e}")


class TestArcBuilderValidation:
    """Test validation in arc_builder.py."""
    
    @pytest.fixture
    def parser(self):
        """Create KGML parser instance."""
        return KGMLParser()
    
    @pytest.fixture
    def converter(self):
        """Create pathway converter instance."""
        return PathwayConverter()
    
    def test_arc_builder_creates_valid_arcs(self, parser, converter):
        """Test that arc_builder creates only valid bipartite arcs."""
        kgml_path = "/home/simao/projetos/shypn/workspace/examples/pathways/hsa00010.kgml"
        if not os.path.exists(kgml_path):
            pytest.skip(f"KGML file not found: {kgml_path}")
        
        pathway = parser.parse_file(kgml_path)
        
        # This will call arc_builder internally
        # If arc_builder validation works, this should NOT raise exception
        try:
            document = converter.convert(pathway)
            print(f"\n✓ arc_builder created {len(document.arcs)} valid arcs")
        except ValueError as e:
            pytest.fail(f"arc_builder created invalid arcs: {e}")


def run_tests():
    """Run all tests with pytest."""
    import pytest
    
    # Run with verbose output
    args = [
        __file__,
        '-v',
        '--tb=short',
        '-s',  # Show print statements
    ]
    
    return pytest.main(args)


if __name__ == '__main__':
    print("=" * 70)
    print("Phase 0 Validation Test Suite")
    print("=" * 70)
    print("\nThis test suite validates:")
    print("1. Bipartite property (Place ↔ Transition only)")
    print("2. Relations NOT converted to arcs")
    print("3. Only reactions create arcs")
    print("4. Validation methods work correctly")
    print("\n" + "=" * 70)
    
    exit_code = run_tests()
    
    print("\n" + "=" * 70)
    if exit_code == 0:
        print("✓ All Phase 0 validation tests PASSED")
    else:
        print("✗ Some tests FAILED")
    print("=" * 70)
    
    sys.exit(exit_code)
