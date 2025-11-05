"""
Integration Helper - Safe integration of lifecycle manager with existing code.

This module provides helper functions to safely integrate the new lifecycle
system into existing code without breaking current functionality.

Key principles:
1. Gradual migration - both old and new systems work in parallel
2. Backward compatibility - existing code continues to work
3. Safe fallbacks - if new system fails, fall back to old behavior
4. Clear logging - track migration progress and issues
"""

import logging
from typing import Optional, Callable
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from .lifecycle_manager import CanvasLifecycleManager
from .adapter import LifecycleAdapter
from .canvas_context import CanvasContext

logger = logging.getLogger(__name__)


class IntegrationHelper:
    """Helper for safe integration of lifecycle manager.
    
    This class provides methods to safely integrate the new system
    while maintaining compatibility with existing code.
    """
    
    @staticmethod
    def create_with_fallback(
        lifecycle_manager: CanvasLifecycleManager,
        adapter: LifecycleAdapter,
        drawing_area: Gtk.DrawingArea,
        canvas_manager: any,
        legacy_creator: Optional[Callable] = None
    ) -> tuple:
        """Create canvas using new system with fallback to legacy.
        
        This method attempts to create a canvas using the new lifecycle
        manager. If that fails, it falls back to the legacy creation method.
        
        Args:
            lifecycle_manager: New lifecycle manager
            adapter: Adapter for backward compatibility
            drawing_area: GTK DrawingArea widget
            canvas_manager: ModelCanvasManager instance
            legacy_creator: Optional function to call if new system fails
            
        Returns:
            Tuple of (success: bool, context: Optional[CanvasContext])
        """
        try:
            # Try new system
            logger.info(f"Creating canvas {id(drawing_area)} with lifecycle manager")
            context = lifecycle_manager.create_canvas(drawing_area, canvas_manager)
            
            # Sync with adapter for backward compatibility
            adapter.sync_from_context(context)
            
            logger.info(f"✓ Canvas {id(drawing_area)} created successfully via new system")
            return (True, context)
            
        except Exception as e:
            logger.error(f"✗ Failed to create canvas via new system: {e}")
            logger.info("Falling back to legacy canvas creation")
            
            # Fall back to legacy if provided
            if legacy_creator:
                try:
                    legacy_creator()
                    logger.info("✓ Canvas created via legacy method")
                except Exception as legacy_e:
                    logger.error(f"✗ Legacy creation also failed: {legacy_e}")
            
            return (False, None)
    
    @staticmethod
    def safe_reset(
        lifecycle_manager: CanvasLifecycleManager,
        adapter: LifecycleAdapter,
        drawing_area: Gtk.DrawingArea,
        legacy_reset: Optional[Callable] = None
    ) -> bool:
        """Reset canvas with safe fallback.
        
        Args:
            lifecycle_manager: New lifecycle manager
            adapter: Adapter for backward compatibility
            drawing_area: GTK DrawingArea widget
            legacy_reset: Optional function to call if new system fails
            
        Returns:
            True if reset successful
        """
        try:
            # Try via adapter (handles both systems)
            adapter.reset_canvas(drawing_area)
            logger.info(f"✓ Canvas {id(drawing_area)} reset successfully")
            return True
            
        except Exception as e:
            logger.error(f"✗ Failed to reset canvas via adapter: {e}")
            
            # Fall back to legacy if provided
            if legacy_reset:
                try:
                    legacy_reset()
                    logger.info("✓ Canvas reset via legacy method")
                    return True
                except Exception as legacy_e:
                    logger.error(f"✗ Legacy reset also failed: {legacy_e}")
            
            return False
    
    @staticmethod
    def safe_get_controller(
        adapter: LifecycleAdapter,
        drawing_area: Gtk.DrawingArea,
        legacy_dict: Optional[dict] = None
    ) -> Optional[any]:
        """Safely get controller with fallback.
        
        Args:
            adapter: Adapter for backward compatibility
            drawing_area: GTK DrawingArea widget
            legacy_dict: Optional legacy controllers dictionary
            
        Returns:
            SimulationController or None
        """
        # Try via adapter (tries new system first, then legacy)
        controller = adapter.get_controller(drawing_area)
        
        # Final fallback to provided legacy dict
        if not controller and legacy_dict:
            controller = legacy_dict.get(drawing_area)
        
        return controller
    
    @staticmethod
    def safe_sync_after_load(
        lifecycle_manager: CanvasLifecycleManager,
        drawing_area: Gtk.DrawingArea,
        file_path: str
    ) -> bool:
        """Safely sync after file load.
        
        Args:
            lifecycle_manager: New lifecycle manager
            drawing_area: GTK DrawingArea widget
            file_path: Path to loaded file
            
        Returns:
            True if sync successful
        """
        try:
            context = lifecycle_manager.get_context(drawing_area)
            if context:
                lifecycle_manager.sync_after_file_load(drawing_area, file_path)
                logger.info(f"✓ Synced canvas {id(drawing_area)} after loading {file_path}")
                return True
            else:
                logger.debug(f"Canvas {id(drawing_area)} not in lifecycle manager, skipping sync")
                return False
                
        except Exception as e:
            logger.error(f"✗ Failed to sync after load: {e}")
            return False
    
    @staticmethod
    def validate_context(context: CanvasContext) -> list:
        """Validate a canvas context for issues.
        
        Args:
            context: CanvasContext to validate
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Check required components
        if not context.drawing_area:
            errors.append("Missing drawing_area")
        
        if not context.document_model:
            errors.append("Missing document_model")
        
        if not context.controller:
            errors.append("Missing controller")
        
        if not context.palette:
            errors.append("Missing palette")
        
        # Check component linkage
        if context.controller and context.document_model:
            if context.controller.model != context.document_model:
                errors.append("Controller.model != document_model")
        
        # Check palette linkage
        if context.palette:
            simulate_tools = context.palette.widget_palette_instances.get('simulate')
            if simulate_tools:
                if simulate_tools.simulation != context.controller:
                    errors.append("Palette simulation controller not linked")
        
        # Check ID scope
        if not context.id_scope:
            errors.append("Missing id_scope")
        
        return errors
    
    @staticmethod
    def diagnostic_report(
        lifecycle_manager: CanvasLifecycleManager,
        adapter: LifecycleAdapter
    ) -> dict:
        """Generate diagnostic report of system state.
        
        Args:
            lifecycle_manager: Lifecycle manager instance
            adapter: Adapter instance
            
        Returns:
            Dictionary with diagnostic information
        """
        report = {
            'lifecycle_manager': {
                'active_canvases': lifecycle_manager.get_active_canvas_count(),
                'registered_contexts': len(lifecycle_manager.canvas_registry),
                'id_scopes': len(lifecycle_manager.id_manager.get_all_scopes())
            },
            'adapter': adapter.get_migration_status(),
            'contexts': [],
            'validation_errors': []
        }
        
        # Validate each context
        for context in lifecycle_manager.get_all_contexts():
            errors = IntegrationHelper.validate_context(context)
            
            context_info = {
                'canvas_id': context.canvas_id,
                'display_name': context.display_name,
                'id_scope': context.id_scope,
                'is_modified': context.is_modified,
                'is_simulation_running': context.is_simulation_running,
                'object_counts': context.get_object_counts(),
                'valid': len(errors) == 0,
                'errors': errors
            }
            
            report['contexts'].append(context_info)
            
            if errors:
                report['validation_errors'].extend([
                    f"Canvas {context.canvas_id}: {error}" for error in errors
                ])
        
        return report
    
    @staticmethod
    def log_diagnostic_report(
        lifecycle_manager: CanvasLifecycleManager,
        adapter: LifecycleAdapter
    ):
        """Log diagnostic report to logger.
        
        Args:
            lifecycle_manager: Lifecycle manager instance
            adapter: Adapter instance
        """
        report = IntegrationHelper.diagnostic_report(lifecycle_manager, adapter)
        
        logger.info("=" * 70)
        logger.info("CANVAS LIFECYCLE DIAGNOSTIC REPORT")
        logger.info("=" * 70)
        
        logger.info(f"Active Canvases: {report['lifecycle_manager']['active_canvases']}")
        logger.info(f"ID Scopes: {report['lifecycle_manager']['id_scopes']}")
        logger.info(f"Migration Status: {report['adapter']}")
        
        if report['validation_errors']:
            logger.warning(f"Validation Errors: {len(report['validation_errors'])}")
            for error in report['validation_errors']:
                logger.warning(f"  - {error}")
        else:
            logger.info("✓ All contexts valid")
        
        logger.info("=" * 70)


def enable_lifecycle_system(model_canvas_loader_instance) -> tuple:
    """Enable lifecycle system in ModelCanvasLoader instance.
    
    This function initializes the lifecycle manager and adapter,
    attaching them to an existing ModelCanvasLoader instance.
    
    Args:
        model_canvas_loader_instance: Instance of ModelCanvasLoader
        
    Returns:
        Tuple of (lifecycle_manager, adapter)
        
    Example:
        # In ModelCanvasLoader.__init__:
        from shypn.canvas.lifecycle.integration import enable_lifecycle_system
        self.lifecycle_manager, self.lifecycle_adapter = enable_lifecycle_system(self)
    """
    logger.info("Enabling canvas lifecycle system...")
    
    # Create lifecycle manager
    lifecycle_manager = CanvasLifecycleManager()
    
    # Create adapter
    adapter = LifecycleAdapter(lifecycle_manager)
    
    # Attach to instance
    model_canvas_loader_instance.lifecycle_manager = lifecycle_manager
    model_canvas_loader_instance.lifecycle_adapter = adapter
    
    logger.info("✓ Canvas lifecycle system enabled")
    logger.info(f"  Lifecycle manager: {lifecycle_manager}")
    logger.info(f"  Adapter: {adapter}")
    
    return (lifecycle_manager, adapter)
