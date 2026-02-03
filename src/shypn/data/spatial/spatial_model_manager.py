"""Spatial model manager with lazy loading.

This module provides a ModelCanvasManager subclass that loads tiles
on-demand based on the viewport, reducing memory usage for large models.

Classes:
    SpatialModelManager: ModelCanvasManager with spatial partitioning
"""

import os
import json
import logging
from typing import Set, List, Dict, Any
from shypn.data.model_canvas_manager import ModelCanvasManager
from shypn.data.spatial.tile_coord import TileGrid, TileCoord
from shypn.data.spatial.tile_cache import TileCache
from shypn.data.spatial.tile_serializer import TileSerializer

logger = logging.getLogger(__name__)


class SpatialModelManager(ModelCanvasManager):
    """ModelCanvasManager with lazy loading via spatial partitioning.
    
    Extends ModelCanvasManager to load only tiles visible in the current
    viewport, dramatically reducing memory usage for genome-scale models.
    
    Attributes:
        model_dir: Path to tiled model directory
        tiles_dir: Path to tiles subdirectory
        metadata: Model metadata dictionary
        index: Spatial index dictionary
        grid: TileGrid for coordinate conversion
        cache: TileCache for loaded tiles
        serializer: TileSerializer for object deserialization
        active_tiles: Set of currently loaded tile coordinates
    
    Example:
        >>> manager = SpatialModelManager('model.shy')
        >>> manager.update_viewport(0, 0, 1920, 1080, 0.5)
        >>> visible_objects = manager.get_visible_objects()
    """
    
    def __init__(self, model_dir: str, canvas_width=2000, canvas_height=2000):
        """Initialize spatial model manager.
        
        Args:
            model_dir: Path to tiled model directory
            canvas_width: Canvas width in pixels
            canvas_height: Canvas height in pixels
        
        Raises:
            FileNotFoundError: If model directory or required files not found
            ValueError: If model format is invalid
        """
        super().__init__(canvas_width, canvas_height)
        
        if not os.path.isdir(model_dir):
            raise FileNotFoundError(f"Model directory not found: {model_dir}")
        
        self.model_dir = model_dir
        self.tiles_dir = os.path.join(model_dir, 'tiles')
        
        if not os.path.isdir(self.tiles_dir):
            raise FileNotFoundError(f"Tiles directory not found: {self.tiles_dir}")
        
        # Load metadata and index
        self._load_metadata()
        self._load_index()
        
        # Validate format
        if self.tile_metadata.get('format_type') != 'tiled':
            raise ValueError(f"Invalid format type: {self.tile_metadata.get('format_type')}")
        
        # Initialize tile system
        self.grid = TileGrid(self.tile_metadata['tile_size'])
        self.cache = TileCache(max_tiles=16)
        self.serializer = TileSerializer()
        
        # Track active tiles
        self.active_tiles: Set[TileCoord] = set()
        
        # Object ID tracking for deduplication
        self._loaded_place_ids: Set[str] = set()
        self._loaded_transition_ids: Set[str] = set()
        self._loaded_arc_ids: Set[str] = set()
        
        # Clear default collections (we'll populate on demand)
        self.places.clear()
        self.transitions.clear()
        self.arcs.clear()
        
        logger.info(f"Opened tiled model: {len(self.tile_index['tiles'])} tiles, "
                   f"tile_size={self.tile_metadata['tile_size']}, "
                   f"{self.tile_metadata['total_objects']['places']} places, "
                   f"{self.tile_metadata['total_objects']['transitions']} transitions, "
                   f"{self.tile_metadata['total_objects']['arcs']} arcs")
    
    def _load_metadata(self):
        """Load model metadata from JSON file."""
        metadata_path = os.path.join(self.model_dir, 'metadata.json')
        
        if not os.path.exists(metadata_path):
            raise FileNotFoundError(f"Metadata file not found: {metadata_path}")
        
        with open(metadata_path, 'r') as f:
            self.tile_metadata = json.load(f)
        
        logger.debug(f"Loaded metadata: format={self.tile_metadata.get('format_type')}, "
                    f"version={self.tile_metadata.get('format_version')}")
    
    def _load_index(self):
        """Load spatial index from JSON file."""
        index_path = os.path.join(self.model_dir, 'index.json')
        
        if not os.path.exists(index_path):
            raise FileNotFoundError(f"Index file not found: {index_path}")
        
        with open(index_path, 'r') as f:
            self.tile_index = json.load(f)
        
        logger.debug(f"Loaded spatial index: {len(self.tile_index['tiles'])} tiles")
    
    def update_viewport(self, viewport_x: float, viewport_y: float,
                       viewport_width: float, viewport_height: float,
                       zoom: float):
        """Update viewport and load/unload tiles accordingly.
        
        Args:
            viewport_x: Viewport X coordinate (world space)
            viewport_y: Viewport Y coordinate (world space)
            viewport_width: Viewport width (pixels)
            viewport_height: Viewport height (pixels)
            zoom: Zoom level (1.0 = 100%)
        """
        # Calculate visible world bounds
        world_width = viewport_width / zoom
        world_height = viewport_height / zoom
        
        # Add margin for smooth scrolling (load tiles before they're visible)
        margin = self.tile_metadata['tile_size'] * 0.5
        
        min_x = viewport_x - margin
        max_x = viewport_x + world_width + margin
        min_y = viewport_y - margin
        max_y = viewport_y + world_height + margin
        
        # Determine which tiles should be loaded
        required_tiles = self.grid.get_tiles_in_bounds(
            min_x, min_y, max_x, max_y
        )
        
        # Load new tiles
        tiles_to_load = required_tiles - self.active_tiles
        if tiles_to_load:
            logger.debug(f"Loading {len(tiles_to_load)} new tiles")
            for tile_coord in tiles_to_load:
                self._load_tile(tile_coord)
        
        # Unload distant tiles
        tiles_to_unload = self.active_tiles - required_tiles
        if tiles_to_unload:
            logger.debug(f"Unloading {len(tiles_to_unload)} distant tiles")
            # For now, just mark as inactive but keep objects loaded
            # TODO: Implement proper unloading with reference counting
        
        self.active_tiles = required_tiles
        
        # Log cache stats periodically
        if logger.isEnabledFor(logging.DEBUG):
            stats = self.cache.get_stats()
            logger.debug(f"Active tiles: {len(self.active_tiles)}, "
                        f"Cache: {stats['size']}/{stats['max_size']}, "
                        f"Hit rate: {stats['hit_rate']:.1%}")
    
    def _load_tile(self, tile_coord: TileCoord):
        """Load a tile into memory.
        
        Args:
            tile_coord: Tile coordinate to load
        """
        # Check cache first
        tile_data = self.cache.get(tile_coord)
        
        if tile_data is None:
            # Load from disk
            tile_filename = f"tile_{tile_coord.x}_{tile_coord.y}.bin"
            tile_path = os.path.join(self.tiles_dir, tile_filename)
            
            if not os.path.exists(tile_path):
                # Empty tile (no objects in this region)
                logger.debug(f"Tile {tile_coord} is empty (no file)")
                tile_data = {'places': [], 'transitions': [], 'arcs': []}
                self.cache.put(tile_coord, tile_data)
                return
            
            # Load and deserialize
            try:
                tile_data = self.serializer.load_tile(tile_path)
                self.cache.put(tile_coord, tile_data)
                
                logger.debug(f"Loaded tile {tile_coord}: "
                            f"{len(tile_data['places'])} places, "
                            f"{len(tile_data['transitions'])} transitions, "
                            f"{len(tile_data['arcs'])} arcs")
            except Exception as e:
                logger.error(f"Failed to load tile {tile_coord}: {e}")
                return
        
        # Add objects to active collections (avoid duplicates)
        for place_data in tile_data.get('places', []):
            if place_data['id'] not in self._loaded_place_ids:
                place = self.serializer.deserialize_place(place_data)
                self.places.append(place)
                self._loaded_place_ids.add(place.id)
        
        for trans_data in tile_data.get('transitions', []):
            if trans_data['id'] not in self._loaded_transition_ids:
                trans = self.serializer.deserialize_transition(trans_data)
                self.transitions.append(trans)
                self._loaded_transition_ids.add(trans.id)
        
        # Resolve and create arcs after places and transitions are loaded
        for arc_data in tile_data.get('arcs', []):
            if arc_data['id'] not in self._loaded_arc_ids:
                # Arc deserialization returns dict, need to resolve references
                arc = self._resolve_arc(arc_data)
                if arc:  # Only add if both source and target found
                    self.arcs.append(arc)
                    self._loaded_arc_ids.add(arc.id)
    
    def _resolve_arc(self, arc_data: Dict[str, Any]):
        """Resolve arc references to actual Place/Transition objects.
        
        Args:
            arc_data: Dictionary with arc properties including source_id/target_id
        
        Returns:
            Arc instance, or None if source/target not found
        """
        # Find source and target objects
        source_id = arc_data['source_id']
        target_id = arc_data['target_id']
        
        # Search for source
        source = None
        for place in self.places:
            if place.id == source_id:
                source = place
                break
        if not source:
            for trans in self.transitions:
                if trans.id == source_id:
                    source = trans
                    break
        
        # Search for target
        target = None
        for place in self.places:
            if place.id == target_id:
                target = place
                break
        if not target:
            for trans in self.transitions:
                if trans.id == target_id:
                    target = trans
                    break
        
        if not source or not target:
            logger.debug(f"Cannot resolve arc {arc_data['id']}: "
                        f"source={source_id} ({'found' if source else 'missing'}), "
                        f"target={target_id} ({'found' if target else 'missing'})")
            return None
        
        # Determine arc class based on arc_type
        arc_type = arc_data.get('arc_type', 'normal')
        
        if arc_type == 'test':
            from shypn.netobjs.test_arc import TestArc
            arc_class = TestArc
        elif arc_type == 'inhibitor':
            from shypn.netobjs.inhibitor_arc import InhibitorArc
            arc_class = InhibitorArc
        elif arc_type == 'signal_flow':
            from shypn.netobjs.signal_flow_arc import SignalFlowArc
            arc_class = SignalFlowArc
        else:
            from shypn.netobjs.arc import Arc
            arc_class = Arc
        
        # Create Arc instance
        arc = arc_class(
            source, target,
            id=arc_data['id'],
            name=arc_data.get('name', arc_data['id']),
            weight=arc_data.get('weight', 1.0)
        )
        
        # Set additional properties
        if 'threshold' in arc_data and arc_data['threshold'] is not None:
            arc.threshold = arc_data['threshold']
        if 'is_curved' in arc_data:
            arc.is_curved = arc_data['is_curved']
        if 'control_offset_x' in arc_data:
            arc.control_offset_x = arc_data['control_offset_x']
        if 'control_offset_y' in arc_data:
            arc.control_offset_y = arc_data['control_offset_y']
        
        return arc
    
    def _unload_tile(self, tile_coord: TileCoord):
        """Unload a tile from active collections.
        
        Note: Objects remain in cache for fast re-loading. This method
        removes objects from the active places/transitions/arcs lists.
        
        Args:
            tile_coord: Tile coordinate to unload
        """
        # Get tile bounds to identify objects to unload
        bounds = self.grid.tile_to_world_bounds(tile_coord)
        min_x, min_y, max_x, max_y = bounds
        
        # Remove places in this tile
        self.places = [
            p for p in self.places
            if not (min_x <= p.x < max_x and min_y <= p.y < max_y)
        ]
        
        # Remove transitions in this tile
        self.transitions = [
            t for t in self.transitions
            if not (min_x <= t.x < max_x and min_y <= t.y < max_y)
        ]
        
        # Update ID tracking
        self._loaded_place_ids = {p.id for p in self.places}
        self._loaded_transition_ids = {t.id for t in self.transitions}
        
        # Arcs are trickier - remove only if source/target not loaded
        self.arcs = [
            a for a in self.arcs
            if a.source in self._loaded_place_ids or 
               a.source in self._loaded_transition_ids or
               a.target in self._loaded_place_ids or
               a.target in self._loaded_transition_ids
        ]
        self._loaded_arc_ids = {a.id for a in self.arcs}
        
        logger.debug(f"Unloaded tile {tile_coord}")
    
    def get_visible_objects(self):
        """Get objects currently loaded (override parent method).
        
        With spatial partitioning, we only return loaded objects.
        No additional viewport culling needed.
        
        Returns:
            List of all currently loaded objects
        """
        return list(self.places) + list(self.transitions) + list(self.arcs)
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get tile cache statistics.
        
        Returns:
            Dictionary with cache performance metrics
        """
        return self.cache.get_stats()
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information.
        
        Returns:
            Dictionary with model metadata and loading status
        """
        return {
            'format': self.tile_metadata.get('format_type'),
            'version': self.tile_metadata.get('format_version'),
            'tile_size': self.tile_metadata['tile_size'],
            'total_tiles': len(self.tile_index['tiles']),  # Non-empty tiles only
            'active_tiles': len(self.active_tiles),  # All tiles in viewport (may include empty)
            'total_objects': self.tile_metadata['total_objects'],
            'loaded_objects': {
                'places': len(self.places),
                'transitions': len(self.transitions),
                'arcs': len(self.arcs)
            },
            'cache_stats': self.get_cache_stats(),
            'bounds': self.tile_metadata.get('bounds')
        }
    
    def preload_neighbors(self):
        """Preload neighbor tiles for active tiles.
        
        Improves responsiveness by loading tiles adjacent to currently
        visible tiles in advance.
        """
        all_neighbors = set()
        for tile_coord in self.active_tiles:
            all_neighbors.update(tile_coord.neighbors(include_diagonals=False))
        
        # Remove already active tiles
        neighbors_to_load = all_neighbors - self.active_tiles
        
        logger.debug(f"Preloading {len(neighbors_to_load)} neighbor tiles")
        for tile_coord in neighbors_to_load:
            # Only load to cache, don't add to active
            tile_filename = f"tile_{tile_coord.x}_{tile_coord.y}.bin"
            tile_path = os.path.join(self.tiles_dir, tile_filename)
            
            if os.path.exists(tile_path) and tile_coord not in self.cache:
                try:
                    tile_data = self.serializer.load_tile(tile_path)
                    self.cache.put(tile_coord, tile_data)
                except Exception as e:
                    logger.warning(f"Failed to preload tile {tile_coord}: {e}")
    
    def load_all_tiles(self):
        """Load all tiles in the model.
        
        Required before applying graph algorithms (force-directed layout, etc.)
        that need the complete graph structure.
        
        Returns:
            int: Number of tiles loaded
        """
        logger.info("Loading all tiles for complete graph structure...")
        print("\n[LOADING] Loading all tiles for layout operation...")
        
        # Get all tile coordinates from index
        all_tile_coords = set()
        for tile_key in self.tile_index['tiles'].keys():
            # Parse "x_y" key format (underscore, not comma!)
            x, y = map(int, tile_key.split('_'))
            all_tile_coords.add(TileCoord(x, y))
        
        # Load tiles that aren't already loaded
        tiles_to_load = all_tile_coords - self.active_tiles
        
        total_tiles = len(all_tile_coords)
        loaded_count = 0
        
        print(f"   Total tiles to load: {len(tiles_to_load)} of {total_tiles}")
        print(f"   Already loaded: {len(self.active_tiles)}")
        
        for tile_coord in tiles_to_load:
            self._load_tile(tile_coord)
            loaded_count += 1
            
            # Progress indicator every 50 tiles
            if loaded_count % 50 == 0:
                print(f"   Progress: {loaded_count + len(self.active_tiles)}/{total_tiles} tiles loaded")
        
        # Mark all as active
        self.active_tiles = all_tile_coords
        
        logger.info(f"Loaded all {total_tiles} tiles: "
                   f"{len(self.places)} places, "
                   f"{len(self.transitions)} transitions, "
                   f"{len(self.arcs)} arcs")
        
        print(f"\n[COMPLETE] All tiles loaded: {len(self.places)} places, {len(self.transitions)} transitions, {len(self.arcs)} arcs")
        print(f"   {len(self.arcs)} arcs fully resolved (complete graph structure)\n")
        
        return total_tiles
