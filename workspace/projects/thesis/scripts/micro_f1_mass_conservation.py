"""F1 mass-conservation micro-test.

Replicates the v4 thesis Source_ATP_regen wiring at minimum complexity:

    ADP_pool --signal_flow(W=40)--> T_regen --curved_opposite_signal_flow(W=40)--> ATP_pool

Continuous transition, rate = 1.0 (constant). Run 100 s.

Expected if `signal_flow` and `curved_opposite_signal_flow` are both
consumption/production at rate*W*dt: ATP gains ~4000, ADP loses ~4000,
sum stays at 5000.

If sum != 5000 ⇒ engine is asymmetric on the two arc types ⇒ this is
the leak source in the v4 sweep.
"""

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from shypn.data.canvas.document_model import DocumentModel
from shypn.engine.simulation.controller import SimulationController


def build_model_dict():
    return {
        "version": "2.0",
        "metadata": {"object_counts": {"places": 2, "transitions": 1, "arcs": 2}},
        "places": [
            {
                "id": "P1", "name": "ATP_pool", "label": "ATP_pool",
                "object_type": "place", "x": 0, "y": 0, "radius": 30.0,
                "marking": 0.0, "initial_marking": 0.0, "capacity": "Infinity",
                "is_signal_place": False,
            },
            {
                "id": "P2", "name": "ADP_pool", "label": "ADP_pool",
                "object_type": "place", "x": 200, "y": 0, "radius": 30.0,
                "marking": 5000.0, "initial_marking": 5000.0, "capacity": "Infinity",
                "is_signal_place": False,
            },
        ],
        "transitions": [
            {
                "id": "T1", "name": "T_regen", "label": "T_regen",
                "object_type": "transition", "x": 100, "y": 0,
                "width": 40.0, "height": 20.0, "horizontal": True,
                "transition_type": "continuous", "guard": "1",
                "is_source": False, "is_sink": False,
                "properties": {"rate_function": "1.0"},
            }
        ],
        "arcs": [
            {
                "id": "A1", "name": "A1", "object_type": "arc",
                "arc_type": "signal_flow",
                "source_id": "P2", "source_type": "place",
                "target_id": "T1", "target_type": "transition",
                "weight": 40.0, "threshold": 0,
                "consumes": True, "produces": True,
            },
            {
                "id": "A2", "name": "A2", "object_type": "curved_arc",
                "arc_type": "curved_opposite_signal_flow",
                "source_id": "T1", "source_type": "transition",
                "target_id": "P1", "target_type": "place",
                "weight": 40.0,
            },
        ],
        "arc_type": "normal",
        "modules": [], "events": [],
    }


def run_variant(label, mutator=None):
    md = build_model_dict()
    if mutator:
        mutator(md)
    with tempfile.NamedTemporaryFile("w", suffix=".shy", delete=False) as f:
        json.dump(md, f)
        path = f.name

    model = DocumentModel.load_from_file(path)

    atp = next(p for p in model.places if p.name == "ATP_pool")
    adp = next(p for p in model.places if p.name == "ADP_pool")

    ctrl = SimulationController(model)
    duration = 100.0
    dt = 0.1
    ctrl.run(time_step=dt, max_steps=int(duration / dt))

    s = atp.tokens + adp.tokens
    print(f"[{label}] after {duration}s  ATP={atp.tokens:.3f}  "
          f"ADP={adp.tokens:.3f}  sum={s:.3f}  Δsum={s - 5000:+.3f}")
    return atp.tokens, adp.tokens, s


if __name__ == "__main__":
    print("Variant 1: signal_flow input + curved_opposite_signal_flow output (v4 wiring)")
    run_variant("v4-wiring")

    print()
    print("Variant 2: normal arcs both sides (classical PT semantics)")
    def to_normal(md):
        for a in md["arcs"]:
            a["arc_type"] = "normal"
            a["object_type"] = "arc"
            a.pop("threshold", None)
    run_variant("normal-both", to_normal)

    print()
    print("Variant 3: signal_flow input + normal output")
    def mixed(md):
        md["arcs"][1]["arc_type"] = "normal"
        md["arcs"][1]["object_type"] = "arc"
    run_variant("sigflow-in/normal-out", mixed)

    print()
    print("Variant 4: normal input + curved_opposite_signal_flow output")
    def mixed2(md):
        md["arcs"][0]["arc_type"] = "normal"
        md["arcs"][0].pop("threshold", None)
    run_variant("normal-in/opposite-out", mixed2)
