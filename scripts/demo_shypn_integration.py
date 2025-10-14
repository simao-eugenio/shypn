#!/usr/bin/env python3
"""Demo: CrossFetch integration with real Shypn classes.

This demo shows how CrossFetch enrichers work with actual Shypn Place
and Transition objects (not mocks).

Example workflow:
    1. Create Shypn pathway objects (Place, Transition)
    2. Wrap in ShypnPathwayAdapter
    3. Use CrossFetch enrichers to enrich
    4. Verify enrichment worked

Next step: Load/save .shy files
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))

from shypn.netobjs.place import Place
from shypn.netobjs.transition import Transition
from shypn.crossfetch.adapters.shypn_adapter import ShypnPathwayAdapter
from shypn.crossfetch.enrichers.concentration_enricher import ConcentrationEnricher
from shypn.crossfetch.enrichers.kinetics_enricher import KineticsEnricher
from shypn.crossfetch.models.fetch_result import (
    FetchResult, FetchStatus, QualityMetrics, SourceAttribution
)


def create_simple_pathway():
    """Create a simple pathway with real Shypn objects."""
    print("=" * 60)
    print("Creating Simple Pathway (Real Shypn Objects)")
    print("=" * 60)
    
    # Create places (species)
    glucose = Place(x=100, y=100, id=1, name="P1", label="Glucose")
    glucose.tokens = 10
    glucose.initial_marking = 10
    
    g6p = Place(x=300, y=100, id=2, name="P2", label="Glucose-6-P")
    g6p.tokens = 0
    g6p.initial_marking = 0
    
    atp = Place(x=100, y=200, id=3, name="P3", label="ATP")
    atp.tokens = 100
    atp.initial_marking = 100
    
    adp = Place(x=300, y=200, id=4, name="P4", label="ADP")
    adp.tokens = 0
    adp.initial_marking = 0
    
    places = [glucose, g6p, atp, adp]
    
    # Create transition (reaction)
    hexokinase = Transition(x=200, y=150, id=1, name="T1", label="Hexokinase")
    hexokinase.transition_type = 'continuous'
    hexokinase.rate = 1.0
    
    transitions = [hexokinase]
    
    # No arcs for this simple demo
    arcs = []
    
    print(f"Created {len(places)} places:")
    for place in places:
        print(f"  - {place.name} ({place.label}): {place.tokens} tokens")
    
    print(f"\nCreated {len(transitions)} transitions:")
    for trans in transitions:
        print(f"  - {trans.name} ({trans.label}): type={trans.transition_type}, rate={trans.rate}")
    
    return places, transitions, arcs


def test_concentration_enrichment():
    """Test concentration enricher with real Shypn objects."""
    print("\n" + "=" * 60)
    print("Test 1: Concentration Enrichment")
    print("=" * 60)
    
    # Create pathway
    places, transitions, arcs = create_simple_pathway()
    
    # Create adapter
    adapter = ShypnPathwayAdapter(
        places=places,
        transitions=transitions,
        arcs=arcs,
        pathway_id="test_pathway"
    )
    
    print(f"\nAdapter: {adapter}")
    
    # Create proper FetchResult object (simulating BioModels data)
    concentration_data = {
        'concentrations': {
            'Glucose': {'value': 5.5, 'unit': 'mM'},  # 5.5 mM glucose
            'ATP': {'value': 3.0, 'unit': 'mM'},      # 3.0 mM ATP
            'Glucose-6-P': {'value': 0.8, 'unit': 'mM'}  # 0.8 mM G6P
        }
    }
    
    fetch_result = FetchResult(
        data=concentration_data,
        data_type='concentrations',
        status=FetchStatus.SUCCESS,
        quality_metrics=QualityMetrics(
            completeness=1.0,
            source_reliability=0.95,
            consistency=0.9,
            validation_status=1.0
        ),
        attribution=SourceAttribution(
            source_name='BioModels',
            source_url='https://www.ebi.ac.uk/biomodels/',
            database_version='v32'
        ),
        fields_filled=['concentrations'],
        fields_missing=[]
    )
    
    print("\nMock concentration data:")
    for species, data in concentration_data['concentrations'].items():
        print(f"  - {species}: {data['value']} {data['unit']}")
    
    # Apply concentration enricher
    print("\nApplying ConcentrationEnricher...")
    enricher = ConcentrationEnricher()
    
    try:
        result = enricher.apply(adapter, fetch_result)
        
        if result.success:
            print(f"✓ Enrichment successful!")
            print(f"  - Modified {result.objects_modified} objects")
            print(f"  - Applied {len(result.changes)} changes")
            
            # Show token changes
            print("\nToken changes:")
            for place in places:
                print(f"  - {place.name} ({place.label}): {place.tokens} tokens")
        else:
            print(f"✗ Enrichment failed: {result.error}")
    except Exception as e:
        print(f"✗ Exception during enrichment: {e}")
        import traceback
        traceback.print_exc()


def test_kinetics_enrichment():
    """Test kinetics enricher with real Shypn objects."""
    print("\n" + "=" * 60)
    print("Test 2: Kinetics Enrichment")
    print("=" * 60)
    
    # Create pathway
    places, transitions, arcs = create_simple_pathway()
    
    # Create adapter
    adapter = ShypnPathwayAdapter(
        places=places,
        transitions=transitions,
        arcs=arcs,
        pathway_id="test_pathway"
    )
    
    # Create proper FetchResult object (simulating KEGG kinetic data)
    kinetic_data = {
        'kinetics': {
            'Hexokinase': {
                'law_type': 'michaelis_menten',
                'kcat': 150.0,  # s^-1
                'Km_glucose': 0.1,  # mM
                'Km_ATP': 0.5  # mM
            }
        }
    }
    
    fetch_result = FetchResult(
        data=kinetic_data,
        data_type='kinetics',
        status=FetchStatus.SUCCESS,
        quality_metrics=QualityMetrics(
            completeness=0.8,
            source_reliability=0.9,
            consistency=0.85,
            validation_status=1.0
        ),
        attribution=SourceAttribution(
            source_name='KEGG',
            source_url='https://www.kegg.jp/',
            database_version='release_101'
        ),
        fields_filled=['kinetics'],
        fields_missing=[]
    )
    
    print("\nMock kinetic data:")
    for enzyme, params in kinetic_data['kinetics'].items():
        print(f"  - {enzyme}:")
        for param, value in params.items():
            print(f"    * {param}: {value}")
    
    # Apply kinetics enricher
    print("\nApplying KineticsEnricher...")
    enricher = KineticsEnricher()
    
    try:
        result = enricher.apply(adapter, fetch_result)
        
        if result.success:
            print(f"✓ Enrichment successful!")
            print(f"  - Modified {result.objects_modified} objects")
            print(f"  - Applied {len(result.changes)} changes")
            
            # Show rate changes
            print("\nRate changes:")
            for trans in transitions:
                print(f"  - {trans.name} ({trans.label}): rate={trans.rate}")
                if hasattr(trans, 'properties'):
                    print(f"    Properties: {trans.properties}")
        else:
            print(f"✗ Enrichment failed: {result.error}")
    except Exception as e:
        print(f"✗ Exception during enrichment: {e}")
        import traceback
        traceback.print_exc()


def test_adapter_methods():
    """Test adapter helper methods."""
    print("\n" + "=" * 60)
    print("Test 3: Adapter Helper Methods")
    print("=" * 60)
    
    # Create pathway
    places, transitions, arcs = create_simple_pathway()
    
    # Create adapter
    adapter = ShypnPathwayAdapter(
        places=places,
        transitions=transitions,
        arcs=arcs,
        pathway_id="test_pathway"
    )
    
    # Test lookups by ID
    print("\nTest: Get place by ID")
    place = adapter.get_place_by_id(1)
    print(f"  - Place ID 1: {place.name} ({place.label})" if place else "  - Not found")
    
    # Test lookups by name
    print("\nTest: Get transition by name")
    trans = adapter.get_transition_by_name("T1")
    print(f"  - Transition T1: {trans.label}" if trans else "  - Not found")
    
    # Test label search
    print("\nTest: Find place by label")
    place = adapter.find_place_by_label("glucose")
    print(f"  - Search 'glucose': {place.name} ({place.label})" if place else "  - Not found")
    
    place = adapter.find_place_by_label("ATP")
    print(f"  - Search 'ATP': {place.name} ({place.label})" if place else "  - Not found")
    
    # Test serialization
    print("\nTest: Serialization to dict")
    data = adapter.to_dict()
    print(f"  - Serialized pathway_id: {data['pathway_id']}")
    print(f"  - Places: {len(data['places'])}")
    print(f"  - Transitions: {len(data['transitions'])}")
    print(f"  - Arcs: {len(data['arcs'])}")


def main():
    """Run all integration tests."""
    print("CrossFetch + Shypn Integration Demo")
    print("=" * 60)
    print("This demo tests CrossFetch enrichers with real Shypn objects")
    print()
    
    # Run tests
    test_concentration_enrichment()
    test_kinetics_enrichment()
    test_adapter_methods()
    
    print("\n" + "=" * 60)
    print("Integration Demo Complete!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("  1. ✓ Adapter working with real Shypn objects")
    print("  2. TODO: Test with .shy file loading/saving")
    print("  3. TODO: Create UI integration (menu items, dialogs)")
    print("  4. TODO: CLI tool for batch enrichment")


if __name__ == '__main__':
    main()
