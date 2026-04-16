#!/usr/bin/env python3
"""
Set compartment property for all transitions based on their biological location.

Assigns compartments based on:
- Biological process location (transcription in nucleus, translation in cytoplasm)
- Connected places (input/output arcs)
- Reaction mechanism (where the transition fires)
"""

import json
import shutil
from pathlib import Path

MODEL_FILE = Path(__file__).parent.parent / 'models' / 'phase3a_spatial.shy'

print("=" * 70)
print("SET TRANSITION COMPARTMENTS")
print("=" * 70)
print()

# Backup
backup_file = MODEL_FILE.with_suffix('.shy.backup_before_transition_compartments')
shutil.copy2(MODEL_FILE, backup_file)
print(f"✅ Backup created: {backup_file.name}")
print()

# Load model
with open(MODEL_FILE, 'r') as f:
    model = json.load(f)

# Define compartment assignments based on biological function
transition_compartments = {
    # Signal production/clearance - Extracellular
    'EPO_production': 'extracellular',
    'EPO_clearance': 'extracellular',
    'GCSF_production': 'extracellular',
    'GCSF_clearance': 'extracellular',
    
    # Receptor dynamics - Membrane (interface between extracellular and cytoplasm)
    'EPO_EPOR_binding': 'membrane',
    'EPO_EPOR_unbinding': 'membrane',
    'GCSF_GCSFR_binding': 'membrane',
    'GCSF_GCSFR_unbinding': 'membrane',
    'EPOR_internalization': 'membrane',
    'GCSFR_internalization': 'membrane',
    
    # Transcription - Nucleus (DNA → mRNA)
    'GATA1_transcription': 'nucleus',
    'PU1_transcription': 'nucleus',
    
    # mRNA export - Nucleus (where process initiates, nuclear pore)
    'GATA1_mRNA_export': 'nucleus',
    'PU1_mRNA_export': 'nucleus',
    
    # Translation - Cytoplasm (ribosomes)
    'GATA1_translation': 'cytoplasm',
    'PU1_translation': 'cytoplasm',
    
    # Nuclear import - Cytoplasm (where process initiates, nuclear pore)
    'GATA1_nuclear_import': 'cytoplasm',
    'PU1_nuclear_import': 'cytoplasm',
    
    # mRNA degradation - Location-specific
    'GATA1_mRNA_nuc_degradation': 'nucleus',
    'PU1_mRNA_nuc_degradation': 'nucleus',
    'GATA1_mRNA_cyto_degradation': 'cytoplasm',
    'PU1_mRNA_cyto_degradation': 'cytoplasm',
    
    # Protein degradation - Location-specific
    'GATA1_Protein_nuc_degradation': 'nucleus',
    'PU1_Protein_nuc_degradation': 'nucleus',
    'GATA1_Protein_cyto_degradation': 'cytoplasm',
    'PU1_Protein_cyto_degradation': 'cytoplasm',
    
    # Energy metabolism - Mitochondria/Cytoplasm
    'ATP_synthesis': 'mitochondria',  # Could also be 'cytoplasm' if simplified
    'GTP_regeneration': 'cytoplasm',
}

print("Compartment Assignments:")
print("=" * 70)
print()

# Group by compartment for display
by_compartment = {}
for name, compartment in transition_compartments.items():
    if compartment not in by_compartment:
        by_compartment[compartment] = []
    by_compartment[compartment].append(name)

for compartment in sorted(by_compartment.keys()):
    print(f"{compartment.upper()}:")
    for name in sorted(by_compartment[compartment]):
        print(f"  • {name}")
    print()

# Apply compartments to transitions
print("=" * 70)
print("APPLYING COMPARTMENTS")
print("=" * 70)
print()

updated_count = 0
missing_transitions = []

for t in model['transitions']:
    name = t['name']
    
    if name in transition_compartments:
        compartment = transition_compartments[name]
        
        # Set compartment field
        t['compartment'] = compartment
        
        # Also add to properties for consistency
        if 'properties' not in t:
            t['properties'] = {}
        t['properties']['compartment'] = compartment
        
        print(f"✅ {name} ({t['id']}): {compartment}")
        updated_count += 1
    else:
        missing_transitions.append(name)
        print(f"⚠️  {name} ({t['id']}): NOT IN ASSIGNMENT MAP")

print()

if missing_transitions:
    print("=" * 70)
    print("WARNING: Unassigned Transitions")
    print("=" * 70)
    for name in missing_transitions:
        print(f"  • {name}")
    print()

# Save model
with open(MODEL_FILE, 'w') as f:
    json.dump(model, f, indent=2)

print("=" * 70)
print(f"SUMMARY: Updated {updated_count}/{len(model['transitions'])} transitions")
print("=" * 70)
print()
print(f"✅ Model saved: {MODEL_FILE}")
print(f"✅ Backup: {backup_file.name}")
print()

print("Compartment Distribution:")
for compartment in sorted(by_compartment.keys()):
    count = len(by_compartment[compartment])
    print(f"  {compartment}: {count} transitions")

print()
print("=" * 70)
print("TRANSITION COMPARTMENTS SET")
print("=" * 70)
