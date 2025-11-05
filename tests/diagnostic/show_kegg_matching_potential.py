#!/usr/bin/env python3
"""
Show Matching Potential with KEGG Import

Demonstrates how many database matches would occur if transitions
had EC numbers from KEGG import.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from shypn.crossfetch.database.heuristic_db import HeuristicDatabase


def analyze_matching_potential():
    """Analyze how many matches would occur with KEGG data."""
    
    print("=" * 80)
    print("KEGG IMPORT MATCHING POTENTIAL ANALYSIS")
    print("=" * 80)
    
    db = HeuristicDatabase()
    
    # Get all EC numbers in database
    all_params = db.query_parameters(limit=1000)
    ec_numbers = set(p['ec_number'] for p in all_params if p.get('ec_number'))
    
    print(f"\nDatabase has parameters for {len(ec_numbers)} unique EC numbers:")
    print()
    
    # Group by EC class
    by_class = {}
    for ec in sorted(ec_numbers):
        ec_class = ec.split('.')[0]
        class_name = {
            '1': 'Oxidoreductases',
            '2': 'Transferases', 
            '3': 'Hydrolases',
            '4': 'Lyases',
            '5': 'Isomerases',
            '6': 'Ligases'
        }.get(ec_class, 'Other')
        
        if class_name not in by_class:
            by_class[class_name] = []
        by_class[class_name].append(ec)
    
    # Show organized by class
    for class_name, ecs in sorted(by_class.items()):
        print(f"{class_name} (EC {ecs[0].split('.')[0]}.x.x.x): {len(ecs)} enzymes")
        
        # Show first few examples
        for ec in ecs[:5]:
            params = [p for p in all_params if p.get('ec_number') == ec]
            if params:
                p = params[0]
                enzyme = p.get('enzyme_name', 'Unknown')
                vmax = p['parameters'].get('vmax', 'N/A')
                km = p['parameters'].get('km', 'N/A')
                print(f"  • EC {ec}: {enzyme}")
                print(f"    Vmax={vmax}, Km={km}")
        
        if len(ecs) > 5:
            print(f"  ... and {len(ecs) - 5} more")
        print()
    
    # Show KEGG pathway example
    print("=" * 80)
    print("EXAMPLE: KEGG Glycolysis Pathway (hsa00010)")
    print("=" * 80)
    print()
    
    # Example glycolysis enzymes
    glycolysis_enzymes = [
        ("2.7.1.11", "Phosphofructokinase"),
        ("2.7.1.40", "Pyruvate kinase"),
        ("1.2.1.12", "Glyceraldehyde-3-phosphate dehydrogenase"),
        ("5.3.1.9", "Glucose-6-phosphate isomerase"),
        ("4.1.2.13", "Fructose-bisphosphate aldolase"),
        ("5.4.2.2", "Phosphoglyceromutase"),
        ("2.7.2.3", "Phosphoglycerate kinase"),
        ("4.2.1.11", "Enolase"),
        ("5.4.2.12", "Phosphoglucomutase"),
        ("2.7.1.1", "Hexokinase")
    ]
    
    print("If you import hsa00010 (Glycolysis), transitions will have:")
    print()
    
    matches_found = 0
    no_matches = []
    
    for ec, name in glycolysis_enzymes:
        # Check if database has this EC
        params = [p for p in all_params if p.get('ec_number') == ec]
        
        if params:
            p = params[0]
            vmax = p['parameters'].get('vmax', 'N/A')
            km = p['parameters'].get('km', 'N/A')
            organism = p['organism']
            source = p['source']
            confidence = p['confidence_score']
            
            print(f"✅ EC {ec}: {name}")
            print(f"   Match found! {source} ({organism})")
            print(f"   Vmax={vmax}, Km={km}, Confidence={confidence*100:.0f}%")
            print()
            matches_found += 1
        else:
            print(f"❌ EC {ec}: {name}")
            print(f"   No match - will use heuristics (Vmax=100, Km=0.1)")
            print()
            no_matches.append((ec, name))
    
    # Summary
    print("=" * 80)
    print("MATCHING SUMMARY")
    print("=" * 80)
    print()
    print(f"Glycolysis enzymes: {len(glycolysis_enzymes)}")
    print(f"Would match to database: {matches_found} ({matches_found/len(glycolysis_enzymes)*100:.1f}%)")
    print(f"Would use heuristics: {len(no_matches)} ({len(no_matches)/len(glycolysis_enzymes)*100:.1f}%)")
    print()
    
    if matches_found > 0:
        print("✨ DATABASE MATCHING WORKS!")
        print(f"   {matches_found} transitions would get real BioModels parameters")
        print(f"   Instead of generic heuristics")
        print()
    
    if no_matches:
        print("📝 Unmatched enzymes could be added by:")
        print("   - Importing more BioModels")
        print("   - Fetching from SABIO-RK")
        print("   - Manual parameter entry")
        print()
    
    # What user would see
    print("=" * 80)
    print("WHAT YOU WOULD SEE IN UI")
    print("=" * 80)
    print()
    print("WITHOUT KEGG (current situation):")
    print("┌─────────────────────────────────────────────────────────┐")
    print("│ ID  │ Source    │ EC/Enzyme │ Vmax  │ Km   │ Conf      │")
    print("├─────────────────────────────────────────────────────────┤")
    print("│ T1  │ Heuristic │ -         │ 100   │ 0.1  │ 60% ⭐⭐  │")
    print("│ T2  │ Heuristic │ -         │ 100   │ 0.1  │ 60% ⭐⭐  │")
    print("│ T3  │ Heuristic │ -         │ 50    │ 0.05 │ 75% ⭐⭐⭐│")
    print("└─────────────────────────────────────────────────────────┘")
    print()
    print("WITH KEGG IMPORT (what you'd get):")
    print("┌──────────────────────────────────────────────────────────────────┐")
    print("│ ID  │ Source    │ EC/Enzyme              │ Vmax   │ Km   │ Conf    │")
    print("├──────────────────────────────────────────────────────────────────┤")
    
    for i, (ec, name) in enumerate(glycolysis_enzymes[:5], 1):
        params = [p for p in all_params if p.get('ec_number') == ec]
        if params:
            p = params[0]
            vmax = p['parameters'].get('vmax', 100)
            km = p['parameters'].get('km', 0.1)
            source = p['source'][:8]  # Truncate
            confidence = p['confidence_score']
            stars = "⭐" * min(5, int(confidence * 5) + 1)
            print(f"│ T{i}  │ {source:<9} │ EC {ec} {name[:10]:<10} │ {vmax:<6.1f} │ {km:<4.2f} │ {confidence*100:.0f}% {stars:<4}│")
        else:
            print(f"│ T{i}  │ Heuristic │ EC {ec} {name[:10]:<10} │ 100.0  │ 0.1  │ 60% ⭐⭐ │")
    
    print("└──────────────────────────────────────────────────────────────────┘")
    print()
    
    print("🎯 Notice the difference:")
    print(f"   • {matches_found} transitions have real BioModels data")
    print("   • Vmax values are specific to each enzyme")
    print("   • Source shows where data came from")
    print("   • Confidence is higher (85% vs 60%)")
    print()
    
    # Instructions
    print("=" * 80)
    print("HOW TO TEST THIS")
    print("=" * 80)
    print()
    print("1. Open Shypn application")
    print("2. File → Import → Import from KEGG")
    print("3. Enter pathway ID: hsa00010 (Glycolysis)")
    print("4. Go to Pathway Operations → Heuristic Parameters")
    print("5. Select: Enhanced (Database Fetch)")
    print("6. Click: Analyze & Infer Parameters")
    print()
    print(f"Expected result: {matches_found}/{len(glycolysis_enzymes)} transitions match database!")
    print()


if __name__ == '__main__':
    analyze_matching_potential()
