"""Recon of v3_p8 UI snapshot at workspace/projects/canabidiol/data/simulation_data.csv."""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import pandas as pd

CSV = Path("workspace/projects/canabidiol/data/simulation_data.csv")
df = pd.read_csv(CSV)
df.columns = [c.replace(" (mM)", "").replace(" (firings)", "_fires").replace(" (s)", "") for c in df.columns]
t = df["Time"].to_numpy()
T_END = t[-1]
print(f"rows={len(df)}  t∈[{t[0]:.1f}, {T_END:.1f}] s ({T_END/3600:.2f} h)  dt_mean={np.mean(np.diff(t)):.3f} s")

# ── Experiment plan (▢ + ◇) ─────────────────────────────────────────────
print("\n=== Experiment plan ▢ parameters (initial values) ===")
for k in ["TEMPERATURE","PH","AGE","DISEASE_SEVERITY","LOADING_DOSE","MAINT_DOSE","DOSE_INTERVAL"]:
    print(f"  {k:18s} = {df[k].iloc[0]:.4f}   (constant: {df[k].nunique()==1})")

print("\n=== Pattern-A ◇ spatial signals (initial → t=2.88s → final) ===")
for k in ["Temperature_factor","Age_factor","pH_acidosis","pH_neutrality"]:
    a, b, c = df[k].iloc[0], df[k].iloc[1], df[k].iloc[-1]
    print(f"  {k:20s} {a:8.4f} → {b:8.4f} → {c:8.4f}   (fired: {abs(b-a)>1e-9})")

# ── Healthy vs disease classification ─────────────────────────────────
DSev = df["DISEASE_SEVERITY"].iloc[0]
print(f"\n>>> Regime: {'HEALTHY (DSev=0)' if DSev==0 else f'DISEASE (DSev={DSev})'}")

# ── CBD pharmacokinetics ──────────────────────────────────────────────
print("\n=== CBD PK ===")
cbd_e, cbd_i = df["CBD_extracellular"].to_numpy(), df["CBD_intracellular"].to_numpy()
peak_i = cbd_i.argmax()
print(f"  CBD_extra : t0={cbd_e[0]:.3f}  min={cbd_e.min():.3f}  max={cbd_e.max():.3f}  final={cbd_e[-1]:.3f}")
print(f"  CBD_intra : t0={cbd_i[0]:.3f}  peak={cbd_i.max():.3f} @ t={t[peak_i]:.0f}s  final={cbd_i[-1]:.3f}")
absorb_fires = df["CBD_Absorption_fires"].iloc[-1]
clear_fires  = df["CBD_Systemic_Clearance_fires"].iloc[-1]
print(f"  Absorption fires={absorb_fires:.1f}   Systemic clearance fires={clear_fires:.1f}")

# ── Disease-axis: Aβ cascade & APP ───────────────────────────────────
print("\n=== Amyloid cascade ===")
for k in ["APP_mRNA","APP","Abeta_Monomer","Abeta_Oligomer","Abeta_Plaque"]:
    v = df[k].to_numpy()
    print(f"  {k:18s} init={v[0]:8.3f}  final={v[-1]:8.3f}  Δ={v[-1]-v[0]:+8.3f}")
for k in ["APP_Transcription_fires","APP_Translation_fires","Abeta_Production_fires",
          "Abeta_Aggregation_fires","Plaque_Formation_fires","Plaque_Clearance_fires",
          "Abeta_Monomer_Clearance_fires","Abeta_Oligomer_Clearance_fires"]:
    if k in df.columns:
        print(f"  {k:34s} fires={df[k].iloc[-1]:.1f}")

# ── Inflammation axis ────────────────────────────────────────────────
print("\n=== Inflammation (NF-κB / cytokines / microglia) ===")
for k in ["IKK","NFkB_IkB","NFkB_p65","TNFa","IL1b","IL6","COX2","Microglia_M1","Microglia_M2"]:
    v = df[k].to_numpy()
    print(f"  {k:14s} init={v[0]:8.3f}  final={v[-1]:8.3f}  Δ={v[-1]-v[0]:+8.3f}")

# ── Oxidative stress / Nrf2 axis ─────────────────────────────────────
print("\n=== Redox (ROS / Nrf2 / antioxidants) ===")
for k in ["ROS","Glutathione","GSSG","Keap1_Nrf2","Nrf2_free","HO1","SOD"]:
    v = df[k].to_numpy()
    print(f"  {k:14s} init={v[0]:8.3f}  final={v[-1]:8.3f}  Δ={v[-1]-v[0]:+8.3f}")

# ── CBD targets ─────────────────────────────────────────────────────
print("\n=== CBD pharmacological targets ===")
for k in ["GPR3","GPR3_inactive","HT1A_active","PPARg_active","A2A_active","BDNF","Gamma_Secretase"]:
    v = df[k].to_numpy()
    print(f"  {k:18s} init={v[0]:8.3f}  final={v[-1]:8.3f}  Δ={v[-1]-v[0]:+8.3f}")

# ── Outcome ─────────────────────────────────────────────────────────
print("\n=== OUTCOME: Neuron_Health ===")
nh = df["Neuron_Health"].to_numpy()
print(f"  init={nh[0]:.3f}  min={nh.min():.3f} @ t={t[nh.argmin()]:.0f}s  final={nh[-1]:.3f}  Δ={nh[-1]-nh[0]:+.3f}")
neuro_fires = df["Neurotoxicity_fires"].iloc[-1] if "Neurotoxicity_fires" in df.columns else None
bdnf_fires  = df["BDNF_neuroprotection_fires"].iloc[-1] if "BDNF_neuroprotection_fires" in df.columns else None
print(f"  Neurotoxicity_fires={neuro_fires}   BDNF_neuroprotection_fires={bdnf_fires}")

# ── Zero-firing (dead) transitions ──────────────────────────────────
print("\n=== Zero-firing transitions over the run ===")
fire_cols = [c for c in df.columns if c.endswith("_fires")]
dead = [c for c in fire_cols if df[c].iloc[-1] == 0]
print(f"  total transitions logged: {len(fire_cols)}   dead: {len(dead)}")
for c in dead:
    print(f"    · {c}")

# ── Top-firing transitions ──────────────────────────────────────────
print("\n=== Top 10 most-active transitions ===")
totals = sorted(((df[c].iloc[-1], c) for c in fire_cols), reverse=True)[:10]
for n, c in totals:
    print(f"  {n:10.1f}  {c}")
