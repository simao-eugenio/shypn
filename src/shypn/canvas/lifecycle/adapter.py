"""
Legacy Adapter - Bridges new lifecycle system with existing code.

This adapter provides backward compatibility during migration from the old
per-canvas dictionary pattern to the new CanvasLifecycleManager architecture.

It wraps the lifecycle manager and provides the same interface that existing
code expects, allowing gradual migration without breaking existing functionality.
"""

import logging
from typing import Optional, Dict, Any
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from .lifecycle_manager import CanvasLifecycleManager
from .canvas_context import CanvasContext

logger = logging.getLogger(__name__)


class LifecycleAdapter:
    """Adapter that bridges CanvasLifecycleManager with existing code patterns.
    
    This class maintains the same interface as the old dictionary-based system
    while delegating to the new lifecycle manager under the hood.
    
    Old Pattern (existing code):
        self.document_models[drawing_area] = model
        self.simulation_controllers[drawing_area] = controller
        
    New Pattern (with adapter):
        self.lifecycle.register_canvas(drawing_area, model, controller)
        model = self.lifecycle.get_document_model(drawing_area)
        controller = self.lifecycle.get_controller(drawing_area)
    
    The adapter also maintains legacy dictionaries for code that directly
    accesses them, keeping both old and new systems in sync.
    """
    
    def __init__(self, lifecycle_manager: CanvasLifecycleManager):
        """
        Initialize adapter with reference to lifecycle manager.
        
        Args:
            lifecycle_manager: The lifecycle manager to wrap
        """
        self.lifecycle_manager = lifecycle_manager
        
        # Legacy dictionaries - kept in sync for backward compatibility
        self.document_models: Dict[Any, Any] = {}
        self.simulation_controllers: Dict[Any, Any] = {}
        self.swissknife_palettes: Dict[Any, Any] = {}
        
        logger.info("LifecycleAdapter initialized (legacy compatibility mode)")
        
    def register_canvas(self, 
                       drawing_area: Any,
                       document_model: Any,
                       simulation_controller: Any,
                       swissknife_palette: Any) -> None:
        """
        Register existing canvas components with lifecycle system.
        
        This method allows gradual migration by registering components
        that were created outside the lifecycle system.
        
        Args:
            drawing_area: Canvas widget (scope key)
            document_model: Document model/canvas manager
            simulation_controller: Simulation engine
            swissknife_palette: UI palette
        """
        # Create context from existing components
        # Note: canvas_manager is same as document_model in current architecture
        context = CanvasContext(
            drawing_area=drawing_area,
            document_model=document_model,
            controller=simulation_controller,
            palette=swissknife_palette,
            id_scope=f"canvas_{id(drawing_area)}",
            canvas_manager=document_model  # Same as document_model
        )
        
        # Register with lifecycle manager
        canvas_id = id(drawing_area)
        self.lifecycle_manager.canvas_registry[canvas_id] = context
        
        # Set ID scope for this canvas
        scope_id = f"canvas_{id(drawing_area)}"
        self.lifecycle_manager.id_manager.set_scope(scope_id)
        
        # Update legacy dictionaries for backward compatibility
        self.document_models[drawing_area] = document_model
        self.simulation_controllers[drawing_area] = simulation_controller
        self.swissknife_palettes[drawing_area] = swissknife_palette
        
        logger.debug(f"Registered canvas {id(drawing_area)} with lifecycle system")
    
    def sync_from_context(self, context: CanvasContext):
        """Sync legacy dictionaries from a CanvasContext.
        
        This is called after lifecycle_manager.create_canvas() to populate
        the legacy dictionaries that existing code expects.
        
        Args:
            context: CanvasContext from lifecycle manager
        """
        logger.debug(f"Syncing legacy dicts from context {context.canvas_id}")
        
        self.document_models[context.drawing_area] = context.document_model
        self.simulation_controllers[context.drawing_area] = context.controller
        self.swissknife_palettes[context.drawing_area] = context.palette
        
        logger.debug(f"  Synced: {len(self.document_models)} models, "
                    f"{len(self.simulation_controllers)} controllers, "
                    f"{len(self.swissknife_palettes)} palettes")
    
    def get_document_model(self, drawing_area: Gtk.DrawingArea) -> Optional[Any]:
        """Get document model for a canvas.
        
        Args:
            drawing_area: GTK DrawingArea widget
            
        Returns:
            DocumentModel or None
        """
        # Try new system first
        context = self.lifecycle_manager.get_context(drawing_area)
        if context:
            return context.document_model
        
        # Fall back to legacy dictionary
        return self.document_models.get(drawing_area)
    
    def get_controller(self, drawing_area: Gtk.DrawingArea) -> Optional[Any]:
        """Get simulation controller for a canvas.
        
        Args:
            drawing_area: GTK DrawingArea widget
            
        Returns:
            SimulationController or None
        """
        # Try new system first
        context = self.lifecycle_manager.get_context(drawing_area)
        if context:
            return context.controller
        
        # Fall back to legacy dictionary
        return self.simulation_controllers.get(drawing_area)
    
    def get_palette(self, drawing_area: Gtk.DrawingArea) -> Optional[Any]:
        """Get SwissKnifePalette for a canvas.
        
        Args:
            drawing_area: GTK DrawingArea widget
            
        Returns:
            SwissKnifePalette or None
        """
        # Try new system first
        context = self.lifecycle_manager.get_context(drawing_area)
        if context:
            return context.palette
        
        # Fall back to legacy dictionary
        return self.swissknife_palettes.get(drawing_area)
    
    def remove_canvas(self, drawing_area: Gtk.DrawingArea):
        """Remove a canvas from both systems.
        
        Args:
            drawing_area: GTK DrawingArea widget
        """
        logger.debug(f"Removing canvas {id(drawing_area)} from adapter")
        
        # Remove from new system
        try:
            self.lifecycle_manager.destroy_canvas(drawing_area)
        except ValueError:
            logger.debug("  Canvas not in lifecycle manager")
        
        # Remove from legacy dictionaries
        if drawing_area in self.document_models:
            del self.document_models[drawing_area]
        
        if drawing_area in self.simulation_controllers:
            del self.simulation_controllers[drawing_area]
        
        if drawing_area in self.swissknife_palettes:
            del self.swissknife_palettes[drawing_area]
        
        logger.debug("  Canvas removed from both systems")
    
    def reset_canvas(self, drawing_area: Gtk.DrawingArea):
        """Reset canvas in both systems.
        
        Args:
            drawing_area: GTK DrawingArea widget
        """
        logger.debug(f"Resetting canvas {id(drawing_area)} via adapter")
        
        # Reset via new system
        context = self.lifecycle_manager.get_context(drawing_area)
        if context:
            self.lifecycle_manager.reset_canvas(drawing_area)
            # Sync legacy dicts
            self.sync_from_context(context)
        else:
            # Legacy reset if not in new system
            logger.debug("  Using legacy reset (canvas not in lifecycle manager)")
            
            model = self.document_models.get(drawing_area)
            if model:
                model.places.clear()
                model.transitions.clear()
                model.arcs.clear()
            
            controller = self.simulation_controllers.get(drawing_area)
            if controller:
                controller.reset()
                if hasattr(controller, 'behavior_cache'):
                    controller.behavior_cache.clear()
    
    def switch_to_canvas(self, drawing_area: Any) -> None:
        """
        Switch to a different canvas, updating ID scope.
        
        Args:
            drawing_area: Target canvas widget
        """
        # Call with from_area=None (adapter doesn't track current)
        result = self.lifecycle_manager.switch_canvas(None, drawing_area)
        return result
        
    def destroy_canvas(self, drawing_area: Any) -> bool:
        """
        Destroy canvas and cleanup resources.
        
        Args:
            drawing_area: Canvas widget to destroy
            
        Returns:
            bool: True if successful
        """
        return self.lifecycle_manager.destroy_canvas(drawing_area)
        
    def get_canvas_context(self, drawing_area: Any) -> Optional[CanvasContext]:
        """
        Get canvas context for drawing_area.
        
        Args:
            drawing_area: Canvas widget
            
        Returns:
            CanvasContext if found, None otherwise
        """
        canvas_id = id(drawing_area)
        return self.lifecycle_manager.canvas_registry.get(canvas_id)
    
    def has_canvas(self, drawing_area: Gtk.DrawingArea) -> bool:
        """Check if canvas is registered in either system.
        
        Args:
            drawing_area: GTK DrawingArea widget
            
        Returns:
            True if canvas exists in new or legacy system
        """
        # Check new system
        if self.lifecycle_manager.get_context(drawing_area):
            return True
        
        # Check legacy system
        return drawing_area in self.document_models
    
    def migrate_canvas(self, drawing_area: Gtk.DrawingArea) -> bool:
        """Migrate a legacy canvas to the new lifecycle system.
        
        This is used during gradual migration to move canvases from the
        old dictionary pattern to the new lifecycle manager.
        
        Args:
            drawing_area: GTK DrawingArea widget
            
        Returns:
            True if migration successful, False if already migrated or not found
        """
        # Check if already in new system
        if self.lifecycle_manager.get_context(drawing_area):
            logger.debug(f"Canvas {id(drawing_area)} already migrated")
            return False
        
        # Check if in legacy system
        canvas_manager = self.document_models.get(drawing_area)
        if not canvas_manager:
            logger.warning(f"Canvas {id(drawing_area)} not found in legacy system")
            return False
        
        logger.info(f"Migrating canvas {id(drawing_area)} to new system")
        
        try:
            # Create in new system
            context = self.lifecycle_manager.create_canvas(
                drawing_area,
                canvas_manager,
                file_path=None  # Unknown during migration
            )
            
            # If canvas had a controller, update the reference
            legacy_controller = self.simulation_controllers.get(drawing_area)
            if legacy_controller:
                # Replace with new controller
                self.simulation_controllers[drawing_area] = context.controller
                logger.debug("  Updated controller reference")
            
            # If canvas had a palette, update the reference
            legacy_palette = self.swissknife_palettes.get(drawing_area)
            if legacy_palette:
                # Replace with new palette
                self.swissknife_palettes[drawing_area] = context.palette
                logger.debug("  Updated palette reference")
            
            logger.info(f"✓ Canvas {id(drawing_area)} migration complete")
            return True
            
        except Exception as e:
            logger.error(f"✗ Failed to migrate canvas {id(drawing_area)}: {e}")
            return False
    
    def get_migration_status(self) -> dict:
        """Get status of migration from legacy to new system.
        
        Returns:
            Dictionary with migration statistics
        """
        total_legacy = len(self.document_models)
        total_new = self.lifecycle_manager.get_active_canvas_count()
        
        # Count how many are in both systems
        migrated = 0
        for area in self.document_models:
            if self.lifecycle_manager.get_context(area):
                migrated += 1
        
        return {
            'total_legacy_canvases': total_legacy,
            'total_new_canvases': total_new,
            'migrated_canvases': migrated,
            'legacy_only': total_legacy - migrated,
            'migration_complete': (migrated == total_legacy and total_legacy > 0)
        }
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        status = self.get_migration_status()
        return (
            f"LifecycleAdapter("
            f"legacy={status['total_legacy_canvases']}, "
            f"new={status['total_new_canvases']}, "
            f"migrated={status['migrated_canvases']})"
        )
