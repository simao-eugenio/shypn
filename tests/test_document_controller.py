"""Tests for DocumentController.

Tests Petri net object management, document state, and metadata.
"""

import sys
from pathlib import Path
from datetime import datetime

# Add src to path
src_path = Path(__file__).parent.parent / 'src'
sys.path.insert(0, str(src_path))

from shypn.core.controllers.document_controller import DocumentController
from shypn.netobjs import Place, Transition, Arc


class TestDocumentInitialization:
    """Test document controller initialization."""
    
    def test_default_initialization(self):
        """Should initialize with default values."""
        dc = DocumentController()
        
        assert dc.filename == "default"
        assert dc.modified == False
        assert len(dc.places) == 0
        assert len(dc.transitions) == 0
        assert len(dc.arcs) == 0
        assert dc._next_place_id == 1
        assert dc._next_transition_id == 1
        assert dc._next_arc_id == 1
        assert dc.created_at is not None
        assert dc.modified_at is None
        
    def test_custom_filename(self):
        """Should accept custom filename."""
        dc = DocumentController(filename="test_model")
        
        assert dc.filename == "test_model"


class TestObjectCreation:
    """Test object creation with auto ID generation."""
    
    def test_add_place(self):
        """Should create place with auto-incremented ID."""
        dc = DocumentController()
        
        p1 = dc.add_place(100, 200)
        
        assert p1 is not None
        assert p1.id == 1
        assert p1.name == "P1"
        assert p1.x == 100
        assert p1.y == 200
        assert len(dc.places) == 1
        assert dc._next_place_id == 2
        
    def test_add_multiple_places(self):
        """Should create places with incrementing IDs."""
        dc = DocumentController()
        
        p1 = dc.add_place(0, 0)
        p2 = dc.add_place(100, 0)
        p3 = dc.add_place(200, 0)
        
        assert p1.id == 1
        assert p2.id == 2
        assert p3.id == 3
        assert len(dc.places) == 3
        
    def test_add_transition(self):
        """Should create transition with auto-incremented ID."""
        dc = DocumentController()
        
        t1 = dc.add_transition(50, 50)
        
        assert t1 is not None
        assert t1.id == 1
        assert t1.name == "T1"
        assert t1.x == 50
        assert t1.y == 50
        assert len(dc.transitions) == 1
        assert dc._next_transition_id == 2
        
    def test_add_multiple_transitions(self):
        """Should create transitions with incrementing IDs."""
        dc = DocumentController()
        
        t1 = dc.add_transition(0, 0)
        t2 = dc.add_transition(100, 0)
        
        assert t1.id == 1
        assert t2.id == 2
        assert len(dc.transitions) == 2
        
    def test_add_arc(self):
        """Should create arc with auto-incremented ID."""
        dc = DocumentController()
        
        p1 = dc.add_place(0, 0)
        t1 = dc.add_transition(100, 0)
        a1 = dc.add_arc(p1, t1)
        
        assert a1 is not None
        assert a1.id == 1
        assert a1.name == "A1"
        assert a1.source == p1
        assert a1.target == t1
        assert len(dc.arcs) == 1
        assert dc._next_arc_id == 2
        
    def test_add_multiple_arcs(self):
        """Should create arcs with incrementing IDs."""
        dc = DocumentController()
        
        p1 = dc.add_place(0, 0)
        t1 = dc.add_transition(50, 0)
        p2 = dc.add_place(100, 0)
        
        a1 = dc.add_arc(p1, t1)
        a2 = dc.add_arc(t1, p2)
        
        assert a1.id == 1
        assert a2.id == 2
        assert len(dc.arcs) == 2
        
    def test_creation_marks_modified(self):
        """Creating objects should mark document as modified."""
        dc = DocumentController()
        assert dc.modified == False
        
        dc.add_place(0, 0)
        
        assert dc.modified == True
        assert dc.modified_at is not None


class TestObjectRemoval:
    """Test object removal operations."""
    
    def test_remove_place(self):
        """Should remove place from collection."""
        dc = DocumentController()
        p1 = dc.add_place(0, 0)
        
        dc.remove_place(p1)
        
        assert len(dc.places) == 0
        
    def test_remove_place_cascades_arcs(self):
        """Removing place should remove connected arcs."""
        dc = DocumentController()
        
        p1 = dc.add_place(0, 0)
        t1 = dc.add_transition(50, 0)
        p2 = dc.add_place(100, 0)
        
        a1 = dc.add_arc(p1, t1)
        a2 = dc.add_arc(t1, p2)
        
        # Remove p1
        dc.remove_place(p1)
        
        # p1 should be gone
        assert len(dc.places) == 1
        assert p2 in dc.places
        
        # a1 should be removed (connected to p1)
        assert len(dc.arcs) == 1
        assert a2 in dc.arcs
        assert a1 not in dc.arcs
        
    def test_remove_transition(self):
        """Should remove transition from collection."""
        dc = DocumentController()
        t1 = dc.add_transition(0, 0)
        
        dc.remove_transition(t1)
        
        assert len(dc.transitions) == 0
        
    def test_remove_transition_cascades_arcs(self):
        """Removing transition should remove connected arcs."""
        dc = DocumentController()
        
        p1 = dc.add_place(0, 0)
        t1 = dc.add_transition(50, 0)
        p2 = dc.add_place(100, 0)
        
        a1 = dc.add_arc(p1, t1)
        a2 = dc.add_arc(t1, p2)
        
        # Remove t1
        dc.remove_transition(t1)
        
        # t1 should be gone
        assert len(dc.transitions) == 0
        
        # Both arcs should be removed (both connected to t1)
        assert len(dc.arcs) == 0
        
    def test_remove_arc(self):
        """Should remove arc from collection."""
        dc = DocumentController()
        
        p1 = dc.add_place(0, 0)
        t1 = dc.add_transition(50, 0)
        a1 = dc.add_arc(p1, t1)
        
        dc.remove_arc(a1)
        
        assert len(dc.arcs) == 0
        # Nodes should remain
        assert len(dc.places) == 1
        assert len(dc.transitions) == 1
        
    def test_removal_marks_modified(self):
        """Removing objects should mark document as modified."""
        dc = DocumentController()
        p1 = dc.add_place(0, 0)
        dc.modified = False  # Reset flag
        
        dc.remove_place(p1)
        
        assert dc.modified == True


class TestArcReplacement:
    """Test arc replacement for transformations."""
    
    def test_replace_arc(self):
        """Should replace arc in collection."""
        dc = DocumentController()
        
        p1 = dc.add_place(0, 0)
        t1 = dc.add_transition(50, 0)
        old_arc = dc.add_arc(p1, t1)
        
        # Create new arc (simulating transformation)
        new_arc = Arc(p1, t1, old_arc.id, old_arc.name)
        
        dc.replace_arc(old_arc, new_arc)
        
        assert len(dc.arcs) == 1
        assert dc.arcs[0] == new_arc
        assert old_arc not in dc.arcs
        
    def test_replace_nonexistent_arc(self):
        """Should handle replacing arc that doesn't exist."""
        dc = DocumentController()
        
        p1 = dc.add_place(0, 0)
        t1 = dc.add_transition(50, 0)
        fake_arc = Arc(p1, t1, 999, "A999")
        new_arc = Arc(p1, t1, 999, "A999")
        
        # Should not raise exception
        dc.replace_arc(fake_arc, new_arc)


class TestObjectLookup:
    """Test object lookup operations."""
    
    def test_get_all_objects(self):
        """Should return all objects in rendering order."""
        dc = DocumentController()
        
        p1 = dc.add_place(0, 0)
        t1 = dc.add_transition(50, 0)
        p2 = dc.add_place(100, 0)
        a1 = dc.add_arc(p1, t1)
        a2 = dc.add_arc(t1, p2)
        
        objects = dc.get_all_objects()
        
        # Should have all 5 objects
        assert len(objects) == 5
        
        # Rendering order: arcs first, then places and transitions
        assert objects[0] in [a1, a2]  # Arcs first
        assert objects[1] in [a1, a2]
        assert objects[2] in [p1, p2, t1]  # Then nodes
        assert objects[3] in [p1, p2, t1]
        assert objects[4] in [p1, p2, t1]
        
    def test_find_object_at_position(self):
        """Should find object at given position."""
        dc = DocumentController()
        
        p1 = dc.add_place(0, 0, radius=20)
        t1 = dc.add_transition(100, 0, width=40, height=40)
        
        # Should find place at its center
        found = dc.find_object_at_position(0, 0)
        assert found == p1
        
        # Should find transition at its center
        found = dc.find_object_at_position(100, 0)
        assert found == t1
        
        # Should return None for empty position
        found = dc.find_object_at_position(500, 500)
        assert found is None
        
    def test_get_object_count(self):
        """Should return object counts by type."""
        dc = DocumentController()
        
        dc.add_place(0, 0)
        dc.add_place(50, 0)
        dc.add_transition(100, 0)
        
        counts = dc.get_object_count()
        
        assert counts['places'] == 2
        assert counts['transitions'] == 1
        assert counts['arcs'] == 0


class TestDocumentOperations:
    """Test document-level operations."""
    
    def test_create_new_document(self):
        """Should reset to new document state."""
        dc = DocumentController()
        
        # Add some objects
        dc.add_place(0, 0)
        dc.add_transition(50, 0)
        
        # Create new document
        dc.create_new_document(filename="new_model")
        
        assert dc.filename == "new_model"
        assert dc.modified == False
        assert len(dc.places) == 0
        assert len(dc.transitions) == 0
        assert len(dc.arcs) == 0
        assert dc._next_place_id == 1
        assert dc._next_transition_id == 1
        assert dc._next_arc_id == 1
        
    def test_clear_all_objects(self):
        """Should remove all objects and reset counters."""
        dc = DocumentController()
        
        dc.add_place(0, 0)
        dc.add_place(50, 0)
        dc.add_transition(100, 0)
        
        dc.clear_all_objects()
        
        assert len(dc.places) == 0
        assert len(dc.transitions) == 0
        assert len(dc.arcs) == 0
        assert dc._next_place_id == 1
        assert dc._next_transition_id == 1
        
    def test_create_test_objects(self):
        """Should create test Petri net."""
        dc = DocumentController()
        
        dc.create_test_objects()
        
        # Should have 2 places, 1 transition, 2 arcs
        assert len(dc.places) == 2
        assert len(dc.transitions) == 1
        assert len(dc.arcs) == 2
        
        # Places should have labels and tokens
        assert dc.places[0].label == "P1"
        assert dc.places[0].tokens == 2


class TestDocumentMetadata:
    """Test document metadata management."""
    
    def test_mark_modified(self):
        """Should mark document as modified."""
        dc = DocumentController()
        assert dc.modified == False
        
        dc.mark_modified()
        
        assert dc.modified == True
        assert dc.modified_at is not None
        
    def test_mark_clean(self):
        """Should mark document as clean."""
        dc = DocumentController()
        dc.modified = True
        
        dc.mark_clean()
        
        assert dc.modified == False
        
    def test_set_filename(self):
        """Should set filename and mark modified."""
        dc = DocumentController()
        dc.modified = False
        
        dc.set_filename("new_name")
        
        assert dc.filename == "new_name"
        assert dc.modified == True
        
    def test_set_same_filename_no_change(self):
        """Setting same filename should not mark modified."""
        dc = DocumentController(filename="test")
        dc.modified = False
        
        dc.set_filename("test")
        
        # Should not change
        assert dc.modified == False
        
    def test_is_default_filename(self):
        """Should detect default filename."""
        dc = DocumentController()
        
        assert dc.is_default_filename() == True
        
        dc.set_filename("custom")
        
        assert dc.is_default_filename() == False
        
    def test_get_document_info(self):
        """Should return document info dict."""
        dc = DocumentController(filename="test_doc")
        dc.add_place(0, 0)
        dc.add_transition(50, 0)
        
        info = dc.get_document_info()
        
        assert info['filename'] == "test_doc"
        assert info['modified'] == True
        assert info['created_at'] is not None
        assert 'object_count' in info
        assert info['object_count']['places'] == 1
        assert info['object_count']['transitions'] == 1


class TestRedrawManagement:
    """Test redraw flag management."""
    
    def test_initial_needs_redraw(self):
        """Should initially need redraw."""
        dc = DocumentController()
        
        assert dc.needs_redraw() == True
        
    def test_mark_dirty(self):
        """Should mark as needing redraw."""
        dc = DocumentController()
        dc._needs_redraw = False
        
        dc.mark_dirty()
        
        assert dc.needs_redraw() == True
        
    def test_mark_redraw_clean(self):
        """Should mark as drawn."""
        dc = DocumentController()
        
        dc.mark_redraw_clean()
        
        assert dc.needs_redraw() == False
        
    def test_operations_mark_dirty(self):
        """Operations should mark dirty."""
        dc = DocumentController()
        
        # Create object marks dirty
        dc.mark_redraw_clean()
        assert dc.needs_redraw() == False
        p1 = dc.add_place(0, 0)
        assert dc.needs_redraw() == True
        
        # Remove object marks dirty
        dc.mark_redraw_clean()
        assert dc.needs_redraw() == False
        assert len(dc.places) > 0, "Should have at least one place"
        dc.remove_place(p1)
        assert dc.needs_redraw() == True


class TestChangeCallback:
    """Test change callback system."""
    
    def test_set_change_callback(self):
        """Should set callback on controller."""
        dc = DocumentController()
        
        callback_called = []
        def callback():
            callback_called.append(True)
        
        dc.set_change_callback(callback)
        
        assert dc._on_change_callback == callback
        
    def test_callback_applied_to_new_objects(self):
        """New objects should get the callback."""
        dc = DocumentController()
        
        callback_called = []
        def callback():
            callback_called.append(True)
        
        dc.set_change_callback(callback)
        
        # Create object - should have callback
        p1 = dc.add_place(0, 0)
        assert p1.on_changed == callback
        
    def test_callback_applied_to_existing_objects(self):
        """Setting callback should update existing objects."""
        dc = DocumentController()
        
        # Create objects first
        p1 = dc.add_place(0, 0)
        t1 = dc.add_transition(50, 0)
        
        # Then set callback
        callback_called = []
        def callback():
            callback_called.append(True)
        
        dc.set_change_callback(callback)
        
        # Existing objects should have callback
        assert p1.on_changed == callback
        assert t1.on_changed == callback


def run_all_tests():
    """Run all document controller tests."""
    test_classes = [
        TestDocumentInitialization(),
        TestObjectCreation(),
        TestObjectRemoval(),
        TestArcReplacement(),
        TestObjectLookup(),
        TestDocumentOperations(),
        TestDocumentMetadata(),
        TestRedrawManagement(),
        TestChangeCallback(),
    ]
    
    for test_class in test_classes:
        class_name = test_class.__class__.__name__
        print(f"\nRunning {class_name}...")
        
        # Get all test methods
        test_methods = [method for method in dir(test_class) 
                       if method.startswith('test_')]
        
        for method_name in test_methods:
            try:
                method = getattr(test_class, method_name)
                method()
                print(f"  ✓ {method_name}")
            except AssertionError as e:
                print(f"  ✗ {method_name}: {e}")
                return False
            except Exception as e:
                print(f"  ✗ {method_name}: Unexpected error: {e}")
                import traceback
                traceback.print_exc()
                return False
    
    print("\n" + "="*60)
    print("✅ All document controller tests passed!")
    print("="*60)
    return True


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
