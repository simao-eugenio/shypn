#!/usr/bin/env python3
"""Dataclasses for Viability Panel.

Defines the data structures used for:
- Issues detected in the model
- Suggestions for fixing issues
- Changes applied (for undo)
- Boundary analysis between localities
- Comparison reports between localities

Author: Simão Eugénio
Date: November 10, 2025
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional


@dataclass
class Issue:
    """Represents a detected issue in the model.
    
    Issues can be structural (topology), biological (semantics),
    or kinetic (parameters).
    """
    id: str
    category: str  # "structural", "biological", "kinetic"
    severity: str  # "critical", "warning", "info"
    title: str
    description: str
    element_id: str  # Place, transition, or arc ID
    element_type: str  # "place", "transition", "arc"
    locality_id: Optional[str] = None
    suggestions: List['Suggestion'] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __repr__(self):
        return f"Issue({self.severity}: {self.title} - {self.element_id})"


@dataclass
class Suggestion:
    """Represents a suggested fix for an issue.
    
    Contains:
    - What action to take
    - What category of knowledge it comes from
    - Parameters needed to apply it
    - Confidence score (0-1)
    - Reasoning/explanation
    """
    action: str  # "set_marking", "add_source", "set_rate", "set_weight", etc.
    category: str  # "structural", "biological", "kinetic"
    parameters: Dict[str, Any]
    confidence: float  # 0.0 - 1.0
    reasoning: str
    preview_elements: List[str] = field(default_factory=list)  # IDs to highlight
    
    def __repr__(self):
        return f"Suggestion({self.action}, {self.confidence:.0%})"


@dataclass
class Change:
    """Record of an applied change (for undo).
    
    Tracks what was changed, from what value to what value,
    and when it was changed. Used for the undo stack.
    """
    element_id: str
    element_type: str  # "place", "transition", "arc"
    property: str  # "tokens", "rate", "weight"
    old_value: Any
    new_value: Any
    timestamp: datetime = field(default_factory=datetime.now)
    locality_id: Optional[str] = None
    suggestion_id: Optional[str] = None
    
    def __repr__(self):
        return f"Change({self.element_id}.{self.property}: {self.old_value} → {self.new_value})"


@dataclass
class BoundaryAnalysis:
    """Analysis of locality boundaries.
    
    When analyzing a locality, this tracks:
    - Input places (from other localities)
    - Output places (to other localities)
    - Interface transitions
    - Issues at the boundary
    - Suggestions for boundary fixes
    """
    locality_id: str
    input_places: List[Tuple[str, str, str]] = field(default_factory=list)
    # (place_id, source_locality, status)
    
    output_places: List[Tuple[str, str, str]] = field(default_factory=list)
    # (place_id, dest_locality, status)
    
    interface_transitions: List[str] = field(default_factory=list)
    boundary_issues: List[Issue] = field(default_factory=list)
    suggestions: List[Suggestion] = field(default_factory=list)
    
    def __repr__(self):
        return f"BoundaryAnalysis({self.locality_id}: {len(self.boundary_issues)} issues)"


@dataclass
class ComparisonReport:
    """Comparison between two localities.
    
    Used for comparing health scores, issues, and recommendations
    across different model regions.
    """
    locality_1_id: str
    locality_2_id: str
    
    health_comparison: Dict[str, Tuple[float, float]] = field(default_factory=dict)
    # category -> (health1, health2)
    # e.g., {"structural": (0.85, 0.60), "biological": (0.90, 0.75)}
    
    common_issues: List[str] = field(default_factory=list)
    # Issue titles that appear in both localities
    
    unique_issues_1: List[Issue] = field(default_factory=list)
    unique_issues_2: List[Issue] = field(default_factory=list)
    
    recommendations: List[str] = field(default_factory=list)
    
    def __repr__(self):
        return f"ComparisonReport({self.locality_1_id} vs {self.locality_2_id})"


@dataclass
class MultiDomainSuggestion:
    """A suggestion that combines knowledge from multiple domains.
    
    This is the key innovation: showing how structural, biological,
    and kinetic knowledge all contribute to the same fix.
    
    Example:
    - Structural: "Add 5 tokens to P3 (empty siphon)"
    - Biological: "P3 is ATP (C00002), typical conc: 1-10 mM"
    - Kinetic: "Rate 0.5 mM/s based on EC 2.7.1.1 (hexokinase)"
    """
    issue_id: str
    element_id: str
    
    structural_suggestion: Optional[Suggestion] = None
    biological_suggestion: Optional[Suggestion] = None
    kinetic_suggestion: Optional[Suggestion] = None
    
    combined_confidence: float = 0.0
    combined_reasoning: str = ""
    
    def has_multiple_domains(self) -> bool:
        """Check if this combines suggestions from multiple domains."""
        count = sum([
            self.structural_suggestion is not None,
            self.biological_suggestion is not None,
            self.kinetic_suggestion is not None
        ])
        return count >= 2
    
    def get_domains(self) -> List[str]:
        """Get list of domains that contributed to this suggestion."""
        domains = []
        if self.structural_suggestion:
            domains.append("structural")
        if self.biological_suggestion:
            domains.append("biological")
        if self.kinetic_suggestion:
            domains.append("kinetic")
        return domains
    
    def __repr__(self):
        domains = "+".join(self.get_domains())
        return f"MultiDomainSuggestion({domains}, {self.combined_confidence:.0%})"
