#!/usr/bin/env python3
"""
GATA1/PU.1 Phase 2A Model Generator

This script generates the enhanced Petri net model with:
- Receptor binding dynamics
- Nuclear/cytoplasmic compartments
- ATP/GTP metabolic coupling  
- Dynamic signal sources

Usage:
    python generate_phase2a_model.py --output phase2a_core_enhanced.shy
"""

import json
import os
from pathlib import Path

def load_parameters(param_file):
    """Load parameters from JSON file"""
    with open(param_file, 'r') as f:
        return json.load(f)

def generate_places(params):
    """Generate all places for Phase 2A model"""
    places = []
    place_id = 1
    
    # Layer 1: Extracellular signals (2 places)
    places.append({
        'id': f'P{place_id}',
        'name': 'EPO_external',
        'initial': params['initial_conditions']['signals']['EPO_external']['value'],
        'units': 'µM',
        'compartment': 'extracellular',
        'layer': 1,
        'description': 'Extracellular EPO (dynamic source)'
    })
    place_id += 1
    
    places.append({
        'id': f'P{place_id}',
        'name': 'GCSF_external',
        'initial': params['initial_conditions']['signals']['GCSF_external']['value'],
        'units': 'µM',
        'compartment': 'extracellular',
        'layer': 1,
        'description': 'Extracellular GCSF (dynamic source)'
    })
    place_id += 1
    
    # Layer 2: Receptors (6 places)
    receptor_places = [
        ('EPOR_free', 'receptors'),
        ('EPOR_bound', 'receptors'),
        ('EPOR_internalized', 'receptors'),
        ('GCSFR_free', 'receptors'),
        ('GCSFR_bound', 'receptors'),
        ('GCSFR_internalized', 'receptors'),
    ]
    
    for name, category in receptor_places:
        places.append({
            'id': f'P{place_id}',
            'name': name,
            'initial': params['initial_conditions'][category][name]['value'],
            'units': 'receptors/cell',
            'compartment': 'membrane',
            'layer': 2,
            'description': params['initial_conditions'][category][name]['description']
        })
        place_id += 1
    
    # Layer 3: Gene layer (2 places)
    places.append({
        'id': f'P{place_id}',
        'name': 'GATA1_Gene',
        'initial': params['initial_conditions']['gene_layer']['GATA1_Gene']['value'],
        'units': 'copies',
        'compartment': 'nucleus',
        'layer': 3,
        'description': 'GATA1 gene locus'
    })
    place_id += 1
    
    places.append({
        'id': f'P{place_id}',
        'name': 'PU1_Gene',
        'initial': params['initial_conditions']['gene_layer']['PU1_Gene']['value'],
        'units': 'copies',
        'compartment': 'nucleus',
        'layer': 3,
        'description': 'PU.1 gene locus'
    })
    place_id += 1
    
    # Layer 4: Nuclear mRNA (2 places)
    places.append({
        'id': f'P{place_id}',
        'name': 'GATA1_mRNA_nuc',
        'initial': params['initial_conditions']['mrna_nuclear']['GATA1_mRNA_nuc']['value'],
        'units': 'molecules',
        'compartment': 'nucleus',
        'layer': 4,
        'description': 'Nuclear GATA1 mRNA'
    })
    place_id += 1
    
    places.append({
        'id': f'P{place_id}',
        'name': 'PU1_mRNA_nuc',
        'initial': params['initial_conditions']['mrna_nuclear']['PU1_mRNA_nuc']['value'],
        'units': 'molecules',
        'compartment': 'nucleus',
        'layer': 4,
        'description': 'Nuclear PU.1 mRNA'
    })
    place_id += 1
    
    # Layer 5: Cytoplasmic mRNA (2 places)
    places.append({
        'id': f'P{place_id}',
        'name': 'GATA1_mRNA_cyto',
        'initial': params['initial_conditions']['mrna_cytoplasmic']['GATA1_mRNA_cyto']['value'],
        'units': 'molecules',
        'compartment': 'cytoplasm',
        'layer': 5,
        'description': 'Cytoplasmic GATA1 mRNA'
    })
    place_id += 1
    
    places.append({
        'id': f'P{place_id}',
        'name': 'PU1_mRNA_cyto',
        'initial': params['initial_conditions']['mrna_cytoplasmic']['PU1_mRNA_cyto']['value'],
        'units': 'molecules',
        'compartment': 'cytoplasm',
        'layer': 5,
        'description': 'Cytoplasmic PU.1 mRNA'
    })
    place_id += 1
    
    # Layer 6: Cytoplasmic proteins (2 places)
    places.append({
        'id': f'P{place_id}',
        'name': 'GATA1_Protein_cyto',
        'initial': params['initial_conditions']['protein_cytoplasmic']['GATA1_Protein_cyto']['value'],
        'units': 'µM',
        'compartment': 'cytoplasm',
        'layer': 6,
        'description': 'Cytoplasmic GATA1 protein'
    })
    place_id += 1
    
    places.append({
        'id': f'P{place_id}',
        'name': 'PU1_Protein_cyto',
        'initial': params['initial_conditions']['protein_cytoplasmic']['PU1_Protein_cyto']['value'],
        'units': 'µM',
        'compartment': 'cytoplasm',
        'layer': 6,
        'description': 'Cytoplasmic PU.1 protein'
    })
    place_id += 1
    
    # Layer 7: Nuclear proteins (2 places)
    places.append({
        'id': f'P{place_id}',
        'name': 'GATA1_Protein_nuc',
        'initial': params['initial_conditions']['protein_nuclear']['GATA1_Protein_nuc']['value'],
        'units': 'µM',
        'compartment': 'nucleus',
        'layer': 7,
        'description': 'Nuclear GATA1 (functional TF)'
    })
    place_id += 1
    
    places.append({
        'id': f'P{place_id}',
        'name': 'PU1_Protein_nuc',
        'initial': params['initial_conditions']['protein_nuclear']['PU1_Protein_nuc']['value'],
        'units': 'µM',
        'compartment': 'nucleus',
        'layer': 7,
        'description': 'Nuclear PU.1 (functional TF)'
    })
    place_id += 1
    
    # Layer 8: Metabolic pools (5 places)
    metabolic_species = ['ATP', 'ADP', 'GTP', 'GDP', 'Pi']
    for species in metabolic_species:
        places.append({
            'id': f'P{place_id}',
            'name': species,
            'initial': params['initial_conditions']['metabolic_pools'][species]['value'],
            'units': 'µM',
            'compartment': 'cytoplasm',
            'layer': 8,
            'description': params['initial_conditions']['metabolic_pools'][species]['description']
        })
        place_id += 1
    
    return places

def generate_transitions(params, places):
    """Generate all transitions for Phase 2A model"""
    transitions = []
    trans_id = 1
    
    # Create place name lookup
    place_lookup = {p['name']: p['id'] for p in places}
    
    # T1: EPO production (dynamic source)
    transitions.append({
        'id': f'T{trans_id}',
        'name': 'EPO_production',
        'rate': '0',  # Set to 0, signals controlled via initial conditions
        'products': [place_lookup['EPO_external']],
        'stoichiometry': {'products': {place_lookup['EPO_external']: 1}},
        'description': 'Dynamic EPO source (pulse, ramp, constant)',
        'layer': 'signal_dynamics'
    })
    trans_id += 1
    
    # T2: EPO clearance
    k_clear_EPO = params['signal_dynamics']['EPO_clearance']['k_clearance_per_min']
    transitions.append({
        'id': f'T{trans_id}',
        'name': 'EPO_clearance',
        'rate': f'{k_clear_EPO} * EPO_external',
        'reactants': [place_lookup['EPO_external']],
        'stoichiometry': {'reactants': {place_lookup['EPO_external']: 1}},
        'description': f'EPO degradation (t½ = 5 hours)',
        'layer': 'signal_dynamics'
    })
    trans_id += 1
    
    # T3: GCSF production
    transitions.append({
        'id': f'T{trans_id}',
        'name': 'GCSF_production',
        'rate': '0',  # Set to 0, signals controlled via initial conditions
        'products': [place_lookup['GCSF_external']],
        'stoichiometry': {'products': {place_lookup['GCSF_external']: 1}},
        'description': 'Dynamic GCSF source',
        'layer': 'signal_dynamics'
    })
    trans_id += 1
    
    # T4: GCSF clearance
    k_clear_GCSF = params['signal_dynamics']['GCSF_clearance']['k_clearance_per_min']
    transitions.append({
        'id': f'T{trans_id}',
        'name': 'GCSF_clearance',
        'rate': f'{k_clear_GCSF} * GCSF_external',
        'reactants': [place_lookup['GCSF_external']],
        'stoichiometry': {'reactants': {place_lookup['GCSF_external']: 1}},
        'description': f'GCSF degradation (t½ = 3.5 hours)',
        'layer': 'signal_dynamics'
    })
    trans_id += 1
    
    # T5: EPO-EPOR binding
    Kd_EPO = params['receptor_binding']['EPO_EPOR']['Kd_uM']
    kon_EPO = params['receptor_binding']['EPO_EPOR']['kon_per_M_per_s']
    transitions.append({
        'id': f'T{trans_id}',
        'name': 'EPO_EPOR_binding',
        'rate': f'{kon_EPO} * EPO_external * EPOR_free / ({Kd_EPO} + EPO_external)',
        'reactants': [place_lookup['EPO_external'], place_lookup['EPOR_free']],
        'products': [place_lookup['EPOR_bound']],
        'stoichiometry': {
            'reactants': {
                place_lookup['EPO_external']: 1,
                place_lookup['EPOR_free']: 1
            },
            'products': {place_lookup['EPOR_bound']: 1}
        },
        'reversible': True,
        'description': f'EPO-EPOR binding (Kd = {Kd_EPO} µM)',
        'layer': 'receptor_binding'
    })
    trans_id += 1
    
    # T6: EPO-EPOR unbinding (reverse)
    koff_EPO = params['receptor_binding']['EPO_EPOR']['koff_per_s']
    transitions.append({
        'id': f'T{trans_id}',
        'name': 'EPO_EPOR_unbinding',
        'rate': f'{koff_EPO} * EPOR_bound',
        'reactants': [place_lookup['EPOR_bound']],
        'products': [place_lookup['EPO_external'], place_lookup['EPOR_free']],
        'stoichiometry': {
            'reactants': {place_lookup['EPOR_bound']: 1},
            'products': {
                place_lookup['EPO_external']: 1,
                place_lookup['EPOR_free']: 1
            }
        },
        'description': 'EPO-EPOR dissociation',
        'layer': 'receptor_binding'
    })
    trans_id += 1
    
    # T7-8: GCSF-GCSFR binding/unbinding (similar to EPO)
    Kd_GCSF = params['receptor_binding']['GCSF_GCSFR']['Kd_uM']
    kon_GCSF = params['receptor_binding']['GCSF_GCSFR']['kon_per_M_per_s']
    koff_GCSF = params['receptor_binding']['GCSF_GCSFR']['koff_per_s']
    
    transitions.append({
        'id': f'T{trans_id}',
        'name': 'GCSF_GCSFR_binding',
        'rate': f'{kon_GCSF} * GCSF_external * GCSFR_free / ({Kd_GCSF} + GCSF_external)',
        'reactants': [place_lookup['GCSF_external'], place_lookup['GCSFR_free']],
        'products': [place_lookup['GCSFR_bound']],
        'reversible': True,
        'description': f'GCSF-GCSFR binding (Kd = {Kd_GCSF} µM)',
        'layer': 'receptor_binding'
    })
    trans_id += 1
    
    transitions.append({
        'id': f'T{trans_id}',
        'name': 'GCSF_GCSFR_unbinding',
        'rate': f'{koff_GCSF} * GCSFR_bound',
        'reactants': [place_lookup['GCSFR_bound']],
        'products': [place_lookup['GCSF_external'], place_lookup['GCSFR_free']],
        'description': 'GCSF-GCSFR dissociation',
        'layer': 'receptor_binding'
    })
    trans_id += 1
    
    # T9: Receptor internalization (EPO)
    k_intern = params['receptor_binding']['receptor_trafficking']['k_internalization_per_min']
    transitions.append({
        'id': f'T{trans_id}',
        'name': 'EPOR_internalization',
        'rate': f'{k_intern} * EPOR_bound',
        'reactants': [place_lookup['EPOR_bound']],
        'products': [place_lookup['EPOR_internalized']],
        'description': 'Receptor-mediated endocytosis',
        'layer': 'receptor_trafficking'
    })
    trans_id += 1
    
    # T10: Receptor internalization (GCSF)
    transitions.append({
        'id': f'T{trans_id}',
        'name': 'GCSFR_internalization',
        'rate': f'{k_intern} * GCSFR_bound',
        'reactants': [place_lookup['GCSFR_bound']],
        'products': [place_lookup['GCSFR_internalized']],
        'description': 'Receptor-mediated endocytosis',
        'layer': 'receptor_trafficking'
    })
    trans_id += 1
    
    # T11: GATA1 transcription (enhanced)
    gata1_params = params['transcription']['GATA1']
    rate_gata1 = gata1_params['rate_equation']
    transitions.append({
        'id': f'T{trans_id}',
        'name': 'GATA1_transcription',
        'rate': rate_gata1,
        'catalysts': [place_lookup['GATA1_Gene']],
        'products': [place_lookup['GATA1_mRNA_nuc']],
        'stoichiometry': {
            'products': {place_lookup['GATA1_mRNA_nuc']: 1}
        },
        'description': 'GATA1 transcription with feedback and signal',
        'layer': 'transcription'
    })
    trans_id += 1
    
    # T12: PU.1 transcription (enhanced)
    pu1_params = params['transcription']['PU1']
    rate_pu1 = pu1_params['rate_equation']
    transitions.append({
        'id': f'T{trans_id}',
        'name': 'PU1_transcription',
        'rate': rate_pu1,
        'catalysts': [place_lookup['PU1_Gene']],
        'products': [place_lookup['PU1_mRNA_nuc']],
        'stoichiometry': {
            'products': {place_lookup['PU1_mRNA_nuc']: 1}
        },
        'description': 'PU.1 transcription with feedback and signal',
        'layer': 'transcription'
    })
    trans_id += 1
    
    # T13: GATA1 mRNA export (GTP-dependent)
    k_export = params['nuclear_transport']['mrna_export']['k_export_per_min']
    Km_GTP = params['nuclear_transport']['mrna_export']['Km_GTP_uM']
    transitions.append({
        'id': f'T{trans_id}',
        'name': 'GATA1_mRNA_export',
        'rate': f'{k_export} * GATA1_mRNA_nuc * GTP / ({Km_GTP} + GTP)',
        'reactants': [place_lookup['GATA1_mRNA_nuc'], place_lookup['GTP']],
        'products': [place_lookup['GATA1_mRNA_cyto'], place_lookup['GDP']],
        'stoichiometry': {
            'reactants': {
                place_lookup['GATA1_mRNA_nuc']: 1,
                place_lookup['GTP']: 1
            },
            'products': {
                place_lookup['GATA1_mRNA_cyto']: 1,
                place_lookup['GDP']: 1
            }
        },
        'description': 'GTP-dependent mRNA nuclear export',
        'layer': 'nuclear_transport'
    })
    trans_id += 1
    
    # T14: PU1 mRNA export (GTP-dependent)
    transitions.append({
        'id': f'T{trans_id}',
        'name': 'PU1_mRNA_export',
        'rate': f'{k_export} * PU1_mRNA_nuc * GTP / ({Km_GTP} + GTP)',
        'reactants': [place_lookup['PU1_mRNA_nuc'], place_lookup['GTP']],
        'products': [place_lookup['PU1_mRNA_cyto'], place_lookup['GDP']],
        'description': 'GTP-dependent mRNA nuclear export',
        'layer': 'nuclear_transport'
    })
    trans_id += 1
    
    # T15: GATA1 translation
    k_trans = params['translation']['GATA1_mRNA']['k_translation_per_min']
    transitions.append({
        'id': f'T{trans_id}',
        'name': 'GATA1_translation',
        'rate': f'{k_trans} * GATA1_mRNA_cyto',
        'catalysts': [place_lookup['GATA1_mRNA_cyto']],
        'products': [place_lookup['GATA1_Protein_cyto']],
        'description': 'GATA1 translation (simplified - no GTP coupling yet)',
        'layer': 'translation'
    })
    trans_id += 1
    
    # T16: PU1 translation
    transitions.append({
        'id': f'T{trans_id}',
        'name': 'PU1_translation',
        'rate': f'{k_trans} * PU1_mRNA_cyto',
        'catalysts': [place_lookup['PU1_mRNA_cyto']],
        'products': [place_lookup['PU1_Protein_cyto']],
        'description': 'PU.1 translation',
        'layer': 'translation'
    })
    trans_id += 1
    
    # T17: GATA1 protein nuclear import (GTP-dependent)
    k_import = params['nuclear_transport']['protein_import']['k_import_per_min']
    Km_GTP_import = params['nuclear_transport']['protein_import']['Km_GTP_uM']
    transitions.append({
        'id': f'T{trans_id}',
        'name': 'GATA1_nuclear_import',
        'rate': f'{k_import} * GATA1_Protein_cyto * GTP / ({Km_GTP_import} + GTP)',
        'reactants': [place_lookup['GATA1_Protein_cyto'], place_lookup['GTP']],
        'products': [place_lookup['GATA1_Protein_nuc'], place_lookup['GDP']],
        'description': 'GTP-dependent protein nuclear import',
        'layer': 'nuclear_transport'
    })
    trans_id += 1
    
    # T18: PU1 protein nuclear import (GTP-dependent)
    transitions.append({
        'id': f'T{trans_id}',
        'name': 'PU1_nuclear_import',
        'rate': f'{k_import} * PU1_Protein_cyto * GTP / ({Km_GTP_import} + GTP)',
        'reactants': [place_lookup['PU1_Protein_cyto'], place_lookup['GTP']],
        'products': [place_lookup['PU1_Protein_nuc'], place_lookup['GDP']],
        'description': 'GTP-dependent protein nuclear import',
        'layer': 'nuclear_transport'
    })
    trans_id += 1
    
    # T19-22: mRNA degradation
    k_deg_mrna = params['degradation']['mRNA']['GATA1_k_deg_per_min']
    transitions.extend([
        {
            'id': f'T{trans_id}',
            'name': 'GATA1_mRNA_nuc_degradation',
            'rate': f'{k_deg_mrna} * GATA1_mRNA_nuc',
            'reactants': [place_lookup['GATA1_mRNA_nuc']],
            'description': 'Nuclear mRNA degradation',
            'layer': 'degradation'
        },
        {
            'id': f'T{trans_id + 1}',
            'name': 'GATA1_mRNA_cyto_degradation',
            'rate': f'{k_deg_mrna} * GATA1_mRNA_cyto',
            'reactants': [place_lookup['GATA1_mRNA_cyto']],
            'description': 'Cytoplasmic mRNA degradation',
            'layer': 'degradation'
        },
        {
            'id': f'T{trans_id + 2}',
            'name': 'PU1_mRNA_nuc_degradation',
            'rate': f'{k_deg_mrna} * PU1_mRNA_nuc',
            'reactants': [place_lookup['PU1_mRNA_nuc']],
            'description': 'Nuclear mRNA degradation',
            'layer': 'degradation'
        },
        {
            'id': f'T{trans_id + 3}',
            'name': 'PU1_mRNA_cyto_degradation',
            'rate': f'{k_deg_mrna} * PU1_mRNA_cyto',
            'reactants': [place_lookup['PU1_mRNA_cyto']],
            'description': 'Cytoplasmic mRNA degradation',
            'layer': 'degradation'
        }
    ])
    trans_id += 4
    
    # T23-26: Protein degradation
    k_deg_prot = params['degradation']['protein']['GATA1_k_deg_per_min']
    transitions.extend([
        {
            'id': f'T{trans_id}',
            'name': 'GATA1_Protein_cyto_degradation',
            'rate': f'{k_deg_prot} * GATA1_Protein_cyto',
            'reactants': [place_lookup['GATA1_Protein_cyto']],
            'description': 'Cytoplasmic protein degradation',
            'layer': 'degradation'
        },
        {
            'id': f'T{trans_id + 1}',
            'name': 'GATA1_Protein_nuc_degradation',
            'rate': f'{k_deg_prot} * GATA1_Protein_nuc',
            'reactants': [place_lookup['GATA1_Protein_nuc']],
            'description': 'Nuclear protein degradation',
            'layer': 'degradation'
        },
        {
            'id': f'T{trans_id + 2}',
            'name': 'PU1_Protein_cyto_degradation',
            'rate': f'{k_deg_prot} * PU1_Protein_cyto',
            'reactants': [place_lookup['PU1_Protein_cyto']],
            'description': 'Cytoplasmic protein degradation',
            'layer': 'degradation'
        },
        {
            'id': f'T{trans_id + 3}',
            'name': 'PU1_Protein_nuc_degradation',
            'rate': f'{k_deg_prot} * PU1_Protein_nuc',
            'reactants': [place_lookup['PU1_Protein_nuc']],
            'description': 'Nuclear protein degradation',
            'layer': 'degradation'
        }
    ])
    trans_id += 4
    
    # T27: ATP synthesis
    Vmax_ATP = params['metabolic_rates']['ATP_synthesis']['Vmax_uM_per_min']
    Km_ADP = params['metabolic_rates']['ATP_synthesis']['Km_ADP_uM']
    Km_Pi = params['metabolic_rates']['ATP_synthesis']['Km_Pi_uM']
    transitions.append({
        'id': f'T{trans_id}',
        'name': 'ATP_synthesis',
        'rate': f'{Vmax_ATP} * ADP * Pi / (({Km_ADP} + ADP) * ({Km_Pi} + Pi))',
        'reactants': [place_lookup['ADP'], place_lookup['Pi']],
        'products': [place_lookup['ATP']],
        'description': 'Mitochondrial ATP synthesis',
        'layer': 'metabolism'
    })
    trans_id += 1
    
    # T28: GTP regeneration
    k_regen = params['metabolic_rates']['GTP_regeneration']['k_regen_per_min']
    Km_GDP_regen = params['metabolic_rates']['GTP_regeneration']['Km_GDP_uM']
    transitions.append({
        'id': f'T{trans_id}',
        'name': 'GTP_regeneration',
        'rate': f'{k_regen} * GDP * ATP / (({Km_GDP_regen} + GDP) * (500 + ATP))',
        'reactants': [place_lookup['GDP'], place_lookup['ATP']],
        'products': [place_lookup['GTP'], place_lookup['ADP']],
        'description': 'NDP kinase: GDP + ATP -> GTP + ADP',
        'layer': 'metabolism'
    })
    trans_id += 1
    
    return transitions

def generate_model_summary(params, places, transitions):
    """Generate human-readable summary"""
    summary = f"""
# GATA1/PU.1 Phase 2A Model Summary

**Model:** {params['model_metadata']['name']}
**Version:** {params['model_metadata']['version']}
**Generated:** {params['model_metadata']['created']}

## Structure
- **Places:** {len(places)}
  - Extracellular signals: 2
  - Receptors: 6
  - Gene layer: 2
  - Nuclear mRNA: 2
  - Cytoplasmic mRNA: 2
  - Cytoplasmic proteins: 2
  - Nuclear proteins: 2
  - Metabolic pools: 5

- **Transitions:** {len(transitions)}
  - Signal dynamics: 4 (production + clearance)
  - Receptor binding: 6 (on/off/internalization ×2)
  - Transcription: 2 (with feedback)
  - mRNA export: 2 (GTP-dependent)
  - Translation: 2
  - Protein import: 2 (GTP-dependent)
  - mRNA degradation: 4
  - Protein degradation: 4
  - Metabolism: 2 (ATP synthesis + GTP regeneration)

## Key Enhancements over Phase 1
1. ✅ Receptor layer (EPOR/GCSFR with Kd-based binding)
2. ✅ Nuclear/cytoplasmic compartments (7 layers vs 4)
3. ✅ ATP/GTP coupling (energy conservation)
4. ✅ Dynamic signal sources (production + clearance)

## Validation Targets
- Reproduce Phase 1 bistability (33:1 ratios)
- Energy conservation (ATP+ADP = 3300 µM)
- Signal clearance (EPO t½ = 5h, GCSF t½ = 3.5h)
- Receptor equilibration (Kd = 100pM for EPO, 600pM for GCSF)

## Next Steps
- Test model against Phase 1 results
- Verify thermodynamic consistency
- Add Phase 2B: chromatin + JAK-STAT signaling
"""
    return summary

def main():
    """Main model generation workflow"""
    
    # Paths
    base_dir = Path(__file__).parent.parent  # Go up to project root
    param_file = base_dir / 'parameters' / 'phase2a_parameters.json'
    output_dir = base_dir / 'models'
    output_dir.mkdir(exist_ok=True)
    
    print("="*70)
    print("GATA1/PU.1 Phase 2A Model Generator")
    print("="*70)
    print()
    
    # Load parameters
    print(f"Loading parameters from: {param_file}")
    params = load_parameters(param_file)
    print(f"✓ Parameters loaded: {params['model_metadata']['name']}")
    print()
    
    # Generate model components
    print("Generating model components...")
    places = generate_places(params)
    print(f"✓ Generated {len(places)} places")
    
    transitions = generate_transitions(params, places)
    print(f"✓ Generated {len(transitions)} transitions")
    print()
    
    # Generate summary
    summary = generate_model_summary(params, places, transitions)
    print(summary)
    
    # Save model structure to JSON
    model_structure = {
        'metadata': params['model_metadata'],
        'compartments': params['compartments'],
        'places': places,
        'transitions': transitions,
        'initial_conditions': params['initial_conditions'],
        'validation_criteria': params['validation_criteria']
    }
    
    output_file = output_dir / 'phase2a_model_structure.json'
    with open(output_file, 'w') as f:
        json.dump(model_structure, f, indent=2)
    
    print(f"✓ Model structure saved to: {output_file}")
    print()
    print("="*70)
    print("MODEL GENERATION COMPLETE")
    print("="*70)
    print()
    print("Next steps:")
    print("1. Review generated model structure")
    print("2. Import into ShyPN GUI or use programmatic builder")
    print("3. Run validation against Phase 1 results")
    print("4. Test energy conservation and signal dynamics")

if __name__ == '__main__':
    main()
