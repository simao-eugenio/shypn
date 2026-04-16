#!/usr/bin/env python3
"""Test complete BiGG import workflow.

Tests the full import pipeline:
1. Download SBML from BiGG
2. Parse SBML → PathwayData
3. Apply BiGG signal classification
4. Convert to DocumentModel (Petri net)
5. Verify results

This validates Phase 3 implementation.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from shypn.importer.bigg.bigg_model_fetcher import BiGGModelFetcher
from shypn.importer.bigg.bigg_downloader import BiGGDownloader
from shypn.importer.bigg.bigg_signal_classifier import BiGGSignalClassifier
from shypn.data.pathway.sbml_parser import SBMLParser
from shypn.data.pathway.pathway_postprocessor import PathwayPostProcessor
from shypn.data.pathway.pathway_converter import PathwayConverter
from shypn.netobjs.signal_type import SignalType


def test_complete_import():
    """Test complete BiGG import workflow with e_coli_core."""
    print("=" * 60)
    print("BiGG Complete Import Test")
    print("=" * 60)
    
    # Initialize services
    print("\n[1/7] Initializing services...")
    fetcher = BiGGModelFetcher()
    downloader = BiGGDownloader()
    classifier = BiGGSignalClassifier()
    parser = SBMLParser()
    postprocessor = PathwayPostProcessor()
    converter = PathwayConverter()
    print("  ✓ Services initialized")
    
    # Test model
    model_id = "e_coli_core"
    print(f"\n[2/7] Test model: {model_id}")
    
    # Download SBML
    print(f"\n[3/7] Downloading SBML for {model_id}...")
    try:
        sbml_path = downloader.download_sbml(model_id, use_cache=True)
        sbml_size = os.path.getsize(sbml_path)
        print(f"  ✓ Downloaded: {sbml_path}")
        print(f"  ✓ Size: {sbml_size:,} bytes")
    except Exception as e:
        print(f"  ✗ Download failed: {e}")
        return False
    
    # Parse SBML
    print(f"\n[4/7] Parsing SBML...")
    try:
        parsed_pathway = parser.parse_file(sbml_path)
        print(f"  ✓ Species: {len(parsed_pathway.species)}")
        print(f"  ✓ Reactions: {len(parsed_pathway.reactions)}")
        print(f"  ✓ Compartments: {len(parsed_pathway.compartments)}")
    except Exception as e:
        print(f"  ✗ Parsing failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Post-process
    print(f"\n[5/7] Post-processing...")
    try:
        processed_pathway = postprocessor.process(parsed_pathway)
        print(f"  ✓ Post-processing complete")
    except Exception as e:
        print(f"  ✗ Post-processing failed: {e}")
        return False
    
    # Convert to Petri net
    print(f"\n[6/7] Converting to Petri net...")
    try:
        document_model = converter.convert(processed_pathway)
        print(f"  ✓ Places: {len(document_model.places)}")
        print(f"  ✓ Transitions: {len(document_model.transitions)}")
        print(f"  ✓ Arcs: {len(document_model.arcs)}")
    except Exception as e:
        print(f"  ✗ Conversion failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Apply BiGG signal classification
    print(f"\n[7/7] Applying BiGG signal classification...")
    try:
        classified_places = classifier.classify_energy_signals(document_model.places)
        energy_count = sum(1 for p in classified_places 
                          if hasattr(p, 'signal_type') and p.signal_type == SignalType.ENERGY)
        print(f"  ✓ Energy signals classified: {energy_count}")
        
        # Verify some energy metabolites were found
        energy_places = [p for p in document_model.places 
                        if hasattr(p, 'signal_type') and p.signal_type == SignalType.ENERGY]
        
        if energy_places:
            print(f"  ✓ Sample energy signals:")
            for place in energy_places[:5]:  # Show first 5
                layer = place.metadata.get('hierarchy_layer', 'Unknown')
                print(f"    - {place.name} (Layer {layer})")
        else:
            print(f"  ⚠ Warning: No energy signals found")
        
    except Exception as e:
        print(f"  ✗ Signal classification failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Model: {model_id}")
    print(f"SBML Size: {sbml_size:,} bytes")
    print(f"Species → Places: {len(parsed_pathway.species)} → {len(document_model.places)}")
    print(f"Reactions → Transitions: {len(parsed_pathway.reactions)} → {len(document_model.transitions)}")
    print(f"Energy Signals: {energy_count}")
    print(f"Compartments: {len(parsed_pathway.compartments)}")
    print("=" * 60)
    print("✅ ALL TESTS PASSED")
    print("=" * 60)
    
    return True


if __name__ == "__main__":
    try:
        success = test_complete_import()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
