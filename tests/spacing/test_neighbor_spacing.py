#!/usr/bin/env python3
"""
Debug script to find discrepant neighbor coordinates in tree layout.

Analyzes coordinate spacing between neighbors in the same layer to find
unusually large or small gaps that indicate layout problems.
"""

import sys
import statistics
sys.path.insert(0, '/home/simao/projetos/shypn/src')

from shypn.data.pathway.pathway_data import Species, Reaction, PathwayData
from shypn.data.pathway.pathway_postprocessor import PathwayPostProcessor
from collections import defaultdict


def analyze_neighbor_spacing(processed_pathway):
    """Analyze spacing between neighbors in same layer."""
    
    positions = processed_pathway.positions
    
    # Group by Y coordinate (layer)
    layers = defaultdict(list)
    for obj_id, (x, y) in positions.items():
        # Round Y to group into layers (tolerance for floating point)
        layer_y = round(y / 10) * 10
        layers[layer_y].append((obj_id, x, y))
    
    print(f"\n{'='*70}")
    print("NEIGHBOR SPACING ANALYSIS")
    print(f"{'='*70}")
    print(f"Total layers: {len(layers)}")
    
    all_gaps = []
    problematic_layers = []
    
    for layer_y in sorted(layers.keys()):
        layer_objects = sorted(layers[layer_y], key=lambda t: t[1])  # Sort by X
        
        if len(layer_objects) < 2:
            continue
        
        print(f"\nLayer Y≈{layer_y:.0f}: {len(layer_objects)} objects")
        
        gaps = []
        for i in range(len(layer_objects) - 1):
            obj1_id, x1, y1 = layer_objects[i]
            obj2_id, x2, y2 = layer_objects[i + 1]
            gap = x2 - x1
            gaps.append(gap)
            all_gaps.append(gap)
        
        if gaps:
            min_gap = min(gaps)
            max_gap = max(gaps)
            avg_gap = statistics.mean(gaps)
            stdev_gap = statistics.stdev(gaps) if len(gaps) > 1 else 0
            
            print(f"  Gaps: min={min_gap:.1f}, max={max_gap:.1f}, avg={avg_gap:.1f}, stdev={stdev_gap:.1f}")
            
            # Check for discrepant gaps (>2 std devs from mean)
            if stdev_gap > 0:
                discrepant = []
                for i, gap in enumerate(gaps):
                    z_score = abs((gap - avg_gap) / stdev_gap)
                    if z_score > 2:
                        obj1_id = layer_objects[i][0]
                        obj2_id = layer_objects[i + 1][0]
                        discrepant.append((obj1_id, obj2_id, gap, z_score))
                
                if discrepant:
                    print(f"  ⚠️  {len(discrepant)} discrepant gaps:")
                    for obj1, obj2, gap, z in discrepant:
                        print(f"      {obj1:20s} → {obj2:20s}: {gap:6.1f}px (z={z:.1f})")
                    problematic_layers.append((layer_y, discrepant))
    
    # Overall statistics
    if all_gaps:
        print(f"\n{'='*70}")
        print("OVERALL STATISTICS")
        print(f"{'='*70}")
        print(f"Total gaps analyzed: {len(all_gaps)}")
        print(f"Min gap: {min(all_gaps):.1f}px")
        print(f"Max gap: {max(all_gaps):.1f}px")
        print(f"Avg gap: {statistics.mean(all_gaps):.1f}px")
        print(f"Stdev: {statistics.stdev(all_gaps):.1f}px" if len(all_gaps) > 1 else "Stdev: N/A")
        
        # Check for extremely discrepant gaps
        if len(all_gaps) > 1:
            overall_mean = statistics.mean(all_gaps)
            overall_stdev = statistics.stdev(all_gaps)
            extreme = [g for g in all_gaps if abs(g - overall_mean) > 3 * overall_stdev]
            
            if extreme:
                print(f"\n⚠️  {len(extreme)} EXTREME gaps (>3σ from mean): {sorted(extreme)}")
    
    return problematic_layers


def main():
    # Create complex test pathway
    species = []
    reactions = []
    
    # Create branching structure with different widths at different levels
    species.append(Species(id='root', name='Root', initial_concentration=10.0))
    
    # Level 1: 3 children
    for i in range(3):
        sid = f'l1_{i}'
        species.append(Species(id=sid, name=f'L1_{i}', initial_concentration=0.0))
        reactions.append(Reaction(id=f'r0_{i}', name=f'R0_{i}',
                                 reactants=[('root', 1.0)], products=[(sid, 1.0)]))
    
    # Level 2: First child has 4 children, second has 2, third has 3
    children_counts = [4, 2, 3]
    for parent_idx, num_children in enumerate(children_counts):
        parent_id = f'l1_{parent_idx}'
        for child_idx in range(num_children):
            sid = f'l2_{parent_idx}_{child_idx}'
            species.append(Species(id=sid, name=f'L2_{parent_idx}_{child_idx}', initial_concentration=0.0))
            reactions.append(Reaction(id=f'r1_{parent_idx}_{child_idx}', name=f'R1_{parent_idx}_{child_idx}',
                                     reactants=[(parent_id, 1.0)], products=[(sid, 1.0)]))
    
    pathway = PathwayData(species=species, reactions=reactions, compartments={}, 
                         metadata={'name': 'Asymmetric Test'})
    
    print("="*70)
    print("TESTING ASYMMETRIC BRANCHING PATHWAY")
    print("="*70)
    print(f"Structure: Root → [4,2,3] children at L2")
    
    postprocessor = PathwayPostProcessor(use_tree_layout=True)
    processed = postprocessor.process(pathway)
    
    problematic = analyze_neighbor_spacing(processed)
    
    if problematic:
        print(f"\n{'='*70}")
        print(f"SUMMARY: Found {len(problematic)} layers with discrepant gaps")
        print(f"{'='*70}")
    else:
        print(f"\n{'='*70}")
        print("✓ No discrepant neighbor spacing found!")
        print(f"{'='*70}")


if __name__ == '__main__':
    main()
