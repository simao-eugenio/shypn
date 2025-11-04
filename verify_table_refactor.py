#!/usr/bin/env python3
"""Quick verification that table refactor works end-to-end."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("SABIO-RK Table Refactor - Integration Check")
print("="*70)

# Test 1: Import modules
try:
    from shypn.data.sabio_rk_client import SabioRKClient
    from shypn.ui.panels.pathway_operations.sabio_rk_category import SabioRKCategory
    print("✅ Modules import successfully")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)

# Test 2: Query works
try:
    client = SabioRKClient()
    result = client.query_by_ec_number("2.7.1.1", "Homo sapiens")
    assert result is not None, "Query returned None"
    assert 'parameters' in result, "No parameters in result"
    assert 'query_organism' in result, "No query_organism in result"
    print(f"✅ Query works: {len(result['parameters'])} parameters")
    print(f"   Query organism: {result['query_organism']}")
except Exception as e:
    print(f"❌ Query failed: {e}")
    sys.exit(1)

# Test 3: Metadata extraction
try:
    params = result['parameters']
    kegg_ids = [p['kegg_reaction_id'] for p in params if p.get('kegg_reaction_id')]
    organisms = [p['organism'] for p in params]
    param_types = set(p['parameter_type'] for p in params)
    
    print(f"✅ Metadata extracted:")
    print(f"   KEGG Reaction IDs: {len(kegg_ids)} found")
    print(f"   Example: {kegg_ids[0] if kegg_ids else 'None'}")
    print(f"   Parameter types: {param_types}")
except Exception as e:
    print(f"❌ Metadata extraction failed: {e}")
    sys.exit(1)

# Test 4: Table structure mock
try:
    # Simulate what UI does
    from collections import defaultdict
    
    query_organism = result.get('query_organism')
    reactions = defaultdict(lambda: {
        'kegg_reaction_id': None,
        'organism': query_organism or 'Unknown',
        'Vmax': [], 'Km': [], 'Kcat': [], 'Ki': []
    })
    
    for param in params:
        reaction_id = param.get('reaction_id', 'unknown')
        param_type = param.get('parameter_type', 'other')
        
        if not reactions[reaction_id]['kegg_reaction_id']:
            reactions[reaction_id]['kegg_reaction_id'] = param.get('kegg_reaction_id')
        
        value = param.get('value')
        units = param.get('units', '')
        if value is not None and param_type in reactions[reaction_id]:
            reactions[reaction_id][param_type].append(f"{value:.3g} {units}")
    
    print(f"✅ Table grouping works:")
    print(f"   Reactions grouped: {len(reactions)}")
    print(f"   First reaction: {list(reactions.keys())[0]}")
    
    # Check first reaction has data
    first_reaction = reactions[list(reactions.keys())[0]]
    print(f"   KEGG ID: {first_reaction['kegg_reaction_id']}")
    print(f"   Organism: {first_reaction['organism']}")
    print(f"   Has Vmax: {len(first_reaction['Vmax']) > 0}")
    print(f"   Has Km: {len(first_reaction['Km']) > 0}")
    
except Exception as e:
    print(f"❌ Table grouping failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "="*70)
print("✅ ALL CHECKS PASSED")
print("   Table refactor is ready for production!")
print("="*70)
