#!/usr/bin/env python3
"""Implementation script for per-document panel normalization.

This script guides the implementation of per-document panel instances,
following the OOP architecture defined in base_panel_loader.py.

Usage:
    python scripts/implement_per_document_panels.py

Phases:
    1. PathwayPanelLoader - Most complex (8 categories)
    2. AnalysesPanelLoader - Medium complexity (3 categories + plots)
    3. TopologyPanelLoader - Medium complexity (4 categories + cache)
    
Author: SHYPN Development Team
Date: 2026-01-06
"""
import os
import sys

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_header(text):
    """Print section header."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(70)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}\n")


def print_step(step_num, text):
    """Print implementation step."""
    print(f"{Colors.OKBLUE}{Colors.BOLD}Step {step_num}:{Colors.ENDC} {text}")


def print_success(text):
    """Print success message."""
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")


def print_warning(text):
    """Print warning message."""
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")


def print_error(text):
    """Print error message."""
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")


def print_info(text):
    """Print info message."""
    print(f"{Colors.OKCYAN}ℹ {text}{Colors.ENDC}")


def check_file_exists(filepath):
    """Check if file exists."""
    return os.path.exists(filepath)


def main():
    """Main implementation guide."""
    print_header("Per-Document Panel Normalization Implementation")
    
    print_info("This script will guide you through implementing per-document panel instances.")
    print_info("Follow the steps for each panel type.\n")
    
    # Check base class exists
    base_class_path = "src/shypn/helpers/base_panel_loader.py"
    if check_file_exists(base_class_path):
        print_success(f"Base class exists: {base_class_path}")
    else:
        print_error(f"Base class missing: {base_class_path}")
        print_error("Run: Create base_panel_loader.py first")
        return 1
    
    # Check architecture doc exists
    arch_doc_path = "doc/PER_DOCUMENT_PANEL_ARCHITECTURE.md"
    if check_file_exists(arch_doc_path):
        print_success(f"Architecture doc exists: {arch_doc_path}")
    else:
        print_warning(f"Architecture doc missing: {arch_doc_path}")
    
    # Check tests exist
    tests_path = "tests/test_per_document_panels.py"
    if check_file_exists(tests_path):
        print_success(f"Tests exist: {tests_path}")
    else:
        print_error(f"Tests missing: {tests_path}")
        return 1
    
    print()
    
    # ==========================================================================
    # Phase 1: PathwayPanelLoader
    # ==========================================================================
    print_header("Phase 1: PathwayPanelLoader Implementation")
    
    print_step(1, "Create src/shypn/helpers/pathway_panel_loader.py")
    print_info("Implement PathwayPanelLoader(PerDocumentPanelLoader)")
    print_info("  - Inherits from PerDocumentPanelLoader")
    print_info("  - Creates PathwayOperationsPanel instance")
    print_info("  - Passes model, workspace_settings, parent_window")
    print()
    
    pathway_loader_path = "src/shypn/helpers/pathway_panel_loader.py"
    if check_file_exists(pathway_loader_path):
        print_success(f"✓ {pathway_loader_path} exists")
    else:
        print_warning(f"⚠ {pathway_loader_path} not found - needs implementation")
    
    print_step(2, "Update OverlayManager in model_canvas_loader.py")
    print_info("Add: self.pathway_panel_loader = None")
    print()
    
    print_step(3, "Update add_document() in model_canvas_loader.py")
    print_info("Create pathway panel instance:")
    print_info("  overlay_manager.pathway_panel_loader = ")
    print_info("    self.panel_factory.create_pathway_panel(canvas_manager)")
    print()
    
    print_step(4, "Update shypn.py")
    print_info("Replace pathway_panel_loader creation with container:")
    print_info("  pathways_panel_container = Gtk.Box(...)")
    print_info("  model_canvas_loader.pathways_panel_container = ...")
    print()
    
    print_step(5, "Update tab switch handler")
    print_info("Add to _on_notebook_switch_page():")
    print_info("  self._swap_panel_instance('pathways', ...)")
    print()
    
    print_step(6, "Test PathwayPanelLoader")
    print_info("Run: pytest tests/test_per_document_panels.py -v -k pathway")
    print()
    
    # ==========================================================================
    # Phase 2: AnalysesPanelLoader
    # ==========================================================================
    print_header("Phase 2: AnalysesPanelLoader Implementation")
    
    print_step(1, "Create src/shypn/helpers/analyses_panel_loader.py")
    print_info("Implement AnalysesPanelLoader(PerDocumentPanelLoader)")
    print_info("  - Creates DynamicAnalysesPanel instance")
    print_info("  - Handles data_collector parameter")
    print_info("  - Maintains convenience accessors (place_panel, transition_panel)")
    print()
    
    analyses_loader_path = "src/shypn/helpers/analyses_panel_loader.py"
    if check_file_exists(analyses_loader_path):
        print_success(f"✓ {analyses_loader_path} exists")
    else:
        print_warning(f"⚠ {analyses_loader_path} not found - needs implementation")
    
    print_step(2, "Update OverlayManager")
    print_info("Add: self.analyses_panel_loader = None")
    print()
    
    print_step(3, "Update add_document()")
    print_info("Create analyses panel instance:")
    print_info("  overlay_manager.analyses_panel_loader = ")
    print_info("    self.panel_factory.create_analyses_panel(canvas_manager, data_collector)")
    print()
    
    print_step(4, "Remove state clearing logic")
    print_info("Delete from _on_notebook_switch_page():")
    print_info("  - transition_panel.selected_objects.clear()")
    print_info("  - place_panel.selected_objects.clear()")
    print_info("  (No longer needed - each document has its own panel!)")
    print()
    
    print_step(5, "Update shypn.py")
    print_info("Replace right_panel_loader creation with container")
    print()
    
    print_step(6, "Test AnalysesPanelLoader")
    print_info("Run: pytest tests/test_per_document_panels.py -v -k analyses")
    print()
    
    # ==========================================================================
    # Phase 3: TopologyPanelLoader
    # ==========================================================================
    print_header("Phase 3: TopologyPanelLoader Implementation")
    
    print_step(1, "Refactor TopologyPanelLoader")
    print_info("Modify existing topology_panel_loader.py:")
    print_info("  - Inherit from PerDocumentPanelLoader")
    print_info("  - Move controller to per-instance (cache is now per-instance)")
    print_info("  - Remove global on_tab_switched() callback")
    print()
    
    topology_loader_path = "src/shypn/helpers/topology_panel_loader.py"
    if check_file_exists(topology_loader_path):
        print_success(f"✓ {topology_loader_path} exists")
        print_info("  Needs refactoring to inherit from PerDocumentPanelLoader")
    else:
        print_error(f"✗ {topology_loader_path} not found")
    
    print_step(2, "Update TopologyController")
    print_info("Remove drawing_area keys from cache:")
    print_info("  OLD: self.cache[drawing_area] = results")
    print_info("  NEW: self.cache['analysis_type'] = results")
    print_info("  (Each controller instance serves one document)")
    print()
    
    print_step(3, "Update OverlayManager")
    print_info("Add: self.topology_panel_loader = None")
    print()
    
    print_step(4, "Update add_document()")
    print_info("Create topology panel instance:")
    print_info("  overlay_manager.topology_panel_loader = ")
    print_info("    self.panel_factory.create_topology_panel(canvas_manager)")
    print()
    
    print_step(5, "Remove global tab switch callback")
    print_info("Delete from shypn.py:")
    print_info("  - on_canvas_tab_switched() callback")
    print_info("  - notebook.connect('switch-page', ...) for topology")
    print_info("  (No longer needed - each document has its own controller)")
    print()
    
    print_step(6, "Test TopologyPanelLoader")
    print_info("Run: pytest tests/test_per_document_panels.py -v -k topology")
    print()
    
    # ==========================================================================
    # Phase 4: Integration & Testing
    # ==========================================================================
    print_header("Phase 4: Integration & Testing")
    
    print_step(1, "Unify tab switch handler")
    print_info("Create _swap_panel_instance() helper in model_canvas_loader.py")
    print_info("Use for all panels: pathways, analyses, topology, viability, report")
    print()
    
    print_step(2, "Update backward-compatible accessors")
    print_info("Add @property methods to model_canvas_loader:")
    print_info("  @property")
    print_info("  def pathway_panel_loader(self):")
    print_info("    return self.overlay_managers[current_da].pathway_panel_loader")
    print()
    
    print_step(3, "Run all tests")
    print_info("Run: pytest tests/test_per_document_panels.py -v")
    print()
    
    print_step(4, "Integration testing")
    print_info("Manual test:")
    print_info("  1. Create 3 documents")
    print_info("  2. Make changes in each (import pathways, add analyses, run topology)")
    print_info("  3. Switch tabs rapidly")
    print_info("  4. Verify: State preserved in each tab")
    print()
    
    print_step(5, "Memory profiling")
    print_info("Test with 10 documents, verify memory usage acceptable")
    print()
    
    print_step(6, "Update documentation")
    print_info("Update:")
    print_info("  - doc/PER_DOCUMENT_PANEL_ARCHITECTURE.md")
    print_info("  - PANEL_TAB_SWITCHING_AUDIT.md")
    print_info("  - CHANGELOG.md")
    print()
    
    # ==========================================================================
    # Summary
    # ==========================================================================
    print_header("Implementation Summary")
    
    files_to_create = [
        "src/shypn/helpers/pathway_panel_loader.py",
        "src/shypn/helpers/analyses_panel_loader.py"
    ]
    
    files_to_modify = [
        "src/shypn/helpers/topology_panel_loader.py (refactor to inherit from base)",
        "src/shypn/helpers/model_canvas_loader.py (add OverlayManager fields, factory, tab switch)",
        "src/shypn.py (replace panel creation with containers)"
    ]
    
    print(f"{Colors.BOLD}Files to CREATE:{Colors.ENDC}")
    for f in files_to_create:
        if check_file_exists(f):
            print_success(f"  {f}")
        else:
            print_warning(f"  {f}")
    print()
    
    print(f"{Colors.BOLD}Files to MODIFY:{Colors.ENDC}")
    for f in files_to_modify:
        filepath = f.split()[0]  # Extract filepath before description
        if check_file_exists(filepath):
            print_success(f"  {f}")
        else:
            print_error(f"  {f}")
    print()
    
    print_info(f"{Colors.BOLD}Estimated Time:{Colors.ENDC} 3-5 days")
    print_info(f"{Colors.BOLD}Testing:{Colors.ENDC} Run tests after each phase")
    print_info(f"{Colors.BOLD}Documentation:{Colors.ENDC} Update docs in Phase 4")
    print()
    
    print_header("Ready to Begin Implementation!")
    print_info("Start with Phase 1: PathwayPanelLoader")
    print_info("Follow the architecture defined in doc/PER_DOCUMENT_PANEL_ARCHITECTURE.md")
    print()
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
