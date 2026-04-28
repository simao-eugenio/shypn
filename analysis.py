import pandas as pd
import numpy as np

path = 'workspace/projects/canabidiol/data/simulation_data.csv'
df = pd.read_csv(path)
orig_cols = list(df.columns)
df.columns = [c.split(" (")[0].strip() for c in orig_cols]
firing_cols = [c.split(" (")[0].strip() for c in orig_cols if "(firings)" in c]
state_cols  = [c.split(" (")[0].strip() for c in orig_cols if "(mM)" in c]
time_col = "Time"

# 1. Time span
t_min, t_max = df[time_col].min(), df[time_col].max()
dt = df[time_col].diff().median()
rows = len(df)
print(f"1. Time: {t_min} to {t_max}, dt={dt:.2f}, rows={rows}")

# 2. Aβ cascade firing counts
ab_firings = ['Abeta_Production', 'Abeta_Aggregation', 'Plaque_Formation', 'Abeta_Monomer_Clearance', 'Abeta_Oligomer_Clearance', 'Plaque_Clearance', 'Nrf2_degradation']
print("\n2. Abeta Cascade Firings:")
for f in ab_firings:
    val = df[f].iloc[-1]
    status = "[ZERO]" if val == 0 else "ALIVE"
    print(f"  {f}: {val} {status}")

# 3. Aβ trajectories
ab_states = ['Abeta_Monomer', 'Abeta_Oligomer', 'Abeta_Plaque']
print("\n3. Abeta Trajectories:")
for s in ab_states:
    vals = df[s]
    t3 = df.iloc[(df[time_col]-3600).abs().argsort()[:1]][s].values[0]
    t7 = df.iloc[(df[time_col]-7200).abs().argsort()[:1]][s].values[0]
    t10 = df.iloc[(df[time_col]-10800).abs().argsort()[:1]][s].values[0]
    print(f"  {s}: init={vals.iloc[0]:.2e}, final={vals.iloc[-1]:.2e}, min={vals.min():.2e}, max={vals.max():.2e}, t~3600={t3:.2e}, t~7200={t7:.2e}, t~10800={t10:.2e}")

# 4. Top 15 state changes
diffs = (df[state_cols].iloc[-1] - df[state_cols].iloc[0]).abs().sort_values(ascending=False)
print("\n4. Top 15 State Changes |final-init|:")
print(diffs.head(15))

# 5. Firings still at 0
zeros = [f for f in firing_cols if df[f].iloc[-1] == 0]
print(f"\n5. Firings at zero: {len(zeros)} items")
if zeros: print(f"  {', '.join(zeros[:10])}...")

# 6. Aβ mass balance
in_val = df['Abeta_Production'].iloc[-1]
out_val = df['Abeta_Monomer_Clearance'].iloc[-1] + df['Abeta_Oligomer_Clearance'].iloc[-1] + df['Plaque_Clearance'].iloc[-1]
s_init = df[ab_states].iloc[0].sum()
s_final = df[ab_states].iloc[-1].sum()
delta_sum = s_final - s_init
print(f"\n6. Abeta Mass Balance: In={in_val:.2e}, Out={out_val:.2e}, DeltaSum={delta_sum:.2e}")

# 7. Health/inflammation
h_states = ['Neuron_Health', 'ROS', 'NFkB_p65', 'BDNF', 'IL1b', 'IL6', 'TNFa', 'COX2', 'Microglia_M1', 'Microglia_M2']
print("\n7. Health/Inflammation (init -> final):")
for s in h_states:
    if s in df.columns:
        print(f"  {s}: {df[s].iloc[0]:.2e} -> {df[s].iloc[-1]:.2e}")

# 8. Integrity
nans = df.isna().sum().sum()
infs = np.isinf(df.select_dtypes(include=np.number)).sum().sum()
negatives = (df[state_cols] < 0).sum().sum()
print(f"\n8. Integrity: NaNs={nans}, Infs={infs}, Negatives={negatives}")

# 9. Drift
n = len(df)
mid_start, mid_end = int(0.45*n), int(0.55*n)
last_start = int(0.9*n)
mid_mean = df[state_cols].iloc[mid_start:mid_end].mean()
last_mean = df[state_cols].iloc[last_start:].mean()
drift = ((last_mean - mid_mean).abs() / mid_mean.replace(0, 1e-12)).sort_values(ascending=False)
significant_drift = drift[drift > 0.05]
print(f"\n9. States with >5% relative drift: {len(significant_drift)}")
if not significant_drift.empty:
    print(significant_drift.head(10))

# 10. CBD PK
cbd = ['CBD_extracellular', 'CBD_intracellular']
print("\n10. CBD PK:")
for s in cbd:
    if s in df.columns:
        t0 = df[s].iloc[0]
        t3 = df.iloc[(df[time_col]-3600).abs().argsort()[:1]][s].values[0]
        t7 = df.iloc[(df[time_col]-7200).abs().argsort()[:1]][s].values[0]
        tend = df[s].iloc[-1]
        print(f"  {s}: t0={t0:.2e}, t3600={t3:.2e}, t7200={t7:.2e}, end={tend:.2e}")
