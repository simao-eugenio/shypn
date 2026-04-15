#!/usr/bin/env python3
"""
Create phase3a_spatial_scaled.shy
===================================
Loads phase3a_spatial_clean.shy and scales all place initial conditions
by 0.1×, excluding physical constants (pH, Temperature).

The scaled model is for the IC-scale sensitivity experiment (Research Q4):
testing whether zero stochastic heterogeneity at EPO* is physical
or a numerical artefact of the high-concentration (µM) regime.

Output:
    workspace/projects/gata/models/phase3a_spatial_scaled.shy
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from shypn.data.canvas.document_model import DocumentModel

# ── Configuration ────────────────────────────────────────────────────────────
MODEL_IN  = "workspace/projects/gata/models/phase3a_spatial_clean.shy"
MODEL_OUT = "workspace/projects/gata/models/phase3a_spatial_scaled.shy"
SCALE     = 0.1

# Place names that represent physical constants — must NOT be scaled
PHYSICAL_CONSTANTS = {
    "pH_cytoplasm",
    "pH_nucleus",
    "Temperature",
}

# ── Load ─────────────────────────────────────────────────────────────────────
print(f"Loading: {MODEL_IN}")
model = DocumentModel.load_from_file(MODEL_IN)
print(f"  Places: {len(model.places)}, Transitions: {len(model.transitions)}")

# ── Scale ────────────────────────────────────────────────────────────────────
print(f"\nScaling place ICs by {SCALE}×  (excluding: {PHYSICAL_CONSTANTS})\n")
print(f"  {'Place name':<30}  {'Original':>12}  {'Scaled':>12}  {'Skipped':>8}")
print(f"  {'-'*30}  {'-'*12}  {'-'*12}  {'-'*8}")

scaled_count = 0
skipped_count = 0

for place in model.places:
    original = place.initial_marking
    if place.name in PHYSICAL_CONSTANTS:
        print(f"  {place.name:<30}  {original:>12.4f}  {'—':>12}  {'yes':>8}  (physical constant)")
        skipped_count += 1
        continue

    scaled = original * SCALE
    place.initial_marking = scaled
    place.tokens = scaled
    if hasattr(place, 'marking'):
        place.marking = scaled

    print(f"  {place.name:<30}  {original:>12.4f}  {scaled:>12.4f}")
    scaled_count += 1

print(f"\n  Scaled: {scaled_count} places    Skipped: {skipped_count} places")

# ── Save ─────────────────────────────────────────────────────────────────────
print(f"\nSaving: {MODEL_OUT}")
model.save_to_file(MODEL_OUT)
print("Done.")

# ── Verify round-trip ────────────────────────────────────────────────────────
print("\nVerifying round-trip...")
verify = DocumentModel.load_from_file(MODEL_OUT)
errors = []
for orig_place in model.places:
    vp = next((p for p in verify.places if p.id == orig_place.id), None)
    if vp is None:
        errors.append(f"MISSING place {orig_place.id} ({orig_place.name})")
        continue
    if abs(vp.initial_marking - orig_place.initial_marking) > 1e-12:
        errors.append(
            f"MISMATCH {orig_place.name}: "
            f"expected {orig_place.initial_marking}, got {vp.initial_marking}"
        )

if errors:
    print("ERRORS:")
    for e in errors:
        print(f"  {e}")
    sys.exit(1)
else:
    print(f"  All {len(verify.places)} places verified OK.")
    print(f"  Output: {MODEL_OUT}")
