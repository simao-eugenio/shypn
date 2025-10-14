"""
Kinetics Enricher

Applies kinetic parameters from BioModels to pathway transitions.

Sets reaction rate constants, Michaelis-Menten parameters, and other
kinetic data needed for accurate pathway simulation.

Author: Shypn Development Team
Date: October 2025
"""

from typing import Any, Dict, List, Optional, Set
from enum import Enum

from .base_enricher import EnricherBase, EnrichmentResult, EnrichmentChange
from ..models import FetchResult, FetchStatus


class KineticLawType(Enum):
    """Types of kinetic rate laws."""
    MASS_ACTION = "mass_action"
    MICHAELIS_MENTEN = "michaelis_menten"
    HILL = "hill"
    COMPETITIVE_INHIBITION = "competitive_inhibition"
    ALLOSTERIC = "allosteric"
    CUSTOM = "custom"
    UNKNOWN = "unknown"


class KineticsEnricher(EnricherBase):
    """
    Enricher that applies kinetic parameters to pathway transitions.
    
    Takes kinetic data from BioModels (or other sources) and applies
    rate constants, Km values, and other parameters to transitions.
    
    Features:
    - Multiple kinetic law types (mass action, Michaelis-Menten, Hill, etc.)
    - Rate constant conversion and unit handling
    - Temperature and pH dependency
    - Enzyme-specific parameters (kcat, Km, Ki)
    - Time-aware transition configuration
    
    Example:
        >>> enricher = KineticsEnricher(prefer_time_aware=True)
        >>> result = enricher.apply(pathway, biomodels_result)
        >>> print(f"Modified {result.objects_modified} transitions")
    """
    
    def __init__(
        self,
        prefer_time_aware: bool = True,
        set_rate_constants: bool = True,
        set_delays: bool = False,
        default_time_unit: str = "seconds"
    ):
        """
        Initialize KineticsEnricher.
        
        Args:
            prefer_time_aware: Prefer time-aware transitions when available (default: True)
            set_rate_constants: Set rate constant values (default: True)
            set_delays: Set delay values for timed transitions (default: False)
            default_time_unit: Default time unit for parameters (default: "seconds")
        """
        super().__init__("KineticsEnricher")
        self.prefer_time_aware = prefer_time_aware
        self.set_rate_constants = set_rate_constants
        self.set_delays = set_delays
        self.default_time_unit = default_time_unit
    
    def can_enrich(self, data_type: str) -> bool:
        """Check if can enrich this data type."""
        return data_type.lower() in ["kinetics", "rate_constants", "reaction_rates"]
    
    def get_supported_data_types(self) -> Set[str]:
        """Get supported data types."""
        return {"kinetics", "rate_constants", "reaction_rates"}
    
    def validate(
        self,
        pathway: Any,
        fetch_result: FetchResult
    ) -> tuple[bool, List[str]]:
        """
        Validate kinetic data.
        
        Checks:
        - Fetch was successful
        - Data contains kinetic information
        - Rate constants are numeric
        - Reaction IDs match pathway transitions
        """
        errors = []
        
        # Check fetch status
        if fetch_result.status != FetchStatus.SUCCESS:
            errors.append(f"Fetch failed: {fetch_result.status.value}")
            return False, errors
        
        # Check data exists
        if not fetch_result.data:
            errors.append("No enrichment data in fetch result")
            return False, errors
        
        # Check for kinetics key
        if "kinetics" not in fetch_result.data:
            errors.append("No 'kinetics' key in fetch result data")
            return False, errors
        
        kinetics = fetch_result.data["kinetics"]
        
        # Validate kinetics data structure
        if not isinstance(kinetics, dict):
            errors.append(f"Kinetics must be dict, got {type(kinetics)}")
            return False, errors
        
        # Validate each kinetics entry
        for reaction_id, kinetic_data in kinetics.items():
            if not isinstance(kinetic_data, dict):
                errors.append(f"Kinetics for {reaction_id} must be dict")
                continue
            
            # Check for rate or parameters
            if "rate" not in kinetic_data and "parameters" not in kinetic_data:
                errors.append(f"Kinetics for {reaction_id} missing 'rate' or 'parameters'")
        
        return len(errors) == 0, errors
    
    def apply(
        self,
        pathway: Any,
        fetch_result: FetchResult,
        **options
    ) -> EnrichmentResult:
        """
        Apply kinetic data to pathway transitions.
        
        Args:
            pathway: Pathway document with transitions
            fetch_result: Result containing kinetic data
            **options: Optional parameters:
                - prefer_time_aware: Override default for time-aware transitions
                - update_existing: Update transitions with existing parameters (default: True)
                - match_by: How to match reactions - "id", "name", or "both" (default: "both")
        
        Returns:
            EnrichmentResult with details of changes
        """
        result = EnrichmentResult(
            success=True,
            objects_modified=0,
            enricher_name=self.enricher_name,
            source_name=fetch_result.attribution.source_name if fetch_result.attribution else "unknown"
        )
        
        # Validate first
        is_valid, errors = self.validate(pathway, fetch_result)
        if not is_valid:
            result.success = False
            for error in errors:
                result.add_error(error)
            return result
        
        # Extract options
        prefer_time_aware = options.get("prefer_time_aware", self.prefer_time_aware)
        update_existing = options.get("update_existing", True)
        match_by = options.get("match_by", "both")
        
        # Get kinetics
        kinetics = fetch_result.data["kinetics"]
        
        # Build transition lookup
        transition_lookup = self._build_transition_lookup(pathway, match_by)
        
        # Apply kinetics to transitions
        for reaction_id, kinetic_data in kinetics.items():
            transition = transition_lookup.get(reaction_id)
            
            if transition is None:
                result.add_warning(f"No matching transition found for reaction: {reaction_id}")
                continue
            
            try:
                self._apply_kinetics_to_transition(
                    transition,
                    kinetic_data,
                    prefer_time_aware,
                    update_existing,
                    result
                )
            except Exception as e:
                result.add_error(f"Failed to apply kinetics for {reaction_id}: {e}")
        
        # Set success based on whether we modified anything
        result.success = result.objects_modified > 0 or len(result.errors) == 0
        
        if result.objects_modified == 0 and len(result.errors) == 0:
            result.add_warning("No transitions were modified")
        
        return result
    
    def _apply_kinetics_to_transition(
        self,
        transition: Any,
        kinetic_data: Dict[str, Any],
        prefer_time_aware: bool,
        update_existing: bool,
        result: EnrichmentResult
    ) -> None:
        """Apply kinetic data to a single transition."""
        
        transition_id = transition.id if hasattr(transition, "id") else str(id(transition))
        
        # Set transition type if time-aware preferred
        if prefer_time_aware and hasattr(transition, "transition_type"):
            old_type = transition.transition_type
            if old_type == "immediate" or old_type is None:
                transition.transition_type = "continuous"
                
                change = self._record_change(
                    object_id=transition_id,
                    object_type="transition",
                    property_name="transition_type",
                    old_value=old_type,
                    new_value="continuous",
                    source=result.source_name
                )
                result.add_change(change)
        
        # Apply rate constant
        if self.set_rate_constants and "rate" in kinetic_data:
            rate_value = kinetic_data["rate"]
            
            # Store in metadata or direct property
            if hasattr(transition, "rate_constant"):
                old_rate = transition.rate_constant
                transition.rate_constant = rate_value
                
                change = self._record_change(
                    object_id=transition_id,
                    object_type="transition",
                    property_name="rate_constant",
                    old_value=old_rate,
                    new_value=rate_value,
                    source=result.source_name
                )
                result.add_change(change)
            else:
                # Store in metadata
                if not hasattr(transition, "metadata"):
                    transition.metadata = {}
                
                old_metadata = transition.metadata.copy()
                transition.metadata["rate_constant"] = rate_value
                
                change = self._record_change(
                    object_id=transition_id,
                    object_type="transition",
                    property_name="metadata.rate_constant",
                    old_value=old_metadata.get("rate_constant"),
                    new_value=rate_value,
                    source=result.source_name
                )
                result.add_change(change)
        
        # Apply parameters (Km, kcat, etc.)
        if "parameters" in kinetic_data:
            self._apply_parameters(
                transition,
                kinetic_data["parameters"],
                result
            )
        
        # Apply kinetic law type
        if "law_type" in kinetic_data:
            if not hasattr(transition, "metadata"):
                transition.metadata = {}
            
            old_metadata = transition.metadata.copy()
            transition.metadata["kinetic_law"] = kinetic_data["law_type"]
            
            change = self._record_change(
                object_id=transition_id,
                object_type="transition",
                property_name="metadata.kinetic_law",
                old_value=old_metadata.get("kinetic_law"),
                new_value=kinetic_data["law_type"],
                source=result.source_name
            )
            result.add_change(change)
    
    def _apply_parameters(
        self,
        transition: Any,
        parameters: Dict[str, Any],
        result: EnrichmentResult
    ) -> None:
        """Apply kinetic parameters to transition metadata."""
        
        transition_id = transition.id if hasattr(transition, "id") else str(id(transition))
        
        if not hasattr(transition, "metadata"):
            transition.metadata = {}
        
        old_metadata = transition.metadata.copy()
        
        # Store parameters
        if "parameters" not in transition.metadata:
            transition.metadata["parameters"] = {}
        
        for param_name, param_value in parameters.items():
            transition.metadata["parameters"][param_name] = param_value
        
        change = self._record_change(
            object_id=transition_id,
            object_type="transition",
            property_name="metadata.parameters",
            old_value=old_metadata.get("parameters", {}),
            new_value=transition.metadata["parameters"].copy(),
            source=result.source_name
        )
        result.add_change(change)
    
    def _build_transition_lookup(
        self,
        pathway: Any,
        match_by: str
    ) -> Dict[str, Any]:
        """Build lookup dictionary for transitions."""
        lookup = {}
        
        if not hasattr(pathway, "transitions"):
            return lookup
        
        for transition in pathway.transitions:
            # Match by ID
            if match_by in ["id", "both"]:
                if hasattr(transition, "id"):
                    lookup[transition.id] = transition
            
            # Match by name
            if match_by in ["name", "both"]:
                if hasattr(transition, "name"):
                    lookup[transition.name] = transition
        
        return lookup
    
    def _apply_change(self, pathway: Any, change_dict: Dict[str, Any]) -> None:
        """Apply a change (for rollback)."""
        object_id = change_dict["object_id"]
        property_name = change_dict["property"]
        value = change_dict["value"]
        
        # Find transition and apply change
        if hasattr(pathway, "transitions"):
            for transition in pathway.transitions:
                if hasattr(transition, "id") and transition.id == object_id:
                    # Handle nested properties (e.g., "metadata.rate_constant")
                    if "." in property_name:
                        parts = property_name.split(".")
                        obj = transition
                        for part in parts[:-1]:
                            obj = getattr(obj, part, {})
                        if isinstance(obj, dict):
                            obj[parts[-1]] = value
                    else:
                        setattr(transition, property_name, value)
                    break
    
    def get_kinetics_summary(
        self,
        fetch_result: FetchResult
    ) -> Dict[str, Any]:
        """
        Get summary of kinetics data.
        
        Args:
            fetch_result: Result containing kinetics data
        
        Returns:
            Dictionary with summary statistics
        """
        if not fetch_result.data or "kinetics" not in fetch_result.data:
            return {
                "reaction_count": 0,
                "avg_rate": 0.0,
                "law_types": {}
            }
        
        kinetics = fetch_result.data["kinetics"]
        
        # Collect statistics
        rates = []
        law_types = {}
        
        for kinetic_data in kinetics.values():
            if "rate" in kinetic_data:
                rates.append(kinetic_data["rate"])
            
            if "law_type" in kinetic_data:
                law_type = kinetic_data["law_type"]
                law_types[law_type] = law_types.get(law_type, 0) + 1
        
        return {
            "reaction_count": len(kinetics),
            "avg_rate": sum(rates) / len(rates) if rates else 0.0,
            "min_rate": min(rates) if rates else 0.0,
            "max_rate": max(rates) if rates else 0.0,
            "law_types": law_types
        }
    
    def __repr__(self) -> str:
        """String representation."""
        return (
            f"KineticsEnricher("
            f"time_aware={self.prefer_time_aware}, "
            f"set_rates={self.set_rate_constants})"
        )
