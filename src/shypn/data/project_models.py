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

from .pathway_document import PathwayDocument
from .enrichment_document import EnrichmentDocument
from .project_pathway_manager import ProjectPathwayManager


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
        
        # Pathway management (new structured approach)
        self._pathway_manager = ProjectPathwayManager(self)
        
        self.simulations = []  # List of simulation result file paths
        self.tags = []
        self.settings = {
            'auto_backup': True,
            'backup_frequency': 'daily',
            'keep_backups': 5
        }
    
    def __str__(self) -> str:
        """String representation showing project name (user-friendly)."""
        return self.name
    
    def __repr__(self) -> str:
        """Detailed representation for debugging."""
        return f"Project(name='{self.name}', id='{self.id[:8]}...', models={len(self.models)})"
    
    def get_project_file_path(self) -> Optional[str]:
        """Get the path to .project.shy file (hidden from user)."""
        if self.base_path:
            return os.path.join(self.base_path, '.project.shy')
        return None
    
    def get_models_dir(self) -> Optional[str]:
        """Get the models directory path."""
        if self.base_path:
            return os.path.join(self.base_path, 'models')
        return None
    
    def get_pathways_dir(self) -> Optional[Path]:
        """Get the pathways directory path.
        
        Returns:
            Path object for pathways directory, or None if base_path not set
        """
        if self.base_path:
            return Path(self.base_path) / 'pathways'
        return None
    
    def get_simulations_dir(self) -> Optional[str]:
        """Get the simulations directory path."""
        if self.base_path:
            return os.path.join(self.base_path, 'simulations')
        return None
    
    def get_enrichments_dir(self) -> Optional[str]:
        """Get the enrichments directory path.
        
        Returns:
            Absolute path to enrichments directory, or None if base_path not set
        """
        if self.base_path:
            return os.path.join(self.base_path, 'enrichments')
        return None
    
    # Pathway management properties and methods
    @property
    def pathways(self) -> ProjectPathwayManager:
        """Get the pathway manager for this project.
        
        Returns:
            ProjectPathwayManager instance
        """
        return self._pathway_manager
    
    def add_pathway(self, pathway_doc: PathwayDocument) -> None:
        """Add a pathway to the project.
        
        Args:
            pathway_doc: PathwayDocument to add
        """
        self._pathway_manager.add_pathway(pathway_doc)
    
    def remove_pathway(self, pathway_id: str) -> bool:
        """Remove a pathway from the project.
        
        Args:
            pathway_id: UUID of pathway to remove
            
        Returns:
            True if removed, False if not found
        """
        return self._pathway_manager.remove_pathway(pathway_id)
    
    def get_pathway(self, pathway_id: str) -> Optional[PathwayDocument]:
        """Get a pathway by ID.
        
        Args:
            pathway_id: UUID of pathway
            
        Returns:
            PathwayDocument if found, None otherwise
        """
        return self._pathway_manager.get_pathway(pathway_id)
    
    def find_pathway_by_model_id(self, model_id: str) -> Optional[PathwayDocument]:
        """Find pathway that was converted to a specific model.
        
        Args:
            model_id: UUID of ModelDocument
            
        Returns:
            PathwayDocument if found, None otherwise
        """
        return self._pathway_manager.find_pathway_by_model_id(model_id)
    
    def save_pathway_file(self, filename: str, content: str) -> str:
        """Save a pathway file to the project's pathways directory.
        
        Args:
            filename: Name of file to save
            content: File content (text)
            
        Returns:
            Absolute path to saved file
            
        Raises:
            ValueError: If project base_path not set
        """
        pathways_dir = self.get_pathways_dir()
        if not pathways_dir:
            raise ValueError("Project base_path not set, cannot save pathway file")
        
        # Ensure pathways directory exists
        os.makedirs(pathways_dir, exist_ok=True)
        
        # Save file
        file_path = os.path.join(pathways_dir, filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return file_path
    
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
            'version': '2.0',  # Bumped version for pathway schema change
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
                'pathways': self._pathway_manager.to_dict(),  # New structured format
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
        
        # Load pathways (with migration support)
        pathways_data = content.get('pathways', [])
        if isinstance(pathways_data, dict):
            # New format (v2.0): dict of PathwayDocument objects
            project._pathway_manager.from_dict(pathways_data)
        elif isinstance(pathways_data, list):
            # Old format (v1.0): flat list of file paths - migrate
            project._pathway_manager.migrate_from_list(pathways_data)
        
        project.simulations = content.get('simulations', [])
        project.tags = metadata.get('tags', [])
        project.settings = metadata.get('settings', project.settings)
        
        return project
    
    def save(self):
        """Save project to .project.shy file (hidden from user)."""
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
        """Load project from .project.shy file.
        
        Args:
            project_file: Path to .project.shy file
            
        Returns:
            Loaded Project instance
        """
        with open(project_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        project = cls.from_dict(data)
        
        # Sync with file system (discover new files, remove deleted ones)
        if project.settings.get('auto_sync_on_load', True):
            project._sync_with_filesystem()
        
        return project
    
    def _sync_with_filesystem(self):
        """Sync PathwayDocuments with actual files in pathways directory.
        
        Actions:
            - Remove PathwayDocuments for missing files
            - Discover new files not tracked
        """
        pathways_dir = self.get_pathways_dir()
        if not pathways_dir or not pathways_dir.exists():
            return
        
        # Find and remove PathwayDocuments for missing files
        for pathway_id, pathway_doc in list(self._pathway_manager.pathways.items()):
            if pathway_doc.raw_file:
                file_path = pathways_dir / pathway_doc.raw_file
                if not file_path.exists():
                    # File was deleted externally
                    self.remove_pathway(pathway_id)
        
        # Discover new files (if auto-discovery enabled)
        if self.settings.get('auto_discover_pathways', True):
            for file_path in pathways_dir.glob('*.kgml'):
                self._discover_pathway_file(file_path)
            
            for file_path in pathways_dir.glob('*.xml'):
                if not file_path.name.endswith('.meta.xml'):
                    self._discover_pathway_file(file_path)
            
            for file_path in pathways_dir.glob('*.sbml'):
                self._discover_pathway_file(file_path)
    
    def _discover_pathway_file(self, file_path: Path):
        """Discover a pathway file if not already tracked.
        
        Args:
            file_path: Path to pathway file
        """
        from .project_file_observer import ProjectFileHandler
        
        filename = file_path.name
        
        # Check if already tracked
        for pathway in self._pathway_manager.list_pathways():
            if pathway.raw_file == filename:
                return  # Already tracked
        
        # Use file handler to discover
        handler = ProjectFileHandler(self)
        handler._handle_pathway_file_added(file_path)
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
    """Global singleton for managing all projects in workspace.
    
    Responsibilities:
    - Maintain list of open projects
    - Provide project lookup and creation
    - Manage project file observers
    - Handle workspace-level operations
    
    Usage:
        manager = ProjectManager.get_instance()
        project = manager.load_project("path/to/.project.shy")
        manager.close_project(project.id)
    """
    
    _instance = None
    
    def __init__(self):
        """Initialize project manager (singleton)."""
        self.projects: Dict[str, Project] = {}
        self.observers: Dict[str, 'ProjectFileObserver'] = {}
        self.workspace_path = None
    
    @classmethod
    def get_instance(cls) -> 'ProjectManager':
        """Get singleton instance.
        
        Returns:
            ProjectManager singleton
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def set_workspace_path(self, path: str):
        """Set the workspace root path.
        
        Args:
            path: Absolute path to workspace directory
        """
        self.workspace_path = path
    
    def load_project(self, project_file: str) -> Project:
        """Load a project and start file monitoring.
        
        Args:
            project_file: Path to .project.shy file
            
        Returns:
            Loaded Project instance
        """
        project = Project.load(project_file)
        self.projects[project.id] = project
        
        # Start file system observer
        try:
            from .project_file_observer import ProjectFileObserver
            observer = ProjectFileObserver(project)
            observer.start_monitoring()
            self.observers[project.id] = observer
        except ImportError:
            # watchdog not available
            pass
        
        return project
    
    def close_project(self, project_id: str) -> bool:
        """Close a project and stop monitoring.
        
        Args:
            project_id: UUID of project to close
            
        Returns:
            True if closed, False if not found
        """
        # Stop observer
        if project_id in self.observers:
            self.observers[project_id].stop_monitoring()
            del self.observers[project_id]
        
        # Remove from active projects
        if project_id in self.projects:
            del self.projects[project_id]
            return True
        
        return False
    
    def get_project(self, project_id: str) -> Optional[Project]:
        """Get an open project by ID.
        
        Args:
            project_id: UUID of project
            
        Returns:
            Project instance or None
        """
        return self.projects.get(project_id)
    
    def list_projects(self) -> List[Project]:
        """Get all open projects.
        
        Returns:
            List of Project instances
        """
        return list(self.projects.values())
    
    def create_project(self, name: str, base_path: str) -> Project:
        """Create a new project.
        
        Args:
            name: Project name
            base_path: Directory for project
            
        Returns:
            New Project instance
        """
        project = Project(name=name, base_path=base_path)
        
        # Create directory structure
        os.makedirs(base_path, exist_ok=True)
        os.makedirs(project.get_models_dir(), exist_ok=True)
        os.makedirs(project.get_pathways_dir(), exist_ok=True)
        os.makedirs(project.get_simulations_dir(), exist_ok=True)
        
        # Save project file
        project.save()
        
        # Add to managed projects
        self.projects[project.id] = project
        
        # Start observer
        try:
            from .project_file_observer import ProjectFileObserver
            observer = ProjectFileObserver(project)
            observer.start_monitoring()
            self.observers[project.id] = observer
        except ImportError:
            pass
        
        return project
    
    def _setup_default_paths(self):
        """Setup default project paths in workspace directory."""
        # Try to find repository root
        try:
            # This file is in src/shypn/data/
            current_dir = os.path.dirname(os.path.abspath(__file__))
            repo_root = os.path.normpath(os.path.join(current_dir, '..', '..', '..'))
            # Use workspace/projects/ to isolate from application code
            self.projects_root = os.path.join(repo_root, 'workspace', 'projects')
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
                self.recent_projects = []
        else:
            self.recent_projects = []
    
    def save_recent_projects(self):
        """Save recent projects list to disk."""
        recent_file = self.get_recent_projects_file()
        os.makedirs(os.path.dirname(recent_file), exist_ok=True)
        with open(recent_file, 'w', encoding='utf-8') as f:
            json.dump(self.recent_projects[:self.max_recent], f, indent=2)
    
    def _sanitize_directory_name(self, name: str) -> str:
        """Convert project name to valid directory name.
        
        Args:
            name: Project name
            
        Returns:
            Sanitized directory name
        """
        # Replace spaces and invalid characters with underscores
        import re
        sanitized = re.sub(r'[^\w\s-]', '_', name)
        sanitized = re.sub(r'[\s]+', '_', sanitized)
        sanitized = sanitized.strip('_')
        return sanitized if sanitized else "Project"
    
    def create_project(self, name: str, description: str = "") -> Project:
        """Create a new project.
        
        Creates an empty project with standard directory structure.
        Users can then import data using KEGG/SBML import panels.
        
        Args:
            name: Project name
            description: Optional description
            
        Returns:
            Created Project instance
        """
        project = Project(name=name, description=description)
        
        # Set base path using sanitized project name (not UUID)
        base_name = self._sanitize_directory_name(name)
        
        # Handle naming conflicts by appending counter
        counter = 1
        dir_name = base_name
        while os.path.exists(os.path.join(self.projects_root, dir_name)):
            counter += 1
            dir_name = f"{base_name}_{counter}"
        
        project.base_path = os.path.join(self.projects_root, dir_name)
        
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
        project_file = os.path.join(project_info['path'], '.project.shy')
        
        if not os.path.exists(project_file):
            return None
        
        try:
            project = Project.load(project_file)
            self.current_project = project
            self.add_to_recent(project_id)
            return project
        except Exception as e:
            return None
    
    def open_project_by_path(self, project_file: str) -> Optional[Project]:
        """Open a project by file path.
        
        Args:
            project_file: Path to .project.shy file
            
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
                pass  # Silently ignore save errors when closing
        
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
        """Get information about recent projects (with human-friendly names).
        
        Returns:
            List of project info dicts with display names
        """
        results = []
        for project_id in self.recent_projects:
            if project_id in self.project_index:
                results.append(self.project_index[project_id])
        return results
    
    def get_project_by_name(self, name: str) -> Optional[Project]:
        """Get a project by its name (alias for UUID).
        
        This allows looking up projects by human-friendly name instead of UUID.
        Case-insensitive search.
        
        Args:
            name: Project name to search for
            
        Returns:
            Project instance if found, None otherwise
        """
        name_lower = name.lower()
        for project_id, info in self.project_index.items():
            if info['name'].lower() == name_lower:
                return self.open_project(project_id)
        return None
    
    def find_projects_by_name(self, name_pattern: str) -> List[Dict[str, Any]]:
        """Find projects matching a name pattern (partial match).
        
        Args:
            name_pattern: Pattern to search for in project names
            
        Returns:
            List of project info dicts matching the pattern
        """
        pattern_lower = name_pattern.lower()
        matches = []
        for project_id, info in self.project_index.items():
            if pattern_lower in info['name'].lower():
                matches.append(info)
        return matches
    
    def get_project_display_name(self, project_id: str) -> str:
        """Get human-friendly display name for a project.
        
        Returns the project name instead of UUID for display purposes.
        
        Args:
            project_id: UUID of the project
            
        Returns:
            Project name, or truncated UUID if not found
        """
        if project_id in self.project_index:
            return self.project_index[project_id]['name']
        return f"Project {project_id[:8]}..."
    
    def list_all_projects(self) -> List[Dict[str, Any]]:
        """Get list of all projects with display information.
        
        Returns sorted list by project name (not UUID).
        
        Returns:
            List of dicts with keys: id, name, path, created_date, modified_date
        """
        projects = list(self.project_index.values())
        # Sort by name (human-friendly)
        projects.sort(key=lambda p: p['name'].lower())
        return projects
    
    def delete_project(self, project_id: str, delete_files: bool = False) -> bool:
        """Delete a project from index.
        
        SAFETY: Deletion is permanent and cannot be undone! Consider archiving instead.
        
        Args:
            project_id: UUID of project to delete
            delete_files: Whether to delete files from disk (DANGEROUS!)
            
        Returns:
            True if deleted, False if not found
            
        Raises:
            ValueError: If attempting to delete files outside projects directory
        """
        if project_id not in self.project_index:
            return False
        
        project_info = self.project_index[project_id]
        
        # SAFETY CHECK: Verify path is within projects directory
        if delete_files:
            project_path = os.path.abspath(project_info['path'])
            projects_root_abs = os.path.abspath(self.projects_root)
            
            # Ensure path is under projects_root
            if not project_path.startswith(projects_root_abs + os.sep):
                raise ValueError(
                    f"SAFETY ERROR: Project path '{project_path}' is outside "
                    f"projects directory '{projects_root_abs}'. Deletion blocked."
                )
            
            # Additional safety: Check path contains UUID or project name
            project_name_sanitized = self._sanitize_directory_name(project_info['name'])
            path_basename = os.path.basename(project_path)
            
            if project_id not in project_path and project_name_sanitized not in path_basename:
                raise ValueError(
                    f"SAFETY ERROR: Project path '{project_path}' doesn't contain "
                    f"expected identifiers. Deletion blocked."
                )
        
        # Remove from index
        del self.project_index[project_id]
        self.save_index()
        
        # Remove from recent
        if project_id in self.recent_projects:
            self.recent_projects.remove(project_id)
            self.save_recent_projects()
        
        # Delete files if requested (with safety checks passed)
        if delete_files:
            import shutil
            try:
                # Final confirmation: path exists and is a directory
                if os.path.exists(project_path) and os.path.isdir(project_path):
                    shutil.rmtree(project_path)
                else:
                    pass  # Path doesn't exist or isn't a directory
            except Exception as e:
                # Re-add to index if file deletion failed
                self.project_index[project_id] = project_info
                self.save_index()
                raise  # Re-raise to let caller handle
        
        return True
    
    def archive_project(self, project_id: str, archive_path: str = None) -> str:
        """Archive a project to a ZIP file (SAFER alternative to deletion).
        
        This creates a backup before removing from index, allowing recovery.
        
        Args:
            project_id: UUID of project to archive
            archive_path: Optional custom path for archive file.
                         If None, creates in projects_root/archives/
            
        Returns:
            Path to created archive file
            
        Raises:
            FileNotFoundError: If project not found
            ValueError: If archive operation fails
        """
        if project_id not in self.project_index:
            raise FileNotFoundError(f"Project {project_id} not found")
        
        project_info = self.project_index[project_id]
        project_path = project_info['path']
        
        # Create archives directory if needed
        if archive_path is None:
            archives_dir = os.path.join(self.projects_root, 'archives')
            os.makedirs(archives_dir, exist_ok=True)
            
            # Use sanitized name + timestamp for archive filename
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_name = self._sanitize_directory_name(project_info['name'])
            archive_filename = f"{safe_name}_{timestamp}.zip"
            archive_path = os.path.join(archives_dir, archive_filename)
        
        # Create ZIP archive
        import shutil
        try:
            # shutil.make_archive expects base name without extension
            base_name = archive_path.rsplit('.zip', 1)[0] if archive_path.endswith('.zip') else archive_path
            shutil.make_archive(base_name, 'zip', project_path)
            
            # Ensure .zip extension
            final_archive_path = base_name + '.zip'
            
            
            # Now safe to remove from index (files preserved in archive)
            del self.project_index[project_id]
            self.save_index()
            
            if project_id in self.recent_projects:
                self.recent_projects.remove(project_id)
                self.save_recent_projects()
            
            return final_archive_path
            
        except Exception as e:
            raise ValueError(f"Failed to archive project: {e}")


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
