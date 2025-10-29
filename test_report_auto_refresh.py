#!/usr/bin/env python3
"""Test Report Panel auto-refresh when topology analyses complete.

Tests that:
1. TopologyPanel can notify Report Panel
2. Report Panel automatically refreshes when topology updates
3. Data flows correctly and UI updates
"""
import sys
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

# Add src to path
sys.path.insert(0, '/home/simao/projetos/shypn/src')

from shypn.ui.panels.topology.topology_panel import TopologyPanel
from shypn.ui.panels.report.report_panel import ReportPanel


def test_notification_wiring():
    """Test that notification callback is properly wired."""
    print("=" * 60)
    print("TEST 1: Notification Wiring")
    print("=" * 60)
    
    # Create topology panel
    topology_panel = TopologyPanel(model_canvas=None)
    
    # Create report panel
    report_panel = ReportPanel(project=None, model_canvas=None)
    
    # Wire topology to report
    report_panel.set_topology_panel(topology_panel)
    
    # Verify callback was set
    assert topology_panel._report_refresh_callback is not None, \
        "Report refresh callback not set on topology panel"
    
    print("✓ Notification callback successfully wired")
    print(f"  Callback: {topology_panel._report_refresh_callback}")
    
    return topology_panel, report_panel


def test_manual_notification():
    """Test manual notification trigger."""
    print("\n" + "=" * 60)
    print("TEST 2: Manual Notification Trigger")
    print("=" * 60)
    
    topology_panel, report_panel = test_notification_wiring()
    
    # Track if report was refreshed
    refresh_count = [0]  # Use list to allow modification in closure
    
    # Monkey-patch the refresh method to track calls
    original_refresh = None
    for category in report_panel.categories:
        from shypn.ui.panels.report.topology_analyses_category import TopologyAnalysesCategory
        if isinstance(category, TopologyAnalysesCategory):
            original_refresh = category.refresh
            
            def tracked_refresh():
                refresh_count[0] += 1
                original_refresh()
            
            category.refresh = tracked_refresh
            break
    
    # Trigger notification
    print("Triggering topology panel notification...")
    topology_panel.notify_report_panel()
    
    # Check if refresh was called
    assert refresh_count[0] > 0, "Report panel was not refreshed after notification"
    
    print(f"✓ Report panel automatically refreshed")
    print(f"  Refresh count: {refresh_count[0]}")
    
    return topology_panel, report_panel


def test_category_notification():
    """Test that categories trigger notification when analyses complete."""
    print("\n" + "=" * 60)
    print("TEST 3: Category Auto-Notification")
    print("=" * 60)
    
    topology_panel, report_panel = test_notification_wiring()
    
    # Track notifications
    notification_count = [0]
    
    def track_notification():
        notification_count[0] += 1
        print(f"  → Notification #{notification_count[0]} received")
    
    topology_panel.set_report_refresh_callback(track_notification)
    
    # Verify categories have parent_panel set
    for i, category in enumerate(topology_panel.categories, 1):
        assert category.parent_panel is topology_panel, \
            f"Category {i} doesn't have parent_panel set"
        print(f"✓ Category {i}: parent_panel correctly set")
    
    # Simulate analysis completion by calling _update_summary on a category
    # First, we need to simulate a drawing area and analyzed set
    print("\nSimulating analysis completion...")
    category = topology_panel.categories[0]
    
    # Create a mock drawing area
    class MockDrawingArea:
        pass
    
    mock_da = MockDrawingArea()
    
    # Pretend category has model_canvas that returns this drawing area
    class MockModelCanvas:
        def get_current_document(self):
            return mock_da
    
    category.model_canvas = MockModelCanvas()
    
    # Add some analyzed data so _update_summary doesn't return early
    category.analyzed[mock_da] = {'p_invariants'}
    category.results_cache[mock_da] = {'p_invariants': {'data': []}}
    
    # Now call _update_summary which should notify parent
    category._update_summary()
    
    assert notification_count[0] > 0, "Category didn't notify parent panel"
    
    print(f"\n✓ Category automatically notified parent panel")
    print(f"  Total notifications: {notification_count[0]}")
    
    return True


def test_full_auto_refresh_flow():
    """Test complete auto-refresh flow."""
    print("\n" + "=" * 60)
    print("TEST 4: Complete Auto-Refresh Flow")
    print("=" * 60)
    
    # Create topology panel
    topology_panel = TopologyPanel(model_canvas=None)
    
    # Create report panel
    report_panel = ReportPanel(project=None, model_canvas=None)
    
    # Wire them together
    report_panel.set_topology_panel(topology_panel)
    
    # Verify complete wiring
    print("✓ Panels wired together")
    
    # Check that topology can notify report
    assert topology_panel._report_refresh_callback is not None
    print("✓ Topology → Report callback exists")
    
    # Check that categories know their parent
    for category in topology_panel.categories:
        assert category.parent_panel is topology_panel
    print("✓ Categories → Topology parent links exist")
    
    # Simulate analysis completing
    print("\nSimulating analysis completion...")
    
    # Track report refreshes
    refresh_log = []
    
    for category in report_panel.categories:
        from shypn.ui.panels.report.topology_analyses_category import TopologyAnalysesCategory
        if isinstance(category, TopologyAnalysesCategory):
            original_refresh = category.refresh
            
            def logged_refresh():
                refresh_log.append("Report refreshed")
                original_refresh()
            
            category.refresh = logged_refresh
            break
    
    # Trigger analysis completion on topology category
    category = topology_panel.categories[0]
    
    # Create mock drawing area and data
    class MockDrawingArea:
        pass
    
    mock_da = MockDrawingArea()
    
    class MockModelCanvas:
        def get_current_document(self):
            return mock_da
    
    category.model_canvas = MockModelCanvas()
    category.analyzed[mock_da] = {'p_invariants'}
    category.results_cache[mock_da] = {'p_invariants': {'data': []}}
    
    # Now trigger update
    category._update_summary()
    
    # Verify report was refreshed
    assert len(refresh_log) > 0, "Report panel didn't auto-refresh"
    
    print(f"✓ Report panel auto-refreshed: {len(refresh_log)} time(s)")
    print("\n✓ Complete auto-refresh flow working!")
    
    return True


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("TOPOLOGY → REPORT AUTO-REFRESH TEST")
    print("=" * 60 + "\n")
    
    try:
        # Test 1: Wiring
        test_notification_wiring()
        
        # Test 2: Manual notification
        test_manual_notification()
        
        # Test 3: Category auto-notification
        test_category_notification()
        
        # Test 4: Full flow
        test_full_auto_refresh_flow()
        
        print("\n" + "=" * 60)
        print("ALL TESTS PASSED ✓")
        print("=" * 60)
        print("\nAuto-refresh is working correctly!")
        print("\nFlow:")
        print("1. User expands analyzer in Topology Panel")
        print("2. Analysis completes in background thread")
        print("3. Category calls _update_summary()")
        print("4. Category notifies parent TopologyPanel")
        print("5. TopologyPanel calls report refresh callback")
        print("6. Report Panel automatically updates")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
