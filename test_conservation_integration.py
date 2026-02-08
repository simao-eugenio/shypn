#!/usr/bin/env python3
"""Test conservation enforcement integrated into SimulationController.

This test runs one of the minimal energy test models with conservation
enforcement enabled, verifying that the 33% loss is corrected to 0%.
"""

import json
import logging
import sys
from pathlib import Path

# Fix GTK version conflict
import gi
gi.require_version('Gtk', '3.0')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:%(name)s:%(message)s'
)
logger = logging.getLogger(__name__)

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from shypn.netobjs.place import Place
from shypn.netobjs.transition import Transition
from shypn.netobjs.arc import Arc
from shypn.data.model_canvas_manager import ModelCanvasManager
from shypn.engine.simulation.controller import SimulationController


def test_conservation_enforcement():
    """Run test model WITH conservation enforcement enabled."""
    
    print("=" * 80)
    print("  CONSERVATION ENFORCEMENT INTEGRATION TEST")
    print("=" * 80)
    
    # Load test model JSON
    model_path = Path(__file__).parent / 'workspace' / 'projects' / 'My_Project' / 'energy_test' / 'atp_cycle_all_normal_adaptive.shy'
    
    if not model_path.exists():
        logger.error(f"Test model not found: {model_path}")
        return False
    
    logger.info(f"Loading test model: {model_path.name}")
    
    with open(model_path) as f:
        model_data = json.load(f)
    
    # Create model canvas manager manually
    canvas_manager = ModelCanvasManager()
    
    #  Load places
    places = []
    for p_data in model_data.get('places', []):
        place = Place.from_dict(p_data)
        places.append(place)
    places_dict = {p.id: p for p in places}
    
    # Load transitions
    transitions = []
    for t_data in model_data.get('transitions', []):
        trans = Transition.from_dict(t_data)
        transitions.append(trans)
    transitions_dict = {t.id: t for t in transitions}
    
    # Load arcs
    arcs = []
    for a_data in model_data['arcs']:
        arc = Arc.from_dict(a_data, places_dict, transitions_dict)
        arcs.append(arc)
    
    # Load objects into canvas manager
    canvas_manager.load_objects(places=places, transitions=transitions, arcs=arcs)
    
    logger.info(f"Model loaded: {len(places)} places, {len(transitions)} transitions, {len(arcs)} arcs")
    
    # Create controller
    controller = SimulationController(canvas_manager, verbose=False)
    
    # Configure simulation (10 seconds, adaptive hybrid mode)
    controller.settings.duration = 10.0
    controller.settings.duration_unit = 's'
    controller.settings.dt = 0.01
    
    # === KEY: Configure conservation enforcement ===
    logger.info("Configuring conservation enforcement for ATP + ADP + Pi")
    controller.configure_conservation(
        name='energy_cycle',
        place_ids=['P1', 'P2', 'P3'],  # Use actual place IDs, not names
        expected_total=15.0  # Initial: 5+5+5 = 15 mM
    )
    
    # Record initial state
    initial_atp = places[0].tokens
    initial_adp = places[1].tokens
    initial_pi = places[2].tokens
    initial_total = initial_atp + initial_adp + initial_pi
    
    logger.info(f"Initial state:")
    logger.info(f"  ATP = {initial_atp:.3f} mM")
    logger.info(f"  ADP = {initial_adp:.3f} mM")
    logger.info(f"  Pi  = {initial_pi:.3f} mM")
    logger.info(f"  Total = {initial_total:.3f} mM")
    
    # Run simulation
    logger.info(f"Running simulation for {controller.settings.duration}s...")
    step_count = 0
    while controller.time < controller.settings.duration:
        success = controller.step()
        step_count += 1
        if not success:
            break
    
    logger.info(f"Simulation complete: {step_count} steps")
    
    # Check final state
    final_atp = places[0].tokens
    final_adp = places[1].tokens
    final_pi = places[2].tokens
    final_total = final_atp + final_adp + final_pi
    
    logger.info(f"\nFinal state:")
    logger.info(f"  ATP = {final_atp:.6f} mM")
    logger.info(f"  ADP = {final_adp:.6f} mM")
    logger.info(f"  Pi  = {final_pi:.6f} mM")
    logger.info(f"  Total = {final_total:.6f} mM")
    
    # Calculate loss
    loss = initial_total - final_total
    loss_percent = (loss / initial_total * 100) if initial_total > 0 else 0
    
    logger.info(f"\n📊 CONSERVATION RESULTS:")
    logger.info(f"  Expected total: {initial_total:.6f} mM")
    logger.info(f"  Actual total:   {final_total:.6f} mM")
    logger.info(f"  Error:          {abs(loss):.6f} mM ({abs(loss_percent):.4f}%)")
    
    # Check firing counts
    t1_count = transitions[0].firing_count
    t2_count = transitions[1].firing_count
    logger.info(f"\n🔥 FIRING COUNTS:")
    logger.info(f"  ATP_synthesis: {t1_count:.0f} firings")
    logger.info(f"  ATPase:        {t2_count:.0f} firings")
    logger.info(f"  Imbalance:     {abs(t1_count - t2_count):.0f} firings")
    
    # Get enforcement statistics
    stats = controller.conservation_enforcer.get_statistics()
    logger.info(f"\n⚙️  ENFORCEMENT STATISTICS:")
    logger.info(f"  Total corrections: {stats['total_corrections']}")
    logger.info(f"  Max violation:     {stats['max_violation_observed']:.6f} mM")
    
    # Verify conservation (should be near-zero loss)
    tolerance = 0.01  # 0.01% tolerance
    if abs(loss_percent) < tolerance:
        logger.info(f"\n✅ SUCCESS: Conservation maintained within tolerance!")
        logger.info(f"   (error {abs(loss_percent):.6f}% < {tolerance:.6f}%)")
        return True
    else:
        logger.error(f"\n❌ FAILURE: Conservation violated!")
        logger.error(f"   (error {abs(loss_percent):.6f}% > {tolerance:.6f}%)")
        return False


if __name__ == '__main__':
    success = test_conservation_enforcement()
    sys.exit(0 if success else 1)
