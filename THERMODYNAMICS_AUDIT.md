# Thermodynamics Implementation Audit

**Date:** January 5, 2026  
**Branch:** Usability-and-Manuscripts  
**Status:** DUAL IMPLEMENTATION DISCOVERED

---

## Executive Summary

SHYPN has **TWO SEPARATE thermodynamics implementations** that are **NOT INTEGRATED**:

### 1. **Legacy Topology Analyzer** (`src/shypn/topology/biological/thermodynamics.py`)
- **Status:** Basic heuristic implementation (no real ΔG calculations)
- **Location:** Topology Panel → Biological Analysis
- **Capabilities:**
  - Pattern matching for ATP/GTP detection
  - Keyword-based reversibility checks
  - Simple futile cycle detection
  - **Does NOT use chemical databases**
  - **Does NOT calculate actual Gibbs free energy**
  
### 2. **Advanced Thermodynamics Module** (`src/shypn/thermodynamics/`)
- **Status:** Production-ready with eQuilibrator integration
- **Location:** Report Panel (validation results only), SBML import
- **Capabilities:**
  - Real ΔG°' calculations from compound databases
  - pH/temperature/ionic strength corrections
  - K_eq validation against kinetic rate constants
  - Multi-source provider (eQuilibrator API, static data, cached)
  - Compound resolver (KEGG ↔ ChEBI mapping)
  - **Full thermodynamic validation framework**

---

## Critical Issues

### ⚠️ **Issue 1: Topology Panel Uses Wrong Implementation**

**Current State:**
```python
# src/shypn/ui/panels/topology/biological_category.py
from shypn.topology.biological.thermodynamics import ThermodynamicAnalyzer  # ← BASIC/LEGACY

def _get_analyzers(self):
    return {
        'thermodynamics': ThermodynamicAnalyzer,  # ← WRONG ONE
    }
```

**Problem:**
- Topology panel shows "thermodynamics" analyzer but it's just heuristics
- Users think they're getting real thermodynamic analysis
- The advanced module exists but isn't exposed here

**User Experience:**
- Click "Thermodynamics" in Topology Panel → Get basic keyword matching
- Import SBML → Get real ΔG validation in Report Panel (hidden unless you know to look)

---

### ⚠️ **Issue 2: No Document-Level Settings Integration**

**Current State:**
- DocumentModel now has `thermodynamic_settings` (✅ just added)
- But validators don't read from it yet
- ThermodynamicSimulationValidator hardcoded to:
  ```python
  ph=7.0, temperature=298.15, ionic_strength=0.1
  ```

**Missing Integration:**
```python
# What SHOULD happen but doesn't:
validator = ThermodynamicSimulationValidator(
    tolerance=document.get_thermodynamic_setting('tolerance'),
    enable_web=False  # Could also come from settings
)

result = validator.validate_reversible_reaction(
    ...,
    ph=document.get_thermodynamic_setting('ph'),
    temperature=document.get_thermodynamic_setting('temperature')
)
```

---

### ⚠️ **Issue 3: Topology Analyzer Not Aware of Advanced Module**

The legacy `ThermodynamicAnalyzer` has a TODO comment:
```python
"""
CURRENT IMPLEMENTATION: Basic checks without chemical database integration
FUTURE ENHANCEMENT: Full ΔG°' calculations with compound database
"""
```

But the "future enhancement" **already exists** in `src/shypn/thermodynamics/`!

---

## Recommendations

### **Option A: Replace Topology Analyzer (Recommended)**

**Action:** Replace the basic topology analyzer with the advanced module

**Changes:**
1. Update `biological_category.py` to use real thermodynamics module
2. Create wrapper adapter if needed (topology API → thermodynamics API)
3. Display actual ΔG values, K_eq, violations in Topology panel
4. Deprecate/remove `src/shypn/topology/biological/thermodynamics.py`

**Pros:**
- Users get real thermodynamic analysis everywhere
- No duplicate implementations
- Leverage existing production-ready code

**Cons:**
- Requires API adapter (topology format vs validation format)
- May be slower (database lookups vs heuristics)

---

### **Option B: Keep Both, Clarify Purpose**

**Action:** Rename and clearly differentiate the two analyzers

**Changes:**
1. Rename topology analyzer to "Basic Feasibility Checker"
2. Add new topology analyzer "Thermodynamic Validation" using advanced module
3. Let users choose between fast heuristics vs accurate calculations

**Pros:**
- Fast heuristics still available for large models
- Full analysis available when needed
- No breaking changes

**Cons:**
- Maintains code duplication
- Confusing to have two "thermodynamic" analyzers

---

### **Option C: Unified Architecture (Best Long-Term)**

**Action:** Refactor both into unified system with modes

**Design:**
```python
class UnifiedThermodynamicAnalyzer:
    def __init__(self, model, mode='auto'):
        """
        mode options:
        - 'heuristic': Fast keyword-based (no DB)
        - 'database': Full ΔG calculations
        - 'auto': Use DB if compounds identified, else heuristic
        """
        self.basic_analyzer = BasicFeasibilityChecker(model)
        self.advanced_validator = ThermodynamicSimulationValidator()
```

**Integration Points:**
1. Topology Panel → Use unified analyzer (auto mode)
2. SBML Import → Use database mode with document settings
3. Report Panel → Show results from last analysis

**Pros:**
- Single entry point for all thermodynamics
- Performance vs accuracy tradeoff transparent
- Document settings integrated throughout

**Cons:**
- Significant refactoring required
- Need to maintain both backends

---

## Document Settings Integration Plan

Regardless of which option above, need to:

### **Phase 1: Wire Document Settings to Validators**

```python
# src/shypn/thermodynamics/simulation_integration.py
class ThermodynamicSimulationValidator:
    def __init__(self, document=None, **kwargs):
        if document and hasattr(document, 'thermodynamic_settings'):
            settings = document.thermodynamic_settings
            self.default_ph = settings.get('ph', 7.0)
            self.default_temp = settings.get('temperature', 298.15)
            self.tolerance = settings.get('tolerance', 0.5)
            self.enabled = settings.get('enable_validation', True)
        else:
            # Fallback to kwargs or defaults
            ...
```

### **Phase 2: Update SBML Import**

```python
# src/shypn/data/pathway/sbml_parser.py
validator = ThermodynamicSimulationValidator(document=document)
# Now automatically uses document's pH/temperature/tolerance
```

### **Phase 3: Update Simulation Controller**

```python
# src/shypn/engine/simulation/controller.py
if document.get_thermodynamic_setting('enable_validation'):
    validator = ThermodynamicSimulationValidator(document=document)
    results = validator.validate_sbml_reactions(...)
```

---

## UI Panel Plan (Revised)

### **Current State:**
- Report Panel: Shows validation results (read-only)
- Pathway Operations: KEGG, BiGG, SBML import categories
- Topology Panel: Mass balance, stoichiometry, **thermodynamics (basic)**

### **Proposed Addition:**

**New Category in Pathway Operations:**
```
Pathway Operations Panel
├── KEGG Import
├── BiGG Import
├── SBML Import
└── Thermodynamic Settings  ← NEW
    ├── Status: "Using E. coli cytoplasm preset"
    ├── Preset selector: [Dropdown]
    ├── pH: [7.4] slider
    ├── Temperature: [37°C] entry
    ├── Ionic Strength: [0.15 M] slider
    ├── Tolerance: [±50%] slider
    ├── Enable validation: [✓] checkbox
    ├── [Apply] [Reset] buttons
    └── "Settings apply to this model only"
```

**Updated Topology Panel:**
```
Biological Analysis
├── Mass Balance
├── Stoichiometry
├── Flux Balance
├── Thermodynamic Validation ← RENAMED/UPGRADED
│   ├── Show ΔG values
│   ├── Show K_eq vs k_f/k_r
│   └── Link: "Edit settings in Pathway Operations"
└── Dependency & Coupling
```

---

## Decision Required

**Please choose approach:**

1. **Option A:** Replace topology analyzer with advanced module
2. **Option B:** Keep both, rename to avoid confusion
3. **Option C:** Unified architecture (more work, best outcome)

**Also decide:**

4. Should UI panel be in Pathway Operations or new top-level category?
5. Implement Phase 1-3 document integration first, then UI?
6. Remove/deprecate legacy topology analyzer now or later?

---

## Files Requiring Changes

### **DocumentModel Integration (Priority 1):**
- [x] `src/shypn/data/canvas/document_model.py` - Settings storage ✅ DONE
- [ ] `src/shypn/thermodynamics/simulation_integration.py` - Read from document
- [ ] `src/shypn/data/pathway/sbml_parser.py` - Pass document to validator
- [ ] `src/shypn/engine/simulation/controller.py` - Use document settings

### **UI Panel (Priority 2):**
- [ ] `src/shypn/ui/panels/pathway_operations/thermodynamic_category.py` - NEW FILE
- [ ] `src/shypn/ui/panels/pathway_operations_panel.py` - Register category
- [ ] `src/shypn/ui/panels/report/thermodynamic_validation_category.py` - Add link

### **Topology Analyzer (Priority 3 - Pending decision):**
- [ ] `src/shypn/ui/panels/topology/biological_category.py` - Replace or rename
- [ ] `src/shypn/topology/biological/thermodynamics.py` - Deprecate or refactor

---

## Testing Requirements

- [ ] Load legacy model without thermodynamic_settings
- [ ] Apply preset, verify serialization
- [ ] Custom settings, verify in validation results
- [ ] SBML import uses model settings
- [ ] Topology panel shows correct analysis
- [ ] Disable validation, verify skipped
- [ ] Temperature in °C converts correctly to K

---

**Next Steps:** Await decision on architecture approach before proceeding.
