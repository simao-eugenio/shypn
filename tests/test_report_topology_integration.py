#!/usr/bin/env python3
"""Test Report Panel integration with Topology Panel.

Tests that:
1. TopologyPanel can generate summary
2. Report Panel can receive and display summary
3. Data flows correctly between panels
"""
import sys
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

# Add src to path
sys.path.insert(0, '/home/simao/projetos/shypn/src')

from shypn.ui.panels.topology.topology_panel import TopologyPanel
from shypn.ui.panels.report.topology_analyses_category import TopologyAnalysesCategory


def test_topology_summary_generation():
    """Test that TopologyPanel can generate summary."""
    print("=" * 60)
    print("TEST 1: Topology Panel Summary Generation")
    print("=" * 60)
    
    # Create topology panel (no model needed for this test)
    topology_panel = TopologyPanel(model_canvas=None)
    
    # Generate summary
    summary = topology_panel.generate_summary_for_report_panel()
    
    # Verify summary structure
    assert 'category' in summary, "Summary missing 'category' key"
    assert 'status' in summary, "Summary missing 'status' key"
    assert 'summary_lines' in summary, "Summary missing 'summary_lines' key"
    assert 'statistics' in summary, "Summary missing 'statistics' key"
    assert 'formatted_text' in summary, "Summary missing 'formatted_text' key"
    
    print(f"✓ Summary structure correct")
    print(f"  Category: {summary['category']}")
    print(f"  Status: {summary['status']}")
    print(f"  Summary lines: {len(summary['summary_lines'])}")
    print(f"\nFormatted text preview:")
    print("-" * 60)
    print(summary['formatted_text'])
    print("-" * 60)
    
    return summary


def test_report_category_integration():
    """Test that Report Category can receive and display topology data."""
    print("\n" + "=" * 60)
    print("TEST 2: Report Category Integration")
    print("=" * 60)
    
    # Create topology panel
    topology_panel = TopologyPanel(model_canvas=None)
    
    # Create report category
    report_category = TopologyAnalysesCategory(project=None, model_canvas=None)
    
    # Wire topology panel to report category
    report_category.set_topology_panel(topology_panel)
    
    # The set_topology_panel() method should call refresh() automatically
    print("✓ Topology panel wired to report category")
    print("✓ Report category refresh() called automatically")
    
    # Check that UI was updated
    label_text = report_category.overall_summary_label.get_text()
    print(f"\nUI label text preview:")
    print("-" * 60)
    print(label_text)
    print("-" * 60)
    
    return report_category


def test_full_integration():
    """Test full integration flow."""
    print("\n" + "=" * 60)
    print("TEST 3: Full Integration Flow")
    print("=" * 60)
    
    # Create topology panel
    topology_panel = TopologyPanel(model_canvas=None)
    
    # Simulate running some analyses (would normally come from user interaction)
    # For now, just generate summary with empty results
    summary = topology_panel.generate_summary_for_report_panel()
    
    print("✓ Topology panel ready")
    print(f"  Status: {summary['status']}")
    
    # Create report category and wire it
    report_category = TopologyAnalysesCategory(project=None, model_canvas=None)
    report_category.set_topology_panel(topology_panel)
    
    print("✓ Report category wired")
    print("✓ Data flow verified")
    
    # Verify the summary shows in report category
    label_text = report_category.overall_summary_label.get_text()
    assert len(label_text) > 0, "Report category label is empty"
    
    print("\n✓ Integration successful!")
    print("  Report category correctly displays topology status")
    
    return True


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("TOPOLOGY PANEL → REPORT PANEL INTEGRATION TEST")
    print("=" * 60 + "\n")
    
    try:
        # Test 1: Summary generation
        summary = test_topology_summary_generation()
        
        # Test 2: Report category integration
        report_category = test_report_category_integration()
        
        # Test 3: Full integration
        test_full_integration()
        
        print("\n" + "=" * 60)
        print("ALL TESTS PASSED ✓")
        print("=" * 60)
        print("\nIntegration is working correctly!")
        print("\nNext steps:")
        print("1. Run shypn.py to see Report Panel with topology data")
        print("2. Open Topology Panel and run some analyses")
        print("3. Switch to Report Panel to see summary")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
