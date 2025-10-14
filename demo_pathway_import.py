#!/usr/bin/env python3
"""Demo: Complete pathway import workflow.

This demo shows the complete workflow from pathway ID to rendered Shypn model:
1. User enters pathway ID (e.g., "hsa00010" for glycolysis)
2. CrossFetch fetches data from KEGG/BioModels/Reactome
3. PathwayBuilder converts to Place/Transition/Arc objects
4. Model is ready for rendering/simulation in Shypn

This is the ENTRY POINT workflow - CrossFetch creates new models from scratch.
"""

import sys
sys.path.insert(0, 'src')

import logging
from shypn.crossfetch.core.enrichment_pipeline import EnrichmentPipeline
from shypn.crossfetch.builders.pathway_builder import PathwayBuilder

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(name)s - %(message)s'
)

logger = logging.getLogger(__name__)


def demo_pathway_import(pathway_id: str):
    """Demonstrate complete pathway import workflow.
    
    Args:
        pathway_id: Pathway ID to import (e.g., "hsa00010")
    """
    print("=" * 80)
    print("DEMO: Pathway Import Workflow")
    print("=" * 80)
    print(f"\nImporting pathway: {pathway_id}")
    print("\n" + "=" * 80)
    
    # Step 1: Fetch data from external source
    print("\nStep 1: Fetching pathway data...")
    print("-" * 80)
    
    pipeline = EnrichmentPipeline()
    fetch_results = pipeline.fetch(pathway_id)
    
    if not fetch_results:
        print(f"❌ No data found for pathway '{pathway_id}'")
        return
    
    print(f"✅ Fetched {len(fetch_results)} data sets:")
    for result in fetch_results:
        print(f"   - {result.source}: {result.data_type} (quality: {result.quality_score:.2f})")
    
    # Step 2: Build Petri net model
    print("\n" + "=" * 80)
    print("Step 2: Building Petri net model...")
    print("-" * 80)
    
    builder = PathwayBuilder()
    build_result = builder.build_from_fetch_results(fetch_results)
    
    print(f"✅ Model built successfully:")
    print(f"   - Places (species):     {len(build_result.places)}")
    print(f"   - Transitions (reactions): {len(build_result.transitions)}")
    print(f"   - Arcs (connections):      {len(build_result.arcs)}")
    
    if build_result.warnings:
        print(f"\n⚠️  {len(build_result.warnings)} warnings:")
        for warning in build_result.warnings[:5]:  # Show first 5
            print(f"   - {warning}")
        if len(build_result.warnings) > 5:
            print(f"   ... and {len(build_result.warnings) - 5} more")
    
    # Step 3: Display model details
    print("\n" + "=" * 80)
    print("Step 3: Model details")
    print("-" * 80)
    
    print("\nMetadata:")
    for key, value in build_result.metadata.items():
        print(f"   {key}: {value}")
    
    print("\nSample places (first 5):")
    for i, place in enumerate(list(build_result.places.values())[:5]):
        print(f"   {place.name}: {place.label} (tokens: {place.tokens}, pos: ({place.x:.1f}, {place.y:.1f}))")
    
    print("\nSample transitions (first 5):")
    for i, transition in enumerate(list(build_result.transitions.values())[:5]):
        print(f"   {transition.name}: {transition.label} (rate: {transition.rate}, pos: ({transition.x:.1f}, {transition.y:.1f}))")
    
    print("\nSample arcs (first 5):")
    for i, arc in enumerate(list(build_result.arcs.values())[:5]):
        print(f"   {arc.name}: {arc.source.name} → {arc.target.name} (weight: {arc.weight})")
    
    # Step 4: Show what's next
    print("\n" + "=" * 80)
    print("Step 4: Next steps")
    print("-" * 80)
    print("""
✅ Model is ready for:
   1. Rendering in Shypn canvas
   2. User editing (add/remove/modify objects)
   3. Simulation execution
   4. Saving to .shy file

Next integration steps:
   - Add 'Import from Database' menu item to Shypn UI
   - Create dialog for pathway ID input and source selection
   - Wire PathwayBuilder into main window workflow
   - Save imported model as .shy file
    """)
    
    print("=" * 80)
    print("DEMO COMPLETE")
    print("=" * 80)


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        pathway_id = sys.argv[1]
    else:
        # Default: KEGG glycolysis pathway
        pathway_id = "hsa00010"
    
    demo_pathway_import(pathway_id)
