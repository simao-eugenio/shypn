#!/usr/bin/env python3
"""Quick test: Dialog should open instantly on imported Glycolysis model."""
import sys
import os
import json
import time

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def main():
    print("\n" + "="*70)
    print("QUICK TEST: Dialog Opening Speed on Imported Model")
    print("="*70)
    
    model_path = "workspace/projects/Flow_Test/models/Glycolysis_01_.shy"
    
    # Load model
    print(f"\n1. Loading {model_path}...")
    with open(model_path, 'r') as f:
        data = json.load(f)
    
    from shypn.data.canvas.document_model import DocumentModel
    document = DocumentModel.from_dict(data)
    print(f"✓ Loaded: {len(document.places)} places, {len(document.transitions)} transitions, {len(document.arcs)} arcs")
    
    # Test Place dialog
    print("\n2. Creating Place dialog...")
    place = document.places[0]
    print(f"   Place: {place.name} (ID: {place.id})")
    
    from shypn.helpers.place_prop_dialog_loader import PlacePropDialogLoader
    
    start = time.time()
    dialog_loader = PlacePropDialogLoader(
        place_obj=place,
        parent_window=None,
        persistency_manager=None,
        model=document
    )
    elapsed = time.time() - start
    
    print(f"✓ Dialog created in {elapsed:.3f} seconds")
    
    # Check result
    if elapsed < 1.0:
        print(f"\n✅ SUCCESS! Dialog opens instantly ({elapsed:.3f}s < 1.0s)")
        print("   Fix verified: Removing populate() call prevents freeze")
        return 0
    else:
        print(f"\n⚠️  SLOW: Dialog took {elapsed:.3f}s (expected < 1.0s)")
        return 1

if __name__ == '__main__':
    sys.exit(main())
