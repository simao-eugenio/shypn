"""Data Transfer Objects for Knowledge Base.

This module provides a normalized interface for transferring data from
various sources (Report Panel, Topology Analyzer, BRENDA, etc.) into
the Knowledge Base. All external modules should use these DTOs instead
of passing raw objects or dicts.

DESIGN PRINCIPLE:
-----------------
The KB should NEVER receive:
- Model objects directly (Place, Transition, Arc)
- Raw dictionaries with inconsistent schemas
- String representations of objects

The KB should ONLY receive:
- Strongly-typed DTOs with validated fields
- Explicit IDs (strings)
- Well-defined data structures

Author: Simão Eugénio
Date: November 11, 2025
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any


# ============================================================================
# STRUCTURAL DTOs - From Report Panel / Model
# ============================================================================

@dataclass
class PlaceDTO:
    """Normalized place data for KB ingestion."""
    place_id: str
    label: str = ""
    initial_marking: int = 0
    
    # Optional metadata from SBML/KEGG import
    compound_id: Optional[str] = None      # e.g., "C00031"
    compound_name: Optional[str] = None    # e.g., "D-Glucose"
    chebi_id: Optional[str] = None
    
    @classmethod
    def from_object(cls, place_obj) -> 'PlaceDTO':
        """Create DTO from model Place object.
        
        Args:
            place_obj: Place object with .id, .label, .tokens attributes
            
        Returns:
            PlaceDTO with normalized data
        """
        # Extract compound metadata if available
        compound_id = None
        compound_name = None
        chebi_id = None
        
        if hasattr(place_obj, 'metadata') and place_obj.metadata:
            compound_id = place_obj.metadata.get('kegg_id') or place_obj.metadata.get('compound_id')
            compound_name = place_obj.metadata.get('compound_name')
            chebi_id = place_obj.metadata.get('chebi_id')
        
        return cls(
            place_id=str(place_obj.id) if hasattr(place_obj, 'id') else str(place_obj),
            label=str(place_obj.label) if hasattr(place_obj, 'label') else '',
            initial_marking=int(place_obj.tokens) if hasattr(place_obj, 'tokens') else 0,
            compound_id=compound_id,
            compound_name=compound_name,
            chebi_id=chebi_id
        )
    
    @classmethod
    def from_dict(cls, data: dict) -> 'PlaceDTO':
        """Create DTO from dictionary.
        
        Args:
            data: Dict with 'place_id', 'label', 'initial_marking' keys
            
        Returns:
            PlaceDTO with normalized data
        """
        return cls(
            place_id=str(data.get('place_id', data.get('id', ''))),
            label=str(data.get('label', data.get('name', ''))),
            initial_marking=int(data.get('initial_marking', data.get('marking', 0))),
            compound_id=data.get('compound_id'),
            compound_name=data.get('compound_name'),
            chebi_id=data.get('chebi_id')
        )


@dataclass
class TransitionDTO:
    """Normalized transition data for KB ingestion."""
    transition_id: str
    label: str = ""
    
    # Transition behavior type
    transition_type: str = "immediate"     # "immediate", "timed", "stochastic", "continuous"
    
    # Optional metadata from SBML/KEGG import
    reaction_id: Optional[str] = None      # e.g., "R00200"
    reaction_name: Optional[str] = None    # e.g., "Hexokinase"
    ec_number: Optional[str] = None        # e.g., "2.7.1.1"
    
    # Optional kinetics
    rate: Optional[float] = None           # For stochastic/timed transitions
    kinetic_law: Optional[str] = None      # e.g., "michaelis_menten(P1, vmax=10, km=5)"
    
    @classmethod
    def from_object(cls, transition_obj) -> 'TransitionDTO':
        """Create DTO from model Transition object.
        
        Args:
            transition_obj: Transition object with .id, .label attributes
            
        Returns:
            TransitionDTO with normalized data
        """
        # Extract transition type
        transition_type = "immediate"  # default
        if hasattr(transition_obj, 'transition_type'):
            transition_type = str(transition_obj.transition_type)
        elif hasattr(transition_obj, 'type'):
            transition_type = str(transition_obj.type)
        
        # Extract reaction metadata if available
        reaction_id = None
        reaction_name = None
        ec_number = None
        rate = None
        kinetic_law = None
        
        if hasattr(transition_obj, 'metadata') and transition_obj.metadata:
            reaction_id = transition_obj.metadata.get('reaction_id')
            reaction_name = transition_obj.metadata.get('reaction_name')
            ec_number = transition_obj.metadata.get('ec_number')
            kinetic_law = transition_obj.metadata.get('kinetic_law')
        
        if hasattr(transition_obj, 'rate'):
            rate = float(transition_obj.rate) if transition_obj.rate is not None else None
        
        return cls(
            transition_id=str(transition_obj.id) if hasattr(transition_obj, 'id') else str(transition_obj),
            label=str(transition_obj.label) if hasattr(transition_obj, 'label') else '',
            transition_type=transition_type,
            reaction_id=reaction_id,
            reaction_name=reaction_name,
            ec_number=ec_number,
            rate=rate,
            kinetic_law=kinetic_law
        )
    
    @classmethod
    def from_dict(cls, data: dict) -> 'TransitionDTO':
        """Create DTO from dictionary.
        
        Args:
            data: Dict with 'transition_id', 'label' keys
            
        Returns:
            TransitionDTO with normalized data
        """
        return cls(
            transition_id=str(data.get('transition_id', data.get('id', ''))),
            label=str(data.get('label', data.get('name', ''))),
            transition_type=str(data.get('transition_type', data.get('type', 'immediate'))),
            reaction_id=data.get('reaction_id'),
            reaction_name=data.get('reaction_name'),
            ec_number=data.get('ec_number'),
            rate=float(data['rate']) if 'rate' in data and data['rate'] is not None else None,
            kinetic_law=data.get('kinetic_law')
        )


@dataclass
class ArcDTO:
    """Normalized arc data for KB ingestion."""
    arc_id: str
    source_id: str      # Place or Transition ID
    target_id: str      # Place or Transition ID
    arc_type: str       # "place_to_transition" or "transition_to_place"
    weight: int = 1
    
    @classmethod
    def from_object(cls, arc_obj) -> 'ArcDTO':
        """Create DTO from model Arc object.
        
        Args:
            arc_obj: Arc object with .id, .source, .target, .weight attributes
            
        Returns:
            ArcDTO with normalized data
        """
        # Determine arc type
        arc_type = "unknown"
        if hasattr(arc_obj, 'arc_type'):
            arc_type = str(arc_obj.arc_type)
        elif hasattr(arc_obj, 'source') and hasattr(arc_obj, 'target'):
            # Infer from source/target types
            from shypn.model.objects import Place, Transition
            if isinstance(arc_obj.source, Place) and isinstance(arc_obj.target, Transition):
                arc_type = "place_to_transition"
            elif isinstance(arc_obj.source, Transition) and isinstance(arc_obj.target, Place):
                arc_type = "transition_to_place"
            else:
                # Debug: unexpected types
                source_type = type(arc_obj.source).__name__ if hasattr(arc_obj, 'source') else 'None'
                target_type = type(arc_obj.target).__name__ if hasattr(arc_obj, 'target') else 'None'
                print(f"[DTO] Warning: Arc {getattr(arc_obj, 'id', '?')} has unexpected types: {source_type} → {target_type}")
        
        return cls(
            arc_id=str(arc_obj.id) if hasattr(arc_obj, 'id') else str(arc_obj),
            source_id=str(arc_obj.source.id) if hasattr(arc_obj, 'source') and hasattr(arc_obj.source, 'id') else '',
            target_id=str(arc_obj.target.id) if hasattr(arc_obj, 'target') and hasattr(arc_obj.target, 'id') else '',
            arc_type=arc_type,
            weight=int(arc_obj.weight) if hasattr(arc_obj, 'weight') else 1
        )
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ArcDTO':
        """Create DTO from dictionary.
        
        Args:
            data: Dict with 'arc_id', 'source_id', 'target_id' keys
            
        Returns:
            ArcDTO with normalized data
        """
        # Determine arc type from source_type and target_type if available
        arc_type = "unknown"
        if 'source_type' in data and 'target_type' in data:
            source_type = data['source_type']
            target_type = data['target_type']
            if source_type == 'place' and target_type == 'transition':
                arc_type = "place_to_transition"
            elif source_type == 'transition' and target_type == 'place':
                arc_type = "transition_to_place"
        elif data.get('arc_type') in ['place_to_transition', 'transition_to_place']:
            arc_type = data['arc_type']
        
        return cls(
            arc_id=str(data.get('arc_id', data.get('id', ''))),
            source_id=str(data.get('source_id', '')),
            target_id=str(data.get('target_id', '')),
            arc_type=arc_type,
            weight=int(data.get('weight', 1))
        )


# ============================================================================
# SIMULATION DTOs - From Simulation Engine
# ============================================================================

@dataclass
class SimulationResultDTO:
    """Normalized simulation results for KB ingestion."""
    time_points: List[float] = field(default_factory=list)
    
    # Place data: place_id -> list of token counts over time
    place_traces: Dict[str, List[int]] = field(default_factory=dict)
    
    # Transition data: transition_id -> total firing count
    total_firings: Dict[str, int] = field(default_factory=dict)
    
    # Initial/final states
    initial_marking: Dict[str, int] = field(default_factory=dict)
    final_marking: Dict[str, int] = field(default_factory=dict)
    
    @classmethod
    def from_data_collector(cls, data_collector) -> 'SimulationResultDTO':
        """Create DTO from DataCollector object.
        
        Args:
            data_collector: DataCollector instance with simulation data
            
        Returns:
            SimulationResultDTO with normalized data
        """
        time_points = []
        place_traces = {}
        total_firings = {}
        initial_marking = {}
        final_marking = {}
        
        # Extract time points
        if hasattr(data_collector, 'time_points'):
            time_points = list(data_collector.time_points)
        
        # Extract place data
        if hasattr(data_collector, 'place_data'):
            for place_id, values in data_collector.place_data.items():
                if values:
                    place_traces[str(place_id)] = [int(v) for v in values]
                    initial_marking[str(place_id)] = int(values[0])
                    final_marking[str(place_id)] = int(values[-1])
        
        # Extract transition firing counts
        if hasattr(data_collector, 'transition_data'):
            for trans_id, values in data_collector.transition_data.items():
                if values:
                    # Assuming cumulative counts
                    total_firings[str(trans_id)] = int(values[-1])
        
        return cls(
            time_points=time_points,
            place_traces=place_traces,
            total_firings=total_firings,
            initial_marking=initial_marking,
            final_marking=final_marking
        )


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def normalize_places(places_data) -> List[PlaceDTO]:
    """Convert any format of places data to PlaceDTO list.
    
    Args:
        places_data: List of Place objects or dicts
        
    Returns:
        List[PlaceDTO]: Normalized place data
    """
    result = []
    for place in places_data:
        if isinstance(place, dict):
            result.append(PlaceDTO.from_dict(place))
        else:
            result.append(PlaceDTO.from_object(place))
    return result


def normalize_transitions(transitions_data) -> List[TransitionDTO]:
    """Convert any format of transitions data to TransitionDTO list.
    
    Args:
        transitions_data: List of Transition objects or dicts
        
    Returns:
        List[TransitionDTO]: Normalized transition data
    """
    result = []
    for transition in transitions_data:
        if isinstance(transition, dict):
            result.append(TransitionDTO.from_dict(transition))
        else:
            result.append(TransitionDTO.from_object(transition))
    return result


def normalize_arcs(arcs_data) -> List[ArcDTO]:
    """Convert any format of arcs data to ArcDTO list.
    
    Args:
        arcs_data: List of Arc objects or dicts
        
    Returns:
        List[ArcDTO]: Normalized arc data
    """
    result = []
    for arc in arcs_data:
        if isinstance(arc, dict):
            result.append(ArcDTO.from_dict(arc))
        else:
            result.append(ArcDTO.from_object(arc))
    return result


__all__ = [
    'PlaceDTO',
    'TransitionDTO',
    'ArcDTO',
    'SimulationResultDTO',
    'normalize_places',
    'normalize_transitions',
    'normalize_arcs',
]
