#!/usr/bin/env python3
"""
GATA1/PU.1 Lineage Commitment - Phase 1: Minimal Bistable Model
================================================================

Demonstrates emergent preemption through biochemical thresholds:
- Mutual inhibition (GATA1 -| PU.1, PU.1 -| GATA1)
- Positive feedback (GATA1 → GATA1, PU.1 → PU.1)
- Cytokine modulation (EPO boosts GATA1, G-CSF boosts PU.1)

Architecture based on Lambda Phage Switch (Biochemical-Examples/22).

Expected outcome: ~50:50 erythroid:myeloid distribution from symmetric initial conditions.

Author: Simão Eugénio
Date: February 14, 2026
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from shypn.data.canvas.document_model import DocumentModel
from shypn.netobjs.signal_type import SignalType

print("="*70)
print("Building GATA1/PU.1 Phase 1: Minimal Bistable Model")
print("="*70)

# Create new document
doc = DocumentModel()
doc.name = "GATA1_PU1_Minimal_Bistable"

# ============================================================================
# PLACES (8 total)
# ============================================================================
print("\n📍 Creating Places...")

# GATA1 module (Erythroid lineage)
p1_gata1_gene = doc.create_place(x=100, y=100, label="GATA1_Gene")
p1_gata1_gene.name = "GATA1_Gene"
p1_gata1_gene.initial_marking = 1  # Gene copy number
p1_gata1_gene.tokens = 1
print(f"✓ {p1_gata1_gene.id}: GATA1_Gene (catalyst)")

p2_gata1_mrna = doc.create_place(x=100, y=200, label="GATA1_mRNA")
p2_gata1_mrna.name = "GATA1_mRNA"
p2_gata1_mrna.initial_marking = 10  # Low symmetric start
p2_gata1_mrna.tokens = 10
print(f"✓ {p2_gata1_mrna.id}: GATA1_mRNA")

p3_gata1_protein = doc.create_place(x=100, y=300, label="GATA1_Protein")
p3_gata1_protein.name = "GATA1_Protein"
p3_gata1_protein.initial_marking = 50  # Symmetric with PU.1
p3_gata1_protein.tokens = 50
print(f"✓ {p3_gata1_protein.id}: GATA1_Protein")

# PU.1 module (Myeloid lineage)
p4_pu1_gene = doc.create_place(x=400, y=100, label="PU1_Gene")
p4_pu1_gene.name = "PU1_Gene"
p4_pu1_gene.initial_marking = 1  # Gene copy number
p4_pu1_gene.tokens = 1
print(f"✓ {p4_pu1_gene.id}: PU1_Gene (catalyst)")

p5_pu1_mrna = doc.create_place(x=400, y=200, label="PU1_mRNA")
p5_pu1_mrna.name = "PU1_mRNA"
p5_pu1_mrna.initial_marking = 10  # Low symmetric start
p5_pu1_mrna.tokens = 10
print(f"✓ {p5_pu1_mrna.id}: PU1_mRNA")

p6_pu1_protein = doc.create_place(x=400, y=300, label="PU1_Protein")
p6_pu1_protein.name = "PU1_Protein"
p6_pu1_protein.initial_marking = 50  # Symmetric with GATA1
p6_pu1_protein.tokens = 50
print(f"✓ {p6_pu1_protein.id}: PU1_Protein")

# Cytokine signals (QUORUM signal places)
p7_epo = doc.create_place(x=100, y=400, label="EPO_Signal")
p7_epo.name = "EPO_Signal"
p7_epo.initial_marking = 50  # Mid-level (titrate 0-100 later)
p7_epo.tokens = 50
p7_epo.is_signal_place = True
p7_epo.signal_type = SignalType.QUORUM  # Cytokine = cell communication
p7_epo.color = (0.0, 0.4, 0.8)  # Blue for signal places
print(f"✓ {p7_epo.id}: EPO_Signal [SIGNAL - cytokine]")

p8_gcsf = doc.create_place(x=400, y=400, label="GCSF_Signal")
p8_gcsf.name = "GCSF_Signal"
p8_gcsf.initial_marking = 0  # OFF for Phase 1 (erythroid bias)
p8_gcsf.tokens = 0
p8_gcsf.is_signal_place = True
p8_gcsf.signal_type = SignalType.QUORUM
p8_gcsf.color = (0.0, 0.4, 0.8)
print(f"✓ {p8_gcsf.id}: GCSF_Signal [SIGNAL - cytokine]")

# ============================================================================
# PARAMETERS (Symmetric - Critical for Balanced Bistability!)
# ============================================================================
print("\n⚙️  Setting Parameters...")

# Based on Lambda Phage balanced model (batch_20251217_171118: 42:48 split)
BASAL_TRANSCRIPTION = 2.0      # Symmetric basal rate (mM/s)
FEEDBACK_STRENGTH = 0.5        # Positive feedback coefficient
FEEDBACK_KM = 5.0              # Michaelis-Menten half-saturation (mM)
INHIBITION_KI = 15.0           # Inhibitor arc threshold (mM)
HILL_COOPERATIVITY = 2         # Hill coefficient for repression

TRANSLATION_RATE = 5.0         # mRNA → Protein (molecules/mRNA)
MRNA_DEGRADATION = 0.5         # mRNA decay rate (1/s)
PROTEIN_DEGRADATION = 0.1      # Protein decay rate (1/s)

CYTOKINE_BOOST_MAX = 2.0       # Maximum fold-change from cytokine
CYTOKINE_KM = 50.0             # Half-maximal cytokine response

print(f"  Basal transcription: {BASAL_TRANSCRIPTION} mM/s")
print(f"  Inhibition threshold: {INHIBITION_KI} mM (Hill n={HILL_COOPERATIVITY})")
print(f"  Feedback Km: {FEEDBACK_KM} mM")
print(f"  Cytokine boost: {CYTOKINE_BOOST_MAX}× max")

# ============================================================================
# TRANSITIONS (12 total)
# ============================================================================
print("\n🔄 Creating Transitions...")

# --- GATA1 Module ---

# T1: GATA1 Transcription (Stochastic)
# Positive feedback + PU.1 inhibition + EPO boost
# Rate = basal * (1 + feedback) / (1 + inhibition^n) * cytokine_boost
t1_gata1_txn = doc.create_transition(x=100, y=150, label="GATA1_Transcription")
t1_gata1_txn.name = "GATA1_Transcription"
t1_gata1_txn.transition_type = "stochastic"  # Gene expression noise
t1_gata1_txn.rate_function = (
    f"{BASAL_TRANSCRIPTION} * "
    f"(1 + {FEEDBACK_STRENGTH} * GATA1_Protein / ({FEEDBACK_KM} + GATA1_Protein)) / "
    f"(1 + (PU1_Protein / {INHIBITION_KI})**{HILL_COOPERATIVITY}) * "
    f"(1 + {CYTOKINE_BOOST_MAX} * EPO_Signal / ({CYTOKINE_KM} + EPO_Signal))"
)
print(f"✓ {t1_gata1_txn.id}: GATA1_Transcription (stochastic, with PU.1 inhibition)")

# T2: GATA1 Translation (Continuous)
t2_gata1_trl = doc.create_transition(x=100, y=250, label="GATA1_Translation")
t2_gata1_trl.name = "GATA1_Translation"
t2_gata1_trl.transition_type = "continuous"
t2_gata1_trl.rate_function = f"{TRANSLATION_RATE} * GATA1_mRNA"
print(f"✓ {t2_gata1_trl.id}: GATA1_Translation (continuous)")

# T3: GATA1 mRNA Degradation
t3_gata1_mrna_deg = doc.create_transition(x=50, y=200, label="GATA1_mRNA_Degradation")
t3_gata1_mrna_deg.name = "GATA1_mRNA_Degradation"
t3_gata1_mrna_deg.transition_type = "continuous"
t3_gata1_mrna_deg.rate_function = f"{MRNA_DEGRADATION} * GATA1_mRNA"
print(f"✓ {t3_gata1_mrna_deg.id}: GATA1_mRNA_Degradation")

# T4: GATA1 Protein Degradation
t4_gata1_prot_deg = doc.create_transition(x=50, y=300, label="GATA1_Protein_Degradation")
t4_gata1_prot_deg.name = "GATA1_Protein_Degradation"
t4_gata1_prot_deg.transition_type = "continuous"
t4_gata1_prot_deg.rate_function = f"{PROTEIN_DEGRADATION} * GATA1_Protein"
print(f"✓ {t4_gata1_prot_deg.id}: GATA1_Protein_Degradation")

# --- PU.1 Module (Perfectly Symmetric) ---

# T5: PU.1 Transcription (Stochastic)
# Positive feedback + GATA1 inhibition + G-CSF boost
t5_pu1_txn = doc.create_transition(x=400, y=150, label="PU1_Transcription")
t5_pu1_txn.name = "PU1_Transcription"
t5_pu1_txn.transition_type = "stochastic"
t5_pu1_txn.rate_function = (
    f"{BASAL_TRANSCRIPTION} * "
    f"(1 + {FEEDBACK_STRENGTH} * PU1_Protein / ({FEEDBACK_KM} + PU1_Protein)) / "
    f"(1 + (GATA1_Protein / {INHIBITION_KI})**{HILL_COOPERATIVITY}) * "
    f"(1 + {CYTOKINE_BOOST_MAX} * GCSF_Signal / ({CYTOKINE_KM} + GCSF_Signal))"
)
print(f"✓ {t5_pu1_txn.id}: PU1_Transcription (stochastic, symmetric with GATA1 inhibition)")

# T6: PU.1 Translation (Continuous)
t6_pu1_trl = doc.create_transition(x=400, y=250, label="PU1_Translation")
t6_pu1_trl.name = "PU1_Translation"
t6_pu1_trl.transition_type = "continuous"
t6_pu1_trl.rate_function = f"{TRANSLATION_RATE} * PU1_mRNA"
print(f"✓ {t6_pu1_trl.id}: PU1_Translation (continuous)")

# T7: PU.1 mRNA Degradation
t7_pu1_mrna_deg = doc.create_transition(x=450, y=200, label="PU1_mRNA_Degradation")
t7_pu1_mrna_deg.name = "PU1_mRNA_Degradation"
t7_pu1_mrna_deg.transition_type = "continuous"
t7_pu1_mrna_deg.rate_function = f"{MRNA_DEGRADATION} * PU1_mRNA"
print(f"✓ {t7_pu1_mrna_deg.id}: PU1_mRNA_Degradation")

# T8: PU.1 Protein Degradation
t8_pu1_prot_deg = doc.create_transition(x=450, y=300, label="PU1_Protein_Degradation")
t8_pu1_prot_deg.name = "PU1_Protein_Degradation"
t8_pu1_prot_deg.transition_type = "continuous"
t8_pu1_prot_deg.rate_function = f"{PROTEIN_DEGRADATION} * PU1_Protein"
print(f"✓ {t8_pu1_prot_deg.id}: PU1_Protein_Degradation")

# ============================================================================
# ARCS (28 total)
# ============================================================================
print("\n➡️  Creating Arcs...")

arc_count = 0

# --- GATA1 Transcription Arcs ---
# Gene catalyst (test arc)
doc.create_arc(source=p1_gata1_gene, target=t1_gata1_txn, weight=1, arc_type='test')
arc_count += 1

# Positive feedback (test arc - non-consuming)
doc.create_arc(source=p3_gata1_protein, target=t1_gata1_txn, weight=1, arc_type='test')
arc_count += 1

# EPO signal boost (test arc)
doc.create_arc(source=p7_epo, target=t1_gata1_txn, weight=1, arc_type='test')
arc_count += 1

# PU.1 sensing (test arc - read-only)
# Allows rate formula to access PU1_Protein for inhibition calculation
doc.create_arc(source=p6_pu1_protein, target=t1_gata1_txn, weight=1, arc_type='test')
arc_count += 1
print(f"  ✓ PU.1 -| GATA1 transcription (test arc + rate function)")

# mRNA output
doc.create_arc(source=t1_gata1_txn, target=p2_gata1_mrna, weight=1, arc_type='normal')
arc_count += 1

# --- GATA1 Translation Arcs ---
doc.create_arc(source=p2_gata1_mrna, target=t2_gata1_trl, weight=1, arc_type='normal')
doc.create_arc(source=t2_gata1_trl, target=p3_gata1_protein, weight=1, arc_type='normal')
arc_count += 2

# --- GATA1 Degradation Arcs ---
doc.create_arc(source=p2_gata1_mrna, target=t3_gata1_mrna_deg, weight=1, arc_type='normal')
doc.create_arc(source=p3_gata1_protein, target=t4_gata1_prot_deg, weight=1, arc_type='normal')
arc_count += 2

# --- PU.1 Transcription Arcs (Symmetric!) ---
# Gene catalyst
doc.create_arc(source=p4_pu1_gene, target=t5_pu1_txn, weight=1, arc_type='test')
arc_count += 1

# Positive feedback
doc.create_arc(source=p6_pu1_protein, target=t5_pu1_txn, weight=1, arc_type='test')
arc_count += 1

# G-CSF signal boost
doc.create_arc(source=p8_gcsf, target=t5_pu1_txn, weight=1, arc_type='test')
arc_count += 1

# GATA1 sensing (test arc - read-only)
# Allows rate formula to access GATA1_Protein for inhibition calculation
doc.create_arc(source=p3_gata1_protein, target=t5_pu1_txn, weight=1, arc_type='test')
arc_count += 1
print(f"  ✓ GATA1 -| PU.1 transcription (test arc + rate function)")

# mRNA output
doc.create_arc(source=t5_pu1_txn, target=p5_pu1_mrna, weight=1, arc_type='normal')
arc_count += 1

# --- PU.1 Translation Arcs ---
doc.create_arc(source=p5_pu1_mrna, target=t6_pu1_trl, weight=1, arc_type='normal')
doc.create_arc(source=t6_pu1_trl, target=p6_pu1_protein, weight=1, arc_type='normal')
arc_count += 2

# --- PU.1 Degradation Arcs ---
doc.create_arc(source=p5_pu1_mrna, target=t7_pu1_mrna_deg, weight=1, arc_type='normal')
doc.create_arc(source=p6_pu1_protein, target=t8_pu1_prot_deg, weight=1, arc_type='normal')
arc_count += 2

print(f"✓ Created {arc_count} arcs")

# ============================================================================
# SUMMARY & SAVE
# ============================================================================
print("\n" + "="*70)
print("MODEL SUMMARY")
print("="*70)
print(f"Places: {len(doc.places)}")
print(f"  - GATA1 module: 3 (Gene, mRNA, Protein)")
print(f"  - PU.1 module: 3 (Gene, mRNA, Protein)")
print(f"  - Signal places: 2 (EPO, G-CSF)")
print(f"Transitions: {len(doc.transitions)}")
print(f"  - Stochastic: 2 (transcription)")
print(f"  - Continuous: 6 (translation, degradation)")
print(f"Arcs: {len(doc.arcs)}")
print(f"  - Normal: {len([a for a in doc.arcs if a.arc_type == 'normal'])}")
print(f"  - Test: {len([a for a in doc.arcs if a.arc_type == 'test'])}")
print(f"  - Inhibitor: {len([a for a in doc.arcs if a.arc_type == 'inhibitor'])}")

print("\n" + "="*70)
print("KEY FEATURES")
print("="*70)
print("✓ Symmetric rate functions (critical for balanced bistability)")
print("✓ Mutual inhibition via rate formulas (Hill n=2, Lambda Phage pattern)")
print("✓ Positive feedback via test arcs (non-consuming)")
print("✓ Stochastic transcription (gene expression noise)")
print("✓ Cytokine modulation (EPO/G-CSF as signal places)")
print("✓ Zero initial conditions (symmetric start: GATA1=PU1=50)")

print("\n" + "="*70)
print("EXPECTED OUTCOME")
print("="*70)
print("Run 100 replicates (Gillespie SSA) for 3000 seconds:")
print("  • ~50% cells → High GATA1, Low PU.1 (Erythroid fate)")
print("  • ~50% cells → Low GATA1, High PU.1 (Myeloid fate)")
print("  • Bimodal distribution emerges from symmetric start")
print("  • No manual priorities - preemption from biochemical thresholds!")

# Save model
output_path = Path(__file__).parent.parent / "models" / "phase1_minimal_bistable.shy"
output_path.parent.mkdir(exist_ok=True)
doc.save_to_file(str(output_path))

print("\n" + "="*70)
print(f"✓ Model saved: {output_path}")
print("="*70)
print("\nNext steps:")
print("  1. Open in shypn GUI: shypn models/phase1_minimal_bistable.shy")
print("  2. Set simulation: Gillespie SSA, 3000 sec, 100 replicates")
print("  3. Record: GATA1_Protein, PU1_Protein")
print("  4. Analyze: Bimodal distribution? Commitment ratio?")
print("  5. If balanced → Proceed to Phase 2 (threshold sweep)")
