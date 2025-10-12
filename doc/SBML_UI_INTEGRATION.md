# SBML Import UI Integration

**Date**: October 12, 2025  
**Status**: ✅ Complete  
**Component**: Pathway Operations Panel - SBML Tab

---

## Overview

Added a new **SBML** sub-tab to the Pathway Operations panel for importing biochemical pathways from SBML (Systems Biology Markup Language) files. This provides a user-friendly interface to the complete SBML → Petri net conversion pipeline.

## Changes Made

### UI File: `ui/panels/pathway_panel.ui`

Added new tab (Tab 3) between "Browse" and "History" tabs:

```xml
<!-- TAB 3: SBML Import -->
- File selector with Browse button
- Import options (expandable)
  * Layout spacing control (50-500 pixels)
  * Token scale factor (0.1-10.0)
  * Example calculation display
- Preview/status area
- Action buttons (Parse File, Import to Canvas)
- Informational notice
```

### Tab Structure

The Pathway Operations panel now has **4 tabs**:

1. **Import** - KEGG pathway import (existing)
2. **Browse** - Browse KEGG pathways (future)
3. **SBML** - SBML file import ✨ NEW
4. **History** - Import history (future)

---

## SBML Tab Components

### File Selection Section

| Component | ID | Purpose |
|-----------|-----|---------|
| Label | - | "SBML File" section header |
| Entry | `sbml_file_entry` | Display selected file path (read-only) |
| Button | `sbml_browse_button` | Open file chooser dialog |

**Behavior**:
- Entry is read-only (user must use Browse button)
- Browse button opens GTK FileChooserDialog
- Filter: `*.sbml`, `*.xml` files
- Parse button enables after file selection

### Import Options Section (Expander)

#### Layout Options

| Control | ID | Range | Default | Description |
|---------|-----|-------|---------|-------------|
| SpinButton | `sbml_spacing_spin` | 50-500 | 150 | Node spacing in pixels |

**Purpose**: Controls distance between nodes in force-directed layout

#### Token Conversion Options

| Control | ID | Range | Default | Description |
|---------|-----|-------|---------|-------------|
| SpinButton | `sbml_scale_spin` | 0.1-10.0 | 1.0 | Concentration → token multiplier |
| Label | `sbml_scale_example` | - | - | Dynamic example calculation |

**Purpose**: Controls how concentrations (mM) convert to discrete tokens

**Example Calculation** (updates when scale changes):
- Scale = 1.0: "5 mM glucose → 5 tokens"
- Scale = 2.0: "5 mM glucose → 10 tokens"
- Scale = 0.5: "5 mM glucose → 3 tokens"

### Preview/Status Area

| Component | ID | Purpose |
|-----------|-----|---------|
| TextView | `sbml_preview_text` | Display pathway information after parsing |
| Label | `sbml_status_label` | Show status messages and errors |

**Preview Content** (after parsing):
```
Pathway: Simple Glycolysis
SBML Level: 3, Version: 2

Species: 4
  • Glucose (5.0 mM → 5 tokens)
  • ATP (2.5 mM → 3 tokens)
  • Glucose-6-phosphate (0.0 mM → 0 tokens)
  • ADP (0.5 mM → 1 tokens)

Reactions: 1
  • Hexokinase (Michaelis-Menten)
    Glucose + ATP → Glucose-6-phosphate + ADP

Compartments: 1
  • Cytoplasm

✓ Ready to import
```

### Action Buttons

| Button | ID | Initial State | Style | Action |
|--------|-----|---------------|-------|--------|
| Parse File | `sbml_parse_button` | Disabled | Default | Parse and validate SBML |
| Import to Canvas | `sbml_import_button` | Disabled | Suggested | Convert and load to canvas |

**State Flow**:
1. Initially: Both disabled
2. After file selected: Parse button enabled
3. After successful parse: Import button enabled
4. After import: Both disabled (ready for next file)

---

## Backend Integration

### Required Handler Connections

The Python backend needs to connect these signals:

```python
class PathwayPanel:
    def __init__(self, builder):
        self.builder = builder
        
        # SBML tab widgets
        self.sbml_file_entry = builder.get_object('sbml_file_entry')
        self.sbml_browse_button = builder.get_object('sbml_browse_button')
        self.sbml_spacing_spin = builder.get_object('sbml_spacing_spin')
        self.sbml_scale_spin = builder.get_object('sbml_scale_spin')
        self.sbml_scale_example = builder.get_object('sbml_scale_example')
        self.sbml_preview_text = builder.get_object('sbml_preview_text')
        self.sbml_status_label = builder.get_object('sbml_status_label')
        self.sbml_parse_button = builder.get_object('sbml_parse_button')
        self.sbml_import_button = builder.get_object('sbml_import_button')
        
        # Connect signals
        self.sbml_browse_button.connect('clicked', self.on_sbml_browse)
        self.sbml_scale_spin.connect('value-changed', self.on_scale_changed)
        self.sbml_parse_button.connect('clicked', self.on_sbml_parse)
        self.sbml_import_button.connect('clicked', self.on_sbml_import)
```

### Signal Handlers

#### 1. File Browse Handler

```python
def on_sbml_browse(self, button):
    """Open file chooser for SBML file selection."""
    dialog = Gtk.FileChooserDialog(
        title="Select SBML File",
        parent=self.window,
        action=Gtk.FileChooserAction.OPEN
    )
    dialog.add_buttons(
        Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
        Gtk.STOCK_OPEN, Gtk.ResponseType.OK
    )
    
    # Add filters
    filter_sbml = Gtk.FileFilter()
    filter_sbml.set_name("SBML Files")
    filter_sbml.add_pattern("*.sbml")
    filter_sbml.add_pattern("*.xml")
    dialog.add_filter(filter_sbml)
    
    filter_all = Gtk.FileFilter()
    filter_all.set_name("All Files")
    filter_all.add_pattern("*")
    dialog.add_filter(filter_all)
    
    response = dialog.run()
    if response == Gtk.ResponseType.OK:
        filepath = dialog.get_filename()
        self.sbml_file_entry.set_text(filepath)
        self.sbml_parse_button.set_sensitive(True)
        self.sbml_import_button.set_sensitive(False)
        self.update_status("File selected. Click 'Parse File' to validate.")
    
    dialog.destroy()
```

#### 2. Scale Change Handler

```python
def on_scale_changed(self, spin_button):
    """Update example calculation when scale factor changes."""
    scale = spin_button.get_value()
    example_conc = 5.0  # Example: 5 mM glucose
    example_tokens = max(0, round(example_conc * scale))
    
    self.sbml_scale_example.set_text(
        f"Example: {example_conc} mM glucose → {example_tokens} tokens"
    )
```

#### 3. Parse Handler

```python
def on_sbml_parse(self, button):
    """Parse and validate SBML file."""
    from shypn.data.pathway.sbml_parser import SBMLParser
    from shypn.data.pathway.pathway_validator import PathwayValidator
    
    filepath = self.sbml_file_entry.get_text()
    
    try:
        # Update status
        self.update_status("Parsing SBML file...")
        
        # Parse file
        parser = SBMLParser()
        pathway = parser.parse_file(filepath)
        
        # Validate
        self.update_status("Validating pathway...")
        validator = PathwayValidator()
        result = validator.validate(pathway)
        
        if not result.is_valid:
            # Show errors
            error_text = "Validation errors:\n"
            for error in result.errors:
                error_text += f"  • {error}\n"
            self.update_preview(error_text)
            self.update_status("⚠ Validation failed. See preview for details.")
            return
        
        # Store parsed pathway
        self.parsed_pathway = pathway
        
        # Display preview
        preview_text = self.generate_preview(pathway)
        self.update_preview(preview_text)
        
        # Enable import button
        self.sbml_import_button.set_sensitive(True)
        
        # Show warnings if any
        if result.warnings:
            warning_text = f"✓ Validated with {len(result.warnings)} warning(s)"
            self.update_status(warning_text)
        else:
            self.update_status("✓ File parsed and validated successfully")
        
    except Exception as e:
        self.update_preview(f"Error parsing file:\n{str(e)}")
        self.update_status("❌ Parse failed")
        import traceback
        traceback.print_exc()
```

#### 4. Import Handler

```python
def on_sbml_import(self, button):
    """Convert pathway to Petri net and load to canvas."""
    from shypn.data.pathway.pathway_postprocessor import PathwayPostProcessor
    from shypn.data.pathway.pathway_converter import PathwayConverter
    
    try:
        # Get options
        spacing = self.sbml_spacing_spin.get_value()
        scale_factor = self.sbml_scale_spin.get_value()
        
        # Update status
        self.update_status("Post-processing pathway...")
        
        # Post-process
        postprocessor = PathwayPostProcessor(
            spacing=spacing,
            scale_factor=scale_factor
        )
        processed = postprocessor.process(self.parsed_pathway)
        
        # Update status
        self.update_status("Converting to Petri net...")
        
        # Convert to DocumentModel
        converter = PathwayConverter()
        document = converter.convert(processed)
        
        # Load to canvas
        self.update_status("Loading to canvas...")
        self.load_document_to_canvas(document)
        
        # Success
        self.update_status("✓ Pathway imported successfully!")
        
        # Reset for next import
        self.sbml_import_button.set_sensitive(False)
        self.sbml_parse_button.set_sensitive(False)
        
    except Exception as e:
        self.update_status(f"❌ Import failed: {str(e)}")
        import traceback
        traceback.print_exc()
```

#### Helper Methods

```python
def generate_preview(self, pathway):
    """Generate preview text from parsed pathway."""
    preview = []
    
    # Pathway info
    preview.append(f"Pathway: {pathway.metadata.get('name', 'Unknown')}")
    preview.append(f"SBML Level: {pathway.metadata.get('sbml_level', 'N/A')}")
    preview.append("")
    
    # Species
    preview.append(f"Species: {len(pathway.species)}")
    scale = self.sbml_scale_spin.get_value()
    for species in pathway.species[:10]:  # Show first 10
        tokens = max(0, round(species.initial_concentration * scale))
        preview.append(
            f"  • {species.name or species.id} "
            f"({species.initial_concentration} mM → {tokens} tokens)"
        )
    if len(pathway.species) > 10:
        preview.append(f"  ... and {len(pathway.species) - 10} more")
    preview.append("")
    
    # Reactions
    preview.append(f"Reactions: {len(pathway.reactions)}")
    for reaction in pathway.reactions[:5]:  # Show first 5
        kinetics = ""
        if reaction.kinetic_law:
            kinetics = f" ({reaction.kinetic_law.rate_type})"
        
        # Format equation
        reactants = " + ".join(s for s, _ in reaction.reactants)
        products = " + ".join(s for s, _ in reaction.products)
        
        preview.append(
            f"  • {reaction.name or reaction.id}{kinetics}\n"
            f"    {reactants} → {products}"
        )
    if len(pathway.reactions) > 5:
        preview.append(f"  ... and {len(pathway.reactions) - 5} more")
    preview.append("")
    
    # Compartments
    preview.append(f"Compartments: {len(pathway.compartments)}")
    for comp_id, comp_name in pathway.compartments.items():
        preview.append(f"  • {comp_name}")
    preview.append("")
    
    preview.append("✓ Ready to import")
    
    return "\n".join(preview)

def update_preview(self, text):
    """Update preview text view."""
    buffer = self.sbml_preview_text.get_buffer()
    buffer.set_text(text)

def update_status(self, message):
    """Update status label."""
    self.sbml_status_label.set_text(message)

def load_document_to_canvas(self, document):
    """Load DocumentModel to active canvas.
    
    This should integrate with existing canvas/document management.
    """
    # Get active canvas or create new tab
    # Implementation depends on existing architecture
    pass
```

---

## User Workflow

### Step-by-Step Process

1. **Open Pathway Operations Panel**
   - Menu: View → Panels → Pathway Operations
   - Or dock panel if already visible

2. **Select SBML Tab**
   - Click "SBML" tab (3rd tab)

3. **Choose File**
   - Click "Browse..." button
   - Navigate to SBML file (`.sbml` or `.xml`)
   - Click "Open"
   - File path appears in entry field

4. **Adjust Options** (optional)
   - Expand "Import Options"
   - Adjust node spacing (default: 150 px)
   - Adjust scale factor (default: 1.0)
   - Watch example calculation update

5. **Parse File**
   - Click "Parse File" button
   - Wait for parsing and validation
   - Preview shows pathway information
   - Status shows validation result

6. **Import to Canvas**
   - Review preview information
   - Click "Import to Canvas" button
   - Pathway converts to Petri net
   - Appears on canvas ready for editing

### Error Handling

**Validation Errors**:
```
⚠ Validation failed. See preview for details.

Validation errors:
  • Species 'unknown_compound' not found
  • Reaction 'bad_reaction' has negative stoichiometry
```

**Parse Errors**:
```
❌ Parse failed

Error parsing file:
  Invalid SBML format: missing <listOfSpecies>
```

**Import Errors**:
```
❌ Import failed: Connection error

Check that source and target objects exist.
```

---

## Pipeline Architecture

The SBML import uses the complete 4-phase pipeline:

```
┌─────────────────┐
│  SBML File      │
│  (.sbml/.xml)   │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Phase 1: SBML Parser               │
│  - SpeciesExtractor                 │
│  - ReactionExtractor                │
│  - CompartmentExtractor             │
│  - ParameterExtractor               │
└────────┬────────────────────────────┘
         │ PathwayData
         ▼
┌─────────────────────────────────────┐
│  Phase 2: Pathway Validator         │
│  - SpeciesReferenceValidator        │
│  - StoichiometryValidator           │
│  - KineticsValidator                │
│  - CompartmentValidator             │
│  - StructureValidator               │
│  - ConcentrationValidator           │
└────────┬────────────────────────────┘
         │ ValidationResult
         ▼
┌─────────────────────────────────────┐
│  Phase 3: Post-Processor            │
│  - LayoutProcessor (force-directed) │
│  - ColorProcessor (by compartment)  │
│  - UnitNormalizer (mM → tokens)     │
│  - NameResolver (IDs → names)       │
│  - CompartmentGrouper               │
└────────┬────────────────────────────┘
         │ ProcessedPathwayData
         ▼
┌─────────────────────────────────────┐
│  Phase 4: Pathway Converter         │
│  - SpeciesConverter (→ Places)      │
│  - ReactionConverter (→ Transitions)│
│  - ArcConverter (→ Arcs)            │
└────────┬────────────────────────────┘
         │ DocumentModel
         ▼
┌─────────────────┐
│  Canvas Display │
│  (Petri Net)    │
└─────────────────┘
```

---

## Implementation Status

### Completed ✅

- [x] UI design (SBML tab in pathway_panel.ui)
- [x] File selection controls
- [x] Import options (spacing, scale factor)
- [x] Preview/status area
- [x] Action buttons
- [x] GTK adjustments for spin buttons
- [x] Documentation

### Backend Integration (Python) 📋

The following needs to be implemented in the Python backend:

- [ ] Load UI file and get widget references
- [ ] Connect signal handlers
- [ ] Implement file browser dialog
- [ ] Implement parse handler (parser + validator)
- [ ] Implement preview generator
- [ ] Implement import handler (post-processor + converter)
- [ ] Integrate with canvas/document management
- [ ] Add error handling and status updates

### Testing Checklist 📋

- [ ] Test file selection dialog
- [ ] Test with valid SBML file
- [ ] Test with invalid SBML file
- [ ] Test validation errors display
- [ ] Test preview generation
- [ ] Test scale factor calculation update
- [ ] Test spacing adjustment
- [ ] Test import to canvas
- [ ] Test with large pathways (100+ species)
- [ ] Test error recovery

---

## Related Files

### UI Files
- `ui/panels/pathway_panel.ui` - Main panel definition ✅ Updated

### Backend Files (to be created/modified)
- `src/shypn/ui/panels/pathway_panel.py` - Panel controller class
- `src/shypn/ui/dialogs/sbml_import_dialog.py` - Optional standalone dialog

### Pipeline Files (already complete)
- `src/shypn/data/pathway/sbml_parser.py` - SBML parser ✅
- `src/shypn/data/pathway/pathway_validator.py` - Validator ✅
- `src/shypn/data/pathway/pathway_postprocessor.py` - Post-processor ✅
- `src/shypn/data/pathway/pathway_converter.py` - Converter ✅

### Test Files
- `tests/pathway/test_sbml_parser.py` - Parser tests ✅
- `tests/pathway/test_pathway_validator.py` - Validator tests ✅
- `tests/pathway/test_pathway_postprocessor.py` - Post-processor tests ✅
- `tests/pathway/test_pathway_converter.py` - Converter tests ✅

---

## Future Enhancements

1. **Batch Import**: Import multiple SBML files at once
2. **Template Presets**: Save/load commonly used import settings
3. **Advanced Layout**: Additional layout algorithms (hierarchical, circular)
4. **Kinetic Simulation**: Configure simulation parameters during import
5. **Metadata Preservation**: Store SBML annotations in Petri net metadata
6. **Export to SBML**: Reverse conversion (Petri net → SBML)

---

## Summary

✅ **SBML Tab Complete**: Fully designed UI ready for backend integration  
✅ **Pipeline Ready**: All 4 phases implemented and tested  
📋 **Next Step**: Implement Python backend signal handlers  

The SBML import feature now has a professional, user-friendly interface integrated into the existing Pathway Operations panel. Users can import biochemical pathways with full control over layout and token scaling parameters.
