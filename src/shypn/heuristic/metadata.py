"""
Kinetics Metadata

Tracks the source and confidence of kinetic assignments for transitions.
This metadata is stored in transition.metadata dict (legacy) or 
transition.kinetic_metadata (new structured metadata).

COMPATIBILITY LAYER:
This module bridges the old metadata system (dict-based) with the new
structured KineticMetadata classes. It checks both systems and prefers
the new structured metadata when available.
"""

from typing import Optional, Dict, Any
from .assignment_result import ConfidenceLevel, AssignmentSource

# Import new kinetic metadata classes
try:
    from shypn.data.kinetics import (
        KineticMetadata as NewKineticMetadata,
        KineticSource,
        ConfidenceLevel as NewConfidenceLevel
    )
    NEW_METADATA_AVAILABLE = True
except ImportError:
    NEW_METADATA_AVAILABLE = False
    NewKineticMetadata = None
    KineticSource = None
    NewConfidenceLevel = None


class KineticsMetadata:
    """
    Metadata about kinetic assignment for a transition.
    
    Stored in transition.metadata['kinetics'] as a dict.
    Tracks where kinetic data came from and how reliable it is.
    """
    
    # Metadata keys
    SOURCE_KEY = 'kinetics_source'
    CONFIDENCE_KEY = 'kinetics_confidence'
    RULE_KEY = 'kinetics_rule'
    PARAMETERS_KEY = 'kinetics_parameters'
    ORIGINAL_KEY = 'kinetics_original'
    
    @classmethod
    def set_from_result(cls, transition, result) -> None:
        """
        Set metadata on transition from assignment result.
        
        Args:
            transition: Transition object to update
            result: AssignmentResult with assignment details
        """
        if not hasattr(transition, 'metadata'):
            transition.metadata = {}
        
        transition.metadata[cls.SOURCE_KEY] = result.source.value
        transition.metadata[cls.CONFIDENCE_KEY] = result.confidence.value
        
        if result.rule:
            transition.metadata[cls.RULE_KEY] = result.rule
        
        if result.parameters:
            transition.metadata[cls.PARAMETERS_KEY] = result.parameters.copy()
    
    @classmethod
    def get_source(cls, transition) -> AssignmentSource:
        """Get assignment source from transition metadata."""
        if not hasattr(transition, 'metadata'):
            return AssignmentSource.DEFAULT
        
        source_str = transition.metadata.get(cls.SOURCE_KEY)
        if not source_str:
            return AssignmentSource.DEFAULT
        
        try:
            return AssignmentSource(source_str)
        except ValueError:
            return AssignmentSource.DEFAULT
    
    @classmethod
    def get_confidence(cls, transition) -> ConfidenceLevel:
        """Get confidence level from transition metadata."""
        if not hasattr(transition, 'metadata'):
            return ConfidenceLevel.UNKNOWN
        
        conf_str = transition.metadata.get(cls.CONFIDENCE_KEY)
        if not conf_str:
            return ConfidenceLevel.UNKNOWN
        
        try:
            return ConfidenceLevel(conf_str)
        except ValueError:
            return ConfidenceLevel.UNKNOWN
    
    @classmethod
    def get_rule(cls, transition) -> Optional[str]:
        """Get heuristic rule from transition metadata."""
        if not hasattr(transition, 'metadata'):
            return None
        return transition.metadata.get(cls.RULE_KEY)
    
    @classmethod
    def should_enhance(cls, transition) -> bool:
        """
        Check if transition should be enhanced with kinetics.
        
        PRIORITY: Checks new structured metadata first, falls back to legacy.
        
        Never enhance if:
        - New metadata: SBML or Manual source (definitive/high confidence)
        - New metadata: Locked flag set
        - Legacy: Source is 'explicit' (from curated model)
        - Legacy: Source is 'user' (user configured)
        - Legacy: Confidence is 'high' and source is 'database'
        
        Returns:
            True if safe to enhance, False otherwise
        """
        # PRIORITY 1: Check new structured metadata (if available)
        if NEW_METADATA_AVAILABLE:
            if hasattr(transition, 'kinetic_metadata') and transition.kinetic_metadata:
                # Use new metadata preservation logic
                return not NewKineticMetadata.should_preserve(transition.kinetic_metadata)
        
        # FALLBACK: Check legacy metadata
        source = cls.get_source(transition)
        confidence = cls.get_confidence(transition)
        
        # Never override these sources
        if source in (AssignmentSource.EXPLICIT, AssignmentSource.USER):
            return False
        
        # Don't override high-confidence database values
        if source == AssignmentSource.DATABASE and confidence == ConfidenceLevel.HIGH:
            return False
        
        # Safe to enhance
        return True
    
    @classmethod
    def save_original(cls, transition) -> None:
        """
        Save original kinetic state before enhancement.
        Allows rollback if needed.
        """
        if not hasattr(transition, 'metadata'):
            transition.metadata = {}
        
        transition.metadata[cls.ORIGINAL_KEY] = {
            'transition_type': transition.transition_type,
            'rate': transition.rate,
            'properties': transition.properties.copy() if hasattr(transition, 'properties') else {}
        }
    
    @classmethod
    def restore_original(cls, transition) -> bool:
        """
        Restore original kinetic state.
        
        Returns:
            True if restored, False if no original state saved
        """
        if not hasattr(transition, 'metadata'):
            return False
        
        original = transition.metadata.get(cls.ORIGINAL_KEY)
        if not original:
            return False
        
        transition.transition_type = original['transition_type']
        transition.rate = original['rate']
        if hasattr(transition, 'properties'):
            transition.properties = original['properties'].copy()
        
        return True
    
    @classmethod
    def clear(cls, transition) -> None:
        """Clear all kinetics metadata."""
        if not hasattr(transition, 'metadata'):
            return
        
        keys_to_remove = [
            cls.SOURCE_KEY,
            cls.CONFIDENCE_KEY,
            cls.RULE_KEY,
            cls.PARAMETERS_KEY,
            cls.ORIGINAL_KEY
        ]
        
        for key in keys_to_remove:
            transition.metadata.pop(key, None)
    
    @classmethod
    def to_dict(cls, transition) -> Dict[str, Any]:
        """Get all kinetics metadata as dict."""
        if not hasattr(transition, 'metadata'):
            return {}
        
        return {
            'source': transition.metadata.get(cls.SOURCE_KEY),
            'confidence': transition.metadata.get(cls.CONFIDENCE_KEY),
            'rule': transition.metadata.get(cls.RULE_KEY),
            'parameters': transition.metadata.get(cls.PARAMETERS_KEY),
        }
    
    @classmethod
    def format_for_display(cls, transition) -> str:
        """
        Format metadata for user display.
        
        Returns formatted string like:
        "Heuristic (Medium confidence) - enzymatic_mm"
        """
        source = cls.get_source(transition)
        confidence = cls.get_confidence(transition)
        rule = cls.get_rule(transition)
        
        parts = [source.value.capitalize()]
        
        if confidence != ConfidenceLevel.UNKNOWN:
            parts.append(f"({confidence.value.capitalize()} confidence)")
        
        if rule:
            parts.append(f"- {rule}")
        
        return " ".join(parts)
