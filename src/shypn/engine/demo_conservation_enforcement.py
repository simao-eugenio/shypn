#!/usr/bin/env python3
"""Demonstration: Mass Conservation Enforcement on Energy Test Model.

This script shows how conservation enforcement prevents the 33% energy loss
observed in the adaptive mode test (atp_cycle_all_normal_adaptive).

WITHOUT enforcement:
    Initial: 15.0 mM
    Final: 10.0 mM
    Loss: 5.0 mM (33.33%)

WITH enforcement:
    Initial: 15.0 mM
    Final: 15.0 mM
    Loss: 0.0 mM (0%)
"""

import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shypn.engine.conservation_enforcer import ConservationEnforcer


def demonstrate_conservation_enforcement():
    """Show conservation enforcement on the test model."""
    
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Simulate the test model structure
    class MockPlace:
        def __init__(self, id, name, tokens):
            self.id = id
            self.name = name
            self.tokens = tokens
        
        def set_tokens(self, value):
            self.tokens = max(0.0, float(value))
    
    class MockModel:
        def __init__(self):
            self.places = [
                MockPlace('P1', 'ATP_pool', 5.0),
                MockPlace('P2', 'ADP_pool', 5.0),
                MockPlace('P3', 'Pi_pool', 5.0)
            ]
    
    # Create model and enforcer
    model = MockModel()
    enforcer = ConservationEnforcer(model)
    
    # Register conservation group
    enforcer.add_conservation_group(
        name='energy_cycle',
        place_ids=['P1', 'P2', 'P3'],
        expected_total=15.0,
        tolerance=1e-6,
        auto_correct=True
    )
    
    logger.info("=" * 80)
    logger.info("DEMONSTRATION: Conservation Enforcement")
    logger.info("=" * 80)
    
    # Initial state
    total_initial = sum(p.tokens for p in model.places)
    logger.info(f"\n📊 INITIAL STATE:")
    for p in model.places:
        logger.info(f"   {p.name}: {p.tokens:.6f} mM")
    logger.info(f"   TOTAL: {total_initial:.6f} mM")
    
    # Simulate firing imbalance (195 synth vs 190 ATPase)
    # This mimics what happened in the adaptive mode test
    logger.info(f"\n🔄 SIMULATING 200s ADAPTIVE MODE:")
    logger.info(f"   ATP_synthesis: 195 firings (ADP+Pi → ATP)")
    logger.info(f"   ATPase: 190 firings (ATP → ADP+Pi)")
    
    # Apply the token changes without enforcement
    # T1 (195 firings): consume 195 ADP + 195 Pi, produce 195 ATP
    model.places[1].tokens -= 195  # ADP consumed
    model.places[2].tokens -= 195  # Pi consumed
    model.places[0].tokens += 195  # ATP produced
    
    # T2 (190 firings): consume 190 ATP, produce 190 ADP + 190 Pi
    model.places[0].tokens -= 190  # ATP consumed
    model.places[1].tokens += 190  # ADP produced
    model.places[2].tokens += 190  # Pi produced
    
    logger.info(f"\n📊 AFTER SIMULATION (before enforcement):")
    total_before = sum(p.tokens for p in model.places)
    for p in model.places:
        logger.info(f"   {p.name}: {p.tokens:.6f} mM")
    logger.info(f"   TOTAL: {total_before:.6f} mM")
    logger.info(f"   LOSS: {total_initial - total_before:.6f} mM ({((total_initial - total_before) / total_initial * 100):.2f}%)")
    
    # Apply enforcement
    logger.info(f"\n🔧 APPLYING CONSERVATION ENFORCEMENT:")
    violations = enforcer.verify_and_correct()
    
    if violations:
        for v in violations:
            logger.info(
                f"   ⚠️  Violation detected in '{v['group']}': "
                f"error={v['error']:.6f} mM ({v['percent']:.3f}%)"
            )
            if v['corrected']:
                logger.info(f"   ✅ Correction applied")
    
    # Final state
    logger.info(f"\n📊 AFTER ENFORCEMENT:")
    total_after = sum(p.tokens for p in model.places)
    for p in model.places:
        logger.info(f"   {p.name}: {p.tokens:.6f} mM")
    logger.info(f"   TOTAL: {total_after:.6f} mM")
    logger.info(f"   LOSS: {total_initial - total_after:.6f} mM ({((total_initial - total_after) / total_initial * 100):.9f}%)")
    
    # Statistics
    stats = enforcer.get_statistics()
    logger.info(f"\n📈 ENFORCEMENT STATISTICS:")
    logger.info(f"   Total corrections: {stats['total_corrections']}")
    logger.info(f"   Max violation: {stats['max_violation_observed']:.9f} mM")
    
    logger.info("=" * 80)
    
    # Verify conservation
    if abs(total_after - 15.0) < 1e-9:
        logger.info("✅ CONSERVATION VERIFIED: Total energy = 15.0 mM")
    else:
        logger.error("❌ CONSERVATION FAILED!")


if __name__ == "__main__":
    demonstrate_conservation_enforcement()
