"""Regression test: inhibitor arcs MUST NOT consume tokens.

Per the 13-tuple Bio-PN formalism (Simão 2025) and classical PN literature
(Murata 1989, ISO/IEC 15909, GreatSPN, Snoopy), inhibitor arcs (including
SHyPN's ``curved_inhibitor_arc`` variant) are presence-absence checks: they
invert the enablement predicate (``tokens >= threshold → disabled``) but
transfer **no mass** when the transition fires.

SHyPN's only extension to the classical inhibitor arc is the *flexibility on
threshold evaluation*: ``threshold`` may be any runtime expression rather
than a static integer. Consumption semantics are unchanged.

Background: the bacillus_sporulation_v2 thesis model exposed silent
Spo0A pool annihilation when the engine consumed inhibitor tokens
(2026-05-08). This regression test pins the corrected behaviour so the
defect cannot reappear.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from shypn.netobjs.place import Place
from shypn.netobjs.transition import Transition
from shypn.netobjs.inhibitor_arc import InhibitorArc
from shypn.netobjs.curved_inhibitor_arc import CurvedInhibitorArc


def test_inhibitor_arc_consumes_tokens_returns_false():
    """InhibitorArc.consumes_tokens() must return False (classical PN)."""
    src = Place(x=0, y=0, id='p1', name='Product')
    src.tokens = 10
    tgt = Transition(x=100, y=0, id='t1', name='T_produce')
    arc = InhibitorArc(src, tgt, id='i1', name='I1', weight=5.0)
    assert arc.consumes_tokens() is False, (
        "InhibitorArc must be non-consuming per classical PN semantics"
    )


def test_curved_inhibitor_arc_consumes_tokens_returns_false():
    """CurvedInhibitorArc.consumes_tokens() must return False."""
    src = Place(x=0, y=0, id='p1', name='Product')
    src.tokens = 10
    tgt = Transition(x=100, y=0, id='t1', name='T_produce')
    arc = CurvedInhibitorArc(src, tgt, id='ci1', name='CI1', weight=5.0)
    assert arc.consumes_tokens() is False, (
        "CurvedInhibitorArc must be non-consuming per classical PN semantics"
    )


def test_arc_loaded_with_inhibitor_arc_type_is_non_consuming():
    """A plain Arc with arc_type='inhibitor' (loaded from .shy via
    ``_arc_type_override``) must report non-consuming."""
    from shypn.netobjs.arc import Arc

    src = Place(x=0, y=0, id='p1', name='Product')
    src.tokens = 10
    tgt = Transition(x=100, y=0, id='t1', name='T_produce')
    arc = Arc(src, tgt, id='a1', name='A1', weight=5.0)
    arc._arc_type_override = 'inhibitor'
    assert arc.consumes_tokens() is False


def test_arc_loaded_with_curved_inhibitor_arc_type_is_non_consuming():
    """A plain Arc with arc_type='curved_inhibitor_arc' must report
    non-consuming (substring match)."""
    from shypn.netobjs.arc import Arc

    src = Place(x=0, y=0, id='p1', name='Product')
    src.tokens = 10
    tgt = Transition(x=100, y=0, id='t1', name='T_produce')
    arc = Arc(src, tgt, id='a1', name='A1', weight=5.0)
    arc._arc_type_override = 'curved_inhibitor_arc'
    assert arc.consumes_tokens() is False


def test_normal_arc_consumes_tokens():
    """Sanity check — normal arcs MUST consume."""
    from shypn.netobjs.arc import Arc

    src = Place(x=0, y=0, id='p1', name='S')
    src.tokens = 10
    tgt = Transition(x=100, y=0, id='t1', name='T')
    arc = Arc(src, tgt, id='a1', name='A1', weight=1.0)
    assert arc.consumes_tokens() is True


if __name__ == '__main__':
    test_inhibitor_arc_consumes_tokens_returns_false()
    test_curved_inhibitor_arc_consumes_tokens_returns_false()
    test_arc_loaded_with_inhibitor_arc_type_is_non_consuming()
    test_arc_loaded_with_curved_inhibitor_arc_type_is_non_consuming()
    test_normal_arc_consumes_tokens()
    print("All inhibitor non-consumption invariants OK.")
