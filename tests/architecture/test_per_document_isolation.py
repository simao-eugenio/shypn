"""Test per-document isolation - verifying SHYpn's MDI architecture.

This test suite validates that all components maintain per-document instance
isolation, which is fundamental to SHYpn's Multiple Document Interface (MDI)
architecture.

Critical Requirement:
- Each document must have independent state (ID counters, object collections, etc.)
- Opening multiple documents simultaneously must not cause state interference
- No shared global state that could leak between documents
"""

import pytest
from shypn.data.canvas.document_model import DocumentModel
from shypn.builders.place_builder import PlaceBuilder
from shypn.builders.transition_builder import TransitionBuilder
from shypn.builders.arc_builder import ArcBuilder
from shypn.builders.petri_net_builder import PetriNetBuilder


class TestPerDocumentIsolation:
    """Validate per-document isolation for MDI architecture."""
    
    def test_document_model_has_independent_id_managers(self):
        """Each DocumentModel instance must have its own IDManager."""
        doc1 = DocumentModel()
        doc2 = DocumentModel()
        doc3 = DocumentModel()
        
        # Each document must have different IDManager instances
        assert doc1.id_manager is not doc2.id_manager
        assert doc1.id_manager is not doc3.id_manager
        assert doc2.id_manager is not doc3.id_manager
        
        # Verify they are actual different objects in memory
        id_managers = {id(doc1.id_manager), id(doc2.id_manager), id(doc3.id_manager)}
        assert len(id_managers) == 3, "All three documents must have unique IDManager instances"
    
    def test_id_sequences_are_per_document(self):
        """ID generation must be isolated per document (P1, T1, etc. start fresh)."""
        doc1 = DocumentModel()
        doc2 = DocumentModel()
        
        # Create objects in doc1
        p1_doc1 = PlaceBuilder(id_manager=doc1.id_manager).build()
        p2_doc1 = PlaceBuilder(id_manager=doc1.id_manager).build()
        t1_doc1 = TransitionBuilder(id_manager=doc1.id_manager).build()
        t2_doc1 = TransitionBuilder(id_manager=doc1.id_manager).build()
        
        # Create objects in doc2 - should start from P1, T1 again
        p1_doc2 = PlaceBuilder(id_manager=doc2.id_manager).build()
        p2_doc2 = PlaceBuilder(id_manager=doc2.id_manager).build()
        t1_doc2 = TransitionBuilder(id_manager=doc2.id_manager).build()
        t2_doc2 = TransitionBuilder(id_manager=doc2.id_manager).build()
        
        # Doc1 should have P1, P2, T1, T2
        assert p1_doc1.id == "P1"
        assert p2_doc1.id == "P2"
        assert t1_doc1.id == "T1"
        assert t2_doc1.id == "T2"
        
        # Doc2 should ALSO have P1, P2, T1, T2 (independent sequence)
        assert p1_doc2.id == "P1"
        assert p2_doc2.id == "P2"
        assert t1_doc2.id == "T1"
        assert t2_doc2.id == "T2"
    
    def test_multiple_documents_simultaneous_creation(self):
        """Simulate MDI scenario: multiple documents open simultaneously."""
        docs = [DocumentModel() for _ in range(5)]
        
        # Create objects in each document
        for i, doc in enumerate(docs):
            # Each document creates same structure
            p1 = PlaceBuilder(id_manager=doc.id_manager).with_name(f"Source_{i}").build()
            p2 = PlaceBuilder(id_manager=doc.id_manager).with_name(f"Target_{i}").build()
            t = TransitionBuilder(f"React_{i}", id_manager=doc.id_manager).build()
            
            # IDs should be same pattern in each document
            assert p1.id == "P1", f"Doc {i} should start with P1"
            assert p2.id == "P2", f"Doc {i} should have P2"
            assert t.id == "T1", f"Doc {i} should have T1"
    
    def test_petri_net_builder_uses_document_id_manager(self):
        """PetriNetBuilder must use the document's IDManager."""
        builder = PetriNetBuilder("test_model")
        
        # Builder creates a DocumentModel internally
        assert hasattr(builder._model, 'id_manager')
        
        # Create place directly and add to builder
        p1 = PlaceBuilder(id_manager=builder._model.id_manager).with_name("P1").build()
        p2 = PlaceBuilder(id_manager=builder._model.id_manager).with_name("P2").build()
        t1 = TransitionBuilder("T1", id_manager=builder._model.id_manager).build()
        
        builder.add_place(p1)
        builder.add_place(p2)
        builder.add_transition(t1)
        
        model = builder.build()
        
        # Objects should use document's ID sequence
        assert model.places[0].id == "P1"
        assert model.places[1].id == "P2"
        assert model.transitions[0].id == "T1"
    
    def test_builder_integration_with_document(self):
        """Builders integrated with document must respect document's ID manager."""
        doc = DocumentModel()
        
        # Create places using document's id_manager
        p1 = PlaceBuilder(id_manager=doc.id_manager).with_name("S1").build()
        p2 = PlaceBuilder(id_manager=doc.id_manager).with_name("S2").build()
        
        # Create transitions using same document's id_manager
        t1 = TransitionBuilder("R1", id_manager=doc.id_manager).build()
        t2 = TransitionBuilder("R2", id_manager=doc.id_manager).build()
        
        # All should follow document's sequence
        assert p1.id == "P1"
        assert p2.id == "P2"
        assert t1.id == "T1"
        assert t2.id == "T2"
    
    def test_document_object_collections_are_independent(self):
        """Object collections (places, transitions, arcs) must be per-document."""
        doc1 = DocumentModel()
        doc2 = DocumentModel()
        
        # Add objects to doc1
        p1 = PlaceBuilder(id_manager=doc1.id_manager).build()
        doc1.add_place(p1)
        
        # Add objects to doc2
        p2 = PlaceBuilder(id_manager=doc2.id_manager).build()
        doc2.add_place(p2)
        
        # Collections must be independent
        assert len(doc1.places) == 1
        assert len(doc2.places) == 1
        assert doc1.places[0] is not doc2.places[0]
        
        # Doc1's place should not appear in doc2
        assert p1 not in doc2.places
        assert p2 not in doc1.places
    
    def test_no_global_state_leakage(self):
        """Verify no module-level globals that could leak state between documents."""
        # Create document, generate some IDs
        doc1 = DocumentModel()
        for _ in range(5):
            PlaceBuilder(id_manager=doc1.id_manager).build()
            TransitionBuilder(id_manager=doc1.id_manager).build()
        
        # Create new document - should start fresh, not continue from doc1
        doc2 = DocumentModel()
        p_new = PlaceBuilder(id_manager=doc2.id_manager).build()
        t_new = TransitionBuilder(id_manager=doc2.id_manager).build()
        
        # Should be P1 and T1, NOT P6 and T6
        assert p_new.id == "P1", "New document must start with P1, not continue previous sequence"
        assert t_new.id == "T1", "New document must start with T1, not continue previous sequence"
    
    def test_standalone_builders_do_not_interfere_with_documents(self):
        """Standalone builders (no id_manager) must not affect document instances."""
        doc = DocumentModel()
        
        # Create standalone builder objects (creates temporary IDManager each time)
        standalone_place = PlaceBuilder().build()
        standalone_trans = TransitionBuilder().build()
        
        # Now create using document's id_manager
        doc_place = PlaceBuilder(id_manager=doc.id_manager).build()
        doc_trans = TransitionBuilder(id_manager=doc.id_manager).build()
        
        # Document's sequence should start fresh regardless of standalone usage
        assert doc_place.id == "P1"
        assert doc_trans.id == "T1"


class TestMDIScenarios:
    """Test real-world MDI usage scenarios."""
    
    def test_load_multiple_models_simultaneously(self):
        """Simulate loading multiple saved models (common MDI operation)."""
        # Simulate 3 models loaded from disk
        model_a = DocumentModel()
        model_b = DocumentModel()
        model_c = DocumentModel()
        
        # Each model reconstructs objects with its own IDManager
        for model, prefix in [(model_a, "A"), (model_b, "B"), (model_c, "C")]:
            p = PlaceBuilder(id_manager=model.id_manager).with_name(f"{prefix}_place").build()
            t = TransitionBuilder(f"{prefix}_trans", id_manager=model.id_manager).build()
            model.add_place(p)
            model.add_transition(t)
        
        # All models should have P1, T1 (independent sequences)
        assert model_a.places[0].id == "P1"
        assert model_b.places[0].id == "P1"
        assert model_c.places[0].id == "P1"
        
        assert model_a.transitions[0].id == "T1"
        assert model_b.transitions[0].id == "T1"
        assert model_c.transitions[0].id == "T1"
    
    def test_copy_paste_between_documents(self):
        """Test copying objects from one document to another."""
        source_doc = DocumentModel()
        target_doc = DocumentModel()
        
        # Create object in source
        source_place = PlaceBuilder(id_manager=source_doc.id_manager).with_name("Source").build()
        assert source_place.id == "P1"
        
        # "Copy" to target (in real implementation, would need new ID from target's manager)
        target_place = PlaceBuilder(id_manager=target_doc.id_manager).with_name("Source_copy").build()
        
        # Target should use its own ID sequence
        assert target_place.id == "P1"  # Target starts fresh
        
        # Both documents can have objects with same ID (different instances)
        assert source_place.id == target_place.id == "P1"
        assert source_place is not target_place
