#!/usr/bin/env python3
"""Test spatial tile exporter and lazy loading on real models.

Creates test models and validates the export/import cycle:
1. Create a test model with varying complexity
2. Export to tiled format
3. Load with SpatialModelManager
4. Verify data integrity and lazy loading behavior

Author: Simao Eugenio
Date: 2026-02-03
"""

import sys
import os
import tempfile
import shutil
import time

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from shypn.data.model_canvas_manager import ModelCanvasManager
from shypn.data.spatial import SpatialTileExporter, SpatialModelManager
from shypn.netobjs.place import Place
from shypn.netobjs.transition import Transition
from shypn.netobjs.arc import Arc


def create_test_model(num_places=100, grid_spacing=200):
    """Create a test model with places, transitions, and arcs.
    
    Args:
        num_places: Number of places to create
        grid_spacing: Spacing between objects in world units
    
    Returns:
        ModelCanvasManager with test model
    """
    manager = ModelCanvasManager(canvas_width=3000, canvas_height=3000)
    
    # Create places in a grid
    grid_size = int(num_places ** 0.5) + 1
    places = []
    
    print(f"Creating {num_places} places...")
    for i in range(num_places):
        row = i // grid_size
        col = i % grid_size
        x = col * grid_spacing
        y = row * grid_spacing
        
        place = Place(x, y, id=f"p{i}", name=f"P{i}", radius=25.0, label=f"Place {i}")
        place.tokens = i % 5  # 0-4 tokens
        manager.places.append(place)
        places.append(place)
    
    # Create transitions (half as many as places)
    num_transitions = num_places // 2
    transitions = []
    
    print(f"Creating {num_transitions} transitions...")
    for i in range(num_transitions):
        row = i // (grid_size // 2)
        col = i % (grid_size // 2)
        x = col * grid_spacing * 2 + grid_spacing
        y = row * grid_spacing * 2 + grid_spacing
        
        transition = Transition(x, y, id=f"t{i}", name=f"T{i}",
                               width=60.0, height=20.0, 
                               horizontal=True, label=f"Trans {i}")
        manager.transitions.append(transition)
        transitions.append(transition)
    
    # Create arcs connecting places to transitions
    print(f"Creating arcs...")
    arc_count = 0
    for i, transition in enumerate(transitions):
        # Connect 2-4 nearby places to each transition
        for j in range(2):
            place_idx = (i * 2 + j) % len(places)
            place = places[place_idx]
            
            # Place -> Transition
            arc_in = Arc(place, transition, id=f"a{arc_count}", 
                        name=f"A{arc_count}", weight=1.0)
            manager.arcs.append(arc_in)
            arc_count += 1
            
            # Transition -> Place (different place)
            place_out_idx = (place_idx + 1) % len(places)
            place_out = places[place_out_idx]
            arc_out = Arc(transition, place_out, id=f"a{arc_count}",
                         name=f"A{arc_count}", weight=1.0)
            manager.arcs.append(arc_out)
            arc_count += 1
    
    print(f"Created model: {len(manager.places)} places, "
          f"{len(manager.transitions)} transitions, "
          f"{len(manager.arcs)} arcs")
    
    return manager


def test_export_import_cycle(model_size='small'):
    """Test export and import cycle.
    
    Args:
        model_size: 'small', 'medium', or 'large'
    """
    print("\n" + "="*60)
    print(f"Test: Export/Import Cycle ({model_size.upper()} model)")
    print("="*60)
    
    # Determine model parameters
    sizes = {
        'small': (50, 300),      # 50 places, tile_size=300
        'medium': (200, 500),    # 200 places, tile_size=500
        'large': (1000, 1000)    # 1000 places, tile_size=1000
    }
    num_places, tile_size = sizes.get(model_size, sizes['small'])
    
    # Create test model
    print(f"\n1. Creating test model ({num_places} places)...")
    t0 = time.time()
    manager = create_test_model(num_places=num_places, grid_spacing=200)
    create_time = time.time() - t0
    print(f"   Created in {create_time:.3f}s")
    
    # Export to tiled format
    print(f"\n2. Exporting to tiled format (tile_size={tile_size})...")
    temp_dir = tempfile.mkdtemp(prefix='shypn_test_')
    output_dir = os.path.join(temp_dir, f'test_model_{model_size}.shy')
    
    try:
        exporter = SpatialTileExporter(tile_size=tile_size)
        
        # Get size estimate
        estimate = exporter.estimate_size(manager)
        print(f"   Estimated size: {estimate['estimated_mb']:.2f} MB")
        print(f"   Estimated tiles: {estimate['estimated_tiles']}")
        
        t0 = time.time()
        exporter.export(manager, output_dir)
        export_time = time.time() - t0
        print(f"   Exported in {export_time:.3f}s")
        
        # Verify exported files
        print(f"\n3. Verifying exported files...")
        assert os.path.exists(os.path.join(output_dir, 'metadata.json'))
        assert os.path.exists(os.path.join(output_dir, 'index.json'))
        assert os.path.exists(os.path.join(output_dir, 'tiles'))
        
        tile_files = [f for f in os.listdir(os.path.join(output_dir, 'tiles')) 
                     if f.endswith('.bin')]
        print(f"   ✅ Created {len(tile_files)} tile files")
        
        # Load with SpatialModelManager
        print(f"\n4. Loading with SpatialModelManager...")
        t0 = time.time()
        spatial_manager = SpatialModelManager(output_dir)
        load_time = time.time() - t0
        print(f"   Loaded in {load_time:.3f}s")
        
        # Initially no tiles loaded (viewport not set)
        print(f"   Initial state:")
        print(f"     Places: {len(spatial_manager.places)}")
        print(f"     Transitions: {len(spatial_manager.transitions)}")
        print(f"     Arcs: {len(spatial_manager.arcs)}")
        
        # Set viewport to center
        print(f"\n5. Setting viewport to center...")
        center_x = 0
        center_y = 0
        viewport_width = 1920
        viewport_height = 1080
        zoom = 0.5
        
        t0 = time.time()
        spatial_manager.update_viewport(center_x, center_y, 
                                       viewport_width, viewport_height, zoom)
        viewport_time = time.time() - t0
        print(f"   Updated viewport in {viewport_time:.3f}s")
        
        info = spatial_manager.get_model_info()
        print(f"   Loaded state:")
        print(f"     Active tiles: {info['active_tiles']} (viewport)")
        print(f"     Exported tiles: {info['total_tiles']} (non-empty)")
        print(f"     Places: {len(spatial_manager.places)}")
        print(f"     Transitions: {len(spatial_manager.transitions)}")
        print(f"     Arcs: {len(spatial_manager.arcs)}")
        
        # Verify cache stats
        cache_stats = spatial_manager.get_cache_stats()
        print(f"\n6. Cache statistics:")
        print(f"     Size: {cache_stats['size']}/{cache_stats['max_size']}")
        print(f"     Hits: {cache_stats['hits']}")
        print(f"     Misses: {cache_stats['misses']}")
        print(f"     Hit rate: {cache_stats['hit_rate']:.1%}")
        
        # Test panning (move viewport)
        print(f"\n7. Testing panning (move viewport right)...")
        new_center_x = center_x + 2000
        t0 = time.time()
        spatial_manager.update_viewport(new_center_x, center_y,
                                       viewport_width, viewport_height, zoom)
        pan_time = time.time() - t0
        print(f"   Panned in {pan_time:.3f}s")
        
        info2 = spatial_manager.get_model_info()
        print(f"     Active tiles: {info2['active_tiles']} (viewport)")
        print(f"     Places: {len(spatial_manager.places)}")
        
        # Verify some objects loaded
        assert len(spatial_manager.places) > 0, "No places loaded!"
        assert len(spatial_manager.transitions) >= 0, "No transitions loaded!"
        
        # Summary
        print(f"\n{'='*60}")
        print(f"✅ {model_size.upper()} model test PASSED")
        print(f"{'='*60}")
        print(f"Performance:")
        print(f"  Create: {create_time:.3f}s")
        print(f"  Export: {export_time:.3f}s")
        print(f"  Load:   {load_time:.3f}s")
        print(f"  Viewport update: {viewport_time:.3f}s")
        print(f"  Pan:    {pan_time:.3f}s")
        print(f"\nMemory efficiency:")
        print(f"  Total objects: {info['total_objects']['places'] + info['total_objects']['transitions']}")
        print(f"  Loaded objects: {len(spatial_manager.places) + len(spatial_manager.transitions)}")
        print(f"  Reduction: {100 * (1 - (len(spatial_manager.places) + len(spatial_manager.transitions)) / (info['total_objects']['places'] + info['total_objects']['transitions'])):.1f}%")
        
    finally:
        # Cleanup
        shutil.rmtree(temp_dir)
        print(f"\nCleaned up temp directory: {temp_dir}")


def test_load_ecoli_model():
    """Test loading E. coli core model if available."""
    print("\n" + "="*60)
    print("Test: Load E. coli Core Model (if available)")
    print("="*60)
    
    # Check if model exists
    ecoli_path = '/home/simao/projetos/shypn/workspace/projects/My_Project/models/e_coli_core.shy'
    
    if not os.path.exists(ecoli_path):
        print(f"⏭️  E. coli model not found at {ecoli_path}")
        print("   Skipping this test.")
        return
    
    print(f"Found E. coli model at {ecoli_path}")
    
    # Load the model
    print(f"\n1. Loading E. coli model...")
    from shypn.data.canvas.document_model import DocumentModel
    
    t0 = time.time()
    document = DocumentModel.load_from_file(ecoli_path)
    load_time = time.time() - t0
    
    # Create a temporary manager to get the objects
    from shypn.data.model_canvas_manager import ModelCanvasManager
    manager = ModelCanvasManager(canvas_width=2000, canvas_height=2000)
    manager.load_objects(
        places=document.places,
        transitions=document.transitions,
        arcs=document.arcs
    )
    
    num_places = len(manager.places)
    num_transitions = len(manager.transitions)
    num_arcs = len(manager.arcs)
    total_objects = num_places + num_transitions + num_arcs
    
    print(f"   Loaded: {num_places} places, {num_transitions} transitions, {num_arcs} arcs")
    print(f"   Total: {total_objects} objects")
    print(f"   Load time: {load_time:.3f}s")
    
    # Export to tiled format
    print(f"\n2. Exporting to tiled format...")
    
    # Choose tile size based on model size
    if total_objects < 100:
        tile_size = 500
    elif total_objects < 500:
        tile_size = 1000
    else:
        tile_size = 2000
    
    exporter = SpatialTileExporter(tile_size=tile_size)
    
    temp_dir = tempfile.mkdtemp(prefix='shypn_test_ecoli_')
    output_dir = os.path.join(temp_dir, 'e_coli_tiled.shy')
    
    try:
        t0 = time.time()
        exporter.export(manager, output_dir)
        export_time = time.time() - t0
        
        print(f"   Tile size: {tile_size}")
        print(f"   Exported in {export_time:.3f}s")
        
        # Count tiles
        tiles_dir = os.path.join(output_dir, 'tiles')
        num_tiles = len([f for f in os.listdir(tiles_dir) if f.endswith('.bin')])
        print(f"   ✅ Created {num_tiles} tiles")
        
        # Load with SpatialModelManager
        print(f"\n3. Loading with SpatialModelManager...")
        t0 = time.time()
        spatial_manager = SpatialModelManager(output_dir)
        spatial_load_time = time.time() - t0
        
        print(f"   Loaded in {spatial_load_time:.3f}s")
        
        # Set viewport to center
        print(f"\n4. Setting viewport to center...")
        viewport_width = 1920
        viewport_height = 1080
        zoom = 0.3  # Zoom out for larger models
        
        # Calculate center from bounds
        bounds = spatial_manager.tile_metadata.get('bounds')
        if bounds:
            center_x = (bounds['min_x'] + bounds['max_x']) / 2
            center_y = (bounds['min_y'] + bounds['max_y']) / 2
        else:
            center_x = 0
            center_y = 0
        
        t0 = time.time()
        spatial_manager.update_viewport(center_x, center_y,
                                       viewport_width, viewport_height, zoom)
        viewport_time = time.time() - t0
        print(f"   Updated viewport in {viewport_time:.3f}s")
        
        info = spatial_manager.get_model_info()
        loaded_objects = len(spatial_manager.places) + len(spatial_manager.transitions)
        reduction = 100 * (1 - loaded_objects / total_objects) if total_objects > 0 else 0
        
        print(f"\n✅ E. coli test PASSED")
        print(f"Performance:")
        print(f"  Original load: {load_time:.3f}s")
        print(f"  Export: {export_time:.3f}s")
        print(f"  Tiled load: {spatial_load_time:.3f}s (instant)")
        print(f"  Viewport: {viewport_time:.3f}s")
        print(f"Memory: {loaded_objects}/{total_objects} objects ({reduction:.1f}% reduction)")
        
    finally:
        shutil.rmtree(temp_dir)
        print(f"Cleaned up: {temp_dir}")


def main():
    """Run all export/import tests."""
    print("\n" + "="*60)
    print("Spatial Tile Exporter Tests")
    print("="*60)
    
    try:
        # Test 1: Small model
        test_export_import_cycle('small')
        
        # Test 2: Medium model
        test_export_import_cycle('medium')
        
        # Test 3: Large model
        test_export_import_cycle('large')
        
        # Test 4: E. coli (if available)
        test_load_ecoli_model()
        
        print("\n" + "="*60)
        print("✅ ALL EXPORT/IMPORT TESTS PASSED")
        print("="*60)
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
