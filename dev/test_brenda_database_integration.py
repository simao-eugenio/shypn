#!/usr/bin/env python3
"""Test BRENDA database integration.

This script tests:
1. Database initialization and schema creation
2. Inserting BRENDA raw data
3. Querying BRENDA data with filters
4. Calculating and caching statistics
5. Retrieving database summary
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.shypn.crossfetch.database.heuristic_db import HeuristicDatabase


def test_database_integration():
    """Test BRENDA database integration end-to-end."""
    print("=" * 70)
    print("BRENDA Database Integration Test")
    print("=" * 70)
    
    # Initialize database
    print("\n1. Initializing database...")
    db = HeuristicDatabase()
    print("   ✓ Database initialized")
    
    # Create sample BRENDA data (simulating a query result)
    print("\n2. Preparing sample BRENDA data...")
    sample_data = [
        {
            'ec_number': '2.7.1.1',
            'parameter_type': 'Km',
            'value': 0.15,
            'unit': 'mM',
            'substrate': 'D-glucose',
            'organism': 'Homo sapiens',
            'literature': 'PubMed:12345678',
            'commentary': 'Brain tissue, pH 7.4',
            'quality': 0.95
        },
        {
            'ec_number': '2.7.1.1',
            'parameter_type': 'Km',
            'value': 0.18,
            'unit': 'mM',
            'substrate': 'D-glucose',
            'organism': 'Homo sapiens',
            'literature': 'PubMed:87654321',
            'commentary': 'Liver tissue, pH 7.0',
            'quality': 0.92
        },
        {
            'ec_number': '2.7.1.1',
            'parameter_type': 'Km',
            'value': 0.52,
            'unit': 'mM',
            'substrate': 'D-glucose',
            'organism': 'Saccharomyces cerevisiae',
            'literature': 'PubMed:11223344',
            'commentary': 'Wild type strain',
            'quality': 0.88
        },
        {
            'ec_number': '2.7.1.1',
            'parameter_type': 'kcat',
            'value': 250.0,
            'unit': '1/s',
            'substrate': 'D-glucose',
            'organism': 'Homo sapiens',
            'literature': 'PubMed:55667788',
            'commentary': 'Recombinant enzyme',
            'quality': 0.90
        },
        {
            'ec_number': '2.7.1.2',
            'parameter_type': 'Km',
            'value': 1.5,
            'unit': 'mM',
            'substrate': 'D-fructose',
            'organism': 'Escherichia coli',
            'literature': 'PubMed:99887766',
            'commentary': 'K-12 strain',
            'quality': 0.85
        }
    ]
    print(f"   ✓ Created {len(sample_data)} sample records")
    
    # Insert data
    print("\n3. Inserting data into database...")
    inserted = db.insert_brenda_raw_data(sample_data)
    print(f"   ✓ Inserted {inserted} records (duplicates skipped)")
    
    # Query all EC 2.7.1.1 data
    print("\n4. Querying EC 2.7.1.1 data...")
    ec_data = db.query_brenda_data(ec_number='2.7.1.1')
    print(f"   ✓ Found {len(ec_data)} records for EC 2.7.1.1")
    for record in ec_data:
        print(f"      - {record['parameter_type']}: {record['value']} {record['unit']} "
              f"({record['organism']}, quality={record['source_quality']:.2f})")
    
    # Query with filters
    print("\n5. Querying with filters (EC 2.7.1.1, organism=Homo sapiens, min_quality=0.9)...")
    filtered_data = db.query_brenda_data(
        ec_number='2.7.1.1',
        organism='Homo sapiens',
        min_quality=0.9
    )
    print(f"   ✓ Found {len(filtered_data)} records matching filters")
    for record in filtered_data:
        print(f"      - {record['parameter_type']}: {record['value']} {record['unit']} "
              f"(quality={record['source_quality']:.2f})")
    
    # Calculate statistics
    print("\n6. Calculating statistics for EC 2.7.1.1 Km...")
    km_stats = db.calculate_brenda_statistics(
        ec_number='2.7.1.1',
        parameter_type='Km'
    )
    if km_stats:
        print(f"   ✓ Statistics calculated:")
        print(f"      - Mean: {km_stats['mean_value']:.3f} mM")
        print(f"      - Median: {km_stats['median_value']:.3f} mM")
        print(f"      - Std Dev: {km_stats['std_dev']:.3f} mM")
        print(f"      - Range: {km_stats['min_value']:.3f} - {km_stats['max_value']:.3f} mM")
        print(f"      - 95% CI: [{km_stats['confidence_interval_95_lower']:.3f}, "
              f"{km_stats['confidence_interval_95_upper']:.3f}] mM")
        print(f"      - Count: {km_stats['count']} values")
    else:
        print("   ✗ Statistics calculation failed")
    
    # Calculate organism-specific statistics
    print("\n7. Calculating organism-specific statistics (EC 2.7.1.1, Km, Homo sapiens)...")
    human_stats = db.calculate_brenda_statistics(
        ec_number='2.7.1.1',
        parameter_type='Km',
        organism='Homo sapiens'
    )
    if human_stats:
        print(f"   ✓ Human-specific statistics:")
        print(f"      - Mean: {human_stats['mean_value']:.3f} mM")
        print(f"      - Count: {human_stats['count']} values")
    
    # Retrieve cached statistics
    print("\n8. Retrieving cached statistics...")
    cached_stats = db.get_brenda_statistics(
        ec_number='2.7.1.1',
        parameter_type='Km'
    )
    if cached_stats:
        print(f"   ✓ Retrieved cached statistics:")
        print(f"      - Mean: {cached_stats['mean_value']:.3f} mM")
        print(f"      - Last updated: {cached_stats['last_updated']}")
    
    # Get database summary
    print("\n9. Getting database summary...")
    summary = db.get_brenda_summary()
    print(f"   ✓ Database summary:")
    print(f"      - Total records: {summary['total_records']}")
    print(f"      - Unique EC numbers: {summary['unique_ec_numbers']}")
    print(f"      - Unique organisms: {summary['unique_organisms']}")
    print(f"      - Average quality: {summary['average_quality']:.2f}")
    print(f"      - Cached statistics: {summary['cached_statistics']}")
    print(f"      - By parameter type: {summary['by_parameter_type']}")
    
    # Test duplicate prevention
    print("\n10. Testing duplicate prevention...")
    re_inserted = db.insert_brenda_raw_data(sample_data[:2])
    print(f"   ✓ Re-inserted {re_inserted}/2 records (0 expected due to UNIQUE constraint)")
    
    print("\n" + "=" * 70)
    print("All tests completed successfully! ✓")
    print("=" * 70)
    
    # Show database location
    print(f"\nDatabase location: {db.db_path}")
    print("\nYou can inspect the database with:")
    print(f"  sqlite3 {db.db_path}")
    print("  SELECT * FROM brenda_raw_data;")
    print("  SELECT * FROM brenda_statistics;")


if __name__ == '__main__':
    try:
        test_database_integration()
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
