# Pathway Panel Widget ID Synchronization Fix

**Date:** 2024  
**Issue:** Error 71 (Protocol error) and non-functional radio buttons in pathway panel  
**Root Cause:** Mismatch between widget IDs in UI file and signal wiring code

---

## Problem Description

When integrating the normalized pathway panel into the main shypn application, two issues were discovered:

1. **Wayland Error 71:** Protocol error when showing pathway panel in GtkStack
2. **Non-functional UI:** Radio buttons visible but not responding to user input

Investigation revealed that the second issue was caused by widget IDs in the UI file not matching the IDs used in the signal wiring code, resulting in widgets not being found and signals not being connected.

---

## Widget ID Mapping

### KEGG Tab

**UI File (pathway_panel.ui):**
```xml
<GtkRadioButton id="kegg_database_radio">
  <property name="label">KEGG Database</property>
  <property name="active">True</property>
</GtkRadioButton>

<GtkRadioButton id="kegg_local_radio">
  <property name="label">Local File</property>
</GtkRadioButton>

<GtkBox id="kegg_database_box" visible="True">
  <!-- Database ID entry, organism combo -->
</GtkBox>

<GtkBox id="kegg_local_box" visible="False">
  <!-- File chooser, browse button -->
</GtkBox>
```

**Signal Code (pathway_panel_loader.py):**
```python
# WRONG (before fix):
kegg_external_radio = self.builder.get_object('kegg_external_radio')  # NOT FOUND!
kegg_external_box = self.builder.get_object('kegg_external_box')      # NOT FOUND!

# CORRECT (after fix):
kegg_database_radio = self.builder.get_object('kegg_database_radio')  # ✓ Found
kegg_database_box = self.builder.get_object('kegg_database_box')      # ✓ Found
```

**Rationale:** UI uses descriptive "database" (vs "local"), not generic "external"

---

### SBML Tab

**UI File (pathway_panel.ui):**
```xml
<GtkRadioButton id="sbml_local_radio">
  <property name="label">Local File</property>
  <property name="active">True</property>
</GtkRadioButton>

<GtkRadioButton id="sbml_biomodels_radio">
  <property name="label">BioModels Database</property>
</GtkRadioButton>

<GtkBox id="sbml_local_box" visible="True">
  <!-- File chooser, browse button -->
</GtkBox>

<GtkBox id="sbml_biomodels_box" visible="False">
  <!-- BioModels ID entry, fetch button -->
</GtkBox>
```

**Signal Code (pathway_panel_loader.py):**
```python
# WRONG (before fix):
sbml_external_radio = self.builder.get_object('sbml_external_radio')  # NOT FOUND!
sbml_external_box = self.builder.get_object('sbml_external_box')      # NOT FOUND!

# CORRECT (after fix):
sbml_biomodels_radio = self.builder.get_object('sbml_biomodels_radio')  # ✓ Found
sbml_biomodels_box = self.builder.get_object('sbml_biomodels_box')      # ✓ Found
```

**Rationale:** UI uses specific "biomodels" (the actual database name), not generic "external"

---

### BRENDA Tab

**UI File (pathway_panel.ui):**
```xml
<GtkRadioButton id="brenda_external_radio">
  <property name="label">BRENDA Database</property>
  <property name="active">True</property>
</GtkRadioButton>

<GtkRadioButton id="brenda_local_radio">
  <property name="label">Local File</property>
</GtkRadioButton>

<GtkBox id="brenda_external_box" visible="True">
  <!-- Credentials status, configure button, organism combo -->
</GtkBox>

<GtkBox id="brenda_local_box" visible="False">
  <!-- File chooser, browse button -->
</GtkBox>
```

**Signal Code (pathway_panel_loader.py):**
```python
# Already correct:
brenda_external_radio = self.builder.get_object('brenda_external_radio')  # ✓ Found
brenda_external_box = self.builder.get_object('brenda_external_box')      # ✓ Found
```

**Status:** No changes needed ✓

---

## Code Changes Summary

### File: `src/shypn/helpers/pathway_panel_loader.py`

#### 1. Signal Setup (Line ~188-223)

**KEGG Tab:**
```python
# Changed:
kegg_database_radio = self.builder.get_object('kegg_database_radio')
kegg_local_radio = self.builder.get_object('kegg_local_radio')

if kegg_database_radio:
    kegg_database_radio.connect('toggled', self._on_kegg_source_toggled)
```

**SBML Tab:**
```python
# Changed:
sbml_biomodels_radio = self.builder.get_object('sbml_biomodels_radio')
sbml_local_radio = self.builder.get_object('sbml_local_radio')

if sbml_biomodels_radio:
    sbml_biomodels_radio.connect('toggled', self._on_sbml_source_toggled)
```

**BRENDA Tab:**
```python
# No changes needed:
brenda_external_radio = self.builder.get_object('brenda_external_radio')
brenda_local_radio = self.builder.get_object('brenda_local_radio')

if brenda_external_radio:
    brenda_external_radio.connect('toggled', self._on_brenda_source_toggled)
```

#### 2. Toggle Handlers (Line ~231-379)

**KEGG Handler:**
```python
def _on_kegg_source_toggled(self, radio):
    """Handle KEGG source selection (Database/Local) radio button toggle."""
    if not radio.get_active():
        return
    
    # Changed:
    kegg_database_box = self.builder.get_object('kegg_database_box')
    kegg_local_box = self.builder.get_object('kegg_local_box')
    kegg_database_radio = self.builder.get_object('kegg_database_radio')
    
    is_database = kegg_database_radio.get_active()
    
    if kegg_database_box:
        kegg_database_box.set_visible(is_database)
    if kegg_local_box:
        kegg_local_box.set_visible(not is_database)
```

**SBML Handler:**
```python
def _on_sbml_source_toggled(self, radio):
    """Handle SBML source selection (BioModels/Local) radio button toggle."""
    if not radio.get_active():
        return
    
    # Changed:
    sbml_biomodels_box = self.builder.get_object('sbml_biomodels_box')
    sbml_local_box = self.builder.get_object('sbml_local_box')
    sbml_biomodels_radio = self.builder.get_object('sbml_biomodels_radio')
    
    is_biomodels = sbml_biomodels_radio.get_active()
    
    if sbml_biomodels_box:
        sbml_biomodels_box.set_visible(is_biomodels)
    if sbml_local_box:
        sbml_local_box.set_visible(not is_biomodels)
```

#### 3. Import Button Handlers (Line ~271-369)

**KEGG Import Handler:**
```python
def _on_kegg_import_clicked(self, button):
    """Handle unified KEGG Import to Canvas button."""
    # Changed:
    kegg_database_radio = self.builder.get_object('kegg_database_radio')
    
    if kegg_database_radio and kegg_database_radio.get_active():
        # Database source: fetch from KEGG API
        self.kegg_import_controller._on_fetch_clicked(button)
    else:
        # Local source: load from file
        kegg_file_entry = self.builder.get_object('kegg_file_entry')
        # ... file loading logic
```

**SBML Import Handler:**
```python
def _on_sbml_import_clicked(self, button):
    """Handle unified SBML Import to Canvas button."""
    # Changed:
    sbml_biomodels_radio = self.builder.get_object('sbml_biomodels_radio')
    
    if sbml_biomodels_radio and sbml_biomodels_radio.get_active():
        # BioModels source: fetch from database
        self.sbml_import_controller.on_fetch_clicked(button)
    else:
        # Local source: parse and load
        self.sbml_import_controller.on_parse_clicked(button)
```

---

## ID Naming Convention (Established)

Going forward, widget IDs should follow this pattern:

### Radio Buttons
- Use **specific source name**, not generic "external"
- Examples:
  - `kegg_database_radio` (not `kegg_external_radio`)
  - `sbml_biomodels_radio` (not `sbml_external_radio`)
  - `brenda_external_radio` (OK - "external" is the actual label)
- Always pair with `{tab}_local_radio`

### Container Boxes
- Match the corresponding radio button name
- Examples:
  - `kegg_database_box` ↔ `kegg_database_radio`
  - `sbml_biomodels_box` ↔ `sbml_biomodels_radio`
  - `brenda_external_box` ↔ `brenda_external_radio`
- Always pair with `{tab}_local_box`

### Other Widgets
- Use clear, descriptive names
- Examples:
  - `kegg_import_button` (not `kegg_fetch_button` or `kegg_load_button`)
  - `sbml_browse_button` (for file browsing)
  - `brenda_enrich_button` (specific action)

---

## Verification Checklist

After making ID changes, verify:

- [ ] **UI File IDs Match Code:**
  ```bash
  grep 'id="kegg_' ui/panels/pathway_panel.ui
  grep 'kegg_.*_radio\|kegg_.*_box' src/shypn/helpers/pathway_panel_loader.py
  ```

- [ ] **Signal Connections Work:**
  ```python
  # All should return widget objects (not None):
  widget = self.builder.get_object('widget_id')
  assert widget is not None, f"Widget 'widget_id' not found!"
  ```

- [ ] **Radio Button Behavior:**
  - Click database radio → database box shows, local box hides
  - Click local radio → local box shows, database box hides
  - Visual feedback (radio button selection changes)

- [ ] **Import Button Routing:**
  - Database radio active + Import → calls fetch method
  - Local radio active + Import → calls parse/load method

- [ ] **No Console Errors:**
  ```
  # Should NOT appear:
  Gtk-WARNING **: ... Failed to get property '...' 
  Gtk-CRITICAL **: ... assertion '... != NULL' failed
  ```

---

## Testing Strategy

### 1. Isolated Tests
```bash
# Test pathway panel in isolation
python3 dev/test_pathway_stack_mode.py

# Expected output:
Widget kegg_database_radio: FOUND ✓
Widget kegg_local_radio: FOUND ✓
Widget sbml_biomodels_radio: FOUND ✓
Widget brenda_external_radio: FOUND ✓
All radio buttons toggleable: YES ✓
```

### 2. Integration Test
```bash
# Test in main application
python3 src/shypn.py

# User actions:
1. Click Master Palette button
2. Click "Pathways" item
3. Switch between KEGG/SBML/BRENDA tabs
4. Toggle radio buttons in each tab
5. Click browse buttons
6. Click import buttons

# Expected:
- No Error 71
- Radio buttons respond to clicks
- Boxes show/hide correctly
- Buttons trigger correct actions
```

### 3. Debug Logging (if needed)
```python
def _on_kegg_source_toggled(self, radio):
    print(f"DEBUG: KEGG radio toggled, active={radio.get_active()}")
    
    kegg_database_box = self.builder.get_object('kegg_database_box')
    print(f"DEBUG: kegg_database_box found: {kegg_database_box is not None}")
    
    if kegg_database_box:
        kegg_database_box.set_visible(is_database)
        print(f"DEBUG: Set visibility to {is_database}")
```

---

## Root Cause Analysis

**Why did this happen?**

1. **Temporal Separation:** UI file created/modified separately from signal wiring code
2. **Semantic Drift:** Used descriptive names in UI ("database", "biomodels") but generic names in code ("external")
3. **Missing Verification:** No automated check that widget IDs exist in UI file

**How to prevent in future?**

1. **ID Audit Tool:** Create script to validate UI ↔ code consistency
   ```bash
   # Example: scripts/validate_widget_ids.py
   python3 scripts/validate_widget_ids.py ui/panels/pathway_panel.ui \
       src/shypn/helpers/pathway_panel_loader.py
   ```

2. **Documentation First:** Document widget IDs before implementing signals
   ```markdown
   ## Widget IDs for KEGG Tab
   - kegg_database_radio (radio button)
   - kegg_database_box (container)
   - kegg_import_button (action)
   ```

3. **Test-Driven Development:** Write widget verification test before signal wiring
   ```python
   def test_kegg_widgets_exist():
       assert builder.get_object('kegg_database_radio') is not None
       assert builder.get_object('kegg_database_box') is not None
   ```

---

## Related Issues

- **Wayland Error 71:** Fixed separately with `_show_visible_children()` method
- **See:** `show_in_stack()` method in `pathway_panel_loader.py` (line ~811)
- **Approach:** Use `show()` not `show_all()`, recursively show visible children

---

## Status

- ✅ KEGG tab IDs fixed
- ✅ SBML tab IDs fixed
- ✅ BRENDA tab IDs verified (already correct)
- ⏳ Integration testing pending
- ⏳ Error 71 verification pending

---

## Next Steps

1. Test in main shypn.py application
2. Verify no Error 71
3. Verify radio buttons work correctly
4. Document final status
5. Create ID validation script (optional)

