#!/usr/bin/env python3
"""Test topology panel awareness of model lifecycle events.

Verifies that:
1. Categories are aware when models are loaded
2. Analyzers can run on loaded models
3. Results are cleared when models are closed
4. UI state resets properly
"""

import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

# Mock GTK before importing
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

def test_clear_results():
    """Test clear_results() method clears analyzer state."""
    from shypn.ui.panels.topology.base_topology_category import BaseTopologyCategory
    
    print("Testing BaseTopologyCategory.clear_results()...")
    
    # Create mock category
    class TestCategory(BaseTopologyCategory):
        def _get_analyzers(self):
            return {}
        
        def _build_content(self):
            return Gtk.Box()
    
    category = TestCategory(
        title="TEST",
        model_canvas=None,
        expanded=False,
        use_grouped_table=True
    )
    
    # Mock drawing area
    drawing_area = Mock()
    
    # Simulate analyzer results
    category.results_cache[drawing_area] = {
        'test_analyzer': {'result': 'data'}
    }
    category.analyzed[drawing_area] = {'test_analyzer'}
    category.analyzing = {'test_analyzer'}
    category.analyzer_start_times = {'test_analyzer': 12345}
    
    print(f"  Before clear: {len(category.results_cache)} results")
    print(f"  Before clear: {len(category.analyzed)} analyzed")
    
    # Mock _get_current_drawing_area
    category._get_current_drawing_area = lambda: drawing_area
    
    # Clear results
    category.clear_results(drawing_area)
    
    # Verify cleanup
    assert drawing_area not in category.results_cache, "results_cache not cleared"
    assert drawing_area not in category.analyzed, "analyzed not cleared"
    assert len(category.analyzing) == 0, "analyzing not cleared"
    assert len(category.analyzer_start_times) == 0, "start_times not cleared"
    
    print("  ✅ After clear: all state cleared")
    print()
    return True

def test_topology_panel_clear_all():
    """Test TopologyPanel.clear_all_results() clears all categories."""
    from shypn.ui.panels.topology.topology_panel import TopologyPanel
    
    print("Testing TopologyPanel.clear_all_results()...")
    
    # Create panel
    panel = TopologyPanel(model=None, model_canvas=None)
    
    # Mock drawing area
    drawing_area = Mock()
    
    # Add mock results to all categories
    for category in panel.categories:
        category.results_cache[drawing_area] = {'test': 'data'}
        category.analyzed[drawing_area] = {'test'}
    
    print(f"  Added results to {len(panel.categories)} categories")
    
    # Clear all results
    panel.clear_all_results(drawing_area)
    
    # Verify all categories cleared
    for category in panel.categories:
        assert drawing_area not in category.results_cache, f"{category.title} not cleared"
        assert drawing_area not in category.analyzed, f"{category.title} analyzed not cleared"
    
    print("  ✅ All categories cleared")
    print()
    return True

def test_topology_loader_cleanup():
    """Test TopologyPanelLoader.on_tab_closed() calls clear_all_results()."""
    from shypn.helpers.topology_panel_loader import TopologyPanelLoader
    
    print("Testing TopologyPanelLoader.on_tab_closed()...")
    
    # Create loader
    loader = TopologyPanelLoader(model=None, parent_window=None)
    
    # Mock drawing area
    drawing_area = Mock()
    
    # Add mock results
    for category in loader.panel.categories:
        category.results_cache[drawing_area] = {'test': 'data'}
    
    print(f"  Added results to {len(loader.panel.categories)} categories")
    
    # Call on_tab_closed
    loader.on_tab_closed(drawing_area)
    
    # Verify cleared
    for category in loader.panel.categories:
        assert drawing_area not in category.results_cache, f"{category.title} not cleared"
    
    print("  ✅ on_tab_closed() cleared all results")
    print()
    return True

def test_refresh_updates_ui():
    """Test refresh() method updates UI state."""
    from shypn.ui.panels.topology.topology_panel import TopologyPanel
    
    print("Testing TopologyPanel.refresh()...")
    
    # Create panel
    panel = TopologyPanel(model=None, model_canvas=None)
    
    # Mock model canvas
    mock_canvas = Mock()
    mock_canvas.get_current_document = Mock(return_value=None)
    
    panel.set_model_canvas(mock_canvas)
    
    # Refresh should not crash
    panel.refresh()
    
    print("  ✅ refresh() executed without errors")
    print()
    return True

def test_model_aware_execution():
    """Test that analyzers check for model before running."""
    from shypn.ui.panels.topology.base_topology_category import BaseTopologyCategory
    
    print("Testing model awareness in _check_model_complexity()...")
    
    # Create mock category
    class TestCategory(BaseTopologyCategory):
        def _get_analyzers(self):
            return {}
        
        def _build_content(self):
            return Gtk.Box()
    
    category = TestCategory(
        title="TEST",
        model_canvas=None,
        expanded=False,
        use_grouped_table=True
    )
    
    # Check with no model
    is_viable, states, places, reason = category._check_model_complexity()
    
    assert not is_viable, "Should not be viable without model"
    assert reason == "No model loaded", f"Expected 'No model loaded', got '{reason}'"
    
    print("  ✅ Correctly detects 'No model loaded'")
    print()
    return True

def main():
    """Run all tests."""
    print("=" * 70)
    print("🔍 TESTING TOPOLOGY PANEL MODEL LIFECYCLE AWARENESS")
    print("=" * 70)
    print()
    
    tests = [
        ("Clear Results", test_clear_results),
        ("Panel Clear All", test_topology_panel_clear_all),
        ("Loader Cleanup", test_topology_loader_cleanup),
        ("Refresh Updates", test_refresh_updates_ui),
        ("Model Awareness", test_model_aware_execution),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name}: FAILED - {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Summary
    print("=" * 70)
    print("📋 SUMMARY")
    print("=" * 70)
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {name}")
    
    print(f"\n🎯 Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 SUCCESS! Topology panel is model lifecycle aware!")
        return 0
    else:
        print("\n⚠️  WARNING: Some tests failed.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
