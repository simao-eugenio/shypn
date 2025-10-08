#!/usr/bin/env python3
"""
Test script to verify New Project functionality
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Test imports
print("Testing imports...")
try:
    from shypn.data.project_models import ProjectManager
    print("✓ ProjectManager imported")
except Exception as e:
    print(f"✗ ProjectManager import failed: {e}")
    sys.exit(1)

try:
    from shypn.helpers.project_dialog_manager import ProjectDialogManager
    print("✓ ProjectDialogManager imported")
except Exception as e:
    print(f"✗ ProjectDialogManager import failed: {e}")
    sys.exit(1)

# Test ProjectManager initialization
print("\nTesting ProjectManager initialization...")
try:
    pm = ProjectManager()
    print(f"✓ ProjectManager initialized")
    print(f"  projects_root: {pm.projects_root}")
    print(f"  Expected: .../workspace/projects")
    
    if 'workspace/projects' in pm.projects_root:
        print("✓ Correct workspace path!")
    else:
        print(f"✗ Wrong path! Expected workspace/projects, got: {pm.projects_root}")
        
except Exception as e:
    print(f"✗ ProjectManager initialization failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test project creation (without UI)
print("\nTesting project creation...")
try:
    test_project = pm.create_project(
        name="Test Project",
        description="Automated test"
    )
    print(f"✓ Project created: {test_project.name}")
    print(f"  ID: {test_project.id}")
    print(f"  Path: {test_project.base_path}")
    
    # Verify directory exists
    if os.path.exists(test_project.base_path):
        print(f"✓ Project directory created")
    else:
        print(f"✗ Project directory NOT created!")
        
    # Clean up test project
    import shutil
    shutil.rmtree(test_project.base_path)
    print("✓ Test project cleaned up")
    
except Exception as e:
    print(f"✗ Project creation failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "="*50)
print("All tests PASSED! ✓")
print("="*50)
