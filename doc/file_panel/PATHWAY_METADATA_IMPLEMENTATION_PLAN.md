# Pathway Metadata Schema - Implementation Plan

## Overview

This plan implements the pathway-enrichment coupling system described in `PATHWAY_METADATA_SCHEMA.md`. The goal is to enable full traceability between imported pathways (KEGG/SBML), converted models, and enrichment data (BRENDA).

**Prerequisites:**
- FILE_PANEL_COMPLETION_PLAN.md Phase 1 & 2 (Project Information & Actions)
- Understanding of current import workflows (KEGG, SBML, BRENDA)

**Timeline:** ~6-9 days across 8 phases

---

## Phase 0: Preparation & Analysis (0.5 days)

**Goal:** Understand current codebase and validate design assumptions

### Tasks

- [ ] **Audit Current Import Flows**
  - [ ] Map KEGG import: `fetch_pathway` → `parse_kgml` → `convert_pathway`
  - [ ] Map SBML import: File chooser → SBML parser → converter
  - [ ] Map BRENDA enrichment: Query → Match transitions → Apply parameters
  - [ ] Identify where to inject PathwayDocument creation

- [ ] **Review Existing Metadata Systems**
  - [ ] Check `ModelDocument.analysis_cache` - can it be leveraged?
  - [ ] Review `transition.metadata` structure (BRENDA already uses this)
  - [ ] Check `MetadataEnhancer` class - how does it store metadata?
  - [ ] Identify metadata standards/conventions already in use

- [ ] **Validate Storage Assumptions**
  - [ ] Confirm `project.shy` uses JSON serialization
  - [ ] Verify `pathways/` directory creation strategy
  - [ ] Test file path handling (absolute vs relative)
  - [ ] Check if migration is needed (any existing projects?)

### Deliverables
- [ ] Document: `CURRENT_IMPORT_FLOW_ANALYSIS.md`
- [ ] List of files to modify (with line numbers)
- [ ] Potential conflicts or blockers identified

### Success Criteria
✅ Clear understanding of injection points for PathwayDocument
✅ No major architectural conflicts discovered
✅ Storage strategy validated

---

## Phase 1: Core Data Model (1-2 days)

**Goal:** Implement `PathwayDocument` and `EnrichmentDocument` classes

### Tasks

#### 1.1 Create Data Classes

- [ ] **Add PathwayDocument class** (`src/shypn/data/project_models.py`)
  ```python
  class PathwayDocument:
      """Represents an external pathway with metadata and enrichments."""
      def __init__(self, ...):
          self.id: str
          self.name: str
          self.source_type: str  # "kegg", "sbml"
          self.source_id: str
          self.source_organism: str
          self.raw_file: str
          self.metadata_file: str
          self.imported_date: str
          self.last_modified: str
          self.enrichments: List[EnrichmentDocument]
          self.model_id: Optional[str]
          self.tags: List[str]
          self.notes: str
      
      def to_dict(self) -> Dict[str, Any]:
          """Serialize to JSON-compatible dict."""
      
      @classmethod
      def from_dict(cls, data: Dict[str, Any]) -> 'PathwayDocument':
          """Deserialize from dict."""
  ```

- [ ] **Add EnrichmentDocument class** (`src/shypn/data/project_models.py`)
  ```python
  class EnrichmentDocument:
      """Represents enrichment data from external source."""
      def __init__(self, ...):
          self.id: str
          self.type: str  # "kinetics", "structural", "functional"
          self.source: str  # "brenda", "reactome", etc.
          self.source_query: Dict
          self.data_file: str
          self.applied_date: str
          self.transitions_enriched: List[str]
          self.parameters_added: Dict
          self.confidence: str  # "high", "medium", "low"
          self.citations: List[str]
      
      def to_dict(self) -> Dict[str, Any]:
          """Serialize to JSON-compatible dict."""
      
      @classmethod
      def from_dict(cls, data: Dict[str, Any]) -> 'EnrichmentDocument':
          """Deserialize from dict."""
  ```

#### 1.2 Update Project Class

- [ ] **Refactor Project.pathways** (`src/shypn/data/project_models.py`)
  ```python
  # OLD: self.pathways = []
  # NEW: self.pathways = {}  # pathway_id -> PathwayDocument
  ```

- [ ] **Add pathway management methods**
  - [ ] `add_pathway(pathway_doc: PathwayDocument) -> None`
  - [ ] `remove_pathway(pathway_id: str) -> None`
  - [ ] `get_pathway(pathway_id: str) -> Optional[PathwayDocument]`
  - [ ] `find_pathway_by_model_id(model_id: str) -> Optional[PathwayDocument]`
  - [ ] `find_pathways_by_source(source_type: str) -> List[PathwayDocument]`
  - [ ] `list_pathways() -> List[PathwayDocument]`

- [ ] **Add file operation helpers**
  - [ ] `save_pathway_file(filename: str, content: str) -> None`
  - [ ] `save_pathway_metadata(filename: str, metadata: Dict) -> None`
  - [ ] `save_enrichment_file(filename: str, data: Dict) -> None`
  - [ ] `load_pathway_file(filename: str) -> str`

#### 1.3 Update Serialization

- [ ] **Update Project.to_dict()**
  ```python
  'content': {
      'models': [...],
      'pathways': {
          pathway_id: pathway_doc.to_dict()
          for pathway_id, pathway_doc in self.pathways.items()
      },
      'simulations': [...]
  }
  ```

- [ ] **Update Project.from_dict()**
  ```python
  # Load pathways
  pathways_data = content.get('pathways', {})
  if isinstance(pathways_data, dict):  # New format
      for pathway_id, pathway_data in pathways_data.items():
          pathway_doc = PathwayDocument.from_dict(pathway_data)
          project.pathways[pathway_id] = pathway_doc
  elif isinstance(pathways_data, list):  # Old format - migrate
      project.pathways = project._migrate_pathways_v1(pathways_data)
  ```

- [ ] **Add migration function**
  ```python
  def _migrate_pathways_v1(self, old_pathways: List[str]) -> Dict[str, PathwayDocument]:
      """Migrate old flat list to new PathwayDocument structure."""
  ```

### Testing

- [ ] **Unit tests** (`tests/data/test_project_models.py`)
  - [ ] Test PathwayDocument creation and serialization
  - [ ] Test EnrichmentDocument creation and serialization
  - [ ] Test Project.add_pathway() / remove_pathway()
  - [ ] Test Project.find_pathway_by_model_id()
  - [ ] Test migration from old format
  - [ ] Test save/load cycle with pathways

### Deliverables
- [ ] `PathwayDocument` class implemented
- [ ] `EnrichmentDocument` class implemented
- [ ] `Project` class updated with pathway management
- [ ] Unit tests passing (>90% coverage)

### Success Criteria
✅ Can create PathwayDocument with full metadata
✅ Can serialize/deserialize to JSON
✅ Project.save() and Project.load() work with new structure
✅ Migration from old format works (if needed)

---

## Phase 2: KEGG Import Integration (1 day)

**Goal:** Make KEGG import create PathwayDocument and save raw data

### Tasks

#### 2.1 Update KEGG Import Panel

- [ ] **Modify KEGGPathwayPanel** (`src/shypn/ui/panels/pathways/kegg_pathway_panel.py`)
  - [ ] After successful fetch, create `PathwayDocument`
  - [ ] Extract metadata from `KEGGPathway` object
  - [ ] Save raw KGML file to `project.pathways/`
  - [ ] Save metadata JSON to `project.pathways/`
  - [ ] Register PathwayDocument with project
  - [ ] Update UI to show "saved to project" confirmation

#### 2.2 Create Metadata Extractor

- [ ] **Add KEGG metadata extractor** (`src/shypn/helpers/kegg_metadata.py`)
  ```python
  def extract_kegg_metadata(pathway: KEGGPathway) -> Dict[str, Any]:
      """Extract metadata from KEGG pathway.
      
      Returns:
          {
              'title': pathway.title,
              'organism': pathway.org,
              'pathway_id': pathway.name,
              'genes': [...],
              'compounds': [...],
              'reactions': [...],
              'entry_count': {...}
          }
      """
  ```

#### 2.3 Update Conversion Flow

- [ ] **Link PathwayDocument to ModelDocument**
  - [ ] When user clicks "Convert to Canvas", find PathwayDocument
  - [ ] After conversion, set `pathway_doc.model_id = model.id`
  - [ ] Save project to persist link

#### 2.4 Update Import Function Signature

- [ ] **Modify high-level import API** (if exists)
  ```python
  def import_kegg_pathway(project: Project, 
                          pathway_id: str,
                          organism: str = 'hsa',
                          convert_to_canvas: bool = False) -> PathwayDocument:
      """Import KEGG pathway and save to project.
      
      Args:
          project: Target project
          pathway_id: KEGG pathway ID (e.g., "00010")
          organism: Organism code (e.g., "hsa")
          convert_to_canvas: Immediately convert to model
          
      Returns:
          Created PathwayDocument
      """
  ```

### Testing

- [ ] **Integration tests** (`tests/integration/test_kegg_import_with_project.py`)
  - [ ] Test KEGG import saves PathwayDocument
  - [ ] Test raw KGML file is saved
  - [ ] Test metadata JSON is created
  - [ ] Test conversion links PathwayDocument to ModelDocument
  - [ ] Test Project.find_pathway_by_model_id() works after conversion

### Deliverables
- [ ] KEGG import creates and saves PathwayDocument
- [ ] Raw KGML files saved to project structure
- [ ] Metadata extraction working
- [ ] Integration tests passing

### Success Criteria
✅ Import KEGG pathway → PathwayDocument created
✅ Files saved: `hsa00010.kgml`, `hsa00010.meta.json`
✅ Project.pathways contains entry
✅ Conversion links pathway to model

---

## Phase 3: SBML Import Integration (1 day)

**Goal:** Make SBML import create PathwayDocument and save raw data

### Tasks

#### 3.1 Update SBML Import Panel

- [ ] **Modify SBMLImportPanel** (`src/shypn/ui/panels/pathways/sbml_panel.py` or similar)
  - [ ] After file selection, create `PathwayDocument`
  - [ ] Extract metadata from SBML file
  - [ ] Copy SBML file to `project.pathways/`
  - [ ] Save metadata JSON
  - [ ] Register PathwayDocument with project

#### 3.2 Create SBML Metadata Extractor

- [ ] **Add SBML metadata extractor** (`src/shypn/helpers/sbml_metadata.py`)
  ```python
  def extract_sbml_metadata(sbml_file: str) -> Dict[str, Any]:
      """Extract metadata from SBML file.
      
      Returns:
          {
              'model_name': ...,
              'model_id': ...,
              'species_count': ...,
              'reactions_count': ...,
              'compartments': [...],
              'annotations': {...}
          }
      """
  ```

#### 3.3 Handle File Copying

- [ ] **Implement safe file copy**
  - [ ] Copy SBML file to `project.pathways/`
  - [ ] Handle filename conflicts (append counter if needed)
  - [ ] Preserve original filename in PathwayDocument.source_id

#### 3.4 Update Import Flow

- [ ] **Track SBML source in PathwayDocument**
  ```python
  pathway_doc.source_type = "sbml"
  pathway_doc.source_id = original_filename  # "glycolysis.xml"
  pathway_doc.raw_file = copied_filename     # "glycolysis.sbml"
  ```

### Testing

- [ ] **Integration tests** (`tests/integration/test_sbml_import_with_project.py`)
  - [ ] Test SBML import saves PathwayDocument
  - [ ] Test SBML file is copied to project
  - [ ] Test metadata extraction
  - [ ] Test filename conflict handling

### Deliverables
- [ ] SBML import creates and saves PathwayDocument
- [ ] Raw SBML files copied to project structure
- [ ] Metadata extraction working

### Success Criteria
✅ Import SBML → PathwayDocument created
✅ Files saved: `glycolysis.sbml`, `glycolysis.meta.json`
✅ Project.pathways contains entry with source_type="sbml"

---

## Phase 4: BRENDA Enrichment Integration (1-2 days)

**Goal:** Make BRENDA enrichment create EnrichmentDocument and link to PathwayDocument

### Tasks

#### 4.1 Update BRENDA Enrichment Flow

- [ ] **Modify BRENDA enrichment logic** (find current implementation)
  - [ ] Before enrichment: Find PathwayDocument for active model
  - [ ] During enrichment: Track which transitions are enriched
  - [ ] After enrichment: Create EnrichmentDocument
  - [ ] Save BRENDA query results to file
  - [ ] Link EnrichmentDocument to PathwayDocument
  - [ ] Update project

#### 4.2 Create BRENDA Data Serializer

- [ ] **Add BRENDA result serializer** (`src/shypn/helpers/brenda_persistence.py`)
  ```python
  def serialize_brenda_results(results: List[BRENDAResult]) -> Dict[str, Any]:
      """Serialize BRENDA results to JSON-compatible format.
      
      Includes:
          - EC numbers queried
          - Organism
          - Kinetic parameters found (Km, kcat, Ki)
          - Citations (PubMed IDs)
          - Query timestamp
      """
  ```

#### 4.3 Track Enrichment Details

- [ ] **Capture enrichment metrics**
  ```python
  enrichment = EnrichmentDocument()
  enrichment.type = "kinetics"
  enrichment.source = "brenda"
  enrichment.source_query = {
      "ec_numbers": ["2.7.1.1", "2.7.1.11"],
      "organism": "Homo sapiens"
  }
  enrichment.transitions_enriched = ["R01_Hexokinase", "R02_PFK"]
  enrichment.parameters_added = {
      "km_values": 8,
      "kcat_values": 5,
      "ki_values": 2,
      "citations": 12
  }
  enrichment.confidence = "high"
  enrichment.citations = ["PMID:12345678", ...]
  ```

#### 4.4 Handle Models Without Source Pathway

- [ ] **Fallback for manual models**
  - [ ] If no PathwayDocument found for model, log warning
  - [ ] Still apply BRENDA enrichment to transitions
  - [ ] Store enrichment in ModelDocument.analysis_cache as fallback
  - [ ] UI shows "Enriched but not linked to pathway source"

#### 4.5 Update BRENDA Panel UI

- [ ] **Show enrichment status in panel**
  - [ ] Display linked PathwayDocument info
  - [ ] Show previous enrichments (if any)
  - [ ] Option to "Re-enrich" or "Update enrichment"

### Testing

- [ ] **Integration tests** (`tests/integration/test_brenda_enrichment_with_project.py`)
  - [ ] Test BRENDA enrichment creates EnrichmentDocument
  - [ ] Test enrichment data file is saved
  - [ ] Test PathwayDocument.enrichments list updated
  - [ ] Test enrichment on model without source pathway (fallback)
  - [ ] Test multiple enrichments on same pathway

### Deliverables
- [ ] BRENDA enrichment creates EnrichmentDocument
- [ ] Enrichment data saved to files
- [ ] PathwayDocument tracks enrichments

### Success Criteria
✅ BRENDA enrichment → EnrichmentDocument created
✅ File saved: `brenda_hsa00010_20251025.json`
✅ PathwayDocument.enrichments list contains entry
✅ Can trace: Model → Pathway → Enrichments

---

## Phase 5: File Panel UI Integration (1-2 days)

**Goal:** Display pathways and enrichments in File Panel

### Tasks

#### 5.1 Update Project Information Category

- [ ] **Display pathway statistics** (File Panel → Project Information)
  - [ ] "Pathways: 3 (2 KEGG, 1 SBML)"
  - [ ] "Enrichments: 2 (BRENDA)"
  - [ ] "Linked Models: 2 of 3 converted"

#### 5.2 Add Pathway List View

- [ ] **Create pathway list widget** (File Panel → new section)
  ```
  PATHWAYS
  ├── 📊 hsa00010 - Glycolysis (KEGG)
  │   ├── Imported: 2025-10-25 14:30
  │   ├── Model: Glycolysis_Model ✓
  │   └── Enrichments: BRENDA (high confidence)
  ├── 📊 hsa00020 - TCA Cycle (KEGG)
  │   ├── Imported: 2025-10-25 15:00
  │   └── Model: Not converted
  └── 📊 glycolysis_v2 (SBML)
      ├── Imported: 2025-10-25 16:00
      └── Model: Alternative_Model ✓
  ```

- [ ] **Add context menu**
  - [ ] "View Source" → Open raw KGML/SBML file
  - [ ] "View Metadata" → Show metadata JSON
  - [ ] "Convert to Canvas" → Convert pathway to model
  - [ ] "View Enrichments" → Show enrichment details
  - [ ] "Delete Pathway" → Remove pathway and files

#### 5.3 Add Enrichment Details Dialog

- [ ] **Create enrichment viewer**
  ```
  BRENDA Enrichment - hsa00010
  ══════════════════════════════════
  Applied: 2025-10-25 15:30:00
  Source: BRENDA Enzyme Database
  Query: EC 2.7.1.1, 2.7.1.11 (Homo sapiens)
  
  STATISTICS
  ├── Transitions enriched: 3
  ├── Km values: 8
  ├── kcat values: 5
  ├── Ki values: 2
  └── Citations: 12
  
  TRANSITIONS
  ├── R01 - Hexokinase (EC 2.7.1.1)
  │   ├── Km: 0.15 mM (substrate: glucose)
  │   ├── kcat: 150 s⁻¹
  │   └── Citations: PMID:12345678, PMID:23456789
  └── R02 - Phosphofructokinase (EC 2.7.1.11)
      ├── Km: 0.08 mM (substrate: F6P)
      └── kcat: 300 s⁻¹
  
  [View Raw Data] [Export Report]
  ```

#### 5.4 Update Project Actions

- [ ] **Add pathway actions** (File Panel → Project Actions)
  - [ ] "Import Pathway..." → Opens pathway import dialog
  - [ ] "Export Pathways..." → Export pathway data bundle
  - [ ] "Generate Report..." → Report with pathway lineage

### Testing

- [ ] **UI tests** (`tests/ui/test_file_panel_pathways.py`)
  - [ ] Test pathway list displays correctly
  - [ ] Test enrichment details dialog
  - [ ] Test context menu actions
  - [ ] Test "View Source" opens file

### Deliverables
- [ ] File Panel shows pathways and enrichments
- [ ] Context menus working
- [ ] Enrichment viewer dialog implemented

### Success Criteria
✅ Can see pathways in File Panel
✅ Can view enrichment details
✅ Can trace pathway → model → enrichments in UI

---

## Phase 6: Report Generation (1 day)

**Goal:** Generate reports with full pathway lineage

### Tasks

#### 6.1 Create Report Generator

- [ ] **Add pathway report generator** (`src/shypn/reporting/pathway_report.py`)
  ```python
  class PathwayLineageReport:
      """Generate report with full pathway and enrichment lineage."""
      
      def generate(self, model_id: str, project: Project) -> str:
          """Generate HTML/PDF report.
          
          Sections:
              1. Model Overview
              2. Source Pathway (KEGG/SBML)
              3. Enrichment History
              4. Data Provenance
              5. Citations
          """
  ```

#### 6.2 Add Report Templates

- [ ] **Create HTML template** (`src/shypn/reporting/templates/pathway_lineage.html`)
  - [ ] Header with project info
  - [ ] Pathway source section (with images if available)
  - [ ] Enrichment sections (collapsible)
  - [ ] Citation list (formatted bibliography)
  - [ ] Footer with generation date

#### 6.3 Integrate with UI

- [ ] **Add "Generate Report" action**
  - [ ] Right-click model → "Generate Lineage Report"
  - [ ] File Panel → Project Actions → "Generate Reports..."
  - [ ] Select output format (HTML, PDF, Markdown)

#### 6.4 Export Functionality

- [ ] **Add pathway export**
  - [ ] Export single pathway with enrichments
  - [ ] Export entire project data bundle
  - [ ] Include all raw files (KGML, SBML, JSON)

### Testing

- [ ] **Report tests** (`tests/reporting/test_pathway_report.py`)
  - [ ] Test report generation
  - [ ] Test with/without enrichments
  - [ ] Test citation formatting
  - [ ] Test export bundle

### Deliverables
- [ ] Report generator implemented
- [ ] HTML template created
- [ ] Export functionality working

### Success Criteria
✅ Can generate report from model
✅ Report includes pathway source and enrichments
✅ Citations properly formatted
✅ Can export project data bundle

---

## Phase 7: File System Observer (1 day)

**Goal:** Monitor project directory for external file changes and sync with Project state

### Background

Users may manipulate files directly in the project folder:
- Copy KGML files to `pathways/` directory
- Delete pathway files via file manager
- Edit metadata JSON files externally
- Move files between directories

The Project state should automatically reflect these changes without requiring manual refresh or app restart.

### Tasks

#### 7.1 Create ProjectFileObserver Class

- [ ] **Add file system observer** (`src/shypn/data/project_file_observer.py`)
  ```python
  class ProjectFileObserver:
      """Monitors project directory for file system changes.
      
      Uses watchdog library to detect:
          - New files added to pathways/
          - Files deleted from pathways/
          - Files modified in pathways/
          - Metadata changes
      
      Automatically syncs Project state when changes detected.
      """
      
      def __init__(self, project: Project):
          self.project = project
          self.observer = Observer()  # watchdog
          self.handler = ProjectFileHandler(project)
      
      def start_monitoring(self):
          """Start watching project directory."""
          pathways_dir = self.project.get_pathways_dir()
          self.observer.schedule(self.handler, pathways_dir, recursive=False)
          self.observer.start()
      
      def stop_monitoring(self):
          """Stop watching project directory."""
          self.observer.stop()
          self.observer.join()
  ```

#### 7.2 Implement File Event Handler

- [ ] **Create event handler** (`src/shypn/data/project_file_observer.py`)
  ```python
  class ProjectFileHandler(FileSystemEventHandler):
      """Handles file system events in project directory."""
      
      def __init__(self, project: Project):
          self.project = project
      
      def on_created(self, event):
          """Handle new file added to pathways/ directory.
          
          Example: User copies hsa00010.kgml to pathways/
          Action: Create PathwayDocument if not exists
          """
          if not event.is_directory:
              self._handle_pathway_file_added(event.src_path)
      
      def on_deleted(self, event):
          """Handle file deleted from pathways/ directory.
          
          Example: User deletes hsa00010.kgml
          Action: Remove PathwayDocument if exists
          """
          if not event.is_directory:
              self._handle_pathway_file_deleted(event.src_path)
      
      def on_modified(self, event):
          """Handle file modified in pathways/ directory.
          
          Example: User edits metadata JSON
          Action: Reload PathwayDocument metadata
          """
          if not event.is_directory:
              self._handle_pathway_file_modified(event.src_path)
  ```

#### 7.3 Auto-Discovery Logic

- [ ] **Implement auto-discovery** for orphaned files
  ```python
  def _handle_pathway_file_added(self, file_path: Path):
      """Auto-create PathwayDocument for new file.
      
      Strategy:
          1. Detect file type (KGML, SBML) by extension
          2. Try to extract metadata from file
          3. Create PathwayDocument with source_type='external'
          4. Tag as 'auto-discovered'
          5. Add to project
      """
      filename = Path(file_path).name
      
      # Check if already tracked
      for pathway in self.project.pathways.list_pathways():
          if pathway.raw_file == filename:
              return  # Already tracked
      
      # Auto-discover
      if filename.endswith('.kgml') or filename.endswith('.xml'):
          pathway_doc = self._discover_kegg_file(file_path)
      elif filename.endswith('.sbml'):
          pathway_doc = self._discover_sbml_file(file_path)
      else:
          return  # Unknown file type
      
      # Add to project
      self.project.add_pathway(pathway_doc)
      self.project.save()
      
      # Notify UI (optional)
      self._emit_notification(f"New pathway discovered: {pathway_doc.name}")
  ```

- [ ] **Implement KEGG auto-discovery**
  ```python
  def _discover_kegg_file(self, file_path: Path) -> PathwayDocument:
      """Auto-discover KEGG pathway from KGML file.
      
      Extract:
          - Pathway ID from filename (e.g., hsa00010)
          - Organism from pathway ID (e.g., hsa = Homo sapiens)
          - Pathway name from KGML <pathway> tag
      """
      from shypn.importer.kegg import parse_kgml
      
      filename = file_path.name
      pathway_id = Path(filename).stem  # "hsa00010"
      
      # Parse KGML to extract metadata
      kgml_data = file_path.read_text()
      pathway = parse_kgml(kgml_data)
      
      # Create PathwayDocument
      pathway_doc = PathwayDocument(
          name=pathway.title or pathway_id,
          source_type='kegg',
          source_id=pathway_id,
          source_organism=pathway.org or self._infer_organism(pathway_id)
      )
      pathway_doc.raw_file = filename
      pathway_doc.tags = ['auto-discovered', 'external']
      pathway_doc.notes = f'Auto-discovered from file system: {file_path}'
      
      return pathway_doc
  ```

#### 7.4 Sync on Project Load

- [ ] **Add sync check on project load**
  ```python
  class Project:
      @classmethod
      def load(cls, project_file: str) -> 'Project':
          """Load project and sync with file system."""
          with open(project_file, 'r') as f:
              data = json.load(f)
          
          project = cls.from_dict(data)
          
          # Sync with file system
          project._sync_with_filesystem()
          
          return project
      
      def _sync_with_filesystem(self):
          """Sync PathwayDocuments with actual files.
          
          Actions:
              1. Remove PathwayDocuments for missing files
              2. Discover new files not tracked
              3. Update modified dates if files changed
          """
          pathways_dir = self.get_pathways_dir()
          if not pathways_dir or not pathways_dir.exists():
              return
          
          # Find missing files
          for pathway_id, pathway_doc in list(self.pathways.pathways.items()):
              file_path = pathways_dir / pathway_doc.raw_file
              if not file_path.exists():
                  # File was deleted externally
                  self.remove_pathway(pathway_id)
          
          # Discover new files
          for file_path in pathways_dir.glob('*.kgml'):
              self._discover_pathway_file(file_path)
          
          for file_path in pathways_dir.glob('*.sbml'):
              self._discover_pathway_file(file_path)
  ```

#### 7.5 UI Integration

- [ ] **Add observer to ProjectManager**
  ```python
  class ProjectManager:
      """Global singleton for managing projects."""
      
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
          # Stop observer
          if project_id in self.observers:
              self.observers[project_id].stop_monitoring()
              del self.observers[project_id]
          
          # Remove from active projects
          if project_id in self.projects:
              del self.projects[project_id]
  ```

- [ ] **Add refresh button to File Panel**
  - Manual refresh option if auto-sync disabled
  - Shows last sync time
  - Force re-scan of pathways directory

#### 7.6 Configuration Options

- [ ] **Add settings for file observer**
  ```python
  project.settings.update({
      'file_observer_enabled': True,
      'file_observer_interval': 1.0,  # seconds
      'auto_discover_pathways': True,
      'notify_on_changes': True
  })
  ```

### Dependencies

- [ ] **Install watchdog library**
  ```bash
  pip install watchdog
  ```
  
- [ ] **Add to requirements.txt**
  ```
  watchdog>=3.0.0
  ```

### Testing

- [ ] **Unit tests** (`tests/data/test_project_file_observer.py`)
  - [ ] Test file creation detection
  - [ ] Test file deletion detection
  - [ ] Test file modification detection
  - [ ] Test auto-discovery of KEGG files
  - [ ] Test auto-discovery of SBML files
  - [ ] Test sync on project load

- [ ] **Integration tests**
  - [ ] Copy file to pathways/ → PathwayDocument created
  - [ ] Delete file → PathwayDocument removed
  - [ ] Edit metadata.json → PathwayDocument updated
  - [ ] Multiple rapid changes handled correctly

### Edge Cases

- [ ] **Handle rapid changes** (debouncing)
  - Multiple files copied at once
  - File being written (wait for complete)
  
- [ ] **Handle conflicts**
  - File deleted but PathwayDocument has enrichments
  - File modified while enrichment in progress
  
- [ ] **Handle network drives**
  - May not support file system events
  - Fallback to periodic polling

### Deliverables

- [ ] `ProjectFileObserver` class implemented
- [ ] `ProjectFileHandler` class implemented
- [ ] Auto-discovery logic for KEGG/SBML
- [ ] Sync on project load
- [ ] UI refresh button
- [ ] Integration tests passing

### Success Criteria

✅ Copy KGML file to pathways/ → Appears in File Panel immediately  
✅ Delete pathway file → Removed from File Panel  
✅ Project load syncs with file system  
✅ Can disable observer if desired  
✅ No crashes on rapid file changes

---

## Phase 8: Documentation & Validation (0.5 days)

**Goal:** Document new features and validate complete workflow

### Tasks

#### 7.1 Update Documentation

- [ ] **User documentation**
  - [ ] Update File Panel documentation
  - [ ] Document pathway import workflow
  - [ ] Document enrichment workflow
  - [ ] Document report generation

- [ ] **Developer documentation**
  - [ ] Update API documentation for Project class
  - [ ] Document PathwayDocument / EnrichmentDocument schemas
  - [ ] Add examples to README
  - [ ] Update architecture diagrams

#### 7.2 Create Tutorial

- [ ] **End-to-end tutorial**
  ```
  Tutorial: Importing and Enriching Pathways
  ═══════════════════════════════════════════
  
  1. Create new project
  2. Import KEGG pathway (hsa00010)
  3. Convert to canvas
  4. Enrich with BRENDA
  5. View enrichment in File Panel
  6. Generate lineage report
  7. Export project
  ```

#### 7.3 Validation Testing

- [ ] **Complete workflow tests**
  - [ ] Import KEGG → Convert → Enrich → Report
  - [ ] Import SBML → Convert → Enrich → Report
  - [ ] Multiple pathways in same project
  - [ ] Save/load project with pathways
  - [ ] Migration from old project format

- [ ] **Performance testing**
  - [ ] Test with 10+ pathways
  - [ ] Test with large SBML files
  - [ ] Test project load time

#### 7.4 Update VALIDATION_METRICS.txt

- [ ] **Add new metrics**
  ```
  [Pathway Management]
  - Pathway import success rate: 100%
  - Metadata extraction accuracy: 100%
  - Enrichment linking success: 100%
  - Report generation success: 100%
  ```

### Deliverables
- [ ] Updated documentation
- [ ] Tutorial created
- [ ] All validation tests passing

### Success Criteria
✅ Complete workflow documented
✅ Tutorial walkthrough successful
✅ All tests passing
✅ Performance acceptable

---

## Integration with FILE_PANEL_COMPLETION_PLAN.md

This plan is **Phase 3** of the File Panel completion:

```
FILE_PANEL_COMPLETION_PLAN.md:
├── Phase 1: Project Information Category ✓ (prerequisite)
├── Phase 2: Project Actions Category ✓ (prerequisite)
├── Phase 3: Data Persistence ← THIS PLAN
│   ├── Phase 0: Preparation
│   ├── Phase 1: Core Data Model
│   ├── Phase 2: KEGG Integration
│   ├── Phase 3: SBML Integration
│   ├── Phase 4: BRENDA Integration
│   ├── Phase 5: File Panel UI
│   ├── Phase 6: Report Generation
│   └── Phase 7: Documentation
└── Phase 4: Validation & Testing (after this plan)
```

## Risk Assessment

### High Risk
- **Data model changes** - Requires careful serialization testing
- **Migration from old format** - Need to handle edge cases
- **File path handling** - Absolute vs relative paths

### Medium Risk
- **BRENDA integration** - Complex matching logic
- **UI updates** - Need to maintain responsiveness with many pathways
- **Report generation** - Citation formatting can be tricky

### Low Risk
- **KEGG integration** - Well-understood API
- **SBML integration** - Standard format
- **Documentation** - Straightforward

## Mitigation Strategies

1. **Incremental Development**
   - Each phase is independently testable
   - Can deploy phases 1-3 without phases 4-7

2. **Backward Compatibility**
   - Migration function for old projects
   - Fallback for models without PathwayDocument

3. **Comprehensive Testing**
   - Unit tests for each component
   - Integration tests for workflows
   - Performance tests for scale

4. **Documentation First**
   - Write docs alongside implementation
   - Update examples in real-time

## Success Metrics

**Code Quality:**
- [ ] Test coverage > 90%
- [ ] No critical bugs
- [ ] All linting rules passing

**Functionality:**
- [ ] Can import and track pathways
- [ ] Can enrich and track enrichments
- [ ] Can generate reports with lineage

**User Experience:**
- [ ] Workflow is intuitive
- [ ] File Panel shows clear information
- [ ] Reports are readable and useful

**Performance:**
- [ ] Project load time < 2s (with 10 pathways)
- [ ] UI remains responsive
- [ ] Report generation < 5s

## Timeline Summary

| Phase | Duration | Dependencies |
|-------|----------|--------------|
| Phase 0: Preparation | 0.5 days | None |
| Phase 1: Core Data Model | 1-2 days | Phase 0 |
| Phase 2: KEGG Integration | 1 day | Phase 1 |
| Phase 3: SBML Integration | 1 day | Phase 1 |
| Phase 4: BRENDA Integration | 1-2 days | Phases 1, 2, 3 |
| Phase 5: File Panel UI | 1-2 days | Phases 1-4 |
| Phase 6: Report Generation | 1 day | Phases 1-5 |
| Phase 7: File System Observer | 1 day | Phase 1 |
| Phase 8: Documentation | 0.5 days | Phases 1-7 |

**Total: 7-11 days** (optimistic-pessimistic range)

## Next Steps

1. **Review this plan** - Get feedback on approach
2. **Start Phase 0** - Audit current codebase
3. **Create branch** - `feature/pathway-metadata-schema`
4. **Begin Phase 1** - Implement core data model

---

**Created:** October 25, 2025  
**Related Documents:**
- `PATHWAY_METADATA_SCHEMA.md` - Design specification
- `FILE_PANEL_COMPLETION_PLAN.md` - Parent plan
- `PATHWAY_DATA_ISOLATION_PLAN.md` - Related architectural work
