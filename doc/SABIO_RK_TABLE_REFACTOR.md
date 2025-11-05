# SABIO-RK Results Table Refactor

**Date:** November 4, 2025  
**Status:** ✅ COMPLETE

## Changes Requested

User requested table refactoring with the following fixes:

1. **ID Column**: Show transition internal ID (from model) ✅
2. **Name Column**: Show KEGG reaction code (e.g., R00746) ✅
3. **EC Number**: Keep as-is ✅
4. **Parameter Columns**: Add Vmax, Km, Kcat, Ki as separate columns ✅
5. **Organism**: Fix display (was showing 'REAC_0', should show organism name) ✅

## Implementation

### 1. Enhanced SBML Parser (`sabio_rk_client.py`)

**Added RDF Annotation Parsing (lines 292-310):**
```python
# Define RDF namespace for annotations
rdf_ns = {'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
          'bqbiol': 'http://biomodels.net/biology-qualifiers/'}

# Extract KEGG reaction ID from annotations
kegg_refs = annotation.findall('.//rdf:li[@rdf:resource]', rdf_ns)
for ref in kegg_refs:
    resource = ref.get('{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource', '')
    if 'kegg.reaction' in resource:
        kegg_reaction_id = resource.split('/')[-1]  # Extract "R00299"
        break
```

**Enhanced Parameter Metadata (lines 340-345):**
```python
all_parameters.append({
    'reaction_id': reaction_id,
    'reaction_name': reaction_name,
    'kegg_reaction_id': kegg_reaction_id,  # NEW: KEGG R-ID
    'organism': organism or 'Unknown',      # NEW: Organism name
    'parameter_id': param_id,
    'parameter_name': param_name,
    'value': value_float,
    'units': param_units,
    'parameter_type': self._classify_parameter(param_id, param_name)
})
```

**Added Organism Tracking (lines 114-118):**
```python
# Add query organism to result for display
if result and organism:
    result['query_organism'] = organism
```

**Added Taxonomy Mapping (lines 369-387):**
```python
def _map_taxonomy_id(self, tax_id: str) -> str:
    """Map NCBI taxonomy IDs to organism names."""
    tax_map = {
        '9606': 'Homo sapiens',
        '10090': 'Mus musculus',
        '562': 'Escherichia coli',
        '4932': 'Saccharomyces cerevisiae',
        # ... more mappings
    }
    return tax_map.get(tax_id, f'Tax:{tax_id}')
```

### 2. Refactored Table Structure (`sabio_rk_category.py`)

**New Table Columns (lines 270-288):**
```python
self.results_store = Gtk.ListStore(
    bool,    # 0: Select checkbox
    str,     # 1: Transition ID (internal model ID)
    str,     # 2: Reaction ID (KEGG R-ID)
    str,     # 3: EC Number
    str,     # 4: Vmax
    str,     # 5: Km
    str,     # 6: Kcat
    str,     # 7: Ki
    str,     # 8: Organism
    object   # 9: Result data (hidden)
)

columns = [
    ("ID", 1, 80),           # Transition internal ID
    ("Reaction", 2, 100),    # KEGG R-ID (R00746, R00299, etc.)
    ("EC", 3, 90),           # EC number (2.7.1.1)
    ("Vmax", 4, 120),        # Vmax values with units
    ("Km", 5, 120),          # Km values with units
    ("Kcat", 6, 120),        # Kcat values with units
    ("Ki", 7, 120),          # Ki values with units
    ("Organism", 8, 150)     # Organism name (Homo sapiens)
]
```

**Refactored Data Population (lines 557-623):**
```python
# Group parameters by reaction_id
reactions = defaultdict(lambda: {
    'kegg_reaction_id': None,
    'organism': query_organism or 'Unknown',
    'Vmax': [], 'Km': [], 'Kcat': [], 'Ki': []
})

for param in parameters:
    reaction_id = param.get('reaction_id')
    param_type = param.get('parameter_type')
    
    # Collect metadata
    if not reactions[reaction_id]['kegg_reaction_id']:
        reactions[reaction_id]['kegg_reaction_id'] = param.get('kegg_reaction_id')
    
    # Group parameters by type
    value = param.get('value')
    units = param.get('units', '')
    if value is not None and param_type in reactions[reaction_id]:
        reactions[reaction_id][param_type].append(f"{value:.3g} {units}")

# Add one row per reaction
for reaction_id, reaction_data in reactions.items():
    self.results_store.append([
        True,
        result.get('transition_id'),           # T1, T2, T3 (model ID)
        reaction_data['kegg_reaction_id'],     # R00299, R01326 (KEGG)
        result.get('identifiers', {}).get('ec_number'),  # 2.7.1.1
        vmax,  # "9.31e-07 M/s" or "-"
        km,    # "0.0006 M, 4.7e-05 M" or "-"
        kcat,  # "2.89e+05 /s" or "-"
        ki,    # "2.2e-05 M, 1.5e-05 M" or "-"
        organism,  # "Homo sapiens"
        result
    ])
```

## Before vs After

### Before (Old Table):
| ☑ | ID | Name | EC | Parameters | Organism |
|---|----|----|----|----|---|
| ✓ | EC_2.7.1.1 | EC 2.7.1.1 | 2.7.1.1 | Vmax, Km, Ki | REAC_0 |

**Problems:**
- ❌ ID showed "EC_2.7.1.1" (not transition ID)
- ❌ Name duplicated EC number
- ❌ Parameters showed types as text
- ❌ Organism showed internal SBML reaction ID

### After (New Table):
| ☑ | ID | Reaction | EC | Vmax | Km | Kcat | Ki | Organism |
|---|---|-------|---|------|----|----|---|---|
| ✓ | T1 | R00299 | 2.7.1.1 | 9.31e-07 M/s | 0.0006 M, 4.7e-05 M | 2.89e+05 /s | 2.2e-05 M | Homo sapiens |
| ✓ | T1 | R01326 | 2.7.1.1 | 5.53e-05 M/s | 7e-05 M | - | - | Homo sapiens |

**Improvements:**
- ✅ ID shows transition model ID (T1, T2, T3)
- ✅ Reaction shows KEGG R-ID (R00299, R01326)
- ✅ Parameter values displayed in separate columns
- ✅ Organism shows actual name (Homo sapiens)
- ✅ Multiple reactions per EC number visible
- ✅ Easy to compare parameters across reactions

## Data Flow

```
User Query (EC + Organism)
    ↓
SABIO-RK API
    ↓
SBML XML (Level 3)
    ↓
Parser extracts:
  - KEGG Reaction IDs from RDF annotations
  - Parameters from <localParameter> elements
  - Query organism preserved
    ↓
Group by reaction_id
    ↓
Display table with:
  - One row per unique KEGG reaction
  - Parameters as separate columns
  - Organism from query
```

## Testing

### Test Results (`test_sabio_table_refactor.py`):

```
Query: EC 2.7.1.1 + Homo sapiens
Results: 292 parameters from 149 SABIO-RK entries

✅ Parameters extracted: 292
✅ KEGG Reaction IDs found: 276 (94.5% coverage)
✅ Query organism preserved: "Homo sapiens"
✅ Table grouping works correctly

Sample Grouped Data:
Reaction     Vmax                  Km                   Kcat                 Ki                  
R00299       9.31e-07 M/s, 0...   0.0006 M, 4.7e-05 M  2.89e+05 /s, ...     2.2e-05 M, 1.5e-05 M
R01326       5.53e-05 M/s, ...    7e-05 M, 7e-05 M     -                    -                   
R01961       0.00128 M/s, ...     0.0005 M, 0.0005 M   -                    -                   
```

## User Workflow

1. **Context Menu**: Right-click transition → "Enrich with SABIO-RK"
2. **Query**: EC number + organism pre-filled
3. **Search**: API returns kinetic data
4. **Results Table**: 
   - Checkbox to select reactions
   - **ID**: T1, T2, T3 (transition in model)
   - **Reaction**: R00299, R01326 (KEGG reaction code)
   - **EC**: 2.7.1.1 (enzyme classification)
   - **Vmax**: Maximum velocity values
   - **Km**: Michaelis constants
   - **Kcat**: Turnover numbers
   - **Ki**: Inhibition constants
   - **Organism**: Homo sapiens
5. **Apply**: Select parameters → Apply to transition

## Edge Cases Handled

1. **Missing KEGG Reaction ID**: Shows "N/A" (some SABIO-RK entries lack KEGG mapping)
2. **Multiple Parameters**: Shows first 2 values, e.g., "0.0006 M, 4.7e-05 M"
3. **No Parameters of Type**: Shows "-" for empty columns
4. **Long Values**: Truncated to 30 chars with "..."
5. **Unknown Organism**: Falls back to query organism, then "Unknown"
6. **Manual Query**: Uses "EC_{ec_number}" as transition ID fallback

## Files Modified

1. **`src/shypn/data/sabio_rk_client.py`**:
   - Lines 292-365: RDF annotation parsing, organism extraction
   - Lines 369-387: Taxonomy ID mapping
   - Lines 114-118, 349-351: Query organism tracking

2. **`src/shypn/ui/panels/pathway_operations/sabio_rk_category.py`**:
   - Lines 270-310: New table structure (9 columns)
   - Lines 557-623: Refactored data grouping and population

3. **Test files**:
   - `test_sabio_table_refactor.py`: Validates new structure

## Performance Notes

- **Grouping**: Parameters grouped by KEGG reaction ID (O(n) operation)
- **Display**: Up to 2 values per parameter type shown
- **Memory**: One row per unique reaction (typically 1-5 reactions per transition)
- **Rendering**: GTK TreeView handles large datasets efficiently

## Future Enhancements

1. **Expandable Rows**: Click reaction to see all parameter values
2. **Unit Conversion**: Normalize units (e.g., M ↔ mM)
3. **Parameter Filtering**: Show/hide specific parameter types
4. **Export**: Save table to CSV for external analysis
5. **Sorting**: Click column headers to sort by parameter values

## Conclusion

✅ **All requested changes implemented**  
✅ **Table structure improved for usability**  
✅ **KEGG reaction IDs properly extracted**  
✅ **Organism information correctly displayed**  
✅ **Parameters organized as separate columns**

The refactored table provides a much clearer view of SABIO-RK data, making it easy to compare kinetic parameters across different reactions for the same enzyme.
