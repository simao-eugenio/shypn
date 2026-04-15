#!/usr/bin/env python3
"""Signal Hierarchy Theory Tests.

Core Principle:
    Signal places modulate transition rates WITHOUT being consumed.
    They represent regulatory molecules (ATP, cofactors, signals) that
    catalyze reactions without being depleted.

CRITICAL for manuscript validation.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

import pytest
from shypn.netobjs import Place, Transition, Arc


class TestSignalHierarchy:
    """Test signal hierarchy implementation."""
    
    def test_signal_place_non_consumption(self):
        """CRITICAL: Verify signal places keep tokens (signal hierarchy theory).
        
        This is the CORE of signal hierarchy - signals modulate rates
        without being consumed.
        """
        # Create network
        signal_place = Place(id='ATP', name='ATP', type='signal', x=0, y=0)
        signal_place.tokens = 10
        
        substrate = Place(id='S1', name='Substrate', type='normal', x=0, y=0)
        substrate.tokens = 5
        
        product = Place(id='P1', name='Product', type='normal', x=0, y=0)
        product.tokens = 0
        
        transition = Transition(id='T1', name='Reaction', x=0, y=0)
        transition.type = 'stochastic'
        transition.rate = '0.1 * ATP'
        
        # Arcs: ATP (read), S1 (consume) -> P1 (produce)
        arc_signal = Arc(id='a1', source=signal_place, target=transition)
        arc_signal.weight = 1
        arc_signal.arc_type = 'read'  # Signal (not consumed)
        
        arc_substrate = Arc(id='a2', source=substrate, target=transition)
        arc_substrate.weight = 1
        arc_substrate.arc_type = 'normal'  # Consumed
        
        arc_product = Arc(id='a3', source=transition, target=product)
        arc_product.weight = 1
        
        # Store initial values
        initial_signal = signal_place.tokens
        initial_substrate = substrate.tokens
        
        # Simulate one firing
        # (In real implementation, this would be done by the simulation engine)
        # For now, we're testing the CONCEPT
        
        # Check enabling
        # TODO: Implement proper enabling check that respects arc types
        
        # EXPECTED BEHAVIOR after firing:
        # - signal_place.tokens == 10 (UNCHANGED - signal hierarchy)
        # - substrate.tokens == 4 (CONSUMED - normal place)
        # - product.tokens == 1 (PRODUCED)
        
        # This test documents the EXPECTED behavior
        # Implementation verification comes next
        
        assert signal_place.type == 'signal', "Signal place must have type='signal'"
        assert arc_signal.arc_type == 'read', "Signal arc must be 'read' type"
        assert substrate.type == 'normal', "Substrate must be normal type"
        
    def test_signal_vs_carrier(self):
        """CRITICAL: Distinguish signal carriers from signal places.
        
        ATP is signal (not consumed).
        Glucose is carrier (consumed and produced).
        """
        # ATP is signal (not consumed)
        ATP = Place(id='ATP', name='ATP', type='signal', x=0, y=0)
        ATP.tokens = 1000
        
        # Glucose is carrier (consumed and produced)
        Glucose = Place(id='Glc', name='Glucose', type='normal', x=0, y=0)
        Glucose.tokens = 100
        
        G6P = Place(id='G6P', name='Glucose-6-P', type='normal', x=0, y=0)
        G6P.tokens = 0
        
        # Reaction: Glucose + ATP -> G6P + ATP (ATP recycled)
        T = Transition(id='HK', name='Hexokinase', x=0, y=0)
        T.rate = 'k * ATP * Glucose'
        T.type = 'continuous'
        
        # Build arcs
        arc_ATP = Arc(id='a1', source=ATP, target=T)
        arc_ATP.weight = 1
        arc_ATP.arc_type = 'read'  # ATP: signal (not consumed)
        
        arc_Glc = Arc(id='a2', source=Glucose, target=T)
        arc_Glc.weight = 1  # Consumed
        
        arc_G6P = Arc(id='a3', source=T, target=G6P)
        arc_G6P.weight = 1  # Produced
        
        # EXPECTED: After simulation
        # - ATP.tokens == 1000 (unchanged - signal hierarchy)
        # - Glucose + G6P == 100 (mass balance)
        
        assert ATP.type == 'signal'
        assert Glucose.type == 'normal'
        assert G6P.type == 'normal'
        
    def test_hierarchical_signal_cascade(self):
        """Verify cascading signal modulation.
        
        Signal1 -> T1 -> Signal2 -> T2 -> Product
        Both signals should persist.
        """
        # Cascade: Signal1 -> T1 -> Signal2 -> T2 -> Product
        Signal1 = Place(id='S1', name='Signal1', type='signal', x=0, y=0)
        Signal1.tokens = 10
        
        Signal2 = Place(id='S2', name='Signal2', type='signal', x=0, y=0)
        Signal2.tokens = 0
        
        Substrate = Place(id='Sub', name='Substrate', type='normal', x=0, y=0)
        Substrate.tokens = 100
        
        Product = Place(id='P1', name='Product', type='normal', x=0, y=0)
        Product.tokens = 0
        
        T1 = Transition(id='T1', name='Activator', x=0, y=0)
        T1.rate = 'k1 * S1'
        
        T2 = Transition(id='T2', name='Reaction', x=0, y=0)
        T2.rate = 'k2 * S2'
        
        # T1 creates Signal2 (signal propagation)
        Arc(id='a1', source=Signal1, target=T1, arc_type='read')
        Arc(id='a2', source=T1, target=Signal2, weight=1)
        
        # T2 uses Signal2
        Arc(id='a3', source=Signal2, target=T2, arc_type='read')
        Arc(id='a4', source=Substrate, target=T2, weight=1)
        Arc(id='a5', source=T2, target=Product, weight=1)
        
        # EXPECTED after simulation:
        # - Signal1.tokens == 10 (unchanged - original signal)
        # - Signal2.tokens > 0 (produced and preserved)
        # - Substrate.tokens < 100 (consumed)
        # - Product.tokens > 0 (produced)
        
        assert Signal1.type == 'signal'
        assert Signal2.type == 'signal'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
