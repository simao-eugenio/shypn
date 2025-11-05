"""
Diagnose why KEGG auto-load isn't working.
"""

print("=" * 80)
print("AUTO-LOAD DIAGNOSIS")
print("=" * 80)

print("\n1. CHECKING KEGG CATEGORY AUTO-LOAD FLOW:")
with open("src/shypn/ui/panels/pathway_operations/kegg_category.py") as f:
    kegg_lines = f.readlines()

# Find where canvas_manager gets objects loaded
for i, line in enumerate(kegg_lines, 1):
    if i >= 625 and i <= 730:
        if any(key in line for key in ['canvas_loader', 'canvas_manager', 'load_objects', 'fit_to_page', 'mark_needs_redraw']):
            print(f"  {i}: {line.rstrip()}")

print("\n" + "=" * 80)
print("2. CHECKING RESET_MANAGER_FOR_LOAD:")
with open("src/shypn/helpers/model_canvas_loader.py") as f:
    loader_lines = f.readlines()

in_reset = False
for i, line in enumerate(loader_lines, 1):
    if "def _reset_manager_for_load" in line:
        in_reset = True
        print(f"\n  Found at line {i}")
    
    if in_reset:
        if "_suppress_callbacks" in line:
            print(f"  {i}: {line.rstrip()}")
        if line.strip().startswith("def ") and "_reset_manager_for_load" not in line:
            break

print("\n" + "=" * 80)
print("3. CRITICAL SEQUENCE CHECK:")
print("=" * 80)

print("""
For auto-load to work, this must happen IN ORDER:

1. ✓ canvas_manager = get canvas manager
2. ✓ _reset_manager_for_load(canvas_manager, filename)
      → Sets _suppress_callbacks = False
3. ✓ canvas_manager.load_objects(places, transitions, arcs)
      → Adds objects to manager
4. ✓ canvas_manager.set_change_callback(...)
      → Wires up change detection
5. ✓ canvas_manager.mark_clean()
      → Prevents asterisk
6. ✓ canvas_manager.fit_to_page(deferred=True)
      → Schedules fit for next draw
7. ✓ canvas_manager.mark_needs_redraw()
      → Triggers draw event
8. ? _ensure_simulation_reset(drawing_area)
      → Resets simulation state

POTENTIAL ISSUE: Step 8 might be resetting TOO MUCH!
""")

# Check what _ensure_simulation_reset does
print("\n4. CHECKING _ensure_simulation_reset:")
in_ensure = False
for i, line in enumerate(loader_lines, 1):
    if "def _ensure_simulation_reset" in line:
        in_ensure = True
        print(f"\n  Found at line {i}")
    
    if in_ensure:
        if i < 900:  # Limit output
            print(f"  {i}: {line.rstrip()}")
        if line.strip() and line.strip().startswith("def ") and "_ensure_simulation_reset" not in line:
            break

