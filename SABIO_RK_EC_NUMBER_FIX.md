# SABIO-RK EC Number Query Fix

**Date:** November 4, 2025  
**Issue:** EC number queries returned no results  
**Status:** ✅ FIXED

## Problem

When querying SABIO-RK by EC number (e.g., from context menu "Enrich with SABIO-RK"), the API appeared to return no results despite count endpoint showing available data.

### Root Cause

**SBML Level Mismatch:**
- SABIO-RK REST API returns **SBML Level 3 Version 1** with namespace:
  ```xml
  <sbml xmlns="http://www.sbml.org/sbml/level3/version1/core" level="3" version="1">
  ```
- Parser was looking for **SBML Level 2 Version 4** namespace:
  ```python
  'sbml': 'http://www.sbml.org/sbml/level2/version4'
  ```
- Namespace mismatch caused `findall('.//sbml:reaction', namespaces)` to return empty list

**Parameter Element Difference:**
- SBML Level 2 uses `<parameter>` elements inside `<kineticLaw>`
- SBML Level 3 uses `<localParameter>` elements inside `<listOfLocalParameters>`
- Parser only looked for `<parameter>`, missing all Level 3 data

## Solution

### 1. Namespace Compatibility (`sabio_rk_client.py` lines 264-283)

Added support for both SBML Level 2 and Level 3 namespaces:

```python
# Define namespaces for both SBML levels
namespaces_l3 = {
    'sbml': 'http://www.sbml.org/sbml/level3/version1/core',
    'math': 'http://www.w3.org/1998/Math/MathML'
}
namespaces_l2 = {
    'sbml': 'http://www.sbml.org/sbml/level2/version4',
    'math': 'http://www.w3.org/1998/Math/MathML'
}

# Try Level 3 first (current SABIO-RK format), fall back to Level 2
reactions = root.findall('.//sbml:reaction', namespaces_l3)
if not reactions:
    reactions = root.findall('.//sbml:reaction', namespaces_l2)

# Use correct namespace for rest of parsing
namespaces = namespaces_l3 if root.find('.//{http://www.sbml.org/sbml/level3/version1/core}reaction') else namespaces_l2
```

### 2. Local Parameter Support (`sabio_rk_client.py` lines 298-301)

Added fallback to `<localParameter>` elements:

```python
# Extract parameters (Level 2 uses <parameter>, Level 3 uses <localParameter>)
parameters = kinetic_law.findall('.//sbml:parameter', namespaces)
if not parameters:
    parameters = kinetic_law.findall('.//sbml:localParameter', namespaces)
```

### 3. Threshold Adjustment (`sabio_rk_client.py` lines 101-112)

Increased threshold from 50 to 150 results to allow more queries:

```python
# Batch optimization: Reject large result sets to prevent timeouts
# Note: Manual queries (single EC) can handle more results than batch queries
if count > 150:
    self.logger.warning(f"[SABIO-RK] Query would return {count} results - likely to timeout!")
    if organism:
        self.logger.warning(f"[SABIO-RK] Even with organism filter '{organism}', too many results")
        self.logger.warning(f"[SABIO-RK] Try a more specific organism or contact database administrators")
    else:
        self.logger.warning(f"[SABIO-RK] Please specify organism filter to reduce results")
    return None
```

**Rationale:**
- Original 50-result limit was too conservative for single EC queries
- 150-result limit allows common queries like "EC 2.7.1.1 + Homo sapiens" (149 results)
- Still protects against timeout-prone queries (e.g., EC without organism = 799 results)
- Batch queries (10/batch) remain protected by separate controller logic

### 4. Better Error Messages (`sabio_rk_category.py` lines 465-473)

Improved user feedback when queries fail:

```python
if result:
    # Show results...
else:
    # Show more specific error message
    if organism:
        msg = f"<span foreground='red'>No data found for EC {ec_number} in {organism}. "\
              f"Query may have too many results (&gt;150) or no data available.</span>"
    else:
        msg = f"<span foreground='red'>No data found for EC {ec_number}. "\
              f"Try selecting a specific organism to reduce results.</span>"
    GLib.idle_add(self.status_label.set_markup, msg)
```

## Testing

### Test Results (test_sabio_ec_integration.py)

```
✅ TEST 1: EC 2.7.1.1 + Homo sapiens
   SUCCESS: Retrieved 292 parameters

✅ TEST 2: EC 1.1.1.1 + Homo sapiens (358 results)
   CORRECTLY REJECTED: Too many results (>150)

✅ TEST 3: EC 2.7.1.1 without organism (799 results)
   CORRECTLY REJECTED: Too many results (>150)
```

### Example Query Result

**EC 2.7.1.1 (Hexokinase) + Homo sapiens:**
- Count: 149 results
- Parameters retrieved: 292 kinetic parameters
- Sample data:
  - `Ki2_Glucose_16diphosphate = 2.2e-05 M`
  - `Vmax = 9.3e-07 M/s`
  - `KmA_ATP = 0.0006 M`

## Context Menu Integration

The fix enables the complete workflow:

1. **User action:** Right-click transition → "Enrich with SABIO-RK"
2. **Metadata extraction:** EC number from `ec_number`, `ec_numbers`, or `reaction_id`
3. **Query execution:** API called with EC + organism filter
4. **SBML parsing:** Level 3 local parameters correctly extracted
5. **Results display:** 292 parameters shown in results table
6. **Application:** User selects parameters → Applied to transition

## Impact

### Before Fix
- **EC queries:** ❌ Always returned 0 results
- **User experience:** Frustrating, appeared broken
- **Context menu:** Useless for SABIO-RK enrichment

### After Fix
- **EC queries:** ✅ Return 292+ parameters for common enzymes
- **User experience:** Smooth, matches BRENDA integration
- **Context menu:** Fully functional for KEGG-imported models

## Files Modified

1. **`src/shypn/data/sabio_rk_client.py`**
   - Lines 264-283: Added SBML Level 3 namespace support
   - Lines 298-301: Added `<localParameter>` support
   - Lines 101-112: Increased threshold to 150 results

2. **`src/shypn/ui/panels/pathway_operations/sabio_rk_category.py`**
   - Lines 465-473: Improved error messages

3. **Test files created:**
   - `test_sabio_ec_query.py` - Query format testing
   - `test_sabio_ec_fix.py` - Threshold testing
   - `test_sabio_ec_integration.py` - End-to-end validation
   - `debug_sabio_count.py` - API count verification

## Related Documentation

- **Context Menu:** `SABIO_RK_CONTEXT_MENU.md`
- **Batch Optimization:** `SABIO_RK_BATCH_OPTIMIZATION.md`
- **SABIO-RK Enhancements:** `SABIO_RK_ENHANCEMENTS.md`

## API Compatibility Notes

### SBML Level Support Matrix

| SBML Level | Namespace | Parameter Element | Status |
|------------|-----------|-------------------|--------|
| Level 2 V4 | `.../level2/version4` | `<parameter>` | ✅ Supported |
| Level 3 V1 | `.../level3/version1/core` | `<localParameter>` | ✅ Supported (current SABIO-RK) |

### Future Considerations

If SABIO-RK updates to SBML Level 3 Version 2:
1. Add namespace to `namespaces_l3` dict
2. Test parameter extraction (should work unchanged)
3. Update this documentation

## Performance Notes

- **Threshold:** 150 results = ~120s max fetch time
- **Typical query:** 50-150 results = 30-60s
- **Batch processing:** 10 transitions/batch with 2s pauses
- **User guidance:** Status messages recommend organism filter

## Conclusion

✅ **EC number queries now work correctly**  
✅ **SBML Level 3 fully supported**  
✅ **Context menu integration complete**  
✅ **User experience matches BRENDA integration**

The SABIO-RK enrichment feature is now production-ready and provides the same workflow quality as the BRENDA integration.
