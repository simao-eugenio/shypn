#!/usr/bin/env python3
"""Test script for heuristic database functionality.

This script tests:
1. Database creation and schema
2. Parameter storage
3. Query functionality
4. Cache operations
5. Organism compatibility
6. Statistics

Run: python test_heuristic_database.py
"""

import sys
import os
import tempfile
import logging

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from shypn.crossfetch.database import HeuristicDatabase

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def test_database_creation():
    """Test database creation and schema."""
    logger.info("=" * 60)
    logger.info("TEST 1: Database Creation")
    logger.info("=" * 60)
    
    # Create temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    try:
        db = HeuristicDatabase(db_path)
        logger.info(f"✓ Database created at: {db_path}")
        
        # Check schema version
        stats = db.get_statistics()
        logger.info(f"✓ Database initialized with {stats['total_parameters']} parameters")
        
        return db, db_path
    except Exception as e:
        logger.error(f"✗ Database creation failed: {e}")
        raise


def test_parameter_storage(db):
    """Test storing parameters."""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 2: Parameter Storage")
    logger.info("=" * 60)
    
    # Test 1: Store immediate transition parameters
    logger.info("\nStoring immediate transition parameters...")
    param_id1 = db.store_parameter(
        transition_type='immediate',
        organism='Homo sapiens',
        parameters={'priority': 90, 'weight': 1.0},
        source='Heuristic',
        confidence_score=0.80,
        biological_semantics='burst',
        ec_number='2.7.1.1',
        enzyme_name='hexokinase',
        notes='Regulatory burst event'
    )
    logger.info(f"✓ Stored immediate parameters (ID: {param_id1})")
    
    # Test 2: Store continuous transition parameters
    logger.info("\nStoring continuous transition parameters...")
    param_id2 = db.store_parameter(
        transition_type='continuous',
        organism='Homo sapiens',
        parameters={'vmax': 226.0, 'km': 0.1, 'kcat': 1500},
        source='SABIO-RK',
        confidence_score=0.95,
        biological_semantics='enzyme_kinetics',
        ec_number='2.7.1.1',
        enzyme_name='hexokinase',
        reaction_id='R00299',
        temperature=37.0,
        ph=7.4,
        notes='Human liver hexokinase'
    )
    logger.info(f"✓ Stored continuous parameters (ID: {param_id2})")
    
    # Test 3: Store yeast parameters (for cross-species testing)
    logger.info("\nStoring yeast parameters...")
    param_id3 = db.store_parameter(
        transition_type='continuous',
        organism='Saccharomyces cerevisiae',
        parameters={'vmax': 180.0, 'km': 0.12, 'kcat': 1200},
        source='SABIO-RK',
        confidence_score=0.90,
        biological_semantics='enzyme_kinetics',
        ec_number='2.7.1.1',
        enzyme_name='hexokinase',
        temperature=30.0,
        ph=7.0,
        notes='Yeast hexokinase (highly conserved)'
    )
    logger.info(f"✓ Stored yeast parameters (ID: {param_id3})")
    
    return param_id1, param_id2, param_id3


def test_parameter_queries(db):
    """Test querying parameters."""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 3: Parameter Queries")
    logger.info("=" * 60)
    
    # Query 1: Get all continuous parameters
    logger.info("\nQuery: All continuous transitions...")
    results = db.query_parameters(transition_type='continuous', min_confidence=0.0)
    logger.info(f"✓ Found {len(results)} continuous parameters")
    for r in results:
        logger.info(f"  - {r['enzyme_name']} ({r['organism']}): "
                   f"Vmax={r['parameters']['vmax']}, Confidence={r['confidence_score']}")
    
    # Query 2: Get hexokinase parameters for humans
    logger.info("\nQuery: Hexokinase (EC 2.7.1.1) for Homo sapiens...")
    results = db.query_parameters(
        ec_number='2.7.1.1',
        organism='Homo sapiens',
        min_confidence=0.5
    )
    logger.info(f"✓ Found {len(results)} matching parameters")
    
    # Query 3: Get high-confidence parameters only
    logger.info("\nQuery: High confidence (≥0.90) parameters...")
    results = db.query_parameters(min_confidence=0.90)
    logger.info(f"✓ Found {len(results)} high-confidence parameters")


def test_cache_operations(db, param_id):
    """Test cache operations."""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 4: Cache Operations")
    logger.info("=" * 60)
    
    # Cache a query result
    query_key = "continuous|EC:2.7.1.1|Homo sapiens"
    logger.info(f"\nCaching query: {query_key}")
    
    db.cache_query(
        query_key=query_key,
        recommended_id=param_id,
        alternatives=[],
        confidence_score=0.95
    )
    logger.info("✓ Query cached")
    
    # Retrieve from cache
    logger.info("\nRetrieving cached query...")
    cached = db.get_cached_query(query_key)
    if cached:
        logger.info(f"✓ Cache hit! Parameter ID: {cached['recommended_parameter_id']}, "
                   f"Confidence: {cached['confidence_score']}")
        logger.info(f"  Hit count: {cached['hit_count']}")
    else:
        logger.error("✗ Cache miss (unexpected)")
    
    # Test cache hit again (should increment counter)
    logger.info("\nRetrieving cached query again...")
    cached = db.get_cached_query(query_key)
    if cached:
        logger.info(f"✓ Cache hit again! Hit count: {cached['hit_count']}")


def test_organism_compatibility(db):
    """Test organism compatibility scoring."""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 5: Organism Compatibility")
    logger.info("=" * 60)
    
    test_cases = [
        ("Homo sapiens", "Homo sapiens", None),
        ("Rattus norvegicus", "Homo sapiens", None),
        ("Saccharomyces cerevisiae", "Homo sapiens", "EC 2.7.1"),
        ("Saccharomyces cerevisiae", "Homo sapiens", None),
        ("Escherichia coli", "Homo sapiens", None),
        ("generic", "Homo sapiens", None),
    ]
    
    logger.info("\nCompatibility scores:")
    for source, target, ec_class in test_cases:
        score = db.get_compatibility_score(source, target, ec_class)
        logger.info(f"  {source:30s} → {target:15s} "
                   f"({ec_class or 'any'}): {score:.2f}")


def test_enrichment_tracking(db, param_id):
    """Test enrichment tracking."""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 6: Enrichment Tracking")
    logger.info("=" * 60)
    
    # Record enrichment
    logger.info("\nRecording enrichment...")
    db.record_enrichment(
        parameter_id=param_id,
        transition_id='T5',
        pathway_id='hsa00010',
        pathway_name='Glycolysis',
        reaction_id='R00299',
        project_path='/home/user/project.shypn'
    )
    logger.info("✓ Enrichment recorded")
    
    # Check usage count
    param = db.get_parameter(param_id)
    logger.info(f"✓ Parameter usage count: {param['usage_count']}")
    
    # Get enrichment history
    logger.info("\nRetrieving enrichment history...")
    history = db.get_enrichment_history(pathway_id='hsa00010', limit=10)
    logger.info(f"✓ Found {len(history)} enrichment records for glycolysis")


def test_statistics(db):
    """Test statistics retrieval."""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 7: Statistics")
    logger.info("=" * 60)
    
    stats = db.get_statistics()
    
    logger.info(f"\nDatabase Statistics:")
    logger.info(f"  Total parameters: {stats['total_parameters']}")
    logger.info(f"  Cache entries: {stats['cache_entries']}")
    logger.info(f"  Cache hits: {stats['cache_hits']}")
    logger.info(f"  Total enrichments: {stats['total_enrichments']}")
    
    if stats['by_type']:
        logger.info(f"\n  By transition type:")
        for t_type, count in stats['by_type'].items():
            logger.info(f"    {t_type}: {count}")
    
    if stats['by_source']:
        logger.info(f"\n  By source:")
        for source, count in stats['by_source'].items():
            logger.info(f"    {source}: {count}")
    
    if stats['most_used']:
        logger.info(f"\n  Most used parameters:")
        for param in stats['most_used'][:5]:
            logger.info(f"    {param['enzyme_name'] or 'N/A'} "
                       f"(EC {param['ec_number'] or 'N/A'}): "
                       f"{param['usage_count']} times")


def main():
    """Run all tests."""
    logger.info("Starting Heuristic Database Tests\n")
    
    try:
        # Test 1: Create database
        db, db_path = test_database_creation()
        
        # Test 2: Store parameters
        param_id1, param_id2, param_id3 = test_parameter_storage(db)
        
        # Test 3: Query parameters
        test_parameter_queries(db)
        
        # Test 4: Cache operations
        test_cache_operations(db, param_id2)
        
        # Test 5: Organism compatibility
        test_organism_compatibility(db)
        
        # Test 6: Enrichment tracking
        test_enrichment_tracking(db, param_id2)
        
        # Test 7: Statistics
        test_statistics(db)
        
        logger.info("\n" + "=" * 60)
        logger.info("✓ ALL TESTS PASSED!")
        logger.info("=" * 60)
        logger.info(f"\nTest database location: {db_path}")
        logger.info("You can inspect it with: sqlite3 " + db_path)
        
        # Cleanup option
        import time
        time.sleep(1)
        if os.path.exists(db_path):
            os.unlink(db_path)
            logger.info("Test database cleaned up.")
        
    except Exception as e:
        logger.error(f"\n✗ TEST FAILED: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
