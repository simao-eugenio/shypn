#!/usr/bin/env python3
"""Module - Partition of a modular Bio-PN.

This module defines the Module class for representing subsystem boundaries
in the modular Bio-PN architecture. Modules enable clean separation of
biological subsystems coupled through signal places rather than arcs.

Key principles:
- Each module contains a subset of places and transitions
- Modules share only signal places (Ψ_shared), never regular places
- No arcs cross module boundaries (enforced by validation)
- Modules can be hierarchical (parent/child relationships)
"""

from typing import Set, List, Optional, Tuple, TYPE_CHECKING
from shypn.netobjs.petri_net_object import PetriNetObject

if TYPE_CHECKING:
    from shypn.netobjs.place import Place
    from shypn.netobjs.transition import Transition


class Module:
    """Represents a partition of a Bio-PN (modular architecture).
    
    A Module is a subsystem containing places and transitions that interact
    locally through arcs, and globally through shared signal places.
    
    Mathematical definition (from modular Bio-PN formalism):
        M = (P_M, T_M, F_M, Ψ_M)
    where:
        - P_M ⊆ P: Places in this module
        - T_M ⊆ T: Transitions in this module
        - F_M: Flow relation (arcs within module)
        - Ψ_M ⊆ Ψ_shared: Boundary signals (read by this module)
    
    Properties:
        - Module independence: (Pᵢ ∩ Pⱼ) ⊆ Ψ_shared for all module pairs
        - Arc locality: All arcs stay within module boundaries
        - Signal coupling: Modules coordinate through Ψ_shared only
    
    Attributes:
        module_id: Unique identifier (e.g., "M_cytoplasm", "M1")
        name: Display name (e.g., "Cytoplasm", "Mitochondria")
        compartment_id: SBML compartment ID if mapped from SBML
        places: Set of Place objects in this module
        transitions: Set of Transition objects in this module
        boundary_signals: Set of signal places (Ψ_shared) readable by this module
        parent_module: Parent module (for hierarchical organization)
        child_modules: Child modules (for hierarchical organization)
        color: Visual color for GUI rendering (RGB tuple 0-1)
        collapsed: Whether module is collapsed in GUI (default: False)
    """
    
    def __init__(self, 
                 module_id: str,
                 name: str,
                 compartment_id: Optional[str] = None):
        """Initialize a module.
        
        Args:
            module_id: Unique identifier (e.g., "M1", "M_cytoplasm")
            name: Display name (e.g., "Cytoplasm", "Mitochondria")
            compartment_id: SBML compartment ID if mapped from SBML
        """
        self.module_id = module_id
        self.name = name
        self.compartment_id = compartment_id
        
        # Collections (using object references, not IDs)
        # Using Sets for O(1) membership testing
        self.places: Set = set()  # Place objects
        self.transitions: Set = set()  # Transition objects
        self.boundary_signals: Set = set()  # Signal Place objects (Ψ_shared)
        
        # Hierarchical organization
        self.parent_module: Optional['Module'] = None
        self.child_modules: List['Module'] = []
        
        # Visual properties (for GUI rendering - no implementation yet)
        self.color: Tuple[float, float, float] = (0.9, 0.9, 0.9)  # Light gray default
        self.collapsed: bool = False  # Whether module is visually collapsed
        
        # Metadata
        self.description: str = ""  # Optional description
        self.properties: dict = {}  # Extensible properties
    
    def add_place(self, place: 'Place') -> None:
        """Add a place to this module and set bidirectional reference.
        
        Args:
            place: Place object to add
        
        Note:
            Sets place.module_id to this module's ID (bidirectional link)
        """
        self.places.add(place)
        place.module_id = self.module_id
    
    def add_transition(self, transition: 'Transition') -> None:
        """Add a transition to this module and set bidirectional reference.
        
        Args:
            transition: Transition object to add
        
        Note:
            Sets transition.module_id to this module's ID (bidirectional link)
        """
        self.transitions.add(transition)
        transition.module_id = self.module_id
    
    def add_boundary_signal(self, signal_place: 'Place') -> None:
        """Mark a signal place as boundary (Ψ_shared).
        
        Args:
            signal_place: Signal Place object to add to boundary
        
        Raises:
            ValueError: If place is not marked as a signal place
        
        Note:
            Boundary signals enable cross-module information flow without arcs.
            They must be marked as is_signal_place = True.
        """
        if not signal_place.is_signal_place:
            raise ValueError(
                f"Place {signal_place.name} must be a signal place to be added as boundary signal. "
                f"Set is_signal_place=True first."
            )
        self.boundary_signals.add(signal_place)
    
    def remove_place(self, place: 'Place') -> None:
        """Remove a place from this module and clear its module reference.
        
        Args:
            place: Place object to remove
        """
        self.places.discard(place)
        if place.module_id == self.module_id:
            place.module_id = None
    
    def remove_transition(self, transition: 'Transition') -> None:
        """Remove a transition from this module and clear its module reference.
        
        Args:
            transition: Transition object to remove
        """
        self.transitions.discard(transition)
        if transition.module_id == self.module_id:
            transition.module_id = None
    
    def remove_boundary_signal(self, signal_place: 'Place') -> None:
        """Remove a signal place from boundary.
        
        Args:
            signal_place: Signal Place object to remove from boundary
        """
        self.boundary_signals.discard(signal_place)
    
    def set_parent(self, parent_module: Optional['Module']) -> None:
        """Set parent module (for hierarchical organization).
        
        Args:
            parent_module: Parent Module object, or None to clear
        
        Note:
            Updates bidirectional relationship (parent's child_modules list)
        """
        # Remove from old parent's children if exists
        if self.parent_module is not None:
            if self in self.parent_module.child_modules:
                self.parent_module.child_modules.remove(self)
        
        # Set new parent
        self.parent_module = parent_module
        
        # Add to new parent's children if not None
        if parent_module is not None:
            if self not in parent_module.child_modules:
                parent_module.child_modules.append(self)
    
    def add_child(self, child_module: 'Module') -> None:
        """Add a child module (for hierarchical organization).
        
        Args:
            child_module: Child Module object
        
        Note:
            Updates bidirectional relationship (child's parent_module)
        """
        if child_module not in self.child_modules:
            self.child_modules.append(child_module)
        child_module.parent_module = self
    
    def remove_child(self, child_module: 'Module') -> None:
        """Remove a child module.
        
        Args:
            child_module: Child Module object to remove
        """
        if child_module in self.child_modules:
            self.child_modules.remove(child_module)
            child_module.parent_module = None
    
    def get_all_places(self, recursive: bool = False) -> Set:
        """Get all places in this module.
        
        Args:
            recursive: If True, include places from child modules
        
        Returns:
            Set of Place objects
        """
        places = set(self.places)
        
        if recursive:
            for child in self.child_modules:
                places.update(child.get_all_places(recursive=True))
        
        return places
    
    def get_all_transitions(self, recursive: bool = False) -> Set:
        """Get all transitions in this module.
        
        Args:
            recursive: If True, include transitions from child modules
        
        Returns:
            Set of Transition objects
        """
        transitions = set(self.transitions)
        
        if recursive:
            for child in self.child_modules:
                transitions.update(child.get_all_transitions(recursive=True))
        
        return transitions
    
    def __repr__(self) -> str:
        """Return string representation for debugging."""
        return (
            f"Module(id='{self.module_id}', name='{self.name}', "
            f"places={len(self.places)}, transitions={len(self.transitions)}, "
            f"boundary_signals={len(self.boundary_signals)})"
        )
    
    def __str__(self) -> str:
        """Return human-readable string representation."""
        return f"{self.name} ({self.module_id})"
    
    def to_dict(self) -> dict:
        """Convert module to dictionary for serialization.
        
        Returns:
            Dictionary with module data (for JSON persistence)
        """
        return {
            'module_id': self.module_id,
            'name': self.name,
            'compartment_id': self.compartment_id,
            'place_ids': [p.id for p in self.places],
            'transition_ids': [t.id for t in self.transitions],
            'boundary_signal_ids': [s.id for s in self.boundary_signals],
            'parent_module_id': self.parent_module.module_id if self.parent_module else None,
            'child_module_ids': [c.module_id for c in self.child_modules],
            'color': self.color,
            'collapsed': self.collapsed,
            'description': self.description,
            'properties': self.properties
        }
    
    @staticmethod
    def from_dict(data: dict, place_lookup: dict, transition_lookup: dict) -> 'Module':
        """Create module from dictionary.
        
        Args:
            data: Dictionary with module data (from to_dict())
            place_lookup: Dict mapping place IDs to Place objects
            transition_lookup: Dict mapping transition IDs to Transition objects
        
        Returns:
            Module object
        
        Note:
            Parent/child relationships must be resolved after all modules are created
        """
        module = Module(
            module_id=data['module_id'],
            name=data['name'],
            compartment_id=data.get('compartment_id')
        )
        
        # Restore places
        for place_id in data.get('place_ids', []):
            if place_id in place_lookup:
                module.add_place(place_lookup[place_id])
        
        # Restore transitions
        for transition_id in data.get('transition_ids', []):
            if transition_id in transition_lookup:
                module.add_transition(transition_lookup[transition_id])
        
        # Restore boundary signals
        for signal_id in data.get('boundary_signal_ids', []):
            if signal_id in place_lookup:
                signal_place = place_lookup[signal_id]
                if signal_place.is_signal_place:
                    module.boundary_signals.add(signal_place)
        
        # Restore visual properties
        module.color = tuple(data.get('color', (0.9, 0.9, 0.9)))
        module.collapsed = data.get('collapsed', False)
        module.description = data.get('description', '')
        module.properties = data.get('properties', {})
        
        return module
