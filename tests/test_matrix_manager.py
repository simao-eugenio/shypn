#!/usr/bin/env python3
"""Test suite for MatrixManager integration layer.

Tests the integration between incidence matrix and simulation system.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
from shypn.data.canvas.document_model import DocumentModel
from shypn.netobjs import Place, Transition, Arc
from shypn.matrix import MatrixManager


class TestMatrixManagerBasics:
    """Test basic MatrixManager functionality."""
    
    @pytest.fixture
    def simple_document(self):
        """Create simple document: P1 → T1 → P2."""
        doc = DocumentModel()
        
        p1 = Place(x=100, y=100, id=1, name="P1", label="P1")
        p2 = Place(x=300, y=100, id=2, name="P2", label="P2")
        t1 = Transition(x=200, y=100, id=1, name="T1", label="T1")
        
        p1.tokens = 5
        p1.initial_marking = 5
        
        a1 = Arc(source=p1, target=t1, id=1, name="A1", weight=1)
        a2 = Arc(source=t1, target=p2, id=2, name="A2", weight=1)
        
        doc.places.extend([p1, p2])
        doc.transitions.append(t1)
        doc.arcs.extend([a1, a2])
        
        return doc
    
    def test_manager_creation(self, simple_document):
        """Test creating MatrixManager."""
        manager = MatrixManager(simple_document)
        
        assert manager.matrix is not None
        assert manager.document == simple_document
        
        print("\n✓ MatrixManager created successfully")
    
    def test_auto_build(self, simple_document):
        """Test automatic matrix building."""
        manager = MatrixManager(simple_document)
        
        stats = manager.get_statistics()
        assert stats['built']
        assert stats['places'] == 2
        assert stats['transitions'] == 1
        assert stats['total_arcs'] == 2
        
        print("\n✓ Auto-build works correctly")
    
    def test_query_methods(self, simple_document):
        """Test matrix query delegation."""
        manager = MatrixManager(simple_document)
        
        t1_id = simple_document.transitions[0].id
        p1_id = simple_document.places[0].id
        p2_id = simple_document.places[1].id
        
        # Test input weights
        assert manager.get_input_weights(t1_id, p1_id) == 1
        assert manager.get_input_weights(t1_id, p2_id) == 0
        
        # Test output weights
        assert manager.get_output_weights(t1_id, p1_id) == 0
        assert manager.get_output_weights(t1_id, p2_id) == 1
        
        # Test incidence
        assert manager.get_incidence(t1_id, p1_id) == -1
        assert manager.get_incidence(t1_id, p2_id) == 1
        
        print("\n✓ Query methods work correctly")


class TestSimulationIntegration:
    """Test integration with simulation."""
    
    @pytest.fixture
    def simulation_document(self):
        """Create document for simulation testing."""
        doc = DocumentModel()
        
        # P1 --2--> T1 --3--> P2
        p1 = Place(x=100, y=100, id=1, name="P1", label="P1")
        p2 = Place(x=300, y=100, id=2, name="P2", label="P2")
        t1 = Transition(x=200, y=100, id=1, name="T1", label="T1")
        
        p1.tokens = 10
        p1.initial_marking = 10
        
        a1 = Arc(source=p1, target=t1, id=1, name="A1", weight=2)
        a2 = Arc(source=t1, target=p2, id=2, name="A2", weight=3)
        
        doc.places.extend([p1, p2])
        doc.transitions.append(t1)
        doc.arcs.extend([a1, a2])
        
        return doc
    
    def test_get_marking_from_document(self, simulation_document):
        """Test extracting marking from document."""
        manager = MatrixManager(simulation_document)
        
        marking = manager.get_marking_from_document()
        
        p1_id = simulation_document.places[0].id
        p2_id = simulation_document.places[1].id
        
        assert marking[p1_id] == 10
        assert marking[p2_id] == 0
        
        print("\n✓ Marking extraction works")
    
    def test_is_enabled(self, simulation_document):
        """Test enabling check via manager."""
        manager = MatrixManager(simulation_document)
        
        t1_id = simulation_document.transitions[0].id
        marking = manager.get_marking_from_document()
        
        # T1 requires 2 tokens from P1
        assert manager.is_enabled(t1_id, marking)
        
        # Reduce tokens below requirement
        p1_id = simulation_document.places[0].id
        marking[p1_id] = 1
        assert not manager.is_enabled(t1_id, marking)
        
        print("\n✓ Enabling check works")
    
    def test_fire(self, simulation_document):
        """Test firing via manager."""
        manager = MatrixManager(simulation_document)
        
        t1_id = simulation_document.transitions[0].id
        p1_id = simulation_document.places[0].id
        p2_id = simulation_document.places[1].id
        
        marking = manager.get_marking_from_document()
        
        # Fire T1: consume 2 from P1, produce 3 in P2
        new_marking = manager.fire(t1_id, marking)
        
        assert new_marking[p1_id] == 8  # 10 - 2
        assert new_marking[p2_id] == 3  # 0 + 3
        
        print("\n✓ Firing works correctly")
    
    def test_apply_marking_to_document(self, simulation_document):
        """Test applying marking back to document."""
        manager = MatrixManager(simulation_document)
        
        t1_id = simulation_document.transitions[0].id
        marking = manager.get_marking_from_document()
        
        # Fire and apply
        new_marking = manager.fire(t1_id, marking)
        manager.apply_marking_to_document(new_marking)
        
        # Check document was updated
        assert simulation_document.places[0].tokens == 8
        assert simulation_document.places[1].tokens == 3
        
        print("\n✓ Marking application works")
    
    def test_get_enabled_transitions(self, simulation_document):
        """Test getting list of enabled transitions."""
        manager = MatrixManager(simulation_document)
        
        t1_id = simulation_document.transitions[0].id
        
        # With sufficient tokens
        marking = manager.get_marking_from_document()
        enabled = manager.get_enabled_transitions(marking)
        
        assert t1_id in enabled
        
        # With insufficient tokens
        p1_id = simulation_document.places[0].id
        marking[p1_id] = 1
        enabled = manager.get_enabled_transitions(marking)
        
        assert t1_id not in enabled
        
        print("\n✓ Enabled transitions list works")


class TestDocumentChanges:
    """Test handling of document changes."""
    
    @pytest.fixture
    def mutable_document(self):
        """Create document that will be modified."""
        doc = DocumentModel()
        
        p1 = Place(x=100, y=100, id=1, name="P1", label="P1")
        t1 = Transition(x=200, y=100, id=1, name="T1", label="T1")
        a1 = Arc(source=p1, target=t1, id=1, name="A1")
        
        doc.places.append(p1)
        doc.transitions.append(t1)
        doc.arcs.append(a1)
        
        return doc
    
    def test_auto_rebuild_on_change(self, mutable_document):
        """Test automatic rebuild when document changes."""
        manager = MatrixManager(mutable_document, auto_rebuild=True)
        
        initial_hash = manager._last_build_hash
        
        # Add new place
        p2 = Place(x=300, y=100, id=2, name="P2", label="P2")
        mutable_document.places.append(p2)
        
        # Next query should trigger rebuild
        stats = manager.get_statistics()
        
        assert stats['places'] == 2
        assert manager._last_build_hash != initial_hash
        
        print("\n✓ Auto-rebuild on document change works")
    
    def test_manual_invalidation(self, mutable_document):
        """Test manual invalidation."""
        manager = MatrixManager(mutable_document, auto_rebuild=False)
        
        initial_hash = manager._last_build_hash
        
        # Invalidate
        manager.invalidate()
        
        assert manager._last_build_hash is None
        
        # Rebuild
        manager.build()
        assert manager._last_build_hash is not None
        
        print("\n✓ Manual invalidation works")


class TestValidation:
    """Test validation and analysis methods."""
    
    @pytest.fixture
    def valid_document(self):
        """Create valid bipartite document."""
        doc = DocumentModel()
        
        p1 = Place(x=100, y=100, id=1, name="P1", label="P1")
        t1 = Transition(x=200, y=100, id=1, name="T1", label="T1")
        p2 = Place(x=300, y=100, id=2, name="P2", label="P2")
        
        a1 = Arc(source=p1, target=t1, id=1, name="A1")
        a2 = Arc(source=t1, target=p2, id=2, name="A2")
        
        doc.places.extend([p1, p2])
        doc.transitions.append(t1)
        doc.arcs.extend([a1, a2])
        
        return doc
    
    def test_validate_bipartite(self, valid_document):
        """Test bipartite validation."""
        manager = MatrixManager(valid_document)
        
        is_valid, errors = manager.validate_bipartite()
        
        assert is_valid
        assert len(errors) == 0
        
        print("\n✓ Bipartite validation works")
    
    def test_get_dimensions(self, valid_document):
        """Test getting matrix dimensions."""
        manager = MatrixManager(valid_document)
        
        num_transitions, num_places = manager.get_dimensions()
        
        assert num_transitions == 1
        assert num_places == 2
        
        print("\n✓ Dimension query works")


class TestRealPathway:
    """Test with real KEGG pathway."""
    
    @pytest.fixture
    def glycolysis_document(self):
        """Load glycolysis pathway."""
        from shypn.importer.kegg.kgml_parser import KGMLParser
        from shypn.importer.kegg.pathway_converter import PathwayConverter
        
        kgml_path = "/home/simao/projetos/shypn/workspace/examples/pathways/hsa00010.kgml"
        if not os.path.exists(kgml_path):
            pytest.skip(f"KGML file not found: {kgml_path}")
        
        parser = KGMLParser()
        pathway = parser.parse_file(kgml_path)
        
        converter = PathwayConverter()
        document = converter.convert(pathway)
        
        return document
    
    def test_glycolysis_integration(self, glycolysis_document):
        """Test MatrixManager with glycolysis pathway."""
        manager = MatrixManager(glycolysis_document)
        
        stats = manager.get_statistics()
        
        assert stats['built']
        assert stats['places'] == 26
        assert stats['transitions'] == 34
        assert stats['total_arcs'] == 73
        
        print("\n✓ MatrixManager works with glycolysis pathway")
        print(f"  {manager}")
    
    def test_glycolysis_simulation(self, glycolysis_document):
        """Test simulation operations on glycolysis."""
        manager = MatrixManager(glycolysis_document)
        
        # Get initial marking from document
        marking = manager.get_marking_from_document()
        
        # Find enabled transitions
        enabled = manager.get_enabled_transitions(marking)
        
        print(f"\n✓ Glycolysis simulation ready")
        print(f"  Enabled transitions: {len(enabled)}")
        
        # Try firing one enabled transition (if any)
        if enabled:
            t_id = enabled[0]
            new_marking = manager.fire(t_id, marking)
            print(f"  Fired transition {t_id}")
            print(f"  Marking changed: {marking != new_marking}")


def run_tests():
    """Run all tests with pytest."""
    args = [
        __file__,
        '-v',
        '--tb=short',
        '-s',
    ]
    
    return pytest.main(args)


if __name__ == '__main__':
    print("=" * 70)
    print("MatrixManager Integration Test Suite")
    print("=" * 70)
    print("\nTesting integration layer:")
    print("- MatrixManager creation and auto-build")
    print("- Query method delegation")
    print("- Simulation integration (marking, enabling, firing)")
    print("- Document change handling")
    print("- Validation methods")
    print("- Real pathway integration")
    print("\n" + "=" * 70)
    
    exit_code = run_tests()
    
    print("\n" + "=" * 70)
    if exit_code == 0:
        print("✓ All MatrixManager integration tests PASSED")
    else:
        print("✗ Some tests FAILED")
    print("=" * 70)
    
    sys.exit(exit_code)
