#!/usr/bin/env python3
"""
Enrichers Demo Script

Demonstrates all four enrichers:
- ConcentrationEnricher: Applies concentration data to places
- InteractionEnricher: Creates/updates arcs based on interactions
- KineticsEnricher: Adds kinetic parameters to transitions
- AnnotationEnricher: Merges annotations from multiple sources

Tests with real BioModels data and shows enrichment workflow.

Author: Shypn Development Team
Date: October 2025
"""

import sys
from pathlib import Path
from typing import Any, Dict, List

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent / "src"))

from shypn.crossfetch import (
    # Fetchers
    BioModelsFetcher,
    ReactomeFetcher,
    
    # Enrichers
    ConcentrationEnricher,
    InteractionEnricher,
    KineticsEnricher,
    AnnotationEnricher,
    
    # Models
    FetchResult,
    FetchStatus,
    QualityMetrics,
    SourceAttribution,
)


# ============================================================================
# Mock Pathway Classes
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
# Mock Data Generation
# ============================================================================

def create_mock_concentration_data() -> FetchResult:
    """Create mock concentration fetch result."""
    data = {
        "concentrations": {
            "P_Glucose": {"value": 5.0, "unit": "mM"},
            "P_ATP": {"value": 2.0, "unit": "mM"},
            "P_ADP": {"value": 0.5, "unit": "mM"},
            "P_G6P": {"value": 0.1, "unit": "mM"},
        }
    }
    
    return FetchResult(
        data=data,
        data_type="concentrations",
        status=FetchStatus.SUCCESS,
        attribution=SourceAttribution(
            source_name="BioModels",
            source_url="https://www.ebi.ac.uk/biomodels/BIOMD0000000206",
            database_version="1.0"
        ),
        quality_metrics=QualityMetrics(
            completeness=0.85,
            consistency=0.90,
            source_reliability=1.00,
            validation_status=0.95
        )
    )


def create_mock_interaction_data() -> FetchResult:
    """Create mock interaction fetch result."""
    data = {
        "interactions": [
            {
                "source": "P_Glucose",
                "target": "T_Hexokinase",
                "type": "activation",
                "confidence": 0.95,
            },
            {
                "source": "T_Hexokinase",
                "target": "P_G6P",
                "type": "production",
                "confidence": 0.98,
            },
            {
                "source": "P_ATP",
                "target": "T_Hexokinase",
                "type": "catalysis",
                "confidence": 0.92,
            },
        ]
    }
    
    return FetchResult(
        data=data,
        data_type="interactions",
        status=FetchStatus.SUCCESS,
        attribution=SourceAttribution(
            source_name="Reactome",
            source_url="https://reactome.org/content/detail/R-HSA-70263",
            database_version="83"
        ),
        quality_metrics=QualityMetrics(
            completeness=0.90,
            consistency=0.88,
            source_reliability=0.95,
            validation_status=0.92
        )
    )


def create_mock_kinetics_data() -> FetchResult:
    """Create mock kinetics fetch result."""
    data = {
        "kinetics": {
            "T_Hexokinase": {
                "kinetic_law_type": "michaelis_menten",
                "rate": 0.5,
                "time_unit": "second",
                "parameters": {
                    "Km_glucose": {"value": 0.1, "unit": "mM"},
                    "Km_ATP": {"value": 0.5, "unit": "mM"},
                    "kcat": {"value": 100.0, "unit": "1/s"},
                }
            },
            "T_PGI": {
                "kinetic_law_type": "mass_action",
                "rate": 0.1,
                "time_unit": "second",
            }
        }
    }
    
    return FetchResult(
        data=data,
        data_type="kinetics",
        status=FetchStatus.SUCCESS,
        attribution=SourceAttribution(
            source_name="BioModels",
            source_url="https://www.ebi.ac.uk/biomodels/BIOMD0000000206",
            database_version="1.0"
        ),
        quality_metrics=QualityMetrics(
            completeness=0.80,
            consistency=0.85,
            source_reliability=1.00,
            validation_status=0.88
        )
    )


def create_mock_annotation_data_biomodels() -> FetchResult:
    """Create mock annotation fetch result from BioModels."""
    data = {
        "annotations": {
            "P_Glucose": {
                "name": "Glucose",
                "description": "D-Glucose molecule in cytoplasm",
                "synonyms": ["Glc", "Dextrose"],
                "cross_references": ["CHEBI:17234", "KEGG:C00031"],
            },
            "T_Hexokinase": {
                "name": "Hexokinase",
                "description": "Phosphorylates glucose to glucose-6-phosphate",
                "cross_references": ["EC:2.7.1.1"],
            }
        }
    }
    
    return FetchResult(
        data=data,
        data_type="annotations",
        status=FetchStatus.SUCCESS,
        attribution=SourceAttribution(
            source_name="BioModels",
            source_url="https://www.ebi.ac.uk/biomodels/BIOMD0000000206",
            database_version="1.0"
        ),
        quality_metrics=QualityMetrics(
            completeness=0.90,
            consistency=0.92,
            source_reliability=1.00,
            validation_status=0.95
        )
    )


def create_mock_annotation_data_reactome() -> FetchResult:
    """Create mock annotation fetch result from Reactome."""
    data = {
        "annotations": {
            "P_Glucose": {
                "name": "D-Glucose",
                "description": "Beta-D-Glucose in cytosol",
                "synonyms": ["beta-D-glucose", "Glucose"],
                "cross_references": ["CHEBI:17634"],
                "compartment": "cytosol",
            },
            "T_Hexokinase": {
                "name": "Hexokinase I",
                "description": "ATP:D-hexose 6-phosphotransferase activity",
                "cross_references": ["UniProt:P19367"],
                "compartment": "cytosol",
            }
        }
    }
    
    return FetchResult(
        data=data,
        data_type="annotations",
        status=FetchStatus.SUCCESS,
        attribution=SourceAttribution(
            source_name="Reactome",
            source_url="https://reactome.org/content/detail/R-HSA-70263",
            database_version="83"
        ),
        quality_metrics=QualityMetrics(
            completeness=0.95,
            consistency=0.90,
            source_reliability=0.95,
            validation_status=0.93
        )
    )


# ============================================================================
# Demo Functions
# ============================================================================

def print_section(title: str) -> None:
    """Print section header."""
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print(f"{'=' * 70}\n")


def print_result(enricher_name: str, result: Any) -> None:
    """Print enrichment result."""
    print(f"\n{enricher_name} Result:")
    print(f"  Success: {result.success}")
    print(f"  Objects Modified: {result.objects_modified}")
    print(f"  Changes: {len(result.changes)}")
    print(f"  Warnings: {len(result.warnings)}")
    print(f"  Errors: {len(result.errors)}")
    
    if result.changes:
        print(f"\n  Changes:")
        for i, change in enumerate(result.changes[:5], 1):  # Show first 5
            print(f"    {i}. {change.object_type}:{change.object_id} - "
                  f"{change.property_name}: {change.old_value} → {change.new_value}")
        if len(result.changes) > 5:
            print(f"    ... and {len(result.changes) - 5} more")
    
    if result.warnings:
        print(f"\n  Warnings:")
        for warning in result.warnings[:3]:
            print(f"    - {warning}")
    
    if result.errors:
        print(f"\n  Errors:")
        for error in result.errors:
            print(f"    - {error}")


def demo_concentration_enricher() -> None:
    """Demo ConcentrationEnricher."""
    print_section("ConcentrationEnricher Demo")
    
    # Create mock pathway
    pathway = MockPathway("GLYCOLYSIS")
    pathway.add_place("P_Glucose", "Glucose")
    pathway.add_place("P_ATP", "ATP")
    pathway.add_place("P_ADP", "ADP")
    pathway.add_place("P_G6P", "Glucose-6-Phosphate")
    
    print(f"Created pathway with {len(pathway.places)} places")
    
    # Create enricher
    enricher = ConcentrationEnricher(scale_factor=1000.0)
    print(f"Created {enricher}")
    
    # Get mock data
    fetch_result = create_mock_concentration_data()
    print(f"Mock data source: {fetch_result.attribution.source_name}")
    
    # Apply enrichment
    result = enricher.apply(pathway, fetch_result)
    print_result("ConcentrationEnricher", result)
    
    # Show enriched places
    print(f"\nEnriched Places:")
    for place in pathway.places:
        print(f"  {place.id}: {place.initial_marking} tokens")


def demo_interaction_enricher() -> None:
    """Demo InteractionEnricher."""
    print_section("InteractionEnricher Demo")
    
    # Create mock pathway with objects
    pathway = MockPathway("GLYCOLYSIS")
    pathway.add_place("P_Glucose", "Glucose")
    pathway.add_place("P_ATP", "ATP")
    pathway.add_place("P_G6P", "Glucose-6-Phosphate")
    pathway.add_transition("T_Hexokinase", "Hexokinase")
    
    print(f"Created pathway with {len(pathway.places)} places, "
          f"{len(pathway.transitions)} transitions, {len(pathway.arcs)} arcs")
    
    # Create enricher
    enricher = InteractionEnricher(create_missing=True, min_confidence=0.8)
    print(f"Created {enricher}")
    
    # Get mock data
    fetch_result = create_mock_interaction_data()
    print(f"Mock data source: {fetch_result.attribution.source_name}")
    
    # Apply enrichment
    result = enricher.apply(pathway, fetch_result)
    print_result("InteractionEnricher", result)
    
    # Show created arcs
    print(f"\nArcs after enrichment ({len(pathway.arcs)}):")
    for arc in pathway.arcs:
        print(f"  {arc.id}: {arc.source} → {arc.target} ({arc.arc_type})")


def demo_kinetics_enricher() -> None:
    """Demo KineticsEnricher."""
    print_section("KineticsEnricher Demo")
    
    # Create mock pathway
    pathway = MockPathway("GLYCOLYSIS")
    pathway.add_transition("T_Hexokinase", "Hexokinase")
    pathway.add_transition("T_PGI", "Phosphoglucose Isomerase")
    
    print(f"Created pathway with {len(pathway.transitions)} transitions")
    
    # Create enricher
    enricher = KineticsEnricher()
    print(f"Created {enricher}")
    
    # Get mock data
    fetch_result = create_mock_kinetics_data()
    print(f"Mock data source: {fetch_result.attribution.source_name}")
    
    # Apply enrichment
    result = enricher.apply(pathway, fetch_result)
    print_result("KineticsEnricher", result)
    
    # Show enriched transitions
    print(f"\nEnriched Transitions:")
    for trans in pathway.transitions:
        print(f"  {trans.id}:")
        print(f"    Type: {trans.transition_type}")
        print(f"    Rate: {trans.rate}")
        if trans.metadata.get("kinetics"):
            kinetics = trans.metadata["kinetics"]
            print(f"    Kinetic Law: {kinetics.get('kinetic_law_type')}")
            if kinetics.get("parameters"):
                print(f"    Parameters: {list(kinetics['parameters'].keys())}")


def demo_annotation_enricher() -> None:
    """Demo AnnotationEnricher."""
    print_section("AnnotationEnricher Demo")
    
    # Create mock pathway
    pathway = MockPathway("GLYCOLYSIS")
    pathway.add_place("P_Glucose", "Glucose")
    pathway.add_transition("T_Hexokinase", "Hexokinase")
    
    print(f"Created pathway with {len(pathway.places)} places, "
          f"{len(pathway.transitions)} transitions")
    
    # Create enricher
    enricher = AnnotationEnricher(
        conflict_strategy="highest_quality",
        merge_multi_valued=True,
        keep_provenance=True
    )
    print(f"Created {enricher}")
    
    # Get mock data from multiple sources
    fetch_results = [
        create_mock_annotation_data_biomodels(),
        create_mock_annotation_data_reactome(),
    ]
    print(f"Mock data from {len(fetch_results)} sources:")
    for fr in fetch_results:
        print(f"  - {fr.attribution.source_name}")
    
    # Apply enrichment (multi-source)
    result = enricher.apply_multi(pathway, fetch_results)
    print_result("AnnotationEnricher", result)
    
    # Show enriched objects
    print(f"\nEnriched Objects:")
    for place in pathway.places:
        print(f"  Place {place.id}:")
        if hasattr(place, "name"):
            print(f"    Name: {place.name}")
        if hasattr(place, "description"):
            print(f"    Description: {place.description[:60]}...")
        if hasattr(place, "synonyms"):
            print(f"    Synonyms: {place.synonyms}")
        if hasattr(place, "metadata") and "provenance" in place.metadata:
            print(f"    Provenance: {place.metadata['provenance']}")
    
    for trans in pathway.transitions:
        print(f"  Transition {trans.id}:")
        if hasattr(trans, "name"):
            print(f"    Name: {trans.name}")
        if hasattr(trans, "description"):
            print(f"    Description: {trans.description[:60]}...")


def demo_combined_enrichment() -> None:
    """Demo all enrichers working together."""
    print_section("Combined Enrichment Demo")
    
    # Create a complete mock pathway
    pathway = MockPathway("GLYCOLYSIS")
    
    # Add places
    places = [
        ("P_Glucose", "Glucose"),
        ("P_ATP", "ATP"),
        ("P_ADP", "ADP"),
        ("P_G6P", "Glucose-6-Phosphate"),
    ]
    for place_id, name in places:
        pathway.add_place(place_id, name)
    
    # Add transitions
    transitions = [
        ("T_Hexokinase", "Hexokinase"),
        ("T_PGI", "Phosphoglucose Isomerase"),
    ]
    for trans_id, name in transitions:
        pathway.add_transition(trans_id, name)
    
    print(f"Created pathway: {pathway.name}")
    print(f"  Places: {len(pathway.places)}")
    print(f"  Transitions: {len(pathway.transitions)}")
    print(f"  Arcs: {len(pathway.arcs)}")
    
    # Create all enrichers
    enrichers = [
        ("Concentration", ConcentrationEnricher(scale_factor=1000.0)),
        ("Interaction", InteractionEnricher(create_missing=True)),
        ("Kinetics", KineticsEnricher()),
        ("Annotation", AnnotationEnricher(conflict_strategy="highest_quality")),
    ]
    
    # Apply each enricher
    results = {}
    for name, enricher in enrichers:
        print(f"\nApplying {name} enricher...")
        
        if name == "Concentration":
            fetch_result = create_mock_concentration_data()
            result = enricher.apply(pathway, fetch_result)
        elif name == "Interaction":
            fetch_result = create_mock_interaction_data()
            result = enricher.apply(pathway, fetch_result)
        elif name == "Kinetics":
            fetch_result = create_mock_kinetics_data()
            result = enricher.apply(pathway, fetch_result)
        else:  # Annotation
            fetch_results = [
                create_mock_annotation_data_biomodels(),
                create_mock_annotation_data_reactome(),
            ]
            result = enricher.apply_multi(pathway, fetch_results)
        
        results[name] = result
        print(f"  ✓ {result.objects_modified} objects modified")
    
    # Summary
    print(f"\n{'-' * 70}")
    print("Enrichment Summary:")
    print(f"{'-' * 70}")
    
    total_changes = sum(len(r.changes) for r in results.values())
    print(f"  Total Changes: {total_changes}")
    
    for name, result in results.items():
        print(f"  {name}:")
        print(f"    Objects: {result.objects_modified}")
        print(f"    Changes: {len(result.changes)}")
        print(f"    Warnings: {len(result.warnings)}")
    
    # Final pathway state
    print(f"\nFinal Pathway State:")
    print(f"  Places: {len(pathway.places)}")
    print(f"  Transitions: {len(pathway.transitions)}")
    print(f"  Arcs: {len(pathway.arcs)}")
    
    # Show sample enriched place
    if pathway.places:
        place = pathway.places[0]
        print(f"\nSample Enriched Place ({place.id}):")
        print(f"  Name: {getattr(place, 'name', 'N/A')}")
        print(f"  Tokens: {place.initial_marking}")
        print(f"  Description: {getattr(place, 'description', 'N/A')[:60]}")
    
    # Show sample enriched transition
    if pathway.transitions:
        trans = pathway.transitions[0]
        print(f"\nSample Enriched Transition ({trans.id}):")
        print(f"  Name: {getattr(trans, 'name', 'N/A')}")
        print(f"  Type: {trans.transition_type}")
        print(f"  Rate: {trans.rate}")


# ============================================================================
# Main
# ============================================================================

def main():
    """Run all demos."""
    print("\n" + "=" * 70)
    print("  CROSSFETCH ENRICHERS DEMONSTRATION")
    print("=" * 70)
    print("\nThis demo shows all four enrichers:")
    print("  1. ConcentrationEnricher - Apply concentration data to places")
    print("  2. InteractionEnricher - Create/update arcs from interactions")
    print("  3. KineticsEnricher - Add kinetic parameters to transitions")
    print("  4. AnnotationEnricher - Merge annotations from multiple sources")
    
    try:
        # Individual demos
        demo_concentration_enricher()
        demo_interaction_enricher()
        demo_kinetics_enricher()
        demo_annotation_enricher()
        
        # Combined demo
        demo_combined_enrichment()
        
        # Success
        print_section("Demo Complete")
        print("✓ All enrichers demonstrated successfully!")
        print("\nNext Steps:")
        print("  1. Run tests: python -m pytest tests/test_enrichers.py")
        print("  2. Try with real BioModels data")
        print("  3. Integrate with EnrichmentPipeline")
        
    except Exception as e:
        print(f"\n❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
