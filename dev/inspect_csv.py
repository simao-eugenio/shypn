"""Show trajectory of GATA1(P17), PU1(P18), EPOR(P4), ATP(P19) at key time points."""
path = "workspace/projects/gata/experiments/results/experiment_EPO_external=0.445_20260227_113254/results.csv"
lines = open(path).readlines()

# Find header
header_idx = None
headers = None
for i, line in enumerate(lines):
    if line.startswith("Time,"):
        header_idx = i
        headers = [h.strip() for h in line.split(",")]
        break

n_cols = len(headers)
idx = {h: i for i, h in enumerate(headers)}

# Collect all full data rows
full_rows = []
for line in lines[header_idx + 1:]:
    parts = [v.strip() for v in line.split(",")]
    if len(parts) == n_cols:
        try:
            float(parts[0])
            full_rows.append(parts)
        except ValueError:
            pass

print(f"Total rows: {len(full_rows)}  t_range: {full_rows[0][0]} -> {full_rows[-1][0]}")
print()
print(f"{'Time':>10} {'GATA1(P17)':>12} {'PU1(P18)':>12} {'EPOR_b(P4)':>12} {'ATP(P19)':>12}")
print("-" * 62)

# Sample every ~10% of the simulation
n = len(full_rows)
sample_indices = [0, n//10, n//5, 3*n//10, 2*n//5, n//2, 3*n//5, 7*n//10, 4*n//5, 9*n//10, -2, -1]
seen = set()
for i in sample_indices:
    if i in seen:
        continue
    seen.add(i)
    row = full_rows[i]
    t   = float(row[idx["Time"]])
    g   = float(row[idx["P17"]])
    p   = float(row[idx["P18"]])
    ep  = float(row[idx["P4"]])
    atp = float(row[idx["P19"]])
    print(f"{t:>10.1f} {g:>12.5f} {p:>12.5f} {ep:>12.5f} {atp:>12.2f}")

