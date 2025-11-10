# Viability Panel - Knowledge Base Integration Progress

**Branch:** viability  
**Latest Commit:** 1c80583 - Phase 0.6: Add Topology Panel → Knowledge Base update hooks  
**Date:** 2025-01-XX

## Vision Statement

Build an intelligent "Master Mind" system for model repair in Shypn. The Knowledge Base aggregates information from all panels (Topology, Pathway, BRENDA, Analyses) to enable multi-domain reasoning and provide smart repair suggestions through the Viability Panel.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     VIABILITY PANEL                         │
│              (Smart Repair Suggestions UI)                  │
└─────────────────────┬───────────────────────────────────────┘
                      │ queries
                      ▼
┌─────────────────────────────────────────────────────────────┐
│              MODEL KNOWLEDGE BASE                           │
│           (Unified Intelligence Repository)                 │
│                                                             │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐   │
│  │  Structural │  │  Behavioral  │  │   Biological    │   │
│  │  Knowledge  │  │  Knowledge   │  │   Knowledge     │   │
│  │             │  │              │  │                 │   │
│  │ P-Invariants│  │  Liveness    │  │ Pathway IDs    │   │
│  │ T-Invariants│  │  Deadlocks   │  │ Compound Names │   │
│  │ Siphons     │  │  Boundedness │  │ EC Numbers     │   │
│  └─────────────┘  └──────────────┘  └─────────────────┘   │
│                                                             │
│  ┌─────────────┐  ┌──────────────┐                        │
│  │ Biochemical │  │   Dynamic    │                        │
│  │  Knowledge  │  │  Knowledge   │                        │
│  │             │  │              │                        │
│  │ Km Values   │  │ Firing Hist. │                        │
│  │ Vmax        │  │ Token Hist.  │                        │
│  │ Substrates  │  │ Bottlenecks  │                        │
│  └─────────────┘  └──────────────┘                        │
└───────▲───────▲───────▲───────▲────────────────────────────┘
        │       │       │       │
        │       │       │       │ update hooks
        │       │       │       │
┌───────┴───┐ ┌─┴───────┴┐ ┌───┴──────┐ ┌──────────────┐
│ TOPOLOGY  │ │ PATHWAY  │ │  BRENDA  │ │  SIMULATION  │
│  PANEL    │ │  PANEL   │ │  PANEL   │ │  (Future)    │
└───────────┘ └──────────┘ └──────────┘ └──────────────┘
```

---

## Completed Phases ✅

### Phase 1: Viability Panel UI
**Commit:** 3b4d8e2 + f9e8a1d (fix)  
**Files:**
- `src/shypn/ui/panels/viability/viability_panel.py` (295 lines)
- `src/shypn/helpers/viability_panel_loader.py` (295 lines)
- `src/shypn.py` (Master Palette integration)

**Features:**
- ✅ Viability Panel with DiagnosisView
- ✅ Float/attach mechanism matching topology pattern
- ✅ Master Palette button integration
- ✅ Header with title and float button
- ✅ Scrolled window for future content

---

### Phase 0: Knowledge Base Foundation
**Commits:** c5e62ba, a7f4921, 8b65ef7  
**Files:**
- `doc/viability/KNOWLEDGE_BASE_ARCHITECTURE.md` (600+ lines)
- `src/shypn/viability/knowledge/data_structures.py` (340 lines, 15 dataclasses)
- `src/shypn/viability/knowledge/knowledge_base.py` (600+ lines)

**Data Structures (15 Dataclasses):**
1. `PlaceKnowledge` - Place metadata, compound mapping, invariant membership
2. `TransitionKnowledge` - Transition metadata, reaction mapping, liveness
3. `ArcKnowledge` - Arc weights, stoichiometry
4. `PInvariant` - Place invariants (conservation laws)
5. `TInvariant` - Transition invariants (reproducible sequences)
6. `Siphon` - Siphons/traps, suggested sources
7. `PathwayInfo` - KEGG pathway metadata
8. `CompoundInfo` - KEGG compound details
9. `ReactionInfo` - KEGG reaction details
10. `KineticParams` - Km, Vmax, substrates/products
11. `SimulationTrace` - Token history, firing counts
12. `Issue` - Detected problems (multi-domain)
13. `RepairSuggestion` - Suggested fixes with confidence
14. `AnalysisContext` - Analysis state
15. `ModelMetadata` - Model-level info

**Knowledge Base API (30+ Methods):**

**Update Methods (15):**
- `update_topology_structural()` - Basic place/transition info
- `update_p_invariants()` - P-invariants from topology
- `update_t_invariants()` - T-invariants from topology
- `update_siphons_traps()` - Siphons/traps from topology
- `update_liveness()` - Liveness levels from topology
- `update_deadlocks()` - Deadlock states from topology
- `update_boundedness()` - Boundedness analysis
- `update_pathway_metadata()` - KEGG pathway mapping
- `update_compound_info()` - KEGG compound details
- `update_reaction_info()` - KEGG reaction details
- `update_kinetic_parameters()` - BRENDA Km/Vmax
- `update_simulation_trace()` - Token/firing history
- `record_issue()` - Add detected problem
- `add_repair_suggestion()` - Add suggested fix
- `clear_suggestions()` - Reset suggestions

**Query Methods (15):**
- `get_place()` - Retrieve place knowledge
- `get_transition()` - Retrieve transition knowledge
- `get_dead_transitions()` - Find dead transitions
- `get_empty_places()` - Find empty places
- `get_conserved_places()` - Get places in same invariant
- `get_compound_for_place()` - Pathway mapping lookup
- `get_reaction_for_transition()` - Pathway mapping lookup
- `get_kinetic_params()` - Get Km/Vmax for transition
- `get_transitions_in_pathway()` - Filter by pathway
- `get_issues()` - Retrieve recorded problems
- `get_suggestions()` - Retrieve repair suggestions
- `get_knowledge_summary()` - Overall KB stats
- Query methods with filters (liveness, pathway, etc.)

**Inference Methods (4 stubs):**
- `infer_initial_marking()` - Suggest tokens based on basal concentration
- `infer_arc_weight()` - Suggest stoichiometry
- `infer_firing_rate()` - Suggest rate based on Km/Vmax
- `suggest_source_placement()` - Fix empty siphons

---

### Phase 0.5: Model Lifecycle Integration
**Commit:** 053f2f3  
**Files:**
- `src/shypn/helpers/model_canvas_loader.py` (modified)
- `src/shypn/ui/panels/viability/viability_panel.py` (modified)

**Features:**
- ✅ One KB instance per model (stored in `model_canvas_loader.knowledge_bases` dict)
- ✅ Automatic KB creation in `_setup_canvas_manager()` after model load
- ✅ Automatic KB cleanup in `close_tab()` when tab closes
- ✅ Access methods: `get_current_knowledge_base()`, `get_knowledge_base(drawing_area)`
- ✅ Viability Panel KB access via `get_knowledge_base()`
- ✅ KB stored per drawing_area (tab) for isolation

**Lifecycle Flow:**
```
1. User opens model
   ├─> model_canvas_loader._setup_canvas_manager()
   ├─> manager.create_new_document()
   ├─> ModelKnowledgeBase instantiated
   └─> Stored in self.knowledge_bases[drawing_area]

2. Analyses run
   └─> Update KB via kb.update_*() methods

3. User closes tab
   ├─> model_canvas_loader.close_tab()
   ├─> del self.knowledge_bases[drawing_area]
   └─> KB garbage collected
```

---

### Phase 0.6: Topology Panel Update Hooks
**Commit:** 1c80583  
**Files:**
- `src/shypn/ui/panels/topology/base_topology_category.py` (modified)
- `src/shypn/ui/panels/topology/topology_panel.py` (modified)
- `doc/viability/PHASE_0.6_TOPOLOGY_KB_INTEGRATION_TEST.md` (test plan)

**Features:**
- ✅ `get_knowledge_base()` method in TopologyPanel and BaseTopologyCategory
- ✅ `_update_knowledge_base()` method to process analysis results
- ✅ KB updates run on GTK main thread for thread safety
- ✅ Raw analyzer output converted to KB dataclasses
- ✅ 7 analyzer types routed to KB update methods

**Data Pipeline:**

| Analyzer Type | Analyzer Output | KB Dataclass | KB Method |
|---------------|-----------------|--------------|-----------|
| `p_invariants` | `{'invariants': [{'vector': [...], 'places': [...]}]}` | `PInvariant` | `update_p_invariants()` |
| `t_invariants` | `{'invariants': [{'vector': [...], 'transitions': [...]}]}` | `TInvariant` | `update_t_invariants()` |
| `liveness` | `{'transitions': {tid: {'level': int}}}` | Dict | `update_liveness()` |
| `siphons` | `{'siphons': [{'place_ids': [...], 'is_minimal': bool}]}` | `Siphon` | `update_siphons_traps()` |
| `traps` | `{'traps': [{'place_ids': [...], 'is_minimal': bool}]}` | `Siphon` | `update_siphons_traps()` |
| `deadlocks` | `{'deadlock_states': [...], 'has_deadlocks': bool}` | List | `update_deadlocks()` |
| `boundedness` | `{'bounded': bool, 'bounds': {...}}` | Dict | `update_boundedness()` |

**Console Output:**
```
✓ Knowledge Base updated: 3 P-invariants
✓ Knowledge Base updated: 2 T-invariants
✓ Knowledge Base updated: Liveness for 5 transitions
✓ Knowledge Base updated: 1 siphons
✓ Knowledge Base updated: Boundedness
```

---

## Pending Phases 🔧

### Phase 0.7: Pathway Panel Integration
**Status:** Not started  
**Goal:** Connect Pathway Panel to KB

**Tasks:**
1. Add `get_knowledge_base()` to PathwayPanel
2. Hook pathway metadata updates: `kb.update_pathway_metadata()`
3. Hook compound info: `kb.update_compound_info()`
4. Hook reaction info: `kb.update_reaction_info()`

**Data to Capture:**
- Place ID → Compound ID mapping
- Compound names, formulas, molecular weight
- Reaction names, EC numbers, equation
- Pathway context (glycolysis, TCA, etc.)

---

### Phase 0.8: BRENDA Panel Integration
**Status:** Not started  
**Goal:** Connect BRENDA kinetic data to KB

**Tasks:**
1. Add `get_knowledge_base()` to BRENDAPanel
2. Hook kinetic parameter updates: `kb.update_kinetic_parameters()`

**Data to Capture:**
- Transition ID → EC number mapping
- Km values (substrate → value)
- Vmax values
- Substrate/product lists

---

### Phase 0.9: Complete Integration Test
**Status:** Not started  
**Goal:** Test full multi-domain data flow

**Test Scenario:**
1. Load SBML model (e.g., glycolysis)
2. Run Topology analyses (P-invariants, Liveness, etc.)
3. Load Pathway mappings (KEGG)
4. Query BRENDA for kinetic parameters
5. Open Viability Panel
6. Verify KB has data from all 3 domains

**Multi-Domain Query Example:**
```python
kb = self.model_canvas.get_current_knowledge_base()

# Find dead transition
dead_transitions = kb.get_dead_transitions()
for tid in dead_transitions:
    trans = kb.get_transition(tid)
    
    # Domain 1: Topology
    print(f"Transition {tid}: Liveness = {trans.liveness_level}")
    
    # Domain 2: Pathway
    reaction = kb.get_reaction_for_transition(tid)
    print(f"  Reaction: {reaction.name} ({reaction.ec_number})")
    
    # Domain 3: BRENDA
    kinetics = kb.get_kinetic_params(tid)
    print(f"  Km: {kinetics.km_values}, Vmax: {kinetics.vmax}")
    
    # Inference: Why is it dead?
    marking = kb.infer_initial_marking(place_id)
    print(f"  Suggestion: Increase tokens in upstream places")
```

---

### Phase 2: Inference Engines
**Status:** Not started (stubs exist)  
**Goal:** Implement multi-domain reasoning

**Methods to Implement:**

1. **`infer_initial_marking(place_id)`**
   - Check if place is empty (Topology)
   - Get compound basal concentration (BRENDA)
   - Suggest token value based on concentration range
   - Confidence: High if BRENDA data exists

2. **`suggest_source_placement(siphon)`**
   - Identify empty siphon (Topology)
   - Get compounds in siphon (Pathway)
   - Find source compounds from KEGG (Pathway)
   - Suggest adding source transition
   - Confidence: High if source compound identified

3. **`infer_firing_rate(transition_id)`**
   - Check if transition is dead (Topology)
   - Get Km/Vmax from BRENDA (Biochemical)
   - Check substrate availability (Topology + Pathway)
   - Suggest rate adjustment
   - Confidence: Medium (depends on substrate levels)

4. **`infer_arc_weight(arc_id)`**
   - Check stoichiometry from reaction equation (Pathway)
   - Compare to current arc weight (Topology)
   - Suggest correction if mismatch
   - Confidence: High (direct from KEGG equation)

**Example Inference Chain:**
```
Problem: Transition T5 is dead
   ↓
Query 1: What is T5's liveness? (Topology) → "dead"
   ↓
Query 2: What reaction is T5? (Pathway) → "Hexokinase (EC 2.7.1.1)"
   ↓
Query 3: What are T5's substrates? (Pathway) → "Glucose, ATP"
   ↓
Query 4: Which places represent substrates? (Pathway) → "P1 (Glucose), P2 (ATP)"
   ↓
Query 5: What are token levels? (Topology) → "P1: 0 tokens, P2: 5 tokens"
   ↓
Query 6: What is basal glucose concentration? (BRENDA) → "5.0 mM"
   ↓
Inference: P1 (Glucose) is empty but should have ~5 tokens
   ↓
Suggestion: "Set initial marking of P1 to 5 tokens (basal glucose concentration)"
Confidence: 0.85 (high - based on BRENDA data)
```

---

## File Structure

```
src/shypn/
├── viability/
│   ├── __init__.py
│   └── knowledge/
│       ├── __init__.py
│       ├── data_structures.py     # 15 dataclasses (340 lines)
│       └── knowledge_base.py      # ModelKnowledgeBase (600+ lines)
│
├── ui/panels/viability/
│   ├── __init__.py
│   └── viability_panel.py         # ViabilityPanel UI (295 lines)
│
├── helpers/
│   ├── model_canvas_loader.py     # KB lifecycle integration (modified)
│   └── viability_panel_loader.py  # Float/attach mechanism (295 lines)
│
└── ui/panels/topology/
    ├── topology_panel.py           # KB access (modified)
    └── base_topology_category.py   # KB update hooks (modified)

doc/viability/
├── KNOWLEDGE_BASE_ARCHITECTURE.md  # Architecture design (600+ lines)
├── PHASE_0.6_TOPOLOGY_KB_INTEGRATION_TEST.md  # Test plan
└── PROGRESS_SUMMARY.md             # This file
```

---

## Commit History

```bash
git log --oneline viability
```

**Expected (8 commits on viability branch):**
```
1c80583 Phase 0.6: Add Topology Panel → Knowledge Base update hooks
053f2f3 Phase 0.5: Integrate Knowledge Base with model lifecycle
8b65ef7 Phase 0: Implement ModelKnowledgeBase foundation
a7f4921 Phase 0: Add Knowledge Base data structures
c5e62ba Phase 0: Create Knowledge Base architecture document
f9e8a1d Fix viability panel loader to match topology pattern
3b4d8e2 Phase 1: Implement Viability Panel UI foundation
... (previous commits on main)
```

---

## Metrics

**Lines of Code Added:**
- Knowledge Base: ~1,000 lines (data_structures.py + knowledge_base.py)
- Viability Panel: ~590 lines (viability_panel.py + loader)
- Integration: ~150 lines (modifications to model_canvas_loader, topology panel)
- Documentation: ~1,500 lines (architecture + test plans)
- **Total: ~3,240 lines**

**Test Coverage:**
- Phase 1 (UI): ✅ Tested (float/attach works)
- Phase 0 (KB Foundation): ✅ Tested (imports, instantiation)
- Phase 0.5 (Lifecycle): ✅ Tested (KB per model works)
- Phase 0.6 (Topology→KB): 🔧 Ready for testing

---

## Next Immediate Steps

1. **Test Phase 0.6:** Load model, verify console shows "✓ Knowledge Base updated" messages
2. **Fix Issues:** Debug any KB update failures
3. **Phase 0.7:** Add Pathway Panel → KB hooks
4. **Phase 0.8:** Add BRENDA Panel → KB hooks
5. **Phase 0.9:** Complete integration test (all domains)
6. **Phase 2:** Implement inference engines

---

## Success Criteria for Complete System

✅ **When We Can Say "Viability Panel Works":**

1. User opens model with issues (e.g., dead transitions, empty places)
2. Topology, Pathway, BRENDA analyses auto-populate KB
3. User clicks "Diagnose" in Viability Panel
4. Viability Panel queries KB across all domains
5. System generates repair suggestions:
   - "Transition T5 (Hexokinase) is dead because Place P1 (Glucose) is empty"
   - "Suggestion: Set initial marking of P1 to 5 tokens (basal concentration: 5.0 mM)"
   - "Confidence: 85% (based on BRENDA data)"
6. User applies suggestion → Model now viable

---

**Status:** 🚀 Phase 0.6 Complete, Ready to Test  
**Next Milestone:** Phase 0.7 - Pathway Panel Integration  
**Target:** Multi-domain intelligent model repair by end of Phase 2
