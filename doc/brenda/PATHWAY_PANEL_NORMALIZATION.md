# Pathway Panel Normalization

**Date:** 2025-01-XX  
**Status:** ✅ Completed  
**File:** `ui/panels/pathway_panel.ui`

## Objective

Standardize the UI pattern across all three import tabs (KEGG, SBML, BRENDA) to create a consistent, intuitive user experience with minimal confusion.

## Design Principles

### User Requirements

From user specification:
> "just to normalize the 3 tabs, in all theere must be a possibility to open local pure file from external and submit to parser, but the preference is from external source using accession ID...unique button import to canvas...try to let all panels with the same UI resources as possible to not confuse user"

**Key principles:**
1. **External source is PRIMARY** - Default and emphasized
2. **Local file is SECONDARY** - Available but not default
3. **Single unified action** - One "Import to Canvas" button (not Fetch + Import)
4. **Consistent UI pattern** - All tabs follow the same structure

## Unified Tab Pattern

```
┌─────────────────────────────────────────┐
│ 1. SOURCE SELECTION (Radio Buttons)    │
│    ● External (Accession ID) ← DEFAULT │
│    ○ Local File                        │
├─────────────────────────────────────────┤
│ 2. INPUT AREA (Dynamic, shows one of): │
│    [External: ID + options]  OR        │
│    [Local: File chooser + Browse]      │
├─────────────────────────────────────────┤
│ 3. OPTIONS (Expander - optional)        │
│    ▼ Import Options                     │
│       [checkboxes, settings]            │
├─────────────────────────────────────────┤
│ 4. PREVIEW/STATUS (optional)            │
│    [feedback, warnings]                 │
├─────────────────────────────────────────┤
│ 5. ACTION BUTTON (Single, unified)      │
│    [     Import to Canvas     ]         │
└─────────────────────────────────────────┘
```

## Implementation Details

### Tab 1: KEGG

**External Source (Default):**
- Pathway ID entry (`pathway_id_entry`)
- Organism combo (`organism_combo`) - hsa, mmu, dme, sce, eco
- Fetches from KEGG REST API

**Local Source:**
- File path entry (`kegg_file_entry`)
- Browse button (`kegg_browse_button`)
- Accepts .xml KGML files

**Action:**
- Single button: `kegg_import_button` - "Import to Canvas"
- Replaces old `fetch_button` + `import_button` two-step workflow

**Widget IDs:**
- `kegg_external_radio` (active=True by default)
- `kegg_local_radio` (group: kegg_external_radio)
- `kegg_external_box` (visible=True by default)
- `kegg_local_box` (visible=False by default)

### Tab 2: SBML

**External Source (Default):**
- BioModels ID entry (`biomodels_id_entry`)
- Fetches from BioModels repository

**Local Source:**
- File path entry (`sbml_file_entry`)
- Browse button (`sbml_browse_button`)
- Accepts .sbml or .xml files

**Action:**
- Single button: `sbml_import_button` - "Import to Canvas"
- Replaces old `sbml_fetch_button` + `sbml_parse_button` workflow

**Widget IDs:**
- `sbml_external_radio` (active=True by default)
- `sbml_local_radio` (group: sbml_external_radio)
- `sbml_external_box` (visible=True by default)
- `sbml_local_box` (visible=False by default)

### Tab 3: BRENDA

**External Source (Default):**
- **Credentials status indicator** (`brenda_credentials_status`)
  - ❌ Not configured
  - ⏳ Pending approval (1-2 days)
  - ✅ Active
- Configure button (`brenda_configure_button`) → User Profile dialog
- EC number entry (`ec_number_entry`) - e.g., 1.1.1.1, 2.3.1.15
- Organism filter combo (`brenda_organism_combo`) - optional
- Help text: "BRENDA registration takes 1-2 business days"
- Fetches from BRENDA SOAP API

**Local Source:**
- File path entry (`brenda_file_entry`)
- Browse button (`brenda_browse_button`)
- Accepts CSV or JSON files (BRENDA exports)

**Options (Expander):**
- `brenda_km_check` - Include Km values ✓
- `brenda_kcat_check` - Include kcat values ✓
- `brenda_ki_check` - Include Ki values ✓
- `brenda_citations_check` - Include literature citations ✓
- `brenda_update_check` - Update existing parameters ✓

**Action:**
- Single button: `brenda_enrich_button` - "**Analyze and Enrich Canvas**"
- **Different workflow from KEGG/SBML**: BRENDA enriches existing models, doesn't create new ones

**Enrichment Workflow:**
1. Scan entire canvas for transitions (potential enzymes)
2. Query BRENDA API (external) or load file (local) for kinetic data
3. Match BRENDA data to canvas transitions (by EC number, name)
4. Generate enrichment report showing:
   - Which transitions have matching BRENDA data
   - What parameters would be added/updated
   - Conflicts with existing data (for SBML models)
5. User reviews report and selects which enrichments to apply
6. Apply selected data to canvas

**Precautions for SBML Models:**
- SBML models may already have curated kinetic data
- `brenda_override_check` (default: OFF) controls whether to replace existing parameters
- Recommended: OFF for SBML, ON for KEGG (which has no kinetics)
- Warning dialog shown if override is enabled

**KEGG Pathways:**
- Pure topology, no kinetic data
- Safe to enrich without precautions
- All BRENDA data is additive

**Widget IDs:**
- `brenda_external_radio` (active=True by default)
- `brenda_local_radio` (group: brenda_external_radio)
- `brenda_external_box` (visible=True by default)
- `brenda_local_box` (visible=False by default)

## Changes Made

### 1. KEGG Tab Standardization

**Before:**
```xml
<!-- Separate Fetch + Import buttons -->
<GtkButton id="fetch_button">Fetch Pathway</GtkButton>
<GtkButton id="import_button">Import</GtkButton>

<!-- No source selection -->
<GtkEntry id="pathway_id_entry"/>
<GtkComboBoxText id="organism_combo"/>
```

**After:**
```xml
<!-- Source selection radio buttons -->
<GtkRadioButton id="kegg_external_radio">External (KEGG API)</GtkRadioButton>
<GtkRadioButton id="kegg_local_radio">Local KGML File</GtkRadioButton>

<!-- Dynamic boxes (external shown, local hidden) -->
<GtkBox id="kegg_external_box" visible="True">
  <GtkEntry id="pathway_id_entry"/>
  <GtkComboBoxText id="organism_combo"/>
</GtkBox>

<GtkBox id="kegg_local_box" visible="False">
  <GtkEntry id="kegg_file_entry"/>
  <GtkButton id="kegg_browse_button"/>
</GtkBox>

<!-- Single unified action button -->
<GtkButton id="kegg_import_button">Import to Canvas</GtkButton>
```

### 2. SBML Tab Standardization

**Before:**
```xml
<!-- Separate Fetch + Parse buttons -->
<GtkButton id="sbml_fetch_button">Fetch from BioModels</GtkButton>
<GtkButton id="sbml_parse_button">Parse and Load</GtkButton>

<!-- Source selection already existed (kept and renamed IDs) -->
```

**After:**
```xml
<!-- Standardized IDs and single action button -->
<GtkButton id="sbml_import_button">Import to Canvas</GtkButton>
```

### 3. BRENDA Tab Creation

**Before:**
```xml
<!-- Placeholder with feature list -->
<GtkLabel>BRENDA Data Enrichment</GtkLabel>
<GtkLabel>(Phase 4: Wire BRENDA connector)</GtkLabel>
```

**After:**
```xml
<!-- Full implementation with unified pattern -->
<GtkRadioButton id="brenda_external_radio">External (BRENDA API)</GtkRadioButton>
<GtkRadioButton id="brenda_local_radio">Local File</GtkRadioButton>

<!-- Credentials status -->
<GtkLabel id="brenda_credentials_status">❌ Credentials not configured</GtkLabel>
<GtkButton id="brenda_configure_button">Configure...</GtkButton>

<!-- EC Number + Organism -->
<GtkEntry id="ec_number_entry"/>
<GtkComboBoxText id="brenda_organism_combo"/>

<!-- Options expander with checkboxes -->
<GtkExpander>Import Options</GtkExpander>

<!-- Action button -->
<GtkButton id="brenda_import_button">Import to Canvas</GtkButton>
```

## Benefits

### User Experience

1. **Consistency** - Same pattern in all three tabs
2. **Clarity** - One clear action: "Import to Canvas"
3. **Flexibility** - Both external and local sources available
4. **Emphasis** - External source (preferred) is default and visible
5. **Simplicity** - No confusion about Fetch vs Import workflow

### Developer Benefits

1. **Maintainability** - Same structure across tabs
2. **Documentation** - One pattern to explain
3. **Testing** - Consistent test procedures
4. **Extensibility** - Easy to add new tabs following template

## Next Steps

### Phase 1: Signal Wiring (1-2 days)

```python
# Add signal handlers for radio button toggling
# Example for KEGG tab:

def on_kegg_external_radio_toggled(self, radio):
    """Show external box when External selected."""
    is_external = radio.get_active()
    self.kegg_external_box.set_visible(is_external)
    self.kegg_local_box.set_visible(not is_external)

def on_kegg_browse_button_clicked(self, button):
    """Open file chooser for KGML file."""
    dialog = Gtk.FileChooserDialog(
        title="Select KGML File",
        parent=self.parent_window,
        action=Gtk.FileChooserAction.OPEN
    )
    # Add filter for .xml files
    # Update kegg_file_entry with selected path
```

### Phase 2: Controller Integration (2-3 days)

Wire existing controllers to new UI:
- `KEGGImportPanel` → KEGG tab
- `SBMLImportPanel` → SBML tab
- `BRENDAConnector` (new) → BRENDA tab

### Phase 3: Action Button Implementation (3-5 days)

```python
def on_kegg_import_button_clicked(self, button):
    """Handle unified Import to Canvas action."""
    if self.kegg_external_radio.get_active():
        # External source workflow
        pathway_id = self.pathway_id_entry.get_text()
        organism = self.organism_combo.get_active_id()
        
        # Fetch from KEGG API
        kgml_data = self.kegg_ctrl.fetch_pathway(pathway_id, organism)
        
        # Parse and import
        self.kegg_ctrl.import_to_canvas(kgml_data)
    else:
        # Local source workflow
        file_path = self.kegg_file_entry.get_text()
        
        # Load from file
        kgml_data = self.kegg_ctrl.load_kgml_file(file_path)
        
        # Parse and import
        self.kegg_ctrl.import_to_canvas(kgml_data)
```

### Phase 4: BRENDA Implementation (2-3 weeks)

1. **Credentials Management** (3-5 days)
   - CredentialsManager with encryption
   - User Profile dialog integration
   - Test Connection button functionality

2. **BRENDA Connector** (5-7 days)
   - SOAP client setup
   - Authentication (email + SHA256 password)
   - Query methods (by EC number, by name, etc.)
   - Data parsing and structure

3. **Auto-Enrichment** (5-7 days)
   - Match canvas elements to BRENDA data
   - Update kinetic parameters
   - Add citations
   - Create enrichment report

### Phase 5: Testing (1 week)

- Unit tests for each tab
- Integration tests for import workflows
- UI/UX testing with users
- Error handling and edge cases

## Technical Notes

### Radio Button Groups

GTK radio buttons are linked via the `group` property:
```xml
<GtkRadioButton id="kegg_external_radio">
  <property name="active">True</property>
</GtkRadioButton>

<GtkRadioButton id="kegg_local_radio">
  <property name="group">kegg_external_radio</property>
</GtkRadioButton>
```

When one is activated, the other is automatically deactivated.

### Dynamic Visibility

The `visible` property controls initial state:
- External box: `visible="True"` (shown by default)
- Local box: `visible="False"` (hidden by default)

Signal handlers update visibility based on radio button state.

### Button Styling

All action buttons use the `suggested-action` style class:
```xml
<style>
  <class name="suggested-action"/>
</style>
```

This provides visual emphasis (typically blue/accent color).

## Related Documentation

- **BRENDA Authentication:** `doc/brenda/BRENDA_INTEGRATION_SESSION.md`
- **BRENDA Data Reference:** `doc/brenda/BRENDA_DATA_REFERENCE.md`
- **Auto-Enrichment Pipeline:** `doc/brenda/AUTO_ENRICHMENT_PIPELINE.md`
- **Pathway Panel Controller:** `src/shypn/helpers/pathway_panel_loader.py` (old)
- **New Panel Architecture:** `src/shypn/ui/panels/pathways_panel.py` (Phase 4)

## Architecture Decision

**Note:** This UI file (`ui/panels/pathway_panel.ui`) is part of the **old implementation** that will eventually be replaced by the **new BasePanel architecture** (`pathways_panel.py`).

However, the normalized tab pattern designed here should be **preserved and replicated** in the new implementation:
1. The programmatic UI in `pathways_panel.py` should follow the same structure
2. The signal wiring should implement the same behavior
3. The unified "Import to Canvas" button pattern should be maintained

This ensures a smooth migration path and consistent UX regardless of the underlying architecture.

## Validation Checklist

### UI Structure ✅
- [x] All three tabs have Source Selection radio buttons
- [x] External source is default (active=True) in all tabs
- [x] Dynamic boxes (External/Local) have correct visibility
- [x] Single unified "Import to Canvas" button in all tabs
- [x] Consistent widget naming convention (tab_type_widget_type)
- [x] No XML syntax errors

### Tab-Specific Features ✅
- [x] KEGG: Pathway ID + Organism combo
- [x] KEGG: Local file chooser with Browse button
- [x] SBML: BioModels ID input
- [x] SBML: Local file chooser with Browse button
- [x] BRENDA: Credentials status indicator
- [x] BRENDA: EC number + Organism filter
- [x] BRENDA: Options expander with parameter checkboxes
- [x] BRENDA: Local file chooser for CSV/JSON

### Pending ⏳
- [ ] Radio button signal handlers (toggle visibility)
- [ ] Browse button file chooser dialogs
- [ ] Action button routing logic
- [ ] Controller integration
- [ ] Testing with real data

## Success Metrics

**User Experience:**
- Users understand the pattern immediately
- No confusion about External vs Local workflow
- Single clear action reduces cognitive load
- Consistent feedback across all tabs

**Code Quality:**
- DRY (Don't Repeat Yourself) - same pattern replicated
- Maintainable - easy to modify/extend
- Testable - clear structure for unit tests
- Documented - this file + inline comments

**Timeline:**
- UI normalization: ✅ Complete (2 hours)
- Signal wiring: ⏳ 1-2 days
- Controller integration: ⏳ 2-3 days
- Full BRENDA implementation: ⏳ 2-3 weeks

---

**Status:** Ready for signal wiring and controller integration  
**Next Action:** Implement radio button toggling and Browse button handlers
