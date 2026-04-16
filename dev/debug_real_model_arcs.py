#!/usr/bin/env python3
"""Debug how arcs are structured when loaded from actual model files."""

import sys
import os
sys.path.insert(0, os.path.abspath('src'))

import json
from shypn.data.canvas.document_model import DocumentModel

def debug_model_arcs():
    print("Debugging Arc Structure in Loaded Models\n")
    print("=" * 70)
    
    # Find a model file with adaptive transitions
    workspace_dir = "workspace/projects"
    
    # Look for any .json model files
    import glob
    model_files = []
    for root, dirs, files in os.walk(workspace_dir):
        for file in files:
            if file.endswith('.json') and 'model' in file.lower():
                model_files.append(os.path.join(root, file))
    
    if not model_files:
        print("No model files found in workspace")
        return
    
    print(f"Found {len(model_files)} model files")
    print(f"Testing first model: {model_files[0]}\n")
    
    # Load model using DocumentModel
    model = DocumentModel.load_from_file(model_files[0])
    
    print(f"Model loaded: {model.name if hasattr(model, 'name') else 'unnamed'}")
    print(f"Number of arcs: {len(model.arcs)}")
    print(f"Type of model.arcs: {type(model.arcs)}")
    
    # Check arc structure
    if isinstance(model.arcs, dict):
        arcs = list(model.arcs.values())
    else:
        arcs = list(model.arcs)
    
    if arcs:
        print(f"\nInspecting first arc:")
        first_arc = arcs[0]
        print(f"  Arc ID: {first_arc.id}")
        print(f"  Arc name: {first_arc.name}")
        print(f"  Arc type: {type(first_arc)}")
        print(f"\n  Source:")
        print(f"    - Type: {type(first_arc.source)}")
        print(f"    - Value: {first_arc.source}")
        print(f"    - Has .id attr: {hasattr(first_arc.source, 'id')}")
        if hasattr(first_arc.source, 'id'):
            print(f"    - source.id: {first_arc.source.id}")
        
        print(f"\n  Target:")
        print(f"    - Type: {type(first_arc.target)}")
        print(f"    - Value: {first_arc.target}")
        print(f"    - Has .id attr: {hasattr(first_arc.target, 'id')}")
        if hasattr(first_arc.target, 'id'):
            print(f"    - target.id: {first_arc.target.id}")
        
        print(f"\n  Properties:")
        print(f"    - hasattr 'source_id': {hasattr(first_arc, 'source_id')}")
        print(f"    - hasattr 'target_id': {hasattr(first_arc, 'target_id')}")
        
        if hasattr(first_arc, 'source_id'):
            try:
                print(f"    - arc.source_id property: {first_arc.source_id}")
            except Exception as e:
                print(f"    - arc.source_id ERROR: {e}")
        
        if hasattr(first_arc, 'target_id'):
            try:
                print(f"    - arc.target_id property: {first_arc.target_id}")
            except Exception as e:
                print(f"    - arc.target_id ERROR: {e}")
    
    # Find adaptive transitions
    print("\n" + "=" * 70)
    print("Searching for adaptive transitions:")
    
    if isinstance(model.transitions, dict):
        transitions = model.transitions.values()
    else:
        transitions = model.transitions
    
    adaptive_transitions = [t for t in transitions if t.transition_type == 'adaptive']
    
    if not adaptive_transitions:
        print("  No adaptive transitions found")
        return
    
    print(f"  Found {len(adaptive_transitions)} adaptive transitions")
    
    for trans in adaptive_transitions[:2]:  # Check first 2
        print(f"\n  Transition: {trans.name} (id={trans.id})")
        
        # Try to get input/output arcs
        input_arcs = []
        output_arcs = []
        
        for arc in arcs:
            # Check if target matches transition
            target_matches = False
            source_matches = False
            
            # Try different comparison methods
            try:
                if isinstance(arc.target, str):
                    target_matches = (arc.target == trans.id)
                elif hasattr(arc.target, 'id'):
                    target_matches = (arc.target.id == trans.id)
                elif arc.target == trans:
                    target_matches = True
            except:
                pass
            
            try:
                if isinstance(arc.source, str):
                    source_matches = (arc.source == trans.id)
                elif hasattr(arc.source, 'id'):
                    source_matches = (arc.source.id == trans.id)
                elif arc.source == trans:
                    source_matches = True
            except:
                pass
            
            if target_matches:
                input_arcs.append(arc)
            if source_matches:
                output_arcs.append(arc)
        
        print(f"    Input arcs found: {len(input_arcs)}")
        print(f"    Output arcs found: {len(output_arcs)}")
        
        if input_arcs:
            print(f"    First input arc: {input_arcs[0].name}")
        if output_arcs:
            print(f"    First output arc: {output_arcs[0].name}")


if __name__ == "__main__":
    try:
        debug_model_arcs()
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
