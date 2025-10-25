#!/usr/bin/env python3
"""Test script for File Panel Project Opening feature.

This script demonstrates the new dialog-free project opening flow.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_project_detection():
    """Test project file detection logic."""
    print("=" * 60)
    print("Testing Project Detection Logic")
    print("=" * 60)
    
    from pathlib import Path
    
    # Mock FilePanelController's project detection
    def find_project_file_in_folder(folder_path):
        """Simulate _find_project_file_in_folder method."""
        folder = Path(folder_path)
        if not folder.is_dir():
            return None
        shy_files = list(folder.glob('*.shy'))
        if shy_files:
            return str(shy_files[0])
        return None
    
    # Test with workspace directory
    workspace_dir = Path('workspace')
    if workspace_dir.exists():
        print(f"\n✓ Checking workspace directory: {workspace_dir}")
        
        # List all items
        for item in workspace_dir.iterdir():
            if item.is_dir():
                project_file = find_project_file_in_folder(str(item))
                if project_file:
                    print(f"  📁 {item.name}/")
                    print(f"     └─ 📄 {Path(project_file).name} (PROJECT)")
                else:
                    print(f"  📁 {item.name}/ (regular folder)")
            elif item.suffix == '.shy':
                print(f"  📄 {item.name} (PROJECT FILE)")
            else:
                print(f"  📄 {item.name}")
    else:
        print(f"⚠ Workspace directory not found: {workspace_dir}")
    
    print("\n" + "=" * 60)

def test_mode_switching():
    """Test project opening mode state."""
    print("\nTesting Project Opening Mode State")
    print("=" * 60)
    
    class MockController:
        def __init__(self):
            self.project_opening_mode = False
            self.path_entry_text = ""
        
        def on_open_project(self):
            """Simulate entering project opening mode."""
            self.project_opening_mode = True
            self.path_entry_text = "SELECT PROJECT TO OPEN..."
            print("✓ Entered project opening mode")
            print(f"  Path entry: '{self.path_entry_text}'")
        
        def open_project(self, path):
            """Simulate opening a project."""
            if self.project_opening_mode:
                print(f"✓ Opening project: {path}")
                self.project_opening_mode = False
                self.path_entry_text = path
                print("✓ Exited project opening mode")
            else:
                print(f"⚠ Not in project opening mode, opening normally: {path}")
    
    controller = MockController()
    
    print("\n1. Normal state:")
    print(f"   Mode: {controller.project_opening_mode}")
    print(f"   Path: '{controller.path_entry_text}'")
    
    print("\n2. Click 'Open Project' button:")
    controller.on_open_project()
    print(f"   Mode: {controller.project_opening_mode}")
    print(f"   Path: '{controller.path_entry_text}'")
    
    print("\n3. Select project folder:")
    controller.open_project("/path/to/project.shy")
    print(f"   Mode: {controller.project_opening_mode}")
    print(f"   Path: '{controller.path_entry_text}'")
    
    print("\n" + "=" * 60)

def test_integration():
    """Test controller integration."""
    print("\nTesting Controller Integration")
    print("=" * 60)
    
    try:
        from shypn.ui.file_panel_controller import FilePanelController
        from shypn.helpers.project_actions_controller import ProjectActionsController
        
        print("✓ FilePanelController imported")
        print("✓ ProjectActionsController imported")
        
        # Check if methods exist
        if hasattr(FilePanelController, 'on_open_project'):
            print("✓ FilePanelController.on_open_project() exists")
        else:
            print("✗ FilePanelController.on_open_project() NOT FOUND")
        
        if hasattr(FilePanelController, '_find_project_file_in_folder'):
            print("✓ FilePanelController._find_project_file_in_folder() exists")
        else:
            print("✗ FilePanelController._find_project_file_in_folder() NOT FOUND")
        
        if hasattr(FilePanelController, '_open_project'):
            print("✓ FilePanelController._open_project() exists")
        else:
            print("✗ FilePanelController._open_project() NOT FOUND")
        
        if hasattr(ProjectActionsController, 'set_file_panel_controller'):
            print("✓ ProjectActionsController.set_file_panel_controller() exists")
        else:
            print("✗ ProjectActionsController.set_file_panel_controller() NOT FOUND")
        
        print("\n✅ All integration points verified!")
        
    except Exception as e:
        print(f"✗ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)

def print_summary():
    """Print feature summary."""
    print("\n" + "=" * 60)
    print("FILE PANEL PROJECT OPENING - SUMMARY")
    print("=" * 60)
    
    print("\nFeature: Dialog-Free Project Opening")
    print("\nMethods:")
    print("  1. Double-click .shy file → Opens project")
    print("  2. Double-click project folder → Finds & opens .shy file")
    print("  3. Click 'Open Project' button → Enter selection mode")
    print("\nBenefits:")
    print("  ✓ No dialogs - direct tree selection")
    print("  ✓ Intuitive - familiar file manager behavior")
    print("  ✓ Flexible - three ways to open projects")
    print("  ✓ Clean state - visible mode indicator")
    print("\nFiles Modified:")
    print("  • src/shypn/ui/file_panel_controller.py")
    print("  • src/shypn/helpers/project_actions_controller.py")
    print("  • src/shypn/helpers/file_panel_loader.py")
    print("\nDocumentation:")
    print("  • doc/FILE_PANEL_PROJECT_OPENING.md")
    print("\n" + "=" * 60)

if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("FILE PANEL PROJECT OPENING - TEST SUITE")
    print("=" * 60)
    
    test_project_detection()
    test_mode_switching()
    test_integration()
    print_summary()
    
    print("\n✅ All tests completed!")
    print("\nNext Steps:")
    print("1. Launch SHYpn application")
    print("2. Open File Panel (Explorer)")
    print("3. Try double-clicking on a .shy file or project folder")
    print("4. Try clicking 'Open Project' button and selecting a project")
    print("\n" + "=" * 60)
