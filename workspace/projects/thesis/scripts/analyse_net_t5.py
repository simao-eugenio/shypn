#!/usr/bin/env python3
"""NET-T5 analysis — Schnakenberg EPR decomposition + G5 deep analysis.
Run from ~/shypn/ with .venv activated:
  python3 workspace/projects/thesis/scripts/analyse_net_t5.py
"""
import csv, json, math, pathlib, re

RUN = pathlib.Path(
    "workspace/projects/thesis/experiments/results/run_20260707_152611"
)

# ── Schnakenberg stoichiometry (NTP/firing → ΔG/firing in kBT) ───────────────
# T = 310.15 K; ΔG_ATP = ΔG_GTP = 57 kJ/mol / (R*T) * kBT
# At 310.15 K: kBT = 4.28e-21 J; ΔG_NTP = 57000/(6.022e23) / kBT = 23.27 kBT
DG_NTP = 23.27   # kBT per NTP hydrolysed

STOICH = {
    # (ATP/firing, GTP/firing)
    "T_KinA_activation":         (5,  0),   # 5 ATP for kinase autophosphorylation
    "T_Spo0F_phosphorylation":   (0,  0),   # phosphotransfer (no NTP consumed)
    "T_Spo0F_dephos":            (0,  0),   # phosphatase (no NTP)
    "T_Spo0A_phosphorylation":   (0,  0),   # phosphotransfer
    "T_Spo0A_dephosphorylation": (0,  0),   # phosphatase
    "T_septation":               (32, 50),  # structural synthesis (ATP + GTP)
    "T_SinI_synthesis":          (0,  5),   # small protein, ~5 GTP translation
}

def dg_per_firing(t_name):
    atp, gtp = STOICH.get(t_name, (0, 0))
    return (atp + gtp) * DG_NTP

DURATION = 21600.0  # seconds

def mean(v): return sum(v)/len(v) if v else 0.0
def std(v):
    if len(v)<2: return 0.0
    m=mean(v); return math.sqrt(sum((x-m)**2 for x in v)/(len(v)-1))

def read_traj(path):
    with open(path) as fh:
        lines = [l for l in fh if not l.startswith("#")]
    return list(csv.DictReader(lines))

CONDS = {
    100:  "condition_[param]_INITIAL_NUTRIENTS_eq_100",
    1600: "condition_[param]_INITIAL_NUTRIENTS_eq_1600",
    2200: "condition_[param]_INITIAL_NUTRIENTS_eq_2200",
}

TRANSITIONS = list(STOICH.keys())
fire_cols = [t + "_firings" for t in TRANSITIONS]

print("NET-T5 ANALYSIS -- Schnakenberg EPR Decomposition")
print("Run:", RUN.name)
print("="*72)

all_results = {}
for n0, cname in sorted(CONDS.items()):
    cdir = RUN / cname
    rows = list(csv.DictReader(open(cdir/"replicates.csv")))
    traj_files = sorted((cdir/"replicates_trajectories").glob("run_*.csv"))
    n = len(rows)
    spore_mask = [float(r.get("Mature_spore_final",0))>0.5 for r in rows]
    n_s = sum(spore_mask)

    # ── Per-replicate firing rates ─────────────────────────────────────────
    fire_rates = {t: [] for t in TRANSITIONS}   # firings/s
    for r in rows:
        for t in TRANSITIONS:
            col = t + "_firings"
            val = float(r.get(col, 0))
            fire_rates[t].append(val / DURATION)

    # ── EPR per transition (kBT/s) ─────────────────────────────────────────
    epr = {}
    for t in TRANSITIONS:
        rate_mean = mean(fire_rates[t])
        epr[t] = rate_mean * dg_per_firing(t)

    total_epr = sum(epr.values())

    # ── Split by fate ──────────────────────────────────────────────────────
    epr_spor = {}; epr_veg = {}
    for t in TRANSITIONS:
        spor_rates = [fire_rates[t][i] for i,s in enumerate(spore_mask) if s]
        veg_rates  = [fire_rates[t][i] for i,s in enumerate(spore_mask) if not s]
        epr_spor[t] = mean(spor_rates) * dg_per_firing(t) if spor_rates else 0
        epr_veg[t]  = mean(veg_rates)  * dg_per_firing(t) if veg_rates  else 0

    total_spor = sum(epr_spor.values()); total_veg = sum(epr_veg.values())

    # ── G5 trajectory: σH peak timing and commitment moment for EPR burst ──
    burst_t = []   # time of septation firing burst
    for i, traj_f in enumerate(traj_files[:50]):  # sample first 50 for speed
        if not spore_mask[i]: continue
        traj = read_traj(traj_f)
        if not traj: continue
        times = [float(r["time"])/60 for r in traj]
        sept  = [float(r.get("Septum",0)) for r in traj]
        first = [t for t,s in zip(times,sept) if s>0.5]
        burst_t.append(first[0] if first else float("nan"))

    valid_bt = [t for t in burst_t if not math.isnan(t)]

    # ── Covariance: top firing-rate correlations ───────────────────────────
    cov_data = json.loads(open(cdir/"covariance.json").read())
    top_corr = []
    # Use firing count columns from statistics.json if available
    stats = json.loads(open(cdir/"statistics.json").read())

    all_results[n0] = {
        "n":n,"ns":n_s,"sf":n_s/n,
        "epr":epr,"total_epr":total_epr,
        "epr_spor":epr_spor,"total_spor":total_spor,
        "epr_veg":epr_veg,"total_veg":total_veg,
        "fire_rates":fire_rates,
        "burst_t_mean":mean(valid_bt),"burst_t_std":std(valid_bt),
    }

# ── Print EPR table ────────────────────────────────────────────────────────────
print()
for n0, r in sorted(all_results.items()):
    regime = {100:"Sub-critical (100% spor)", 1600:"Critical (~14% spor)",
               2200:"Super-critical (0% spor)"}[n0]
    print(f"\nN0={n0} µM — {regime}")
    print("  %-30s  %8s  %8s  %7s  %7s" % (
        "Transition","dG/firing","Rate/s","EPR(kBT/s)","% total"))
    print("  "+"-"*65)
    for t in TRANSITIONS:
        rate = mean(r["fire_rates"][t])
        dg   = dg_per_firing(t)
        ep   = r["epr"][t]
        pct  = 100*ep/r["total_epr"] if r["total_epr"]>0 else 0
        print("  %-30s  %8.1f  %8.3e  %10.1f  %6.1f%%" % (
            t.replace("T_",""), dg, rate, ep, pct))
    print("  "+"-"*65)
    print("  %-30s  %8s  %8s  %10.1f  100.0%%" % (
        "TOTAL", "", "", r["total_epr"]))
    if r["burst_t_mean"] > 0:
        print("  EPR burst (septation) at commit: t=%.0f±%.0f min" % (
            r["burst_t_mean"], r["burst_t_std"]))

# ── Decision vs Execution EPR split ───────────────────────────────────────────
print()
print("="*72)
print("DECISION vs EXECUTION EPR SPLIT")
print("Decision transitions: KinA_activation, Spo0F/Spo0A phosphorylation/dephos")
print("Execution transitions: septation, SinI_synthesis")
print()
DECISION = {"T_KinA_activation","T_Spo0F_phosphorylation","T_Spo0F_dephos",
            "T_Spo0A_phosphorylation","T_Spo0A_dephosphorylation"}
EXECUTION = {"T_septation","T_SinI_synthesis"}

for n0, r in sorted(all_results.items()):
    dec_epr = sum(r["epr"][t] for t in DECISION)
    exc_epr = sum(r["epr"][t] for t in EXECUTION)
    tot     = r["total_epr"]
    if tot > 0:
        print("N0=%5d: Decision=%6.1f kBT/s (%4.1f%%)  Execution=%8.1f kBT/s (%5.1f%%)" % (
            n0, dec_epr, 100*dec_epr/tot, exc_epr, 100*exc_epr/tot))

# ── Firing rate comparison: sporulating vs vegetative at N0=1600 ───────────────
print()
print("="*72)
print("FIRING RATES: sporulating vs vegetative replicates (N0=1600 critical condition)")
r = all_results[1600]
print("  %-30s  %10s  %10s  %8s" % ("Transition","Spor.rate/s","Veg.rate/s","Ratio"))
print("  "+"-"*65)
for t in TRANSITIONS:
    sp_rates = [r["fire_rates"][t][i] for i,s in enumerate(
        [float(row.get("Mature_spore_final",0))>0.5
         for row in csv.DictReader(open(RUN/"condition_[param]_INITIAL_NUTRIENTS_eq_1600"/"replicates.csv"))]) if s]
    vg_rates = [r["fire_rates"][t][i] for i,s in enumerate(
        [float(row.get("Mature_spore_final",0))>0.5
         for row in csv.DictReader(open(RUN/"condition_[param]_INITIAL_NUTRIENTS_eq_1600"/"replicates.csv"))]) if not s]
    sp = mean(sp_rates); vg = mean(vg_rates)
    ratio = sp/vg if vg > 1e-15 else float("inf")
    print("  %-30s  %10.4e  %10.4e  %8.1f" % (t.replace("T_",""), sp, vg, ratio))
