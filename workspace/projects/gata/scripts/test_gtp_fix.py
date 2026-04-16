#!/usr/bin/env python3
"""
Quick Test of Phase 3A Model with Fixed GTP

Runs a 500s simulation to verify:
1. GTP charge stays > 70%
2. Energy balance maintained
3. Model behaves correctly

Date: 2026-02-17
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../src'))

from shypn.core.model import Model
from shypn.engine.simulation import SimulationController
from shypn.engine.simulation.executors import ContinuousExecutor

def quick_test():
    """Run quick 500s test simulation"""
    
    print("=" * 70)
    print("PHASE 3A QUICK TEST - GTP FIX VERIFICATION")
    print("=" * 70)
    print()
    
    # Load model
    model_path = "workspace/projects/gata/models/phase3a_spatial.shy"
    print(f"📂 Loading model: {model_path}")
    
    try:
        model = Model.load_from_json(model_path)
        print(f"✅ Model loaded: {len(model.places)} places, {len(model.transitions)} transitions")
    except Exception as e:
        print(f"❌ Failed to load model: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print()
    
    # Check adaptive transitions
    print("🔍 Adaptive transitions:")
    adaptive_count = 0
    for t in model.transitions:
        if t.transition_type == 'adaptive':
            adaptive_count += 1
            print(f"   - {t.name}")
    print(f"   Total: {adaptive_count}")
    print()
    
    # Setup controller
    print("⚙️  Setting up simulation controller...")
    controller = SimulationController(model)
    
    # Configure for 500s duration
    duration = 500.0  # seconds
    time_step = 0.01  # 10ms steps for accuracy
    
    print(f"   Duration: {duration}s")
    print(f"   Time step: {time_step}s")
    print()
    
    # Record initial state
    print("📊 INITIAL STATE:")
    try:
        atp_place = next(p for p in model.places if 'ATP' in p.name and 'ADP' not in p.name)
        gtp_place = next(p for p in model.places if 'GTP' in p.name and 'GDP' not in p.name)
        gdp_place = next(p for p in model.places if 'GDP' in p.name)
        
        atp_initial = atp_place.tokens
        gtp_initial = gtp_place.tokens
        gdp_initial = gdp_place.tokens
        
        print(f"   ATP: {atp_initial:.1f} mM")
        print(f"   GTP: {gtp_initial:.1f} mM")
        print(f"   GDP: {gdp_initial:.1f} mM")
        print(f"   GTP charge: {gtp_initial / (gtp_initial + gdp_initial):.1%}")
    except Exception as e:
        print(f"   ⚠️  Could not get initial state: {e}")
    
    print()
    print("🚀 Running simulation...")
    print("   (This should take ~30-60 seconds)")
    print()
    
    # Run simulation
    try:
        executor = ContinuousExecutor(controller)
        
        # Set duration
        controller._duration = duration
        controller._time_step = time_step
        
        # Run synchronously (blocking)
        success = controller.run(duration=duration, time_step=time_step, executor=executor)
        
        if not success:
            print("⚠️  Simulation returned False (may have stopped early)")
        else:
            print("✅ Simulation completed successfully!")
        
    except Exception as e:
        print(f"❌ Simulation failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print()
    
    # Check final state
    print("=" * 70)
    print("FINAL STATE")
    print("=" * 70)
    print()
    
    try:
        atp_final = atp_place.tokens
        gtp_final = gtp_place.tokens
        gdp_final = gdp_place.tokens
        
        gtp_total = gtp_final + gdp_final
        gtp_charge = gtp_final / gtp_total if gtp_total > 0 else 0
        
        print(f"⚡ ENERGY:")
        print(f"   ATP: {atp_final:.1f} mM")
        print(f"   GTP: {gtp_final:.1f} mM")
        print(f"   GDP: {gdp_final:.1f} mM")
        print(f"   GTP charge: {gtp_charge:.1%}")
        print()
        
        # Check lineage commitment
        gata1_nuc = next(p for p in model.places if 'GATA1_Protein_nuc' in p.name).tokens
        pu1_nuc = next(p for p in model.places if 'PU1_Protein_nuc' in p.name).tokens
        
        print(f"🧬 LINEAGE:")
        print(f"   GATA1_nuc: {gata1_nuc:.1f} mM")
        print(f"   PU1_nuc: {pu1_nuc:.1f} mM")
        print(f"   Ratio: {gata1_nuc / pu1_nuc if pu1_nuc > 0 else float('inf'):.2f}")
        print()
        
        # Verdict
        print("=" * 70)
        print("VERDICT")
        print("=" * 70)
        print()
        
        if gtp_charge > 0.7:
            print("✅ GTP BALANCE FIXED! (charge > 70%)")
        elif gtp_charge > 0.5:
            print("⚠️  GTP improved but still suboptimal (charge 50-70%)")
        else:
            print("❌ GTP still depleted (charge < 50%)")
        
        print()
        print(f"GTP regeneration 5× increase:")
        print(f"  Initial: {gtp_initial / (gtp_initial + gdp_initial):.1%} charge")
        print(f"  Final:   {gtp_charge:.1%} charge")
        print(f"  Change:  {(gtp_charge - gtp_initial/(gtp_initial + gdp_initial))*100:+.1f}%")
        print()
        
    except Exception as e:
        print(f"❌ Could not analyze final state: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    quick_test()
