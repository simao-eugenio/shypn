# Phase 3: Viability Panel UI Design

**Goal**: Provide actionable inference suggestions organized by domain categories.

## UI Organization: Category Tabs

The Viability Panel will have **4 category tabs**, each focused on a different type of inference:

```
┌─────────────────────────────────────────────────────────┐
│ 🏗️ Structural │ 🧬 Biological │ ⚡ Kinetic │ 🔍 Diagnosis │
├─────────────────────────────────────────────────────────┤
│                                                           │
│   [Content for selected category]                        │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

---

## 🏗️ Category 1: Structural Inference

**Focus**: Topology-based fixes using P-invariants, T-invariants, siphons, liveness.

**Data Sources**: 
- P-invariants, T-invariants
- Siphons, traps
- Liveness levels
- Deadlock analysis

### UI Layout

```
┌─────────────────────────────────────────────────────────┐
│ 🏗️ STRUCTURAL INFERENCE                                  │
├─────────────────────────────────────────────────────────┤
│                                                           │
│ 📊 Current Status                                        │
│   • P-invariants: 3                                      │
│   • T-invariants: 0 ⚠️                                   │
│   • Siphons: 0                                           │
│   • Dead transitions: 2 🔴                               │
│                                                           │
│ ──────────────────────────────────────────────────────  │
│                                                           │
│ 🔍 Issues Detected:                                      │
│                                                           │
│ ┌───────────────────────────────────────────────────┐   │
│ │ 🔴 Critical: Transition T5 is DEAD                 │   │
│ │    • Has no input tokens (Place P3 empty)         │   │
│ │    • Downstream of glycolysis pathway             │   │
│ │                                                    │   │
│ │    Suggestions:                                    │   │
│ │    1. Add 5 tokens to P3 (80% confidence)         │   │
│ │       [Apply Initial Marking] [Preview]           │   │
│ │                                                    │   │
│ │    2. Add source transition (60% confidence)      │   │
│ │       [Add Source] [Preview]                      │   │
│ └───────────────────────────────────────────────────┘   │
│                                                           │
│ ┌───────────────────────────────────────────────────┐   │
│ │ ⚠️  Warning: Empty siphon detected                 │   │
│ │    • Places: {P3, P7, P11}                        │   │
│ │    • Risk: Deadlock if P3 becomes empty           │   │
│ │                                                    │   │
│ │    Suggestions:                                    │   │
│ │    1. Add source to P3 (ATP) at rate 1.0 (85%)   │   │
│ │       [Add Source Transition]                     │   │
│ └───────────────────────────────────────────────────┘   │
│                                                           │
│ [Scan for Issues]  [Clear All]  [Undo Last]             │
└─────────────────────────────────────────────────────────┘
```

### Inference Methods Used

| Issue Type | Detection | Inference Method | Output |
|------------|-----------|------------------|--------|
| Dead transitions | `liveness_level == 'dead'` | `infer_initial_marking(place_id)` | Tokens to add |
| Empty places | `current_marking == 0` | `infer_initial_marking(place_id)` | Tokens to add |
| Empty siphons | Siphon analysis | `suggest_source_placement()` | Source transition + rate |
| Missing T-invariants | Count == 0 | (Future) cycle suggestion | Transitions to add |

### Actions Supported

1. **Apply Initial Marking**: Sets `place.tokens = N`
2. **Add Source Transition**: Creates new transition with output arc to place
3. **Preview**: Highlights affected elements on canvas (yellow glow)

---

## 🧬 Category 2: Biological Inference

**Focus**: Biochemical semantics using KEGG compounds, reactions, pathways.

**Data Sources**:
- KEGG compound metadata (name, formula, molecular weight)
- KEGG reaction metadata (substrates, products, EC numbers)
- Pathway context (hsa00010, etc.)

### UI Layout

```
┌─────────────────────────────────────────────────────────┐
│ 🧬 BIOLOGICAL INFERENCE                                   │
├─────────────────────────────────────────────────────────┤
│                                                           │
│ 📊 Current Knowledge                                     │
│   • Compounds: 26                                        │
│   • Reactions: 32                                        │
│   • Pathway: hsa00010 (Glycolysis)                      │
│                                                           │
│ ──────────────────────────────────────────────────────  │
│                                                           │
│ 🔍 Issues Detected:                                      │
│                                                           │
│ ┌───────────────────────────────────────────────────┐   │
│ │ 🔴 Stoichiometry mismatch                          │   │
│ │    • Arc A12 (P3→T5) has weight 1                 │   │
│ │    • Reaction R00200 requires 2 ATP molecules     │   │
│ │                                                    │   │
│ │    Suggestion:                                     │   │
│ │    Set arc weight to 2 (90% confidence)           │   │
│ │    [Apply Stoichiometry] [View Reaction]          │   │
│ └───────────────────────────────────────────────────┘   │
│                                                           │
│ ┌───────────────────────────────────────────────────┐   │
│ │ ⚠️  Missing compound annotation                    │   │
│ │    • Place P7 has no compound mapping             │   │
│ │    • Connected to reaction R00710 (Hexokinase)    │   │
│ │                                                    │   │
│ │    Suggestions:                                    │   │
│ │    1. Map to C00031 (D-Glucose) (75%)             │   │
│ │       [Apply Mapping]                             │   │
│ │                                                    │   │
│ │    2. Map to C00267 (α-D-Glucose) (60%)           │   │
│ │       [Apply Mapping]                             │   │
│ └───────────────────────────────────────────────────┘   │
│                                                           │
│ ┌───────────────────────────────────────────────────┐   │
│ │ 💡 Conservation suggestion                         │   │
│ │    • ATP + ADP should be conserved                │   │
│ │    • Places: {P2 (ATP), P8 (ADP)}                 │   │
│ │    • Current sum: 8 tokens                        │   │
│ │                                                    │   │
│ │    Expected P-invariant:                           │   │
│ │    1×P2 + 1×P8 = 10 tokens (typical)              │   │
│ │                                                    │   │
│ │    Suggestion:                                     │   │
│ │    Add 2 tokens to ATP pool (P2) (70%)            │   │
│ │    [Apply Conservation]                           │   │
│ └───────────────────────────────────────────────────┘   │
│                                                           │
│ [Scan Semantics]  [Clear All]  [Undo Last]              │
└─────────────────────────────────────────────────────────┘
```

### Inference Methods Used

| Issue Type | Detection | Inference Method | Output |
|------------|-----------|------------------|--------|
| Wrong stoichiometry | Arc weight ≠ reaction | `infer_arc_weight(arc_id)` | Correct weight |
| Missing compound | `place.compound_id == None` | (Future) KEGG lookup | Compound ID |
| Conservation violation | P-invariant broken | (Future) rebalance | Token adjustments |
| Initial concentration | No basal value | `infer_initial_marking()` (compound-based) | Tokens from mM |

### Actions Supported

1. **Apply Stoichiometry**: Sets `arc.weight = N`
2. **Apply Mapping**: Links place to KEGG compound
3. **Apply Conservation**: Adjusts tokens to maintain P-invariant
4. **View Reaction**: Opens KEGG reaction page in browser

---

## ⚡ Category 3: Kinetic Inference

**Focus**: Firing rates using BRENDA/SABIO-RK kinetic parameters.

**Data Sources**:
- Km values (Michaelis constant)
- Vmax (maximum velocity)
- Kcat (turnover number)
- EC numbers
- HeuristicDatabase (local SQLite)

### UI Layout

```
┌─────────────────────────────────────────────────────────┐
│ ⚡ KINETIC INFERENCE                                      │
├─────────────────────────────────────────────────────────┤
│                                                           │
│ 📊 Current Parameters                                    │
│   • Transitions with kinetics: 4 / 39                   │
│   • Database: HeuristicDatabase (offline)               │
│   • Coverage: 10% ⚠️                                     │
│                                                           │
│ ──────────────────────────────────────────────────────  │
│                                                           │
│ 🔍 Issues Detected:                                      │
│                                                           │
│ ┌───────────────────────────────────────────────────┐   │
│ │ 🔴 Transition T5 has no firing rate                │   │
│ │    • EC: 2.7.1.1 (Hexokinase)                     │   │
│ │    • Substrate: D-Glucose (P7)                    │   │
│ │                                                    │   │
│ │    BRENDA Data Found:                              │   │
│ │    • Km(glucose) = 0.15 mM (BRENDA)               │   │
│ │    • Vmax = 2.3 mM/s (BRENDA, confidence: 75%)    │   │
│ │                                                    │   │
│ │    Suggestion:                                     │   │
│ │    Set firing rate to 2.30 s⁻¹ (75% confidence)   │   │
│ │    [Apply Rate] [View BRENDA Entry]               │   │
│ └───────────────────────────────────────────────────┘   │
│                                                           │
│ ┌───────────────────────────────────────────────────┐   │
│ │ ⚠️  Non-enzymatic transition T12                   │   │
│ │    • No EC number assigned                        │   │
│ │    • No kinetic data available                    │   │
│ │                                                    │   │
│ │    Suggestion:                                     │   │
│ │    1. Set mass action rate: 0.10 s⁻¹ (20%)       │   │
│ │       [Apply Default Rate]                        │   │
│ │                                                    │   │
│ │    2. Assign EC number manually                   │   │
│ │       [Search BRENDA]                             │   │
│ └───────────────────────────────────────────────────┘   │
│                                                           │
│ ┌───────────────────────────────────────────────────┐   │
│ │ 💡 Enzymatic heuristic available                   │   │
│ │    • Transition T8 (EC: 1.2.1.12)                 │   │
│ │    • Database: 156 Km values, 89 Vmax values      │   │
│ │                                                    │   │
│ │    Estimated Rate:                                 │   │
│ │    • From Kcat = 450 s⁻¹                          │   │
│ │    • Assuming [E] = 0.01 mM                       │   │
│ │    • Vmax ≈ 4.5 mM/s                              │   │
│ │                                                    │   │
│ │    Suggestion:                                     │   │
│ │    Set firing rate to 4.50 s⁻¹ (60% confidence)   │   │
│ │    [Apply Estimated Rate]                         │   │
│ └───────────────────────────────────────────────────┘   │
│                                                           │
│ [Scan Kinetics]  [Query BRENDA]  [Undo Last]            │
└─────────────────────────────────────────────────────────┘
```

### Inference Methods Used

| Issue Type | Detection | Inference Method | Output |
|------------|-----------|------------------|--------|
| No firing rate | `transition.rate == None` | `infer_firing_rate(trans_id)` | Rate (Vmax or default) |
| Low confidence | Confidence < 50% | (Future) BRENDA query | Better parameters |
| Inconsistent units | Rate units mismatch | (Future) unit conversion | Normalized rate |

### Actions Supported

1. **Apply Rate**: Sets `transition.rate = N`
2. **Apply Estimated Rate**: Uses Kcat calculation
3. **Apply Default Rate**: Uses mass action fallback
4. **View BRENDA Entry**: Opens BRENDA web interface
5. **Query BRENDA**: Fetches fresh data from online API

---

## 🔍 Category 4: Diagnosis & Repair

**Focus**: Overall model health and **locality-based diagnosis** for focused analysis.

**Data Sources**: All knowledge base layers combined + Locality context.

**Key Feature**: Users can select localities (model segments) to get targeted diagnosis and suggestions.

### UI Layout

```
┌─────────────────────────────────────────────────────────┐
│ 🔍 DIAGNOSIS & REPAIR                                     │
├─────────────────────────────────────────────────────────┤
│                                                           │
│ 🎯 Diagnosis Scope:                                      │
│   ○ Full Model (39 transitions, 26 places)              │
│   ● Selected Locality: "Glycolysis Upper Phase"         │
│     └─ 5 transitions, 6 places, 11 arcs                 │
│                                                           │
│   [Select Locality ▼]  [Manage Localities]              │
│                                                           │
│ ──────────────────────────────────────────────────────  │
│                                                           │
│ 📊 Locality Health Score: 65% ⚠️                         │
│                                                           │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ Structural:     █████████░░░░░  70%                 │ │
│ │ Biological:     ████████░░░░░░  60%                 │ │
│ │ Kinetic:        ███░░░░░░░░░░░  25% 🔴              │ │
│ │ Viability:      ██████████░░░░  75%                 │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                           │
│ ──────────────────────────────────────────────────────  │
│                                                           │
│ 🚨 Critical Issues in This Locality (2)                  │
│                                                           │
│ ┌───────────────────────────────────────────────────┐   │
│ │ 🔴 Transition T5 (Hexokinase) is DEAD              │   │
│ │    • Location: Locality "Glycolysis Upper Phase"  │   │
│ │    • Missing: Substrate tokens in P3 (Glucose)    │   │
│ │    • Impact: Blocks downstream pathway            │   │
│ │                                                    │   │
│ │    Multi-Domain Suggestions:                       │   │
│ │    ┌─────────────────────────────────────────────┐ │   │
│ │    │ 🏗️ STRUCTURAL (80% confidence)              │ │   │
│ │    │    Add 5 tokens to P3                       │ │   │
│ │    │    [Apply Initial Marking]                  │ │   │
│ │    ├─────────────────────────────────────────────┤ │   │
│ │    │ 🧬 BIOLOGICAL (70% confidence)              │ │   │
│ │    │    P3 = C00031 (D-Glucose)                  │ │   │
│ │    │    Typical: 5 mM (physiological)            │ │   │
│ │    │    [Apply Basal Concentration]              │ │   │
│ │    ├─────────────────────────────────────────────┤ │   │
│ │    │ ⚡ KINETIC (60% confidence)                  │ │   │
│ │    │    T5: Set rate = 2.3 s⁻¹ (BRENDA Vmax)    │ │   │
│ │    │    Km(glucose) = 0.15 mM                    │ │   │
│ │    │    [Apply Kinetic Parameters]              │ │   │
│ │    └─────────────────────────────────────────────┘ │   │
│ │                                                    │   │
│ │    [Apply All 3 Fixes]  [Preview on Canvas]       │   │
│ └───────────────────────────────────────────────────┘   │
│                                                           │
│ ┌───────────────────────────────────────────────────┐   │
│ │ ⚠️  Arc A7 (P3→T5) has default weight              │   │
│ │    • Location: Locality "Glycolysis Upper Phase"  │   │
│ │    • Current: weight = 1                          │   │
│ │    • Reaction: R00710 (Hexokinase)                │   │
│ │                                                    │   │
│ │    Multi-Domain Suggestions:                       │   │
│ │    ┌─────────────────────────────────────────────┐ │   │
│ │    │ 🧬 BIOLOGICAL (90% confidence)              │ │   │
│ │    │    Stoichiometry: 1 Glucose → 1 G6P         │ │   │
│ │    │    Keep weight = 1 (correct)                │ │   │
│ │    │    [No Change Needed]                       │ │   │
│ │    ├─────────────────────────────────────────────┤ │   │
│ │    │ 🏗️ STRUCTURAL (85% confidence)              │ │   │
│ │    │    P-invariant conserves glucose tokens     │ │   │
│ │    │    Weight = 1 is consistent                 │ │   │
│ │    │    ✓ Verified                               │ │   │
│ │    └─────────────────────────────────────────────┘ │   │
│ └───────────────────────────────────────────────────┘   │
│                                                           │
│ ──────────────────────────────────────────────────────  │
│                                                           │
│ 💡 Locality-Specific Insights                            │
│                                                           │
│ ┌───────────────────────────────────────────────────┐   │
│ │ 📊 Pathway Coverage (Glycolysis Upper Phase)       │   │
│ │    • 5/5 transitions have EC numbers ✓            │   │
│ │    • 6/6 places mapped to compounds ✓             │   │
│ │    • 1/5 transitions have kinetics ⚠️  (20%)      │   │
│ │                                                    │   │
│ │    [Auto-complete Kinetics for Locality]          │   │
│ └───────────────────────────────────────────────────┘   │
│                                                           │
│ ┌───────────────────────────────────────────────────┐   │
│ │ 🔗 Boundary Analysis                               │   │
│ │    • Inputs: P3 (Glucose), P2 (ATP)               │   │
│ │    • Outputs: P8 (G6P)                            │   │
│ │    • Interface transitions: T1, T5                │   │
│ │                                                    │   │
│ │    Suggestion: Check boundary conditions          │   │
│ │    [Analyze Input/Output Flow]                    │   │
│ └───────────────────────────────────────────────────┘   │
│                                                           │
│ [Run Locality Diagnosis]  [Compare with Full Model]      │
│ [Export Locality Report]  [Undo Last Change]             │
└─────────────────────────────────────────────────────────┘
```

### Inference Methods Used

All methods combined + batch operations + **locality filtering**:
- `scan_locality_issues(locality_id)` - Focused diagnosis on model segment
- `scan_all_issues()` - Comprehensive full model check
- `fix_all_dead_transitions(locality_id=None)` - Batch apply marking suggestions
- `assign_all_rates(locality_id=None)` - Batch apply rate suggestions
- `verify_conservation_laws(locality_id=None)` - Check P-invariants in scope
- `analyze_locality_boundaries(locality_id)` - Input/output flow analysis
- `compare_locality_health(locality_id_1, locality_id_2)` - Compare segments

### Locality Integration Features

#### 1. Locality Selection Dropdown
```python
Dropdown shows:
• "Full Model" (default)
• "Glycolysis Upper Phase" (5T, 6P)
• "Glycolysis Lower Phase" (8T, 10P)
• "Pentose Phosphate Pathway" (7T, 9P)
• Custom locality: [Create New...]
```

#### 2. Multi-Domain Issue Cards
Each issue shows suggestions from **all relevant categories**:
```
Issue: Dead Transition T5
├─ 🏗️ Structural suggestion (80%)
├─ 🧬 Biological suggestion (70%)
├─ ⚡ Kinetic suggestion (60%)
└─ [Apply All] button for combined fix
```

#### 3. Locality-Specific Metrics
- **Coverage**: % of elements with complete data
- **Boundary Analysis**: Inputs/outputs to other localities
- **Pathway Completeness**: All reactions mapped?
- **Kinetic Completeness**: All rates assigned?

#### 4. Comparative Analysis
```
[Compare Localities]
• Glycolysis vs Pentose Phosphate
• Show relative health scores
• Identify common issues
• Suggest inter-locality fixes
```

### Actions Supported

1. **Run Locality Diagnosis**: Scans only selected segment
2. **Apply All Fixes**: Batch apply high-confidence suggestions (>70%) in locality
3. **Export Locality Report**: Save diagnosis as PDF/HTML for this segment
4. **Fix All Dead Transitions**: Batch operation (filtered by locality)
5. **Auto-assign Rates**: Batch operation for kinetics (filtered by locality)
6. **Analyze Boundaries**: Check input/output flow between localities
7. **Compare with Full Model**: Side-by-side health comparison
8. **Auto-complete Kinetics for Locality**: Query BRENDA for all transitions in segment

### Locality Boundary Analysis

When a locality is selected, the system analyzes:

**Input Places**: Places that receive tokens from outside the locality
- Check if they have appropriate initial marking
- Suggest source transitions if needed
- Verify connection to upstream localities

**Output Places**: Places that send tokens to outside the locality  
- Check if downstream transitions are enabled
- Verify stoichiometry matches interface
- Suggest rate adjustments if bottleneck

**Interface Transitions**: Transitions on the boundary
- Higher priority for diagnosis (affects multiple localities)
- Check for rate consistency across boundary
- Verify arc weights match biological stoichiometry

Example:
```
🔗 Boundary Analysis for "Glycolysis Upper Phase"

INPUTS:
  • P3 (Glucose) ← from "Import/Export"
    ⚠️  Currently: 0 tokens
    Suggestion: Add source (5 mM basal) [Apply]
  
  • P2 (ATP) ← from "Energy Metabolism"
    ✓ OK: 8 tokens available

OUTPUTS:
  • P8 (G6P) → to "Glycolysis Lower Phase"
    ✓ OK: Transition T5 enabled
  
  • P9 (ADP) → to "Energy Metabolism"
    ⚠️  Rate mismatch: Producing faster than consuming
    Suggestion: Balance rates [Analyze]
```

### Actions Supported

1. **Run Full Diagnosis**: Scans all 4 categories
2. **Apply All Fixes**: Batch apply high-confidence suggestions (>70%)
3. **Export Report**: Save diagnosis as PDF/HTML
4. **Fix All Dead Transitions**: Batch operation
5. **Auto-assign Rates**: Batch operation for kinetics

---

## Common UI Elements (All Tabs)

### Confidence Indicator
```
[Apply] button color based on confidence:
• Green:  ≥ 70% (high confidence)
• Yellow: 50-69% (moderate)
• Orange: 30-49% (low)
• Red:    < 30% (very low)
```

### Action Buttons
- **[Apply]**: Executes change immediately
- **[Preview]**: Highlights affected elements (no change)
- **[Undo Last]**: Reverts last applied change
- **[Clear All]**: Removes all detected issues from display

### Issue Priority Icons
- 🔴 **Critical**: Prevents model execution (dead transitions, empty siphons)
- ⚠️  **Warning**: Reduces model quality (missing rates, low confidence)
- 💡 **Suggestion**: Potential improvements (optimization, best practices)

---

## Implementation Priority

### Phase 3.1: Core Infrastructure (Week 1)
- Implement `Issue`, `Suggestion`, `Change`, `BoundaryAnalysis` dataclasses
- Implement locality filtering in KB methods
- Add `get_locality_elements()` method
- Build Undo stack mechanism

### Phase 3.2: Structural Tab (Week 2)
- Issue detection for dead transitions
- Initial marking inference
- Source placement suggestions
- Apply/Preview/Undo buttons
- **Locality filtering** for structural issues

### Phase 3.3: Kinetic Tab (Week 3)
- Firing rate inference
- BRENDA integration display
- Batch rate assignment
- **Locality-aware** rate suggestions

### Phase 3.4: Biological Tab (Week 4)
- Arc weight inference (stoichiometry)
- Conservation law verification
- Compound mapping suggestions
- **Boundary analysis** for stoichiometry

### Phase 3.5: Diagnosis Tab with Localities (Week 5)
- Locality selection dropdown
- Multi-domain issue cards (combined suggestions)
- Health score calculation (per locality)
- Boundary analysis UI
- Batch operations ("Fix All" in locality)
- Report export (locality-specific)
- Comparative analysis (locality vs locality)

---

## Locality Integration Details

### How Localities Work in Shypn

Shypn already has a locality system in the Analyses Panel that allows users to:
1. Select model elements (places, transitions, arcs)
2. Group them into named localities (e.g., "Glycolysis Upper Phase")
3. Save/load locality definitions
4. Run analyses on specific localities

The Viability Panel will **reuse this system** by:
- Reading existing locality definitions
- Filtering KB queries by locality membership
- Providing locality-aware suggestions
- Respecting locality boundaries in inference

### Data Flow with Localities

```
1. User selects locality in dropdown
   ↓
2. viability_panel.py gets locality elements from analyses_panel
   ↓
3. viability_panel.py calls kb.scan_locality_issues(locality_id)
   ↓
4. KB filters places/transitions/arcs to those in locality
   ↓
5. KB runs inference methods only on filtered elements
   ↓
6. KB also analyzes boundary (elements connecting to outside)
   ↓
7. Returns Issues with locality_id and is_boundary_issue flags
   ↓
8. UI displays locality-specific issues + boundary analysis
```

### Example: Locality-Filtered Diagnosis

**Scenario**: User selects "Glycolysis Upper Phase" locality

**KB Processing**:
```python
def scan_locality_issues(self, locality_id: str) -> Dict[str, List[Issue]]:
    # Get elements in this locality
    locality_elements = self.get_locality_elements(locality_id)
    places = locality_elements['places']
    transitions = locality_elements['transitions']
    arcs = locality_elements['arcs']
    
    issues = {
        'structural': [],
        'biological': [],
        'kinetic': []
    }
    
    # Structural issues (only in locality)
    for trans_id in transitions:
        trans = self.transitions[trans_id]
        if trans.liveness_level == 'dead':
            # Multi-domain analysis for this transition
            multi_suggestions = self.get_multi_domain_suggestions(trans_id, 'transition')
            
            issue = Issue(
                severity='critical',
                category='structural',
                title=f'Transition {trans_id} is DEAD',
                affected_elements=[trans_id],
                locality_id=locality_id,
                is_boundary_issue=self._is_boundary_element(trans_id, locality_elements),
                suggestions=multi_suggestions['structural'],
                multi_domain_suggestions=multi_suggestions
            )
            issues['structural'].append(issue)
    
    # Kinetic issues (only in locality)
    for trans_id in transitions:
        trans = self.transitions[trans_id]
        if trans.current_rate is None:
            issue = Issue(
                severity='warning',
                category='kinetic',
                title=f'Transition {trans_id} has no firing rate',
                affected_elements=[trans_id],
                locality_id=locality_id,
                suggestions=self._get_rate_suggestions(trans_id)
            )
            issues['kinetic'].append(issue)
    
    # Biological issues (arcs in locality)
    for arc_id in arcs:
        arc = self.arcs[arc_id]
        if arc.stoichiometry and arc.current_weight != arc.stoichiometry:
            issue = Issue(
                severity='warning',
                category='biological',
                title=f'Arc {arc_id} stoichiometry mismatch',
                affected_elements=[arc_id],
                locality_id=locality_id,
                suggestions=self._get_stoichiometry_suggestions(arc_id)
            )
            issues['biological'].append(issue)
    
    return issues

def get_multi_domain_suggestions(self, element_id: str, element_type: str) -> Dict[str, List[Suggestion]]:
    """Get suggestions from all relevant categories for a single element."""
    suggestions = {
        'structural': [],
        'biological': [],
        'kinetic': []
    }
    
    if element_type == 'transition':
        trans = self.transitions[element_id]
        
        # Structural: Check if dead, suggest marking
        if trans.liveness_level == 'dead':
            # Find input places that are empty
            for arc_id, arc in self.arcs.items():
                if arc.target_id == element_id and arc.arc_type == 'place_to_transition':
                    place = self.places[arc.source_id]
                    if place.current_marking == 0:
                        marking_result = self.infer_initial_marking(place.place_id)
                        if marking_result:
                            tokens, confidence, reasoning = marking_result
                            suggestions['structural'].append(Suggestion(
                                action='set_marking',
                                category='structural',
                                parameters={'place_id': place.place_id, 'tokens': tokens},
                                confidence=confidence,
                                reasoning=reasoning
                            ))
        
        # Biological: Check compound concentrations
        for arc_id, arc in self.arcs.items():
            if arc.target_id == element_id:
                place = self.places[arc.source_id]
                if place.compound_id and place.basal_concentration:
                    tokens = int(place.basal_concentration)  # mM to tokens
                    suggestions['biological'].append(Suggestion(
                        action='set_marking',
                        category='biological',
                        parameters={'place_id': place.place_id, 'tokens': tokens},
                        confidence=0.7,
                        reasoning=f'Basal concentration: {place.basal_concentration} mM'
                    ))
        
        # Kinetic: Infer firing rate
        rate_result = self.infer_firing_rate(element_id)
        if rate_result:
            rate, confidence, reasoning = rate_result
            suggestions['kinetic'].append(Suggestion(
                action='set_rate',
                category='kinetic',
                parameters={'transition_id': element_id, 'rate': rate},
                confidence=confidence,
                reasoning=reasoning
            ))
    
    return suggestions
```

### UI Example: Multi-Domain Issue Card

When displaying an issue, show suggestions from all domains:

```
┌─────────────────────────────────────────────────────┐
│ 🔴 Transition T5 (Hexokinase) is DEAD               │
│    Location: "Glycolysis Upper Phase"               │
│    Impact: Blocks downstream pathway                │
│                                                      │
│    MULTI-DOMAIN SUGGESTIONS:                        │
│    ┌───────────────────────────────────────────────┐│
│    │ 🏗️ STRUCTURAL (80% confidence)                ││
│    │    Add 5 tokens to P3 (Glucose)               ││
│    │    Reason: Feeds dead transition              ││
│    │    [Apply]                                    ││
│    ├───────────────────────────────────────────────┤│
│    │ 🧬 BIOLOGICAL (70% confidence)                ││
│    │    Add 5 tokens to P3 (Glucose)               ││
│    │    Reason: Basal concentration 5 mM           ││
│    │    [Apply]                                    ││
│    ├───────────────────────────────────────────────┤│
│    │ ⚡ KINETIC (60% confidence)                    ││
│    │    Set rate = 2.3 s⁻¹                         ││
│    │    Reason: BRENDA Vmax (EC 2.7.1.1)           ││
│    │    [Apply]                                    ││
│    └───────────────────────────────────────────────┘│
│                                                      │
│    [Apply All 3 Fixes]  [Apply Best (80%)]          │
│    [Preview on Canvas]  [Dismiss]                   │
└─────────────────────────────────────────────────────┘
```

Notice:
- **Same issue** (dead transition) gets **3 different perspectives**
- Structural: Add tokens (topology reasoning)
- Biological: Add tokens (biochemical reasoning - basal concentration)
- Kinetic: Set rate (BRENDA data)
- User can apply individually or **all at once**
- "Apply Best" uses highest confidence suggestion

---

## Technical Implementation Notes

### Data Flow
```
1. User clicks [Scan for Issues]
   ↓
2. viability_panel.py calls kb.scan_structural_issues()
   ↓
3. KB runs all inference methods, returns Issue objects
   ↓
4. viability_panel.py populates GTK TreeView/ListBox
   ↓
5. User clicks [Apply] button
   ↓
6. viability_panel.py calls model_canvas.apply_suggestion()
   ↓
7. model_canvas updates model, marks as modified
   ↓
8. UI refreshes (canvas redraws, panels update)
```

### New KB Methods Needed
```python
# Locality-aware scanning
def scan_structural_issues(locality_id: Optional[str] = None) -> List[Issue]
def scan_biological_issues(locality_id: Optional[str] = None) -> List[Issue]
def scan_kinetic_issues(locality_id: Optional[str] = None) -> List[Issue]
def scan_locality_issues(locality_id: str) -> Dict[str, List[Issue]]  # All categories
def scan_all_issues() -> List[Issue]

# Health scoring (locality-aware)
def calculate_structural_health(locality_id: Optional[str] = None) -> float
def calculate_biological_health(locality_id: Optional[str] = None) -> float
def calculate_kinetic_health(locality_id: Optional[str] = None) -> float
def calculate_overall_health(locality_id: Optional[str] = None) -> float

# Batch fixes (locality-aware)
def fix_all_dead_transitions(locality_id: Optional[str] = None) -> List[Change]
def assign_all_rates(confidence_threshold=0.5, locality_id: Optional[str] = None) -> List[Change]
def fix_all_stoichiometry(locality_id: Optional[str] = None) -> List[Change]
def apply_all_suggestions(confidence_threshold=0.7, locality_id: Optional[str] = None) -> List[Change]

# Locality-specific analysis
def analyze_locality_boundaries(locality_id: str) -> BoundaryAnalysis
def get_locality_elements(locality_id: str) -> Dict[str, List[str]]  # {places, transitions, arcs}
def compare_localities(locality_id_1: str, locality_id_2: str) -> ComparisonReport
def get_locality_coverage(locality_id: str) -> Dict[str, float]  # Coverage percentages

# Multi-domain suggestions (NEW!)
def get_multi_domain_suggestions(element_id: str, element_type: str) -> Dict[str, Suggestion]
```

### Issue Data Structure (Enhanced)
```python
@dataclass
class Issue:
    severity: str  # "critical", "warning", "suggestion"
    category: str  # "structural", "biological", "kinetic"
    title: str
    description: str
    affected_elements: List[str]  # IDs
    locality_id: Optional[str] = None  # NEW: Which locality this belongs to
    is_boundary_issue: bool = False     # NEW: Affects locality boundary
    suggestions: List[Suggestion] = field(default_factory=list)
    multi_domain_suggestions: Dict[str, List[Suggestion]] = field(default_factory=dict)  # NEW!

@dataclass
class Suggestion:
    action: str  # "set_marking", "add_source", "set_rate", etc.
    category: str  # NEW: "structural", "biological", "kinetic"
    parameters: Dict[str, Any]
    confidence: float
    reasoning: str
    
@dataclass  
class Change:
    """Record of applied change (for undo)."""
    element_id: str
    element_type: str  # "place", "transition", "arc"
    property: str  # "tokens", "rate", "weight"
    old_value: Any
    new_value: Any
    timestamp: datetime
    locality_id: Optional[str] = None  # NEW: Track which locality was affected

@dataclass
class BoundaryAnalysis:
    """Analysis of locality boundaries."""
    locality_id: str
    input_places: List[Tuple[str, str, str]]  # (place_id, source_locality, status)
    output_places: List[Tuple[str, str, str]]  # (place_id, dest_locality, status)
    interface_transitions: List[str]
    boundary_issues: List[Issue]
    suggestions: List[Suggestion]

@dataclass
class ComparisonReport:
    """Comparison between two localities."""
    locality_1_id: str
    locality_2_id: str
    health_comparison: Dict[str, Tuple[float, float]]  # category -> (health1, health2)
    common_issues: List[str]
    unique_issues_1: List[Issue]
    unique_issues_2: List[Issue]
    recommendations: List[str]
```

---

## Next Steps

1. ✅ Review enhanced design with user (locality integration)
2. Implement `Issue`, `Suggestion`, `Change`, `BoundaryAnalysis`, `ComparisonReport` dataclasses
3. Implement locality filtering methods in KB
4. Implement `get_multi_domain_suggestions()` - key innovation!
5. Build GTK UI for Diagnosis tab first (most powerful)
6. Add locality selection dropdown (integrates with existing Analyses Panel)
7. Implement multi-domain issue cards
8. Add Preview highlighting on canvas
9. Implement Undo stack
10. Expand to individual category tabs (Structural, Kinetic, Biological)

**Estimated Total Time**: 5 weeks for full implementation

**Key Innovation**: Multi-domain suggestions let users see how **structural**, **biological**, and **kinetic** knowledge all contribute to solving the same issue. This is the "Master Mind" concept in action!
