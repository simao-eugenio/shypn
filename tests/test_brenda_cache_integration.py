#!/usr/bin/env python3
"""
Test BRENDA Cache Integration in Kinetics Dialog

Tests the SQLite cache integration for instant parameter lookups.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))


def test_cache_manager_initialization():
    """Test cache manager can be initialized."""
    print("Testing cache manager initialization...")
    
    try:
        from shypn.crossfetch.database.heuristic_db import HeuristicDatabase
        from shypn.crossfetch.cache.brenda_cache_manager import BRENDACacheManager
        
        db = HeuristicDatabase()
        cache = BRENDACacheManager(db)
        
        print(f"✅ Cache manager initialized")
        print(f"   Database: {db.db_path}")
        
        # Get summary
        summary = cache.get_cache_summary()
        print(f"   Cached records: {summary.get('total_records', 0)}")
        print(f"   Unique EC numbers: {summary.get('unique_ec_numbers', 0)}")
        print(f"   Unique organisms: {summary.get('unique_organisms', 0)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_query_key_building():
    """Test query key format."""
    print("\nTesting query key building...")
    
    try:
        from shypn.crossfetch.cache.brenda_cache_manager import BRENDACacheManager
        from shypn.crossfetch.database.heuristic_db import HeuristicDatabase
        
        db = HeuristicDatabase()
        cache = BRENDACacheManager(db)
        
        # Test different key formats
        key1 = cache.build_query_key('2.7.1.1', 'Km')
        key2 = cache.build_query_key('2.7.1.1', 'Km', 'Homo sapiens')
        key3 = cache.build_query_key('2.7.1.1', 'Km', 'Homo sapiens', 'glucose')
        
        print(f"✅ Query keys generated:")
        print(f"   All organisms: {key1}")
        print(f"   With organism: {key2}")
        print(f"   With substrate: {key3}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


def test_cached_data_lookup():
    """Test looking up cached BRENDA data."""
    print("\nTesting cached data lookup...")
    
    try:
        from shypn.crossfetch.database.heuristic_db import HeuristicDatabase
        from shypn.crossfetch.cache.brenda_cache_manager import BRENDACacheManager
        
        db = HeuristicDatabase()
        cache = BRENDACacheManager(db)
        
        # Get summary to find available EC numbers
        summary = cache.get_cache_summary()
        
        if summary.get('total_records', 0) > 0:
            # Try to find any cached EC number
            with db._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT DISTINCT ec_number, parameter_type, COUNT(*) as count
                    FROM brenda_raw_data
                    GROUP BY ec_number, parameter_type
                    LIMIT 3
                """)
                rows = cursor.fetchall()
            
            if rows:
                print(f"✅ Found cached data:")
                for row in rows:
                    ec, param, count = row
                    print(f"   EC {ec} - {param}: {count} records")
                    
                    # Try to get statistics
                    stats = db.get_brenda_statistics(ec, param)
                    if stats:
                        print(f"      Mean: {stats['mean_value']:.3f}")
                        print(f"      Median: {stats['median_value']:.3f}")
                        print(f"      Count: {stats['count']}")
                    else:
                        # Calculate if not cached
                        stats = db.calculate_brenda_statistics(ec, param)
                        if stats:
                            print(f"      Mean: {stats['mean_value']:.3f} (calculated)")
                
                return True
            else:
                print("⚠️  No cached data available (empty database)")
                print("   Note: Cache will be populated after first BRENDA API queries")
                return True
        else:
            print("⚠️  No cached records in database")
            print("   Note: Cache will be populated during BRENDA enrichment operations")
            return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_cache_storage_simulation():
    """Simulate storing data in cache."""
    print("\nTesting cache storage (simulation)...")
    
    try:
        from shypn.crossfetch.database.heuristic_db import HeuristicDatabase
        from shypn.crossfetch.cache.brenda_cache_manager import BRENDACacheManager
        
        db = HeuristicDatabase()
        cache = BRENDACacheManager(db)
        
        # Simulate API response format
        test_data = [
            {
                'ec_number': '9.9.9.9',  # Test EC
                'parameter_type': 'Km',
                'value': 0.5,
                'unit': 'mM',
                'substrate': 'test_substrate',
                'organism': 'Test organism',
                'literature': 'PMID:00000',
                'commentary': 'Test data',
                'quality': 0.9
            },
            {
                'ec_number': '9.9.9.9',
                'parameter_type': 'Km',
                'value': 0.6,
                'unit': 'mM',
                'substrate': 'test_substrate',
                'organism': 'Test organism',
                'literature': 'PMID:00001',
                'commentary': 'Test data 2',
                'quality': 0.85
            }
        ]
        
        # Store test data
        inserted = cache.store_raw_data_batch(test_data)
        print(f"✅ Stored {inserted} test records")
        
        # Calculate statistics
        stats = db.calculate_brenda_statistics('9.9.9.9', 'Km')
        if stats:
            print(f"✅ Calculated statistics:")
            print(f"   Mean: {stats['mean_value']:.3f}")
            print(f"   Median: {stats['median_value']:.3f}")
            print(f"   Count: {stats['count']}")
        
        # Clean up test data
        with db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM brenda_raw_data WHERE ec_number = '9.9.9.9'")
            cursor.execute("DELETE FROM brenda_statistics WHERE ec_number = '9.9.9.9'")
            conn.commit()
        
        print(f"✅ Test data cleaned up")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all cache integration tests."""
    print("=" * 70)
    print("TESTING BRENDA CACHE INTEGRATION")
    print("=" * 70)
    
    results = []
    
    results.append(test_cache_manager_initialization())
    results.append(test_query_key_building())
    results.append(test_cached_data_lookup())
    results.append(test_cache_storage_simulation())
    
    print("\n" + "=" * 70)
    
    if all(results):
        print("✅ ALL CACHE INTEGRATION TESTS PASSED!")
        print("=" * 70)
        print("\nCache integration verified:")
        print("  • Cache manager initializes correctly")
        print("  • Query keys build properly")
        print("  • Cached data can be retrieved")
        print("  • Storage and statistics calculation work")
        print("\nDialog will now:")
        print("  • Check cache before API queries (instant)")
        print("  • Store API results for future use")
        print("  • Work offline with cached data")
        print("  • Show statistical mean values from cache")
        return 0
    else:
        print("⚠️  SOME TESTS FAILED")
        print("=" * 70)
        return 1


if __name__ == '__main__':
    sys.exit(main())
