"""
Transition Type Models

Data models for Petri net transition types and their parameters.

Author: Shypn Development Team
Date: November 2025
"""

from enum import Enum
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field


class TransitionType(Enum):
    """Petri net transition types."""
    IMMEDIATE = "immediate"
    TIMED = "timed"
    STOCHASTIC = "stochastic"
    CONTINUOUS = "continuous"
    UNKNOWN = "unknown"


class BiologicalSemantics(Enum):
    """Biological semantics for transitions."""
    BURST = "burst"  # Immediate burst events
    DETERMINISTIC = "deterministic"  # Timed delays
    MASS_ACTION = "mass_action"  # Stochastic kinetics
    ENZYME_KINETICS = "enzyme_kinetics"  # Continuous enzymatic
    REGULATION = "regulation"  # Regulatory events
    TRANSPORT = "transport"  # Transport processes
    UNKNOWN = "unknown"


@dataclass
class TransitionParameters:
    """Base class for transition parameters."""
    transition_type: TransitionType
    biological_semantics: BiologicalSemantics
    ec_number: Optional[str] = None
    reaction_id: Optional[str] = None
    enzyme_name: Optional[str] = None
    organism: str = "Homo sapiens"
    confidence_score: float = 0.0
    source: str = "Heuristic"
    source_id: Optional[str] = None
    pubmed_id: Optional[str] = None
    notes: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'transition_type': self.transition_type.value,
            'biological_semantics': self.biological_semantics.value,
            'ec_number': self.ec_number,
            'reaction_id': self.reaction_id,
            'enzyme_name': self.enzyme_name,
            'organism': self.organism,
            'confidence_score': self.confidence_score,
            'source': self.source,
            'source_id': self.source_id,
            'pubmed_id': self.pubmed_id,
            'notes': self.notes
        }


@dataclass
class ImmediateParameters(TransitionParameters):
    """Parameters for immediate (instantaneous) transitions."""
    transition_type: TransitionType = TransitionType.IMMEDIATE
    biological_semantics: BiologicalSemantics = BiologicalSemantics.UNKNOWN
    priority: int = 0
    weight: float = 1.0
    
    def __post_init__(self):
        self.transition_type = TransitionType.IMMEDIATE
        if self.biological_semantics == BiologicalSemantics.UNKNOWN:
            self.biological_semantics = BiologicalSemantics.BURST
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data['parameters'] = {
            'priority': self.priority,
            'weight': self.weight
        }
        return data


@dataclass
class TimedParameters(TransitionParameters):
    """Parameters for timed (deterministic) transitions."""
    transition_type: TransitionType = TransitionType.TIMED
    biological_semantics: BiologicalSemantics = BiologicalSemantics.UNKNOWN
    delay: float = 5.0
    time_unit: str = "minutes"
    
    def __post_init__(self):
        self.transition_type = TransitionType.TIMED
        if self.biological_semantics == BiologicalSemantics.UNKNOWN:
            self.biological_semantics = BiologicalSemantics.DETERMINISTIC
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data['parameters'] = {
            'delay': self.delay,
            'time_unit': self.time_unit
        }
        return data


@dataclass
class StochasticParameters(TransitionParameters):
    """Parameters for stochastic (mass action) transitions."""
    transition_type: TransitionType = TransitionType.STOCHASTIC
    biological_semantics: BiologicalSemantics = BiologicalSemantics.UNKNOWN
    lambda_param: float = 0.05
    k_forward: Optional[float] = None
    k_reverse: Optional[float] = None
    rate_function: Optional[str] = None
    temperature: float = 37.0
    ph: float = 7.4
    
    def __post_init__(self):
        self.transition_type = TransitionType.STOCHASTIC
        if self.biological_semantics == BiologicalSemantics.UNKNOWN:
            self.biological_semantics = BiologicalSemantics.MASS_ACTION
        
        # Auto-generate rate function if not provided
        if not self.rate_function and self.k_forward:
            self.rate_function = f"mass_action({self.k_forward})"
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data['parameters'] = {
            'lambda': self.lambda_param,
            'k_forward': self.k_forward,
            'k_reverse': self.k_reverse,
            'rate_function': self.rate_function,
            'temperature': self.temperature,
            'ph': self.ph
        }
        return data


@dataclass
class ContinuousParameters(TransitionParameters):
    """Parameters for continuous (enzyme kinetics) transitions."""
    transition_type: TransitionType = TransitionType.CONTINUOUS
    biological_semantics: BiologicalSemantics = BiologicalSemantics.UNKNOWN
    vmax: Optional[float] = None
    km: Optional[float] = None
    kcat: Optional[float] = None
    ki: Optional[float] = None
    hill_coefficient: Optional[float] = None
    enzyme_concentration: Optional[float] = None
    rate_function: Optional[str] = None
    temperature: float = 37.0
    ph: float = 7.4
    
    def __post_init__(self):
        self.transition_type = TransitionType.CONTINUOUS
        if self.biological_semantics == BiologicalSemantics.UNKNOWN:
            self.biological_semantics = BiologicalSemantics.ENZYME_KINETICS
        
        # Auto-generate rate function if not provided
        if not self.rate_function and self.vmax and self.km:
            self.rate_function = f"michaelis_menten(S, {self.vmax}, {self.km})"
    
    @property
    def rate(self) -> Optional[float]:
        """Alias for vmax (for display purposes)."""
        return self.vmax
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data['parameters'] = {
            'vmax': self.vmax,
            'km': self.km,
            'kcat': self.kcat,
            'ki': self.ki,
            'hill_coefficient': self.hill_coefficient,
            'enzyme_concentration': self.enzyme_concentration,
            'rate_function': self.rate_function,
            'rate': self.vmax,  # Alias for display
            'temperature': self.temperature,
            'ph': self.ph
        }
        return data


@dataclass
class InferenceResult:
    """Result of parameter inference for a transition."""
    transition_id: str
    parameters: TransitionParameters
    alternatives: List[TransitionParameters] = field(default_factory=list)
    inference_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'transition_id': self.transition_id,
            'parameters': self.parameters.to_dict(),
            'alternatives': [alt.to_dict() for alt in self.alternatives],
            'inference_metadata': self.inference_metadata
        }
