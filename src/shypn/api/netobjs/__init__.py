"""Petri Net Object Primitives.

This package contains the core Petri net modeling primitives:
- PetriNetObject: Base class for all Petri net objects
- Place: Circular nodes that hold tokens
- Transition: Rectangular bars representing events/actions
- Arc: Directed arrows connecting places and transitions
- InhibitorArc: Special arcs that inhibit transitions

All classes are exported at the package level for convenient importing.
"""
from shypn.api.netobjs.petri_net_object import PetriNetObject
from shypn.api.netobjs.place import Place
from shypn.api.netobjs.transition import Transition
from shypn.api.netobjs.arc import Arc
from shypn.api.netobjs.inhibitor_arc import InhibitorArc

__all__ = ['PetriNetObject', 'Place', 'Transition', 'Arc', 'InhibitorArc']
