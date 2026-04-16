#!/usr/bin/env python3
"""Interactive demonstration of bidirectional compound mapping.

Shows how name ↔ ID auto-suggestion works in the thermodynamic properties dialog.
"""

import sys
sys.path.insert(0, 'src')

from shypn.thermodynamics.compound_mapper import CompoundMapper


def demo_name_to_id():
    """Demonstrate: User types compound name → System suggests ID."""
    print("=" * 60)
    print("SCENARIO 1: User creates a place for ATP")
    print("=" * 60)
    print()
    print("User actions:")
    print("  1. Creates new place (gets default name 'P1')")
    print("  2. Opens Place Properties dialog")
    print("  3. Types 'ATP' in Name field")
    print()
    print("System response:")
    print("  → Detects 'ATP' matches known compound")
    
    # Simulate lookup
    compound_id = CompoundMapper.name_to_id("ATP")
    if compound_id:
        print(f"  → Auto-suggests compound_id: '{compound_id}'")
        print(f"  → Populates 'Compound Name' label: 'ATP'")
        print(f"  → Shows info icon: 'Suggestion from place name \"ATP\"'")
    
    print()
    print("✅ User saves → Place.name='ATP' + compound_id='C00002'")
    print()


def demo_id_to_name():
    """Demonstrate: User types compound ID → System suggests name."""
    print("=" * 60)
    print("SCENARIO 2: User fetches compound data by ID")
    print("=" * 60)
    print()
    print("User actions:")
    print("  1. Creates new place (gets default name 'P5')")
    print("  2. Opens Place Properties → Thermodynamics tab")
    print("  3. Types 'C00031' in Compound ID field")
    print()
    print("System response:")
    print("  → Looks up C00031 in compound database")
    
    # Simulate lookup
    compound_name = CompoundMapper.id_to_name("C00031")
    if compound_name:
        print(f"  → Finds: '{compound_name}'")
        print(f"  → Populates 'Compound Name' label: '{compound_name}'")
        print(f"  → Auto-fills Name field: '{compound_name}' (if still default 'P5')")
        print(f"  → Shows info icon: 'Suggestion from compound ID C00031'")
    
    print()
    print("✅ User saves → Place.name='Glucose' + compound_id='C00031'")
    print()


def demo_fuzzy_search():
    """Demonstrate: Partial name search."""
    print("=" * 60)
    print("SCENARIO 3: User searches for compound")
    print("=" * 60)
    print()
    print("User actions:")
    print("  1. Opens Place Properties dialog")
    print("  2. Types 'glut' in Name field")
    print()
    print("System response:")
    print("  → Searches for compounds matching 'glut'")
    
    # Simulate search
    suggestions = CompoundMapper.suggest_names("glut", max_results=5)
    if suggestions:
        print(f"  → Found {len(suggestions)} matches:")
        for name, compound_id in suggestions:
            print(f"      • {name} ({compound_id})")
    
    print()
    print("Note: Full autocomplete dropdown could be added in future")
    print("      Current implementation: auto-fills on exact match")
    print()


def demo_coverage():
    """Show coverage of common metabolites."""
    print("=" * 60)
    print("SUPPORTED COMPOUNDS (80+ metabolites)")
    print("=" * 60)
    print()
    
    categories = {
        'Energy carriers': ['ATP', 'ADP', 'AMP', 'NAD+', 'NADH', 'NADPH', 'FAD'],
        'Glycolysis': ['Glucose', 'G6P', 'F6P', 'Pyruvate', 'Lactate'],
        'TCA cycle': ['Citrate', 'Succinate', 'Malate', 'Oxaloacetate'],
        'Amino acids': ['Glutamate', 'Glutamine', 'Alanine', 'Glycine'],
    }
    
    for category, compounds in categories.items():
        print(f"{category}:")
        for name in compounds:
            compound_id = CompoundMapper.name_to_id(name)
            if compound_id:
                print(f"  • {name:20s} ↔ {compound_id}")
        print()


if __name__ == '__main__':
    print()
    print("╔" + "═" * 58 + "╗")
    print("║  BIDIRECTIONAL COMPOUND MAPPING - INTERACTIVE DEMO      ║")
    print("╚" + "═" * 58 + "╝")
    print()
    
    demo_name_to_id()
    input("Press Enter to continue...")
    
    demo_id_to_name()
    input("Press Enter to continue...")
    
    demo_fuzzy_search()
    input("Press Enter to continue...")
    
    demo_coverage()
    
    print("=" * 60)
    print("BENEFITS")
    print("=" * 60)
    print()
    print("✅ Faster workflow: Type 'ATP' → Get 'C00002' automatically")
    print("✅ Fewer errors: No need to remember compound IDs")
    print("✅ Consistency: Place name matches compound identity")
    print("✅ Discovery: See suggestions for partial names")
    print()
    print("Try it!")
    print("  1. Create a new place")
    print("  2. Open Place Properties dialog")
    print("  3. Type 'Glucose' in Name field")
    print("  4. Switch to Thermodynamics tab")
    print("  5. See 'C00031' auto-populated in Compound ID")
    print()
