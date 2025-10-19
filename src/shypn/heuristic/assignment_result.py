"""
Kinetics Assignment Result

Contains the result of a kinetics assignment operation,
including success status, confidence level, and metadata.
"""

from typing import Optional, Dict, Any
from enum import Enum


class ConfidenceLevel(Enum):
    """Confidence levels for kinetic assignments."""
    HIGH = "high"           # From explicit data or validated database
    MEDIUM = "medium"       # From heuristic analysis with good indicators
    LOW = "low"            # Default fallback values
    UNKNOWN = "unknown"    # Not yet analyzed


class AssignmentSource(Enum):
    """Source of kinetic assignment."""
    EXPLICIT = "explicit"          # From SBML <kineticLaw> or similar
    DATABASE = "database"          # From EC number lookup (BRENDA, etc.)
    HEURISTIC = "heuristic"        # From reaction structure analysis
    USER = "user"                  # User configured manually
    DEFAULT = "default"            # System default (unassigned)


class AssignmentResult:
    """
    Result of a kinetics assignment operation.
    
    Attributes:
        success: Whether assignment succeeded
        confidence: Confidence level of the assignment
        source: Source of the assignment
        rule: Heuristic rule used (if applicable)
        parameters: Assigned kinetic parameters
        rate_function: Generated rate function string
        message: Human-readable description
    """
    
    def __init__(
        self,
        success: bool,
        confidence: ConfidenceLevel = ConfidenceLevel.UNKNOWN,
        source: AssignmentSource = AssignmentSource.DEFAULT,
        rule: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
        rate_function: Optional[str] = None,
        message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize assignment result.
        
        Args:
            success: Whether assignment succeeded
            confidence: Confidence level
            source: Source of assignment
            rule: Heuristic rule name (if heuristic)
            parameters: Kinetic parameters dict
            rate_function: Rate function string
            message: Description of the assignment
            metadata: Additional metadata (e.g., enzyme name, reference)
        """
        self.success = success
        self.confidence = confidence
        self.source = source
        self.rule = rule
        self.parameters = parameters or {}
        self.rate_function = rate_function
        self.message = message or self._generate_message()
        self.metadata = metadata or {}  # Store additional information
    
    def _generate_message(self) -> str:
        """Generate default message based on result."""
        if not self.success:
            return "Assignment failed"
        
        if self.source == AssignmentSource.EXPLICIT:
            return "Used explicit kinetic data"
        elif self.source == AssignmentSource.DATABASE:
            return f"Looked up from database (confidence: {self.confidence.value})"
        elif self.source == AssignmentSource.HEURISTIC:
            rule_desc = f" using rule '{self.rule}'" if self.rule else ""
            return f"Estimated by heuristic{rule_desc} (confidence: {self.confidence.value})"
        elif self.source == AssignmentSource.USER:
            return "User configured"
        else:
            return f"Assigned with {self.confidence.value} confidence"
    
    def __repr__(self) -> str:
        return (
            f"AssignmentResult(success={self.success}, "
            f"confidence={self.confidence.value}, "
            f"source={self.source.value}, "
            f"rule={self.rule})"
        )
    
    def __str__(self) -> str:
        return self.message
    
    @classmethod
    def failed(cls, message: str = "Assignment failed") -> 'AssignmentResult':
        """Create a failed result."""
        return cls(
            success=False,
            confidence=ConfidenceLevel.UNKNOWN,
            source=AssignmentSource.DEFAULT,
            message=message
        )
    
    @classmethod
    def explicit(cls, parameters: Dict[str, Any], rate_function: str) -> 'AssignmentResult':
        """Create result for explicit kinetic data."""
        return cls(
            success=True,
            confidence=ConfidenceLevel.HIGH,
            source=AssignmentSource.EXPLICIT,
            parameters=parameters,
            rate_function=rate_function,
            message="Used explicit kinetic data from model"
        )
    
    @classmethod
    def from_database(
        cls,
        parameters: Dict[str, Any],
        rate_function: str,
        ec_number: Optional[str] = None
    ) -> 'AssignmentResult':
        """Create result for database lookup."""
        msg = "Looked up kinetic parameters from database"
        if ec_number:
            msg += f" (EC {ec_number})"
        
        return cls(
            success=True,
            confidence=ConfidenceLevel.HIGH,
            source=AssignmentSource.DATABASE,
            parameters=parameters,
            rate_function=rate_function,
            message=msg
        )
    
    @classmethod
    def from_heuristic(
        cls,
        rule: str,
        confidence: ConfidenceLevel,
        parameters: Dict[str, Any],
        rate_function: str
    ) -> 'AssignmentResult':
        """Create result for heuristic assignment."""
        return cls(
            success=True,
            confidence=confidence,
            source=AssignmentSource.HEURISTIC,
            rule=rule,
            parameters=parameters,
            rate_function=rate_function
        )
