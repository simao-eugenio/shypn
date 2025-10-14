# Initial Markings from BioModels - Quick Reference

**Question**: "Can we get initial markings for the model when fetching pathway data from BioModels?"

**Answer**: ✅ **YES - Already fully implemented and working!**

---

## Summary

When you import SBML files from BioModels (or other sources):

1. ✅ Initial concentrations **automatically extracted** from SBML
2. ✅ Concentrations **converted to discrete tokens** (with scale factor)
3. ✅ Tokens **applied to places** as initial markings
4. ✅ Original values **preserved in metadata**
5. ✅ Reset button **restores initial state**

**No coding needed** - it just works! 🎉

---

## How It Works

```
SBML File                                Petri Net Place
─────────                                ───────────────
<species id="glucose"                    Place: "Glucose"
  initialConcentration="5.0"/>    →      tokens: 50
                                         initial_marking: 50
(with scale_factor=10.0)                 metadata.concentration: 5.0
```

---

## Configuration

### Scale Factor (Token Conversion)

**Located in**: `PathwayPostProcessor(scale_factor=...)`

```python
# How many tokens per 1 mM concentration?

scale_factor = 1.0    # 1 mM → 1 token   (small scale)
scale_factor = 10.0   # 1 mM → 10 tokens (recommended)
scale_factor = 100.0  # 1 mM → 100 tokens (large scale)
```

**Examples**:
- Glucose: 5.0 mM × 10.0 = **50 tokens**
- ATP: 2.5 mM × 10.0 = **25 tokens**
- G6P: 0.0 mM × 10.0 = **0 tokens** (empty)

**Recommendation**: Use `scale_factor=10.0` for most BioModels pathways.

---

## File Locations

| Component | File | What It Does |
|-----------|------|--------------|
| **Parser** | `src/shypn/data/pathway/sbml_parser.py` | Extracts initial concentrations from SBML |
| **Normalizer** | `src/shypn/data/pathway/pathway_postprocessor.py` | Converts concentrations → tokens |
| **Converter** | `src/shypn/data/pathway/pathway_converter.py` | Applies tokens to places |
| **Data** | `src/shypn/data/pathway/pathway_data.py` | Species and Place data structures |

---

## Code Snippets

### Parsing (Automatic)
```python
# In sbml_parser.py - already implemented
if sbml_species.isSetInitialConcentration():
    initial_concentration = sbml_species.getInitialConcentration()
elif sbml_species.isSetInitialAmount():
    initial_concentration = sbml_species.getInitialAmount()
else:
    initial_concentration = 0.0  # Default
```

### Normalization (Automatic)
```python
# In pathway_postprocessor.py - already implemented
concentration = species.initial_concentration
tokens = max(0, round(concentration * scale_factor))
species.initial_tokens = tokens
```

### Application (Automatic)
```python
# In pathway_converter.py - already implemented
place.set_tokens(species.initial_tokens)
place.set_initial_marking(species.initial_tokens)
```

---

## Testing

### Quick Test with Repressilator

1. **Download**:
   ```bash
   wget "https://www.ebi.ac.uk/biomodels/model/download/BIOMD0000000012.2?filename=BIOMD0000000012_url.xml"
   ```

2. **Import in Shypn**:
   - File → Import → From BioModels
   - Select downloaded file

3. **Verify**:
   - Each place should show token circles
   - Right-click place → Properties
   - Check "Tokens" field has value > 0
   - Check "Initial Marking" matches "Tokens"

4. **Test Reset**:
   - Run simulation (tokens change)
   - Click "Reset" button
   - Verify tokens return to initial values ✓

---

## Data Structures

### Species (After Parsing)
```python
species.id = "glucose"
species.name = "Glucose"
species.initial_concentration = 5.0    # From SBML (mM)
species.initial_tokens = 0             # Not set yet
```

### Species (After Post-Processing)
```python
species.id = "glucose"
species.name = "Glucose"
species.initial_concentration = 5.0    # Preserved
species.initial_tokens = 50            # Now set! (5.0 × 10)
```

### Place (After Conversion)
```python
place.label = "Glucose"
place.tokens = 50                      # Current state
place.initial_marking = 50             # Reset reference
place.metadata = {
    'species_id': 'glucose',
    'concentration': 5.0,              # Original SBML value
    'compartment': 'cytosol'
}
```

---

## Visual Example

### Before Simulation
```
Glucose: ●●●●● (50 tokens)
     ↓
Hexokinase (transition)
     ↓
   G6P: (empty - 0 tokens)
```

### After Running Simulation
```
Glucose: ●●● (30 tokens)
     ↓
Hexokinase
     ↓
   G6P: ●●●● (20 tokens)
```

### After Clicking "Reset"
```
Glucose: ●●●●● (50 tokens) ← Restored!
     ↓
Hexokinase
     ↓
   G6P: (empty - 0 tokens) ← Restored!
```

---

## Common Scenarios

### Scenario 1: All Species Have Initial Values
```xml
<species id="glucose" initialConcentration="5.0"/>
<species id="atp" initialConcentration="2.5"/>
<species id="g6p" initialConcentration="1.0"/>
```
✅ **Result**: All places get tokens (50, 25, 10 with scale=10)

### Scenario 2: Some Species Empty
```xml
<species id="glucose" initialConcentration="5.0"/>
<species id="product" initialConcentration="0.0"/>
```
✅ **Result**: Glucose gets 50 tokens, Product gets 0 tokens

### Scenario 3: No Initial Values Specified
```xml
<species id="molecule"/>  <!-- No initial value -->
```
✅ **Result**: Defaults to 0 tokens (safe fallback)

### Scenario 4: Very Small Concentrations
```xml
<species id="enzyme" initialConcentration="0.001"/>  <!-- 1 µM -->
```
- With scale=1: 0.001 × 1 = 0.001 → **0 tokens** ❌ (rounds down)
- With scale=10: 0.001 × 10 = 0.01 → **0 tokens** ❌ (still too small)
- With scale=1000: 0.001 × 1000 = 1.0 → **1 token** ✅

**Solution**: Adjust scale factor if many concentrations round to zero.

---

## Adjusting Scale Factor

### Where to Change It

**Option 1: In Code** (during import pipeline)
```python
# In pathway import handler
postprocessor = PathwayPostProcessor(
    spacing=150.0,
    scale_factor=10.0  # ← Change this value
)
```

**Option 2: User Setting** (future enhancement)
```python
# Could add to preferences dialog
Settings → Import → SBML Scale Factor: [10.0]
```

### Choosing the Right Scale

| Concentration Range | Recommended Scale | Example |
|---------------------|-------------------|---------|
| 0.1 - 10 mM | 10.0 | Glycolysis metabolites |
| 0.01 - 1 mM | 100.0 | Trace metabolites |
| 1 - 100 mM | 1.0 | High-abundance species |
| Mixed ranges | 10.0 - 50.0 | Most BioModels pathways |

**Rule of Thumb**: Choose scale so smallest non-zero concentration → ≥ 1 token

---

## Metadata Preservation

All original SBML data is preserved in place metadata:

```python
# Access original concentration
place.metadata['concentration']  # → 5.0 (mM from SBML)

# Access species ID
place.metadata['species_id']     # → "C00031" (KEGG ID)

# Access compartment
place.metadata['compartment']    # → "cytosol"
```

This allows:
- ✅ Traceability back to original model
- ✅ Export back to SBML with original units
- ✅ Display original values in properties dialog
- ✅ Unit conversion for analysis/plotting

---

## Troubleshooting

### Problem: All places have 0 tokens
**Cause**: Scale factor too small for concentration range  
**Solution**: Increase `scale_factor` (try 10.0, 100.0, or 1000.0)

### Problem: Simulation is very slow
**Cause**: Scale factor too large (too many tokens)  
**Solution**: Decrease `scale_factor` (try 1.0, 5.0, or 10.0)

### Problem: Some places empty when shouldn't be
**Cause**: Small concentrations rounding down to 0  
**Solution**: Increase `scale_factor` or check SBML has `initialConcentration`

### Problem: Can't find where scale is set
**Location**: Look for `PathwayPostProcessor` instantiation in import handler  
**File**: `src/shypn/helpers/model_canvas_loader.py` (likely) or import dialog

---

## Implementation Status

| Feature | Status | File |
|---------|--------|------|
| Extract initial concentration | ✅ Complete | `sbml_parser.py:107-112` |
| Extract initial amount | ✅ Complete | `sbml_parser.py:109-110` |
| Default to 0 if missing | ✅ Complete | `sbml_parser.py:111-112` |
| Convert to tokens | ✅ Complete | `pathway_postprocessor.py:316-321` |
| Apply to places | ✅ Complete | `pathway_converter.py:104-105` |
| Set initial_marking | ✅ Complete | `pathway_converter.py:105` |
| Preserve metadata | ✅ Complete | `pathway_converter.py:112-116` |
| Round to integer | ✅ Complete | `pathway_postprocessor.py:321` |
| Non-negative tokens | ✅ Complete | `pathway_postprocessor.py:321` |
| Compartment volumes | ✅ Complete | `sbml_parser.py:122-123` |

**All features implemented!** No work needed. 🎉

---

## See Also

- **Full Documentation**: `doc/PATHWAY_INITIAL_MARKINGS_COMPLETE.md`
- **Import Architecture**: `doc/PATHWAY_IMPORT_ARCHITECTURE.md`
- **Data Structures**: `src/shypn/data/pathway/pathway_data.py`
- **SBML Parser**: `src/shypn/data/pathway/sbml_parser.py`
- **Post-Processor**: `src/shypn/data/pathway/pathway_postprocessor.py`
- **Converter**: `src/shypn/data/pathway/pathway_converter.py`

---

## Quick Answer

**Q**: Can we get initial markings from BioModels?  
**A**: ✅ **YES - Already working!** Import SBML → Places automatically get tokens from initial concentrations. Just import and run simulation! 🚀
