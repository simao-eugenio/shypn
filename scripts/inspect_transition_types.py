#!/usr/bin/env python3
"""
Inspect KEGG pathway import - Check transition types and kinetics

Analyzes transitions created from KEGG pathway to verify kinetics assignment.
"""

import sys
sys.path.insert(0, '/home/simao/projetos/shypn/src')

from shypn.importer.kegg.loader import load_kegg_pathway
from shypn.data.canvas.document_model import DocumentModel
import logging

# Enable detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(name)s - %(levelname)s: %(message)s'
)

print("=" * 80)
print("KEGG Pathway Import - Transition Analysis")
print("=" * 80)

# Load Glycolysis pathway (hsa00010)
print("\n1. Loading KEGG Glycolysis pathway (hsa00010)...")
print("-" * 80)

try:
    document = load_kegg_pathway(
        pathway_id="hsa00010",
        enhance_kinetics=True,
        offline_mode=True
    )
    
    print(f"\n✅ Pathway loaded successfully!")
    print(f"   Places: {len(document.places)}")
    print(f"   Transitions: {len(document.transitions)}")
    print(f"   Arcs: {len(document.arcs)}")
    
except Exception as e:
    print(f"\n✗ Error loading pathway: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Analyze transitions
print("\n2. Analyzing Transitions")
print("-" * 80)

type_counts = {}
confidence_counts = {}
ec_count = 0
database_assigned = 0

for i, t in enumerate(document.transitions, 1):
    # Get transition type
    t_type = t.transition_type if hasattr(t, 'transition_type') else 'unknown'
    type_counts[t_type] = type_counts.get(t_type, 0) + 1
    
    # Get metadata
    metadata = getattr(t, 'metadata', {})
    
    # Check EC numbers
    has_ec = 'ec_numbers' in metadata
    if has_ec:
        ec_count += 1
    
    # Check confidence
    confidence = metadata.get('kinetics_confidence', 'none')
    confidence_counts[confidence] = confidence_counts.get(confidence, 0) + 1
    
    # Check if from database
    lookup_source = metadata.get('lookup_source', None)
    if lookup_source:
        database_assigned += 1
    
    # Print first 10 transitions in detail
    if i <= 10:
        print(f"\nTransition {i}: {t.label}")
        print(f"  System name: {t.name}")
        print(f"  Type: {t_type}")
        print(f"  Rate: {t.rate_function if hasattr(t, 'rate_function') else 'none'}")
        
        if metadata:
            print(f"  Metadata:")
            if 'kegg_reaction_name' in metadata:
                print(f"    KEGG reaction: {metadata['kegg_reaction_name']}")
            if 'ec_numbers' in metadata:
                print(f"    EC numbers: {metadata['ec_numbers']}")
            if 'kinetics_confidence' in metadata:
                print(f"    Confidence: {metadata['kinetics_confidence']}")
            if 'lookup_source' in metadata:
                print(f"    Source: {metadata['lookup_source']}")
            if 'enzyme_name' in metadata:
                print(f"    Enzyme: {metadata['enzyme_name']}")

# Summary
print("\n" + "=" * 80)
print("Summary")
print("=" * 80)

print(f"\nTransition Types:")
for t_type, count in sorted(type_counts.items()):
    print(f"  {t_type}: {count}")

print(f"\nKinetics Confidence:")
for conf, count in sorted(confidence_counts.items()):
    print(f"  {conf}: {count}")

print(f"\nEC Number Coverage:")
print(f"  Transitions with EC numbers: {ec_count}/{len(document.transitions)}")
print(f"  Transitions from database: {database_assigned}/{len(document.transitions)}")

# Check if all stochastic
if type_counts.get('stochastic', 0) == len(document.transitions):
    print("\n⚠️  WARNING: All transitions are STOCHASTIC!")
    print("   This suggests kinetics enhancement may not be working correctly.")
    print("\nPossible causes:")
    print("  1. EC numbers not being fetched from KEGG API")
    print("  2. Database lookup failing")
    print("  3. Kinetics enhancement not being called")
    print("  4. Default fallback to stochastic type")

if ec_count == 0:
    print("\n⚠️  WARNING: No EC numbers found in metadata!")
    print("   KEGG EC enrichment may not be working.")

if database_assigned == 0:
    print("\n⚠️  WARNING: No database assignments!")
    print("   Hybrid API may not be working.")

print("\n" + "=" * 80)
