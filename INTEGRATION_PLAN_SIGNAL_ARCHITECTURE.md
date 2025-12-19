# Integration Plan: Signal Places Modular Architecture

**Branch:** Signal-Information-Flow  
**Target:** SHYpn v2.0 - Modular Biological Systems Support  
**Date:** December 19, 2025

---

## Executive Summary

This plan outlines integration of the **signal places modular architecture** theory into SHYpn's core system. The goal is to enable modeling of complex biological systems through **module partitioning and signal-mediated coupling**.

**Core Principle:**  
Biological networks = Local modules (arcs) + Global coordination (signals)

---

## Phase 1: Foundation (Data Model & Detection)

### 1.1 Extend Data Model
**Target:** `src/shypn/data/pathway/`

**Signal Place Classification:**
- Add `Place.is_signal: bool` property
- Add `Place.signal_type: Enum` with values:
  - `Ψ_quorum` - Cell-cell communication
  - `Ψ_energy` - Metabolic state (ATP/ADP ratios)
  - `Ψ_regulatory` - Gene expression control
  - `Ψ_spatial` - Compartment sensing
- Add `Place.signal_scope: str` (module IDs that can read)

**Module Structure:**
- Create `Module` class:
  ```python
  class Module:
      module_id: str
      name: str  # e.g., "Cytoplasm", "Mitochondria"
      places: Set[Place]
      transitions: Set[Transition]
      boundary_signals: Set[Place]  # Ψ_shared
      parent_module: Optional[Module]  # For hierarchy
  ```
- Add `Place.module_id` and `Transition.module_id`

**Files to modify:**
- `src/shypn/data/pathway/place.py`
- `src/shypn/data/pathway/transition.py`
- Create `src/shypn/data/pathway/module.py`
- `src/shypn/data/pathway/document.py` (module collection)

### 1.2 Signal Detection Service
**Target:** Create `src/shypn/services/signal_detection_service.py`

**Heuristics:**
1. **Modifier-based:** Places only read by transitions (no input/output arcs)
2. **Energy metabolites:** ATP, ADP, NADH, etc. if used across modules
3. **Regulatory factors:** Transcription factors, signaling proteins
4. **Spatial markers:** Compartment-specific indicators

**Algorithm:**
```python
def detect_signals(pathway: Pathway) -> List[Place]:
    candidates = []
    for place in pathway.places:
        if is_modifier_only(place):  # Existing modifier detection
            candidates.append(place)
        if is_energy_metabolite(place.name):
            candidates.append(place)
        if spans_multiple_modules(place):
            candidates.append(place)
    return candidates
```

### 1.3 SBML Compartment Mapping
**Target:** `src/shypn/services/sbml_loader_service.py`

**Mapping Strategy:**
1. Parse SBML `<compartment>` elements → Module objects
2. Assign species to modules based on `species.compartment` attribute
3. Detect boundary species:
   - Species in multiple compartments (shouldn't happen but check)
   - Modifiers acting across compartments → signal candidates
4. Handle compartment hierarchy (outside/inside relationships)

**SBML-to-Module mapping:**
```xml
<compartment id="c" name="Cytoplasm"/>
<compartment id="m" name="Mitochondria" outside="c"/>
<species id="ATP_c" compartment="c"/>
<species id="ATP_m" compartment="m"/>
```
↓
```
Module("Cytoplasm"): {places: [ATP_c], ...}
Module("Mitochondria"): {places: [ATP_m], ...}
Boundary signals: None (separate ATP pools)
```

---

## Phase 2: Semantics & Validation

### 2.1 Module Coupling Semantics
**Target:** Create `src/shypn/services/module_coupling_service.py`

**Validation Rules:**
1. **No direct arcs between modules:**
   ```python
   for arc in pathway.arcs:
       source_module = arc.source.module_id
       target_module = arc.target.module_id
       assert source_module == target_module, "Arc crosses module boundary!"
   ```

2. **Signal-only coupling:**
   - If transition in module M₁ reads place from module M₂ → place must be signal
   - Build coupling matrix: `C[i,j] = {Ψ ∈ Ψ_shared : read_by(M_i) ∧ written_by(M_j)}`

3. **Module independence theorem verification:**
   - Ensure `(Pᵢ ∩ Pⱼ) ⊆ Ψ_shared` for all module pairs
   - No regular places shared between modules

**Output:**
- Coupling graph showing module dependencies
- List of violations (arcs/places crossing boundaries incorrectly)

### 2.2 Simulation Engine Updates
**Target:** `src/shypn/continuous_behavior.py`

**Signal Place Semantics:**
1. **Read-only marking:** Signal places broadcast, not consumed
   ```python
   if place.is_signal:
       # Don't update marking from transitions
       # All transitions read same value simultaneously
       marking[place.id] = signal_value  # Broadcast
   ```

2. **Cross-module rate evaluation:**
   - Transitions can read signals from other modules
   - Ensure transition sees current signal state, not historical

3. **Module isolation check:**
   - During simulation, verify modules only interact via signals
   - Log warnings if unexpected coupling detected

**Backward compatibility:**
- Existing models without modules work as single module
- Signal places default to global scope if no modules defined

---

## Phase 3: Visualization (GUI)

### 3.1 Module Boundary Display
**Target:** `src/shypn/ui/canvas/` (Petri net renderer)

**Visual Design:**
- **Module boxes:** Rounded rectangles enclosing places/transitions
- **Color coding:** Each module gets distinct pastel background
- **Labels:** Module name in corner
- **Hierarchy:** Nested boxes for parent/child compartments

**Implementation:**
- Add `ModuleGroupWidget` to canvas
- Draw before rendering places/transitions (background layer)
- Handle overlap for shared signals (draw outside boxes or at boundary)

### 3.2 Signal Place Icons
**Target:** Place rendering code

**Visual Design:**
- **Signal symbol:** Ψ character or wave icon overlaid on circle
- **Type indicator:** Color or icon variation:
  - 🔵 Blue = Ψ_quorum (communication)
  - ⚡ Yellow = Ψ_energy (metabolic)
  - 🧬 Purple = Ψ_regulatory (gene expression)
  - 📍 Green = Ψ_spatial (location)

**Connections:**
- Dashed lines for signal read relationships (not arcs)
- Or: No visual line, just proximity indicates sensing

### 3.3 Module Collapse/Expand
**Target:** GUI interaction layer

**Feature:**
- **Collapsed view:** Module as single box with boundary signals visible
- **Expanded view:** Full internal structure shown
- **Toggle:** Double-click module header or tree view control
- **State persistence:** Save expansion state in `.shypn` document

**Use case:** Large multi-compartment model with hundreds of reactions
- Initially show only module boundaries and signal flows
- User drills down into specific compartments of interest

### 3.4 Signal Place Creation Tools
**Target:** GUI dialogs and toolbars

**Tools:**
1. **Create Signal Place:** Toolbar button or menu item
   - Dialog: Name, Type (dropdown), Scope (checkbox list of modules)
   
2. **Convert to Signal:** Right-click context menu on existing place
   - Auto-detect suggested type based on connections
   
3. **Module Assignment:** Properties panel for places/transitions
   - Dropdown to select module
   - Validation warning if arc would cross boundary

---

## Phase 4: Analysis & Insights

### 4.1 Module-Aware Analysis Tools
**Target:** `cli/analysis/` and GUI Analysis Panel

**New Analyses:**

1. **Module Connectivity Graph:**
   - Nodes = Modules
   - Edges = Signal coupling (labeled with signal names)
   - Metrics: Coupling strength (# of signals), cycle detection

2. **Module Independence Score:**
   - Measure how well modules are isolated
   - Penalty for arc violations or non-signal coupling
   - Score: 0 (monolithic) to 1 (perfect modular)

3. **Signal Flow Analysis:**
   - Trace signal propagation through module hierarchy
   - Identify bottleneck signals (high fan-out)
   - Suggest signal candidates for weakly coupled modules

4. **Compartmentalization Quality:**
   - Compare to SBML compartment definitions
   - Detect species that should be split per-compartment (ATP_c vs ATP_m)

**Output Formats:**
- GraphML export of module connectivity
- JSON report with metrics
- Visualization in GUI (network diagram of modules)

### 4.2 Module-Based Simulation Analysis
**Target:** Extend simulation tools

**Features:**
- **Per-module dynamics:** Plot concentrations grouped by compartment
- **Signal trace:** Timeline showing signal values and module responses
- **Isolation validation:** Detect if modules truly independent (parallel simulation test)

---

## Phase 5: Testing & Validation

### 5.1 Unit Tests
**Target:** `tests/` (create new test suite)

**Test Coverage:**
1. Module data model (creation, assignment, validation)
2. Signal detection heuristics (mock pathways with known signals)
3. Coupling semantics (boundary violation detection)
4. Simulation with signals (read-only behavior, broadcasting)

### 5.2 Integration Tests with SBML Models

**Test Models:**

1. **Yeast Glycolysis-TCA-OxPhos:**
   - Compartments: Cytoplasm, Mitochondria
   - Signals: ATP/ADP energy state, NADH/NAD+ redox
   - Expected: 2 modules, ~5 boundary signals
   - Source: BioModels Database (BIOMD0000000064)

2. **Eukaryotic Gene Expression:**
   - Compartments: Nucleus, Cytoplasm
   - Signals: Transcription factors, mRNA export
   - Expected: 2 modules, transcriptional regulatory signals
   - Source: BioModels (BIOMD0000000010 or similar)

3. **Bacterial Quorum Sensing (LuxI/LuxR):**
   - Compartments: Multiple cells + extracellular
   - Signals: AHL (autoinducer)
   - Expected: N+1 modules (N cells + environment)
   - Source: Original motivation for signal places

**Validation Criteria:**
- Correct module assignment from SBML compartments
- Signal places identified automatically
- No arc violations
- Simulation produces biologically plausible dynamics
- GUI renders module boundaries clearly

### 5.3 Performance Benchmarks
**Target:** Large-scale models

**Test:**
1. Load 1000+ reaction SBML model with 10+ compartments
2. Measure:
   - Module detection time
   - Rendering performance (with/without module boxes)
   - Simulation speed (compare to monolithic)
3. Goal: <5% overhead for modular architecture

---

## Phase 6: Documentation & Examples

### 6.1 User Documentation
**Target:** Update `QUICKSTART.md`, create `doc/MODULAR_ARCHITECTURE_GUIDE.md`

**Content:**
1. **Concepts:**
   - What are signal places?
   - Why modular architecture matters
   - When to use signal-mediated coupling

2. **How-To:**
   - Import multi-compartment SBML
   - Manually create modules
   - Designate signal places
   - Collapse/expand modules in GUI

3. **Examples:**
   - Metabolic compartmentalization (glycolysis/TCA)
   - Cell communication (quorum sensing)
   - Gene regulation (nucleus/cytoplasm)

### 6.2 Example Models
**Target:** `examples/modular_systems/`

**Create:**
1. `glycolysis_tca.shypn` - Energy metabolism with compartments
2. `gene_expression.shypn` - Transcriptional regulation across nucleus/cytoplasm
3. `quorum_sensing.shypn` - Multi-cellular bacterial signaling
4. `synthetic_circuit.shypn` - Minimal example showing all signal types

**Each includes:**
- Visual `.png` screenshot
- README explaining biological context
- Expected simulation behavior

### 6.3 API Documentation
**Target:** Docstrings and auto-generated docs

**Document:**
- `Module` class API
- Signal detection functions
- Coupling validation methods
- GUI components for module visualization

---

## Timeline & Dependencies

### Dependency Graph
```
Phase 1.1 (Data Model)
    ↓
Phase 1.2 (Detection) + Phase 1.3 (SBML Import)
    ↓
Phase 2.1 (Validation) + Phase 2.2 (Simulation)
    ↓
Phase 3 (Visualization) + Phase 4 (Analysis)
    ↓
Phase 5 (Testing)
    ↓
Phase 6 (Documentation)
```

### Estimated Effort
- **Phase 1:** 5-7 days (foundation is critical)
- **Phase 2:** 3-4 days (semantics well-defined in theory)
- **Phase 3:** 7-10 days (GUI work is time-intensive)
- **Phase 4:** 3-5 days (analysis builds on existing tools)
- **Phase 5:** 5-7 days (thorough testing essential)
- **Phase 6:** 2-3 days (documentation)

**Total:** ~4-6 weeks for complete integration

### Milestones
1. **Week 1:** Data model + SBML import with modules ✓
2. **Week 2:** Simulation engine + validation working
3. **Week 3-4:** GUI visualization complete
4. **Week 5:** Analysis tools + testing
5. **Week 6:** Documentation + examples

---

## Risk Mitigation

### Technical Risks

1. **Backward compatibility:**
   - **Risk:** Existing `.shypn` files break
   - **Mitigation:** Module-free models treated as single implicit module

2. **Performance:**
   - **Risk:** Module checks slow down large models
   - **Mitigation:** Cache module assignments, optimize boundary detection

3. **SBML ambiguity:**
   - **Risk:** Not all models use compartments correctly
   - **Mitigation:** Provide manual module assignment tools

### Design Risks

1. **Over-abstraction:**
   - **Risk:** Module concept too complex for users
   - **Mitigation:** Make it optional, show clear visual benefits

2. **Signal detection false positives:**
   - **Risk:** Heuristics mark regular places as signals
   - **Mitigation:** Conservative defaults, easy manual override

---

## Success Criteria

### Functional
- ✅ Import multi-compartment SBML and auto-detect modules
- ✅ Visualize module boundaries and signal places in GUI
- ✅ Simulate with correct signal semantics (read-only broadcast)
- ✅ Validate no arc violations across boundaries
- ✅ Collapse/expand modules for clarity

### Quality
- ✅ Zero regressions on existing SBML models
- ✅ <5% performance overhead
- ✅ User testing confirms intuitive interface
- ✅ 90%+ test coverage on new code

### Impact
- ✅ Enable modeling of systems previously impossible in SHYpn (multi-cellular, multi-compartment)
- ✅ Demonstrate theoretical contribution (publishable examples)
- ✅ User adoption of modular features in community models

---

## Next Immediate Actions

1. **Review current codebase:** Identify exact files needing modification
2. **Create module.py:** Start with clean data model implementation
3. **Extend Place class:** Add signal properties with tests
4. **Prototype SBML import:** Test compartment detection on yeast model
5. **Spike GUI module boxes:** Quick visualization proof-of-concept

**Start with:** Phase 1.1 (Data Model) - foundation for everything else.

---

## References

- Theoretical foundation: `doc/signal_hierarchy/SIGNAL_PLACES_MODULAR_ARCHITECTURE.md` (local)
- Public summary: `SIGNAL_HIERARCHY_THEORY.md`
- SBML specification: Sections on compartments, species, modifiers
- Existing modifier implementation: `src/shypn/services/sbml_kinetics_service.py`
