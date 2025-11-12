"""Base analyzer interface for all analysis levels."""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from ..investigation import Issue, Suggestion


class BaseAnalyzer(ABC):
    """Abstract base class for all analyzers.
    
    Defines the common interface for locality, dependency, boundary,
    and conservation analyzers.
    """
    
    def __init__(self):
        """Initialize base analyzer."""
        self.issues: List[Issue] = []
        self.suggestions: List[Suggestion] = []
    
    @abstractmethod
    def analyze(self, context: Dict[str, Any]) -> List[Issue]:
        """Perform analysis and return issues found.
        
        Args:
            context: Analysis context with required data (KB, sim data, etc.)
            
        Returns:
            List of Issue objects
        """
        pass
    
    @abstractmethod
    def generate_suggestions(self, issues: List[Issue], context: Dict[str, Any]) -> List[Suggestion]:
        """Generate suggestions to fix issues.
        
        Args:
            issues: List of issues to address
            context: Analysis context
            
        Returns:
            List of Suggestion objects
        """
        pass
    
    def clear(self):
        """Clear stored issues and suggestions."""
        self.issues.clear()
        self.suggestions.clear()
    
    def _get_human_readable_name(self, kb: Any, element_id: str, element_type: str = "unknown") -> str:
        """Convert element ID to human-readable name with biological context.
        
        Args:
            kb: Knowledge base
            element_id: Place or transition ID
            element_type: "place" or "transition"
            
        Returns:
            Human-readable name like "P5 (Glucose / C00031)"
        """
        if not kb:
            return element_id
        
        if element_type == "place" or element_id.startswith('P'):
            place = kb.places.get(element_id)
            if place:
                parts = [element_id]
                
                # Add compound name if available
                if hasattr(place, 'compound_id') and place.compound_id:
                    compound = kb.compounds.get(place.compound_id)
                    if compound and hasattr(compound, 'name') and compound.name:
                        parts.append(compound.name)
                    else:
                        parts.append(place.compound_id)
                
                # Add label if available and different
                if hasattr(place, 'label') and place.label and place.label != place.compound_id:
                    if not any(place.label in p for p in parts):
                        parts.append(place.label)
                
                return " / ".join(parts) if len(parts) > 1 else element_id
        
        elif element_type == "transition" or element_id.startswith('T'):
            trans = kb.transitions.get(element_id)
            if trans:
                parts = [element_id]
                
                # Add reaction name if available
                if hasattr(trans, 'reaction_name') and trans.reaction_name:
                    parts.append(trans.reaction_name)
                elif hasattr(trans, 'reaction_id') and trans.reaction_id:
                    parts.append(trans.reaction_id)
                
                # Add label if available and different
                if hasattr(trans, 'label') and trans.label:
                    if not any(trans.label in p for p in parts):
                        parts.append(trans.label)
                
                return " / ".join(parts) if len(parts) > 1 else element_id
        
        return element_id
