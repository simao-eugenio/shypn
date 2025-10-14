#!/usr/bin/env python3
"""Demo: SBML Enrichment PRE-Processing Workflow.

This demonstrates the CORRECT architecture:

1. Fetch SBML from BioModels (primary source - has structure)
2. PRE-PROCESS with CrossFetch (enrich missing data)
3. POST-PROCESS with existing Shypn converters (SBML → Petri net)

This is NOT a replacement for SBML import - it's a PRE-processor!
"""

import sys
sys.path.insert(0, 'src')

import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(name)s - %(message)s'
)

logger = logging.getLogger(__name__)


def demo_sbml_enrichment(pathway_id: str):
    """Demonstrate SBML enrichment PRE-processing.
    
    Args:
        pathway_id: Pathway ID (e.g., "BIOMD0000000002" or "hsa00010")
    """
    print("=" * 80)
    print("DEMO: SBML Enrichment PRE-Processing")
    print("=" * 80)
    print(f"\nPathway ID: {pathway_id}")
    print("\nArchitecture:")
    print("  1. Fetch SBML from BioModels (primary source)")
    print("  2. CrossFetch PRE-processing (enrich missing data) ← THIS DEMO")
    print("  3. Existing POST-processing (SBML → Shypn model)")
    print("\n" + "=" * 80)
    
    # Import enricher
    from shypn.crossfetch.sbml_enricher import SBMLEnricher
    
    # Step 1: Create enricher
    print("\nStep 1: Creating SBML enricher...")
    print("-" * 80)
    
    enricher = SBMLEnricher(
        fetch_sources=["KEGG", "Reactome"],
        enrich_concentrations=True,
        enrich_kinetics=True,
        enrich_annotations=True
    )
    print("✅ Enricher created")
    print(f"   Sources: KEGG, Reactome")
    print(f"   Will enrich: concentrations, kinetics, annotations")
    
    # Step 2: Fetch and enrich SBML
    print("\n" + "=" * 80)
    print("Step 2: Fetching and enriching SBML...")
    print("-" * 80)
    
    try:
        enriched_sbml = enricher.enrich_by_pathway_id(pathway_id)
        
        print("✅ SBML enriched successfully")
        print(f"   Enriched SBML size: {len(enriched_sbml)} characters")
        
        # Show snippet of enriched SBML
        print("\n   First 500 characters of enriched SBML:")
        print("   " + "-" * 76)
        for line in enriched_sbml[:500].split('\n')[:10]:
            print(f"   {line}")
        print("   " + "-" * 76)
        
    except Exception as e:
        print(f"❌ Enrichment failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Step 3: What happens next
    print("\n" + "=" * 80)
    print("Step 3: Next steps (POST-processing)")
    print("-" * 80)
    print("""
The enriched SBML is now ready for the EXISTING Shypn import flow:

1. SBMLParser parses enriched SBML
   - Extracts species (now with concentrations!)
   - Extracts reactions (now with kinetics!)
   - Extracts annotations (now complete!)

2. PathwayConverter converts to Shypn objects
   - Species → Places (with initial tokens from concentrations)
   - Reactions → Transitions (with rates from kinetics)
   - Stoichiometry → Arcs

3. PathwayPostProcessor applies layout and refinements
   - Auto-layout algorithm
   - Arc routing
   - Visual polish

4. Final Shypn model is ready for rendering/simulation

This enrichment is TRANSPARENT to the existing code!
The parsers/converters see richer SBML data but don't need changes.
    """)
    
    print("=" * 80)
    print("DEMO COMPLETE")
    print("=" * 80)
    print(f"\nSummary:")
    print(f"  • SBML fetched from BioModels: ✅")
    print(f"  • Missing data fetched from KEGG/Reactome: ✅")
    print(f"  • Data merged into SBML: ✅")
    print(f"  • Ready for existing parsers: ✅")
    print()


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        pathway_id = sys.argv[1]
    else:
        # Default: BioModels glycolysis model
        pathway_id = "BIOMD0000000206"  # Teusink2000 - Glycolysis model
    
    demo_sbml_enrichment(pathway_id)
