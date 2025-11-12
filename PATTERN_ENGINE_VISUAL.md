# Pattern Recognition Engine - Visual Architecture

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                     PATTERN RECOGNITION ENGINE v1.0                          ║
║                        Multi-Domain Model Analysis                           ║
╚══════════════════════════════════════════════════════════════════════════════╝

┌──────────────────────────────────────────────────────────────────────────────┐
│  USER WORKFLOW                                                               │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. Load Model          →  SBML/PNML file loaded                           │
│  2. Run Simulation      →  Token dynamics captured                         │
│  3. Click "Analyze All" →  Pattern recognition triggered                   │
│  4. View Suggestions    →  Grouped by category with confidence             │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

                                      ↓

┌──────────────────────────────────────────────────────────────────────────────┐
│  KNOWLEDGE BASE                                                              │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Places                  Transitions              Arcs                       │
│  ├─ P1: Glucose         ├─ T1: Hexokinase        ├─ A1: T1 → P1            │
│  ├─ P2: ATP             ├─ T2: PFK-1             ├─ A2: P2 → T2            │
│  ├─ P3: Pyruvate        ├─ T3: Pyruvate DH       ├─ A3: T2 → P3            │
│  └─ ...                 └─ ...                    └─ ...                     │
│                                                                              │
│  Compounds               Reactions                SimulationTraces           │
│  ├─ C00031: Glucose     ├─ R00200: HK reaction   ├─ firing_counts          │
│  ├─ C00002: ATP         ├─ R00756: PFK-1         ├─ token_averages         │
│  └─ ...                 └─ ...                    └─ ...                     │
│                                                                              │
│  Arc Query API (NEW):                                                        │
│  • get_input_arcs_for_place(P1)      → List[transition → P1]              │
│  • get_output_arcs_for_place(P1)     → List[P1 → transition]              │
│  • get_input_arcs_for_transition(T1) → List[place → T1]                   │
│  • is_source_transition(T1)          → bool                                │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

                                      ↓

╔══════════════════════════════════════════════════════════════════════════════╗
║                      PATTERN RECOGNITION ENGINE                              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  ┌────────────────────┐  ┌────────────────────┐  ┌────────────────────┐   ║
║  │ STRUCTURAL         │  │ BIOCHEMICAL        │  │ KINETIC            │   ║
║  │ DETECTOR           │  │ DETECTOR           │  │ DETECTOR           │   ║
║  ├────────────────────┤  ├────────────────────┤  ├────────────────────┤   ║
║  │                    │  │                    │  │                    │   ║
║  │ 1. Dead-End        │  │ 4. Missing         │  │ 5. Rate Too Low    │   ║
║  │    ✓ P1: 10 tokens │  │    Cofactor        │  │                    │   ║
║  │      no outputs    │  │    • Check KEGG    │  │    • Has kinetic   │   ║
║  │                    │  │      reactions     │  │      but never     │   ║
║  │ 2. Bottleneck      │  │    • Compare with  │  │      fires         │   ║
║  │    • Token pile-up │  │      model         │  │                    │   ║
║  │    • High output   │  │                    │  │ 6. Missing         │   ║
║  │      weights       │  │                    │  │    Substrate       │   ║
║  │                    │  │                    │  │    ✓ T5: EC number │   ║
║  │ 3. Unused Path     │  │                    │  │      but constant  │   ║
║  │    • Competition   │  │                    │  │      rate          │   ║
║  │    • Never fires   │  │                    │  │                    │   ║
║  │                    │  │                    │  │ 7. Pathway         │   ║
║  │                    │  │                    │  │    Imbalance       │   ║
║  │                    │  │                    │  │    • Rate mismatch │   ║
║  │                    │  │                    │  │      in sequence   │   ║
║  │                    │  │                    │  │                    │   ║
║  └────────────────────┘  └────────────────────┘  └────────────────────┘   ║
║                                                                              ║
║                              AGGREGATES TO                                   ║
║                                    ↓                                         ║
║                                                                              ║
║  ┌─────────────────────────────────────────────────────────────────────┐   ║
║  │                        PATTERN AGGREGATOR                            │   ║
║  │                                                                      │   ║
║  │  Detected Patterns:                                                  │   ║
║  │  • PatternType.DEAD_END (1x, confidence=0.90)                       │   ║
║  │  • PatternType.MISSING_SUBSTRATE_DEPENDENCE (1x, confidence=0.85)   │   ║
║  │                                                                      │   ║
║  │  Evidence:                                                           │   ║
║  │  • P1: {current_tokens: 10, output_arcs: 0}                         │   ║
║  │  • T5: {ec_number: '1.1.1.1', has_kinetic_law: False}               │   ║
║  │                                                                      │   ║
║  └─────────────────────────────────────────────────────────────────────┘   ║
║                                    ↓                                         ║
║                                                                              ║
║  ┌─────────────────────────────────────────────────────────────────────┐   ║
║  │                        REPAIR SUGGESTER                              │   ║
║  │                                                                      │   ║
║  │  For Each Pattern:                                                   │   ║
║  │                                                                      │   ║
║  │  Dead-End (P1) →                                                     │   ║
║  │    ✓ Add output transition (conf=0.90)                              │   ║
║  │      Parameters: {suggested_label: 'Consume_Glucose'}               │   ║
║  │      Rationale: "Place accumulates 10 tokens with no way out"       │   ║
║  │                                                                      │   ║
║  │    • Mark as intentional sink (conf=0.70)                           │   ║
║  │      Parameters: {is_sink: True}                                    │   ║
║  │      Rationale: "If accumulation is intentional"                    │   ║
║  │                                                                      │   ║
║  │  Missing Kinetic Law (T5) →                                          │   ║
║  │    ✓ Add Michaelis-Menten kinetics (conf=0.90)                     │   ║
║  │      Parameters: {kinetic_law: 'michaelis_menten(P4, ...)'}        │   ║
║  │      Rationale: "Enzyme should have substrate-dependent rate"       │   ║
║  │                                                                      │   ║
║  └─────────────────────────────────────────────────────────────────────┘   ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

                                      ↓

┌──────────────────────────────────────────────────────────────────────────────┐
│  VIABILITY OBSERVER INTEGRATION                                              │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  def generate_all_suggestions(kb, simulation_data):                         │
│                                                                              │
│      # Traditional diagnosis (existing)                                      │
│      inactive_transitions = kb.get_inactive_transitions()                   │
│      for trans_id in inactive_transitions:                                   │
│          diagnosis = _diagnose_dead_transition(kb, trans_id)                │
│          suggestions['structural'].append(diagnosis)                         │
│                                                                              │
│      # Pattern recognition engine (NEW)                                      │
│      if PATTERN_ENGINE_AVAILABLE:                                            │
│          engine = PatternRecognitionEngine(kb)                              │
│          analysis = engine.analyze()                                         │
│                                                                              │
│          for suggestion in analysis['suggestions']:                          │
│              category = map_action_to_category(suggestion.action)           │
│              suggestions[category].append(convert_to_ui_format(suggestion)) │
│                                                                              │
│      return suggestions  # Dict[category, List[suggestion_dict]]            │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

                                      ↓

┌──────────────────────────────────────────────────────────────────────────────┐
│  USER INTERFACE (GTK TREEVIEW)                                               │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Viability Suggestions                                                │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │                                                                      │   │
│  │  STRUCTURAL (2 issues)                                               │   │
│  │  ● Add output transition from Glucose              [Conf: 0.90] ★★★ │   │
│  │    Rationale: Place accumulates 10 tokens with no way to remove     │   │
│  │    Action: add_output_transition → P1                               │   │
│  │                                                                      │   │
│  │  ○ Mark Glucose as intentional sink                [Conf: 0.70] ★★  │   │
│  │    Rationale: If token accumulation is intentional                  │   │
│  │                                                                      │   │
│  │  KINETIC (1 issue)                                                   │   │
│  │  ● Add Michaelis-Menten kinetics for T5           [Conf: 0.90] ★★★ │   │
│  │    Rationale: Enzyme (EC 1.1.1.1) should have substrate-dependent   │   │
│  │    Action: add_kinetic_law → michaelis_menten(P4, vmax=1.0, km=0.1)│   │
│  │                                                                      │   │
│  │  BIOLOGICAL (0 issues)                                               │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  Legend:                                                                     │
│  ★★★ = High confidence (≥0.85)    ● = Recommended                           │
│  ★★  = Medium confidence (0.70+)  ○ = Alternative                           │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘


╔══════════════════════════════════════════════════════════════════════════════╗
║                           DATA FLOW SUMMARY                                  ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  1. Model Loading       → KB populated with places/transitions/arcs         ║
║  2. Simulation          → KB updated with firing_counts, avg_tokens         ║
║  3. Pattern Detection   → 7 detectors scan KB for patterns                  ║
║  4. Evidence Collection → Each pattern stores detection evidence            ║
║  5. Repair Generation   → Suggester creates fixes with parameters           ║
║  6. UI Rendering        → Suggestions displayed grouped by category         ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝


╔══════════════════════════════════════════════════════════════════════════════╗
║                        PATTERN TYPE REFERENCE                                ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  STRUCTURAL PATTERNS                                                         ║
║  ├─ DEAD_END              Place with inputs but no outputs                  ║
║  ├─ BOTTLENECK            Token accumulation due to output constraints      ║
║  ├─ UNUSED_PATH           Competing transitions where some never fire       ║
║  └─ SOURCE_NO_RATE        Source transition without firing rate             ║
║                                                                              ║
║  BIOCHEMICAL PATTERNS                                                        ║
║  ├─ STOICHIOMETRY_MISMATCH   Arc weights don't match KEGG stoichiometry    ║
║  ├─ MISSING_COFACTOR         KEGG reaction requires absent compounds        ║
║  └─ REVERSIBILITY_ISSUE      Should be reversible but isn't                 ║
║                                                                              ║
║  KINETIC PATTERNS                                                            ║
║  ├─ RATE_TOO_LOW             Kinetic law but never fires                    ║
║  ├─ KM_MISMATCH              Km values don't match BRENDA data              ║
║  ├─ MISSING_SUBSTRATE_DEP    Enzyme using constant rate                     ║
║  └─ PATHWAY_IMBALANCE        Sequential transitions with rate mismatch      ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝


╔══════════════════════════════════════════════════════════════════════════════╗
║                      CONFIDENCE SCORING GUIDE                                ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  0.90-1.00  ★★★  HIGH        Strong evidence, clear pattern                 ║
║                              Example: Dead-end with 10 tokens                ║
║                                                                              ║
║  0.70-0.89  ★★   MEDIUM      Clear pattern, some assumptions                ║
║                              Example: Enzyme missing kinetic law             ║
║                                                                              ║
║  0.50-0.69  ★    LOW         Speculative, needs validation                  ║
║                              Example: Intentional sink vs error              ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```
