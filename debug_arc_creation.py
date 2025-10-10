#!/usr/bin/env python3
"""Debug script to intercept arc creation during KEGG import.

This script patches the ModelCanvasManager.add_arc() method to log
all arcs being added, including their source and target types.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from shypn.data.model_canvas_manager import ModelCanvasManager
from shypn.importer.kegg.kgml_parser import KGMLParser
from shypn.importer.kegg.pathway_converter import convert_pathway_enhanced
from shypn.pathway.options import EnhancementOptions

# Patch ModelCanvasManager to log arc additions
original_add_arc = ModelCanvasManager.add_arc

arc_log = []

def patched_add_arc(self, arc):
    """Patched add_arc that logs all arcs."""
    source_type = type(arc.source).__name__
    target_type = type(arc.target).__name__
    
    # Calculate distance
    dx = arc.target.x - arc.source.x
    dy = arc.target.y - arc.source.y
    distance = (dx*dx + dy*dy) ** 0.5
    
    log_entry = {
        'source': source_type,
        'target': target_type,
        'distance': distance,
        'source_label': getattr(arc.source, 'label', '?'),
        'target_label': getattr(arc.target, 'label', '?'),
    }
    arc_log.append(log_entry)
    
    print(f"Arc added: {source_type}({log_entry['source_label']}) → {target_type}({log_entry['target_label']}) [distance={distance:.1f}]")
    
    return original_add_arc(self, arc)

ModelCanvasManager.add_arc = patched_add_arc

# Parse and convert pathway
print("=" * 80)
print("KEGG IMPORT ARC CREATION DEBUG")
print("=" * 80)
print()

kegg_file = "workspace/projects/kegg_hsa00010.xml"
print(f"Parsing: {kegg_file}")

parser = KGMLParser()
pathway = parser.parse_file(kegg_file)

print(f"Parsed pathway: {len(pathway.entries)} entries, {len(pathway.reactions)} reactions, {len(pathway.relations)} relations")
print()

# Convert with no enhancements (to avoid extra arc modifications)
print("Converting to Petri net (no enhancements)...")
enhancement_options = EnhancementOptions(
    enable_layout_optimization=False,
    enable_arc_routing=False,
    enable_metadata_enhancement=False
)

document = convert_pathway_enhanced(
    pathway,
    coordinate_scale=1.0,
    include_cofactors=False,
    enhancement_options=enhancement_options
)

print()
print("=" * 80)
print(f"CONVERSION COMPLETE: {len(document.places)} places, {len(document.transitions)} transitions, {len(document.arcs)} arcs")
print("=" * 80)
print()

# Just analyze the document directly (don't need manager)
print("Analyzing document arcs directly...")
print()

# Analyze arcs from document
print("=" * 80)
print("DOCUMENT ARC ANALYSIS")
print("=" * 80)

place_to_place = []
trans_to_trans = []
long_arcs = []

for arc in document.arcs:
    source_type = type(arc.source).__name__
    target_type = type(arc.target).__name__
    
    dx = arc.target.x - arc.source.x
    dy = arc.target.y - arc.source.y
    distance = (dx*dx + dy*dy) ** 0.5
    
    source_label = getattr(arc.source, 'label', '?')
    target_label = getattr(arc.target, 'label', '?')
    
    if source_type == 'Place' and target_type == 'Place':
        place_to_place.append((source_label, target_label, distance))
    
    if source_type == 'Transition' and target_type == 'Transition':
        trans_to_trans.append((source_label, target_label, distance))
    
    if distance > 500:
        long_arcs.append((source_type, source_label, target_type, target_label, distance))

print(f"Total arcs in document: {len(document.arcs)}")
print(f"Place→Place arcs: {len(place_to_place)}")
print(f"Transition→Transition arcs: {len(trans_to_trans)}")
print(f"Long arcs (>500px): {len(long_arcs)}")

if place_to_place:
    print()
    print("❌ FOUND PLACE→PLACE ARCS:")
    for src, tgt, dist in place_to_place:
        print(f"  {src} → {tgt} (distance={dist:.1f})")

if long_arcs:
    print()
    print("⚠️  FOUND LONG ARCS:")
    for src_type, src_label, tgt_type, tgt_label, dist in long_arcs:
        print(f"  {src_type}({src_label}) → {tgt_type}({tgt_label}) (distance={dist:.1f})")

