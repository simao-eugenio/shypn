"""
Concentration Enricher

Applies concentration data from BioModels to pathway places.

Converts molecular concentrations (typically in mM) to discrete token counts
for Petri net simulation. Uses a configurable scale factor to map continuous
concentrations to integer token values.

Author: Shypn Development Team
Date: October 2025
"""

from typing import Any, Dict, List, Optional, Set
import math

from .base_enricher import EnricherBase, EnrichmentResult, EnrichmentChange
from ..models import FetchResult, FetchStatus


class ConcentrationEnricher(EnricherBase):
    """
    Enricher that applies concentration data to pathway places.
    
    Takes concentration values from BioModels (or other sources) and
    converts them to initial token markings for Petri net places.
    
    Features:
    - Concentration to token conversion with scale factor
    - Support for different concentration units (mM, µM, nM)
    - Minimum token thresholds
    - Rounding strategies (floor, ceil, round)
    
    Example:
        >>> enricher = ConcentrationEnricher(scale_factor=10.0)
        >>> result = enricher.apply(pathway, biomodels_result)
        >>> print(f"Modified {result.objects_modified} places")
    """
    
    # Default scale factor: 10 tokens per mM
    DEFAULT_SCALE_FACTOR = 10.0
    
    # Minimum tokens to assign (0 = allow empty places)
    DEFAULT_MIN_TOKENS = 0
    
    # Maximum tokens to prevent overflow
    DEFAULT_MAX_TOKENS = 1000000
    
    # Unit conversion factors to mM
    UNIT_CONVERSIONS = {
        "mM": 1.0,
        "millimolar": 1.0,
        "uM": 0.001,
        "µM": 0.001,
        "micromolar": 0.001,
        "nM": 0.000001,
        "nanomolar": 0.000001,
        "M": 1000.0,
        "molar": 1000.0,
    }
    
    def __init__(
        self,
        scale_factor: float = DEFAULT_SCALE_FACTOR,
        min_tokens: int = DEFAULT_MIN_TOKENS,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        rounding: str = "round"  # "floor", "ceil", "round"
    ):
        """
        Initialize ConcentrationEnricher.
        
        Args:
            scale_factor: Tokens per mM concentration (default: 10.0)
            min_tokens: Minimum tokens to assign (default: 0)
            max_tokens: Maximum tokens to prevent overflow (default: 1000000)
            rounding: Rounding strategy - "floor", "ceil", or "round" (default: "round")
        """
        super().__init__("ConcentrationEnricher")
        self.scale_factor = scale_factor
        self.min_tokens = min_tokens
        self.max_tokens = max_tokens
        self.rounding = rounding
    
    def can_enrich(self, data_type: str) -> bool:
        """Check if can enrich this data type."""
        return data_type.lower() in ["concentrations", "initial_concentrations"]
    
    def get_supported_data_types(self) -> Set[str]:
        """Get supported data types."""
        return {"concentrations", "initial_concentrations"}
    
    def validate(
        self,
        pathway: Any,
        fetch_result: FetchResult
    ) -> tuple[bool, List[str]]:
        """
        Validate concentration data.
        
        Checks:
        - Fetch was successful
        - Data contains concentration information
        - Concentrations are numeric
        - Place IDs match pathway places
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
        
        # Check for concentrations key
        if "concentrations" not in fetch_result.data:
            errors.append("No 'concentrations' key in fetch result data")
            return False, errors
        
        concentrations = fetch_result.data["concentrations"]
        
        # Validate concentration data structure
        if not isinstance(concentrations, dict):
            errors.append(f"Concentrations must be dict, got {type(concentrations)}")
            return False, errors
        
        # Validate each concentration entry
        for species_id, conc_data in concentrations.items():
            if not isinstance(conc_data, dict):
                errors.append(f"Concentration for {species_id} must be dict")
                continue
            
            if "value" not in conc_data:
                errors.append(f"Missing 'value' for species {species_id}")
                continue
            
            try:
                float(conc_data["value"])
            except (TypeError, ValueError):
                errors.append(f"Invalid concentration value for {species_id}: {conc_data['value']}")
        
        return len(errors) == 0, errors
    
    def apply(
        self,
        pathway: Any,
        fetch_result: FetchResult,
        **options
    ) -> EnrichmentResult:
        """
        Apply concentration data to pathway places.
        
        Args:
            pathway: Pathway document with places
            fetch_result: Result containing concentration data
            **options: Optional parameters:
                - scale_factor: Override default scale factor
                - update_existing: Update places that already have tokens (default: True)
                - match_by: How to match species to places - "id", "name", or "both" (default: "both")
        
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
        scale_factor = options.get("scale_factor", self.scale_factor)
        update_existing = options.get("update_existing", True)
        match_by = options.get("match_by", "both")
        
        # Get concentrations
        concentrations = fetch_result.data["concentrations"]
        
        # Build place lookup
        place_lookup = self._build_place_lookup(pathway, match_by)
        
        # Apply concentrations to places
        for species_id, conc_data in concentrations.items():
            place = place_lookup.get(species_id)
            
            if place is None:
                result.add_warning(f"No matching place found for species: {species_id}")
                continue
            
            # Skip if place already has tokens and update_existing is False
            if not update_existing and hasattr(place, "tokens") and place.tokens > 0:
                result.add_warning(f"Skipping {species_id} - already has {place.tokens} tokens")
                continue
            
            # Convert concentration to tokens
            try:
                tokens = self._concentration_to_tokens(
                    conc_data["value"],
                    conc_data.get("unit", "mM"),
                    scale_factor
                )
                
                # Record old value
                old_tokens = place.tokens if hasattr(place, "tokens") else 0
                
                # Apply new tokens
                place.tokens = tokens
                
                # Record change
                change = self._record_change(
                    object_id=place.id,
                    object_type="place",
                    property_name="tokens",
                    old_value=old_tokens,
                    new_value=tokens,
                    source=result.source_name
                )
                
                result.add_change(change)
                
            except Exception as e:
                result.add_error(f"Failed to apply concentration for {species_id}: {e}")
        
        # Set success based on whether we modified anything
        result.success = result.objects_modified > 0
        
        if result.objects_modified == 0 and len(result.errors) == 0:
            result.add_warning("No places were modified")
        
        return result
    
    def _build_place_lookup(
        self,
        pathway: Any,
        match_by: str
    ) -> Dict[str, Any]:
        """
        Build lookup dictionary for matching species to places.
        
        Args:
            pathway: Pathway document
            match_by: Matching strategy - "id", "name", or "both"
        
        Returns:
            Dictionary mapping species identifiers to place objects
        """
        lookup = {}
        
        if not hasattr(pathway, "places"):
            return lookup
        
        for place in pathway.places:
            # Match by ID
            if match_by in ["id", "both"]:
                if hasattr(place, "id"):
                    lookup[place.id] = place
            
            # Match by name
            if match_by in ["name", "both"]:
                if hasattr(place, "name"):
                    lookup[place.name] = place
        
        return lookup
    
    def _concentration_to_tokens(
        self,
        concentration: float,
        unit: str,
        scale_factor: float
    ) -> int:
        """
        Convert concentration to token count.
        
        Args:
            concentration: Concentration value
            unit: Concentration unit (mM, µM, nM, etc.)
            scale_factor: Tokens per mM
        
        Returns:
            Integer token count
        """
        # Convert to mM
        conversion_factor = self.UNIT_CONVERSIONS.get(unit, 1.0)
        concentration_mM = concentration * conversion_factor
        
        # Convert to tokens
        tokens_float = concentration_mM * scale_factor
        
        # Apply rounding strategy
        if self.rounding == "floor":
            tokens = math.floor(tokens_float)
        elif self.rounding == "ceil":
            tokens = math.ceil(tokens_float)
        else:  # "round"
            tokens = round(tokens_float)
        
        # Apply bounds
        tokens = max(self.min_tokens, min(self.max_tokens, tokens))
        
        return tokens
    
    def _apply_change(self, pathway: Any, change_dict: Dict[str, Any]) -> None:
        """Apply a change (for rollback)."""
        object_id = change_dict["object_id"]
        property_name = change_dict["property"]
        value = change_dict["value"]
        
        # Find place and apply change
        if hasattr(pathway, "places"):
            for place in pathway.places:
                if hasattr(place, "id") and place.id == object_id:
                    setattr(place, property_name, value)
                    break
    
    def get_concentration_summary(
        self,
        fetch_result: FetchResult
    ) -> Dict[str, Any]:
        """
        Get summary of concentration data.
        
        Args:
            fetch_result: Result containing concentration data
        
        Returns:
            Dictionary with summary statistics
        """
        if not fetch_result.data or "concentrations" not in fetch_result.data:
            return {
                "species_count": 0,
                "min_concentration": 0.0,
                "max_concentration": 0.0,
                "avg_concentration": 0.0
            }
        
        concentrations = fetch_result.data["concentrations"]
        values = [c["value"] for c in concentrations.values() if "value" in c]
        
        if not values:
            return {
                "species_count": 0,
                "min_concentration": 0.0,
                "max_concentration": 0.0,
                "avg_concentration": 0.0
            }
        
        return {
            "species_count": len(values),
            "min_concentration": min(values),
            "max_concentration": max(values),
            "avg_concentration": sum(values) / len(values),
            "units": list(set(c.get("unit", "mM") for c in concentrations.values()))
        }
    
    def __repr__(self) -> str:
        """String representation."""
        return (
            f"ConcentrationEnricher("
            f"scale={self.scale_factor}, "
            f"min={self.min_tokens}, "
            f"max={self.max_tokens}, "
            f"rounding={self.rounding})"
        )
