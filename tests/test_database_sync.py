#!/usr/bin/env python3
"""Test the complete workflow with fresh database (like UI will do)."""

import sys
import os

# This is a script-style test intended to be run directly (not via pytest).
if __name__ != '__main__':
    import pytest
    pytest.skip('Script-style test, run directly with python3', allow_module_level=True)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from shypn.thermodynamics.compound_database import CompoundDatabase

print("="*70)
print("SIMULATING UI FETCH WORKFLOW (Fresh Database)")
print("="*70)

# Use actual database path
db = CompoundDatabase("workspace/compound_cache.db")

print("\n1️⃣  User enters C00002 and clicks 'Fetch from Database'...")
print("   Checking local cache first...")

# STEP 1: Check cache (should be empty)
data = db.get_compound('C00002')
if data:
    print("   ✓ Found in cache")
else:
    print("   ❌ Not in cache (expected for fresh database)")
    
    print("\n2️⃣  Showing dialog: 'Compound not in cache. Fetch from remote?'")
    print("   User clicks: YES")
    
    # STEP 2: Fetch from remote (with new placeholder code)
    print("\n3️⃣  Fetching from remote API (placeholder)...")
    data = db.fetch_remote('C00002', source='equilibrator')
    
    print("\n   Received data:")
    print(f"     Compound ID: {data['compound_id']}")
    print(f"     Name: {data['compound_name']}")
    print(f"     ΔGf°: {data['delta_g_formation']} kJ/mol")
    print(f"     Charge: {data['charge']}")
    print(f"     #Protons: {data['n_protons']}")
    print(f"     pKa: {data['pKa_values']}")
    
    # Verify it's complete
    assert data['delta_g_formation'] == -2292.5, "Wrong ΔGf° value!"
    assert data['charge'] == -4, "Wrong charge!"
    assert data['compound_name'] == 'ATP', "Wrong name!"
    
    print("\n   ✅ Data is complete!")
    
    # STEP 3: Cache the results
    print("\n4️⃣  Caching results for future use...")
    db.cache_compound(data)
    print("   ✓ Cached successfully")
    
    # STEP 4: UI populates fields (simulated by _populate_fetched_data)
    print("\n5️⃣  UI populates thermodynamic fields:")
    print(f"     thermo_compound_name_label.set_text('{data['compound_name']}')")
    print(f"     thermo_delta_g_entry.set_text('{data['delta_g_formation']:.2f}')")
    print(f"     thermo_charge_spin.set_value({data['charge']})")
    print(f"     thermo_n_protons_spin.set_value({data['n_protons']})")
    print(f"     thermo_pka_entry.set_text('{', '.join(str(x) for x in data['pKa_values'])}')")
    
    print("\n   ✅ All UI fields populated!")

# STEP 5: Verify cache retrieval
print("\n" + "="*70)
print("TESTING CACHE RETRIEVAL (Simulating Second Fetch)")
print("="*70)

print("\n6️⃣  User reopens dialog and fetches C00002 again...")
cached_data = db.get_compound('C00002')

if cached_data:
    print("   ✓ Found in local cache (instant retrieval)")
    print(f"\n   Retrieved data:")
    print(f"     Name: {cached_data['compound_name']}")
    print(f"     ΔGf°: {cached_data['delta_g_formation']} kJ/mol")
    print(f"     Charge: {cached_data['charge']}")
    print(f"     #Protons: {cached_data['n_protons']}")
    
    assert cached_data['delta_g_formation'] == -2292.5
    assert cached_data['compound_name'] == 'ATP'
    
    print("\n   ✅ Cache contains complete thermodynamic data!")
else:
    print("   ❌ Not found in cache (unexpected!)")
    sys.exit(1)

print("\n" + "="*70)
print("✅ SUCCESS: DATABASE IS NOW SYNCED!")
print("="*70)
print("\nThe UI fetch workflow will now work correctly:")
print("  • First fetch: Gets placeholder data from fetch_remote()")
print("  • Data cached with all thermodynamic properties")
print("  • UI fields populate correctly")
print("  • Second fetch: Retrieves instantly from cache")
print("\n💡 Try it in the GUI now!")
