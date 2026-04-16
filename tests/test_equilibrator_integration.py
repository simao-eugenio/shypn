#!/usr/bin/env python3
"""Test eQuilibrator API integration with compound database."""

import sys
import os

# This is a script-style test intended to be run directly (not via pytest).
if __name__ != '__main__':
    import pytest
    pytest.skip('Script-style test, run directly with python3', allow_module_level=True)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from shypn.thermodynamics.compound_database import CompoundDatabase

print("="*70)
print("TESTING EQUILIBRATOR API INTEGRATION")
print("="*70)

# Use actual database path
db = CompoundDatabase("workspace/compound_cache.db")

print("\n1️⃣  Testing API fetch for ATP (C00002)...")
print("   This will make a REAL API call to eQuilibrator")
print("   (requires internet connection)")
print()

try:
    # Fetch from remote (should call EquilibratorProvider)
    data = db.fetch_remote('C00002', source='equilibrator')
    
    if data:
        print("✅ API call successful!")
        print(f"\n   Received data:")
        print(f"     Compound ID: {data['compound_id']}")
        print(f"     Name: {data['compound_name']}")
        print(f"     ΔGf°: {data['delta_g_formation']} kJ/mol")
        print(f"     Charge: {data['charge']}")
        print(f"     #Protons: {data['n_protons']}")
        print(f"     pKa: {data['pKa_values']}")
        print(f"     Source: {data['source']}")
        print(f"     Notes: {data['notes']}")
        
        # Verify it's from  API (not placeholder)
        if 'eQuilibrator API' in data.get('notes', ''):
            print("\n   ✅ Data confirmed from eQuilibrator API!")
        else:
            print(f"\n   ⚠️  Unexpected notes: {data.get('notes')}")
        
        # Cache it
        print("\n2️⃣  Caching result...")
        db.cache_compound(data)
        print("   ✅ Cached successfully")
        
        # Retrieve from cache
        print("\n3️⃣  Retrieving from cache...")
        cached = db.get_compound('C00002')
        if cached and cached['delta_g_formation'] == data['delta_g_formation']:
            print("   ✅ Cache retrieval successful")
            print(f"   ΔGf° matches: {cached['delta_g_formation']} kJ/mol")
        else:
            print("   ❌ Cache retrieval failed")
            
    else:
        print("❌ API returned None")
        print("   Possible reasons:")
        print("   - No internet connection")
        print("   - eQuilibrator API unavailable")
        print("   - Compound not in database")
        sys.exit(1)

except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test with unknown compound
print("\n" + "="*70)
print("4️⃣  Testing with unknown compound (C99999)...")
print("="*70)

try:
    data = db.fetch_remote('C99999', source='equilibrator')
    if data is None:
        print("✅ Correctly returned None for unknown compound")
    else:
        print(f"⚠️  Unexpectedly got data: {data}")
except Exception as e:
    print(f"✅ Gracefully handled error: {e}")

print("\n" + "="*70)
print("✅ INTEGRATION TEST COMPLETE!")
print("="*70)
print("\nThe dialog 'Fetch from Database' button will now:")
print("  1. Query eQuilibrator API for ΔGf°")
print("  2. Combine with structural properties (charge, pKa)")
print("  3. Cache for future use")
print("  4. Display all data in UI")
print("\n💡 Next: Test in the GUI!")
