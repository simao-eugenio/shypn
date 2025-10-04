#!/usr/bin/env python3
"""Test drag integration with EditingController."""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from shypn.edit.editing_controller import EditingController
from shypn.edit.drag_controller import DragController
from shypn.netobjs import Place


class MockCanvas:
    """Mock canvas for testing."""
    
    def __init__(self, zoom=1.0, pan_x=0, pan_y=0):
        self.zoom = zoom
        self.pan_x = pan_x
        self.pan_y = pan_y
    
    def screen_to_world(self, screen_x, screen_y):
        """Convert screen to world coordinates."""
        world_x = (screen_x / self.zoom) - self.pan_x
        world_y = (screen_y / self.zoom) - self.pan_y
        return world_x, world_y


class MockManager:
    """Mock manager for testing."""
    
    def __init__(self):
        self.zoom = 1.0
        self.pan_x = 0
        self.pan_y = 0
        self.objects = []
        # Initialize selection_manager from editing controller
        from shypn.edit.selection_manager import SelectionManager
        self.selection_manager = SelectionManager()
    
    def screen_to_world(self, screen_x, screen_y):
        """Convert screen to world coordinates."""
        world_x = (screen_x / self.zoom) - self.pan_x
        world_y = (screen_y / self.zoom) - self.pan_y
        return world_x, world_y
    
    def get_all_objects(self):
        """Get all objects."""
        return self.objects


def test_drag_single_object():
    """Test dragging a single object."""
    print("\n=== Test: Drag Single Object ===")
    
    # Create objects (note: Place(x, y, id, name))
    place = Place(100, 100, 1, "P1")
    place.selected = True
    
    # Create manager
    manager = MockManager()
    manager.objects = [place]
    
    # Create editing controller with manager's selection_manager
    editing_controller = EditingController(selection_manager=manager.selection_manager)
    
    # Start drag with click
    print(f"Before click: is_dragging={editing_controller.is_dragging()}")
    result = editing_controller.handle_click(place, 100, 100, is_ctrl=False, manager=manager)
    print(f"After click: is_dragging={editing_controller.is_dragging()}, result={result}")
    print(f"Potential drag start: {editing_controller._potential_drag_start}")
    
    # Move mouse to trigger drag
    print(f"\nBefore motion: position=({place.x}, {place.y})")
    print(f"Selected objects from manager: {manager.get_all_objects()}")
    print(f"Place.selected: {place.selected}")
    print(f"Selected objects: {editing_controller._get_selected_objects(manager)}")
    result = editing_controller.handle_motion(150, 150, manager)
    print(f"After motion: is_dragging={editing_controller.is_dragging()}, result={result}")
    print(f"Position: ({place.x}, {place.y})")
    
    # Check if object moved
    print(f"\nInitial position: (100, 100)")
    print(f"Final position: ({place.x}, {place.y})")
    print(f"Expected: (~150, ~150)")
    
    # End drag
    editing_controller.handle_release()
    
    # Verify object moved
    assert place.x == 150, f"Expected x=150, got {place.x}"
    assert place.y == 150, f"Expected y=150, got {place.y}"
    
    print("✓ Object moved correctly")


def test_drag_multiple_objects():
    """Test dragging multiple objects."""
    print("\n=== Test: Drag Multiple Objects ===")
    
    # Create objects (note: Place(x, y, id, name))
    place1 = Place(100, 100, 1, "P1")
    place2 = Place(200, 200, 2, "P2")
    place1.selected = True
    place2.selected = True
    
    # Create manager
    manager = MockManager()
    manager.objects = [place1, place2]
    
    # Create editing controller with manager's selection_manager
    editing_controller = EditingController(selection_manager=manager.selection_manager)
    
    # Start drag with click on first place
    editing_controller.handle_click(place1, 100, 100, is_ctrl=False, manager=manager)
    
    # Move mouse to trigger drag
    editing_controller.handle_motion(150, 150, manager)
    
    # Check if both objects moved
    print(f"Place1: ({place1.x}, {place1.y}) - Expected: (~150, ~150)")
    print(f"Place2: ({place2.x}, {place2.y}) - Expected: (~250, ~250)")
    
    # End drag
    editing_controller.handle_release()
    
    # Verify both objects moved by same delta (50, 50)
    assert place1.x == 150, f"Expected place1.x=150, got {place1.x}"
    assert place1.y == 150, f"Expected place1.y=150, got {place1.y}"
    assert place2.x == 250, f"Expected place2.x=250, got {place2.x}"
    assert place2.y == 250, f"Expected place2.y=250, got {place2.y}"
    
    print("✓ Multiple objects moved correctly")


def test_drag_threshold():
    """Test that drag doesn't start until threshold exceeded."""
    print("\n=== Test: Drag Threshold ===")
    
    # Create object (note: Place(x, y, id, name))
    place = Place(100, 100, 1, "P1")
    place.selected = True
    
    # Create manager
    manager = MockManager()
    manager.objects = [place]
    
    # Create editing controller with manager's selection_manager
    editing_controller = EditingController(selection_manager=manager.selection_manager)
    
    # Start drag with click
    editing_controller.handle_click(place, 100, 100, is_ctrl=False, manager=manager)
    
    # Move mouse by only 2 pixels (below 5-pixel threshold)
    editing_controller.handle_motion(102, 102, manager)
    
    # Check if drag started
    print(f"Position after 2px move: ({place.x}, {place.y})")
    print(f"Is dragging: {editing_controller.is_dragging()}")
    
    # Object should NOT have moved yet
    assert place.x == 100, f"Expected x=100 (no drag), got {place.x}"
    assert place.y == 100, f"Expected y=100 (no drag), got {place.y}"
    assert not editing_controller.is_dragging(), "Should not be dragging yet"
    
    # Now move by 10 pixels (exceeds threshold)
    editing_controller.handle_motion(110, 110, manager)
    
    print(f"Position after 10px move: ({place.x}, {place.y})")
    print(f"Is dragging: {editing_controller.is_dragging()}")
    
    # Now drag should be active and object moved
    assert editing_controller.is_dragging(), "Should be dragging now"
    assert place.x == 110, f"Expected x=110, got {place.x}"
    assert place.y == 110, f"Expected y=110, got {place.y}"
    
    # End drag
    editing_controller.handle_release()
    
    print("✓ Drag threshold works correctly")


if __name__ == '__main__':
    test_drag_single_object()
    test_drag_multiple_objects()
    test_drag_threshold()
    
    print("\n" + "="*50)
    print("All tests passed! ✓")
    print("="*50)
