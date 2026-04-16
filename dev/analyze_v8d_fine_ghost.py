#!/usr/bin/env python3
"""Ghost analysis: extract MYE commit times from trajectory data for G-v8d-fine.

Fate classifier: GATA1_Protein_nuc / PU1_Protein_nuc > 1.5  → ERY
                 PU1_Protein_nuc / GATA1_Protein_nuc > 1.5  → MYE

Commit time = first time the ratio crosses the threshold and STAYS there
(never reverts). This detects critical slowing down near EPO*.
"""
import csv, os, statistics

BASE = "workspace/projects/gata/experiments/results/run_20260320_181741"
THRESHOLD = 1.5  # matches fate_summary classifier

def find_commit_time(traj_csv, direction='mye'):
    """Return the time of last threshold crossing (= 'committed since').
    
    For MYE: first t where PU1_nuc / GATA1_nuc > threshold for all t' >= t.
    If cell ends undecided (ratio never crossed threshold), return None.
    """
    lines = [l for l in open(traj_csv) if not l.startswith('#')]
    if len(lines) < 2:
        return None
    reader = list(csv.DictReader(lines))
    if not reader:
        return None

    times = []
    ratios = []  # positive = MYE dominant, negative = ERY dominant
    for row in reader:
        try:
            t = float(row['time'])
            g = float(row['GATA1_Protein_nuc'])
            p = float(row['PU1_Protein_nuc'])
            if g + p < 0.01:
                continue
            # ratio > 1 → MYE dominant; < 1 → ERY dominant
            if direction == 'mye':
                ratio = p / max(g, 1e-6)  # > threshold → MYE
            else:
                ratio = g / max(p, 1e-6)  # > threshold → ERY
            times.append(t)
            ratios.append(ratio)
        except (ValueError, KeyError):
            continue

    if not times:
        return None

    # Find last index where direction switched  (= last reversion)
    committed = [r > THRESHOLD for r in ratios]
    if not any(committed):
        return None  # Never committed to this fate

    # Walk backward from end to find commit point
    last_reversion = -1
    for i in range(len(committed) - 1, -1, -1):
        if not committed[i]:
            last_reversion = i
            break

    # Commit time = time of first crossing AFTER last reversion
    start_search = last_reversion + 1
    for i in range(start_search, len(committed)):
        if committed[i]:
            return times[i]
    return None


def analyze_condition(dir_path, epo):
    traj_dir = os.path.join(dir_path, 'replicates_trajectories')
    if not os.path.isdir(traj_dir):
        return None

    # Get fate from replicates.csv
    rep_csv = os.path.join(dir_path, 'replicates.csv')
    fates = {}
    if os.path.exists(rep_csv):
        lines = [l for l in open(rep_csv) if not l.startswith('#')]
        for row in csv.DictReader(lines):
            rid = int(row['replicate_id'])
            fates[rid] = row.get('fate_class', '').strip().lower()

    mye_commits = []
    ery_commits = []
    traj_files = sorted(f for f in os.listdir(traj_dir) if f.endswith('.csv'))

    for i, fname in enumerate(traj_files):
        fate = fates.get(i, 'unknown')
        if fate == 'mye':
            ct = find_commit_time(os.path.join(traj_dir, fname), 'mye')
            if ct is not None:
                mye_commits.append(ct)
        elif fate == 'ery':
            ct = find_commit_time(os.path.join(traj_dir, fname), 'ery')
            if ct is not None:
                ery_commits.append(ct)

    n_mye = len([v for v in fates.values() if v == 'mye'])
    n_ery = len([v for v in fates.values() if v == 'ery'])
    n = len(fates)

    mye_mean = statistics.mean(mye_commits) if mye_commits else None
    mye_std  = statistics.stdev(mye_commits) if len(mye_commits) > 1 else None
    ery_mean = statistics.mean(ery_commits) if ery_commits else None

    return {
        'epo': epo, 'n': n, 'n_ery': n_ery, 'n_mye': n_mye,
        'mye_commits': mye_commits, 'ery_commits': ery_commits,
        'mye_mean': mye_mean, 'mye_std': mye_std, 'ery_mean': ery_mean,
    }


import re
results = []
for dname in sorted(os.listdir(BASE)):
    dpath = os.path.join(BASE, dname)
    if not os.path.isdir(dpath):
        continue
    m = re.search(r'EPO_external=([0-9.]+)', dname)
    if not m:
        continue
    epo = float(m.group(1))
    print(f"  Processing EPO={epo:.3f} ...", end=' ', flush=True)
    r = analyze_condition(dpath, epo)
    if r:
        results.append(r)
        print(f"done  MYE={r['n_mye']}  ERY={r['n_ery']}")
    else:
        print("SKIP")

results.sort(key=lambda x: x['epo'])

print(f"\n{'EPO':>6}  {'N':>4}  {'ERY%':>5}  {'MYE%':>5}  {'t_MYE_commit':>16}  {'t_ERY_commit':>14}")
print("-" * 72)
for r in results:
    n = r['n']
    epo = r['epo']
    ery_pct = 100*r['n_ery']/n if n else 0
    mye_pct = 100*r['n_mye']/n if n else 0
    if r['mye_mean'] is not None:
        t_mye = f"{r['mye_mean']:.1f}s"
        if r['mye_std'] is not None:
            t_mye += f" ±{r['mye_std']:.1f}"
    else:
        t_mye = "-"
    t_ery = f"{r['ery_mean']:.1f}s" if r['ery_mean'] is not None else "-"
    print(f"{epo:6.3f}  {n:4d}  {ery_pct:5.1f}  {mye_pct:5.1f}  {t_mye:>16}  {t_ery:>14}")

# Ghost signal: look for monotonic increase in t_MYE as EPO → EPO*
print("\n--- Ghost / critical slowing down ---")
mye_dominant = [(r['epo'], r['mye_mean']) for r in results if r['n_ery'] <= 5 and r['mye_mean'] is not None]
if mye_dominant:
    print("MYE-dominant conditions sorted by EPO (expect t_MYE ↑ near EPO*):")
    for epo, tm in mye_dominant:
        print(f"  EPO={epo:.3f}  t_MYE={tm:.1f}s")
    epovalues = [e for e, _ in mye_dominant]
    tvalues   = [t for _, t in mye_dominant]
    if len(tvalues) > 1:
        slope = (tvalues[-1] - tvalues[0]) / (epovalues[-1] - epovalues[0])
        print(f"\n  Rate of slowing: {slope:.0f} s per unit EPO")
        print(f"  Max t_MYE at EPO={mye_dominant[-1][0]:.3f}: {mye_dominant[-1][1]:.1f}s")
        print(f"  EPO*(pH=8.0) confirmed between {mye_dominant[-1][0]:.3f} and ",
              end='')
        ery_start = [(r['epo'], r['n_ery']) for r in results if r['n_ery'] > 10]
        if ery_start:
            print(f"{min(e for e,_ in ery_start):.3f}")
        else:
            print("?")
