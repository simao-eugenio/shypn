"""
Analysis script for test arc refinement issues:
1) Test arcs render center-to-center (should be perimeter-to-perimeter)
2) Isolated catalyst places with no test arcs
3) Isolated places included in layout algorithms
4) Isolated places disrupting layout
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))

from shypn.data.canvas.document_model import DocumentModel
from shypn.netobjs.place import Place
from shypn.netobjs.transition import Transition
from shypn.netobjs.test_arc import TestArc
from shypn.netobjs.arc import Arc


def create_test_model():
    """Create a simple model with test arcs to analyze rendering."""
    doc = DocumentModel()
    
    # Create places
    substrate = Place(id="P1", name="Substrate", x=100, y=100, tokens=1)
    product = Place(id="P2", name="Product", x=300, y=100, tokens=0)
    enzyme = Place(id="P3", name="Enzyme", x=200, y=50, tokens=1)
    isolated_catalyst = Place(id="P4", name="Isolated", x=200, y=200, tokens=1)
    
    doc.places.extend([substrate, product, enzyme, isolated_catalyst])
    
    # Create transition
    reaction = Transition(id="T1", name="Reaction", x=200, y=100)
    doc.transitions.append(reaction)
    
    # Create normal arcs
    arc1 = Arc(source=substrate, target=reaction, id="A1", name="A1", weight=1)
    arc2 = Arc(source=reaction, target=product, id="A2", name="A2", weight=1)
    doc.arcs.extend([arc1, arc2])
    
    # Create test arc (catalyst)
    test_arc = TestArc(source=enzyme, target=reaction, id="A3", name="TA3", weight=1)
    doc.arcs.append(test_arc)
    
    return doc


def analyze_issue_1_rendering():
    """Issue 1: Test arcs render center-to-center instead of perimeter-to-perimeter."""
    print("=" * 80)
    print("ISSUE 1: Test Arc Rendering (Center vs Perimeter)")
    print("=" * 80)
    
    doc = create_test_model()
    
    # Find test arc
    test_arc = [a for a in doc.arcs if isinstance(a, TestArc)][0]
    normal_arc = [a for a in doc.arcs if isinstance(a, Arc) and not isinstance(a, TestArc)][0]
    
    print(f"\n📊 Normal Arc (A1): {normal_arc.source.name} → {normal_arc.target.name}")
    print(f"   Source: {normal_arc.source.__class__.__name__} at ({normal_arc.source.x}, {normal_arc.source.y})")
    print(f"   Target: {normal_arc.target.__class__.__name__} at ({normal_arc.target.x}, {normal_arc.target.y})")
    print(f"   ✓ Normal arcs use _get_boundary_point() for perimeter intersection")
    
    print(f"\n📊 Test Arc (A3): {test_arc.source.name} → {test_arc.target.name}")
    print(f"   Source: {test_arc.source.__class__.__name__} at ({test_arc.source.x}, {test_arc.source.y})")
    print(f"   Target: {test_arc.target.__class__.__name__} at ({test_arc.target.x}, {test_arc.target.y})")
    
    # Check rendering code
    print(f"\n🔍 Analysis:")
    print(f"   Normal Arc render() uses:")
    print(f"      - _get_boundary_point() to find perimeter intersections")
    print(f"      - Connects at node boundaries (perimeter-to-perimeter)")
    print(f"\n   Test Arc render() uses:")
    print(f"      - x1, y1 = self.source.x, self.source.y  # CENTER!")
    print(f"      - x2, y2 = self.target.x, self.target.y  # CENTER!")
    print(f"      - ❌ Does NOT use _get_boundary_point()")
    print(f"      - ❌ Connects at node centers (center-to-center)")
    
    print(f"\n💡 ROOT CAUSE:")
    print(f"   TestArc.render() directly uses source/target positions (centers)")
    print(f"   instead of calling inherited _get_boundary_point() method.")
    
    print(f"\n✅ FIX:")
    print(f"   TestArc.render() should use same approach as Arc.render():")
    print(f"   1. Calculate direction vector from centers")
    print(f"   2. Call _get_boundary_point() for both source and target")
    print(f"   3. Draw line between boundary points (not centers)")


def analyze_issue_2_isolated():
    """Issue 2: Some catalyst places have no test arcs connecting them."""
    print("\n" + "=" * 80)
    print("ISSUE 2: Isolated Catalyst Places (No Test Arcs)")
    print("=" * 80)
    
    doc = create_test_model()
    
    # Count connections
    connected_places = set()
    for arc in doc.arcs:
        connected_places.add(arc.source)
        connected_places.add(arc.target)
    
    isolated_places = [p for p in doc.places if p not in connected_places]
    
    print(f"\n📊 Connection Analysis:")
    print(f"   Total places: {len(doc.places)}")
    print(f"   Connected places: {len(connected_places)}")
    print(f"   Isolated places: {len(isolated_places)}")
    
    if isolated_places:
        print(f"\n   Isolated Places:")
        for p in isolated_places:
            is_enzyme = p.metadata.get('is_enzyme', False) if hasattr(p, 'metadata') else False
            print(f"      - {p.name} (id={p.id}, is_enzyme={is_enzyme})")
    
    print(f"\n🔍 Analysis:")
    print(f"   In KEGG/SBML imports with create_enzyme_places=True:")
    print(f"   1. Enzyme places are created")
    print(f"   2. KEGGEnzymeConverter/ModifierConverter should create test arcs")
    print(f"   3. BUT: If enzyme.reaction doesn't match any transition, arc NOT created")
    print(f"   4. Result: Enzyme place exists but is isolated")
    
    print(f"\n💡 ROOT CAUSE:")
    print(f"   Test arc creation can fail if:")
    print(f"   - Enzyme entry has no 'reaction' attribute")
    print(f"   - Enzyme.reaction doesn't match any transition ID")
    print(f"   - Transition not created due to filtering")
    
    print(f"\n✅ FIX:")
    print(f"   Option 1: Don't create enzyme place if test arc can't be created")
    print(f"   Option 2: Log warning and continue (current behavior)")
    print(f"   Option 3: Create 'orphan enzyme' visual indicator")


def analyze_issue_3_layout():
    """Issue 3: Isolated places are included in layout algorithms."""
    print("\n" + "=" * 80)
    print("ISSUE 3: Isolated Places Included in Layout")
    print("=" * 80)
    
    print(f"\n📊 Hierarchical Layout Algorithm:")
    print(f"   1. _build_dependency_graph() - builds graph from reactions")
    print(f"      - Extracts reactants and products")
    print(f"      - ❌ Ignores modifiers/catalysts")
    print(f"      - Result: Enzyme places NOT in dependency graph")
    print(f"\n   2. _assign_layers() - assigns species to layers using topological sort")
    print(f"      - Uses dependency graph (which excludes enzymes)")
    print(f"      - Enzymes NOT assigned to any layer")
    print(f"\n   3. _position_layers() - positions species within layers")
    print(f"      - Only processes species in layers")
    print(f"      - Enzymes NOT positioned here")
    
    print(f"\n🔍 Current Behavior:")
    print(f"   - Connected enzyme places (with test arcs): NOT positioned by layout")
    print(f"   - Isolated enzyme places (no test arcs): NOT positioned by layout")
    print(f"   - Both cases: Enzyme position remains at original (KGML x,y) or (0,0)")
    
    print(f"\n💡 ROOT CAUSE:")
    print(f"   Hierarchical layout ONLY processes species in dependency graph")
    print(f"   Catalysts/modifiers are NOT in dependency graph")
    print(f"   Therefore catalysts keep original positions (or 0,0 if none)")
    
    print(f"\n✅ CLARIFICATION:")
    print(f"   This is NOT about isolated places disrupting layout")
    print(f"   This is about catalysts NOT BEING POSITIONED by layout")
    print(f"   Layout works fine for reactants/products, ignores catalysts")


def analyze_issue_4_disruption():
    """Issue 4: Isolated places disrupt layout algorithms."""
    print("\n" + "=" * 80)
    print("ISSUE 4: Layout Disruption from Isolated Places")
    print("=" * 80)
    
    print(f"\n📊 How Layout Could Be Disrupted:")
    print(f"\n   Scenario A: Force-directed layout")
    print(f"      - All nodes (including isolated) participate in forces")
    print(f"      - Isolated nodes have no edge constraints")
    print(f"      - Can drift to edges or overlap with connected nodes")
    print(f"      - ⚠️ Could disrupt connected component layout")
    
    print(f"\n   Scenario B: Hierarchical layout")
    print(f"      - Only processes nodes in dependency graph")
    print(f"      - Isolated nodes NOT in graph, NOT processed")
    print(f"      - Keep original positions (KGML x,y or 0,0)")
    print(f"      - ✓ Does NOT disrupt layout (just not positioned)")
    
    print(f"\n🔍 Actual Disruption:")
    print(f"   Based on ENZYME_LAYOUT_ISSUE.md:")
    print(f"   - Enzymes are NOT isolated (have test arcs)")
    print(f"   - But enzymes are NOT positioned by hierarchical layout")
    print(f"   - Result: Enzymes at original positions or (0,0)")
    print(f"   - Visual: Test arcs from (0,0) or wrong positions")
    
    print(f"\n💡 ROOT CAUSE:")
    print(f"   Not 'disruption' but 'missing positioning':")
    print(f"   - Layout algorithm works correctly for reactants/products")
    print(f"   - Layout algorithm ignores catalysts/modifiers")
    print(f"   - Catalysts need separate positioning logic")
    
    print(f"\n✅ FIX:")
    print(f"   Add _position_enzymes() method to hierarchical_layout.py:")
    print(f"   1. After _position_layers(), check for enzyme places")
    print(f"   2. For each enzyme with test arc to transition:")
    print(f"      - Use original KGML position if available")
    print(f"      - Otherwise position 'above' catalyzed reaction")
    print(f"   3. Update positions dictionary")


def main():
    """Run all analyses."""
    print("\n")
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 20 + "TEST ARC REFINEMENT ANALYSIS" + " " * 30 + "║")
    print("╚" + "═" * 78 + "╝")
    
    analyze_issue_1_rendering()
    analyze_issue_2_isolated()
    analyze_issue_3_layout()
    analyze_issue_4_disruption()
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"""
Issue 1: Test Arc Rendering
   Problem: Renders center-to-center instead of perimeter-to-perimeter
   Root Cause: TestArc.render() doesn't use _get_boundary_point()
   Fix: Update TestArc.render() to use boundary calculations
   Priority: MEDIUM (visual quality)

Issue 2: Isolated Catalyst Places
   Problem: Some enzyme places have no test arcs
   Root Cause: Test arc creation fails when enzyme.reaction doesn't match transition
   Fix: Either skip enzyme place creation or add visual indicator
   Priority: LOW (edge case in malformed data)

Issue 3: Catalysts Not Positioned by Layout
   Problem: Enzyme places not positioned by hierarchical layout
   Root Cause: Layout only processes dependency graph (reactants/products)
   Fix: Add _position_enzymes() method after main layout
   Priority: HIGH (affects all biological models)

Issue 4: "Disruption" Clarification
   Problem: Not actual disruption, but missing positioning
   Root Cause: Same as Issue 3 - catalysts ignored by layout
   Fix: Same as Issue 3 - position enzymes separately
   Priority: HIGH (same as Issue 3)

Recommended Action Plan:
   1. Fix Issue 3/4: Implement enzyme positioning (HIGH priority)
   2. Fix Issue 1: Update test arc rendering (MEDIUM priority)
   3. Fix Issue 2: Handle isolated enzymes gracefully (LOW priority)
""")
    print("=" * 80)


if __name__ == "__main__":
    main()
