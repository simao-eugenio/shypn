# REPORT MODELS CATEGORY - REFINEMENT PROPOSAL
## Tabulated Data Instead of Text Lists

**Date**: November 2, 2025  
**Refinement Goal**: Replace text lists with structured tables for better data presentation

---

## CURRENT IMPLEMENTATION (Text Lists)

### Species/Places List - Current Format:
```
1. [P45] C00033 | KEGG:cpd:C00033
2. [P88] C00103 | KEGG:cpd:C00103, Formula:C6H12O6
3. [P89] C00631 | KEGG:cpd:C00631, Mass:180.16
```

**Problems:**
- Hard to scan visually
- Difficult to compare values
- No column alignment
- Mixed metadata presentation

### Reactions/Transitions List - Current Format:
```
1. [T1] R00710 | stochastic | KEGG:42, EC:2.7.1.1
2. [T2] R00711 | stochastic | KEGG:44, EC:5.3.1.9
```

**Problems:**
- Same issues as species list
- Kinetic parameters hidden in metadata
- Type mixing with data

---

## PROPOSED REFINEMENT: TABULATED DATA

### Section 4: Species/Places Table

**Component**: GTK TreeView with sortable columns  
**Display**: Expander with scrollable table  
**Default State**: Collapsed

#### Table Columns:

| # | Petri Net ID | Biological Name | KEGG ID | Initial Tokens | Formula | Mass | Type |
|---|--------------|-----------------|---------|----------------|---------|------|------|
| 1 | P45 | Acetate | cpd:C00033 | 0 | C2H4O2 | 60.05 | metabolite |
| 2 | P88 | D-Glucose | cpd:C00103 | 10 | C6H12O6 | 180.16 | substrate |
| 3 | P89 | 2-Phosphoglycerate | cpd:C00631 | 0 | C3H7O7P | 186.06 | intermediate |

#### Column Details:

1. **# (Index)**
   - **Type**: Integer
   - **Purpose**: Sequential numbering
   - **Sortable**: No
   - **Width**: Fixed 40px

2. **Petri Net ID**
   - **Field**: `place.id`
   - **Type**: String
   - **Purpose**: Internal identifier
   - **Sortable**: Yes
   - **Example**: `P45`, `P88`, `P_glucose_6_phosphate`

3. **Biological Name**
   - **Field**: `place.label` or `place.name`
   - **Type**: String
   - **Purpose**: Human-readable name
   - **Sortable**: Yes
   - **Example**: `D-Glucose`, `ATP`, `Pyruvate`

4. **KEGG ID**
   - **Field**: `place.metadata['kegg_id']` or `place.metadata['compound_id']`
   - **Type**: String
   - **Purpose**: Cross-reference to KEGG database
   - **Sortable**: Yes
   - **Example**: `cpd:C00103`, `cpd:C00002`
   - **Empty**: `-` if not available

5. **Initial Tokens**
   - **Field**: `place.initial_marking` or `place.tokens`
   - **Type**: Numeric (int or float)
   - **Purpose**: Initial concentration/amount
   - **Sortable**: Yes (numeric)
   - **Format**: Integer or scientific notation for large numbers
   - **Example**: `0`, `10`, `1.5e6`
   - **Empty**: `0` (default)

6. **Formula**
   - **Field**: `place.metadata['formula']`
   - **Type**: String
   - **Purpose**: Chemical formula
   - **Sortable**: Yes
   - **Example**: `C6H12O6`, `C10H16N5O13P3`
   - **Empty**: `-` if not available

7. **Mass**
   - **Field**: `place.metadata['mass']` or `place.metadata['molecular_weight']`
   - **Type**: Numeric (float)
   - **Purpose**: Molecular weight (g/mol)
   - **Sortable**: Yes (numeric)
   - **Format**: `{mass:.2f}`
   - **Example**: `180.16`, `507.18`
   - **Empty**: `-` if not available

8. **Type**
   - **Field**: `place.metadata['type']` or inferred
   - **Type**: String (enum)
   - **Purpose**: Biological classification
   - **Sortable**: Yes
   - **Values**: `metabolite`, `substrate`, `product`, `intermediate`, `cofactor`, `enzyme`
   - **Example**: `metabolite`, `cofactor`
   - **Empty**: `unknown`

#### Additional Columns (Optional, toggleable):

9. **Compartment** - `place.metadata['compartment']` (e.g., `cytoplasm`, `mitochondria`)
10. **Charge** - `place.metadata['charge']` (e.g., `-2`, `0`)
11. **Current Tokens** - `place.tokens` (current marking, may differ from initial)

---

### Section 5: Reactions/Transitions Table

**Component**: GTK TreeView with sortable columns  
**Display**: Expander with scrollable table  
**Default State**: Collapsed

#### Table Columns:

| # | Petri Net ID | Biological Name | Type | KEGG Reaction | EC Number | Rate Law | Rate Constant | Reversible |
|---|--------------|-----------------|------|---------------|-----------|----------|---------------|------------|
| 1 | T1 | Hexokinase | stochastic | rn:R00710 | 2.7.1.1 | mass_action | k=0.5 | No |
| 2 | T2 | Glucose-6-phosphate isomerase | stochastic | rn:R00711 | 5.3.1.9 | michaelis_menten | Vmax=10, Km=0.1 | Yes |
| 3 | T9 | Pyruvate dehydrogenase | continuous | rn:R00200 | 1.2.4.1 | hill | k=2.5, n=4 | No |

#### Column Details:

1. **# (Index)**
   - **Type**: Integer
   - **Purpose**: Sequential numbering
   - **Sortable**: No
   - **Width**: Fixed 40px

2. **Petri Net ID**
   - **Field**: `transition.id`
   - **Type**: String
   - **Purpose**: Internal identifier
   - **Sortable**: Yes
   - **Example**: `T1`, `T_hexokinase`, `R_PFK`

3. **Biological Name**
   - **Field**: `transition.label` or `transition.name`
   - **Type**: String
   - **Purpose**: Reaction/enzyme name
   - **Sortable**: Yes
   - **Example**: `Hexokinase`, `Phosphofructokinase`, `R00710`

4. **Type**
   - **Field**: `transition.transition_type`
   - **Type**: String (enum)
   - **Purpose**: Petri net transition type
   - **Sortable**: Yes
   - **Values**: `stochastic`, `continuous`, `timed`, `immediate`
   - **Example**: `stochastic`, `continuous`
   - **Color-coded**: Different background colors for each type

5. **KEGG Reaction**
   - **Field**: `transition.metadata['kegg_reaction_id']` or `transition.metadata['kegg_reaction_name']`
   - **Type**: String
   - **Purpose**: Cross-reference to KEGG reaction database
   - **Sortable**: Yes
   - **Example**: `rn:R00710`, `rn:R00711`
   - **Empty**: `-` if not available

6. **EC Number**
   - **Field**: `transition.metadata['ec_number']` or `transition.metadata['ec_numbers'][0]`
   - **Type**: String
   - **Purpose**: Enzyme Commission number
   - **Sortable**: Yes
   - **Example**: `2.7.1.1`, `5.3.1.9`
   - **Empty**: `-` if not available

7. **Rate Law**
   - **Field**: `transition.metadata['kinetic_law']` or `transition.metadata['kinetics_rule']`
   - **Type**: String (enum)
   - **Purpose**: Type of kinetic equation
   - **Sortable**: Yes
   - **Values**: `mass_action`, `michaelis_menten`, `hill`, `custom`, `constant`
   - **Example**: `michaelis_menten`, `mass_action`
   - **Empty**: `-` if not available

8. **Rate Constant / Parameters**
   - **Field**: `transition.metadata['kinetics_parameters']` or extracted from metadata
   - **Type**: String (formatted)
   - **Purpose**: Kinetic parameters
   - **Sortable**: No (complex data)
   - **Format**: 
     - Simple: `k=0.5`
     - Complex: `Vmax=10, Km=0.1`
     - Multiple: `k1=2.5, k2=1.3, n=4`
   - **Example**: `k=0.5`, `Vmax=10, Km=0.1`
   - **Empty**: `-` if not available

9. **Reversible**
   - **Field**: `transition.metadata['reversible']`
   - **Type**: Boolean (displayed as Yes/No)
   - **Purpose**: Whether reaction can go backward
   - **Sortable**: Yes
   - **Display**: `Yes` / `No` or `✓` / `✗`
   - **Example**: `Yes`, `No`
   - **Empty**: `Unknown` if not specified

#### Additional Columns (Optional, toggleable):

10. **Stoichiometry** - Summary of inputs/outputs (e.g., `2ATP + Glucose → 2ADP + G6P`)
11. **Enabled** - Current enablement state (in simulation context)
12. **Fire Count** - Number of times fired (in simulation context)
13. **Pathway** - Associated pathway (e.g., `Glycolysis`, `TCA Cycle`)

---

## IMPLEMENTATION PLAN

### Phase 1: Replace Text Lists with Tables

**Files to Modify:**
- `src/shypn/ui/panels/report/model_structure_category.py`

**Changes:**

1. **Replace Species Expander**:
   ```python
   # OLD: GTK TextView with text buffer
   self.species_expander = Gtk.Expander(label="Show Species/Places List")
   scrolled, self.species_textview, self.species_buffer = self._create_scrolled_textview()
   
   # NEW: GTK TreeView with table
   self.species_expander = Gtk.Expander(label="Show Species/Places Table")
   scrolled, self.species_treeview, self.species_store = self._create_species_table()
   ```

2. **Replace Reactions Expander**:
   ```python
   # OLD: GTK TextView with text buffer
   self.reactions_expander = Gtk.Expander(label="Show Reactions/Transitions List")
   scrolled, self.reactions_textview, self.reactions_buffer = self._create_scrolled_textview()
   
   # NEW: GTK TreeView with table
   self.reactions_expander = Gtk.Expander(label="Show Reactions/Transitions Table")
   scrolled, self.reactions_treeview, self.reactions_store = self._create_reactions_table()
   ```

### Phase 2: Create Table Builders

**New Methods:**

```python
def _create_species_table(self):
    """Create TreeView for species/places with sortable columns.
    
    Returns:
        tuple: (ScrolledWindow, TreeView, ListStore)
    """
    # Create ListStore with column types
    # Columns: index (int), id (str), name (str), kegg_id (str), 
    #          tokens (float), formula (str), mass (float), type (str)
    store = Gtk.ListStore(int, str, str, str, float, str, float, str)
    
    # Create TreeView
    treeview = Gtk.TreeView(model=store)
    treeview.set_grid_lines(Gtk.TreeViewGridLines.BOTH)
    
    # Add columns with renderers
    self._add_column(treeview, "#", 0, width=40)
    self._add_column(treeview, "Petri Net ID", 1, sortable=True)
    self._add_column(treeview, "Biological Name", 2, sortable=True)
    self._add_column(treeview, "KEGG ID", 3, sortable=True)
    self._add_column(treeview, "Initial Tokens", 4, sortable=True, numeric=True)
    self._add_column(treeview, "Formula", 5, sortable=True)
    self._add_column(treeview, "Mass (g/mol)", 6, sortable=True, numeric=True)
    self._add_column(treeview, "Type", 7, sortable=True)
    
    # Create scrolled window
    scrolled = Gtk.ScrolledWindow()
    scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
    scrolled.set_min_content_height(300)
    scrolled.add(treeview)
    
    return scrolled, treeview, store

def _create_reactions_table(self):
    """Create TreeView for reactions/transitions with sortable columns.
    
    Returns:
        tuple: (ScrolledWindow, TreeView, ListStore)
    """
    # Create ListStore with column types
    # Columns: index (int), id (str), name (str), type (str), 
    #          kegg_reaction (str), ec_number (str), rate_law (str),
    #          parameters (str), reversible (str)
    store = Gtk.ListStore(int, str, str, str, str, str, str, str, str)
    
    # Create TreeView
    treeview = Gtk.TreeView(model=store)
    treeview.set_grid_lines(Gtk.TreeViewGridLines.BOTH)
    
    # Add columns with renderers
    self._add_column(treeview, "#", 0, width=40)
    self._add_column(treeview, "Petri Net ID", 1, sortable=True)
    self._add_column(treeview, "Biological Name", 2, sortable=True)
    self._add_column(treeview, "Type", 3, sortable=True)
    self._add_column(treeview, "KEGG Reaction", 4, sortable=True)
    self._add_column(treeview, "EC Number", 5, sortable=True)
    self._add_column(treeview, "Rate Law", 6, sortable=True)
    self._add_column(treeview, "Parameters", 7, sortable=False)
    self._add_column(treeview, "Reversible", 8, sortable=True)
    
    # Create scrolled window
    scrolled = Gtk.ScrolledWindow()
    scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
    scrolled.set_min_content_height(300)
    scrolled.add(treeview)
    
    return scrolled, treeview, store

def _add_column(self, treeview, title, column_id, sortable=False, 
                width=None, numeric=False):
    """Helper to add a column to TreeView.
    
    Args:
        treeview: TreeView widget
        title: Column title
        column_id: Column index in ListStore
        sortable: Whether column is sortable
        width: Fixed width (None for auto)
        numeric: Whether to right-align (for numbers)
    """
    renderer = Gtk.CellRendererText()
    if numeric:
        renderer.set_property('xalign', 1.0)  # Right-align numbers
    
    column = Gtk.TreeViewColumn(title, renderer, text=column_id)
    column.set_resizable(True)
    if width:
        column.set_fixed_width(width)
    if sortable:
        column.set_sort_column_id(column_id)
    
    treeview.append_column(column)
```

### Phase 3: Populate Tables

**Updated Refresh Method:**

```python
def refresh(self):
    """Refresh models data with tabulated information."""
    # ... existing overview/structure/provenance code ...
    
    # Populate species table
    self._populate_species_table(model)
    
    # Populate reactions table
    self._populate_reactions_table(model)

def _populate_species_table(self, model):
    """Populate species table with current model data."""
    self.species_store.clear()
    
    for i, place in enumerate(model.places, 1):
        # Extract data
        place_id = place.id if hasattr(place, 'id') else f"P{i}"
        name = place.label if hasattr(place, 'label') and place.label else place_id
        
        # KEGG ID
        kegg_id = "-"
        if hasattr(place, 'metadata') and place.metadata:
            kegg_id = place.metadata.get('kegg_id', 
                      place.metadata.get('compound_id', '-'))
        
        # Initial tokens
        tokens = 0.0
        if hasattr(place, 'initial_marking'):
            tokens = float(place.initial_marking)
        elif hasattr(place, 'tokens'):
            tokens = float(place.tokens)
        
        # Formula
        formula = "-"
        if hasattr(place, 'metadata') and place.metadata:
            formula = place.metadata.get('formula', '-')
        
        # Mass
        mass = 0.0
        if hasattr(place, 'metadata') and place.metadata:
            mass_val = place.metadata.get('mass', 
                       place.metadata.get('molecular_weight', 0))
            if mass_val:
                mass = float(mass_val)
        
        # Type
        type_val = "unknown"
        if hasattr(place, 'metadata') and place.metadata:
            type_val = place.metadata.get('type', 'unknown')
        
        # Add row to table
        self.species_store.append([
            i,           # index
            place_id,    # Petri Net ID
            name,        # Biological Name
            kegg_id,     # KEGG ID
            tokens,      # Initial Tokens
            formula,     # Formula
            mass,        # Mass
            type_val     # Type
        ])

def _populate_reactions_table(self, model):
    """Populate reactions table with current model data."""
    self.reactions_store.clear()
    
    for i, transition in enumerate(model.transitions, 1):
        # Extract data
        trans_id = transition.id if hasattr(transition, 'id') else f"T{i}"
        name = transition.label if hasattr(transition, 'label') and transition.label else trans_id
        
        # Type
        trans_type = "unknown"
        if hasattr(transition, 'transition_type'):
            trans_type = transition.transition_type
        
        # KEGG Reaction
        kegg_reaction = "-"
        if hasattr(transition, 'metadata') and transition.metadata:
            kegg_reaction = transition.metadata.get('kegg_reaction_id',
                           transition.metadata.get('kegg_reaction_name', '-'))
        
        # EC Number
        ec_number = "-"
        if hasattr(transition, 'metadata') and transition.metadata:
            ec_val = transition.metadata.get('ec_number',
                     transition.metadata.get('ec_numbers', []))
            if isinstance(ec_val, list) and ec_val:
                ec_number = ec_val[0]
            elif ec_val:
                ec_number = str(ec_val)
        
        # Rate Law
        rate_law = "-"
        if hasattr(transition, 'metadata') and transition.metadata:
            rate_law = transition.metadata.get('kinetic_law',
                       transition.metadata.get('kinetics_rule', '-'))
        
        # Parameters (formatted string)
        parameters = "-"
        if hasattr(transition, 'metadata') and transition.metadata:
            params = transition.metadata.get('kinetics_parameters', {})
            if params:
                params_str = ", ".join([f"{k}={v}" for k, v in params.items()])
                parameters = params_str
        
        # Reversible
        reversible = "Unknown"
        if hasattr(transition, 'metadata') and transition.metadata:
            rev_val = transition.metadata.get('reversible')
            if rev_val is not None:
                reversible = "Yes" if rev_val else "No"
        
        # Add row to table
        self.reactions_store.append([
            i,               # index
            trans_id,        # Petri Net ID
            name,            # Biological Name
            trans_type,      # Type
            kegg_reaction,   # KEGG Reaction
            ec_number,       # EC Number
            rate_law,        # Rate Law
            parameters,      # Parameters
            reversible       # Reversible
        ])
```

---

## BENEFITS OF TABULATED DATA

1. **Better Visual Scanning**: Columns align, easy to compare values
2. **Sortable**: Click column headers to sort by any field
3. **Filterable**: Future enhancement - add search box above table
4. **Selectable**: Click rows to select/copy individual entries
5. **Exportable**: Tables export cleanly to CSV, Excel, PDF
6. **Professional**: Standard data presentation format
7. **Extensible**: Easy to add/remove columns
8. **Performance**: TreeView handles thousands of rows efficiently

---

## EXPORT ENHANCEMENTS

### CSV Export:
```csv
#,Petri Net ID,Biological Name,KEGG ID,Initial Tokens,Formula,Mass,Type
1,P45,Acetate,cpd:C00033,0,C2H4O2,60.05,metabolite
2,P88,D-Glucose,cpd:C00103,10,C6H12O6,180.16,substrate
```

### Excel Export:
- Proper column types (numeric for tokens/mass)
- Formatting (bold headers, alternating row colors)
- Frozen header row
- Auto-fit columns

### PDF Export:
- Professional table layout
- Page breaks at appropriate points
- Column headers repeated on each page

---

## SUMMARY OF REFINEMENTS

### What Changes:
1. ✅ **Species/Places**: Text list → Sortable table with 8 columns
2. ✅ **Reactions/Transitions**: Text list → Sortable table with 9 columns
3. ✅ **Add kinetic parameters column** - Previously hidden in metadata
4. ✅ **Add initial tokens column** - Concentration/marking data
5. ✅ **Add reversibility column** - Important reaction property
6. ✅ **Sortable by any column** - Better data exploration
7. ✅ **Professional presentation** - Industry-standard table format

### What Stays:
1. ✅ Overview section (text is fine for metadata)
2. ✅ Structure section (counts are fine as text)
3. ✅ Provenance section (metadata is fine as text)
4. ✅ Manual refresh policy
5. ✅ Expandable sections (collapsed by default)

### Implementation Effort:
- **Lines of code**: ~300-400 new lines
- **Files modified**: 1 (`model_structure_category.py`)
- **Testing**: Use existing test script
- **Backwards compatibility**: No breaking changes
