"""Data structures for Model Knowledge Base.

Defines all domain-specific knowledge structures used by the
ModelKnowledgeBase to store multi-domain information.

Author: Simão Eugénio
Date: November 9, 2025
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime


# ============================================================================
# STRUCTURAL KNOWLEDGE
# ============================================================================

@dataclass
class PlaceKnowledge:
    """Complete knowledge about a single place."""
    place_id: str
    label: str = ""
    
    # Biological context
    compound_id: Optional[str] = None      # KEGG compound ID (e.g., "C00031")
    compound_name: Optional[str] = None    # e.g., "D-Glucose"
    
    # Current state
    current_marking: int = 0
    
    # Topology analysis results
    in_p_invariants: List[int] = field(default_factory=list)  # Which P-invariants include this
    in_siphons: List[int] = field(default_factory=list)       # Which siphons include this
    in_traps: List[int] = field(default_factory=list)         # Which traps include this
    is_bounded: bool = False
    bound_value: Optional[int] = None
    
    # Biochemical context
    basal_concentration: Optional[float] = None  # From BRENDA/literature (mM)
    concentration_range: Optional[Tuple[float, float]] = None  # (min, max) mM
    
    # Dynamic behavior
    token_history: List[int] = field(default_factory=list)  # From simulation
    avg_tokens: Optional[float] = None
    peak_tokens: Optional[int] = None
    
    # Constraints for repair
    must_have_tokens: bool = False  # Required for liveness
    suggested_initial_marking: Optional[int] = None


@dataclass
class TransitionKnowledge:
    """Complete knowledge about a single transition."""
    transition_id: str
    label: str = ""
    
    # Biological context
    reaction_id: Optional[str] = None      # KEGG reaction ID (e.g., "R00200")
    reaction_name: Optional[str] = None    # e.g., "Hexokinase"
    ec_number: Optional[str] = None        # e.g., "2.7.1.1"
    
    # Topology analysis results
    liveness_level: Optional[str] = None   # "L4-live", "L3-live", "L1-live", "dead"
    in_t_invariants: List[int] = field(default_factory=list)
    is_deadlock_causing: bool = False
    
    # Biochemical kinetics
    km_values: Dict[str, float] = field(default_factory=dict)  # substrate -> Km (mM)
    vmax: Optional[float] = None           # Maximum velocity
    kcat: Optional[float] = None           # Turnover number (1/sec)
    
    # Current state
    current_rate: Optional[float] = None   # tokens/sec
    is_enabled: bool = False
    
    # Dynamic behavior
    firing_count: int = 0                  # Times fired in simulation
    avg_firing_rate: Optional[float] = None
    
    # Constraints for repair
    must_be_live: bool = False
    suggested_firing_rate: Optional[float] = None


@dataclass
class ArcKnowledge:
    """Complete knowledge about a single arc."""
    arc_id: str
    source_id: str
    target_id: str
    arc_type: str  # "place_to_transition", "transition_to_place"
    
    # Current state
    current_weight: int = 1
    
    # Biological context
    stoichiometry: Optional[int] = None    # From KEGG/SBML reaction
    
    # Constraints for repair
    suggested_weight: Optional[int] = None
    biological_justification: Optional[str] = None


# ============================================================================
# BEHAVIORAL KNOWLEDGE
# ============================================================================

@dataclass
class PInvariant:
    """A P-invariant (conservation law)."""
    vector: List[int]           # Coefficient for each place
    place_ids: List[str]        # Place IDs in order
    conserved_value: int        # Weighted sum of tokens
    
    # Semantic interpretation
    name: Optional[str] = None          # e.g., "ATP/ADP cycle"
    biological_meaning: Optional[str] = None


@dataclass
class TInvariant:
    """A T-invariant (firing sequence that returns to initial state)."""
    vector: List[int]           # Firing count for each transition
    transition_ids: List[str]   # Transition IDs in order
    
    # Semantic interpretation
    name: Optional[str] = None          # e.g., "Glycolysis cycle"
    biological_meaning: Optional[str] = None


@dataclass
class Siphon:
    """A minimal siphon (can become empty and stay empty)."""
    place_ids: List[str]
    is_minimal: bool = True
    is_properly_marked: bool = False  # Has tokens in current marking
    
    # Repair suggestion
    suggested_source: Optional[str] = None  # Place to add controlled source
    suggested_rate: Optional[float] = None


# ============================================================================
# BIOLOGICAL KNOWLEDGE
# ============================================================================

@dataclass
class PathwayInfo:
    """Biological pathway metadata from KEGG/SBML."""
    pathway_id: str            # e.g., "hsa00010"
    pathway_name: str          # e.g., "Glycolysis / Gluconeogenesis"
    organism: Optional[str] = None    # e.g., "Homo sapiens"
    source: str = "unknown"    # "kegg", "sbml", "user"
    
    # Context
    description: Optional[str] = None
    biological_function: Optional[str] = None


@dataclass
class CompoundInfo:
    """Information about a metabolic compound."""
    compound_id: str           # KEGG ID (e.g., "C00031")
    name: str
    formula: Optional[str] = None
    
    # Biochemical properties
    molecular_weight: Optional[float] = None
    basal_concentration: Optional[float] = None  # mM
    concentration_range: Optional[Tuple[float, float]] = None
    
    # Context
    role: Optional[str] = None  # "substrate", "product", "cofactor"


@dataclass
class ReactionInfo:
    """Information about a biochemical reaction."""
    reaction_id: str           # KEGG ID (e.g., "R00200")
    name: str
    ec_number: Optional[str] = None
    
    # Stoichiometry
    substrates: List[Tuple[str, int]] = field(default_factory=list)  # (compound_id, coefficient)
    products: List[Tuple[str, int]] = field(default_factory=list)
    
    # Context
    reversible: bool = False
    pathway_context: Optional[str] = None


# ============================================================================
# BIOCHEMICAL KNOWLEDGE
# ============================================================================

@dataclass
class KineticParams:
    """Kinetic parameters for a transition/reaction."""
    transition_id: str
    ec_number: Optional[str] = None
    
    # Michaelis-Menten parameters
    km_values: Dict[str, float] = field(default_factory=dict)  # substrate -> Km (mM)
    vmax: Optional[float] = None           # Maximum velocity (mM/sec)
    kcat: Optional[float] = None           # Turnover number (1/sec)
    
    # Additional parameters
    ki_values: Dict[str, float] = field(default_factory=dict)  # inhibitor -> Ki
    optimal_ph: Optional[float] = None
    optimal_temp: Optional[float] = None  # Celsius
    
    # Data source
    source: str = "brenda"
    organism: Optional[str] = None
    confidence: float = 0.5  # 0.0 to 1.0


# ============================================================================
# DYNAMIC KNOWLEDGE
# ============================================================================

@dataclass
class SimulationTrace:
    """Results from a simulation run."""
    timestamp: datetime = field(default_factory=datetime.now)
    initial_marking: Dict[str, int] = field(default_factory=dict)  # place_id -> tokens
    
    # Time series data
    time_points: List[float] = field(default_factory=list)         # seconds
    place_traces: Dict[str, List[int]] = field(default_factory=dict)  # place_id -> token counts over time
    transition_firings: Dict[str, List[int]] = field(default_factory=dict)  # transition_id -> firing times
    
    # Summary statistics
    final_marking: Dict[str, int] = field(default_factory=dict)
    total_firings: Dict[str, int] = field(default_factory=dict)    # transition_id -> count
    reached_steady_state: bool = False


# ============================================================================
# ISSUE DATABASE
# ============================================================================

@dataclass
class Issue:
    """A problem detected by analysis."""
    issue_id: str              # Unique ID
    severity: str              # "critical", "warning", "info"
    category: str              # "liveness", "deadlock", "boundedness", "siphon"
    
    # Description
    title: str = ""
    description: str = ""
    
    # Context
    affected_elements: List[str] = field(default_factory=list)  # IDs of places/transitions involved
    detected_by: str = "unknown"           # "topology", "simulation", "brenda", etc.
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Root cause analysis
    root_causes: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)  # Constraints for repair
    
    # Repair suggestions (to be filled by inference engine)
    suggestions: List['RepairSuggestion'] = field(default_factory=list)


@dataclass
class RepairSuggestion:
    """A suggested fix for an issue."""
    suggestion_id: str
    issue_id: str              # Which issue this fixes
    
    # Type of repair
    repair_type: str           # "add_marking", "add_arc", "modify_weight", "add_source", "modify_rate"
    
    # Specification
    target_element: str        # ID of element to modify
    parameter: str             # What to change (e.g., "initial_marking", "weight", "rate")
    suggested_value: Any       # New value
    
    # Justification (multi-domain reasoning)
    reasoning: List[str] = field(default_factory=list)  # Step-by-step explanation
    knowledge_sources: List[str] = field(default_factory=list)  # Which analyses contributed
    confidence: float = 0.5    # 0.0 to 1.0
    
    # Impact assessment
    fixes_issues: List[str] = field(default_factory=list)     # Issue IDs
    may_cause_issues: List[str] = field(default_factory=list) # Potential side effects


__all__ = [
    # Structural
    'PlaceKnowledge',
    'TransitionKnowledge',
    'ArcKnowledge',
    # Behavioral
    'PInvariant',
    'TInvariant',
    'Siphon',
    # Biological
    'PathwayInfo',
    'CompoundInfo',
    'ReactionInfo',
    # Biochemical
    'KineticParams',
    # Dynamic
    'SimulationTrace',
    # Issues
    'Issue',
    'RepairSuggestion'
]
