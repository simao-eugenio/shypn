# BRENDA Database Integration - Complete

**Status:** ✅ **FULLY IMPLEMENTED AND TESTED**  
**Date:** 2025-11-06  
**Feature:** Auto-save BRENDA query results to local SQLite database

---

## Overview

The BRENDA database integration provides automatic local storage of all BRENDA SOAP API query results in a SQLite database. This enables:

1. **Progressive Data Accumulation** - Build a local BRENDA cache over time
2. **Statistical Analysis** - Calculate mean, median, std_dev, confidence intervals
3. **Fast Offline Access** - Query local database instead of BRENDA API
4. **Heuristic Inference** - Train parameter estimation from accumulated data
5. **Quality Tracking** - Store quality scores alongside raw data

---

## Architecture

### Database Schema

#### New Tables Added to `heuristic_parameters.db`

**1. `brenda_raw_data` - Raw BRENDA Query Results**
```sql
CREATE TABLE brenda_raw_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ec_number TEXT NOT NULL,
    parameter_type TEXT NOT NULL,  -- 'Km', 'kcat', 'Ki'
    value REAL NOT NULL,
    unit TEXT,                     -- 'mM', '1/s', etc.
    substrate TEXT,
    organism TEXT,
    literature TEXT,               -- PubMed citations
    commentary TEXT,               -- Experimental conditions
    query_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    source_quality REAL,           -- 0.0-1.0 quality score
    UNIQUE(ec_number, parameter_type, value, organism, substrate, literature)
);

CREATE INDEX idx_brenda_ec ON brenda_raw_data(ec_number);
CREATE INDEX idx_brenda_organism ON brenda_raw_data(organism);
CREATE INDEX idx_brenda_quality ON brenda_raw_data(source_quality);
```

**2. `brenda_statistics` - Aggregated Statistics Cache**
```sql
CREATE TABLE brenda_statistics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ec_number TEXT NOT NULL,
    parameter_type TEXT NOT NULL,
    organism TEXT DEFAULT 'all',
    substrate TEXT DEFAULT 'all',
    count INTEGER,
    mean_value REAL,
    median_value REAL,
    std_dev REAL,
    min_value REAL,
    max_value REAL,
    confidence_interval_95_lower REAL,
    confidence_interval_95_upper REAL,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(ec_number, parameter_type, organism, substrate)
);

CREATE INDEX idx_brenda_stats ON brenda_statistics(ec_number, parameter_type);
```

### Key Features

1. **UNIQUE Constraint** - Prevents duplicate storage of identical results
2. **Quality Scoring** - Stores BRENDADataFilter quality scores (0.0-1.0)
3. **Statistical Aggregation** - Auto-calculates mean, median, std_dev, 95% CI
4. **Indexing** - Fast queries by EC number, organism, quality threshold
5. **Timestamp Tracking** - Records when data was queried/calculated

---

## Implementation

### 1. Database Methods (`heuristic_db.py`)

**New Methods Added:**

```python
# Bulk insert BRENDA results
def insert_brenda_raw_data(self, results: List[Dict]) -> int:
    """Insert BRENDA query results. Returns count of inserted records."""
    # Handles duplicates with INSERT OR IGNORE
    # Logs: "Inserted {count}/{total} BRENDA records"

# Query with filters
def query_brenda_data(self, 
                     ec_number: str = None,
                     parameter_type: str = None,
                     organism: str = None,
                     substrate: str = None,
                     min_quality: float = 0.0,
                     limit: int = None) -> List[Dict]:
    """Query BRENDA raw data with optional filters."""
    # Supports partial matching for organism/substrate (LIKE query)
    # Orders by quality DESC, date DESC

# Calculate and cache statistics
def calculate_brenda_statistics(self, 
                                ec_number: str,
                                parameter_type: str,
                                organism: str = None,
                                substrate: str = None) -> Dict:
    """Calculate mean, median, std_dev, 95% CI and cache in database."""
    # Queries raw data, calculates stats, inserts into brenda_statistics
    # Returns: {mean_value, median_value, std_dev, count, confidence_interval_95_*}

# Retrieve cached statistics
def get_brenda_statistics(self,
                         ec_number: str,
                         parameter_type: str,
                         organism: str = None,
                         substrate: str = None) -> Dict:
    """Retrieve cached statistics without recalculation."""

# Database summary
def get_brenda_summary(self) -> Dict:
    """Get summary: total_records, unique_ec_numbers, unique_organisms, 
       by_parameter_type, average_quality, cached_statistics."""
```

### 2. UI Integration (`brenda_category.py`)

**Auto-Save on Query Completion:**

```python
def _on_query_all_complete(self, result: Dict[str, Any]):
    """Callback when batch query completes."""
    # ... existing code ...
    
    # Auto-save to database if available
    if self.heuristic_db and results:
        # Insert raw data
        inserted_count = self.heuristic_db.insert_brenda_raw_data(results)
        self.logger.info(f"Saved {inserted_count} BRENDA results to local database")
        
        # Calculate statistics for each unique EC number
        unique_ecs = set(r.get('ec_number') for r in results)
        for ec_number in unique_ecs:
            for param_type in ['Km', 'kcat', 'Ki']:
                stats = self.heuristic_db.calculate_brenda_statistics(
                    ec_number=ec_number,
                    parameter_type=param_type
                )
                if stats:
                    self.logger.info(f"Calculated {param_type} statistics for {ec_number}: "
                                   f"mean={stats['mean_value']:.3f}, n={stats['count']}")
        
        # Show database summary
        db_summary = self.heuristic_db.get_brenda_summary()
        self.logger.info(f"Database now contains {db_summary['total_records']} BRENDA records "
                       f"from {db_summary['unique_ec_numbers']} EC numbers")
```

**Single Query Auto-Save:**

```python
def _on_search_complete(self, results):
    """Callback when single EC query completes."""
    # ... existing code ...
    
    # Auto-save to database
    if self.heuristic_db and results and 'parameters' in results:
        # Convert to database format
        db_results = []
        for param in results['parameters']:
            db_results.append({
                'ec_number': results.get('ec_number', ''),
                'parameter_type': param.get('type', ''),
                'value': param.get('value', 0.0),
                # ... other fields ...
            })
        
        inserted_count = self.heuristic_db.insert_brenda_raw_data(db_results)
        self.logger.info(f"Saved {inserted_count} BRENDA results to local database")
```

---

## Testing

### Test Script: `dev/test_brenda_database_integration.py`

**Test Coverage:**
1. ✅ Database initialization and schema creation
2. ✅ Bulk insert of BRENDA raw data
3. ✅ Query with filters (EC, organism, quality threshold)
4. ✅ Statistical calculation (mean, median, std_dev, 95% CI)
5. ✅ Organism-specific statistics
6. ✅ Cached statistics retrieval
7. ✅ Database summary (total records, unique ECs, etc.)
8. ✅ Duplicate prevention (UNIQUE constraint)

**Test Results:**
```
======================================================================
BRENDA Database Integration Test
======================================================================

1. Initializing database...
   ✓ Database initialized

2. Preparing sample BRENDA data...
   ✓ Created 5 sample records

3. Inserting data into database...
   ✓ Inserted 4 records (duplicates skipped)

4. Querying EC 2.7.1.1 data...
   ✓ Found 3 records for EC 2.7.1.1
      - Km: 0.15 mM (Homo sapiens, quality=0.95)
      - Km: 0.18 mM (Homo sapiens, quality=0.92)
      - Km: 0.52 mM (Saccharomyces cerevisiae, quality=0.88)

5. Querying with filters (EC 2.7.1.1, organism=Homo sapiens, min_quality=0.9)...
   ✓ Found 2 records matching filters
      - Km: 0.15 mM (quality=0.95)
      - Km: 0.18 mM (quality=0.92)

6. Calculating statistics for EC 2.7.1.1 Km...
   ✓ Statistics calculated:
      - Mean: 0.283 mM
      - Median: 0.180 mM
      - Std Dev: 0.206 mM
      - Range: 0.150 - 0.520 mM
      - 95% CI: [0.051, 0.516] mM
      - Count: 3 values

7. Calculating organism-specific statistics (EC 2.7.1.1, Km, Homo sapiens)...
   ✓ Human-specific statistics:
      - Mean: 0.165 mM
      - Count: 2 values

8. Retrieving cached statistics...
   ✓ Retrieved cached statistics:
      - Mean: 0.283 mM
      - Last updated: 2025-11-06 22:38:25

9. Getting database summary...
   ✓ Database summary:
      - Total records: 4
      - Unique EC numbers: 2
      - Unique organisms: 3
      - Average quality: 0.90
      - Cached statistics: 2
      - By parameter type: {'Km': 4}

10. Testing duplicate prevention...
   ✓ Re-inserted 0/2 records (0 expected due to UNIQUE constraint)

======================================================================
All tests completed successfully! ✓
======================================================================
```

---

## Usage Examples

### Example 1: Query Local Database for Cached Results

```python
from shypn.crossfetch.database.heuristic_db import HeuristicDatabase

db = HeuristicDatabase()

# Get all Km values for hexokinase
results = db.query_brenda_data(
    ec_number='2.7.1.1',
    parameter_type='Km',
    min_quality=0.8  # Only high-quality results
)

print(f"Found {len(results)} Km values for hexokinase")
for result in results:
    print(f"  {result['value']} {result['unit']} ({result['organism']})")
```

### Example 2: Get Statistical Summary

```python
# Get cached statistics for hexokinase Km
stats = db.get_brenda_statistics(
    ec_number='2.7.1.1',
    parameter_type='Km'
)

if stats:
    print(f"Hexokinase Km: {stats['mean_value']:.2f} ± {stats['std_dev']:.2f} mM")
    print(f"Based on {stats['count']} experimental values")
    print(f"95% CI: [{stats['confidence_interval_95_lower']:.2f}, "
          f"{stats['confidence_interval_95_upper']:.2f}] mM")
```

### Example 3: Organism-Specific Heuristics

```python
# Get human-specific statistics
human_stats = db.calculate_brenda_statistics(
    ec_number='2.7.1.1',
    parameter_type='Km',
    organism='Homo sapiens'
)

# Get yeast-specific statistics
yeast_stats = db.calculate_brenda_statistics(
    ec_number='2.7.1.1',
    parameter_type='Km',
    organism='Saccharomyces cerevisiae'
)

print(f"Human Km: {human_stats['mean_value']:.2f} mM (n={human_stats['count']})")
print(f"Yeast Km: {yeast_stats['mean_value']:.2f} mM (n={yeast_stats['count']})")
```

---

## Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    BRENDA SOAP API Query                        │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                │ Results (6,928 records)
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│              BRENDACategory._on_query_all_complete()            │
│  • Parse results                                                 │
│  • Calculate quality scores (BRENDADataFilter)                   │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                ┌───────────────┴───────────────┐
                │                               │
                ▼                               ▼
┌─────────────────────────┐    ┌──────────────────────────────┐
│  brenda_raw_data table  │    │   Gtk.TreeView Display       │
│  • Store ALL results    │    │   • Show to user             │
│  • Quality scores       │    │   • Allow filtering          │
│  • UNIQUE constraint    │    │   • Manual selection         │
└────────────┬────────────┘    └──────────────────────────────┘
             │
             │ Auto-aggregate
             ▼
┌─────────────────────────┐
│ brenda_statistics table │
│  • Calculate mean/SD    │
│  • 95% confidence       │
│  • Cache for fast query │
└─────────────────────────┘
```

---

## Benefits

### 1. Progressive Knowledge Accumulation
- Each BRENDA query builds local database
- Over time, accumulate comprehensive kinetic parameter library
- No need to re-query BRENDA for previously fetched data

### 2. Offline Access
- Query local database instead of BRENDA API
- Instant results (no network latency)
- Works without internet connection

### 3. Statistical Analysis
- Calculate mean Km ± std_dev for each enzyme
- 95% confidence intervals
- Organism-specific statistics
- Quality-weighted averages

### 4. Heuristic Inference
- Train parameter estimation models on accumulated data
- "For enzyme X in organism Y, typical Km is Z ± σ"
- Fill gaps when BRENDA has no exact match

### 5. Quality Tracking
- Store quality scores alongside data
- Filter by minimum quality threshold
- Identify high-confidence vs uncertain values

---

## Future Enhancements

### 1. Migration System
For existing databases without BRENDA tables:
```python
def migrate_to_brenda_schema(self):
    """Migrate existing database to include BRENDA tables."""
    with self._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT schema_version FROM schema_version")
        version = cursor.fetchone()[0]
        
        if version < 2:
            # Add BRENDA tables
            # Update schema_version to 2
```

### 2. Smart Cache-First Queries
```python
def get_km_values(ec_number, organism=None):
    """Get Km values, preferring local cache over BRENDA API."""
    # 1. Check local database first
    local_results = db.query_brenda_data(ec_number=ec_number, organism=organism)
    
    if len(local_results) >= 10:  # Sufficient local data
        return local_results
    else:
        # 2. Query BRENDA API
        api_results = brenda_api.get_km_values(ec_number)
        # 3. Save to database
        db.insert_brenda_raw_data(api_results)
        return api_results
```

### 3. Background Bulk Import
```python
def bulk_import_ec_list(ec_numbers: List[str]):
    """Background import of multiple EC numbers."""
    for ec in ec_numbers:
        # Check if already cached
        if db.query_brenda_data(ec_number=ec):
            continue
        
        # Query BRENDA
        results = brenda_api.get_all_parameters(ec)
        
        # Save to database
        db.insert_brenda_raw_data(results)
```

### 4. Machine Learning Integration
```python
def train_km_predictor():
    """Train ML model to predict Km from sequence/structure."""
    # Load all BRENDA data
    all_data = db.query_brenda_data()
    
    # Extract features (EC number, organism, substrate)
    # Train regression model
    # Predict Km for unknown enzymes
```

---

## Files Modified

### 1. `src/shypn/crossfetch/database/heuristic_db.py`
- **Lines 246-336:** Added `brenda_raw_data` and `brenda_statistics` tables to schema
- **Lines 821-960:** Added 6 new methods for BRENDA data management:
  - `insert_brenda_raw_data()`
  - `query_brenda_data()`
  - `calculate_brenda_statistics()`
  - `get_brenda_statistics()`
  - `get_brenda_summary()`

### 2. `src/shypn/ui/panels/pathway_operations/brenda_category.py`
- **Lines 36-47:** Added imports for `BRENDADataFilter` and `HeuristicDatabase`
- **Lines 95-106:** Initialize `self.heuristic_db` in `__init__()`
- **Lines 675-714:** Auto-save in `_on_search_complete()` (single query)
- **Lines 884-933:** Auto-save in `_on_query_all_complete()` (batch query)

### 3. `dev/test_brenda_database_integration.py`
- **NEW FILE:** Comprehensive test script (188 lines)
- Tests all database operations end-to-end

---

## Database Location

**Path:** `~/.shypn/heuristic_parameters.db`

**Inspect with:**
```bash
# Install sqlite3 (if needed)
sudo apt install sqlite3

# Query raw data
sqlite3 ~/.shypn/heuristic_parameters.db "SELECT * FROM brenda_raw_data LIMIT 10;"

# Query statistics
sqlite3 ~/.shypn/heuristic_parameters.db "SELECT * FROM brenda_statistics;"

# Get summary
sqlite3 ~/.shypn/heuristic_parameters.db "
  SELECT parameter_type, COUNT(*) as count, AVG(source_quality) as avg_quality
  FROM brenda_raw_data
  GROUP BY parameter_type;
"
```

---

## Summary

✅ **BRENDA database integration is complete and fully tested.**

The system now automatically:
1. Saves all BRENDA query results to local SQLite database
2. Calculates statistical aggregations (mean, std_dev, 95% CI)
3. Indexes data for fast queries by EC, organism, quality
4. Prevents duplicate storage with UNIQUE constraints
5. Provides comprehensive query API for offline access

**Next Steps:**
1. Implement cache-first query strategy (check database before BRENDA API)
2. Add background bulk import for EC number lists
3. Integrate statistical heuristics into model parameter inference
4. Build ML predictor trained on accumulated BRENDA data

**Key Achievement:**
Every BRENDA query now permanently enriches the local knowledge base, progressively building a comprehensive kinetic parameter library for heuristic inference and model enrichment.
