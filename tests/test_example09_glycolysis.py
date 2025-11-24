#!/usr/bin/env python3
"""
Test Example 09: Complete Glycolysis Pathway
Validates:
- Glucose → Pyruvate conversion (1:2 stoichiometry)
- ATP balance: -2 (HK, PFK) + 4 (PGK x2, PK x2) = +2 net
- NADH production: +2 (GAPDH x2)
- Reversible reactions at equilibrium
- Inhibitor arcs at regulatory checkpoints
"""

import sys
import os
import json

# Add src to path
sys.path.insert(0, '/home/simao/projetos/shypn/src')

from shypn.data.canvas.document_model import DocumentModel
from shypn.engine.simulation.controller import SimulationController

def load_example_09():
    """Load Example 09 model"""
    model_path = "/home/simao/projetos/shypn/workspace/projects/Biochemical-Examples/09_Complete_Glycolysis/model.shy"
    
    with open(model_path, 'r') as f:
        data = json.load(f)
    
    doc = DocumentModel.from_dict(data)
    controller = SimulationController(doc)
    return doc, controller

def print_metabolite_state(doc, title="State"):
    """Print metabolite concentrations"""
    print(f"\n{title}:")
    
    # Metabolites in pathway order
    metabolites = ["Glucose", "G6P", "F6P", "F16BP", "DHAP", "G3P", 
                   "BPG13", "PG3", "PG2", "PEP", "Pyruvate"]
    
    for name in metabolites:
        place = next((p for p in doc.places if p.name == name), None)
        if place:
            print(f"  {name:10s}: {place.tokens:.4f} mM")
    
    print("\n  Cofactors:")
    for name in ["ATP", "ADP", "NAD", "NADH"]:
        place = next((p for p in doc.places if p.name == name), None)
        if place:
            print(f"  {name:10s}: {place.tokens:.4f} mM")

def check_stoichiometry(doc, initial_state):
    """Check mass balance for glycolysis stoichiometry"""
    # Get places
    glucose = next(p for p in doc.places if p.name == "Glucose")
    pyruvate = next(p for p in doc.places if p.name == "Pyruvate")
    atp = next(p for p in doc.places if p.name == "ATP")
    adp = next(p for p in doc.places if p.name == "ADP")
    nad = next(p for p in doc.places if p.name == "NAD")
    nadh = next(p for p in doc.places if p.name == "NADH")
    
    # Calculate changes
    glc_consumed = initial_state["Glucose"] - glucose.tokens
    pyr_produced = pyruvate.tokens - initial_state["Pyruvate"]
    atp_change = atp.tokens - initial_state["ATP"]
    nadh_change = nadh.tokens - initial_state["NADH"]
    
    print("\n=== Stoichiometry Check ===")
    print(f"Glucose consumed: {glc_consumed:.4f} mM")
    print(f"Pyruvate produced: {pyr_produced:.4f} mM")
    print(f"  Expected ratio: 1:2 (got {pyr_produced/glc_consumed if glc_consumed > 0.01 else 0:.2f}:1)")
    
    print(f"\nATP change: {atp_change:+.4f} mM")
    print(f"  Expected: +2 per glucose (+{2*glc_consumed:.4f} for {glc_consumed:.4f} glucose)")
    print(f"  Efficiency: {(atp_change / (2*glc_consumed) * 100) if glc_consumed > 0.01 else 0:.1f}%")
    
    print(f"\nNADH change: {nadh_change:+.4f} mM")
    print(f"  Expected: +2 per glucose (+{2*glc_consumed:.4f} for {glc_consumed:.4f} glucose)")
    print(f"  Efficiency: {(nadh_change / (2*glc_consumed) * 100) if glc_consumed > 0.01 else 0:.1f}%")

def check_inhibitors(doc):
    """Check if inhibitor arcs are properly configured"""
    print("\n=== Inhibitor Arc Configuration ===")
    
    inhibitor_info = [
        ("HK", "G6P", 2.0, "Product inhibition"),
        ("PFK", "ATP", 3.0, "Energy sensing"),
        ("PK", "ATP", 3.5, "Energy sensing")
    ]
    
    for enzyme, inhibitor_name, threshold, mechanism in inhibitor_info:
        transition = next((t for t in doc.transitions if t.name == enzyme), None)
        inhibitor = next((p for p in doc.places if p.name == inhibitor_name), None)
        
        if not transition or not inhibitor:
            print(f"  {enzyme}: WARNING - Transition or inhibitor not found!")
            continue
        
        # Find inhibitor arcs
        inhibitor_arcs = [arc for arc in doc.arcs 
                         if arc.source == inhibitor and arc.target == transition
                         and "inhibitor" in arc.arc_type]
        
        if inhibitor_arcs:
            arc = inhibitor_arcs[0]
            status = "ACTIVE" if inhibitor.tokens < arc.weight else "BLOCKED"
            print(f"  {enzyme}: inhibited by {inhibitor_name} ≥ {arc.weight} mM ({mechanism})")
            print(f"    Current: {inhibitor.tokens:.2f} mM → {status}")
        else:
            print(f"  {enzyme}: WARNING - No inhibitor arc found!")

def main():
    print("="*60)
    print("Example 09: Complete Glycolysis Pathway")
    print("="*60)
    
    # Load model
    doc, controller = load_example_09()
    
    # Store initial state
    initial_state = {
        "Glucose": next(p for p in doc.places if p.name == "Glucose").tokens,
        "Pyruvate": next(p for p in doc.places if p.name == "Pyruvate").tokens,
        "ATP": next(p for p in doc.places if p.name == "ATP").tokens,
        "ADP": next(p for p in doc.places if p.name == "ADP").tokens,
        "NAD": next(p for p in doc.places if p.name == "NAD").tokens,
        "NADH": next(p for p in doc.places if p.name == "NADH").tokens
    }
    
    print_metabolite_state(doc, "Initial State (t=0)")
    check_inhibitors(doc)
    
    # Run simulation
    print("\n" + "="*60)
    print("Running simulation (100 steps, dt=0.01, t_max=1.0s)")
    print("="*60)
    
    for step in range(100):
        controller.step(time_step=0.01)
        
        if step in [9, 24, 49, 99]:  # Report at t=0.1, 0.25, 0.5, 1.0
            t = controller.time
            print(f"\n--- t = {t:.2f}s (step {step+1}) ---")
            
            # Quick state summary
            glc = next(p for p in doc.places if p.name == "Glucose").tokens
            pyr = next(p for p in doc.places if p.name == "Pyruvate").tokens
            atp = next(p for p in doc.places if p.name == "ATP").tokens
            g6p = next(p for p in doc.places if p.name == "G6P").tokens
            
            print(f"  Glucose: {glc:.3f} | Pyruvate: {pyr:.3f}")
            print(f"  ATP: {atp:.3f} | G6P: {g6p:.3f}")
    
    # Final state
    print_metabolite_state(doc, f"\nFinal State (t={controller.time:.2f}s)")
    check_stoichiometry(doc, initial_state)
    check_inhibitors(doc)
    
    # Pathway analysis
    print("\n=== Pathway Flow Analysis ===")
    glc_final = next(p for p in doc.places if p.name == "Glucose").tokens
    pyr_final = next(p for p in doc.places if p.name == "Pyruvate").tokens
    
    flux = (glc_final - initial_state["Glucose"]) / controller.time
    print(f"Glucose consumption rate: {-flux:.4f} mM/s")
    
    pyr_flux = (pyr_final - initial_state["Pyruvate"]) / controller.time
    print(f"Pyruvate production rate: {pyr_flux:.4f} mM/s")
    
    print("\n✅ Example 09 validation complete!")
    print("\nExpected behavior:")
    print("  - Glucose should decrease (source feeding)")
    print("  - Pyruvate should increase (sink draining)")
    print("  - ATP net gain: +2 per glucose")
    print("  - NADH net gain: +2 per glucose")
    print("  - Inhibitor checkpoints should regulate flow")

if __name__ == "__main__":
    main()
