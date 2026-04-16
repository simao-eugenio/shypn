"""
Thermodynamic Baseline Analysis — run_20260301_182620

Mines the existing 4-condition × 50-replicate × ~3700-timepoint dataset
(EPO = 0.430, 0.440, 0.449, 0.455 µM, 0.01× ICs, T=310.15 K, pH_nuc=7.5 nominal)
to answer:

  1. Bottleneck identification — which transition fires slowest → which Ea
     dominates temperature sensitivity?
  2. pH-Hill repression variation — how much does the Hill factor actually
     vary per replicate during stochastic oscillations?
  3. Energy status — does ATP/ADP ratio fluctuate enough to affect translation?
  4. Commitment timing — when does GATA1/PU1 ratio first cross 1.5?
     And when does GATA1_transcription first exceed PU1_transcription (flux signal)?
  5. Rate-asymmetry cascade — how does T11/T12 flux ratio evolve over time?
  6. pGATA1 activation curve — when does the T34 amplifier engage?

Output:
  workspace/projects/gata/experiments/results/run_20260301_182620/
      thermo_baseline_analysis/
          bottleneck_fluxes.csv
          fate_summary.csv
          commitment_times.csv
          per_replicate_stats.csv
          plots/ (if matplotlib available)

Usage:
    python dev/analyze_thermo_baseline.py
"""

import os
import sys
import math
import pandas as pd
import numpy as np
from pathlib import Path

# ─────────────────────────────────────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────────────────────────────────────

RUN_DIR = Path("workspace/projects/gata/experiments/results/run_20260301_182620")
OUT_DIR = RUN_DIR / "thermo_baseline_analysis"
OUT_DIR.mkdir(exist_ok=True)

EPO_CONDITIONS = [0.430, 0.440, 0.449, 0.455]

# Fate thresholds (GATA1_nuc / PU1_nuc ratio)
ERY_THRESHOLD = 1.5
MYE_THRESHOLD = 0.8

# Nominal thermodynamic parameters
T_REF = 310.15   # K
PH_NUC_REF = 7.5
K_INH_NOM = 8.0 * (10 ** (0.5 * (PH_NUC_REF - 7.5)))  # = 8.0 µM

# Arrhenius Ea/R values (K) embedded in rate functions
EA_R = {
    "GATA1_transcription":        7215.0,   # T11
    "PU1_transcription":          7215.0,   # T12
    "GATA1_mRNA_export":          7215.0,   # T13
    "PU1_mRNA_export":            7215.0,   # T14
    "GATA1_translation":          4810.0,   # T15
    "PU1_translation":            4810.0,   # T16
    "GATA1_nuclear_import":       6012.0,   # T17
    "PU1_nuclear_import":         6012.0,   # T18
    "GATA1_mRNA_nuc_degradation": 6012.0,   # T19
    "GATA1_mRNA_cyto_degradation":6012.0,   # T20
    "PU1_mRNA_nuc_degradation":   6012.0,   # T21
    "PU1_mRNA_cyto_degradation":  6012.0,   # T22
    "GATA1_Protein_cyto_degradation": 6012.0,  # T23
    "GATA1_Protein_nuc_degradation":  6012.0,  # T24
    "PU1_Protein_cyto_degradation":   6012.0,  # T25
    "PU1_Protein_nuc_degradation":    6012.0,  # T26
    "ATP_synthesis":              3608.0,   # T27
    "GTP_regeneration":           3608.0,   # T28
    "pGATA1_nuc_degradation":     6012.0,   # T33
}

# Delta T magnitudes to evaluate (for sensitivity table)
DELTA_T = [308.15, 310.15, 312.15]


def load_experiment(exp_dir: Path):
    """Load replicates.csv and all trajectory files for one experiment."""
    rep = pd.read_csv(exp_dir / "replicates.csv", comment="#")
    traj_dir = exp_dir / "replicates_trajectories"
    trajs = {}
    for f in sorted(traj_dir.glob("*.csv")):
        rep_id = int(f.stem.split("_")[-1])
        df = pd.read_csv(f, comment="#")
        trajs[rep_id] = df
    return rep, trajs


def classify_fate(gata1, pu1):
    if pu1 == 0:
        return "unk"
    r = gata1 / pu1
    if r > ERY_THRESHOLD:
        return "ery"
    if r < MYE_THRESHOLD:
        return "mye"
    return "unc"


def wilson_ci(k, n, z=1.96):
    """Wilson 95% CI for a proportion."""
    if n == 0:
        return 0.0, 0.0, 0.0
    p = k / n
    denom = 1 + z**2 / n
    centre = (p + z**2 / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / denom
    return p, max(0, centre - half), min(1, centre + half)


def commitment_time(traj: pd.DataFrame) -> float:
    """First time GATA1_nuc / PU1_nuc ratio crosses ERY_THRESHOLD."""
    valid = traj[traj["PU1_Protein_nuc"] > 0].copy()
    valid["ratio"] = valid["GATA1_Protein_nuc"] / valid["PU1_Protein_nuc"]
    committed = valid[valid["ratio"] > ERY_THRESHOLD]
    return committed["time"].iloc[0] if len(committed) > 0 else float("nan")


def flux_commitment_time(traj: pd.DataFrame) -> float:
    """First time GATA1_transcription > PU1_transcription (flux asymmetry appears)."""
    t11 = traj["GATA1_transcription"]
    t12 = traj["PU1_transcription"]
    crossed = traj[(t11 > t12) & (t12 > 0)]
    return traj.loc[crossed.index[0], "time"] if len(crossed) > 0 else float("nan")


def ph_hill_factor(pu1_series: pd.Series, ph: float = 7.5) -> pd.Series:
    """
    Actual Hill repression factor on GATA1 transcription due to PU1 nuclear:
        f = 1 / (1 + (PU1_nuc / K_inh)²)
    where K_inh = 8.0 × 10^(0.5 × (pH - 7.5))
    """
    k_inh = 8.0 * (10 ** (0.5 * (ph - 7.5)))
    return 1.0 / (1.0 + (pu1_series / k_inh) ** 2)


def arrhenius_sensitivity(rate_nom: float, ea_r: float, T_nom: float, T_new: float) -> float:
    """Predicted rate at T_new relative to T_nom."""
    return rate_nom * math.exp(-ea_r * (1 / T_new - 1 / T_nom))


def main():
    print(f"Run dir: {RUN_DIR}")
    print(f"Output:  {OUT_DIR}\n")

    all_fate_rows = []
    all_commitment_rows = []
    all_flux_rows = []
    all_ph_hill_rows = []
    all_energy_rows = []
    all_rep_stats = []

    for epo in EPO_CONDITIONS:
        # Find matching experiment directory
        matches = [d for d in RUN_DIR.iterdir()
                   if d.is_dir() and f"EPO_external={epo}" in d.name]
        if not matches:
            print(f"  [WARN] No directory found for EPO={epo}")
            continue
        exp_dir = matches[0]
        print(f"Processing EPO={epo}  ({exp_dir.name})")

        rep_df, trajs = load_experiment(exp_dir)
        n = len(rep_df)

        fates = []          # parallel lists, positional
        commit_times = []
        flux_times = []
        rep_ids_ordered = []  # actual rep_ids in sorted order
        ph_hill_at_t = []
        energy_at_t = []
        rep_stats = []

        for rep_id, traj in sorted(trajs.items()):
            rep_ids_ordered.append(rep_id)
            # ── Fate classification ──
            final = traj.iloc[-1]
            gata1_f = final["GATA1_Protein_nuc"]
            pu1_f = final["PU1_Protein_nuc"]
            fate = classify_fate(gata1_f, pu1_f)
            fates.append(fate)

            # ── Commitment timing ──
            ct = commitment_time(traj)
            ft = flux_commitment_time(traj)
            commit_times.append(ct)
            flux_times.append(ft)

            # ── pH-Hill repression factor (at each time point) ──
            # Use actual PU1_nuc trajectory; pH_nucleus is constant 7.5 in this run
            ph_hill = ph_hill_factor(traj["PU1_Protein_nuc"], ph=7.5)
            ph_hill_at_t.append({
                "epo": epo, "rep_id": rep_id, "fate": fate,
                "hill_mean": ph_hill.mean(),
                "hill_min": ph_hill.min(),
                "hill_max": ph_hill.max(),
                "hill_std": ph_hill.std(),
                # Hill factor RANGE: how much does pH sensitivity matter?
                "hill_range": ph_hill.max() - ph_hill.min(),
                # At pH=7.0 (K_inh=2.53), same PU1 → what would hill be?
                "hill_acidic_mean": ph_hill_factor(traj["PU1_Protein_nuc"], 7.0).mean(),
                "hill_alkaline_mean": ph_hill_factor(traj["PU1_Protein_nuc"], 8.0).mean(),
            })

            # ── Energy status ──
            atp_frac = traj["ATP"] / (traj["ATP"] + traj["ADP"])
            energy_at_t.append({
                "epo": epo, "rep_id": rep_id, "fate": fate,
                "atp_frac_mean": atp_frac.mean(),
                "atp_frac_min": atp_frac.min(),
                "atp_frac_std": atp_frac.std(),
                "atp_final": final["ATP"],
                "adp_final": final["ADP"],
                "gtp_final": final["GTP"],
                "gdp_final": final["GDP"],
                "charge": (final["ATP"] + 0.5 * final["ADP"]) /
                          (final["ATP"] + final["ADP"] + 0.001),
            })

            # ── Per-replicate summary ──
            final_t11 = final.get("GATA1_transcription", float("nan"))
            final_t12 = final.get("PU1_transcription", float("nan"))
            rep_stats.append({
                "epo": epo, "rep_id": rep_id, "fate": fate,
                "gata1_final": gata1_f,
                "pu1_final": pu1_f,
                "ratio_final": gata1_f / pu1_f if pu1_f > 0 else float("nan"),
                "pGATA1_final": final.get("pGATA1_nuc", float("nan")),
                "EPOR_bound_final": final.get("EPOR_bound", float("nan")),
                "t11_final": final_t11,
                "t12_final": final_t12,
                "t11_t12_ratio": final_t11 / final_t12 if final_t12 > 0 else float("nan"),
                "commit_time": ct,
                "flux_commit_time": ft,
                "n_timepoints": len(traj),
            })

        # ── Fate summary for this condition ──
        n_ery = fates.count("ery")
        n_mye = fates.count("mye")
        n_unc = fates.count("unc")
        p_ery, ci_lo, ci_hi = wilson_ci(n_ery, n)
        all_fate_rows.append({
            "epo": epo, "n": n,
            "n_ery": n_ery, "n_mye": n_mye, "n_unc": n_unc,
            "p_ery": p_ery, "ci_lo_95": ci_lo, "ci_hi_95": ci_hi,
        })

        # ── Mean fluxes across all replicates at final time point ──
        transitions = [c for c in next(iter(trajs.values())).columns if c not in [
            "time", "EPO_external", "PU1_Gene", "GATA1_mRNA_nuc", "PU1_mRNA_nuc",
            "GATA1_mRNA_cyto", "PU1_mRNA_cyto", "GATA1_Protein_cyto", "PU1_Protein_cyto",
            "GATA1_Protein_nuc", "PU1_Protein_nuc", "ATP", "GCSF_external", "ADP",
            "GTP", "GDP", "Pi", "pH_cytoplasm", "pH_nucleus", "Mg_cytoplasm",
            "Temperature", "pGATA1_nuc", "EPOR_free", "EPOR_bound",
            "EPOR_internalized", "GCSFR_free", "GCSFR_bound", "GCSFR_internalized",
            "GATA1_Gene",
        ]]

        # Build rep_id → fate lookup for subsetting
        fate_by_rid = {r["rep_id"]: r["fate"] for r in rep_stats if r["epo"] == epo}

        # Collect mean final rates across all replicates (by fate group)
        for fate_group in ["all", "ery", "mye", "unc"]:
            if fate_group == "all":
                subset = list(trajs.values())
            else:
                subset = [t for rid, t in trajs.items()
                          if fate_by_rid.get(rid) == fate_group]
            if not subset:
                continue
            final_rates = {}
            for trans in transitions:
                vals = [df.iloc[-1].get(trans, float("nan")) for df in subset]
                vals = [v for v in vals if not (isinstance(v, float) and math.isnan(v))]
                if vals:
                    final_rates[trans] = np.mean(vals)

            # Sort by rate to find bottleneck
            sorted_rates = sorted(final_rates.items(), key=lambda x: x[1])
            for rank, (trans, rate) in enumerate(sorted_rates):
                ea_r = EA_R.get(trans, float("nan"))
                # Predicted rate sensitivity to ±2°C
                if not math.isnan(ea_r) and rate > 0:
                    rate_at_fever = arrhenius_sensitivity(rate, ea_r, T_REF, 312.15)
                    rate_at_hypo = arrhenius_sensitivity(rate, ea_r, T_REF, 308.15)
                    fever_pct = (rate_at_fever / rate - 1) * 100
                    hypo_pct = (rate_at_hypo / rate - 1) * 100
                else:
                    fever_pct = float("nan")
                    hypo_pct = float("nan")

                all_flux_rows.append({
                    "epo": epo, "fate_group": fate_group, "transition": trans,
                    "mean_rate_final": rate, "rank_slow_to_fast": rank + 1,
                    "ea_r": ea_r,
                    "fever_pct_change": fever_pct,
                    "hypo_pct_change": hypo_pct,
                })

        all_commitment_rows.extend([
            {"epo": epo, "rep_id": rep_ids_ordered[i], "fate": fates[i],
             "commit_time_conc": commit_times[i],
             "commit_time_flux": flux_times[i]}
            for i in range(len(fates))
        ])
        all_ph_hill_rows.extend(ph_hill_at_t)
        all_energy_rows.extend(energy_at_t)
        all_rep_stats.extend(rep_stats)

        # ── Print brief summary ──
        valid_ct = [t for t in commit_times if not math.isnan(t)]
        valid_ft = [t for t in flux_times if not math.isnan(t)]
        print(f"  fates: {n_ery}ery / {n_mye}mye / {n_unc}unc  "
              f"P(ery)={p_ery:.2f} [{ci_lo:.2f},{ci_hi:.2f}]")
        if valid_ct:
            print(f"  commit_time (conc): n={len(valid_ct)}  "
                  f"med={np.median(valid_ct):.0f}s  "
                  f"mean={np.mean(valid_ct):.0f}±{np.std(valid_ct):.0f}s")
        if valid_ft:
            print(f"  commit_time (flux): n={len(valid_ft)}  "
                  f"med={np.median(valid_ft):.0f}s  "
                  f"mean={np.mean(valid_ft):.0f}±{np.std(valid_ft):.0f}s")

    # ─────────────────────────────────────────────────────────────────────────
    # Save outputs
    # ─────────────────────────────────────────────────────────────────────────

    fate_df = pd.DataFrame(all_fate_rows)
    fate_df.to_csv(OUT_DIR / "fate_summary.csv", index=False)
    print(f"\n── Fate summary ──")
    print(fate_df.to_string(index=False))

    commit_df = pd.DataFrame(all_commitment_rows)
    commit_df.to_csv(OUT_DIR / "commitment_times.csv", index=False)

    flux_df = pd.DataFrame(all_flux_rows)
    flux_df.to_csv(OUT_DIR / "bottleneck_fluxes.csv", index=False)

    ph_hill_df = pd.DataFrame(all_ph_hill_rows)
    ph_hill_df.to_csv(OUT_DIR / "ph_hill_variation.csv", index=False)

    energy_df = pd.DataFrame(all_energy_rows)
    energy_df.to_csv(OUT_DIR / "energy_status.csv", index=False)

    rep_stats_df = pd.DataFrame(all_rep_stats)
    rep_stats_df.to_csv(OUT_DIR / "per_replicate_stats.csv", index=False)

    # ─────────────────────────────────────────────────────────────────────────
    # Print key insights
    # ─────────────────────────────────────────────────────────────────────────

    print("\n── Bottleneck Transitions (slowest 5 across all EPO, fate=all) ──")
    bottleneck = flux_df[flux_df["fate_group"] == "all"].copy()
    bottleneck = bottleneck.groupby("transition")["mean_rate_final"].mean().reset_index()
    bottleneck = bottleneck.sort_values("mean_rate_final").head(10)
    bottleneck["fever_pct"] = bottleneck["transition"].map(
        lambda t: EA_R.get(t, float("nan"))
    ).apply(lambda ea: (math.exp(-ea * (1/312.15 - 1/T_REF)) - 1) * 100
            if not math.isnan(ea) else float("nan"))
    print(bottleneck.to_string(index=False))

    print("\n── pH-Hill factor variation (mean across replicates per EPO) ──")
    ph_summary = ph_hill_df.groupby("epo").agg(
        hill_mean=("hill_mean", "mean"),
        hill_range=("hill_range", "mean"),
        hill_acidic_mean=("hill_acidic_mean", "mean"),
        hill_alkaline_mean=("hill_alkaline_mean", "mean"),
    ).reset_index()
    ph_summary["fold_change_acid_to_alk"] = \
        ph_summary["hill_acidic_mean"] / ph_summary["hill_alkaline_mean"]
    print(ph_summary.to_string(index=False))

    print("\n── Energy status (ATP fraction mean per EPO, by fate) ──")
    energy_summary = energy_df.groupby(["epo", "fate"]).agg(
        atp_frac_mean=("atp_frac_mean", "mean"),
        atp_frac_std=("atp_frac_std", "mean"),
        charge_mean=("charge", "mean"),
    ).reset_index()
    print(energy_summary.to_string(index=False))

    print("\n── Flux asymmetry lead-time (flux commit - conc commit, seconds) ──")
    commit_df["lead_time"] = commit_df["commit_time_flux"] - commit_df["commit_time_conc"]
    lt_summary = commit_df.dropna(subset=["commit_time_conc", "commit_time_flux"]) \
                          .groupby("epo")["lead_time"].describe()
    print(lt_summary.to_string())

    # ─────────────────────────────────────────────────────────────────────────
    # Thermodynamic sensitivity table
    # ─────────────────────────────────────────────────────────────────────────

    print("\n── Predicted rate change at fever (312.15 K) for key transitions ──")
    key_trans = ["GATA1_transcription", "PU1_transcription",
                 "GATA1_translation", "PU1_translation",
                 "GATA1_nuclear_import", "ATP_synthesis"]
    sens_rows = []
    for t in key_trans:
        ea_r = EA_R.get(t, float("nan"))
        if math.isnan(ea_r):
            continue
        # Mean rate at EPO=0.449 (near bifurcation), all fates
        rate_rows = flux_df[(flux_df["epo"] == 0.449) &
                            (flux_df["fate_group"] == "all") &
                            (flux_df["transition"] == t)]
        if rate_rows.empty:
            continue
        rate_nom = rate_rows.iloc[0]["mean_rate_final"]
        sens_rows.append({
            "transition": t,
            "ea_kj_mol": ea_r * 8.314 / 1000,
            "rate_310K": rate_nom,
            "rate_308K": arrhenius_sensitivity(rate_nom, ea_r, T_REF, 308.15),
            "rate_312K": arrhenius_sensitivity(rate_nom, ea_r, T_REF, 312.15),
            "pct_change_fever": (arrhenius_sensitivity(rate_nom, ea_r, T_REF, 312.15) / rate_nom - 1) * 100,
            "pct_change_hypo":  (arrhenius_sensitivity(rate_nom, ea_r, T_REF, 308.15) / rate_nom - 1) * 100,
        })
    sens_df = pd.DataFrame(sens_rows)
    if not sens_df.empty:
        print(sens_df.to_string(index=False))

    print(f"\nAll outputs written to {OUT_DIR}")

    # ─────────────────────────────────────────────────────────────────────────
    # Optional plots
    # ─────────────────────────────────────────────────────────────────────────
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        plots_dir = OUT_DIR / "plots"
        plots_dir.mkdir(exist_ok=True)

        # 1. GATA1 final distribution per EPO (violin / strip)
        fig, axes = plt.subplots(1, 4, figsize=(14, 4), sharey=True)
        for ax, epo in zip(axes, EPO_CONDITIONS):
            sub = rep_stats_df[rep_stats_df["epo"] == epo]
            colors = {"ery": "#e74c3c", "mye": "#3498db", "unc": "#95a5a6"}
            for fate, grp in sub.groupby("fate"):
                ax.scatter([epo] * len(grp), grp["gata1_final"],
                           c=colors.get(fate, "grey"), alpha=0.6, s=20, label=fate)
            ax.set_title(f"EPO={epo}")
            ax.set_xlabel("EPO (µM)")
            if ax == axes[0]:
                ax.set_ylabel("GATA1_nuc final (µM)")
        axes[0].legend(title="fate", fontsize=7)
        plt.tight_layout()
        plt.savefig(plots_dir / "gata1_final_by_fate.png", dpi=150)
        plt.close()

        # 2. Commitment times
        fig, ax = plt.subplots(figsize=(7, 4))
        epo_jitter = {epo: i for i, epo in enumerate(EPO_CONDITIONS)}
        colors = {"ery": "#e74c3c", "mye": "#3498db", "unc": "#95a5a6"}
        for _, row in commit_df.iterrows():
            if not math.isnan(row["commit_time_conc"]):
                x = epo_jitter[row["epo"]] + np.random.uniform(-0.15, 0.15)
                c = colors.get(row["fate"], "grey")
                ax.scatter(x, row["commit_time_conc"], c=c, alpha=0.5, s=15)
        ax.set_xticks(list(epo_jitter.values()))
        ax.set_xticklabels([str(e) for e in EPO_CONDITIONS])
        ax.set_xlabel("EPO (µM)")
        ax.set_ylabel("Commitment time (s) — conc. crossing")
        ax.set_title("First-crossing time — GATA1/PU1 ratio > 1.5")
        plt.tight_layout()
        plt.savefig(plots_dir / "commitment_times.png", dpi=150)
        plt.close()

        # 3. pH-Hill factor variation per EPO
        fig, axes = plt.subplots(1, 4, figsize=(14, 4))
        for ax, epo in zip(axes, EPO_CONDITIONS):
            sub = ph_hill_df[ph_hill_df["epo"] == epo]
            ax.bar(["nom\n(pH 7.5)", "acid\n(pH 7.0)", "alk\n(pH 8.0)"],
                   [sub["hill_mean"].mean(), sub["hill_acidic_mean"].mean(),
                    sub["hill_alkaline_mean"].mean()],
                   color=["#2ecc71", "#e74c3c", "#3498db"])
            ax.set_title(f"EPO={epo}")
            ax.set_ylabel("Mean Hill repression factor")
            ax.set_ylim(0, 1)
        plt.suptitle("pH-Hill repression factor on GATA1 transcription\n"
                     f"f = 1/(1+(PU1/K_inh)²)  K_inh(7.0)=2.53, (7.5)=8, (8.0)=25.3 µM")
        plt.tight_layout()
        plt.savefig(plots_dir / "ph_hill_factor.png", dpi=150)
        plt.close()

        # 4. Energy status (ATP fraction) per EPO, per fate
        fig, ax = plt.subplots(figsize=(8, 4))
        for i, epo in enumerate(EPO_CONDITIONS):
            sub = energy_df[energy_df["epo"] == epo]
            for fate, grp in sub.groupby("fate"):
                jitter = np.random.uniform(-0.1, 0.1, len(grp))
                c = colors.get(fate, "grey")
                ax.scatter(i + jitter, grp["atp_frac_mean"], c=c, alpha=0.5, s=15)
        ax.set_xticks(range(len(EPO_CONDITIONS)))
        ax.set_xticklabels([str(e) for e in EPO_CONDITIONS])
        ax.set_xlabel("EPO (µM)")
        ax.set_ylabel("ATP/(ATP+ADP) mean fraction")
        ax.set_title("Energy charge by fate and EPO dose")
        plt.tight_layout()
        plt.savefig(plots_dir / "energy_status.png", dpi=150)
        plt.close()

        # 5. Bottleneck flux bar chart
        fig, ax = plt.subplots(figsize=(10, 5))
        bt = flux_df[(flux_df["fate_group"] == "all") &
                     (flux_df["epo"] == 0.449)].sort_values("mean_rate_final")
        ax.barh(bt["transition"], bt["mean_rate_final"])
        ax.set_xlabel("Mean final rate (µM/s)")
        ax.set_title("Transition rates at EPO=0.449 (all fates) — bottleneck identification")
        plt.tight_layout()
        plt.savefig(plots_dir / "bottleneck_fluxes_EPO0449.png", dpi=150)
        plt.close()

        print(f"Plots saved to {plots_dir}")

    except Exception as e:
        print(f"[WARN] Plotting skipped: {e}")


if __name__ == "__main__":
    main()
