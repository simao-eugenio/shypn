# Report Panel - "Show Selected" Locality Category Implementation Plan

**Date**: November 9, 2025  
**Purpose**: Add new sub-category expander to Models category showing selected transition's locality data in a unified table

---

## Overview

Add a new expandable section **"Show Selected Locality"** to the Models category in the Report panel that displays:
- The currently selected transition from the Analyses panel
- All related input places
- All related output places
- Unified in a single sortable table with comprehensive information

Similar to "Show Species/Places Table" and "Show Reactions/Transitions Table", but filtered to show only the locality (P-T-P structure) for the transition currently under analysis.

---

## User Experience

### Usage Flow

1. User adds transition to Analyses panel (e.g., "T1 with locality")
2. User opens Report panel
3. Under MODELS category, expands "Show Selected Locality"
4. Sees unified table with:
   - Selected transition (1 row) - highlighted
   - Input places (N rows) - marked as "← Input"
   - Output places (M rows) - marked as "→ Output"

### Benefits

- **Unified View**: See transition + locality in one place (vs separate tabs in Analyses)
- **Detailed Data**: Full biological/kinetic data for locality components
- **Export Ready**: Can export this specific locality data for reports
- **Analysis Context**: Understand what's being analyzed without switching panels

---

## Technical Architecture

### 1. Data Structure

The table will combine:
- **Transition data** (1 row): From selected transition
- **Place data** (N rows): From locality input/output places

### 2. Table Schema

**Unified ListStore**:
```python
Gtk.ListStore(
    int,    # 0: index
    str,    # 1: Type ("Transition", "Place")
    str,    # 2: Direction ("", "← Input", "→ Output")
    str,    # 3: Petri Net ID (T1, P1, P2, etc.)
    str,    # 4: Biological Name
    str,    # 5: Additional Info (type for transition, tokens for place)
    float,  # 6: Numeric Value (rate for transition, token count for place)
    str,    # 7: Units
    str,    # 8: Parameters (EC/Km/Vmax for transition, Mass for place)
)
```

### 3. Table Columns

| # | Column | Width | Sortable | Description |
|---|--------|-------|----------|-------------|
| 0 | # | 40 | No | Row index |
| 1 | Type | 100 | Yes | "Transition" or "Place" |
| 2 | Direction | 100 | Yes | "", "← Input", "→ Output" |
| 3 | ID | 100 | Yes | Petri Net ID |
| 4 | Name | 250 | Yes | Biological name |
| 5 | Info | 120 | Yes | Type (T) or Current Amount (P) |
| 6 | Value | 100 | Yes | Numeric: rate or token count |
| 7 | Units | 80 | Yes | Units string |
| 8 | Parameters | 200 | Yes | Key parameters |

### 4. Visual Design

**Table appearance**:
```
┌───┬────────────┬────────────┬─────┬─────────────┬──────────┬───────┬────────┬─────────────────────────┐
│ # │ Type       │ Direction  │ ID  │ Name        │ Info     │ Value │ Units  │ Parameters              │
├───┼────────────┼────────────┼─────┼─────────────┼──────────┼───────┼────────┼─────────────────────────┤
│ 1 │ Place      │ ← Input    │ P1  │ Glucose     │ 5.0      │ 5.0   │ mmol   │ Mass: 180.16 g/mol      │
│ 2 │ Place      │ ← Input    │ P2  │ ATP         │ 10.0     │ 10.0  │ mmol   │ Mass: 507.18 g/mol      │
│ 3 │ Transition │            │ T1  │ Hexokinase  │ CON      │ 0.025 │ 1/s    │ EC:2.7.1.1 Vmax:0.1 ... │
│ 4 │ Place      │ → Output   │ P3  │ G6P         │ 0.0      │ 0.0   │ mmol   │ Mass: 260.14 g/mol      │
│ 5 │ Place      │ → Output   │ P4  │ ADP         │ 0.0      │ 0.0   │ mmol   │ Mass: 427.20 g/mol      │
└───┴────────────┴────────────┴─────┴─────────────┴──────────┴───────┴────────┴─────────────────────────┘
```

**Color coding** (via CSS):
- Transition row: Light blue background
- Input rows: Light green background
- Output rows: Light yellow background

---

## Implementation Details

### File: `src/shypn/ui/panels/report/model_structure_category.py`

#### A. Add Instance Variables

```python
def __init__(self, project=None, model_canvas=None):
    """Initialize models category."""
    # ... existing code ...
    
    # Selected locality tracking
    self.selected_transition = None
    self.selected_locality = None
    self.locality_store = None
    self.locality_treeview = None
    self.locality_expander = None
```

#### B. Add Expander in `_build_content()`

Add after the reactions expander (around line 150):

```python
# === SELECTED LOCALITY TABLE (conditional) ===
self.locality_expander = Gtk.Expander(label="Show Selected Locality (sortable)")
self.locality_expander.set_expanded(False)
scrolled_locality, self.locality_treeview, self.locality_store = self._create_locality_table()
self.locality_expander.add(scrolled_locality)
box.pack_start(self.locality_expander, False, False, 0)
```

#### C. Create Table Method

```python
def _create_locality_table(self):
    """Create TreeView for selected transition locality.
    
    Shows transition + input places + output places in unified table.
    
    Returns:
        tuple: (ScrolledWindow, TreeView, ListStore)
    """
    # Create ListStore
    store = Gtk.ListStore(
        int,    # 0: index
        str,    # 1: Type
        str,    # 2: Direction
        str,    # 3: Petri Net ID
        str,    # 4: Biological Name
        str,    # 5: Info
        float,  # 6: Value
        str,    # 7: Units
        str     # 8: Parameters
    )
    
    # Create TreeView
    treeview = Gtk.TreeView(model=store)
    treeview.set_grid_lines(Gtk.TreeViewGridLines.BOTH)
    treeview.set_enable_search(True)
    treeview.set_search_column(4)  # Search by name
    
    # Add columns
    self._add_column(treeview, "#", 0, width=40, sortable=False)
    self._add_column(treeview, "Type", 1, sortable=True, width=100)
    self._add_column(treeview, "Direction", 2, sortable=True, width=100)
    self._add_column(treeview, "ID", 3, sortable=True, width=100)
    self._add_column(treeview, "Name", 4, sortable=True, width=250)
    self._add_column(treeview, "Info", 5, sortable=True, width=120)
    self._add_column(treeview, "Value", 6, sortable=True, numeric=True, width=100)
    self._add_column(treeview, "Units", 7, sortable=True, width=80)
    self._add_column(treeview, "Parameters", 8, sortable=True, width=200)
    
    # Create scrolled window
    scrolled = Gtk.ScrolledWindow()
    scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
    scrolled.set_min_content_height(200)
    scrolled.add(treeview)
    
    return scrolled, treeview, store
```

#### D. Populate Method

```python
def _populate_locality_table(self):
    """Populate locality table with selected transition + locality places.
    
    Called when user selects transition in Analyses panel.
    """
    self.locality_store.clear()
    
    if not self.selected_transition or not self.selected_locality:
        # Hide expander when no selection
        self.locality_expander.set_visible(False)
        return
    
    # Show expander
    self.locality_expander.set_visible(True)
    
    transition = self.selected_transition
    locality = self.selected_locality
    
    index = 0
    
    # === ADD INPUT PLACES ===
    for place in locality.input_places:
        index += 1
        
        # Extract place data
        place_id = f"P{place.id}"
        bio_name = getattr(place, 'biological_name', place.name)
        tokens = getattr(place, 'tokens', 0.0)
        units = getattr(place, 'token_units', 'tokens')
        
        # Mass parameter
        mass = getattr(place, 'mass', 0.0)
        mass_source = getattr(place, 'mass_source', 'unknown')
        params = f"Mass: {mass:.2f} g/mol ({mass_source})"
        
        self.locality_store.append([
            index,
            "Place",
            "← Input",
            place_id,
            bio_name,
            f"{tokens:.3f}",
            tokens,
            units,
            params
        ])
    
    # === ADD TRANSITION ===
    index += 1
    
    trans_id = f"T{transition.id}"
    trans_name = getattr(transition, 'biological_name', transition.name)
    trans_type = getattr(transition, 'transition_type', 'continuous')
    
    # Type abbreviation
    type_abbrev = {
        'immediate': 'IMM',
        'timed': 'TIM',
        'stochastic': 'STO',
        'continuous': 'CON'
    }.get(trans_type, trans_type[:3].upper())
    
    # Extract rate and parameters
    rate = getattr(transition, 'rate', 0.0)
    units = getattr(transition, 'rate_units', '1/s')
    
    # Build parameters string
    params_list = []
    if hasattr(transition, 'ec_number') and transition.ec_number:
        params_list.append(f"EC:{transition.ec_number}")
    if hasattr(transition, 'vmax') and transition.vmax:
        params_list.append(f"Vmax:{transition.vmax}")
    if hasattr(transition, 'km') and transition.km:
        params_list.append(f"Km:{transition.km}")
    params = " ".join(params_list) if params_list else "N/A"
    
    self.locality_store.append([
        index,
        "Transition",
        "",  # No direction
        trans_id,
        trans_name,
        type_abbrev,
        rate,
        units,
        params
    ])
    
    # === ADD OUTPUT PLACES ===
    for place in locality.output_places:
        index += 1
        
        # Extract place data
        place_id = f"P{place.id}"
        bio_name = getattr(place, 'biological_name', place.name)
        tokens = getattr(place, 'tokens', 0.0)
        units = getattr(place, 'token_units', 'tokens')
        
        # Mass parameter
        mass = getattr(place, 'mass', 0.0)
        mass_source = getattr(place, 'mass_source', 'unknown')
        params = f"Mass: {mass:.2f} g/mol ({mass_source})"
        
        self.locality_store.append([
            index,
            "Place",
            "→ Output",
            place_id,
            bio_name,
            f"{tokens:.3f}",
            tokens,
            units,
            params
        ])
    
    # Update expander label with count
    n_inputs = len(locality.input_places)
    n_outputs = len(locality.output_places)
    total = n_inputs + 1 + n_outputs
    self.locality_expander.set_label(
        f"Show Selected Locality: {trans_name} ({n_inputs}→T→{n_outputs}, {total} rows)"
    )
```

#### E. Selection Update Method

```python
def set_selected_locality(self, transition, locality):
    """Set the selected transition and its locality for display.
    
    Called from Analyses panel when user selects a transition.
    
    Args:
        transition: Transition object
        locality: Locality object from LocalityDetector
    """
    self.selected_transition = transition
    self.selected_locality = locality
    self._populate_locality_table()
```

#### F. Update refresh() Method

In the existing `refresh()` method, add:

```python
def refresh(self):
    """Refresh tables when model changes or tab switches."""
    # ... existing code for overview, structure, species, reactions ...
    
    # Refresh locality table if selection exists
    if self.selected_transition and self.selected_locality:
        self._populate_locality_table()
```

---

## Integration Points

### 1. Analyses Panel → Report Panel Communication

**File**: `src/shypn/analyses/transition_rate_panel.py`

Add callback mechanism to notify Report panel of selection changes:

```python
def __init__(self, data_collector=None, place_panel=None):
    # ... existing code ...
    
    # Callback for selection change
    self.on_selection_changed_callback = None

def add_object(self, obj):
    """Add transition to plot."""
    # ... existing code ...
    
    # Notify Report panel of selection
    if self.on_selection_changed_callback:
        # Get locality for this transition
        from shypn.diagnostic import LocalityDetector
        detector = LocalityDetector(self.search_model)
        locality = detector.get_locality_for_transition(obj)
        
        # Notify callback
        self.on_selection_changed_callback(obj, locality)
```

### 2. Wire Callback in Main App

**File**: `src/shypn.py`

Wire the callback when creating panels:

```python
# Around line 800-900 where panels are created
transition_panel = TransitionRatePanel(...)
report_panel_loader = ReportPanelLoader(...)

# Wire selection callback
def on_transition_selected(transition, locality):
    """Called when user selects transition in Analyses panel."""
    if report_panel_loader and report_panel_loader.panel:
        # Find Models category
        for category in report_panel_loader.panel.categories:
            if isinstance(category, ModelsCategory):
                category.set_selected_locality(transition, locality)
                break

transition_panel.on_selection_changed_callback = on_transition_selected
```

### 3. Alternative: Manual Sync Button

If automatic sync is complex, add a "Sync from Analyses" button:

```python
# In Report panel header
sync_button = Gtk.Button(label="⟳ Sync Selected")
sync_button.set_tooltip_text("Sync selected transition from Analyses panel")
sync_button.connect('clicked', self._on_sync_clicked)

def _on_sync_clicked(self, button):
    """Sync selected transition from Analyses panel."""
    # Get analyses panel reference
    if self.controller:
        analyses_panel = self.controller.get_analyses_panel()
        if analyses_panel:
            transition_panel = analyses_panel.get_transition_panel()
            if transition_panel and transition_panel.selected_objects:
                # Get first selected transition
                transition = transition_panel.selected_objects[0]
                locality_data = transition_panel._locality_places.get(transition.id)
                
                if locality_data:
                    # Build Locality object
                    from shypn.diagnostic import Locality
                    locality = Locality(
                        transition=transition,
                        input_places=locality_data['input_places'],
                        output_places=locality_data['output_places']
                    )
                    
                    # Update Models category
                    for category in self.categories:
                        if isinstance(category, ModelsCategory):
                            category.set_selected_locality(transition, locality)
                            break
```

---

## Export Functionality

### Add Export Button

In the locality expander, add export button:

```python
# In _build_content() where locality expander is created
expander_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)

# Toolbar with export button
toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
toolbar.set_margin_start(6)
toolbar.set_margin_end(6)
toolbar.set_margin_top(6)

export_btn = Gtk.Button(label="📋 Export CSV")
export_btn.connect('clicked', self._on_export_locality_clicked)
toolbar.pack_start(export_btn, False, False, 0)

expander_box.pack_start(toolbar, False, False, 0)
expander_box.pack_start(scrolled_locality, True, True, 0)

self.locality_expander.add(expander_box)
```

### Export Method

```python
def _on_export_locality_clicked(self, button):
    """Export locality table to CSV."""
    if not self.selected_transition:
        return
    
    import csv
    from gi.repository import Gtk
    
    # File chooser dialog
    dialog = Gtk.FileChooserDialog(
        title="Export Locality Data",
        action=Gtk.FileChooserAction.SAVE
    )
    dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
    dialog.add_button("Save", Gtk.ResponseType.OK)
    dialog.set_current_name(f"locality_{self.selected_transition.name}.csv")
    
    response = dialog.run()
    if response == Gtk.ResponseType.OK:
        filename = dialog.get_filename()
        
        # Write CSV
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # Header
            writer.writerow([
                "#", "Type", "Direction", "ID", "Name",
                "Info", "Value", "Units", "Parameters"
            ])
            
            # Data
            for row in self.locality_store:
                writer.writerow(row)
        
        print(f"Exported locality data to: {filename}")
    
    dialog.destroy()
```

---

## Testing Checklist

### Basic Functionality
- [ ] Expander appears in MODELS category
- [ ] Initially hidden (no selection)
- [ ] Shows when transition selected in Analyses
- [ ] Table shows correct number of rows
- [ ] Input places marked with "← Input"
- [ ] Output places marked with "→ Output"
- [ ] Transition row has no direction marker

### Data Accuracy
- [ ] Place names match model
- [ ] Token counts are current
- [ ] Transition parameters correct (EC, Vmax, Km)
- [ ] Mass values shown for places
- [ ] Units displayed correctly

### Sorting
- [ ] Can sort by Type
- [ ] Can sort by Direction
- [ ] Can sort by ID
- [ ] Can sort by Name
- [ ] Can sort by Value (numeric)

### Edge Cases
- [ ] Source transition (no inputs) - shows only outputs
- [ ] Sink transition (no outputs) - shows only inputs
- [ ] Transition with no locality - expander hidden
- [ ] Multiple transition switches - table updates correctly
- [ ] Tab switching - selection preserved per document

### Export
- [ ] CSV export works
- [ ] Filename includes transition name
- [ ] All columns exported
- [ ] Data format correct

---

## Timeline

### Phase 1: Core Table (2-3 hours)
1. Add instance variables
2. Create `_create_locality_table()` method
3. Create `_populate_locality_table()` method
4. Add expander to UI
5. Test basic display

### Phase 2: Integration (1-2 hours)
1. Add `set_selected_locality()` method
2. Wire callback from Analyses panel
3. Test selection sync
4. Handle edge cases

### Phase 3: Polish (1 hour)
1. Add CSS styling (colors)
2. Add export button
3. Implement CSV export
4. Update documentation

**Total Estimated Time**: 4-6 hours

---

## Future Enhancements

### Phase 2 (Future)
- [ ] Click row to highlight object in canvas
- [ ] Real-time token updates during simulation
- [ ] Compare multiple localities side-by-side
- [ ] Locality metrics (balance, flow rate, etc.)

### Phase 3 (Future)
- [ ] Export to JSON/XML formats
- [ ] Include locality diagram (graphical)
- [ ] Historical token values (time series)
- [ ] Locality recommendations (optimization)

---

## Summary

This implementation adds a valuable "Show Selected Locality" feature to the Report panel that:

✅ **Unified View**: Shows transition + places in one table  
✅ **Detailed Data**: All biological/kinetic parameters visible  
✅ **Export Ready**: CSV export for reports  
✅ **Sortable**: All columns sortable for analysis  
✅ **Context Aware**: Automatically syncs with Analyses selection  
✅ **Per-Document**: Works with per-document Report panel architecture  

This feature bridges the gap between the Analyses panel (focused on plotting) and the Report panel (focused on comprehensive data summary), giving users a complete locality view for their analysis context.
