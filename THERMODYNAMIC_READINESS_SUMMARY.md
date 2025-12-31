# Thermodynamic Constraints - Readiness Summary

**Date**: 2024  
**Branch**: `Thermodynamic-Constraints-Gibbs-Free-Energy`  
**Status**: ✅ READY TO BEGIN IMPLEMENTATION

---

## Updates Completed

### 1. SBML Validator Updated ✅
**File**: [src/shypn/data/pathway/sbml_validator.py](src/shypn/data/pathway/sbml_validator.py#L368)

**Changes**:
- ✅ Updated `_check_reversible_formulas_stochastic_risk()` method
- ✅ Changed severity: `WARNING` → `INFO`
- ✅ Changed message: Now informs about **Skellam distribution support**
- ✅ Updated recommendations: Stochastic mode now recommended (uses Skellam)

**Before** (obsolete warning):
```
⚠️ STOCHASTIC SIMULATION RISK:
Reversible reactions with net rate formulas can produce NEGATIVE rates.
Avoid STOCHASTIC mode (will fail if rates become negative).
```

**After** (informative message):
```
ℹ️ REVERSIBLE REACTIONS WITH SKELLAM DISTRIBUTION:
Reversible reactions are now FULLY SUPPORTED in stochastic simulation.
The τ-leaping engine automatically uses Skellam sampling.
✓ STOCHASTIC with τ-leaping: Automatically uses Skellam (recommended)
```

### 2. KEGG Importer Status ✅
**Files**: `src/shypn/importer/kegg/*.py`

**Current State** (no changes needed):
- ✅ Already stores `reversible` metadata on transitions
- ✅ Has `split_reversible` option (creates forward/backward transitions)
- ✅ Default behavior: single transition with reversible flag
- ✅ Compatible with Skellam distribution

**Key Code**:
```python
# reaction_mapper.py:228
transition.metadata['reversible'] = reaction.is_reversible()

# converter_base.py:63
split_reversible: bool = False  # Default: single transition
```

### 3. Skellam Distribution Integration ✅
**Version**: τ-leaping v0.3.0

**Features**:
- ✅ Auto-detects reversible formulas (pattern matching)
- ✅ Routes reversible → Skellam, irreversible → Poisson
- ✅ Handles net reverse flux (negative Δn values)
- ✅ Statistics tracking: `reversible_reactions`, `irreversible_reactions`

**Test Results**:
```
test_skellam.py::test_skellam_balanced                PASSED ✓
test_skellam.py::test_skellam_net_forward            PASSED ✓
test_skellam.py::test_detect_reversible_formula      PASSED ✓
test_skellam.py::test_skellam_batch_sampling         PASSED ✓
```

---

## Thermodynamic Plan Created ✅

**Document**: [THERMODYNAMIC_CONSTRAINTS_PLAN.md](THERMODYNAMIC_CONSTRAINTS_PLAN.md) (955 lines)

### Plan Highlights

#### 📐 Core Components
1. **GibbsCalculator**: ΔG° and K_eq calculations
2. **ThermodynamicDatabase**: eQuilibrator API integration
3. **CompoundResolver**: KEGG ↔ ChEBI ID mapping
4. **EquilibriumValidator**: k_f/k_r vs K_eq consistency checks
5. **ThermodynamicCorrector**: pH, temperature, ionic strength

#### 🔬 Scientific Foundation
```
ΔG = ΔG° + RT ln(Q)
K_eq = e^(-ΔG°/RT)
k_f / k_r ≈ K_eq  (thermodynamic consistency)
```

#### 🗂️ Module Structure
```
src/shypn/thermodynamics/
├── __init__.py
├── gibbs_calculator.py           # Core ΔG calculations
├── equilibrium_validator.py      # K_eq validation
├── database_interface.py         # eQuilibrator API client
├── compound_resolver.py          # ID mapping
├── thermodynamic_corrector.py    # pH/T corrections
└── data/
    ├── compound_gibbs.json       # Local cache
    └── reaction_gibbs.json
```

#### 🔗 Integration Points
- **SBML Import**: Add thermodynamic validation to `sbml_validator.py`
- **Simulation Init**: Optional `check_thermodynamics` flag
- **Skellam**: Validate forward/reverse rate ratios
- **GUI**: Display K_eq consistency in transition properties

#### 🧪 Testing Strategy
- **Unit Tests**: 80% coverage target
- **Real Models**: BIOMD0000000061 (circadian), BIOMD0000000010 (glycolysis)
- **Validation**: Compare to experimental K_eq values

#### ⏱️ Timeline (6 weeks)
| Week | Focus | Deliverable |
|------|-------|-------------|
| 1 | Core Calculator | `GibbsCalculator` + tests |
| 2 | Database | eQuilibrator API + cache |
| 3 | Validation | `EquilibriumValidator` |
| 4 | Integration | SBML/KEGG hooks |
| 5 | Testing | Comprehensive suite |
| 6 | Polish | Documentation + review |

#### 📦 Dependencies (to add)
```toml
[project]
dependencies = [
    "equilibrator-api>=0.4.5",  # Thermodynamic database
    "requests>=2.31.0",          # API client
    "diskcache>=5.6.3",          # Local caching
]
```

---

## Git Status

### Commits
```bash
66b82f6 - Update SBML validator to inform about Skellam distribution support
124acda - Add comprehensive thermodynamic constraints implementation plan
```

### Branch Status
```
Branch: Thermodynamic-Constraints-Gibbs-Free-Energy
Ahead of origin/main by 6 commits:
  - 2 new (thermodynamic updates)
  - 4 from Skellam implementation
Status: ✅ Pushed to remote
```

### Files Modified (This Session)
1. `src/shypn/data/pathway/sbml_validator.py` (validator update)
2. `THERMODYNAMIC_CONSTRAINTS_PLAN.md` (new, 955 lines)
3. `THERMODYNAMIC_READINESS_SUMMARY.md` (this file)

---

## Readiness Checklist

### Prerequisites ✅
- [x] Skellam distribution implemented (v0.3.0)
- [x] Reversible reaction detection working
- [x] SBML validator updated for Skellam
- [x] KEGG importer stores reversible metadata
- [x] Tests passing (4/4 Skellam tests)
- [x] Documentation complete

### Ready to Start ✅
- [x] Branch created and active
- [x] Plan documented (955 lines)
- [x] Architecture designed
- [x] Timeline established (6 weeks)
- [x] Integration points identified
- [x] Dependencies specified
- [x] Testing strategy defined

### Next Immediate Steps
1. **Week 1**: Implement `GibbsCalculator`
   - Create `src/shypn/thermodynamics/gibbs_calculator.py`
   - Implement ΔG° calculation: `ΔG° = Σ(ν·ΔG°_f)`
   - Implement K_eq calculation: `K_eq = exp(-ΔG°/RT)`
   - Write unit tests (ATP hydrolysis)

2. **Week 2**: Database integration
   - Set up eQuilibrator API client
   - Implement compound resolver (KEGG ↔ ChEBI)
   - Create local cache system

3. **Week 3**: Validation logic
   - Implement `EquilibriumValidator`
   - Add pH/temperature corrections
   - Test with glycolysis pathway

---

## Scientific Context

### Manuscript Roadmap
1. ✅ Signal classification (Phase 1)
2. ✅ τ-leaping with weak independence (Phase 2)
3. ✅ Skellam for reversible reactions (Phase 2 enhancement)
4. 🎯 **Thermodynamic constraints** (Phase 3 - CURRENT)

### Why This Matters
- **Physical Realism**: Models must respect thermodynamic laws
- **Equilibrium Validation**: Rate ratios should match experimental K_eq
- **Gibbs Feasibility**: Reactions with ΔG > 0 shouldn't proceed spontaneously
- **Integration**: Validates forward/reverse rate pairs in Skellam sampling

### Expected Impact
- Detect thermodynamic violations in SBML models
- Suggest rate constant corrections
- Improve model accuracy and biological realism
- Novel contribution to stochastic simulation field

---

## Key Equations

### Gibbs Free Energy
```
ΔG = ΔG° + RT ln(Q)
```
- **ΔG°**: Standard free energy change (kJ/mol)
- **R**: 8.314 J/(mol·K)
- **T**: Temperature (K)
- **Q**: Reaction quotient

### Equilibrium Constant
```
K_eq = exp(-ΔG° / RT)
```

### Thermodynamic Consistency
```
k_forward / k_reverse ≈ K_eq
```
Deviation tolerance: ±50% (orders of magnitude can vary)

### pH Correction (Biochemical Standard State)
```
ΔG'° = ΔG° + n_H+ · RT ln(10) · (pH - pH_standard)
```

---

## Performance Targets

### Validation Speed
- **Initial validation** (100 reactions): ~5-10 seconds (cold cache)
- **Subsequent runs**: ~0.1-0.5 seconds (warm cache)
- **Memory overhead**: ~50-100 MB

### Cache Strategy
- **Disk cache**: `~/.shypn/thermodynamics/cache/`
- **Cache key**: `(compound_id, pH, T, ionic_strength)` → ΔG°_f
- **Expiry**: 30 days (configurable)
- **Offline mode**: Ship with ~500 common metabolites

---

## References

### Key Papers
1. **Alberty (2003)**: *Thermodynamics of Biochemical Reactions*
2. **Flamholz et al. (2012)**: eQuilibrator—the biochemical thermodynamics calculator
3. **Noor et al. (2013)**: Consistent estimation of Gibbs energy using component contributions
4. **Beard & Qian (2008)**: *Chemical Biophysics: Quantitative Analysis of Cellular Systems*

### Databases
- **eQuilibrator**: https://equilibrator.weizmann.ac.il/
- **ChEBI**: https://www.ebi.ac.uk/chebi/
- **MetaCyc**: https://metacyc.org/

---

## Summary

### What Was Done
1. ✅ Updated SBML validator to reflect Skellam support
2. ✅ Verified KEGG importer compatibility
3. ✅ Created comprehensive 6-week implementation plan (955 lines)
4. ✅ Pushed all changes to remote branch

### What's Ready
- Architecture designed
- Integration points identified
- Testing strategy defined
- Timeline established
- Dependencies specified

### What's Next
**START WEEK 1**: Implement `GibbsCalculator` class with ΔG° and K_eq calculations.

---

**Status**: ✅ **READY TO BEGIN IMPLEMENTATION**  
**Branch**: `Thermodynamic-Constraints-Gibbs-Free-Energy`  
**Estimated Completion**: 6 weeks  
**Contact**: Open GitHub issue with label `thermodynamics`
