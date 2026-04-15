#!/usr/bin/env python3
"""Debug script to inspect transition EC number fields.

This will help us understand what fields are actually available in transitions.
"""
import sys
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

sys.path.insert(0, '/home/simao/projetos/shypn/src')

print("=" * 60)
print("TRANSITION EC NUMBER DEBUG")
print("=" * 60)
print("\nThis script will help identify where EC numbers are stored.")
print("Please run SHYpn, load a KEGG model, then check this output.\n")

print("Checking transition structure...")
print("\nExpected fields to check:")
print("  1. transition.reaction_code")
print("  2. transition.metadata['ec_number']")
print("  3. transition.metadata['ec_numbers']")
print("  4. transition.metadata['kegg_reaction_id']")
print("  5. transition.metadata['enzyme']")
print("  6. transition.label")
print("\n" + "=" * 60)
print("\nTo debug a real model, add this code to _populate_reactions_table:")
print("""
# Debug EC number fields
print(f"\\n[EC_DEBUG] Transition {trans_id}:")
print(f"  label: {name}")
if hasattr(transition, 'reaction_code'):
    print(f"  reaction_code: {transition.reaction_code}")
if hasattr(transition, 'metadata') and transition.metadata:
    print(f"  metadata keys: {list(transition.metadata.keys())}")
    print(f"  ec_number: {transition.metadata.get('ec_number', 'NOT FOUND')}")
    print(f"  ec_numbers: {transition.metadata.get('ec_numbers', 'NOT FOUND')}")
    print(f"  kegg_reaction_id: {transition.metadata.get('kegg_reaction_id', 'NOT FOUND')}")
    print(f"  enzyme: {transition.metadata.get('enzyme', 'NOT FOUND')}")
    print(f"  enzyme_name: {transition.metadata.get('enzyme_name', 'NOT FOUND')}")
""")
print("=" * 60)
