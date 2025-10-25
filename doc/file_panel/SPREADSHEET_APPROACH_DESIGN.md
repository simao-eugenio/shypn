# Pathway Metadata System - Spreadsheet Approach

**Date:** October 25, 2025  
**Concept:** Auto-generated spreadsheets updated during workflow, embedded in File Panel  
**Advantage:** Rich data, exportable, sortable, filterable - familiar tool for scientists

---

## Core Concept

Instead of custom TreeViews, generate **real spreadsheet files** that:
1. **Auto-update** during import/enrichment operations
2. **Live in project directory** (`project/metadata/`)
3. **Open in File Panel** via embedded viewer or external app
4. **Exportable** as-is for publications/reports

---

## Spreadsheet Files Structure

### File 1: `pathways.csv` (or `.ods`, `.xlsx`)

**Location:** `project/metadata/pathways.csv`

**Columns:**
```
| ID | Name | Source | Source_ID | Organism | Status | Model_File | Model_ID | Raw_File | Import_Date | Last_Modified | Enrichments_Count | Notes |
```

**Example Data:**
```csv
ID,Name,Source,Source_ID,Organism,Status,Model_File,Model_ID,Raw_File,Import_Date,Last_Modified,Enrichments_Count,Notes
pathway-abc123,Glycolysis / Gluconeogenesis,KEGG,hsa00010,Homo sapiens,Converted,glycolysis_kegg.shy,model-xyz789,hsa00010.kgml,2025-10-25 14:30:22,2025-10-25 14:30:22,1,
pathway-def456,E. coli Glycolysis,SBML,ecoli_glycolysis,Escherichia coli,Converted,ecoli_glyco.shy,model-abc456,ecoli_glycolysis.sbml,2025-10-24 09:15:30,2025-10-24 09:15:30,0,
pathway-ghi789,TCA Cycle,KEGG,hsa00020,Homo sapiens,Not Converted,,,hsa00020.kgml,2025-10-23 16:45:00,2025-10-23 16:45:00,0,Conversion failed - missing data
```

**Auto-updated when:**
- User imports KEGG pathway → New row added
- User imports SBML model → New row added
- Pathway converted to model → Status, Model_File, Model_ID updated
- Enrichment applied → Enrichments_Count incremented
- User adds notes → Notes column updated

### File 2: `enrichments.csv`

**Location:** `project/metadata/enrichments.csv`

**Columns:**
```
| ID | Pathway_ID | Pathway_Name | Date | Source | Source_Type | Organism | EC_Numbers | Transitions_Enriched | Km_Count | Kcat_Count | Ki_Count | Vmax_Count | Other_Parameters | Citations_Count | Confidence | Data_File | Notes |
```

**Example Data:**
```csv
ID,Pathway_ID,Pathway_Name,Date,Source,Source_Type,Organism,EC_Numbers,Transitions_Enriched,Km_Count,Kcat_Count,Ki_Count,Vmax_Count,Other_Parameters,Citations_Count,Confidence,Data_File,Notes
enrich-111,pathway-abc123,Glycolysis,2025-10-25 14:30:22,BRENDA,API,Homo sapiens,"2.7.1.1,2.7.1.11,1.1.1.1",8,8,8,0,0,0,15,High,brenda_enrichment_20251025_143022.json,
enrich-222,pathway-ghi789,TCA Cycle,2025-10-24 09:15:30,BRENDA,Local File,Homo sapiens,"1.1.1.37,1.2.4.1",5,5,0,5,0,0,8,Medium,brenda_enrichment_20251024_091530.json,Partial data
enrich-333,pathway-abc123,Glycolysis,2025-10-23 16:45:00,SABIO-RK,API,Homo sapiens,"2.7.1.1",3,0,0,0,3,Ki,5,High,sabiork_enrichment_20251023_164500.json,
```

**Auto-updated when:**
- User applies BRENDA enrichment → New row added
- User applies SABIO-RK enrichment → New row added
- User removes enrichment → Row deleted or marked inactive
- User adds notes → Notes column updated

### File 3: `project_summary.csv`

**Location:** `project/metadata/project_summary.csv`

**Columns:**
```
| Metric | Value | Last_Updated |
```

**Example Data:**
```csv
Metric,Value,Last_Updated
Project Name,MyProject,2025-10-25 14:30:22
Project Path,/workspace/projects/MyProject,2025-10-25 14:30:22
Created Date,2025-10-20 10:00:00,2025-10-20 10:00:00
Total Models,3,2025-10-25 14:30:22
Total Pathways,2,2025-10-25 14:30:22
KEGG Pathways,1,2025-10-25 14:30:22
SBML Pathways,1,2025-10-25 14:30:22
Total Enrichments,3,2025-10-25 14:30:22
BRENDA Enrichments,2,2025-10-25 14:30:22
SABIO-RK Enrichments,1,2025-10-25 14:30:22
Total Transitions Enriched,16,2025-10-25 14:30:22
Total Parameters Added,34,2025-10-25 14:30:22
Average Confidence,High,2025-10-25 14:30:22
Last Modified,2025-10-25 14:30:22,2025-10-25 14:30:22
```

---

## Project Structure

```
workspace/projects/MyProject/
├── .project.shy                  # JSON metadata (for programmatic access)
├── metadata/                     # NEW: Auto-generated spreadsheets
│   ├── pathways.csv
│   ├── enrichments.csv
│   ├── project_summary.csv
│   └── README.md                 # Explains spreadsheet structure
├── models/
│   ├── glycolysis_kegg.shy
│   └── ecoli_glyco.shy
├── pathways/
│   ├── hsa00010.kgml
│   └── ecoli_glycolysis.sbml
└── enrichments/
    ├── brenda_enrichment_20251025_143022.json
    └── sabiork_enrichment_20251023_164500.json
```

---

## File Panel Integration

### PROJECT INFORMATION Category (Enhanced)

Instead of just labels, show **spreadsheet viewer** or **link to open**:

```
┌─────────────────────────────────────────────────────┐
│ ▼ PROJECT INFORMATION                               │
├─────────────────────────────────────────────────────┤
│                                                     │
│ Project: MyProject                                  │
│ Path: /workspace/projects/MyProject                 │
│                                                     │
│ Quick Stats:                                        │
│   Models: 3 | Pathways: 2 | Enrichments: 3        │
│                                                     │
│ ┌─────────────────────────────────────────────┐   │
│ │ 📊 Metadata Spreadsheets                    │   │
│ ├─────────────────────────────────────────────┤   │
│ │ • pathways.csv          [📂 Open] [↻]       │   │
│ │   2 pathways, updated Oct 25                │   │
│ │                                              │   │
│ │ • enrichments.csv       [📂 Open] [↻]       │   │
│ │   3 enrichments, updated Oct 25             │   │
│ │                                              │   │
│ │ • project_summary.csv   [📂 Open] [↻]       │   │
│ │   Last updated Oct 25 14:30                 │   │
│ └─────────────────────────────────────────────┘   │
│                                                     │
│ [📊 Open All Spreadsheets] [📤 Export ZIP]         │
│                                                     │
└─────────────────────────────────────────────────────┘
```

**User Actions:**
- Click [📂 Open] → Opens CSV in LibreOffice Calc/Excel (external)
- Click [↻] → Regenerates spreadsheet from .project.shy
- Click [📊 Open All] → Opens all three spreadsheets in tabs
- Click [📤 Export ZIP] → Creates zip with all metadata for sharing

---

## Implementation Strategy

### 1. SpreadsheetGenerator Class

**File:** `src/shypn/data/spreadsheet_generator.py`

```python
class SpreadsheetGenerator:
    """Generate and update CSV spreadsheets from project metadata."""
    
    def __init__(self, project):
        self.project = project
        self.metadata_dir = os.path.join(project.base_path, 'metadata')
    
    def ensure_metadata_dir(self):
        """Create metadata directory if it doesn't exist."""
        os.makedirs(self.metadata_dir, exist_ok=True)
    
    def generate_pathways_csv(self):
        """Generate pathways.csv from project.pathways."""
        filepath = os.path.join(self.metadata_dir, 'pathways.csv')
        
        with open(filepath, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'ID', 'Name', 'Source', 'Source_ID', 'Organism',
                'Status', 'Model_File', 'Model_ID', 'Raw_File',
                'Import_Date', 'Last_Modified', 'Enrichments_Count', 'Notes'
            ])
            writer.writeheader()
            
            for pathway in self.project.pathways.list_pathways():
                writer.writerow({
                    'ID': pathway.id,
                    'Name': pathway.name,
                    'Source': pathway.source_type.upper(),
                    'Source_ID': pathway.source_id,
                    'Organism': pathway.source_organism,
                    'Status': 'Converted' if pathway.model_id else 'Not Converted',
                    'Model_File': self._get_model_filename(pathway.model_id),
                    'Model_ID': pathway.model_id or '',
                    'Raw_File': pathway.raw_file,
                    'Import_Date': pathway.imported_date,
                    'Last_Modified': pathway.last_modified,
                    'Enrichments_Count': len(pathway.enrichments),
                    'Notes': pathway.notes or ''
                })
        
        print(f"[SPREADSHEET] Generated: {filepath}")
        return filepath
    
    def generate_enrichments_csv(self):
        """Generate enrichments.csv from pathway enrichments."""
        filepath = os.path.join(self.metadata_dir, 'enrichments.csv')
        
        with open(filepath, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'ID', 'Pathway_ID', 'Pathway_Name', 'Date', 'Source',
                'Source_Type', 'Organism', 'EC_Numbers', 'Transitions_Enriched',
                'Km_Count', 'Kcat_Count', 'Ki_Count', 'Vmax_Count',
                'Other_Parameters', 'Citations_Count', 'Confidence',
                'Data_File', 'Notes'
            ])
            writer.writeheader()
            
            for pathway in self.project.pathways.list_pathways():
                for enrichment_id in pathway.enrichments:
                    # Get enrichment details (would be stored somewhere)
                    enrichment = self._get_enrichment_details(enrichment_id)
                    if enrichment:
                        writer.writerow({
                            'ID': enrichment.id,
                            'Pathway_ID': pathway.id,
                            'Pathway_Name': pathway.name,
                            'Date': enrichment.applied_date,
                            'Source': enrichment.source.upper(),
                            'Source_Type': enrichment.source_query.get('source_type', 'API'),
                            'Organism': pathway.source_organism,
                            'EC_Numbers': ','.join(enrichment.source_query.get('ec_numbers', [])),
                            'Transitions_Enriched': len(enrichment.transitions_enriched),
                            'Km_Count': enrichment.parameters_added.get('km', 0),
                            'Kcat_Count': enrichment.parameters_added.get('kcat', 0),
                            'Ki_Count': enrichment.parameters_added.get('ki', 0),
                            'Vmax_Count': enrichment.parameters_added.get('vmax', 0),
                            'Other_Parameters': self._count_other_params(enrichment),
                            'Citations_Count': len(enrichment.citations),
                            'Confidence': enrichment.confidence.capitalize(),
                            'Data_File': enrichment.data_file,
                            'Notes': enrichment.notes or ''
                        })
        
        print(f"[SPREADSHEET] Generated: {filepath}")
        return filepath
    
    def generate_project_summary_csv(self):
        """Generate project_summary.csv with aggregate stats."""
        filepath = os.path.join(self.metadata_dir, 'project_summary.csv')
        
        pathways = self.project.pathways.list_pathways()
        
        # Calculate stats
        total_pathways = len(pathways)
        kegg_count = len([p for p in pathways if p.source_type == 'kegg'])
        sbml_count = len([p for p in pathways if p.source_type == 'sbml'])
        total_enrichments = sum(len(p.enrichments) for p in pathways)
        
        stats = [
            ('Project Name', self.project.name),
            ('Project Path', self.project.base_path),
            ('Created Date', self.project.created_date),
            ('Total Models', len(self.project.models)),
            ('Total Pathways', total_pathways),
            ('KEGG Pathways', kegg_count),
            ('SBML Pathways', sbml_count),
            ('Total Enrichments', total_enrichments),
            ('Last Modified', self.project.modified_date)
        ]
        
        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Metric', 'Value', 'Last_Updated'])
            
            now = datetime.now().isoformat()
            for metric, value in stats:
                writer.writerow([metric, value, now])
        
        print(f"[SPREADSHEET] Generated: {filepath}")
        return filepath
    
    def generate_all(self):
        """Generate all spreadsheets."""
        self.ensure_metadata_dir()
        
        files = [
            self.generate_pathways_csv(),
            self.generate_enrichments_csv(),
            self.generate_project_summary_csv()
        ]
        
        # Create README
        readme_path = os.path.join(self.metadata_dir, 'README.md')
        with open(readme_path, 'w') as f:
            f.write(self._generate_readme())
        
        return files
    
    def _generate_readme(self):
        """Generate README explaining spreadsheet structure."""
        return """# Project Metadata Spreadsheets

These CSV files are automatically generated by SHYpn and contain metadata about your project's pathways and enrichments.

## Files

### pathways.csv
Contains information about all imported pathways (KEGG, SBML).
- One row per pathway
- Updated automatically when pathways are imported or converted

### enrichments.csv
Contains information about all enrichments applied to pathways.
- One row per enrichment
- Updated automatically when enrichments are applied

### project_summary.csv
Contains aggregate statistics about the project.
- Summary metrics
- Updated whenever project changes

## Usage

1. **View:** Open in LibreOffice Calc, Excel, or any CSV viewer
2. **Analyze:** Sort, filter, create pivot tables
3. **Export:** Copy/paste into reports or publications
4. **Share:** Send entire metadata/ folder to collaborators

## Important Notes

- These files are **automatically generated** - do not edit manually!
- To refresh: Use the "Regenerate" button in SHYpn File Panel
- These files complement the .project.shy JSON file (for programmatic access)

## For Publications

Include these files in supplementary materials to document:
- Pathway sources and provenance
- Enrichment methodology
- Parameter sources and confidence levels

Generated by SHYpn version X.X.X
"""
```

### 2. Integration with Workflow

**Hook into existing code:**

**In KEGG import panel:**
```python
def _on_import_complete(self, pathway_doc):
    # After creating PathwayDocument:
    self.project.add_pathway(pathway_doc)
    self.project.save()
    
    # NEW: Regenerate spreadsheets
    from shypn.data.spreadsheet_generator import SpreadsheetGenerator
    generator = SpreadsheetGenerator(self.project)
    generator.generate_all()
    
    # Trigger UI refresh
    if hasattr(self, 'file_panel_loader'):
        self.file_panel_loader.refresh_project_info()
```

**In SBML import panel:**
```python
def _on_load_complete(self, document_model, pathway_name):
    # After linking model:
    self.project.save()
    
    # NEW: Regenerate spreadsheets
    from shypn.data.spreadsheet_generator import SpreadsheetGenerator
    generator = SpreadsheetGenerator(self.project)
    generator.generate_all()
    
    # Trigger UI refresh
    if hasattr(self, 'file_panel_loader'):
        self.file_panel_loader.refresh_project_info()
```

**In BRENDA enrichment controller:**
```python
def save_enrichment_to_project(self, brenda_data):
    # After saving enrichment:
    self.project.save()
    
    # NEW: Regenerate spreadsheets
    from shypn.data.spreadsheet_generator import SpreadsheetGenerator
    generator = SpreadsheetGenerator(self.project)
    generator.generate_all()
    
    return True
```

### 3. File Panel UI Enhancement

**Simplified UI - Just links to open spreadsheets:**

```python
def _create_project_info_category(self, container):
    """Create PROJECT INFORMATION category with spreadsheet links."""
    self.project_info_category = CategoryFrame(
        title="PROJECT INFORMATION",
        expanded=False
    )
    
    # Create content
    content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
    content_box.set_margin_start(12)
    content_box.set_margin_end(12)
    content_box.set_margin_top(12)
    content_box.set_margin_bottom(12)
    
    # Project name and path
    info_grid = self._build_project_info_grid()
    content_box.pack_start(info_grid, False, False, 0)
    
    # Separator
    sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
    content_box.pack_start(sep, False, False, 6)
    
    # Metadata spreadsheets section
    metadata_label = Gtk.Label()
    metadata_label.set_markup("<b>Metadata Spreadsheets</b>")
    metadata_label.set_xalign(0)
    content_box.pack_start(metadata_label, False, False, 0)
    
    # Spreadsheet links
    spreadsheets = [
        ('pathways.csv', 'Pathways', 'pathway metadata'),
        ('enrichments.csv', 'Enrichments', 'enrichment details'),
        ('project_summary.csv', 'Summary', 'project statistics')
    ]
    
    for filename, label, tooltip in spreadsheets:
        row = self._create_spreadsheet_row(filename, label, tooltip)
        content_box.pack_start(row, False, False, 3)
    
    # Action buttons
    button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
    button_box.set_margin_top(12)
    
    open_all_btn = Gtk.Button(label="📊 Open All")
    open_all_btn.set_tooltip_text("Open all spreadsheets in default app")
    open_all_btn.connect('clicked', self._on_open_all_spreadsheets)
    button_box.pack_start(open_all_btn, True, True, 0)
    
    export_btn = Gtk.Button(label="📤 Export ZIP")
    export_btn.set_tooltip_text("Export all metadata as ZIP file")
    export_btn.connect('clicked', self._on_export_metadata_zip)
    button_box.pack_start(export_btn, True, True, 0)
    
    content_box.pack_start(button_box, False, False, 0)
    
    self.project_info_category.set_content(content_box)
    container.pack_start(self.project_info_category, False, False, 0)
    self.categories.append(self.project_info_category)

def _create_spreadsheet_row(self, filename, label, tooltip):
    """Create a row for one spreadsheet file."""
    row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
    
    # Icon and label
    label_widget = Gtk.Label(label=f"• {label}")
    label_widget.set_xalign(0)
    label_widget.set_tooltip_text(tooltip)
    row.pack_start(label_widget, True, True, 0)
    
    # Open button
    open_btn = Gtk.Button(label="📂")
    open_btn.set_tooltip_text(f"Open {filename}")
    open_btn.connect('clicked', self._on_open_spreadsheet, filename)
    row.pack_start(open_btn, False, False, 0)
    
    # Refresh button
    refresh_btn = Gtk.Button(label="↻")
    refresh_btn.set_tooltip_text("Regenerate from current data")
    refresh_btn.connect('clicked', self._on_regenerate_spreadsheet, filename)
    row.pack_start(refresh_btn, False, False, 0)
    
    return row

def _on_open_spreadsheet(self, button, filename):
    """Open spreadsheet in default application."""
    if not self.project:
        return
    
    filepath = os.path.join(self.project.base_path, 'metadata', filename)
    
    if not os.path.exists(filepath):
        # Generate if doesn't exist
        from shypn.data.spreadsheet_generator import SpreadsheetGenerator
        generator = SpreadsheetGenerator(self.project)
        generator.generate_all()
    
    # Open in default app (LibreOffice, Excel, etc.)
    import subprocess
    subprocess.Popen(['xdg-open', filepath])

def _on_regenerate_spreadsheet(self, button, filename):
    """Regenerate specific spreadsheet."""
    if not self.project:
        return
    
    from shypn.data.spreadsheet_generator import SpreadsheetGenerator
    generator = SpreadsheetGenerator(self.project)
    
    if filename == 'pathways.csv':
        generator.generate_pathways_csv()
    elif filename == 'enrichments.csv':
        generator.generate_enrichments_csv()
    elif filename == 'project_summary.csv':
        generator.generate_project_summary_csv()
    
    self._show_info(f"Regenerated {filename}")
```

---

## Advantages of Spreadsheet Approach

### 1. **Familiar Tool for Scientists** ✅
- Everyone knows Excel/Calc
- No learning curve
- Rich feature set (sort, filter, pivot tables, charts)

### 2. **Export-Ready** ✅
- CSV is universal format
- Copy-paste to publications
- Include in supplementary materials

### 3. **Human-Readable** ✅
- Open in any text editor
- Version control friendly (git diff works)
- Easy to inspect/debug

### 4. **Extensible** ✅
- Users can add columns (in their copy)
- Easy to merge data from multiple projects
- Import into R/Python for analysis

### 5. **Simple Implementation** ✅
- Python CSV module (built-in)
- No complex UI widgets needed
- Just generate and link

### 6. **Professional** ✅
- Standard format for data exchange
- Accepted by journals
- Easy to share with collaborators

---

## Comparison: TreeView vs Spreadsheet

| Aspect | TreeView (Phase 5 Design) | Spreadsheet (This Design) |
|--------|---------------------------|---------------------------|
| **Implementation** | ~800 lines of code | ~300 lines of code |
| **User Familiarity** | Custom UI to learn | Everyone knows spreadsheets |
| **Export** | Need export function | Already CSV format |
| **Sorting/Filtering** | Need to implement | Built-in to Excel/Calc |
| **Analysis** | View only | Can create charts, pivot tables |
| **Sharing** | Screenshot or export | Send CSV file directly |
| **Publications** | Need to format | Copy-paste to paper |
| **Version Control** | JSON only | CSV diffs are readable |
| **Extensibility** | Hard to add features | Users can customize |
| **Maintenance** | Need to update UI code | Just generate CSV |

---

## User Workflows

### Workflow 1: View Pathway Metadata
```
1. User opens PROJECT INFORMATION category
2. Sees list of spreadsheet files
3. Clicks [📂 Open] next to "pathways.csv"
4. LibreOffice Calc opens with pathway table
5. User can:
   - Sort by date
   - Filter by organism
   - Add personal notes column
   - Create chart of pathways over time
   - Export to PDF for report
```

### Workflow 2: Analyze Enrichments
```
1. User opens "enrichments.csv" in Excel
2. Creates pivot table:
   - Rows: Pathway_Name
   - Columns: Source
   - Values: Count of Enrichments
3. Creates chart showing which pathways have most enrichments
4. Filters by Confidence = "High"
5. Exports filtered data for paper's supplementary material
```

### Workflow 3: Project Report
```
1. User opens all three spreadsheets
2. Copy key stats from project_summary.csv
3. Copy pathway table from pathways.csv (filtered, sorted)
4. Copy enrichment details from enrichments.csv
5. Paste all into report document
6. Include metadata/ folder in project archive for sharing
```

### Workflow 4: Multi-Project Analysis
```
1. User has 5 projects with similar pathways
2. Opens pathways.csv from each project
3. Merges all into one master spreadsheet
4. Analyzes:
   - Which pathways are common?
   - Which have most enrichments?
   - Average confidence levels?
5. Creates comparison charts
```

---

## Implementation Timeline

**Phase 5 (Spreadsheet Approach):** 2-3 days (vs 4-6 for TreeView)

**Day 1:**
- Create SpreadsheetGenerator class
- Implement CSV generation (pathways, enrichments, summary)
- Add README generation

**Day 2:**
- Hook into import/enrichment workflows
- Update File Panel with spreadsheet links
- Test auto-generation

**Day 3:**
- Add export ZIP feature
- Polish UI
- Documentation and testing

---

## Success Criteria

✅ **Spreadsheets auto-generate** when pathways imported  
✅ **Spreadsheets auto-update** when enrichments applied  
✅ **File Panel shows links** to open spreadsheets  
✅ **Opening works** in LibreOffice/Excel  
✅ **Data is complete** (all metadata included)  
✅ **Format is clean** (readable, sortable)  
✅ **README is helpful** (explains structure)  
✅ **Export ZIP works** (for sharing)

---

## Next Steps

1. ✅ Design approved? (This document)
2. Implement SpreadsheetGenerator class
3. Hook into workflow (import/enrichment)
4. Update File Panel UI (links, not TreeViews)
5. Test with real data
6. Documentation

---

## Summary

**Key Innovation:** Instead of building custom TreeViews, **generate real spreadsheets** that users already know how to use.

**Advantages:**
- ✅ Simpler implementation (2-3 days vs 4-6)
- ✅ More powerful for users (sort, filter, analyze)
- ✅ Export-ready (CSV is universal)
- ✅ Professional (standard format)
- ✅ Extensible (users can customize)

**Trade-offs:**
- ❌ Not embedded in panel (opens external app)
- ❌ Context menus need separate implementation
- ✅ But these are minor compared to benefits!

**Recommendation:** Implement spreadsheet approach - better UX, less code, more professional! 🚀
