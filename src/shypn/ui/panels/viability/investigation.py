"""Investigation data classes and manager.

Defines the core investigation structures for locality and subnet analysis.
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Set, Optional, Dict, Any


class InvestigationMode(Enum):
    """Investigation mode."""
    SINGLE_LOCALITY = "single"
    SUBNET = "subnet"


@dataclass
class Locality:
    """Single transition locality (immediate neighborhood)."""
    transition_id: str
    input_places: List[str] = field(default_factory=list)
    output_places: List[str] = field(default_factory=list)
    input_arcs: List[str] = field(default_factory=list)
    output_arcs: List[str] = field(default_factory=list)
    
    def __repr__(self):
        return f"Locality({self.transition_id}: {len(self.input_places)}→{len(self.output_places)})"


@dataclass
class Suggestion:
    """Single actionable suggestion to improve viability."""
    category: str  # 'structural', 'kinetic', 'biological', 'flow', 'boundary', 'conservation'
    action: str  # What to do
    impact: str  # Why it helps
    target_element_id: str  # Which element to modify
    details: Dict[str, Any] = field(default_factory=dict)  # Extra information
    priority: int = 1  # Higher = more important
    
    def __repr__(self):
        return f"{self.category.upper()}: {self.action}"


@dataclass
class Investigation:
    """Investigation results (NEW simplified structure for refactored system)."""
    root_transition_id: str
    subnet: 'Subnet'  # The analyzed subnet
    suggestions: List[Suggestion] = field(default_factory=list)
    fix_sequence: Optional[Any] = None  # FixSequence from sequencer
    timestamp: datetime = field(default_factory=datetime.now)
    
    def __repr__(self):
        return f"Investigation({self.root_transition_id}, {len(self.suggestions)} suggestions)"


@dataclass
class Dependency:
    """Flow dependency between localities in a subnet."""
    source_transition_id: str
    target_transition_id: str
    connecting_place_id: str
    flow_rate: Optional[float] = None
    
    def __repr__(self):
        return f"{self.source_transition_id} → {self.connecting_place_id} → {self.target_transition_id}"


@dataclass
class Subnet:
    """Subnet extracted from multiple localities."""
    transitions: Set[str] = field(default_factory=set)  # Transition IDs
    places: Set[str] = field(default_factory=set)  # Place IDs
    arcs: Set[str] = field(default_factory=set)  # Arc IDs
    boundary_places: Set[str] = field(default_factory=set)  # Places on boundary
    internal_places: Set[str] = field(default_factory=set)  # Places fully internal
    boundary_inputs: List[str] = field(default_factory=list)  # Input places
    boundary_outputs: List[str] = field(default_factory=list)  # Output places
    dependencies: List[Dependency] = field(default_factory=list)
    
    def __len__(self):
        """Return number of transitions in subnet."""
        return len(self.transitions)
    
    def __repr__(self):
        return f"Subnet(T={len(self.transitions)}, P={len(self.places)})"


@dataclass
class Issue:
    """Single issue found during analysis."""
    category: str  # 'structural', 'biological', 'kinetic', 'boundary', 'conservation'
    severity: str  # 'error', 'warning', 'info'
    message: str
    element_id: Optional[str] = None  # Place, transition, or arc ID
    details: Dict[str, Any] = field(default_factory=dict)
    
    def __repr__(self):
        emoji = {'error': '🔴', 'warning': '🟡', 'info': '🟢'}.get(self.severity, '⚪')
        return f"{emoji} [{self.category}] {self.message}"


@dataclass
class Suggestion:
    """Suggested fix for an issue."""
    category: str
    action: str  # 'add_arc', 'modify_weight', 'set_rate', etc.
    message: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    impact: Optional[str] = None  # Impact description
    dependencies: List[str] = field(default_factory=list)  # Suggestion IDs this depends on
    
    def __repr__(self):
        return f"[{self.action}] {self.message}"


@dataclass
class LocalityInvestigation:
    """Investigation of a single locality."""
    transition_id: str
    locality: Any  # Locality object (avoid circular import)
    timestamp: datetime
    mode: InvestigationMode = InvestigationMode.SINGLE_LOCALITY
    issues: List[Issue] = field(default_factory=list)
    suggestions: List[Suggestion] = field(default_factory=list)
    kb_snapshot: Optional[Any] = None  # KB state when investigated
    sim_snapshot: Optional[Dict] = None  # Sim data when investigated
    
    def __repr__(self):
        return f"Investigation({self.transition_id}, {len(self.issues)} issues)"


@dataclass
class BoundaryAnalysis:
    """Results of boundary analysis."""
    accumulating_places: List[str] = field(default_factory=list)
    depleting_places: List[str] = field(default_factory=list)
    balanced_places: List[str] = field(default_factory=list)
    
    def has_issues(self) -> bool:
        """Check if boundary has issues."""
        return len(self.accumulating_places) > 0 or len(self.depleting_places) > 0


@dataclass
class ConservationAnalysis:
    """Results of conservation analysis."""
    conserved_invariants: List[str] = field(default_factory=list)
    violated_invariants: List[str] = field(default_factory=list)
    mass_balance_ok: bool = True
    detected_leaks: List[str] = field(default_factory=list)
    
    def has_issues(self) -> bool:
        """Check if conservation has issues."""
        return len(self.violated_invariants) > 0 or not self.mass_balance_ok


@dataclass
class SubnetInvestigation:
    """Investigation of a subnet (multiple localities)."""
    localities: List[LocalityInvestigation]
    subnet: Subnet
    timestamp: datetime
    mode: InvestigationMode = InvestigationMode.SUBNET
    
    # Multi-level analysis results
    level1_issues: Dict[str, List[Issue]] = field(default_factory=dict)  # Per locality
    level2_dependencies: List[Dependency] = field(default_factory=list)
    level3_boundary: Optional[BoundaryAnalysis] = None
    level4_conservation: Optional[ConservationAnalysis] = None
    
    # Coordinated suggestions
    suggestions: List[Suggestion] = field(default_factory=list)
    
    def __repr__(self):
        total_issues = sum(len(issues) for issues in self.level1_issues.values())
        return f"SubnetInvestigation({self.subnet}, {total_issues} total issues)"
    
    @property
    def transition_ids(self) -> List[str]:
        """Get all transition IDs in subnet."""
        return [loc.transition_id for loc in self.localities]


class InvestigationManager:
    """Manage active investigations."""
    
    def __init__(self):
        """Initialize investigation manager."""
        self.investigations: Dict[str, Any] = {}  # {key: investigation}
        self._next_id = 1
    
    def create_investigation(
        self, 
        transition, 
        locality, 
        mode: InvestigationMode = InvestigationMode.SINGLE_LOCALITY
    ) -> LocalityInvestigation:
        """Create new single locality investigation.
        
        Args:
            transition: Transition object
            locality: Locality object
            mode: Investigation mode
            
        Returns:
            LocalityInvestigation object
        """
        investigation = LocalityInvestigation(
            transition_id=transition.id,
            locality=locality,
            timestamp=datetime.now(),
            mode=mode
        )
        
        key = f"locality_{transition.id}"
        self.investigations[key] = investigation
        
        return investigation
    
    def create_subnet_investigation(
        self, 
        transitions: List, 
        localities: List, 
        subnet: Subnet
    ) -> SubnetInvestigation:
        """Create new subnet investigation.
        
        NOTE: Caller should validate that localities are connected before calling.
        Use SubnetBuilder.build_subnet() which enforces connectivity.
        
        Args:
            transitions: List of transition objects
            localities: List of locality objects
            subnet: Subnet object (already validated as connected)
            
        Returns:
            SubnetInvestigation object
        """
        # Create locality investigations for each transition
        locality_investigations = []
        for trans, loc in zip(transitions, localities):
            loc_inv = LocalityInvestigation(
                transition_id=trans.id,
                locality=loc,
                timestamp=datetime.now(),
                mode=InvestigationMode.SUBNET
            )
            locality_investigations.append(loc_inv)
        
        # Create subnet investigation
        investigation = SubnetInvestigation(
            localities=locality_investigations,
            subnet=subnet,
            timestamp=datetime.now()
        )
        
        # Store with composite key
        key = f"subnet_{'_'.join(sorted(subnet.transitions))}"
        self.investigations[key] = investigation
        
        return investigation
    
    def get_investigation(self, key: str) -> Optional[Any]:
        """Get investigation by key.
        
        Args:
            key: Investigation key
            
        Returns:
            Investigation object or None
        """
        return self.investigations.get(key)
    
    def remove_investigation(self, key: str) -> bool:
        """Remove investigation.
        
        Args:
            key: Investigation key
            
        Returns:
            True if removed, False if not found
        """
        if key in self.investigations:
            del self.investigations[key]
            return True
        return False
    
    def clear_all(self):
        """Clear all investigations."""
        self.investigations.clear()
    
    def list_investigations(self) -> List[str]:
        """List all investigation keys.
        
        Returns:
            List of investigation keys
        """
        return list(self.investigations.keys())
