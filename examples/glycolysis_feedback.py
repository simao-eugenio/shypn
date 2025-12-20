#!/usr/bin/env python3
"""
Example: Glycolysis with Energy Feedback

Demonstrates modular Bio-PN with signal places for metabolic regulation.

This example shows:
- Module creation for glycolysis pathway
- Signal place for ATP/ADP ratio (energy sensing)
- Feedback regulation via signal broadcasting
- Module validation and analysis

Biological Context:
  Glycolysis is regulated by cellular energy status. When ATP is high,
  phosphofructokinase (PFK) is inhibited to slow glucose consumption.
  This is modeled as a signal place that broadcasts energy state without
  being consumed.
"""

from shypn.netobjs.place import Place
from shypn.netobjs.transition import Transition
from shypn.netobjs.arc import Arc
from shypn.netobjs.module import Module
from shypn.netobjs.signal_type import SignalType
from shypn.data.canvas.document_model import DocumentModel


def create_glycolysis_model() -> DocumentModel:
    """Create glycolysis model with energy feedback signal.
    
    Returns:
        DocumentModel with glycolysis module and ATP/ADP signal
    """
    # Create document
    doc = DocumentModel(model_id="glycolysis_feedback")
    
    # =========================================================================
    # Module: Glycolysis Pathway
    # =========================================================================
    glycolysis = doc.create_module(
        name="Glycolysis",
        compartment_id="cytoplasm"
    )
    
    # =========================================================================
    # Regular Places (Mass Transfer)
    # =========================================================================
    
    # Glucose (substrate)
    glucose = Place(x=100, y=100, id="P1", name="Glucose", radius=30)
    glucose.tokens = 100.0  # Initial concentration
    glucose.module_id = glycolysis.module_id
    doc.add_place(glucose)
    glycolysis.places.add(glucose)
    
    # Glucose-6-Phosphate (intermediate)
    g6p = Place(x=300, y=100, id="P2", name="G6P", radius=30)
    g6p.tokens = 10.0
    g6p.module_id = glycolysis.module_id
    doc.add_place(g6p)
    glycolysis.places.add(g6p)
    
    # Fructose-6-Phosphate (intermediate)
    f6p = Place(x=500, y=100, id="P3", name="F6P", radius=30)
    f6p.tokens = 5.0
    f6p.module_id = glycolysis.module_id
    doc.add_place(f6p)
    glycolysis.places.add(f6p)
    
    # Fructose-1,6-bisphosphate (product of committed step)
    fbp = Place(x=700, y=100, id="P4", name="FBP", radius=30)
    fbp.tokens = 2.0
    fbp.module_id = glycolysis.module_id
    doc.add_place(fbp)
    glycolysis.places.add(fbp)
    
    # Pyruvate (final product)
    pyruvate = Place(x=900, y=100, id="P5", name="Pyruvate", radius=30)
    pyruvate.tokens = 0.0
    pyruvate.module_id = glycolysis.module_id
    doc.add_place(pyruvate)
    glycolysis.places.add(pyruvate)
    
    # =========================================================================
    # Signal Place (Information Without Mass Transfer)
    # =========================================================================
    
    # ATP/ADP Ratio - ENERGY SIGNAL
    # This place broadcasts energy state without being consumed
    atp_ratio = Place(x=500, y=300, id="P_ATP", name="ATP_ADP_Ratio", radius=35)
    atp_ratio.tokens = 0.8  # High energy state (0.0 = depleted, 1.0 = saturated)
    atp_ratio.is_signal_place = True
    atp_ratio.signal_type = SignalType.ENERGY
    atp_ratio.signal_scope = [glycolysis.module_id]  # Available to glycolysis module
    atp_ratio.module_id = glycolysis.module_id
    doc.add_place(atp_ratio)
    glycolysis.places.add(atp_ratio)
    glycolysis.boundary_signals.add(atp_ratio)
    
    # =========================================================================
    # Transitions (Reactions)
    # =========================================================================
    
    # Hexokinase: Glucose → G6P
    # Not regulated by ATP (first step)
    hexokinase = Transition(x=200, y=100, id="T1", name="Hexokinase")
    hexokinase.transition_type = "continuous"
    hexokinase.rate = "1.0 * Glucose"  # Simple mass action
    hexokinase.module_id = glycolysis.module_id
    doc.add_transition(hexokinase)
    glycolysis.transitions.add(hexokinase)
    
    # Phosphoglucose Isomerase: G6P ⇌ F6P
    pgi = Transition(x=400, y=100, id="T2", name="PGI")
    pgi.transition_type = "continuous"
    pgi.rate = "0.5 * G6P"  # Reversible, simplified
    pgi.module_id = glycolysis.module_id
    doc.add_transition(pgi)
    glycolysis.transitions.add(pgi)
    
    # Phosphofructokinase: F6P → FBP
    # REGULATED BY ATP/ADP RATIO (committed step)
    pfk = Transition(x=600, y=100, id="T3", name="PFK")
    pfk.transition_type = "continuous"
    pfk.rate = "2.0 * F6P * (1 - ATP_ADP_Ratio)"  # Inhibited by high ATP
    pfk.module_id = glycolysis.module_id
    doc.add_transition(pfk)
    glycolysis.transitions.add(pfk)
    
    # Aldolase + GAPDH + ... (simplified as one step): FBP → Pyruvate
    lower_glycolysis = Transition(x=800, y=100, id="T4", name="Lower_Glycolysis")
    lower_glycolysis.transition_type = "continuous"
    lower_glycolysis.rate = "1.5 * FBP"
    lower_glycolysis.module_id = glycolysis.module_id
    doc.add_transition(lower_glycolysis)
    glycolysis.transitions.add(lower_glycolysis)
    
    # =========================================================================
    # Arcs (Regular - Mass Transfer)
    # =========================================================================
    
    # Hexokinase arcs
    arc1 = Arc(id="A1", source=glucose, target=hexokinase, weight=1.0)
    doc.add_arc(arc1)
    
    arc2 = Arc(id="A2", source=hexokinase, target=g6p, weight=1.0)
    doc.add_arc(arc2)
    
    # PGI arcs
    arc3 = Arc(id="A3", source=g6p, target=pgi, weight=1.0)
    doc.add_arc(arc3)
    
    arc4 = Arc(id="A4", source=pgi, target=f6p, weight=1.0)
    doc.add_arc(arc4)
    
    # PFK arcs
    arc5 = Arc(id="A5", source=f6p, target=pfk, weight=1.0)
    doc.add_arc(arc5)
    
    arc6 = Arc(id="A6", source=pfk, target=fbp, weight=1.0)
    doc.add_arc(arc6)
    
    # Lower glycolysis arcs
    arc7 = Arc(id="A7", source=fbp, target=lower_glycolysis, weight=1.0)
    doc.add_arc(arc7)
    
    arc8 = Arc(id="A8", source=lower_glycolysis, target=pyruvate, weight=2.0)  # 2 pyruvate per FBP
    doc.add_arc(arc8)
    
    # =========================================================================
    # Signal Arc (Information Flow - Dashed Line in Visualization)
    # =========================================================================
    
    # ATP/ADP ratio modulates PFK activity
    # This is NOT consumed - PFK reads the signal value
    signal_arc = Arc(id="A_signal", source=atp_ratio, target=pfk, weight=1.0)
    signal_arc.properties = {"kind": "modifier"}  # Modifier arc (read-only)
    doc.add_arc(signal_arc)
    
    return doc


def run_example():
    """Run the glycolysis feedback example."""
    print("=" * 80)
    print("GLYCOLYSIS WITH ENERGY FEEDBACK EXAMPLE")
    print("=" * 80)
    print()
    
    # Create model
    model = create_glycolysis_model()
    
    print(f"Model: {model.model_id}")
    print(f"Modules: {len(model.modules)}")
    print(f"Places: {len(model.places)}")
    print(f"Transitions: {len(model.transitions)}")
    print(f"Arcs: {len(model.arcs)}")
    print()
    
    # Show module contents
    for module_id, module in model.modules.items():
        print(f"Module: {module.name} ({module_id})")
        print(f"  Places: {len(module.places)}")
        print(f"  Transitions: {len(module.transitions)}")
        print(f"  Boundary Signals: {len(module.boundary_signals)}")
        for signal in module.boundary_signals:
            signal_place = model.places[signal]
            print(f"    - {signal_place.name} ({signal_place.signal_type.value}): {signal_place.tokens:.2f}")
        print()
    
    print("Key Features Demonstrated:")
    print("  ✓ Signal place (ATP_ADP_Ratio) broadcasts energy state")
    print("  ✓ PFK transition reads signal without consuming it")
    print("  ✓ High ATP → Inhibits PFK → Slows glycolysis")
    print("  ✓ Module encapsulates glycolysis pathway")
    print()
    
    print("Expected Behavior During Simulation:")
    print("  1. Glucose flows through pathway to pyruvate")
    print("  2. ATP_ADP_Ratio stays constant (signal is read-only)")
    print("  3. PFK rate modulated by ATP_ADP_Ratio")
    print("  4. If ATP high (0.8) → PFK slow (20% of max)")
    print("  5. If ATP low (0.2) → PFK fast (80% of max)")
    print()
    
    # Save model
    output_file = "workspace/examples/glycolysis_feedback.json"
    model.save_to_file(output_file)
    print(f"Model saved to: {output_file}")
    print()
    
    print("To simulate this model:")
    print("  1. Open in SHYpn GUI")
    print("  2. Configure continuous simulation")
    print("  3. Observe: Glucose decreases, Pyruvate increases")
    print("  4. Notice: ATP_ADP_Ratio remains constant (signal)")
    print()
    
    print("To analyze module architecture:")
    print(f"  python -m cli.analysis.module_analysis {output_file}")
    print()


if __name__ == "__main__":
    run_example()
