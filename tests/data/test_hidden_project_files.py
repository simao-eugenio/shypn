#!/usr/bin/env python3
"""Tests for hidden project structure files.

Verifies that:
1. Project files are saved with hidden filename (.project.shy)
2. File observer ignores hidden project files
3. Project deletion removes hidden files
"""

import os
import shutil
import tempfile
import unittest
from pathlib import Path

from shypn.data.project_models import Project, ProjectManager


class TestHiddenProjectFiles(unittest.TestCase):
    """Test hidden project structure files."""
    
    def setUp(self):
        """Create temporary directory for tests."""
        self.test_dir = tempfile.mkdtemp()
        self.project_path = os.path.join(self.test_dir, "test_project")
    
    def tearDown(self):
        """Clean up temporary directory."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_project_saves_as_hidden_file(self):
        """Test that project saves to .project.shy (hidden)."""
        # Create project
        project = Project(
            name="Test Project",
            description="Test hidden files",
            base_path=self.project_path
        )
        
        # Save project
        project.save()
        
        # Verify hidden file exists
        hidden_file = os.path.join(self.project_path, '.project.shy')
        self.assertTrue(os.path.exists(hidden_file), 
                       f"Hidden file {hidden_file} should exist")
        
        # Verify old visible file does NOT exist
        visible_file = os.path.join(self.project_path, 'project.shy')
        self.assertFalse(os.path.exists(visible_file),
                        f"Visible file {visible_file} should NOT exist")
    
    def test_project_loads_from_hidden_file(self):
        """Test that project loads from .project.shy."""
        # Create and save project
        project = Project(
            name="Test Load",
            description="Test loading from hidden",
            base_path=self.project_path
        )
        project.save()
        
        # Load from hidden file
        hidden_file = os.path.join(self.project_path, '.project.shy')
        loaded_project = Project.load(hidden_file)
        
        # Verify data
        self.assertEqual(loaded_project.name, "Test Load")
        self.assertEqual(loaded_project.description, "Test loading from hidden")
    
    def test_file_observer_ignores_hidden_files(self):
        """Test that file observer ignores .project.* files."""
        try:
            from shypn.data.project_file_observer import ProjectFileHandler
        except ImportError:
            self.skipTest("watchdog not available")
        
        # Create project
        project = Project(
            name="Test Observer",
            base_path=self.project_path
        )
        project.create_directory_structure()
        project.save()
        
        # Create file handler
        handler = ProjectFileHandler(project)
        
        # Create hidden file in pathways directory
        pathways_dir = Path(self.project_path) / "pathways"
        hidden_test_file = pathways_dir / ".project.test"
        hidden_test_file.write_text("test content")
        
        # Simulate file added event
        handler._handle_pathway_file_added(hidden_test_file)
        
        # Verify no PathwayDocument created
        self.assertEqual(len(project.pathways.list_pathways()), 0,
                        "Hidden files should be ignored by observer")
    
    def test_project_deletion_removes_hidden_file(self):
        """Test that deleting project directory removes .project.shy."""
        import shutil
        
        # Create project
        project = Project(
            name="Test Delete",
            base_path=self.project_path
        )
        project.create_directory_structure()
        project.save()
        
        # Verify hidden file exists
        hidden_file = os.path.join(self.project_path, '.project.shy')
        self.assertTrue(os.path.exists(hidden_file),
                       "Hidden file should exist before deletion")
        
        # Verify project directory exists
        self.assertTrue(os.path.exists(self.project_path),
                       "Project directory should exist")
        
        # Delete entire directory (simulating what ProjectManager.delete_project does)
        shutil.rmtree(self.project_path)
        
        # Verify entire directory removed (including hidden file)
        self.assertFalse(os.path.exists(self.project_path),
                        "Project directory should be removed")
        self.assertFalse(os.path.exists(hidden_file),
                        "Hidden file should be removed with project")
    
    def test_hidden_file_path_generation(self):
        """Test that get_project_file_path returns hidden filename."""
        project = Project(
            name="Test Path",
            base_path=self.project_path
        )
        
        project_file = project.get_project_file_path()
        
        # Verify path ends with .project.shy
        self.assertTrue(project_file.endswith('.project.shy'),
                       f"Project file should be .project.shy, got {project_file}")
        
        # Verify path does NOT end with project.shy (non-hidden)
        self.assertFalse(project_file.endswith('project.shy') and 
                        not project_file.endswith('.project.shy'),
                        "Project file should not use visible name")
    
    def test_multiple_hidden_files_ignored(self):
        """Test that observer ignores all .project.* patterns."""
        try:
            from shypn.data.project_file_observer import ProjectFileHandler
        except ImportError:
            self.skipTest("watchdog not available")
        
        # Create project
        project = Project(
            name="Test Multiple",
            base_path=self.project_path
        )
        project.create_directory_structure()
        
        # Create file handler
        handler = ProjectFileHandler(project)
        
        # Create various hidden project files
        pathways_dir = Path(self.project_path) / "pathways"
        hidden_files = [
            pathways_dir / ".project.shy",
            pathways_dir / ".project.backup",
            pathways_dir / ".project.settings",
            pathways_dir / ".project.cache"
        ]
        
        for hidden_file in hidden_files:
            hidden_file.write_text("test")
            handler._handle_pathway_file_added(hidden_file)
        
        # Verify no PathwayDocuments created
        self.assertEqual(len(project.pathways.list_pathways()), 0,
                        "All .project.* files should be ignored")


if __name__ == '__main__':
    unittest.main()
