#!/usr/bin/env python3
"""Analyze G-v8d-fine: pH=8.0, EPO 0.545-0.555, N=200, t_end=2000s."""
import csv, os, statistics

BASE = "workspace/projects/gata/experiments/results/run_20260320_181741"

rows_out = []
for dname in sorted(os.listdir(BASE)):
    dpath = os.path.join(BASE, dname)
    if not os.path.isdir(dpath):
        continue
    import re
    m = re.search(r'EPO_external=([0-9.]+)', dname)
    if not m:
        continue
    epo = float(m.group(1))

    rep_csv = os.path.join(dpath, "replicates.csv")
    if not os.path.exists(rep_csv):
        print(f"EPO={epo}: NO replicates.csv")
        continue

    # Strip comment lines starting with #
    clean_rows = []
    with open(rep_csv) as f:
        reader = None
        for line in f:
            if line.startswith('#'):
                continue
            if reader is None:
                # First non-comment line is header — handle wrapped header
                header = line.strip()
                reader = True
                break
        # Now read the rest as CSV
        f.seek(0)
    
    # Collect all non-comment lines
    lines = [l for l in open(rep_csv) if not l.startswith('#')]
    reader = csv.DictReader(lines)
    replicates = list(reader)

    if not replicates:
        print(f"EPO={epo}: EMPTY")
        continue

    # Fate counts
    fates = [r.get('fate_class', '').strip().lower() for r in replicates]
    ery = sum(1 for f in fates if f == 'ery')
    mye = sum(1 for f in fates if f == 'mye')
    unk = sum(1 for f in fates if f not in ('ery', 'mye'))
    n = len(fates)

    # sim_duration for each fate (time at which the cell committed/finished)
    def safe_float(v):
        try:
            return float(v)
        except (TypeError, ValueError):
            return None

    mye_dur = [safe_float(r.get('sim_duration')) for r in replicates if r.get('fate_class','').strip().lower() == 'mye']
    ery_dur = [safe_float(r.get('sim_duration')) for r in replicates if r.get('fate_class','').strip().lower() == 'ery']
    mye_dur = [x for x in mye_dur if x is not None]
    ery_dur = [x for x in ery_dur if x is not None]

    # Cells that hit t_end=2000 without committing (deadlocked or ran full sim)
    deadlocked = [r for r in replicates if str(r.get('deadlocked','')).strip().lower() == 'true']
    full_run = [r for r in replicates if safe_float(r.get('final_time')) == 2000.0 and safe_float(r.get('sim_duration')) == 2000.0]

    mye_mean = f"{statistics.mean(mye_dur):.1f}s" if mye_dur else "-"
    mye_std  = f"±{statistics.stdev(mye_dur):.1f}" if len(mye_dur) > 1 else ""
    ery_mean = f"{statistics.mean(ery_dur):.1f}s" if ery_dur else "-"
    ery_std  = f"±{statistics.stdev(ery_dur):.1f}" if len(ery_dur) > 1 else ""

    rows_out.append((epo, n, ery, mye, unk, mye_mean+mye_std, ery_mean+ery_std, len(deadlocked)))

rows_out.sort(key=lambda x: x[0])

print(f"\n{'EPO':>6}  {'N':>4}  {'ERY':>6}  {'MYE':>6}  {'t_MYE (mean)':>16}  {'t_ERY (mean)':>16}  {'deadlk':>6}")
print("-" * 75)
for epo, n, ery, mye, unk, t_mye, t_ery, dl in rows_out:
    ery_pct = 100*ery/n if n else 0
    mye_pct = 100*mye/n if n else 0
    print(f"{epo:6.3f}  {n:4d}  {ery:3d}({ery_pct:3.0f}%)  {mye:3d}({mye_pct:3.0f}%)  {t_mye:>16}  {t_ery:>16}  {dl:6d}")

print()
# Ghost signal: MYE commit time should peak at EPO* - epsilon
mye_rows = [(r[0], r[5]) for r in rows_out if r[2] == 0 and r[3] > 0]  # pure MYE conditions
if mye_rows:
    print("Ghost (MYE-only conditions)  — critical slowing = longer t_MYE near EPO*:")
    for epo, t_mye in mye_rows:
        print(f"  EPO={epo:.3f}  t_MYE={t_mye}")

# Transition boundary
ery_rows = [(r[0], r[2]) for r in rows_out]
below = [(e, ery) for e,ery in ery_rows if ery == 0]
above = [(e, ery) for e,ery in ery_rows if ery > 0]
if below and above:
    lo = max(e for e,_ in below)
    hi = min(e for e,_ in above)
    mid = (lo + hi) / 2
    print(f"\nTransition boundary:  EPO* in ({lo:.3f}, {hi:.3f}),  midpoint = {mid:.4f}")
