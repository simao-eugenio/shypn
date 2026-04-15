#!/usr/bin/env python3
"""
Test that fetch_remote() now returns thermodynamic data that populates the UI.
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from shypn.thermodynamics.compound_database import CompoundDatabase


def test_fetch_remote_returns_thermodynamic_data():
    """Test that fetch_remote returns all required fields for UI population."""
    db = CompoundDatabase(':memory:')
    
    # Test C00002 (ATP) - the compound user tested
    print("Testing fetch_remote for C00002 (ATP)...")
    data = db.fetch_remote('C00002', source='equilibrator')
    
    # Verify all required fields exist
    required_fields = [
        'compound_id',
        'compound_name',
        'delta_g_formation',
        'charge',
        'n_protons',
        'pKa_values',
        'source',
        'fetch_date'
    ]
    
    print(f"\nReturned data:")
    for field in required_fields:
        value = data.get(field)
        status = '✓' if field in data else '✗'
        print(f"  {status} {field}: {value}")
    
    # Verify values are realistic for ATP
    assert data['compound_id'] == 'C00002'
    assert data['compound_name'] == 'ATP'
    assert data['delta_g_formation'] == -2292.5  # Standard ΔGf° for ATP
    assert data['charge'] == -4  # ATP at pH 7
    assert data['n_protons'] == 12
    assert len(data['pKa_values']) == 3
    assert data['source'] == 'equilibrator'
    
    print("\n✅ All required fields present with correct values!")
    
    # Test another common compound
    print("\n" + "="*60)
    print("Testing fetch_remote for C00031 (Glucose)...")
    data = db.fetch_remote('C00031', source='equilibrator')
    
    print(f"\nReturned data:")
    for field in required_fields:
        value = data.get(field)
        status = '✓' if field in data else '✗'
        print(f"  {status} {field}: {value}")
    
    assert data['compound_name'] == 'Glucose'
    assert 'delta_g_formation' in data
    assert 'charge' in data
    
    print("\n✅ Glucose data also complete!")
    
    # Test unknown compound (should still return all fields with defaults)
    print("\n" + "="*60)
    print("Testing fetch_remote for C99999 (Unknown compound)...")
    data = db.fetch_remote('C99999', source='equilibrator')
    
    print(f"\nReturned data:")
    for field in required_fields:
        value = data.get(field)
        status = '✓' if field in data else '✗'
        print(f"  {status} {field}: {value}")
    
    # Should have all fields even for unknown compound
    assert all(field in data for field in required_fields)
    print("\n✅ Unknown compound handled gracefully with default values!")
    
    print("\n" + "="*60)
    print("🎉 SUCCESS: fetch_remote() now returns complete thermodynamic data!")
    print("="*60)


def test_cache_and_retrieve():
    """Test that cached data includes thermodynamic properties."""
    import tempfile
    import os
    
    # Use temporary file for database
    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    try:
        db = CompoundDatabase(db_path)
        
        print("\nTesting cache workflow (like UI fetch button)...")
        
        # Simulate fetch from remote and cache
        data = db.fetch_remote('C00002')
        db.cache_compound(data)
        
        # Retrieve from cache
        cached = db.get_compound('C00002')
        
        print(f"\nCached data for ATP:")
        print(f"  Name: {cached['compound_name']}")
        print(f"  ΔGf°: {cached['delta_g_formation']} kJ/mol")
        print(f"  Charge: {cached['charge']}")
        print(f"  #Protons: {cached['n_protons']}")
        print(f"  pKa: {cached['pKa_values']}")
        
        assert cached['delta_g_formation'] == -2292.5
        assert cached['charge'] == -4
        
        print("\n✅ Cached data includes all thermodynamic properties!")
        
    finally:
        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)


if __name__ == '__main__':
    print("="*60)
    print("TESTING FETCH_REMOTE FIX")
    print("="*60)
    
    try:
        test_fetch_remote_returns_thermodynamic_data()
        print()
        test_cache_and_retrieve()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED")
        print("="*60)
        print("\nThe UI should now populate correctly when fetching C00002 (ATP)")
        print("and other common metabolites.")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
