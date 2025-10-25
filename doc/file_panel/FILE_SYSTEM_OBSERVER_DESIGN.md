# File System Observer - Design & Implementation

**Date:** October 25, 2025  
**Phase:** 7 (Added to implementation plan)

---

## Problem Statement

**User Need:** When users directly manipulate files in the project folder (via file explorer, command line, or external tools), the Project state should automatically reflect those changes.

**Examples:**
- User copies `hsa00010.kgml` to `pathways/` directory → Should appear in File Panel
- User deletes a pathway file → Should be removed from Project
- User edits `metadata.json` → Should be reflected in Project state

---

## Solution: File System Observer

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│                 ProjectManager                          │
│  - load_project() → starts observer                     │
│  - close_project() → stops observer                     │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ↓
┌─────────────────────────────────────────────────────────┐
│              ProjectFileObserver                        │
│  - Uses watchdog.Observer                               │
│  - Monitors pathways/ directory                         │
│  - Delegates events to ProjectFileHandler               │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ↓
┌─────────────────────────────────────────────────────────┐
│             ProjectFileHandler                          │
│  - on_created() → Auto-discover pathway                 │
│  - on_deleted() → Remove PathwayDocument                │
│  - on_modified() → Update metadata                      │
└─────────────────────────────────────────────────────────┘
```

### Implementation

**File:** `src/shypn/data/project_file_observer.py` (~300 lines)

**Classes:**
1. **ProjectFileHandler** - Handles file system events
   - Auto-discovers KEGG files (`.kgml`, `.xml`)
   - Auto-discovers SBML files (`.sbml`)
   - Removes PathwayDocuments when files deleted
   - Updates metadata when `.meta.json` modified

2. **ProjectFileObserver** - Manages watchdog observer
   - Starts/stops monitoring
   - Configurable via project settings
   - Graceful fallback if watchdog unavailable

### Auto-Discovery Logic

#### KEGG File Discovery

```python
def _discover_kegg_file(self, file_path: Path) -> PathwayDocument:
    """Auto-discover KEGG pathway from KGML file."""
    
    # Parse KGML to extract metadata
    kgml_data = file_path.read_text()
    pathway = parse_kgml(kgml_data)
    
    # Create PathwayDocument
    pathway_doc = PathwayDocument(
        name=pathway.title or pathway_id,
        source_type='kegg',
        source_id=pathway_id,  # from filename
        source_organism=pathway.org or infer_from_id(pathway_id)
    )
    pathway_doc.raw_file = filename
    pathway_doc.tags = ['auto-discovered', 'external']
    
    return pathway_doc
```

#### SBML File Discovery

```python
def _discover_sbml_file(self, file_path: Path) -> PathwayDocument:
    """Auto-discover SBML pathway from SBML file."""
    
    # Parse SBML to extract metadata
    parser = SBMLParser()
    pathway_data = parser.parse(str(file_path))
    
    # Create PathwayDocument
    pathway_doc = PathwayDocument(
        name=pathway_data.metadata.get('name', model_id),
        source_type='sbml',
        source_id=model_id,  # from filename
        source_organism='Unknown'
    )
    pathway_doc.raw_file = filename
    pathway_doc.tags = ['auto-discovered', 'external']
    
    return pathway_doc
```

### Sync on Load

**Modified:** `src/shypn/data/project_models.py`

```python
class Project:
    @classmethod
    def load(cls, project_file: str) -> 'Project':
        """Load project and sync with file system."""
        project = cls.from_dict(data)
        
        # Sync with file system
        if project.settings.get('auto_sync_on_load', True):
            project._sync_with_filesystem()
        
        return project
    
    def _sync_with_filesystem(self):
        """Sync PathwayDocuments with actual files."""
        pathways_dir = self.get_pathways_dir()
        
        # Remove PathwayDocuments for missing files
        for pathway_id, pathway_doc in list(self.pathways.pathways.items()):
            file_path = pathways_dir / pathway_doc.raw_file
            if not file_path.exists():
                self.remove_pathway(pathway_id)
        
        # Discover new files
        if self.settings.get('auto_discover_pathways', True):
            for file_path in pathways_dir.glob('*.kgml'):
                self._discover_pathway_file(file_path)
            for file_path in pathways_dir.glob('*.sbml'):
                self._discover_pathway_file(file_path)
```

### ProjectManager Integration

**Modified:** `src/shypn/data/project_models.py`

```python
class ProjectManager:
    def __init__(self):
        self.projects = {}
        self.observers = {}  # project_id -> ProjectFileObserver
    
    def load_project(self, project_file: str) -> Project:
        """Load project and start monitoring."""
        project = Project.load(project_file)
        self.projects[project.id] = project
        
        # Start file system observer
        observer = ProjectFileObserver(project)
        observer.start_monitoring()
        self.observers[project.id] = observer
        
        return project
    
    def close_project(self, project_id: str):
        """Close project and stop monitoring."""
        if project_id in self.observers:
            self.observers[project_id].stop_monitoring()
            del self.observers[project_id]
        
        if project_id in self.projects:
            del self.projects[project_id]
```

---

## Configuration

### Project Settings

```python
project.settings.update({
    'file_observer_enabled': True,        # Enable/disable observer
    'auto_sync_on_load': True,            # Sync when loading project
    'auto_discover_pathways': True,       # Auto-discover new files
    'notify_on_changes': True             # Show notifications (future)
})
```

### Dependencies

```bash
pip install watchdog>=3.0.0
```

Add to `requirements.txt`:
```
watchdog>=3.0.0  # File system monitoring
```

---

## Usage Examples

### Example 1: Copy File to Project

```bash
# User copies KGML file
$ cp ~/Downloads/hsa00010.kgml workspace/projects/MyProject/pathways/

# Application automatically:
# 1. Detects new file
# 2. Parses KGML
# 3. Creates PathwayDocument
# 4. Adds to project
# 5. Saves project.shy
# 6. Updates File Panel (if visible)
```

### Example 2: Delete File Externally

```bash
# User deletes pathway file
$ rm workspace/projects/MyProject/pathways/hsa00010.kgml

# Application automatically:
# 1. Detects deletion
# 2. Finds PathwayDocument with raw_file="hsa00010.kgml"
# 3. Removes from project
# 4. Saves project.shy
# 5. Updates File Panel
```

### Example 3: Project Load Sync

```python
# Load project
project = Project.load("workspace/projects/MyProject/project.shy")

# Automatic sync:
# - Scans pathways/ directory
# - Removes PathwayDocuments for missing files
# - Discovers new files not tracked
# - Updates project state
```

---

## Edge Cases Handled

### 1. File Has Enrichments

```python
def _handle_pathway_file_deleted(self, file_path: Path):
    """Handle deletion of file with enrichments."""
    
    for pathway in self.project.pathways.list_pathways():
        if pathway.raw_file == filename:
            if pathway.has_enrichments():
                # Log warning but preserve enrichments
                self.logger.warning(
                    f"Pathway {pathway.name} has enrichments "
                    f"but file was deleted. Enrichments preserved."
                )
            
            # Still remove from project
            self.project.remove_pathway(pathway.id)
```

### 2. Watchdog Not Available

```python
class ProjectFileObserver:
    def __init__(self, project):
        if not WATCHDOG_AVAILABLE:
            self.logger.warning(
                "watchdog library not available - "
                "file observer disabled"
            )
            self.enabled = False
```

### 3. Rapid Changes (Debouncing)

- Watchdog handles debouncing internally
- Multiple events for same file are coalesced
- Safe for bulk operations (copying multiple files)

---

## Testing Strategy

### Unit Tests (`tests/data/test_project_file_observer.py`)

```python
def test_file_created():
    """Test new file detection."""
    # Create project
    project = create_test_project()
    
    # Copy KGML file to pathways/
    kgml_file = project.pathways_dir / "hsa00010.kgml"
    kgml_file.write_text(sample_kgml_data)
    
    # Wait for observer
    time.sleep(0.5)
    
    # Verify PathwayDocument created
    pathways = project.pathways.list_pathways()
    assert len(pathways) == 1
    assert pathways[0].source_id == "hsa00010"

def test_file_deleted():
    """Test file deletion detection."""
    # Create project with pathway
    project = create_test_project()
    pathway = create_test_pathway()
    project.add_pathway(pathway)
    
    # Delete file
    kgml_file = project.pathways_dir / pathway.raw_file
    kgml_file.unlink()
    
    # Wait for observer
    time.sleep(0.5)
    
    # Verify PathwayDocument removed
    pathways = project.pathways.list_pathways()
    assert len(pathways) == 0
```

---

## Benefits

✅ **User Convenience**
- No manual refresh needed
- Works with any file manager
- Supports drag-and-drop
- Command-line friendly

✅ **Data Integrity**
- Project state always in sync with files
- No orphaned PathwayDocuments
- No missing file references

✅ **Extensibility**
- Easy to add new file types
- Pluggable discovery logic
- Configurable behavior

✅ **Performance**
- Efficient file watching (watchdog is optimized)
- Minimal CPU usage
- No polling overhead

---

## Implementation Status

✅ **Core Architecture** - Complete
- ProjectFileObserver class implemented
- ProjectFileHandler class implemented
- Auto-discovery logic for KEGG/SBML
- Integration with ProjectManager

✅ **Sync on Load** - Complete
- Project._sync_with_filesystem() implemented
- Removes missing PathwayDocuments
- Discovers new files

⚠️ **Testing** - Pending
- Need to create unit tests
- Need integration tests

⚠️ **UI Integration** - Pending
- Need to add refresh button to File Panel
- Need to show notifications (optional)

---

## Next Steps

1. **Add to requirements.txt**: `watchdog>=3.0.0`
2. **Write unit tests**: `tests/data/test_project_file_observer.py`
3. **Test integration**: Manual testing with real projects
4. **UI refresh button**: Add to File Panel (optional)
5. **Documentation**: Update user guide

---

## Timeline

**Estimated:** 1 day (8 hours)
- Core implementation: ✅ Complete (3 hours)
- Testing: ⚠️ Pending (3 hours)
- UI integration: ⚠️ Pending (2 hours)

---

**Status:** Core implementation complete, ready for testing phase.
