# Pathway Data Isolation Plan

## Problem Statement

Currently, there's no clear separation between:
1. **Transient external data** - KEGG pathways fetched from API (temporary, external source)
2. **Project-specific data** - User's local pathway edits and annotations (persistent, local)

This mixing can cause:
- Loss of user modifications when re-fetching from KEGG
- Confusion about data provenance (is this from KEGG or user-edited?)
- Difficulty in version control and data management
- No clear workflow for "import → edit → save as project pathway"

---

## Proposed Architecture

### Directory Structure

```
models/
├── pathway/
│   ├── external/          # NEW - Transient external data
│   │   ├── kegg/          # KEGG-fetched pathways (temporary cache)
│   │   │   ├── hsa00010.xml      # Raw KGML from KEGG
│   │   │   ├── hsa00010.json     # Parsed pathway metadata
│   │   │   └── cache_index.json  # Cache management
│   │   │
│   │   └── reactome/      # Future: Other pathway databases
│   │
│   ├── project/           # NEW - User's project pathways
│   │   ├── glycolysis_modified.shypn   # User-edited pathway
│   │   ├── my_custom_pathway.shypn     # User-created pathway
│   │   └── project_index.json          # Project pathway registry
│   │
│   └── templates/         # NEW - Reusable pathway templates
│       ├── basic_metabolism.shypn
│       └── signaling_cascade.shypn
│
data/
├── projects/              # EXISTING - Project files
│   └── [project_name]/
│       ├── pathways/      # NEW - Pathways specific to this project
│       │   ├── pathway1.shypn
│       │   └── pathway2.shypn
│       └── metadata.json  # Project metadata including pathway refs
│
└── cache/                 # NEW - Application-wide cache
    ├── kegg/              # KEGG cache (auto-cleaned)
    └── downloads/         # Temporary downloads
```

---

## Data Flow Architecture

### Phase 1: External Data Fetch (Transient)

```
User Action: Fetch KEGG Pathway
    ↓
[KEGG API] → Raw KGML
    ↓
[Parser] → PathwayData (in-memory)
    ↓
[Cache] → models/pathway/external/kegg/hsa00010.json
    ↓
[Preview UI] → User reviews pathway
    ↓
Decision Point: Import or Discard?
```

**Characteristics:**
- ✅ Stored in `models/pathway/external/kegg/`
- ✅ Marked as `source: "kegg"` in metadata
- ✅ Has `fetch_date` timestamp
- ✅ Can be re-fetched (overwrites cache)
- ✅ Auto-cleaned after N days (configurable)
- ❌ NOT included in project saves
- ❌ NOT version controlled

---

### Phase 2: Import to Project (Persistent)

```
User Action: Import Pathway
    ↓
[External Data] → models/pathway/external/kegg/hsa00010.json
    ↓
[Converter] → Creates ProjectPathway object
    ↓
[User Edits] → Modifications applied
    ↓
[Save] → data/projects/[project]/pathways/glycolysis_v1.shypn
    ↓
[Project Registry] → Links pathway to project
```

**Characteristics:**
- ✅ Stored in `data/projects/[project]/pathways/`
- ✅ Marked as `source: "imported_from_kegg"` + original KEGG ID
- ✅ Has `import_date` and `modified_date` timestamps
- ✅ Preserves KEGG metadata as reference
- ✅ Included in project saves/exports
- ✅ Can be version controlled
- ✅ User owns and can modify freely

---

## Data Model Classes

### 1. ExternalPathway (Transient)

```python
class ExternalPathway:
    """Represents a pathway from external source (KEGG, Reactome, etc.)"""
    
    # Identity
    source: str               # "kegg", "reactome", etc.
    external_id: str          # "hsa00010" (KEGG ID)
    version: str              # External version/revision
    
    # Metadata
    title: str
    organism: str
    description: str
    fetch_date: datetime
    cache_path: Path          # models/pathway/external/kegg/hsa00010.json
    
    # Data
    document_model: DocumentModel  # Parsed Petri net structure
    raw_data: Dict            # Original KGML/XML for reference
    
    # Status
    is_cached: bool
    cache_expiry: datetime
    
    # Methods
    def to_project_pathway(self) -> 'ProjectPathway'
    def refresh_from_source(self) -> bool
    def clear_cache(self) -> None
```

### 2. ProjectPathway (Persistent)

```python
class ProjectPathway:
    """Represents a user's project-specific pathway"""
    
    # Identity
    pathway_id: str           # UUID for this project pathway
    name: str                 # User-defined name
    project_id: str           # Which project owns this
    
    # Provenance
    source_type: str          # "imported", "created", "template"
    original_source: str      # "kegg:hsa00010" or "user_created"
    import_date: datetime     # When imported
    modified_date: datetime   # Last modification
    
    # Metadata (preserved from external source)
    external_metadata: Dict   # Original KEGG metadata for reference
    user_notes: str           # User annotations
    tags: List[str]           # User-defined tags
    
    # Data
    document_model: DocumentModel  # User's editable Petri net
    file_path: Path           # data/projects/[project]/pathways/name.shypn
    
    # Version control
    version: int              # Local version number
    parent_version: Optional[str]  # For branching/merging
    
    # Methods
    def save(self) -> bool
    def export(self, format: str) -> Path
    def get_diff_from_external(self) -> PathwayDiff
    def sync_with_external(self, strategy: str) -> bool
```

### 3. PathwayCache (Management)

```python
class PathwayCache:
    """Manages external pathway cache"""
    
    cache_dir: Path           # models/pathway/external/
    max_age_days: int         # Default: 30 days
    max_size_mb: int          # Default: 100 MB
    
    def get(self, source: str, external_id: str) -> Optional[ExternalPathway]
    def store(self, pathway: ExternalPathway) -> bool
    def cleanup_expired(self) -> int
    def clear_source(self, source: str) -> bool
    def get_cache_info(self) -> CacheInfo
```

---

## Implementation Phases

### Phase 1: Data Structure Setup (Day 1)
**Priority: HIGH**

- [ ] Create directory structure
  - [ ] `models/pathway/external/kegg/`
  - [ ] `models/pathway/project/`
  - [ ] `data/cache/kegg/`
  
- [ ] Implement data model classes
  - [ ] `ExternalPathway` class
  - [ ] `ProjectPathway` class
  - [ ] `PathwayCache` class
  
- [ ] Create cache management
  - [ ] Cache index file
  - [ ] Auto-cleanup policy
  - [ ] Cache statistics

**Deliverables:**
- `src/shypn/models/pathway_models.py`
- `src/shypn/models/pathway_cache.py`
- Cache directory structure

---

### Phase 2: KEGG Integration Update (Day 2)
**Priority: HIGH**

- [ ] Modify KEGG importer to use ExternalPathway
  - [ ] Store fetched data in cache
  - [ ] Mark as transient/external
  - [ ] Add metadata tracking
  
- [ ] Update preview UI
  - [ ] Show data source indicator
  - [ ] Show cache status
  - [ ] Add "Import to Project" button
  
- [ ] Implement import workflow
  - [ ] Convert ExternalPathway → ProjectPathway
  - [ ] Prompt for project pathway name
  - [ ] Save to project directory

**Deliverables:**
- Updated `kegg_import_panel.py`
- New `pathway_importer.py`
- Import workflow UI

---

### Phase 3: Project Pathway Management (Day 3)
**Priority: MEDIUM**

- [ ] Create project pathway panel
  - [ ] List all pathways in current project
  - [ ] Show provenance (source, import date)
  - [ ] Allow renaming, tagging
  
- [ ] Implement pathway operations
  - [ ] Load project pathway
  - [ ] Save modifications
  - [ ] Export to various formats
  - [ ] Delete pathway
  
- [ ] Add metadata editor
  - [ ] Edit user notes
  - [ ] Add/remove tags
  - [ ] View original source metadata

**Deliverables:**
- `project_pathway_panel.ui`
- `project_pathway_manager.py`
- Metadata editor UI

---

### Phase 4: Data Provenance & Sync (Day 4)
**Priority: MEDIUM**

- [ ] Implement provenance tracking
  - [ ] Visual indicators (badges, icons)
  - [ ] Provenance info dialog
  - [ ] Change history log
  
- [ ] Add sync functionality
  - [ ] Compare project pathway with external source
  - [ ] Show differences (diff viewer)
  - [ ] Merge strategies (keep local, update from external, manual merge)
  
- [ ] Implement conflict resolution
  - [ ] Detect conflicts
  - [ ] Present choices to user
  - [ ] Apply resolution strategy

**Deliverables:**
- `pathway_diff.py`
- `pathway_sync.py`
- Sync/merge UI

---

### Phase 5: File Format & Persistence (Day 5)
**Priority: HIGH**

- [ ] Define `.shypn` pathway format
  - [ ] Include provenance metadata
  - [ ] Store original external data reference
  - [ ] Support versioning
  
- [ ] Implement serialization
  - [ ] ProjectPathway → .shypn file
  - [ ] .shypn file → ProjectPathway
  - [ ] Migration from old format
  
- [ ] Update project save/load
  - [ ] Include pathway references
  - [ ] Handle missing pathways
  - [ ] Validate pathway data

**Deliverables:**
- `.shypn` format specification
- `pathway_serializer.py`
- Migration tools

---

### Phase 6: UI/UX Polish (Day 6)
**Priority: LOW**

- [ ] Visual indicators throughout UI
  - [ ] Source badges (KEGG logo, "Local", etc.)
  - [ ] Modified indicator (*)
  - [ ] Cache status indicator
  
- [ ] Improved workflows
  - [ ] Drag-and-drop import
  - [ ] Quick actions menu
  - [ ] Keyboard shortcuts
  
- [ ] User preferences
  - [ ] Default cache duration
  - [ ] Auto-cleanup settings
  - [ ] Import preferences

**Deliverables:**
- Updated UI elements
- Preferences panel
- User documentation

---

## User Workflows

### Workflow 1: Fetch & Preview External Pathway

```
1. User clicks "Pathways" button
2. Opens KEGG Import tab
3. Enters pathway ID (e.g., "hsa00010")
4. Clicks "Fetch"
   → Data stored in models/pathway/external/kegg/
   → Preview shown with "KEGG" badge
5. User reviews pathway structure
6. Options:
   a) "Import to Project" → Proceeds to Workflow 2
   b) "Close" → Data remains in cache (temporary)
```

**Key Points:**
- ⚠️ Preview clearly shows "External Data - Not in Project"
- 📊 User can explore structure without committing
- 🗑️ Cache auto-cleaned after 30 days

---

### Workflow 2: Import to Project

```
1. User clicks "Import to Project" from preview
2. Dialog appears:
   - Original source: KEGG hsa00010 (Glycolysis)
   - Import as: [text field: "Glycolysis_Human"]
   - Add tags: [metabolism, core-pathway]
   - Notes: [text area]
3. User clicks "Import"
   → Creates data/projects/[current]/pathways/Glycolysis_Human.shypn
   → Loads into canvas for editing
   → Shows "Local" badge (imported from KEGG)
4. User can now modify freely
```

**Key Points:**
- ✅ Clear transition from external → project
- 📝 Preserved metadata for reference
- 🔓 User has full ownership

---

### Workflow 3: Modify Project Pathway

```
1. User loads project pathway
2. Makes edits (add places, transitions, etc.)
3. Pathway marked as modified (*)
4. User saves:
   - Save → Updates .shypn file
   - Save As → Creates new project pathway
   - Export → Exports to various formats
```

**Key Points:**
- 💾 Changes persist in project
- 🔄 Version tracking
- 📤 Export flexibility

---

### Workflow 4: Sync with External Source

```
1. User opens project pathway (originally from KEGG)
2. Menu: "Pathway" → "Check for Updates"
3. System:
   - Fetches latest from KEGG API
   - Compares with project pathway
   - Shows diff:
     • New reactions: 3
     • Modified compounds: 2
     • Deleted entries: 1
4. User chooses strategy:
   a) "Keep My Changes" → No update
   b) "Update from KEGG" → Overwrites local
   c) "Review & Merge" → Manual merge UI
```

**Key Points:**
- 🔍 User stays aware of external changes
- ⚙️ Flexible merge strategies
- 🛡️ Prevents accidental data loss

---

## Technical Considerations

### 1. Cache Management

```python
# Cache configuration
CACHE_CONFIG = {
    'max_age_days': 30,          # Auto-delete after 30 days
    'max_size_mb': 100,          # Max 100 MB cache
    'cleanup_interval': 'daily',  # Run cleanup daily
    'compression': True,          # Compress cached data
}

# Cache cleanup policy
def cleanup_cache():
    - Remove entries older than max_age_days
    - If cache > max_size_mb, remove oldest first
    - Keep cache_index.json updated
    - Log cleanup actions
```

### 2. Data Integrity

```python
# Checksums for external data
class ExternalPathway:
    checksum: str  # SHA256 of raw data
    
    def validate(self) -> bool:
        """Verify data integrity"""
        current = sha256(self.raw_data)
        return current == self.checksum

# Validation on load
def load_external_pathway(path: Path) -> ExternalPathway:
    pathway = deserialize(path)
    if not pathway.validate():
        # Re-fetch from source or warn user
        raise DataCorruptionError()
    return pathway
```

### 3. Backward Compatibility

```python
# Migration from old format
def migrate_legacy_pathway(old_doc: DocumentModel) -> ProjectPathway:
    """Convert old document format to new project pathway"""
    return ProjectPathway(
        pathway_id=str(uuid.uuid4()),
        name="Migrated Pathway",
        source_type="migrated",
        original_source="legacy",
        import_date=datetime.now(),
        document_model=old_doc,
        external_metadata={},
    )
```

### 4. Performance Optimization

- **Lazy Loading**: Load pathway data only when needed
- **Caching**: Keep frequently accessed pathways in memory
- **Indexing**: Fast lookup by ID, name, tags
- **Compression**: Compress cached external data

---

## File Format Specification

### .shypn File Format (Project Pathway)

```json
{
  "format_version": "2.0",
  "pathway_type": "project",
  
  "identity": {
    "pathway_id": "uuid-here",
    "name": "Glycolysis_Human_Modified",
    "project_id": "project-uuid"
  },
  
  "provenance": {
    "source_type": "imported",
    "original_source": {
      "type": "kegg",
      "id": "hsa00010",
      "version": "2025-10-01",
      "fetch_date": "2025-10-08T10:30:00Z"
    },
    "import_date": "2025-10-08T10:35:00Z",
    "modified_date": "2025-10-08T14:20:00Z"
  },
  
  "metadata": {
    "user_notes": "Modified to include our lab's custom reactions",
    "tags": ["metabolism", "glycolysis", "lab-specific"],
    "external_metadata": {
      "kegg_title": "Glycolysis / Gluconeogenesis",
      "kegg_organism": "Homo sapiens",
      "kegg_description": "..."
    }
  },
  
  "version": {
    "version_number": 3,
    "parent_version": "uuid-of-v2"
  },
  
  "document_model": {
    "places": [...],
    "transitions": [...],
    "arcs": [...]
  }
}
```

---

## Benefits of This Architecture

### For Users:
✅ **Clear Data Ownership** - Know what's external vs. local
✅ **Safe Experimentation** - Preview before importing
✅ **Preserved Provenance** - Always know data origin
✅ **Flexible Workflows** - Import, edit, sync as needed
✅ **No Accidental Loss** - Project data protected from cache cleanup

### For Developers:
✅ **Separation of Concerns** - Clear boundaries between modules
✅ **Testability** - Easy to mock external sources
✅ **Maintainability** - Logical organization
✅ **Extensibility** - Easy to add new external sources (Reactome, etc.)
✅ **Performance** - Efficient caching and loading

### For Data Management:
✅ **Version Control Ready** - Project pathways can be in git
✅ **Reproducibility** - Know exact source and version
✅ **Audit Trail** - Complete history of modifications
✅ **Backup/Restore** - Clear what needs backing up

---

## Migration Strategy

### For Existing Users:

1. **Detect Legacy Format**
   ```python
   if not has_provenance_metadata(doc):
       # This is a legacy document
       migrate_to_project_pathway(doc)
   ```

2. **Auto-Migration**
   - On first load, detect legacy pathways
   - Prompt user: "Would you like to migrate to new format?"
   - Create project pathway with "migrated" source type
   - Keep backup of original

3. **Gradual Adoption**
   - Old format still works (read-only)
   - New features require new format
   - User chooses when to migrate

---

## Testing Strategy

### Unit Tests:
- [ ] ExternalPathway serialization/deserialization
- [ ] ProjectPathway serialization/deserialization
- [ ] Cache management (add, get, cleanup)
- [ ] Data validation and checksums

### Integration Tests:
- [ ] Complete fetch → preview → import workflow
- [ ] Project save/load with pathways
- [ ] Cache expiration and cleanup
- [ ] Migration from legacy format

### E2E Tests:
- [ ] User imports KEGG pathway
- [ ] User modifies and saves
- [ ] User syncs with updated KEGG data
- [ ] User exports to various formats

---

## Documentation Requirements

### User Documentation:
- [ ] "Understanding Pathway Data Sources" guide
- [ ] "Importing from KEGG" tutorial
- [ ] "Managing Project Pathways" guide
- [ ] "Syncing with External Sources" how-to

### Developer Documentation:
- [ ] Data model architecture
- [ ] Cache management API
- [ ] Adding new external sources (extension guide)
- [ ] File format specification

---

## Open Questions / Decisions Needed

1. **Cache Location**: Use XDG dirs or project-relative?
   - Proposal: `~/.cache/shypn/pathways/` for user cache
   - Proposal: `data/cache/` for project-specific cache

2. **Sync Frequency**: How often to check for updates?
   - Proposal: Manual only (user-initiated)
   - Alternative: Weekly auto-check with notification

3. **Conflict Resolution**: Default merge strategy?
   - Proposal: Always ask user
   - Alternative: Configurable preference

4. **Cache Size Limit**: What's reasonable?
   - Proposal: 100 MB default, configurable
   - For reference: ~1000 pathways ≈ 50 MB

5. **Version Control**: Include external metadata in git?
   - Proposal: Yes, but compress for large metadata
   - Store checksums for verification

---

## Next Steps

### Immediate (This Session):
1. Review and approve this plan
2. Create directory structure
3. Start implementing Phase 1 (Data Structure Setup)

### This Week:
- Complete Phases 1-2 (Data models + KEGG integration)
- Test basic fetch → cache → import workflow
- Update documentation

### Next Week:
- Complete Phases 3-4 (Project management + sync)
- User testing and feedback
- Refine workflows based on usage

---

## Success Criteria

✅ User can fetch KEGG pathway without cluttering project
✅ Clear visual distinction between external and project data
✅ User can import, edit, and save project pathways
✅ Cache automatically cleaned to prevent bloat
✅ Provenance always preserved and visible
✅ Sync with external source works reliably
✅ No data loss during any operation
✅ Performance is acceptable (< 1s for most operations)

---

**Status**: 📋 READY FOR REVIEW
**Priority**: 🔴 HIGH (Foundation for pathway editing features)
**Estimated Effort**: 6 days (1 developer)
**Dependencies**: None (can start immediately)
