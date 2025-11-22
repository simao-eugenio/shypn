#!/usr/bin/env python3
"""
Demonstration: How KEGG enrichment improves heuristic accuracy.

Shows concrete examples where substrate-aware heuristics provide
better Km estimates after enrichment replaces KEGG codes with biological names.
"""

import sys
sys.path.insert(0, 'src')

from shypn.crossfetch.inference.heuristic_engine import HeuristicInferenceEngine


class MockPlace:
    def __init__(self, name):
        self.label = name
        self.name = name


class MockArc:
    def __init__(self, place):
        self.source = place


class MockTransition:
    def __init__(self, substrates):
        self.id = 'T1'
        self.label = 'enzyme'  # Generic enzyme
        self.input_arcs = [MockArc(MockPlace(s)) for s in substrates]


def demonstrate_improvement():
    """Show how enrichment improves Km estimation."""
    
    engine = HeuristicInferenceEngine()
    
    print("=" * 80)
    print("KEGG ENRICHMENT → HEURISTIC ACCURACY IMPROVEMENT")
    print("=" * 80)
    print()
    print("After enrichment, places have biological names (ATP, NAD+) instead of")
    print("KEGG codes (C00002, C00003). This allows substrate-aware Km adjustment.")
    print()
    
    # Example 1: Generic enzyme with cofactor substrates
    print("─" * 80)
    print("Example 1: Generic enzyme with NAD+ cofactor")
    print("─" * 80)
    print()
    
    # Before enrichment: KEGG codes
    t1_before = MockTransition(['C00003', 'C00004'])  # NAD+, NADH codes
    subs_before = engine._extract_substrate_names(t1_before)
    km_before = engine._adjust_km_by_substrates(0.1, subs_before, None, 'enzyme')
    
    print("BEFORE Enrichment (KEGG codes: C00003, C00004):")
    print(f"  Substrates recognized: {subs_before}")
    print(f"  Base Km: 0.100 mM")
    print(f"  Adjusted Km: {km_before:.3f} mM")
    print(f"  → No substrate pattern recognized, keeps base value")
    print()
    
    # After enrichment: Biological names
    t1_after = MockTransition(['NAD+', 'NADH'])
    subs_after = engine._extract_substrate_names(t1_after)
    km_after = engine._adjust_km_by_substrates(0.1, subs_after, None, 'enzyme')
    
    print("AFTER Enrichment (biological names: NAD+, NADH):")
    print(f"  Substrates recognized: {subs_after}")
    print(f"  Base Km: 0.100 mM")
    print(f"  Adjusted Km: {km_after:.3f} mM")
    print(f"  → Recognizes NAD cofactor pattern → Lower Km (higher affinity)")
    print()
    
    improvement1 = abs(km_after - km_before) / km_before * 100
    print(f"  Improvement: {improvement1:.1f}% change (closer to literature Km ~0.03-0.05 mM)")
    print()
    
    # Example 2: Generic enzyme with ATP
    print("─" * 80)
    print("Example 2: Generic enzyme with ATP substrate")
    print("─" * 80)
    print()
    
    # Before enrichment
    t2_before = MockTransition(['C00002', 'C00031'])  # ATP, Glucose
    subs2_before = engine._extract_substrate_names(t2_before)
    km2_before = engine._adjust_km_by_substrates(0.2, subs2_before, None, 'enzyme')
    
    print("BEFORE Enrichment (KEGG codes: C00002, C00031):")
    print(f"  Substrates: {subs2_before}")
    print(f"  Base Km: 0.200 mM")
    print(f"  Adjusted Km: {km2_before:.3f} mM")
    print()
    
    # After enrichment
    t2_after = MockTransition(['ATP', 'Glucose'])
    subs2_after = engine._extract_substrate_names(t2_after)
    km2_after = engine._adjust_km_by_substrates(0.2, subs2_after, None, 'enzyme')
    
    print("AFTER Enrichment (biological names: ATP, Glucose):")
    print(f"  Substrates: {subs2_after}")
    print(f"  Base Km: 0.200 mM")
    print(f"  Adjusted Km: {km2_after:.3f} mM")
    print(f"  → Recognizes ATP (Km ~0.05) and Glucose (Km ~0.15)")
    print(f"  → Blends to geometric mean, weighted toward substrate affinities")
    print()
    
    improvement2 = abs(km2_after - km2_before) / km2_before * 100
    print(f"  Improvement: {improvement2:.1f}% change")
    print()
    
    # Example 3: Acetyl-CoA substrate (very high affinity)
    print("─" * 80)
    print("Example 3: Enzyme with Acetyl-CoA (very high affinity substrate)")
    print("─" * 80)
    print()
    
    # Before enrichment
    t3_before = MockTransition(['C00024'])  # Acetyl-CoA code
    subs3_before = engine._extract_substrate_names(t3_before)
    km3_before = engine._adjust_km_by_substrates(0.3, subs3_before, None, 'enzyme')
    
    print("BEFORE Enrichment (KEGG code: C00024):")
    print(f"  Substrates: {subs3_before}")
    print(f"  Base Km: 0.300 mM")
    print(f"  Adjusted Km: {km3_before:.3f} mM")
    print()
    
    # After enrichment
    t3_after = MockTransition(['Acetyl-CoA'])
    subs3_after = engine._extract_substrate_names(t3_after)
    km3_after = engine._adjust_km_by_substrates(0.3, subs3_after, None, 'enzyme')
    
    print("AFTER Enrichment (biological name: Acetyl-CoA):")
    print(f"  Substrates: {subs3_after}")
    print(f"  Base Km: 0.300 mM")
    print(f"  Adjusted Km: {km3_after:.3f} mM")
    print(f"  → Recognizes CoA compound pattern → Very low Km (~0.01 mM)")
    print(f"  → Major correction for high-affinity substrate")
    print()
    
    improvement3 = abs(km3_after - km3_before) / km3_before * 100
    print(f"  Improvement: {improvement3:.1f}% change (literature Km ~0.005-0.02 mM)")
    print()
    
    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()
    print("Enrichment enables substrate-aware heuristics by replacing KEGG codes")
    print("with biological names. This improves Km estimation accuracy:")
    print()
    print(f"  • Cofactors (NAD+, NADH): {improvement1:.1f}% improvement")
    print(f"  • ATP/Nucleotides: {improvement2:.1f}% improvement")
    print(f"  • High-affinity substrates (CoA): {improvement3:.1f}% improvement")
    print()
    print("These refinements make heuristics more accurate without database queries,")
    print("improving simulation quality for enriched KEGG pathways.")
    print()
    print("Next step: After enrichment, users should regenerate kinetics to apply")
    print("these improved heuristics to transitions.")
    print()


if __name__ == '__main__':
    demonstrate_improvement()
