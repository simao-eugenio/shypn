# Knowledge Base Quick Reference

## Overview
The Knowledge Base (KB) system provides caching and provenance tracking for parameter enrichment from SABIO-RK and BRENDA databases.

---

## Components

### Cache Managers

**SABIO-RK Cache**:
```python
from shypn.crossfetch.cache.sabio_rk_cache_manager import SabioRKCacheManager
from shypn.crossfetch.database.heuristic_db import HeuristicDatabase

db = HeuristicDatabase()
cache = SabioRKCacheManager(db)

# Query with automatic caching
result = cache.query_with_cache(
    query_key="sabio_rk|2.7.1.1|Homo sapiens",
    api_function=lambda: fetch_from_sabio_rk(ec, organism)
)

# Get statistics
stats = cache.get_statistics()  # hits, misses, hit_rate
summary = cache.get_cache_summary()  # total_cached_queries, etc.

# Invalidate specific query
cache.invalidate_cache(query_key)
```

**BRENDA Cache**:
```python
from shypn.crossfetch.cache.brenda_cache_manager import BRENDACacheManager

cache = BRENDACacheManager(db)

# Build query key
key = cache.build_query_key(
    ec_number="2.7.1.1",
    parameter_type="Km",
    organism="Homo sapiens",
    substrate="glucose"
)

# Query with caching
result = cache.query_with_cache(key, api_function)
```

### Parameter Tracker

```python
from shypn.crossfetch.tracking.parameter_tracker import ParameterTracker

tracker = ParameterTracker(db)

# Track parameter application
record_id = tracker.track_application(
    transition_id="trans_001",
    parameters={'Km': 0.1, 'Vmax': 226.0},
    source='SABIO-RK',
    ec_number='2.7.1.1',
    organism='Homo sapiens',
    pathway_id='pathway_001',
    confidence_score=0.85  # Optional - auto-calculated if omitted
)

# Phase 2: Update user rating
tracker.update_rating(
    parameter_id=record_id,
    rating=1,  # -1 (poor), 0 (neutral), 1 (good)
    comment="Parameters match experimental data well"
)

# Phase 2: Get filtered history
history = tracker.get_filtered_history(
    source='SABIO-RK',           # Optional filter
    pathway_id='pathway_001',    # Optional filter
    rating=1,                    # Optional: filter by rating
    date_range=('2025-01-01', '2025-12-31'),  # Optional
    include_undone=False,        # Exclude undone applications
    limit=100
)

# Phase 2: Undo application
result = tracker.undo_application(parameter_id=record_id)
if result['success']:
    print(f"Reverted to: {result['previous_parameters']}")

# Get history
history = tracker.get_transition_history(transition_id="trans_001")
pathway_history = tracker.get_pathway_history(pathway_id="pathway_001")

# Get statistics
stats = tracker.get_source_statistics(source='SABIO-RK')
# Returns: total_applications, used_count, avg_confidence, avg_user_rating
```

---

## Database Tables

### `sabio_rk_cache`
Caches SABIO-RK API results.

**Columns**:
- `id`: Primary key
- `query_key`: Unique identifier (format: `sabio_rk|{ec}|{organism}`)
- `result_data`: JSON result from API
- `created_at`: First cache time
- `last_accessed`: Last retrieval time
- `access_count`: Number of cache hits

### `transition_parameters`
Tracks parameter applications.

**Key Columns**:
- `transition_id`: Transition identifier
- `parameters`: JSON dict of applied parameters
- `source`: 'SABIO-RK', 'BRENDA', or 'Heuristic'
- `ec_number`: EC number
- `organism`: Organism name
- `confidence_score`: Confidence (0.0-1.0)
- `user_rating`: User feedback (-1: poor, 0: neutral, 1: good)
- `usage_count`: Times this parameter used
- `notes`: User comments (Phase 2)
- `undone`: Boolean flag for undone applications (Phase 2)
- `undo_timestamp`: When application was undone (Phase 2)

### `brenda_raw_data`
Raw BRENDA measurements (used by cache).

### `brenda_statistics`
Pre-calculated BRENDA statistics (used by cache).

---

## Common Use Cases

### 1. Query with Caching
```python
# SABIO-RK
query_key = cache_manager.build_query_key(ec_number, organism)
result = cache_manager.query_with_cache(
    query_key,
    api_function=lambda: query_sabio_rk_api(ec_number, organism)
)

if result['cached']:
    logger.info(f"Cache hit for {query_key}")
else:
    logger.info(f"Cache miss, fetched from API")
```

### 2. Track Parameter Application
```python
# After applying parameters to a transition
tracker.track_application(
    transition_id=transition.id,
    parameters=applied_params,
    source='SABIO-RK',
    ec_number=transition.ec_number,
    organism=selected_organism,
    pathway_id=current_pathway.id,
    pathway_name=current_pathway.name,
    confidence_score=calculate_confidence(result)
)
```

### 3. View Enrichment History
```python
# Get all parameter applications for a transition
history = tracker.get_transition_history("trans_glycolysis_001")

for entry in history:
    print(f"Source: {entry['source']}")
    print(f"Parameters: {entry['parameters']}")
    print(f"Applied: {entry['applied_date']}")
    print(f"Confidence: {entry['confidence_score']}")
    if entry['user_rating']:
        print(f"User rating: {entry['user_rating']}")
```

### 4. Analyze Source Performance
```python
# Get statistics for each source
for source in ['SABIO-RK', 'BRENDA', 'Heuristic']:
    stats = tracker.get_source_statistics(source)
    print(f"\n{source}:")
    print(f"  Applications: {stats['total_applications']}")
    print(f"  Avg confidence: {stats['avg_confidence']:.2f}")
    if stats['avg_user_rating']:
        print(f"  Avg rating: {stats['avg_user_rating']:.2f}")
```

### 5. Cache Maintenance
```python
# Get cache statistics
stats = cache_manager.get_statistics()
print(f"Hit rate: {stats['hit_rate_percent']:.1f}%")
print(f"Total queries: {stats['total_queries']}")

# Get detailed summary
summary = cache_manager.get_cache_summary()
print(f"Cached queries: {summary['total_cached_queries']}")
print(f"Unique EC numbers: {summary['unique_ec_numbers']}")

# Invalidate old/incorrect entries
cache_manager.invalidate_cache(specific_query_key)
# or invalidate all:
cache_manager.invalidate_all()
```

### 6. Rate and Review Parameters (Phase 2)
```python
# After user reviews applied parameters
tracker.update_rating(
    parameter_id=123,
    rating=1,  # Good
    comment="Matches our experimental data perfectly"
)

# View rated parameters
good_params = tracker.get_filtered_history(rating=1)
poor_params = tracker.get_filtered_history(rating=-1)

# Undo bad parameter application
result = tracker.undo_application(parameter_id=456)
if result['success']:
    print(f"Undone! Previous params: {result['previous_parameters']}")
```

### 7. Browse Enrichment History (Phase 2)
```python
# UI: Open Pathway Operations panel → ENRICHMENT HISTORY category

# Programmatic access:
from shypn.ui.panels.pathway_operations.enrichment_history_category import EnrichmentHistoryCategory

category = EnrichmentHistoryCategory()
# Shows filterable history with:
# - Source filter (SABIO-RK, BRENDA, Heuristic)
# - Rating filter (Good, Neutral, Poor, Unrated)
# - Date range filter (Last 24h, 7d, 30d, All time)
# - TreeView with all enrichments
# - Detail panel with full metadata
# - Rate/Undo/Refresh buttons
```

---

## Performance Tips

1. **Cache Hit Rate**: Aim for >80% hit rate for optimal performance
   - Monitor with `get_statistics()`
   - 60-120s API call → <1s cache hit

2. **Query Key Consistency**: Always use same organism/EC format
   - Normalize organism names (e.g., "Homo sapiens" not "human")
   - Use canonical EC numbers (e.g., "2.7.1.1" not "EC:2.7.1.1")

3. **Batch Operations**: Use tracker's batch methods when available
   - More efficient than individual tracking calls

4. **Database Maintenance**: 
   - Monitor database size (`~/.shypn/heuristic_parameters.db`)
   - Periodically invalidate old cache entries
   - Expected growth: ~1-2 KB per query

---

## Testing

### Run Tests
```bash
# Cache managers
pytest tests/test_cache_managers.py -v

# Parameter tracker (includes Phase 2 features)
pytest tests/test_parameter_tracker.py -v

# Phase 2 integration tests
pytest tests/test_enrichment_history_integration.py -v

# All KB tests
pytest tests/test_cache_managers.py tests/test_parameter_tracker.py tests/test_enrichment_history_integration.py -v
```

### Integration Test
```bash
cd /home/simao/projetos/shypn
PYTHONPATH=/home/simao/projetos/shypn/src python -c "
from shypn.crossfetch.cache.sabio_rk_cache_manager import SabioRKCacheManager
from shypn.crossfetch.tracking.parameter_tracker import ParameterTracker
from shypn.crossfetch.database.heuristic_db import HeuristicDatabase

db = HeuristicDatabase()
cache = SabioRKCacheManager(db)
tracker = ParameterTracker(db)

print('✅ KB components initialized successfully')
"
```

---

## Troubleshooting

### Import Errors
```bash
# Ensure PYTHONPATH is set
export PYTHONPATH=/home/simao/projetos/shypn/src
# Or use from project root:
cd /home/simao/projetos/shypn
python -m shypn.crossfetch.cache.sabio_rk_cache_manager
```

### Database Location
```bash
# Check database exists
ls -lh ~/.shypn/heuristic_parameters.db

# View tables
sqlite3 ~/.shypn/heuristic_parameters.db ".tables"

# Check cache entries
sqlite3 ~/.shypn/heuristic_parameters.db "SELECT COUNT(*) FROM sabio_rk_cache;"
```

### Cache Not Working
1. Verify database initialized: `db = HeuristicDatabase()`
2. Check query key format: `cache.build_query_key(ec, organism)`
3. Review cache statistics: `cache.get_statistics()`
4. Check logs for errors

---

## Architecture

```
src/shypn/crossfetch/
├── cache/
│   ├── __init__.py
│   ├── base_cache_manager.py      # Abstract base
│   ├── sabio_rk_cache_manager.py  # SABIO-RK concrete
│   └── brenda_cache_manager.py    # BRENDA concrete
├── tracking/
│   ├── __init__.py
│   └── parameter_tracker.py       # Provenance tracking (Phase 1 & 2)
└── database/
    └── heuristic_db.py             # SQLite interface (schema v2)

src/shypn/ui/
├── dialogs/
│   └── parameter_rating_dialog.py # User rating dialog (Phase 2)
└── panels/pathway_operations/
    └── enrichment_history_category.py  # History viewer (Phase 2)

src/shypn/helpers/
├── sabio_rk_enrichment_controller.py  # SABIO-RK integration (Phase 2)
└── brenda_enrichment_controller.py    # BRENDA integration (Phase 2)

Inheritance:
  BaseCacheManager
  ├── SabioRKCacheManager
  └── BRENDACacheManager
  
  BasePathwayCategory
  ├── KEGGCategory
  ├── SBMLCategory
  ├── BRENDACategory
  ├── SabioRKCategory
  ├── HeuristicParametersCategory
  └── EnrichmentHistoryCategory (Phase 2)
```

---

## Phase 2 Features (Implemented)

### User Feedback System
- **Rating Dialog**: Thumbs up/down/neutral after parameter application
- **Confidence Scoring**: Dynamic confidence based on source, usage, and ratings
  - SABIO-RK baseline: 0.85
  - BRENDA baseline: 0.80
  - Heuristic baseline: 0.70
  - Usage boost: +1% per use (max +10%)
  - Rating influence: -15% (poor), 0% (neutral), +10% (good)

### Enrichment History Viewer
- **Location**: Pathway Operations panel → ENRICHMENT HISTORY category
- **Features**:
  - Filter by source, rating, date range
  - TreeView with all enrichments
  - Detail panel showing full metadata
  - Rate/Undo/Refresh buttons
  - Global view across all pathways

### Undo Functionality
- Mark applications as undone (preserves audit trail)
- Returns previous parameter values
- Confirmation dialog
- Automatic history refresh

### API Changes
- `track_application()`: Now auto-calculates confidence if not provided
- `update_rating()`: New method for user feedback
- `get_filtered_history()`: New method with multiple filters
- `undo_application()`: New method for reverting enrichments
- `_calculate_confidence()`: New smart scoring algorithm

### Database Schema v2
- Added `undone` column (Boolean)
- Added `undo_timestamp` column
- Updated `user_rating` constraint (-1/0/1 instead of 1-5)
- Automatic migration from v1 to v2

---

## Future Enhancements (Phase 3+)

- **Cache TTL**: Automatic invalidation of old entries
- **Analytics Dashboard**: Visualize usage patterns and performance
- **ML-based Confidence**: Learn from user ratings to improve scoring
- **Bulk Operations**: Batch undo, bulk rating updates
- **Export/Import**: Share enrichment history between users

---

## Support

- **Documentation**: `doc/KB/`
- **Tests**: `tests/test_cache_managers.py`, `tests/test_parameter_tracker.py`, `tests/test_enrichment_history_integration.py`
- **Examples**: See controller implementations in `src/shypn/helpers/`
- **Phase 2 Architecture**: `doc/KB/PHASE2_UI_ARCHITECTURE.md`
