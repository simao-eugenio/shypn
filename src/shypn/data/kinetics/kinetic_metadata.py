"""
Kinetic Metadata Classes

Data structures for tracking kinetic data sources and confidence levels.

Architecture:
- KineticMetadata: Base class for all kinetic metadata
- SBMLKineticMetadata: SBML-specific metadata (definitive confidence)
- DatabaseKineticMetadata: Database lookup metadata (medium-high confidence)
- HeuristicKineticMetadata: Heuristic analysis metadata (medium confidence)
- ManualKineticMetadata: User-entered metadata (high confidence)

Design Principles:
- OOP inheritance (base class + specialized subclasses)
- Separate modules (this file is standalone)
- Immutable source tracking (timestamp, source file)
- Confidence scoring (0.0-1.0)
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum


class ConfidenceLevel(Enum):
    """Confidence levels for kinetic data."""
    DEFINITIVE = "definitive"  # 1.0 - SBML explicit kinetics
    HIGH = "high"              # 0.95 - Manual user entry
    MEDIUM_HIGH = "medium_high"  # 0.7-0.8 - Database lookup
    MEDIUM = "medium"          # 0.5-0.6 - Heuristic analysis
    LOW = "low"                # 0.3 - Default/placeholder
    UNKNOWN = "unknown"        # 0.0 - Not yet assessed


class KineticSource(Enum):
    """Source types for kinetic data."""
    SBML = "sbml"                    # From SBML file
    MANUAL = "manual"                # User-entered
    DATABASE = "database_lookup"     # EC number database lookup
    HEURISTIC = "heuristic"          # Structure-based inference
    DEFAULT = "default"              # Placeholder/fallback
    UNKNOWN = "unknown"              # Not yet determined


@dataclass
class KineticMetadata:
    """
    Base class for kinetic metadata tracking.
    
    Tracks source, confidence, and kinetic parameters for transitions.
    Used for:
    - Preventing accidental overwrite of reliable data
    - Project report generation
    - UI confidence indicators
    - Audit trail
    
    Design Note:
    - Does NOT store transition ID or reference (to avoid circular dependencies)
    - Metadata is attached to Transition object as an attribute
    - Transition owns its metadata, not the other way around
    
    Attributes:
        source: Data source type
        confidence: Confidence level
        confidence_score: Numeric confidence (0.0-1.0)
        rate_type: Type of kinetic model
        formula: Mathematical expression
        parameters: Parameter values
        timestamp: When metadata was created
        locked: Prevent enrichment from overwriting
        needs_review: Flag for manual review
        manually_edited: True if user modified after initial assignment
    """
    
    # Source tracking
    source: KineticSource = KineticSource.UNKNOWN
    source_file: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    # Confidence
    confidence: ConfidenceLevel = ConfidenceLevel.UNKNOWN
    confidence_score: float = 0.0  # 0.0-1.0
    
    # Kinetic details
    rate_type: Optional[str] = None  # "michaelis_menten", "mass_action", "hill", etc.
    formula: Optional[str] = None
    parameters: Dict[str, float] = field(default_factory=dict)
    
    # Quality flags
    needs_review: bool = False
    manually_edited: bool = False
    locked: bool = False  # Prevent enrichment from overwriting
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary for serialization."""
        return {
            "source": self.source.value,
            "source_file": self.source_file,
            "timestamp": self.timestamp,
            "confidence": self.confidence.value,
            "confidence_score": self.confidence_score,
            "rate_type": self.rate_type,
            "formula": self.formula,
            "parameters": self.parameters,
            "needs_review": self.needs_review,
            "manually_edited": self.manually_edited,
            "locked": self.locked,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'KineticMetadata':
        """Create metadata from dictionary."""
        return cls(
            source=KineticSource(data.get("source", "unknown")),
            source_file=data.get("source_file"),
            timestamp=data.get("timestamp", datetime.now().isoformat()),
            confidence=ConfidenceLevel(data.get("confidence", "unknown")),
            confidence_score=data.get("confidence_score", 0.0),
            rate_type=data.get("rate_type"),
            formula=data.get("formula"),
            parameters=data.get("parameters", {}),
            needs_review=data.get("needs_review", False),
            manually_edited=data.get("manually_edited", False),
            locked=data.get("locked", False),
        )
    
    @staticmethod
    def should_preserve(metadata: Optional['KineticMetadata']) -> bool:
        """
        Check if kinetic data should be preserved (not overwritten).
        
        Preserves data from:
        - SBML (definitive)
        - Manual entry (high confidence)
        - Locked metadata (explicit protection)
        
        Args:
            metadata: Kinetic metadata to check
            
        Returns:
            True if data should be preserved, False if can be overwritten
        """
        if metadata is None:
            return False
        
        # Always preserve locked metadata
        if metadata.locked:
            return True
        
        # Preserve SBML and manual sources
        if metadata.source in (KineticSource.SBML, KineticSource.MANUAL):
            return True
        
        # Preserve high confidence data
        if metadata.confidence in (ConfidenceLevel.DEFINITIVE, ConfidenceLevel.HIGH):
            return True
        
        return False


@dataclass
class SBMLKineticMetadata(KineticMetadata):
    """
    SBML-specific kinetic metadata.
    
    SBML kinetics are treated as definitive source data.
    They should never be overwritten by enrichment.
    
    Additional SBML-specific attributes:
        sbml_level: SBML specification level
        sbml_version: SBML specification version
        sbml_reaction_id: Original SBML reaction ID
        sbml_model_id: Original SBML model ID
    """
    
    # SBML-specific fields
    sbml_level: Optional[int] = None
    sbml_version: Optional[int] = None
    sbml_reaction_id: Optional[str] = None
    sbml_model_id: Optional[str] = None
    
    def __post_init__(self):
        """Set default values for SBML metadata."""
        self.source = KineticSource.SBML
        self.confidence = ConfidenceLevel.DEFINITIVE
        self.confidence_score = 1.0
        self.locked = True  # SBML kinetics are always locked
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with SBML-specific fields."""
        data = super().to_dict()
        data.update({
            "sbml_level": self.sbml_level,
            "sbml_version": self.sbml_version,
            "sbml_reaction_id": self.sbml_reaction_id,
            "sbml_model_id": self.sbml_model_id,
        })
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SBMLKineticMetadata':
        """Create SBML metadata from dictionary."""
        return cls(
            source_file=data.get("source_file"),
            timestamp=data.get("timestamp", datetime.now().isoformat()),
            rate_type=data.get("rate_type"),
            formula=data.get("formula"),
            parameters=data.get("parameters", {}),
            sbml_level=data.get("sbml_level"),
            sbml_version=data.get("sbml_version"),
            sbml_reaction_id=data.get("sbml_reaction_id"),
            sbml_model_id=data.get("sbml_model_id"),
            needs_review=data.get("needs_review", False),
            manually_edited=data.get("manually_edited", False),
        )


@dataclass
class ManualKineticMetadata(KineticMetadata):
    """
    Manual user-entered kinetic metadata.
    
    Manual entry is treated as high-confidence data.
    
    Additional manual-entry attributes:
        entered_by: Username or identifier
        rationale: Why this kinetic model was chosen
    """
    
    # Manual entry fields
    entered_by: Optional[str] = None
    rationale: Optional[str] = None
    
    def __post_init__(self):
        """Set default values for manual metadata."""
        self.source = KineticSource.MANUAL
        self.confidence = ConfidenceLevel.HIGH
        self.confidence_score = 0.95
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with manual-entry fields."""
        data = super().to_dict()
        data.update({
            "entered_by": self.entered_by,
            "rationale": self.rationale,
        })
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ManualKineticMetadata':
        """Create manual metadata from dictionary."""
        return cls(
            source_file=data.get("source_file"),
            timestamp=data.get("timestamp", datetime.now().isoformat()),
            rate_type=data.get("rate_type"),
            formula=data.get("formula"),
            parameters=data.get("parameters", {}),
            entered_by=data.get("entered_by"),
            rationale=data.get("rationale"),
            needs_review=data.get("needs_review", False),
            manually_edited=data.get("manually_edited", False),
            locked=data.get("locked", False),
        )


@dataclass
class DatabaseKineticMetadata(KineticMetadata):
    """
    Database lookup kinetic metadata.
    
    Medium-high confidence based on EC number database.
    
    Additional database-lookup attributes:
        ec_number: EC classification number
        organism: Organism species
        database: Source database name
        database_id: Entry ID in database
    """
    
    # Database lookup fields
    ec_number: Optional[str] = None  # e.g., "2.7.1.1"
    organism: Optional[str] = None   # e.g., "Homo sapiens"
    database: Optional[str] = None   # "brenda", "kegg", "sabio-rk"
    database_id: Optional[str] = None
    
    def __post_init__(self):
        """Set default values for database metadata."""
        self.source = KineticSource.DATABASE
        self.confidence = ConfidenceLevel.MEDIUM_HIGH
        self.confidence_score = 0.75  # Default, can be adjusted
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with database-lookup fields."""
        data = super().to_dict()
        data.update({
            "ec_number": self.ec_number,
            "organism": self.organism,
            "database": self.database,
            "database_id": self.database_id,
        })
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DatabaseKineticMetadata':
        """Create database metadata from dictionary."""
        return cls(
            source_file=data.get("source_file"),
            timestamp=data.get("timestamp", datetime.now().isoformat()),
            rate_type=data.get("rate_type"),
            formula=data.get("formula"),
            parameters=data.get("parameters", {}),
            ec_number=data.get("ec_number"),
            organism=data.get("organism"),
            database=data.get("database"),
            database_id=data.get("database_id"),
            confidence_score=data.get("confidence_score", 0.75),
            needs_review=data.get("needs_review", False),
            manually_edited=data.get("manually_edited", False),
            locked=data.get("locked", False),
        )


@dataclass
class HeuristicKineticMetadata(KineticMetadata):
    """
    Heuristic analysis kinetic metadata.
    
    Medium confidence based on reaction structure analysis.
    
    Additional heuristic-analysis attributes:
        heuristic_method: Name of heuristic method used
        locality_context: Neighborhood information
    """
    
    # Heuristic analysis fields
    heuristic_method: Optional[str] = None  # "structure_based", "stoichiometry", etc.
    locality_context: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Set default values for heuristic metadata."""
        self.source = KineticSource.HEURISTIC
        self.confidence = ConfidenceLevel.MEDIUM
        self.confidence_score = 0.55  # Default, can be adjusted
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with heuristic-analysis fields."""
        data = super().to_dict()
        data.update({
            "heuristic_method": self.heuristic_method,
            "locality_context": self.locality_context,
        })
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HeuristicKineticMetadata':
        """Create heuristic metadata from dictionary."""
        return cls(
            source_file=data.get("source_file"),
            timestamp=data.get("timestamp", datetime.now().isoformat()),
            rate_type=data.get("rate_type"),
            formula=data.get("formula"),
            parameters=data.get("parameters", {}),
            heuristic_method=data.get("heuristic_method"),
            locality_context=data.get("locality_context"),
            confidence_score=data.get("confidence_score", 0.55),
            needs_review=data.get("needs_review", False),
            manually_edited=data.get("manually_edited", False),
            locked=data.get("locked", False),
        )


def create_metadata_from_dict(data: Dict[str, Any]) -> KineticMetadata:
    """
    Factory function to create appropriate metadata subclass from dictionary.
    
    Args:
        data: Dictionary with metadata fields
        
    Returns:
        Appropriate KineticMetadata subclass instance
    """
    source = data.get("source", "unknown")
    
    if source == "sbml":
        return SBMLKineticMetadata.from_dict(data)
    elif source == "manual":
        return ManualKineticMetadata.from_dict(data)
    elif source == "database_lookup":
        return DatabaseKineticMetadata.from_dict(data)
    elif source == "heuristic":
        return HeuristicKineticMetadata.from_dict(data)
    else:
        return KineticMetadata.from_dict(data)
