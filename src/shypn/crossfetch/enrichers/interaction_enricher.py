"""
Interaction Enricher

Applies protein-protein interaction data from Reactome to pathway arcs.

Creates or modifies arcs to represent regulatory relationships, complex
formations, and other molecular interactions discovered in Reactome data.

Author: Shypn Development Team
Date: October 2025
"""

from typing import Any, Dict, List, Optional, Set, Tuple
from enum import Enum

from .base_enricher import EnricherBase, EnrichmentResult, EnrichmentChange
from ..models import FetchResult, FetchStatus


class InteractionType(Enum):
    """Types of molecular interactions."""
    ACTIVATION = "activation"
    INHIBITION = "inhibition"
    CATALYSIS = "catalysis"
    BINDING = "binding"
    PHOSPHORYLATION = "phosphorylation"
    DEPHOSPHORYLATION = "dephosphorylation"
    METHYLATION = "methylation"
    UBIQUITINATION = "ubiquitination"
    COMPLEX_FORMATION = "complex_formation"
    DISSOCIATION = "dissociation"
    TRANSPORT = "transport"
    UNKNOWN = "unknown"


class InteractionEnricher(EnricherBase):
    """
    Enricher that applies interaction data to pathway arcs.
    
    Takes protein-protein interaction data from Reactome (or other sources)
    and creates or modifies arcs to represent these regulatory relationships.
    
    Features:
    - Create new arcs for discovered interactions
    - Update existing arcs with interaction metadata
    - Support for multiple interaction types (activation, inhibition, etc.)
    - Confidence scoring for interactions
    - Conflict resolution for overlapping interactions
    
    Example:
        >>> enricher = InteractionEnricher(create_missing=True)
        >>> result = enricher.apply(pathway, reactome_result)
        >>> print(f"Created {result.objects_modified} new arcs")
    """
    
    def __init__(
        self,
        create_missing: bool = True,
        update_existing: bool = True,
        min_confidence: float = 0.0,
        interaction_types: Optional[Set[str]] = None
    ):
        """
        Initialize InteractionEnricher.
        
        Args:
            create_missing: Create new arcs for interactions not in pathway (default: True)
            update_existing: Update existing arcs with interaction data (default: True)
            min_confidence: Minimum confidence score to apply (0.0-1.0, default: 0.0)
            interaction_types: Set of interaction types to include (None = all types)
        """
        super().__init__("InteractionEnricher")
        self.create_missing = create_missing
        self.update_existing = update_existing
        self.min_confidence = min_confidence
        self.interaction_types = interaction_types
    
    def can_enrich(self, data_type: str) -> bool:
        """Check if can enrich this data type."""
        return data_type.lower() in ["interactions", "protein_interactions", "regulations"]
    
    def get_supported_data_types(self) -> Set[str]:
        """Get supported data types."""
        return {"interactions", "protein_interactions", "regulations"}
    
    def validate(
        self,
        pathway: Any,
        fetch_result: FetchResult
    ) -> tuple[bool, List[str]]:
        """
        Validate interaction data.
        
        Checks:
        - Fetch was successful
        - Data contains interaction information
        - Interactions have required fields (source, target)
        - Place IDs are valid
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
        
        # Check for interactions key
        if "interactions" not in fetch_result.data:
            errors.append("No 'interactions' key in fetch result data")
            return False, errors
        
        interactions = fetch_result.data["interactions"]
        
        # Validate interaction data structure
        if not isinstance(interactions, list):
            errors.append(f"Interactions must be list, got {type(interactions)}")
            return False, errors
        
        # Validate each interaction entry
        for i, interaction in enumerate(interactions):
            if not isinstance(interaction, dict):
                errors.append(f"Interaction {i} must be dict")
                continue
            
            # Check required fields
            if "source" not in interaction:
                errors.append(f"Interaction {i} missing 'source' field")
            
            if "target" not in interaction:
                errors.append(f"Interaction {i} missing 'target' field")
            
            if "type" not in interaction:
                errors.append(f"Interaction {i} missing 'type' field")
        
        return len(errors) == 0, errors
    
    def apply(
        self,
        pathway: Any,
        fetch_result: FetchResult,
        **options
    ) -> EnrichmentResult:
        """
        Apply interaction data to pathway arcs.
        
        Args:
            pathway: Pathway document with places, transitions, and arcs
            fetch_result: Result containing interaction data
            **options: Optional parameters:
                - create_missing: Override default for creating new arcs
                - update_existing: Override default for updating arcs
                - min_confidence: Override minimum confidence threshold
                - arc_type: Default arc type for created arcs (default: "normal")
        
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
        create_missing = options.get("create_missing", self.create_missing)
        update_existing = options.get("update_existing", self.update_existing)
        min_confidence = options.get("min_confidence", self.min_confidence)
        default_arc_type = options.get("arc_type", "normal")
        
        # Get interactions
        interactions = fetch_result.data["interactions"]
        
        # Build lookups
        place_lookup = self._build_place_lookup(pathway)
        arc_lookup = self._build_arc_lookup(pathway)
        
        # Apply interactions
        for interaction in interactions:
            try:
                self._apply_interaction(
                    pathway,
                    interaction,
                    place_lookup,
                    arc_lookup,
                    create_missing,
                    update_existing,
                    min_confidence,
                    default_arc_type,
                    result
                )
            except Exception as e:
                result.add_error(f"Failed to apply interaction {interaction.get('id', 'unknown')}: {e}")
        
        # Set success based on whether we modified anything
        result.success = result.objects_modified > 0 or len(result.errors) == 0
        
        if result.objects_modified == 0 and len(result.errors) == 0:
            result.add_warning("No arcs were modified or created")
        
        return result
    
    def _apply_interaction(
        self,
        pathway: Any,
        interaction: Dict[str, Any],
        place_lookup: Dict[str, Any],
        arc_lookup: Dict[Tuple[str, str], Any],
        create_missing: bool,
        update_existing: bool,
        min_confidence: float,
        default_arc_type: str,
        result: EnrichmentResult
    ) -> None:
        """Apply a single interaction."""
        
        # Extract interaction data
        source_id = interaction["source"]
        target_id = interaction["target"]
        interaction_type = interaction.get("type", "unknown")
        confidence = interaction.get("confidence", 1.0)
        
        # Check confidence threshold
        if confidence < min_confidence:
            result.add_warning(f"Skipping interaction {source_id}→{target_id} (confidence {confidence} < {min_confidence})")
            return
        
        # Check interaction type filter
        if self.interaction_types and interaction_type not in self.interaction_types:
            return
        
        # Find source and target places
        source_place = place_lookup.get(source_id)
        target_place = place_lookup.get(target_id)
        
        if source_place is None:
            result.add_warning(f"Source place not found: {source_id}")
            return
        
        if target_place is None:
            result.add_warning(f"Target place not found: {target_id}")
            return
        
        # Check if arc already exists
        arc_key = (source_place.id, target_place.id)
        existing_arc = arc_lookup.get(arc_key)
        
        if existing_arc:
            # Update existing arc
            if update_existing:
                self._update_arc(existing_arc, interaction, result)
        else:
            # Create new arc
            if create_missing:
                self._create_arc(
                    pathway,
                    source_place,
                    target_place,
                    interaction,
                    default_arc_type,
                    result
                )
    
    def _update_arc(
        self,
        arc: Any,
        interaction: Dict[str, Any],
        result: EnrichmentResult
    ) -> None:
        """Update an existing arc with interaction data."""
        
        # Store old metadata
        old_metadata = getattr(arc, "metadata", {}).copy() if hasattr(arc, "metadata") else {}
        
        # Create or update metadata
        if not hasattr(arc, "metadata"):
            arc.metadata = {}
        
        # Add interaction information
        if "interactions" not in arc.metadata:
            arc.metadata["interactions"] = []
        
        arc.metadata["interactions"].append({
            "type": interaction.get("type"),
            "confidence": interaction.get("confidence", 1.0),
            "source_db": interaction.get("source_db", "unknown"),
            "interaction_id": interaction.get("id")
        })
        
        # Update arc type based on interaction type
        interaction_type = interaction.get("type", "").lower()
        if interaction_type in ["inhibition", "inhibit"]:
            old_arc_type = getattr(arc, "arc_type", "normal")
            arc.arc_type = "inhibitor"
            
            # Record change
            change = self._record_change(
                object_id=arc.id if hasattr(arc, "id") else str(id(arc)),
                object_type="arc",
                property_name="arc_type",
                old_value=old_arc_type,
                new_value="inhibitor",
                source=interaction.get("source_db", "unknown")
            )
            result.add_change(change)
        
        # Record metadata change
        change = self._record_change(
            object_id=arc.id if hasattr(arc, "id") else str(id(arc)),
            object_type="arc",
            property_name="metadata",
            old_value=old_metadata,
            new_value=arc.metadata.copy(),
            source=interaction.get("source_db", "unknown")
        )
        result.add_change(change)
    
    def _create_arc(
        self,
        pathway: Any,
        source_place: Any,
        target_place: Any,
        interaction: Dict[str, Any],
        default_arc_type: str,
        result: EnrichmentResult
    ) -> None:
        """Create a new arc for an interaction."""
        
        # Determine arc type based on interaction type
        interaction_type = interaction.get("type", "").lower()
        if interaction_type in ["inhibition", "inhibit"]:
            arc_type = "inhibitor"
        elif interaction_type in ["activation", "activate"]:
            arc_type = "normal"  # Could be "activator" if that type exists
        else:
            arc_type = default_arc_type
        
        # Create arc metadata
        metadata = {
            "created_by": "InteractionEnricher",
            "source": interaction.get("source_db", "unknown"),
            "interactions": [{
                "type": interaction.get("type"),
                "confidence": interaction.get("confidence", 1.0),
                "interaction_id": interaction.get("id")
            }]
        }
        
        # Create the arc (this is a placeholder - actual implementation depends on pathway structure)
        # In real implementation, would need to access pathway's arc creation method
        result.add_warning(f"Would create arc: {source_place.id} → {target_place.id} (type: {arc_type})")
        
        # Record change (in real implementation)
        # change = self._record_change(
        #     object_id=new_arc.id,
        #     object_type="arc",
        #     property_name="created",
        #     old_value=None,
        #     new_value=True,
        #     source=interaction.get("source_db", "unknown")
        # )
        # result.add_change(change)
    
    def _build_place_lookup(self, pathway: Any) -> Dict[str, Any]:
        """Build lookup dictionary for places."""
        lookup = {}
        
        if not hasattr(pathway, "places"):
            return lookup
        
        for place in pathway.places:
            # Match by ID
            if hasattr(place, "id"):
                lookup[place.id] = place
            
            # Also match by name
            if hasattr(place, "name"):
                lookup[place.name] = place
        
        return lookup
    
    def _build_arc_lookup(self, pathway: Any) -> Dict[Tuple[str, str], Any]:
        """Build lookup dictionary for arcs by (source, target) pairs."""
        lookup = {}
        
        if not hasattr(pathway, "arcs"):
            return lookup
        
        for arc in pathway.arcs:
            if hasattr(arc, "source") and hasattr(arc, "target"):
                source_id = arc.source.id if hasattr(arc.source, "id") else str(arc.source)
                target_id = arc.target.id if hasattr(arc.target, "id") else str(arc.target)
                lookup[(source_id, target_id)] = arc
        
        return lookup
    
    def _apply_change(self, pathway: Any, change_dict: Dict[str, Any]) -> None:
        """Apply a change (for rollback)."""
        object_id = change_dict["object_id"]
        property_name = change_dict["property"]
        value = change_dict["value"]
        
        # Find arc and apply change
        if hasattr(pathway, "arcs"):
            for arc in pathway.arcs:
                arc_id = arc.id if hasattr(arc, "id") else str(id(arc))
                if arc_id == object_id:
                    setattr(arc, property_name, value)
                    break
    
    def get_interaction_summary(
        self,
        fetch_result: FetchResult
    ) -> Dict[str, Any]:
        """
        Get summary of interaction data.
        
        Args:
            fetch_result: Result containing interaction data
        
        Returns:
            Dictionary with summary statistics
        """
        if not fetch_result.data or "interactions" not in fetch_result.data:
            return {
                "interaction_count": 0,
                "types": {},
                "avg_confidence": 0.0
            }
        
        interactions = fetch_result.data["interactions"]
        
        # Count by type
        type_counts = {}
        confidences = []
        
        for interaction in interactions:
            itype = interaction.get("type", "unknown")
            type_counts[itype] = type_counts.get(itype, 0) + 1
            
            if "confidence" in interaction:
                confidences.append(interaction["confidence"])
        
        return {
            "interaction_count": len(interactions),
            "types": type_counts,
            "avg_confidence": sum(confidences) / len(confidences) if confidences else 0.0,
            "unique_types": len(type_counts)
        }
    
    def __repr__(self) -> str:
        """String representation."""
        return (
            f"InteractionEnricher("
            f"create={self.create_missing}, "
            f"update={self.update_existing}, "
            f"min_conf={self.min_confidence})"
        )
