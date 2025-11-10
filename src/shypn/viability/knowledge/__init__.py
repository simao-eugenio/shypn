"""Knowledge Base Module for Model Intelligence.

This module provides the unified knowledge repository that aggregates
information from all Shypn panels and modules to enable intelligent
model repair and inference.

Author: Simão Eugénio
Date: November 9, 2025
"""

from .knowledge_base import ModelKnowledgeBase
from .data_structures import (
    PlaceKnowledge,
    TransitionKnowledge,
    ArcKnowledge,
    PInvariant,
    TInvariant,
    Siphon,
    PathwayInfo,
    CompoundInfo,
    ReactionInfo,
    KineticParams,
    SimulationTrace,
    Issue,
    RepairSuggestion
)

__all__ = [
    'ModelKnowledgeBase',
    'PlaceKnowledge',
    'TransitionKnowledge',
    'ArcKnowledge',
    'PInvariant',
    'TInvariant',
    'Siphon',
    'PathwayInfo',
    'CompoundInfo',
    'ReactionInfo',
    'KineticParams',
    'SimulationTrace',
    'Issue',
    'RepairSuggestion'
]
