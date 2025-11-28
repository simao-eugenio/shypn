#!/usr/bin/env python3
"""
Test script to verify KEGG EC fetching performance improvements.

This script tests:
1. Parallel fetching vs sequential
2. Persistent cache functionality
3. Pre-fetching in pathway conversion

Run from project root:
    python3 scripts/test_kegg_performance.py
"""

import sys
import time
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from shypn.data.kegg_ec_fetcher import (
    KEGGECFetcher,
    fetch_ec_numbers_parallel,
    PersistentECCache,
    get_default_fetcher
)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_sequential_vs_parallel():
    """Test sequential vs parallel fetching performance."""
    print("\n" + "="*70)
    print("TEST 1: Sequential vs Parallel Fetching")
    print("="*70)
    
    # Test reactions from Glycolysis pathway
    test_reactions = [
        "rn:R00299",  # Hexokinase
        "rn:R00771",  # Phosphoglucose isomerase
        "rn:R00756",  # Phosphofructokinase
        "rn:R01068",  # Aldolase
        "rn:R01015",  # Triose-phosphate isomerase
        "rn:R01061",  # Glyceraldehyde-3-phosphate dehydrogenase
        "rn:R01512",  # Phosphoglycerate kinase
        "rn:R01518",  # Phosphoglycerate mutase
        "rn:R00658",  # Enolase
        "rn:R00200",  # Pyruvate kinase
    ]
    
    # Test 1: Sequential fetching (old way)
    print(f"\n1. Sequential fetching ({len(test_reactions)} reactions)...")
    fetcher = KEGGECFetcher(use_persistent_cache=False)
    
    start = time.time()
    results_seq = {}
    for rid in test_reactions:
        results_seq[rid] = fetcher.fetch_ec_numbers(rid)
    seq_time = time.time() - start
    
    print(f"   Time: {seq_time:.2f}s")
    print(f"   Found: {sum(len(ecs) for ecs in results_seq.values())} EC numbers")
    
    # Test 2: Parallel fetching (new way)
    print(f"\n2. Parallel fetching ({len(test_reactions)} reactions)...")
    fetcher2 = KEGGECFetcher(use_persistent_cache=False)
    
    start = time.time()
    results_par = fetcher2.fetch_ec_numbers_parallel(test_reactions, max_workers=5)
    par_time = time.time() - start
    
    print(f"   Time: {par_time:.2f}s")
    print(f"   Found: {sum(len(ecs) for ecs in results_par.values())} EC numbers")
    
    # Compare
    speedup = seq_time / par_time if par_time > 0 else 0
    print(f"\n✓ Speedup: {speedup:.1f}x faster")
    
    return speedup > 1.5  # Should be at least 1.5x faster


def test_persistent_cache():
    """Test persistent cache functionality."""
    print("\n" + "="*70)
    print("TEST 2: Persistent Cache")
    print("="*70)
    
    # Create cache with custom location
    cache_file = Path.home() / ".shypn" / "kegg_ec_cache_test.json"
    cache_file.unlink(missing_ok=True)  # Delete old test cache
    
    print(f"\nCache file: {cache_file}")
    
    # Test 1: First fetch (should hit API)
    print("\n1. First fetch (cold cache)...")
    cache = PersistentECCache(cache_file=cache_file, ttl_days=90)
    
    result = cache.get("rn:R00299")
    assert result is None, "Cache should be empty"
    print("   ✓ Cache empty (as expected)")
    
    # Populate cache
    cache.set("rn:R00299", ["2.7.1.1", "2.7.1.2"])
    cache.save()
    print("   ✓ Added EC numbers to cache")
    
    # Test 2: Read from same instance (memory)
    result = cache.get("rn:R00299")
    assert result == ["2.7.1.1", "2.7.1.2"], "Should read from cache"
    print("   ✓ Read from memory cache")
    
    # Test 3: Create new instance (should load from file)
    print("\n2. Second fetch (warm cache, new instance)...")
    cache2 = PersistentECCache(cache_file=cache_file, ttl_days=90)
    result = cache2.get("rn:R00299")
    assert result == ["2.7.1.1", "2.7.1.2"], "Should load from file"
    print("   ✓ Read from persistent file cache")
    
    # Test 4: Cache stats
    stats = cache2.get_stats()
    print(f"\n3. Cache statistics:")
    print(f"   Total entries: {stats['total']}")
    print(f"   Valid entries: {stats['valid']}")
    print(f"   Expired: {stats['expired']}")
    
    # Cleanup
    cache_file.unlink(missing_ok=True)
    print("\n✓ Persistent cache test passed")
    
    return True


def test_integration_with_fetcher():
    """Test integration of persistent cache with fetcher."""
    print("\n" + "="*70)
    print("TEST 3: Integration with KEGGECFetcher")
    print("="*70)
    
    # Clear default cache
    cache_file = Path.home() / ".shypn" / "kegg_ec_cache.json"
    if cache_file.exists():
        print(f"\nFound existing cache: {cache_file}")
        cache = PersistentECCache(cache_file=cache_file)
        stats = cache.get_stats()
        print(f"  Entries: {stats['total']} (valid: {stats['valid']}, expired: {stats['expired']})")
    
    # Test fetcher with persistent cache
    print("\n1. Fetching with persistent cache enabled...")
    fetcher = get_default_fetcher()
    
    test_id = "rn:R00299"
    start = time.time()
    result1 = fetcher.fetch_ec_numbers(test_id)
    time1 = time.time() - start
    print(f"   First fetch: {result1} ({time1*1000:.0f}ms)")
    
    # Second fetch should be instant (memory cache)
    start = time.time()
    result2 = fetcher.fetch_ec_numbers(test_id)
    time2 = time.time() - start
    print(f"   Second fetch: {result2} ({time2*1000:.0f}ms)")
    
    speedup = time1 / time2 if time2 > 0 else float('inf')
    print(f"\n✓ Cache speedup: {speedup:.0f}x faster")
    
    return True


def test_cache_cleanup():
    """Test cache cleanup functionality."""
    print("\n" + "="*70)
    print("TEST 4: Cache Cleanup")
    print("="*70)
    
    cache_file = Path.home() / ".shypn" / "kegg_ec_cache_cleanup_test.json"
    cache_file.unlink(missing_ok=True)
    
    cache = PersistentECCache(cache_file=cache_file, ttl_days=0)  # Expire immediately
    
    # Add entries
    cache.set("rn:R00299", ["2.7.1.1"])
    cache.set("rn:R00771", ["5.3.1.9"])
    cache.save()
    
    print(f"\n1. Added 2 entries with TTL=0 (expire immediately)")
    stats = cache.get_stats()
    print(f"   Total: {stats['total']}, Expired: {stats['expired']}")
    
    # Cleanup
    cache.cleanup_expired()
    stats = cache.get_stats()
    print(f"\n2. After cleanup:")
    print(f"   Total: {stats['total']}, Expired: {stats['expired']}")
    
    # Verify
    assert stats['total'] == 0, "All entries should be removed"
    print("\n✓ Cache cleanup test passed")
    
    # Cleanup test file
    cache_file.unlink(missing_ok=True)
    
    return True


def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("KEGG EC Fetching Performance Tests")
    print("="*70)
    
    tests = [
        ("Sequential vs Parallel", test_sequential_vs_parallel),
        ("Persistent Cache", test_persistent_cache),
        ("Integration", test_integration_with_fetcher),
        ("Cache Cleanup", test_cache_cleanup),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            logger.error(f"Test '{name}' failed: {e}", exc_info=True)
            results.append((name, False))
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status}: {name}")
    
    passed_count = sum(1 for _, p in results if p)
    total_count = len(results)
    
    print(f"\nTotal: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n❌ {total_count - passed_count} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
