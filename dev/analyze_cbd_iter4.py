"""Iter 4 analysis: CBD AD neuroprotection sim after stochastic-gate fix.

Focus: did Abeta_Aggregation / Plaque_Formation come alive?
"""
from pathlib import Path
import pandas as pd

CSV = Path("workspace/projects/canabidiol/data/simulation_data.csv")
df = pd.read_csv(CSV)

t = df["Time (s)"]
T_FINAL = float(t.iloc[-1])
print(f"=== Run length: {T_FINAL:.1f} s, {len(df)} rows ===\n")

# ---------- Transition firings ----------
firing_cols = [c for c in df.columns if c.endswith("(firings)")]
final = df[firing_cols].iloc[-1].astype(float)
final.index = [c.replace(" (firings)", "") for c in final.index]

zero = final[final == 0].sort_index()
nonzero = final[final > 0].sort_values(ascending=False)

print("=== TRANSITIONS THAT NEVER FIRED ===")
if len(zero) == 0:
    print("  (none — all transitions fired at least once)")
else:
    for name in zero.index:
        print(f"  {name}")
print()

print("=== TOP 15 MOST ACTIVE TRANSITIONS ===")
for name, n in nonzero.head(15).items():
    print(f"  {name:40s} {int(n):>10,}")
print()

# Focus transitions
focus = ["Abeta_Aggregation", "Plaque_Formation", "Abeta_Oligomer_Clearance",
         "Plaque_Clearance", "Abeta_Production", "Abeta_Monomer_Clearance",
         "Nrf2_degradation", "Neurotoxicity", "BDNF_neuroprotection"]
print("=== FOCUS TRANSITIONS ===")
for f in focus:
    val = final.get(f, "MISSING")
    print(f"  {f:35s} {val if val == 'MISSING' else f'{int(val):>10,}'}")
print()

# ---------- Aβ cascade markings ----------
abeta_places = ["Abeta_Monomer", "Abeta_Oligomer", "Abeta_Plaque", "APP", "APP_mRNA"]
print("=== Aβ CASCADE TRAJECTORY ===")
print(f"  {'place':25s} {'t=0':>10s} {'t=mid':>10s} {'t=end':>10s}")
mid = len(df) // 2
for p in abeta_places:
    col = f"{p} (mM)"
    if col in df.columns:
        print(f"  {p:25s} {df[col].iloc[0]:>10.4f} {df[col].iloc[mid]:>10.4f} {df[col].iloc[-1]:>10.4f}")
print()

# ---------- Health & inflammation ----------
key_places = ["Neuron_Health", "ROS", "TNFa", "IL1b", "IL6", "NFkB_p65",
              "Nrf2_free", "HO1", "SOD", "Glutathione", "BDNF",
              "Microglia_M1", "Microglia_M2", "CBD_intracellular"]
print("=== HEALTH & INFLAMMATION TRAJECTORY ===")
print(f"  {'place':25s} {'t=0':>10s} {'t=mid':>10s} {'t=end':>10s}    {'Δ end-init':>10s}")
for p in key_places:
    col = f"{p} (mM)"
    if col in df.columns:
        v0 = df[col].iloc[0]
        vmid = df[col].iloc[mid]
        vend = df[col].iloc[-1]
        print(f"  {p:25s} {v0:>10.4f} {vmid:>10.4f} {vend:>10.4f}    {vend - v0:>+10.4f}")
print()

# ---------- Aβ aggregation vs clearance balance ----------
agg = final.get("Abeta_Aggregation", 0)
clr = final.get("Abeta_Oligomer_Clearance", 0)
plf = final.get("Plaque_Formation", 0)
plc = final.get("Plaque_Clearance", 0)
print("=== Aβ FLOW BALANCE ===")
print(f"  Monomer → Oligomer (Abeta_Aggregation):  {int(agg):>10,}")
print(f"  Oligomer clearance:                       {int(clr):>10,}")
print(f"  Oligomer → Plaque (Plaque_Formation):    {int(plf):>10,}")
print(f"  Plaque clearance:                         {int(plc):>10,}")
print()

# ---------- Final Aβ concentrations ----------
print("=== FINAL Aβ POOL (mM) ===")
for p in ["Abeta_Monomer", "Abeta_Oligomer", "Abeta_Plaque"]:
    col = f"{p} (mM)"
    if col in df.columns:
        print(f"  {p:20s} {df[col].iloc[-1]:.6f}")
