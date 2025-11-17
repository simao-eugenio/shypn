# Knowledge Base (KB) Completion Plan

**Goal**: Fully integrate the HeuristicDatabase (KB) with enrichment controllers to enable caching, learning, and intelligent parameter recommendation.

**Database Location**: `~/.shypn/heuristic_parameters.db`

---

## Current State Analysis

### ✅ What's Working
- **Database Schema**: Complete (7 tables)
- **BRENDA Data Storage**: `insert_brenda_raw_data()`, `calculate_brenda_statistics()`
- **Query Cache**: `get_cached_query()`, `cache_query()` in `heuristic_engine.py`
- **Organism Compatibility**: Default compatibility scores loaded
- **Unit Conversion**: Standardized units (mM, mM/s, s⁻¹)

### ❌ What's Missing
- **SABIO-RK → KB**: No caching of SABIO-RK results
- **BRENDA → KB**: No integration with `brenda_enrichment_controller.py`
- **Apply → KB**: No recording of applied parameters
- **User Feedback**: No usage tracking, no rating system
- **Learning**: No recommendation ranking based on history
- **Statistics**: No pre-calculated stats from SABIO-RK

---

## Implementation Phases

### **Phase 1: Data Ingestion** (Priority: HIGH)
**Objective**: Cache all API results in KB for instant retrieval

#### Task 1.1: SABIO-RK Result Caching
**Files**: `src/shypn/helpers/sabio_rk_enrichment_controller.py`

**Changes Needed**:
```python
# In __init__():
from shypn.crossfetch.database.heuristic_db import HeuristicDatabase
self.db = HeuristicDatabase()

# In query_for_transition():
def query_for_transition(self, transition_info, organism=None):
    # 1. Check cache first
    query_key = f"sabio_rk|{ec_number}|{organism or 'all'}"
    cached = self.db.get_cached_sabio_query(query_key)
    if cached:
        self.logger.info(f"KB cache hit: {query_key}")
        return cached
    
    # 2. Query SABIO-RK API (slow)
    result = self.sabio_client.query_by_ec(ec_number, organism)
    
    # 3. Store in cache
    if result and result.get('parameters'):
        self.db.store_sabio_rk_result(ec_number, organism, result)
    
    return result
```

**New DB Methods Needed**:
- `store_sabio_rk_result(ec_number, organism, result_dict)`
- `get_cached_sabio_query(query_key) -> Dict`
- Add table: `sabio_rk_raw_data` (similar to `brenda_raw_data`)

**Estimated Effort**: 4 hours

---

#### Task 1.2: BRENDA Integration
**Files**: `src/shypn/helpers/brenda_enrichment_controller.py`

**Changes Needed**:
```python
# In __init__():
self.db = HeuristicDatabase()

# In query_brenda_by_ec():
def query_brenda_by_ec(self, ec_number, organism=None):
    # 1. Check cache
    cached_stats = self.db.get_brenda_statistics(
        ec_number=ec_number,
        parameter_type='Km',  # or Kcat, Vmax
        organism=organism
    )
    if cached_stats:
        return cached_stats
    
    # 2. Query BRENDA API
    results = self.brenda_client.query(ec_number)
    
    # 3. Store raw results
    self.db.insert_brenda_raw_data(results)
    
    # 4. Calculate and cache statistics
    stats = self.db.calculate_brenda_statistics(ec_number, 'Km', organism)
    
    return stats
```

**Status**: Schema exists, just needs integration in controller

**Estimated Effort**: 2 hours

---

### **Phase 2: Application Tracking** (Priority: HIGH)
**Objective**: Record when users apply parameters to transitions

#### Task 2.1: Track Applied Parameters
**Files**: `src/shypn/helpers/sabio_rk_enrichment_controller.py`, `brenda_enrichment_controller.py`

**Changes in `apply_parameters()`**:
```python
def apply_parameters(self, transition_info, selected_params, ...):
    # ... existing code to apply params ...
    
    # NEW: Store in KB
    param_id = self.db.store_parameter(
        transition_type='continuous',
        organism=selected_params.get('organism'),
        parameters={
            'vmax': converted_vmax,
            'km': converted_km,
            'kcat': converted_kcat,
            'ki': converted_ki
        },
        source='SABIO-RK',
        source_id=selected_params.get('sabio_id'),
        confidence_score=0.9,  # High confidence for SABIO-RK
        ec_number=transition_info.get('ec_number'),
        reaction_id=transition_info.get('reaction_id'),
        temperature=selected_params.get('temperature'),
        ph=selected_params.get('ph'),
        pubmed_id=selected_params.get('pubmed_id')
    )
    
    # Record enrichment
    self.db.record_enrichment(
        parameter_id=param_id,
        transition_id=transition.id,
        pathway_id=getattr(transition, 'pathway_id', None),
        reaction_id=transition_info.get('reaction_id'),
        project_path=None  # TODO: Get from project context
    )
    
    return success, message
```

**Benefits**:
- Provenance tracking (what was applied where)
- Usage statistics (which parameters work best)
- Foundation for learning

**Estimated Effort**: 3 hours per controller (6 hours total)

---

### **Phase 3: User Feedback** (Priority: MEDIUM)
**Objective**: Capture user satisfaction with applied parameters

#### Task 3.1: Rating System UI
**Files**: New UI component in `src/shypn/ui/dialogs/parameter_rating_dialog.py`

**Design**:
```
┌────────────────────────────────────┐
│  Rate Applied Parameters           │
├────────────────────────────────────┤
│  Transition: T42 (Hexokinase)      │
│  Source: SABIO-RK                  │
│  Vmax: 226.0 mM/s, Km: 0.1 mM      │
│                                    │
│  How well did these values work?   │
│  ★ ★ ★ ★ ★                         │
│  (1=Poor, 5=Excellent)             │
│                                    │
│  Notes: ___________________        │
│                                    │
│  [Skip]  [Submit Rating]           │
└────────────────────────────────────┘
```

**Trigger**: Show after simulation runs or on-demand

**Backend**:
```python
self.db.set_user_rating(parameter_id, rating=4)
self.db.update_usage(parameter_id)
```

**Estimated Effort**: 6 hours

---

#### Task 3.2: Enrichment History Viewer
**Files**: New panel in `src/shypn/ui/panels/enrichment_history_panel.py`

**Features**:
- Show all applied enrichments for current project
- Display sources, confidence, ratings
- Allow "Undo Enrichment" (restore previous values)
- Export enrichment report (CSV/PDF)

**Backend**:
```python
history = self.db.get_enrichment_history(
    pathway_id='hsa00010',
    limit=50
)
```

**Estimated Effort**: 8 hours

---

### **Phase 4: Intelligent Recommendations** (Priority: MEDIUM)
**Objective**: Use KB data to rank and recommend parameters

#### Task 4.1: Confidence Scoring
**Files**: `src/shypn/crossfetch/inference/heuristic_engine.py`

**Enhanced Query**:
```python
def query_parameters_ranked(self, ec_number, organism, transition_type):
    # Get all matches
    candidates = self.db.query_parameters(
        transition_type=transition_type,
        ec_number=ec_number,
        min_confidence=0.3
    )
    
    # Score each candidate
    scored = []
    for param in candidates:
        score = param['confidence_score']
        
        # Boost score based on usage
        if param['usage_count'] > 0:
            usage_boost = min(0.1, param['usage_count'] * 0.01)
            score += usage_boost
        
        # Boost score based on user rating
        if param['user_rating']:
            rating_boost = (param['user_rating'] - 3) * 0.05
            score += rating_boost
        
        # Organism compatibility
        compat = self.db.get_compatibility_score(
            param['organism'], organism
        )
        score *= compat
        
        scored.append((score, param))
    
    # Sort by score descending
    scored.sort(reverse=True, key=lambda x: x[0])
    
    return [param for score, param in scored]
```

**Benefits**:
- Better suggestions over time
- Personalized to user's organism/pathway
- Learn from community usage

**Estimated Effort**: 4 hours

---

#### Task 4.2: Pre-emptive Statistics
**Files**: Background task in `src/shypn/background/statistics_calculator.py`

**Functionality**:
```python
# Calculate statistics for common queries
for ec_number in frequent_ecs:
    for param_type in ['Km', 'Kcat', 'Vmax']:
        stats = db.calculate_brenda_statistics(
            ec_number, param_type
        )
        # Now cached for instant retrieval
```

**Trigger**: Run during app startup or idle time

**Estimated Effort**: 3 hours

---

### **Phase 5: Learning Engine** (Priority: LOW)
**Objective**: Implement machine learning for parameter prediction

#### Task 5.1: Feature Engineering
**Features to Extract**:
- EC number class (first 2 digits)
- Organism phylogenetic distance
- Substrate molecular weight
- Reaction stoichiometry
- Temperature/pH conditions
- Historical usage patterns

#### Task 5.2: Model Training
**Approach**: Regression model (scikit-learn)
```python
# Predict Km given EC number + organism
from sklearn.ensemble import RandomForestRegressor

model = RandomForestRegressor()
X = extract_features(db.query_parameters())  # Training data
y = [p['parameters']['km'] for p in X]
model.fit(X, y)

# Predict for new enzyme
predicted_km = model.predict(new_enzyme_features)
```

**Estimated Effort**: 20+ hours (research project)

---

## Priority Roadmap

### Sprint 1 (Immediate - 1 week)
- ✅ Fix unit conversion bugs (DONE)
- ✅ Fix SABIO-RK median selection (DONE)
- 🔲 **Task 1.1**: SABIO-RK caching (4h)
- 🔲 **Task 1.2**: BRENDA integration (2h)
- 🔲 **Task 2.1**: Application tracking (6h)

**Deliverable**: All API results cached, applied parameters tracked

---

### Sprint 2 (Near-term - 2 weeks)
- 🔲 **Task 3.1**: Rating system UI (6h)
- 🔲 **Task 3.2**: Enrichment history viewer (8h)
- 🔲 **Task 4.1**: Confidence scoring (4h)

**Deliverable**: User can rate parameters, view history, get better suggestions

---

### Sprint 3 (Future - 1 month)
- 🔲 **Task 4.2**: Pre-emptive statistics (3h)
- 🔲 Cross-organism parameter transfer wizard
- 🔲 Bulk enrichment from KB (enrich all transitions at once)

**Deliverable**: Fast queries, intelligent cross-species mapping

---

### Sprint 4 (Research - 3+ months)
- 🔲 **Task 5.1, 5.2**: Machine learning engine
- 🔲 Community KB sharing (upload/download parameter sets)
- 🔲 Literature mining for parameter extraction

**Deliverable**: Predictive parameter inference, community knowledge

---

## Database Schema Extensions

### New Table: `sabio_rk_raw_data`
```sql
CREATE TABLE sabio_rk_raw_data (
    id INTEGER PRIMARY KEY,
    ec_number TEXT NOT NULL,
    organism TEXT,
    parameter_type TEXT CHECK(parameter_type IN ('Km', 'Vmax', 'Kcat', 'Ki')),
    value REAL NOT NULL,
    unit TEXT NOT NULL,
    substrate TEXT,
    temperature REAL,
    ph REAL,
    pubmed_id TEXT,
    sabio_entry_id TEXT,
    query_date TEXT NOT NULL,
    UNIQUE(ec_number, organism, parameter_type, substrate, value, pubmed_id)
);
```

### Enhanced Table: `transition_parameters`
```sql
-- Add columns for learning
ALTER TABLE transition_parameters ADD COLUMN success_rate REAL DEFAULT 0.0;
ALTER TABLE transition_parameters ADD COLUMN rejection_count INTEGER DEFAULT 0;
ALTER TABLE transition_parameters ADD COLUMN last_rating_date TEXT;
```

---

## Testing Strategy

### Unit Tests
- `test_kb_sabio_integration.py`: Verify SABIO-RK caching
- `test_kb_brenda_integration.py`: Verify BRENDA caching
- `test_kb_tracking.py`: Verify enrichment recording
- `test_kb_scoring.py`: Verify confidence scoring

### Integration Tests
- `test_enrichment_workflow_with_kb.py`: Full workflow with KB
- `test_kb_performance.py`: Cache hit rates, query speed

### Manual Tests
- Apply SABIO-RK params → check DB has record
- Rate parameter → check rating stored
- Re-query same EC → verify cache hit
- View enrichment history → see all past applications

---

## Performance Metrics

### Before KB Integration
- SABIO-RK query: **60-120 seconds** (API call)
- BRENDA query: **30-60 seconds** (SOAP call)
- Repeated queries: Same slow performance
- No usage analytics

### After KB Integration (Target)
- First query: 60-120 seconds (cache miss)
- Repeated query: **<1 second** (cache hit)
- Cache hit rate: **>80%** after 1 week of use
- Confidence scoring: Improves suggestion quality by **30%**

---

## Success Criteria

✅ **Phase 1 Complete When**:
- All SABIO-RK/BRENDA results cached in DB
- Cache hit rate >50% after 1 day of use
- No duplicate API calls for same query

✅ **Phase 2 Complete When**:
- Every applied parameter recorded in DB
- Can generate enrichment report showing all changes
- Provenance trail exists for reproducibility

✅ **Phase 3 Complete When**:
- User can rate applied parameters
- Rating influences future recommendations
- Enrichment history viewable in UI

✅ **Phase 4 Complete When**:
- KB suggests best parameters based on history
- Cross-organism recommendations work
- Query response time <1s for cached data

✅ **Phase 5 Complete When**:
- ML model predicts parameters with >70% accuracy
- Community KB sharing implemented
- System learns from all users (opt-in)

---

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| DB corruption | HIGH | Regular backups, schema versioning |
| Cache staleness | MEDIUM | TTL expiry, manual refresh button |
| Privacy concerns | HIGH | Local-only DB, opt-in for sharing |
| Disk space growth | MEDIUM | Cleanup old entries, compression |
| Learning bias | LOW | Diverse training data, validation |

---

## Migration Path

### For Existing Users
```bash
# Automatic migration on first launch after update
# ~/.shypn/heuristic_parameters.db created
# Old enrichment data imported from project files
```

### For New Users
```bash
# DB created on first use
# Pre-populated with default organism compatibility
# Empty cache (will fill as user works)
```

---

## Documentation Needed

1. **User Guide**: "Understanding the Knowledge Base"
2. **Dev Guide**: "KB API Reference"
3. **FAQ**: "Why cache? How to clear? Privacy?"
4. **Tutorial**: "Rate parameters to improve suggestions"

---

## Next Steps

**Immediate Actions**:
1. Review this plan with team
2. Prioritize Sprint 1 tasks
3. Create GitHub issues for each task
4. Start with Task 1.1 (SABIO-RK caching)

**Weekly Progress Tracking**:
- Cache hit rate metric
- Parameters stored count
- User ratings collected
- Query performance graphs

---

*Document Version: 1.0*  
*Date: November 16, 2025*  
*Author: AI Assistant + User*
