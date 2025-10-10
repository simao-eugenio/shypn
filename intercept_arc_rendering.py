#!/usr/bin/env python3
"""
Final diagnostic: Print every arc that would be rendered and check for issues.
Run this, then import a pathway and check the console output.
"""

import sys
sys.path.insert(0, 'src')

# Monkey-patch Arc.render() to log what's being drawn
from shypn.netobjs import arc

original_render = arc.Arc.render
render_calls = []

def debug_render(self, cr, transform=None, zoom=1.0):
    """Wrapped render with detailed logging."""
    
    # Get source and target info
    src_id = self.source.id if self.source else "None"
    tgt_id = self.target.id if self.target else "None"
    
    src_x = self.source.x if self.source else 0
    src_y = self.source.y if self.source else 0
    tgt_x = self.target.x if self.target else 0
    tgt_y = self.target.y if self.target else 0
    
    src_label = getattr(self.source, 'label', src_id)
    tgt_label = getattr(self.target, 'label', tgt_id)
    
    # Calculate distance
    import math
    distance = math.sqrt((tgt_x - src_x)**2 + (tgt_y - src_y)**2)
    
    # Store call info
    call_info = {
        'arc_id': self.id,
        'src': src_label,
        'tgt': tgt_label,
        'src_pos': (src_x, src_y),
        'tgt_pos': (tgt_x, tgt_y),
        'distance': distance
    }
    render_calls.append(call_info)
    
    # Print suspicious arcs immediately
    if distance > 500:
        print(f"⚠️  LONG ARC: {self.id} {src_label} → {tgt_label} ({distance:.0f} px)")
    
    # Call original
    return original_render(self, cr, transform, zoom)

# Monkey patch
arc.Arc.render = debug_render

print("=" * 80)
print("ARC RENDERING INTERCEPTOR ACTIVE")
print("=" * 80)
print("\nThis will log every arc rendered to the console.")
print("Look for:")
print("  - Arcs with distance > 500 pixels (suspiciously long)")
print("  - Same arc rendered multiple times")
print("  - Arcs with unexpected endpoints")
print("\nImport a pathway and watch the console...")
print("=" * 80)
print()

# Also patch get_all_objects to see if it's called multiple times per frame
from shypn.data import model_canvas_manager

original_get_all = model_canvas_manager.ModelCanvasManager.get_all_objects
get_all_count = 0

def debug_get_all(self):
    global get_all_count
    get_all_count += 1
    if get_all_count % 60 == 1:  # Every 60 frames
        arc_count = len(self.arcs)
        print(f"[get_all_objects] Frame {get_all_count}: returning {arc_count} arcs")
    return original_get_all(self)

model_canvas_manager.ModelCanvasManager.get_all_objects = debug_get_all

# Launch GUI
from shypn import main
try:
    main()
finally:
    # Print summary
    print("\n" + "=" * 80)
    print("RENDERING SUMMARY")
    print("=" * 80)
    
    if render_calls:
        print(f"\nTotal arc render calls: {len(render_calls)}")
        
        # Find suspicious long arcs
        long_arcs = [c for c in render_calls if c['distance'] > 500]
        if long_arcs:
            print(f"\n⚠️  {len(long_arcs)} suspiciously long arcs (>500px):")
            for call in long_arcs[:10]:
                print(f"   {call['arc_id']}: {call['src']} → {call['tgt']} ({call['distance']:.0f} px)")
        
        # Check for duplicates
        arc_ids = [c['arc_id'] for c in render_calls]
        from collections import Counter
        counts = Counter(arc_ids)
        duplicates = {aid: count for aid, count in counts.items() if count > 10}
        
        if duplicates:
            print(f"\n⚠️  Arcs rendered many times (might be normal for animation):")
            for arc_id, count in list(duplicates.items())[:5]:
                print(f"   Arc {arc_id}: {count} times")
    else:
        print("\nNo arcs rendered yet.")
