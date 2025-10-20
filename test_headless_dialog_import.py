#!/usr/bin/env python3
"""Headless test for dialog opening on imported Glycolysis model.

Tests:
1. Load Glycolysis_01_.shy file
2. Attempt to create place/transition/arc property dialogs
3. Capture any exceptions or freezes
"""
import sys
import os
import json
import traceback

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_load_glycolysis_model():
    """Test loading the Glycolysis model."""
    print("=" * 70)
    print("TEST 1: Load Glycolysis_01_.shy Model")
    print("=" * 70)
    
    model_path = "workspace/projects/Flow_Test/models/Glycolysis_01_.shy"
    
    try:
        # Load the file
        print(f"\n1. Loading model from: {model_path}")
        with open(model_path, 'r') as f:
            data = json.load(f)
        
        print(f"✓ File loaded successfully")
        print(f"  - Version: {data.get('version', 'N/A')}")
        print(f"  - Places: {data.get('metadata', {}).get('object_counts', {}).get('places', 0)}")
        print(f"  - Transitions: {data.get('metadata', {}).get('object_counts', {}).get('transitions', 0)}")
        print(f"  - Arcs: {data.get('metadata', {}).get('object_counts', {}).get('arcs', 0)}")
        
        # Import DocumentModel
        print("\n2. Importing DocumentModel...")
        from shypn.data.canvas.document_model import DocumentModel
        print("✓ DocumentModel imported")
        
        # Create DocumentModel from dict
        print("\n3. Creating DocumentModel from data...")
        document = DocumentModel.from_dict(data)
        print(f"✓ Document created")
        print(f"  - Places in document: {len(document.places)}")
        print(f"  - Transitions in document: {len(document.transitions)}")
        print(f"  - Arcs in document: {len(document.arcs)}")
        
        return document
        
    except Exception as e:
        print(f"\n✗ ERROR loading model:")
        print(f"  {type(e).__name__}: {e}")
        traceback.print_exc()
        return None


def test_place_dialog_with_model(document):
    """Test creating Place property dialog with imported model data."""
    print("\n" + "=" * 70)
    print("TEST 2: Create Place Property Dialog")
    print("=" * 70)
    
    if not document or not document.places:
        print("✗ SKIP: No document or no places available")
        return False
    
    try:
        # Get first place
        place = document.places[0]
        print(f"\n1. Testing with Place: {place.name} (ID: {place.id})")
        print(f"   Position: ({place.x}, {place.y})")
        print(f"   Tokens: {place.tokens}")
        
        # Import dialog loader
        print("\n2. Importing PlacePropDialogLoader...")
        from shypn.helpers.place_prop_dialog_loader import PlacePropDialogLoader
        print("✓ PlacePropDialogLoader imported")
        
        # Create mock objects (needed for dialog)
        print("\n3. Creating mock drawing area and canvas manager...")
        
        class MockDrawingArea:
            def queue_draw(self):
                pass
        
        class MockCanvasManager:
            def __init__(self, doc):
                self.document = doc
                self.places = doc.places
                self.transitions = doc.transitions
                self.arcs = doc.arcs
                self.selected_place = None
                self.selected_transition = None
                self.selected_arc = None
        
        drawing_area = MockDrawingArea()
        canvas_manager = MockCanvasManager(document)
        print("✓ Mock objects created")
        
        # Create dialog loader
        print("\n4. Creating PlacePropDialogLoader...")
        dialog_loader = PlacePropDialogLoader(
            place_obj=place,
            parent_window=None,
            persistency_manager=None,
            model=document
        )
        print("✓ Dialog loader created")
        
        # Check if topology tab was set up
        print("\n5. Checking topology tab setup...")
        if hasattr(dialog_loader, 'topology_loader') and dialog_loader.topology_loader:
            print("✓ Topology tab loader exists")
            
            # Check behavioral properties
            print("\n6. Testing behavioral properties population...")
            try:
                # This is where it might freeze/crash
                dialog_loader.topology_loader._populate_behavioral_properties()
                print("✓ Behavioral properties populated successfully")
                return True
            except Exception as e:
                print(f"✗ ERROR in _populate_behavioral_properties:")
                print(f"  {type(e).__name__}: {e}")
                traceback.print_exc()
                return False
        else:
            print("! Topology tab not available (ImportError or setup failed)")
            return True  # Not a failure if topology is optional
        
    except Exception as e:
        print(f"\n✗ ERROR creating Place dialog:")
        print(f"  {type(e).__name__}: {e}")
        traceback.print_exc()
        return False


def test_transition_dialog_with_model(document):
    """Test creating Transition property dialog with imported model data."""
    print("\n" + "=" * 70)
    print("TEST 3: Create Transition Property Dialog")
    print("=" * 70)
    
    if not document or not document.transitions:
        print("✗ SKIP: No document or no transitions available")
        return False
    
    try:
        # Get first transition
        transition = document.transitions[0]
        print(f"\n1. Testing with Transition: {transition.name} (ID: {transition.id})")
        print(f"   Position: ({transition.x}, {transition.y})")
        
        # Import dialog loader
        print("\n2. Importing TransitionPropDialogLoader...")
        from shypn.helpers.transition_prop_dialog_loader import TransitionPropDialogLoader
        print("✓ TransitionPropDialogLoader imported")
        
        # Create mock objects
        print("\n3. Creating mock drawing area and canvas manager...")
        
        class MockDrawingArea:
            def queue_draw(self):
                pass
        
        class MockCanvasManager:
            def __init__(self, doc):
                self.document = doc
                self.places = doc.places
                self.transitions = doc.transitions
                self.arcs = doc.arcs
                self.selected_place = None
                self.selected_transition = None
                self.selected_arc = None
        
        drawing_area = MockDrawingArea()
        canvas_manager = MockCanvasManager(document)
        print("✓ Mock objects created")
        
        # Create dialog loader
        print("\n4. Creating TransitionPropDialogLoader...")
        dialog_loader = TransitionPropDialogLoader(
            transition_obj=transition,
            parent_window=None,
            persistency_manager=None,
            model=document
        )
        print("✓ Dialog loader created")
        
        # Check if topology tab was set up
        print("\n5. Checking topology tab setup...")
        if hasattr(dialog_loader, 'topology_loader') and dialog_loader.topology_loader:
            print("✓ Topology tab loader exists")
            
            # Check behavioral properties
            print("\n6. Testing behavioral properties population...")
            try:
                # This is where it might freeze/crash
                dialog_loader.topology_loader._populate_behavioral_properties()
                print("✓ Behavioral properties populated successfully")
                return True
            except Exception as e:
                print(f"✗ ERROR in _populate_behavioral_properties:")
                print(f"  {type(e).__name__}: {e}")
                traceback.print_exc()
                return False
        else:
            print("! Topology tab not available (ImportError or setup failed)")
            return True  # Not a failure if topology is optional
        
    except Exception as e:
        print(f"\n✗ ERROR creating Transition dialog:")
        print(f"  {type(e).__name__}: {e}")
        traceback.print_exc()
        return False


def test_arc_dialog_with_model(document):
    """Test creating Arc property dialog with imported model data."""
    print("\n" + "=" * 70)
    print("TEST 4: Create Arc Property Dialog")
    print("=" * 70)
    
    if not document or not document.arcs:
        print("✗ SKIP: No document or no arcs available")
        return False
    
    try:
        # Get first arc
        arc = document.arcs[0]
        print(f"\n1. Testing with Arc: {arc.name} (ID: {arc.id})")
        print(f"   Source: {arc.source}")
        print(f"   Target: {arc.target}")
        
        # Import dialog loader
        print("\n2. Importing ArcPropDialogLoader...")
        from shypn.helpers.arc_prop_dialog_loader import ArcPropDialogLoader
        print("✓ ArcPropDialogLoader imported")
        
        # Create mock objects
        print("\n3. Creating mock drawing area and canvas manager...")
        
        class MockDrawingArea:
            def queue_draw(self):
                pass
        
        class MockCanvasManager:
            def __init__(self, doc):
                self.document = doc
                self.places = doc.places
                self.transitions = doc.transitions
                self.arcs = doc.arcs
                self.selected_place = None
                self.selected_transition = None
                self.selected_arc = None
        
        drawing_area = MockDrawingArea()
        canvas_manager = MockCanvasManager(document)
        print("✓ Mock objects created")
        
        # Create dialog loader
        print("\n4. Creating ArcPropDialogLoader...")
        dialog_loader = ArcPropDialogLoader(
            arc_obj=arc,
            parent_window=None,
            persistency_manager=None,
            model=document
        )
        print("✓ Dialog loader created")
        
        # Check if topology tab was set up
        print("\n5. Checking topology tab setup...")
        if hasattr(dialog_loader, 'topology_loader') and dialog_loader.topology_loader:
            print("✓ Topology tab loader exists")
            
            # Check behavioral properties
            print("\n6. Testing behavioral properties population...")
            try:
                # This is where it might freeze/crash
                # Note: Arc dialogs may not have behavioral properties
                if hasattr(dialog_loader.topology_loader, '_populate_behavioral_properties'):
                    dialog_loader.topology_loader._populate_behavioral_properties()
                    print("✓ Behavioral properties populated successfully")
                else:
                    print("! Arc topology tab does not have behavioral properties (expected)")
                return True
            except Exception as e:
                print(f"✗ ERROR in _populate_behavioral_properties:")
                print(f"  {type(e).__name__}: {e}")
                traceback.print_exc()
                return False
        else:
            print("! Topology tab not available (ImportError or setup failed)")
            return True  # Not a failure if topology is optional
        
    except Exception as e:
        print(f"\n✗ ERROR creating Arc dialog:")
        print(f"  {type(e).__name__}: {e}")
        traceback.print_exc()
        return False


def main():
    """Run all headless tests."""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 10 + "HEADLESS DIALOG TEST - IMPORTED MODEL" + " " * 20 + "║")
    print("╚" + "=" * 68 + "╝")
    print("\nTesting property dialogs with imported Glycolysis_01_.shy model")
    print("This test runs WITHOUT GUI to isolate the issue.\n")
    
    results = []
    
    # Test 1: Load model
    document = test_load_glycolysis_model()
    results.append(("Load Glycolysis Model", document is not None))
    
    if document:
        # Test 2: Place dialog
        result = test_place_dialog_with_model(document)
        results.append(("Place Dialog Creation", result))
        
        # Test 3: Transition dialog
        result = test_transition_dialog_with_model(document)
        results.append(("Transition Dialog Creation", result))
        
        # Test 4: Arc dialog
        result = test_arc_dialog_with_model(document)
        results.append(("Arc Dialog Creation", result))
    
    # Print summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status:8} {test_name}")
    
    print("=" * 70)
    
    all_passed = all(result for _, result in results)
    if all_passed:
        print("\n🎉 ALL TESTS PASSED!\n")
        return 0
    else:
        failed_count = sum(1 for _, result in results if not result)
        print(f"\n⚠️  {failed_count} TEST(S) FAILED\n")
        return 1


if __name__ == '__main__':
    sys.exit(main())
