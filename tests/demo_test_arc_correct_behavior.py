#!/usr/bin/env python3
"""
Simple demonstration that test arcs work correctly.

Test arcs check token presence WITHOUT consuming - they are READ ARCS.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from shypn.netobjs.place import Place
from shypn.netobjs.transition import Transition
from shypn.netobjs.arc import Arc
from shypn.netobjs.test_arc import TestArc
from shypn.engine.immediate_behavior import ImmediateBehavior


def main():
    """Simple enzyme-catalyzed reaction demonstration."""
    print("\n" + "=" * 70)
    print("TEST ARC DEMONSTRATION: Enzyme-Catalyzed Reaction")
    print("=" * 70)
    print()
    print("Model: Substrate + Enzyme -> Product")
    print("  - Substrate: Normal arc (CONSUMED)")
    print("  - Enzyme: Test arc (NOT CONSUMED - catalyst)")
    print("  - Product: Output (PRODUCED)")
    print()
    
    # Create places
    substrate = Place(x=100, y=100, id='substrate', name='Substrate')
    substrate.tokens = 10.0
    
    enzyme = Place(x=100, y=200, id='enzyme', name='Enzyme')
    enzyme.tokens = 5.0
    
    product = Place(x=300, y=100, id='product', name='Product')
    product.tokens = 0.0
    
    # Create transition
    reaction = Transition(x=200, y=100, id='reaction', name='Reaction')
    reaction_behavior = ImmediateBehavior(reaction, None)
    
    # Create arcs
    arc_substrate = Arc(substrate, reaction, id='a1', name='A1', weight=1.0)
    arc_enzyme = TestArc(enzyme, reaction, id='a2', name='A2', weight=1.0)
    arc_product = Arc(reaction, product, id='a3', name='A3', weight=1.0)
    
    print("Initial Marking:")
    print(f"  Substrate: {substrate.tokens}")
    print(f"  Enzyme: {enzyme.tokens} ← catalyst (test arc)")
    print(f"  Product:   {product.tokens}")
    print()
    
    print("Arc Configuration:")
    print(f"  Substrate → Reaction: {arc_substrate.arc_type} arc (consumes={not hasattr(arc_substrate, 'consumes_tokens') or arc_substrate.consumes_tokens()})")
    print(f"  Enzyme → Reaction: {arc_enzyme.arc_type} arc (consumes={arc_enzyme.consumes_tokens()})")
    print(f"  Reaction → Product: {arc_product.arc_type} arc")
    print()
    
    # Fire 3 times
    print("Firing Reaction 3 Times:")
    print("-" * 70)
    
    input_arcs = [arc_substrate, arc_enzyme]
    output_arcs = [arc_product]
    
    for i in range(3):
        success, details = reaction_behavior.fire(input_arcs, output_arcs)
        
        if success:
            print(f"  Firing {i+1}: Substrate={substrate.tokens}, Enzyme={enzyme.tokens}, Product={product.tokens}")
        else:
            print(f"  Firing {i+1}: FAILED - {details.get('reason', 'unknown')}")
            break
    
    print()
    print("Final Marking:")
    print(f"  Substrate: {substrate.tokens} (10 - 3 = 7) ✓ Consumed")
    print(f"  Enzyme: {enzyme.tokens} (still 5) ✓ NOT consumed (test arc)")
    print(f"  Product: {product.tokens} (0 + 3 = 3) ✓ Produced")
    print()
    
    # Verify
    if substrate.tokens == 7.0 and enzyme.tokens == 5.0 and product.tokens == 3.0:
        print("=" * 70)
        print("✓ TEST ARCS WORKING CORRECTLY")
        print("=" * 70)
        print()
        print("Test arcs (read arcs) check token presence WITHOUT consuming.")
        print("This correctly models catalysts, enzymes, and regulatory molecules.")
        print()
        return 0
    else:
        print("=" * 70)
        print("❌ UNEXPECTED RESULT")
        print("=" * 70)
        print()
        print(f"Expected: Substrate=7, Enzyme=5, Product=3")
        print(f"Got: Substrate={substrate.tokens}, Enzyme={enzyme.tokens}, Product={product.tokens}")
        print()
        return 1


if __name__ == '__main__':
    sys.exit(main())
