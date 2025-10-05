"""Petri Net Object Primitives.

This package contains the core Petri net modeling primitives:
- PetriNetObject: Base class for all Petri net objects
- Place: Circular nodes that hold tokens
- Transition: Rectangular bars representing events/actions
- Arc: Directed arrows connecting places and transitions (straight line)
- InhibitorArc: Inhibitor arcs with hollow circle marker (straight line)
- CurvedArc: Regular arcs with bezier curve (two-line arrowhead)
- CurvedInhibitorArc: Inhibitor arcs with bezier curve (hollow circle marker)

All classes are exported at the package level for convenient importing.
"""
from shypn.netobjs.petri_net_object import PetriNetObject
from shypn.netobjs.place import Place
from shypn.netobjs.transition import Transition
from shypn.netobjs.arc import Arc
from shypn.netobjs.inhibitor_arc import InhibitorArc
from shypn.netobjs.curved_arc import CurvedArc
from shypn.netobjs.curved_inhibitor_arc import CurvedInhibitorArc

__all__ = [
    'PetriNetObject',
    'Place',
    'Transition',
    'Arc',
    'InhibitorArc',
    'CurvedArc',
    'CurvedInhibitorArc'
]
