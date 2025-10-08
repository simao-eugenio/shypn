#!/usr/bin/env python3
"""Project Management Data Models.

This module defines the core data structures for managing shypn projects,
following the PATHWAY_DATA_ISOLATION_PLAN.md specifications.

Classes:
    Project: Represents a single shypn project with models, pathways, and simulations
    ProjectManager: Global singleton for managing all projects and workspace state
    ModelDocument: Represents an individual Petri net model within a project
"""

import os
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path


class ModelDocument:
    """Represents an individual Petri net model within a project.
    
    Attributes:
        id: Unique identifier (UUID)
        name: Display name
        description: Optional description
        file_path: Absolute path to .shy file
        created_date: ISO timestamp
        modified_date: ISO timestamp
        tags: List of user tags
        analysis_cache: Cached analysis results
    """
    
    def __init__(self, id: str = None, name: str = "Untitled Model",
                 description: str = "", file_path: str = None):
        """Initialize a ModelDocument.
        
        Args:
            id: UUID string, generated if None
            name: Model display name
            description: Optional description
            file_path: Path to .shy file
        """
        self.id = id or str(uuid.uuid4())
        self.name = name
        self.description = description
        self.file_path = file_path
        self.created_date = datetime.now().isoformat()
        self.modified_date = self.created_date
        self.tags = []
        self.analysis_cache = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'file_path': self.file_path,
            'created_date': self.created_date,
            'modified_date': self.modified_date,
            'tags': self.tags,
            'analysis_cache': self.analysis_cache
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ModelDocument':
        """Create from dictionary."""
        doc = cls(
            id=data.get('id'),
            name=data.get('name', 'Untitled Model'),
            description=data.get('description', ''),
            file_path=data.get('file_path')
        )
        doc.created_date = data.get('created_date', doc.created_date)
        doc.modified_date = data.get('modified_date', doc.modified_date)
        doc.tags = data.get('tags', [])
        doc.analysis_cache = data.get('analysis_cache', {})
        return doc
    
    def update_modified_date(self):
        """Update the modified date to now."""
        self.modified_date = datetime.now().isoformat()


class Project:
    """Represents a shypn project with models, pathways, and simulations.
    
    Attributes:
        id: Unique identifier (UUID)
        name: Display name
        description: Optional description
        created_date: ISO timestamp
        modified_date: ISO timestamp
        base_path: Absolute path to project directory
        models: Dict mapping model_id -> ModelDocument
        pathways: List of pathway file paths
        simulations: List of simulation result file paths
        tags: User-defined tags
        settings: Project-specific settings
    """
    
    def __init__(self, id: str = None, name: str = "Untitled Project",
                 description: str = "", base_path: str = None):
        """Initialize a Project.
        
        Args:
            id: UUID string, generated if None
            name: Project display name
            description: Optional description
            base_path: Path to project directory (created if needed)
        """
        self.id = id or str(uuid.uuid4())
        self.name = name
        self.description = description
        self.created_date = datetime.now().isoformat()
        self.modified_date = self.created_date
        self.base_path = base_path
        self.models = {}  # model_id -> ModelDocument
        self.pathways = []  # List of pathway .shy file paths
        self.simulations = []  # List of simulation .json file paths
        self.tags = []
        self.settings = {
            'auto_backup': True,
            'backup_frequency': 'daily',
            'keep_backups': 5
        }
    
    def get_project_file_path(self) -> Optional[str]:
        """Get the path to project.shy file."""
        if self.base_path:
            return os.path.join(self.base_path, 'project.shy')
        return None
    
    def get_models_dir(self) -> Optional[str]:
        """Get the models directory path."""
        if self.base_path:
            return os.path.join(self.base_path, 'models')
        return None
    
    def get_pathways_dir(self) -> Optional[str]:
        """Get the pathways directory path."""
        if self.base_path:
            return os.path.join(self.base_path, 'pathways')
        return None
    
    def get_simulations_dir(self) -> Optional[str]:
        """Get the simulations directory path."""
        if self.base_path:
            return os.path.join(self.base_path, 'simulations')
        return None
    
    def add_model(self, model: ModelDocument):
        """Add a model to the project."""
        self.models[model.id] = model
        self.update_modified_date()
    
    def remove_model(self, model_id: str) -> bool:
        """Remove a model from the project.
        
        Returns:
            True if model was removed, False if not found
        """
        if model_id in self.models:
            del self.models[model_id]
            self.update_modified_date()
            return True
        return False
    
    def get_model(self, model_id: str) -> Optional[ModelDocument]:
        """Get a model by ID."""
        return self.models.get(model_id)
    
    def update_modified_date(self):
        """Update the modified date to now."""
        self.modified_date = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'document_type': 'project',
            'version': '1.0',
            'identity': {
                'id': self.id,
                'name': self.name,
                'description': self.description,
                'created_date': self.created_date,
                'modified_date': self.modified_date
            },
            'location': {
                'base_path': self.base_path
            },
            'content': {
                'models': [model.to_dict() for model in self.models.values()],
                'pathways': self.pathways,
                'simulations': self.simulations
            },
            'metadata': {
                'tags': self.tags,
                'settings': self.settings
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Project':
        """Create from dictionary."""
        identity = data.get('identity', {})
        location = data.get('location', {})
        content = data.get('content', {})
        metadata = data.get('metadata', {})
        
        project = cls(
            id=identity.get('id'),
            name=identity.get('name', 'Untitled Project'),
            description=identity.get('description', ''),
            base_path=location.get('base_path')
        )
        
        project.created_date = identity.get('created_date', project.created_date)
        project.modified_date = identity.get('modified_date', project.modified_date)
        
        # Load models
        for model_data in content.get('models', []):
            model = ModelDocument.from_dict(model_data)
            project.models[model.id] = model
        
        project.pathways = content.get('pathways', [])
        project.simulations = content.get('simulations', [])
        project.tags = metadata.get('tags', [])
        project.settings = metadata.get('settings', project.settings)
        
        return project
    
    def save(self):
        """Save project to project.shy file."""
        project_file = self.get_project_file_path()
        if not project_file:
            raise ValueError("Project base_path not set, cannot save")
        
        # Create directories if needed
        os.makedirs(os.path.dirname(project_file), exist_ok=True)
        
        # Write JSON
        with open(project_file, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
    
    @classmethod
    def load(cls, project_file: str) -> 'Project':
        """Load project from project.shy file.
        
        Args:
            project_file: Path to project.shy file
            
        Returns:
            Loaded Project instance
        """
        with open(project_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.from_dict(data)
    
    def create_directory_structure(self):
        """Create the project directory structure."""
        if not self.base_path:
            raise ValueError("Project base_path not set")
        
        # Create main directories
        os.makedirs(self.get_models_dir(), exist_ok=True)
        os.makedirs(self.get_pathways_dir(), exist_ok=True)
        os.makedirs(self.get_simulations_dir(), exist_ok=True)
        os.makedirs(os.path.join(self.base_path, 'exports'), exist_ok=True)
        os.makedirs(os.path.join(self.base_path, 'metadata', 'backups'), exist_ok=True)


class ProjectManager:
    """Global singleton for managing all projects and workspace state.
    
    Manages the project index, recent projects, and current active project.
    """
    
    _instance = None
    
    def __new__(cls):
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the ProjectManager."""
        if self._initialized:
            return
        
        self._initialized = True
        self.projects_root = None  # Will be set to data/projects/
        self.current_project = None  # Currently active Project
        self.project_index = {}  # project_id -> project_info dict
        self.recent_projects = []  # List of project_ids, most recent first
        self.max_recent = 10
        
        # Initialize default paths
        self._setup_default_paths()
    
    def _setup_default_paths(self):
        """Setup default project paths."""
        # Try to find repository root
        try:
            # This file is in src/shypn/data/
            current_dir = os.path.dirname(os.path.abspath(__file__))
            repo_root = os.path.normpath(os.path.join(current_dir, '..', '..', '..'))
            self.projects_root = os.path.join(repo_root, 'data', 'projects')
        except Exception:
            # Fallback to user home
            self.projects_root = os.path.expanduser('~/shypn-projects')
        
        # Create projects root if needed
        os.makedirs(self.projects_root, exist_ok=True)
    
    def get_project_index_file(self) -> str:
        """Get path to project_index.json."""
        return os.path.join(self.projects_root, 'project_index.json')
    
    def get_recent_projects_file(self) -> str:
        """Get path to recent_projects.json."""
        return os.path.join(self.projects_root, 'recent_projects.json')
    
    def load_index(self):
        """Load project index from disk."""
        index_file = self.get_project_index_file()
        if os.path.exists(index_file):
            try:
                with open(index_file, 'r', encoding='utf-8') as f:
                    self.project_index = json.load(f)
            except Exception as e:
                print(f"Warning: Failed to load project index: {e}")
                self.project_index = {}
        else:
            self.project_index = {}
    
    def save_index(self):
        """Save project index to disk."""
        index_file = self.get_project_index_file()
        os.makedirs(os.path.dirname(index_file), exist_ok=True)
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(self.project_index, f, indent=2, ensure_ascii=False)
    
    def load_recent_projects(self):
        """Load recent projects list from disk."""
        recent_file = self.get_recent_projects_file()
        if os.path.exists(recent_file):
            try:
                with open(recent_file, 'r', encoding='utf-8') as f:
                    self.recent_projects = json.load(f)
            except Exception as e:
                print(f"Warning: Failed to load recent projects: {e}")
                self.recent_projects = []
        else:
            self.recent_projects = []
    
    def save_recent_projects(self):
        """Save recent projects list to disk."""
        recent_file = self.get_recent_projects_file()
        os.makedirs(os.path.dirname(recent_file), exist_ok=True)
        with open(recent_file, 'w', encoding='utf-8') as f:
            json.dump(self.recent_projects[:self.max_recent], f, indent=2)
    
    def create_project(self, name: str, description: str = "",
                      template: str = None) -> Project:
        """Create a new project.
        
        Args:
            name: Project name
            description: Optional description
            template: Optional template name ('basic', 'kegg', etc.)
            
        Returns:
            Created Project instance
        """
        project = Project(name=name, description=description)
        
        # Set base path: data/projects/[uuid]/
        project.base_path = os.path.join(self.projects_root, project.id)
        
        # Create directory structure
        project.create_directory_structure()
        
        # Save project file
        project.save()
        
        # Add to index
        self.project_index[project.id] = {
            'id': project.id,
            'name': project.name,
            'path': project.base_path,
            'created_date': project.created_date,
            'modified_date': project.modified_date
        }
        self.save_index()
        
        # Add to recent projects
        self.add_to_recent(project.id)
        
        return project
    
    def open_project(self, project_id: str) -> Optional[Project]:
        """Open a project by ID.
        
        Args:
            project_id: UUID of project to open
            
        Returns:
            Loaded Project instance or None if not found
        """
        # Check if project exists in index
        if project_id not in self.project_index:
            return None
        
        project_info = self.project_index[project_id]
        project_file = os.path.join(project_info['path'], 'project.shy')
        
        if not os.path.exists(project_file):
            print(f"Warning: Project file not found: {project_file}")
            return None
        
        try:
            project = Project.load(project_file)
            self.current_project = project
            self.add_to_recent(project_id)
            return project
        except Exception as e:
            print(f"Error loading project: {e}")
            return None
    
    def open_project_by_path(self, project_file: str) -> Optional[Project]:
        """Open a project by file path.
        
        Args:
            project_file: Path to project.shy file
            
        Returns:
            Loaded Project instance or None on error
        """
        try:
            project = Project.load(project_file)
            self.current_project = project
            
            # Add to index if not present
            if project.id not in self.project_index:
                self.project_index[project.id] = {
                    'id': project.id,
                    'name': project.name,
                    'path': project.base_path,
                    'created_date': project.created_date,
                    'modified_date': project.modified_date
                }
                self.save_index()
            
            self.add_to_recent(project.id)
            return project
        except Exception as e:
            print(f"Error loading project: {e}")
            return None
    
    def close_current_project(self, save: bool = True):
        """Close the current project.
        
        Args:
            save: Whether to save before closing
        """
        if self.current_project and save:
            try:
                self.current_project.save()
            except Exception as e:
                print(f"Error saving project: {e}")
        
        self.current_project = None
    
    def add_to_recent(self, project_id: str):
        """Add project to recent projects list (moves to front)."""
        # Remove if already present
        if project_id in self.recent_projects:
            self.recent_projects.remove(project_id)
        
        # Add to front
        self.recent_projects.insert(0, project_id)
        
        # Trim to max
        self.recent_projects = self.recent_projects[:self.max_recent]
        
        # Save
        self.save_recent_projects()
    
    def get_recent_projects_info(self) -> List[Dict[str, Any]]:
        """Get information about recent projects.
        
        Returns:
            List of project info dicts
        """
        results = []
        for project_id in self.recent_projects:
            if project_id in self.project_index:
                results.append(self.project_index[project_id])
        return results
    
    def delete_project(self, project_id: str, delete_files: bool = False) -> bool:
        """Delete a project from index.
        
        Args:
            project_id: UUID of project to delete
            delete_files: Whether to delete files from disk
            
        Returns:
            True if deleted, False if not found
        """
        if project_id not in self.project_index:
            return False
        
        project_info = self.project_index[project_id]
        
        # Remove from index
        del self.project_index[project_id]
        self.save_index()
        
        # Remove from recent
        if project_id in self.recent_projects:
            self.recent_projects.remove(project_id)
            self.save_recent_projects()
        
        # Delete files if requested
        if delete_files:
            import shutil
            try:
                shutil.rmtree(project_info['path'])
            except Exception as e:
                print(f"Warning: Failed to delete project files: {e}")
        
        return True


# Global singleton instance
_project_manager = None


def get_project_manager() -> ProjectManager:
    """Get the global ProjectManager singleton.
    
    Returns:
        ProjectManager instance
    """
    global _project_manager
    if _project_manager is None:
        _project_manager = ProjectManager()
        _project_manager.load_index()
        _project_manager.load_recent_projects()
    return _project_manager
