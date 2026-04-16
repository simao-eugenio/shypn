"""
Analyse GATA/EPO bifurcation sweep results.

Column mapping (from PARAMETRIZATION STATE header):
  P17 = GATA1_Protein_nuc
  P18 = PU1_Protein_nuc
  P4  = EPOR_bound
  P1  = EPO_external
  Time = simulation time (s)

ERYTHROID commitment threshold: GATA1/PU1 ratio > 1.5
"""
import os

BASE = "workspace/projects/gata/experiments/results"

# Previous sweep for context
prev = {
    "0.41": ("experiment_EPO_external=0.41_20260227_100432", None),
    "0.42": ("experiment_EPO_external=0.42_20260227_100432", None),
    "0.43": ("experiment_EPO_external=0.43_20260227_100432", None),
    "0.44": ("experiment_EPO_external=0.44_20260227_100432", None),
}

new_experiments = {
    "0.445": "experiment_EPO_external=0.445_20260227_113254",
    "0.447": "experiment_EPO_external=0.447_20260227_113248",
    "0.449": "experiment_EPO_external=0.449_20260227_113246",
    "0.450": "experiment_EPO_external=0.45_20260227_113252",
    "0.451": "experiment_EPO_external=0.451_20260227_113251",
    "0.453": "experiment_EPO_external=0.453_20260227_113243",
    "0.455": "experiment_EPO_external=0.455_20260227_113249",
}

# Place-ID to semantic name (from # PARAMETRIZATION STATE section)
PLACE_NAMES = {
    "P1":  "EPO_external",
    "P2":  "GCSF_external",
    "P3":  "EPOR_free",
    "P4":  "EPOR_bound",
    "P5":  "EPOR_internalized",
    "P6":  "GCSFR_free",
    "P7":  "GCSFR_bound",
    "P8":  "GCSFR_internalized",
    "P9":  "GATA1_Gene",
    "P10": "PU1_Gene",
    "P11": "GATA1_mRNA_nuc",
    "P12": "PU1_mRNA_nuc",
    "P13": "GATA1_mRNA_cyto",
    "P14": "PU1_mRNA_cyto",
    "P15": "GATA1_Protein_cyto",
    "P16": "PU1_Protein_cyto",
    "P17": "GATA1_Protein_nuc",
    "P18": "PU1_Protein_nuc",
    "P19": "ATP",
    "P20": "ADP",
    "P21": "GTP",
    "P22": "GDP",
    "P23": "Pi",
    "P24": "pH_cytoplasm",
    "P25": "pH_nucleus",
    "P26": "Mg_cytoplasm",
    "P27": "Temperature",
    "P28": "pGATA1_nuc",
}


def parse_experiment(path):
    """Parse a results.csv and return final-state dict with semantic names."""
    with open(path) as f:
        lines = f.readlines()

    # Extract Time_Span from comments
    time_span = None
    n_reps_meta = None
    for line in lines:
        if "Time_Span:" in line:
            time_span = line.split("Time_Span:")[-1].strip()
        if "N_Replicates:" in line and line.startswith("#"):
            n_reps_meta = line.split("N_Replicates:")[-1].strip()

    # Find data table header (starts with "Time,")
    header_idx = None
    headers = None
    for i, line in enumerate(lines):
        if line.startswith("Time,"):
            header_idx = i
            headers = [h.strip() for h in line.split(",")]
            break

    if headers is None:
        return None, time_span, n_reps_meta

    n_cols = len(headers)

    # Find last complete data row (same number of columns as header, first col is float)
    last_data = None
    for line in reversed(lines[header_idx + 1:]):
        parts = [v.strip() for v in line.split(",")]
        if len(parts) == n_cols:
            try:
                float(parts[0])
                last_data = parts
                break
            except ValueError:
                pass

    if last_data is None:
        return None, time_span, n_reps_meta

    row = dict(zip(headers, last_data))

    # Map internal IDs to semantic names
    result = {}
    for col_id, value_str in row.items():
        name = PLACE_NAMES.get(col_id, col_id)
        try:
            result[name] = float(value_str)
        except ValueError:
            result[name] = value_str

    return result, time_span, n_reps_meta


print("=" * 80)
print("GATA/EPO BIFURCATION SWEEP ANALYSIS")
print("Erythroid commitment threshold: GATA1_nuc / PU1_nuc > 1.5")
print("=" * 80)
print(f"\n{'EPO (µM)':<10} {'t_final (s)':<13} {'GATA1_nuc':<12} {'PU1_nuc':<12} {'Ratio':<8} {'EPOR_bound':<12} Fate")
print("-" * 80)

all_experiments = list(new_experiments.items())

for epo, dirname in all_experiments:
    path = os.path.join(BASE, dirname, "results.csv")
    if not os.path.exists(path):
        print(f"{epo:<10} FILE NOT FOUND: {path}")
        continue

    data, time_span, n_reps_meta = parse_experiment(path)
    if data is None:
        print(f"{epo:<10} PARSE FAILED")
        continue

    t = data.get("Time", "?")
    t_str = f"{t:.0f}" if isinstance(t, float) else str(t)
    g = data.get("GATA1_Protein_nuc", 0.0)
    p = data.get("PU1_Protein_nuc", 0.0)
    eb = data.get("EPOR_bound", 0.0)
    ratio = g / p if p > 0 else float("inf")
    fate = "ERYTHROID ***" if ratio > 1.5 else "uncommitted"
    # metadata note
    meta_warn = ""
    if time_span and "120" in time_span:
        meta_warn = f"  [META BUG: Time_Span={time_span}, N_Reps_meta={n_reps_meta}]"

    print(f"{epo:<10} {t_str:<13} {g:<12.5f} {p:<12.5f} {ratio:<8.4f} {eb:<12.4f} {fate}{meta_warn}")

print("-" * 80)
print("\nNote: Place-ID mapping from PARAMETRIZATION STATE header.")
print("GATA1_Protein_nuc = P17  |  PU1_Protein_nuc = P18  |  EPOR_bound = P4")
