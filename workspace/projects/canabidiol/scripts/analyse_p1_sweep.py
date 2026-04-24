"""Analyse a P1 factorial sweep run using per-replicate final values.

Reads each condition_*/replicates.csv (small; ~12 KB per condition vs
~1 GB statistics.json) and prints a 4-axis summary table plus marginal
breakdowns.

Run on the server::

    python3 workspace/projects/canabidiol/scripts/analyse_p1_sweep.py <run_dir>
"""
from __future__ import annotations

import csv
import os
import re
import sys
from typing import Any, Dict, List

KEY_PLACES = [
    'CBD_extracellular', 'CBD_intracellular',
    'Abeta_Oligomer', 'Abeta_Plaque',
    'NFkB_p65', 'ROS',
    'Microglia_M1', 'Microglia_M2',
    'Glutathione', 'Neuron_Health',
    'TNFa', 'IL1b', 'IL6',
]


def parse_condition(name: str) -> Dict[str, float] | None:
    if name == 'Baseline':
        return None
    parts = dict(re.findall(r'(?:\[param\]_)?([A-Za-z_]+?)_eq_([0-9.]+)', name))
    return {
        'sev': float(parts.get('Disease_Severity', 0)),
        'load': float(parts.get('LOADING_DOSE', 0)),
        'maint': float(parts.get('MAINT_DOSE', 0)),
        'age': float(parts.get('_Age', 65)),
    }


def end_means(csv_path: str) -> Dict[str, float]:
    with open(csv_path, newline='') as f:
        rows = list(csv.DictReader(f))
    if not rows:
        return {}
    out: Dict[str, float] = {}
    for k in KEY_PLACES:
        col = f'{k}_final'
        if col in rows[0]:
            vals = [float(r[col]) for r in rows if r.get(col) not in (None, '')]
            if vals:
                out[k] = sum(vals) / len(vals)
    return out


def main(run_dir: str) -> None:
    rows: List[Dict[str, Any]] = []
    conds = sorted(d for d in os.listdir(run_dir) if d.startswith('condition_'))
    for c in conds:
        p = parse_condition(c.replace('condition_', ''))
        if p is None:
            continue
        cf = os.path.join(run_dir, c, 'replicates.csv')
        if not os.path.exists(cf):
            continue
        rows.append({**p, **end_means(cf)})

    print(f"Loaded {len(rows)} parametrised conditions from {run_dir}")
    print()

    ref = next((r for r in rows
                if r['sev'] == 0 and r['age'] == 65
                and r['load'] == 0 and r['maint'] == 0), None)
    if ref:
        print("Healthy reference (Sev=0, Age=65, no drug):")
        for k in KEY_PLACES:
            if k in ref:
                print(f"  {k:<22} {ref[k]:8.2f}")
        print()

    for sev in sorted({int(r['sev']) for r in rows}):
        print(f"=== Disease_Severity = {sev} ===")
        hdr = (
            f"{'Ld':>3} {'Mt':>3} {'Age':>3}  "
            f"{'NeuH':>5} {'AbO':>6} {'AbPlq':>6} {'ROS':>5} {'NFkB':>5} "
            f"{'M1':>5} {'M2':>5} {'GSH':>5} {'TNFa':>5} {'CBDex':>6} {'CBDin':>6}"
        )
        print(hdr)
        print('-' * len(hdr))
        sub = [r for r in rows if int(r['sev']) == sev]
        for r in sorted(sub, key=lambda r: (r['age'], r['load'], r['maint'])):
            print(
                f"{int(r['load']):>3} {int(r['maint']):>3} {int(r['age']):>3}  "
                f"{r.get('Neuron_Health', 0):>5.1f} "
                f"{r.get('Abeta_Oligomer', 0):>6.1f} {r.get('Abeta_Plaque', 0):>6.1f} "
                f"{r.get('ROS', 0):>5.1f} {r.get('NFkB_p65', 0):>5.1f} "
                f"{r.get('Microglia_M1', 0):>5.1f} {r.get('Microglia_M2', 0):>5.1f} "
                f"{r.get('Glutathione', 0):>5.1f} {r.get('TNFa', 0):>5.1f} "
                f"{r.get('CBD_extracellular', 0):>6.2f} {r.get('CBD_intracellular', 0):>6.2f}"
            )
        print()

    print("=== Marginal drug effect on Neuron_Health (mean over Age) ===")
    print(f"{'Sev':>3} {'Ld':>3} {'Mt':>3}  {'meanNeuH':>9}  {'delta':>8}")
    print('-' * 38)
    grouped: Dict[tuple, List[float]] = {}
    for r in rows:
        if 'Neuron_Health' not in r:
            continue
        key = (int(r['sev']), int(r['load']), int(r['maint']))
        grouped.setdefault(key, []).append(r['Neuron_Health'])
    means = {k: sum(v) / len(v) for k, v in grouped.items()}
    for sev in sorted({k[0] for k in means}):
        no_drug = means.get((sev, 0, 0))
        for ld in sorted({k[1] for k in means if k[0] == sev}):
            for mt in sorted({k[2] for k in means if k[0] == sev and k[1] == ld}):
                m = means[(sev, ld, mt)]
                d = (m - no_drug) if no_drug is not None else 0.0
                print(f"{sev:>3} {ld:>3} {mt:>3}  {m:>9.2f}  {d:>+8.2f}")

    print()
    print("=== Disease burden (no drug): Neuron_Health vs Severity & Age ===")
    sevs = sorted({int(r['sev']) for r in rows})
    print(f"{'Age':>3}  " + "  ".join(f"Sev{s}" for s in sevs))
    for age in sorted({int(r['age']) for r in rows}):
        cells = []
        for sev in sevs:
            cell = next((r for r in rows
                         if int(r['sev']) == sev and int(r['age']) == age
                         and r['load'] == 0 and r['maint'] == 0), None)
            cells.append(f"{cell['Neuron_Health']:5.1f}" if cell else '   - ')
        print(f"{age:>3}  " + "  ".join(cells))


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(f"usage: {sys.argv[0]} <run_dir>")
    main(sys.argv[1])
