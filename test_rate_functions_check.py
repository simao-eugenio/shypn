#!/usr/bin/env python3
"""
Quick diagnostic: Check if rate functions were auto-generated on transitions.

Run this after doing BRENDA enrichment to verify that transitions now have
rate_function properties set.
"""

import sys
sys.path.insert(0, '/home/simao/projetos/shypn/src')

from shypn.document.document_model import DocumentModel

def check_rate_functions():
    """Check transitions for auto-generated rate functions."""
    
    # Try to load the current model (if saved)
    # For now, just print instructions
    print("\n" + "="*70)
    print("RATE FUNCTION DIAGNOSTIC")
    print("="*70)
    print("\nTo check if rate functions were auto-generated:")
    print("\n1. In the Shypn UI, right-click on an enriched transition (T19, T15, etc.)")
    print("2. Select 'Properties' from the context menu")
    print("3. Look for 'rate_function' field in the properties dialog")
    print("4. It should show something like:")
    print("     michaelis_menten(P_glucose, 2.5, 0.05)")
    print("\nExpected rate functions based on your BRENDA enrichment:")
    print("\n  T19 (Hexokinase):        michaelis_menten(substrate, 2.5, 0.05)")
    print("  T15 (Phosphofructo...):  michaelis_menten(substrate, 5.8, 0.08)")
    print("  T17 (Glucose-6-P iso):   michaelis_menten(substrate, 8.5, 0.18)")
    print("  T29 (Phosphoglycerate):  michaelis_menten(substrate, 22.0, 0.12)")
    print("\nWith competitive inhibition (if Ki > 0 and inhibitor place detected):")
    print("  Format: michaelis_menten(S, Vmax, Km * (1 + I/Ki))")
    print("\n" + "="*70)
    
    # Alternative: Try to connect to running app via document state
    print("\nAlternative: Check terminal output for [BRENDA_MM] messages")
    print("These should appear when enrichment happens:")
    print("  [BRENDA_MM] ========== RATE FUNCTION GENERATOR CALLED ==========")
    print("  [BRENDA_MM] Found input place: P_glucose")
    print("  [BRENDA_MM] Generated simple MM: michaelis_menten(...)")
    print("  [BRENDA_MM] ✅ Successfully set rate_function on transition T19")
    print("\nIf you don't see these messages, check:")
    print("  1. Is transition_obj being passed correctly? (check logs for 'transition_obj')")
    print("  2. Are there any exceptions being caught silently?")
    print("  3. Is the function being called at all? (check apply_enrichment_to_transition)")
    print("="*70 + "\n")

if __name__ == '__main__':
    check_rate_functions()
