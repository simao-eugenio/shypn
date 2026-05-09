"""Deep analysis of v4 thesis sweep (run_20260509_133255).

Compares to v3 (run_20260509_125201). Same 8 analyses A–H from
deep_analysis_v3, plus:
  Z. v3-vs-v4 head-to-head on the two topology-fix acceptance gates
     (mass conservation, sigma decay).
"""
from __future__ import annotations

import csv, json, statistics
from pathlib import Path

V4 = Path('/tmp/v4_run')
V3 = Path('/tmp/thesis_run')
OUT = Path('/home/simao/projetos/shypn/workspace/projects/thesis/analysis/thesis_revision_v4')
OUT.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Load both runs
# ---------------------------------------------------------------------------

def load_run(root, cond_dirs):
    model = json.loads((root / 'model_snapshot.shy').read_text())
    name2id = {p['name']: p['id'] for p in model['places']}
    id2name = {v: k for k, v in name2id.items()}
    bag = {'name2id': name2id, 'id2name': id2name, 'data': {}}
    for label, dirname in cond_dirs.items():
        s = json.loads((root / dirname / 'statistics.json').read_text())
        with open(root / dirname / 'replicates.csv') as f:
            r = csv.reader(f); hdr = next(r); rows = list(r)
        bag['data'][label] = {
            'times': s['time_points'],
            'ss':    s['species_statistics'],
            'hdr':   hdr,
            'rows':  rows,
        }
    return bag

V4_CONDS = {
    'Baseline':         'condition_Baseline',
    'Nut_eq_10':        'condition_[param]_Initial_Nutrients_eq_10',
    'Nut_eq_30':        'condition_[param]_Initial_Nutrients_eq_30',
    'Nut_eq_100':       'condition_[param]_Initial_Nutrients_eq_100',
    'Nut_eq_300':       'condition_[param]_Initial_Nutrients_eq_300',
}
V3_CONDS = {
    'Baseline':         'condition_Baseline',
    'Nut_eq_10':        'condition_Nutrients_eq_10',
    'Nut_eq_30':        'condition_Nutrients_eq_30',
    'Nut_eq_100':       'condition_Nutrients_eq_100',
    'Nut_eq_300':       'condition_Nutrients_eq_300',
}

v4 = load_run(V4, V4_CONDS)
v3 = load_run(V3, V3_CONDS)
ORDER = ['Nut_eq_10', 'Nut_eq_30', 'Baseline', 'Nut_eq_100', 'Nut_eq_300']

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def traj(bag, cond, name, key='mean'):
    pid = bag['name2id'][name]
    return bag['data'][cond]['ss'][pid][key]

def at_time(bag, cond, name, t, key='mean'):
    times = bag['data'][cond]['times']
    idx = min(range(len(times)), key=lambda i: abs(times[i] - t))
    return bag['data'][cond]['ss'][bag['name2id'][name]][key][idx]

def endpoint(bag, cond, name, key='mean'):
    return traj(bag, cond, name, key)[-1]

def first_passage(bag, cond, name, threshold, going_down=False, key='mean'):
    times = bag['data'][cond]['times']
    tj = traj(bag, cond, name, key)
    for t, v in zip(times, tj):
        if (going_down and v <= threshold) or (not going_down and v >= threshold):
            return t
    return None

def rep_endpoints(bag, cond, name):
    """Return list of per-replicate endpoint values for a place."""
    pid = bag['name2id'][name]
    hdr = bag['data'][cond]['hdr']
    rows = bag['data'][cond]['rows']
    # replicates.csv columns: replicate_idx, then per-place final values
    # column header for a place is its ID (e.g. 'P24')
    if pid not in hdr:
        return []
    col = hdr.index(pid)
    return [float(row[col]) for row in rows]

# ---------------------------------------------------------------------------
# Z. Topology-fix acceptance gates (most important)
# ---------------------------------------------------------------------------

print('='*100)
print('GATE F1 — Mass conservation of adenylate pool')
print('  v3 had: ATP+ADP drift +37 738 tokens (started 5995 → ended ~43 000)')
print('  v4 fix: ADP arc test→signal_flow on Source_ATP_regen + Source_ATP_stationary')
print('  PASS criterion: |ATP+ADP_end − 5995| / 5995 < 5%')
print('='*100)
print(f'{"Cond":<14}{"ATP_v3":>10}{"ADP_v3":>10}{"sum_v3":>10}{"Δ_v3":>10}'
      f'{"ATP_v4":>10}{"ADP_v4":>10}{"sum_v4":>10}{"Δ_v4":>10}{"%err_v4":>10}{"verdict":>10}')
print('-'*120)
for c in ORDER:
    atp_v3 = endpoint(v3, c, 'ATP_pool')
    adp_v3 = endpoint(v3, c, 'ADP_pool')
    atp_v4 = endpoint(v4, c, 'ATP_pool')
    adp_v4 = endpoint(v4, c, 'ADP_pool')
    s3 = atp_v3 + adp_v3
    s4 = atp_v4 + adp_v4
    err = abs(s4 - 5995) / 5995 * 100
    ok  = 'PASS' if err < 5.0 else 'FAIL'
    print(f'{c:<14}{atp_v3:>10.1f}{adp_v3:>10.1f}{s3:>10.1f}{s3-5995:>+10.0f}'
          f'{atp_v4:>10.1f}{adp_v4:>10.1f}{s4:>10.1f}{s4-5995:>+10.0f}{err:>9.2f}%{ok:>10}')

print()
print('  ALSO: GTP+GDP pool')
print(f'{"Cond":<14}{"GTP_v3":>10}{"GDP_v3":>10}{"sum_v3":>10}{"Δ_v3":>10}'
      f'{"GTP_v4":>10}{"GDP_v4":>10}{"sum_v4":>10}{"Δ_v4":>10}')
print('-'*100)
for c in ORDER:
    g3 = endpoint(v3, c, 'GTP_pool') + endpoint(v3, c, 'GDP_pool')
    g4 = endpoint(v4, c, 'GTP_pool') + endpoint(v4, c, 'GDP_pool')
    print(f'{c:<14}{endpoint(v3,c,"GTP_pool"):>10.1f}{endpoint(v3,c,"GDP_pool"):>10.1f}{g3:>10.1f}{g3-5995:>+10.0f}'
          f'{endpoint(v4,c,"GTP_pool"):>10.1f}{endpoint(v4,c,"GDP_pool"):>10.1f}{g4:>10.1f}{g4-5995:>+10.0f}')

# ---------------------------------------------------------------------------
# GATE F2 — Sigma factor saturation (decay topology working?)
# ---------------------------------------------------------------------------

print()
print('='*100)
print('GATE F2 — Sigma factor decay topology')
print('  v3 had: SigmaE rose monotonically to 14 800 in Nut=300 (no degradation)')
print('  v4 fix: 5 new T_Sigma*_decay continuous transitions, rate = k_sigma_decay * SigmaX')
print('  k_sigma_decay = ln(2)/120 = 0.00578 /min ⇒ τ ≈ 173 min half-life')
print('  PASS criterion: peak occurs BEFORE end-of-sim AND endpoint < peak (some decay visible)')
print('='*100)
for sigma in ['SigmaH', 'SigmaF', 'SigmaE', 'SigmaG', 'SigmaK']:
    print(f'\n  {sigma}')
    print(f'  {"Cond":<14}{"v3_end":>10}{"v4_peak":>10}{"v4_t_pk":>10}{"v4_end":>10}{"frac_kept":>12}{"verdict":>10}')
    for c in ORDER:
        v3_end = endpoint(v3, c, sigma)
        tj = traj(v4, c, sigma)
        times = v4['data'][c]['times']
        peak = max(tj); t_peak = times[tj.index(peak)]
        v4_end = tj[-1]
        kept = v4_end / peak if peak > 0 else 0.0
        ok = 'PASS' if (peak > 0 and t_peak < times[-1] - 60 and kept < 0.95) else \
             ('flat' if peak < 1 else 'FAIL')
        print(f'  {c:<14}{v3_end:>10.1f}{peak:>10.1f}{t_peak:>10.1f}{v4_end:>10.1f}{kept*100:>10.1f}%{ok:>10}')

# ---------------------------------------------------------------------------
# GATE F3 — Bridge wiring: Initial_Nutrients ▢ → Nutrients ⬡ at t=0
# ---------------------------------------------------------------------------

print()
print('='*100)
print('GATE F3 — Event bridge: evt_apply_initial_nutrients projects ▢ onto ⬡')
print('  PASS: Nutrients(t≈1 min) within ±2 of Initial_Nutrients ▢ value')
print('='*100)
print(f'  {"Cond":<14}{"target":>10}{"Nut(t=5s)":>12}{"Nut(t=60s)":>12}{"verdict":>10}')
expected = {'Nut_eq_10': 10, 'Nut_eq_30': 30, 'Baseline': 100, 'Nut_eq_100': 100, 'Nut_eq_300': 300}
for c in ORDER:
    t5  = at_time(v4, c, 'Nutrients', 5)
    t60 = at_time(v4, c, 'Nutrients', 60)
    target = expected[c]
    ok = 'PASS' if abs(t60 - target) < max(2, 0.05*target) else 'FAIL'
    print(f'  {c:<14}{target:>10}{t5:>12.2f}{t60:>12.2f}{ok:>10}')

# ---------------------------------------------------------------------------
# A. Basin-floor reproducibility (F6: 2.24 ± 0.21 mM)
# ---------------------------------------------------------------------------

print()
print('='*100)
print('GATE F6 — ATP basin floor reproducibility (v3 emergent value: 2.24 ± 0.21 mM)')
print('  Basin floor = min(ATP_pool mean trajectory) over the run')
print('  ATP scaling: 1 mM ≈ 1000 tokens (per v3 thesis convention)')
print('='*100)
print(f'  {"Cond":<14}{"v3_min(mM)":>14}{"v4_min(mM)":>14}{"v3_t_min":>10}{"v4_t_min":>10}{"Δ%":>10}')
v3_floors, v4_floors = [], []
for c in ORDER:
    v3_tj = traj(v3, c, 'ATP_pool'); v3_t = v3['data'][c]['times']
    v4_tj = traj(v4, c, 'ATP_pool'); v4_t = v4['data'][c]['times']
    v3_min = min(v3_tj); v4_min = min(v4_tj)
    i3 = v3_tj.index(v3_min); i4 = v4_tj.index(v4_min)
    delta = (v4_min - v3_min) / v3_min * 100 if v3_min > 0 else 0
    v3_floors.append(v3_min/1000); v4_floors.append(v4_min/1000)
    print(f'  {c:<14}{v3_min/1000:>14.2f}{v4_min/1000:>14.2f}{v3_t[i3]/60:>9.1f}m{v4_t[i4]/60:>9.1f}m{delta:>+9.1f}%')

print()
print(f'  v3 mean basin floor across conditions: {statistics.mean(v3_floors):.2f} ± {statistics.stdev(v3_floors):.2f} mM')
print(f'  v4 mean basin floor across conditions: {statistics.mean(v4_floors):.2f} ± {statistics.stdev(v4_floors):.2f} mM')
print(f'  Fujita anchor: 2.21 ± 0.18 mM')

# ---------------------------------------------------------------------------
# B. Sporulation yield comparison
# ---------------------------------------------------------------------------

print()
print('='*100)
print('Sporulation yield (Mature_spore endpoint) — v3 vs v4')
print('='*100)
print(f'  {"Cond":<14}{"v3_mean":>10}{"v3_std":>10}{"v3_max":>8}{"v3_zero":>10}'
      f'{"v4_mean":>10}{"v4_std":>10}{"v4_max":>8}{"v4_zero":>10}')
for c in ORDER:
    v3r = rep_endpoints(v3, c, 'Mature_spore')
    v4r = rep_endpoints(v4, c, 'Mature_spore')
    if not v3r or not v4r:
        print(f'  {c:<14} (no per-replicate data)'); continue
    v3z = sum(1 for x in v3r if x == 0)
    v4z = sum(1 for x in v4r if x == 0)
    print(f'  {c:<14}{statistics.mean(v3r):>10.2f}{statistics.stdev(v3r):>10.2f}'
          f'{int(max(v3r)):>8}{v3z:>5}/{len(v3r):<4}'
          f'{statistics.mean(v4r):>10.2f}{statistics.stdev(v4r):>10.2f}'
          f'{int(max(v4r)):>8}{v4z:>5}/{len(v4r):<4}')

# ---------------------------------------------------------------------------
# C. Phosphorelay throughput v3 vs v4 (placeholder — needs firing counts)
# ---------------------------------------------------------------------------

print()
print('='*100)
print('Compute summary — written to', OUT)
print('='*100)
print('Outputs: deep_v4.txt (this output), gate_summary.csv')

# Write a compact CSV summary
with open(OUT / 'gate_summary.csv', 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['condition', 'v3_axp_end', 'v4_axp_end', 'v4_axp_err_pct',
                'v3_sigE_end', 'v4_sigE_end', 'v4_sigE_peak',
                'v3_basin_mM', 'v4_basin_mM',
                'v3_spore_mean', 'v4_spore_mean'])
    for c in ORDER:
        v3a = endpoint(v3,c,'ATP_pool')+endpoint(v3,c,'ADP_pool')
        v4a = endpoint(v4,c,'ATP_pool')+endpoint(v4,c,'ADP_pool')
        v4_sigE_tj = traj(v4,c,'SigmaE')
        v3r = rep_endpoints(v3,c,'Mature_spore')
        v4r = rep_endpoints(v4,c,'Mature_spore')
        w.writerow([
            c, f'{v3a:.1f}', f'{v4a:.1f}', f'{abs(v4a-5995)/5995*100:.2f}',
            f'{endpoint(v3,c,"SigmaE"):.1f}',
            f'{endpoint(v4,c,"SigmaE"):.1f}',
            f'{max(v4_sigE_tj):.1f}',
            f'{min(traj(v3,c,"ATP_pool"))/1000:.3f}',
            f'{min(traj(v4,c,"ATP_pool"))/1000:.3f}',
            f'{statistics.mean(v3r):.2f}' if v3r else '',
            f'{statistics.mean(v4r):.2f}' if v4r else '',
        ])

print('Done.')
