#!/usr/bin/env python3
"""
Test Pure Force-Directed Layout (No Projection)

This script tests raw NetworkX spring_layout output without any geometric
post-processing. Useful for isolating physics parameter effects.

Usage:
    python scripts/test_pure_force_directed.py BIOMD0000000001
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from shypn.data.pathway.sbml_parser import SBMLParser
from shypn.data.pathway.pathway_validator import PathwayValidator
from shypn.data.pathway.pathway_postprocessor import PathwayPostProcessor


def test_pure_force_directed(biomodels_id: str, k: float = 1.5, iterations: int = 100):
    """Test pure force-directed layout without projection.
    
    Args:
        biomodels_id: BioModels identifier (e.g., BIOMD0000000001)
        k: Optimal node distance (0.5-5.0)
        iterations: Number of physics simulation steps (20-200)
    """
    
    print(f"\n{'='*70}")
    print(f"PURE FORCE-DIRECTED TEST: {biomodels_id}")
    print(f"Parameters: k={k}, iterations={iterations}")
    print(f"{'='*70}\n")
    
    # Fetch and parse SBML
    import urllib.request
    import tempfile
    
    url = f"https://www.ebi.ac.uk/biomodels/model/download/{biomodels_id}?filename={biomodels_id}_url.xml"
    temp_file = os.path.join(tempfile.gettempdir(), f"{biomodels_id}.xml")
    
    print(f"1. Fetching {biomodels_id} from BioModels...")
    try:
        urllib.request.urlretrieve(url, temp_file)
        print(f"   ✓ Downloaded to {temp_file}")
    except Exception as e:
        print(f"   ✗ Failed to download: {e}")
        return
    
    print(f"\n2. Parsing SBML file...")
    parser = SBMLParser()
    try:
        pathway = parser.parse_file(temp_file)
        print(f"   ✓ Species: {len(pathway.species)}, Reactions: {len(pathway.reactions)}")
    except Exception as e:
        print(f"   ✗ Parse failed: {e}")
        return
    
    print(f"\n3. Validating pathway...")
    validator = PathwayValidator()
    result = validator.validate(pathway)
    if result.is_valid:
        print(f"   ✓ Valid (warnings: {len(result.warnings)})")
    else:
        print(f"   ✗ Invalid (errors: {len(result.errors)})")
        for error in result.errors[:3]:
            print(f"      - {error}")
        return
    
    # Test PURE force-directed (no projection)
    print(f"\n4. Running PURE force-directed layout (no projection)...")
    print(f"   Physics parameters:")
    print(f"   - k = {k} (optimal node distance)")
    print(f"   - iterations = {iterations}")
    print(f"   - threshold = 1e-6")
    print(f"   - weight_mode = stoichiometry")
    
    postprocessor = PathwayPostProcessor(
        spacing=150.0,
        scale_factor=1.0,
        use_tree_layout=False,
        use_spiral_layout=False,
        use_raw_force_directed=True  # 🔬 BYPASS PROJECTION!
    )
    
    try:
        processed = postprocessor.process(pathway)
        
        layout_type = processed.metadata.get('layout_type', 'unknown')
        canvas_width = processed.metadata.get('canvas_width', 'N/A')
        canvas_height = processed.metadata.get('canvas_height', 'N/A')
        
        print(f"\n5. Results:")
        print(f"   Layout type: {layout_type}")
        print(f"   Canvas: {canvas_width:.0f}x{canvas_height:.0f}px")
        print(f"   Positions: {len(processed.positions)}")
        
        # Show sample positions
        if processed.positions:
            print(f"\n   Sample positions (raw physics output):")
            for i, (node_id, (x, y)) in enumerate(list(processed.positions.items())[:5]):
                print(f"      {node_id}: ({x:.1f}, {y:.1f})")
            if len(processed.positions) > 5:
                print(f"      ... and {len(processed.positions) - 5} more")
        
        print(f"\n{'='*70}")
        print(f"✓ Pure force-directed test complete!")
        print(f"  No projection applied - this is raw NetworkX spring_layout output")
        print(f"  Use Swiss Layout Palette in GUI to test different k values")
        print(f"{'='*70}\n")
        
    except Exception as e:
        print(f"\n   ✗ Layout failed: {e}")
        import traceback
        traceback.print_exc()


def parameter_sweep():
    """Test multiple parameter combinations."""
    
    print("\n" + "="*70)
    print("PARAMETER SWEEP TEST")
    print("="*70)
    
    biomodels_id = "BIOMD0000000001"
    
    test_params = [
        (0.5, 50, "Low k, few iterations"),
        (1.0, 100, "Medium k, standard iterations"),
        (2.0, 100, "High k, standard iterations"),
        (1.0, 200, "Medium k, many iterations"),
        (3.0, 50, "Very high k, few iterations"),
    ]
    
    for k, iterations, description in test_params:
        print(f"\n{'─'*70}")
        print(f"Test: {description}")
        print(f"{'─'*70}")
        test_pure_force_directed(biomodels_id, k, iterations)
        input("Press Enter to continue to next test...")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python test_pure_force_directed.py BIOMD0000000001")
        print("  python test_pure_force_directed.py BIOMD0000000001 1.5 100")
        print("  python test_pure_force_directed.py --sweep")
        sys.exit(1)
    
    if sys.argv[1] == '--sweep':
        parameter_sweep()
    else:
        biomodels_id = sys.argv[1]
        k = float(sys.argv[2]) if len(sys.argv) > 2 else 1.5
        iterations = int(sys.argv[3]) if len(sys.argv) > 3 else 100
        test_pure_force_directed(biomodels_id, k, iterations)
