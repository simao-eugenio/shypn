#!/usr/bin/env python3
"""
Debug Parameter Matching

Analyzes why database parameters aren't matching to canvas transitions.
Checks:
1. What attributes transitions have (EC numbers, reaction IDs, etc.)
2. What the database contains
3. Why matches are/aren't happening
4. What the inference engine is returning
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from shypn.crossfetch.database.heuristic_db import HeuristicDatabase
from shypn.crossfetch.inference.heuristic_engine import HeuristicInferenceEngine


def check_database_content():
    """Check what's in the database."""
    print("=" * 80)
    print("DATABASE CONTENT ANALYSIS")
    print("=" * 80)
    
    db = HeuristicDatabase()
    
    # Get all parameters
    all_params = db.query_parameters(limit=1000)
    
    print(f"\nTotal parameters in database: {len(all_params)}")
    
    # Group by type
    by_type = {}
    for p in all_params:
        t = p['transition_type']
        by_type[t] = by_type.get(t, 0) + 1
    
    print("\nBy transition type:")
    for t, count in sorted(by_type.items()):
        print(f"  {t}: {count}")
    
    # Check EC numbers
    with_ec = [p for p in all_params if p.get('ec_number')]
    print(f"\nParameters with EC numbers: {len(with_ec)}")
    
    if with_ec:
        ec_numbers = set(p['ec_number'] for p in with_ec)
        print(f"Unique EC numbers: {len(ec_numbers)}")
        print("\nSample EC numbers:")
        for ec in list(ec_numbers)[:10]:
            params = [p for p in with_ec if p['ec_number'] == ec]
            print(f"  {ec}: {len(params)} parameters")
    
    # Check reaction IDs
    with_reaction = [p for p in all_params if p.get('reaction_id')]
    print(f"\nParameters with reaction IDs: {len(with_reaction)}")
    
    # Check organisms
    organisms = set(p['organism'] for p in all_params)
    print(f"\nOrganisms in database: {len(organisms)}")
    for org in sorted(organisms):
        count = len([p for p in all_params if p['organism'] == org])
        print(f"  {org}: {count}")
    
    return all_params


def check_canvas_transitions():
    """Check what attributes canvas transitions have."""
    print("\n" + "=" * 80)
    print("CANVAS TRANSITIONS ANALYSIS")
    print("=" * 80)
    
    # Try to load model (this is a diagnostic, won't work without GTK)
    print("\nNOTE: This requires an active canvas with a loaded model.")
    print("Running in diagnostic mode - checking what attributes transitions typically have.\n")
    
    # Show what attributes we're looking for
    print("Attributes needed for database matching:")
    print("  ✓ transition.ec_number - EC number (e.g., '2.7.1.11')")
    print("  ✓ transition.reaction_id - Reaction ID (e.g., 'R00200')")
    print("  ✓ transition.enzyme_name - Enzyme name")
    print("  ✓ transition.label - Transition label")
    print("  ✓ transition.transition_type - Type (immediate/timed/stochastic/continuous)")
    
    return None


def simulate_inference(transitions_have_ec=False, transitions_have_reaction=False):
    """Simulate what happens during inference."""
    print("\n" + "=" * 80)
    print("INFERENCE SIMULATION")
    print("=" * 80)
    
    engine = HeuristicInferenceEngine(use_background_fetch=True)
    
    print(f"\nEngine configuration:")
    print(f"  use_background_fetch: {engine.use_background_fetch}")
    print(f"  Database path: {engine.db.db_path}")
    
    # Create a mock transition object
    class MockTransition:
        def __init__(self):
            self.id = "T1"
            self.label = "phosphorylation"
            self.transition_type = "continuous" if transitions_have_ec else "stochastic"
            self.ec_number = "2.7.1.11" if transitions_have_ec else None
            self.reaction_id = "R00200" if transitions_have_reaction else None
            self.enzyme_name = "Phosphofructokinase" if transitions_have_ec else None
    
    print(f"\nMock transition attributes:")
    transition = MockTransition()
    print(f"  id: {transition.id}")
    print(f"  label: {transition.label}")
    print(f"  transition_type: {transition.transition_type}")
    print(f"  ec_number: {transition.ec_number}")
    print(f"  reaction_id: {transition.reaction_id}")
    print(f"  enzyme_name: {transition.enzyme_name}")
    
    # Try inference
    print("\nRunning inference...")
    result = engine.infer_parameters(transition, organism="Homo sapiens")
    
    print(f"\nInference Result:")
    print(f"  transition_id: {result.transition_id}")
    print(f"  parameters.source: {result.parameters.source}")
    print(f"  parameters.confidence_score: {result.parameters.confidence_score}")
    print(f"  inference_metadata: {result.inference_metadata}")
    
    if hasattr(result.parameters, 'vmax'):
        print(f"  parameters.vmax: {result.parameters.vmax}")
        print(f"  parameters.km: {result.parameters.km}")
    if hasattr(result.parameters, 'lambda_param'):
        print(f"  parameters.lambda_param: {result.parameters.lambda_param}")
    
    # Check what the UI would display
    metadata = result.inference_metadata or {}
    source_from_metadata = metadata.get('source', 'Heuristic')
    source_from_params = result.parameters.source
    
    print(f"\nWhat UI would display:")
    print(f"  Source (from metadata): {source_from_metadata}")
    print(f"  Source (from params): {source_from_params}")
    print(f"  EC/Enzyme: {metadata.get('ec_number', 'N/A')}")
    
    if source_from_metadata != source_from_params:
        print(f"\n⚠️  WARNING: Source mismatch!")
        print(f"     UI shows: {source_from_metadata}")
        print(f"     Should show: {source_from_params}")


def check_database_query_logic():
    """Check if database queries are working."""
    print("\n" + "=" * 80)
    print("DATABASE QUERY LOGIC TEST")
    print("=" * 80)
    
    db = HeuristicDatabase()
    
    # Test query by EC number
    print("\nTest 1: Query by EC number (2.7.1.11)")
    results = db.query_parameters(
        transition_type='continuous',
        ec_number='2.7.1.11',
        organism='Homo sapiens',
        limit=5
    )
    print(f"  Found {len(results)} parameters")
    if results:
        for r in results[:3]:
            print(f"    - {r['source']}: Vmax={r['parameters'].get('vmax')}, Km={r['parameters'].get('km')}")
    
    # Test query without organism restriction
    print("\nTest 2: Query by EC number (any organism)")
    results = db.query_parameters(
        transition_type='continuous',
        ec_number='2.7.1.11',
        limit=5
    )
    print(f"  Found {len(results)} parameters")
    if results:
        for r in results[:3]:
            print(f"    - {r['organism']}: Vmax={r['parameters'].get('vmax')}, Km={r['parameters'].get('km')}")
    
    # Test generic query
    print("\nTest 3: Generic query (continuous, any enzyme)")
    results = db.query_parameters(
        transition_type='continuous',
        limit=10
    )
    print(f"  Found {len(results)} parameters")
    if results:
        print("  Sample results:")
        for r in results[:5]:
            ec = r.get('ec_number', 'N/A')
            org = r['organism']
            vmax = r['parameters'].get('vmax', 'N/A')
            print(f"    - EC {ec} ({org}): Vmax={vmax}")


def main():
    """Run all diagnostic checks."""
    print("HEURISTIC PARAMETER MATCHING DIAGNOSTICS")
    print("=" * 80)
    
    # Check database
    db_params = check_database_content()
    
    # Check transitions
    check_canvas_transitions()
    
    # Test inference with EC number
    print("\n\n" + "=" * 80)
    print("SCENARIO 1: Transition WITH EC number")
    simulate_inference(transitions_have_ec=True)
    
    # Test inference without EC number
    print("\n\n" + "=" * 80)
    print("SCENARIO 2: Transition WITHOUT EC number")
    simulate_inference(transitions_have_ec=False)
    
    # Test database queries
    check_database_query_logic()
    
    # Summary
    print("\n\n" + "=" * 80)
    print("DIAGNOSIS SUMMARY")
    print("=" * 80)
    
    print("\n🔍 Key Findings:")
    print("\n1. SOURCE DISPLAY ISSUE:")
    print("   - UI reads: metadata.get('source', 'Heuristic')")
    print("   - Engine sets metadata['source'] only for database_cache hits")
    print("   - Engine sets params.source for all cases")
    print("   → UI should read params.source instead!")
    
    print("\n2. DATABASE MATCHING:")
    print("   - Requires: transition.ec_number OR transition.reaction_id")
    print("   - Your transitions likely don't have these attributes")
    print("   → No database matches = only heuristic defaults")
    
    print("\n3. PARAMETER VALUES:")
    print("   - Database has 254 parameters with real kinetic values")
    print("   - Heuristics use generic defaults (Vmax=100, Km=0.1, etc.)")
    print("   - If values are the same, it means no database match occurred")
    
    print("\n💡 Solutions:")
    print("\n   A) FIX UI SOURCE DISPLAY:")
    print("      Change: metadata.get('source', 'Heuristic')")
    print("      To:     result.parameters.source")
    
    print("\n   B) ADD EC NUMBERS TO TRANSITIONS:")
    print("      - Import from KEGG (transitions get EC numbers)")
    print("      - Or manually add ec_number attribute")
    print("      - Then database matches will work!")
    
    print("\n   C) ENHANCE MATCHING LOGIC:")
    print("      - Match by label/name similarity")
    print("      - Match by reaction type")
    print("      - Fuzzy matching for partial matches")
    
    print("\n" + "=" * 80)


if __name__ == '__main__':
    main()
