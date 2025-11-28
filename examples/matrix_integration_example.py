#!/usr/bin/env python3
"""Example: MatrixManager integration with simulation system.

Demonstrates:
1. Creating a Petri net document
2. Setting up MatrixManager
3. Running simulation using matrix-based semantics
4. Comparing with formal state equation
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from shypn.data.canvas.document_model import DocumentModel
from shypn.netobjs import Place, Transition, Arc
from shypn.matrix import MatrixManager


def create_producer_consumer_net():
    """Create a producer-consumer Petri net.
    
    Structure:
        P1 (buffer, capacity=5)
        P2 (producing)
        P3 (consuming)
        
        T1 (produce): P2 → P1
        T2 (consume): P1 → P3
    
    Initial marking: P1=2, P2=1, P3=0
    """
    doc = DocumentModel()
    
    # Places
    p1 = Place(x=200, y=100, id=1, name="P1", label="Buffer")
    p2 = Place(x=100, y=100, id=2, name="P2", label="Producing")
    p3 = Place(x=300, y=100, id=3, name="P3", label="Consuming")
    
    # Initial marking
    p1.tokens = 2
    p1.initial_marking = 2
    p2.tokens = 1
    p2.initial_marking = 1
    p3.tokens = 0
    p3.initial_marking = 0
    
    # Transitions
    t1 = Transition(x=150, y=100, id=1, name="T1", label="Produce")
    t2 = Transition(x=250, y=100, id=2, name="T2", label="Consume")
    
    # Arcs
    a1 = Arc(source=p2, target=t1, id=1, name="A1", weight=1)  # P2 → T1
    a2 = Arc(source=t1, target=p1, id=2, name="A2", weight=1)  # T1 → P1
    a3 = Arc(source=p1, target=t2, id=3, name="A3", weight=1)  # P1 → T2
    a4 = Arc(source=t2, target=p3, id=4, name="A4", weight=1)  # T2 → P3
    a5 = Arc(source=t2, target=p2, id=5, name="A5", weight=1)  # T2 → P2 (cycle)
    
    doc.places.extend([p1, p2, p3])
    doc.transitions.extend([t1, t2])
    doc.arcs.extend([a1, a2, a3, a4, a5])
    
    return doc


def print_marking(marking, places, prefix=""):
    """Pretty-print a marking."""
    p_names = {p.id: p.label for p in places}
    mark_str = ", ".join(f"{p_names[pid]}={tokens}" 
                        for pid, tokens in sorted(marking.items()))
    print(f"{prefix}{mark_str}")


def main():
    print("=" * 70)
    print("MatrixManager Integration Example")
    print("=" * 70)
    
    # Create net
    print("\n1. Creating producer-consumer Petri net...")
    doc = create_producer_consumer_net()
    
    print(f"   Places: {len(doc.places)}")
    print(f"   Transitions: {len(doc.transitions)}")
    print(f"   Arcs: {len(doc.arcs)}")
    
    # Create manager
    print("\n2. Creating MatrixManager...")
    manager = MatrixManager(doc)
    
    stats = manager.get_statistics()
    print(f"   Implementation: {manager.matrix.__class__.__name__}")
    print(f"   Matrix built: {stats['built']}")
    
    # Validate structure
    print("\n3. Validating bipartite structure...")
    is_valid, errors = manager.validate_bipartite()
    if is_valid:
        print("   ✓ Structure is valid")
    else:
        print(f"   ✗ Validation errors: {errors}")
        return
    
    # Show incidence matrix
    print("\n4. Incidence matrix C:")
    print("   (rows=transitions, cols=places)")
    print("   ", end="")
    for p in doc.places:
        print(f"{p.label:>10}", end="")
    print()
    
    for t in doc.transitions:
        print(f"   {t.label:<3}", end="")
        for p in doc.places:
            c = manager.get_incidence(t.id, p.id)
            print(f"{c:>10}", end="")
        print()
    
    # Run simulation
    print("\n5. Running simulation (10 steps)...")
    print("   State equation: M' = M + C·σ")
    print()
    
    marking = manager.get_marking_from_document()
    print_marking(marking, doc.places, "   Initial: ")
    
    for step in range(10):
        # Get enabled transitions
        enabled = manager.get_enabled_transitions(marking)
        
        if not enabled:
            print(f"\n   Deadlock at step {step}")
            break
        
        # Choose first enabled (or implement scheduling policy)
        t_id = enabled[0]
        t = next(t for t in doc.transitions if t.id == t_id)
        
        # Fire transition
        new_marking = manager.fire(t_id, marking)
        
        # Show change
        print(f"   Step {step+1}: Fire {t.label} → ", end="")
        print_marking(new_marking, doc.places, "")
        
        marking = new_marking
    
    # Apply final marking to document
    print("\n6. Applying final marking to document...")
    manager.apply_marking_to_document(marking)
    
    print("   Document updated:")
    for p in doc.places:
        print(f"   {p.label}: {p.tokens} tokens")
    
    # Show matrix statistics
    print("\n7. Matrix statistics:")
    for key, value in stats.items():
        if key != 'built':
            print(f"   {key}: {value}")
    
    print("\n" + "=" * 70)
    print("✓ Integration example complete")
    print("=" * 70)


if __name__ == '__main__':
    main()
