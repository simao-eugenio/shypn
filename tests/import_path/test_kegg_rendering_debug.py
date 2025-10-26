#!/usr/bin/env python3
"""Debug KEGG import rendering issues.

This script helps diagnose why KEGG pathways might not render after import.
Run after attempting a KEGG import to see what happened.
"""
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

def check_kegg_import_code():
    """Check KEGG import code for rendering-related patterns."""
    print("=" * 60)
    print("KEGG IMPORT RENDERING DIAGNOSTIC")
    print("=" * 60)
    
    kegg_file = os.path.join(
        os.path.dirname(__file__), 
        '..', '..', 
        'src', 'shypn', 'helpers', 'kegg_import_panel.py'
    )
    
    with open(kegg_file, 'r') as f:
        content = f.read()
    
    print("\n1. Checking queue_draw() call:")
    if 'drawing_area.queue_draw()' in content:
        print("   ✓ queue_draw() call present")
        # Find where it's called
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            if 'drawing_area.queue_draw()' in line:
                print(f"   ✓ Found at line {i}")
                # Show context
                print(f"\n   Context (5 lines before):")
                for j in range(max(0, i-6), i-1):
                    print(f"   {j+1}: {lines[j]}")
                print(f"   → {i}: {lines[i-1]}")
                print(f"\n   Context (5 lines after):")
                for j in range(i, min(len(lines), i+5)):
                    print(f"   {j+1}: {lines[j]}")
                break
    else:
        print("   ✗ queue_draw() call NOT FOUND")
    
    print("\n2. Checking load_objects call:")
    if 'manager.load_objects(' in content:
        print("   ✓ load_objects() call present")
    else:
        print("   ✗ load_objects() call NOT FOUND")
    
    print("\n3. Checking fit_to_page call:")
    if 'manager.fit_to_page(' in content:
        print("   ✓ fit_to_page() call present")
        if 'deferred=True' in content:
            print("   ℹ Uses deferred=True (async operation)")
    else:
        print("   ✗ fit_to_page() call NOT FOUND")
    
    print("\n4. Checking object verification:")
    if 'manager.places' in content:
        print("   ✓ Accesses manager.places")
    else:
        print("   ⚠ Does not access manager.places directly")
    
    print("\n5. Checking operation order:")
    # Find the order of key operations
    operations = [
        ('load_objects', 'manager.load_objects('),
        ('set_change_callback', 'set_change_callback'),
        ('fit_to_page', 'manager.fit_to_page('),
        ('mark_as_imported', 'mark_as_imported'),
        ('queue_draw', 'drawing_area.queue_draw()'),
    ]
    
    positions = {}
    for op_name, op_pattern in operations:
        pos = content.find(op_pattern)
        if pos != -1:
            positions[op_name] = pos
    
    if positions:
        print("   Operation order:")
        for op_name, pos in sorted(positions.items(), key=lambda x: x[1]):
            print(f"   {pos:6d}: {op_name}")
    
    print("\n6. Comparing with SBML import:")
    sbml_file = os.path.join(
        os.path.dirname(__file__), 
        '..', '..', 
        'src', 'shypn', 'helpers', 'sbml_import_panel.py'
    )
    
    if os.path.exists(sbml_file):
        with open(sbml_file, 'r') as f:
            sbml_content = f.read()
        
        # Check SBML's queue_draw position
        sbml_operations = {}
        for op_name, op_pattern in operations:
            pos = sbml_content.find(op_pattern)
            if pos != -1:
                sbml_operations[op_name] = pos
        
        if sbml_operations and positions:
            print("   SBML operation order:")
            for op_name, pos in sorted(sbml_operations.items(), key=lambda x: x[1]):
                print(f"   {pos:6d}: {op_name}")
            
            # Compare
            print("\n   Comparison:")
            kegg_order = [k for k, v in sorted(positions.items(), key=lambda x: x[1])]
            sbml_order = [k for k, v in sorted(sbml_operations.items(), key=lambda x: x[1])]
            
            if kegg_order == sbml_order:
                print("   ✓ KEGG and SBML have SAME operation order")
            else:
                print("   ⚠ KEGG and SBML have DIFFERENT operation order")
                print(f"   KEGG: {' → '.join(kegg_order)}")
                print(f"   SBML: {' → '.join(sbml_order)}")


def suggest_fixes():
    """Suggest potential fixes based on common issues."""
    print("\n" + "=" * 60)
    print("COMMON RENDERING ISSUES & FIXES")
    print("=" * 60)
    
    print("\n1. Objects loaded but not visible:")
    print("   → Ensure queue_draw() is called AFTER load_objects()")
    print("   → Check if objects have valid coordinates")
    print("   → Verify zoom/pan state is correct")
    
    print("\n2. Canvas appears empty:")
    print("   → Check console for 'Objects loaded successfully!' message")
    print("   → Verify manager.places/transitions/arcs are not empty")
    print("   → Try manually zooming out (objects might be off-screen)")
    
    print("\n3. Deferred operations:")
    print("   → fit_to_page(deferred=True) is async")
    print("   → queue_draw() should be called AFTER async operations")
    print("   → Consider using deferred=False for immediate effect")
    
    print("\n4. Debug steps:")
    print("   → Check console output during import")
    print("   → Look for 'Verifying loaded objects in manager...'")
    print("   → Check if counts are > 0")
    print("   → Look for 'Triggering canvas redraw...'")


if __name__ == '__main__':
    check_kegg_import_code()
    suggest_fixes()
    
    print("\n" + "=" * 60)
    print("NEXT STEPS")
    print("=" * 60)
    print("\n1. Try importing a KEGG pathway (e.g., hsa00010)")
    print("2. Watch console output for debugging messages")
    print("3. If still not rendering, check:")
    print("   - Are objects loaded? (check counts in console)")
    print("   - Is drawing_area valid?")
    print("   - Is manager valid?")
    print("   - Does manual zoom/pan show objects?")
    print("\n" + "=" * 60)
