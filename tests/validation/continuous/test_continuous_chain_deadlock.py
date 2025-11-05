"""Test continuous transition chain equilibrium and deadlock scenarios.

Tests various configurations of continuous transitions in chains to verify:
1. Equilibrium states (production = consumption)
2. Deadlock conditions (transitions stop firing)
3. Continuous vs stochastic source behavior with discrete consumers
"""

import pytest
from shypn.engine.simulation.controller import SimulationController
from shypn.data.model_canvas_manager import ModelCanvasManager


class TestContinuousChainEquilibrium:
    """Test equilibrium and deadlock in continuous transition chains."""
    
    def test_continuous_source_immediate_consumer_deadlock(self):
        """Test deadlock: continuous source + immediate consumer with weight=1.
        
        Setup:
            T_source(continuous, rate=1.0, is_source=True) --> P1(0) --> T_consumer(immediate, rate=MM)
        
        Expected:
            - P1 accumulates fractional tokens (< 1.0)
            - T_consumer requires full token (weight=1)
            - System reaches equilibrium before T_consumer can fire
            - DEADLOCK: T_consumer never fires
        """
        manager = ModelCanvasManager(canvas_width=2000, canvas_height=2000)
        doc_ctrl = manager.document_controller
        
        # Create chain: T_source -> P1 -> T_consumer -> P2
        p1 = doc_ctrl.add_place(x=200, y=100, label="P1")
        p2 = doc_ctrl.add_place(x=400, y=100, label="P2")
        p1.tokens = 0.0
        p2.tokens = 0.0
        
        t_source = doc_ctrl.add_transition(x=100, y=100, label="T_source")
        t_source.transition_type = "continuous"
        t_source.is_source = True
        t_source.properties = {'rate_function': '1.0'}
        
        t_consumer = doc_ctrl.add_transition(x=300, y=100, label="T_consumer")
        t_consumer.transition_type = "immediate"
        t_consumer.properties = {'rate_function': '5.0'}  # High rate, should fire if enabled
        
        arc_source_out = doc_ctrl.add_arc(source=t_source, target=p1, weight=1.0)
        arc_consumer_in = doc_ctrl.add_arc(source=p1, target=t_consumer, weight=1.0)  # Requires 1.0 token
        arc_consumer_out = doc_ctrl.add_arc(source=t_consumer, target=p2, weight=1.0)
        
        controller = SimulationController(manager)
        
        # Run simulation for 10 seconds
        time_step = 0.01
        total_time = 10.0
        steps = int(total_time / time_step)
        
        for _ in range(steps):
            controller.step(time_step=time_step)
        
        # Verify deadlock condition
        print(f"\nDEADLOCK TEST RESULTS:")
        print(f"  P1 tokens: {p1.tokens:.4f}")
        print(f"  P2 tokens: {p2.tokens:.4f}")
        print(f"  T_consumer enabled: {t_consumer.is_enabled()}")
        
        # P1 should have fractional tokens (< 1.0)
        assert p1.tokens < 1.0, f"P1 should have < 1.0 tokens, got {p1.tokens}"
        assert p1.tokens > 0.0, f"P1 should have > 0 tokens, got {p1.tokens}"
        
        # P2 should be empty (T_consumer never fired)
        assert p2.tokens == 0.0, f"P2 should be empty, got {p2.tokens}"
        
        # T_consumer should be disabled (insufficient tokens)
        assert not t_consumer.is_enabled(), "T_consumer should be disabled"
        
        print("  ✓ DEADLOCK CONFIRMED: Continuous source cannot feed immediate consumer")
    
    def test_stochastic_source_immediate_consumer_works(self):
        """Test stochastic source + immediate consumer works (bursts provide full tokens).
        
        Setup:
            T_source(stochastic, rate=1.0, is_source=True) --> P1(0) --> T_consumer(immediate)
        
        Expected:
            - P1 receives discrete bursts of 1.0 token each
            - T_consumer fires when P1 >= 1.0
            - P2 accumulates tokens
            - NO DEADLOCK
        """
        manager = ModelCanvasManager(canvas_width=2000, canvas_height=2000)
        doc_ctrl = manager.document_controller
        
        # Create chain: T_source -> P1 -> T_consumer -> P2
        p1 = doc_ctrl.add_place(x=200, y=100, label="P1")
        p2 = doc_ctrl.add_place(x=400, y=100, label="P2")
        p1.tokens = 0.0
        p2.tokens = 0.0
        
        t_source = doc_ctrl.add_transition(x=100, y=100, label="T_source")
        t_source.transition_type = "stochastic"  # Changed to stochastic
        t_source.is_source = True
        t_source.properties = {'rate_function': '1.0'}
        
        t_consumer = doc_ctrl.add_transition(x=300, y=100, label="T_consumer")
        t_consumer.transition_type = "immediate"
        t_consumer.properties = {'rate_function': '5.0'}
        
        arc_source_out = doc_ctrl.add_arc(source=t_source, target=p1, weight=1.0)
        arc_consumer_in = doc_ctrl.add_arc(source=p1, target=t_consumer, weight=1.0)
        arc_consumer_out = doc_ctrl.add_arc(source=t_consumer, target=p2, weight=1.0)
        
        controller = SimulationController(manager)
        
        # Run simulation
        time_step = 0.01
        total_time = 10.0
        steps = int(total_time / time_step)
        
        for _ in range(steps):
            controller.step(time_step=time_step)
        
        print(f"\nSTOCHASTIC SOURCE TEST RESULTS:")
        print(f"  P1 tokens: {p1.tokens:.4f}")
        print(f"  P2 tokens: {p2.tokens:.4f}")
        
        # P2 should have accumulated tokens (T_consumer fired)
        assert p2.tokens > 0.0, f"P2 should have tokens, got {p2.tokens}"
        
        print("  ✓ SUCCESS: Stochastic source provides bursts, immediate consumer fires")
    
    def test_continuous_chain_equilibrium(self):
        """Test equilibrium in continuous chain with competing consumers.
        
        Setup:
            T_source(rate=1.0) --> P1(0) --> T1(rate=0.3) --> P2
                                      |--> T2(rate=0.3) --> P3
        
        Expected:
            - P1 reaches equilibrium when production = total consumption
            - T_source rate = T1 rate + T2 rate
            - Steady-state at P1 = some equilibrium value
            - P2 and P3 accumulate at equal rates
        """
        manager = ModelCanvasManager(canvas_width=2000, canvas_height=2000)
        doc_ctrl = manager.document_controller
        
        # Create topology
        p1 = doc_ctrl.add_place(x=200, y=200, label="P1")
        p2 = doc_ctrl.add_place(x=400, y=100, label="P2")
        p3 = doc_ctrl.add_place(x=400, y=300, label="P3")
        p1.tokens = 0.0
        p2.tokens = 0.0
        p3.tokens = 0.0
        
        t_source = doc_ctrl.add_transition(x=100, y=200, label="T_source")
        t_source.transition_type = "continuous"
        t_source.is_source = True
        t_source.properties = {'rate_function': '1.0'}
        
        t1 = doc_ctrl.add_transition(x=300, y=100, label="T1")
        t1.transition_type = "continuous"
        t1.properties = {'rate_function': '0.3'}
        
        t2 = doc_ctrl.add_transition(x=300, y=300, label="T2")
        t2.transition_type = "continuous"
        t2.properties = {'rate_function': '0.3'}
        
        # Connect topology
        doc_ctrl.add_arc(source=t_source, target=p1, weight=1.0)
        doc_ctrl.add_arc(source=p1, target=t1, weight=1.0)
        doc_ctrl.add_arc(source=t1, target=p2, weight=1.0)
        doc_ctrl.add_arc(source=p1, target=t2, weight=1.0)
        doc_ctrl.add_arc(source=t2, target=p3, weight=1.0)
        
        controller = SimulationController(manager)
        
        # Run until equilibrium
        time_step = 0.01
        total_time = 20.0
        steps = int(total_time / time_step)
        
        p1_history = []
        
        for i in range(steps):
            controller.step(time_step=time_step)
            if i % 100 == 0:  # Sample every second
                p1_history.append(p1.tokens)
        
        print(f"\nCONTINUOUS CHAIN EQUILIBRIUM TEST:")
        print(f"  P1 tokens (final): {p1.tokens:.4f}")
        print(f"  P2 tokens (final): {p2.tokens:.4f}")
        print(f"  P3 tokens (final): {p3.tokens:.4f}")
        print(f"  P1 equilibrium stability: {p1_history[-5:]}")
        
        # P1 should reach equilibrium (not growing unboundedly)
        assert p1.tokens < 10.0, f"P1 should stabilize, got {p1.tokens}"
        
        # P2 and P3 should accumulate (consumption rate 0.3 + 0.3 < production rate 1.0)
        assert p2.tokens > 0.0, "P2 should accumulate"
        assert p3.tokens > 0.0, "P3 should accumulate"
        
        # Check P1 stability (last 5 samples should be similar)
        if len(p1_history) >= 5:
            variance = max(p1_history[-5:]) - min(p1_history[-5:])
            assert variance < 0.5, f"P1 not stable, variance={variance}"
        
        # With production=1.0 and consumption=0.6, excess 0.4 goes downstream
        expected_p2_p3_total = 0.4 * total_time
        actual_p2_p3_total = p2.tokens + p3.tokens
        # Allow 10% error
        assert abs(actual_p2_p3_total - expected_p2_p3_total) / expected_p2_p3_total < 0.15, \
            f"Expected ~{expected_p2_p3_total} in P2+P3, got {actual_p2_p3_total}"
        
        print("  ✓ EQUILIBRIUM REACHED: Production balanced with consumption")
    
    def test_continuous_chain_exact_balance_deadlock(self):
        """Test exact balance deadlock: production exactly equals consumption.
        
        Setup:
            T_source(rate=1.0) --> P1(0) --> T1(rate=0.5) --> P2
                                      |--> T2(rate=0.5) --> P3
        
        Expected:
            - P1 reaches equilibrium at some steady-state value
            - Total consumption = production (0.5 + 0.5 = 1.0)
            - P2 and P3 accumulate at equal rates
            - No deadlock, but P1 stays at constant equilibrium
        """
        manager = ModelCanvasManager(canvas_width=2000, canvas_height=2000)
        doc_ctrl = manager.document_controller
        
        # Create topology
        p1 = doc_ctrl.add_place(x=200, y=200, label="P1")
        p2 = doc_ctrl.add_place(x=400, y=100, label="P2")
        p3 = doc_ctrl.add_place(x=400, y=300, label="P3")
        p1.tokens = 0.0
        p2.tokens = 0.0
        p3.tokens = 0.0
        
        t_source = doc_ctrl.add_transition(x=100, y=200, label="T_source")
        t_source.transition_type = "continuous"
        t_source.is_source = True
        t_source.properties = {'rate_function': '1.0'}
        
        t1 = doc_ctrl.add_transition(x=300, y=100, label="T1")
        t1.transition_type = "continuous"
        t1.properties = {'rate_function': '0.5'}  # Exactly half of source rate
        
        t2 = doc_ctrl.add_transition(x=300, y=300, label="T2")
        t2.transition_type = "continuous"
        t2.properties = {'rate_function': '0.5'}  # Other half
        
        # Connect topology
        doc_ctrl.add_arc(source=t_source, target=p1, weight=1.0)
        doc_ctrl.add_arc(source=p1, target=t1, weight=1.0)
        doc_ctrl.add_arc(source=t1, target=p2, weight=1.0)
        doc_ctrl.add_arc(source=p1, target=t2, weight=1.0)
        doc_ctrl.add_arc(source=t2, target=p3, weight=1.0)
        
        controller = SimulationController(manager)
        
        # Run simulation
        time_step = 0.01
        total_time = 20.0
        steps = int(total_time / time_step)
        
        for _ in range(steps):
            controller.step(time_step=time_step)
        
        print(f"\nEXACT BALANCE TEST:")
        print(f"  P1 tokens (equilibrium): {p1.tokens:.4f}")
        print(f"  P2 tokens: {p2.tokens:.4f}")
        print(f"  P3 tokens: {p3.tokens:.4f}")
        print(f"  P2/P3 ratio: {p2.tokens/p3.tokens if p3.tokens > 0 else 'N/A':.4f}")
        
        # P1 should be at equilibrium (small, stable value)
        assert p1.tokens < 2.0, f"P1 should be at equilibrium, got {p1.tokens}"
        
        # P2 and P3 should accumulate equally (rate=0.5 each, time=20 -> ~10 each)
        expected_accumulation = 0.5 * total_time
        assert abs(p2.tokens - expected_accumulation) / expected_accumulation < 0.15
        assert abs(p3.tokens - expected_accumulation) / expected_accumulation < 0.15
        
        # P2 and P3 should be approximately equal
        if p2.tokens > 0 and p3.tokens > 0:
            ratio = p2.tokens / p3.tokens
            assert 0.9 < ratio < 1.1, f"P2 and P3 should be equal, ratio={ratio}"
        
        print("  ✓ EXACT BALANCE: System maintains steady-state flow")
    
    def test_continuous_michaelis_menten_equilibrium(self):
        """Test equilibrium with Michaelis-Menten kinetics (like KEGG model).
        
        Setup:
            T_source(rate=1.0) --> P1(0) --> T1(rate=MM(P1, 10, 0.5))
        
        Expected:
            - P1 reaches equilibrium where production = MM consumption
            - Equilibrium point depends on Vmax and Km
            - System naturally finds steady-state
        """
        manager = ModelCanvasManager(canvas_width=2000, canvas_height=2000)
        doc_ctrl = manager.document_controller
        
        # Create chain
        p1 = doc_ctrl.add_place(x=200, y=100, label="P1")
        p2 = doc_ctrl.add_place(x=400, y=100, label="P2")
        p1.tokens = 0.0
        p2.tokens = 0.0
        
        t_source = doc_ctrl.add_transition(x=100, y=100, label="T_source")
        t_source.transition_type = "continuous"
        t_source.is_source = True
        t_source.properties = {'rate_function': '1.0'}
        
        t1 = doc_ctrl.add_transition(x=300, y=100, label="T1")
        t1.transition_type = "continuous"
        t1.properties = {'rate_function': 'michaelis_menten(P1, 10.0, 0.5)'}
        
        doc_ctrl.add_arc(source=t_source, target=p1, weight=1.0)
        doc_ctrl.add_arc(source=p1, target=t1, weight=1.0)
        doc_ctrl.add_arc(source=t1, target=p2, weight=1.0)
        
        controller = SimulationController(manager)
        
        # Run simulation
        time_step = 0.01
        total_time = 20.0
        steps = int(total_time / time_step)
        
        p1_samples = []
        
        for i in range(steps):
            controller.step(time_step=time_step)
            if i % 100 == 0:
                p1_samples.append(p1.tokens)
        
        print(f"\nMICHAELIS-MENTEN EQUILIBRIUM TEST:")
        print(f"  P1 equilibrium: {p1.tokens:.4f}")
        print(f"  P2 accumulated: {p2.tokens:.4f}")
        print(f"  P1 trajectory (last 5): {p1_samples[-5:]}")
        
        # P1 should reach small equilibrium (since Vmax=10 >> source rate=1.0)
        # At equilibrium: 1.0 = 10*P1/(0.5+P1) -> P1 ≈ 0.056
        expected_equilibrium = 0.056  # Analytical solution
        
        assert p1.tokens < 0.2, f"P1 should be at low equilibrium, got {p1.tokens}"
        assert abs(p1.tokens - expected_equilibrium) < 0.05, \
            f"Expected equilibrium ~{expected_equilibrium}, got {p1.tokens}"
        
        # Check stability
        if len(p1_samples) >= 5:
            variance = max(p1_samples[-5:]) - min(p1_samples[-5:])
            assert variance < 0.02, f"P1 not stable, variance={variance}"
        
        print(f"  ✓ MM EQUILIBRIUM: P1 stabilized at ~{p1.tokens:.4f} (expected ~{expected_equilibrium:.4f})")


# ============================================================================
# Summary Documentation
# ============================================================================

def test_documentation():
    """Document test findings and design guidelines."""
    print("\n" + "="*70)
    print("CONTINUOUS CHAIN EQUILIBRIUM TEST SUMMARY")
    print("="*70)
    print()
    print("KEY FINDINGS:")
    print()
    print("1. CONTINUOUS SOURCE + IMMEDIATE CONSUMER = DEADLOCK")
    print("   - Continuous produces fractional tokens")
    print("   - Immediate requires full integer tokens")
    print("   - System stalls at equilibrium < 1.0")
    print()
    print("2. STOCHASTIC SOURCE + IMMEDIATE CONSUMER = WORKS")
    print("   - Stochastic fires in discrete bursts")
    print("   - Each burst provides full token(s)")
    print("   - Immediate transition can fire")
    print()
    print("3. CONTINUOUS CHAINS REACH EQUILIBRIUM")
    print("   - Production rate = consumption rate")
    print("   - Steady-state concentration maintained")
    print("   - Biologically realistic (homeostasis)")
    print()
    print("4. MICHAELIS-MENTEN KINETICS")
    print("   - Natural feedback regulation")
    print("   - Equilibrium point: rate_source = Vmax*[S]/(Km+[S])")
    print("   - Models enzymatic reactions accurately")
    print()
    print("DESIGN GUIDELINES:")
    print()
    print("  ✓ Continuous -> Continuous: Use for ODE-like models")
    print("  ✓ Stochastic -> Immediate: Use for discrete event chains")
    print("  ✓ Continuous -> Immediate: AVOID (causes deadlock)")
    print("  ✓ Equilibrium behavior: Expected in metabolic pathways")
    print()
    print("="*70)
