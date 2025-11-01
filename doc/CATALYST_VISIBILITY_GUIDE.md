# Catalyst Visibility in KEGG/SBML Imports

## Current Status: Why You Don't See Catalysts

### KEGG Imports ❌ (Catalysts Hidden by Default)

**Default Behavior**: Enzyme places are **NOT created** by default.

**Reason**: The `create_enzyme_places` option defaults to `False` for **clean visual layout** that matches the original KEGG pathway visualization.

```python
# In converter_base.py (line 59):
create_enzyme_places: bool = False  # Keep layout clean by default
```

**Current UI Import** (kegg_category.py line 533):
```python
document_model = convert_pathway_enhanced(
    parsed_pathway,
    coordinate_scale=coordinate_scale,
    include_cofactors=filter_cofactors,
    filter_isolated_compounds=True,
    # NOTE: create_enzyme_places NOT passed → defaults to False
    enhancement_options=enhancement_options
)
```

**Result**: 
- ✅ Compounds shown as places
- ✅ Reactions shown as transitions
- ❌ Enzymes NOT shown as places
- ❌ Test arcs NOT created

---

### SBML Imports ✅ (Catalysts Should Appear if Present)

**Default Behavior**: Modifiers are **automatically converted** to test arcs.

**Implementation** (pathway_converter.py lines 733-746):
```python
# BIOLOGICAL PETRI NET: Convert modifiers to test arcs (catalysts/enzymes)
modifier_converter = ModifierConverter(
    pathway, document,
    species_to_place, reaction_to_transition
)
test_arcs = modifier_converter.convert()

# Update metadata if test arcs exist
if test_arcs:
    document.metadata["model_type"] = "Biological Petri Net"
    document.metadata["has_test_arcs"] = True
```

**Current Test File** (BIOMD0000000001.xml):
- ❌ Does NOT contain `<listOfModifiers>` elements
- Result: No catalysts to show

---

## How to See Catalysts

### Option 1: Enable KEGG Enzyme Places (Programmatic)

Modify the KEGG import code to pass `create_enzyme_places=True`:

**File**: `src/shypn/ui/panels/pathway_operations/kegg_category.py`  
**Line**: ~533

```python
# BEFORE:
document_model = convert_pathway_enhanced(
    parsed_pathway,
    coordinate_scale=coordinate_scale,
    include_cofactors=filter_cofactors,
    filter_isolated_compounds=True,
    enhancement_options=enhancement_options
)

# AFTER:
document_model = convert_pathway_enhanced(
    parsed_pathway,
    coordinate_scale=coordinate_scale,
    include_cofactors=filter_cofactors,
    filter_isolated_compounds=True,
    create_enzyme_places=True,  # ← ADD THIS
    enhancement_options=enhancement_options
)
```

**Result**:
- Enzyme entries (type="gene"/"enzyme"/"ortholog") become places
- Test arcs created from enzyme places to reaction transitions
- Document metadata: `model_type = "Biological Petri Net"`
- Visual: Dashed lines with hollow diamonds

---

### Option 2: Add UI Checkbox (Recommended)

Add a user-facing option in the KEGG import dialog:

**Implementation Plan**:

1. **UI**: Add checkbox to KEGG import dialog
   ```
   [ ] Show enzymes as places (Biological Petri Net mode)
   ```

2. **Code**: Pass checkbox state to converter
   ```python
   show_enzymes = self.show_enzymes_checkbox.get_active()
   document_model = convert_pathway_enhanced(
       parsed_pathway,
       create_enzyme_places=show_enzymes,
       ...
   )
   ```

3. **Default**: Unchecked (clean layout)
4. **Tooltip**: "When enabled, enzyme entries become places connected by test arcs (catalysts). Useful for biological analysis but may clutter the layout."

---

### Option 3: Import SBML with Modifiers

Use SBML files that contain `<listOfModifiers>` elements:

**Example SBML with Modifier**:
```xml
<reaction id="R1">
  <listOfReactants>
    <speciesReference species="Glucose"/>
  </listOfReactants>
  <listOfProducts>
    <speciesReference species="G6P"/>
  </listOfProducts>
  <listOfModifiers>
    <modifierSpeciesReference species="Hexokinase"/>
  </listOfModifiers>
</reaction>
```

**Result**: Hexokinase becomes a place with a test arc to reaction R1.

---

## Expected Visual Appearance

When catalysts ARE visible, you should see:

```
     [Enzyme]
        |  (dashed line with hollow diamond)
        ↓
[S] → [T] → [P]
```

**Visual Characteristics**:
- ✅ Enzyme place: Circle (like other places)
- ✅ Test arc: Dashed line (indicates non-consuming)
- ✅ Endpoint: Hollow diamond (catalyst symbol)
- ✅ Color: Gray (less prominent than normal arcs)
- ✅ Connection: Perimeter-to-perimeter (fixed in latest patch)

---

## Why Catalysts Are Hidden by Default (KEGG)

### Rationale

1. **Visual Clarity**: KEGG pathways are already dense with compounds and reactions
2. **Layout Quality**: Adding 10-50+ enzyme places can disrupt hierarchical layout
3. **KEGG Convention**: Original KEGG visualization shows enzymes as labels, not nodes
4. **Default Use Case**: Most users want to see substrate/product flow, not enzyme mechanics

### When to Enable

Enable `create_enzyme_places=True` when:
- Analyzing enzyme regulation patterns
- Studying multi-substrate enzyme mechanisms
- Performing biological topology analysis
- Using Dependency & Coupling Analyzer
- Using Regulatory Structure Analyzer
- Need explicit catalyst representation for biological questions

Keep disabled (default) when:
- Visualizing metabolic pathways
- Analyzing substrate/product flow
- Presenting to non-technical audiences
- Layout clarity is priority
- Classical Petri net analysis sufficient

---

## Testing Catalyst Visibility

### Quick Test: KEGG with Enzymes

```python
from shypn.importer.kegg import parse_kgml_file, convert_pathway

# Parse KEGG pathway
pathway = parse_kgml_file("path/to/kegg_pathway.xml")

# Convert WITH enzyme places
document = convert_pathway(pathway, create_enzyme_places=True)

# Check results
print(f"Places: {len(document.places)}")
print(f"Transitions: {len(document.transitions)}")
print(f"Arcs: {len(document.arcs)}")

# Count test arcs
test_arcs = [a for a in document.arcs if hasattr(a, 'consumes_tokens') and not a.consumes_tokens()]
print(f"Test arcs (catalysts): {len(test_arcs)}")

# Check metadata
print(f"Model type: {document.metadata.get('model_type', 'Standard')}")
```

### Quick Test: SBML with Modifiers

```python
from shypn.data.sbml.sbml_parser import SBMLParser
from shypn.data.pathway.pathway_converter import PathwayConverter

# Parse SBML
parser = SBMLParser()
pathway = parser.parse_file("path/to/sbml_with_modifiers.xml")

# Convert (modifiers → test arcs automatically)
converter = PathwayConverter()
document = converter.convert(pathway)

# Check for test arcs
test_arcs = [a for a in document.arcs if type(a).__name__ == 'TestArc']
print(f"Test arcs found: {len(test_arcs)}")
print(f"Model type: {document.metadata.get('model_type', 'Standard')}")
```

---

## Implementation Status

| Feature | Status | Notes |
|---------|--------|-------|
| Test arc implementation | ✅ Complete | Non-consuming, visual: dashed + hollow diamond |
| Test arc rendering (perimeter-to-perimeter) | ✅ Fixed | Latest patch |
| SBML modifier → test arc conversion | ✅ Complete | Automatic in PathwayConverter |
| KEGG enzyme → test arc conversion | ✅ Complete | KEGGEnzymeConverter class |
| KEGG `create_enzyme_places` option | ✅ Complete | Defaults to False |
| UI checkbox for enzyme visibility | ❌ Not implemented | Would require kegg_category.py changes |
| Enzyme positioning in layout | ❌ Not implemented | Issue #3/4 in TEST_ARC_REFINEMENTS.md |

---

## Recommendation: Add UI Control

**Immediate Action**: Add checkbox to KEGG import dialog

**Benefits**:
1. Users can choose when to see enzymes
2. No code changes needed for different use cases
3. Self-documenting (checkbox explains what it does)
4. Preserves current default (clean layout)

**Implementation**:
1. Add checkbox to KEGG import UI (GTK CheckButton)
2. Pass state to `convert_pathway_enhanced()`
3. Add tooltip explaining biological analysis vs visual clarity tradeoff

This gives users **control** while maintaining the current sensible default! 🎯
