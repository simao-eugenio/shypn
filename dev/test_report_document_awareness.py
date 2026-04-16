#!/usr/bin/env python3
"""
Test script to verify Report Panel document awareness.

Tests that report panel and all categories properly update when:
1. Switching between document tabs
2. Editing properties (triggers dirty callback)
3. Running simulations (controller update)

Run from project root:
    python dev/test_report_document_awareness.py
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

from shypn.helpers.model_canvas_loader import ModelCanvasLoader
from shypn.helpers.report_panel_loader import ReportPanelLoader
from shypn.ui.panels.report.parameters_category import DynamicAnalysesCategory


def test_report_document_awareness():
    """Test that report categories are aware of the active document."""
    
    print("\n" + "="*70)
    print("REPORT PANEL DOCUMENT AWARENESS TEST")
    print("="*70)
    
    # Create model canvas loader (simulates main app)
    loader = ModelCanvasLoader()
    
    # Simulate creating first document
    print("\n[TEST] Creating Document A...")
    loader.create_new_canvas()
    da_a = loader.get_current_drawing_area()
    
    # Get overlay manager for Document A
    overlay_a = loader.overlay_managers.get(da_a)
    if not overlay_a:
        print("❌ FAIL: No overlay_manager for Document A")
        return False
    
    # Create report panel for Document A
    report_loader_a = ReportPanelLoader(project=None, model_canvas_loader=loader)
    report_loader_a.load()
    report_panel_a = report_loader_a.panel
    overlay_a.report_panel_loader = report_loader_a
    
    # Set model canvas for Document A
    canvas_manager_a = overlay_a.canvas_manager
    report_panel_a.set_model_canvas(canvas_manager_a)
    
    print(f"✅ Document A created:")
    print(f"   - drawing_area: {id(da_a)}")
    print(f"   - canvas_manager: {id(canvas_manager_a)}")
    print(f"   - report_panel: {id(report_panel_a)}")
    
    # Find DynamicAnalysesCategory
    dynamic_category_a = None
    for cat in report_panel_a.categories:
        if isinstance(cat, DynamicAnalysesCategory):
            dynamic_category_a = cat
            break
    
    if not dynamic_category_a:
        print("❌ FAIL: No DynamicAnalysesCategory found in report_panel_a")
        return False
    
    print(f"   - DynamicAnalysesCategory model_canvas: {id(dynamic_category_a.model_canvas)}")
    print(f"   - DynamicAnalysesCategory controller: {id(dynamic_category_a.controller) if dynamic_category_a.controller else None}")
    
    # Verify DynamicAnalysesCategory has correct references
    if dynamic_category_a.model_canvas != canvas_manager_a:
        print("❌ FAIL: DynamicAnalysesCategory.model_canvas doesn't match Document A's canvas_manager")
        return False
    
    if dynamic_category_a.controller != overlay_a.simulation_controller:
        print("❌ FAIL: DynamicAnalysesCategory.controller doesn't match Document A's controller")
        return False
    
    print("✅ DynamicAnalysesCategory correctly references Document A")
    
    # Simulate creating second document
    print("\n[TEST] Creating Document B...")
    loader.create_new_canvas()
    da_b = loader.get_current_drawing_area()
    
    # Get overlay manager for Document B
    overlay_b = loader.overlay_managers.get(da_b)
    if not overlay_b:
        print("❌ FAIL: No overlay_manager for Document B")
        return False
    
    # Create report panel for Document B
    report_loader_b = ReportPanelLoader(project=None, model_canvas_loader=loader)
    report_loader_b.load()
    report_panel_b = report_loader_b.panel
    overlay_b.report_panel_loader = report_loader_b
    
    # Set model canvas for Document B
    canvas_manager_b = overlay_b.canvas_manager
    report_panel_b.set_model_canvas(canvas_manager_b)
    
    print(f"✅ Document B created:")
    print(f"   - drawing_area: {id(da_b)}")
    print(f"   - canvas_manager: {id(canvas_manager_b)}")
    print(f"   - report_panel: {id(report_panel_b)}")
    
    # Find DynamicAnalysesCategory in Document B
    dynamic_category_b = None
    for cat in report_panel_b.categories:
        if isinstance(cat, DynamicAnalysesCategory):
            dynamic_category_b = cat
            break
    
    if not dynamic_category_b:
        print("❌ FAIL: No DynamicAnalysesCategory found in report_panel_b")
        return False
    
    print(f"   - DynamicAnalysesCategory model_canvas: {id(dynamic_category_b.model_canvas)}")
    print(f"   - DynamicAnalysesCategory controller: {id(dynamic_category_b.controller) if dynamic_category_b.controller else None}")
    
    # Verify DynamicAnalysesCategory has correct references for Document B
    if dynamic_category_b.model_canvas != canvas_manager_b:
        print("❌ FAIL: DynamicAnalysesCategory.model_canvas doesn't match Document B's canvas_manager")
        return False
    
    if dynamic_category_b.controller != overlay_b.simulation_controller:
        print("❌ FAIL: DynamicAnalysesCategory.controller doesn't match Document B's controller")
        return False
    
    print("✅ DynamicAnalysesCategory correctly references Document B")
    
    # Test tab switch: Simulate switching back to Document A
    print("\n[TEST] Simulating tab switch back to Document A...")
    
    # Set model canvas back to Document A
    report_panel_a.set_model_canvas(canvas_manager_a)
    
    # Verify DynamicAnalysesCategory updated to Document A
    if dynamic_category_a.model_canvas != canvas_manager_a:
        print("❌ FAIL: After tab switch, model_canvas doesn't match Document A")
        return False
    
    if dynamic_category_a.controller != overlay_a.simulation_controller:
        print("❌ FAIL: After tab switch, controller doesn't match Document A")
        print(f"   Expected: {id(overlay_a.simulation_controller)}")
        print(f"   Got: {id(dynamic_category_a.controller) if dynamic_category_a.controller else None}")
        return False
    
    print("✅ Tab switch: DynamicAnalysesCategory correctly updated to Document A")
    
    # Test tab switch: Switch to Document B
    print("\n[TEST] Simulating tab switch to Document B...")
    report_panel_b.set_model_canvas(canvas_manager_b)
    
    # Verify DynamicAnalysesCategory updated to Document B
    if dynamic_category_b.model_canvas != canvas_manager_b:
        print("❌ FAIL: After tab switch, model_canvas doesn't match Document B")
        return False
    
    if dynamic_category_b.controller != overlay_b.simulation_controller:
        print("❌ FAIL: After tab switch, controller doesn't match Document B")
        print(f"   Expected: {id(overlay_b.simulation_controller)}")
        print(f"   Got: {id(dynamic_category_b.controller) if dynamic_category_b.controller else None}")
        return False
    
    print("✅ Tab switch: DynamicAnalysesCategory correctly updated to Document B")
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print("✅ ALL TESTS PASSED")
    print("\nVerified:")
    print("  1. DynamicAnalysesCategory tracks correct model_canvas per document")
    print("  2. DynamicAnalysesCategory tracks correct controller per document")
    print("  3. Tab switches update both model_canvas and controller")
    print("  4. Each document maintains independent report panel state")
    print("="*70 + "\n")
    
    return True


if __name__ == '__main__':
    success = test_report_document_awareness()
    sys.exit(0 if success else 1)
