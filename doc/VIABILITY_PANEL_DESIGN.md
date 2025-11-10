# Viability Panel - Intelligent Model Repair Assistant

**Status:** Design Phase  
**Priority:** High - Critical missing feature  
**Target:** Version 3.0  
**Branch:** `viability`

---

## Executive Summary

### The Problem

Shypn currently excels at:
- ✅ Loading biological models (SBML, KEGG)
- ✅ Inferring kinetic parameters (BRENDA integration)
- ✅ Simulating dynamics (token game, time evolution)
- ✅ Analyzing topology (structural, graph, behavioral properties)
- ✅ Generating reports for publication

**Critical Gap:** When a model has structural or semantic issues (deadlocks, dead transitions, unbounded places), Shypn can **detect** them but cannot **fix** them.

Users are left to manually:
- Interpret topology analysis results
- Guess appropriate initial markings
- Trial-and-error arc weights
- Apply Petri net theory knowledge to repair models

### The Solution: Viability Panel

A **6th major panel** that acts as an intelligent assistant to:

1. **Diagnose** structural, semantic, and behavioral issues
2. **Suggest** concrete fixes with explanations
3. **Apply** changes automatically or interactively
4. **Validate** that fixes actually resolve the issues

**Goal:** Make any model "alive" - ensure all transitions can fire, no deadlocks, bounded behavior, and biological plausibility.

---

## Vision Statement

> "Transform Shypn from a model **analyzer** into a model **optimizer** - the first Petri net tool that doesn't just report problems, but actively helps you fix them."

---

## User Stories

### Story 1: Beginner User
**As a** biology student with limited Petri net knowledge  
**I want** automated suggestions to fix my model  
**So that** I can focus on biological accuracy, not mathematical theory

**Scenario:**
1. Import SBML model from database
2. Open Viability Panel
3. See "🔴 Critical: Dead transition T5 - never fires"
4. Click "Show Fixes"
5. See "Add 1 token to place P3" with explanation
6. Click "Apply" and see T5 highlighted as now live
7. Re-run analysis to confirm fix

---

### Story 2: Expert User
**As a** Petri net researcher  
**I want** algorithmic repair suggestions based on classical theory  
**So that** I can quickly prototype liveness-enforcing supervisors

**Scenario:**
1. Create custom model with complex dependencies
2. Topology analysis detects "Blocked siphon {P2, P5, P8}"
3. Viability Panel suggests: "Add monitor place PM with trap structure"
4. Preview shows the exact arcs to add
5. Apply and verify deadlock-freedom proven

---

### Story 3: Batch Processing
**As a** computational biologist  
**I want** to auto-repair 100+ models from BioModels database  
**So that** I can analyze them without manual intervention

**Scenario:**
1. Load model batch
2. Enable "Auto-Pilot Mode" in Viability Panel
3. Set constraints: "Only safe fixes, no element deletion"
4. Run batch repair
5. Export success/failure report with applied changes

---

## Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     VIABILITY PANEL                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────┐  ┌──────────────────┐              │
│  │  Diagnosis       │  │  Suggestion      │              │
│  │  Engine          │→ │  Engine          │              │
│  │                  │  │                  │              │
│  │ • Topology data  │  │ • Rule-based     │              │
│  │ • Simulation     │  │ • Algorithmic    │              │
│  │ • Constraints    │  │ • ML (future)    │              │
│  └──────────────────┘  └──────────────────┘              │
│           │                      │                         │
│           └──────────┬───────────┘                         │
│                      ↓                                     │
│           ┌─────────────────────┐                         │
│           │  Repair Actions     │                         │
│           │                     │                         │
│           │ • Modify M₀         │                         │
│           │ • Add/modify arcs   │                         │
│           │ • Change weights    │                         │
│           │ • Set policies      │                         │
│           └─────────────────────┘                         │
│                      │                                     │
│                      ↓                                     │
│           ┌─────────────────────┐                         │
│           │  Validation         │                         │
│           │                     │                         │
│           │ • Re-analyze        │                         │
│           │ • Verify fixes      │                         │
│           │ • Track changes     │                         │
│           └─────────────────────┘                         │
└─────────────────────────────────────────────────────────────┘
```

---

### Data Flow

```
INPUT SOURCES:
┌──────────────────┐
│ Topology Panel   │ → Structural issues (siphons, dead nodes, boundedness)
└──────────────────┘
┌──────────────────┐
│ Dynamic Analyses │ → Behavioral issues (deadlocks, reachability)
└──────────────────┘
┌──────────────────┐
│ Model Canvas     │ → Current structure (places, transitions, arcs)
└──────────────────┘
┌──────────────────┐
│ BRENDA/Kinetics  │ → Biological constraints (rate ranges, feasibility)
└──────────────────┘

                ↓
         
    ┌──────────────────┐
    │ DIAGNOSIS ENGINE │
    └──────────────────┘
                ↓
         Issue Database
         (prioritized)
                ↓
    ┌──────────────────┐
    │ SUGGESTION ENGINE│
    └──────────────────┘
                ↓
         Fix Proposals
         (ranked)
                ↓
    ┌──────────────────┐
    │ USER INTERACTION │ → Manual/Auto/Wizard mode
    └──────────────────┘
                ↓
         
OUTPUT ACTIONS:
┌──────────────────┐
│ Model Canvas     │ ← Apply structural changes
└──────────────────┘
┌──────────────────┐
│ Topology Panel   │ ← Trigger re-analysis
└──────────────────┘
┌──────────────────┐
│ Report Panel     │ ← Log changes and validation
└──────────────────┘
```

---

## Issue Categories

### 1. Structural Issues (from Topology Panel)

#### Dead Transitions
**Definition:** Transition that can never fire under any reachable marking

**Diagnosis:**
```python
if transition not in fireable_set and transition not in reachability_graph:
    issue = DeadTransitionIssue(transition)
```

**Suggestions:**
1. Add tokens to input places
2. Reduce arc weights on input arcs
3. Add new input arc from marked place
4. Remove transition if biologically unnecessary

**Example:**
```
Problem: Transition "T3: glucose_transport" never fires
Cause: Place "P5: extracellular_glucose" has 0 tokens, no source
Suggestions:
  ✓ Add M₀(P5) = 10 tokens (biologically: ambient glucose)
  ✓ Add arc from "environment" source place
  ✗ Remove T3 (would break pathway)
```

---

#### Dead Places
**Definition:** Place that never receives tokens

**Diagnosis:**
```python
if place not in marked_places_in_reachability:
    issue = DeadPlaceIssue(place)
```

**Suggestions:**
1. Add tokens to M₀
2. Add input arc from active transition
3. Remove place if redundant

---

#### Blocked Siphons → Deadlock
**Definition:** Minimal siphon that can become empty, causing deadlock

**Diagnosis:**
```python
for siphon in minimal_siphons:
    if not is_trap(siphon) and can_become_empty(siphon):
        issue = BlockedSiphonIssue(siphon)
```

**Suggestions (Classical Petri Net Theory):**
1. **Monitor Place Method** (Ezpeleta et al.)
   - Add monitor place PM
   - Connect to create trap structure
   - Ensures siphon never empties
   
2. **Initial Marking Increase**
   - Add more tokens to siphon places
   - May not guarantee liveness
   
3. **Arc Weight Adjustment**
   - Reduce consumption from siphon
   - Increase production to siphon

**Example:**
```
Problem: Siphon {P3: ATP, P7: ADP} can become empty → deadlock
Cause: ATP consumed faster than regenerated
Suggestions:
  ✓ Add monitor place "PM_ATP" with compensating arcs
  ✓ Increase M₀(P3) from 5 to 10
  ⚠️ Change arc weight P3→T2 from 2 to 1 (affects kinetics!)
```

---

#### Unbounded Places
**Definition:** Place where token count can grow indefinitely

**Diagnosis:**
```python
if place in unbounded_places or coverability_graph_shows_omega(place):
    issue = UnboundedPlaceIssue(place)
```

**Suggestions:**
1. **Inhibitor Arc** (capacity control)
   - Add inhibitor arc with threshold
   - Blocks producer transition when full
   
2. **Increase Consumption**
   - Higher arc weights on output arcs
   - Add competing consumer transitions
   
3. **Change Firing Policy**
   - Priority to consumer transitions
   - Fair scheduling

**Example:**
```
Problem: Place "P9: ROS" grows unbounded (0→∞)
Cause: Production transition fires more often than consumption
Suggestions:
  ✓ Add inhibitor arc P9⊣T4 (threshold: 20) - prevents overproduction
  ✓ Increase weight P9→T5 from 1 to 2 - faster consumption
  ⚠️ Priority policy: T5 (consumer) > T4 (producer)
```

---

### 2. Semantic Issues (from Model Structure)

#### Missing Initial Marking
**Definition:** M₀ is empty or insufficient to start simulation

**Diagnosis:**
```python
if sum(initial_marking.values()) == 0:
    issue = EmptyInitialMarkingIssue()
elif not can_fire_any_transition(initial_marking):
    issue = InsufficientInitialMarkingIssue()
```

**Suggestions:**
1. Biological default: M₀(substrate_places) = 100
2. Minimal marking: Enable at least one transition per strongly connected component
3. Import from SBML initial conditions

---

#### Conflicting Arc Weights
**Definition:** Weights that make biological sense impossible

**Diagnosis:**
```python
if arc.weight > source_place.capacity:
    issue = ConflictingWeightIssue(arc)
```

**Suggestions:**
1. Reduce weight to match capacity
2. Increase place capacity
3. Split into multiple arcs

---

### 3. Behavioral Issues (from Dynamic Analyses)

#### Not Live
**Definition:** System where some transitions can never fire after some reachable marking

**Diagnosis:**
```python
if liveness_level < 4:  # L4 = live
    issue = NotLiveIssue(dead_transitions)
```

**Suggestions:**
1. Apply siphon control methods
2. Add fairness constraints
3. Restructure conflicting resource allocation

---

#### Not Reversible
**Definition:** Cannot return to initial marking M₀

**Diagnosis:**
```python
if M₀ not in reachable_from_all_markings:
    issue = NotReversibleIssue()
```

**Suggestions:**
1. Add "reset" transition (T_reset: all_places → M₀)
2. Ensure all cycles are reversible
3. Check for degradation pathways

---

## Suggestion Engine Architecture

### Level 1: Rule-Based Heuristics

**Fast, deterministic, safe fixes**

```python
class RuleBasedEngine:
    def suggest_fixes(self, issue):
        if isinstance(issue, DeadTransitionIssue):
            return self._fix_dead_transition(issue)
        elif isinstance(issue, BlockedSiphonIssue):
            return self._fix_blocked_siphon(issue)
        # ...
    
    def _fix_dead_transition(self, issue):
        fixes = []
        
        # Rule 1: Add tokens to input places
        for place in issue.transition.input_places:
            if place.tokens == 0:
                fixes.append(AddTokensFix(
                    place=place,
                    amount=1,
                    rationale="Enable transition firing",
                    safety=SafetyLevel.SAFE
                ))
        
        # Rule 2: Reduce arc weights
        for arc in issue.transition.input_arcs:
            if arc.weight > 1:
                fixes.append(ReduceWeightFix(
                    arc=arc,
                    new_weight=1,
                    rationale="Lower firing threshold",
                    safety=SafetyLevel.AFFECTS_KINETICS
                ))
        
        return fixes
```

---

### Level 2: Algorithmic Repair (Classical Theory)

**Theory-based, proven correct**

#### Algorithm 1: Siphon Control (Ezpeleta et al., 1995)

```python
def create_monitor_place_for_siphon(siphon: Set[Place]):
    """Add monitor place to prevent siphon from emptying.
    
    Creates a trap that includes the siphon, guaranteeing
    at least one token remains in the control structure.
    """
    # Create monitor place
    monitor = Place(
        id=f"PM_{siphon_id}",
        name=f"Monitor for {siphon.name}",
        type=PlaceType.MONITOR
    )
    
    # Calculate initial marking for monitor
    # M₀(PM) = |T•∩•S| where T = transitions, S = siphon
    monitor.initial_marking = calculate_control_tokens(siphon)
    
    # Add arcs to create trap structure
    for transition in transitions_connected_to_siphon(siphon):
        if transition.produces_to_siphon():
            add_arc(monitor, transition)  # PM → T
        if transition.consumes_from_siphon():
            add_arc(transition, monitor)  # T → PM
    
    return MonitorPlaceFix(
        monitor=monitor,
        siphon=siphon,
        rationale="Prevents deadlock via trap creation",
        safety=SafetyLevel.STRUCTURAL_CHANGE,
        references=["Ezpeleta et al. 1995, IEEE TAC"]
    )
```

---

#### Algorithm 2: Minimal Liveness-Enforcing Supervisor (Li & Zhou, 2006)

```python
def compute_minimal_supervisor(net: PetriNet):
    """Compute minimal set of monitor places for liveness.
    
    Uses integer programming to find optimal control structure
    that enforces liveness with minimum additional places.
    """
    # Identify all deadly marked siphons
    deadly_siphons = find_deadly_marked_siphons(net)
    
    # Formulate as integer linear program
    # Variables: x_i = 1 if monitor i is added
    # Minimize: sum(x_i)
    # Subject to: Each deadly siphon is controlled
    
    model = LinearProgram()
    for siphon in deadly_siphons:
        model.add_constraint(
            sum(monitor_controls_siphon(m, siphon) * x[m] 
                for m in candidate_monitors) >= 1
        )
    
    solution = model.solve()
    
    return [create_monitor_place(m) for m in solution.selected_monitors]
```

---

### Level 3: Machine Learning (Future)

**Learn from user preferences and successful repairs**

```python
class MLRepairEngine:
    def __init__(self):
        self.model = None  # Will load trained model
        self.training_data = []
    
    def suggest_fixes(self, issue, context):
        """Use ML to rank fix suggestions based on:
        - User's past accepted/rejected fixes
        - Biological plausibility scores
        - Similarity to successful repairs in database
        """
        features = extract_features(issue, context)
        candidate_fixes = generate_candidates(issue)
        
        # Rank by predicted user acceptance
        scored_fixes = [
            (fix, self.model.predict_acceptance(fix, features))
            for fix in candidate_fixes
        ]
        
        return sorted(scored_fixes, key=lambda x: x[1], reverse=True)
    
    def learn_from_feedback(self, fix, accepted: bool):
        """Update model when user accepts/rejects a suggestion"""
        self.training_data.append((fix, accepted))
        if len(self.training_data) >= BATCH_SIZE:
            self.retrain_model()
```

---

## User Interface Design

### Master Palette Integration

```
┌─────────────────────────┐
│ 📁 FILES                │  (Panel 1)
│ 🧬 PATHWAYS             │  (Panel 2)
│ 📊 ANALYSES             │  (Panel 3)
│ 🔬 TOPOLOGY             │  (Panel 4)
│ ⚡ VIABILITY            │  (Panel 5) ← NEW!
│ 📄 REPORT               │  (Panel 6)
└─────────────────────────┘
```

**Icon Design:** ⚡ Lightning bolt = "bring model to life"

---

### Panel Layout (3 Sections)

```
┌─────────────────────────────────────────────────────────┐
│ ⚡ VIABILITY                                      [?][⚙] │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓ │
│ ┃ 🔍 DIAGNOSIS                           [🔄 Scan] ┃ │
│ ┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫ │
│ ┃                                                  ┃ │
│ ┃ 🔴 Critical Issues (2)                          ┃ │
│ ┃   ├─ Dead Transition: T3 (glycolysis)          ┃ │
│ ┃   │   └─ Input place P5 has 0 tokens           ┃ │
│ ┃   └─ Deadlock: Can occur after 5 steps         ┃ │
│ ┃       └─ Blocked siphon {P3, P7}               ┃ │
│ ┃                                                  ┃ │
│ ┃ 🟡 Warnings (3)                                 ┃ │
│ ┃   ├─ Unbounded Place: P9 (ROS)                 ┃ │
│ ┃   ├─ Not Reversible: Cannot return to M₀       ┃ │
│ ┃   └─ Low Liveness: Level 2 (should be 4)       ┃ │
│ ┃                                                  ┃ │
│ ┃ 🟢 Suggestions (1)                              ┃ │
│ ┃   └─ Consider priority scheduling for fairness ┃ │
│ ┃                                                  ┃ │
│ ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛ │
│                                                         │
│ ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓ │
│ ┃ 💡 SUGGESTED FIXES                               ┃ │
│ ┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫ │
│ ┃                                                  ┃ │
│ ┃ Fix #1: Add tokens to place P5                  ┃ │
│ ┃ ┌────────────────────────────────────────────┐  ┃ │
│ ┃ │ Place: P5 (extracellular_glucose)         │  ┃ │
│ ┃ │ Action: M₀(P5) = 0 → 10                   │  ┃ │
│ ┃ │ Impact: Enables T3 to fire                │  ┃ │
│ ┃ │ Rationale: Represents ambient glucose     │  ┃ │
│ ┃ │ Safety: ✓ Safe (no structural change)     │  ┃ │
│ ┃ │                                            │  ┃ │
│ ┃ │ [Preview] [Apply] [Reject] [Explain More] │  ┃ │
│ ┃ └────────────────────────────────────────────┘  ┃ │
│ ┃                                                  ┃ │
│ ┃ Fix #2: Create monitor place for siphon         ┃ │
│ ┃ ┌────────────────────────────────────────────┐  ┃ │
│ ┃ │ Siphon: {P3: ATP, P7: ADP}                │  ┃ │
│ ┃ │ Action: Add monitor place PM_ATP          │  ┃ │
│ ┃ │ Impact: Prevents deadlock (proven)        │  ┃ │
│ ┃ │ Method: Ezpeleta et al. 1995              │  ┃ │
│ ┃ │ Safety: ⚠ Adds new place (review arcs)    │  ┃ │
│ ┃ │                                            │  ┃ │
│ ┃ │ [Preview] [Apply] [Reject] [Show Theory]  │  ┃ │
│ ┃ └────────────────────────────────────────────┘  ┃ │
│ ┃                                                  ┃ │
│ ┃ Fix #3: Add inhibitor arc to P9                 ┃ │
│ ┃ ┌────────────────────────────────────────────┐  ┃ │
│ ┃ │ Arc: P9 ⊣ T4 (threshold: 20)              │  ┃ │
│ ┃ │ Impact: Bounds P9, prevents explosion     │  ┃ │
│ ┃ │ Rationale: Capacity control mechanism     │  ┃ │
│ ┃ │ Safety: ⚠ Changes firing behavior         │  ┃ │
│ ┃ │                                            │  ┃ │
│ ┃ │ [Preview] [Apply] [Reject] [Alternative]  │  ┃ │
│ ┃ └────────────────────────────────────────────┘  ┃ │
│ ┃                                                  ┃ │
│ ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛ │
│                                                         │
│ ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓ │
│ ┃ ⚙️ OPTIONS                                       ┃ │
│ ┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫ │
│ ┃                                                  ┃ │
│ ┃ Mode: ◉ Manual Review                           ┃ │
│ ┃       ○ Auto-Pilot (apply all safe fixes)       ┃ │
│ ┃       ○ Wizard (step-by-step guidance)          ┃ │
│ ┃                                                  ┃ │
│ ┃ Constraints:                                     ┃ │
│ ┃ ☑ Respect BRENDA kinetic constraints            ┃ │
│ ┃ ☑ Highlight changes on canvas                   ┃ │
│ ┃ ☑ Preserve biological meaning                   ┃ │
│ ┃ ☐ Allow structural changes (add/remove nodes)   ┃ │
│ ┃ ☐ Allow arc weight modifications                ┃ │
│ ┃                                                  ┃ │
│ ┃ [ Re-analyze After Apply ]                      ┃ │
│ ┃                                                  ┃ │
│ ┃ [🔄 Re-scan] [✓ Apply All Safe] [↩ Undo Last]   ┃ │
│ ┃                                                  ┃ │
│ ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛ │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

### Canvas Integration

When a fix is previewed or applied, highlight affected elements:

```python
def preview_fix(fix):
    """Show visual preview of fix on canvas"""
    
    if isinstance(fix, AddTokensFix):
        # Highlight place
        canvas.highlight_place(fix.place, color='green')
        # Show token count change
        canvas.show_label(fix.place, f"M₀: {fix.place.tokens} → {fix.place.tokens + fix.amount}")
    
    elif isinstance(fix, AddArcFix):
        # Show ghost arc
        canvas.draw_ghost_arc(fix.source, fix.target, style='dashed')
        # Animate token flow
        canvas.animate_token_flow(fix.source, fix.target)
    
    elif isinstance(fix, MonitorPlaceFix):
        # Show new monitor place (ghost)
        canvas.draw_ghost_place(fix.monitor, color='blue', label='Monitor')
        # Show all new arcs
        for arc in fix.arcs:
            canvas.draw_ghost_arc(arc.source, arc.target, style='dashed')
```

---

## Implementation Plan

### Phase 1: Foundation (Weeks 1-2)

**Goal:** Basic panel with diagnosis display

#### Tasks:
1. **Create panel structure**
   - `src/shypn/ui/panels/viability/viability_panel.py`
   - `src/shypn/ui/panels/viability/__init__.py`
   - `src/shypn/helpers/viability_panel_loader.py`

2. **Integrate with Master Palette**
   - Add 6th button to Master Palette
   - Wire show/hide handlers
   - Test mutual exclusivity with other panels

3. **Read Topology Panel data**
   - Connect to TopologyPanel via `set_topology_panel()`
   - Parse structural analysis results
   - Display in diagnosis tree view

4. **Basic UI components**
   - Diagnosis expander (collapsible)
   - Issue tree view (with icons)
   - Scan button (triggers re-analysis)

**Deliverable:** Panel appears, shows topology issues, no fixes yet

---

### Phase 2: Rule-Based Fixes (Weeks 3-5)

**Goal:** Implement suggestion engine and apply mechanism

#### Tasks:
1. **Create fix data structures**
   - `src/shypn/viability/fixes/base_fix.py` (abstract)
   - `src/shypn/viability/fixes/token_fix.py`
   - `src/shypn/viability/fixes/arc_fix.py`
   - `src/shypn/viability/fixes/weight_fix.py`

2. **Implement rule-based engine**
   - `src/shypn/viability/engines/rule_based_engine.py`
   - Rules for dead transitions
   - Rules for unbounded places
   - Rules for missing initial marking

3. **Apply mechanism**
   - `src/shypn/viability/actions/applier.py`
   - Modify model via ModelCanvas API
   - Track changes for undo
   - Validate after apply

4. **UI for fixes**
   - Suggested fixes list
   - Apply/Reject buttons
   - Preview on canvas (highlight)

**Deliverable:** Can suggest and apply simple fixes (tokens, weights)

---

### Phase 3: Algorithmic Repair (Weeks 6-9)

**Goal:** Implement classical Petri net theory algorithms

#### Tasks:
1. **Siphon control**
   - Implement Ezpeleta et al. monitor place method
   - Detect deadly marked siphons
   - Create trap structures

2. **Liveness enforcement**
   - Implement Li & Zhou minimal supervisor
   - Integer programming formulation
   - Optimal monitor placement

3. **Boundedness control**
   - Implement capacity enforcement mechanisms
   - Inhibitor arc suggestion
   - Structural boundedness analysis

4. **Validation framework**
   - Re-run topology analysis after fix
   - Verify issue is resolved
   - Detect new issues introduced by fix

**Deliverable:** Can repair complex issues using proven algorithms

---

### Phase 4: Biological Constraints (Weeks 10-12)

**Goal:** Integrate with BRENDA, ensure biological plausibility

#### Tasks:
1. **Constraint checker**
   - Check if fix violates kinetic constraints
   - Verify stoichiometry preservation
   - Validate against BRENDA data

2. **Bio-aware suggestions**
   - Prefer fixes that align with biological knowledge
   - Suggest realistic token counts (concentrations)
   - Avoid unnatural structures (e.g., monitors for biological pathways)

3. **Explanation system**
   - Generate human-readable rationales
   - Link to literature (PubMed, BRENDA refs)
   - Explain Petri net theory concepts

**Deliverable:** Fixes are biologically realistic and explained

---

### Phase 5: Advanced Features (Weeks 13-16)

**Goal:** Auto-pilot, wizard, ML foundation

#### Tasks:
1. **Auto-pilot mode**
   - Batch apply safe fixes
   - Generate report of changes
   - Rollback mechanism

2. **Interactive wizard**
   - Step-by-step guided repair
   - Educational explanations
   - Progress tracking

3. **ML infrastructure**
   - Collect fix acceptance data
   - Feature extraction from models
   - Initial ranking model

4. **Testing & refinement**
   - Test on BioModels database
   - User testing with biologists
   - Performance optimization

**Deliverable:** Production-ready viability assistant

---

## Testing Strategy

### Unit Tests

```python
# tests/viability/test_diagnosis.py
def test_detect_dead_transition():
    model = create_test_model_with_dead_transition()
    engine = DiagnosisEngine(model)
    issues = engine.scan()
    assert any(isinstance(i, DeadTransitionIssue) for i in issues)

# tests/viability/test_suggestions.py
def test_suggest_fix_for_dead_transition():
    issue = DeadTransitionIssue(transition_id='T3')
    engine = RuleBasedEngine()
    fixes = engine.suggest_fixes(issue)
    assert len(fixes) > 0
    assert any(isinstance(f, AddTokensFix) for f in fixes)

# tests/viability/test_applier.py
def test_apply_token_fix():
    model = load_model('test_model.xml')
    fix = AddTokensFix(place='P1', amount=10)
    applier = FixApplier(model)
    applier.apply(fix)
    assert model.get_place('P1').initial_marking == 10
```

---

### Integration Tests

```python
# tests/integration/test_viability_panel.py
def test_full_repair_workflow():
    # 1. Load model with known issue
    app = launch_shypn()
    model = app.load_model('models/deadlock_test.xml')
    
    # 2. Open viability panel
    viability_panel = app.open_panel('viability')
    
    # 3. Scan for issues
    viability_panel.scan()
    issues = viability_panel.get_issues()
    assert len(issues) > 0
    
    # 4. Get suggestions
    fixes = viability_panel.get_suggested_fixes()
    assert len(fixes) > 0
    
    # 5. Apply first fix
    viability_panel.apply_fix(fixes[0])
    
    # 6. Re-scan
    viability_panel.scan()
    new_issues = viability_panel.get_issues()
    
    # 7. Verify issue resolved
    assert len(new_issues) < len(issues)
```

---

### Validation Tests (BioModels Database)

```python
# scripts/test_biomodels_repair.py
def test_biomodels_batch_repair():
    """Test on 100 models from BioModels database"""
    
    results = []
    for model_id in BIOMODELS_TEST_SET:
        model = load_biomodel(model_id)
        
        # Scan
        issues = diagnose(model)
        
        if len(issues) == 0:
            results.append({'model': model_id, 'status': 'already_viable'})
            continue
        
        # Auto-repair
        fixes_applied = auto_repair(model, safety_level='safe_only')
        
        # Re-scan
        remaining_issues = diagnose(model)
        
        results.append({
            'model': model_id,
            'initial_issues': len(issues),
            'fixes_applied': len(fixes_applied),
            'remaining_issues': len(remaining_issues),
            'success': len(remaining_issues) < len(issues)
        })
    
    # Generate report
    success_rate = sum(1 for r in results if r['success']) / len(results)
    print(f"Success rate: {success_rate * 100:.1f}%")
    
    return results
```

---

## File Structure

```
src/shypn/
├── ui/
│   └── panels/
│       └── viability/
│           ├── __init__.py
│           ├── viability_panel.py           # Main panel UI
│           ├── diagnosis_view.py            # Issue tree view
│           ├── suggestions_view.py          # Fix list view
│           └── options_view.py              # Mode and constraints
│
├── helpers/
│   └── viability_panel_loader.py            # Panel loader (minimal)
│
├── viability/                               # Business logic
│   ├── __init__.py
│   │
│   ├── diagnosis/                           # Issue detection
│   │   ├── __init__.py
│   │   ├── engine.py                        # Main diagnosis engine
│   │   ├── issues.py                        # Issue data classes
│   │   └── collectors/
│   │       ├── structural_collector.py      # From topology
│   │       ├── semantic_collector.py        # From model
│   │       └── behavioral_collector.py      # From simulation
│   │
│   ├── suggestions/                         # Fix generation
│   │   ├── __init__.py
│   │   ├── rule_based_engine.py            # Heuristic fixes
│   │   ├── algorithmic_engine.py           # Theory-based fixes
│   │   └── ml_engine.py                    # ML-based ranking (future)
│   │
│   ├── fixes/                               # Fix data structures
│   │   ├── __init__.py
│   │   ├── base_fix.py                     # Abstract base
│   │   ├── token_fix.py                    # M₀ modifications
│   │   ├── arc_fix.py                      # Add/remove arcs
│   │   ├── weight_fix.py                   # Change weights
│   │   ├── monitor_fix.py                  # Add monitors
│   │   └── policy_fix.py                   # Firing policies
│   │
│   ├── actions/                             # Apply fixes
│   │   ├── __init__.py
│   │   ├── applier.py                      # Main applier
│   │   ├── validator.py                    # Validate after apply
│   │   └── undo_manager.py                 # Undo/redo stack
│   │
│   ├── algorithms/                          # Classical PN theory
│   │   ├── __init__.py
│   │   ├── siphon_control.py               # Ezpeleta et al.
│   │   ├── liveness_supervisor.py          # Li & Zhou
│   │   └── boundedness_control.py          # Capacity enforcement
│   │
│   ├── constraints/                         # Biological validation
│   │   ├── __init__.py
│   │   ├── kinetic_checker.py              # BRENDA constraints
│   │   ├── stoichiometry_checker.py        # Mass balance
│   │   └── plausibility_scorer.py          # Realism metrics
│   │
│   └── utils/                               # Utilities
│       ├── __init__.py
│       ├── ranking.py                       # Rank fix suggestions
│       ├── explanation.py                   # Generate rationales
│       └── reporting.py                     # Change reports
│
tests/
├── viability/
│   ├── test_diagnosis.py
│   ├── test_suggestions.py
│   ├── test_fixes.py
│   ├── test_applier.py
│   ├── test_algorithms.py
│   └── test_constraints.py
│
└── integration/
    └── test_viability_panel.py

doc/
├── VIABILITY_PANEL_DESIGN.md               # This file
├── viability/
│   ├── USER_GUIDE.md                        # How to use
│   ├── ALGORITHM_REFERENCES.md              # Literature
│   ├── EXAMPLES.md                          # Common scenarios
│   └── API.md                               # Developer API
```

---

## Success Metrics

### Technical Metrics
- **Coverage:** % of BioModels database models that can be repaired
- **Accuracy:** % of fixes that actually resolve the issue
- **Safety:** % of fixes that don't introduce new issues
- **Performance:** Time to scan and suggest fixes (target: <1s)

### User Metrics
- **Acceptance rate:** % of suggested fixes accepted by users
- **Learning curve:** Time for new user to successfully repair first model
- **Satisfaction:** User survey scores (1-5 scale)

### Research Metrics
- **Novel contribution:** First tool with automated PN repair for biology
- **Publications:** Papers on algorithms, ML approach, benchmark results
- **Adoption:** # of users, # of models repaired, citations

---

## Related Work

### Petri Net Tools
- **CPN Tools:** Verification, no repair suggestions
- **PIPE:** Analysis, no automated fixes
- **Snoopy:** Simulation, no viability assistant
- **Yasper:** Education-focused, limited analysis

**Shypn Advantage:** Only tool with automated, bio-aware repair suggestions

### Research Papers
1. **Ezpeleta et al. (1995)** - "A Petri net based deadlock prevention policy for flexible manufacturing systems"
2. **Li & Zhou (2006)** - "Elementary siphons of Petri nets and their application to deadlock prevention"
3. **Giua & DiCesare (1994)** - "Supervisory design using Petri nets"
4. **Chen et al. (2011)** - "Design of a maximally permissive liveness-enforcing supervisor"

---

## Future Enhancements

### Version 3.1
- Export repair report to PDF/Excel
- Batch repair for multiple models
- Repair history database (learn from past fixes)

### Version 3.2
- Machine learning for fix ranking
- User preference learning
- Context-aware suggestions (pathway-specific)

### Version 3.3
- Multi-objective optimization (liveness + boundedness + realism)
- Genetic algorithms for parameter tuning
- Integration with pathway databases (KEGG, Reactome)

### Version 4.0
- Real-time repair during model editing
- Predictive suggestions ("This change may cause deadlock")
- Collaborative repair (share fix strategies)

---

## References

### Petri Net Theory
1. Murata, T. (1989). "Petri nets: Properties, analysis and applications." Proceedings of the IEEE.
2. Ezpeleta, J., Colom, J. M., & Martinez, J. (1995). "A Petri net based deadlock prevention policy for FMS." IEEE TAC.
3. Li, Z. W., & Zhou, M. C. (2006). "Elementary siphons of Petri nets and their application." IEEE TSMCA.

### Systems Biology
4. Chaouiya, C. (2007). "Petri net modelling of biological networks." Briefings in Bioinformatics.
5. Heiner, M., Gilbert, D., & Donaldson, R. (2008). "Petri nets for systems and synthetic biology." SFM.

### Software Engineering
6. Gamma, E. et al. (1994). "Design Patterns: Elements of Reusable Object-Oriented Software."

---

## Glossary

- **Dead Transition:** Transition that never fires under any reachable marking
- **Siphon:** Set of places where tokens can leave but not enter
- **Trap:** Set of places where tokens can enter but not leave
- **Liveness:** Property that all transitions can always eventually fire
- **Boundedness:** Property that place token counts remain finite
- **Monitor Place:** Control place added to enforce liveness or boundedness
- **Supervisor:** Control structure that restricts behavior to safe subset
- **M₀:** Initial marking (token distribution at start)

---

## Conclusion

The Viability Panel represents a **paradigm shift** from passive analysis to active assistance. By combining:

1. ✅ **Classical Petri net theory** (proven correct)
2. ✅ **Biological domain knowledge** (BRENDA integration)
3. ✅ **Modern UI/UX** (interactive, visual)
4. ✅ **Future AI/ML** (learn from users)

Shypn will become the **first truly intelligent** biological modeling tool - not just reporting problems, but solving them.

**Next Steps:**
1. ✅ Review and approve this design
2. ⏳ Create `viability` branch
3. ⏳ Implement Phase 1 (foundation)
4. ⏳ Iterate based on user feedback

---

**Author:** Simão Eugénio & GitHub Copilot  
**Date:** November 9, 2025  
**Status:** Design Complete - Ready for Implementation  
**Estimated Timeline:** 16 weeks to production-ready v3.0
