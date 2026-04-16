#!/usr/bin/env python3
"""Test BiGG namespace parser with actual model IDs."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from shypn.importer.bigg.bigg_namespace_parser import BiGGNamespaceParser

parser = BiGGNamespaceParser()

test_ids = [
    "M_atp_c",
    "M_adp_c",
    "M_nad_c",
    "M_nadh_c",
    "M_coa_c",
    "M_glc__D_e",
    "M_h2o_c"
]

print("Testing BiGG namespace parser:")
print("="*60)

for bigg_id in test_ids:
    metabolite_id, compartment = parser.parse_species_id(bigg_id)
    is_energy = parser.is_energy_metabolite(metabolite_id)
    compartment_name = parser.get_compartment_name(compartment)
    
    print(f"\nBiGG ID: {bigg_id}")
    print(f"  Metabolite: {metabolite_id}")
    print(f"  Compartment: {compartment} ({compartment_name})")
    print(f"  Is Energy: {is_energy}")
