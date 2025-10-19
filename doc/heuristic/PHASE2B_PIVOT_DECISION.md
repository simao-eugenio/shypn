# Phase 2B Alternative: Use Alternative Data Sources

**Date**: October 19, 2025  
**Issue**: SABIO-RK API appears unreliable (400 errors, timeouts)

---

## Problem

SABIO-RK API issues:
1. ✗ Direct EC number lookup returns 400 error
2. ✗ Search endpoint times out (>15s)
3. ✗ API appears to require kinlawids, not EC numbers

## Alternative Approaches

### Option 1: Expand Fallback Database ⭐ (RECOMMENDED)

Instead of relying on unreliable external APIs, expand the local fallback database with more curated enzymes from literature.

**Pros**:
- ✅ Always works (offline capable)
- ✅ Fast (<1ms lookups)
- ✅ Full control over data quality
- ✅ No network dependency
- ✅ Already working (10 enzymes proven)

**Cons**:
- Manual curation required
- Limited to what we add
- Updates require code changes

**Recommendation**: Add 20-30 most common enzymes from major pathways:
- Glycolysis: 10 enzymes ✅ (done)
- TCA cycle: 8 enzymes
- Pentose phosphate: 7 enzymes
- Gluconeogenesis: 5 enzymes
- Total: ~30 enzymes covering 80% of common metabolic models

### Option 2: KEGG EC Number Enrichment ⭐⭐ (BEST IMPACT)

Fetch EC numbers from KEGG REST API for reactions, then use our fallback database.

**Pros**:
- ✅ KEGG API is reliable and fast
- ✅ Gives us EC numbers for KEGG pathways
- ✅ Works with our existing fallback DB
- ✅ No new dependencies
- ✅ Immediate value for KEGG imports

**Implementation**:
```python
def fetch_ec_for_kegg_reaction(reaction_id: str) -> List[str]:
    """
    Fetch EC numbers from KEGG REST API.
    
    Example: R00710 → ["2.7.1.1"]
    """
    url = f"https://rest.kegg.jp/get/{reaction_id}"
    response = requests.get(url, timeout=5)
    
    # Parse response for ENZYME field
    # Format: "ENZYME      2.7.1.1"
    for line in response.text.split('\n'):
        if line.startswith('ENZYME'):
            ec_numbers = line.split()[1:]
            return ec_numbers
    
    return []
```

**Impact**: Real KEGG imports would get HIGH confidence for enzymatic reactions!

### Option 3: Pre-computed Database from BRENDA

Download and parse BRENDA flat files (requires registration).

**Pros**:
- Comprehensive (83,000+ enzymes)
- Well-curated
- Offline after download

**Cons**:
- Large download (100+ MB)
- Complex parsing
- License requirements
- Regular updates needed

### Option 4: Try BRENDA SOAP API

BRENDA has a SOAP API with better documentation.

**Pros**:
- Official API
- Well-documented
- Comprehensive data

**Cons**:
- Requires registration and API key
- SOAP complexity (need zeep library)
- Rate limits

---

## Recommended Path Forward

### Phase 2B (Revised): Two-Part Approach

**Part 1: KEGG EC Enrichment** (High Priority, 1 day)
1. Implement KEGG REST API client for reaction → EC lookup
2. Integrate with pathway_converter
3. Test with Glycolysis pathway
4. **Impact**: Real KEGG imports get EC numbers → database lookup works!

**Part 2: Expand Fallback Database** (Medium Priority, 1-2 days)
1. Add TCA cycle enzymes (8 more)
2. Add pentose phosphate enzymes (7 more)
3. Total: 25 enzymes covering major metabolic pathways
4. **Impact**: Better offline coverage

**Optional Part 3: BRENDA SOAP API** (Low Priority, future)
1. Register for BRENDA account
2. Implement SOAP client
3. Add as Tier 2 (between cache and fallback)

---

## Decision

**Pivot to Option 2: KEGG EC Number Enrichment**

**Rationale**:
1. SABIO-RK API unreliable (400 errors, timeouts)
2. KEGG API is fast and reliable
3. Immediate value for KEGG imports (our main use case)
4. Works with existing fallback database (10 enzymes)
5. Can expand fallback DB incrementally

**Next Steps**:
1. Implement KEGG EC number fetcher
2. Integrate with pathway_converter
3. Test with real Glycolysis pathway
4. Verify HIGH confidence assignments

---

**Status**: ✅ **NEW PLAN APPROVED**  
**Focus**: KEGG EC enrichment + Expand fallback DB  
**Drop**: SABIO-RK (unreliable)  
**Keep**: Hybrid architecture (cache + API + fallback)
