"""Petri Net Object Primitives.

This package contains the core Petri net modeling primitives:
- PetriNetObject: Base class for all Petri net objects
- Place: Circular nodes that hold tokens
- Transition: Rectangular bars representing events/actions
- Arc: Directed arrows connecting places and transitions
- InhibitorArc: Special arcs that inhibit transitions

All classes are exported at the package level for convenient importing.
"""
from shypn.netobjs.petri_net_object import PetriNetObject
from shypn.netobjs.place import Place
from shypn.netobjs.transition import Transition
from shypn.netobjs.arc import Arc
from shypn.netobjs.inhibitor_arc import InhibitorArc

__all__ = ['PetriNetObject', 'Place', 'Transition', 'Arc', 'InhibitorArc']
