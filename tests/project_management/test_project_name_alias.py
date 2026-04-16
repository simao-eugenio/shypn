#!/usr/bin/env python3
"""Test script for project name alias system.

This script verifies that:
1. Projects display names (not UUIDs)
2. Lookup by name works correctly
3. Directory names use sanitized project names
4. All new methods function as expected
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add src to path
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir / 'src'))

from shypn.data.project_models import ProjectManager


def test_project_name_display():
    """Test that projects display names instead of UUIDs."""
    print("=" * 70)
    print("TEST: Project Name Display System")
    print("=" * 70)
    
    # Create temporary workspace
    temp_dir = tempfile.mkdtemp(prefix="test_project_names_")
    print(f"\n✓ Created temporary workspace: {temp_dir}")
    
    try:
        # Initialize project manager and override workspace
        manager = ProjectManager()
        manager.projects_root = temp_dir
        # Create necessary directories
        os.makedirs(temp_dir, exist_ok=True)
        # Reset project index for clean test
        manager.project_index = {}
        manager.recent_projects = []
        print(f"✓ Initialized ProjectManager")
        
        # Test 1: Create project with name
        print("\n" + "-" * 70)
        print("Test 1: Create project and verify display")
        print("-" * 70)
        
        project = manager.create_project(
            name="Neural Network Analysis",
            description="Test project for name display"
        )
        
        print(f"Created project:")
        print(f"  UUID: {project.id}")
        print(f"  Name: {project.name}")
        print(f"  str(project): {str(project)}")
        print(f"  repr(project): {repr(project)}")
        print(f"  Directory: {project.base_path}")
        
        assert str(project) == "Neural Network Analysis", "str() should return name"
        # Check that sanitized name is in path (spaces become underscores)
        sanitized_name = project.name.replace(" ", "_")
        assert sanitized_name in project.base_path, f"Directory should use sanitized name (expected '{sanitized_name}' in '{project.base_path}')"
        assert project.id not in str(project), "str() should not show UUID"
        print("✓ PASSED: Project displays name, not UUID")
        
        # Test 2: Lookup by name
        print("\n" + "-" * 70)
        print("Test 2: Lookup project by name")
        print("-" * 70)
        
        found = manager.get_project_by_name("Neural Network Analysis")
        assert found is not None, "Should find project by name"
        assert found.id == project.id, "Should return correct project"
        print(f"✓ Found project by exact name: {found.name}")
        
        # Test case-insensitive
        found_lower = manager.get_project_by_name("neural network analysis")
        assert found_lower is not None, "Should be case-insensitive"
        assert found_lower.id == project.id, "Should return same project"
        print(f"✓ Case-insensitive lookup works")
        
        # Test not found
        not_found = manager.get_project_by_name("NonExistent Project")
        assert not_found is None, "Should return None for missing project"
        print(f"✓ Returns None for non-existent project")
        
        print("✓ PASSED: Lookup by name works correctly")
        
        # Test 3: Create another project for search
        print("\n" + "-" * 70)
        print("Test 3: Partial name search")
        print("-" * 70)
        
        project2 = manager.create_project(
            name="Bio Simulation Model",
            description="Second test project"
        )
        print(f"Created second project: {project2.name}")
        
        # Search for "Network"
        matches = manager.find_projects_by_name("Network")
        print(f"\nSearch for 'Network': found {len(matches)} match(es)")
        for info in matches:
            print(f"  - {info['name']}")
        assert len(matches) == 1, "Should find one match"
        assert matches[0]['name'] == "Neural Network Analysis"
        
        # Search for "Simulation" (should find second project)
        matches = manager.find_projects_by_name("Simulation")
        print(f"\nSearch for 'Simulation': found {len(matches)} match(es)")
        for info in matches:
            print(f"  - {info['name']}")
        assert len(matches) == 1, "Should find one match"
        assert matches[0]['name'] == "Bio Simulation Model"
        
        # Search for common term (should find both if any match)
        matches = manager.find_projects_by_name("Model")
        print(f"\nSearch for 'Model': found {len(matches)} match(es)")
        for info in matches:
            print(f"  - {info['name']}")
        
        print("✓ PASSED: Partial name search works")
        
        # Test 4: Get display name from UUID
        print("\n" + "-" * 70)
        print("Test 4: Get display name from UUID")
        print("-" * 70)
        
        display_name = manager.get_project_display_name(project.id)
        print(f"UUID: {project.id}")
        print(f"Display name: {display_name}")
        assert display_name == "Neural Network Analysis"
        
        # Test with unknown UUID
        unknown_uuid = "00000000-0000-0000-0000-000000000000"
        fallback_name = manager.get_project_display_name(unknown_uuid)
        print(f"\nUnknown UUID: {unknown_uuid}")
        print(f"Fallback display: {fallback_name}")
        assert fallback_name.startswith("Project"), "Should provide fallback"
        
        print("✓ PASSED: Display name from UUID works")
        
        # Test 5: List all projects (sorted by name)
        print("\n" + "-" * 70)
        print("Test 5: List all projects sorted by name")
        print("-" * 70)
        
        all_projects = manager.list_all_projects()
        print(f"Total projects: {len(all_projects)}")
        print("\nProjects (sorted by name):")
        for i, info in enumerate(all_projects, 1):
            print(f"  {i}. {info['name']}")
            print(f"     Path: {info['path']}")
            print(f"     UUID: {info['id'][:8]}...")
        
        assert len(all_projects) == 2, "Should have 2 projects"
        names = [p['name'] for p in all_projects]
        assert names == sorted(names, key=str.lower), "Should be sorted by name"
        
        print("✓ PASSED: List all projects sorted correctly")
        
        # Test 6: Recent projects info
        print("\n" + "-" * 70)
        print("Test 6: Recent projects info (with names)")
        print("-" * 70)
        
        recent = manager.get_recent_projects_info()
        print(f"Recent projects: {len(recent)}")
        for i, info in enumerate(recent, 1):
            print(f"  {i}. {info['name']} (modified: {info['modified_date'][:10]})")
        
        assert len(recent) > 0, "Should have recent projects"
        assert all('name' in info for info in recent), "All should have names"
        
        print("✓ PASSED: Recent projects include display names")
        
        # Test 7: Directory naming
        print("\n" + "-" * 70)
        print("Test 7: Directory uses sanitized project name")
        print("-" * 70)
        
        # Create project with special characters
        project3 = manager.create_project(
            name="Test Project (v2.0)!",
            description="Project with special chars"
        )
        
        print(f"Project name: {project3.name}")
        print(f"Directory: {project3.base_path}")
        
        # Check directory exists and uses sanitized name
        assert os.path.exists(project3.base_path), "Directory should exist"
        dir_name = os.path.basename(project3.base_path)
        print(f"Directory name: {dir_name}")
        
        # Directory should not contain special chars
        assert "(" not in dir_name, "Directory should not have parentheses"
        assert "!" not in dir_name, "Directory should not have exclamation"
        assert "." not in dir_name or dir_name.endswith("."), "Directory should handle dots"
        
        print("✓ PASSED: Directory uses sanitized name")
        
        # Summary
        print("\n" + "=" * 70)
        print("ALL TESTS PASSED!")
        print("=" * 70)
        print("\nSummary:")
        print("✓ Projects display names (not UUIDs)")
        print("✓ Lookup by name (exact and case-insensitive)")
        print("✓ Partial name search")
        print("✓ Display name from UUID")
        print("✓ List all projects sorted by name")
        print("✓ Recent projects include names")
        print("✓ Directories use sanitized names")
        print("\n✓ Name alias system working correctly!")
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        return False
        
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Cleanup
        try:
            shutil.rmtree(temp_dir)
            print(f"\n✓ Cleaned up temporary workspace")
        except Exception as e:
            print(f"\n⚠ Warning: Could not clean up {temp_dir}: {e}")
    
    return True


if __name__ == "__main__":
    success = test_project_name_display()
    sys.exit(0 if success else 1)
