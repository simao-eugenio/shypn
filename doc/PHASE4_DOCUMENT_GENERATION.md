# Phase 4: Document Generation System

## Overview

Phase 4 implements a comprehensive document generation system for creating professional reports from model metadata. The system supports three output formats (PDF, Excel, HTML) and three document types (Technical, Publication, Summary).

## Architecture

### Generator Classes

All generators inherit from `BaseDocumentGenerator` which provides:
- Common document composition logic
- Template management infrastructure  
- Metadata and user profile integration
- Document type enumeration (TECHNICAL, PUBLICATION, SUMMARY)

**Implemented Generators:**

1. **HTMLGenerator** (`html_generator.py`)
   - Generates styled HTML documents with embedded CSS
   - Three document types with different layouts
   - No external dependencies

2. **PDFGenerator** (`pdf_generator.py`)
   - Converts HTML to PDF using WeasyPrint
   - PDF-specific CSS for optimal print layout
   - Requires: `weasyprint>=60.0`

3. **ExcelGenerator** (`excel_generator.py`)
   - Creates multi-sheet Excel workbooks
   - Formatted tables with styling
   - Requires: `openpyxl>=3.1.0`

### Document Types

**TECHNICAL** - Comprehensive technical report including:
- Basic information
- Complete authorship details
- Biological context
- Provenance information
- References
- System information

**PUBLICATION** - Publication-ready document focusing on:
- Title and authors
- Abstract (from description)
- Biological system overview
- Model information
- References

**SUMMARY** - Brief summary sheet with:
- Key facts table
- Essential metadata only
- Quick overview format

## File Structure

```
src/shypn/reporting/generators/
├── __init__.py              # Package exports
├── base_generator.py        # Abstract base class
├── html_generator.py        # HTML generation
├── pdf_generator.py         # PDF generation (WeasyPrint)
└── excel_generator.py       # Excel generation (openpyxl)
```

## Integration

### ExportToolbar Integration

The generators are fully integrated into the Report Panel's ExportToolbar:

```python
# In export_toolbar.py
from shypn.reporting.generators import (
    HTMLGenerator, PDFGenerator, ExcelGenerator, DocumentType
)
```

**Button Actions:**
- **PDF Button**: Opens document type dialog → file chooser → generates PDF
- **Excel Button**: Opens document type dialog → file chooser → generates workbook
- **HTML Button**: Opens document type dialog → file chooser → generates HTML

**Error Handling:**
- Missing dependencies show informative error dialogs
- File chooser with overwrite confirmation
- Success/failure notifications

### Metadata Requirements

All generators require `ModelMetadata` to be populated. Minimal fields:
- `model_name` - Model name
- `description` - Model description (optional but recommended)
- `primary_author` - Author name (optional)

Optional but enhances output:
- Authorship: contributors, institution, department, contact_email
- Biological context: organism, biological_system, pathway_name, cell_type
- References: publications (list of DOI/PubMed IDs)
- Provenance: import_source, original_model_id, import_date

## Usage

### Programmatic Usage

```python
from pathlib import Path
from shypn.reporting import ModelMetadata, UserProfile
from shypn.reporting.generators import HTMLGenerator, DocumentType

# Create metadata
metadata = ModelMetadata()
metadata.model_name = "My Model"
metadata.description = "A test model"
metadata.organism = "Homo sapiens"

# Generate document
generator = HTMLGenerator(metadata)
success = generator.generate(
    output_path=Path("output.html"),
    document_type=DocumentType.TECHNICAL,
    include_timestamp=True
)
```

### UI Usage

1. Open a model in Shypn
2. Click **Metadata** button in Report Panel
3. Fill in metadata fields
4. Click **Save** (metadata stored in .shypn file)
5. Click **PDF**, **Excel**, or **HTML** button
6. Choose document type (Technical/Publication/Summary)
7. Choose save location
8. Document generated

## Dependencies

Added to `pyproject.toml`:

```toml
dependencies = [
    "weasyprint>=60.0",      # PDF generation
    "openpyxl>=3.1.0",       # Excel generation
    "platformdirs>=4.0.0",   # User profile storage
]
```

**Installation:**

```bash
# Install all dependencies
pip install -e .

# Or install individually
pip install weasyprint openpyxl platformdirs
```

**Note:** WeasyPrint requires system dependencies on some platforms:
- Linux: `apt install libpango-1.0-0 libpangocairo-1.0-0`
- macOS: Usually works out of the box
- Windows: Download GTK runtime

## Testing

### Test Script

Run `test_phase4_generators.py` to verify all generators:

```bash
cd /home/simao/projetos/shypn
PYTHONPATH=/home/simao/projetos/shypn/src python3 test_phase4_generators.py
```

**Test Output:**
- Generates 3 HTML files (technical, publication, summary)
- Generates 1 PDF file (if WeasyPrint installed)
- Generates 3 Excel files (if openpyxl installed)
- All files saved to `test_output/` directory

### Manual Testing

1. Start Shypn application
2. Load a model
3. Edit metadata (Metadata button)
4. Try each export button
5. Verify generated documents

## Features

### HTML Generator

**Strengths:**
- No dependencies required
- Embedded CSS styling
- Responsive design
- View in any web browser
- Easy to share

**CSS Styling:**
- Professional typography
- Colored section headers
- Formatted tables
- Print-friendly layouts
- Document-type-specific styles

### PDF Generator

**Strengths:**
- Print-ready output
- Professional appearance
- Portable format
- Page breaks optimized

**Implementation:**
- Reuses HTMLGenerator internally
- Adds PDF-specific CSS
- A4 page size with margins
- Handles page breaks intelligently

### Excel Generator

**Strengths:**
- Structured data format
- Multiple sheets organization
- Cell formatting and styling
- Easily editable
- Data analysis ready

**Workbook Structure:**
- Summary sheet (always)
- Basic Information sheet
- Authorship sheet (with contributor details)
- Biological Context sheet
- Provenance sheet (Technical only)
- References sheet
- System Information sheet (Technical only)

## Future Enhancements

### Planned for Future Phases

1. **Template System**
   - User-customizable HTML templates
   - Template gallery
   - Custom CSS injection

2. **Analysis Data Integration**
   - Include simulation results
   - Add viability analysis tables
   - Export graphs/charts

3. **Batch Export**
   - Export multiple models at once
   - Automated report generation
   - Scheduled exports

4. **Additional Formats**
   - Markdown export
   - LaTeX export
   - DOCX export

## Troubleshooting

### WeasyPrint Installation Issues

**Linux:**
```bash
# Install system dependencies first
sudo apt install libpango-1.0-0 libharfbuzz0b libpangoft2-1.0-0
pip install weasyprint
```

**macOS:**
```bash
# Usually works directly
pip install weasyprint
```

**Windows:**
- Download GTK3 runtime from https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer
- Install GTK3
- Then: `pip install weasyprint`

### Missing Metadata

If exports are empty or minimal:
1. Click **Metadata** button
2. Fill in at least `model_name` and `description`
3. Add authorship and biological context for richer reports
4. Click **Save**
5. Try export again

### Permission Errors

If file save fails:
- Check write permissions in target directory
- Close file if already open (Excel especially)
- Choose different filename

## Implementation Notes

### Metadata Structure Alignment

Generators are aligned with the actual `ModelMetadata` structure:
- Uses `model_name` not `name`
- Uses `model_id` not `id`
- Uses `primary_author` and `contributors` list
- Publications are simple strings (DOIs/PubMed IDs)
- Dates stored in `system` section

### Error Handling

All generators include:
- Try-catch blocks for generation errors
- Import error detection for missing dependencies
- Informative error messages to users
- Graceful degradation (missing fields = empty sections)

### Performance

- HTML generation: < 100ms for typical model
- PDF generation: 1-2 seconds (WeasyPrint rendering)
- Excel generation: < 500ms for typical model

## Credits

**Author:** Simão Eugénio  
**Date:** November 15, 2025  
**Phase:** 4 - Document Generation System  
**Branch:** Report_Doc_Generation
