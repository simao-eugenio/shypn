#!/usr/bin/env python3
"""
End-to-End CrossFetch Demo

Demonstrates complete workflow:
1. Fetch data from multiple sources (KEGG, BioModels, Reactome)
2. Score quality and select best sources
3. Apply enrichments to pathway objects using enrichers
4. Show results and statistics

This demo uses mock pathway objects for demonstration.
In production, you would load actual .shy files.

Author: Shypn Development Team
Date: October 2025
"""

import sys
from pathlib import Path
from typing import Any, Dict, List

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent / "src"))

from shypn.crossfetch import (
    # Core
    EnrichmentPipeline,
    
    # Models
    EnrichmentRequest,
    DataType,
    FetchStatus,
    
    # For demo: direct access to enrichers for standalone testing
    ConcentrationEnricher,
    InteractionEnricher,
    KineticsEnricher,
    AnnotationEnricher,
)


# ============================================================================
# Mock Pathway Classes (Same as demo_enrichers.py)
# ============================================================================

class MockPlace:
    """Mock place for testing."""
    def __init__(self, place_id: str, name: str = ""):
        self.id = place_id
        self.name = name
        self.initial_marking = 0
        self.metadata = {}


class MockTransition:
    """Mock transition for testing."""
    def __init__(self, trans_id: str, name: str = ""):
        self.id = trans_id
        self.name = name
        self.transition_type = "immediate"
        self.rate = None
        self.metadata = {}


class MockArc:
    """Mock arc for testing."""
    def __init__(self, arc_id: str, source_id: str, target_id: str):
        self.id = arc_id
        self.source = source_id
        self.target = target_id
        self.weight = 1
        self.arc_type = "normal"
        self.metadata = {}


class MockPathway:
    """Mock pathway for testing."""
    def __init__(self, pathway_id: str):
        self.id = pathway_id
        self.name = f"Test Pathway {pathway_id}"
        self.places = []
        self.transitions = []
        self.arcs = []
        self.metadata = {}
    
    def add_place(self, place_id: str, name: str = "") -> MockPlace:
        """Add a place."""
        place = MockPlace(place_id, name)
        self.places.append(place)
        return place
    
    def add_transition(self, trans_id: str, name: str = "") -> MockTransition:
        """Add a transition."""
        trans = MockTransition(trans_id, name)
        self.transitions.append(trans)
        return trans
    
    def add_arc(self, arc_id: str, source_id: str, target_id: str) -> MockArc:
        """Add an arc."""
        arc = MockArc(arc_id, source_id, target_id)
        self.arcs.append(arc)
        return arc


# ============================================================================
# Demo Functions
# ============================================================================

def print_section(title: str) -> None:
    """Print section header."""
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print(f"{'=' * 70}\n")


def create_glycolysis_pathway() -> MockPathway:
    """Create a mock glycolysis pathway."""
    pathway = MockPathway("GLYCOLYSIS")
    pathway.name = "Glycolysis Pathway"
    
    # Add key places
    places = [
        ("P_Glucose", "Glucose"),
        ("P_G6P", "Glucose-6-Phosphate"),
        ("P_F6P", "Fructose-6-Phosphate"),
        ("P_FBP", "Fructose-1,6-Bisphosphate"),
        ("P_ATP", "ATP"),
        ("P_ADP", "ADP"),
        ("P_NAD", "NAD+"),
        ("P_NADH", "NADH"),
    ]
    
    for place_id, name in places:
        pathway.add_place(place_id, name)
    
    # Add key transitions
    transitions = [
        ("T_Hexokinase", "Hexokinase"),
        ("T_PGI", "Phosphoglucose Isomerase"),
        ("T_PFK", "Phosphofructokinase"),
        ("T_Aldolase", "Aldolase"),
        ("T_GAPDH", "Glyceraldehyde-3-phosphate Dehydrogenase"),
    ]
    
    for trans_id, name in transitions:
        pathway.add_transition(trans_id, name)
    
    # Add some basic arcs
    arcs = [
        ("A1", "P_Glucose", "T_Hexokinase"),
        ("A2", "T_Hexokinase", "P_G6P"),
        ("A3", "P_G6P", "T_PGI"),
        ("A4", "T_PGI", "P_F6P"),
    ]
    
    for arc_id, source, target in arcs:
        pathway.add_arc(arc_id, source, target)
    
    return pathway


def demo_pipeline_basic():
    """Demo basic pipeline setup."""
    print_section("Pipeline Basic Setup")
    
    # Create pipeline
    pipeline = EnrichmentPipeline()
    
    print(f"Pipeline created: {pipeline}")
    print(f"\nRegistered fetchers: {list(pipeline.fetchers.keys())}")
    print(f"Registered enrichers: {list(pipeline.enrichers.keys())}")
    print(f"Available sources: {pipeline.get_available_sources()}")
    
    # Show enricher capabilities
    print(f"\nEnricher Capabilities:")
    for name, enricher in pipeline.enrichers.items():
        data_types = enricher.get_supported_data_types()
        print(f"  {name}: {', '.join(data_types)}")


def demo_enrichment_request():
    """Demo creating enrichment requests."""
    print_section("Enrichment Request Creation")
    
    # Simple request
    request1 = EnrichmentRequest.create_simple(
        pathway_id="hsa00010",
        data_types=["concentrations", "kinetics"]
    )
    
    print(f"Simple Request:")
    print(f"  Pathway: {request1.pathway_id}")
    print(f"  Data Types: {[dt.value for dt in request1.get_data_types()]}")
    print(f"  Min Quality: {request1.min_quality_score}")
    
    # Full request
    request2 = EnrichmentRequest(
        pathway_id="BIOMD0000000206",
        data_types=[
            DataType.CONCENTRATIONS,
            DataType.KINETICS,
            DataType.INTERACTIONS,
            DataType.ANNOTATIONS
        ],
        min_quality_score=0.7,
        preferred_sources=["BioModels", "Reactome"]
    )
    
    print(f"\nFull Request:")
    print(f"  Pathway: {request2.pathway_id}")
    print(f"  Data Types: {[dt.value for dt in request2.get_data_types()]}")
    print(f"  Min Quality: {request2.min_quality_score}")
    print(f"  Preferred Sources: {request2.preferred_sources}")


def demo_end_to_end_enrichment():
    """Demo complete end-to-end enrichment workflow."""
    print_section("End-to-End Enrichment Workflow")
    
    # Create pathway
    pathway = create_glycolysis_pathway()
    print(f"Created pathway: {pathway.name}")
    print(f"  Places: {len(pathway.places)}")
    print(f"  Transitions: {len(pathway.transitions)}")
    print(f"  Arcs: {len(pathway.arcs)}")
    
    # Create pipeline
    pipeline = EnrichmentPipeline()
    print(f"\nPipeline: {pipeline}")
    
    # Create enrichment request
    # Note: We're using a BioModels ID that the fetcher will try to fetch
    # For demo purposes, this may fail but will show the workflow
    request = EnrichmentRequest.create_simple(
        pathway_id="BIOMD0000000206",  # Glycolysis model
        data_types=["concentrations", "kinetics", "annotations"]
    )
    
    print(f"\nEnrichment Request:")
    print(f"  Pathway: {request.pathway_id}")
    print(f"  Data Types: {[dt.value for dt in request.get_data_types()]}")
    
    # Mock pathway file
    pathway_file = Path("/tmp/mock_glycolysis.shy")
    
    print(f"\nFetching data from sources...")
    print(f"(This may take a few seconds...)")
    
    # Run enrichment (with pathway object)
    results = pipeline.enrich(
        pathway_file=pathway_file,
        request=request,
        pathway_object=pathway
    )
    
    # Display results
    print(f"\n{'-' * 70}")
    print(f"Enrichment Results:")
    print(f"{'-' * 70}")
    
    print(f"\nPathway: {results['pathway_id']}")
    print(f"File: {results['pathway_file']}")
    
    if results['errors']:
        print(f"\nErrors: {len(results['errors'])}")
        for error in results['errors']:
            print(f"  - {error}")
    
    print(f"\nFetch Results:")
    for enrichment in results['enrichments']:
        print(f"\n  Data Type: {enrichment['data_type']}")
        print(f"    Sources Queried: {enrichment['sources_queried']}")
        print(f"    Sources Successful: {enrichment['sources_successful']}")
        print(f"    Best Source: {enrichment['best_source']}")
        print(f"    Quality Score: {enrichment['quality_score']:.2f}")
        
        if enrichment['errors']:
            print(f"    Errors:")
            for error in enrichment['errors']:
                print(f"      - {error}")
    
    print(f"\nApplied Enrichments:")
    for applied in results.get('applied_enrichments', []):
        print(f"\n  Data Type: {applied['data_type']}")
        print(f"    Enricher: {applied['enricher_used']}")
        print(f"    Success: {applied['success']}")
        print(f"    Objects Modified: {applied['objects_modified']}")
        print(f"    Changes: {len(applied['changes'])}")
        
        if applied['changes']:
            print(f"    Sample Changes:")
            for change in applied['changes'][:3]:
                print(f"      - {change['object_type']}:{change['object_id']}")
                print(f"        {change['property']}: {change['old_value']} → {change['new_value']}")
        
        if applied['warnings']:
            print(f"    Warnings: {len(applied['warnings'])}")
        
        if applied['errors']:
            print(f"    Errors:")
            for error in applied['errors']:
                print(f"      - {error}")
    
    print(f"\nStatistics:")
    stats = results.get('statistics', {})
    if stats:
        print(f"  Total Enrichments: {stats.get('total_enrichments', 0)}")
        print(f"  Successful: {stats.get('successful_enrichments', 0)}")
        print(f"  Failed: {stats.get('failed_enrichments', 0)}")
        print(f"  Success Rate: {stats.get('success_rate', 0.0):.1%}")
    else:
        print(f"  No statistics available")
    
    # Show final pathway state
    print(f"\nFinal Pathway State:")
    print(f"  Places: {len(pathway.places)}")
    print(f"  Transitions: {len(pathway.transitions)}")
    print(f"  Arcs: {len(pathway.arcs)}")
    
    # Show sample enriched objects
    if pathway.places:
        place = pathway.places[0]
        print(f"\n  Sample Place ({place.id}):")
        print(f"    Name: {place.name}")
        print(f"    Tokens: {place.initial_marking}")
        if hasattr(place, 'description'):
            print(f"    Description: {getattr(place, 'description', 'N/A')[:60]}")
    
    if pathway.transitions:
        trans = pathway.transitions[0]
        print(f"\n  Sample Transition ({trans.id}):")
        print(f"    Name: {trans.name}")
        print(f"    Type: {trans.transition_type}")
        print(f"    Rate: {trans.rate}")


def demo_custom_configuration():
    """Demo custom pipeline configuration."""
    print_section("Custom Pipeline Configuration")
    
    # Create pipeline
    pipeline = EnrichmentPipeline()
    
    print(f"Default configuration:")
    print(f"  Fetchers: {list(pipeline.fetchers.keys())}")
    print(f"  Enrichers: {list(pipeline.enrichers.keys())}")
    
    # Remove default enrichers
    for name in list(pipeline.enrichers.keys()):
        pipeline.unregister_enricher(name)
    
    print(f"\nAfter removing enrichers:")
    print(f"  Enrichers: {list(pipeline.enrichers.keys())}")
    
    # Add custom enrichers with specific config
    pipeline.register_enricher(
        ConcentrationEnricher(
            scale_factor=10000.0,  # Higher scale
            min_tokens=1,
            max_tokens=100000
        )
    )
    
    pipeline.register_enricher(
        InteractionEnricher(
            create_missing=False,  # Don't create new arcs
            update_existing=True,
            min_confidence=0.9  # Higher threshold
        )
    )
    
    print(f"\nWith custom enrichers:")
    print(f"  Enrichers: {list(pipeline.enrichers.keys())}")
    
    print(f"\nCustom enricher configs:")
    for name, enricher in pipeline.enrichers.items():
        print(f"  {name}: {enricher}")


# ============================================================================
# Main
# ============================================================================

def main():
    """Run all demos."""
    print("\n" + "=" * 70)
    print("  CROSSFETCH END-TO-END DEMONSTRATION")
    print("=" * 70)
    print("\nThis demo shows the complete CrossFetch workflow:")
    print("  1. Pipeline setup with fetchers and enrichers")
    print("  2. Creating enrichment requests")
    print("  3. Fetching data from multiple sources")
    print("  4. Quality scoring and source selection")
    print("  5. Applying enrichments to pathway objects")
    print("  6. Viewing results and statistics")
    
    try:
        # Individual demos
        demo_pipeline_basic()
        demo_enrichment_request()
        demo_custom_configuration()
        
        # Main demo
        demo_end_to_end_enrichment()
        
        # Success
        print_section("Demo Complete")
        print("✓ End-to-end workflow demonstrated successfully!")
        print("\nKey Features Demonstrated:")
        print("  • Pipeline with multiple fetchers and enrichers")
        print("  • Automatic source selection based on quality")
        print("  • Data application to pathway objects")
        print("  • Change tracking and reporting")
        print("  • Error handling and warnings")
        print("\nNext Steps:")
        print("  1. Try with real .shy pathway files")
        print("  2. Test with actual BioModels IDs")
        print("  3. Experiment with different enricher configurations")
        print("  4. Review enrichment metadata")
        
    except Exception as e:
        print(f"\n❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
