"""Deep biological-insight mining from run_20260509_125201.

Runs eight analyses on the time-series statistics + per-replicate endpoints:
  A. ATP-cascade phase diagram (where is the cascade when ATP crosses 2.21?)
  B. Cascade ignition velocity (slope of first-appearance per species)
  C. Sporulation success heterogeneity (per-rep distribution of Mature_spore)
  D. Energy budget (ATP turnover vs spore yield efficiency)
  E. Mass conservation (ATP+ADP, GTP+GDP)
  F. Sigma factor accumulation peaks (when each peaks, amplitude)
  G. Stochastic CV per species (decision-noise sensitivity)
  H. Phosphorelay throughput (KinA/Spo0F/Spo0A firing balance)
"""
import json, csv, statistics
from pathlib import Path

RUN = Path('/tmp/thesis_run')
OUT = Path('/home/simao/projetos/shypn/workspace/projects/thesis/analysis/thesis_revision_v3')
OUT.mkdir(parents=True, exist_ok=True)

model = json.loads((RUN / 'model_snapshot.shy').read_text())
ID2NAME = {p['id']: p['name'] for p in model['places']}
NAME2ID = {v: k for k, v in ID2NAME.items()}

CONDITIONS = ['Nutrients_eq_10', 'Nutrients_eq_30', 'Baseline',
              'Nutrients_eq_100', 'Nutrients_eq_300']
NUT_M0 = {'Nutrients_eq_10': 10, 'Nutrients_eq_30': 30, 'Baseline': 100,
          'Nutrients_eq_100': 100, 'Nutrients_eq_300': 300}

CASCADE = ['Spo0A_P', 'SigmaH', 'SigmaF', 'SigmaE', 'SigmaG', 'SigmaK',
           'Septum', 'Forespore', 'Mother_cell',
           'Cortex', 'Inner_coat', 'Outer_coat', 'Mature_spore']

# Load all condition data
data = {}
for c in CONDITIONS:
    s = json.loads((RUN / f'condition_{c}' / 'statistics.json').read_text())
    with open(RUN / f'condition_{c}' / 'replicates.csv') as f:
        r = csv.reader(f); hdr = next(r); rows = list(r)
    data[c] = {
        'times': s['time_points'],
        'ss': s['species_statistics'],
        'rep_hdr': hdr,
        'rep_rows': rows,
    }

def get_traj(cond, place_name, key='mean'):
    return data[cond]['ss'][NAME2ID[place_name]][key]

def get_at_time(cond, place_name, t, key='mean'):
    times = data[cond]['times']
    idx = min(range(len(times)), key=lambda i: abs(times[i] - t))
    return data[cond]['ss'][NAME2ID[place_name]][key][idx]

def first_passage(cond, place_name, threshold, going_down=False, key='mean'):
    times = data[cond]['times']
    traj = get_traj(cond, place_name, key)
    for t, v in zip(times, traj):
        if (going_down and v <= threshold) or (not going_down and v >= threshold):
            return t
    return None

def get_rep_col(cond, col_name):
    """Per-replicate endpoint values for a column."""
    hdr = data[cond]['rep_hdr']
    if col_name not in hdr:
        return None
    idx = hdr.index(col_name)
    return [float(row[idx]) for row in data[cond]['rep_rows']]

# ============================================================================
# A. ATP-cascade phase diagram: where is the cascade when ATP crosses 2.21 mM?
# ============================================================================
print('=' * 100)
print('ANALYSIS A — ATP-cascade phase diagram')
print('At the moment ATP crosses the Fujita anchor (2.21 mM), where is the cascade?')
print('=' * 100)
print(f"{'Condition':22s} {'t_cross (min)':>14s}", end='')
for sp in ['Spo0A_P', 'SigmaH', 'SigmaF', 'SigmaE', 'SigmaG', 'SigmaK',
          'Septum', 'Mature_spore']:
    print(f" {sp[:10]:>11s}", end='')
print()
print('-' * 130)
for c in CONDITIONS:
    t_cross = first_passage(c, 'ATP_pool', 2.21, going_down=True)
    if t_cross is None:
        print(f"{c:22s} {'—':>14s} (basin floor never reached 2.21 in mean traj)")
        continue
    print(f"{c:22s} {t_cross/60:>14.1f}", end='')
    for sp in ['Spo0A_P', 'SigmaH', 'SigmaF', 'SigmaE', 'SigmaG', 'SigmaK',
              'Septum', 'Mature_spore']:
        v = get_at_time(c, sp, t_cross)
        print(f" {v:>11.2f}", end='')
    print()

# ============================================================================
# B. Cascade ignition velocity — how fast does each species rise after appearance?
# ============================================================================
print('\n' + '=' * 100)
print('ANALYSIS B — Cascade ignition velocity (rate of rise in first 60 s after first appearance)')
print('=' * 100)
print(f"{'Condition':22s}", end='')
for sp in ['Spo0A_P', 'SigmaF', 'SigmaE', 'Mature_spore']:
    print(f" {sp+'_v':>14s}", end='')
print()
print('-' * 90)
for c in CONDITIONS:
    print(f"{c:22s}", end='')
    times = data[c]['times']
    for sp in ['Spo0A_P', 'SigmaF', 'SigmaE', 'Mature_spore']:
        traj = get_traj(c, sp)
        # find first time where mean > 0.5
        t0_idx = next((i for i, v in enumerate(traj) if v > 0.5), None)
        if t0_idx is None or t0_idx + 12 >= len(traj):
            print(f" {'—':>14s}", end='')
            continue
        # 60 s = 12 samples (5 s resolution)
        t1_idx = t0_idx + 12
        v0, v1 = traj[t0_idx], traj[t1_idx]
        dv_dt = (v1 - v0) / ((times[t1_idx] - times[t0_idx]) / 60)  # tokens/min
        print(f" {dv_dt:>14.3f}", end='')
    print('   tokens/min')

# ============================================================================
# C. Sporulation success heterogeneity — per-replicate distribution
# ============================================================================
print('\n' + '=' * 100)
print('ANALYSIS C — Sporulation heterogeneity (per-replicate Mature_spore distribution)')
print('Are replicates bimodal (some commit, some don\'t) or unimodal?')
print('=' * 100)
print(f"{'Condition':22s} {'min':>6s} {'p25':>6s} {'p50':>6s} {'p75':>6s} {'max':>6s} "
      f"{'mean':>7s} {'std':>7s} {'CV':>5s} {'#zero':>6s} {'#high':>6s}")
print('-' * 100)
for c in CONDITIONS:
    vals = sorted(get_rep_col(c, 'Mature_spore_final'))
    n = len(vals)
    p25 = vals[n//4]; p50 = vals[n//2]; p75 = vals[3*n//4]
    mu = sum(vals)/n
    sd = (sum((v-mu)**2 for v in vals)/n)**0.5
    cv = sd/mu if mu > 0 else float('inf')
    n_zero = sum(1 for v in vals if v == 0)
    threshold_high = max(5, 2*mu)  # "high" = at least 2× mean or ≥5 spores
    n_high = sum(1 for v in vals if v >= threshold_high)
    print(f"{c:22s} {vals[0]:>6.0f} {p25:>6.0f} {p50:>6.0f} {p75:>6.0f} {vals[-1]:>6.0f} "
          f"{mu:>7.2f} {sd:>7.2f} {cv:>5.2f} {n_zero:>6d} {n_high:>6d}")

# ============================================================================
# D. Energy budget — ATP turnover vs spore yield
# ============================================================================
print('\n' + '=' * 100)
print('ANALYSIS D — Energy budget (ATP turnover vs sporulation yield)')
print('=' * 100)
print(f"{'Condition':22s} {'ATP_regen':>11s} {'ATP_basal':>11s} {'KinA_fir':>10s} "
      f"{'Total_fir':>10s} {'Spore':>7s} {'ATP/spore':>11s}")
print('-' * 100)
for c in CONDITIONS:
    atp_regen = sum(get_rep_col(c, 'Source_ATP_regen_firings')) / 16
    atp_basal = sum(get_rep_col(c, 'Source_ATP_stationary_firings')) / 16
    kina = sum(get_rep_col(c, 'T_KinA_activation_firings')) / 16
    # sum all firings as proxy for total ATP work
    total_fir = 0
    for col in data[c]['rep_hdr']:
        if col.endswith('_firings') and 'ATP_regen' not in col and 'GTP_regen' not in col and 'nutrient' not in col and 'cell_density' not in col and 'stationary' not in col:
            total_fir += sum(float(row[data[c]['rep_hdr'].index(col)]) for row in data[c]['rep_rows']) / 16
    spore = sum(get_rep_col(c, 'Mature_spore_final')) / 16
    eff = total_fir / spore if spore > 0 else float('inf')
    print(f"{c:22s} {atp_regen:>11.0f} {atp_basal:>11.0f} {kina:>10.0f} "
          f"{total_fir:>10.0f} {spore:>7.2f} {eff:>11.0f}")

# ============================================================================
# E. Mass conservation — ATP + ADP, GTP + GDP at endpoints
# ============================================================================
print('\n' + '=' * 100)
print('ANALYSIS E — Mass conservation (adenylate + guanylate pools)')
print('Initial: ATP+ADP = 5995, GTP+GDP = 5995 per replicate')
print('=' * 100)
print(f"{'Condition':22s} {'ATP+ADP_end':>14s} {'GTP+GDP_end':>14s} "
      f"{'ΔAxP':>8s} {'ΔGxP':>8s}")
print('-' * 80)
for c in CONDITIONS:
    atp = get_rep_col(c, 'ATP_pool_final')
    adp = get_rep_col(c, 'ADP_pool_final')
    gtp = get_rep_col(c, 'GTP_pool_final')
    gdp = get_rep_col(c, 'GDP_pool_final')
    axp = sum(a+d for a,d in zip(atp,adp))/16
    gxp = sum(g+d for g,d in zip(gtp,gdp))/16
    print(f"{c:22s} {axp:>14.1f} {gxp:>14.1f} {axp-5995:>+8.0f} {gxp-5995:>+8.0f}")

# ============================================================================
# F. Sigma factor accumulation peaks
# ============================================================================
print('\n' + '=' * 100)
print('ANALYSIS F — Sigma factor accumulation peaks (peak time and amplitude)')
print('=' * 100)
for c in CONDITIONS:
    print(f'\n  {c} (Nut₀ = {NUT_M0[c]}):')
    print(f"    {'Sigma':>10s}  {'t_peak (min)':>14s}  {'peak_value':>12s}  {'endpoint':>10s}  {'fraction_kept':>14s}")
    times = data[c]['times']
    for sp in ['SigmaH', 'SigmaF', 'SigmaE', 'SigmaG', 'SigmaK']:
        traj = get_traj(c, sp)
        peak = max(traj)
        peak_t = times[traj.index(peak)]
        endpoint = traj[-1]
        kept = endpoint / peak if peak > 0 else 0
        print(f"    {sp:>10s}  {peak_t/60:>14.1f}  {peak:>12.1f}  {endpoint:>10.1f}  {kept:>14.2%}")

# ============================================================================
# G. Stochastic CV per species (decision-noise sensitivity)
# ============================================================================
print('\n' + '=' * 100)
print('ANALYSIS G — Stochastic CV at endpoint (per-replicate variability)')
print('Species with high CV are decision-noise-sensitive (bimodal commitment)')
print('=' * 100)
SPECIES = ['Spo0A_P', 'SigmaH', 'SigmaF', 'SigmaE', 'SigmaG', 'SigmaK',
           'Septum', 'Forespore', 'Mother_cell', 'Cortex',
           'Inner_coat', 'Outer_coat', 'Mature_spore']
print(f"{'Species':>14s}", end='')
for c in CONDITIONS:
    print(f" {c[:12]:>13s}", end='')
print()
print('-' * 100)
for sp in SPECIES:
    print(f"{sp:>14s}", end='')
    for c in CONDITIONS:
        vals = get_rep_col(c, f'{sp}_final')
        if vals is None:
            print(f" {'—':>13s}", end=''); continue
        mu = sum(vals)/16
        sd = (sum((v-mu)**2 for v in vals)/16)**0.5
        cv = sd/mu if mu > 0 else float('inf')
        cv_str = f"{cv:.2f}" if cv != float('inf') else "∞"
        print(f" {cv_str:>13s}", end='')
    print()

# ============================================================================
# H. Phosphorelay throughput
# ============================================================================
print('\n' + '=' * 100)
print('ANALYSIS H — Phosphorelay throughput (firings per replicate)')
print('Bottleneck identification: which step caps the cascade?')
print('=' * 100)
print(f"{'Condition':22s}", end='')
for col in ['T_KinA_activation', 'T_Spo0F_phosphorylation', 'T_Spo0A_phosphorylation',
            'T_Spo0F_dephos', 'T_Spo0A_dephosphorylation', 'T_sigmaH_transcription']:
    print(f" {col.replace('T_','')[:12]:>13s}", end='')
print()
print('-' * 130)
for c in CONDITIONS:
    print(f"{c:22s}", end='')
    for col in ['T_KinA_activation', 'T_Spo0F_phosphorylation', 'T_Spo0A_phosphorylation',
                'T_Spo0F_dephos', 'T_Spo0A_dephosphorylation', 'T_sigmaH_transcription']:
        vals = get_rep_col(c, f'{col}_firings')
        mu = sum(vals)/16
        print(f" {mu:>13.0f}", end='')
    print()

print(f'\n✓ Deep analysis complete. Tables above. Stored in {OUT}/')
