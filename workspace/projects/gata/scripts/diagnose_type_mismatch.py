#!/usr/bin/env python3
"""Diagnose _get_behavior type mismatch issue."""

import sys
import os
import json

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))))
sys.path.insert(0, os.path.join(project_root, 'src'))

def main():
    model_path = os.path.join(os.path.dirname(__file__), '..', 'models', 'adaptive_test_simple.shy')
    
    with open(model_path, 'r') as f:
        model_data = json.load(f)
    
    from shypn.data.canvas.document_model import DocumentModel
    from shypn.engine.simulation import SimulationController
    
    document = DocumentModel.from_dict(model_data)
    controller = SimulationController(document, verbose=False)
    controller._update_enablement_states()
    
    print("="*80)
    print("DIAGNOSING TYPE MISMATCH IN _get_behavior()")
    print("="*80)
    print()
    
    for trans in document.transitions:
        print(f"{trans.name} (ID={trans.id}):")
        print(f"  current transition_type: '{trans.transition_type}'")
        
        # Check if already cached
        if trans.id in controller.behavior_cache:
            cached = controller.behavior_cache[trans.id]
            cached_type = cached.get_type_name()
            print(f"  cached behavior type: '{cached_type}'")
            
            # Reproduce normalization logic
            type_name_map = {
                'Immediate': 'immediate',
                'Timed (TPN)': 'timed',
                'Stochastic (FSPN)': 'stochastic',
                'Continuous (SHPN)': 'continuous'
            }
            cached_type_normalized = type_name_map.get(cached_type, cached_type.lower())
            current_type = trans.transition_type
            
            print(f"  cached_type_normalized: '{cached_type_normalized}'")
            print(f"  current_type: '{current_type}'")
            print(f"  MATCH: {cached_type_normalized == current_type}")
            
            if cached_type_normalized != current_type:
                print(f"  ❌ TYPE MISMATCH - State will be deleted!")
        else:
            print(f"  (not cached yet)")
        
        print()

if __name__ == '__main__':
    main()
