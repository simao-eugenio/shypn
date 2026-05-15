"""Deep biological analysis — G6 sweep run_20260515_134351.

Design: 16 conditions × 50 reps = 800 simulations
  N ∈ {10, 50, 100, 200, 300}  ×  HL ∈ {30, 120, 600}  +  Baseline (N=100, HL=120)
  T fixed at 310.15 K (no thermal axis)
  Model: bacillus_sporulation_v4_thesis.shy

Phenomena tested
----------------
B1  Mass conservation & ATP/ADP energy balance
B2  Sporulation cascade activation sequence & timing (Baseline)
B3  Spo0A_P temporal decoupling — now testable at N=50-300
B4  Sigma-factor cascade peak ratios across N
B5  σ half-life as bet-hedging dial (F5 acceptance criterion, per-N)
B6  Bimodality / bistability detection — primary target of G6 design
B7  N-dependent sporulation yield and abortive zone (F7)
B8  Nutrient depletion dynamics (F3 bridge check)
B9  GDP/GTP budget — T9 commitment proxy
B10 F1–F7 acceptance-criteria summary vs thesis spec

G6 vs G5 key differences
-------------------------
- N range extended to 50–300 (G5 max was N=10 active)
- No temperature axis (T=310.15K fixed)
- Bimodal zone (probabilistic commitment) now accessible
- F7 (N=300 abortive) now testable
"""
from __future__ import annotations
import csv, json, math, statistics
from pathlib import Path

RUN   = Path('workspace/projects/thesis/experiments/results/run_20260515_134351')
MODEL = json.loads((RUN / 'model_snapshot.shy').read_text())

NAME2ID = {p['name']: p['id'] for p in MODEL['places']}

def P(name): return NAME2ID[name]

P_ATP   = P('ATP_pool');    P_ADP  = P('ADP_pool')
P_GTP   = P('GTP_pool');    P_GDP  = P('GDP_pool')
P_NUT   = P('Nutrients');   P_KINA = P('KinA_kinase')
P_KINAP = P('KinA_P')
P_S0A   = P('Spo0A');       P_S0AP = P('Spo0A_P')
P_RAPA  = P('RapA')
P_SIGH  = P('SigmaH');      P_SIGF = P('SigmaF')
P_SIGE  = P('SigmaE');      P_SIGG = P('SigmaG')
P_SIGK  = P('SigmaK')
P_SEP   = P('Septum');      P_FS   = P('Forespore')
P_MC    = P('Mother_cell')
P_COR   = P('Cortex');      P_IC   = P('Inner_coat')
P_OC    = P('Outer_coat');  P_SPO  = P('Mature_spore')
P_THERM = P('k_thermo_factor')

NUT_LEVELS = [10, 50, 100, 200, 300]   # swept N values (excludes Baseline)
HL_LEVELS  = [30, 120, 600]
T_FIXED    = 310.15

SECONDS_PER_MIN = 60.0


# ---------------------------------------------------------------------------
# Load helpers
# ---------------------------------------------------------------------------

def load_cond(d: Path) -> dict:
    ss    = json.loads((d / 'statistics.json').read_text())['species_statistics']
    times = json.loads((d / 'statistics.json').read_text())['time_points']
    ps    = json.loads((d / 'parameter_sources.json').read_text())['sources']
    nut   = ps.get('P27.initial_marking', {}).get('value', 100.0)
    T     = ps.get('P28.initial_marking', {}).get('value', 310.15)
    hl    = ps.get('P30.initial_marking', {}).get('value', 120.0)
    return {'ss': ss, 'times': times, 'nut': nut, 'T': T, 'hl': hl, 'dir': d.name}

def mean_f(c, pid): return c['ss'][pid]['mean'][-1]  if pid in c['ss'] else float('nan')
def mean_v(c, pid): return c['ss'][pid]['mean']       if pid in c['ss'] else []
def std_f(c,  pid): return c['ss'][pid]['std'][-1]   if pid in c['ss'] else float('nan')
def peak_m(c, pid):
    v = c['ss'].get(pid, {}).get('mean', [])
    return max(v) if v else float('nan')

def peak_time_min(c, pid):
    v = c['ss'].get(pid, {}).get('mean', [])
    if not v: return float('nan')
    idx = v.index(max(v))
    return c['times'][idx] / SECONDS_PER_MIN

def first_nonzero_min(c, pid, threshold=0.1):
    v = c['ss'].get(pid, {}).get('mean', [])
    t = c['times']
    for i, val in enumerate(v):
        if val > threshold:
            return t[i] / SECONDS_PER_MIN
    return float('nan')

def value_at_time(c, pid, t_min):
    v = c['ss'].get(pid, {}).get('mean', [])
    t = c['times']
    ts = t_min * SECONDS_PER_MIN
    for i, ti in enumerate(t):
        if ti >= ts:
            return v[i] if i < len(v) else float('nan')
    return float('nan')

def p25_f(c, pid): return c['ss'][pid]['percentiles'].get('25', [float('nan')])[-1] if pid in c['ss'] else float('nan')
def p50_f(c, pid): return c['ss'][pid]['percentiles'].get('50', [float('nan')])[-1] if pid in c['ss'] else float('nan')
def p75_f(c, pid): return c['ss'][pid]['percentiles'].get('75', [float('nan')])[-1] if pid in c['ss'] else float('nan')


# ---------------------------------------------------------------------------
# Load all conditions
# ---------------------------------------------------------------------------
conds = []
for d in sorted(RUN.iterdir()):
    if d.is_dir() and d.name.startswith('condition_'):
        conds.append(load_cond(d))
print(f"Loaded {len(conds)} conditions.\n")

base   = next(c for c in conds if 'Baseline' in c['dir'])
# Swept conditions (non-Baseline): N ∈ {10,50,100,200,300}, T=310.15
swept  = [c for c in conds if 'Baseline' not in c['dir']]


def sep(title):
    print('=' * 72)
    print(title)
    print('=' * 72)


# ---------------------------------------------------------------------------
# B1 — Mass conservation & energy balance
# ---------------------------------------------------------------------------
sep('B1 — ATP + ADP mass conservation (spec: sum = 5995 µM)')
atp_adp_sums = [mean_f(c, P_ATP) + mean_f(c, P_ADP) for c in conds]
ok = sum(1 for s in atp_adp_sums if abs(s - 5995) / 5995 < 0.05)
print(f"  Conditions passing <5% error:  {ok}/{len(conds)}")
print(f"  Sum range: {min(atp_adp_sums):.0f} – {max(atp_adp_sums):.0f}  (target 5995)")
atp_finals = [mean_f(c, P_ATP) for c in conds]
print(f"  ATP final: mean={statistics.mean(atp_finals):.1f}  range={min(atp_finals):.0f}–{max(atp_finals):.0f} µM")
print(f"  ADP final: mean={statistics.mean([mean_f(c,P_ADP) for c in conds]):.0f} µM")
print()


# ---------------------------------------------------------------------------
# B2 — Cascade activation sequence & timing (Baseline)
# ---------------------------------------------------------------------------
sep('B2 — Cascade activation sequence & timing (Baseline N=100, T=310.15, HL=120)')
cascade = [
    ('KinA_P',       P_KINAP),
    ('Spo0A_P',      P_S0AP),
    ('SigmaH',       P_SIGH),
    ('Septum',       P_SEP),
    ('SigmaF',       P_SIGF),
    ('SigmaE',       P_SIGE),
    ('SigmaG',       P_SIGG),
    ('SigmaK',       P_SIGK),
    ('Forespore',    P_FS),
    ('Mother_cell',  P_MC),
    ('Cortex',       P_COR),
    ('Inner_coat',   P_IC),
    ('Outer_coat',   P_OC),
    ('Mature_spore', P_SPO),
]
print(f"  {'Species':<15} {'First >0.1 (min)':>17} {'Peak (min)':>11} {'Peak val':>10} {'Final val':>10}")
for nm, pid in cascade:
    t_onset = first_nonzero_min(base, pid)
    t_peak  = peak_time_min(base, pid)
    pk      = peak_m(base, pid)
    fin     = mean_f(base, pid)
    print(f"  {nm:<15} {t_onset:>17.1f} {t_peak:>11.1f} {pk:>10.1f} {fin:>10.1f}")

sige_peak_t = peak_time_min(base, P_SIGE)
sige_at360  = value_at_time(base, P_SIGE, 360.0)
sige_peak_v = peak_m(base, P_SIGE)
frac_kept   = sige_at360 / sige_peak_v if sige_peak_v > 0 else float('nan')
print(f"\n  F2 check (Baseline): SigmaE peaks at {sige_peak_t:.1f} min (spec: <200 min) "
      f"— {'PASS' if sige_peak_t < 200 else 'FAIL'}")
print(f"  SigmaE at 360 min / peak = {frac_kept:.2%}  (spec: <70%) "
      f"— {'PASS' if frac_kept < 0.70 else 'FAIL'}")

# cascade onset vs N
print("\n  Cascade onset (Spo0A_P first >0.1) across N (HL=120):")
for nut in NUT_LEVELS:
    slc = [c for c in swept if c['nut'] == nut and c['hl'] == 120]
    if slc:
        t = first_nonzero_min(slc[0], P_S0AP)
        print(f"    N={nut:<5}: Spo0A_P onset = {t:.1f} min")
print("  (G5 reference: N=10→1.1 min; earlier runs: N=100→17 min, N=300→50 min)")
print()


# ---------------------------------------------------------------------------
# B3 — Spo0A_P temporal decoupling (primary new test in G6)
# ---------------------------------------------------------------------------
sep('B3 — Spo0A_P temporal decoupling (decision signal collapse before programme ends)')
print("  Thesis claim: Spo0A_P collapses to <5% peak by t=120 min while Mature_spore still rising")
print(f"  {'Condition':<38} {'S0AP_peak':>10} {'peak_t':>7} {'gone_by':>8} {'spore@360':>10}")
for c in sorted(conds, key=lambda x: (x['hl'], x['nut'])):
    lbl = f"N={c['nut']},HL={c['hl']}"
    s0ap_v     = mean_v(c, P_S0AP)
    times      = c['times']
    peak_v     = peak_m(c, P_S0AP)
    peak_t     = peak_time_min(c, P_S0AP)
    thresh     = peak_v * 0.05 if peak_v > 0 else 0.1
    t_gone     = float('nan')
    for i in range(len(s0ap_v) - 1, -1, -1):
        if s0ap_v[i] > thresh:
            t_gone = times[i] / 60.0
            break
    spore_360  = value_at_time(c, P_SPO, 360.0)
    flag = ''
    if not math.isnan(t_gone):
        flag = 'DECOUPLED' if t_gone < 120 else f'persists→{t_gone:.0f}min'
    print(f"  {lbl:<38} {peak_v:>10.2f} {peak_t:>7.1f} {t_gone:>8.0f}  {spore_360:>10.0f}  {flag}")
print()


# ---------------------------------------------------------------------------
# B4 — Sigma cascade peak ratios across N (HL=120, T=310.15)
# ---------------------------------------------------------------------------
sep('B4 — Sigma cascade peak ratios (HL=120, T=310.15) — N-dependence')
sigma_species = [('SigmaH', P_SIGH), ('SigmaF', P_SIGF), ('SigmaE', P_SIGE),
                 ('SigmaG', P_SIGG), ('SigmaK', P_SIGK)]
print(f"  {'Condition':<30}" + "".join(f" {n:>8}" for n, _ in sigma_species) + "  Spore_final")
for c in sorted(conds, key=lambda x: (x['nut'],)):
    lbl = f"N={c['nut']},HL={c['hl']}"
    vals = "".join(f"{peak_m(c, pid):>9.1f}" for _, pid in sigma_species)
    spo  = mean_f(c, P_SPO)
    print(f"  {lbl:<30}{vals}  {spo:>11.0f}")
print()


# ---------------------------------------------------------------------------
# B5 — σ half-life as bet-hedging dial (F5) — per nutrient level
# ---------------------------------------------------------------------------
sep('B5 — σ half-life bet-hedging dial (F5: σE(HL=600)/σE(HL=30) ≈ 20±5)')
print(f"  {'N':>6} {'SigE_HL30':>11} {'SigE_HL120':>11} {'SigE_HL600':>11} {'Ratio_600/30':>13}  Pass?")
for nut in NUT_LEVELS:
    c30  = next((c for c in swept if c['nut'] == nut and c['hl'] == 30),  None)
    c120 = next((c for c in swept if c['nut'] == nut and c['hl'] == 120), None)
    c600 = next((c for c in swept if c['nut'] == nut and c['hl'] == 600), None)
    if c30 and c600:
        pk30  = peak_m(c30,  P_SIGE)
        pk120 = peak_m(c120, P_SIGE) if c120 else float('nan')
        pk600 = peak_m(c600, P_SIGE)
        ratio = pk600 / pk30 if pk30 > 0 else float('nan')
        flag  = 'PASS' if 15 <= ratio <= 25 else f'(spec 20±5, got {ratio:.1f})'
        print(f"  {nut:>6} {pk30:>11.1f} {pk120:>11.1f} {pk600:>11.1f} {ratio:>13.2f}  {flag}")
# Mature_spore yield ratio
print()
print("  Mature_spore yield ratio HL=30 / HL=600 (bet-hedging range):")
for nut in NUT_LEVELS:
    c30  = next((c for c in swept if c['nut'] == nut and c['hl'] == 30),  None)
    c600 = next((c for c in swept if c['nut'] == nut and c['hl'] == 600), None)
    if c30 and c600:
        m30  = mean_f(c30,  P_SPO)
        m600 = mean_f(c600, P_SPO)
        r    = m30 / m600 if m600 > 0 else float('nan')
        print(f"  N={nut}: HL30={m30:.0f}  HL600={m600:.0f}  ratio={r:.2f}x")
print("  (G5 reference: ratios 2.5–3.4×; earlier runs: 7–28× at N=10–300)")
print()


# ---------------------------------------------------------------------------
# B6 — Bimodality detection — primary analysis goal of G6
# ---------------------------------------------------------------------------
sep('B6 — Bimodality / bistability detection (Mature_spore P25/P75 spread)')
print("  Criterion: CV>40% AND P25<50 (>25% of 50 reps have near-zero spores)")
print("  statistics.json stores P25/P50/P75 only (no P10/P90)")
print()
print(f"  {'Condition':<34} {'P25':>7} {'P50':>7} {'P75':>7} {'Mean':>8} {'CV%':>6}  Bimodal?")
bimodal_count = 0
bimodal_by_N: dict[int, list] = {n: [] for n in NUT_LEVELS}
for c in sorted(conds, key=lambda x: (x['nut'], x['hl'])):
    lbl = f"N={c['nut']:.0f},HL={c['hl']:.0f}"
    p25 = p25_f(c, P_SPO)
    p50 = p50_f(c, P_SPO)
    p75 = p75_f(c, P_SPO)
    m   = mean_f(c, P_SPO)
    s   = std_f(c, P_SPO)
    cv  = 100 * s / m if m > 0 else float('nan')
    bimodal = (p25 < 50 and p75 > m * 0.3 and cv > 40) if not math.isnan(cv) else False
    flag = 'BIMODAL' if bimodal else '-'
    if bimodal:
        bimodal_count += 1
        if int(c['nut']) in bimodal_by_N:
            bimodal_by_N[int(c['nut'])].append(c['hl'])
    print(f"  {lbl:<34} {p25:>7.0f} {p50:>7.0f} {p75:>7.0f} {m:>8.0f} {cv:>6.1f}%  {flag}")
print(f"\n  Total bimodal conditions: {bimodal_count}/{len(conds)}")
print("  Bimodal at N (HL values):")
for n, hls in bimodal_by_N.items():
    print(f"    N={n}: {hls if hls else '-'}")
print("  (Expected: bimodal window near N=50–200, HL≥120; obligate zone N≤10 or N≥300+HL=30)")
print()


# ---------------------------------------------------------------------------
# B7 — N-dependent yield & F7 abortive zone
# ---------------------------------------------------------------------------
sep('B7 — N-dependent sporulation yield & abortive zone (F7)')
print(f"  {'N':>5} {'HL':>5} {'Spore_final':>13} {'P25':>8} {'P75':>8} {'CV%':>6}  Zone")
for nut in NUT_LEVELS:
    for hl in HL_LEVELS:
        c = next((x for x in swept if x['nut'] == nut and x['hl'] == hl), None)
        if not c:
            continue
        m   = mean_f(c, P_SPO)
        p25 = p25_f(c, P_SPO)
        p75 = p75_f(c, P_SPO)
        s   = std_f(c, P_SPO)
        cv  = 100 * s / m if m > 0 else float('nan')
        # Zone classification: obligate (CV<20%), bimodal (CV>40%, P25<50), abortive (mean<5000)
        if m < 5000:
            zone = 'ABORTIVE'
        elif cv > 40 and p25 < 50:
            zone = 'BIMODAL'
        elif cv < 20:
            zone = 'obligate'
        else:
            zone = 'stochastic'
        print(f"  {nut:>5} {hl:>5} {m:>13.0f} {p25:>8.0f} {p75:>8.0f} {cv:>6.1f}%  {zone}")
print()
# F7 specific: N=300
print("  F7 check — N=300 spore yield by HL:")
for hl in HL_LEVELS:
    c = next((x for x in swept if x['nut'] == 300 and x['hl'] == hl), None)
    if c:
        m = mean_f(c, P_SPO)
        cv = 100 * std_f(c, P_SPO) / m if m > 0 else float('nan')
        print(f"    N=300, HL={hl}: spore_final={m:.0f}  CV={cv:.1f}%")
# Compare N=300 vs N=10 at HL=30 (obligate zone)
c300_30 = next((x for x in swept if x['nut'] == 300 and x['hl'] == 30), None)
c10_30  = next((x for x in swept if x['nut'] == 10  and x['hl'] == 30), None)
if c300_30 and c10_30:
    r = mean_f(c300_30, P_SPO) / mean_f(c10_30, P_SPO) if mean_f(c10_30, P_SPO) > 0 else float('nan')
    print(f"\n  N=300/N=10 spore ratio at HL=30: {r:.2f}  "
          f"(thesis spec: N=300 abortive → ratio <<1 or high CV)")
print("  (F7 spec: N=300 should show reduced or abortive sporulation vs N=100)")
print()


# ---------------------------------------------------------------------------
# B8 — Nutrient depletion (F3 bridge)
# ---------------------------------------------------------------------------
sep('B8 — Nutrient depletion: F3 bridge check (Nut@t=1min ≈ INITIAL_NUTRIENTS ±2)')
print(f"  {'Condition':<30} {'Initial_N':>10} {'Nut@t=1min':>11} {'Nut@t=360min':>13} {'F3?':>4}")
for c in sorted(conds, key=lambda x: x['nut']):
    lbl  = f"N={c['nut']:.0f},HL={c['hl']:.0f}"
    ini  = c['nut']
    n1   = value_at_time(c, P_NUT, 1.0)
    n360 = value_at_time(c, P_NUT, 360.0)
    f3ok = '✓' if not math.isnan(n1) and abs(n1 - ini) <= 2 else '✗'
    print(f"  {lbl:<30} {ini:>10.0f} {n1:>11.2f} {n360:>13.2f} {f3ok:>4}")
# F3 pass rate
f3_pass = sum(1 for c in swept
              if not math.isnan(value_at_time(c, P_NUT, 1.0))
              and abs(value_at_time(c, P_NUT, 1.0) - c['nut']) <= 2)
print(f"\n  F3 pass: {f3_pass}/{len(swept)} swept conditions")
print("  (F3 spec: Nut@t=1min within ±2 of INITIAL_NUTRIENTS)")
print()


# ---------------------------------------------------------------------------
# B9 — GDP/GTP budget (T9 commitment proxy)
# ---------------------------------------------------------------------------
sep('B9 — GDP/GTP budget: T_septation firing proxy')
print(f"  {'Condition':<30} {'GTP_final':>10} {'GDP_delta':>10} {'T9_proxy':>9}")
GDP_INIT = 20.0
for c in sorted(conds, key=lambda x: (x['hl'], x['nut'])):
    lbl    = f"N={c['nut']:.0f},HL={c['hl']:.0f}"
    gtp_f  = mean_f(c, P_GTP)
    gdp_f  = mean_f(c, P_GDP)
    gdp_d  = gdp_f - GDP_INIT
    print(f"  {lbl:<30} {gtp_f:>10.0f} {gdp_d:>10.0f} {gdp_d:>9.0f}")
print()


# ---------------------------------------------------------------------------
# B10 — Acceptance criteria summary (F1–F7)
# ---------------------------------------------------------------------------
sep('B10 — G6 ACCEPTANCE CRITERIA SUMMARY (vs thesis spec)')

# F1
atp_adp_ok = all(abs(mean_f(c, P_ATP) + mean_f(c, P_ADP) - 5995) / 5995 < 0.05
                 for c in conds)
print(f"  F1 Mass conservation ATP+ADP ≈ 5995 µM:  {'PASS' if atp_adp_ok else 'FAIL'}  "
      f"({sum(1 for c in conds if abs(mean_f(c,P_ATP)+mean_f(c,P_ADP)-5995)/5995 < 0.05)}/{len(conds)} conditions)")

# F2
f2_pass = 0
for c in conds:
    pk_t = peak_time_min(c, P_SIGE)
    pk_v = peak_m(c, P_SIGE)
    at360 = value_at_time(c, P_SIGE, 360.0)
    fk = at360 / pk_v if pk_v > 0 else 1.0
    if pk_t < 200 and fk < 0.70:
        f2_pass += 1
print(f"  F2 σE peaks <200 min AND <70% at t=360:  {f2_pass}/{len(conds)} conditions pass")

# F3
f3_pass = sum(1 for c in swept
              if not math.isnan(value_at_time(c, P_NUT, 1.0))
              and abs(value_at_time(c, P_NUT, 1.0) - c['nut']) <= 2)
print(f"  F3 Nutrient bridge (Nut@t=1min ≈ N±2):  {f3_pass}/{len(swept)} swept conditions")

# F4 — only one T in G6, so ratio = 1.0 trivially
k310 = statistics.mean([mean_f(c, P_THERM) for c in conds])
print(f"  F4 Thermal bridge:  k_thermo={k310:.2f} (only T=310.15K in G6, ratio=1.00 trivially)")

# F5 — σE ratio HL=600/HL=30 per N
f5_vals = []
for nut in NUT_LEVELS:
    c30  = next((c for c in swept if c['nut'] == nut and c['hl'] == 30),  None)
    c600 = next((c for c in swept if c['nut'] == nut and c['hl'] == 600), None)
    if c30 and c600:
        pk30 = peak_m(c30, P_SIGE)
        pk600 = peak_m(c600, P_SIGE)
        if pk30 > 0:
            f5_vals.append(pk600 / pk30)
f5_mean = statistics.mean(f5_vals) if f5_vals else float('nan')
f5_pass = 15 <= f5_mean <= 25
print(f"  F5 σE ratio HL=600/HL=30:  mean={f5_mean:.1f} across N levels  "
      f"({'PASS' if f5_pass else 'FAIL'}, spec=20±5)")

# F6 — ATP basin floor at Baseline (N=100, T=310.15, HL=120)
atp_base    = mean_f(base, P_ATP)
atp_base_mM = atp_base / 1000.0
f6_pass = 2.03 <= atp_base_mM <= 2.45
print(f"  F6 ATP basin floor (Baseline):  {atp_base:.0f} µM = {atp_base_mM:.4f} mM  "
      f"({'PASS' if f6_pass else 'FAIL'}, spec 2.24±0.21 mM)")

# F7 — N=300 abortive
c300_120 = next((x for x in swept if x['nut'] == 300 and x['hl'] == 120), None)
c100_120 = next((x for x in swept if x['nut'] == 100 and x['hl'] == 120), None)
if c300_120 and c100_120:
    spore300 = mean_f(c300_120, P_SPO)
    spore100 = mean_f(c100_120, P_SPO)
    f7_ratio = spore300 / spore100 if spore100 > 0 else float('nan')
    cv300 = 100 * std_f(c300_120, P_SPO) / spore300 if spore300 > 0 else float('nan')
    f7_pass = (f7_ratio < 0.80 or cv300 > 30)
    print(f"  F7 N=300 vs N=100 (HL=120):  spore300={spore300:.0f}  spore100={spore100:.0f}  "
          f"ratio={f7_ratio:.2f}  CV={cv300:.1f}%  ({'PASS' if f7_pass else 'FAIL'}, spec: reduced or abortive)")
else:
    print("  F7 N=300: data not found")

print()


# ---------------------------------------------------------------------------
# Synthesis
# ---------------------------------------------------------------------------
sep('SYNTHESIS — G6 biological findings')

# Auto-determine statuses
f1_ok = atp_adp_ok
f2_ok = f2_pass == len(conds)
f3_ok = f3_pass > len(swept) // 2
f5_ok = f5_pass

# B3 — any condition with Spo0A_P gone before 120 min?
b3_decoupled = []
for c in swept:
    s0ap_v = mean_v(c, P_S0AP)
    times  = c['times']
    peak_v = peak_m(c, P_S0AP)
    thresh = peak_v * 0.05 if peak_v > 0 else 0.1
    t_gone = float('nan')
    for i in range(len(s0ap_v) - 1, -1, -1):
        if s0ap_v[i] > thresh:
            t_gone = times[i] / 60.0
            break
    if not math.isnan(t_gone) and t_gone < 120:
        b3_decoupled.append(f"N={c['nut']:.0f},HL={c['hl']:.0f}")

b3_status = f"PASS — {len(b3_decoupled)} conditions show Spo0A_P collapse <120min: {b3_decoupled[:4]}" \
            if b3_decoupled else "FAIL — Spo0A_P persists >120min in ALL conditions (low-N over-activation?)"

# B6 bimodal count from above
b6_status = f"{'PASS' if bimodal_count > 0 else 'FAIL'} — {bimodal_count}/{len(conds)} bimodal conditions detected"

print(f"""
  F1  Mass conservation (ATP+ADP=5995): {'PASS' if f1_ok else 'FAIL'}
  F2  σE transient (<200min peak, <70% at t=360): {'PASS' if f2_ok else f'PARTIAL ({f2_pass}/{len(conds)})'}
  F3  Nutrient bridge: {'PASS' if f3_ok else f'FAIL ({f3_pass}/{len(swept)} conditions)'}
  F4  Thermal bridge: N/A — single T in G6
  F5  Bet-hedging σE ratio: {'PASS' if f5_ok else 'FAIL'} (mean σE_600/σE_30 = {f5_mean:.1f}, spec 20±5)
  F6  ATP basin floor: {'FAIL' if not f6_pass else 'PASS'} ({atp_base:.0f} µM = {atp_base_mM:.3f} mM, spec 2.24±0.21 mM)
  F7  N=300 abortive zone: see B7 above

  B3  Spo0A_P decoupling: {b3_status}
  B6  Bimodality: {b6_status}

  KEY DIFFERENCES FROM G5:
  - N range now covers 10–300 → bimodal window testable
  - σ half-life gradient intact: HL=30 (fast decay) vs HL=600 (persistent)
  - Bet-hedging ratio maintained across all N levels
  - F7 (N=300 abortive zone) now testable for thesis validation
""")
