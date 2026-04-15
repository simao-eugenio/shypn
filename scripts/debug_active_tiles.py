#!/usr/bin/env python3
"""Debug active tiles counting issue."""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from shypn.data.spatial.tile_coord import TileGrid

# Test with small model parameters
tile_size = 300
grid = TileGrid(tile_size)

# Viewport parameters from test
viewport_x = 0
viewport_y = 0
viewport_width = 1920
viewport_height = 1080
zoom = 0.5

# Calculate bounds (same as spatial_model_manager)
world_width = viewport_width / zoom
world_height = viewport_height / zoom
margin = tile_size * 0.5

min_x = viewport_x - margin
max_x = viewport_x + world_width + margin
min_y = viewport_y - margin
max_y = viewport_y + world_height + margin

print(f"Viewport: ({viewport_x}, {viewport_y}) @ {zoom}x")
print(f"World size: {world_width} × {world_height}")
print(f"Margin: {margin}")
print(f"Bounds: ({min_x}, {min_y}) to ({max_x}, {max_y})")

# Get tiles
tiles = grid.get_tiles_in_bounds(min_x, min_y, max_x, max_y)
print(f"\nTiles in bounds: {len(tiles)}")

# Show tile range
min_tile = grid.world_to_tile(min_x, min_y)
max_tile = grid.world_to_tile(max_x, max_y)
print(f"Tile range: {min_tile} to {max_tile}")
print(f"Tile grid size: ({max_tile.x - min_tile.x + 1}, {max_tile.y - min_tile.y + 1})")
print(f"Expected tiles: {(max_tile.x - min_tile.x + 1) * (max_tile.y - min_tile.y + 1)}")

# Show some tiles
print(f"\nFirst 10 tiles:")
for i, tile in enumerate(sorted(tiles, key=lambda t: (t.y, t.x))[:10]):
    bounds = grid.tile_to_world_bounds(tile)
    print(f"  {tile}: bounds={bounds}")
