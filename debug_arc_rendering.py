#!/usr/bin/env python3
"""
Add debug logging to Arc rendering to track what's being drawn.
This will help identify if extra lines are being drawn.
"""

import sys
sys.path.insert(0, 'src')

# Patch Arc.render to add logging
from shypn.netobjs import arc

original_render = arc.Arc.render

render_count = {}

def debug_render(self, cr, transform=None, zoom=1.0):
    """Wrapped render with debug logging."""
    # Count renders per arc
    arc_id = self.id
    render_count[arc_id] = render_count.get(arc_id, 0) + 1
    
    # Log every 60th frame (once per second at 60fps)
    if render_count[arc_id] % 60 == 1:
        src_label = getattr(self.source, 'label', self.source.id) if self.source else 'None'
        tgt_label = getattr(self.target, 'label', self.target.id) if self.target else 'None'
        print(f"[ARC RENDER] {self.id}: {src_label} → {tgt_label}")
    
    # Call original
    return original_render(self, cr, transform, zoom)

# Monkey patch
arc.Arc.render = debug_render

print("=" * 80)
print("ARC RENDERING DEBUG ENABLED")
print("=" * 80)
print("\nThis will print arc rendering info to console.")
print("Look for:")
print("  - Arcs rendering multiple times per frame")
print("  - Arcs with unexpected source/target")
print("  - Extra arcs not in your model")
print("\nLaunching GUI...")
print("=" * 80)
print()

# Launch GUI
from shypn import main
main()
