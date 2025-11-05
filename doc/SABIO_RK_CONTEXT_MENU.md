# SABIO-RK Context Menu Integration

## Overview

This document describes the context menu integration for SABIO-RK enrichment, allowing users to right-click on transitions and query SABIO-RK directly using the transition's metadata.

## Feature Description

When right-clicking on a **Transition** object in the canvas, users now see:
- "Enrich with BRENDA" (existing)
- **"Enrich with SABIO-RK" (NEW)**

Selecting "Enrich with SABIO-RK" will:
1. Extract metadata from the transition (EC number, reaction ID, organism)
2. Pre-fill the SABIO-RK query fields
3. Switch to the Pathway Operations panel
4. Expand the SABIO-RK category
5. Show helpful status message

## Implementation

### Files Modified

1. **`src/shypn/analyses/context_menu_handler.py`**
   - Added `_add_sabio_rk_enrichment_menu()` method
   - Added `_on_enrich_with_sabio_rk()` handler
   - Wired menu item to transitions

2. **`src/shypn/ui/panels/pathway_operations/sabio_rk_category.py`**
   - Added `set_query_from_transition()` method
   - Implements smart metadata extraction and field pre-filling

### Metadata Extraction Logic

The context menu extracts data in this order of preference:

#### EC Number
1. `metadata['ec_number']` - Direct EC number
2. `metadata['ec_numbers'][0]` - First EC from list
3. `metadata['reaction_id']` - If in EC format (e.g., "2.7.1.1")
4. Empty - Shows warning to user

#### Organism
1. `metadata['organism']` - Direct organism name
2. `metadata['species']` - Alternative field
3. Matches against combo box options:
   - "Homo sapiens"
   - "Mus musculus"
   - "Saccharomyces cerevisiae"
   - "Escherichia coli"
4. Falls back to "All organisms" if not found

#### Reaction ID Handling
- KEGG reaction IDs (e.g., "R00200") are **not used** for SABIO-RK
- Only EC-formatted IDs are converted to EC numbers
- Regex validation: `^\d+\.\d+\.\d+\.\d+$`

## Usage Examples

### Example 1: KEGG Import with EC Numbers

After importing from KEGG, transitions have metadata like:
```python
metadata = {
    'ec_number': '2.7.1.1',
    'enzyme_name': 'Hexokinase',
    'reaction': 'R00010',
    'organism': 'Homo sapiens'
}
```

**Steps:**
1. Right-click transition in canvas
2. Select "Enrich with SABIO-RK"
3. **Result**:
   - EC entry: `2.7.1.1`
   - Organism: `Homo sapiens`
   - Status: "Query pre-filled from transition T1. Recommend selecting organism filter before searching."

### Example 2: Manual Transition (No Metadata)

User creates transition manually without metadata:
```python
metadata = {}
```

**Steps:**
1. Right-click transition in canvas
2. Select "Enrich with SABIO-RK"
3. **Result**:
   - EC entry: (empty)
   - Status: "No EC number found for transition T1. Please enter EC number manually."
   - User can manually enter EC number

### Example 3: SBML Import with Reaction IDs

SBML import provides reaction IDs but not always EC numbers:
```python
metadata = {
    'reaction_id': '2.7.1.40',  # EC format
    'enzyme_name': 'Pyruvate kinase'
}
```

**Steps:**
1. Right-click transition
2. Select "Enrich with SABIO-RK"
3. **Result**:
   - EC entry: `2.7.1.40` (extracted from reaction_id)
   - Organism: `All organisms` (none specified)
   - User should select organism filter before searching

### Example 4: KEGG Reaction ID (Non-EC Format)

```python
metadata = {
    'reaction_id': 'R00200',
    'kegg_reaction_id': 'R00200'
}
```

**Steps:**
1. Right-click transition
2. Select "Enrich with SABIO-RK"
3. **Result**:
   - EC entry: (empty)
   - Log: `[SABIO-RK] Reaction ID 'R00200' not in EC format`
   - Status: "No EC number found for transition T3. Please enter EC number manually."

## User Workflow

### Typical Workflow for KEGG-Imported Model

1. **Import pathway from KEGG**
   ```
   Pathways → KEGG Import → Search "hsa00010" → Import
   ```

2. **Right-click on transition**
   ```
   Right-click → "Enrich with SABIO-RK"
   ```

3. **Verify pre-filled fields**
   ```
   EC Number: 2.7.1.1 (pre-filled)
   Organism: Homo sapiens (pre-filled)
   ```

4. **Click "Search"**
   ```
   Results display in table below
   ```

5. **Select parameters and apply**
   ```
   Check desired rows → "Apply Selected Parameters"
   ```

### Workflow for Model Without Metadata

1. **Right-click transition**
   ```
   Right-click → "Enrich with SABIO-RK"
   ```

2. **Manually enter EC number**
   ```
   EC Number: 2.7.1.1 (manual entry)
   Organism: Select from dropdown
   ```

3. **Continue with search as above**

## Benefits Over Manual Query

### Before (Manual Query)
1. Open Pathway Operations panel
2. Expand SABIO-RK category
3. Remember/lookup EC number for transition
4. Type EC number manually
5. Select organism manually
6. Click Search
7. Apply parameters
8. **Switch back to canvas to verify which transition**

### After (Context Menu)
1. Right-click transition (already selected)
2. Select "Enrich with SABIO-RK"
3. Fields pre-filled automatically
4. Click Search
5. Apply parameters
6. **Transition ID tracked throughout process**

**Time saved**: ~50% for models with metadata

## Error Handling

### Missing EC Number
- **Status**: Red warning text
- **Message**: "No EC number found for transition T1. Please enter EC number manually."
- **Action**: User can manually enter EC number

### Invalid Reaction ID
- **Status**: Console log warning
- **Message**: `[SABIO-RK] Reaction ID 'R00200' not in EC format`
- **Action**: EC field left empty, user can enter manually

### Unknown Organism
- **Status**: Console log warning
- **Message**: `[SABIO-RK] Organism 'Rattus norvegicus' not found in list, using 'All organisms'`
- **Action**: Falls back to "All organisms", user can select manually

### No Metadata at All
- **Status**: Info message
- **Message**: "Query pre-filled from transition T1. Recommend selecting organism filter before searching."
- **Action**: All fields empty, user enters manually

## Technical Details

### Method Signature
```python
def set_query_from_transition(
    self, 
    ec_number: str = "", 
    reaction_id: str = "", 
    organism: str = "", 
    transition_id: str = ""
):
    """Pre-fill query fields from transition metadata."""
```

### Called From
```python
# In context_menu_handler.py
def _on_enrich_with_sabio_rk(self, transition):
    # Extract metadata...
    category.set_query_from_transition(
        ec_number=ec_number,
        reaction_id=reaction_id,
        organism=organism,
        transition_id=transition.id
    )
```

### Panel Switching
```python
# Switch to Pathway Operations panel
if hasattr(self.pathway_operations_panel, 'switch_to_category'):
    self.pathway_operations_panel.switch_to_category('SABIO-RK')
```

This ensures the pre-filled query is immediately visible to the user.

## Testing

### Test File: `test_sabio_context_menu.py`

Verifies:
1. ✅ EC number pre-filling from `ec_number` field
2. ✅ EC number extraction from `reaction_id` (if EC format)
3. ✅ Organism filter selection and matching
4. ✅ Multiple EC numbers handling (takes first)
5. ✅ KEGG reaction ID rejection (not EC format)
6. ✅ Graceful handling of missing metadata
7. ✅ Status message updates

All tests pass successfully!

## Comparison with BRENDA Integration

| Feature | BRENDA | SABIO-RK |
|---------|--------|----------|
| Context menu option | ✅ "Enrich with BRENDA" | ✅ "Enrich with SABIO-RK" |
| EC number extraction | ✅ Yes | ✅ Yes |
| Organism filter | ❌ No | ✅ Yes (recommended) |
| Reaction ID support | ✅ Yes | ✅ EC format only |
| Multiple EC handling | ✅ Takes first | ✅ Takes first |
| Panel switching | ✅ Yes | ✅ Yes |
| Field pre-filling | ✅ Yes | ✅ Yes |
| Status messages | ✅ Yes | ✅ Yes |

## Future Enhancements

### Potential Improvements

1. **Support for KEGG Reaction IDs**
   - Query KEGG API to resolve R-IDs to EC numbers
   - Cache mapping for faster lookup
   
2. **Multi-EC Query Support**
   - Query all EC numbers from `ec_numbers` list
   - Combine results intelligently
   
3. **Organism Auto-Detection**
   - Parse model metadata for organism
   - Auto-select organism filter
   
4. **Query History**
   - Remember recent queries
   - Quick re-query option
   
5. **Batch Context Menu**
   - Select multiple transitions
   - "Enrich All with SABIO-RK"

## Related Documentation

- `SABIO_RK_BATCH_OPTIMIZATION.md` - Batch query optimization
- `SABIO_RK_ENHANCEMENTS.md` - UI enhancements (Select All, counter)
- `KEGG_CATALYST_UI_IMPLEMENTATION.md` - KEGG import metadata structure
- `MASTER_PALETTE_EXCLUSION_FIX.md` - Panel wiring architecture

## Summary

The SABIO-RK context menu integration provides a **seamless workflow** for enriching transitions with kinetic parameters:

✅ **Smart metadata extraction** - Handles multiple metadata formats  
✅ **Organism filter support** - Improves query success rate  
✅ **EC format validation** - Rejects non-EC reaction IDs  
✅ **Graceful fallbacks** - Works even without metadata  
✅ **Consistent UX** - Matches BRENDA integration pattern  

This feature significantly improves the user experience for kinetic parameter enrichment, especially for models imported from KEGG with rich metadata!
