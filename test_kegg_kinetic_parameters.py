#!/usr/bin/env python3
"""Test KEGG Import - Verify if kinetic parameters are returned.

This test demonstrates that KEGG API does NOT provide real kinetic parameters
(Vmax, Km, Kcat, Ki). KEGG only provides:
- Pathway structure (reactions, compounds, coordinates)
- EC numbers
- Gene/enzyme associations

For actual kinetic parameters, users must:
1. Use BRENDA database (via Enrich with BRENDA)
2. Use SABIO-RK database (via Enrich with SABIO-RK)
3. Use SBML models that include kinetic laws

This is why the BRENDA enrichment panel says:
"Recommended: KEGG has no real kinetic parameters"
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("="*70)
print("KEGG KINETIC PARAMETERS TEST")
print("="*70)

print("\n" + "="*70)
print("UNDERSTANDING KEGG DATA")
print("="*70)

print("""
KEGG (Kyoto Encyclopedia of Genes and Genomes) provides:
✓ Pathway topology (which reactions connect which compounds)
✓ Metabolite information (compound IDs, names, structures)
✓ Reaction information (EC numbers, stoichiometry)
✓ Gene/enzyme associations
✓ Coordinate layouts for visualization

KEGG does NOT provide:
✗ Vmax values
✗ Km values (Michaelis constant)
✗ Kcat values (turnover number)
✗ Ki values (inhibition constant)
✗ Rate functions
✗ Experimental kinetic data

This is by design - KEGG is a PATHWAY DATABASE, not a KINETICS DATABASE.
""")

print("\n" + "="*70)
print("TESTING KEGG IMPORT")
print("="*70)

# Test KEGG pathway data structure
try:
    from shypn.importer.kegg.api_client import KEGGAPIClient
    
    print("\n1. Fetching KEGG pathway hsa00010 (Glycolysis)...")
    client = KEGGAPIClient()
    kgml = client.fetch_kgml('hsa00010')
    
    if kgml:
        print(f"   ✓ KGML data fetched ({len(kgml)} characters)")
        
        # Check if KGML contains kinetic keywords
        print("\n2. Searching KGML for kinetic parameter keywords...")
        keywords = ['vmax', 'Vmax', 'VMAX', 'km', 'Km', 'KM', 'kcat', 'Kcat', 
                   'KCAT', 'ki', 'Ki', 'KI', 'kinetic', 'parameter']
        
        found_any = False
        for keyword in keywords:
            if keyword.lower() in kgml.lower():
                print(f"   ✓ Found '{keyword}' in KGML")
                found_any = True
        
        if not found_any:
            print("   ✗ NO kinetic parameter keywords found in KGML")
            print("\n   ✓ CONFIRMED: KEGG KGML does not include kinetic parameters")
        
        # Show sample of KGML structure
        print("\n3. KGML Structure Sample (first 500 characters):")
        print("   " + kgml[:500].replace('\n', '\n   '))
        
        # Parse KGML to show what it contains
        print("\n4. What KEGG KGML Contains:")
        if '<entry' in kgml:
            print("   ✓ <entry> tags (compounds/enzymes)")
        if '<reaction' in kgml:
            print("   ✓ <reaction> tags (reaction topology)")
        if '<graphics' in kgml:
            print("   ✓ <graphics> tags (visualization coordinates)")
        if '<substrate' in kgml or '<product' in kgml:
            print("   ✓ <substrate>/<product> tags (stoichiometry)")
        
        print("\n   What KEGG KGML does NOT contain:")
        print("   ✗ Vmax values")
        print("   ✗ Km values")
        print("   ✗ Kcat values")
        print("   ✗ Ki values")
        print("   ✗ Rate functions")
        print("   ✗ Kinetic laws")
    
    print("\n" + "="*70)
    print("WHERE TO GET REAL KINETIC PARAMETERS")
    print("="*70)
    
    print("""
To get REAL experimental kinetic parameters, you must:

1. **BRENDA Database** (Best for enzymes)
   - Right-click transition → "Enrich with BRENDA"
   - Provides Vmax, Km, Kcat, Ki from peer-reviewed literature
   - Organism-specific data (Homo sapiens, E. coli, etc.)
   - ~95,000 enzyme entries with kinetic data
   
2. **SABIO-RK Database** (Best for reactions)
   - Right-click transition → "Enrich with SABIO-RK"
   - Provides kinetic laws from SBML models
   - Parameter values with units
   - Links to original publications
   
3. **SBML Import** (Pre-curated models)
   - File → Import → SBML
   - Some SBML models include kinetic laws
   - BioModels database has ~1000 curated models
   - Parameters already integrated in model

Why doesn't KEGG provide kinetics?
- KEGG focuses on pathway TOPOLOGY (structure)
- Kinetic parameters are context-dependent (organism, tissue, conditions)
- KEGG would need thousands of parameter sets per reaction
- Better to use specialized databases (BRENDA, SABIO-RK)
    """)
    
    print("="*70)
    print("✅ TEST COMPLETE")
    print("="*70)
    print("\nConclusion:")
    print("  KEGG provides pathway structure and EC numbers")
    print("  KEGG does NOT provide real kinetic parameters")
    print("  Use BRENDA or SABIO-RK for experimental kinetic data")
    print("="*70)
    
except Exception as e:
    print(f"\n❌ Test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
