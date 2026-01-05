#!/usr/bin/env python3
"""Test script for compound mapper system.

This script tests the newly created OOP mapper system.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from shypn.data.canvas.document_model import DocumentModel
from shypn.thermodynamics.mappers import CompoundMapperService


def test_label_based_mapping():
    """Test label-based compound mapping."""
    print("=" * 60)
    print("TEST 1: Label-Based Mapping")
    print("=" * 60)
    
    # Create test document
    doc = DocumentModel()
    
    # Create places with various labels
    doc.create_place(100, 100, label="ATP")
    doc.create_place(200, 100, label="Glucose (C00031)")
    doc.create_place(300, 100, label="NADH")
    doc.create_place(400, 100, label="Unknown Compound")
    doc.create_place(500, 100, label="Pyruvate")
    
    print(f"\nCreated {len(doc.places)} test places")
    
    # Run mapper service
    service = CompoundMapperService()
    mappings, confidences = service.map_all_places(doc)
    
    print(f"\nMapped {len(mappings)} places:")
    for place in doc.places:
        compound_id = mappings.get(place.id, "NOT MAPPED")
        confidence = confidences.get(place.id, 0.0)
        print(f"  {place.label:20} → {compound_id:10} (confidence: {confidence:.2f})")
    
    # Get summary
    summary = service.get_mapping_summary(mappings, confidences)
    print(f"\nSummary:")
    print(f"  Total mapped: {summary['total_mapped']}")
    print(f"  High confidence (≥0.9): {summary['high_confidence']}")
    print(f"  Medium confidence (0.5-0.9): {summary['medium_confidence']}")
    print(f"  Average confidence: {summary['average_confidence']:.2f}")
    
    return len(mappings) > 0


def test_document_persistence():
    """Test that compound mappings persist through save/load."""
    print("\n" + "=" * 60)
    print("TEST 2: Document Persistence")
    print("=" * 60)
    
    # Create document with mappings
    doc = DocumentModel()
    doc.create_place(100, 100, label="ATP")
    doc.create_place(200, 100, label="Glucose")
    
    # Map compounds
    service = CompoundMapperService()
    mappings, _ = service.map_all_places(doc)
    
    print(f"\nOriginal mappings: {doc.compound_mappings}")
    
    # Save to dict (simulating file save)
    data = doc.to_dict()
    print(f"Serialized mappings: {data.get('compound_mappings', {})}")
    
    # Load from dict (simulating file load)
    doc2 = DocumentModel.from_dict(data)
    print(f"Restored mappings: {doc2.compound_mappings}")
    
    # Verify mappings preserved
    success = doc.compound_mappings == doc2.compound_mappings
    print(f"\nMappings preserved: {success}")
    
    return success


def test_manual_override():
    """Test manual mapping updates."""
    print("\n" + "=" * 60)
    print("TEST 3: Manual Mapping Override")
    print("=" * 60)
    
    # Create document
    doc = DocumentModel()
    place1 = doc.create_place(100, 100, label="Custom Metabolite")
    
    # Auto-map (will fail for unknown name)
    service = CompoundMapperService()
    mappings, _ = service.map_all_places(doc)
    
    print(f"\nBefore manual update:")
    print(f"  {place1.label} → {mappings.get(place1.id, 'NOT MAPPED')}")
    
    # Manual override
    service.update_mapping(doc, place1.id, "C00999", confidence=1.0)
    
    print(f"\nAfter manual update:")
    print(f"  {place1.label} → {doc.compound_mappings[place1.id]}")
    
    # Test removal
    service.remove_mapping(doc, place1.id)
    
    print(f"\nAfter removal:")
    print(f"  {place1.label} → {doc.compound_mappings.get(place1.id, 'NOT MAPPED')}")
    
    return True


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("COMPOUND MAPPER SYSTEM TEST")
    print("=" * 60)
    
    tests = [
        ("Label-Based Mapping", test_label_based_mapping),
        ("Document Persistence", test_document_persistence),
        ("Manual Override", test_manual_override),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"\n❌ TEST FAILED: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
