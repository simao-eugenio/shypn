"""C1 verification — does evt_apply_thermodynamics actually fire?

Loads v3_p8, overrides TEMPERATURE / PH / AGE before run, advances the
simulator past t=0 a few steps, then inspects the four ◇ spatial-signal
places (Temperature_factor, Age_factor, pH_acidosis, pH_neutrality).

Expected if the event fires:
    TEMPERATURE = 320  ⇒ Temperature_factor = 2^((320-273.15-37)/10) ≈ 2.0
    AGE         = 85   ⇒ Age_factor         = 1 + 0.02*(85-65)        = 1.4
    PH          = 6.5  ⇒ pH_acidosis        = max(0, 7.0-6.5)         = 0.5
                         pH_neutrality       = 1 - 0.3*|6.5-7.4|       = 0.73

If the event does NOT fire, all four places stay at their static
initial markings (1.0, 1.2, 0.0, 1.0).
"""
from __future__ import annotations
import math
import os
import sys
from pathlib import Path

os.environ.setdefault("DISPLAY", "")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from shypn.data.canvas.document_model import DocumentModel  # noqa: E402
from shypn.engine.simulation.controller import SimulationController  # noqa: E402

MODEL = ROOT / "workspace/projects/canabidiol/models/cbd_ad_neuroprotection_v3_p8.shy"

OVERRIDES = {"TEMPERATURE": 320.0, "PH": 6.5, "AGE": 85.0}

EXPECTED = {
    "Temperature_factor": 2 ** (((320.0 - 273.15) - 37) / 10),
    "Age_factor":         1 + 0.02 * (85.0 - 65.0),
    "pH_acidosis":        max(0.0, 7.0 - 6.5),
    "pH_neutrality":      1 - 0.3 * abs(6.5 - 7.4),
}

STATIC_INITIAL = {
    "Temperature_factor": 1.0,
    "Age_factor":         1.2,
    "pH_acidosis":        0.0,
    "pH_neutrality":      1.0,
}


def main() -> int:
    print(f"Loading {MODEL.name}...")
    model = DocumentModel.load_from_file(str(MODEL))

    by_name = {p.name: p for p in model.places}
    print(f"Model has {len(model.places)} places, "
          f"{len(model.transitions)} transitions, "
          f"{len(getattr(model, 'events', []))} events.")
    print()

    print("=== Overriding parameter places (before run) ===")
    for name, val in OVERRIDES.items():
        place = by_name[name]
        before = place.tokens
        place.tokens = val
        if hasattr(place, "initial_tokens"):
            place.initial_tokens = val
        if hasattr(place, "initial_marking"):
            place.initial_marking = val
        print(f"  {name:15s} {before:10.3f} -> {place.tokens:10.3f}")
    print()

    print("=== Spatial signals BEFORE run ===")
    for name in EXPECTED:
        print(f"  {name:25s} = {by_name[name].tokens:.4f}")
    print()

    # Build controller and step until t > ~150 s so all event triggers
    # (t > 0.0, t > 0.01, t > 0.1, t > 60) have a chance to fire.
    controller = SimulationController(model)
    controller.settings.use_tau_leaping = True
    controller.settings.duration = 200.0
    controller.time = 0.0

    print("=== Stepping engine until t > 150 s (covers all event triggers) ===")
    target_time = 150.0
    n_steps = 0
    while controller.time < target_time and n_steps < 200000:
        controller.step()
        n_steps += 1
    print(f"  controller.time = {controller.time:.4f}  (after {n_steps} steps)")
    print()

    print("=== Spatial signals AFTER run ===")
    print(f"  {'place':25s}  {'observed':>10s}  {'expected':>10s}  {'static_init':>12s}  {'verdict':>20s}")
    all_pass = True
    fired_any = False
    for name, expected in EXPECTED.items():
        observed = by_name[name].tokens
        static = STATIC_INITIAL[name]
        if math.isclose(observed, expected, rel_tol=0.02, abs_tol=0.01):
            verdict = "✓ MATCHES expected"
            fired_any = True
        elif math.isclose(observed, static, rel_tol=1e-6, abs_tol=1e-6):
            verdict = "✗ stayed at static"
            all_pass = False
        else:
            verdict = "? unexpected value"
            all_pass = False
        print(f"  {name:25s}  {observed:>10.4f}  {expected:>10.4f}  {static:>12.4f}  {verdict:>20s}")
    print()

    print("=== Event last-triggered map (controller._event_last_triggered) ===")
    if hasattr(controller, "_event_last_triggered"):
        for k, v in controller._event_last_triggered.items():
            print(f"  {k}: {v}")
    else:
        print("  (no _event_last_triggered attribute)")
    print()

    if all_pass:
        print("RESULT: ✓ evt_apply_thermodynamics fires correctly. Pattern-A bridge OK.")
        return 0
    if not fired_any:
        print("RESULT: ✗ evt_apply_thermodynamics did NOT fire. Trigger string '0.0' is not parsed as 'fire at t=0'.")
        return 2
    print("RESULT: ⚠ partial — some assignments fired but values mismatch. Inspect.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
