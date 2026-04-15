#!/usr/bin/env python3
"""
Demo: Using SHYPN Metadata System for Sweep Experiments

This demonstrates how to use the OOP metadata framework to:
1. Generate comprehensive CSV headers for sweep experiments
2. Load and parse existing headers
3. Update headers post-execution
"""

import json
from pathlib import Path
from datetime import datetime

# Import metadata framework
from shypn.metadata import (
    SweepHeaderGenerator,
    load_header,
    ModelMetadata,
    SweepConfiguration,
    ConservationLaws
)


def demo_generate_header():
    """Demo 1: Generate header for new sweep experiment"""
    
    print("="*70)
    print("DEMO 1: Generate Metadata Header")
    print("="*70)
    print()
    
    # Load model
    model_path = 'models/manuscript/macrocycle_transport_normal_nme_0_enhanced.shy'
    
    if not Path(model_path).exists():
        print(f"Model not found: {model_path}")
        print("Using mock data for demo...")
        model = {'places': [], 'transitions': [], 'arcs': []}
    else:
        with open(model_path, 'r') as f:
            model = json.load(f)
    
    # Define sweep configuration
    sweep_config = {
        'sweep_type': 'Parameter_Dose_Response',
        'sweep_parameter': 'P7.initial_marking',
        'sweep_range': (0, 5000),
        'sweep_step': 10,
        'sweep_units': 'µM',
        'current_value': 100
    }
    
    # Define simulation settings
    simulation_config = {
        'time_span': (0, 120),
        'time_units': 'seconds',
        'n_replicates': 3,
        'random_seed': 42,
        'solver': 'Gillespie_SSA',
        'timestep': 'adaptive'
    }
    
    # Define conservation sets
    conservation_sets = {
        'Drug': ['P1', 'P2', 'P3', 'P4', 'P6'],
        'Energy': ['P7', 'P8', 'P9']
    }
    
    # Get initial state from model
    initial_state = {}
    for place in model.get('places', []):
        place_id = place.get('id')
        marking = place.get('initial_marking', 0)
        initial_state[place_id] = marking
    
    # Build complete context
    context = {
        'model_path': model_path,
        'model': model,
        **sweep_config,
        'simulation_config': simulation_config,
        'conservation_sets': conservation_sets,
        'initial_state': initial_state,
        'sweep_start_time': datetime.utcnow(),
        'experiment_start_time': datetime.utcnow(),
        'phase': 'Phase_1_Data_Extraction',
        'documentation': 'doc/PHASE1_COMPLETION_SUMMARY.md',
        'related_analysis': 'atp_sweep_metrics.csv',
        'critical_places': ['P1', 'P7', 'P8', 'P9'],
        'stoichiometry_arcs': ['A45', 'A46', 'A47', 'A48', 'A49']
    }
    
    # Generate header
    generator = SweepHeaderGenerator()
    generator.set_context(context)
    header = generator.generate()
    
    # Validate
    is_valid, errors = generator.validate()
    print(f"Header validation: {'PASS' if is_valid else 'FAIL'}")
    if errors:
        print("Errors:")
        for error in errors:
            print(f"  - {error}")
    print()
    
    # Get header text
    header_text = generator.to_header_text()
    
    print("Generated header preview (first 30 lines):")
    print("-"*70)
    lines = header_text.split('\n')[:30]
    print('\n'.join(lines))
    print("...")
    print("-"*70)
    print()
    
    # Save to file
    output_file = 'demo_sweep_header.txt'
    Path(output_file).write_text(header_text)
    print(f"✅ Full header saved to: {output_file}")
    print()
    
    # Save metadata as JSON
    json_file = 'demo_sweep_metadata.json'
    generator.save_metadata_json(json_file)
    print(f"✅ Metadata JSON saved to: {json_file}")
    print()
    
    return header_text


def demo_quick_generate():
    """Demo 2: Quick header generation using convenience method"""
    
    print("="*70)
    print("DEMO 2: Quick Header Generation")
    print("="*70)
    print()
    
    model_path = 'models/manuscript/macrocycle_transport_normal_nme_0_enhanced.shy'
    
    if not Path(model_path).exists():
        print(f"Model not found: {model_path}")
        return
    
    # One-line header generation
    header_text = SweepHeaderGenerator.create_sweep_header(
        model_path=model_path,
        sweep_type='Parameter_Dose_Response',
        sweep_parameter='P7.initial_marking',
        sweep_range=(0, 5000),
        sweep_step=10,
        current_value=250,
        phase='Phase_0'
    )
    
    print("Quick-generated header (first 20 lines):")
    print("-"*70)
    lines = header_text.split('\n')[:20]
    print('\n'.join(lines))
    print("...")
    print("-"*70)
    print()


def demo_load_header():
    """Demo 3: Load existing header"""
    
    print("="*70)
    print("DEMO 3: Load and Parse Existing Header")
    print("="*70)
    print()
    
    # Check if demo file exists
    if not Path('demo_sweep_header.txt').exists():
        print("No demo header file found. Run demo 1 first.")
        return
    
    # Create a mock CSV with header
    csv_content = Path('demo_sweep_header.txt').read_text()
    csv_content += '\n# Species Statistics - Mean Trajectories\n'
    csv_content += 'Time,P1,P2,P3,P4,P5,P6,P7,P8,P9\n'
    csv_content += '0.0,100,0,11,89,10,0,5000,5000,5000\n'
    
    demo_csv = 'demo_experiment.csv'
    Path(demo_csv).write_text(csv_content)
    
    # Load header
    header = load_header(demo_csv)
    
    print(f"✅ Loaded header with {len(header.sections)} sections:")
    for section in header.sections:
        print(f"   - {section.section_name}")
    print()
    
    # Access specific sections
    model_section = header.get_section(ModelMetadata)
    if model_section:
        print("Model Information:")
        print(f"  Name: {model_section.get_field('Model_Name')}")
        print(f"  Path: {model_section.get_field('Model_Path')}")
        print(f"  Places: {model_section.get_field('N_Places')}")
        print()
    
    sweep_section = header.get_section(SweepConfiguration)
    if sweep_section:
        print("Sweep Configuration:")
        print(f"  Type: {sweep_section.get_field('Sweep_Type')}")
        print(f"  Parameter: {sweep_section.get_field('Sweep_Parameter')}")
        print(f"  Range: {sweep_section.get_field('Sweep_Range')}")
        print()
    
    conservation_section = header.get_section(ConservationLaws)
    if conservation_section:
        print("Conservation Laws:")
        drug_total = conservation_section.get_field('Drug_Total')
        energy_total = conservation_section.get_field('Energy_Total')
        if drug_total:
            print(f"  Drug Total: {drug_total}")
        if energy_total:
            print(f"  Energy Total: {energy_total}")
        print()


def demo_ui_integration():
    """Demo 4: UI integration - editable fields"""
    
    print("="*70)
    print("DEMO 4: UI Integration - Editable Fields")
    print("="*70)
    print()
    
    print("Editable fields from SweepConfiguration:")
    print()
    
    from shypn.metadata.sweep import SweepConfiguration
    
    for field_name, field_descriptor in SweepConfiguration.EDITABLE_FIELDS.items():
        print(f"Field: {field_name}")
        print(f"  Type: {field_descriptor.field_type.__name__}")
        print(f"  Default: {field_descriptor.default}")
        print(f"  Editable: {field_descriptor.editable}")
        
        if field_descriptor.choices:
            print(f"  Choices: {field_descriptor.choices}")
        
        if field_descriptor.min_value is not None:
            print(f"  Min: {field_descriptor.min_value}")
        
        if field_descriptor.max_value is not None:
            print(f"  Max: {field_descriptor.max_value}")
        
        if field_descriptor.description:
            print(f"  Description: {field_descriptor.description}")
        
        print()
    
    print("These fields can be rendered as:")
    print("  - Dropdown menus (for choices)")
    print("  - Number spinners (for numeric with min/max)")
    print("  - Text inputs (for strings)")
    print("in the Statistics Viewer table/tree view.")
    print()


if __name__ == '__main__':
    print()
    print("╔" + "═"*68 + "╗")
    print("║" + " "*15 + "SHYPN METADATA SYSTEM DEMO" + " "*27 + "║")
    print("╚" + "═"*68 + "╝")
    print()
    
    try:
        # Run all demos
        demo_generate_header()
        input("Press Enter to continue to Demo 2...")
        print()
        
        demo_quick_generate()
        input("Press Enter to continue to Demo 3...")
        print()
        
        demo_load_header()
        input("Press Enter to continue to Demo 4...")
        print()
        
        demo_ui_integration()
        
        print()
        print("="*70)
        print("DEMO COMPLETE")
        print("="*70)
        print()
        print("Generated files:")
        print("  - demo_sweep_header.txt")
        print("  - demo_sweep_metadata.json")
        print("  - demo_experiment.csv")
        print()
        print("Next steps:")
        print("  1. Integrate generator into batch_executor.py")
        print("  2. Create UI widgets for editable fields in Statistics Viewer")
        print("  3. Add header parsing to experiment result loader")
        print()
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
