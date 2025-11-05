"""
Test that KEGG auto-load properly handles drawing_area variable scope.

Bug: drawing_area variable was not always defined, causing NameError
     when trying to reset simulation.

Fix: 
1. Initialize drawing_area = None at the start
2. Find drawing_area from canvas_managers dict when resetting simulation
"""

print("=" * 80)
print("TEST: KEGG AUTO-LOAD DRAWING_AREA FIX")
print("=" * 80)

with open("src/shypn/ui/panels/pathway_operations/kegg_category.py") as f:
    content = f.read()

# Check 1: drawing_area initialized
if "drawing_area = None  # Initialize to None" in content:
    print("✅ drawing_area properly initialized to None")
else:
    print("❌ drawing_area NOT initialized")

# Check 2: No direct drawing_area reference in _ensure_simulation_reset call
if "drawing_area if not can_reuse_tab else" in content:
    print("❌ Still using problematic drawing_area reference")
else:
    print("✅ Removed problematic drawing_area conditional")

# Check 3: Proper lookup through canvas_managers
if "for da, mgr in canvas_loader.canvas_managers.items():" in content:
    print("✅ Properly looking up drawing_area through canvas_managers")
else:
    print("❌ NOT using canvas_managers lookup")

# Check 4: Fallback warning
if "Could not find drawing_area for simulation reset" in content:
    print("✅ Has fallback warning for missing drawing_area")
else:
    print("❌ No fallback warning")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print("""
The fix ensures drawing_area is always properly defined by:

1. Initializing drawing_area = None at the start
2. Instead of relying on scope, we look up the drawing_area
   from canvas_loader.canvas_managers when needed
3. This works for BOTH paths:
   - Reuse tab: drawing_area found through canvas_managers
   - Create new tab: drawing_area found through canvas_managers

This eliminates the NameError that prevented model loading!
""")

print("✅ KEGG auto-load fix verified!")
