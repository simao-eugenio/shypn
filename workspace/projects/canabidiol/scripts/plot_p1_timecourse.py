"""Plot CBD, plaque, and inflammation over time at Sev=2, Age=75 across
LOADING_DOSE ∈ {0, 5, 10, 20}, for a chosen MAINT_DOSE.

Reads statistics.json (huge!) but extracts only 3 series per file.
Writes a PNG to <run_dir>/figures/cbd_plaque_inflammation_timecourse_MT<MT>.png.

Usage::

    python3 workspace/projects/canabidiol/scripts/plot_p1_timecourse.py \\
        workspace/projects/canabidiol/experiments/results/run_20260424_005438 [MT]

Default MT = 0.
"""
from __future__ import annotations

import glob
import json
import os
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Place-id mapping (from cbd_ad_neuroprotection_v3.shy / event_protocol_v3.md)
PLACE_ID = {
    'CBD_extracellular': 'P1',
    'Abeta_Plaque':      'P7',
    'NFkB_p65':          'P9',
}

LOADS = [0, 5, 10, 20]
COLORS = {0: '#888888', 5: '#3a86ff', 10: '#ff7f00', 20: '#d62728'}


def find_condition(run_dir, sev, ld, mt, age):
    pattern = (f'condition_*Disease_Severity_eq_{sev}*'
               f'LOADING_DOSE_eq_{ld}_*'
               f'MAINT_DOSE_eq_{mt}_*'
               f'Age_eq_{age}')
    matches = glob.glob(os.path.join(run_dir, pattern))
    if not matches:
        return None
    return matches[0]


def extract_series(stats_path):
    """Return (t, {species: (mean, std)}) loading only what we need."""
    with open(stats_path) as f:
        j = json.load(f)
    t = j['time_points']
    out = {}
    for name, pid in PLACE_ID.items():
        s = j['species_statistics'][pid]
        out[name] = (s['mean'], s['std'])
    return t, out


def downsample(arr, n=600):
    step = max(1, len(arr) // n)
    return arr[::step]


def main():
    if len(sys.argv) not in (2, 3):
        print(__doc__); sys.exit(2)
    run_dir = sys.argv[1]
    mt = int(sys.argv[2]) if len(sys.argv) == 3 else 0
    fig_dir = os.path.join(run_dir, 'figures')
    os.makedirs(fig_dir, exist_ok=True)

    series_by_load = {}
    for ld in LOADS:
        cond = find_condition(run_dir, 2, ld, mt, 75)
        if cond is None:
            print(f'WARN: no match for LD={ld}, MT={mt}'); continue
        sp = os.path.join(cond, 'statistics.json')
        print(f'Reading LD={ld} MT={mt} from {os.path.basename(cond)} …', flush=True)
        t, data = extract_series(sp)
        series_by_load[ld] = (t, data)

    fig, axes = plt.subplots(3, 1, figsize=(9, 9), sharex=True)
    titles = [
        ('CBD_extracellular', 'CBD$_{\\,extracellular}$  (µM)',  'CBD bolus + maintenance', 'linear', None),
        ('Abeta_Plaque',      'Aβ$_{\\,plaque}$  (units)',       'Plaque accumulation',     'symlog', 0.1),
        ('NFkB_p65',          'NF-κB p65  (units)',              'Inflammation',            'symlog', 0.1),
    ]
    for ax, (key, ylabel, subtitle, scale, linthresh) in zip(axes, titles):
        for ld in LOADS:
            if ld not in series_by_load: continue
            t, data = series_by_load[ld]
            mean, std = data[key]
            ts = downsample(t)
            ms = downsample(mean)
            ss = downsample(std)
            t_h = [x / 3600.0 for x in ts]
            color = COLORS[ld]
            ax.plot(t_h, ms, color=color, lw=1.6, label=f'LD = {ld} µM')
            ax.fill_between(t_h,
                            [m - s for m, s in zip(ms, ss)],
                            [m + s for m, s in zip(ms, ss)],
                            color=color, alpha=0.15, linewidth=0)
        ax.set_ylabel(ylabel)
        ax.set_title(subtitle, loc='left', fontsize=10, color='#333')
        ax.grid(alpha=0.25, linestyle=':', which='both')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        if scale == 'symlog':
            ax.set_yscale('symlog', linthresh=linthresh)
            ax.axhline(linthresh, color='k', lw=0.4, ls='--', alpha=0.3)

    axes[0].legend(loc='upper right', frameon=False, ncol=4)
    axes[2].set_xlabel('time (h)')
    fig.suptitle('CBD pharmacokinetics, plaque burden and inflammation\n'
                 f'Disease_Severity = 2, Age = 75, MAINT_DOSE = {mt}   '
                 '(mean ± SD across 30 replicates)',
                 fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, 0.95))

    out = os.path.join(fig_dir, f'cbd_plaque_inflammation_timecourse_MT{mt}.png')
    fig.savefig(out, dpi=150, bbox_inches='tight')
    print(f'Wrote {out}')


if __name__ == '__main__':
    main()
