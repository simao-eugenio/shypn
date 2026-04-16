"""
Shared fixtures for UI validation tests.

These fixtures provide reusable components for testing dialog behavior,
persistence, and dynamic updates.
"""
import pytest
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'src'))

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from shypn.netobjs.place import Place
from shypn.netobjs.transition import Transition
from shypn.netobjs.arc import Arc
from shypn.core.controllers.document_controller import DocumentController
from shypn.engine.simulation.controller import SimulationController


# ============================================================================
# Manager Fixtures
# ============================================================================

@pytest.fixture
def document_controller():
    """Create a DocumentController for managing net objects."""
    controller = DocumentController()
    yield controller
    # Cleanup
    controller.clear_all_objects()


@pytest.fixture
def simulation_controller(document_controller):
    """Create a SimulationController for mode switching tests."""
    controller = SimulationController(document_controller)
    yield controller
    # Cleanup
    if controller.is_running():
        controller.stop()


# ============================================================================
# Object Creation Fixtures
# ============================================================================

@pytest.fixture
def create_place(document_controller):
    """Factory fixture to create places with custom properties."""
    def _create_place(x=100, y=100, label="P1", tokens=0, capacity=float('inf'), 
                     radius=30, border_width=2.0, border_color=(0.0, 0.0, 0.0)):
        """Create a place with specified properties.
        
        Args:
            x, y: Position coordinates
            label: Place label
            tokens: Initial marking
            capacity: Maximum tokens (default: inf)
            radius: Circle radius
            border_width: Line width
            border_color: RGB tuple (0.0-1.0)
            
        Returns:
            Place: Created place object
        """
        place = document_controller.add_place(x=x, y=y, label=label)
        place.tokens = tokens
        place.initial_marking = tokens
        place.capacity = capacity
        place.radius = radius
        place.border_width = border_width
        place.border_color = border_color
        return place
    
    return _create_place


@pytest.fixture
def create_transition(document_controller):
    """Factory fixture to create transitions with custom properties."""
    def _create_transition(x=200, y=100, label="T1", transition_type='immediate',
                          priority=1, rate=None, guard=None, 
                          border_width=3.0, border_color=(0.0, 0.0, 0.0)):
        """Create a transition with specified properties.
        
        Args:
            x, y: Position coordinates
            label: Transition label
            transition_type: 'immediate', 'timed', 'stochastic', or 'continuous'
            priority: Priority level (for immediate transitions)
            rate: Rate value (for timed/stochastic/continuous)
            guard: Guard expression
            border_width: Line width
            border_color: RGB tuple (0.0-1.0)
            
        Returns:
            Transition: Created transition object
        """
        trans = document_controller.add_transition(x=x, y=y, label=label)
        trans.transition_type = transition_type
        trans.priority = priority
        if rate is not None:
            trans.rate = rate
        if guard is not None:
            trans.guard = guard
        trans.border_width = border_width
        trans.border_color = border_color
        trans.fill_color = border_color
        return trans
    
    return _create_transition


@pytest.fixture
def create_arc(document_controller, create_place, create_transition):
    """Factory fixture to create arcs with custom properties."""
    def _create_arc(direction='place_to_transition', weight=1, 
                   arc_type='normal', line_width=2.0, color=(0.0, 0.0, 0.0)):
        """Create an arc with specified properties.
        
        Args:
            direction: 'place_to_transition' or 'transition_to_place'
            weight: Arc weight
            arc_type: 'normal' or 'inhibitor'
            line_width: Line width
            color: RGB tuple (0.0-1.0)
            
        Returns:
            Arc: Created arc object
        """
        # Create source and target
        if direction == 'place_to_transition':
            source = create_place(x=100, y=100, label="P_src")
            target = create_transition(x=200, y=100, label="T_tgt")
        else:
            source = create_transition(x=100, y=100, label="T_src")
            target = create_place(x=200, y=100, label="P_tgt")
        
        # Create arc
        arc = document_controller.add_arc(source=source, target=target, weight=weight)
        
        # Set arc type (transform if needed)
        if arc_type == 'inhibitor' and direction == 'place_to_transition':
            from shypn.utils.arc_transform import convert_to_inhibitor
            arc = convert_to_inhibitor(arc)
        
        arc.width = line_width
        arc.color = color
        
        return arc
    
    return _create_arc


# ============================================================================
# Dialog Fixtures
# ============================================================================

@pytest.fixture
def mock_window():
    """Create a mock GTK window for dialog parents (when needed).
    
    Note: Most tests should use parent_window=None to avoid showing windows.
    This fixture is for tests that specifically need a parent window.
    """
    window = Gtk.Window(title="Test Window")
    window.set_default_size(400, 300)
    yield window
    # Don't destroy - let GTK handle cleanup


# ============================================================================
# Utility Fixtures
# ============================================================================

@pytest.fixture
def ui_dir():
    """Get the UI directory path."""
    return Path(__file__).parent.parent.parent.parent / 'ui' / 'dialogs'


@pytest.fixture
def assert_field_visible():
    """Helper to check if a widget is visible."""
    def _check(widget, expected_visible=True, msg=None):
        """Check widget visibility.
        
        Args:
            widget: GTK widget to check
            expected_visible: Expected visibility state
            msg: Optional custom error message
        """
        if widget is None:
            raise AssertionError(f"Widget is None{': ' + msg if msg else ''}")
        
        actual = widget.get_visible()
        if actual != expected_visible:
            state = "visible" if expected_visible else "hidden"
            raise AssertionError(
                f"Widget should be {state} but is {'visible' if actual else 'hidden'}"
                f"{': ' + msg if msg else ''}"
            )
    
    return _check


@pytest.fixture
def assert_field_value():
    """Helper to check field values."""
    def _check(entry_widget, expected_value, msg=None):
        """Check entry widget value.
        
        Args:
            entry_widget: GtkEntry widget
            expected_value: Expected text value
            msg: Optional custom error message
        """
        if entry_widget is None:
            raise AssertionError(f"Entry widget is None{': ' + msg if msg else ''}")
        
        actual = entry_widget.get_text()
        if str(actual) != str(expected_value):
            raise AssertionError(
                f"Expected '{expected_value}' but got '{actual}'"
                f"{': ' + msg if msg else ''}"
            )
    
    return _check
