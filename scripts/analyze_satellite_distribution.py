"""Detailed analysis of satellite distribution around hubs."""

import sys
from pathlib import Path
import math

# Add src to Python path
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root / "src"))

from shypn.data.canvas.document_model import DocumentModel
from shypn.layout.sscc import SolarSystemLayoutEngine


def analyze_satellite_distribution():
    """Analyze how satellites are distributed around their hubs."""
    
    print("=" * 80)
    print("SATELLITE DISTRIBUTION ANALYSIS")
    print("=" * 80)
    print()
    
    # Load model
    model_path = repo_root / "workspace" / "Test_flow" / "model" / "hub_constellation.shy"
    document = DocumentModel.load_from_file(str(model_path))
    
    print(f"Loaded: {model_path.name}")
    print(f"  Places: {len(document.places)}")
    print(f"  Transitions: {len(document.transitions)}")
    print(f"  Arcs: {len(document.arcs)}")
    print()
    
    # Apply layout with more iterations for better convergence
    engine = SolarSystemLayoutEngine(iterations=5000)  # Increased from 1000
    positions = engine.apply_layout(
        places=list(document.places),
        transitions=list(document.transitions),
        arcs=list(document.arcs)
    )
    
    # Analyze each hub and its satellites
    print("HUB SYSTEMS ANALYSIS:")
    print("=" * 80)
    print()
    
    for hub_idx, hub in enumerate(document.places, 1):
        hub_pos = positions[hub.id]
        print(f"Hub {hub_idx}: {hub.name} at ({hub_pos[0]:.1f}, {hub_pos[1]:.1f})")
        print("-" * 80)
        
        # Find satellites connected to this hub
        satellites = []
        for arc in document.arcs:
            if arc.source.id == hub.id:
                sat = arc.target
                sat_pos = positions[sat.id]
                
                # Calculate distance and angle from hub
                dx = sat_pos[0] - hub_pos[0]
                dy = sat_pos[1] - hub_pos[1]
                distance = math.sqrt(dx*dx + dy*dy)
                angle = math.degrees(math.atan2(dy, dx))
                
                satellites.append({
                    'name': sat.name,
                    'pos': sat_pos,
                    'distance': distance,
                    'angle': angle
                })
        
        # Sort by angle
        satellites.sort(key=lambda s: s['angle'])
        
        print(f"  Satellites: {len(satellites)}")
        print()
        
        if satellites:
            distances = [s['distance'] for s in satellites]
            avg_dist = sum(distances) / len(distances)
            min_dist = min(distances)
            max_dist = max(distances)
            
            print(f"  Distance from hub:")
            print(f"    Average: {avg_dist:.1f} units")
            print(f"    Min: {min_dist:.1f} units")
            print(f"    Max: {max_dist:.1f} units")
            print(f"    Spread: {max_dist - min_dist:.1f} units")
            print()
            
            print(f"  Satellite positions:")
            for sat in satellites:
                print(f"    {sat['name']:12s}: distance={sat['distance']:6.1f}, angle={sat['angle']:7.1f}°")
            print()
        
        # Check for clustering (satellites too close to each other)
        if len(satellites) > 1:
            min_sat_distance = float('inf')
            for i, sat1 in enumerate(satellites):
                for sat2 in satellites[i+1:]:
                    dx = sat2['pos'][0] - sat1['pos'][0]
                    dy = sat2['pos'][1] - sat1['pos'][1]
                    dist = math.sqrt(dx*dx + dy*dy)
                    min_sat_distance = min(min_sat_distance, dist)
            
            print(f"  Minimum satellite-to-satellite distance: {min_sat_distance:.1f} units")
            if min_sat_distance < 50:
                print(f"  ⚠️  WARNING: Satellites are clustering (< 50 units apart)")
            else:
                print(f"  ✓  Good: Satellites well-separated")
            print()
    
    # Check hub-to-hub distances
    print("=" * 80)
    print("HUB-TO-HUB DISTANCES:")
    print("=" * 80)
    print()
    
    for i, hub1 in enumerate(document.places):
        for hub2 in document.places[i+1:]:
            pos1 = positions[hub1.id]
            pos2 = positions[hub2.id]
            dx = pos2[0] - pos1[0]
            dy = pos2[1] - pos1[1]
            dist = math.sqrt(dx*dx + dy*dy)
            print(f"  {hub1.name} ↔ {hub2.name}: {dist:.1f} units")
    
    print()
    print("=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    analyze_satellite_distribution()
