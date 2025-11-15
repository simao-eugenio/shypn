# Report Document Generation UI - Implementation Plan

**Branch:** Report_Doc_Generation  
**Date:** November 15, 2025  
**Status:** 🎯 PLANNING → IMPLEMENTATION

---

## Current State Analysis

### ✅ What's Working:
- Report Panel with 4 categories (Models, Parameters, Topology, Provenance)
- HTML export fully functional (`_on_export_html()`)
- Text export with clipboard copy (`_on_copy_text()`)
- Base category infrastructure (`base_category.py`)
- Per-document data storage (`document_report_data.py`)
- Float/attach panel mechanism working
- Wayland-safe implementation

### ❌ What's Missing:
- PDF export (shows "not implemented" dialog)
- Document template selection
- Metadata editor dialog
- User profile system
- Excel export
- Document preview

---

## Architecture Principles

### Critical Constraints:
1. **DO NOT disrupt panel show/hide mechanisms**
2. **DO NOT break float/attach functionality**
3. **Maintain Wayland compatibility**
4. **Minimize code in loaders**
5. **Use OOP with base classes and subclasses**
6. **Separate modules for each component**

### Design Patterns:
- **Strategy Pattern:** Document generators (PDF, Excel, HTML)
- **Template Method:** Base document generator with hooks
- **Builder Pattern:** Document assembly from sections
- **Singleton Pattern:** User profile manager

---

## Module Structure

```
src/shypn/
├── reporting/                          # NEW MODULE
│   ├── __init__.py
│   ├── generators/                     # Document generators
│   │   ├── __init__.py
│   │   ├── base_generator.py          # BaseDocumentGenerator (abstract)
│   │   ├── pdf_generator.py           # PDFGenerator (WeasyPrint)
│   │   ├── excel_generator.py         # ExcelGenerator (openpyxl)
│   │   └── html_generator.py          # HTMLGenerator (refactor existing)
│   ├── templates/                      # Document templates
│   │   ├── __init__.py
│   │   ├── base_template.py           # BaseTemplate (abstract)
│   │   ├── scientific_template.py     # Scientific report
│   │   ├── executive_template.py      # Executive summary
│   │   └── technical_template.py      # Technical spec
│   ├── metadata/                       # Metadata management
│   │   ├── __init__.py
│   │   ├── model_metadata.py          # ModelMetadata class
│   │   ├── user_profile.py            # UserProfile class
│   │   └── metadata_storage.py        # Storage utilities
│   └── ui/                             # UI components
│       ├── __init__.py
│       ├── metadata_dialog.py         # Edit Model Metadata
│       ├── profile_dialog.py          # User Profile Settings
│       ├── document_config_dialog.py  # Document generation config
│       └── export_toolbar.py          # Enhanced export toolbar widget
├── ui/panels/report/
│   ├── report_panel.py                # MODIFY: Add new toolbar
│   ├── base_category.py               # NO CHANGES
│   └── ... (other categories)         # NO CHANGES
```

---

## Phase 1: Metadata Infrastructure (Day 1-2)

### 1.1 Model Metadata Class
**File:** `src/shypn/reporting/metadata/model_metadata.py`

```python
class ModelMetadata:
    """Container for model metadata."""
    
    def __init__(self):
        # Basic Info
        self.model_name = ""
        self.model_id = ""
        self.version = "1.0"
        self.description = ""
        self.keywords = []
        
        # Authorship
        self.primary_author = ""
        self.contributors = []
        self.institution = ""
        self.department = ""
        self.contact_email = ""
        
        # Biological Context
        self.organism = ""
        self.biological_system = ""
        self.pathway_name = ""
        self.cell_type = ""
        
        # Provenance
        self.import_source = ""  # "SBML", "KEGG", "Manual"
        self.original_model_id = ""
        self.import_date = None
        self.modification_history = []
        
        # References
        self.publications = []  # List of DOIs/PubMed IDs
        self.related_models = []
        self.external_resources = []
    
    def to_dict(self):
        """Serialize to dictionary for storage."""
        
    def from_dict(self, data):
        """Deserialize from dictionary."""
    
    def validate(self):
        """Validate required fields."""
```

### 1.2 User Profile Class
**File:** `src/shypn/reporting/metadata/user_profile.py`

```python
class UserProfile:
    """User profile for report generation."""
    
    def __init__(self):
        # Personal Info
        self.full_name = ""
        self.email = ""
        self.orcid_id = ""
        self.phone = ""
        
        # Institutional
        self.institution = ""
        self.department = ""
        self.research_group = ""
        self.principal_investigator = ""
        self.address = ""
        
        # Preferences
        self.default_logo_path = ""
        self.default_license = "CC-BY-4.0"
        self.include_orcid = True
        self.report_language = "en"
    
    def save(self):
        """Save to encrypted storage."""
    
    @classmethod
    def load(cls):
        """Load from storage."""
    
    def validate_orcid(self):
        """Validate ORCID format."""
```

### 1.3 Metadata Storage
**File:** `src/shypn/reporting/metadata/metadata_storage.py`

```python
class MetadataStorage:
    """Utilities for saving/loading metadata."""
    
    @staticmethod
    def save_to_shypn_file(filepath, metadata):
        """Save metadata to .shypn file."""
    
    @staticmethod
    def load_from_shypn_file(filepath):
        """Load metadata from .shypn file."""
    
    @staticmethod
    def get_user_profile_path():
        """Get platform-specific profile path."""
        # Linux: ~/.config/shypn/user_profile.json
        # macOS: ~/Library/Application Support/shypn/user_profile.json
        # Windows: %APPDATA%/shypn/user_profile.json
```

---

## Phase 2: UI Dialogs (Day 3-4)

### 2.1 Metadata Editor Dialog
**File:** `src/shypn/reporting/ui/metadata_dialog.py`

**Design:**
```
┌─────────────────────────────────────────────────────┐
│ Edit Model Metadata                        [✖]      │
├─────────────────────────────────────────────────────┤
│ Notebook with tabs:                                 │
│ [Basic] [Authors] [Biology] [Provenance] [Refs]    │
│                                                     │
│ ┌─ Basic Information ─────────────────────────┐   │
│ │ Model Name: [________________________]      │   │
│ │ Model ID:   [________________________]      │   │
│ │ Version:    [________________________]      │   │
│ │ Description:                                │   │
│ │ [______________________________________]    │   │
│ │ [______________________________________]    │   │
│ │ Keywords: [_____] [Add]                     │   │
│ │ [tag1] [x] [tag2] [x]                       │   │
│ └─────────────────────────────────────────────┘   │
│                                                     │
│                    [Cancel] [Save]                  │
└─────────────────────────────────────────────────────┘
```

**Implementation:**
- Extends `Gtk.Dialog`
- Uses `Gtk.Notebook` for tabs
- Loads from `ModelMetadata` instance
- Saves back to `.shypn` file on "Save"
- Modal dialog (blocks parent)

### 2.2 User Profile Dialog
**File:** `src/shypn/reporting/ui/profile_dialog.py`

**Design:**
```
┌─────────────────────────────────────────────────────┐
│ User Profile Settings                      [✖]      │
├─────────────────────────────────────────────────────┤
│ Notebook with tabs:                                 │
│ [Personal] [Institution] [Preferences]              │
│                                                     │
│ ┌─ Personal Information ──────────────────────┐   │
│ │ Full Name: * [________________________]     │   │
│ │ Email: *     [________________________]     │   │
│ │ ORCID iD:    [________________________] [✓] │   │
│ │ Phone:       [________________________]     │   │
│ └─────────────────────────────────────────────┘   │
│                                                     │
│ * Required fields                                   │
│                                                     │
│                    [Cancel] [Save]                  │
└─────────────────────────────────────────────────────┘
```

**Implementation:**
- Extends `Gtk.Dialog`
- ORCID validation with checkmark icon
- Saves to encrypted user config
- Accessible from Edit → Preferences → User Profile

### 2.3 Document Configuration Dialog
**File:** `src/shypn/reporting/ui/document_config_dialog.py`

**Design:**
```
┌─────────────────────────────────────────────────────┐
│ Generate Document                          [✖]      │
├─────────────────────────────────────────────────────┤
│ Document Type:                                      │
│ ○ Scientific Report (Full detail)                   │
│ ○ Executive Summary (Key findings)                  │
│ ○ Technical Specification (All data)                │
│                                                     │
│ Export Format:                                      │
│ ☑ PDF    ☐ Excel    ☐ HTML                         │
│                                                     │
│ Include Sections:                                   │
│ ☑ Model Structure    ☑ Parameters                  │
│ ☑ Topology Analysis  ☑ Provenance                  │
│ ☑ Simulation Results ☑ Figures                     │
│                                                     │
│ Options:                                            │
│ ☑ Include logo       ☑ Table of contents           │
│ ☑ Page numbers       ☑ Header/Footer               │
│                                                     │
│ Output: [/path/to/report.pdf] [Browse...]          │
│                                                     │
│              [Preview] [Cancel] [Generate]          │
└─────────────────────────────────────────────────────┘
```

**Implementation:**
- Extends `Gtk.Dialog`
- RadioButtons for document type
- CheckButtons for sections and options
- FileChooserButton for output path
- Returns configuration dict on "Generate"

---

## Phase 3: Export Toolbar Widget (Day 5)

### 3.1 Enhanced Toolbar
**File:** `src/shypn/reporting/ui/export_toolbar.py`

```python
class ExportToolbar(Gtk.Box):
    """Enhanced export toolbar for Report Panel.
    
    Replaces the simple export buttons with a professional
    document generation interface.
    """
    
    def __init__(self, report_panel):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.report_panel = report_panel
        
        # Metadata button
        self.metadata_btn = Gtk.Button(label="📝 Edit Metadata")
        self.metadata_btn.connect('clicked', self._on_edit_metadata)
        
        # Profile button
        self.profile_btn = Gtk.Button(label="👤 User Profile")
        self.profile_btn.connect('clicked', self._on_edit_profile)
        
        # Document type dropdown
        self.doc_type_combo = Gtk.ComboBoxText()
        self.doc_type_combo.append_text("Scientific Report")
        self.doc_type_combo.append_text("Executive Summary")
        self.doc_type_combo.append_text("Technical Spec")
        self.doc_type_combo.set_active(0)
        
        # Generate button
        self.generate_btn = Gtk.Button(label="📤 Generate Document")
        self.generate_btn.connect('clicked', self._on_generate)
        
        # Pack widgets
        self.pack_start(self.metadata_btn, False, False, 0)
        self.pack_start(self.profile_btn, False, False, 0)
        self.pack_start(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL), False, False, 6)
        self.pack_start(Gtk.Label(label="Document:"), False, False, 0)
        self.pack_start(self.doc_type_combo, False, False, 0)
        self.pack_start(self.generate_btn, False, False, 0)
    
    def _on_edit_metadata(self, button):
        """Show metadata editor dialog."""
        
    def _on_edit_profile(self, button):
        """Show user profile dialog."""
    
    def _on_generate(self, button):
        """Show document configuration and generate."""
```

### 3.2 Integration with Report Panel
**File:** `src/shypn/ui/panels/report/report_panel.py`

**Changes:**
```python
# In _build_ui() method, REPLACE the _create_export_buttons() section:

# OLD CODE (remove):
# export_buttons = self._create_export_buttons()
# self.pack_start(export_buttons, False, False, 0)

# NEW CODE:
from shypn.reporting.ui.export_toolbar import ExportToolbar

# Create enhanced export toolbar
self.export_toolbar = ExportToolbar(self)
self.pack_start(self.export_toolbar, False, False, 0)
```

**Key Points:**
- Toolbar inserted BEFORE category content
- No changes to float button logic
- No changes to show/hide mechanisms
- Maintains Wayland compatibility

---

## Phase 4: Document Generators (Day 6-8)

### 4.1 Base Generator (Abstract)
**File:** `src/shypn/reporting/generators/base_generator.py`

```python
from abc import ABC, abstractmethod

class BaseDocumentGenerator(ABC):
    """Abstract base class for document generators."""
    
    def __init__(self, template_type, metadata, content_sections):
        self.template_type = template_type  # "scientific", "executive", "technical"
        self.metadata = metadata  # ModelMetadata instance
        self.user_profile = UserProfile.load()
        self.content_sections = content_sections  # List of category exports
    
    @abstractmethod
    def generate(self, output_path):
        """Generate document to output_path."""
        pass
    
    @abstractmethod
    def get_supported_formats(self):
        """Return list of supported format extensions."""
        pass
    
    def _build_header(self):
        """Build document header with branding."""
        # Shared header logic for all formats
        
    def _build_toc(self):
        """Build table of contents."""
        
    def _format_section(self, section_data):
        """Format a content section."""
```

### 4.2 PDF Generator
**File:** `src/shypn/reporting/generators/pdf_generator.py`

```python
from weasyprint import HTML, CSS
from .base_generator import BaseDocumentGenerator

class PDFGenerator(BaseDocumentGenerator):
    """Generate PDF documents using WeasyPrint."""
    
    def generate(self, output_path):
        """Generate PDF document."""
        # 1. Build HTML from template
        html_content = self._build_html()
        
        # 2. Apply CSS styling
        css = self._get_css_for_template()
        
        # 3. Convert to PDF
        HTML(string=html_content).write_pdf(
            output_path,
            stylesheets=[CSS(string=css)]
        )
    
    def get_supported_formats(self):
        return ['.pdf']
    
    def _build_html(self):
        """Build complete HTML document."""
        # Use template system
        
    def _get_css_for_template(self):
        """Get CSS based on template type."""
```

### 4.3 Excel Generator
**File:** `src/shypn/reporting/generators/excel_generator.py`

```python
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from .base_generator import BaseDocumentGenerator

class ExcelGenerator(BaseDocumentGenerator):
    """Generate Excel workbooks using openpyxl."""
    
    def generate(self, output_path):
        """Generate Excel workbook."""
        wb = Workbook()
        
        # Create sheets
        self._create_summary_sheet(wb)
        self._create_structure_sheet(wb)
        self._create_parameters_sheet(wb)
        self._create_results_sheet(wb)
        self._create_topology_sheet(wb)
        self._create_provenance_sheet(wb)
        
        # Save
        wb.save(output_path)
    
    def get_supported_formats(self):
        return ['.xlsx', '.xls']
```

---

## Phase 5: Template System (Day 9-10)

### 5.1 Base Template
**File:** `src/shypn/reporting/templates/base_template.py`

```python
from abc import ABC, abstractmethod

class BaseTemplate(ABC):
    """Abstract base class for document templates."""
    
    @abstractmethod
    def get_html_structure(self):
        """Return HTML structure for this template."""
        
    @abstractmethod
    def get_css_styles(self):
        """Return CSS styles for this template."""
    
    @abstractmethod
    def get_included_sections(self):
        """Return list of sections to include."""
```

### 5.2 Scientific Template
**File:** `src/shypn/reporting/templates/scientific_template.py`

```python
class ScientificTemplate(BaseTemplate):
    """Scientific report template - full detail."""
    
    def get_html_structure(self):
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>{{model_name}} - Scientific Report</title>
        </head>
        <body>
            {{header}}
            {{toc}}
            {{abstract}}
            {{introduction}}
            {{methods}}
            {{results}}
            {{discussion}}
            {{references}}
            {{appendices}}
        </body>
        </html>
        """
    
    def get_included_sections(self):
        return ['all']  # Include everything
```

---

## Implementation Checklist

### Week 1: Foundation
- [ ] Create `src/shypn/reporting/` module structure
- [ ] Implement `ModelMetadata` class with serialization
- [ ] Implement `UserProfile` class with storage
- [ ] Implement `MetadataStorage` utilities
- [ ] Add metadata fields to `.shypn` file format
- [ ] Test metadata save/load

### Week 2: UI Components
- [ ] Implement `MetadataDialog` with all tabs
- [ ] Implement `ProfileDialog` with validation
- [ ] Implement `DocumentConfigDialog`
- [ ] Implement `ExportToolbar` widget
- [ ] Integrate toolbar into `report_panel.py`
- [ ] Test dialogs on Wayland and X11

### Week 3: Document Generation
- [ ] Implement `BaseDocumentGenerator` abstract class
- [ ] Implement `PDFGenerator` with WeasyPrint
- [ ] Implement `ExcelGenerator` with openpyxl
- [ ] Implement template system (3 templates)
- [ ] Wire up generate button to generators
- [ ] Test PDF/Excel output

### Week 4: Polish & Testing
- [ ] Progress dialog during generation
- [ ] Error handling and validation
- [ ] Preview functionality
- [ ] Documentation updates
- [ ] User testing
- [ ] Final integration testing

---

## Testing Strategy

### Unit Tests:
- Metadata serialization/deserialization
- User profile save/load
- Template rendering
- Generator output validation

### Integration Tests:
- Dialog open/close without disrupting panel
- Float/attach mechanism still works
- Wayland compatibility
- Generate actual PDF/Excel from test data

### Manual Tests:
- Metadata persistence across sessions
- User profile reuse across projects
- Document generation with all templates
- Export with various section combinations

---

## Dependencies

### Add to `pyproject.toml`:
```toml
[project]
dependencies = [
    # ... existing dependencies ...
    "weasyprint>=60.0",      # PDF from HTML
    "openpyxl>=3.1.0",       # Excel export
    "Pillow>=10.0.0",        # Image handling for PDFs
    "cryptography>=41.0.0",  # Secure credential storage
]
```

---

## Non-Goals (Out of Scope)

- Real-time document preview (too complex)
- Cloud storage integration
- External database auth (separate feature)
- LaTeX export (future)
- Multi-language templates (future)
- Collaborative editing (future)

---

## Success Criteria

1. ✅ Metadata editor saves/loads correctly
2. ✅ User profile persists across sessions
3. ✅ PDF generation produces readable documents
4. ✅ Excel export includes all data sheets
5. ✅ No disruption to panel float/attach mechanisms
6. ✅ Wayland compatibility maintained
7. ✅ All dialogs are modal and non-blocking to main UI
8. ✅ Generated documents include proper headers/branding

---

## Notes

- **Wayland Safety:** All dialogs use `transient_for` and modal flags
- **Float/Attach:** No changes to `float_button` logic in report panel
- **OOP Design:** Clear separation of concerns, base classes for extension
- **Minimal Loader Code:** All logic in dedicated modules, loaders just wire up
- **Progressive Enhancement:** Start with basic PDF, enhance with templates

---

**Next Steps:** Begin Phase 1 implementation with metadata infrastructure.
