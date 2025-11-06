"""
Canvas Lifecycle Manager - Coordinates canvas component lifecycles.

Manages the complete lifecycle of canvas-scoped components:
1. Creation: Initializes all components for a new canvas
2. Synchronization: Keeps components in sync during operations
3. Reset: Clears state when loading new files
4. Cleanup: Properly destroys components when canvas closes

This ensures that global components (SwissKnifePalette, SimulationController)
are properly isolated per canvas and synchronized with canvas/document state.
"""

import logging
from typing import Dict, Optional
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

from .canvas_context import CanvasContext
from .id_scope_manager import IDScopeManager

# Setup logging
logger = logging.getLogger(__name__)


class CanvasLifecycleManager:
    """Manages lifecycle of canvas-scoped global components.
    
    This class coordinates the creation, synchronization, reset, and cleanup
    of all components associated with a canvas instance. It ensures that:
    
    1. Each canvas has isolated instances of:
       - DocumentModel (places, transitions, arcs)
       - SimulationController (simulation state, behaviors)
       - SwissKnifePalette (tools, mode state)
       - IDManager scope (ID counters)
    
    2. Components stay synchronized during:
       - File loading (File → Open)
       - File creation (File → New)
       - Heuristic application
       - Parameter updates
       - Tab switching
    
    3. Resources are properly cleaned up when:
       - Canvas closed (tab closed)
       - Application shutdown
    
    Usage:
        manager = CanvasLifecycleManager()
        
        # Create new canvas
        context = manager.create_canvas(drawing_area, canvas_manager)
        
        # Load file into existing canvas
        manager.load_file(drawing_area, "model.shy")
        
        # Switch between canvases
        manager.switch_canvas(old_area, new_area)
        
        # Clean up closed canvas
        manager.destroy_canvas(drawing_area)
    """
    
    def __init__(self):
        """Initialize lifecycle manager."""
        self.canvas_registry: Dict[int, CanvasContext] = {}  # canvas_id -> context
        self.id_manager = IDScopeManager()
        logger.info("CanvasLifecycleManager initialized")
    
    def create_canvas(
        self,
        drawing_area: Gtk.DrawingArea,
        canvas_manager: 'ModelCanvasManager',
        file_path: Optional[str] = None
    ) -> CanvasContext:
        """Create and register a new canvas with all components.
        
        This method:
        1. Creates a unique ID scope for this canvas
        2. Initializes DocumentModel
        3. Creates SimulationController
        4. Creates SwissKnifePalette
        5. Links all components together
        6. Registers in canvas registry
        
        Args:
            drawing_area: GTK DrawingArea widget for this canvas
            canvas_manager: ModelCanvasManager instance (acts as document model)
            file_path: Optional path to .shy file to load
            
        Returns:
            CanvasContext with all initialized components
            
        Raises:
            ValueError: If canvas already exists
        """
        canvas_id = id(drawing_area)
        
        # Check if canvas already exists
        if canvas_id in self.canvas_registry:
            raise ValueError(f"Canvas {canvas_id} already registered")
        
        logger.info(f"Creating canvas {canvas_id} (file={file_path or 'new'})")
        
        # 1. Set IDManager scope
        scope_name = f"canvas_{canvas_id}"
        self.id_manager.set_scope(scope_name)
        logger.debug(f"  Set ID scope: {scope_name}")
        
        # 2. Document model is the canvas_manager itself
        # (canvas_manager has places, transitions, arcs attributes)
        document_model = canvas_manager
        
        # 3. Load file if provided
        if file_path:
            try:
                # File loading handled by model_canvas_loader
                # This method just tracks the association
                logger.debug(f"  File will be loaded by model_canvas_loader: {file_path}")
            except Exception as e:
                logger.error(f"  Failed to load file {file_path}: {e}")
                raise
        
        # 4. Create simulation controller
        # Import here to avoid circular dependency
        from shypn.engine.simulation import SimulationController
        controller = SimulationController(document_model)
        logger.debug(f"  Created SimulationController: {id(controller)}")
        
        # 5. Create SwissKnife palette
        # Import here to avoid circular dependency
        from shypn.helpers.swissknife_palette import SwissKnifePalette
        from shypn.helpers.tool_registry import ToolRegistry
        
        tool_registry = ToolRegistry()
        palette = SwissKnifePalette(
            mode='edit',
            model=document_model,
            tool_registry=tool_registry
        )
        logger.debug(f"  Created SwissKnifePalette: {id(palette)}")
        
        # 6. Link palette simulation tools to controller
        self._link_palette_to_controller(palette, controller)
        
        # 7. Create context object
        context = CanvasContext(
            drawing_area=drawing_area,
            document_model=document_model,
            controller=controller,
            palette=palette,
            id_scope=scope_name,
            canvas_manager=canvas_manager,
            file_path=file_path
        )
        
        # 8. Register
        self.canvas_registry[canvas_id] = context
        logger.info(f"✓ Canvas {canvas_id} created: {context}")
        
        return context
    
    def _link_palette_to_controller(self, palette, controller):
        """Link SwissKnifePalette simulation tools to SimulationController.
        
        Args:
            palette: SwissKnifePalette instance
            controller: SimulationController instance
        """
        # Get simulate tools palette from SwissKnifePalette widget instances
        simulate_tools = palette.widget_palette_instances.get('simulate')
        
        if simulate_tools:
            # Update controller reference
            simulate_tools.simulation = controller
            logger.debug("    Linked simulate_tools.simulation → controller")
            
            # Register step listeners
            if hasattr(simulate_tools, '_on_simulation_step'):
                controller.add_step_listener(simulate_tools._on_simulation_step)
                logger.debug("    Registered palette step listener")
            
            if hasattr(simulate_tools, 'data_collector'):
                controller.add_step_listener(simulate_tools.data_collector.on_simulation_step)
                controller.data_collector = simulate_tools.data_collector
                logger.debug("    Registered data collector step listener")
        else:
            logger.warning("    simulate_tools palette not found - simulation signals won't work!")
    
    def get_context(self, drawing_area: Gtk.DrawingArea) -> Optional[CanvasContext]:
        """Get canvas context for a drawing area.
        
        Args:
            drawing_area: GTK DrawingArea widget
            
        Returns:
            CanvasContext or None if not found
        """
        canvas_id = id(drawing_area)
        return self.canvas_registry.get(canvas_id)
    
    def reset_canvas(self, drawing_area: Gtk.DrawingArea):
        """Reset canvas to initial state (File → New equivalent).
        
        Clears all objects, resets simulation, reinitializes palette.
        Preserves the canvas instance and ID scope.
        
        Args:
            drawing_area: GTK DrawingArea widget
            
        Raises:
            ValueError: If canvas not registered
        """
        context = self.get_context(drawing_area)
        if not context:
            raise ValueError(f"Canvas {id(drawing_area)} not registered")
        
        logger.info(f"Resetting canvas {context.canvas_id}: {context.display_name}")
        
        # 1. Stop any running simulation
        if context.is_simulation_running:
            logger.debug("  Stopping simulation...")
            context.controller.stop()
        
        # 2. Clear document model
        logger.debug("  Clearing document model...")
        context.document_model.places.clear()
        context.document_model.transitions.clear()
        context.document_model.arcs.clear()
        
        # 3. Reset simulation controller
        logger.debug("  Resetting simulation controller...")
        context.controller.reset()
        # Clear behavior cache
        if hasattr(context.controller, 'behavior_cache'):
            context.controller.behavior_cache.clear()
        
        # 4. Reset palette state
        logger.debug("  Resetting palette...")
        context.palette.set_mode('edit')
        # Reset tool selection if method exists
        if hasattr(context.palette, 'reset_tool_selection'):
            context.palette.reset_tool_selection()
        
        # 5. Reset simulation tools palette UI state
        logger.debug("  Resetting simulation palette UI...")
        sim_palette = context.simulate_tools_palette
        if sim_palette:
            # Re-apply UI defaults (duration, units) to ensure progress bar works
            sim_palette._apply_ui_defaults_to_settings()
            # Reset progress bar display to 0%
            if sim_palette.progress_bar:
                sim_palette.progress_bar.set_fraction(0.0)
                sim_palette.progress_bar.set_text("0%")
            # Reset time display
            if sim_palette.time_display_label:
                sim_palette.time_display_label.set_text("Time: 0.0 s")
            logger.debug("  ✓ Simulation palette UI reset complete")
        
        # 6. Reset IDManager scope
        logger.debug(f"  Resetting ID scope: {context.id_scope}")
        self.id_manager.reset_scope(context.id_scope)
        
        # 7. Update context metadata
        context.file_path = None
        context.is_modified = False
        context.last_save_time = None
        
        logger.info(f"✓ Canvas {context.canvas_id} reset complete")
    
    def sync_after_file_load(self, drawing_area: Gtk.DrawingArea, file_path: str):
        """Synchronize components after loading a file.
        
        This ensures:
        1. IDManager registers all existing IDs
        2. Controller creates TransitionState for all transitions
        3. Palette references are updated
        4. Context metadata is updated
        
        Args:
            drawing_area: GTK DrawingArea widget
            file_path: Path to loaded file
            
        Raises:
            ValueError: If canvas not registered
        """
        context = self.get_context(drawing_area)
        if not context:
            raise ValueError(f"Canvas {id(drawing_area)} not registered")
        
        logger.info(f"Syncing canvas {context.canvas_id} after loading: {file_path}")
        
        # 1. Set correct ID scope
        self.id_manager.set_scope(context.id_scope)
        
        # 2. Register all existing IDs
        logger.debug("  Registering existing IDs...")
        for place in context.document_model.places:
            self.id_manager.register_place_id(str(place.id))
        for transition in context.document_model.transitions:
            self.id_manager.register_transition_id(str(transition.id))
        for arc in context.document_model.arcs:
            self.id_manager.register_arc_id(str(arc.id))
        
        id_state = self.id_manager.get_scope_state(context.id_scope)
        logger.debug(f"  ID state after registration: P={id_state[0]}, T={id_state[1]}, A={id_state[2]}")
        
        # 3. Ensure controller has TransitionState for all transitions
        logger.debug("  Initializing transition states...")
        from shypn.engine.simulation.state.transition_state import TransitionState
        
        for transition in context.document_model.transitions:
            if transition.id not in context.controller.transition_states:
                context.controller.transition_states[transition.id] = TransitionState()
                logger.debug(f"    Created TransitionState for {transition.id}")
        
        # 4. Update context metadata
        context.file_path = file_path
        context.is_modified = False
        context.mark_saved(file_path)
        
        # 5. Re-link palette to controller (in case references changed)
        self._link_palette_to_controller(context.palette, context.controller)
        
        logger.info(f"✓ Canvas {context.canvas_id} sync complete")
    
    def switch_canvas(self, from_area: Optional[Gtk.DrawingArea], to_area: Gtk.DrawingArea):
        """Handle canvas tab switching.
        
        Deactivates old canvas (pauses simulation if running),
        activates new canvas (sets ID scope).
        
        Args:
            from_area: Previous canvas (None if first switch)
            to_area: New canvas to activate
        """
        if from_area:
            old_context = self.get_context(from_area)
            if old_context:
                logger.debug(f"Deactivating canvas {old_context.canvas_id}")
                
                # Pause simulation if running
                if old_context.is_simulation_running:
                    logger.debug("  Pausing simulation...")
                    old_context.controller.stop()
        
        # Activate new canvas
        new_context = self.get_context(to_area)
        if new_context:
            logger.debug(f"Activating canvas {new_context.canvas_id}: {new_context.display_name}")
            
            # Set ID scope
            self.id_manager.set_scope(new_context.id_scope)
            logger.debug(f"  ID scope set to: {new_context.id_scope}")
        else:
            logger.warning(f"Canvas {id(to_area)} not registered - cannot activate")
    
    def destroy_canvas(self, drawing_area: Gtk.DrawingArea):
        """Cleanup canvas resources (tab closed).
        
        Args:
            drawing_area: GTK DrawingArea widget
        """
        context = self.get_context(drawing_area)
        if not context:
            logger.warning(f"Canvas {id(drawing_area)} not registered - nothing to destroy")
            return
        
        logger.info(f"Destroying canvas {context.canvas_id}: {context.display_name}")
        
        # 1. Stop simulation
        if context.is_simulation_running:
            logger.debug("  Stopping simulation...")
            context.controller.stop()
        
        # 2. Cleanup palette
        if hasattr(context.palette, 'cleanup'):
            logger.debug("  Cleaning up palette...")
            context.palette.cleanup()
        
        # 3. Remove step listeners to prevent callbacks to destroyed objects
        if hasattr(context.controller, 'step_listeners'):
            logger.debug("  Clearing step listeners...")
            context.controller.step_listeners.clear()
        
        # 4. Delete ID scope
        logger.debug(f"  Deleting ID scope: {context.id_scope}")
        self.id_manager.delete_scope(context.id_scope)
        
        # 5. Remove from registry
        del self.canvas_registry[context.canvas_id]
        
        logger.info(f"✓ Canvas {context.canvas_id} destroyed")
    
    def get_all_contexts(self) -> list:
        """Get all registered canvas contexts.
        
        Returns:
            List of CanvasContext instances
        """
        return list(self.canvas_registry.values())
    
    def get_active_canvas_count(self) -> int:
        """Get number of active canvases.
        
        Returns:
            Count of registered canvases
        """
        return len(self.canvas_registry)
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"CanvasLifecycleManager("
            f"canvases={len(self.canvas_registry)}, "
            f"id_scopes={len(self.id_manager.get_all_scopes())})"
        )
