"""Tests for Phase 4 UI wiring - canvas controller integration."""

import pytest
try:
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk
except ImportError:
    pytest.skip("GTK3 not available", allow_module_level=True)

from shypn.helpers.model_canvas_loader import ModelCanvasLoader
from shypn.engine.simulation.controller import SimulationController


class TestPhase4UIWiring:
    """Test that simulation controller is properly wired to canvas."""
    
    def test_controller_created_for_new_canvas(self, tmp_path):
        """Test that controller is created when canvas is added."""
        # Create loader
        loader = ModelCanvasLoader()
        loader.load()
        
        # Add a document (canvas)
        page_index, drawing_area = loader.add_document(filename='test')
        
        # Verify controller was created
        controller = loader.get_canvas_controller(drawing_area)
        assert controller is not None, "Controller should be created for canvas"
        assert isinstance(controller, SimulationController)
        
        # Verify controller has all components
        assert hasattr(controller, 'state_detector')
        assert hasattr(controller, 'buffered_settings')
        assert hasattr(controller, 'interaction_guard')
    
    def test_controller_accessible_by_drawing_area(self, tmp_path):
        """Test canvas-centric access pattern."""
        loader = ModelCanvasLoader()
        loader.load()
        
        # Add two documents
        page1, area1 = loader.add_document(filename='doc1')
        page2, area2 = loader.add_document(filename='doc2')
        
        # Each canvas should have its own controller
        controller1 = loader.get_canvas_controller(area1)
        controller2 = loader.get_canvas_controller(area2)
        
        assert controller1 is not None
        assert controller2 is not None
        assert controller1 is not controller2, "Each canvas should have separate controller"
    
    def test_controller_accessible_from_current_document(self):
        """Test getting controller for current document."""
        loader = ModelCanvasLoader()
        loader.load()
        
        # Add document
        loader.add_document(filename='test')
        
        # Get controller without specifying drawing_area (uses current)
        controller = loader.get_canvas_controller()
        assert controller is not None
    
    def test_controller_in_overlay_manager(self):
        """Test that controller is stored in overlay_manager for palette access."""
        loader = ModelCanvasLoader()
        loader.load()
        
        page_index, drawing_area = loader.add_document(filename='test')
        
        # Check overlay_manager has controller reference
        assert drawing_area in loader.overlay_managers
        overlay_mgr = loader.overlay_managers[drawing_area]
        assert hasattr(overlay_mgr, 'simulation_controller')
        assert overlay_mgr.simulation_controller is not None


class TestPhase4PermissionIntegration:
    """Test permission checking in UI handlers."""
    
    def test_controller_has_interaction_guard(self):
        """Test that controller provides interaction guard."""
        loader = ModelCanvasLoader()
        loader.load()
        
        page_index, drawing_area = loader.add_document(filename='test')
        controller = loader.get_canvas_controller(drawing_area)
        
        # Verify interaction guard is available
        assert hasattr(controller, 'interaction_guard')
        guard = controller.interaction_guard
        
        # Verify guard has permission methods
        assert hasattr(guard, 'can_activate_tool')
        assert hasattr(guard, 'check_tool_activation')
        assert hasattr(guard, 'get_block_reason')
    
    def test_permission_check_in_idle_state(self):
        """Test that tools are allowed in IDLE state."""
        loader = ModelCanvasLoader()
        loader.load()
        
        page_index, drawing_area = loader.add_document(filename='test')
        controller = loader.get_canvas_controller(drawing_area)
        
        # In IDLE state, structural tools should be allowed
        allowed, reason = controller.interaction_guard.check_tool_activation('place')
        assert allowed is True
        assert reason is None
        
        allowed, reason = controller.interaction_guard.check_tool_activation('transition')
        assert allowed is True
        
        allowed, reason = controller.interaction_guard.check_tool_activation('arc')
        assert allowed is True
    
    def test_permission_check_when_running(self):
        """Test that structural tools are blocked when simulation running."""
        loader = ModelCanvasLoader()
        loader.load()
        
        page_index, drawing_area = loader.add_document(filename='test')
        controller = loader.get_canvas_controller(drawing_area)
        canvas_manager = loader.get_canvas_manager(drawing_area)
        
        # Simulate RUNNING state:
        # - time > 0 (simulation started)
        # - _running = True (actively executing)
        controller.time = 1.0  # Use 'time' not 'current_time'
        controller._running = True
        
        # Structural tools should now be blocked
        allowed, reason = controller.interaction_guard.check_tool_activation('place')
        assert allowed is False
        assert reason is not None
        assert 'reset' in reason.lower() or 'stop' in reason.lower()
        
        # Selection tools should still be allowed
        allowed, _ = controller.interaction_guard.check_tool_activation('select')
        assert allowed is True


class TestPhase4RefactoringSafety:
    """Test that wiring is safe for SwissPalette refactoring."""
    
    def test_accessor_method_exists(self):
        """Test that get_canvas_controller() accessor exists."""
        loader = ModelCanvasLoader()
        assert hasattr(loader, 'get_canvas_controller')
        assert callable(loader.get_canvas_controller)
    
    def test_controllers_dictionary_exists(self):
        """Test that simulation_controllers storage exists."""
        loader = ModelCanvasLoader()
        assert hasattr(loader, 'simulation_controllers')
        assert isinstance(loader.simulation_controllers, dict)
    
    def test_canvas_keyed_storage(self):
        """Test that controllers are keyed by drawing_area, not palette."""
        loader = ModelCanvasLoader()
        loader.load()
        
        page_index, drawing_area = loader.add_document(filename='test')
        
        # Controller should be in simulation_controllers dict
        assert drawing_area in loader.simulation_controllers
        controller = loader.simulation_controllers[drawing_area]
        assert isinstance(controller, SimulationController)
    
    def test_multiple_access_paths(self):
        """Test that controller can be accessed multiple ways."""
        loader = ModelCanvasLoader()
        loader.load()
        
        page_index, drawing_area = loader.add_document(filename='test')
        
        # Access via get_canvas_controller()
        controller1 = loader.get_canvas_controller(drawing_area)
        
        # Access via simulation_controllers dict
        controller2 = loader.simulation_controllers[drawing_area]
        
        # Access via overlay_manager
        controller3 = loader.overlay_managers[drawing_area].simulation_controller
        
        # All should be the same instance
        assert controller1 is controller2
        assert controller2 is controller3
