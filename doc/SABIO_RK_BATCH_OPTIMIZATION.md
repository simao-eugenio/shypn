# SABIO-RK Batch Query Optimization

## Problem
SABIO-RK REST API has severe performance limitations:
- No pagination support
- Queries returning >50 results typically timeout (30-120+ seconds)
- Even with organism filter, many EC numbers have 100+ entries

## Solution Implemented

### 1. Reduced Result Threshold
**File**: `src/shypn/data/sabio_rk_client.py`
- Reduced maximum results from 150 → 50
- Queries with >50 results are rejected with warning
- Increased timeout for queries with 20-50 results

### 2. Batch Processing with Delays
**File**: `src/shypn/helpers/sabio_rk_enrichment_controller.py`
- `query_all_transitions()` now processes in batches of 10
- 2-second pause between batches to avoid API overload
- Progress logging: "Querying transition 23/50..."
- Better error handling (continues on individual failures)

### 3. User Warnings & Confirmation
**File**: `src/shypn/ui/panels/pathway_operations/sabio_rk_category.py`
- Shows confirmation dialog for >30 transitions
- Explains: "Processing in batches of 10 with 2-second pauses"
- Updates status label: "Querying SABIO-RK: 23/50 transitions..."

## Usage Recommendations

### For Small Models (<10 transitions)
- Use "Query All Transitions" button freely
- Should complete in under 30 seconds

### For Medium Models (10-30 transitions)
- Use "Query All Transitions" with organism filter
- Processing time: ~1-2 minutes
- Batches of 10 with 2-second pauses

### For Large Models (>30 transitions)
- **RECOMMENDED**: Query manually by EC number + organism
- Alternative: Use "Query All" but expect 3-5 minutes
- Confirmation dialog will warn about time

### Optimal Approach
1. **Analyze your model first**: Check how many transitions have EC numbers
2. **Use organism filter**: Always specify (e.g., "Homo sapiens")
3. **Manual queries preferred**: For models with >50 transitions, query critical EC numbers individually
4. **Be patient**: Large models need time due to API limitations

## Performance Metrics

### Before Optimization
- 50 transitions × 30-60s timeout = FAIL (most queries timeout)
- No progress feedback
- No error recovery

### After Optimization
- 50 transitions ÷ 10 batch × 2s pause = ~10s overhead
- Each query: 5-15s with organism filter
- Total: ~5-10 minutes for 50 transitions
- Progressive: Works even if some queries fail
- User informed: Progress updates and warnings

## Technical Details

### Batch Size: 10
- Chosen to balance progress vs. API load
- Can be adjusted via `batch_size` parameter
- 10 queries × 10s avg = ~2 minutes per batch

### Pause Duration: 2 seconds
- Prevents API rate limiting
- Allows server to process previous requests
- Minimal impact on total time

### Timeout Strategy
```python
timeout = 60s (default)
if count < 20: timeout = 60s
if 20 ≤ count ≤ 50: timeout = min(count * 2, 120s)
if count > 50: REJECT with warning
```

## API Limitations Summary

✅ **What Works**:
- Status endpoint (instant)
- Count queries (5-10 seconds)
- Direct ID queries (instant)
- Small result sets (<20): 10-30 seconds
- Organism-filtered queries: Usually <50 results

❌ **What Doesn't Work**:
- Large result sets (>50): Timeout
- Queries without organism filter: Usually >100 results
- Compound-based queries: Too many results
- SOAP API: Discontinued (404)

## Alternative Approaches

### If SABIO-RK remains unusable:

1. **BRENDA** (recommended)
   - Request data access via https://www.brenda-enzymes.org/support.php
   - SOAP API works reliably
   - Comprehensive kinetics database

2. **Manual Entry**
   - Import from literature (PubMed)
   - Use pathway databases (MetaCyc, Reactome)
   - KEGG heuristics as fallback

3. **Direct ID Queries** (SABIO-RK only)
   - If you know specific SABIO-RK entry IDs
   - Direct queries work instantly
   - Requires pre-knowledge of IDs

## Future Improvements

1. **Caching**: Cache SABIO-RK results locally
2. **Offline Database**: Download SABIO-RK bulk data
3. **Alternative APIs**: UniProt, MetaCyc, Reactome
4. **Parallel Queries**: Multi-threaded (risky with current API)

## Date
November 4, 2025
