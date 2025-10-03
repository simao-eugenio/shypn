"""Petri Net API - Object classes for modeling Petri nets.

This package provides the core Petri net object classes:
- PetriNetObject: Base class with shared properties and behaviors
- Place: Circular nodes that hold tokens
- Arc: Directed arrows connecting places and transitions
- InhibitorArc: Inhibitor arcs with circular markers (derived from Arc)
- Transition: Rectangular bars representing events/actions

All classes are exported at the package level for convenient importing.
"""
from shypn.api.petri_net_object import PetriNetObject
from shypn.api.place import Place
from shypn.api.arc import Arc
from shypn.api.inhibitor_arc import InhibitorArc
from shypn.api.transition import Transition

__all__ = ['PetriNetObject', 'Place', 'Arc', 'InhibitorArc', 'Transition']
