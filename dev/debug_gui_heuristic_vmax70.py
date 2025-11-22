#!/usr/bin/env python3
"""
Debug why all transitions get Vmax=70, Km=0.1 in GUI workflow.

This script simulates the GUI workflow:
1. Import KEGG pathway (hsa00010 - Glycolysis)
2. Enrich KEGG names
3. Run heuristic inference
4. Analyze what happened

Expected: Diverse Vmax/Km values based on EC classes
Actual: All Vmax=70, Km=0.1

Hypothesis checklist:
[ ] EC numbers not extracted from names → Check if EC regex works
[ ] Arcs not attached → Check if input_arcs/output_arcs exist
[ ] Stoichiometry penalty applied incorrectly → Check stoich_info
[ ] Label patterns matching wrong defaults → Check what labels match 70.0
"""

import sys
sys.path.insert(0, 'src')

from shypn.data.canvas.document_model import DocumentModel
from shypn.adapters.kegg.kegg_pathway_importer import KEGGPathwayImporter
from shypn.services.kegg_name_enrichment_service import KEGGNameEnrichmentService
from shypn.crossfetch.inference.heuristic_engine import HeuristicInferenceEngine
import re

def main():
    print("=" * 80)
    print("DEBUGGING GUI HEURISTIC WORKFLOW - Vmax=70 Issue")
    print("=" * 80)
    
    # Step 1: Import KEGG pathway
    print("\n[1/4] Importing KEGG pathway hsa00010 (Glycolysis)...")
    importer = KEGGPathwayImporter()
    doc_model = importer.import_pathway('hsa00010')
    
    if not doc_model:
        print("❌ Failed to import pathway")
        return
    
    print(f"✓ Imported {len(doc_model.transitions)} transitions, {len(doc_model.places)} places")
    
    # Step 2: Enrich names
    print("\n[2/4] Enriching KEGG names...")
    enrichment_service = KEGGNameEnrichmentService()
    
    # Enrich places
    place_count = 0
    for place in doc_model.places:
        compound_id = getattr(place, 'kegg_compound_id', None)
        if compound_id:
            enriched_name = enrichment_service.get_compound_name(compound_id)
            if enriched_name:
                place.name = enriched_name
                place_count += 1
    
    # Enrich transitions  
    transition_count = 0
    for transition in doc_model.transitions:
        enzyme_id = getattr(transition, 'kegg_enzyme_id', None)
        if enzyme_id:
            enriched_name = enrichment_service.get_enzyme_name(enzyme_id)
            if enriched_name:
                transition.name = enriched_name
                transition_count += 1
    
    print(f"✓ Enriched {place_count} places, {transition_count} transitions")
    
    # Step 3: Attach arcs (simulate controller)
    print("\n[3/4] Attaching arcs to transitions...")
    for transition in doc_model.transitions:
        # Find input arcs (Place → Transition)
        input_arcs = [arc for arc in doc_model.arcs 
                     if hasattr(arc, 'target') and arc.target == transition]
        
        # Find output arcs (Transition → Place)
        output_arcs = [arc for arc in doc_model.arcs 
                      if hasattr(arc, 'source') and arc.source == transition]
        
        transition.input_arcs = input_arcs
        transition.output_arcs = output_arcs
    
    print(f"✓ Attached arcs to {len(doc_model.transitions)} transitions")
    
    # Step 4: Run heuristic inference
    print("\n[4/4] Running heuristic inference...")
    engine = HeuristicInferenceEngine()
    
    # Sample 5 transitions for detailed analysis
    sample_transitions = doc_model.transitions[:5]
    
    print("\n" + "=" * 80)
    print("DETAILED ANALYSIS (First 5 Transitions)")
    print("=" * 80)
    
    for i, transition in enumerate(sample_transitions, 1):
        print(f"\n--- Transition {i} ---")
        print(f"ID: {transition.id}")
        print(f"Name: {transition.name}")
        print(f"Label: {getattr(transition, 'label', 'N/A')}")
        
        # Check EC number
        ec_number = getattr(transition, 'ec_number', None)
        print(f"EC (attribute): {ec_number}")
        
        # Try extracting from name
        name = getattr(transition, 'name', '')
        ec_match = re.search(r'EC[_\s]*([\d\.]+)', name, re.IGNORECASE)
        if ec_match:
            extracted_ec = ec_match.group(1)
            print(f"EC (extracted): {extracted_ec}")
        else:
            print(f"EC (extracted): None (pattern not found in '{name}')")
        
        # Check arcs
        input_count = len(transition.input_arcs) if hasattr(transition, 'input_arcs') else 0
        output_count = len(transition.output_arcs) if hasattr(transition, 'output_arcs') else 0
        print(f"Input arcs: {input_count}")
        print(f"Output arcs: {output_count}")
        
        # Show substrates
        if input_count > 0:
            substrates = []
            for arc in transition.input_arcs:
                if hasattr(arc, 'source'):
                    place_name = getattr(arc.source, 'name', 'Unknown')
                    substrates.append(place_name)
            print(f"Substrates: {', '.join(substrates[:3])}{'...' if len(substrates) > 3 else ''}")
        else:
            print("Substrates: None")
        
        # Infer parameters
        params = engine._infer_continuous(transition)
        print(f"\nInferred Parameters:")
        print(f"  Vmax: {params.vmax} mM/s")
        print(f"  Km: {params.km} mM")
        print(f"  kcat: {params.kcat} 1/s")
        print(f"  Confidence: {params.confidence_score}")
        if params.notes:
            print(f"  Notes: {params.notes}")
    
    # Summary statistics
    print("\n" + "=" * 80)
    print("SUMMARY STATISTICS (All Transitions)")
    print("=" * 80)
    
    all_vmax = []
    all_km = []
    all_kcat = []
    
    for transition in doc_model.transitions:
        params = engine._infer_continuous(transition)
        all_vmax.append(params.vmax)
        all_km.append(params.km)
        all_kcat.append(params.kcat)
    
    unique_vmax = len(set(all_vmax))
    unique_km = len(set(all_km))
    unique_kcat = len(set(all_kcat))
    
    print(f"\nParameter Diversity:")
    print(f"  Unique Vmax values: {unique_vmax} (out of {len(all_vmax)})")
    print(f"  Unique Km values: {unique_km} (out of {len(all_km)})")
    print(f"  Unique kcat values: {unique_kcat} (out of {len(all_kcat)})")
    
    # Count how many have each value
    from collections import Counter
    vmax_counts = Counter(all_vmax)
    km_counts = Counter(all_km)
    
    print(f"\nMost common Vmax values:")
    for val, count in vmax_counts.most_common(3):
        print(f"  {val} mM/s: {count} transitions ({100*count/len(all_vmax):.1f}%)")
    
    print(f"\nMost common Km values:")
    for val, count in km_counts.most_common(3):
        print(f"  {val} mM: {count} transitions ({100*count/len(all_km):.1f}%)")
    
    # Diagnose the 70.0 issue
    print("\n" + "=" * 80)
    print("DIAGNOSIS: Why Vmax=70?")
    print("=" * 80)
    
    transitions_with_70 = [t for t, v in zip(doc_model.transitions, all_vmax) if v == 70.0]
    
    if transitions_with_70:
        print(f"\nFound {len(transitions_with_70)} transitions with Vmax=70.0")
        print("\nAnalyzing first 3:")
        
        for i, t in enumerate(transitions_with_70[:3], 1):
            print(f"\n{i}. {t.name}")
            label = getattr(t, 'label', '').lower()
            print(f"   Label: '{label}'")
            
            # Check which pattern matches
            if label.startswith('tpi') or label.startswith('gpi'):
                print("   → Matches isomerase pattern (tpi/gpi) → 70.0")
            elif label.startswith('pgam'):
                print("   → Matches mutase pattern (pgam) → 70.0")
            elif label.startswith('pgm') and not label.startswith('pgam'):
                print("   → Matches phosphoglucomutase pattern (pgm) → 70.0")
            elif 'isomerase' in label or 'epimerase' in label or 'mutase' in label:
                print("   → Matches isomerase/mutase pattern → 70.0")
            else:
                print("   → NO DIRECT 70.0 PATTERN MATCH!")
                print("   → May be getting 70.0 from stoichiometry penalty: 100 * 0.7 = 70")
    else:
        print("\n❌ No transitions with Vmax=70.0 found (unexpected!)")
    
    print("\n" + "=" * 80)
    print("END DIAGNOSIS")
    print("=" * 80)

if __name__ == '__main__':
    main()
