# Phase 5: File Panel UI Integration - DESIGN SPECIFICATION

**Date:** October 25, 2025  
**Status:** 📋 DESIGN PHASE  
**UI Pattern:** Expander categories with embedded TreeView (spreadsheet-like)

---

## Overview

Phase 5 will add pathway and enrichment metadata display to the File Panel using SHYpn's established pattern:
- **Expander categories** for organization
- **TreeView widgets** inside expanders (spreadsheet-like presentation)
- **Context menus** for actions
- **Inline buttons** in category headers

---

## UI Architecture Pattern

### Current File Panel Structure

```
EXPLORER Panel (left_panel_vscode.ui)
├─ Float/Attach button (top-right corner)
├─
├─ 📁 FILES (CategoryFrame - expanded by default)
│  ├─ Inline buttons: [+ File] [+ Folder] [⌂]
│  ├─ Path entry: /workspace/projects/MyProject/models
│  └─ TreeView (file browser)
│
├─ ℹ️ PROJECT INFORMATION (CategoryFrame - collapsed)
│  └─ (TODO: Project metadata content)
│
└─ ⚙️ PROJECT ACTIONS (CategoryFrame - collapsed)
   └─ Buttons: [New Project] [Open Project] [Settings]
```

### Phase 5 Addition: New Categories

```
EXPLORER Panel
├─ Float/Attach button
├─
├─ 📁 FILES (existing)
│  └─ TreeView: file/folder browser
│
├─ 🧬 PATHWAYS (NEW - CategoryFrame - collapsed)
│  ├─ Inline buttons: [↻ Refresh] [+ Import]
│  └─ TreeView: pathway metadata spreadsheet
│     ┌─────────────────┬──────────┬────────────┬─────────────┐
│     │ Name            │ Source   │ Organism   │ Status      │
│     ├─────────────────┼──────────┼────────────┼─────────────┤
│     │ Glycolysis      │ KEGG     │ H. sapiens │ ✅ Converted │
│     │ E. coli Glyco.. │ SBML     │ E. coli    │ ✅ Converted │
│     │ TCA Cycle       │ KEGG     │ H. sapiens │ ⚠️ Not conv..│
│     └─────────────────┴──────────┴────────────┴─────────────┘
│     Context menu: View Source | Re-convert | Add Enrichment | Export
│
├─ ⚡ ENRICHMENTS (NEW - CategoryFrame - collapsed)
│  ├─ Inline buttons: [↻ Refresh] [🗑️ Clear All]
│  └─ TreeView: enrichment metadata spreadsheet
│     ┌──────────────┬──────────┬─────────────┬────────────┬────────────┐
│     │ Date         │ Source   │ Transitions │ Parameters │ Confidence │
│     ├──────────────┼──────────┼─────────────┼────────────┼────────────┤
│     │ Oct 25, 2025 │ BRENDA   │ 8           │ 16 (Km/Kc) │ High ⭐     │
│     │ Oct 24, 2025 │ SABIO-RK │ 5           │ 10 (Ki)    │ Medium     │
│     └──────────────┴──────────┴─────────────┴────────────┴────────────┘
│     Context menu: View Details | Re-apply | Remove | Export
│
├─ ℹ️ PROJECT INFORMATION (existing - enhanced)
│  └─ Label Grid: project stats
│     Project: MyProject
│     Path: /workspace/projects/MyProject
│     Models: 3
│     Pathways: 2 ← NEW
│     Enrichments: 1 ← NEW
│     Last Modified: Oct 25, 2025
│
└─ ⚙️ PROJECT ACTIONS (existing)
   └─ Buttons: [New Project] [Open Project] [Settings]
```

---

## Implementation Strategy

### 1. Create PathwaysViewController

**File:** `src/shypn/helpers/pathways_view_controller.py`

**Responsibilities:**
- Populate TreeView with pathway data from project
- Update when project changes
- Handle context menu actions
- Integrate with KEGG/SBML import panels

**TreeView Columns:**
1. **Icon** (GdkPixbuf) - Visual indicator
2. **Name** (str) - Pathway display name
3. **Source** (str) - "KEGG" / "SBML" / "BioModels"
4. **Source ID** (str) - e.g., "hsa00010"
5. **Organism** (str) - e.g., "Homo sapiens"
6. **Status** (str) - "✅ Converted" / "⚠️ Not converted"
7. **Enrichments** (int) - Count of enrichments
8. **Date** (str) - Import date

**Data Model:**
```python
# GtkListStore columns:
# 0: icon (GdkPixbuf)
# 1: name (str)
# 2: source (str)
# 3: source_id (str)
# 4: organism (str)
# 5: status (str)
# 6: enrichments_count (int)
# 7: date (str)
# 8: pathway_id (str, hidden) - for context menu actions

liststore = Gtk.ListStore(
    GdkPixbuf.Pixbuf,  # icon
    str,               # name
    str,               # source
    str,               # source_id
    str,               # organism
    str,               # status
    int,               # enrichments_count
    str,               # date
    str                # pathway_id (hidden)
)
```

**Context Menu:**
```
─────────────────────────
View Source File
Re-convert to Model
─────────────────────────
Add BRENDA Enrichment
Add SABIO-RK Enrichment
─────────────────────────
Export Metadata (JSON)
Copy Pathway ID
─────────────────────────
Remove from Project
```

### 2. Create EnrichmentsViewController

**File:** `src/shypn/helpers/enrichments_view_controller.py`

**Responsibilities:**
- Populate TreeView with enrichment data
- Update when enrichments are applied
- Handle context menu actions
- Show enrichment details dialog

**TreeView Columns:**
1. **Icon** (GdkPixbuf) - Source icon
2. **Date** (str) - "Oct 25, 2025 14:30"
3. **Source** (str) - "BRENDA API" / "BRENDA Local" / "SABIO-RK"
4. **Pathway** (str) - Linked pathway name
5. **Transitions** (int) - Count of enriched transitions
6. **Parameters** (str) - "16 (Km, Kcat)" / "10 (Ki)"
7. **Confidence** (str) - "High ⭐" / "Medium" / "Low"
8. **Citations** (int) - Number of citations

**Data Model:**
```python
liststore = Gtk.ListStore(
    GdkPixbuf.Pixbuf,  # icon
    str,               # date
    str,               # source
    str,               # pathway_name
    int,               # transitions_count
    str,               # parameters_summary
    str,               # confidence
    int,               # citations_count
    str                # enrichment_id (hidden)
)
```

**Context Menu:**
```
─────────────────────────
View Details
View BRENDA Data File
─────────────────────────
Re-apply Enrichment
─────────────────────────
Export Metadata (JSON)
Copy Enrichment ID
─────────────────────────
Remove Enrichment
```

### 3. Update FilePanelLoader

**File:** `src/shypn/helpers/file_panel_loader.py`

**Add methods:**
```python
def _create_pathways_category(self, container):
    """Create PATHWAYS category with TreeView."""
    self.pathways_category = CategoryFrame(
        title="PATHWAYS",
        buttons=[
            ("↻", self._on_refresh_pathways),
            ("+", self._on_import_pathway)
        ],
        expanded=False  # Collapsed by default
    )
    
    # Create TreeView
    pathways_view = self._create_pathways_treeview()
    
    # Wrap in ScrolledWindow
    scroll = Gtk.ScrolledWindow()
    scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
    scroll.add(pathways_view)
    
    self.pathways_category.set_content(scroll)
    container.pack_start(self.pathways_category, False, False, 0)
    self.categories.append(self.pathways_category)

def _create_pathways_treeview(self):
    """Create TreeView for pathways display."""
    # Create ListStore
    store = Gtk.ListStore(
        GdkPixbuf.Pixbuf,  # icon
        str,  # name
        str,  # source
        str,  # organism
        str,  # status
        int,  # enrichments_count
        str,  # date
        str   # pathway_id (hidden)
    )
    
    # Create TreeView
    treeview = Gtk.TreeView(model=store)
    treeview.set_headers_visible(True)
    
    # Add columns
    self._add_column(treeview, "Name", 1, width=150)
    self._add_column(treeview, "Source", 2, width=80)
    self._add_column(treeview, "Organism", 3, width=100)
    self._add_column(treeview, "Status", 4, width=100)
    self._add_column(treeview, "Enrichments", 5, width=80)
    self._add_column(treeview, "Date", 6, width=100)
    
    # Connect signals
    treeview.connect('button-press-event', self._on_pathways_button_press)
    treeview.connect('row-activated', self._on_pathway_row_activated)
    
    return treeview

def _create_enrichments_category(self, container):
    """Create ENRICHMENTS category with TreeView."""
    # Similar to pathways category

def _update_project_info_category(self):
    """Update PROJECT INFORMATION with pathway/enrichment counts."""
    # Add to existing content:
    # Pathways: 2
    # Enrichments: 1
```

### 4. Enhance ProjectInfoController

**File:** `src/shypn/helpers/project_info_controller.py` (NEW)

**Purpose:** Display live project statistics

**Content:**
```python
class ProjectInfoController:
    """Controller for PROJECT INFORMATION category."""
    
    def __init__(self, project, builder):
        self.project = project
        self.content_box = self._build_info_display()
    
    def _build_info_display(self):
        """Build label grid for project info."""
        grid = Gtk.Grid()
        grid.set_row_spacing(6)
        grid.set_column_spacing(12)
        grid.set_margin_start(12)
        grid.set_margin_end(12)
        grid.set_margin_top(6)
        grid.set_margin_bottom(6)
        
        # Row 0: Project name
        self._add_info_row(grid, 0, "Project:", self.project.name)
        
        # Row 1: Path
        self._add_info_row(grid, 1, "Path:", 
                          self._truncate_path(self.project.base_path))
        
        # Row 2: Models count
        models_count = len(self.project.models)
        self._add_info_row(grid, 2, "Models:", str(models_count))
        
        # Row 3: Pathways count (NEW)
        pathways_count = len(self.project.pathways.list_pathways())
        self._add_info_row(grid, 3, "Pathways:", str(pathways_count))
        
        # Row 4: Enrichments count (NEW)
        enrichments_count = self._count_total_enrichments()
        self._add_info_row(grid, 4, "Enrichments:", str(enrichments_count))
        
        # Row 5: Last modified
        self._add_info_row(grid, 5, "Modified:", 
                          self._format_date(self.project.modified_date))
        
        return grid
    
    def _count_total_enrichments(self):
        """Count total enrichments across all pathways."""
        total = 0
        for pathway in self.project.pathways.list_pathways():
            total += len(pathway.enrichments)
        return total
    
    def refresh(self):
        """Refresh displayed information."""
        # Update labels with current project state
```

---

## User Workflows

### Workflow 1: View Imported Pathways

```
User opens File Panel → PATHWAYS category
    ↓
Expander opens, showing TreeView
    ↓
TreeView displays:
    Row 1: Glycolysis | KEGG | H. sapiens | ✅ Converted | 1 enrichment
    Row 2: E. coli Glycolysis | SBML | E. coli | ✅ Converted | 0 enrichments
    ↓
User double-clicks "Glycolysis"
    ↓
Action: Open model in canvas (if converted)
    ↓
User right-clicks → "View Source File"
    ↓
Action: Open pathways/hsa00010.kgml in external viewer
```

### Workflow 2: Re-convert Pathway

```
User right-clicks pathway in TreeView
    ↓
Context menu: "Re-convert to Model"
    ↓
Dialog: "Re-convert 'Glycolysis' pathway?"
        "This will create a new model file."
        [Cancel] [Re-convert]
    ↓
User clicks [Re-convert]
    ↓
System:
    1. Loads KGML from project/pathways/
    2. Runs conversion
    3. Creates new model
    4. Updates PathwayDocument.model_id
    5. Refreshes TreeView
    ↓
Status updated: ✅ Converted (just now)
```

### Workflow 3: View Enrichment Details

```
User opens ENRICHMENTS category
    ↓
TreeView displays enrichments:
    Row 1: Oct 25, 2025 | BRENDA API | Glycolysis | 8 transitions | High ⭐
    ↓
User double-clicks enrichment
    ↓
Dialog: "Enrichment Details"
    ┌─────────────────────────────────────────────┐
    │ BRENDA Enrichment                           │
    │ Applied: October 25, 2025 14:30:22          │
    │                                             │
    │ Pathway: Glycolysis (KEGG hsa00010)         │
    │ Source: BRENDA SOAP API                     │
    │ Organism: Homo sapiens                      │
    │                                             │
    │ Enriched Transitions: 8                     │
    │   T1: Hexokinase (EC 2.7.1.1)              │
    │   T2: Phosphofructokinase (EC 2.7.1.11)    │
    │   ... (6 more)                              │
    │                                             │
    │ Parameters Added: 16 total                  │
    │   • Km values: 8                            │
    │   • Kcat values: 8                          │
    │                                             │
    │ Citations: 15 literature sources            │
    │   PMID:12345678, PMID:23456789, ...        │
    │                                             │
    │ Confidence: High ⭐                         │
    │ Data file: brenda_enrichment_20251025...   │
    │                                             │
    │ [View BRENDA Data] [Re-apply] [Close]      │
    └─────────────────────────────────────────────┘
```

### Workflow 4: Add Enrichment to Pathway

```
User right-clicks pathway in PATHWAYS view
    ↓
Context menu: "Add BRENDA Enrichment"
    ↓
System:
    1. Opens Pathway Panel → BRENDA tab
    2. Pre-fills organism from pathway metadata
    3. User configures enrichment options
    4. Clicks "Analyze and Enrich Canvas"
    ↓
Enrichment applied and tracked
    ↓
Both views update:
    • PATHWAYS: Enrichments count: 0 → 1
    • ENRICHMENTS: New row added
```

---

## Visual Design

### TreeView Styling (CSS)

```css
/* Pathway TreeView */
treeview.pathways-view {
    font-size: 11px;
}

treeview.pathways-view header button {
    font-weight: bold;
    font-size: 10px;
    padding: 4px 8px;
}

/* Status column colors */
treeview.pathways-view .status-converted {
    color: #28a745;  /* Green */
}

treeview.pathways-view .status-not-converted {
    color: #ffc107;  /* Amber */
}

/* Enrichment TreeView */
treeview.enrichments-view {
    font-size: 11px;
}

treeview.enrichments-view .confidence-high {
    color: #28a745;
    font-weight: bold;
}

treeview.enrichments-view .confidence-medium {
    color: #ffc107;
}

treeview.enrichments-view .confidence-low {
    color: #dc3545;
}
```

### Icons

**Pathway Sources:**
- KEGG: 🗺️ (map icon)
- SBML: 🧬 (DNA icon)
- BioModels: 📊 (chart icon)

**Enrichment Sources:**
- BRENDA: ⚡ (bolt icon)
- SABIO-RK: 🔬 (microscope icon)
- Local File: 📄 (file icon)

**Status:**
- Converted: ✅ (green check)
- Not Converted: ⚠️ (warning triangle)
- Converting: ⏳ (hourglass)

**Confidence:**
- High: ⭐ (star)
- Medium: ◐ (half-circle)
- Low: ○ (empty circle)

---

## Integration Points

### 1. KEGG Import Integration

**When user imports KEGG pathway:**
```python
# In kegg_import_panel.py
def _on_import_complete(self, pathway_doc):
    # After creating PathwayDocument:
    # Trigger refresh of PATHWAYS view
    if hasattr(self, 'file_panel_loader'):
        self.file_panel_loader.refresh_pathways_view()
```

### 2. SBML Import Integration

**When user imports SBML:**
```python
# In sbml_import_panel.py
def _on_load_complete(self, document_model, pathway_name):
    # After linking model:
    # Trigger refresh
    if hasattr(self, 'file_panel_loader'):
        self.file_panel_loader.refresh_pathways_view()
```

### 3. BRENDA Enrichment Integration

**When enrichment is applied:**
```python
# In brenda_enrichment_controller.py
def save_enrichment_to_project(self, brenda_data):
    # After saving:
    # Trigger refresh of both views
    if hasattr(self, 'file_panel_loader'):
        self.file_panel_loader.refresh_pathways_view()
        self.file_panel_loader.refresh_enrichments_view()
```

### 4. File System Observer Integration

**When files change:**
```python
# In file_system_observer.py
def _on_file_created(self, path):
    if path.endswith('.kgml') or path.endswith('.sbml'):
        # Pathway file added
        self.file_panel_loader.refresh_pathways_view()
    elif path.endswith('.json') and 'enrichments' in path:
        # Enrichment file added
        self.file_panel_loader.refresh_enrichments_view()
```

---

## Implementation Phases

### Phase 5a: PATHWAYS Category (2-3 days)

**Day 1:**
- Create PathwaysViewController class
- Build TreeView with columns
- Populate from project.pathways
- Basic context menu

**Day 2:**
- Implement context menu actions
  - View Source File
  - Re-convert to Model
  - Export Metadata
- Wire to KEGG/SBML import panels

**Day 3:**
- Add inline buttons (Refresh, Import)
- Polish UI (icons, colors, sizing)
- Testing and bug fixes

### Phase 5b: ENRICHMENTS Category (1-2 days)

**Day 1:**
- Create EnrichmentsViewController class
- Build TreeView with columns
- Populate from pathway enrichments
- Context menu

**Day 2:**
- Enrichment details dialog
- Context menu actions (Re-apply, Remove)
- Wire to BRENDA controller
- Testing

### Phase 5c: PROJECT INFORMATION Enhancement (0.5 days)

- Create ProjectInfoController
- Add pathway/enrichment counts
- Wire to refresh automatically

### Phase 5d: Integration & Polish (1 day)

- Connect all refresh triggers
- File system observer integration
- UI polish and testing
- Documentation

**Total: 4-6 days**

---

## Testing Plan

### Unit Tests

```python
def test_pathways_view_population():
    """Test PATHWAYS view populates correctly."""
    project = create_test_project()
    
    # Add pathway
    pathway = PathwayDocument(
        source_type="kegg",
        source_id="hsa00010",
        name="Glycolysis"
    )
    project.add_pathway(pathway)
    
    # Create view
    controller = PathwaysViewController(project)
    
    # Verify TreeView has 1 row
    assert controller.get_row_count() == 1
    
    # Verify data
    row = controller.get_row(0)
    assert row['name'] == "Glycolysis"
    assert row['source'] == "KEGG"

def test_enrichments_view_population():
    """Test ENRICHMENTS view populates correctly."""
    # Similar test structure
```

### Integration Tests

```python
def test_import_updates_pathways_view():
    """Test importing pathway updates PATHWAYS view."""
    # Import KEGG pathway
    # Verify PATHWAYS view refreshes
    # Verify new row appears

def test_enrichment_updates_views():
    """Test applying enrichment updates both views."""
    # Apply BRENDA enrichment
    # Verify PATHWAYS view shows enrichment count
    # Verify ENRICHMENTS view shows new row
```

### Manual Tests

1. **Category Expansion**
   - Click PATHWAYS header → expands
   - Click ENRICHMENTS header → PATHWAYS collapses
   - Verify exclusive expansion behavior

2. **TreeView Display**
   - Import multiple pathways
   - Verify all appear in TreeView
   - Verify columns align correctly
   - Verify scrolling works

3. **Context Menu**
   - Right-click pathway → menu appears
   - Click "View Source File" → file opens
   - Click "Re-convert" → conversion happens

4. **Refresh Behavior**
   - Import pathway → view refreshes automatically
   - Apply enrichment → both views refresh
   - Close and reopen project → views repopulate

---

## Success Criteria

✅ **PATHWAYS category displays:**
- All imported pathways (KEGG, SBML)
- Correct metadata (name, source, organism)
- Conversion status
- Enrichment counts
- Import dates

✅ **ENRICHMENTS category displays:**
- All applied enrichments
- Linked pathway names
- Source and confidence
- Transition and parameter counts
- Citations count

✅ **Context menus work:**
- View Source File
- Re-convert to Model
- Add Enrichment
- View Details
- Remove

✅ **Integration works:**
- Views refresh when pathways imported
- Views refresh when enrichments applied
- Views persist across project open/close
- File system observer triggers refreshes

✅ **UI fits pattern:**
- Uses CategoryFrame expanders
- TreeView in ScrolledWindow
- Inline buttons in headers
- Exclusive expansion behavior
- Consistent with FILES category

---

## Next Steps After Phase 5

**Phase 6: Report Generation** (1-2 days)
- Generate PDF/HTML reports
- Include pathway lineage
- Include enrichment history
- Format citations properly

**Phase 8: Final Documentation** (0.5 days)
- User guide
- Tutorial video/guide
- Final validation testing

---

## Related Documentation

- `PHASE4_BRENDA_INTEGRATION_COMPLETE.md` - Enrichment infrastructure
- `PHASE3_SBML_INTEGRATION_COMPLETE.md` - SBML import pattern
- `PHASE2_KEGG_INTEGRATION_COMPLETE.md` - KEGG import pattern
- `PATHWAY_METADATA_SCHEMA.md` - Data models
- `src/shypn/ui/category_frame.py` - CategoryFrame widget reference
- `src/shypn/helpers/file_panel_loader.py` - File Panel architecture

---

**Status: Ready for Implementation** ✅  
**UI Pattern: Established and documented** ✅  
**Integration Points: Identified** ✅  
**Estimated Time: 4-6 days** ⏱️
