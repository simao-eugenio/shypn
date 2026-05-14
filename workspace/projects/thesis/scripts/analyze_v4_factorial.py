"""Factorial 3-axis analysis of run_20260509_134037 (v4 thesis).

Axes: INITIAL_NUTRIENTS ∈ {10,100,300} × TEMPERATURE_K ∈ {310.15,320.15}
       × SIGMA_HALFLIFE_MIN ∈ {30,120,600}
= 18 conditions × 16 replicates.

Tests:
  F1   Mass conservation (ATP+ADP)
  F2   Sigma decay topology (peak then decline)
  F3   Event bridge (Nut(t≈0) = INITIAL_NUTRIENTS)
  F4   Q10 thermal — at fixed (Nut, t½), T=320.15 vs T=310.15 → ATP regen flux ratio
  F5   Sigma half-life scaling — at fixed (Nut, T), σE(t½=600)/σE(t½=30) at peak
  F6   Basin-floor reproducibility on the v3-comparable slice (T=310.15, t½=120)
  F7   3-way interaction matrix on Mature_spore endpoint
"""
from __future__ import annotations

import csv, json, statistics, itertools, re
from pathlib import Path

ROOT = Path('/tmp/v4_1_factorial')
OUT  = Path('/home/simao/projetos/shypn/workspace/projects/thesis/analysis/thesis_revision_v4_factorial')
OUT.mkdir(parents=True, exist_ok=True)

NUT_LEVELS  = [10, 100, 300]
T_LEVELS    = [310.15, 320.15]
HALF_LEVELS = [30, 120, 600]

# ---------------------------------------------------------------------------
# Load
# ---------------------------------------------------------------------------

model = json.loads((ROOT / 'model_snapshot.shy').read_text())
NAME2ID = {p['name']: p['id'] for p in model['places']}
ID2NAME = {v: k for k, v in NAME2ID.items()}

def cond_dir(nut, T, half):
    if (nut, T, half) == (100, 310.15, 120):  # baseline = the all-default condition
        # Check whether a [param] dir exists for it; otherwise use Baseline
        explicit = ROOT / f'condition_[param]_INITIAL_NUTRIENTS_eq_{nut}_[param]_TEMPERATURE_K_eq_{T}_[param]_SIGMA_HALFLIFE_MIN_eq_{half}'
        if explicit.exists():
            return explicit
        return ROOT / 'condition_Baseline'
    return ROOT / f'condition_[param]_INITIAL_NUTRIENTS_eq_{nut}_[param]_TEMPERATURE_K_eq_{T}_[param]_SIGMA_HALFLIFE_MIN_eq_{half}'

def fmt_t(T): return f'{T:g}'   # 310.15 stays 310.15
def fmt_h(h): return f'{h}'

# Map name (e.g. f"310.15") used in directory back to numeric value
def load_cond(nut, T, half):
    d = cond_dir(nut, T, half)
    s = json.loads((d / 'statistics.json').read_text())
    with open(d / 'replicates.csv') as f:
        r = csv.reader(f); hdr = next(r); rows = list(r)
    return {'times': s['time_points'], 'ss': s['species_statistics'],
            'hdr': hdr, 'rows': rows, 'dir': d.name}

DATA = {}
for nut, T, half in itertools.product(NUT_LEVELS, T_LEVELS, HALF_LEVELS):
    try:
        DATA[(nut, T, half)] = load_cond(nut, T, half)
    except FileNotFoundError as e:
        print(f'! missing: Nut={nut} T={T} t½={half}: {e}')

print(f'Loaded {len(DATA)} / {3*2*3} conditions')
print()

def traj(nut, T, half, name, key='mean'):
    return DATA[(nut,T,half)]['ss'][NAME2ID[name]][key]

def at_time(nut, T, half, name, t, key='mean'):
    times = DATA[(nut,T,half)]['times']
    idx = min(range(len(times)), key=lambda i: abs(times[i] - t))
    return DATA[(nut,T,half)]['ss'][NAME2ID[name]][key][idx]

def endpoint(nut, T, half, name, key='mean'):
    return traj(nut, T, half, name, key)[-1]

def rep_endpoints(nut, T, half, name):
    pid = NAME2ID[name]
    hdr = DATA[(nut,T,half)]['hdr']
    if pid not in hdr: return []
    col = hdr.index(pid)
    return [float(row[col]) for row in DATA[(nut,T,half)]['rows']]

# ---------------------------------------------------------------------------
# F1 — mass conservation across all 18 conditions
# ---------------------------------------------------------------------------

print('='*100)
print('F1 — Mass conservation of adenylate pool (ATP+ADP) across the 3-axis grid')
print('     PASS criterion per cell: |sum − 5995| / 5995 < 5%')
print('='*100)
print(f'  {"Nut":>4} {"T":>7} {"t½":>5}   {"ATP_end":>10} {"ADP_end":>10} {"sum":>10} {"Δ":>10} {"%err":>8}  {"verdict":>8}')
print('-'*92)
fails = passes = 0
fail_summary = []
for nut, T, half in itertools.product(NUT_LEVELS, T_LEVELS, HALF_LEVELS):
    if (nut,T,half) not in DATA: continue
    a = endpoint(nut,T,half,'ATP_pool')
    d = endpoint(nut,T,half,'ADP_pool')
    s = a + d
    err = abs(s - 5995) / 5995 * 100
    ok = err < 5.0
    passes += ok; fails += not ok
    if not ok: fail_summary.append((nut, T, half, err))
    print(f'  {nut:>4} {T:>7} {half:>5}   {a:>10.1f} {d:>10.1f} {s:>10.1f} {s-5995:>+10.0f} {err:>7.1f}%  {"PASS" if ok else "FAIL":>8}')

print(f'\nF1 summary: {passes}/{passes+fails} PASS, {fails} FAIL')

# Test: does the leak depend on T or t½?
print('\nLeak sensitivity to T and t½ (averaged over Nut levels):')
print(f'  {"T":>8} {"t½":>5}   {"mean_AxP":>10} {"mean_err%":>10}')
for T, half in itertools.product(T_LEVELS, HALF_LEVELS):
    sums = [endpoint(n,T,half,'ATP_pool')+endpoint(n,T,half,'ADP_pool') for n in NUT_LEVELS if (n,T,half) in DATA]
    if sums:
        m = statistics.mean(sums)
        print(f'  {T:>8} {half:>5}   {m:>10.0f} {abs(m-5995)/5995*100:>9.1f}%')

# ---------------------------------------------------------------------------
# F2 — sigma decay topology (test on SigmaE peak vs endpoint, all conditions)
# ---------------------------------------------------------------------------

print()
print('='*100)
print('F2 — Sigma decay topology: σE peaks then declines? Endpoint < 50% of peak required')
print('='*100)
print(f'  {"Nut":>4} {"T":>7} {"t½":>5}   {"σE_peak":>10} {"t_peak(min)":>13} {"σE_end":>10} {"frac_kept":>10}  {"verdict":>8}')
print('-'*92)
for nut, T, half in itertools.product(NUT_LEVELS, T_LEVELS, HALF_LEVELS):
    if (nut,T,half) not in DATA: continue
    tj = traj(nut,T,half,'SigmaE')
    times = DATA[(nut,T,half)]['times']
    pk = max(tj); t_pk = times[tj.index(pk)]
    end = tj[-1]
    kept = end/pk if pk>0 else 0.0
    ok = (pk > 1) and (kept < 0.5)
    print(f'  {nut:>4} {T:>7} {half:>5}   {pk:>10.1f} {t_pk/60:>12.1f}m {end:>10.1f} {kept*100:>9.1f}%  {"PASS" if ok else "low" if pk<1 else "FAIL":>8}')

# ---------------------------------------------------------------------------
# F4 — Q10 thermal: at fixed (Nut, t½), peak ATP regen flux ratio T=320.15/T=310.15
# ---------------------------------------------------------------------------

print()
print('='*100)
print('F4 — Q10 thermal (mean ATP_pool early-trajectory slope ratio at fixed Nut, t½)')
print('     Q10=2 ⇒ k_thermo_factor(320.15)/k_thermo_factor(310.15) = 2.0')
print('     Proxy: max ATP pool reached in first 30 min (regen-dominated phase)')
print('='*100)
print(f'  {"Nut":>4} {"t½":>5}   {"ATP_max_310":>12} {"ATP_max_320":>12} {"ratio":>8}  {"verdict":>10}')
print('-'*72)
for nut, half in itertools.product(NUT_LEVELS, HALF_LEVELS):
    if (nut,310.15,half) not in DATA or (nut,320.15,half) not in DATA: continue
    times = DATA[(nut,310.15,half)]['times']
    early_idx = [i for i,t in enumerate(times) if t <= 1800]
    tj_lo = traj(nut,310.15,half,'ATP_pool')
    tj_hi = traj(nut,320.15,half,'ATP_pool')
    a_lo = max(tj_lo[i] for i in early_idx)
    a_hi = max(tj_hi[i] for i in early_idx)
    r = a_hi / a_lo if a_lo > 0 else 0
    ok = 1.5 < r < 2.5  # Q10 ≈ 2 with tolerance
    print(f'  {nut:>4} {half:>5}   {a_lo:>12.1f} {a_hi:>12.1f} {r:>8.2f}  {"PASS" if ok else "off":>10}')

# ---------------------------------------------------------------------------
# F5 — Sigma half-life scaling: at fixed (Nut, T), σE peak amplitude ratio t½=600 / t½=30
# ---------------------------------------------------------------------------

print()
print('='*100)
print('F5 — σ half-life scaling: σE peak(t½=600) / peak(t½=30), ratio at fixed (Nut, T)')
print('     Decay rate ratio is 20× ⇒ steady-state ratio should be ~20× (but limited by production)')
print('='*100)
print(f'  {"Nut":>4} {"T":>7}   {"σE_peak_30":>11} {"σE_peak_120":>12} {"σE_peak_600":>12} {"r_600/30":>10}')
print('-'*72)
for nut, T in itertools.product(NUT_LEVELS, T_LEVELS):
    cells = [(half, max(traj(nut,T,half,'SigmaE'))) for half in HALF_LEVELS if (nut,T,half) in DATA]
    if len(cells) != 3: continue
    p30, p120, p600 = [c[1] for c in cells]
    r = p600/p30 if p30>0 else 0
    print(f'  {nut:>4} {T:>7}   {p30:>11.1f} {p120:>12.1f} {p600:>12.1f} {r:>10.2f}x')

# ---------------------------------------------------------------------------
# F3 — bridge wiring (Nut(t=60s) ≈ INITIAL_NUTRIENTS)
# ---------------------------------------------------------------------------

print()
print('='*100)
print('F3 — Event bridge: Nutrients(t≈1min) close to INITIAL_NUTRIENTS ▢')
print('='*100)
print(f'  {"Nut":>4} {"T":>7} {"t½":>5}   {"target":>8} {"Nut(t=60s)":>12}  {"verdict":>8}')
print('-'*72)
for nut, T, half in itertools.product(NUT_LEVELS, T_LEVELS, HALF_LEVELS):
    if (nut,T,half) not in DATA: continue
    n60 = at_time(nut,T,half,'Nutrients',60)
    ok = abs(n60 - nut) < max(5, 0.1*nut)  # 10% tolerance after 1 min
    print(f'  {nut:>4} {T:>7} {half:>5}   {nut:>8} {n60:>12.2f}  {"PASS" if ok else "drift":>8}')

# ---------------------------------------------------------------------------
# F7 — Sporulation yield 3-axis matrix
# ---------------------------------------------------------------------------

print()
print('='*100)
print('F7 — Mature_spore endpoint (mean ± std across 16 reps)')
print('='*100)
print(f'  {"Nut":>4} {"T":>7} {"t½":>5}   {"mean":>8} {"std":>8} {"max":>5} {"#zero":>6}')
print('-'*60)
spore_table = {}
for nut, T, half in itertools.product(NUT_LEVELS, T_LEVELS, HALF_LEVELS):
    if (nut,T,half) not in DATA: continue
    r = rep_endpoints(nut,T,half,'Mature_spore')
    if not r:
        # fall back to mean trajectory endpoint
        m = endpoint(nut,T,half,'Mature_spore')
        spore_table[(nut,T,half)] = (m, 0.0, m, 0)
        print(f'  {nut:>4} {T:>7} {half:>5}   {m:>8.2f}     n/a     n/a    n/a')
        continue
    m  = statistics.mean(r); s = statistics.stdev(r) if len(r)>1 else 0
    z  = sum(1 for x in r if x==0)
    spore_table[(nut,T,half)] = (m, s, max(r), z)
    print(f'  {nut:>4} {T:>7} {half:>5}   {m:>8.2f} {s:>8.2f} {int(max(r)):>5} {z:>3}/{len(r):<2}')

# ---------------------------------------------------------------------------
# Marginal main effects (fix two axes, vary third)
# ---------------------------------------------------------------------------
print()
print('='*100)
print('F7b — Main effects on mean Mature_spore yield (averaged over the other two axes)')
print('='*100)
def avg_over(filter_fn):
    vals = [spore_table[k][0] for k in spore_table if filter_fn(*k)]
    return statistics.mean(vals) if vals else 0

print('\n  INITIAL_NUTRIENTS main effect:')
for n in NUT_LEVELS:
    print(f'    Nut={n:>3}: {avg_over(lambda nu,T,h,n=n: nu==n):.2f}')

print('\n  Temperature main effect:')
for T in T_LEVELS:
    print(f'    T={T:>7}: {avg_over(lambda nu,Tx,h,T=T: Tx==T):.2f}')

print('\n  Sigma_halflife main effect:')
for h in HALF_LEVELS:
    print(f'    t½={h:>4}: {avg_over(lambda nu,T,hx,h=h: hx==h):.2f}')

# A x C interaction (does fast decay rescue the abundance sterility?)
print('\n  A × C interaction (Mature_spore mean, marginalised over T):')
print(f'    {"":>5}  ' + ' '.join(f'{f"t½={h}":>10}' for h in HALF_LEVELS))
for n in NUT_LEVELS:
    row = [statistics.mean([spore_table[(n,T,h)][0] for T in T_LEVELS if (n,T,h) in spore_table])
           for h in HALF_LEVELS]
    print(f'    Nut={n:>3} ' + ' '.join(f'{v:>10.2f}' for v in row))

# ---------------------------------------------------------------------------
# Save CSV
# ---------------------------------------------------------------------------
with open(OUT / 'gate_summary_factorial.csv', 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['INITIAL_NUTRIENTS','TEMPERATURE_K','SIGMA_HALFLIFE_MIN',
                'ATP_end','ADP_end','AxP_sum','AxP_err_pct',
                'SigmaE_peak','SigmaE_t_peak_min','SigmaE_end',
                'Nut_at_60s','Spore_mean','Spore_std','Spore_max','Spore_zeros'])
    for nut, T, half in itertools.product(NUT_LEVELS, T_LEVELS, HALF_LEVELS):
        if (nut,T,half) not in DATA: continue
        a = endpoint(nut,T,half,'ATP_pool'); d = endpoint(nut,T,half,'ADP_pool')
        tj = traj(nut,T,half,'SigmaE'); times = DATA[(nut,T,half)]['times']
        pk = max(tj); t_pk = times[tj.index(pk)]/60
        end = tj[-1]
        n60 = at_time(nut,T,half,'Nutrients',60)
        m,s,mx,z = spore_table.get((nut,T,half), (0,0,0,0))
        w.writerow([nut, T, half, f'{a:.1f}', f'{d:.1f}', f'{a+d:.1f}',
                    f'{abs(a+d-5995)/5995*100:.2f}',
                    f'{pk:.1f}', f'{t_pk:.1f}', f'{end:.1f}',
                    f'{n60:.2f}', f'{m:.2f}', f'{s:.2f}', int(mx), z])

print(f'\nCSV → {OUT / "gate_summary_factorial.csv"}')
print('Done.')
