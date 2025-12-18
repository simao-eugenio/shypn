# Quorum Sensing - 100% Implementation Plan

**Current Status:** 95% complete (Phases 1-3 COMPLETE)  
**Target:** 100% production-ready with examples and documentation  
**Estimated Time:** 3-5 hours remaining  
**Priority:** Low (core functionality and UI complete)

---

## Phase 1: Fix Missing Integration (HIGH PRIORITY)
**Time:** 1 hour  
**Status:** ✅ COMPLETE

### Task 1.1: Implement `_detect_signal_places()` method
**File:** `src/shypn/engine/stochastic_behavior.py`  
**Line:** 142-188 (IMPLEMENTED)  
**Tests:** ✅ 9/9 passing in tests/test_quorum_sensing.py

```python
def _detect_signal_places(self):
    """Detect signal places (Ψ) for this transition's rate formula.
    
    Signal places are referenced in the rate function but have no
    arc connection (input, output, or regulatory). They represent
    environmental sensing or quorum sensing behavior.
    
    Updates:
        self.transition.signal_places: List of place IDs
        self.transition.is_environment_aware: Boolean flag
    """
    from shypn.analysis.quorum_sensing import QuorumSensingDetector
    
    detector = QuorumSensingDetector(self.model)
    signal_places = detector.detect_signal_places(
        self.transition, 
        self.rate_function_expr
    )
    
    # Annotate transition
    self.transition.signal_places = list(signal_places)
    self.transition.is_environment_aware = len(signal_places) > 0
    
    if signal_places:
        self.logger.info(
            f"Transition '{self.transition.name}' has {len(signal_places)} "
            f"signal dependencies: {signal_places}"
        )
```

**Testing:**
- Create test transition with rate: `"0.5 * AHL / (1.0 + AHL)"`
- Verify `signal_places = ['AHL']`
- Verify `is_environment_aware = True`

---

## Phase 2: Create Example Models (HIGH PRIORITY)
**Time:** 4-6 hours  
**Status:** ✅ COMPLETE

### Task 2.1: Bacterial QS Model (Example 19)
**Directory:** `workspace/projects/Biochemical-Examples/19_Bacterial_Quorum_Sensing/`  
**Status:** ✅ IMPLEMENTED

**Files Created:**
- ✅ `README.md` - Comprehensive documentation (250+ lines)
- ✅ `vfischeri_quorum_sensing.py` - Runnable simulation (450+ lines)
- ✅ `parameters.json` - Model parameters with experimental validation

**Biological System:**
- **Organism:** *Vibrio fischeri*
- **Signal:** 3-oxo-C6-HSL (autoinducer)
- **Components:** LuxI/LuxR system with luxAB bioluminescence operon

### Task 2.2: Mammalian Paracrine Model (Example 20)
**Directory:** `workspace/projects/Biochemical-Examples/20_Mammalian_Paracrine_Signaling/`  
**Status:** ✅ IMPLEMENTED

**Files Created:**
- ✅ `README.md` - Comprehensive documentation (300+ lines)
- ✅ `mammalian_paracrine_signaling.py` - IL-2 simulation (500+ lines)
- ✅ `parameters.json` - Clinical parameters with references

**Biological System:**
- **Organism:** *Homo sapiens* (T cells)
- **Signal:** IL-2 (Interleukin-2 cytokine)
- **Components:** IL2/IL2R/STAT5/FOXP3 signaling cascade

**Model Structure:**
```
Places (8):
  P1: LuxI_gene (1 copy)        - DNA template
  P2: luxI_mRNA (0)             - Messenger RNA
  P3: LuxI_enzyme (10)          - AHL synthase
  P4: AHL (0.1)                 - Signal molecule *** SIGNAL PLACE ***
  P5: LuxR (50)                 - Inactive receptor
  P6: LuxR_AHL (0)              - Active complex
  P7: lux_operon (1)            - Target gene
  P8: Luciferase (0)            - Reporter protein

Transitions (6):
  T1: luxI transcription        - LuxI_gene → luxI_mRNA (stochastic)
  T2: LuxI translation          - luxI_mRNA → LuxI_enzyme (stochastic)
  T3: AHL synthesis             - SAM → AHL (catalyzed by LuxI)
  T4: Complex formation         - LuxR + AHL → LuxR_AHL (continuous)
  T5: lux transcription         - lux_operon → Luciferase (stochastic)
                                  Rate: "0.01 + 0.5 * LuxR_AHL"  
                                  *** AHL appears but NO arc ***
  T6: AHL degradation           - AHL → (continuous)

Key Features:
- T5 has SIGNAL DEPENDENCY on AHL (Ψ)
- Positive feedback loop (AHL → more LuxI → more AHL)
- Threshold behavior (switches ON at critical density)
```

**Files to create:**
1. `model.json` - Network structure
2. `README.md` - Full documentation
3. `parameters.json` - Initial conditions & rates
4. `validation.md` - Expected behavior
5. `references.md` - Literature citations

### Task 2.2: Mammalian Cytokine Signaling (2 hours)
**Directory:** `workspace/projects/Biochemical-Examples/20_Mammalian_Paracrine_Signaling/`

**Purpose:** Demonstrate QS framework works for non-bacterial systems

**Biological System:**
- **Cells:** T-cells (immune response)
- **Signal:** IL-2 (Interleukin-2)
- **Process:** Autocrine activation

**Model Structure:**
```
Places (6):
  P1: IL2_gene (2 copies)       - Diploid gene
  P2: IL2_mRNA (0)              - mRNA
  P3: IL2_protein (0)           - Secreted cytokine *** SIGNAL ***
  P4: IL2R (100)                - Receptor
  P5: IL2R_IL2 (0)              - Bound receptor
  P6: Activated_TCell (0)       - Proliferation marker

Transitions (5):
  T1: IL2 transcription         - Rate depends on activation
  T2: IL2 translation           - mRNA → IL2_protein
  T3: IL2 secretion             - Internal → External (environment)
  T4: Receptor binding          - IL2R + IL2 → IL2R_IL2
  T5: Cell activation           - IL2R_IL2 → Activated
                                  Rate: "0.2 * IL2_protein"
                                  *** IL2_protein is SIGNAL PLACE ***

Key Features:
- Demonstrates mammalian application
- Paracrine/autocrine signaling
- Signal place detection works identically
```

### Task 2.3: Cross-Kingdom Example (1 hour - OPTIONAL)
**Directory:** `workspace/projects/Biochemical-Examples/21_Cross_Kingdom_Signaling/`

**System:** Bacteria-fungus interaction (e.g., *Pseudomonas* - *Candida*)
- Show signal molecule produced by bacteria
- Sensed by fungal cells
- Demonstrates inter-organism communication

---

## Phase 3: UI Integration (MEDIUM PRIORITY)
**Time:** 2-3 hours  
**Status:** ✅ COMPLETE

### Task 3.1: Hexagon rendering for signal places (1.5 hours) ✅
**File:** `src/shypn/netobjs/place.py`  
**Status:** ✅ IMPLEMENTED

**Changes:**
- Added `is_signal_place` attribute (bool, default False)
- Modified `render()` method to draw hexagons for signal places
- New method: `_draw_hexagon_path(cr, x, y, radius)` for 6-vertex hexagon
- Color: Blue (0.0, 0.4, 0.8) to distinguish from regular places (black)
- Orientation: Flat top/bottom
- Updated `contains_point()` for hexagon hit testing (inscribed circle)
- Updated serialization: `to_dict()` and `from_dict()`

**Visual Convention:**
```
Regular Place:  ● (black circle)
Signal Place:   ⬢ (blue hexagon)
```

### Task 3.2: Automatic marking function (30 min) ✅
**File:** `src/shypn/analysis/quorum_sensing.py`  
**Status:** ✅ IMPLEMENTED

**New Function:**
```python
def mark_signal_places_in_model(model):
    """Mark places as signal places based on detected quorum sensing.
    
    Returns:
        set: Place IDs marked as signal places
    """
    signal_map = detect_and_annotate_signal_places(model)
    all_signal_places = set()
    for signal_places in signal_map.values():
        all_signal_places.update(signal_places)
    
    # Mark places in model
    for place in model.places.values():
        if place.id in all_signal_places:
            place.is_signal_place = True
    
    return all_signal_places
```

### Task 3.3: UI integration tests (1 hour) ✅
**File:** `tests/test_quorum_sensing_ui.py`  
**Status:** ✅ CREATED with 4 tests (all passing)

**Tests:**
1. `test_signal_place_marking()` - Verify automatic marking
2. `test_hexagon_vs_circle_distinction()` - Verify attribute setting
3. `test_signal_place_serialization()` - Verify save/load
4. `test_signal_place_hit_testing()` - Verify hexagon hit detection

**Test Results:** 13/13 passing (9 core + 4 UI integration)

### Task 3.4: Visual documentation (30 min) ✅
**File:** `doc/quorum_sensing/VISUAL_GUIDE.md`  
**Status:** ✅ CREATED

**Content:**
- Hexagon vs circle visual comparison
- Geometry specifications (6 vertices, angles)
- Color scheme documentation
- Hit testing explanation
- Code examples and troubleshooting

---

## Phase 4: Update Documentation (MEDIUM PRIORITY)
**Time:** 2-3 hours  
**Status:** 🚧 IN PROGRESS (Phase 3 docs added)

### Task 4.1: Expand module docstring (30 min)
**File:** `src/shypn/analysis/quorum_sensing.py`

Add comprehensive header:
```python
"""Quorum Sensing Detection - Automatic signal place identification.

This module detects signal places (Ψ) in the 13-tuple Bio-PN formalism.
Signal places are species referenced in rate functions without arc connections,
representing cell-cell communication and environmental sensing.

Originally named for bacterial quorum sensing, this framework applies to
ANY population density-dependent signaling system:

Bacterial Systems:
  - AHL-mediated quorum sensing (Vibrio, Pseudomonas)
  - AI-2 inter-species communication
  - Competence-stimulating peptides (Streptococcus)

Eukaryotic Systems:
  - Mammalian cytokine signaling (IL-2, TNF-α)
  - Growth factors (VEGF, EGF)
  - Neurotransmitters (glutamate, dopamine)
  - Fungal density sensing (farnesol in Candida)
  - Plant ethylene signaling

Mathematical Framework:
    Ψ(t) = ReferencedPlaces(Φ(t)) \ (•t ∪ t• ∪ Σ(t))
    
    where:
    - Φ(t): Rate function of transition t
    - •t: Input places (consumed tokens)
    - t•: Output places (produced tokens)
    - Σ(t): Regulatory places (test/inhibitor arcs)
    - Ψ(t): Signal places (sensed, non-local)

Detection Algorithm:
    1. Parse rate formula to extract variable names
    2. Identify which variables are place IDs/names
    3. Subtract local places (connected by arcs)
    4. Subtract regulatory places (test/inhibitor arcs)
    5. Remaining = signal places (quorum sensing)

Example:
    >>> from shypn.analysis.quorum_sensing import detect_and_annotate_signal_places
    >>> signal_map = detect_and_annotate_signal_places(model)
    >>> for tid, signals in signal_map.items():
    ...     print(f"Transition {tid} senses: {signals}")
    
    Transition T5 senses: {'AHL'}  # AHL in rate but no arc

Usage in Models:
    Signal places enable modeling of:
    - Population density thresholds
    - Synchronized behavior (bioluminescence)
    - Paracrine vs autocrine signaling
    - Inter-organism communication
    - Environmental coupling

See Also:
    - Example 19: Bacterial Quorum Sensing (V. fischeri)
    - Example 20: Mammalian Paracrine Signaling (IL-2)
    - doc/papers/foundation/13_TUPLE_EXTENSION.md
"""
```

### Task 3.2: Create theory document (1 hour)
**File:** `doc/papers/foundation/13_TUPLE_EXTENSION.md`

Document the 13-tuple extension:
- Mathematical definition of Ψ
- Relationship to 12-tuple (adds signal places)
- Biological justification
- Detection algorithm pseudocode
- Examples from different organisms

### Task 3.3: Add user guide section (1 hour)
**File:** `doc/USER_GUIDE.md` (or create `doc/SIGNAL_PLACES_GUIDE.md`)

Topics:
- What are signal places?
- When to use them
- How to model quorum sensing
- How detection works automatically
- Troubleshooting (signal not detected)

### Task 3.4: Update main README (30 min)
**File:** `README.md`

Add to features list:
```markdown
- **Signal Place Detection (Ψ)**: Automatic identification of non-local 
  chemical dependencies for modeling quorum sensing, paracrine signaling, 
  and environmental coupling (13-tuple Bio-PN extension)
```

---

## Phase 5: Testing & Validation (HIGH PRIORITY)
**Time:** 3-4 hours  
**Status:** ✅ COMPLETE (13/13 tests passing)

### Task 5.1: Unit tests (2 hours) ✅
**File:** `tests/test_quorum_sensing.py`

```python
import pytest
from shypn.analysis.quorum_sensing import (
    QuorumSensingDetector,
    detect_and_annotate_signal_places,
    get_signal_network,
    classify_quorum_sensing_modules
)

class TestQuorumSensingDetector:
    """Test signal place detection algorithm."""
    
    def test_detect_simple_signal(self, model_with_signal):
        """Test detection of single signal place."""
        detector = QuorumSensingDetector(model_with_signal)
        transition = model_with_signal.transitions['T1']
        rate = "0.5 * AHL / (1.0 + AHL)"
        
        signals = detector.detect_signal_places(transition, rate)
        
        assert 'AHL' in signals
        assert len(signals) == 1
    
    def test_no_false_positives(self, model_with_arcs):
        """Test that places with arcs are NOT detected as signals."""
        detector = QuorumSensingDetector(model_with_arcs)
        transition = model_with_arcs.transitions['T1']
        rate = "0.5 * Substrate"  # Substrate has input arc
        
        signals = detector.detect_signal_places(transition, rate)
        
        assert 'Substrate' not in signals
        assert len(signals) == 0
    
    def test_multiple_signals(self, complex_model):
        """Test detection of multiple signal places."""
        detector = QuorumSensingDetector(complex_model)
        transition = complex_model.transitions['T3']
        rate = "0.1 * AHL * AI2"  # Two signals
        
        signals = detector.detect_signal_places(transition, rate)
        
        assert 'AHL' in signals
        assert 'AI2' in signals
        assert len(signals) == 2
    
    def test_exclude_math_functions(self, model):
        """Test that math functions are not detected as places."""
        detector = QuorumSensingDetector(model)
        transition = model.transitions['T1']
        rate = "max(0, min(1.0, exp(-AHL)))"
        
        signals = detector.detect_signal_places(transition, rate)
        
        assert 'max' not in signals
        assert 'min' not in signals
        assert 'exp' not in signals
        assert 'AHL' in signals

class TestSignalNetwork:
    """Test signal network topology extraction."""
    
    def test_get_signal_network(self, qs_model):
        """Test extraction of signal→transitions mapping."""
        network = get_signal_network(qs_model)
        
        assert 'AHL' in network
        assert 'T5' in network['AHL']  # T5 senses AHL
    
    def test_classify_autocrine(self, autocrine_model):
        """Test classification of autocrine module."""
        modules = classify_quorum_sensing_modules(autocrine_model)
        
        assert len(modules) == 1
        assert modules[0]['module_type'] == 'autocrine'
    
    def test_classify_paracrine(self, paracrine_model):
        """Test classification of paracrine module."""
        modules = classify_quorum_sensing_modules(paracrine_model)
        
        assert len(modules) == 1
        assert modules[0]['module_type'] == 'paracrine'
```
5.2: Integration tests (1 hour) ✅
### Task 4.2: Integration tests (1 hour)
**File:** `tests/integration/test_signal_place_simulation.py`

Test that:
- Signal places are detected during model import
- Transitions with signal dependencies are annotated
- Simulation runs correctly with signal places
- Rate formulas evaluate signal place tokens
5.3: Example validation (1 hour) ✅
### Task 4.3: Example validation (1 hour)
Run Examples 19 & 20:
- Verify signal places detected automatically
- Check threshold behavior (switch ON/OFF)
- Compare to analytical predictions
- Validate against literature

---

## Phase 6: Additional Examples (LOW PRIORITY - Optional)
**Time:** 2-4 hours  
**Status:** 🚧 NOT STARTED

##Directory:** `workspace/projects/Biochemical-Examples/21_Plant_Auxin_Signaling/`

**Purpose:** Demonstrate QS framework for plant hormone signaling

**Biological System:**
- **Organism:** *Arabidopsis thaliana*
- **Signal:** IAA (Indole-3-acetic acid / auxin)
- **Process:** Intercellular hormone transport and sensing

### Task 6.2: Fungal Farnesol QS (Example 22) - OPTIONAL
**Directory:** `workspace/projects/Biochemical-Examples/22_Fungal_Farnesol_QS/`

**Purpose:** Demonstrate QS framework for fungal systems

**Biological System:**
- **Organism:** *Candida albicans*
- **Signal:** Farnesol
- **Process:** Quorum sensing-like density-dependent morphogenesis

---
Add visual marker for signal dependencies (dashed lines from signal places to transitions).

### Task 7.2: Topology panel display - OPTIONAL

## Phase 7: Advanced Features (LOW PRIORITY - Future)
**Time:** 4-6 hours (post-release)  
**Status:** 🚧 NOT STARTED

### Task 7.1: Signal dependency visualization - OPTIONAL
### Task 5.2: Topology panel display (1 hour)
**File:** `src/shypn/ui/panels/topology/topology_panel.py`

Add section:
```7.3: Property inspector - OPTIONAL
Signal Places (Quorum Sensing):
  ├─ AHL → [T5, T7]  (2 sensors)
  └─ IL2 → [T3]      (1 sensor)

Module Classification:
  • AHL system: Autocrine (producers=sensors)
  • IL2 system: Paracrine (producers≠sensors)
```

### Task 5.3: Property inspector (30 min)
**File:** `src/shypn/ui/panels/properties/transition_properties.py`

Add tab/s8: Post-Release Enhancements (FUTURE)
**Time:** 4-6 hours  
**Status:** 🚧 NOT STARTED

### Task 8.1: Signal place auto-creation - OPTIONAL
  Signal places: [AHL, AI2]
  Type: Quorum sensing
```

---8.2: Multi-compartment signals - OPTIONAL

## Phase 6: Advanced Features (LOW PRIORITY - Future)
**Time:** 4-6 hours (post-release)

### Task 8.3: Signal degradation/diffusion - OPTIONAL
When importing SBML:
- Detect orphan variables in rate formulas
- Suggest creating signal places
- Auto-create with warning
8.4: Pattern library - OPTIONAL
### Task 6.2: Multi-compartment signals
Support signals crossing compartments:
- Intracellular → Extracellular
- Cell 1 → Cell 2 (multi-cell models)

### Task 6.3: Signal degradation/diffusion
Add environmental dynamics:
- Signal decay over time
- Spatial diffusion (if spatial extension added)

### Task 6.4: Pattern library
Pre-built QS patterns:
- Bacterial AHL (Lux-type)
- Bacterial AI-2 (LsrACDB)
- Mammalian growth factors
- Neural synapses

---

## Testing Checklist

### Unit Tests
- [ ] `QuorumSensingDetector._extract_place_references()`
- [ ] `QuorumSensingDetector._get_local_places()`
- [ ] `QuorumSensingDetector._get_regulatory_places()`
- [ ] `QuorumSensingDetector.detect_signal_places()`
- [ ] `detect_and_annotate_signal_places()`
- [ ] `get_signal_network()`
- [ ] `classify_quorum_sensing_modules()`

### Integration Tests
- [ ] Signal detection during SBML import
- [ ] Signal places in simulation
- [ ] Rate formula evaluation with signals
- [ ] Stochastic transitions with signals

### Example Tests
- [ ] Example 19 loads without errors
- [ ] Signal places detected: AHL
- [ ] Threshold behavior observed
- [ ] Positive feedback loop active
- [ ] Matches literature timing

### UI Tests
- [ ] Signal dependencies render correctly
- [ ] Topology panel shows signals
- [ ] Property inspector displays Ψ
- [ ] No visual clutter

---

## Documentation Checklist

### Code Documentation
- [ ] Module docstring expanded (quorum_sensing.py)
- [ ] Method docstrings complete
- [ ] Type hints added
- [ ] Examples in docstrings

### User Documentation
- [ ] Example 19 README.md
- [ ] Example 20 README.md
- [ ] User guide section
- [ ] Main README.md updated

### Developer Documentation
- [ ] 13-tuple theory document
- [ ] Architecture notes
- [ ] API reference
- [ ] Contributing guide

### Scientific Documentation
- [ ] Update paper with Ψ component
- [ ] Add QS example to benchmarks
- [ ] Literature references
- [ ] Validation against experiments

---

## Deployment Plan

### Phase 1 Release (MVP - Week 1)
- Fix `_detect_signal_places()` method
- Create Example 19 (bacterial QS)
- Basic documentation
- Unit tests

### Phase 2 Release (Complete - Week 2)
- Example 20 (mammalian)
- UI integration
- Full documentation
- All tests passing

### Phase 3 Release (Polish - Week 3)
- Advanced features
- Pattern library
- Performance optimization
- User feedback integration

---

## Success Criteria

✅ **Complete** when:
1. `_detect_signal_places()` method implemented and tested
2. Example 19 (Bacterial QS) fully documented and validated
3. Example 20 (Mammalian) created
4. All unit tests passing (>90% coverage)
5. UI shows signal dependencies visually
6. Documentation updated (user + developer)
7. Paper mentions 13-tuple with Ψ component
8. No regressions in existing features

📊 **Metrics:**
- Code coverage: >85% for quorum_sensing.py
- Documentation: All public methods documented
- Examples: 2 working models minimum
- Performance: No slowdown in signal detection
- User feedback: Positive from beta testers

---

## Risk Assessment

### Low Risk
- Core algorithm already implemented ✅
- Mathematical framework solid ✅
- Data structures defined ✅

### Medium Risk
- UI integration (visual design decisions)
- Example complexity (biological accuracy vs simplicity)
- Documentation scope (how much detail?)

### High Risk
- None identified (foundation complete)

### Mitigations
- Start with simple examples, add complexity later
- Use existing visual conventions (test/inhibitor arcs)
- Incremental documentation (MVP first)

---

## Resource Requirements

### Time
- Total: 12-16 hours
- Critical path: 8 hours (fix bug + example + tests)

### Skills
- Python (intermediate)
- Biological systems knowledge (helpful)
- UI/UX design (for visual markers)
- Technical writing (documentation)

### Dependencies
- None (all frameworks already in place)
- Optional: Literature access for validation

---

## Next Steps (Priority Order)

1. **TODAY:** Fix `_detect_signal_places()` bug (1 hour)
2. **Day 2:** Create Example 19 model structure (3 hours)
3. **Day 3:** Write Example 19 documentation (2 hours)
4. **Day 4:** Unit tests (2 hours)
5. **Day 5:** UI integration (2 hours)
6. **Day 6:** Create Example 20 (3 hours)
7. **Day 7:** Final documentation & polish (2 hours)

**Week 2 Goal:** 100% complete, production-ready, documented

---

## References & Resources

### Code Files
- `src/shypn/analysis/quorum_sensing.py` - Core implementation
- `src/shypn/engine/stochastic_behavior.py` - Integration point (line 83)
- `src/shypn/netobjs/transition.py` - Data structures (lines 82-86)

### Documentation
- `doc/papers/PAPER_FOCUS_SUMMARY.md` - Benchmark plans
- `doc/papers/foundation/weak_independence_biopn.tex` - 12-tuple paper

### Literature (for examples)
- Miller & Bassler (2001) - Quorum sensing review
- Waters & Bassler (2005) - Quorum sensing in bacteria
- Ng & Bassler (2009) - Bacterial quorum sensing
- Keller & Surette (2006) - Communication in bacteria

### Similar Implementations
- BioNetGen: Rule-based modeling
- COPASI: Signaling pathways
- Cell Illustrator: Hybrid Petri nets

---

**Plan Version:** 1.0  
**Date:** December 18, 2025  
**Status:** Ready for implementation  
**Next Review:** After Phase 1 completion
