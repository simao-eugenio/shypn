"""
Server-side summarizer for run_20260425_154907 (P6 dose-response sweep).

Reads each condition's statistics.json (huge, 900 MB each), extracts a
compact summary: final value of each place, plus a 200-point downsampled
mean trajectory. Writes a single small summary.json next to itself.

Usage (on server):
    python3 p6_sweep_summary.py [run_dir]
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

RUN_DIR = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(
    "/home/simao/data/results/canabidiol/run_20260425_154907"
)
N_DOWNSAMPLE = 201  # ~ every 72 s for a 14400 s run

# Map place ids (P1..P38) to names by reading model_snapshot.shy
model_path = RUN_DIR / "model_snapshot.shy"
with model_path.open() as f:
    model = json.load(f)
id_to_name = {p["id"]: p.get("name", p["id"]) for p in model.get("places", [])}
flags = {p["id"]: {
    "is_signal_place": p.get("is_signal_place", False),
    "is_parameter_place": p.get("properties", {}).get("is_parameter_place", False),
} for p in model.get("places", [])}

conditions = sorted([d for d in RUN_DIR.iterdir() if d.is_dir() and d.name.startswith("condition_")])

out = {
    "run_dir": str(RUN_DIR),
    "n_conditions": len(conditions),
    "place_id_to_name": id_to_name,
    "place_flags": flags,
    "conditions": {},
}

for cdir in conditions:
    name = cdir.name.replace("condition_", "")
    sf = cdir / "statistics.json"
    if not sf.exists():
        continue
    print(f"reading {cdir.name} ...", flush=True)
    with sf.open() as f:
        d = json.load(f)
    t = d["time_points"]
    n = len(t)
    # downsample indices
    step = max(1, n // N_DOWNSAMPLE)
    idx = list(range(0, n, step))
    if idx[-1] != n - 1:
        idx.append(n - 1)
    species_summary = {}
    for pid, stats in d["species_statistics"].items():
        mean = stats["mean"]
        std = stats["std"]
        species_summary[pid] = {
            "name": id_to_name.get(pid, pid),
            "final_mean": mean[-1],
            "final_std": std[-1],
            "max_mean": max(mean),
            "min_mean": min(mean),
            "t_max": t[mean.index(max(mean))],
            "downsampled_t": [t[i] for i in idx],
            "downsampled_mean": [mean[i] for i in idx],
            "downsampled_std": [std[i] for i in idx],
        }
    out["conditions"][name] = {
        "n_replicates": d["n_replicates"],
        "species": species_summary,
    }

out_path = RUN_DIR / "compact_summary.json"
with out_path.open("w") as f:
    json.dump(out, f)
sz = out_path.stat().st_size
print(f"wrote {out_path}  ({sz/1024:.1f} KiB)")
