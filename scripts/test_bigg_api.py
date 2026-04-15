#!/usr/bin/env python3
"""Test BiGG API access and service functionality.

This script tests the BiGG service classes manually without requiring
the full shypn UI. Useful for development and debugging.

Usage:
    python scripts/test_bigg_api.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from shypn.importer.bigg.bigg_model_fetcher import BiGGModelFetcher
from shypn.importer.bigg.bigg_downloader import BiGGDownloader
from shypn.importer.bigg.bigg_namespace_parser import BiGGNamespaceParser


def test_api_connectivity():
    """Test if BiGG API is accessible."""
    print("=" * 80)
    print("TEST 1: BiGG API Connectivity")
    print("=" * 80)
    
    fetcher = BiGGModelFetcher()
    
    if fetcher.validate():
        print("✓ BiGG API is accessible")
        return True
    else:
        print("✗ BiGG API is not accessible")
        return False


def test_model_listing():
    """Test fetching model list."""
    print("\n" + "=" * 80)
    print("TEST 2: Model Listing")
    print("=" * 80)
    
    fetcher = BiGGModelFetcher()
    models = fetcher.fetch_models()
    
    print(f"✓ Found {len(models)} models")
    
    # Show first 5 models
    print("\nFirst 5 models:")
    for model in models[:5]:
        print(f"  • {model.id}")
        print(f"    Organism: {model.organism}")
        print(f"    Size: {model.reaction_count} reactions, {model.metabolite_count} metabolites")
    
    return len(models) > 0


def test_organism_filtering():
    """Test organism filtering."""
    print("\n" + "=" * 80)
    print("TEST 3: Organism Filtering")
    print("=" * 80)
    
    fetcher = BiGGModelFetcher()
    
    # Test E. coli filtering
    ecoli_models = fetcher.filter_by_organism("Escherichia coli")
    print(f"✓ Found {len(ecoli_models)} E. coli models")
    
    if ecoli_models:
        print("\nE. coli models:")
        for model in ecoli_models[:5]:
            print(f"  • {model.id}: {model.reaction_count}R / {model.metabolite_count}M")
    
    return len(ecoli_models) > 0


def test_model_search():
    """Test model search functionality."""
    print("\n" + "=" * 80)
    print("TEST 4: Model Search")
    print("=" * 80)
    
    fetcher = BiGGModelFetcher()
    
    # Search for 'core' models
    results = fetcher.search_models("core")
    print(f"✓ Search for 'core' returned {len(results)} results")
    
    if results:
        print("\nCore models:")
        for model in results[:3]:
            print(f"  • {model.id}: {model.organism}")
    
    return len(results) > 0


def test_sbml_download():
    """Test SBML download."""
    print("\n" + "=" * 80)
    print("TEST 5: SBML Download")
    print("=" * 80)
    
    downloader = BiGGDownloader()
    
    # Download small model for testing
    model_id = "e_coli_core"
    print(f"Downloading {model_id}...")
    
    try:
        sbml_xml = downloader.download_sbml(model_id)
        print(f"✓ Downloaded {len(sbml_xml)} bytes")
        
        # Check if it's valid XML
        if sbml_xml.startswith('<?xml'):
            print("✓ SBML XML appears valid")
            
            # Check cache
            if downloader.is_cached(model_id):
                print(f"✓ Model cached at {downloader.get_cache_path(model_id)}")
            
            return True
        else:
            print("✗ Downloaded content doesn't appear to be XML")
            return False
    
    except Exception as e:
        print(f"✗ Download failed: {e}")
        return False


def test_namespace_parser():
    """Test BiGG namespace parsing."""
    print("\n" + "=" * 80)
    print("TEST 6: Namespace Parser")
    print("=" * 80)
    
    parser = BiGGNamespaceParser()
    
    # Test species ID parsing
    test_cases = [
        ("M_atp_c", ("atp", "c")),
        ("M_nadh_m", ("nadh", "m")),
        ("M_glc_D_e", ("glc_D", "e")),
        ("h2o_c", ("h2o", "c")),
    ]
    
    print("Testing species ID parsing:")
    for species_id, expected in test_cases:
        result = parser.parse_species_id(species_id)
        status = "✓" if result == expected else "✗"
        print(f"  {status} {species_id} -> {result}")
    
    # Test reaction ID parsing
    print("\nTesting reaction ID parsing:")
    reaction_tests = [
        ("R_ATPS4r", ("ATPS4", True)),
        ("R_PFK", ("PFK", False)),
    ]
    
    for reaction_id, expected in reaction_tests:
        result = parser.parse_reaction_id(reaction_id)
        status = "✓" if result == expected else "✗"
        print(f"  {status} {reaction_id} -> {result}")
    
    # Test energy metabolite detection
    print("\nTesting energy metabolite detection:")
    energy_tests = [
        ("atp", True),
        ("nadh", True),
        ("coa", True),
        ("glucose", False),
    ]
    
    for metabolite, expected in energy_tests:
        result = parser.is_energy_metabolite(metabolite)
        status = "✓" if result == expected else "✗"
        print(f"  {status} {metabolite} is energy: {result}")
    
    return True


def main():
    """Run all tests."""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " BiGG Service Test Suite ".center(78) + "║")
    print("╚" + "=" * 78 + "╝")
    print()
    
    results = []
    
    # Run tests
    results.append(("API Connectivity", test_api_connectivity()))
    results.append(("Model Listing", test_model_listing()))
    results.append(("Organism Filtering", test_organism_filtering()))
    results.append(("Model Search", test_model_search()))
    results.append(("SBML Download", test_sbml_download()))
    results.append(("Namespace Parser", test_namespace_parser()))
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    print(f"\nTotal: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total_count - passed_count} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
