#!/usr/bin/env python3
"""
Diagnostic script to identify spurious coordinates in SBML import.

Analyzes coordinate distributions to find:
- Outliers (> 3 std devs from mean)
- Suspiciously round numbers (e.g., 400.0, 300.0 defaults)
- NaN or Inf values
- Overlapping coordinates
- Very large or very small values

Usage:
    python3 test_sbml_coordinates.py <sbml_file>
"""

import sys
import logging
import statistics
from collections import defaultdict

# Add src to path
sys.path.insert(0, '/home/simao/projetos/shypn/src')

from shypn.data.pathway.sbml_parser import SBMLParser
from shypn.data.pathway.pathway_postprocessor import PathwayPostProcessor

logging.basicConfig(level=logging.WARNING, format='%(levelname)s: %(message)s')


def analyze_coordinates(processed_pathway):
    """Analyze coordinates for suspicious patterns."""
    
    positions = processed_pathway.positions
    
    if not positions:
        print("❌ No positions found!")
        return
    
    # Separate places and transitions
    places = {}
    transitions = {}
    
    for obj_id, coords in positions.items():
        # Heuristic: species IDs vs reaction IDs
        # In practice, you might need to check against processed_pathway.species/reactions
        if any(r.id == obj_id for r in processed_pathway.reactions):
            transitions[obj_id] = coords
        else:
            places[obj_id] = coords
    
    print(f"\n{'='*70}")
    print(f"COORDINATE ANALYSIS")
    print(f"{'='*70}")
    print(f"Total objects: {len(positions)}")
    print(f"  Places: {len(places)}")
    print(f"  Transitions: {len(transitions)}")
    
    # Extract all X and Y values
    all_x = [x for x, y in positions.values()]
    all_y = [y for x, y in positions.values()]
    
    # Basic statistics
    print(f"\n{'='*70}")
    print("RANGE ANALYSIS")
    print(f"{'='*70}")
    print(f"X range: {min(all_x):.2f} to {max(all_x):.2f} (width: {max(all_x)-min(all_x):.2f})")
    print(f"Y range: {min(all_y):.2f} to {max(all_y):.2f} (height: {max(all_y)-min(all_y):.2f})")
    
    if len(all_x) > 1:
        x_mean = statistics.mean(all_x)
        x_median = statistics.median(all_x)
        x_stdev = statistics.stdev(all_x)
        y_mean = statistics.mean(all_y)
        y_median = statistics.median(all_y)
        y_stdev = statistics.stdev(all_y)
        
        print(f"\n{'='*70}")
        print("STATISTICAL ANALYSIS")
        print(f"{'='*70}")
        print(f"X: mean={x_mean:.2f}, median={x_median:.2f}, stdev={x_stdev:.2f}")
        print(f"Y: mean={y_mean:.2f}, median={y_median:.2f}, stdev={y_stdev:.2f}")
    else:
        x_mean = x_median = x_stdev = all_x[0] if all_x else 0
        y_mean = y_median = y_stdev = all_y[0] if all_y else 0
    
    # Check for NaN/Inf
    print(f"\n{'='*70}")
    print("INVALID VALUES CHECK")
    print(f"{'='*70}")
    invalid = []
    for obj_id, (x, y) in positions.items():
        import math
        if math.isnan(x) or math.isnan(y) or math.isinf(x) or math.isinf(y):
            invalid.append((obj_id, x, y))
    
    if invalid:
        print(f"❌ FOUND {len(invalid)} INVALID COORDINATES:")
        for obj_id, x, y in invalid:
            print(f"  {obj_id}: x={x}, y={y}")
    else:
        print("✓ No NaN or Inf values found")
    
    # Check for outliers (> 3 std devs)
    print(f"\n{'='*70}")
    print("OUTLIER DETECTION (>3 std devs)")
    print(f"{'='*70}")
    outliers = []
    for obj_id, (x, y) in positions.items():
        x_zscore = abs((x - x_mean) / x_stdev) if x_stdev > 0 else 0
        y_zscore = abs((y - y_mean) / y_stdev) if y_stdev > 0 else 0
        if x_zscore > 3 or y_zscore > 3:
            obj_type = 'T' if obj_id in transitions else 'P'
            outliers.append((obj_id, x, y, x_zscore, y_zscore, obj_type))
    
    if outliers:
        print(f"⚠️  FOUND {len(outliers)} OUTLIERS:")
        for obj_id, x, y, x_z, y_z, obj_type in sorted(outliers, key=lambda t: max(t[3], t[4]), reverse=True):
            print(f"  [{obj_type}] {obj_id:20s}: x={x:8.2f} (z={x_z:.2f}), y={y:8.2f} (z={y_z:.2f})")
    else:
        print("✓ No statistical outliers found")
    
    # Check for default/fallback coordinates (suspiciously round numbers)
    print(f"\n{'='*70}")
    print("DEFAULT COORDINATE CHECK")
    print(f"{'='*70}")
    defaults = []
    common_defaults = [
        (100.0, 100.0), (200.0, 200.0), (300.0, 300.0), (400.0, 300.0),
        (400.0, 400.0), (500.0, 500.0), (0.0, 0.0)
    ]
    for obj_id, coords in positions.items():
        if coords in common_defaults:
            obj_type = 'T' if obj_id in transitions else 'P'
            defaults.append((obj_id, coords[0], coords[1], obj_type))
    
    if defaults:
        print(f"⚠️  FOUND {len(defaults)} DEFAULT COORDINATES:")
        for obj_id, x, y, obj_type in defaults:
            print(f"  [{obj_type}] {obj_id:20s}: ({x:.1f}, {y:.1f})")
    else:
        print("✓ No obvious default coordinates found")
    
    # Check for overlaps (same coordinates)
    print(f"\n{'='*70}")
    print("OVERLAP CHECK")
    print(f"{'='*70}")
    coord_map = defaultdict(list)
    for obj_id, coords in positions.items():
        # Round to 1 decimal to catch near-overlaps
        rounded = (round(coords[0], 1), round(coords[1], 1))
        coord_map[rounded].append(obj_id)
    
    overlaps = {coords: ids for coords, ids in coord_map.items() if len(ids) > 1}
    
    if overlaps:
        print(f"⚠️  FOUND {len(overlaps)} OVERLAPPING COORDINATES:")
        for coords, ids in sorted(overlaps.items(), key=lambda item: len(item[1]), reverse=True):
            print(f"  ({coords[0]:.1f}, {coords[1]:.1f}): {len(ids)} objects")
            for obj_id in ids:
                obj_type = 'T' if obj_id in transitions else 'P'
                actual_coords = positions[obj_id]
                print(f"    [{obj_type}] {obj_id:20s}: ({actual_coords[0]:.2f}, {actual_coords[1]:.2f})")
    else:
        print("✓ No overlapping coordinates found")
    
    # Print all coordinates sorted by Y, then X
    print(f"\n{'='*70}")
    print("ALL COORDINATES (sorted by Y, then X)")
    print(f"{'='*70}")
    for obj_id, (x, y) in sorted(positions.items(), key=lambda item: (item[1][1], item[1][0])):
        obj_type = 'Trans' if obj_id in transitions else 'Place'
        print(f"{obj_type:6s} {obj_id:25s}: x={x:8.2f}, y={y:8.2f}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 test_sbml_coordinates.py <sbml_file>")
        print("\nOr run without arguments to use internal test:")
        
        # Create internal test
        from shypn.data.pathway.pathway_data import Species, Reaction, PathwayData
        
        print("\n" + "="*70)
        print("Running internal test with complex branching pathway...")
        print("="*70)
        
        species = [Species(id='s0', name='Root', initial_concentration=10.0)]
        reactions = []
        
        # Create branching structure
        for i in range(1, 4):
            species.append(Species(id=f's{i}', name=f'L1_{i}', initial_concentration=0.0))
            reactions.append(Reaction(id=f'r0_{i}', name=f'R0_{i}',
                                     reactants=[('s0', 1.0)], products=[(f's{i}', 1.0)]))
        
        for parent in range(1, 4):
            for child_idx in range(2):
                sid = f's{parent}_{child_idx}'
                species.append(Species(id=sid, name=f'L2_{parent}_{child_idx}', initial_concentration=0.0))
                reactions.append(Reaction(id=f'r{parent}_{child_idx}', name=f'R{parent}_{child_idx}',
                                         reactants=[(f's{parent}', 1.0)], products=[(sid, 1.0)]))
        
        pathway = PathwayData(species=species, reactions=reactions, compartments={}, 
                             metadata={'name': 'Internal Test'})
        
        postprocessor = PathwayPostProcessor(use_tree_layout=True)
        processed = postprocessor.process(pathway)
        
        analyze_coordinates(processed)
        return
    
    # Parse SBML file
    sbml_file = sys.argv[1]
    print(f"\n{'='*70}")
    print(f"PARSING SBML FILE: {sbml_file}")
    print(f"{'='*70}")
    
    parser = SBMLParser()
    pathway = parser.parse(sbml_file)
    
    if not pathway:
        print("❌ Failed to parse SBML file")
        return
    
    print(f"✓ Parsed {len(pathway.species)} species, {len(pathway.reactions)} reactions")
    
    # Post-process with tree layout
    print(f"\n{'='*70}")
    print("POST-PROCESSING WITH TREE LAYOUT")
    print(f"{'='*70}")
    
    postprocessor = PathwayPostProcessor(use_tree_layout=True)
    processed = postprocessor.process(pathway)
    
    # Analyze
    analyze_coordinates(processed)


if __name__ == '__main__':
    main()
