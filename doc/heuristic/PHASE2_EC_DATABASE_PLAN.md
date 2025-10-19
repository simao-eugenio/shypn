# Phase 2: EC Number Database Integration

**Date**: October 19, 2025  
**Status**: 🎯 **PLANNING → ARCHITECTURE UPDATED**  
**Phase**: 2 of 3 (Kinetics Enhancement)

---

## ⚠️ ARCHITECTURE DECISION (Oct 19, 2025)

**Updated Approach**: **Hybrid API System** (External API + Cache + Fallback)

**Original Plan**: Large local database with all enzymes  
**Problem Identified**: Scaling - local DB would grow to 100+ MB, hard to maintain  
**New Plan**: Fetch from external APIs (BRENDA/SABIO-RK), cache locally, minimal fallback

**See Full Analysis**: `ARCHITECTURE_API_VS_LOCAL_DB.md`

### Selected Architecture

```
TIER 1: SQLite Cache (~/.shypn/cache/) → <1 MB, 30-day TTL
         ↓ (miss)
TIER 2: SABIO-RK/BRENDA API → 83,000+ enzymes, always current
         ↓ (offline/fail)
TIER 3: Fallback DB (10 enzymes) → glycolysis only, bundled
```

**Benefits**:
- ✅ **Scales infinitely** (only cache what you use)
- ✅ **Always up-to-date** (fetches from source)
- ✅ **Fast after first fetch** (<10ms from cache)
- ✅ **Works offline** (fallback database)
- ✅ **Proper attribution** (source + PMID from API)

**Implementation**: See `enzyme_kinetics_api.py` instead of large local database

---

## Overview (Updated)

Enhance the kinetics assignment system with **API-based access** to enzyme kinetic parameters from literature databases, enabling high-confidence assignments for enzymatic reactions.

## Current State (After Phase 1)

### What We Have ✅
- ✅ Heuristic assignment system working
- ✅ KEGG integration complete
- ✅ Metadata tracking (source, confidence, rule)
- ✅ KEGG compatibility fixes

### Current Behavior
```
KEGG Import → Detect EC number → Apply heuristic (medium confidence)
  Example: EC 2.7.1.1 → michaelis_menten(..., 10.0, 0.5)
           ↑ Detected  ↑ Estimated parameters
```

### Limitation
**Estimated parameters are generic defaults**:
- Vmax: 10.0 (arbitrary)
- Km: 0.5 (arbitrary)
- Based on reaction structure, not actual enzyme kinetics

## Phase 2 Goal

**Upgrade from estimated to literature-based parameters**:

```
KEGG Import → Detect EC number → Lookup in database → High confidence
  Example: EC 2.7.1.1 → BRENDA → michaelis_menten(..., 450.0, 0.1)
           ↑ Detected  ↑ Found  ↑ Literature values
```

**Result**: High-confidence kinetic parameters from scientific literature.

---

## Architecture

### Database Structure

```python
# File: src/shypn/data/enzyme_kinetics_db.py

ENZYME_KINETICS = {
    "2.7.1.1": {  # Hexokinase
        "enzyme_name": "Hexokinase",
        "ec_number": "2.7.1.1",
        "type": "continuous",
        "law": "michaelis_menten",
        "organism": "Homo sapiens",
        "parameters": {
            "vmax": 450.0,      # μmol/min/mg protein
            "vmax_unit": "μmol/min/mg",
            "km_glucose": 0.1,  # mM
            "km_atp": 0.5,      # mM
            "km_unit": "mM"
        },
        "substrates": ["D-Glucose", "ATP"],
        "products": ["D-Glucose 6-phosphate", "ADP"],
        "source": "BRENDA",
        "reference": "PMID:12345678",
        "confidence": "high",
        "notes": "Brain hexokinase, pH 7.4, 37°C"
    },
    
    "2.7.1.11": {  # Phosphofructokinase
        "enzyme_name": "6-phosphofructokinase",
        "ec_number": "2.7.1.11",
        "type": "continuous",
        "law": "michaelis_menten",
        "organism": "Homo sapiens",
        "parameters": {
            "vmax": 200.0,      # μmol/min/mg
            "vmax_unit": "μmol/min/mg",
            "km_f6p": 0.15,     # mM
            "km_atp": 0.08,     # mM
            "km_unit": "mM"
        },
        "substrates": ["Fructose 6-phosphate", "ATP"],
        "products": ["Fructose 1,6-bisphosphate", "ADP"],
        "source": "BRENDA",
        "reference": "PMID:87654321",
        "confidence": "high",
        "allosteric": {
            "inhibitors": ["ATP", "Citrate"],
            "activators": ["AMP", "ADP", "Fructose 2,6-bisphosphate"]
        },
        "notes": "Muscle PFK, allosterically regulated"
    },
    
    # Add more enzymes from glycolysis, TCA cycle, etc.
}
```

### Database Module

```python
# File: src/shypn/data/enzyme_kinetics_db.py

class EnzymeKineticsDB:
    """
    Database of enzyme kinetic parameters from literature.
    
    Sources:
    - BRENDA (www.brenda-enzymes.org)
    - SABIO-RK (sabio.h-its.org)
    - Literature (PubMed)
    """
    
    def __init__(self):
        """Initialize database."""
        self._db = ENZYME_KINETICS
    
    def lookup(self, ec_number: str, organism: str = "Homo sapiens") -> Optional[Dict]:
        """
        Lookup kinetic parameters by EC number.
        
        Args:
            ec_number: EC number (e.g., "2.7.1.1")
            organism: Organism name (default: human)
        
        Returns:
            Dict with kinetic parameters or None if not found
        """
        entry = self._db.get(ec_number)
        if not entry:
            return None
        
        # Check organism match (could extend to allow other organisms)
        if entry.get("organism") != organism:
            # Could add fuzzy matching or return anyway
            pass
        
        return entry
    
    def get_parameters(self, ec_number: str) -> Optional[Dict]:
        """Get just the parameters dict."""
        entry = self.lookup(ec_number)
        return entry.get("parameters") if entry else None
    
    def get_all_ec_numbers(self) -> List[str]:
        """Get list of all EC numbers in database."""
        return list(self._db.keys())
    
    def has_ec_number(self, ec_number: str) -> bool:
        """Check if EC number is in database."""
        return ec_number in self._db
```

### Integration with KineticsAssigner

```python
# File: src/shypn/heuristic/kinetics_assigner.py

from shypn.data.enzyme_kinetics_db import EnzymeKineticsDB

class KineticsAssigner:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.database = EnzymeKineticsDB()  # NEW
    
    def _assign_from_database(
        self,
        transition,
        reaction,
        substrate_places: Optional[List],
        product_places: Optional[List]
    ) -> AssignmentResult:
        """
        Assign from EC number database lookup.
        
        NEW IMPLEMENTATION (was placeholder in Phase 1).
        """
        # Extract EC number
        ec_numbers = getattr(reaction, 'ec_numbers', [])
        if not ec_numbers:
            return AssignmentResult.failed("No EC number")
        
        ec_number = ec_numbers[0]  # Use first EC number
        
        # Lookup in database
        db_entry = self.database.lookup(ec_number)
        if not db_entry:
            self.logger.debug(f"EC {ec_number} not in database")
            return AssignmentResult.failed(f"EC {ec_number} not found in database")
        
        # Found in database!
        self.logger.info(f"Found EC {ec_number} in database: {db_entry['enzyme_name']}")
        
        # Extract parameters
        params = db_entry['parameters']
        
        # Determine kinetic law
        if db_entry['law'] == 'michaelis_menten':
            transition.transition_type = "continuous"
            
            # Build rate function with database parameters
            substrate_place = substrate_places[0] if substrate_places else None
            if substrate_place:
                # Get Vmax and Km from database
                vmax = params.get('vmax', 10.0)
                
                # Try to match substrate to Km parameter
                # e.g., km_glucose, km_atp, etc.
                km = None
                for key, value in params.items():
                    if key.startswith('km_'):
                        km = value
                        break
                
                if km is None:
                    km = 0.5  # Fallback
                
                rate_function = f"michaelis_menten({substrate_place.name}, {vmax}, {km})"
                
                if not hasattr(transition, 'properties'):
                    transition.properties = {}
                transition.properties['rate_function'] = rate_function
                
                result = AssignmentResult.from_database(
                    parameters=params,
                    rate_function=rate_function,
                    ec_number=ec_number
                )
                
                KineticsMetadata.set_from_result(transition, result)
                
                self.logger.info(
                    f"Assigned database kinetics to {transition.name}: "
                    f"EC {ec_number}, Vmax={vmax}, Km={km}"
                )
                
                return result
        
        # Fallback if law not supported
        return AssignmentResult.failed(f"Unsupported kinetic law: {db_entry['law']}")
```

---

## Implementation Plan

### Step 1: Create Database Module

**File**: `src/shypn/data/enzyme_kinetics_db.py`

**Tasks**:
1. Create `ENZYME_KINETICS` dict with initial entries
2. Implement `EnzymeKineticsDB` class
3. Add lookup methods
4. Add organism filtering (optional)

**Initial Enzymes** (Glycolysis pathway):
```
EC 2.7.1.1   - Hexokinase
EC 5.3.1.9   - Glucose-6-phosphate isomerase
EC 2.7.1.11  - 6-phosphofructokinase
EC 4.1.2.13  - Fructose-bisphosphate aldolase
EC 5.3.1.1   - Triosephosphate isomerase
EC 1.2.1.12  - Glyceraldehyde-3-phosphate dehydrogenase
EC 2.7.2.3   - Phosphoglycerate kinase
EC 5.4.2.12  - Phosphoglycerate mutase
EC 4.2.1.11  - Enolase
EC 2.7.1.40  - Pyruvate kinase
```

### Step 2: Integrate with Assigner

**File**: `src/shypn/heuristic/kinetics_assigner.py`

**Tasks**:
1. Import `EnzymeKineticsDB`
2. Initialize in `__init__()`
3. Implement `_assign_from_database()` (replace placeholder)
4. Update logging

**Expected Flow**:
```
assign() → Tier 1 (explicit) → Tier 2 (database) → Tier 3 (heuristic)
                                      ↑ NEW
```

### Step 3: Update AssignmentResult

**File**: `src/shypn/heuristic/assignment_result.py`

**Already has**:
```python
@classmethod
def from_database(
    cls,
    parameters: Dict[str, Any],
    rate_function: str,
    ec_number: Optional[str] = None
) -> 'AssignmentResult':
    # Already implemented ✓
```

**Verify**:
- Confidence level is HIGH for database lookups
- Source is DATABASE

### Step 4: Testing

**Test 1**: Database Lookup
```python
def test_database_lookup():
    """Test EC number database lookup."""
    db = EnzymeKineticsDB()
    
    # Lookup hexokinase
    entry = db.lookup("2.7.1.1")
    assert entry is not None
    assert entry['enzyme_name'] == "Hexokinase"
    assert 'vmax' in entry['parameters']
    assert entry['confidence'] == 'high'
```

**Test 2**: Integration with Assigner
```python
def test_database_assignment():
    """Test assignment from database."""
    transition = Transition(0, 0, "T1", "T1")
    
    class MockReaction:
        ec_numbers = ["2.7.1.1"]  # Hexokinase
    
    substrate_places = [Place(0, 0, "P1", "Glucose")]
    product_places = [Place(0, 0, "P2", "G6P")]
    
    assigner = KineticsAssigner()
    result = assigner.assign(
        transition, MockReaction(), substrate_places, product_places
    )
    
    # Should use database (high confidence)
    assert result.success
    assert result.confidence == ConfidenceLevel.HIGH
    assert result.source == AssignmentSource.DATABASE
    assert 'michaelis_menten' in transition.properties['rate_function']
    
    # Verify database parameters used (not defaults)
    assert '450.0' in transition.properties['rate_function']  # Database Vmax
    assert '0.1' in transition.properties['rate_function']    # Database Km
```

**Test 3**: KEGG Integration with Database
```python
def test_kegg_with_database():
    """Test KEGG import uses database when EC available."""
    # Import pathway with EC numbers
    # Verify high-confidence assignments
    # Compare to Phase 1 (heuristic only)
```

### Step 5: Documentation

**Update Files**:
1. `KINETICS_ENHANCEMENT_PLAN.md` - Mark Phase 2 complete
2. `PHASE2_EC_DATABASE_IMPLEMENTATION.md` - New doc for Phase 2
3. `INDEX.md` - Add Phase 2 documentation
4. `README.md` - Update status

---

## Data Sources

### BRENDA (Primary)

**Website**: https://www.brenda-enzymes.org

**What to Extract**:
- Vmax (turnover number)
- Km (Michaelis constant) for each substrate
- Organism (prefer Homo sapiens)
- Temperature, pH conditions
- Reference (PMID)

**Example Entry** (Hexokinase):
```
EC 2.7.1.1
Organism: Homo sapiens
Substrate: D-glucose
Km: 0.05 - 0.15 mM (brain, various studies)
Vmax: 300 - 600 μmol/min/mg (brain)
References: Multiple PMIDs
```

### SABIO-RK (Secondary)

**Website**: http://sabio.h-its.org

**Advantage**: Already structured kinetic data
**Format**: Can export as CSV/JSON

### Manual Curation

**For glycolysis enzymes**:
- Use well-studied human enzymes
- Prefer recent reviews
- Note experimental conditions
- Include range (min-max) if available

---

## Example: Complete Glycolysis Database

```python
GLYCOLYSIS_ENZYMES = {
    "2.7.1.1": {
        "enzyme_name": "Hexokinase",
        "ec_number": "2.7.1.1",
        "reaction": "D-Glucose + ATP → D-Glucose 6-phosphate + ADP",
        "organism": "Homo sapiens",
        "isoform": "Brain (HK1)",
        "parameters": {
            "vmax": 450.0,
            "vmax_unit": "μmol/min/mg",
            "km_glucose": 0.1,
            "km_atp": 0.5,
            "km_unit": "mM"
        },
        "conditions": {
            "temperature": 37,
            "temperature_unit": "°C",
            "ph": 7.4
        },
        "source": "BRENDA",
        "reference": "Wilson JE. Hexokinases. Rev Physiol Biochem Pharmacol. 2003;148:1-65.",
        "pmid": "12687400",
        "confidence": "high"
    },
    
    # Add 9 more glycolysis enzymes...
}
```

---

## Expected Results

### Before Phase 2 (Heuristic Only)

```
KEGG Import of Glycolysis:
  34 reactions
  All enhanced with heuristic
  Confidence: LOW (no EC) or MEDIUM (has EC, estimated params)
  
Example:
  Hexokinase (EC 2.7.1.1)
    Type: continuous
    Source: heuristic
    Confidence: medium
    Rate: michaelis_menten(Glucose, 10.0, 0.5)
          ↑ Generic estimates
```

### After Phase 2 (Database Lookup)

```
KEGG Import of Glycolysis:
  34 reactions
  10 enhanced with database (glycolysis enzymes)
  24 enhanced with heuristic (other reactions)
  
Example:
  Hexokinase (EC 2.7.1.1)
    Type: continuous
    Source: database
    Confidence: HIGH
    Rate: michaelis_menten(Glucose, 450.0, 0.1)
          ↑ Literature values from BRENDA
    Reference: PMID:12687400
```

**Impact**: 10x better parameter accuracy for common enzymes!

---

## Timeline

### Week 1 (This Week)
- [ ] Day 1-2: Create database module structure
- [ ] Day 3-4: Populate with 10 glycolysis enzymes
- [ ] Day 5: Integrate with assigner

### Week 2 (Next Week)
- [ ] Day 1-2: Testing and validation
- [ ] Day 3: Documentation
- [ ] Day 4: KEGG integration testing
- [ ] Day 5: Commit Phase 2

### Future
- [ ] Expand to TCA cycle (8 enzymes)
- [ ] Add other major pathways
- [ ] Consider auto-fetching from BRENDA API

---

## Success Criteria

✅ **Phase 2 Complete When**:
1. Database module with 10+ enzymes implemented
2. Database lookup integrated in assigner (Tier 2)
3. Tests passing (database lookup, assignment, KEGG integration)
4. Documentation complete
5. KEGG import of Glycolysis uses database for 10 reactions
6. Confidence upgraded from MEDIUM → HIGH for database entries

---

## Next Phase Preview (Phase 3)

**UI Enhancements**:
- Show kinetics metadata in properties dialog
- Bulk enhancement tool
- Confidence indicators
- Parameter override UI
- Validation warnings before simulation

---

**Status**: 🎯 **READY TO START**  
**Next Step**: Create `enzyme_kinetics_db.py` with 10 glycolysis enzymes  
**Estimated Time**: 1-2 days for database creation
