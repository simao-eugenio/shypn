#!/usr/bin/env python3
"""
Cross-Fetch System - Demo Example

Demonstrates the complete cross-fetch enrichment workflow.

Author: Shypn Development Team
Date: October 2025
"""

from pathlib import Path
import sys
import json

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from shypn.crossfetch import (
    EnrichmentPipeline,
    EnrichmentRequest,
    DataType,
    QualityScorer,
    KEGGFetcher
)


def print_section(title):
    """Print section header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)


def demo_basic_enrichment():
    """Demonstrate basic enrichment workflow."""
    print_section("Basic Enrichment Workflow")
    
    # Create pipeline
    pipeline = EnrichmentPipeline()
    print(f"\n✅ Created enrichment pipeline")
    print(f"   Registered sources: {', '.join(pipeline.fetchers.keys())}")
    
    # Create simple enrichment request
    request = EnrichmentRequest.create_simple(
        pathway_id="hsa00010",
        data_types=["coordinates", "annotations"]
    )
    print(f"\n✅ Created enrichment request")
    print(f"   Pathway: {request.pathway_id}")
    print(f"   Data types: {[dt.value for dt in request.data_types]}")
    
    # Simulate enrichment (using demo pathway file)
    pathway_file = Path("demo_glycolysis.shy")
    results = pipeline.enrich(pathway_file, request)
    
    print(f"\n✅ Enrichment completed")
    print(f"   Total enrichments: {len(results['enrichments'])}")
    
    for enrichment in results['enrichments']:
        print(f"\n   Data type: {enrichment['data_type']}")
        print(f"   Sources queried: {enrichment['sources_queried']}")
        print(f"   Best source: {enrichment['best_source']}")
        print(f"   Quality score: {enrichment['quality_score']:.2f}")
        print(f"   Fields enriched: {enrichment['fields_enriched']}")


def demo_quality_scoring():
    """Demonstrate quality scoring system."""
    print_section("Quality Scoring System")
    
    from shypn.crossfetch.models import FetchResult, QualityMetrics, SourceAttribution
    
    # Create sample fetch results
    results = [
        FetchResult(
            data={"species": [{"x": 100, "y": 200}]},
            data_type="coordinates",
            status="success",
            quality_metrics=QualityMetrics(
                completeness=0.8,
                source_reliability=0.85,
                consistency=0.9,
                validation_status=0.95
            ),
            attribution=SourceAttribution(source_name="KEGG"),
            fields_filled=["species[0].x", "species[0].y"]
        ),
        FetchResult(
            data={"species": [{"x": 105, "y": 205}]},
            data_type="coordinates",
            status="success",
            quality_metrics=QualityMetrics(
                completeness=0.7,
                source_reliability=0.95,
                consistency=0.8,
                validation_status=0.9
            ),
            attribution=SourceAttribution(source_name="BioModels"),
            fields_filled=["species[0].x", "species[0].y"]
        )
    ]
    
    print(f"\n✅ Created {len(results)} sample fetch results")
    
    # Score results
    scorer = QualityScorer()
    scores = scorer.score_results(results)
    
    print(f"\n✅ Quality scores calculated:")
    for i, (result, score) in enumerate(zip(results, scores), 1):
        print(f"   {i}. {result.attribution.source_name}: {score:.3f}")
    
    # Get best result
    best = scorer.get_best_result(results)
    if best:
        print(f"\n✅ Best result: {best.attribution.source_name}")
        print(f"   Quality score: {best.get_quality_score():.3f}")


def demo_fetcher_system():
    """Demonstrate fetcher system."""
    print_section("Fetcher System")
    
    # Create KEGG fetcher
    kegg = KEGGFetcher()
    print(f"\n✅ Created KEGG fetcher")
    print(f"   Source: {kegg.source_name}")
    print(f"   Reliability: {kegg.source_reliability}")
    print(f"   Supported data types: {kegg.get_supported_data_types()}")
    
    # Test fetch
    print(f"\n✅ Testing fetch operation...")
    result = kegg.fetch(
        pathway_id="hsa00010",
        data_type="coordinates"
    )
    
    print(f"   Status: {result.status.value}")
    print(f"   Quality score: {result.get_quality_score():.3f}")
    print(f"   Fields filled: {result.fields_filled}")
    print(f"   Fetch duration: {result.fetch_duration_ms:.2f}ms")


def demo_enrichment_request():
    """Demonstrate enrichment request configuration."""
    print_section("Enrichment Request Configuration")
    
    # Create detailed request
    request = EnrichmentRequest(
        pathway_id="hsa00010",
        data_types=[DataType.COORDINATES, DataType.CONCENTRATIONS],
        preferred_sources=["KEGG", "BioModels"],
        min_quality_score=0.7,
        max_sources_per_field=2,
        allow_partial_results=True
    )
    
    print(f"\n✅ Created enrichment request")
    print(f"   Pathway: {request.pathway_id}")
    print(f"   Data types: {[dt.value for dt in request.data_types]}")
    print(f"   Preferred sources: {request.preferred_sources}")
    print(f"   Min quality: {request.min_quality_score}")
    print(f"   Max sources per field: {request.max_sources_per_field}")
    
    # Check data types
    types_to_enrich = request.get_data_types()
    print(f"\n✅ Data types to enrich: {[dt.value for dt in types_to_enrich]}")
    
    # Check source allowance
    test_sources = ["KEGG", "BioModels", "Reactome"]
    print(f"\n✅ Source allowance:")
    for source in test_sources:
        allowed = request.is_source_allowed(source)
        status = "✓" if allowed else "✗"
        print(f"   {status} {source}")


def demo_pipeline_statistics():
    """Demonstrate pipeline statistics."""
    print_section("Pipeline Statistics")
    
    pipeline = EnrichmentPipeline()
    
    # Simulate multiple enrichments
    for i in range(3):
        request = EnrichmentRequest.create_simple(
            pathway_id=f"hsa0001{i}",
            data_types=["coordinates"]
        )
        pathway_file = Path(f"demo_pathway_{i}.shy")
        results = pipeline.enrich(pathway_file, request)
    
    # Get statistics
    stats = pipeline._get_statistics()
    
    print(f"\n✅ Pipeline statistics:")
    print(f"   Total enrichments: {stats['total_enrichments']}")
    print(f"   Successful: {stats['successful_enrichments']}")
    print(f"   Failed: {stats['failed_enrichments']}")
    print(f"   Success rate: {stats['success_rate']:.1%}")
    print(f"   Registered sources: {stats['registered_sources']}")
    print(f"   Available sources: {stats['available_sources']}")


def main():
    """Run all demos."""
    print("\n" + "="*60)
    print("  CROSS-FETCH ENRICHMENT SYSTEM - DEMO")
    print("="*60)
    print("\nDemonstrating the complete cross-fetch workflow.")
    
    try:
        # Run demos
        demo_basic_enrichment()
        demo_quality_scoring()
        demo_fetcher_system()
        demo_enrichment_request()
        demo_pipeline_statistics()
        
        # Summary
        print_section("Demo Complete")
        print("\n✅ All demos completed successfully!")
        print("\nKey Features Demonstrated:")
        print("  • Multi-source data fetching")
        print("  • Quality-based scoring and ranking")
        print("  • Enrichment pipeline orchestration")
        print("  • Flexible request configuration")
        print("  • Pipeline statistics tracking")
        print("\nNext Steps:")
        print("  • Implement additional fetchers (BioModels, Reactome, etc.)")
        print("  • Add conflict resolution strategies")
        print("  • Implement caching system")
        print("  • Add rate limiting")
        print("  • Create unit tests")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
