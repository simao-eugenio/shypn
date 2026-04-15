#!/usr/bin/env python3
"""Test spatial partitioning core infrastructure.

Tests the tile coordinate system, cache, and serialization components
of the spatial partitioning system.

Author: Simao Eugenio
Date: 2026-02-03
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from shypn.data.spatial.tile_coord import TileCoord, TileGrid
from shypn.data.spatial.tile_cache import TileCache
from shypn.data.spatial.tile_serializer import TileSerializer


def test_tile_coord():
    """Test TileCoord class."""
    print("\n" + "="*60)
    print("Test 1: TileCoord")
    print("="*60)
    
    # Create tile
    tile = TileCoord(0, 0)
    print(f"Created tile: {tile}")
    
    # Test neighbors
    neighbors = tile.neighbors(include_diagonals=True)
    print(f"Neighbors (with diagonals): {len(neighbors)} tiles")
    assert len(neighbors) == 8, "Should have 8 neighbors with diagonals"
    
    cardinal = tile.neighbors(include_diagonals=False)
    print(f"Neighbors (cardinal only): {len(cardinal)} tiles")
    assert len(cardinal) == 4, "Should have 4 neighbors without diagonals"
    
    # Test distance
    other = TileCoord(3, 4)
    euclidean = tile.distance_to(other)
    manhattan = tile.manhattan_distance_to(other)
    print(f"Distance to {other}:")
    print(f"  Euclidean: {euclidean:.2f}")
    print(f"  Manhattan: {manhattan}")
    
    print("✅ TileCoord tests passed")


def test_tile_grid():
    """Test TileGrid class."""
    print("\n" + "="*60)
    print("Test 2: TileGrid")
    print("="*60)
    
    grid = TileGrid(tile_size=1000.0)
    print(f"Created grid: {grid}")
    
    # Test world to tile conversion
    tile1 = grid.world_to_tile(1500.0, 2000.0)
    print(f"World (1500, 2000) → Tile {tile1}")
    assert tile1 == TileCoord(1, 2), "Incorrect tile conversion"
    
    # Test negative coordinates
    tile2 = grid.world_to_tile(-500.0, -1500.0)
    print(f"World (-500, -1500) → Tile {tile2}")
    assert tile2 == TileCoord(-1, -2), "Incorrect negative tile conversion"
    
    # Test tile to world bounds
    bounds = grid.tile_to_world_bounds(TileCoord(0, 0))
    print(f"Tile (0, 0) bounds: {bounds}")
    assert bounds == (0.0, 0.0, 1000.0, 1000.0), "Incorrect bounds"
    
    # Test tiles in bounds
    tiles = grid.get_tiles_in_bounds(500, 500, 2500, 1500)
    print(f"Tiles in bounds (500, 500) to (2500, 1500): {len(tiles)} tiles")
    print(f"  Tiles: {sorted(tiles, key=lambda t: (t.x, t.y))}")
    
    # Test tiles for line
    line_tiles = grid.get_tiles_for_line(0, 0, 2500, 2500, margin=100)
    print(f"Tiles for line (0,0) to (2500,2500): {len(line_tiles)} tiles")
    
    print("✅ TileGrid tests passed")


def test_tile_cache():
    """Test TileCache class."""
    print("\n" + "="*60)
    print("Test 3: TileCache")
    print("="*60)
    
    cache = TileCache(max_tiles=3)
    print(f"Created cache: {cache}")
    
    # Add tiles
    tile1 = TileCoord(0, 0)
    tile2 = TileCoord(1, 1)
    tile3 = TileCoord(2, 2)
    tile4 = TileCoord(3, 3)
    
    cache.put(tile1, {'data': 'tile1'})
    cache.put(tile2, {'data': 'tile2'})
    cache.put(tile3, {'data': 'tile3'})
    print(f"Added 3 tiles, cache size: {len(cache)}")
    
    # Test cache hit
    data = cache.get(tile1)
    assert data == {'data': 'tile1'}, "Cache miss on existing tile"
    print(f"Cache HIT for {tile1}")
    
    # Test eviction (tile1 was just accessed, tile2 is LRU)
    cache.put(tile4, {'data': 'tile4'})
    print(f"Added 4th tile, cache size: {len(cache)} (should evict LRU)")
    
    # tile2 should be evicted
    data2 = cache.get(tile2)
    assert data2 is None, "tile2 should have been evicted"
    print(f"Cache MISS for {tile2} (evicted)")
    
    # tile1 should still be there (was accessed recently)
    data1 = cache.get(tile1)
    assert data1 == {'data': 'tile1'}, "tile1 should still be cached"
    print(f"Cache HIT for {tile1} (not evicted)")
    
    # Get stats
    stats = cache.get_stats()
    print(f"\nCache statistics:")
    print(f"  Size: {stats['size']}/{stats['max_size']}")
    print(f"  Hits: {stats['hits']}")
    print(f"  Misses: {stats['misses']}")
    print(f"  Evictions: {stats['evictions']}")
    print(f"  Hit rate: {stats['hit_rate']:.1%}")
    
    print("✅ TileCache tests passed")


def test_tile_serializer():
    """Test TileSerializer class."""
    print("\n" + "="*60)
    print("Test 4: TileSerializer")
    print("="*60)
    
    serializer = TileSerializer()
    print(f"Created serializer: format={serializer.get_format_info()['format']}")
    
    # Test place serialization
    from shypn.netobjs.place import Place
    
    place = Place(100.0, 200.0, id="place_001", name="P1", radius=25.0, label="Test Place")
    place.tokens = 3
    place.color = (255, 200, 100)
    
    place_dict = serializer.serialize_place(place)
    print(f"\nSerialized place: {place_dict}")
    
    place_restored = serializer.deserialize_place(place_dict)
    print(f"Deserialized place: id={place_restored.id}, "
          f"pos=({place_restored.x}, {place_restored.y}), "
          f"tokens={place_restored.tokens}")
    
    assert place_restored.id == place.id
    assert place_restored.x == place.x
    assert place_restored.y == place.y
    assert place_restored.tokens == place.tokens
    
    # Test transition serialization
    from shypn.netobjs.transition import Transition
    
    transition = Transition(300.0, 400.0, id="trans_001", name="T1",
                           width=60.0, height=20.0, 
                           horizontal=True, label="Test Transition")
    
    trans_dict = serializer.serialize_transition(transition)
    print(f"\nSerialized transition: {trans_dict}")
    
    trans_restored = serializer.deserialize_transition(trans_dict)
    print(f"Deserialized transition: id={trans_restored.id}, "
          f"pos=({trans_restored.x}, {trans_restored.y})")
    
    assert trans_restored.id == transition.id
    assert trans_restored.x == transition.x
    
    # Test arc serialization
    from shypn.netobjs.arc import Arc
    
    arc = Arc(place, transition, id="arc_001", name="A1", weight=2.0)
    
    arc_dict = serializer.serialize_arc(arc)
    print(f"\nSerialized arc: {arc_dict}")
    
    arc_data = serializer.deserialize_arc(arc_dict)
    print(f"Deserialized arc data: id={arc_data['id']}, "
          f"{arc_data['source_id']} → {arc_data['target_id']}, "
          f"weight={arc_data['weight']}")
    
    assert arc_data['id'] == arc.id
    assert arc_data['source_id'] == place.id
    assert arc_data['target_id'] == transition.id
    
    # Test file I/O
    import tempfile
    
    tile_data = {
        'places': [place_dict],
        'transitions': [trans_dict],
        'arcs': [arc_dict]
    }
    
    with tempfile.NamedTemporaryFile(suffix='.bin', delete=False) as f:
        temp_path = f.name
    
    try:
        serializer.save_tile(temp_path, tile_data)
        print(f"\nSaved tile to {temp_path}")
        
        loaded_data = serializer.load_tile(temp_path)
        print(f"Loaded tile: {len(loaded_data['places'])} places, "
              f"{len(loaded_data['transitions'])} transitions, "
              f"{len(loaded_data['arcs'])} arcs")
        
        assert len(loaded_data['places']) == 1
        assert len(loaded_data['transitions']) == 1
        assert len(loaded_data['arcs']) == 1
    finally:
        os.unlink(temp_path)
    
    print("✅ TileSerializer tests passed")


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("Spatial Partitioning Core Infrastructure Tests")
    print("="*60)
    
    try:
        test_tile_coord()
        test_tile_grid()
        test_tile_cache()
        test_tile_serializer()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED")
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
