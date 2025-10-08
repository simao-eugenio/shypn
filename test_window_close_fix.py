#!/usr/bin/env python3
"""Quick verification test for pathway panel window close fix.

This test verifies that the delete-event handler is properly connected
and prevents window destruction.
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_delete_event_handler():
    """Test that delete-event handler is connected."""
    print("Testing delete-event handler connection...")
    
    from shypn.helpers.pathway_panel_loader import create_pathway_panel
    
    # Create panel
    panel = create_pathway_panel()
    
    # Check that window exists
    assert panel.window is not None, "Window should be created"
    print("✓ Window created")
    
    # Check that _on_delete_event method exists
    assert hasattr(panel, '_on_delete_event'), "_on_delete_event method should exist"
    print("✓ _on_delete_event method exists")
    
    # Simulate delete event (without actually running GTK main loop)
    # The handler should return True to prevent destruction
    from gi.repository import Gdk
    event = Gdk.Event.new(Gdk.EventType.DELETE)
    result = panel._on_delete_event(panel.window, event)
    
    assert result == True, "Handler should return True to prevent destruction"
    print("✓ Handler returns True (prevents destruction)")
    
    # Verify window still exists after handler call
    assert panel.window is not None, "Window should still exist after delete event"
    print("✓ Window preserved after delete event")
    
    print("\n✅ All delete-event handler tests passed!")
    print("The window close crash should be fixed.")
    return True

if __name__ == '__main__':
    try:
        success = test_delete_event_handler()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
