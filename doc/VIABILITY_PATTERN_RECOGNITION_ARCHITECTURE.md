# Viability System - Pattern Recognition Architecture

**Date:** November 11, 2025  
**Goal:** Transform viability system into intelligent pattern recognition engine  
**Status:** 🔄 DESIGN + PARTIAL IMPLEMENTATION

---

## 🎯 Vision

The viability system should automatically recognize patterns across **structure, biochemistry, and kinetics**, then suggest specific, actionable modifications to improve model behavior.

**Core Principle:** Multi-domain pattern matching with actionable repair suggestions.

---

## 🧠 Pattern Recognition Domains

### 1. **STRUCTURAL PATTERNS** (Topology)

#### Pattern: Dead Ends
```
Recognition:
  - Place with only input arcs (no outputs)
  - Token accumulation without consumption
  
Diagnosis:
  - "P5 is a dead-end: receives tokens but cannot pass them forward"
  
Suggestions:
  ✓ Add output transition
  ✓ Add arc to existing transition
  ✓ Make this a sink place (if intentional)
```

#### Pattern: Bottlenecks
```
Recognition:
  - High-weight input arcs + low-weight output arcs
  - Token buildup in place (from simulation)
  - Multiple inputs, single output with high arc weight
  
Diagnosis:
  - "P12 is bottleneck: accumulates tokens (avg=45) but output requires 10 tokens"
  
Suggestions:
  ✓ Reduce output arc weight (10 → 5)
  ✓ Add parallel output transition
  ✓ Increase output transition rate
```

#### Pattern: Source Without Rate
```
Recognition:
  - Transition with NO input arcs
  - NO kinetic_law AND NO rate defined
  - Never fired in simulation
  
Diagnosis:
  - "T35 is source but has no rate mechanism"
  
Suggestions:
  ✓ Set kinetic law: michaelis_menten(...)
  ✓ Set stochastic rate
  ✓ Add input places (if not truly a source)
```

#### Pattern: Unused Parallel Paths
```
Recognition:
  - Multiple transitions with same input places
  - One fires frequently, others never fire
  - Different arc weights or priorities
  
Diagnosis:
  - "T12 and T13 compete for P5 tokens, but T12 always wins"
  
Suggestions:
  ✓ Balance arc weights
  ✓ Adjust priorities
  ✓ Add guard conditions
```

---

### 2. **BIOCHEMICAL PATTERNS** (Biology)

#### Pattern: Stoichiometry Mismatch
```
Recognition:
  - Place mapped to compound (e.g., C00031 = Glucose)
  - Arc weight != biological stoichiometry
  - KEGG reaction shows different coefficients
  
Diagnosis:
  - "P1 (Glucose) has arc weight=1, but R00200 requires 2 ATP molecules"
  
Suggestions:
  ✓ Update arc weight to match stoichiometry (1 → 2)
  ✓ Split reaction into multiple steps
  ✓ Add cofactor places
```

#### Pattern: Missing Cofactors
```
Recognition:
  - Transition mapped to enzyme reaction
  - KEGG reaction lists cofactors (ATP, NADH, etc.)
  - No corresponding places in model
  
Diagnosis:
  - "T1 (Hexokinase/R00200) requires ATP but no ATP place connected"
  
Suggestions:
  ✓ Add place for C00002 (ATP)
  ✓ Add input arc: ATP → T1 (weight=1)
  ✓ Add output arc: T1 → ADP (weight=1)
```

#### Pattern: Reversibility Issues
```
Recognition:
  - Reaction marked reversible in KEGG
  - Model has only forward transition
  - No reverse transition exists
  
Diagnosis:
  - "R00200 is reversible but model only has forward transition T1"
  
Suggestions:
  ✓ Add reverse transition T1_rev
  ✓ Connect reverse arcs (products → T1_rev → substrates)
  ✓ Set reverse kinetic law
```

#### Pattern: Compartment Violations
```
Recognition:
  - Places have compartment metadata (cytosol, mitochondria)
  - Transition connects places from different compartments
  - No transporter mechanism
  
Diagnosis:
  - "T5 connects P1 (cytosol) to P10 (mitochondria) without transporter"
  
Suggestions:
  ✓ Add transport transition
  ✓ Add energy cost (ATP consumption)
  ✓ Verify compartment assignments
```

---

### 3. **KINETIC PATTERNS** (Dynamics)

#### Pattern: Rate Too Low
```
Recognition:
  - Transition has kinetic_law
  - Never fires or fires very rarely
  - Input places have sufficient tokens
  
Diagnosis:
  - "T5 has michaelis_menten(P1, vmax=0.01, km=5) but vmax too low"
  
Suggestions:
  ✓ Increase vmax (0.01 → 1.0)
  ✓ Decrease km (5 → 0.5) for higher affinity
  ✓ Query BRENDA for realistic parameters
```

#### Pattern: Missing Substrate Dependence
```
Recognition:
  - Transition is enzymatic (has EC number)
  - kinetic_law is constant rate, not substrate-dependent
  - Multiple input places (substrates)
  
Diagnosis:
  - "T3 (EC 2.7.1.1) uses constant rate but should depend on substrates P1, P2"
  
Suggestions:
  ✓ Replace with michaelis_menten(P1, vmax=?, km=?)
  ✓ Use multi_substrate_mm(P1, P2, ...)
  ✓ Query BRENDA for Km values
```

#### Pattern: Inhibition Not Modeled
```
Recognition:
  - Transition mapped to enzyme with known inhibitors
  - BRENDA shows competitive/non-competitive inhibition
  - No inhibitor places or arcs in model
  
Diagnosis:
  - "T1 (Hexokinase) is inhibited by G6P (P2) but no inhibition modeled"
  
Suggestions:
  ✓ Add inhibitor arc: P2 →[inhibitor]→ T1
  ✓ Use competitive_inhibition(P1, P2, vmax, km, ki)
  ✓ Add allosteric regulation
```

#### Pattern: Km Mismatch
```
Recognition:
  - Transition has kinetic_law with Km parameter
  - BRENDA database has experimental Km values
  - Model Km differs significantly from literature
  
Diagnosis:
  - "T1 uses km=5, but BRENDA reports km=0.1-0.5 mM for human hexokinase"
  
Suggestions:
  ✓ Update km to 0.3 mM (BRENDA median)
  ✓ Use organism-specific value
  ✓ Add confidence bounds
```

#### Pattern: Unbalanced Pathway
```
Recognition:
  - Linear pathway: T1 → P1 → T2 → P2 → T3
  - T1 fires fast, T2 slow, T3 medium
  - P1 accumulates tokens
  
Diagnosis:
  - "Pathway bottleneck at T2 (rate=0.1) vs T1 (rate=10)"
  
Suggestions:
  ✓ Increase T2 rate to match T1
  ✓ Decrease T1 rate to match T2
  ✓ Add regulation (feedback inhibition)
```

---

## 🔧 Implementation Architecture

### Current State (Partial)

```
┌─────────────────────────────────────────────────────────┐
│  VIABILITY OBSERVER                                     │
│  - Records events (simulation, topology)               │
│  - Applies rules to generate suggestions               │
│  - Notifies categories                                 │
└─────────────────────────────────────────────────────────┘
                           │
         ┌─────────────────┼─────────────────┐
         ▼                 ▼                  ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│ STRUCTURAL  │  │ BIOLOGICAL  │  │  KINETIC    │
│  Category   │  │  Category   │  │  Category   │
└─────────────┘  └─────────────┘  └─────────────┘
         │                 │                  │
         └─────────────────┴──────────────────┘
                           │
                           ▼
                ┌─────────────────────┐
                │ KNOWLEDGE BASE (KB) │
                │  - Topology         │
                │  - Simulation       │
                │  - Biochemistry     │
                │  - Kinetics         │
                └─────────────────────┘
```

### Enhanced Architecture (Target)

```
┌───────────────────────────────────────────────────────────┐
│  PATTERN RECOGNITION ENGINE                               │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  Multi-Domain Analyzers                             │  │
│  │  - Structural Analyzer                              │  │
│  │  - Biochemical Analyzer                             │  │
│  │  - Kinetic Analyzer                                 │  │
│  │  - Cross-Domain Correlator                          │  │
│  └─────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────┘
                           │
         ┌─────────────────┼─────────────────┐
         ▼                 ▼                  ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ PATTERN LIBRARY │ │ REPAIR SUGGESTER│ │ CONFIDENCE      │
│ - Template      │ │ - Actionable    │ │ SCORER          │
│   patterns      │ │   repairs       │ │ - Based on      │
│ - Thresholds    │ │ - Parameter     │ │   evidence      │
│ - Heuristics    │ │   values        │ │   quality       │
└─────────────────┘ └─────────────────┘ └─────────────────┘
         │                 │                  │
         └─────────────────┴──────────────────┘
                           │
                           ▼
                ┌─────────────────────┐
                │ KNOWLEDGE BASE (KB) │
                │  + BRENDA API       │
                │  + KEGG API         │
                └─────────────────────┘
```

---

## 📋 Pattern Detection Methods

### Structural Pattern Detection

```python
class StructuralPatternAnalyzer:
    """Detects topological patterns."""
    
    def detect_dead_ends(self, kb) -> List[Pattern]:
        """Places with no output arcs."""
        patterns = []
        for place_id, place in kb.places.items():
            output_arcs = kb.get_output_arcs_for_place(place_id)
            if not output_arcs and place.current_marking > 0:
                patterns.append(DeadEndPattern(
                    place_id=place_id,
                    tokens=place.current_marking,
                    confidence=0.9
                ))
        return patterns
    
    def detect_bottlenecks(self, kb) -> List[Pattern]:
        """Places with token accumulation."""
        patterns = []
        for place_id, place in kb.places.items():
            if place.avg_tokens > place.initial_marking * 3:
                input_weight = sum(a.current_weight for a in kb.get_input_arcs_for_place(place_id))
                output_weight = sum(a.current_weight for a in kb.get_output_arcs_for_place(place_id))
                
                if output_weight > input_weight * 2:
                    patterns.append(BottleneckPattern(
                        place_id=place_id,
                        avg_tokens=place.avg_tokens,
                        input_weight=input_weight,
                        output_weight=output_weight,
                        confidence=0.85
                    ))
        return patterns
    
    def detect_unused_paths(self, kb) -> List[Pattern]:
        """Competing transitions with unequal usage."""
        patterns = []
        # Group transitions by input places
        groups = self._group_by_inputs(kb)
        
        for input_set, transitions in groups.items():
            if len(transitions) > 1:
                firings = [kb.transitions[t].firing_count for t in transitions]
                if max(firings) > 0 and min(firings) == 0:
                    patterns.append(UnusedPathPattern(
                        active_transition=transitions[firings.index(max(firings))],
                        unused_transitions=[t for t, f in zip(transitions, firings) if f == 0],
                        confidence=0.75
                    ))
        return patterns
```

### Biochemical Pattern Detection

```python
class BiochemicalPatternAnalyzer:
    """Detects biological consistency issues."""
    
    def __init__(self, kegg_api, brenda_api):
        self.kegg = kegg_api
        self.brenda = brenda_api
    
    def detect_stoichiometry_mismatch(self, kb) -> List[Pattern]:
        """Compare model arcs with KEGG stoichiometry."""
        patterns = []
        
        for trans_id, trans in kb.transitions.items():
            if trans.reaction_id:  # Has KEGG mapping
                kegg_reaction = self.kegg.get_reaction(trans.reaction_id)
                model_stoich = self._get_model_stoichiometry(kb, trans_id)
                kegg_stoich = kegg_reaction.stoichiometry
                
                mismatches = self._compare_stoichiometry(model_stoich, kegg_stoich)
                if mismatches:
                    patterns.append(StoichiometryMismatchPattern(
                        transition_id=trans_id,
                        mismatches=mismatches,
                        confidence=0.95
                    ))
        return patterns
    
    def detect_missing_cofactors(self, kb) -> List[Pattern]:
        """Find required cofactors not in model."""
        patterns = []
        
        for trans_id, trans in kb.transitions.items():
            if trans.reaction_id:
                kegg_reaction = self.kegg.get_reaction(trans.reaction_id)
                required_compounds = set(kegg_reaction.substrates + kegg_reaction.products)
                
                model_compounds = set()
                for arc in kb.get_input_arcs_for_transition(trans_id):
                    place = kb.places[arc.source_id]
                    if place.compound_id:
                        model_compounds.add(place.compound_id)
                
                missing = required_compounds - model_compounds
                if missing:
                    patterns.append(MissingCofactorPattern(
                        transition_id=trans_id,
                        missing_compounds=missing,
                        confidence=0.85
                    ))
        return patterns
```

### Kinetic Pattern Detection

```python
class KineticPatternAnalyzer:
    """Detects kinetic formulation issues."""
    
    def detect_rate_too_low(self, kb) -> List[Pattern]:
        """Find transitions with insufficient rates."""
        patterns = []
        
        for trans_id, trans in kb.transitions.items():
            if trans.kinetic_law and trans.firing_count == 0:
                input_arcs = kb.get_input_arcs_for_transition(trans_id)
                all_sufficient = all(
                    kb.places[arc.source_id].current_marking >= arc.current_weight
                    for arc in input_arcs
                )
                
                if all_sufficient:
                    # Has tokens but never fired → rate too low
                    params = self._extract_kinetic_params(trans.kinetic_law)
                    patterns.append(RateTooLowPattern(
                        transition_id=trans_id,
                        current_params=params,
                        confidence=0.8
                    ))
        return patterns
    
    def detect_km_mismatch(self, kb, brenda_api) -> List[Pattern]:
        """Compare model Km with BRENDA values."""
        patterns = []
        
        for trans_id, trans in kb.transitions.items():
            if trans.ec_number and trans.kinetic_law:
                model_km = self._extract_km(trans.kinetic_law)
                if model_km:
                    brenda_kms = brenda_api.get_km_values(trans.ec_number)
                    if brenda_kms:
                        median_km = np.median(brenda_kms)
                        if abs(model_km - median_km) / median_km > 0.5:  # >50% difference
                            patterns.append(KmMismatchPattern(
                                transition_id=trans_id,
                                model_km=model_km,
                                brenda_median=median_km,
                                confidence=0.7
                            ))
        return patterns
```

---

## 🔨 Repair Suggestion Generation

### Structural Repairs

```python
class StructuralRepairSuggester:
    """Generate actionable structural repairs."""
    
    def suggest_for_dead_end(self, pattern: DeadEndPattern, kb) -> List[RepairSuggestion]:
        """Suggest fixes for dead-end places."""
        return [
            RepairSuggestion(
                action="add_output_transition",
                target=pattern.place_id,
                description=f"Add output transition from {pattern.place_id}",
                confidence=0.9,
                parameters={}
            ),
            RepairSuggestion(
                action="make_sink",
                target=pattern.place_id,
                description=f"Mark {pattern.place_id} as intentional sink",
                confidence=0.7,
                parameters={'is_sink': True}
            )
        ]
    
    def suggest_for_bottleneck(self, pattern: BottleneckPattern, kb) -> List[RepairSuggestion]:
        """Suggest fixes for bottlenecks."""
        new_weight = int(pattern.output_weight / 2)
        return [
            RepairSuggestion(
                action="reduce_arc_weight",
                target=pattern.place_id,
                description=f"Reduce output arc weights ({pattern.output_weight} → {new_weight})",
                confidence=0.85,
                parameters={'new_weight': new_weight}
            ),
            RepairSuggestion(
                action="add_parallel_transition",
                target=pattern.place_id,
                description=f"Add parallel output transition",
                confidence=0.7,
                parameters={}
            )
        ]
```

### Biochemical Repairs

```python
class BiochemicalRepairSuggester:
    """Generate actionable biochemical repairs."""
    
    def suggest_for_stoichiometry_mismatch(self, pattern, kb) -> List[RepairSuggestion]:
        """Suggest stoichiometry corrections."""
        suggestions = []
        for mismatch in pattern.mismatches:
            suggestions.append(RepairSuggestion(
                action="update_arc_weight",
                target=mismatch.arc_id,
                description=f"Update {mismatch.compound} arc weight {mismatch.model_weight} → {mismatch.kegg_weight}",
                confidence=0.95,
                parameters={
                    'current_weight': mismatch.model_weight,
                    'correct_weight': mismatch.kegg_weight,
                    'source': 'KEGG'
                }
            ))
        return suggestions
    
    def suggest_for_missing_cofactor(self, pattern, kb, kegg_api) -> List[RepairSuggestion]:
        """Suggest adding missing cofactors."""
        suggestions = []
        for compound_id in pattern.missing_compounds:
            compound = kegg_api.get_compound(compound_id)
            suggestions.append(RepairSuggestion(
                action="add_cofactor_place",
                target=pattern.transition_id,
                description=f"Add place for {compound.name} ({compound_id})",
                confidence=0.85,
                parameters={
                    'compound_id': compound_id,
                    'compound_name': compound.name,
                    'stoichiometry': 1  # Default, could be inferred
                }
            ))
        return suggestions
```

### Kinetic Repairs

```python
class KineticRepairSuggester:
    """Generate actionable kinetic repairs."""
    
    def suggest_for_rate_too_low(self, pattern, kb, brenda_api) -> List[RepairSuggestion]:
        """Suggest rate parameter adjustments."""
        suggestions = []
        
        if 'vmax' in pattern.current_params:
            current_vmax = pattern.current_params['vmax']
            # Suggest 10x increase as starting point
            suggestions.append(RepairSuggestion(
                action="update_kinetic_parameter",
                target=pattern.transition_id,
                description=f"Increase vmax ({current_vmax} → {current_vmax * 10})",
                confidence=0.75,
                parameters={
                    'parameter': 'vmax',
                    'current_value': current_vmax,
                    'suggested_value': current_vmax * 10,
                    'reason': 'Transition never fires despite sufficient substrates'
                }
            ))
        
        # Query BRENDA for realistic values
        trans = kb.transitions[pattern.transition_id]
        if trans.ec_number:
            brenda_params = brenda_api.get_kinetic_parameters(trans.ec_number)
            if brenda_params:
                suggestions.append(RepairSuggestion(
                    action="use_brenda_parameters",
                    target=pattern.transition_id,
                    description=f"Use BRENDA parameters: vmax={brenda_params.vmax_median}, km={brenda_params.km_median}",
                    confidence=0.8,
                    parameters=brenda_params.to_dict()
                ))
        
        return suggestions
```

---

## 🎯 Cross-Domain Pattern Correlation

Some patterns only emerge when combining multiple domains:

```python
class CrossDomainCorrelator:
    """Correlate patterns across domains."""
    
    def correlate(self, structural_patterns, biochemical_patterns, kinetic_patterns):
        """Find related patterns across domains."""
        correlations = []
        
        # Example: Bottleneck + Missing Cofactor
        for bottleneck in structural_patterns:
            if isinstance(bottleneck, BottleneckPattern):
                # Check if downstream transition is missing cofactor
                downstream_trans = self._get_downstream_transitions(bottleneck.place_id)
                for trans_id in downstream_trans:
                    missing_cofactor = self._find_pattern(
                        biochemical_patterns,
                        MissingCofactorPattern,
                        transition_id=trans_id
                    )
                    if missing_cofactor:
                        correlations.append(CorrelatedPattern(
                            primary=bottleneck,
                            secondary=missing_cofactor,
                            hypothesis="Bottleneck might resolve if cofactor is added",
                            confidence=0.7
                        ))
        
        # Example: Low Rate + Km Mismatch
        for low_rate in kinetic_patterns:
            if isinstance(low_rate, RateTooLowPattern):
                km_mismatch = self._find_pattern(
                    kinetic_patterns,
                    KmMismatchPattern,
                    transition_id=low_rate.transition_id
                )
                if km_mismatch:
                    correlations.append(CorrelatedPattern(
                        primary=low_rate,
                        secondary=km_mismatch,
                        hypothesis="Correcting Km might resolve firing issue",
                        confidence=0.85
                    ))
        
        return correlations
```

---

## 📊 Confidence Scoring

```python
class ConfidenceScorer:
    """Calculate suggestion confidence."""
    
    def score(self, pattern, kb) -> float:
        """Calculate confidence score (0.0-1.0)."""
        base_confidence = pattern.confidence
        
        # Boost confidence if multiple data sources agree
        if self._has_kegg_mapping(pattern, kb):
            base_confidence += 0.1
        
        if self._has_brenda_data(pattern, kb):
            base_confidence += 0.1
        
        if self._has_simulation_evidence(pattern, kb):
            base_confidence += 0.05
        
        if self._has_topology_evidence(pattern, kb):
            base_confidence += 0.05
        
        return min(base_confidence, 1.0)
```

---

## 🚀 Implementation Roadmap

### Phase 1: Core Pattern Detectors (HIGH PRIORITY)
- [x] Dead transition diagnosis (basic)
- [ ] Dead-end place detection
- [ ] Bottleneck detection
- [ ] Stoichiometry mismatch detection
- [ ] Missing cofactor detection

### Phase 2: Repair Suggesters (HIGH PRIORITY)
- [ ] Structural repair suggester
- [ ] Biochemical repair suggester
- [ ] Kinetic repair suggester
- [ ] Parameter value suggestions from BRENDA

### Phase 3: Advanced Patterns (MEDIUM PRIORITY)
- [ ] Unused path detection
- [ ] Km mismatch detection
- [ ] Rate too low detection
- [ ] Reversibility issues
- [ ] Compartment violations

### Phase 4: Cross-Domain Correlation (LOW PRIORITY)
- [ ] Pattern correlator
- [ ] Confidence scorer
- [ ] Hypothesis generator
- [ ] Repair priority ranker

---

## 💡 Example Output

**Current (Basic):**
```
❌ T5 is source with NO rate
```

**Target (Intelligent):**
```
🔍 PATTERN: Source Without Rate Mechanism
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Transition: T5 / R00014 / Hexokinase
Issue: Source transition has no input places and no rate definition

DIAGNOSIS:
  ✗ No input arcs detected
  ✗ No kinetic_law defined
  ✗ No stochastic rate set
  ✓ Has KEGG mapping (R00014)
  ✓ Has EC number (2.7.1.1)

EVIDENCE:
  • Topology analysis: Confirmed source (0 input arcs)
  • Simulation: Never fired (0/10000 steps)
  • BRENDA: Enzyme data available

SUGGESTIONS (Ranked by Confidence):

1. [●●●●●○] Set Michaelis-Menten kinetics (Confidence: 0.90)
   Action: Add kinetic_law = "michaelis_menten(P14, vmax=1.0, km=0.1)"
   Rationale: Enzyme reaction should depend on substrate concentration
   Data source: BRENDA suggests vmax=0.8-1.2, km=0.05-0.15 for human hexokinase

2. [●●●●○○] Add input places (Confidence: 0.75)
   Action: Connect substrate place(s) to T5
   Rationale: R00014 requires Glucose (C00031) + ATP (C00002) as substrates
   Missing: No ATP place connected

3. [●●●○○○] Set stochastic rate (Confidence: 0.60)
   Action: Set rate = 0.5 tokens/sec
   Rationale: For boundary condition/external input
   Note: Less biologically accurate than Michaelis-Menten

RELATED PATTERNS:
  → Missing Cofactor: T5 requires ATP (C00002) - not connected
  → Stoichiometry: KEGG shows 1:1 ratio for Glucose:ATP

APPLY SUGGESTION? [1/2/3/Dismiss]
```

---

## 🔬 Technical Implementation Notes

### Data Requirements
- KB must store: topology, simulation traces, biochemical mappings, kinetic laws
- External APIs: KEGG (stoichiometry), BRENDA (kinetic parameters)
- Pattern library: Pre-defined pattern templates with thresholds

### Performance Considerations
- Pattern detection should be incremental (not full rescan)
- Cache KEGG/BRENDA queries
- Lazy evaluation: Only detect patterns when user requests analysis
- Parallel pattern detection across domains

### User Experience
- Show patterns grouped by domain
- Allow user to accept/reject suggestions
- Track which suggestions were applied
- Learn from user choices (future: ML-based ranking)

---

**Status:** Architecture defined, basic implementation exists, needs enhancement.
**Next Steps:** Implement Phase 1 pattern detectors with repair suggesters.
