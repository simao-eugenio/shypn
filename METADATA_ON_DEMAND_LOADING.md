# Metadata On-Demand Loading Implementation

## Problem Statement
During KEGG import, multiple cascading `set_model_canvas()` calls from Report Panel and Pathway Operations Panel were causing categories to collapse unexpectedly. Attempts to preserve expansion state with locks and timing mechanisms proved fragile.

## Solution: Lazy Loading
Instead of fighting the cascade, we now **defer metadata population until the user expands the Metadata Inspector**. This approach:
- Eliminates cascade timing issues
- Reduces unnecessary processing during import
- Gives users control over when to view metadata
- Prevents category collapse caused by refresh cascades

## Implementation Details

### 1. Added Expansion Detection
**File:** `kegg_category.py` Line ~386

Connected the `notify::expanded` signal to detect when user expands the metadata inspector:

```python
self.metadata_expander = Gtk.Expander(label="KEGG Metadata Inspector")
self.metadata_expander.set_expanded(False)

# Connect to expansion event - populate metadata when user expands
self.metadata_expander.connect("notify::expanded", self._on_metadata_expander_toggled)
```

### 2. Created Expansion Callback
**File:** `kegg_category.py` Line ~232

New method that triggers metadata refresh only when user expands:

```python
def _on_metadata_expander_toggled(self, expander, param):
    """Called when user expands/collapses the metadata inspector.
    Populates metadata only when expanded to avoid cascade issues.
    """
    if expander.get_expanded():
        # User expanded the inspector - now populate metadata
        self.refresh_metadata_inspector()
```

### 3. Separated Button Updates from Metadata Display
**File:** `kegg_category.py` Line ~243

Created dedicated method for enrichment button updates:

```python
def _update_enrichment_buttons(self):
    """Update enrichment button states based on current document.
    Separated from metadata refresh to avoid cascade issues.
    """
    # Get current document
    document = self._get_canvas_manager_document()
    
    if document and is_kegg_model(document):
        self.stoich_enrich_button.set_sensitive(True)
        self._check_stoich_enrichment_candidates()
    else:
        self.stoich_enrich_button.set_sensitive(False)
```

### 4. Updated `on_tab_switched()`
**File:** `kegg_category.py` Line ~127

Now only updates buttons, not metadata display:

```python
def on_tab_switched(self):
    """Called when the user switches to a different model tab.
    Updates enrichment buttons only.
    Note: Metadata inspector refresh is deferred until user expands it.
    """
    self._update_enrichment_buttons()
```

### 5. Simplified `refresh_metadata_inspector()`
**File:** `kegg_category.py` Line ~2253

Removed button update logic, now only handles metadata display:

```python
def refresh_metadata_inspector(self):
    """Refresh KEGG Metadata Inspector for the currently active document.
    This method is called when the user expands the metadata inspector.
    """
    document = self._get_canvas_manager_document()
    
    if document and is_kegg_model(document):
        pathway_dict = document.metadata.get('kegg_pathway_data')
        if pathway_dict:
            self._load_kegg_metadata_from_dict(pathway_dict)
        else:
            # Legacy import without metadata
            self.metadata_store.clear()
            self.preview_text.set_text("KEGG model (legacy) - Re-import to see metadata")
    else:
        # No KEGG model
        self.metadata_store.clear()
        self.preview_text.set_text("No KEGG pathway loaded")
```

### 6. Removed All Auto-Expansion Code

**Removed from:**
- Line ~638: Local file import flow
- Line ~1058: Auto-add flow
- Line ~1142: Import completion flow  
- Line ~1171: `_update_metadata_display()` method

All instances of `self.metadata_expander.set_expanded(True)` removed.

## User Experience Flow

### Before (Problematic)
```
1. User clicks "Save to Project"
2. Import completes → auto-expand metadata
3. GLib.idle_add → Report Panel refresh
4. Report Panel → GLib.timeout_add(100ms) → delayed_refresh
5. delayed_refresh → set_model_canvas on all categories
6. Pathway Ops propagates → set_model_canvas on KEGG category
7. KEGG category on_tab_switched → refresh_metadata_inspector
8. Multiple cascading calls interfere with expansion state
9. Category collapses unexpectedly ❌
```

### After (Fixed)
```
1. User clicks "Save to Project"
2. Import completes → metadata saved to document
3. Category remains in its current state (no forced expansion/collapse)
4. User clicks on Metadata Inspector to expand it
5. notify::expanded signal fires
6. _on_metadata_expander_toggled() called
7. refresh_metadata_inspector() populates data
8. Metadata displayed instantly ✅
```

## Benefits

1. **No Cascade Issues**: Metadata refresh happens on user action, not during cascading panel updates
2. **Performance**: Avoids unnecessary processing if user doesn't need metadata
3. **Stability**: No timing dependencies or race conditions
4. **User Control**: User decides when to view metadata
5. **Clean Code**: Clear separation between button updates and data display

## Technical Notes

### Signal Connection
`notify::expanded` is a GObject property notification signal that fires when the `expanded` property changes on `Gtk.Expander`. This is the standard GTK way to detect expansion/collapse.

### Deferred Loading Pattern
This follows the "lazy loading" pattern common in UI frameworks:
- UI elements are created immediately
- Data population is deferred until needed
- Reduces initial load time
- Improves responsiveness

### Cascade Avoidance
By moving metadata refresh from `on_tab_switched()` to the expansion callback:
- `set_model_canvas()` cascades only update button states (fast)
- Metadata display happens outside the cascade chain
- No risk of timing conflicts

## Related Files Modified

- `kegg_category.py`: Main implementation (7 changes)
  - Line ~386: Signal connection
  - Line ~127: `on_tab_switched()` simplified
  - Line ~205: `set_model_canvas()` documentation updated
  - Line ~232: New `_on_metadata_expander_toggled()` callback
  - Line ~243: New `_update_enrichment_buttons()` method
  - Line ~2253: Simplified `refresh_metadata_inspector()`
  - Lines ~638, ~1058, ~1142, ~1171: Removed auto-expansion

## Testing Checklist

- [x] Compiles without errors
- [ ] Import KEGG pathway (hsa00010)
- [ ] Verify Save to Project button works
- [ ] Check that category doesn't collapse after import
- [ ] Expand Metadata Inspector manually
- [ ] Verify metadata populates correctly
- [ ] Switch between tabs
- [ ] Verify metadata updates when switching back to KEGG model
- [ ] Check enrichment buttons enable/disable correctly

## Future Enhancements

Consider applying this pattern to other panels that experience cascade issues:
- SBML Metadata Category
- BiGG Metadata Display
- Report Panel categories

The on-demand loading pattern could be generalized into a reusable mixin for any expandable metadata display.
