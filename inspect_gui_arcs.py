#!/usr/bin/env python3
"""Script to inspect arcs in GUI after import.

This script will:
1. Import a KEGG pathway
2. Inspect manager.arcs to see what's actually there
3. Print details of all arcs including long ones
"""

import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from shypn.importer.kegg.kgml_parser import KGMLParser
from shypn.importer.kegg.pathway_converter import convert_pathway_enhanced
from shypn.pathway.options import EnhancementOptions
from shypn.data.model_canvas_manager import ModelCanvasManager

def inspect_arcs():
    """Inspect arcs after import."""
    print("=" * 80)
    print("GUI ARC INSPECTION")
    print("=" * 80)
    
    # Parse pathway
    kegg_file = "workspace/projects/kegg_hsa00010.xml"
    print(f"Parsing: {kegg_file}")
    
    parser = KGMLParser()
    pathway = parser.parse_file(kegg_file)
    print(f"Parsed: {len(pathway.entries)} entries, {len(pathway.reactions)} reactions, {len(pathway.relations)} relations")
    
    # Convert (no enhancements to keep it simple)
    print("\nConverting to Petri net...")
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
    
    print(f"Converted: {len(document.places)} places, {len(document.transitions)} transitions, {len(document.arcs)} arcs")
    
    # Create manager and load document (simulating GUI import)
    print("\nLoading into ModelCanvasManager...")
    manager = ModelCanvasManager()
    manager.places = list(document.places)
    manager.transitions = list(document.transitions)
    manager.arcs = list(document.arcs)
    manager._next_place_id = document._next_place_id
    manager._next_transition_id = document._next_transition_id
    manager._next_arc_id = document._next_arc_id
    
    print(f"\nManager loaded: {len(manager.places)} places, {len(manager.transitions)} transitions, {len(manager.arcs)} arcs")
    
    # Inspect all arcs
    print("\n" + "=" * 80)
    print("ARC ANALYSIS")
    print("=" * 80)
    
    place_to_place = []
    long_arcs = []
    
    for i, arc in enumerate(manager.arcs):
        source_type = type(arc.source).__name__
        target_type = type(arc.target).__name__
        
        dx = arc.target.x - arc.source.x
        dy = arc.target.y - arc.source.y
        distance = (dx*dx + dy*dy) ** 0.5
        
        source_label = getattr(arc.source, 'label', '?')
        target_label = getattr(arc.target, 'label', '?')
        
        if source_type == 'Place' and target_type == 'Place':
            place_to_place.append((i, source_label, target_label, distance))
        
        if distance > 500:
            long_arcs.append((i, source_type, source_label, target_type, target_label, distance))
    
    print(f"Total arcs: {len(manager.arcs)}")
    print(f"Place→Place arcs: {len(place_to_place)}")
    print(f"Long arcs (>500px): {len(long_arcs)}")
    
    if place_to_place:
        print("\n❌ FOUND PLACE→PLACE ARCS:")
        for idx, src, tgt, dist in place_to_place:
            print(f"  Arc #{idx}: {src} → {tgt} (distance={dist:.1f})")
    
    if long_arcs:
        print("\n⚠️  FOUND LONG ARCS:")
        for idx, src_type, src_label, tgt_type, tgt_label, dist in long_arcs:
            print(f"  Arc #{idx}: {src_type}({src_label}) → {tgt_type}({tgt_label}) (distance={dist:.1f})")
    
    print("\n" + "=" * 80)

if __name__ == '__main__':
    inspect_arcs()
