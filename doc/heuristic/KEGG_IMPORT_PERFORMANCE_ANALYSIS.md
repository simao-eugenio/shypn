# KEGG Import Performance Analysis

**Date**: October 19, 2025  
**Status**: Current Implementation Review  
**Question**: Is there performance optimization in KEGG import (batch fetching, global fetch + local map)?

---

## Current Implementation

### Architecture Overview

```
KEGG Import Pipeline:
1. Fetch KGML from KEGG API (1 request per pathway)
2. Parse reactions from KGML
3. For EACH reaction:
   ├─> Create transition(s)
   └─> Fetch EC numbers (1 API request per reaction) ← BOTTLENECK
```

### Performance Characteristics

**Current Approach**: **Sequential per-reaction fetching**

```python
# src/shypn/importer/kegg/reaction_mapper.py (lines 94-103)

for reaction in pathway.reactions:
    # Create transition
    transition = self._create_transition(reaction, x, y, name)
    
    # Fetch EC numbers (1 API call per reaction)
    fetcher = get_default_fetcher()
    ec_numbers = fetcher.fetch_ec_numbers(reaction.name)  # ← API CALL
    
    if ec_numbers:
        transition.metadata['ec_numbers'] = ec_numbers
```

### What Optimizations Exist?

#### 1. ✅ In-Memory Cache (Session-Level)

**File**: `src/shypn/data/kegg_ec_fetcher.py`

**How It Works**:
```python
class KEGGECFetcher:
    def __init__(self):
        self.cache: Dict[str, List[str]] = {}  # reaction_id → EC numbers
    
    def fetch_ec_numbers(self, reaction_id: str) -> List[str]:
        # Check cache first
        if reaction_id in self.cache:
            return self.cache[reaction_id]  # ← NO API CALL
        
        # Fetch from API
        ec_numbers = self._fetch_from_kegg_api(reaction_id)
        
        # Cache result
        self.cache[reaction_id] = ec_numbers
        return ec_numbers
```

**Benefit**: 
- If you import the same pathway twice (e.g., testing), second import is fast
- If two pathways share reactions (common in metabolism), no duplicate fetches

**Limitation**:
- Cache cleared when application closes
- No persistent cache (file/database)

#### 2. ✅ Singleton Fetcher (Shared Cache)

**File**: `src/shypn/data/kegg_ec_fetcher.py` (lines 245-256)

```python
# Global singleton
_default_fetcher: Optional[KEGGECFetcher] = None

def get_default_fetcher() -> KEGGECFetcher:
    """Get shared KEGGECFetcher instance with shared cache."""
    global _default_fetcher
    if _default_fetcher is None:
        _default_fetcher = KEGGECFetcher()
    return _default_fetcher
```

**Benefit**:
- All imports use same fetcher instance
- Cache persists across multiple pathway imports in same session
- Glycolysis and TCA cycle share many reactions → cache helps

---

## Performance Metrics

### Glycolysis Import (hsa00010)

**Reactions**: ~29 reactions  
**API Calls Without Cache**: 29 requests  
**API Calls With Cache (2nd import)**: 0 requests  

**Estimated Time**:
```
First import:
  - KGML fetch: 200ms
  - EC fetching: 29 reactions × 100ms = 2,900ms (2.9s)
  - Total: ~3.1s

Second import (cached):
  - KGML fetch: 200ms
  - EC fetching: 0ms (cache hit)
  - Total: ~0.2s
```

### Cache Hit Rates (Typical)

| Scenario | Cache Hit Rate | Performance Gain |
|----------|---------------|------------------|
| Re-import same pathway | ~100% | 15x faster |
| Import related pathways (TCA + Glycolysis) | ~30-40% | 1.5x faster |
| Fresh session | 0% | No benefit |

---

## What's Missing? (Optimization Opportunities)

### ❌ 1. No Batch API Calls

**Current**:
```python
# 29 reactions = 29 API calls
for reaction in reactions:
    ec = fetch_ec_numbers(reaction.name)  # Individual call
```

**Could Be**:
```python
# 29 reactions = 1 API call
reaction_ids = [r.name for r in reactions]
ec_map = fetch_ec_numbers_batch(reaction_ids)  # Batch call
```

**Problem**: KEGG REST API **doesn't support batch queries**

KEGG API only supports:
```
GET /get/R00710     ✅ Supported
GET /get/R00710+R00299+R01015   ❌ NOT supported
```

**Alternative**: Other databases support batching:
- UniProt API: Supports batch queries (up to 100 IDs)
- BRENDA API: Supports batch queries
- But KEGG is the authoritative source for pathway data

### ❌ 2. No Persistent Cache (File/Database)

**Current**: Cache only lives in memory during application session

**Could Add**:
```python
# Cache to SQLite or JSON file
cache_file = "~/.shypn/kegg_ec_cache.json"

{
  "R00710": ["2.7.1.1"],
  "R00299": ["2.7.1.1", "2.7.1.2"],
  "timestamp": "2025-10-19T03:00:00Z",
  "ttl_days": 30  # EC numbers rarely change
}
```

**Benefits**:
- Cache survives application restart
- First import after restart would be fast
- EC numbers are stable (don't change often)

**Complexity**: Medium (100-150 lines of code)

### ❌ 3. No Parallel Fetching

**Current**: Sequential fetching (blocking)

```python
for reaction in reactions:  # Sequential
    ec = fetch_ec_numbers(reaction.name)  # Blocks
```

**Could Be** (with threading):
```python
import concurrent.futures

with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
    # Submit all fetches in parallel
    futures = {
        executor.submit(fetch_ec_numbers, r.name): r 
        for r in reactions
    }
    
    # Collect results
    for future in concurrent.futures.as_completed(futures):
        reaction = futures[future]
        ec_numbers = future.result()
```

**Benefits**:
- 5-10x faster for pathways with many reactions
- Network latency is parallelized
- CPU doesn't wait for each API call to complete

**Complexity**: Low-Medium (50-80 lines of code)

**Risk**: 
- KEGG might rate-limit parallel requests
- Need to respect fair use policy

### ❌ 4. No Pre-fetching Strategy

**Current**: Fetch when needed (lazy loading)

**Could Add** (global fetch + local map):
```python
# Strategy A: Pre-fetch common reactions
COMMON_REACTIONS = ["R00710", "R00299", ...]  # Top 100 glycolysis/TCA
kegg_fetcher.prefetch(COMMON_REACTIONS)

# Strategy B: Pre-fetch entire pathway's reactions at start
def convert_pathway(pathway):
    # 1. Extract all reaction IDs
    reaction_ids = [r.name for r in pathway.reactions]
    
    # 2. Pre-fetch in parallel
    prefetch_ec_numbers_parallel(reaction_ids)
    
    # 3. Create transitions (all cache hits now!)
    for reaction in pathway.reactions:
        ec = fetcher.fetch_ec_numbers(reaction.name)  # Cache hit!
```

**Benefits**:
- UI shows progress: "Pre-fetching enzyme data... 15/29"
- All subsequent operations are instant (cache hits)
- Better user experience (clear progress indication)

**Complexity**: Medium (100-150 lines)

---

## Recommended Optimizations

### Priority 1: Parallel Fetching (Quick Win) 🎯

**Effort**: 2-3 hours  
**Benefit**: 5-10x faster imports  
**Risk**: Low (just need rate limiting)

```python
# src/shypn/data/kegg_ec_fetcher.py

def fetch_ec_numbers_parallel(reaction_ids: List[str], 
                              max_workers: int = 5) -> Dict[str, List[str]]:
    """
    Fetch EC numbers for multiple reactions in parallel.
    
    Args:
        reaction_ids: List of KEGG reaction IDs
        max_workers: Max parallel requests (default: 5 to be polite)
        
    Returns:
        Dict mapping reaction_id → EC numbers
    """
    import concurrent.futures
    
    fetcher = get_default_fetcher()
    results = {}
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all fetches
        future_to_reaction = {
            executor.submit(fetcher.fetch_ec_numbers, rid): rid 
            for rid in reaction_ids
        }
        
        # Collect results
        for future in concurrent.futures.as_completed(future_to_reaction):
            reaction_id = future_to_reaction[future]
            try:
                results[reaction_id] = future.result()
            except Exception as e:
                logger.warning(f"Failed to fetch EC for {reaction_id}: {e}")
                results[reaction_id] = []
    
    return results
```

**Usage**:
```python
# src/shypn/importer/kegg/reaction_mapper.py

def create_transitions(self, pathway):
    # Pre-fetch all EC numbers in parallel
    reaction_ids = [r.name for r in pathway.reactions]
    ec_map = fetch_ec_numbers_parallel(reaction_ids)
    
    # Create transitions (all cache hits now!)
    for reaction in pathway.reactions:
        transition = self._create_transition(reaction)
        transition.metadata['ec_numbers'] = ec_map.get(reaction.name, [])
```

### Priority 2: Persistent Cache (Medium Win) 💾

**Effort**: 3-4 hours  
**Benefit**: Fast imports even after restart  
**Risk**: Low (just JSON file management)

```python
# src/shypn/data/kegg_ec_cache.py

class PersistentECCache:
    """Persistent cache for KEGG EC numbers."""
    
    def __init__(self, cache_file: Path = Path("~/.shypn/kegg_ec_cache.json")):
        self.cache_file = cache_file.expanduser()
        self.cache = self._load_cache()
    
    def get(self, reaction_id: str) -> Optional[List[str]]:
        """Get EC numbers from cache."""
        entry = self.cache.get(reaction_id)
        if entry and not self._is_expired(entry):
            return entry['ec_numbers']
        return None
    
    def set(self, reaction_id: str, ec_numbers: List[str]):
        """Store EC numbers in cache."""
        self.cache[reaction_id] = {
            'ec_numbers': ec_numbers,
            'timestamp': datetime.now().isoformat(),
        }
        self._save_cache()
    
    def _is_expired(self, entry: dict, ttl_days: int = 90) -> bool:
        """Check if cache entry is expired (default: 90 days)."""
        timestamp = datetime.fromisoformat(entry['timestamp'])
        return (datetime.now() - timestamp).days > ttl_days
```

### Priority 3: Pre-fetch with Progress (Best UX) ✨

**Effort**: 4-5 hours  
**Benefit**: Better user experience, clear progress indication  
**Risk**: Low

```python
# src/shypn/importer/kegg/pathway_converter.py

def convert(self, pathway: KEGGPathway, options: ConversionOptions) -> DocumentModel:
    """Convert with progress indication."""
    
    if options.enhance_kinetics:
        # Pre-fetch EC numbers with progress
        reaction_ids = [r.name for r in pathway.reactions]
        
        self._emit_progress("Fetching enzyme data...", 0, len(reaction_ids))
        
        ec_map = fetch_ec_numbers_parallel(
            reaction_ids,
            progress_callback=lambda i, total: 
                self._emit_progress(f"Fetching enzyme data... {i}/{total}", i, total)
        )
    
    # Rest of conversion (all EC fetches are cache hits now)
    ...
```

**UI shows**:
```
Importing KEGG pathway hsa00010...
├─ Parsing KGML... ✓
├─ Fetching enzyme data... 15/29 (52%)  ← NEW!
├─ Creating transitions... ✓
└─ Building Petri net... ✓
```

---

## Performance Comparison

| Scenario | Current | With Parallel | With Cache | With Both |
|----------|---------|---------------|------------|-----------|
| First import (29 reactions) | 3.1s | **0.8s** | 3.1s | **0.8s** |
| Second import (same session) | 0.2s | 0.2s | 0.2s | 0.2s |
| Second import (new session) | 3.1s | **0.8s** | **0.2s** | **0.2s** |
| Import large pathway (100 reactions) | 10.2s | **2.5s** | 10.2s | **2.5s** |

**Legend**:
- **Bold** = Significant improvement
- Italic = Marginal improvement

---

## Current Status Summary

### ✅ What We Have

1. **In-memory cache** (session-level)
   - Prevents duplicate API calls in same session
   - Shared across all imports via singleton

2. **Reasonable timeout** (5 seconds per request)
   - Prevents hanging on slow connections

3. **Error handling** (graceful degradation)
   - If EC fetch fails, import continues without EC numbers

### ❌ What We Don't Have

1. **Batch API calls** (KEGG doesn't support it)
2. **Parallel fetching** (sequential = slow)
3. **Persistent cache** (cache lost on restart)
4. **Progress indication** (user sees nothing during EC fetching)
5. **Pre-fetching** (lazy loading = wait at each reaction)

---

## Conclusion

**Answer to Original Question**: 

> **NO, there is currently NO batch fetching or global fetch + local map optimization.**

The current implementation fetches EC numbers **sequentially, one reaction at a time**. 

**However**:
- ✅ There IS in-memory caching (prevents duplicate fetches in same session)
- ✅ Cache IS shared across imports (singleton pattern)
- ❌ But NO parallel fetching (sequential = slow)
- ❌ But NO persistent cache (restart = all fetches again)
- ❌ But NO pre-fetching (fetch-as-you-go)

**Biggest Performance Win**: Add parallel fetching (5-10x speedup for 2-3 hours work)

---

## Next Steps

If you want to implement performance improvements:

1. **Quick Win** (2-3 hours): Add parallel fetching
2. **Medium Win** (3-4 hours): Add persistent cache
3. **Best UX** (4-5 hours): Add pre-fetching with progress bar

**Estimated Total**: 9-12 hours for all three optimizations

**Impact**: 
- First import: 3.1s → 0.8s (4x faster)
- Second import (new session): 3.1s → 0.2s (15x faster)
- Large pathway: 10s → 2.5s (4x faster)

---

**Status**: Current implementation is **functional but not optimized**  
**Recommendation**: Add parallel fetching as Priority 1 quick win  
**Date**: October 19, 2025
