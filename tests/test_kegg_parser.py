#!/usr/bin/env python3
"""Test KGML parser with glycolysis pathway."""

import sys
sys.path.insert(0, '/home/simao/projetos/shypn/src')

from shypn.importer.kegg.kgml_parser import KGMLParser

def test_kgml_parser():
    """Test parsing KGML file."""
    print("=" * 60)
    print("Testing KGML Parser")
    print("=" * 60)
    
    parser = KGMLParser()
    
    # Parse the saved KGML file
    print("\nParsing /tmp/hsa00010.kgml...")
    pathway = parser.parse_file("/tmp/hsa00010.kgml")
    
    if not pathway:
        print("✗ Failed to parse KGML")
        return False
    
    print(f"\n✓ Successfully parsed pathway")
    print(f"  ID: {pathway.number}")
    print(f"  Name: {pathway.name}")
    print(f"  Organism: {pathway.org}")
    print(f"  Title: {pathway.title}")
    print(f"  Total entries: {len(pathway.entries)}")
    print(f"  Total reactions: {len(pathway.reactions)}")
    print(f"  Total relations: {len(pathway.relations)}")
    
    # Analyze entries by type
    print("\n" + "=" * 60)
    print("Entry Analysis:")
    compounds = pathway.get_compounds()
    genes = pathway.get_genes()
    
    print(f"  Compounds: {len(compounds)}")
    print(f"  Genes/Enzymes: {len(genes)}")
    print(f"  Other: {len(pathway.entries) - len(compounds) - len(genes)}")
    
    # Show sample compounds
    print("\n  Sample compounds:")
    for compound in compounds[:5]:
        print(f"    [{compound.id}] {compound.graphics.name[:40]}")
    
    # Show sample genes
    print("\n  Sample genes/enzymes:")
    for gene in genes[:5]:
        print(f"    [{gene.id}] {gene.graphics.name[:40]}")
    
    # Analyze reactions
    print("\n" + "=" * 60)
    print("Reaction Analysis:")
    reversible = [r for r in pathway.reactions if r.is_reversible()]
    irreversible = [r for r in pathway.reactions if not r.is_reversible()]
    
    print(f"  Reversible: {len(reversible)}")
    print(f"  Irreversible: {len(irreversible)}")
    
    # Show sample reaction
    if pathway.reactions:
        r = pathway.reactions[0]
        print(f"\n  Sample reaction [{r.id}]: {r.name}")
        print(f"    Type: {r.type}")
        print(f"    Substrates: {len(r.substrates)}")
        for s in r.substrates:
            entry = pathway.get_entry_by_id(s.id)
            name = entry.graphics.name[:30] if entry else "?"
            print(f"      [{s.id}] {name}")
        print(f"    Products: {len(r.products)}")
        for p in r.products:
            entry = pathway.get_entry_by_id(p.id)
            name = entry.graphics.name[:30] if entry else "?"
            print(f"      [{p.id}] {name}")
    
    # Analyze relations
    print("\n" + "=" * 60)
    print("Relation Analysis:")
    relation_types = {}
    for rel in pathway.relations:
        relation_types[rel.type] = relation_types.get(rel.type, 0) + 1
    
    for rel_type, count in sorted(relation_types.items()):
        print(f"  {rel_type}: {count}")
    
    # Show sample relation
    if pathway.relations:
        rel = pathway.relations[0]
        print(f"\n  Sample relation: {rel.entry1} → {rel.entry2}")
        print(f"    Type: {rel.type}")
        print(f"    Subtypes: {', '.join(rel.get_subtype_names())}")
    
    print("\n" + "=" * 60)
    print("✓ Parser test completed successfully!")
    print("=" * 60)
    return True

if __name__ == '__main__':
    try:
        success = test_kgml_parser()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
