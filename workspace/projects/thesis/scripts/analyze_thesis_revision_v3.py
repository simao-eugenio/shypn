"""Analyze run_20260509_125201 — bacillus thesis-revision sweep.

Mines emergent thresholds, cascade timings, mature-spore appearance, and
commitment→completion lag per condition, so Chapter 4 can be rewritten with
honest values from the current SHyPN engine.
"""
import json, csv
from pathlib import Path

RUN = Path('/tmp/thesis_run')
OUT = Path('/home/simao/projetos/shypn/workspace/projects/thesis/analysis/thesis_revision_v3')
OUT.mkdir(parents=True, exist_ok=True)

# Build place-id -> name map from snapshot
model = json.loads((RUN / 'model_snapshot.shy').read_text())
ID2NAME = {p['id']: p['name'] for p in model['places']}
NAME2ID = {v: k for k, v in ID2NAME.items()}

CONDITIONS = ['Baseline', 'Nutrients_eq_10', 'Nutrients_eq_30',
              'Nutrients_eq_100', 'Nutrients_eq_300']

# Cascade species we care about (in expected order)
CASCADE = ['Spo0A_P', 'SigmaH', 'SigmaF', 'SigmaE', 'SigmaG', 'SigmaK',
           'Septum', 'Forespore', 'Mother_cell',
           'Cortex', 'Inner_coat', 'Outer_coat', 'Mature_spore']

# ATP threshold candidates to scan (mM in the model's natural units)
ATP_THRESHOLDS = [4000, 2000, 1000, 500, 200, 100, 50, 20, 10, 5, 2.21, 1, 0.5, 0.1]

def first_passage_time(times, mean_traj, threshold, going_down=True):
    """Return time when mean trajectory first crosses threshold."""
    for t, v in zip(times, mean_traj):
        if going_down and v <= threshold:
            return t
        if not going_down and v >= threshold:
            return t
    return None

def first_appearance(times, mean_traj, eps=0.5):
    """First time mean trajectory exceeds eps (i.e. species 'appears')."""
    return first_passage_time(times, mean_traj, eps, going_down=False)

# Per-condition analysis
report_rows = []
for cond in CONDITIONS:
    stats = json.loads((RUN / f'condition_{cond}' / 'statistics.json').read_text())
    times = stats['time_points']
    ss = stats['species_statistics']

    atp_id = NAME2ID['ATP_pool']
    atp_mean = ss[atp_id]['mean']
    atp_std = ss[atp_id]['std']

    nut_id = NAME2ID['Nutrients']
    nut_mean = ss[nut_id]['mean']

    # ATP first-passage times per threshold
    atp_fpt = {th: first_passage_time(times, atp_mean, th, going_down=True)
               for th in ATP_THRESHOLDS}

    # Nutrient depletion time
    nut_dep_t = first_passage_time(times, nut_mean, 0.5, going_down=True)

    # Cascade first-appearance times (mean ≥ 0.5)
    cascade_t = {}
    for sp in CASCADE:
        if sp not in NAME2ID:
            cascade_t[sp] = None; continue
        sp_id = NAME2ID[sp]
        sp_mean = ss[sp_id]['mean']
        cascade_t[sp] = first_appearance(times, sp_mean, eps=0.5)

    # Endpoints
    endpoints = {}
    for name, pid in NAME2ID.items():
        endpoints[name] = (ss[pid]['mean'][-1], ss[pid]['std'][-1])

    # ATP min and time of min
    atp_min = min(atp_mean)
    atp_min_t = times[atp_mean.index(atp_min)]

    # Mature spore: time to reach 50% of its endpoint mean
    ms_id = NAME2ID['Mature_spore']
    ms_mean = ss[ms_id]['mean']
    ms_end = ms_mean[-1]
    ms_half_t = first_passage_time(times, ms_mean, ms_end * 0.5, going_down=False) if ms_end > 0.5 else None
    ms_first_t = first_appearance(times, ms_mean, eps=0.5)

    report_rows.append({
        'condition': cond,
        'nutrients_M0': model['places'][NAME2ID['Nutrients'].__class__ is str and 0 or 0]['initial_marking'] if cond=='Baseline' else None,
        'atp_at_t0': atp_mean[0],
        'atp_min_mean': atp_min,
        'atp_min_time_min': atp_min_t / 60,
        'atp_endpoint_mean': atp_mean[-1],
        'atp_endpoint_std': atp_std[-1],
        'nutrient_depletion_time_min': nut_dep_t / 60 if nut_dep_t else None,
        'mature_spore_endpoint_mean': endpoints['Mature_spore'][0],
        'mature_spore_endpoint_std': endpoints['Mature_spore'][1],
        'mature_spore_first_appear_min': ms_first_t / 60 if ms_first_t else None,
        'mature_spore_t_half_min': ms_half_t / 60 if ms_half_t else None,
        'atp_fpt': atp_fpt,
        'cascade_t': cascade_t,
        'endpoints': endpoints,
    })

# === Print summary tables ===

# Table 1: Top-line endpoint summary
print('=' * 100)
print('TABLE 1 — Top-line summary per condition (mean values)')
print('=' * 100)
print(f"{'Condition':22s} {'ATP_min':>10s} {'t_ATPmin':>10s} {'Nut_dep_t':>11s} {'MS_end':>9s}±std  {'MS_first':>10s} {'MS_t_half':>10s}")
print(f"{'':22s} {'(mM)':>10s} {'(min)':>10s} {'(min)':>11s} {'(#)':>9s}     {'(min)':>10s} {'(min)':>10s}")
print('-' * 100)
for r in report_rows:
    nd = f"{r['nutrient_depletion_time_min']:.1f}" if r['nutrient_depletion_time_min'] else '   —'
    msf = f"{r['mature_spore_first_appear_min']:.1f}" if r['mature_spore_first_appear_min'] else '   —'
    msh = f"{r['mature_spore_t_half_min']:.1f}" if r['mature_spore_t_half_min'] else '   —'
    print(f"{r['condition']:22s} {r['atp_min_mean']:>10.3f} {r['atp_min_time_min']:>10.1f} {nd:>11s} "
          f"{r['mature_spore_endpoint_mean']:>9.2f}±{r['mature_spore_endpoint_std']:.2f}  "
          f"{msf:>10s} {msh:>10s}")

# Table 2: ATP threshold-crossing times per condition
print('\n' + '=' * 100)
print('TABLE 2 — ATP threshold-crossing times (min) per condition')
print('=' * 100)
hdr = f"{'Threshold (mM)':>15s}"
for r in report_rows:
    hdr += f"  {r['condition'][:14]:>14s}"
print(hdr)
print('-' * 100)
for th in ATP_THRESHOLDS:
    line = f"{th:>15.2f}"
    for r in report_rows:
        v = r['atp_fpt'][th]
        if v is None:
            line += f"  {'    —':>14s}"
        else:
            line += f"  {v/60:>14.1f}"
    print(line)

# Table 3: Cascade first-appearance times per condition
print('\n' + '=' * 100)
print('TABLE 3 — Cascade first-appearance times (min, mean ≥ 0.5)')
print('=' * 100)
hdr = f"{'Species':>14s}"
for r in report_rows:
    hdr += f"  {r['condition'][:14]:>14s}"
print(hdr)
print('-' * 100)
for sp in CASCADE:
    line = f"{sp:>14s}"
    for r in report_rows:
        v = r['cascade_t'][sp]
        line += f"  {'      —':>14s}" if v is None else f"  {v/60:>14.1f}"
    print(line)

# Table 4: All endpoint markings per condition
print('\n' + '=' * 100)
print('TABLE 4 — Endpoint markings per place (mean ± std) at t=21600 s')
print('=' * 100)
all_names = list(NAME2ID.keys())
hdr = f"{'Place':>16s}"
for r in report_rows:
    hdr += f"  {r['condition'][:16]:>20s}"
print(hdr)
print('-' * 110)
for name in all_names:
    line = f"{name:>16s}"
    for r in report_rows:
        m, s = r['endpoints'][name]
        line += f"  {m:>10.3f}±{s:>7.3f}"
    print(line)

# === Write CSVs ===

# Endpoint table
with (OUT / 'endpoint_table.csv').open('w', newline='') as f:
    w = csv.writer(f)
    hdr = ['place'] + [f'{r["condition"]}_mean' for r in report_rows] + [f'{r["condition"]}_std' for r in report_rows]
    w.writerow(hdr)
    for name in all_names:
        row = [name] + [f'{r["endpoints"][name][0]:.6f}' for r in report_rows] + [f'{r["endpoints"][name][1]:.6f}' for r in report_rows]
        w.writerow(row)

# ATP threshold table
with (OUT / 'atp_threshold_table.csv').open('w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['threshold_mM'] + [r['condition'] + '_t_min' for r in report_rows])
    for th in ATP_THRESHOLDS:
        row = [th] + [(r['atp_fpt'][th]/60 if r['atp_fpt'][th] else '') for r in report_rows]
        w.writerow(row)

# Cascade timing table
with (OUT / 'cascade_timing_table.csv').open('w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['species'] + [r['condition'] + '_t_min' for r in report_rows])
    for sp in CASCADE:
        row = [sp] + [(r['cascade_t'][sp]/60 if r['cascade_t'][sp] else '') for r in report_rows]
        w.writerow(row)

print(f'\n✓ CSVs written to {OUT}/')
