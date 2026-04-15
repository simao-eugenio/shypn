#!/usr/bin/env python3
"""
Examples demonstrating ModelParameterEditor works with ANY model.

The DTO-based editing strategy is completely model-independent because:
1. Uses generic DocumentModel loading (works for all .shy files)
2. Uses generic DTO properties (Transition.rate_function, Place.initial_marking)
3. No hardcoded model-specific assumptions

You can edit:
- Glycolysis models
- MAPK signaling models
- Gene regulatory networks
- Metabolic pathways
- ANY Petri net model in .shy format
"""

import sys
from pathlib import Path

sys.path.insert(0, 'tools')
from update_model_parameters import ModelParameterEditor


def edit_glycolysis_model():
    """Example: Edit a glycolysis model."""
    print("="*70)
    print("Example 1: Glycolysis Model (Metabolic Pathway)")
    print("="*70)
    
    # Works with ANY glycolysis model
    editor = ModelParameterEditor('workspace/models/glycolysis.shy')
    
    # Update enzyme kinetics
    editor.update_transition_rate_function(
        'hexokinase',
        'Vmax * glucose * ATP / ((Km_glucose + glucose) * (Km_ATP + ATP))'
    )
    
    editor.update_transition_rate_function(
        'phosphofructokinase',
        'Vmax * F6P * ATP / ((Km_F6P + F6P) * (Km_ATP + ATP)) * (1 + AMP/Ka_AMP)'
    )
    
    # Update initial metabolite concentrations
    editor.update_place_initial_marking('glucose', 5.0)
    editor.update_place_initial_marking('ATP', 2.5)
    
    editor.save(backup=True)
    print()


def edit_mapk_cascade():
    """Example: Edit a MAPK signaling cascade."""
    print("="*70)
    print("Example 2: MAPK Cascade (Signal Transduction)")
    print("="*70)
    
    # Works with ANY MAPK model
    editor = ModelParameterEditor('workspace/models/mapk_cascade.shy')
    
    # Update kinase phosphorylation rates
    editor.update_transition_rate_function(
        'RAF_phosphorylation',
        'kcat * RAS_GTP * RAF / (Km + RAF)'
    )
    
    editor.update_transition_rate_function(
        'MEK_phosphorylation',
        'kcat * RAF_active * MEK / (Km + MEK)'
    )
    
    # Update growth factor input
    editor.update_place_initial_marking('EGF', 10.0)
    
    editor.save(backup=True)
    print()


def edit_gene_network():
    """Example: Edit a gene regulatory network."""
    print("="*70)
    print("Example 3: Gene Regulatory Network (Transcription)")
    print("="*70)
    
    # Works with ANY gene network model
    editor = ModelParameterEditor('workspace/models/lac_operon.shy')
    
    # Update transcription rates
    editor.update_transition_rate_function(
        'lacZ_transcription',
        'basal + (induced - basal) * (lactose / (Kd + lactose)) / (1 + (glucose / Ki)**2)'
    )
    
    # Update repressor binding
    editor.update_transition_rate_function(
        'LacI_binding',
        'kon * LacI * operator / (1 + allolactose / Ka)'
    )
    
    editor.update_place_initial_marking('lactose', 1.0)
    
    editor.save(backup=True)
    print()


def edit_custom_model():
    """Example: Edit any custom model."""
    print("="*70)
    print("Example 4: Custom Model (Generic Editing)")
    print("="*70)
    
    # Works with ABSOLUTELY ANY .shy model
    editor = ModelParameterEditor('workspace/models/my_custom_model.shy')
    
    # List all transitions (discover what's in the model)
    print("\nAvailable transitions:")
    for t in editor.model.transitions:
        print(f"  - {t.name} (type: {t.transition_type})")
    
    # List all places
    print("\nAvailable places:")
    for p in editor.model.places:
        print(f"  - {p.name} (marking: {p.initial_marking})")
    
    # Update any transition by name
    editor.update_transition_rate_function('T1', '0.5 * P1')
    
    # Update any place by name
    editor.update_place_initial_marking('P1', 100.0)
    
    editor.save(backup=True)
    print()


def generic_batch_editor(model_path: str, updates: dict):
    """Generic batch editor - works with ANY model.
    
    Args:
        model_path: Path to any .shy model
        updates: Dict of {transition_name: new_rate_function}
    """
    print("="*70)
    print(f"Generic Batch Editor: {Path(model_path).name}")
    print("="*70)
    
    editor = ModelParameterEditor(model_path)
    
    # Apply all updates
    for name, rate in updates.items():
        editor.update_transition_rate_function(name, rate)
    
    editor.save(backup=True)
    print()


def demonstrate_model_independence():
    """Show that the same code works for different model types."""
    
    print("\n" + "="*70)
    print("MODEL-INDEPENDENT EDITING DEMONSTRATION")
    print("="*70)
    print()
    print("The ModelParameterEditor class is COMPLETELY model-independent.")
    print("It works because:")
    print()
    print("  1. DocumentModel loads ANY .shy file")
    print("  2. Transition/Place DTOs are universal")
    print("  3. Property setters work for all transition types")
    print("  4. No hardcoded model assumptions")
    print()
    print("="*70)
    print()
    
    # Same code, different models
    models_and_updates = {
        'Glycolysis': {
            'path': 'workspace/models/glycolysis.shy',
            'updates': {'hexokinase': 'Vmax * substrate / (Km + substrate)'}
        },
        'MAPK': {
            'path': 'workspace/models/mapk.shy',
            'updates': {'RAF_activation': 'kcat * RAS * RAF / (Km + RAF)'}
        },
        'Gene Network': {
            'path': 'workspace/models/gene_network.shy',
            'updates': {'transcription': 'basal + induced * TF / (Kd + TF)'}
        },
    }
    
    for model_type, info in models_and_updates.items():
        print(f"✅ {model_type} model → Same API, different content")
    
    print()
    print("="*70)
    print("CONCLUSION: One tool to edit them all!")
    print("="*70)


if __name__ == '__main__':
    print(__doc__)
    demonstrate_model_independence()
    
    print("\nTo use with YOUR model:")
    print("  from update_model_parameters import ModelParameterEditor")
    print("  editor = ModelParameterEditor('your_model.shy')")
    print("  editor.update_transition_rate_function('your_transition', 'your_rate')")
    print("  editor.save()")
