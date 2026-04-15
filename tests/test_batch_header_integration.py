#!/usr/bin/env python3
"""
Test script to verify batch execution metadata header integration.

This script simulates the context that will be passed to SweepHeaderGenerator
during batch execution and verifies the header is properly formatted.
"""

import json
import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / 'src'))

from shypn.metadata import SweepHeaderGenerator

def test_batch_integration():
    """Test the integration code that will be used in _save_batch_results()"""
    
    # Find a real model file
    model_path = project_root / 'workspace' / 'projects' / 'Biochemical-Examples' / '11_Glycolysis_TCA_Connection' / 'model.shy'
    
    if not model_path.exists():
        print(f"Warning: Model file not found at {model_path}")
        print("Using mock model data instead")
        model_path_str = None
        model = {
            'formalism': 'Stochastic Petri Net',
            'places': [{'id': f'P{i}'} for i in range(20)],
            'transitions': [{'id': f'T{i}'} for i in range(15)],
            'arcs': [{'id': f'A{i}'} for i in range(50)]
        }
    else:
        # Load real model
        with open(model_path, 'r') as f:
            model = json.load(f)
        model_path_str = str(model_path)
        print(f"✓ Loaded model from {model_path}")
        print(f"  Formalism: {model.get('formalism', 'N/A')}")
        print(f"  Places: {len(model.get('places', []))}")
        print(f"  Transitions: {len(model.get('transitions', []))}")
        print(f"  Arcs: {len(model.get('arcs', []))}")
    
    # Simulate the context from _save_batch_results()
    # This matches what we added to the integration code
    n_replicates = 10
    replicate_id = 0  # First replicate
    
    # Use actual place/transition IDs from the model if available
    if model_path_str:
        recorded_objects = []
        # Add first 3 places
        for i, place in enumerate(model.get('places', [])[:3]):
            recorded_objects.append(place['id'])
        # Add first 3 transitions
        for i, transition in enumerate(model.get('transitions', [])[:3]):
            recorded_objects.append(transition['id'])
    else:
        recorded_objects = ['P1', 'P7', 'P8', 'P9', 'T1', 'T2']
    
    context = {
        'model_path': model_path_str,
        'model': model,
        'n_replicates': n_replicates,
        'recorded_objects': list(recorded_objects),
        'simulation_config': {
            'duration': 1000.0,
            'time_units': 'second',
            'use_tau_leaping': False,
        },
        'current_replicate': replicate_id + 1,
        'total_replicates': n_replicates,
        'phase': 'Batch_Mode'
    }
    
    print("\n" + "="*80)
    print("TESTING BATCH HEADER GENERATION")
    print("="*80)
    
    # Generate header using the exact same code as in _save_batch_results()
    print("\n1. Creating SweepHeaderGenerator...")
    generator = SweepHeaderGenerator()
    
    print("2. Setting context...")
    generator.set_context(context)
    
    print("3. Generating header sections...")
    generator.generate()
    
    print("4. Converting to header text...")
    header_text = generator.to_header_text()
    
    # Validate
    print("\n5. Validating generated header...")
    is_valid, errors = generator.validate()
    if is_valid:
        print("✓ Header validation PASSED")
    else:
        print("✗ Header validation FAILED:")
        for error in errors:
            print(f"  - {error}")
    
    # Write to test file
    output_path = project_root / 'test_batch_replicate_header.csv'
    print(f"\n6. Writing test CSV with header to {output_path.name}...")
    
    with open(output_path, 'w') as f:
        # Write metadata header
        f.write(header_text)
        
        # Write mock CSV data
        import csv
        writer = csv.writer(f)
        writer.writerow(['time', 'P1', 'P7', 'P8', 'P9', 'T1', 'T2'])
        writer.writerow([0.0, 1000, 0, 5000, 5000, 0, 0])
        writer.writerow([100.0, 950, 50, 4900, 4905, 10, 5])
        writer.writerow([200.0, 900, 100, 4800, 4810, 20, 10])
    
    print(f"✓ Test CSV written successfully")
    
    # Display header info
    print("\n" + "="*80)
    print("HEADER SUMMARY")
    print("="*80)
    print(f"Header lines: {len(header_text.splitlines())}")
    print(f"Sections: {len(generator.header.sections)}")
    for section in generator.header.sections:
        print(f"  - {section.__class__.__name__}: {len(section._fields)} fields")
    
    # Show first 20 lines of header
    print("\n" + "="*80)
    print("HEADER PREVIEW (first 20 lines)")
    print("="*80)
    header_lines = header_text.splitlines()
    for i, line in enumerate(header_lines[:20], 1):
        print(f"{i:2}. {line}")
    
    if len(header_lines) > 20:
        print(f"... ({len(header_lines) - 20} more lines)")
    
    print("\n" + "="*80)
    print(f"✓ Integration test complete!")
    print(f"✓ Test CSV available at: {output_path}")
    print("="*80)
    
    return True

if __name__ == '__main__':
    try:
        success = test_batch_integration()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
