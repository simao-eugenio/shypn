# Export Module

**Location:** `src/shypn/export/`  
**Purpose:** Export Petri Net models to various formats (PDF, PNG, SVG)  
**Architecture:** OOP with base class and format-specific subclasses

---

## Quick Start

```python
from shypn.export import PDFExporter

# Create exporter with Wayland-safe parent window
exporter = PDFExporter(parent_window=main_window)

# Show file dialog and export
filepath = exporter.show_file_dialog(default_filename="mymodel")
if filepath:
    success = exporter.export(manager, filepath)
```

## Architecture

```
BaseExporter (Abstract)
└── PDFExporter (Cairo PDFSurface)
    └── Future: PNGExporter, SVGExporter
```

### Base Class: `BaseExporter`

Common functionality for all export formats:
- ✅ Bounding box calculation
- ✅ File dialog management (Wayland-safe)
- ✅ Error handling (`ExportError`)
- ✅ Export validation
- ✅ Template method pattern

### PDF Exporter: `PDFExporter`

Vector PDF export using Cairo:
- ✅ Native Cairo PDFSurface
- ✅ Same rendering as canvas display
- ✅ Vector graphics (infinitely scalable)
- ✅ White background with padding
- ✅ Zero external dependencies

## Files

| File | Purpose | Lines |
|------|---------|-------|
| `__init__.py` | Package exports | ~20 |
| `base_exporter.py` | Abstract base class | ~200 |
| `pdf_exporter.py` | PDF implementation | ~100 |

## Menu Integration

**File Menu:**
- Export to PDF... (Ctrl+E)

**Implementation:**
- Minimal code in `menu_actions.py` (just delegates to exporter)
- Business logic in exporter classes
- Wayland-safe parent window handling

## Testing

**File:** `tests/test_pdf_exporter.py`

```bash
# Run tests
pytest tests/test_pdf_exporter.py -v

# With coverage
pytest tests/test_pdf_exporter.py --cov=shypn.export
```

**Test Classes:**
- `TestBaseExporter` - Common functionality
- `TestPDFExporter` - PDF-specific tests
- `TestCairoIntegration` - Cairo rendering
- `TestErrorHandling` - Error scenarios

## Documentation

- **User Guide:** See [QUICKSTART.md](../../doc/QUICKSTART.md)
- **Architecture:** See [EXPORT_SYSTEM.md](../../doc/EXPORT_SYSTEM.md)
- **Implementation Plan:** See [PLAN_PDF_EXPORT_CAIRO.md](../../doc/PLAN_PDF_EXPORT_CAIRO.md)

## Error Handling

```python
from shypn.export import PDFExporter, ExportError

try:
    exporter = PDFExporter(parent_window=window)
    success = exporter.export(manager, filepath)
except ExportError as e:
    # User-friendly error message
    show_error_dialog(str(e))
```

**ExportError raised for:**
- Empty models (no objects)
- Missing manager/filepath
- Cairo rendering errors
- File I/O errors

## Future Formats

### PNG Export (Planned)
```python
from shypn.export import PNGExporter

exporter = PNGExporter(parent_window=window, dpi=300)
exporter.export(manager, "model.png")
```

### SVG Export (Planned)
```python
from shypn.export import SVGExporter

exporter = SVGExporter(parent_window=window)
exporter.export(manager, "model.svg")
```

## Design Principles

1. **OOP Architecture** - Base class with format subclasses
2. **Separation of Concerns** - Logic in exporters, not loaders
3. **Wayland-Safe** - Proper parent window handling
4. **Cairo Integration** - Reuses existing rendering
5. **Testable** - Comprehensive unit tests with mocks

## Performance

| Model Size | Objects | Export Time | File Size |
|------------|---------|-------------|-----------|
| Small | 10-20 | < 100ms | 10-20 KB |
| Medium | 50-100 | < 500ms | 50-100 KB |
| Large | 200-500 | < 2s | 200-500 KB |
| Very Large | 1000+ | < 5s | 1-2 MB |

---

**Status:** ✅ Implemented (PDF)  
**Version:** 1.0  
**Date:** December 30, 2025
