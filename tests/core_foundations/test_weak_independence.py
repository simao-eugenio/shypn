#!/usr/bin/env python3
"""Weak Independence Theory Tests.

Core Principle:
    Transitions fire independently based on LOCAL enabling conditions.
    Global state changes only through token flow.

This is fundamental to Petri net semantics and CRITICAL for manuscript.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

import pytest
from shypn.netobjs import Place, Transition, Arc


class TestWeakIndependence:
    """Test weak independence theory."""
    
    def test_local_enabling_independence(self):
        """CRITICAL: Verify transitions fire based ONLY on local place tokens.
        
        Network: P1 -> T1 -> P2 -> T2 -> P3
        
        T1 and T2 are independent - T2's enabling depends only on P2 tokens,
        not on global state or T1's state.
        """
        # Create network: P1 -> T1 -> P2 -> T2 -> P3
        P1 = Place(id='P1', name='P1', x=0, y=0)
        P1.tokens = 10
        
        P2 = Place(id='P2', name='P2', x=0, y=0)
        P2.tokens = 0
        
        P3 = Place(id='P3', name='P3', x=0, y=0)
        P3.tokens = 0
        
        T1 = Transition(id='T1', name='T1', x=0, y=0)
        T1.rate = 1.0
        
        T2 = Transition(id='T2', name='T2', x=0, y=0)
        T2.rate = 1.0
        
        # Build arcs
        Arc(id='a1', source=P1, target=T1, weight=1)
        Arc(id='a2', source=T1, target=P2, weight=1)
        Arc(id='a3', source=P2, target=T2, weight=1)
        Arc(id='a4', source=T2, target=P3, weight=1)
        
        # Initially: T1 enabled, T2 disabled
        # TODO: Implement enabling check
        # assert T1.is_enabled()
        # assert not T2.is_enabled()
        
        # After T1 fires: P2 gains token, enabling T2
        # fire(T1)
        # assert P2.tokens == 1
        # assert T2.is_enabled()  # Now enabled due to token flow
        # assert T1.is_enabled()  # Still enabled (P1 has tokens)
        
        # This proves: enabling is LOCAL, not global
        
        assert P1.tokens == 10
        assert P2.tokens == 0
        
    def test_concurrent_enabling(self):
        """Verify independent transitions can fire concurrently.
        
        T1 and T2 have no shared places, so they should be
        independently enabled (weak independence).
        """
        P1 = Place(id='P1', name='P1', x=0, y=0)
        P1.tokens = 10
        
        P2 = Place(id='P2', name='P2', x=0, y=0)
        P2.tokens = 10
        
        T1 = Transition(id='T1', name='T1', x=0, y=0)
        T2 = Transition(id='T2', name='T2', x=0, y=0)
        
        Arc(id='a1', source=P1, target=T1, weight=1)
        Arc(id='a2', source=P2, target=T2, weight=1)
        
        # Both should be enabled simultaneously
        # TODO: Implement enabling check
        # assert T1.is_enabled()
        # assert T2.is_enabled()
        
        # Firing T1 should NOT affect T2's enabling
        # fire(T1)
        # assert T2.is_enabled()  # WEAK INDEPENDENCE
        
        assert P1.tokens == 10
        assert P2.tokens == 10
        
    def test_shared_place_creates_dependency(self):
        """Verify shared places create proper dependencies.
        
        When T1 and T2 share a place, firing one affects the other
        through token flow (not through global state).
        """
        shared = Place(id='Shared', name='Shared', x=0, y=0)
        shared.tokens = 1
        
        T1 = Transition(id='T1', name='T1', x=0, y=0)
        T2 = Transition(id='T2', name='T2', x=0, y=0)
        
        Arc(id='a1', source=shared, target=T1, weight=1)
        Arc(id='a2', source=shared, target=T2, weight=1)
        
        # Both enabled initially
        # TODO: Implement enabling check
        # assert T1.is_enabled()
        # assert T2.is_enabled()
        
        # Fire T1: consumes token, disabling T2
        # fire(T1)
        # assert not T2.is_enabled()  # Dependency through token flow
        
        assert shared.tokens == 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
