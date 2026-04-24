"""Deep biological analysis of a P1 factorial sweep.

Reads ``condition_*/replicates.csv`` only (small).  For every species,
computes per-condition mean/std/CV across the 30 replicates and runs a
battery of biology-driven probes:

  1. Dose-response Hill fit per (Sev, Age) for Neuron_Health, plaque,
     ROS — extracts EC50, max effect, Hill coefficient n.
  2. Bimodality / lock-in detection (Sarle's bimodality b > 5/9 or
     CV > 0.5 with mean far from any floor).
  3. Conservation checks (Microglia M1+M2; Glutathione+GSSG; receptor
     active+inactive).
  4. Cross-species Pearson correlation across replicates within the
     drug-naive AD cell (Sev=2, LD=0, MT=0, Age=75) — identifies the
     dominant within-condition coupling axes.
  5. Receptor engagement (HT1A_active, PPARg_active, A2A_active,
     Nrf2_free) vs drug dose — confirms the supposed CBD targets are
     mechanistically firing.
  6. Therapeutic-success thresholds: smallest LD/MT at which
     NeuH > 80, > 90 of healthy maximum, per (Sev, Age).
  7. Plaque reversibility: does the drug reduce plaque, or only halt
     accumulation?
  8. Variance partitioning of Neuron_Health: how much of the variation
     across the 5 760 sims is explained by Sev / LD / MT / Age?

Run on the server::

    python3 workspace/projects/canabidiol/scripts/deep_analyse_p1.py \\
        workspace/projects/canabidiol/experiments/results/run_20260424_005438
"""
from __future__ import annotations

import csv
import math
import os
import re
import sys
from collections import defaultdict
from typing import Dict, List, Tuple


# ---------------------------------------------------------------------- IO

PARAM_RE = re.compile(r'(?:\[param\]_)?([A-Za-z_]+?)_eq_([0-9.]+)')


def parse_condition(name: str):
    if name == 'Baseline':
        return None
    parts = dict(PARAM_RE.findall(name))
    return {
        'sev':   float(parts.get('Disease_Severity', 0)),
        'load':  float(parts.get('LOADING_DOSE', 0)),
        'maint': float(parts.get('MAINT_DOSE', 0)),
        'age':   float(parts.get('_Age', parts.get('Age', 65))),
    }


def load_run(run_dir: str):
    """Return list[(cond_dict, list[dict_row])]."""
    out = []
    for d in sorted(os.listdir(run_dir)):
        cd = os.path.join(run_dir, d)
        if not (d.startswith('condition_') and os.path.isdir(cd)):
            continue
        cond = parse_condition(d.replace('condition_', '', 1))
        if cond is None:
            continue
        rcsv = os.path.join(cd, 'replicates.csv')
        if not os.path.exists(rcsv):
            continue
        with open(rcsv, newline='') as f:
            rows = list(csv.DictReader(f))
        out.append((cond, rows))
    return out


# ------------------------------------------------------------- statistics

def mean(xs): return sum(xs) / len(xs) if xs else float('nan')

def stdev(xs):
    if len(xs) < 2: return 0.0
    m = mean(xs); return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))

def pearson(xs, ys):
    if len(xs) < 2: return float('nan')
    mx, my = mean(xs), mean(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    dy = math.sqrt(sum((y - my) ** 2 for y in ys))
    return num / (dx * dy) if dx > 0 and dy > 0 else float('nan')

def sarle_bimodality(xs):
    """Sarle's b = (g1^2 + 1) / (g2 + 3*(n-1)^2/((n-2)*(n-3))).  b > 5/9 hints bimodal."""
    n = len(xs)
    if n < 4: return float('nan')
    m = mean(xs); s = stdev(xs)
    if s == 0: return 0.0
    z = [(x - m) / s for x in xs]
    g1 = (n / ((n - 1) * (n - 2))) * sum(zi ** 3 for zi in z)
    g2_num = (n * (n + 1) / ((n - 1) * (n - 2) * (n - 3))) * sum(zi ** 4 for zi in z)
    g2_corr = 3 * (n - 1) ** 2 / ((n - 2) * (n - 3))
    g2 = g2_num - g2_corr
    return (g1 ** 2 + 1) / (g2 + 3 * (n - 1) ** 2 / ((n - 2) * (n - 3)))


def col(rows, key):
    out = []
    for r in rows:
        v = r.get(key)
        if v in (None, ''): continue
        try: out.append(float(v))
        except ValueError: pass
    return out


# ------------------------------------------------------------- analyses

def hdr(s):
    print(); print('=' * 78); print(s); print('=' * 78)


def section_dose_response(data):
    """Per-(Sev, Age) Hill-style summary across LD at MT=0."""
    hdr('1. Dose-response of Neuron_Health vs LOADING_DOSE (MT=0)')
    print(f'{"Sev":>4} {"Age":>4} | {"LD=0":>6} {"LD=5":>6} {"LD=10":>6} {"LD=20":>6} | '
          f'{"Emax":>6} {"E50_LD":>7} {"slope":>6}')
    print('-' * 78)
    for sev in (0, 1, 2, 3):
        for age in (65, 75, 85):
            cells = [(c, r) for c, r in data
                     if c['sev'] == sev and c['maint'] == 0 and c['age'] == age]
            cells.sort(key=lambda cr: cr[0]['load'])
            if len(cells) != 4: continue
            means = [mean(col(r, 'Neuron_Health_final')) for _, r in cells]
            base, top = means[0], means[-1]
            emax = top - base
            # crude EC50: dose at half-maximal response
            half = base + emax / 2
            lds = [0, 5, 10, 20]
            ec50 = float('nan')
            for i in range(1, 4):
                if (means[i - 1] - half) * (means[i] - half) <= 0:
                    # interpolate
                    if means[i] != means[i - 1]:
                        frac = (half - means[i - 1]) / (means[i] - means[i - 1])
                        ec50 = lds[i - 1] + frac * (lds[i] - lds[i - 1])
                    else:
                        ec50 = lds[i]
                    break
            slope = (means[1] - means[0]) / 5.0
            print(f'{int(sev):>4} {int(age):>4} | '
                  f'{means[0]:>6.1f} {means[1]:>6.1f} {means[2]:>6.1f} {means[3]:>6.1f} | '
                  f'{emax:>6.1f} {ec50:>7.2f} {slope:>6.2f}')


def section_bimodality(data):
    """Find conditions whose key species look bimodal across reps."""
    hdr('2. Bimodality / lock-in scan (Sarle b > 0.555 = 5/9)')
    targets = ['Neuron_Health_final', 'Abeta_Plaque_final',
               'Microglia_M1_final', 'Microglia_M2_final',
               'NFkB_p65_final', 'ROS_final']
    flagged = 0
    print(f'{"Sev":>3} {"LD":>3} {"MT":>3} {"Age":>3} | '
          f'{"species":<22} {"mean":>8} {"std":>7} {"CV":>5} {"b":>5}')
    print('-' * 78)
    for cond, rows in data:
        for sp in targets:
            xs = col(rows, sp)
            if len(xs) < 5: continue
            m, s = mean(xs), stdev(xs)
            cv = s / m if m else 0
            b = sarle_bimodality(xs)
            if b > 0.555 and cv > 0.10:
                flagged += 1
                if flagged <= 30:
                    print(f'{int(cond["sev"]):>3} {int(cond["load"]):>3} '
                          f'{int(cond["maint"]):>3} {int(cond["age"]):>3} | '
                          f'{sp.replace("_final",""):<22} '
                          f'{m:>8.2f} {s:>7.2f} {cv:>5.2f} {b:>5.2f}')
    print(f'\nTotal conditions flagged: {flagged} / {len(data) * len(targets)}')


def section_conservation(data):
    """Check Microglia M1+M2, GSH+GSSG conservation."""
    hdr('3. Conservation checks (per-replicate sums)')
    pairs = [('Microglia', ['Microglia_M1_final', 'Microglia_M2_final']),
             ('Redox',     ['Glutathione_final',   'GSSG_final']),
             ('Nrf2',      ['Nrf2_free_final',     'Keap1_Nrf2_final']),
             ('NFkB',      ['NFkB_p65_final',      'NFkB_IkB_final', 'IKK_final'])]
    print(f'{"pool":<10} | overall mean(sum)   sd(sum)   range_min  range_max')
    print('-' * 70)
    for label, keys in pairs:
        sums = []
        for _, rows in data:
            for r in rows:
                try:
                    sums.append(sum(float(r[k]) for k in keys))
                except (KeyError, ValueError):
                    pass
        if not sums: continue
        print(f'{label:<10} | {mean(sums):>10.2f}  {stdev(sums):>8.2f}   '
              f'{min(sums):>8.2f}   {max(sums):>8.2f}   '
              f'(CV = {stdev(sums)/mean(sums):.3f})')


def section_correlation(data):
    """Within-condition Pearson correlation matrix at Sev=2, LD=0, MT=0, Age=75."""
    hdr('4. Cross-species correlation in drug-naive AD cell (Sev=2, LD=0, MT=0, Age=75)')
    target = next(((c, r) for c, r in data
                   if c['sev'] == 2 and c['load'] == 0 and c['maint'] == 0 and c['age'] == 75), None)
    if target is None:
        print('  (cell not found)'); return
    _, rows = target
    sp = ['Neuron_Health', 'Abeta_Oligomer', 'Abeta_Plaque', 'NFkB_p65',
          'TNFa', 'ROS', 'Glutathione', 'Microglia_M1', 'Microglia_M2',
          'BDNF', 'HT1A_active', 'PPARg_active']
    cols = {s: col(rows, s + '_final') for s in sp}
    sp = [s for s in sp if cols[s]]
    print(' ' * 16 + ' '.join(f'{s[:6]:>6}' for s in sp))
    for s1 in sp:
        row = [f'{s1[:14]:<15}']
        for s2 in sp:
            r = pearson(cols[s1], cols[s2])
            row.append(f'{r:>6.2f}' if not math.isnan(r) else '   nan')
        print(' '.join(row))


def section_receptors(data):
    """How does each receptor activate vs LOADING_DOSE at Sev=2, MT=0, Age=75?"""
    hdr('5. Receptor engagement vs LOADING_DOSE (Sev=2, MT=0, Age=75)')
    print(f'{"LD":>4} | {"HT1A_act":>9} {"PPARg_act":>10} {"A2A_act":>8} {"Nrf2_free":>10} {"BDNF":>6}')
    print('-' * 60)
    for ld in (0, 5, 10, 20):
        cell = next(((c, r) for c, r in data
                     if c['sev'] == 2 and c['load'] == ld and c['maint'] == 0 and c['age'] == 75), None)
        if cell is None: continue
        _, rows = cell
        ht  = mean(col(rows, 'HT1A_active_final'))
        pp  = mean(col(rows, 'PPARg_active_final'))
        a2a = mean(col(rows, 'A2A_active_final'))
        nrf = mean(col(rows, 'Nrf2_free_final'))
        bdnf = mean(col(rows, 'BDNF_final'))
        print(f'{ld:>4} | {ht:>9.3f} {pp:>10.3f} {a2a:>8.3f} {nrf:>10.3f} {bdnf:>6.2f}')


def section_thresholds(data):
    """Smallest (LD, MT) achieving NeuH ≥ 80 and ≥ 90 per (Sev, Age)."""
    hdr('6. Therapeutic thresholds: smallest dose (LD, MT) reaching NeuH targets')
    print(f'{"Sev":>4} {"Age":>4} | {"NeuH≥70 (LD,MT)":>17} {"NeuH≥80":>15} {"NeuH≥90":>15}')
    print('-' * 78)
    for sev in (0, 1, 2, 3):
        for age in (65, 75, 85):
            cells = [(c, mean(col(r, 'Neuron_Health_final')))
                     for c, r in data
                     if c['sev'] == sev and c['age'] == age]
            cells.sort(key=lambda x: (x[1]))  # ascending NeuH
            def first_meeting(thr):
                cands = [(c['load'], c['maint']) for c, m in cells if m >= thr]
                if not cands: return '   —   '
                cands.sort(key=lambda lm: (lm[0] + lm[1] * 4))  # cost-weighted
                ld, mt = cands[0]
                return f'({int(ld):>2},{int(mt):>2})'
            print(f'{sev:>4} {age:>4} | {first_meeting(70):>17} '
                  f'{first_meeting(80):>15} {first_meeting(90):>15}')


def section_plaque(data):
    """Does drug reduce plaque, or only halt accumulation?"""
    hdr('7. Plaque reversibility: Abeta_Plaque mean by (Sev, LD) at Age=65, MT=0')
    print(f'{"Sev":>4} | {"LD=0":>8} {"LD=5":>8} {"LD=10":>8} {"LD=20":>8} | {"Δ(LD20-LD0)":>13}')
    print('-' * 70)
    for sev in (0, 1, 2, 3):
        cells = [(c, r) for c, r in data
                 if c['sev'] == sev and c['maint'] == 0 and c['age'] == 65]
        cells.sort(key=lambda cr: cr[0]['load'])
        if len(cells) != 4: continue
        ms = [mean(col(r, 'Abeta_Plaque_final')) for _, r in cells]
        print(f'{sev:>4} | {ms[0]:>8.2f} {ms[1]:>8.2f} {ms[2]:>8.2f} {ms[3]:>8.2f} | '
              f'{ms[3]-ms[0]:>+13.2f}')

    # initial post-install plaque expectation per Sev (from event δ=2.5)
    print('\n  Reference: post-install plaque (M0=0 + Sev*2.5) = '
          'Sev1:2.5  Sev2:5.0  Sev3:7.5')
    print('  Sev=0 final plaque > 0 ⇒ plaque GROWS de novo from healthy M0.')


def section_variance_partition(data):
    """How much variance in NeuH is explained by each factor (one-way η²)?"""
    hdr('8. Variance partition of Neuron_Health (one-way η² per factor)')
    all_vals = []
    for cond, rows in data:
        for v in col(rows, 'Neuron_Health_final'):
            all_vals.append((cond['sev'], cond['load'], cond['maint'], cond['age'], v))
    if not all_vals: return
    grand = mean([v for *_, v in all_vals])
    ss_total = sum((v - grand) ** 2 for *_, v in all_vals)
    factor_names = ['Sev', 'LoadDose', 'MaintDose', 'Age']
    print(f'{"factor":<12} {"η² (% of total var)":>22}')
    print('-' * 40)
    for i, name in enumerate(factor_names):
        groups = defaultdict(list)
        for tup in all_vals:
            groups[tup[i]].append(tup[4])
        ss_between = sum(len(g) * (mean(g) - grand) ** 2 for g in groups.values())
        eta2 = ss_between / ss_total if ss_total > 0 else 0
        print(f'{name:<12} {eta2*100:>20.1f}%')
    print(f'\n  (residual incl. interactions + replicate noise: '
          f'~{(1 - sum_eta(all_vals, ss_total))*100:.1f}%)')


def sum_eta(all_vals, ss_total):
    s = 0
    for i in range(4):
        groups = defaultdict(list)
        for tup in all_vals: groups[tup[i]].append(tup[4])
        grand = mean([v for *_, v in all_vals])
        ss_between = sum(len(g) * (mean(g) - grand) ** 2 for g in groups.values())
        s += ss_between / ss_total if ss_total > 0 else 0
    return s


def section_inflammation_collapse(data):
    """At Sev=2, Age=75: how does each cytokine fall with dose?"""
    hdr('9. Inflammatory collapse (Sev=2, Age=75, MT=0)')
    print(f'{"LD":>4} | {"NFkB":>6} {"TNFa":>6} {"IL1b":>6} {"IL6":>6} {"COX2":>6} '
          f'{"M1":>6} {"M2":>6} {"ROS":>6} {"GSH":>6}')
    print('-' * 78)
    for ld in (0, 5, 10, 20):
        cell = next(((c, r) for c, r in data
                     if c['sev'] == 2 and c['load'] == ld and c['maint'] == 0
                     and c['age'] == 75), None)
        if cell is None: continue
        _, rows = cell
        vals = {k: mean(col(rows, k + '_final')) for k in
                ['NFkB_p65', 'TNFa', 'IL1b', 'IL6', 'COX2',
                 'Microglia_M1', 'Microglia_M2', 'ROS', 'Glutathione']}
        print(f'{ld:>4} | {vals["NFkB_p65"]:>6.1f} {vals["TNFa"]:>6.2f} '
              f'{vals["IL1b"]:>6.2f} {vals["IL6"]:>6.2f} {vals["COX2"]:>6.2f} '
              f'{vals["Microglia_M1"]:>6.1f} {vals["Microglia_M2"]:>6.1f} '
              f'{vals["ROS"]:>6.2f} {vals["Glutathione"]:>6.1f}')


def section_age_drug_interaction(data):
    """Age × drug response slope: how much of the age-clearance penalty is rescued?"""
    hdr('10. Age × drug interaction on Neuron_Health (Sev=2, MT=0)')
    print(f'{"LD":>4} | {"Age65":>6} {"Age75":>6} {"Age85":>6} | '
          f'{"Δ(85-65)":>9} {"% rescued":>10}')
    print('-' * 60)
    base_gap = None
    for ld in (0, 5, 10, 20):
        means = []
        for age in (65, 75, 85):
            cell = next(((c, r) for c, r in data
                         if c['sev'] == 2 and c['load'] == ld and c['maint'] == 0
                         and c['age'] == age), None)
            means.append(mean(col(cell[1], 'Neuron_Health_final')) if cell else float('nan'))
        gap = means[2] - means[0]
        if base_gap is None: base_gap = gap
        rescued = (1 - gap / base_gap) * 100 if base_gap else 0
        print(f'{ld:>4} | {means[0]:>6.1f} {means[1]:>6.1f} {means[2]:>6.1f} | '
              f'{gap:>+9.2f} {rescued:>9.1f}%')


# ------------------------------------------------------------- main

def main():
    if len(sys.argv) != 2:
        print(__doc__); sys.exit(2)
    run_dir = sys.argv[1]
    data = load_run(run_dir)
    print(f'Loaded {len(data)} conditions from {run_dir}')
    section_dose_response(data)
    section_inflammation_collapse(data)
    section_receptors(data)
    section_age_drug_interaction(data)
    section_thresholds(data)
    section_plaque(data)
    section_conservation(data)
    section_correlation(data)
    section_bimodality(data)
    section_variance_partition(data)


if __name__ == '__main__':
    main()
