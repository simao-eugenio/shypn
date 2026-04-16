#!/usr/bin/env python3
"""
Basic integration test for canvas lifecycle system.

Tests the simple registration flow without requiring full component creation.

Author: Canvas Lifecycle Team
Date: 2025-01-05
"""

import sys
sys.path.insert(0, '/home/simao/projetos/shypn/src')

from unittest.mock import Mock
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from shypn.canvas.lifecycle import (
    CanvasContext,
    IDScopeManager,
    CanvasLifecycleManager,
    LifecycleAdapter
)


def create_mock_document_model():
    """Create a mock document model with required attributes."""
    mock = Mock()
    mock.places = []
    mock.transitions = []
    mock.arcs = []
    return mock


def test_id_scope_manager():
    """Test basic ID scoping."""
    print("\n=== Testing IDScopeManager ===")
    manager = IDScopeManager()
    
    # Scope 1
    manager.set_scope("canvas_1")
    p1 = manager.generate_place_id()
    print(f"✓ Canvas 1 - First place ID: {p1}")
    assert p1 == "P1", f"Expected P1, got {p1}"
    
    p2 = manager.generate_place_id()
    print(f"✓ Canvas 1 - Second place ID: {p2}")
    assert p2 == "P2", f"Expected P2, got {p2}"
    
    # Scope 2
    manager.set_scope("canvas_2")
    p1_s2 = manager.generate_place_id()
    print(f"✓ Canvas 2 - First place ID: {p1_s2}")
    assert p1_s2 == "P1", f"Expected P1, got {p1_s2}"
    
    # Back to scope 1
    manager.set_scope("canvas_1")
    p3 = manager.generate_place_id()
    print(f"✓ Canvas 1 - Third place ID: {p3}")
    assert p3 == "P3", f"Expected P3, got {p3}"
    
    print("✓ IDScopeManager test PASSED\n")
    return True


def test_lifecycle_manager():
    """Test basic lifecycle manager without full component creation."""
    print("=== Testing CanvasLifecycleManager (registration only) ===")
    manager = CanvasLifecycleManager()
    
    # Create real GTK drawing area
    da1 = Gtk.DrawingArea()
    doc = create_mock_document_model()
    
    # Manually register (simulating what adapter does)
    context = CanvasContext(
        drawing_area=da1,
        document_model=doc,
        controller=Mock(),
        palette=Mock(),
        id_scope="canvas_12345",
        canvas_manager=doc  # Same as document_model
    )
    
    canvas_id = id(da1)
    manager.canvas_registry[canvas_id] = context
    print(f"✓ Registered canvas context: {canvas_id}")
    
    # Verify retrieval
    retrieved = manager.canvas_registry.get(canvas_id)
    assert retrieved is not None, "Failed to retrieve context"
    assert retrieved.drawing_area == da1, "Retrieved wrong context"
    print(f"✓ Retrieved canvas context successfully")
    
    print("✓ CanvasLifecycleManager test PASSED\n")
    return True


def test_lifecycle_adapter():
    """Test adapter registration."""
    print("=== Testing LifecycleAdapter ===")
    lifecycle_manager = CanvasLifecycleManager()
    adapter = LifecycleAdapter(lifecycle_manager)
    
    # Create real GTK drawing area
    da = Gtk.DrawingArea()
    doc = create_mock_document_model()
    controller = Mock()
    palette = Mock()
    
    # Register
    adapter.register_canvas(da, doc, controller, palette)
    print(f"✓ Registered canvas via adapter")
    
    # Verify
    context = adapter.get_canvas_context(da)
    assert context is not None, "Failed to get context"
    assert context.document_model == doc, "Wrong document model"
    assert context.controller == controller, "Wrong controller"
    assert context.palette == palette, "Wrong palette"
    print(f"✓ Verified canvas components")
    
    print("✓ LifecycleAdapter test PASSED\n")
    return True


def test_multi_canvas_scenario():
    """Test realistic multi-canvas scenario."""
    print("=== Testing Multi-Canvas Scenario ===")
    lifecycle_manager = CanvasLifecycleManager()
    adapter = LifecycleAdapter(lifecycle_manager)
    
    # Create three canvases with real GTK drawing areas
    da1 = Gtk.DrawingArea()
    da2 = Gtk.DrawingArea()
    da3 = Gtk.DrawingArea()
    
    adapter.register_canvas(da1, create_mock_document_model(), Mock(), Mock())
    adapter.register_canvas(da2, create_mock_document_model(), Mock(), Mock())
    adapter.register_canvas(da3, create_mock_document_model(), Mock(), Mock())
    print(f"✓ Registered 3 canvases")
    
    # Verify all registered
    assert adapter.get_canvas_context(da1) is not None
    assert adapter.get_canvas_context(da2) is not None
    assert adapter.get_canvas_context(da3) is not None
    print(f"✓ All canvases accessible")
    
    # Switch between them
    adapter.switch_to_canvas(da2)
    print(f"✓ Switched to canvas 2")
    
    adapter.switch_to_canvas(da1)
    print(f"✓ Switched to canvas 1")
    
    # Destroy one
    adapter.destroy_canvas(da2)
    assert adapter.get_canvas_context(da2) is None
    assert adapter.get_canvas_context(da1) is not None
    assert adapter.get_canvas_context(da3) is not None
    print(f"✓ Destroyed canvas 2, others preserved")
    
    print("✓ Multi-Canvas test PASSED\n")
    return True


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("Canvas Lifecycle Integration - Basic Tests")
    print("="*60)
    
    tests = [
        ("ID Scope Manager", test_id_scope_manager),
        ("Lifecycle Manager", test_lifecycle_manager),
        ("Lifecycle Adapter", test_lifecycle_adapter),
        ("Multi-Canvas Scenario", test_multi_canvas_scenario)
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
                print(f"✗ {name} FAILED")
        except Exception as e:
            failed += 1
            print(f"✗ {name} FAILED with exception:")
            print(f"  {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*60)
    print(f"Results: {passed} passed, {failed} failed")
    print("="*60 + "\n")
    
    return failed == 0


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
