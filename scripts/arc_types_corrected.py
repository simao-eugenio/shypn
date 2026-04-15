#!/usr/bin/env python3
"""
CORRECTED: Arc Type Semantics in shypn
Understanding the difference between NORMAL, TEST, and SIGNAL_FLOW arcs
"""

print("="*80)
print("ARC TYPE SEMANTICS - CORRECTED")
print("="*80)
print()

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                    ARC TYPES: TOKEN CONSUMPTION                             ║
╚════════════════════════════════════════════════════════════════════════════╝

❌ MY ERROR: I incorrectly said signal_flow arcs don't consume tokens

✅ CORRECT SEMANTICS:
───────────────────

1. NORMAL ARCS (32 in your model)
   ─────────────────────────────────
   • Consume tokens from source place
   • Produce tokens at target place
   • Represent MASS TRANSFER (substrates, products)
   
   Example: Glucose + ATP → Glucose-6-P + ADP
            ├─ Glucose consumed (normal arc)
            └─ G6P produced (normal arc)

2. TEST ARCS (24 in your model)
   ───────────────────────────────
   • DO NOT consume tokens
   • Only CHECK presence (≥ weight)
   • Represent CATALYSTS/ENZYMES (read-only)
   
   Example: Glucose + ATP --[Hexokinase]--> G6P + ADP
                            └─ Test arc (enzyme not consumed)
   
   Code confirmation:
   ──────────────────
   class TestArc(Arc):
       def consumes_tokens(self) -> bool:
           return False  # ← Non-consuming!

3. SIGNAL_FLOW ARCS (35 in your model) ✅ DO CONSUME TOKENS
   ──────────────────────────────────────────────────────────
   • DO consume tokens from source
   • Represent INFORMATION TRANSFER with signal depletion
   • Enable hierarchical control through commitment
   
   Example: CII_Protein --signal_flow--> CI_Transcription
            └─ Signal consumed (commitment mechanism)
   
   Code confirmation:
   ──────────────────
   class SignalFlowArc(Arc):
       def consumes_tokens(self) -> bool:
           return True  # ← CONSUMES! (unlike test arcs)
   
   From docstring:
   "Signal flow arcs consume tokens to model signal depletion,
    distinguishing them from test arcs (non-consuming catalytic read)."


╔════════════════════════════════════════════════════════════════════════════╗
║                    WHY SIGNAL_FLOW ARCS CONSUME                             ║
╚════════════════════════════════════════════════════════════════════════════╝

🎯 Signal Depletion Mechanism:
──────────────────────────────
Signal flow arcs implement "hierarchical preemption" through token consumption:

  Enablement: M(signal_place) ≥ θ(transition) + W_s
                                                  └─ Signal weight (quota)
  
  Firing:     M'(signal_place) = M(signal_place) - W_s
                                                    └─ Consumes signal quota!

This creates:
  1. Basin boundaries (commitment thresholds)
  2. Irreversibility (once signal consumed, can't uncommit)
  3. Hierarchical control (higher layer depletes signals)

📊 In Your GATA1/PU.1 Model:
────────────────────────────

NORMAL arcs (32):
  • GATA1_mRNA_cyto → GATA1_translation (consumes mRNA)
  • GATA1_translation → GATA1_Protein_cyto (produces protein)
  • All substrate/product arcs

SIGNAL_FLOW arcs (35): ✅ CONSUME tokens
  • EPO_external → EPO_EPOR_binding (signal consumption)
  • ATP in rate formulas (energy charge coupling)
  • GTP for translation (cofactor consumption via separate mechanism)
  
  Example from simulation:
    EPO_external starts at 0, rises to 3 mM
    → Signal_flow arcs allow transitions to "read" AND "consume"
    → This is why EPO/GCSF have production/clearance transitions

TEST arcs (24): ✅ DO NOT consume
  • pH_cytoplasm → transitions (read pH, don't consume it)
  • pH_nucleus → transitions (constant parameter)
  • Mg_cytoplasm → transitions (cofactor check, not consumed)
  • Temperature → transitions (environmental parameter)
  
  These are constant parameters (capacity=Infinity)
  → Test arcs read them for rate calculations
  → Never depleted (no production/consumption needed)


╔════════════════════════════════════════════════════════════════════════════╗
║                    DISTINCTION SUMMARY                                      ║
╚════════════════════════════════════════════════════════════════════════════╝

┌─────────────────┬────────────┬──────────────┬─────────────────────────┐
│ Arc Type        │ Consumes?  │ Direction    │ Biological Role         │
├─────────────────┼────────────┼──────────────┼─────────────────────────┤
│ NORMAL          │ YES        │ P→T, T→P     │ Mass transfer           │
│ TEST            │ NO         │ P→T only     │ Catalyst (read-only)    │
│ SIGNAL_FLOW     │ YES        │ P→T, T→P     │ Information + depletion │
└─────────────────┴────────────┴──────────────┴─────────────────────────┘

Key Distinction (Test vs Signal Flow):
  TEST arc:        Enzyme present → reaction proceeds (enzyme not consumed)
  SIGNAL_FLOW arc: Signal present → transition fires → signal depleted


╔════════════════════════════════════════════════════════════════════════════╗
║                    CORRECTED MODEL ANALYSIS                                 ║
╚════════════════════════════════════════════════════════════════════════════╝

Your model has 91 arcs:

1. NORMAL arcs (32) - Mass transfer
   ──────────────────────────────────
   • mRNA_cyto → Translation (substrate consumption)
   • Translation → Protein_cyto (product formation)
   • ATP → ATP_synthesis (reactant)
   • All normal biochemical transformations

2. SIGNAL_FLOW arcs (35) - Information transfer WITH consumption
   ─────────────────────────────────────────────────────────────
   • EPO_external → EPO_EPOR_binding (signal consumed)
   • GCSF_external → GCSF_GCSFR_binding (signal consumed)
   • EPO_production → EPO_external (signal produced)
   • Energy metabolites (ATP, GTP) to transitions
   
   ✅ These DO consume/produce tokens
   ✅ Allow multiple transitions to sense same signal
   ✅ But signal is depleted when consumed (unlike test arcs)

3. TEST arcs (24) - Parameter reading WITHOUT consumption
   ────────────────────────────────────────────────────────
   • pH_cytoplasm → transitions (read pH value)
   • pH_nucleus → transitions (read pH value)
   • Mg_cytoplasm → transitions (read Mg concentration)
   • Temperature → transitions (read temperature)
   
   ✅ These NEVER consume tokens
   ✅ Pure read-only for constant parameters
   ✅ Capacity=Infinity (never depleted)


╔════════════════════════════════════════════════════════════════════════════╗
║                    APOLOGY & CLARIFICATION                                  ║
╚════════════════════════════════════════════════════════════════════════════╝

❌ MY MISTAKE:
   I incorrectly stated:
   "SIGNAL_FLOW arcs (35): Read signal without consuming"

✅ CORRECT STATEMENT:
   SIGNAL_FLOW arcs (35): Consume/produce tokens for information transfer
   TEST arcs (24): Read parameters without consuming (true non-consumptive)

The confusion arose because:
  • Signal_flow arcs connect to signal places (like test arcs)
  • Multiple transitions can read signal places (like test behavior)
  • BUT signal_flow arcs DO consume tokens (unlike test arcs)

The key semantic difference:
  • TEST arc = "Read sensor without depleting it"
  • SIGNAL_FLOW arc = "Transfer information and deplete signal quota"

Thank you for the correction!

""")

print("="*80)
print("Reference: src/shypn/netobjs/signal_flow_arc.py")
print("           src/shypn/netobjs/test_arc.py")
print("="*80)
