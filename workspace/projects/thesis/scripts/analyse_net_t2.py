#!/usr/bin/env python3
"""NET-T2 analysis — Non-equilibrium landscape (INITIAL_NUTRIENTS sweep).
Run from ~/shypn/ with .venv activated:
  python3 workspace/projects/thesis/scripts/analyse_net_t2.py
"""
import csv, math, pathlib, re

RUN = pathlib.Path(
    "workspace/projects/thesis/experiments/results/run_20260704_201120"
)


def mean(v): return sum(v)/len(v) if v else float("nan")
def var(v):
    m = mean(v)
    return sum((x - m)**2 for x in v) / len(v) if len(v) > 1 else 0.0
def std(v): return math.sqrt(var(v))
def cv(v): m = mean(v); return std(v)/m if m else float("nan")
def skew(v):
    m = mean(v); s = std(v)
    if s < 1e-15: return 0.0
    return sum(((x - m)/s)**3 for x in v) / len(v)
def kurt(v):
    m = mean(v); s = std(v)
    if s < 1e-15: return 0.0
    return sum(((x - m)/s)**4 for x in v) / len(v)
def sarle_bc(v):
    """Sarle bimodality coefficient. Bimodal if > 0.555."""
    n = len(v)
    if n < 4: return float("nan")
    g1 = skew(v); g2 = kurt(v)
    return (g1**2 + 1) / (g2 + 3*(n-1)**2/((n-2)*(n-3)))


results = {}
for cdir in sorted(RUN.glob("condition_*")):
    m = re.search(r"INITIAL_NUTRIENTS_eq_(\d+)", cdir.name)
    n0 = int(m.group(1)) if m else 100
    rows = list(csv.DictReader(open(cdir / "replicates.csv")))
    n = len(rows)
    spore  = [float(r.get("Mature_spore_final", 0)) > 0.5 for r in rows]
    atp_f  = [float(r.get("ATP_pool_final", 0)) / 1000 for r in rows]  # mM
    spoa_f = [float(r.get("Spo0A_P_final", 0)) for r in rows]
    sigh_f = [float(r.get("SigmaH_final", 0)) for r in rows]
    sinr_f = [float(r.get("SinR_final", 0)) for r in rows]
    n_s    = sum(spore)
    sf     = n_s / n

    # Split ATP into sporulating vs vegetative
    atp_spor = [atp_f[i] for i, s in enumerate(spore) if s]
    atp_veg  = [atp_f[i] for i, s in enumerate(spore) if not s]

    BC = sarle_bc(atp_f)
    results[n0] = {
        "sf": sf, "n": n, "ns": n_s,
        "atp_m": mean(atp_f), "atp_s": std(atp_f), "cv": cv(atp_f),
        "bc": BC,
        "atp_spor": mean(atp_spor), "atp_veg": mean(atp_veg),
        "spoa": mean(spoa_f), "sigh": mean(sigh_f), "sinr": mean(sinr_f),
    }

# ── summary table ────────────────────────────────────────────────────────────
HDR = ("N0(µM)", "Spore%", "BC", "ATP_mean", "ATP_CV", "SigH", "SinR", "Bimodal?")
print("%-8s  %-7s  %-6s  %-9s  %-7s  %-7s  %-7s  %s" % HDR)
print("-" * 80)
for n0 in sorted(results):
    r = results[n0]
    bm = "*** YES" if r["bc"] > 0.555 else "---"
    print("%-8d  %-7s  %-6.3f  %-9.3f  %-7.3f  %-7.3f  %-7.3f  %s" % (
        n0,
        "%.0f%%" % (100*r["sf"]),
        r["bc"],
        r["atp_m"],
        r["cv"],
        r["sigh"],
        r["sinr"],
        bm,
    ))

print()
# ATP basin analysis
print("=== ATP BASINS (sporulating vs vegetative) ===")
print("%-8s  %-12s  %-12s  %-8s" % ("N0", "ATP_spor(mM)", "ATP_veg(mM)", "Spore%"))
for n0 in sorted(results):
    r = results[n0]
    print("%-8d  %-12s  %-12s  %.0f%%" % (
        n0,
        "%.3f" % r["atp_spor"] if not math.isnan(r["atp_spor"]) else "---",
        "%.3f" % r["atp_veg"] if not math.isnan(r["atp_veg"]) else "---",
        100*r["sf"],
    ))

bimodal = [(n0, r) for n0, r in results.items() if r["bc"] > 0.555]
print()
print("Bimodal (BC>0.555):", sorted(n0 for n0, _ in bimodal))
if bimodal:
    peak = max(bimodal, key=lambda x: x[1]["bc"])
    print("Peak BC: N0=%d µM  BC=%.3f  Spore%%=%.0f%%" % (
        peak[0], peak[1]["bc"], 100*peak[1]["sf"]))
