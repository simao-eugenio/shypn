#!/usr/bin/env python3
"""Test suite for incidence matrix implementations.

Tests both sparse and dense implementations to ensure they produce
identical results and correctly implement Petri net semantics.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
from shypn.data.canvas.document_model import DocumentModel
from shypn.netobjs import Place, Transition, Arc
from shypn.matrix import SparseIncidenceMatrix, DenseIncidenceMatrix
from shypn.matrix.loader import load_matrix, get_recommendation


class TestMatrixConstruction:
    """Test matrix construction from document."""
    
    @pytest.fixture
    def simple_document(self):
        """Create a simple Petri net: P1 → T1 → P2."""
        doc = DocumentModel()
        
        # Places
        p1 = Place(x=100, y=100, id=1, name="P1", label="P1")
        p2 = Place(x=300, y=100, id=2, name="P2", label="P2")
        p1.tokens = 1
        p1.initial_marking = 1
        
        # Transition
        t1 = Transition(x=200, y=100, id=1, name="T1", label="T1")
        
        # Arcs
        a1 = Arc(source=p1, target=t1, id=1, name="A1", weight=1)
        a2 = Arc(source=t1, target=p2, id=2, name="A2", weight=1)
        
        doc.places.extend([p1, p2])
        doc.transitions.append(t1)
        doc.arcs.extend([a1, a2])
        
        return doc
    
    def test_sparse_build(self, simple_document):
        """Test sparse matrix construction."""
        matrix = SparseIncidenceMatrix(simple_document)
        matrix.build()
        
        assert matrix._built
        assert len(matrix.places) == 2
        assert len(matrix.transitions) == 1
        assert len(matrix.F_minus_dict) == 1
        assert len(matrix.F_plus_dict) == 1
        
        print("\n✓ Sparse matrix built successfully")
    
    def test_dense_build(self, simple_document):
        """Test dense matrix construction."""
        matrix = DenseIncidenceMatrix(simple_document)
        matrix.build()
        
        assert matrix._built
        assert len(matrix.places) == 2
        assert len(matrix.transitions) == 1
        assert matrix.F_minus is not None
        assert matrix.F_plus is not None
        assert matrix.C is not None
        
        print("\n✓ Dense matrix built successfully")
    
    def test_sparse_dense_equivalence(self, simple_document):
        """Test that sparse and dense produce same results."""
        sparse = SparseIncidenceMatrix(simple_document)
        sparse.build()
        
        dense = DenseIncidenceMatrix(simple_document)
        dense.build()
        
        # Check dimensions
        assert sparse.get_dimensions() == dense.get_dimensions()
        
        # Check all matrix entries
        t1_id = simple_document.transitions[0].id
        for place in simple_document.places:
            p_id = place.id
            
            # F⁻ (input)
            assert sparse.get_input_weights(t1_id, p_id) == dense.get_input_weights(t1_id, p_id)
            
            # F⁺ (output)
            assert sparse.get_output_weights(t1_id, p_id) == dense.get_output_weights(t1_id, p_id)
            
            # C (incidence)
            assert sparse.get_incidence(t1_id, p_id) == dense.get_incidence(t1_id, p_id)
        
        print("\n✓ Sparse and dense matrices are equivalent")


class TestMatrixQueries:
    """Test matrix query operations."""
    
    @pytest.fixture
    def weighted_document(self):
        """Create Petri net with weighted arcs: 2·P1 → T1 → 3·P2."""
        doc = DocumentModel()
        
        p1 = Place(x=100, y=100, id=1, name="P1", label="P1")
        p2 = Place(x=300, y=100, id=2, name="P2", label="P2")
        t1 = Transition(x=200, y=100, id=1, name="T1", label="T1")
        
        a1 = Arc(source=p1, target=t1, id=1, name="A1", weight=2)
        a2 = Arc(source=t1, target=p2, id=2, name="A2", weight=3)
        
        doc.places.extend([p1, p2])
        doc.transitions.append(t1)
        doc.arcs.extend([a1, a2])
        
        return doc
    
    @pytest.mark.parametrize("matrix_class", [SparseIncidenceMatrix, DenseIncidenceMatrix])
    def test_input_weights(self, weighted_document, matrix_class):
        """Test get_input_weights."""
        matrix = matrix_class(weighted_document)
        matrix.build()
        
        t1_id = weighted_document.transitions[0].id
        p1_id = weighted_document.places[0].id
        p2_id = weighted_document.places[1].id
        
        assert matrix.get_input_weights(t1_id, p1_id) == 2
        assert matrix.get_input_weights(t1_id, p2_id) == 0
        
        print(f"\n✓ {matrix_class.__name__}: Input weights correct")
    
    @pytest.mark.parametrize("matrix_class", [SparseIncidenceMatrix, DenseIncidenceMatrix])
    def test_output_weights(self, weighted_document, matrix_class):
        """Test get_output_weights."""
        matrix = matrix_class(weighted_document)
        matrix.build()
        
        t1_id = weighted_document.transitions[0].id
        p1_id = weighted_document.places[0].id
        p2_id = weighted_document.places[1].id
        
        assert matrix.get_output_weights(t1_id, p1_id) == 0
        assert matrix.get_output_weights(t1_id, p2_id) == 3
        
        print(f"\n✓ {matrix_class.__name__}: Output weights correct")
    
    @pytest.mark.parametrize("matrix_class", [SparseIncidenceMatrix, DenseIncidenceMatrix])
    def test_incidence(self, weighted_document, matrix_class):
        """Test get_incidence (C = F⁺ - F⁻)."""
        matrix = matrix_class(weighted_document)
        matrix.build()
        
        t1_id = weighted_document.transitions[0].id
        p1_id = weighted_document.places[0].id
        p2_id = weighted_document.places[1].id
        
        # P1: consumes 2, produces 0 → C = -2
        assert matrix.get_incidence(t1_id, p1_id) == -2
        
        # P2: consumes 0, produces 3 → C = +3
        assert matrix.get_incidence(t1_id, p2_id) == 3
        
        print(f"\n✓ {matrix_class.__name__}: Incidence values correct")


class TestSimulation:
    """Test Petri net simulation (firing transitions)."""
    
    @pytest.fixture
    def simulation_document(self):
        """Create Petri net for simulation testing."""
        doc = DocumentModel()
        
        # P1 --2--> T1 --3--> P2
        p1 = Place(x=100, y=100, id=1, name="P1", label="P1")
        p2 = Place(x=300, y=100, id=2, name="P2", label="P2")
        t1 = Transition(x=200, y=100, id=1, name="T1", label="T1")
        
        a1 = Arc(source=p1, target=t1, id=1, name="A1", weight=2)
        a2 = Arc(source=t1, target=p2, id=2, name="A2", weight=3)
        
        doc.places.extend([p1, p2])
        doc.transitions.append(t1)
        doc.arcs.extend([a1, a2])
        
        return doc
    
    @pytest.mark.parametrize("matrix_class", [SparseIncidenceMatrix, DenseIncidenceMatrix])
    def test_is_enabled(self, simulation_document, matrix_class):
        """Test transition enabling."""
        matrix = matrix_class(simulation_document)
        matrix.build()
        
        t1_id = simulation_document.transitions[0].id
        p1_id = simulation_document.places[0].id
        p2_id = simulation_document.places[1].id
        
        # T1 requires 2 tokens from P1
        marking_enabled = {p1_id: 2, p2_id: 0}
        marking_disabled = {p1_id: 1, p2_id: 0}
        
        assert matrix.is_enabled(t1_id, marking_enabled)
        assert not matrix.is_enabled(t1_id, marking_disabled)
        
        print(f"\n✓ {matrix_class.__name__}: Enabling check correct")
    
    @pytest.mark.parametrize("matrix_class", [SparseIncidenceMatrix, DenseIncidenceMatrix])
    def test_fire(self, simulation_document, matrix_class):
        """Test transition firing (state equation M' = M + C·σ)."""
        matrix = matrix_class(simulation_document)
        matrix.build()
        
        t1_id = simulation_document.transitions[0].id
        p1_id = simulation_document.places[0].id
        p2_id = simulation_document.places[1].id
        
        # Initial marking: P1=5, P2=0
        initial_marking = {p1_id: 5, p2_id: 0}
        
        # Fire T1: should consume 2 from P1, produce 3 in P2
        new_marking = matrix.fire(t1_id, initial_marking)
        
        assert new_marking[p1_id] == 3  # 5 - 2 = 3
        assert new_marking[p2_id] == 3  # 0 + 3 = 3
        
        print(f"\n✓ {matrix_class.__name__}: Firing produces correct marking")
    
    @pytest.mark.parametrize("matrix_class", [SparseIncidenceMatrix, DenseIncidenceMatrix])
    def test_fire_not_enabled(self, simulation_document, matrix_class):
        """Test that firing disabled transition raises error."""
        matrix = matrix_class(simulation_document)
        matrix.build()
        
        t1_id = simulation_document.transitions[0].id
        p1_id = simulation_document.places[0].id
        p2_id = simulation_document.places[1].id
        
        # Insufficient tokens
        marking = {p1_id: 1, p2_id: 0}
        
        with pytest.raises(ValueError, match="not enabled"):
            matrix.fire(t1_id, marking)
        
        print(f"\n✓ {matrix_class.__name__}: Firing disabled transition raises error")


class TestLoader:
    """Test matrix loader functionality."""
    
    @pytest.fixture
    def small_document(self):
        """Small document (should use dense)."""
        doc = DocumentModel()
        p1 = Place(x=100, y=100, id=1, name="P1", label="P1")
        t1 = Transition(x=200, y=100, id=1, name="T1", label="T1")
        a1 = Arc(source=p1, target=t1, id=1, name="A1")
        
        doc.places.append(p1)
        doc.transitions.append(t1)
        doc.arcs.append(a1)
        return doc
    
    def test_auto_select(self, small_document):
        """Test auto-selection of implementation."""
        matrix = load_matrix(small_document, implementation='auto')
        
        assert matrix._built
        assert isinstance(matrix, (SparseIncidenceMatrix, DenseIncidenceMatrix))
        
        print(f"\n✓ Auto-selected: {matrix.__class__.__name__}")
    
    def test_explicit_sparse(self, small_document):
        """Test explicit sparse selection."""
        matrix = load_matrix(small_document, implementation='sparse')
        
        assert isinstance(matrix, SparseIncidenceMatrix)
        assert matrix._built
        
        print("\n✓ Explicit sparse selection works")
    
    def test_explicit_dense(self, small_document):
        """Test explicit dense selection."""
        matrix = load_matrix(small_document, implementation='dense')
        
        assert isinstance(matrix, DenseIncidenceMatrix)
        assert matrix._built
        
        print("\n✓ Explicit dense selection works")
    
    def test_get_recommendation(self, small_document):
        """Test recommendation function."""
        recommendation = get_recommendation(small_document)
        
        assert recommendation in ['sparse', 'dense']
        print(f"\n✓ Recommendation: {recommendation}")


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
    
    @pytest.mark.parametrize("matrix_class", [SparseIncidenceMatrix, DenseIncidenceMatrix])
    def test_glycolysis_build(self, glycolysis_document, matrix_class):
        """Test building matrix from glycolysis pathway."""
        matrix = matrix_class(glycolysis_document)
        matrix.build()
        
        stats = matrix.get_statistics()
        
        assert stats['built']
        assert stats['places'] > 0
        assert stats['transitions'] > 0
        assert stats['total_arcs'] == 73  # Known from Phase 0 tests
        
        print(f"\n✓ {matrix_class.__name__} - Glycolysis:")
        print(f"  Places: {stats['places']}")
        print(f"  Transitions: {stats['transitions']}")
        print(f"  Total arcs: {stats['total_arcs']}")
    
    def test_glycolysis_validation(self, glycolysis_document):
        """Test bipartite validation on glycolysis."""
        matrix = load_matrix(glycolysis_document)
        
        is_valid, errors = matrix.validate_bipartite()
        
        assert is_valid, f"Bipartite validation failed: {errors}"
        print("\n✓ Glycolysis: Bipartite property validated")


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
    print("Incidence Matrix Test Suite")
    print("=" * 70)
    print("\nTesting OOP implementation:")
    print("- Base class (IncidenceMatrix)")
    print("- Sparse implementation (dict-based)")
    print("- Dense implementation (NumPy arrays)")
    print("- Loader (factory)")
    print("\n" + "=" * 70)
    
    exit_code = run_tests()
    
    print("\n" + "=" * 70)
    if exit_code == 0:
        print("✓ All incidence matrix tests PASSED")
    else:
        print("✗ Some tests FAILED")
    print("=" * 70)
    
    sys.exit(exit_code)
