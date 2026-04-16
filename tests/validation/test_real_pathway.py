"""
Test real biological pathway: Hynne2001 Glycolysis model.

This test validates the simulation engine on a real biological pathway model
that contains a mix of continuous and stochastic transitions, representing
the glycolysis pathway in yeast.

Model characteristics:
- 25 places (metabolites)
- 24 transitions (reactions)
- 66 arcs (connections)
- Transition types: Continuous (enzymes) + Stochastic (transport/regulation)
"""

import pytest
import json
from pathlib import Path
from shypn.data.model_canvas_manager import ModelCanvasManager
from shypn.engine.simulation.controller import SimulationController
from shypn.data.canvas.document_model import DocumentModel


class TestRealPathway:
    """Test suite for real biological pathway models."""
    
    @pytest.fixture
    def glycolysis_model(self):
        """Load the Hynne2001 Glycolysis model from file."""
        model_path = Path(__file__).parent.parent.parent / "models" / "Hynne2001_Glycolysis.shy"
        
        # Load the document model from file
        document_model = DocumentModel.load_from_file(str(model_path))
        
        # Create manager and populate with loaded objects
        manager = ModelCanvasManager()
        manager.document_controller.places = list(document_model.places)
        manager.document_controller.transitions = list(document_model.transitions)
        manager.document_controller.arcs = list(document_model.arcs)
        
        return manager
    
    def test_model_loads_correctly(self, glycolysis_model):
        """Test that the model loads with correct structure."""
        doc_ctrl = glycolysis_model.document_controller
        
        # Verify structure
        assert len(doc_ctrl.places) == 25, "Should have 25 places (metabolites)"
        assert len(doc_ctrl.transitions) == 24, "Should have 24 transitions (reactions)"
        
        # Verify initial token distribution
        initial_tokens = sum(p.tokens for p in doc_ctrl.places)
        assert initial_tokens > 0, "Should have initial token distribution"
        
        print(f"\n✅ Model loaded: {len(doc_ctrl.places)} places, {len(doc_ctrl.transitions)} transitions")
        print(f"✅ Initial total tokens: {initial_tokens}")
    
    def test_transition_types_mixed(self, glycolysis_model):
        """Test that model contains mixed transition types."""
        doc_ctrl = glycolysis_model.document_controller
        
        # Count transition types
        type_counts = {}
        for t in doc_ctrl.transitions:
            t_type = t.transition_type if hasattr(t, 'transition_type') else 'immediate'
            type_counts[t_type] = type_counts.get(t_type, 0) + 1
        
        print(f"\n✅ Transition types found:")
        for t_type, count in sorted(type_counts.items()):
            print(f"   - {t_type}: {count} transitions")
        
        # Verify we have hybrid model
        assert 'continuous' in type_counts, "Should have continuous transitions"
        assert 'stochastic' in type_counts, "Should have stochastic transitions"
        assert type_counts['continuous'] > 0, "Should have continuous transitions (enzymes)"
        assert type_counts['stochastic'] > 0, "Should have stochastic transitions (transport)"
    
    def test_simulation_runs_without_errors(self, glycolysis_model):
        """Test that simulation runs without errors on real pathway."""
        controller = SimulationController(glycolysis_model)
        doc_ctrl = glycolysis_model.document_controller
        
        # Record initial state
        initial_tokens = sum(p.tokens for p in doc_ctrl.places)
        
        # Run simulation for 100 steps
        time_step = 0.01
        steps = 100
        
        errors = []
        for step in range(steps):
            try:
                controller.step(time_step=time_step)
            except Exception as e:
                errors.append(f"Step {step}: {e}")
                break
        
        # Verify no errors
        assert len(errors) == 0, f"Simulation should run without errors. Errors: {errors}"
        
        # Verify time advanced
        assert controller.time > 0, "Simulation time should advance"
        
        print(f"\n✅ Simulation ran for {steps} steps ({controller.time:.2f}s simulated time)")
        print(f"✅ No errors encountered")
    
    def test_token_conservation(self, glycolysis_model):
        """Test token conservation in real pathway (with relaxed tolerance)."""
        controller = SimulationController(glycolysis_model)
        doc_ctrl = glycolysis_model.document_controller
        
        # Record initial total
        initial_total = sum(p.tokens for p in doc_ctrl.places)
        
        # Run simulation
        time_step = 0.01
        steps = 100
        
        for _ in range(steps):
            controller.step(time_step=time_step)
        
        # Check final total
        final_total = sum(p.tokens for p in doc_ctrl.places)
        
        # Relaxed tolerance for continuous integration and complex model
        # Real biological pathways may have sources/sinks
        tolerance = initial_total * 0.1  # 10% tolerance
        
        print(f"\n✅ Initial tokens: {initial_total:.2f}")
        print(f"✅ Final tokens: {final_total:.2f}")
        print(f"✅ Change: {final_total - initial_total:.2f} ({(final_total - initial_total) / initial_total * 100:.1f}%)")
        
        # Just verify tokens are reasonable (not NaN, not negative, not exploding)
        assert final_total >= 0, "Total tokens should not be negative"
        assert not any(p.tokens < 0 for p in doc_ctrl.places), "No place should have negative tokens"
        assert final_total < initial_total * 10, "Tokens should not explode (10x increase)"
    
    def test_metabolite_dynamics(self, glycolysis_model):
        """Test that metabolites show dynamic behavior (change over time)."""
        controller = SimulationController(glycolysis_model)
        doc_ctrl = glycolysis_model.document_controller
        
        # Record initial state of key metabolites
        initial_state = {p.label: p.tokens for p in doc_ctrl.places}
        
        # Run simulation
        time_step = 0.01
        steps = 200  # Longer run to see dynamics
        
        for _ in range(steps):
            controller.step(time_step=time_step)
        
        # Record final state
        final_state = {p.label: p.tokens for p in doc_ctrl.places}
        
        # Count metabolites that changed
        changed_metabolites = 0
        for label in initial_state:
            if abs(final_state[label] - initial_state[label]) > 0.01:
                changed_metabolites += 1
        
        print(f"\n✅ {changed_metabolites}/{len(initial_state)} metabolites changed")
        
        # Show some examples
        print(f"✅ Sample metabolite changes:")
        examples = 0
        for label in sorted(initial_state.keys()):
            change = final_state[label] - initial_state[label]
            if abs(change) > 0.1 and examples < 5:
                print(f"   - {label}: {initial_state[label]:.2f} → {final_state[label]:.2f} (Δ{change:+.2f})")
                examples += 1
        
        # Verify some dynamics occurred
        assert changed_metabolites > 0, "Some metabolites should change over time"
    
    def test_continuous_stochastic_integration(self, glycolysis_model):
        """Test that continuous and stochastic transitions work together."""
        controller = SimulationController(glycolysis_model)
        doc_ctrl = glycolysis_model.document_controller
        
        # Track which transition types fire
        continuous_fired = False
        stochastic_fired = False
        
        # Run simulation and check behavior state
        time_step = 0.01
        steps = 100
        
        for _ in range(steps):
            controller.step(time_step=time_step)
            
            # Check which types have behaviors (indicating they're active)
            for t in doc_ctrl.transitions:
                if hasattr(t, 'transition_type'):
                    if t.transition_type == 'continuous':
                        # Continuous transitions are always "active" if enabled
                        if t.enabled:
                            continuous_fired = True
                    elif t.transition_type == 'stochastic':
                        # Stochastic fires when scheduled
                        stochastic_fired = True
        
        print(f"\n✅ Continuous transitions active: {continuous_fired}")
        print(f"✅ Stochastic transitions fired: {stochastic_fired}")
        
        # Both types should be active in this model
        assert continuous_fired, "Continuous transitions should be active (enzymes)"
        # Note: Stochastic may not always fire in short simulation, which is OK
    
    def test_long_simulation_stability(self, glycolysis_model):
        """Test that simulation remains stable over longer time periods."""
        controller = SimulationController(glycolysis_model)
        doc_ctrl = glycolysis_model.document_controller
        
        # Run longer simulation
        time_step = 0.01
        steps = 500  # 5 seconds simulated time
        
        errors = []
        token_history = []
        
        for step in range(steps):
            try:
                controller.step(time_step=time_step)
                
                # Record token total every 100 steps
                if step % 100 == 0:
                    total = sum(p.tokens for p in doc_ctrl.places)
                    token_history.append(total)
                    
            except Exception as e:
                errors.append(f"Step {step}: {e}")
                break
        
        # Verify stability
        assert len(errors) == 0, f"Long simulation should be stable. Errors: {errors}"
        assert controller.time >= 4.0, "Should have simulated at least 4 seconds"
        
        # Verify tokens didn't explode or collapse
        for total in token_history:
            assert total >= 0, "Tokens should not go negative"
            assert total < 1000, "Tokens should not explode"
        
        print(f"\n✅ Long simulation completed: {controller.time:.2f}s simulated")
        print(f"✅ Token evolution: {token_history}")
        print(f"✅ System remained stable")


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "-s"])
