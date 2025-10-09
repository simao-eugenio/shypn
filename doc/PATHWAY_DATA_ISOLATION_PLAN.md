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
workspace/examples/models/
├── pathway/
│   ├── external/          # NEW - Transient external data (NOT user-owned)
│   │   ├── kegg/          # KEGG-fetched pathways (temporary cache)
│   │   │   ├── hsa00010.xml      # Raw KGML from KEGG
│   │   │   ├── hsa00010.json     # Parsed pathway metadata
│   │   │   └── cache_index.json  # Cache management
│   │   │
│   │   └── reactome/      # Future: Other pathway databases
│   │
│   └── templates/         # NEW - Application-provided templates
│       ├── basic_metabolism.shy
│       └── signaling_cascade.shy
│
data/
├── projects/              # NEW - Local project management
│   ├── project_index.json       # Registry of all local projects
│   ├── recent_projects.json     # Recently opened projects
│   │
│   └── [project_id]/            # Individual project directory
│       ├── project.shy          # Main project file (metadata)
│       ├── workspace/examples/models/              # Petri net models in this project
│       │   ├── model1.shy       # Individual model files
│       │   ├── model2.shy
│       │   └── model_index.json
│       │
│       ├── pathways/            # Imported/edited pathways
│       │   ├── glycolysis.shy   # Pathway converted to Petri net
│       │   ├── signaling.shy
│       │   └── pathway_index.json
│       │
│       ├── simulations/         # Simulation results & configs
│       │   ├── sim1.json
│       │   └── sim2.json
│       │
│       ├── exports/             # Exported files
│       │   ├── model1.pnml
│       │   └── pathway1.svg
│       │
│       └── metadata/            # Project-level metadata
│           ├── settings.json    # Project settings
│           ├── history.json     # Edit history
│           └── tags.json        # User-defined tags
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
[Cache] → workspace/cache/kegg/hsa00010.json
    ↓
[Preview UI] → User reviews pathway
    ↓
Decision Point: Import or Discard?
```

**Characteristics:**
- ✅ Stored in `workspace/cache/kegg/`
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
[External Data] → workspace/cache/kegg/hsa00010.json
    ↓
[Converter] → Creates ProjectPathway object
    ↓
[User Edits] → Modifications applied
    ↓
[Save] → workspace/projects/[project_id]/pathways/glycolysis_v1.shy
    ↓
[Project Registry] → Links pathway to project
```

**Characteristics:**
- ✅ Stored in `workspace/projects/[project_id]/pathways/`
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
    cache_path: Path          # workspace/cache/kegg/hsa00010.json
    
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
    file_path: Path           # workspace/projects/[project_id]/pathways/name.shy
    
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
    
    cache_dir: Path           # workspace/cache/
    max_age_days: int         # Default: 30 days
    max_size_mb: int          # Default: 100 MB
    
    def get(self, source: str, external_id: str) -> Optional[ExternalPathway]
    def store(self, pathway: ExternalPathway) -> bool
    def cleanup_expired(self) -> int
    def clear_source(self, source: str) -> bool
    def get_cache_info(self) -> CacheInfo
```

### 4. Project (Local Project Management)

```python
class Project:
    """Represents a local shypn project"""
    
    # Identity
    project_id: str           # UUID for this project
    name: str                 # User-defined project name
    description: str          # Project description
    
    # Location
    project_dir: Path         # workspace/projects/[project_id]/
    project_file: Path        # workspace/projects/[project_id]/project.shy
    
    # Metadata
    created_date: datetime
    modified_date: datetime
    author: str               # User name
    tags: List[str]           # Project tags
    
    # Content
    models: List[str]         # List of model file paths
    pathways: List[str]       # List of pathway file paths
    simulations: List[str]    # List of simulation configs
    
    # Settings
    settings: Dict            # Project-specific settings
    last_opened: datetime     # Last access time
    
    # Methods
    def save(self) -> bool
    def load(cls, project_path: Path) -> 'Project'
    def add_model(self, model: DocumentModel, name: str) -> str
    def add_pathway(self, pathway: ProjectPathway) -> bool
    def remove_model(self, model_id: str) -> bool
    def remove_pathway(self, pathway_id: str) -> bool
    def export_project(self, export_path: Path) -> bool
    def get_all_models(self) -> List[DocumentModel]
    def get_all_pathways(self) -> List[ProjectPathway]
```

### 5. ProjectManager (Global Project Management)

```python
class ProjectManager:
    """Manages all local projects"""
    
    # Configuration
    projects_root: Path       # workspace/projects/
    index_file: Path          # workspace/projects/project_index.json
    recent_projects_file: Path # workspace/projects/recent_projects.json
    
    # State
    current_project: Optional[Project]
    projects_index: Dict[str, ProjectInfo]  # All known projects
    recent_projects: List[str]              # Recent project IDs
    
    # Methods
    def create_project(self, name: str, description: str) -> Project
    def open_project(self, project_id: str) -> Project
    def close_project(self) -> bool
    def delete_project(self, project_id: str) -> bool
    def list_projects(self) -> List[ProjectInfo]
    def search_projects(self, query: str) -> List[ProjectInfo]
    def get_recent_projects(self, limit: int = 10) -> List[ProjectInfo]
    def import_project(self, archive_path: Path) -> Project
    def export_project(self, project_id: str, export_path: Path) -> bool
    def rebuild_index(self) -> bool
```

### 6. ModelDocument (Individual Petri Net Model)

```python
class ModelDocument:
    """Represents a single Petri net model file (.shy)"""
    
    # Identity
    model_id: str             # UUID for this model
    name: str                 # Model name
    project_id: str           # Parent project
    
    # Metadata
    created_date: datetime
    modified_date: datetime
    model_type: str           # "petri_net", "timed_petri_net", "stochastic"
    description: str
    tags: List[str]
    
    # Data
    document_model: DocumentModel  # The actual Petri net
    file_path: Path           # workspace/projects/[project_id]/workspace/examples/models/name.shy
    
    # Analysis results
    analysis_cache: Dict      # Cached analysis results
    
    # Methods
    def save(self) -> bool
    def load(cls, file_path: Path) -> 'ModelDocument'
    def export(self, format: str, output_path: Path) -> bool
    def duplicate(self, new_name: str) -> 'ModelDocument'
    def get_statistics(self) -> ModelStats
```


---

## Implementation Phases

### Phase 1: Data Structure Setup (Days 1-2)
**Priority: HIGH**

- [ ] Create directory structure
  - [ ] `workspace/cache/kegg/`
  - [ ] `workspace/examples/templates/`
  - [ ] `workspace/projects/` (root)
  - [ ] `data/cache/kegg/`
  
- [ ] Implement data model classes
  - [ ] `ExternalPathway` class
  - [ ] `ProjectPathway` class
  - [ ] `PathwayCache` class
  - [ ] `Project` class (NEW)
  - [ ] `ProjectManager` class (NEW)
  - [ ] `ModelDocument` class (NEW)
  
- [ ] Create cache management
  - [ ] Cache index file
  - [ ] Auto-cleanup policy
  - [ ] Cache statistics

- [ ] Create project management (NEW)
  - [ ] Project index system
  - [ ] Recent projects tracking
  - [ ] Project creation/loading logic

**Deliverables:**
- `src/shypn/workspace/examples/models/pathway_models.py`
- `src/shypn/workspace/examples/models/pathway_cache.py`
- `src/shypn/workspace/examples/models/project_manager.py` (NEW)
- `src/shypn/workspace/examples/models/model_document.py` (NEW)
- Cache and project directory structure

---

### Phase 2: File Format & Serialization (Days 3-4)
**Priority: HIGH**

- [ ] Define `.shy` file format specification
  - [ ] Project file format (`project.shy`)
  - [ ] Model file format (`model.shy`)
  - [ ] Pathway file format (`pathway.shy`)
  - [ ] Template file format (`template.shy`)
  
- [ ] Implement serialization
  - [ ] JSON serialization/deserialization
  - [ ] Validation schemas
  - [ ] Migration from old formats
  - [ ] Compression support (optional)
  
- [ ] Update existing save/load
  - [ ] Migrate current DocumentModel to `.shy`
  - [ ] Backward compatibility layer
  - [ ] Test migration paths

**Deliverables:**
- `.shy` format specification document
- `src/shypn/file/shy_format.py`
- `src/shypn/file/shy_serializer.py`
- `src/shypn/file/format_migration.py`
- Unit tests for serialization

---

### Phase 3: Project Management UI (Days 5-6)
**Priority: HIGH**

- [ ] Extend Left Panel (File Explorer) with Project Management
  - [ ] Add "Project Actions" section below tree view
  - [ ] Add "New Project" button
  - [ ] Add "Open Project" button  
  - [ ] Add "Project Settings" button
  - [ ] Add horizontal separator
  - [ ] Add "Quit" button at bottom
  - [ ] Update tree view to show project structure
  
- [ ] Create project management dialogs
  - [ ] New Project dialog (name, location, template)
  - [ ] Open Project dialog (recent, browse, import archive)
  - [ ] Project Properties dialog (metadata, settings)
  
- [ ] Enhance File Browser Tree View
  - [ ] Show project root node with project name
  - [ ] Hierarchical display: Models / Pathways / Simulations
  - [ ] Visual indicators (icons, badges)
  - [ ] Context menus for project items
  - [ ] Drag-and-drop support
  
- [ ] Implement project operations
  - [ ] Create project (with templates)
  - [ ] Open/close project (with recent list)
  - [ ] Save project state
  - [ ] Export/import project archive
  - [ ] Switch between projects
  - [ ] Application quit with save prompt

**Deliverables:**
- `ui/panels/left_panel.ui` (updated with project buttons)
- `ui/dialogs/project_dialogs.ui` (new dialogs)
- `src/shypn/helpers/left_panel_loader.py` (updated)
- `src/shypn/helpers/project_dialog_manager.py` (new)
- `src/shypn/workspace/examples/models/project_manager.py` (new)

**UI Layout Design:**
```
┌─────────────────────────────┐
│ File Explorer          [⇱]  │  ← Panel Header
├─────────────────────────────┤
│ New Open Save Save As... │  ← File Operations
│ New Folder               │
├─────────────────────────────┤
│ Home | ◀ [path] ▶ Refresh │  ← Navigation
├─────────────────────────────┤
│ 📁 My Project           │  ← Tree View
│  ├─ 📁 Models           │     (expandable)
│  │   ├─ 📄 model1.shy   │
│  │   └─ 📄 model2.shy   │
│  ├─ 📁 Pathways         │
│  │   └─ 📄 hsa00010.shy │
│  └─ 📁 Simulations      │
│      └─ 📄 sim1.json    │
│                         │
│  ... (scrollable)       │
│                         │
├─────────────────────────────┤
│ ┌─ Project Actions ───┐ │  ← NEW: Project Section
│ │ [New Project]        │ │
│ │ [Open Project]       │ │
│ │ [Project Settings]   │ │
│ └─────────────────────┘ │
├─────────────────────────────┤
│ [Quit Application]       │  ← NEW: Quit Button
├─────────────────────────────┤
│ Ready                    │  ← Status Bar
└─────────────────────────────┘
```

---

### Phase 4: KEGG Integration Update (Days 7-8)
**Priority: HIGH**

- [ ] Modify KEGG importer to use ExternalPathway
  - [ ] Store fetched data in cache
  - [ ] Mark as transient/external
  - [ ] Add metadata tracking
  
- [ ] Update preview UI
  - [ ] Show data source indicator
  - [ ] Show cache status
  - [ ] Add "Import to Current Project" button
  
- [ ] Implement import workflow
  - [ ] Convert ExternalPathway → ProjectPathway
  - [ ] Prompt for project pathway name
  - [ ] Save to current project's pathways/
  - [ ] Link to project index

**Deliverables:**
- Updated `kegg_import_panel.py`
- New `pathway_importer.py`
- Import workflow UI updates
- Project-aware import logic

---

### Phase 5: Project Pathway Management (Days 9-10)
**Priority: MEDIUM**

- [ ] Enhance pathway operations
  - [ ] Load project pathway
  - [ ] Save modifications
  - [ ] Export to various formats
  - [ ] Delete pathway
  - [ ] Rename/move pathway
  
- [ ] Add metadata editor
  - [ ] Edit user notes
  - [ ] Add/remove tags
  - [ ] View original source metadata
  - [ ] Edit provenance info
  
- [ ] Integrate with Project Explorer
  - [ ] Show pathways in tree view
  - [ ] Visual indicators (KEGG badge, etc.)
  - [ ] Quick actions menu

**Deliverables:**
- `pathway_operations.py`
- Metadata editor UI
- Project Explorer integration
- Context menu actions

---

### Phase 6: Data Provenance & Sync (Days 11-12)
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
- Conflict resolution dialog

---

### Phase 7: Project Backup & Archive (Days 13-14)
**Priority: MEDIUM**

- [ ] Implement project export
  - [ ] Create .zip archive
  - [ ] Include all project files
  - [ ] Add manifest file
  - [ ] Compression
  
- [ ] Implement project import
  - [ ] Extract archive
  - [ ] Validate structure
  - [ ] Resolve conflicts (existing project)
  - [ ] Import into projects directory
  
- [ ] Add automatic backup
  - [ ] Configurable backup schedule
  - [ ] Timestamped backups
  - [ ] Cleanup old backups
  - [ ] Backup restore

**Deliverables:**
- `project_archiver.py`
- Backup manager
- Import/export dialogs
- Backup preferences

---

### Phase 8: UI/UX Polish & Integration (Days 15-16)
**Priority: LOW**

- [ ] Visual indicators throughout UI
  - [ ] Source badges (KEGG logo, "Local", etc.)
  - [ ] Modified indicator (*)
  - [ ] Cache status indicator
  - [ ] Project indicator in title bar
  
- [ ] Improved workflows
  - [ ] Drag-and-drop import
  - [ ] Quick actions menu
  - [ ] Keyboard shortcuts
  - [ ] Welcome screen with recent projects
  
- [ ] User preferences
  - [ ] Default cache duration
  - [ ] Auto-cleanup settings
  - [ ] Import preferences
  - [ ] Project preferences
  
- [ ] Integration testing
  - [ ] Complete workflow tests
  - [ ] Performance testing
  - [ ] User acceptance testing

**Deliverables:**
- Updated UI elements
- Preferences panel
- Welcome screen
- Integration tests
- User documentation

---

## User Workflows

### Workflow 1: Fetch & Preview External Pathway

```
1. User clicks "Pathways" button
2. Opens KEGG Import tab
3. Enters pathway ID (e.g., "hsa00010")
4. Clicks "Fetch"
   → Data stored in workspace/cache/kegg/
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
   → Creates workspace/projects/[current]/pathways/Glycolysis_Human.shypn
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

## Local Project Management Workflows

### Workflow 5: Create New Project
**User Goal:** Start a new shypn project with proper structure

**Steps:**
1. **Click "New Project" button** in File Explorer panel (below tree view)
   ```
   [File Explorer Panel]
   ├─ Tree View (shows current project)
   ├─────────────────────
   │ Project Actions    │
   │ [New Project]  ←── Click here
   │ [Open Project]     │
   │ [Project Settings] │
   ```

2. **Fill New Project Dialog:**
   - Project Name: `"My Pathway Analysis"`
   - Location: `~/Documents/shypn-projects/`
   - Template: `[Empty Project | Basic Petri Net | KEGG Import Template]`
   - Click "Create"

3. **System Actions:**
   - Creates `workspace/projects/[uuid]/` directory structure
   - Generates `project.shy` with metadata
   - Creates subdirectories: `workspace/examples/models/`, `pathways/`, `simulations/`, `exports/`, `metadata/`
   - Updates `project_index.json`
   - Adds to `recent_projects.json`
   - Loads project into File Explorer tree view

4. **Result:** File Explorer now shows:
   ```
   📁 My Pathway Analysis  ← New project loaded
    ├─ 📁 Models
    ├─ 📁 Pathways
    └─ 📁 Simulations
   ```

**Key Points:**
- 🎯 Projects are **UUID-based** but displayed with friendly names
- 📁 Directory structure is **created automatically**
- 🔄 Tree view updates to show new project immediately
- 💾 Recent projects list updated for quick access

---

### Workflow 6: Open Existing Project
**User Goal:** Switch to a different project or open archived project

**Steps:**
1. **Click "Open Project" button** in File Explorer panel
   ```
   [File Explorer Panel]
   ├─ Tree View
   ├─────────────────────
   │ Project Actions    │
   │ [New Project]      │
   │ [Open Project] ←── Click here
   │ [Project Settings] │
   ```

2. **Choose from Open Project Dialog:**
   
   **Option A: Recent Projects Tab**
   - Shows list of recently opened projects
   - Display: Name, Path, Last Modified
   - Click project → Click "Open"
   
   **Option B: Browse Tab**
   - Browse to `workspace/projects/[project_id]/project.shy`
   - Select file → Click "Open"
   
   **Option C: Import Archive Tab**
   - Select `.zip` archive created by "Export Project"
   - Choose import location
   - Click "Import & Open"

3. **System Actions:**
   - Saves current project state (if any)
   - Loads selected `project.shy`
   - Parses project structure
   - Updates File Explorer tree view
   - Restores workspace state (open files, scroll positions)
   - Updates recent projects list

4. **Result:** File Explorer shows selected project structure

**Key Points:**
- 💾 Current project is **auto-saved** before switching
- 🔄 Recent projects provide **quick access**
- 📦 Can import archived projects from `.zip`
- 🎯 Tree view updates with new project content

---

### Workflow 7: Manage Project Content via File Explorer
**User Goal:** Navigate and manage project files using tree view

**Steps:**
1. **Navigate Project in Tree View:**
   ```
   📁 My Project
    ├─ 📁 Models          ← Right-click for context menu
    │   ├─ 📄 model1.shy  ← Double-click to open
    │   └─ 📄 model2.shy  ← Right-click for actions
    ├─ 📁 Pathways
    │   └─ 📄 hsa00010.shy (KEGG) ← Badge shows source
    └─ 📁 Simulations
        └─ 📄 result1.json
   ```

2. **Context Menu Actions:**
   
   **On Folders (Models/Pathways/Simulations):**
   - New Model / New Pathway
   - Import File...
   - Paste (if copied)
   - Refresh
   
   **On Files:**
   - Open
   - Open in New Tab
   - Rename
   - Duplicate
   - Export...
   - Delete
   - Properties (shows metadata)

3. **Drag-and-Drop Operations:**
   - Drag `.shy` file from external location → Import to project
   - Drag file between folders (Models ↔ Pathways)
   - Drag to reorder (within same folder)

4. **Tree View Features:**
   - **Icons:** File type indicators (📄 .shy, 📊 .json, etc.)
   - **Badges:** Data source (🔵 KEGG, 🟢 Local, 🟡 Modified)
   - **Expand/Collapse:** Click folder arrows
   - **Search:** Filter tree view by name

**Key Points:**
- 🎯 **Single source of truth** - All project content in one tree
- 🖱️ **Context-aware** - Right-click menus adapt to item type
- 🔄 **Live updates** - Tree refreshes when files change
- 📁 **Hierarchical** - Clear organization by content type

---

### Workflow 8: Add Model to Project
**User Goal:** Create or import a Petri net model

**Steps:**
1. **Right-click "Models" folder** in tree view
   ```
   📁 Models ← Right-click here
     Context Menu:
     ─────────────────
     • New Model...
     • Import Model...
     • From Template...
     • Paste
   ```

2. **Choose Creation Method:**
   
   **Option A: New Model**
   - Click "New Model..."
   - Enter name: `"Glycolysis Model"`
   - System creates empty `glycolysis_model.shy` in `workspace/examples/models/`
   - Opens in canvas for editing
   
   **Option B: Import Model**
   - Click "Import Model..."
   - Select external `.shy` file
   - System copies to `workspace/examples/models/`
   - Adds to project index
   
   **Option C: From Template**
   - Click "From Template..."
   - Choose template (e.g., "Basic Pathway", "Regulatory Network")
   - Customize name
   - System creates model from template

3. **System Actions:**
   - Creates/copies `.shy` file to `workspace/projects/[project_id]/workspace/examples/models/`
   - Updates `project.shy` content registry
   - Adds to tree view under "Models"
   - Opens in canvas (if requested)

4. **Result:** Tree view shows new model
   ```
   📁 Models
    ├─ 📄 glycolysis_model.shy ← New model
    └─ 📄 model2.shy
   ```

**Key Points:**
- 🆕 **Three ways to add**: New, Import, Template
- 📁 **Auto-organized** - Models go to `workspace/examples/models/` folder
- 🔗 **Linked to project** - Added to content registry
- 🖊️ **Ready to edit** - Opens in canvas immediately

---

### Workflow 9: Project Export/Backup
**User Goal:** Create portable archive or backup of project

**Steps:**
1. **Click "Project Settings" button** in File Explorer panel
   ```
   [File Explorer Panel]
   ├─ Tree View
   ├─────────────────────
   │ Project Actions    │
   │ [New Project]      │
   │ [Open Project]     │
   │ [Project Settings] ←── Click here
   ```

2. **In Project Properties Dialog, choose action:**
   
   **Option A: Export Project Archive**
   - Click "Export..." tab
   - Choose export options:
     - ✅ Include all models
     - ✅ Include pathways
     - ✅ Include simulation results
     - ✅ Compress archive
   - Choose destination: `~/Desktop/my_project_export.zip`
   - Click "Export"
   
   **Option B: Backup Project**
   - Click "Backup" tab
   - Automatic backup settings:
     - Backup frequency: [Daily | Weekly | Manual]
     - Keep last N backups: `5`
     - Backup location: `workspace/projects/[project_id]/metadata/backups/`
   - Click "Backup Now"
   
   **Option C: Export Individual Items**
   - Right-click file in tree view
   - Click "Export..."
   - Choose format (for models: .shy, .pnml, .svg, .png)
   - Save to location

3. **System Actions:**
   - Creates `.zip` archive with manifest
   - Includes all selected content
   - Timestamps export
   - Compresses if requested
   - Or creates timestamped backup in metadata folder

4. **Result:** Archive file created, ready to share or store

**Key Points:**
- 📦 **Portable archives** - Share entire project as `.zip`
- 🔄 **Automatic backups** - Configurable schedule
- 🗜️ **Compressed** - Saves disk space
- 📋 **Selective export** - Choose what to include

---

### Workflow 10: Application Quit with Project Save
**User Goal:** Exit application safely with unsaved changes

**Steps:**
1. **Click "Quit" button** in File Explorer panel (bottom)
   ```
   [File Explorer Panel]
   ├─ Tree View
   ├─────────────────────
   │ Project Actions    │
   │ [New Project]      │
   │ [Open Project]     │
   │ [Project Settings] │
   ├─────────────────────
   │ [Quit Application] ←── Click here
   ├─────────────────────
   │ Ready              │
   ```
   
   **Or:** Close main window with X button

2. **If Unsaved Changes Exist:**
   
   **System shows dialog:**
   ```
   ┌──────────────────────────────┐
   │  Unsaved Changes             │
   ├──────────────────────────────┤
   │ You have unsaved changes in: │
   │  • model1.shy                │
   │  • pathway_edit.shy          │
   │                              │
   │ What would you like to do?   │
   │                              │
   │ [Save & Quit] [Quit Anyway]  │
   │             [Cancel]         │
   └──────────────────────────────┘
   ```

3. **Choose Action:**
   - **Save & Quit:** Saves all modified files, then exits
   - **Quit Anyway:** Discards changes, exits immediately
   - **Cancel:** Returns to application

4. **System Actions (if saving):**
   - Saves all modified `.shy` files
   - Updates `project.shy` metadata
   - Saves workspace state (open files, positions)
   - Writes to `recent_projects.json`
   - Gracefully closes application

5. **Result:** Application exits, project state preserved

**Key Points:**
- 💾 **Unsaved change detection** - Never lose work
- 🚪 **Two quit methods** - Button or window close
- 🔒 **Safe exit** - Prompts before discarding changes
- 🔄 **State preservation** - Restores session next time

---

## File Format Specifications

### Workflow 8: Add Model to Project

```
1. User clicks "+" button in Models section
2. Options appear:
   a) Create New Model
      - Opens blank canvas
      - Prompts for name
   b) Import from File
      - Selects .shy or other format
   c) From Template
      - Chooses template
3. Model created/imported
   → Saved in workspace/projects/[id]/workspace/examples/models/
   → Added to project.shy index
   → Opened in canvas
```

**Key Points:**
- 🆕 Easy model creation
- 📥 Import existing work
- 📋 Templates for common patterns

---

### Workflow 9: Project Export/Backup

```
1. User clicks "File" → "Export Project"
2. Options:
   - Export as Archive (.zip)
     • Includes all models, pathways, simulations
     • Includes project metadata
     • Can share with collaborators
   
   - Export Individual Models
     • Select models to export
     • Choose format (.shy, .pnml, .svg, etc.)
   
   - Backup Project
     • Creates timestamped backup
     • Saved to backups/ directory
3. Export created
   → User can share or archive
```

**Key Points:**
- 📤 Share complete projects
- 💾 Regular backups recommended
- 🔄 Multiple export formats

---

### Workflow 10: Switch Between Projects

```
1. User working in Project A
2. Clicks "File" → "Switch Project"
3. Options:
   a) Recent Projects list
   b) Open Another Project
   c) Create New Project
4. User selects Project B
   → Project A closes (prompts to save)
   → Project B opens
   → Workspace restored to last state
```

**Key Points:**
- 🔄 Smooth project switching
- 💾 Auto-save prompts
- 📍 Workspace state preserved

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

### .shy File Format (Universal shypn Document)

All shypn documents use the `.shy` extension, with the content type differentiated by metadata:

#### 1. Project File (`project.shy`)

```json
{
  "format_version": "2.0",
  "document_type": "project",
  
  "identity": {
    "project_id": "uuid-here",
    "name": "My Research Project",
    "description": "Metabolic pathway analysis for XYZ"
  },
  
  "metadata": {
    "created_date": "2025-10-08T09:00:00Z",
    "modified_date": "2025-10-08T15:30:00Z",
    "author": "Researcher Name",
    "tags": ["metabolism", "research", "2025"]
  },
  
  "content": {
    "models": [
      {
        "model_id": "uuid-1",
        "name": "Main Model",
        "file_path": "workspace/examples/models/main_model.shy",
        "model_type": "petri_net"
      }
    ],
    "pathways": [
      {
        "pathway_id": "uuid-2",
        "name": "Glycolysis",
        "file_path": "pathways/glycolysis.shy",
        "source": "imported_from_kegg"
      }
    ],
    "simulations": [
      {
        "simulation_id": "uuid-3",
        "name": "Baseline Simulation",
        "file_path": "simulations/baseline.json"
      }
    ]
  },
  
  "settings": {
    "default_view": "model_id:uuid-1",
    "analysis_preferences": {},
    "export_preferences": {}
  }
}
```

#### 2. Model File (`model.shy`)

```json
{
  "format_version": "2.0",
  "document_type": "model",
  
  "identity": {
    "model_id": "uuid-here",
    "name": "Main Metabolic Model",
    "project_id": "uuid-of-project"
  },
  
  "metadata": {
    "created_date": "2025-10-08T10:00:00Z",
    "modified_date": "2025-10-08T14:20:00Z",
    "model_type": "petri_net",
    "description": "Core metabolic pathways",
    "tags": ["metabolism", "validated"]
  },
  
  "document_model": {
    "places": [
      {
        "id": 1,
        "name": "ATP",
        "tokens": 10,
        "x": 100,
        "y": 150,
        "properties": {}
      }
    ],
    "transitions": [
      {
        "id": 1,
        "name": "Reaction1",
        "x": 200,
        "y": 150,
        "transition_type": "immediate",
        "properties": {}
      }
    ],
    "arcs": [
      {
        "id": 1,
        "source_id": 1,
        "target_id": 1,
        "weight": 1,
        "kind": "normal",
        "properties": {}
      }
    ],
    "id_counters": {
      "next_place_id": 2,
      "next_transition_id": 2,
      "next_arc_id": 2
    }
  },
  
  "analysis_cache": {
    "last_analysis_date": "2025-10-08T14:00:00Z",
    "invariants": [],
    "reachability": {}
  }
}
```

#### 3. Pathway File (`pathway.shy`)

```json
{
  "format_version": "2.0",
  "document_type": "pathway",
  
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

#### 4. Template File (`template.shy`)

```json
{
  "format_version": "2.0",
  "document_type": "template",
  
  "identity": {
    "template_id": "uuid-here",
    "name": "Basic Metabolism Template"
  },
  
  "metadata": {
    "description": "Template for basic metabolic pathways",
    "category": "metabolism",
    "tags": ["template", "starter"],
    "author": "shypn",
    "created_date": "2025-10-01T00:00:00Z"
  },
  
  "document_model": {
    "places": [...],
    "transitions": [...],
    "arcs": [...]
  },
  
  "usage_instructions": "This template provides basic metabolic reactions..."
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
