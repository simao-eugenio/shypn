"""
Annotation Enricher

Merges annotation data from multiple sources.

Combines annotations from KEGG, BioModels, Reactome, and other sources,
resolving conflicts using quality scores and maintaining provenance.

Author: Shypn Development Team
Date: October 2025
"""

from typing import Any, Dict, List, Optional, Set, Tuple
from collections import defaultdict

from .base_enricher import EnricherBase, EnrichmentResult, EnrichmentChange
from ..models import FetchResult, FetchStatus


class ConflictResolutionStrategy(str):
    """Strategies for resolving annotation conflicts."""
    HIGHEST_QUALITY = "highest_quality"  # Use annotation from highest quality source
    MERGE_ALL = "merge_all"  # Merge all annotations
    NEWEST_FIRST = "newest_first"  # Prefer newest annotations
    LONGEST = "longest"  # Use longest/most detailed annotation
    MAJORITY_VOTE = "majority_vote"  # Use most common value across sources


class AnnotationEnricher(EnricherBase):
    """
    Enricher that merges annotations from multiple sources.
    
    Takes annotation data from multiple fetchers and intelligently
    merges them, handling conflicts through configurable strategies.
    
    Features:
    - Multi-source annotation merging
    - Conflict resolution strategies
    - Quality-based selection
    - Provenance tracking
    - Support for different annotation types (descriptions, names, synonyms, etc.)
    
    Example:
        >>> enricher = AnnotationEnricher(strategy="highest_quality")
        >>> results = [kegg_result, biomodels_result, reactome_result]
        >>> result = enricher.apply_multi(pathway, results)
        >>> print(f"Merged annotations for {result.objects_modified} objects")
    """
    
    # Annotation field types
    SINGLE_VALUE_FIELDS = {"name", "description", "formula", "compartment"}
    MULTI_VALUE_FIELDS = {"synonyms", "cross_references", "tags", "keywords"}
    
    def __init__(
        self,
        conflict_strategy: str = ConflictResolutionStrategy.HIGHEST_QUALITY,
        merge_multi_valued: bool = True,
        keep_provenance: bool = True,
        min_quality_score: float = 0.0
    ):
        """
        Initialize AnnotationEnricher.
        
        Args:
            conflict_strategy: Strategy for resolving conflicts (default: "highest_quality")
            merge_multi_valued: Merge multi-valued fields from all sources (default: True)
            keep_provenance: Track which source provided each annotation (default: True)
            min_quality_score: Minimum quality score to consider (default: 0.0)
        """
        super().__init__("AnnotationEnricher")
        self.conflict_strategy = conflict_strategy
        self.merge_multi_valued = merge_multi_valued
        self.keep_provenance = keep_provenance
        self.min_quality_score = min_quality_score
    
    def can_enrich(self, data_type: str) -> bool:
        """Check if can enrich this data type."""
        return data_type.lower() in ["annotations", "metadata", "descriptions"]
    
    def get_supported_data_types(self) -> Set[str]:
        """Get supported data types."""
        return {"annotations", "metadata", "descriptions"}
    
    def validate(
        self,
        pathway: Any,
        fetch_result: FetchResult
    ) -> tuple[bool, List[str]]:
        """
        Validate annotation data.
        
        Checks:
        - Fetch was successful
        - Data contains annotation information
        - Annotations have valid structure
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
        
        # Check for annotations key
        if "annotations" not in fetch_result.data:
            errors.append("No 'annotations' key in fetch result data")
            return False, errors
        
        annotations = fetch_result.data["annotations"]
        
        # Validate annotations data structure
        if not isinstance(annotations, dict):
            errors.append(f"Annotations must be dict, got {type(annotations)}")
            return False, errors
        
        return len(errors) == 0, errors
    
    def apply(
        self,
        pathway: Any,
        fetch_result: FetchResult,
        **options
    ) -> EnrichmentResult:
        """
        Apply annotations from a single source.
        
        Args:
            pathway: Pathway document
            fetch_result: Result containing annotation data
            **options: Optional parameters
        
        Returns:
            EnrichmentResult with details of changes
        """
        return self.apply_multi(pathway, [fetch_result], **options)
    
    def apply_multi(
        self,
        pathway: Any,
        fetch_results: List[FetchResult],
        **options
    ) -> EnrichmentResult:
        """
        Apply and merge annotations from multiple sources.
        
        Args:
            pathway: Pathway document
            fetch_results: List of results containing annotation data
            **options: Optional parameters:
                - object_types: List of object types to annotate (default: ["place", "transition", "arc"])
                - conflict_strategy: Override default strategy
        
        Returns:
            EnrichmentResult with details of changes
        """
        result = EnrichmentResult(
            success=True,
            objects_modified=0,
            enricher_name=self.enricher_name,
            source_name="multiple"
        )
        
        # Filter valid results
        valid_results = []
        for fetch_result in fetch_results:
            is_valid, errors = self.validate(pathway, fetch_result)
            if is_valid:
                # Check quality score
                if hasattr(fetch_result, "quality_metrics"):
                    overall_score = (
                        0.25 * fetch_result.quality_metrics.completeness +
                        0.30 * fetch_result.quality_metrics.source_reliability +
                        0.20 * fetch_result.quality_metrics.consistency +
                        0.25 * fetch_result.quality_metrics.validation_status
                    )
                    if overall_score >= self.min_quality_score:
                        valid_results.append(fetch_result)
                    else:
                        result.add_warning(
                            f"Skipping {fetch_result.attribution.source_name} "
                            f"(quality {overall_score:.2f} < {self.min_quality_score})"
                        )
                else:
                    valid_results.append(fetch_result)
            else:
                for error in errors:
                    result.add_warning(f"Invalid result: {error}")
        
        if not valid_results:
            result.success = False
            result.add_error("No valid annotation data to apply")
            return result
        
        # Extract options
        object_types = options.get("object_types", ["place", "transition", "arc"])
        conflict_strategy = options.get("conflict_strategy", self.conflict_strategy)
        
        # Collect annotations by object
        annotations_by_object = self._collect_annotations(valid_results, object_types)
        
        # Build object lookups
        object_lookups = self._build_object_lookups(pathway, object_types)
        
        # Apply merged annotations
        for object_id, annotations_list in annotations_by_object.items():
            obj = self._find_object(object_id, object_lookups)
            
            if obj is None:
                result.add_warning(f"Object not found: {object_id}")
                continue
            
            try:
                self._apply_merged_annotations(
                    obj,
                    annotations_list,
                    conflict_strategy,
                    result
                )
            except Exception as e:
                result.add_error(f"Failed to apply annotations for {object_id}: {e}")
        
        # Set success
        result.success = result.objects_modified > 0 or len(result.errors) == 0
        
        if result.objects_modified == 0 and len(result.errors) == 0:
            result.add_warning("No objects were annotated")
        
        return result
    
    def _collect_annotations(
        self,
        fetch_results: List[FetchResult],
        object_types: List[str]
    ) -> Dict[str, List[Tuple[Dict[str, Any], FetchResult]]]:
        """Collect all annotations organized by object ID."""
        
        annotations_by_object = defaultdict(list)
        
        for fetch_result in fetch_results:
            annotations = fetch_result.data["annotations"]
            
            for object_id, annotation_data in annotations.items():
                annotations_by_object[object_id].append((annotation_data, fetch_result))
        
        return annotations_by_object
    
    def _apply_merged_annotations(
        self,
        obj: Any,
        annotations_list: List[Tuple[Dict[str, Any], FetchResult]],
        conflict_strategy: str,
        result: EnrichmentResult
    ) -> None:
        """Apply merged annotations to an object."""
        
        object_id = obj.id if hasattr(obj, "id") else str(id(obj))
        object_type = self._get_object_type(obj)
        
        # Organize annotations by field
        fields_by_source = defaultdict(list)
        
        for annotation_data, fetch_result in annotations_list:
            source_name = fetch_result.attribution.source_name if fetch_result.attribution else "unknown"
            quality = self._get_quality_score(fetch_result)
            
            for field_name, field_value in annotation_data.items():
                fields_by_source[field_name].append((field_value, source_name, quality, fetch_result))
        
        # Merge each field
        for field_name, values_list in fields_by_source.items():
            try:
                merged_value, sources = self._merge_field(
                    field_name,
                    values_list,
                    conflict_strategy
                )
                
                # Apply merged value
                if merged_value is not None:
                    old_value = getattr(obj, field_name, None)
                    setattr(obj, field_name, merged_value)
                    
                    # Record change
                    change = self._record_change(
                        object_id=object_id,
                        object_type=object_type,
                        property_name=field_name,
                        old_value=old_value,
                        new_value=merged_value,
                        source=", ".join(sources) if sources else "unknown"
                    )
                    result.add_change(change)
                    
                    # Add provenance if enabled
                    if self.keep_provenance:
                        self._add_provenance(obj, field_name, sources)
            
            except Exception as e:
                result.add_warning(f"Failed to merge field {field_name} for {object_id}: {e}")
    
    def _merge_field(
        self,
        field_name: str,
        values_list: List[Tuple[Any, str, float, FetchResult]],
        strategy: str
    ) -> Tuple[Any, List[str]]:
        """Merge values for a single field using the specified strategy."""
        
        if not values_list:
            return None, []
        
        # Single value fields
        if field_name in self.SINGLE_VALUE_FIELDS:
            if strategy == ConflictResolutionStrategy.HIGHEST_QUALITY:
                # Sort by quality, take highest
                values_list.sort(key=lambda x: x[2], reverse=True)
                return values_list[0][0], [values_list[0][1]]
            
            elif strategy == ConflictResolutionStrategy.LONGEST:
                # Take longest/most detailed
                longest = max(values_list, key=lambda x: len(str(x[0])))
                return longest[0], [longest[1]]
            
            elif strategy == ConflictResolutionStrategy.MAJORITY_VOTE:
                # Count occurrences
                value_counts = defaultdict(list)
                for value, source, quality, _ in values_list:
                    value_counts[str(value)].append(source)
                
                # Return most common
                most_common = max(value_counts.items(), key=lambda x: len(x[1]))
                return most_common[0], most_common[1]
            
            else:
                # Default: first value
                return values_list[0][0], [values_list[0][1]]
        
        # Multi-value fields
        elif field_name in self.MULTI_VALUE_FIELDS:
            if self.merge_multi_valued:
                # Merge all unique values
                merged = set()
                sources = []
                
                for value, source, quality, _ in values_list:
                    if isinstance(value, (list, set)):
                        merged.update(value)
                    else:
                        merged.add(value)
                    sources.append(source)
                
                return list(merged), list(set(sources))
            else:
                # Take from highest quality source
                values_list.sort(key=lambda x: x[2], reverse=True)
                return values_list[0][0], [values_list[0][1]]
        
        # Unknown field type - merge as multi-value
        else:
            merged = []
            sources = []
            for value, source, quality, _ in values_list:
                if value not in merged:
                    merged.append(value)
                    sources.append(source)
            return merged if len(merged) > 1 else merged[0] if merged else None, sources
    
    def _add_provenance(self, obj: Any, field_name: str, sources: List[str]) -> None:
        """Add provenance information to object metadata."""
        if not hasattr(obj, "metadata"):
            obj.metadata = {}
        
        if "provenance" not in obj.metadata:
            obj.metadata["provenance"] = {}
        
        obj.metadata["provenance"][field_name] = sources
    
    def _get_quality_score(self, fetch_result: FetchResult) -> float:
        """Calculate overall quality score for a fetch result."""
        if not hasattr(fetch_result, "quality_metrics"):
            return 0.5  # Default mid-range score
        
        metrics = fetch_result.quality_metrics
        return (
            0.25 * metrics.completeness +
            0.30 * metrics.source_reliability +
            0.20 * metrics.consistency +
            0.25 * metrics.validation_status
        )
    
    def _get_object_type(self, obj: Any) -> str:
        """Determine the type of an object."""
        class_name = obj.__class__.__name__.lower()
        if "place" in class_name:
            return "place"
        elif "transition" in class_name:
            return "transition"
        elif "arc" in class_name:
            return "arc"
        else:
            return "unknown"
    
    def _build_object_lookups(
        self,
        pathway: Any,
        object_types: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """Build lookup dictionaries for all object types."""
        lookups = {}
        
        if "place" in object_types and hasattr(pathway, "places"):
            lookups["place"] = {p.id: p for p in pathway.places if hasattr(p, "id")}
        
        if "transition" in object_types and hasattr(pathway, "transitions"):
            lookups["transition"] = {t.id: t for t in pathway.transitions if hasattr(t, "id")}
        
        if "arc" in object_types and hasattr(pathway, "arcs"):
            lookups["arc"] = {a.id: a for a in pathway.arcs if hasattr(a, "id")}
        
        return lookups
    
    def _find_object(self, object_id: str, lookups: Dict[str, Dict[str, Any]]) -> Optional[Any]:
        """Find an object by ID in the lookups."""
        for lookup in lookups.values():
            if object_id in lookup:
                return lookup[object_id]
        return None
    
    def _apply_change(self, pathway: Any, change_dict: Dict[str, Any]) -> None:
        """Apply a change (for rollback)."""
        object_id = change_dict["object_id"]
        property_name = change_dict["property"]
        value = change_dict["value"]
        
        # Find object and apply change
        for collection_name in ["places", "transitions", "arcs"]:
            if hasattr(pathway, collection_name):
                for obj in getattr(pathway, collection_name):
                    if hasattr(obj, "id") and obj.id == object_id:
                        setattr(obj, property_name, value)
                        return
    
    def __repr__(self) -> str:
        """String representation."""
        return (
            f"AnnotationEnricher("
            f"strategy={self.conflict_strategy}, "
            f"merge_multi={self.merge_multi_valued}, "
            f"provenance={self.keep_provenance})"
        )
