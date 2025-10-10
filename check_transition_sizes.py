#!/usr/bin/env python3
"""
Check transition sizes in imported KEGG pathway.
Hypothesis: Transitions are so small they're invisible, making Place→T→Place look like Place→Place.
"""

import sys
sys.path.insert(0, '/home/simao/projetos/shypn/src')

from shypn.importer.kegg.pathway_converter import convert_pathway
from shypn.importer.kegg.converter_base import ConversionOptions
from shypn.importer.kegg.kgml_parser import KGMLParser

def check_transition_sizes():
    """Check transition sizes and visibility in imported pathway."""
    
    print("=" * 80)
    print("TRANSITION SIZE CHECK - hsa00010")
    print("=" * 80)
    
    # Import pathway
    pathway_file = '/home/simao/projetos/shypn/data/hsa00010.xml'
    
    # Parse KEGG file
    parser = KGMLParser()
    pathway = parser.parse_file(pathway_file)
    options = ConversionOptions()
    
    document = convert_pathway(pathway, options)
    
    print(f"\n📊 Statistics:")
    print(f"   Places: {len(document.places)}")
    print(f"   Transitions: {len(document.transitions)}")
    print(f"   Arcs: {len(document.arcs)}")
    
    # Check transition sizes
    print(f"\n🔍 Transition Sizes:")
    print(f"{'ID':<12} {'Label':<25} {'Width':<8} {'Height':<8} {'Visible?'}")
    print("-" * 80)
    
    tiny_transitions = []
    small_transitions = []
    normal_transitions = []
    
    for t in sorted(document.transitions, key=lambda x: x.width * x.height):
        width = t.width if hasattr(t, 'width') else 10  # Default
        height = t.height if hasattr(t, 'height') else 10  # Default
        
        area = width * height
        
        # Classify by visibility at normal zoom
        if area < 50:
            visibility = "❌ INVISIBLE"
            tiny_transitions.append(t)
        elif area < 150:
            visibility = "⚠️  TINY"
            small_transitions.append(t)
        else:
            visibility = "✅ VISIBLE"
            normal_transitions.append(t)
        
        label = t.label[:23] + "..." if len(t.label) > 25 else t.label
        print(f"{t.id:<12} {label:<25} {width:<8.1f} {height:<8.1f} {visibility}")
    
    # Summary
    print("\n" + "=" * 80)
    print("📈 SIZE SUMMARY:")
    print("=" * 80)
    print(f"   ❌ Invisible (<50 sq px):  {len(tiny_transitions):2d} transitions")
    print(f"   ⚠️  Tiny (50-150 sq px):   {len(small_transitions):2d} transitions")
    print(f"   ✅ Visible (>150 sq px):  {len(normal_transitions):2d} transitions")
    
    # Check if this explains spurious lines
    print("\n" + "=" * 80)
    print("🔬 SPURIOUS LINE HYPOTHESIS:")
    print("=" * 80)
    
    if len(tiny_transitions) > 5 or len(small_transitions) > 10:
        print("✅ LIKELY CAUSE FOUND!")
        print(f"   {len(tiny_transitions) + len(small_transitions)} transitions are too small to see easily.")
        print("   These create the illusion of direct Place→Place connections.")
        print("\n   Example: Place → [invisible transition] → Place")
        print("            APPEARS AS: Place → Place")
    else:
        print("⚠️  Transitions seem reasonably sized.")
        print("   Spurious lines likely have a different cause.")
    
    # Check specific arcs that look like place-to-place
    print("\n" + "=" * 80)
    print("🎯 CHECKING SPECIFIC 'SPURIOUS' CONNECTIONS:")
    print("=" * 80)
    
    # C01159 and C00036 (user mentioned these)
    c01159_place = next((p for p in document.places if 'C01159' in p.label), None)
    c00036_place = next((p for p in document.places if 'C00036' in p.label), None)
    
    if c01159_place:
        print(f"\n📍 C01159 ({c01159_place.id}) connections:")
        for arc in document.arcs:
            if arc.source_id == c01159_place.id:
                target_trans = next((t for t in document.transitions if t.id == arc.target_id), None)
                if target_trans:
                    size = f"{target_trans.width:.1f}x{target_trans.height:.1f}"
                    visibility = "✅" if target_trans.width * target_trans.height > 150 else "⚠️"
                    print(f"   {c01159_place.id} → {target_trans.id} ({target_trans.label[:20]}) [{size}] {visibility}")
            elif arc.target_id == c01159_place.id:
                source_trans = next((t for t in document.transitions if t.id == arc.source_id), None)
                if source_trans:
                    size = f"{source_trans.width:.1f}x{source_trans.height:.1f}"
                    visibility = "✅" if source_trans.width * source_trans.height > 150 else "⚠️"
                    print(f"   {source_trans.id} ({source_trans.label[:20]}) → {c01159_place.id} [{size}] {visibility}")
    
    if c00036_place:
        print(f"\n📍 C00036 ({c00036_place.id}) connections:")
        for arc in document.arcs:
            if arc.source_id == c00036_place.id:
                target_trans = next((t for t in document.transitions if t.id == arc.target_id), None)
                if target_trans:
                    size = f"{target_trans.width:.1f}x{target_trans.height:.1f}"
                    visibility = "✅" if target_trans.width * target_trans.height > 150 else "⚠️"
                    print(f"   {c00036_place.id} → {target_trans.id} ({target_trans.label[:20]}) [{size}] {visibility}")
            elif arc.target_id == c00036_place.id:
                source_trans = next((t for t in document.transitions if t.id == arc.source_id), None)
                if source_trans:
                    size = f"{source_trans.width:.1f}x{source_trans.height:.1f}"
                    visibility = "✅" if source_trans.width * source_trans.height > 150 else "⚠️"
                    print(f"   {source_trans.id} ({source_trans.label[:20]}) → {c00036_place.id} [{size}] {visibility}")
    
    print("\n" + "=" * 80)
    print("💡 RECOMMENDATION:")
    print("=" * 80)
    
    min_size = min((t.width * t.height) for t in document.transitions)
    avg_size = sum((t.width * t.height) for t in document.transitions) / len(document.transitions)
    
    print(f"   Current: min={min_size:.1f} sq px, avg={avg_size:.1f} sq px")
    
    if min_size < 50 or avg_size < 150:
        print(f"   Suggested: Set minimum transition size to 15x15 pixels (225 sq px)")
        print(f"   File: src/shypn/importer/kegg/reaction_mapper.py")
        print(f"   Change: In create_transitions(), ensure min width/height = 15")
    else:
        print(f"   Transitions seem adequately sized.")
        print(f"   Spurious lines may have a different root cause.")

if __name__ == '__main__':
    check_transition_sizes()
