#!/usr/bin/env python3
"""
Test Hierarchical Layout with Real SBML File

Tests the complete layout pipeline with BIOMD0000000001:
1. Cross-reference (KEGG) - tries first
2. Hierarchical layout - NEW fallback
3. Force-directed - final fallback

Shows which strategy was used and layout quality.
"""

import sys
import os
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Configure logging to see what's happening
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s [%(name)s]: %(message)s'
)

from shypn.data.pathway.sbml_parser import SBMLParser
from shypn.data.pathway.pathway_postprocessor import PathwayPostProcessor


def test_sbml_import(filepath: str):
    """Test SBML import with all layout strategies."""
    
    print("=" * 70)
    print("TESTING HIERARCHICAL LAYOUT WITH REAL SBML FILE")
    print("=" * 70)
    print(f"\nFile: {filepath}\n")
    
    # Phase 1: Import SBML
    print("Phase 1: Parsing SBML...")
    print("-" * 70)
    
    parser = SBMLParser()
    
    try:
        pathway = parser.parse_file(filepath)
        print(f"✓ Parsed: {len(pathway.species)} species, {len(pathway.reactions)} reactions")
    except Exception as e:
        print(f"✗ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Phase 2: Post-process with layout strategies
    print("\nPhase 2: Applying Layout Strategies...")
    print("-" * 70)
    print("Strategy priority:")
    print("  1. Cross-Reference (KEGG coordinates)")
    print("  2. Hierarchical (dependency-based) ← NEW")
    print("  3. Force-Directed (networkx)")
    print("  4. Grid (fallback)")
    print()
    
    postprocessor = PathwayPostProcessor()
    
    try:
        processed_data = postprocessor.process(pathway)
        
        print(f"\n✓ Post-processing complete")
        print(f"  Positions calculated: {len(processed_data.positions)}")
        
        # Analyze which strategy was used by checking log messages
        print("\n" + "=" * 70)
        print("LAYOUT ANALYSIS")
        print("=" * 70)
        
        # Check positions distribution
        if processed_data.positions:
            y_positions = [y for x, y in processed_data.positions.values()]
            unique_y = len(set([round(y, 0) for y in y_positions]))
            
            min_y = min(y_positions)
            max_y = max(y_positions)
            height = max_y - min_y
            
            print(f"\nVertical Distribution:")
            print(f"  Unique Y levels: {unique_y}")
            print(f"  Height range: {min_y:.1f} to {max_y:.1f} ({height:.1f} pixels)")
            print(f"  Average spacing: {height / max(unique_y - 1, 1):.1f} pixels")
            
            # Check if it's hierarchical (discrete Y levels)
            if unique_y <= len(processed_data.positions) * 0.5:
                print("\n✓ Layout appears HIERARCHICAL (discrete layers)")
            else:
                print("\n→ Layout appears CONTINUOUS (force-directed or grid)")
            
            # Show layer distribution
            print(f"\nLayer Distribution:")
            layers = {}
            for node_id, (x, y) in processed_data.positions.items():
                y_key = round(y, 0)
                if y_key not in layers:
                    layers[y_key] = []
                layers[y_key].append(node_id)
            
            for i, (y, nodes) in enumerate(sorted(layers.items())[:10]):  # Show first 10 layers
                species_in_layer = [n for n in nodes if any(s.id == n for s in pathway.species)]
                print(f"  Layer {i} (Y={y:.0f}): {len(nodes)} elements ({len(species_in_layer)} species)")
            
            if len(layers) > 10:
                print(f"  ... and {len(layers) - 10} more layers")
        
        print("\n" + "=" * 70)
        print("TEST COMPLETE")
        print("=" * 70)
        
        # Show what to look for
        print("\nWhat to Check:")
        print("  • Log messages show which strategy was used")
        print("  • Hierarchical: Discrete Y levels, clear layers")
        print("  • Force-directed: Continuous Y distribution")
        print("  • Cross-reference: Message about KEGG layout")
        
        return processed_data
        
    except Exception as e:
        print(f"\n✗ Post-processing failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Run the test."""
    
    # Test file
    test_file = "/tmp/BIOMD0000000001.xml"
    
    if not os.path.exists(test_file):
        print(f"✗ File not found: {test_file}")
        print("\nPlease download it first:")
        print("  wget -O /tmp/BIOMD0000000001.xml 'https://www.ebi.ac.uk/biomodels/model/download/BIOMD0000000001.2?filename=BIOMD0000000001_url.xml'")
        return 1
    
    processed_data = test_sbml_import(test_file)
    
    if processed_data and processed_data.positions:
        print("\n✓ SUCCESS: Layout calculated successfully!")
        return 0
    else:
        print("\n✗ FAILED: Could not calculate layout")
        return 1


if __name__ == "__main__":
    sys.exit(main())
