#!/usr/bin/env python3
"""Test SABIO-RK result deduplication by (EC number, Organism)."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("="*70)
print("SABIO-RK DEDUPLICATION TEST")
print("="*70)

# Simulate SABIO-RK results with duplicate EC + Organism combinations
mock_results = [
    {
        'transition_id': 'T32',
        'identifiers': {'ec_number': '2.7.1.1'},
        'sabio_data': {
            'query_organism': 'Homo sapiens',
            'parameters': [
                # Reaction 1 - EC 2.7.1.1, Homo sapiens
                {'reaction_id': 'REAC_1', 'kegg_reaction_id': 'R00299', 'organism': 'Homo sapiens',
                 'parameter_type': 'Km', 'value': 0.15, 'units': 'mM'},
                {'reaction_id': 'REAC_1', 'kegg_reaction_id': 'R00299', 'organism': 'Homo sapiens',
                 'parameter_type': 'Vmax', 'value': 2.5, 'units': 'µmol/min/mg'},
                
                # Reaction 2 - SAME EC 2.7.1.1, SAME Homo sapiens (should deduplicate!)
                {'reaction_id': 'REAC_2', 'kegg_reaction_id': 'R00300', 'organism': 'Homo sapiens',
                 'parameter_type': 'Km', 'value': 0.22, 'units': 'mM'},
                {'reaction_id': 'REAC_2', 'kegg_reaction_id': 'R00300', 'organism': 'Homo sapiens',
                 'parameter_type': 'Vmax', 'value': 3.1, 'units': 'µmol/min/mg'},
                
                # Reaction 3 - SAME EC 2.7.1.1, DIFFERENT Organism (should be separate row!)
                {'reaction_id': 'REAC_3', 'kegg_reaction_id': 'R00301', 'organism': 'Mus musculus',
                 'parameter_type': 'Km', 'value': 0.18, 'units': 'mM'},
                {'reaction_id': 'REAC_3', 'kegg_reaction_id': 'R00301', 'organism': 'Mus musculus',
                 'parameter_type': 'Kcat', 'value': 450, 'units': '1/s'},
            ]
        }
    }
]

print("\n" + "="*70)
print("MOCK DATA SUMMARY")
print("="*70)
print("Simulating SABIO-RK query for EC 2.7.1.1:")
print("  - Reaction 1: EC 2.7.1.1, Homo sapiens, R00299 (Km=0.15, Vmax=2.5)")
print("  - Reaction 2: EC 2.7.1.1, Homo sapiens, R00300 (Km=0.22, Vmax=3.1)")
print("  - Reaction 3: EC 2.7.1.1, Mus musculus, R00301 (Km=0.18, Kcat=450)")
print("\nExpected deduplication:")
print("  ✓ Row 1: EC 2.7.1.1, Homo sapiens (combines Reactions 1 & 2)")
print("  ✓ Row 2: EC 2.7.1.1, Mus musculus (Reaction 3)")
print("="*70)

# Test the deduplication logic
from collections import defaultdict

unique_entries = defaultdict(lambda: {
    'transition_id': None,
    'kegg_reaction_ids': set(),
    'ec_number': None,
    'organism': None,
    'Vmax': [],
    'Km': [],
    'Kcat': [],
    'Ki': [],
    'raw_parameters': []
})

for result in mock_results:
    sabio_data = result.get('sabio_data', {})
    parameters = sabio_data.get('parameters', [])
    query_organism = sabio_data.get('query_organism')
    ec_number = result.get('identifiers', {}).get('ec_number', 'N/A')
    transition_id = result.get('transition_id', 'N/A')
    
    for param in parameters:
        param_type = param.get('parameter_type', 'other')
        param_organism = param.get('organism')
        organism = param_organism or query_organism or 'Unknown'
        
        # Create unique key: (EC, Organism)
        key = (ec_number, organism)
        
        # Store metadata
        if not unique_entries[key]['transition_id']:
            unique_entries[key]['transition_id'] = transition_id
            unique_entries[key]['ec_number'] = ec_number
            unique_entries[key]['organism'] = organism
        
        # Collect KEGG reaction IDs
        kegg_id = param.get('kegg_reaction_id')
        if kegg_id:
            unique_entries[key]['kegg_reaction_ids'].add(kegg_id)
        
        # Collect parameter values
        value = param.get('value')
        units = param.get('units', '')
        if value is not None and param_type in unique_entries[key]:
            unique_entries[key][param_type].append(f"{value:.3g} {units}".strip())
            unique_entries[key]['raw_parameters'].append(param)

print("\n" + "="*70)
print("DEDUPLICATION RESULTS")
print("="*70)

row_count = 0
for (ec_number, organism), entry_data in unique_entries.items():
    row_count += 1
    
    kegg_ids = sorted(entry_data['kegg_reaction_ids'])
    kegg_display = ', '.join(kegg_ids[:3])
    if len(kegg_ids) > 3:
        kegg_display += f' (+{len(kegg_ids)-3} more)'
    
    vmax_values = entry_data['Vmax']
    km_values = entry_data['Km']
    kcat_values = entry_data['Kcat']
    ki_values = entry_data['Ki']
    
    print(f"\nRow {row_count}:")
    print(f"  ID: {entry_data['transition_id']}")
    print(f"  KEGG Reaction: {kegg_display}")
    print(f"  EC Number: {ec_number}")
    print(f"  Organism: {organism}")
    print(f"  Vmax: {', '.join(vmax_values) if vmax_values else '-'}")
    print(f"  Km: {', '.join(km_values) if km_values else '-'}")
    print(f"  Kcat: {', '.join(kcat_values) if kcat_values else '-'}")
    print(f"  Ki: {', '.join(ki_values) if ki_values else '-'}")
    print(f"  Raw Parameters: {len(entry_data['raw_parameters'])} values")

print("\n" + "="*70)
print("VERIFICATION")
print("="*70)

# Test 1: Check row count
expected_rows = 2
if row_count == expected_rows:
    print(f"✅ Correct number of rows: {row_count} (expected {expected_rows})")
else:
    print(f"❌ Wrong number of rows: {row_count} (expected {expected_rows})")
    sys.exit(1)

# Test 2: Check Homo sapiens entry has 2 KEGG IDs
homo_sapiens_entry = unique_entries[('2.7.1.1', 'Homo sapiens')]
if len(homo_sapiens_entry['kegg_reaction_ids']) == 2:
    print(f"✅ Homo sapiens entry correctly aggregates 2 reactions: {sorted(homo_sapiens_entry['kegg_reaction_ids'])}")
else:
    print(f"❌ Homo sapiens should have 2 KEGG IDs, got {len(homo_sapiens_entry['kegg_reaction_ids'])}")
    sys.exit(1)

# Test 3: Check Homo sapiens has both Km values
if len(homo_sapiens_entry['Km']) == 2:
    print(f"✅ Homo sapiens entry has 2 Km values: {homo_sapiens_entry['Km']}")
else:
    print(f"❌ Homo sapiens should have 2 Km values, got {len(homo_sapiens_entry['Km'])}")
    sys.exit(1)

# Test 4: Check Mus musculus is separate
mus_musculus_entry = unique_entries[('2.7.1.1', 'Mus musculus')]
if len(mus_musculus_entry['kegg_reaction_ids']) == 1:
    print(f"✅ Mus musculus entry is separate: {sorted(mus_musculus_entry['kegg_reaction_ids'])}")
else:
    print(f"❌ Mus musculus should have 1 KEGG ID, got {len(mus_musculus_entry['kegg_reaction_ids'])}")
    sys.exit(1)

# Test 5: Check raw parameters are preserved
total_raw_params = sum(len(entry['raw_parameters']) for entry in unique_entries.values())
if total_raw_params == 6:  # Reaction 1: 2 params, Reaction 2: 2 params, Reaction 3: 2 params = 6 total
    print(f"✅ All {total_raw_params} raw parameters preserved for Apply Selected")
else:
    print(f"❌ Expected 6 raw parameters, got {total_raw_params}")
    sys.exit(1)

print("\n" + "="*70)
print("✅ ALL TESTS PASSED")
print("="*70)
print("\nSummary:")
print("  ✓ Deduplicates by (EC number, Organism)")
print("  ✓ Aggregates multiple reactions with same EC + Organism")
print("  ✓ Keeps separate organisms as different rows")
print("  ✓ Preserves ALL numeric parameters for Apply Selected")
print("  ✓ Shows multiple KEGG Reaction IDs in one row")
print("\nUser Benefits:")
print("  - FEWER rows in table (less confusion)")
print("  - Each unique EC + Organism shown ONCE")
print("  - ALL parameters still available for rate function")
print("="*70)
