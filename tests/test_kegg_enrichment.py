"""Test KEGG name enrichment with real API calls."""

import sys
import os
sys.path.insert(0, 'src')

from shypn.services.kegg_name_enrichment import KEGGNameEnricher, enrich_kegg_names
from shypn.data.canvas.document_model import DocumentModel
from shypn.netobjs.place import Place
from shypn.netobjs.transition import Transition


def progress_callback(current, total, message):
    """Simple progress display."""
    print(f"[{current}/{total}] {message}")


def test_enrichment():
    """Test enriching a mock KEGG model."""
    print("=== Testing KEGG Name Enrichment ===\n")
    
    # Create mock document with KEGG codes
    document = DocumentModel()
    
    # Place with KEGG compound code (C00002 = ATP)
    place1 = document.create_place(x=100, y=100, label="ATP")
    place1.name = "C00002"
    place1.metadata = {'data_source': 'kegg_import'}
    
    # Place with KEGG compound code (C00008 = ADP)
    place2 = document.create_place(x=200, y=100, label="ADP")
    place2.name = "C00008"
    place2.metadata = {'data_source': 'kegg_import'}
    
    # Place with proper name (should not be enriched)
    place3 = document.create_place(x=300, y=100, label="Glucose")
    place3.name = "Glucose"
    place3.metadata = {'data_source': 'kegg_import'}
    
    # Transition with KEGG reaction code (R00086 = Hexokinase)
    trans1 = document.create_transition(x=150, y=200, label="Hexokinase")
    trans1.name = "R00086"
    trans1.metadata = {'data_source': 'kegg_import'}
    
    # Transition with proper name (should not be enriched)
    trans2 = document.create_transition(x=250, y=200, label="PFK")
    trans2.name = "PFK"
    trans2.metadata = {'data_source': 'kegg_import'}
    
    # Manual model place (should not be enriched)
    place4 = document.create_place(x=400, y=100, label="Manual")
    place4.name = "C00001"
    place4.metadata = {'data_source': 'manual'}
    
    print("Before enrichment:")
    print(f"  Place 1: {place1.name}")
    print(f"  Place 2: {place2.name}")
    print(f"  Place 3: {place3.name}")
    print(f"  Place 4 (manual): {place4.name}")
    print(f"  Transition 1: {trans1.name}")
    print(f"  Transition 2: {trans2.name}")
    print()
    
    # Enrich
    print("Enriching...")
    result = enrich_kegg_names(document, progress_callback=progress_callback)
    print()
    
    print("After enrichment:")
    print(f"  Place 1: {place1.name}")
    print(f"  Place 2: {place2.name}")
    print(f"  Place 3: {place3.name} (unchanged)")
    print(f"  Place 4 (manual): {place4.name} (unchanged)")
    print(f"  Transition 1: {trans1.name}")
    print(f"  Transition 2: {trans2.name} (unchanged)")
    print()
    
    print("Statistics:")
    print(f"  Places enriched: {result.places_enriched}")
    print(f"  Transitions enriched: {result.transitions_enriched}")
    print(f"  Places failed: {result.places_failed}")
    print(f"  Transitions failed: {result.transitions_failed}")
    print(f"  Total API calls: {result.total_api_calls}")
    print(f"  Duration: {result.duration_seconds:.2f} seconds")
    print()
    
    if result.details:
        print("Details:")
        for old_name, new_name in result.details.items():
            print(f"  {old_name} → {new_name}")
    
    print()
    print("✓ Enrichment complete")
    
    # Verify
    assert place1.name == "ATP", f"Expected ATP, got {place1.name}"
    assert place2.name == "ADP", f"Expected ADP, got {place2.name}"
    assert place3.name == "Glucose", "Glucose should not change"
    assert place4.name == "C00001", "Manual model should not change"
    assert trans2.name == "PFK", "PFK should not change"
    
    print("✓ All assertions passed")


if __name__ == "__main__":
    test_enrichment()
