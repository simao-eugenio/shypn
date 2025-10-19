# Kinetics Enhancement System - Next Phases Plan

**Date**: October 19, 2025  
**Current Status**: Phase 2C Complete (KEGG EC enrichment)  
**Branch**: `feature/property-dialogs-and-simulation-palette`

---

## Completed Phases ✅

### Phase 1: Core Kinetics Enhancement (✅ Complete - commit 8309b78)
- KineticsAssigner with 5 heuristic strategies
- AssignmentResult with confidence levels
- Integration with KEGG pathway converter
- 8/8 tests passing

### Phase 2: Hybrid API Architecture (✅ Complete - commit cb0147f)
- Three-tier system: Cache → API → Fallback
- EnzymeKineticsAPI (540 lines)
- EnzymeKineticsDB with 10 glycolysis enzymes
- 15/15 tests passing

### Phase 2C: KEGG EC Enrichment (✅ Complete - commit 20e86af)
- KEGGECFetcher for automatic EC number lookup
- Integration with reaction_mapper
- KineticsAssigner reads EC from metadata
- 19/19 tests passing
- **Result**: KEGG imports now get HIGH confidence kinetics!

---

## Remaining Phases 🎯

### Option A: Expand Database Coverage (Practical)

**Goal**: Improve offline support and coverage  
**Effort**: Low (1-2 hours)  
**Impact**: Immediate value for common pathways

#### Tasks:
1. **Add TCA Cycle Enzymes** (8 enzymes)
   - Citrate synthase (2.3.3.1)
   - Aconitase (4.2.1.3)
   - Isocitrate dehydrogenase (1.1.1.42)
   - α-Ketoglutarate dehydrogenase (1.2.4.2)
   - Succinyl-CoA synthetase (6.2.1.5)
   - Succinate dehydrogenase (1.3.5.1)
   - Fumarase (4.2.1.2)
   - Malate dehydrogenase (1.1.1.37)

2. **Add Pentose Phosphate Pathway** (7 enzymes)
   - Glucose-6-phosphate dehydrogenase (1.1.1.49)
   - 6-Phosphogluconolactonase (3.1.1.31)
   - 6-Phosphogluconate dehydrogenase (1.1.1.44)
   - Ribulose-5-phosphate epimerase (5.1.3.1)
   - Ribose-5-phosphate isomerase (5.3.1.6)
   - Transketolase (2.2.1.1)
   - Transaldolase (2.2.1.2)

**Result**: 25 total enzymes (vs 10 now)  
**Coverage**: ~80% of common metabolic models

---

### Option B: UI Enhancements (User-Facing)

**Goal**: Make kinetics enhancement visible and configurable  
**Effort**: Medium (3-4 hours)  
**Impact**: Better user experience

#### Task 1: Show Confidence in Transition Properties Dialog

**Current**:
```
┌─────────────────────────────────┐
│ Transition Properties: T1       │
├─────────────────────────────────┤
│ Type: [Continuous ▼]            │
│                                  │
│ Rate Function:                   │
│ ┌──────────────────────────────┐ │
│ │ michaelis_menten(P1, 10, 0.5)│ │
│ └──────────────────────────────┘ │
└─────────────────────────────────┘
```

**Enhanced**:
```
┌─────────────────────────────────────┐
│ Transition Properties: T1           │
├─────────────────────────────────────┤
│ Type: [Continuous ▼]                │
│                                      │
│ Rate Function:                       │
│ ┌────────────────────────────────┐  │
│ │ michaelis_menten(P1, 450, 0.5) │  │
│ └────────────────────────────────┘  │
│                                      │
│ ⓘ Kinetics: Database (HIGH)         │
│   EC 2.7.1.1 - Hexokinase           │
│   Source: KEGG → Fallback DB        │
│   Vmax: 450 μmol/min/mg             │
│   Km: 0.5 mM                         │
│   Reference: Lowry & Passonneau 72  │
└─────────────────────────────────────┘
```

**Implementation**:
- Add info section to `transition_prop_dialog.ui`
- Update `transition_prop_dialog_loader.py` to show metadata
- Read from `transition.metadata['enzyme_name']`, `'ec_numbers'`, etc.

#### Task 2: Bulk Enhancement Tool (Menu Item)

**Menu**: `Tools → Enhance Kinetics...`

**Dialog**:
```
┌─────────────────────────────────────────┐
│ Enhance Pathway Kinetics                │
├─────────────────────────────────────────┤
│ Scope:                                   │
│ ○ Current pathway only                  │
│ ● All pathways in document              │
│                                          │
│ Transitions found: 34                   │
│   - With EC numbers: 12 (KEGG)          │
│   - Without EC: 22                      │
│                                          │
│ Options:                                 │
│ [x] Use database for EC numbers         │
│     → 12 transitions → HIGH confidence  │
│                                          │
│ [x] Use heuristics for remaining        │
│     → 22 transitions → MEDIUM confidence│
│                                          │
│ [ ] Override existing assignments       │
│                                          │
│ [Cancel] [Enhance]                      │
└─────────────────────────────────────────┘
```

**Implementation**:
- New menu item in `ui/main_menu.ui`
- New dialog `ui/dialogs/enhance_kinetics_dialog.ui`
- New loader `helpers/enhance_kinetics_dialog_loader.py`
- Calls `KineticsAssigner.assign_bulk(transitions, options)`

---

### Option C: Real API Integration (Advanced)

**Goal**: Connect to BRENDA or other APIs for comprehensive coverage  
**Effort**: High (6-8 hours)  
**Impact**: Access to 83,000+ enzymes

#### Task 1: BRENDA SOAP API Integration

**Requirements**:
- Register for BRENDA account
- Get API key
- Install `zeep` library for SOAP

**Implementation**:
```python
# src/shypn/data/brenda_api.py

from zeep import Client

class BRENDAClient:
    def __init__(self, email: str, password: str):
        self.wsdl = 'https://www.brenda-enzymes.org/soap/brenda_zeep.wsdl'
        self.client = Client(self.wsdl)
        
    def get_km_value(self, ec_number: str) -> Dict:
        """Fetch Km values for EC number."""
        result = self.client.service.getKmValue(
            ec_number,
            self.email,
            self.password,
            'organism#Homo sapiens'
        )
        return self._parse_brenda_response(result)
```

**Integration**:
- Add as Tier 2 in `enzyme_kinetics_api.py`
- Cache → **BRENDA API** → Fallback
- Requires API key in config

#### Task 2: Configuration for API Keys

**File**: `~/.shypn/config.yaml`
```yaml
kinetics:
  apis:
    brenda:
      enabled: true
      email: "user@example.com"
      password: "api_key_here"
    sabio_rk:
      enabled: false  # Unreliable
```

---

## Recommended Path Forward 🎯

### Short Term (Today/Tomorrow)

**Option A: Expand Database** ✅ Recommended
- Quick wins (1-2 hours)
- Immediate value
- No dependencies
- Better offline support

**Steps**:
1. Research literature values for TCA cycle (8 enzymes)
2. Research literature values for pentose phosphate (7 enzymes)
3. Add to `enzyme_kinetics_db.py`
4. Test with real pathways
5. Commit as "Phase 2D: Expand enzyme database"

### Medium Term (Next Week)

**Option B: UI Enhancements** ⭐ High impact
- Better user experience
- Makes kinetics visible
- Enables bulk enhancement
- Users can see confidence levels

**Steps**:
1. Add confidence info to transition properties dialog
2. Create bulk enhancement dialog
3. Add menu item
4. Test with Glycolysis pathway
5. Commit as "Phase 3: UI enhancements for kinetics"

### Long Term (Future)

**Option C: BRENDA API** 🔮 Optional
- Comprehensive coverage
- Requires external account
- Adds complexity
- May not be needed if database expansion sufficient

---

## Decision Matrix

| Option | Effort | Impact | Dependencies | Risk |
|--------|--------|--------|--------------|------|
| **A: Expand DB** | Low (1-2h) | Medium | None | Low |
| **B: UI Enhance** | Medium (3-4h) | High | None | Low |
| **C: BRENDA API** | High (6-8h) | High | API key | Medium |

---

## My Recommendation 🎯

### Phase Sequence:

1. **Phase 2D: Expand Database** (1-2 hours) ← START HERE
   - Add TCA cycle + pentose phosphate
   - Test with real pathways
   - Quick win, immediate value

2. **Phase 3: UI Enhancements** (3-4 hours)
   - Show confidence in properties dialog
   - Add bulk enhancement tool
   - Better user experience

3. **Phase 4: BRENDA API** (Future, optional)
   - Only if needed for specific use cases
   - Requires external account
   - Can be skipped if database sufficient

---

## Current System State

**What Works** ✅:
- KEGG imports get EC numbers automatically
- EC numbers → database lookup → HIGH confidence
- Fallback to heuristics for unknown enzymes
- Offline mode functional (10 enzymes)
- All tests passing (19/19 for KEGG EC, 15/15 for API)

**What's Missing** ⏳:
- Limited enzyme coverage (10 enzymes)
- No UI indication of kinetics quality
- No bulk enhancement tool
- No comprehensive API (BRENDA)

**What Would Benefit Most Users** 🎯:
1. More enzymes in database (expand from 10 → 25)
2. UI showing confidence levels
3. Bulk enhancement for entire pathways

---

## Next Steps (Concrete)

### Option 1: Continue with Database Expansion
```bash
# I can start Phase 2D right now:
1. Research TCA cycle enzyme parameters
2. Add to enzyme_kinetics_db.py
3. Test with real pathway
4. Commit
```

### Option 2: Move to UI Enhancements
```bash
# Or start Phase 3 (UI):
1. Update transition_prop_dialog.ui
2. Add confidence display
3. Create bulk enhancement dialog
4. Test with Glycolysis
```

### Option 3: Something Else
```bash
# Or focus on different feature:
- Arc improvements?
- Simulation enhancements?
- Other features?
```

---

**Which option would you like to pursue?**

A. Expand database (quick, practical)  
B. UI enhancements (visible, user-facing)  
C. BRENDA API (comprehensive, complex)  
D. Something else (what?)
