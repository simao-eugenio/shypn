#!/usr/bin/env python3
"""Example: Integrating Conservation Enforcement into Simulation.

This shows how to modify simulation_controller.py to use ConservationEnforcer.
"""

# ============================================================================
# STEP 1: Add initialization in SimulationController.__init__()
# ============================================================================

from shypn.engine.conservation_enforcer import ConservationEnforcer

class SimulationController:
    def __init__(self, model, ...):
        # ... existing initialization ...
        
        # Initialize conservation enforcer
        self.conservation_enforcer = ConservationEnforcer(model)
        
        # Auto-detect conservation groups from model metadata
        self._setup_conservation_groups()
    
    def _setup_conservation_groups(self):
        """Automatically configure conservation groups from model.
        
        Looks for metadata tags like:
        - conservation_group: "energy_cycle"
        - conserved_species: ["ATP", "ADP", "Pi"]
        """
        # Check if model has conservation metadata
        if hasattr(self.model, 'metadata') and 'conservation_groups' in self.model.metadata:
            for group_config in self.model.metadata['conservation_groups']:
                self.conservation_enforcer.add_conservation_group(
                    name=group_config['name'],
                    place_ids=group_config['place_ids'],
                    expected_total=group_config.get('expected_total'),
                    tolerance=group_config.get('tolerance', 1e-6)
                )
        
        # Fallback: Manual configuration for known patterns
        # Example: Detect ATP/ADP/Pi cycles
        energy_places = []
        for place in self.model.places:
            name_lower = place.name.lower()
            if any(compound in name_lower for compound in ['atp', 'adp', 'amp', 'pi']):
                energy_places.append(place.id)
        
        if len(energy_places) >= 2:
            self.conservation_enforcer.add_conservation_group(
                name='energy_cycle',
                place_ids=energy_places,
                expected_total=None,  # Use current sum as reference
                tolerance=1e-6
            )
            self.logger.info(f"Auto-detected energy conservation group: {energy_places}")


# ============================================================================
# STEP 2: Add verification after each simulation step
# ============================================================================

    def step(self, time_step: float = None) -> bool:
        """Execute one simulation step."""
        # ... existing step logic ...
        
        # Fire transitions (existing code)
        for transition in enabled_transitions:
            success, details = self._fire_transition(transition)
            # ... handle firing ...
        
        # CRITICAL: Enforce conservation after all firings
        violations = self.conservation_enforcer.verify_and_correct()
        
        if violations:
            # Log violations for debugging
            for v in violations:
                if v['percent'] > 0.01:  # Log if > 0.01% error
                    self.logger.warning(
                        f"Conservation violation in '{v['group']}': "
                        f"error={v['error']:.6f} ({v['percent']:.3f}%) corrected={v['corrected']}"
                    )
        
        self.current_time += time_step
        return True


# ============================================================================
# STEP 3: Add to adaptive mode switching (CRITICAL for mode switch artifacts)
# ============================================================================

    def _handle_mode_change(self, transition, old_mode, new_mode):
        """Handle transition between continuous and stochastic modes."""
        # ... existing mode change logic ...
        
        # Clear any partial state from old mode
        behavior = self._get_behavior(transition)
        behavior.clear_enablement()
        
        # CRITICAL: Force conservation check after mode switch
        # This prevents token loss during continuous→stochastic or vice versa
        violations = self.conservation_enforcer.verify_and_correct()
        
        if violations:
            self.logger.warning(
                f"Mode switch {old_mode}→{new_mode} caused conservation violations: "
                f"{len(violations)} groups affected"
            )


# ============================================================================
# STEP 4: Add final verification at simulation end
# ============================================================================

    def finalize_simulation(self):
        """Clean up and report final statistics."""
        # ... existing finalization ...
        
        # Final conservation check
        violations = self.conservation_enforcer.verify_and_correct()
        
        if violations:
            self.logger.error(f"Final state has {len(violations)} conservation violations!")
            for v in violations:
                self.logger.error(
                    f"  {v['group']}: expected={v['expected']:.6f}, "
                    f"actual={v['actual']:.6f}, error={v['error']:.6f}"
                )
        
        # Report enforcement statistics
        stats = self.conservation_enforcer.get_statistics()
        self.logger.info(
            f"Conservation enforcement stats: "
            f"corrections={stats['total_corrections']}, "
            f"max_violation={stats['max_violation_observed']:.6f}"
        )


# ============================================================================
# STEP 5: Add configuration option to enable/disable enforcement
# ============================================================================

    def configure_conservation(
        self, 
        enabled: bool = True,
        tolerance: float = 1e-6,
        auto_correct: bool = True
    ):
        """Configure mass conservation enforcement.
        
        Args:
            enabled: Enable/disable enforcement
            tolerance: Allowable numerical error
            auto_correct: Automatically fix violations
        """
        if not enabled:
            self.conservation_enforcer = None
            self.logger.info("Conservation enforcement DISABLED")
            return
        
        # Update tolerance for all groups
        for group in self.conservation_enforcer.conservation_groups.values():
            group.tolerance = tolerance
            group.auto_correct = auto_correct
        
        self.logger.info(
            f"Conservation enforcement configured: "
            f"tolerance={tolerance}, auto_correct={auto_correct}"
        )


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

if __name__ == "__main__":
    # Create simulation
    controller = SimulationController(model)
    
    # Manually add conservation group
    controller.conservation_enforcer.add_conservation_group(
        name='ATP_cycle',
        place_ids=['ATP_pool', 'ADP_pool', 'Pi_pool'],
        expected_total=15.0,  # mM
        tolerance=1e-6
    )
    
    # Run simulation
    controller.run(duration=300.0)
    
    # Check results
    stats = controller.conservation_enforcer.get_statistics()
    print(f"Total corrections applied: {stats['total_corrections']}")
    print(f"Max violation observed: {stats['max_violation_observed']:.9f}")
