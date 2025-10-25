#!/usr/bin/env python3
"""Project File System Observer.

This module monitors project directories for external file changes and
automatically syncs the Project state with the file system.

Classes:
    ProjectFileObserver: Monitors project directory using watchdog
    ProjectFileHandler: Handles file system events
"""

import json
import logging
from pathlib import Path
from typing import Optional

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileSystemEvent
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    Observer = None
    FileSystemEventHandler = object
    FileSystemEvent = object

from .pathway_document import PathwayDocument
from .enrichment_document import EnrichmentDocument


class ProjectFileHandler(FileSystemEventHandler):
    """Handles file system events in project pathways directory.
    
    Automatically discovers new pathway files and removes deleted ones.
    
    Attributes:
        project: Reference to Project instance
        logger: Logger instance
    """
    
    def __init__(self, project):
        """Initialize file handler.
        
        Args:
            project: Project instance to sync with
        """
        super().__init__()
        self.project = project
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def on_created(self, event: FileSystemEvent):
        """Handle new file added to pathways directory.
        
        Args:
            event: File system event
        """
        if event.is_directory:
            return
        
        self._handle_pathway_file_added(Path(event.src_path))
    
    def on_deleted(self, event: FileSystemEvent):
        """Handle file deleted from pathways directory.
        
        Args:
            event: File system event
        """
        if event.is_directory:
            return
        
        self._handle_pathway_file_deleted(Path(event.src_path))
    
    def on_modified(self, event: FileSystemEvent):
        """Handle file modified in pathways directory.
        
        Args:
            event: File system event
        """
        if event.is_directory:
            return
        
        # Only handle metadata file modifications
        if event.src_path.endswith('.meta.json'):
            self._handle_metadata_modified(Path(event.src_path))
    
    def _handle_pathway_file_added(self, file_path: Path):
        """Auto-create PathwayDocument for new file.
        
        Args:
            file_path: Path to new file
        """
        filename = file_path.name
        
        # Ignore hidden project structure files
        if filename.startswith('.project.'):
            return
        
        # Check if already tracked
        for pathway in self.project.pathways.list_pathways():
            if pathway.raw_file == filename:
                self.logger.debug(f"File {filename} already tracked")
                return
        
        # Auto-discover based on file type
        try:
            if filename.endswith('.kgml') or filename.endswith('.xml'):
                pathway_doc = self._discover_kegg_file(file_path)
            elif filename.endswith('.sbml'):
                pathway_doc = self._discover_sbml_file(file_path)
            else:
                self.logger.debug(f"Unknown file type: {filename}")
                return
            
            # Add to project
            self.project.add_pathway(pathway_doc)
            self.project.save()
            
            self.logger.info(f"Auto-discovered pathway: {pathway_doc.name} from {filename}")
            
        except Exception as e:
            self.logger.error(f"Failed to auto-discover {filename}: {e}")
    
    def _handle_pathway_file_deleted(self, file_path: Path):
        """Remove PathwayDocument for deleted file.
        
        Args:
            file_path: Path to deleted file
        """
        filename = file_path.name
        
        # Ignore hidden project structure files
        if filename.startswith('.project.'):
            return
        
        # Find PathwayDocument with this raw_file
        for pathway in self.project.pathways.list_pathways():
            if pathway.raw_file == filename:
                # Check if has enrichments (warn user)
                if pathway.has_enrichments():
                    self.logger.warning(
                        f"Pathway {pathway.name} has enrichments but file was deleted. "
                        f"Enrichments preserved in project."
                    )
                
                # Remove from project
                self.project.remove_pathway(pathway.id)
                self.project.save()
                
                self.logger.info(f"Removed pathway {pathway.name} (file deleted externally)")
                return
    
    def _handle_metadata_modified(self, file_path: Path):
        """Reload PathwayDocument when metadata file changes.
        
        Args:
            file_path: Path to modified metadata file
        """
        filename = file_path.name
        
        # Ignore hidden project structure files
        if filename.startswith('.project.'):
            return
        
        # Find PathwayDocument with this metadata_file
        for pathway in self.project.pathways.list_pathways():
            if pathway.metadata_file == filename:
                # Reload metadata (future enhancement)
                pathway.update_modified_date()
                self.project.save()
                
                self.logger.info(f"Metadata updated for pathway {pathway.name}")
                return
    
    def _discover_kegg_file(self, file_path: Path) -> PathwayDocument:
        """Auto-discover KEGG pathway from KGML file.
        
        Args:
            file_path: Path to KGML file
            
        Returns:
            PathwayDocument instance
        """
        filename = file_path.name
        pathway_id = file_path.stem  # "hsa00010"
        
        # Try to parse KGML for metadata
        try:
            from shypn.importer.kegg import parse_kgml
            
            kgml_data = file_path.read_text(encoding='utf-8')
            pathway = parse_kgml(kgml_data)
            
            pathway_name = pathway.title or pathway_id
            organism = pathway.org or self._infer_organism(pathway_id)
            
        except Exception as e:
            self.logger.warning(f"Could not parse KGML {filename}: {e}")
            pathway_name = pathway_id
            organism = self._infer_organism(pathway_id)
        
        # Create PathwayDocument
        pathway_doc = PathwayDocument(
            name=pathway_name,
            source_type='kegg',
            source_id=pathway_id,
            source_organism=organism
        )
        pathway_doc.raw_file = filename
        pathway_doc.tags = ['auto-discovered', 'external']
        pathway_doc.notes = f'Auto-discovered from file system: {file_path}'
        
        return pathway_doc
    
    def _discover_sbml_file(self, file_path: Path) -> PathwayDocument:
        """Auto-discover SBML pathway from SBML file.
        
        Args:
            file_path: Path to SBML file
            
        Returns:
            PathwayDocument instance
        """
        filename = file_path.name
        model_id = file_path.stem
        
        # Try to parse SBML for metadata
        try:
            from shypn.data.pathway.sbml_parser import SBMLParser
            
            parser = SBMLParser()
            pathway_data = parser.parse(str(file_path))
            
            model_name = pathway_data.metadata.get('name', model_id)
            
        except Exception as e:
            self.logger.warning(f"Could not parse SBML {filename}: {e}")
            model_name = model_id
        
        # Create PathwayDocument
        pathway_doc = PathwayDocument(
            name=model_name,
            source_type='sbml',
            source_id=model_id,
            source_organism='Unknown'
        )
        pathway_doc.raw_file = filename
        pathway_doc.tags = ['auto-discovered', 'external']
        pathway_doc.notes = f'Auto-discovered from file system: {file_path}'
        
        return pathway_doc
    
    def _infer_organism(self, pathway_id: str) -> str:
        """Infer organism from KEGG pathway ID.
        
        Args:
            pathway_id: KEGG pathway ID (e.g., "hsa00010")
            
        Returns:
            Organism name
        """
        organism_map = {
            'hsa': 'Homo sapiens',
            'mmu': 'Mus musculus',
            'rno': 'Rattus norvegicus',
            'dme': 'Drosophila melanogaster',
            'cel': 'Caenorhabditis elegans',
            'sce': 'Saccharomyces cerevisiae',
            'eco': 'Escherichia coli',
            'map': 'Reference pathway'
        }
        
        if len(pathway_id) >= 3:
            org_code = pathway_id[:3]
            return organism_map.get(org_code, 'Unknown')
        
        return 'Unknown'


class ProjectFileObserver:
    """Monitors project directory for file system changes.
    
    Uses watchdog library to detect file changes and automatically
    sync Project state with the file system.
    
    Attributes:
        project: Reference to Project instance
        observer: Watchdog Observer instance
        handler: ProjectFileHandler instance
        logger: Logger instance
    """
    
    def __init__(self, project, enabled: Optional[bool] = None):
        """Initialize file observer.
        
        Args:
            project: Project instance to monitor
            enabled: Override project setting for file observer
        """
        self.project = project
        self.observer = None
        self.handler = None
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Check if enabled
        if enabled is None:
            enabled = project.settings.get('file_observer_enabled', True)
        
        self.enabled = enabled and WATCHDOG_AVAILABLE
        
        if not WATCHDOG_AVAILABLE:
            self.logger.warning("watchdog library not available - file observer disabled")
    
    def start_monitoring(self):
        """Start watching project pathways directory."""
        if not self.enabled:
            self.logger.debug("File observer disabled")
            return
        
        pathways_dir = self.project.get_pathways_dir()
        if not pathways_dir or not pathways_dir.exists():
            self.logger.warning(f"Pathways directory does not exist: {pathways_dir}")
            return
        
        self.handler = ProjectFileHandler(self.project)
        self.observer = Observer()
        self.observer.schedule(self.handler, str(pathways_dir), recursive=False)
        self.observer.start()
        
        self.logger.info(f"Started monitoring: {pathways_dir}")
    
    def stop_monitoring(self):
        """Stop watching project directory."""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.logger.info("Stopped monitoring")
    
    def is_monitoring(self) -> bool:
        """Check if currently monitoring.
        
        Returns:
            True if observer is running
        """
        return self.observer is not None and self.observer.is_alive()
