"""
Primary observables for the bacillus_sporulation_v4_thesis sweep.

Reduces a sweep run directory to two observables per condition:

  1. Outer_coat_final     — endpoint mean ± std across replicates (clean dose-response)
  2. t_first_Mature_spore — earliest time the mean Mature_spore trajectory crosses
                             a threshold (default 1.0 token); 'NaN' if never

Usage:
    python workspace/projects/thesis/scripts/primary_observables.py \
        /tmp/v4_1_factorial                       # any rsynced run dir
    python workspace/projects/thesis/scripts/primary_observables.py \
        --run /tmp/v4_1_factorial --csv obs.csv   # write CSV
"""
from __future__ import annotations
import argparse
import csv
import json
import math
import statistics as st
from pathlib import Path

# v4.1 model: place id → name (single source of truth)
NAMES = {
    'P19': 'Forespore', 'P20': 'Mother_cell', 'P21': 'Cortex',
    'P22': 'Inner_coat', 'P23': 'Outer_coat', 'P24': 'Mature_spore',
}
N2I = {v: k for k, v in NAMES.items()}

OUTER_COAT = N2I['Outer_coat']
MATURE_SPORE = N2I['Mature_spore']


def parse_cond(name: str) -> tuple[int, float, int] | None:
    if 'INITIAL_NUTRIENTS_eq_' not in name:
        return None
    nut = int(name.split('INITIAL_NUTRIENTS_eq_')[1].split('_')[0])
    T = float(name.split('TEMPERATURE_K_eq_')[1].split('_')[0])
    h = int(name.split('SIGMA_HALFLIFE_MIN_eq_')[1])
    return nut, T, h


def first_crossing(times: list[float], values: list[float], threshold: float) -> float:
    """Return the first time at which value >= threshold; NaN if never reached."""
    for t, v in zip(times, values):
        if v >= threshold:
            return t
    return math.nan


def reduce_condition(cond_dir: Path, threshold: float) -> dict:
    stats = json.loads((cond_dir / 'statistics.json').read_text())
    times = stats['time_points']
    sp = stats['species_statistics']

    # t_first_Mature_spore from the mean trajectory
    t_first = first_crossing(times, sp[MATURE_SPORE]['mean'], threshold)

    # Outer_coat_final — read per-rep endpoints from replicates.csv for std
    rep_csv = cond_dir / 'replicates.csv'
    oc_col = 'Outer_coat_final'
    oc_vals: list[float] = []
    if rep_csv.exists():
        with rep_csv.open() as f:
            for row in csv.DictReader(f):
                if row.get(oc_col):
                    oc_vals.append(float(row[oc_col]))
    if oc_vals:
        oc_mean = st.mean(oc_vals)
        oc_std = st.stdev(oc_vals) if len(oc_vals) > 1 else 0.0
        oc_n = len(oc_vals)
    else:  # fallback: trajectory mean endpoint
        oc_mean = sp[OUTER_COAT]['mean'][-1]
        oc_std = sp[OUTER_COAT].get('std', [0.0])[-1]
        oc_n = stats.get('n_replicates', 0)

    return {
        'Outer_coat_final_mean': oc_mean,
        'Outer_coat_final_std': oc_std,
        'Outer_coat_final_n': oc_n,
        't_first_Mature_spore_s': t_first,
        't_first_Mature_spore_min': t_first / 60.0 if not math.isnan(t_first) else math.nan,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('run', nargs='?', help='sweep run directory')
    ap.add_argument('--run', dest='run_kw', help='(alt form) sweep run directory')
    ap.add_argument('--threshold', type=float, default=1.0,
                    help='Mature_spore token level that defines "first appearance" (default 1.0)')
    ap.add_argument('--csv', help='write reduced observables to this CSV file')
    args = ap.parse_args()

    run_dir = Path(args.run or args.run_kw or '')
    if not run_dir.is_dir():
        ap.error(f'run directory not found: {run_dir}')

    rows: list[dict] = []
    for d in sorted(run_dir.glob('condition_*')):
        if not (d / 'statistics.json').exists():
            continue
        parsed = parse_cond(d.name)
        if parsed is None:
            continue  # skip Baseline / unparseable
        nut, T, h = parsed
        obs = reduce_condition(d, args.threshold)
        rows.append({'Nut': nut, 'T': T, 't_half': h, **obs})

    rows.sort(key=lambda r: (r['Nut'], r['T'], r['t_half']))

    print(f'Run: {run_dir}   threshold(Mature_spore) = {args.threshold}')
    print(f'{"Nut":>4} {"T":>7} {"t½":>5} | '
          f'{"Outer_coat_final (mean±std, n)":>34} | {"t_first_Mature_spore (min)":>26}')
    print('-' * 90)
    for r in rows:
        oc = f'{r["Outer_coat_final_mean"]:>10.1f} ± {r["Outer_coat_final_std"]:>6.1f} (n={r["Outer_coat_final_n"]:>2})'
        tm = (f'{r["t_first_Mature_spore_min"]:>10.2f}'
              if not math.isnan(r['t_first_Mature_spore_min']) else f'{"never":>10}')
        print(f'{r["Nut"]:>4} {r["T"]:>7.2f} {r["t_half"]:>5} | {oc:>34} | {tm:>26}')

    if args.csv:
        with open(args.csv, 'w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
        print(f'\nWrote {args.csv}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
