#!/usr/bin/env python3
"""
Test script to verify rendering after file operations.
Run this to check if models are being rendered correctly.
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

print("=" * 80)
print("RENDERING TEST - Phase 5 Side Effects Check")
print("=" * 80)

# Step 1: Test that load_objects works
print("\n[1/3] Testing load_objects() functionality...")
try:
    from shypn.data.model_canvas_manager import ModelCanvasManager
    from shypn.netobjs import Place, Transition, Arc
    
    manager = ModelCanvasManager(2000, 2000, 'test')
    
    p1 = Place(100, 100, 1, 'P1')
    p2 = Place(200, 100, 2, 'P2')
    t1 = Transition(150, 100, 1, 'T1')
    a1 = Arc(p1, t1, 1, 'A1')
    
    manager.load_objects(places=[p1, p2], transitions=[t1], arcs=[a1])
    
    assert len(manager.places) == 2, f"Expected 2 places, got {len(manager.places)}"
    assert len(manager.transitions) == 1, f"Expected 1 transition, got {len(manager.transitions)}"
    assert len(manager.arcs) == 1, f"Expected 1 arc, got {len(manager.arcs)}"
    
    all_objs = manager.get_all_objects()
    assert len(all_objs) == 4, f"Expected 4 objects total, got {len(all_objs)}"
    
    print("✓ load_objects() works correctly")
    print(f"  - Loaded {len(manager.places)} places")
    print(f"  - Loaded {len(manager.transitions)} transitions") 
    print(f"  - Loaded {len(manager.arcs)} arcs")
    print(f"  - get_all_objects() returns {len(all_objs)} objects")
    
except Exception as e:
    print(f"✗ load_objects() FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Step 2: Test file loading
print("\n[2/3] Testing file loading...")
try:
    from shypn.file.netobj_persistency import NetObjPersistency
    from pathlib import Path
    
    # Find a test .shy file
    test_files = list(Path('models').glob('*.shy'))
    if not test_files:
        test_files = list(Path('data').rglob('*.shy'))
    
    if test_files:
        test_file = test_files[0]
        print(f"  - Found test file: {test_file}")
        
        persistency = NetObjPersistency()
        document = persistency.load_from_file(str(test_file))
        
        if document:
            print(f"✓ File loaded successfully")
            print(f"  - {len(document.places)} places")
            print(f"  - {len(document.transitions)} transitions")
            print(f"  - {len(document.arcs)} arcs")
        else:
            print("✗ File loading returned None")
    else:
        print("⚠ No test .shy files found, skipping file load test")
        
except Exception as e:
    print(f"✗ File loading FAILED: {e}")
    import traceback
    traceback.print_exc()

# Step 3: Instructions for manual testing
print("\n[3/3] Manual Testing Required")
print("-" * 80)
print("Please test the following operations in the GUI:")
print()
print("1. OPEN FILE TEST:")
print("   - File → Open")
print("   - Select a .shy file from models/ directory")
print("   - Check if model renders on canvas")
print()
print("2. SBML IMPORT TEST:")
print("   - Pathways → SBML Import")
print("   - Select an SBML file or use BioModels")
print("   - Click Parse File")
print("   - Check if model renders on canvas")
print()
print("3. KEGG IMPORT TEST:")
print("   - Pathways → KEGG Import  ")
print("   - Enter pathway ID (e.g., hsa00010)")
print("   - Click Fetch & Parse")
print("   - Check if model renders on canvas")
print()
print("Expected behavior:")
print("  ✓ Models should render on canvas (places, transitions, arcs visible)")
print("  ✓ No GTK-CRITICAL warnings in console")
print("  ✓ Canvas should zoom/fit imported models")
print()
print("If models DON'T render:")
print("  1. Check console for errors")
print("  2. Try manually creating a place (should appear)")
print("  3. Check if zoom/pan works")
print("  4. Report which import path fails")
print()
print("=" * 80)
print("Start the application with: python3 src/shypn.py")
print("=" * 80)
