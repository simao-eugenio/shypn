"""
Quick test to verify convert_pathway_enhanced accepts create_enzyme_places parameter.
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))

from shypn.importer.kegg import parse_kgml, convert_pathway_enhanced
from shypn.pathway.options import EnhancementOptions

print("Testing convert_pathway_enhanced with create_enzyme_places parameter...")

# Test with minimal KGML
kgml = """<?xml version="1.0"?>
<!DOCTYPE pathway SYSTEM "https://www.kegg.jp/kegg/xml/KGML_v0.7.2_.dtd">
<pathway name="path:test00010" org="test" number="00010">
    <entry id="1" name="cpd:C00031" type="compound">
        <graphics name="C00031" x="100" y="100" type="circle"/>
    </entry>
    <entry id="2" name="cpd:C00068" type="compound">
        <graphics name="C00068" x="200" y="100" type="circle"/>
    </entry>
    <entry id="3" name="gene:12345" type="gene" reaction="rn:R00710">
        <graphics name="TestEnzyme" x="150" y="50" type="rectangle"/>
    </entry>
    <reaction id="4" name="rn:R00710" type="irreversible">
        <substrate id="1" name="cpd:C00031"/>
        <product id="2" name="cpd:C00068"/>
    </reaction>
</pathway>"""

try:
    # Parse
    pathway = parse_kgml(kgml)
    print("✓ Parsed KGML")
    
    # Test 1: Without enzyme places
    enhancement_options = EnhancementOptions(
        enable_layout_optimization=False,
        enable_arc_routing=False
    )
    
    doc1 = convert_pathway_enhanced(
        pathway,
        create_enzyme_places=False,
        enhancement_options=enhancement_options
    )
    print(f"✓ Test 1 (catalysts=False): {len(doc1.places)} places, {len(doc1.arcs)} arcs")
    
    # Test 2: With enzyme places
    doc2 = convert_pathway_enhanced(
        pathway,
        create_enzyme_places=True,
        enhancement_options=enhancement_options
    )
    
    test_arcs = [a for a in doc2.arcs if hasattr(a, 'consumes_tokens') and not a.consumes_tokens()]
    
    print(f"✓ Test 2 (catalysts=True): {len(doc2.places)} places, {len(doc2.arcs)} arcs")
    print(f"  Test arcs: {len(test_arcs)}")
    
    if len(test_arcs) > 0:
        print(f"  ✅ SUCCESS: Test arcs created!")
        print(f"  Model type: {getattr(doc2, 'metadata', {}).get('model_type', 'Standard')}")
    else:
        print(f"  ⚠️  No test arcs created (might be expected if enzyme has no matching reaction)")
    
    print("\n✅ convert_pathway_enhanced() accepts create_enzyme_places parameter!")
    
except TypeError as e:
    if "create_enzyme_places" in str(e):
        print(f"❌ FAILED: {e}")
        print("The parameter is still not accepted!")
    else:
        raise
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
