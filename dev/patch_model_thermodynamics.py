#!/usr/bin/env python3
"""
Patch both phase3a model files to ensure thermodynamic completeness:

PLACE ATTRIBUTES (both models, same physical values — fL volumes scale-independent):
  - compartment string: set for all 28 places (were mostly missing)
  - compartment_volume: fill cytoplasm (200 fL), nucleus (800 fL already set),
    plasma_membrane (1000 fL already set); add to metabolic/pH places
  - is_energy_place=True: ATP, ADP, GTP, GDP, Pi, Mg_cytoplasm (P19-P23, P26)

RATE FUNCTION THERMODYNAMIC TERMS (both models, variable names identical):
  - Degradation T19-T26, T33: add exp(-6012.0*(1/Temperature-1/310.15))
    [Ea = 50 kJ/mol = protease/RNase, same as nuclear import]
  - Energy synthesis T27, T28: add exp(-3608.0*(1/Temperature-1/310.15))
    [Ea = 30 kJ/mol, per Temperature place notes]
  - T33 is adaptive: also add P27 to signal_places

At constant Temperature=310.15 K the Arrhenius factor = exp(0) = 1.0, so
simulation results at the calibration temperature are UNCHANGED. The terms
only matter in temperature-perturbation experiments.
"""

import json
import copy

ARRH_DEG   = "exp(-6012.0*(1/Temperature-1/310.15))"   # Ea=50 kJ/mol
ARRH_SYNTH = "exp(-3608.0*(1/Temperature-1/310.15))"   # Ea=30 kJ/mol

MODELS = {
    "phase3a_spatial_scaled.shy": dict(cytoplasm_vol=200.0, nucleus_vol=800.0, membrane_vol=1000.0),
    "phase3a_spatial_clean.shy":  dict(cytoplasm_vol=200.0, nucleus_vol=800.0, membrane_vol=1000.0),
}

COMPARTMENT_MAP = {
    "P1":  "extracellular",
    "P2":  "extracellular",
    "P3":  "plasma_membrane",
    "P4":  "plasma_membrane",
    "P5":  "endosome",
    "P6":  "plasma_membrane",
    "P7":  "plasma_membrane",
    "P8":  "endosome",
    "P9":  "nucleus",
    "P10": "nucleus",
    "P11": "nucleus",
    "P12": "nucleus",
    "P13": "cytoplasm",
    "P14": "cytoplasm",
    "P15": "cytoplasm",
    "P16": "cytoplasm",
    "P17": "nucleus",
    "P18": "nucleus",
    "P19": "cytoplasm",
    "P20": "cytoplasm",
    "P21": "cytoplasm",
    "P22": "cytoplasm",
    "P23": "cytoplasm",
    "P24": "cytoplasm",
    "P25": "nucleus",
    "P26": "cytoplasm",
    # P27 Temperature: global parameter, no compartment
    "P28": "nucleus",
}

# Places that are metabolic/energy cofactors
ENERGY_PLACES = {"P19", "P20", "P21", "P22", "P23", "P26"}

def compartment_volume(pid, vols):
    if pid in {"P3","P4","P5","P6","P7","P8"}:
        return vols["membrane_vol"]
    if COMPARTMENT_MAP.get(pid) == "nucleus":
        return vols["nucleus_vol"]
    if COMPARTMENT_MAP.get(pid) == "cytoplasm":
        return vols["cytoplasm_vol"]
    return None   # extracellular, Temperature: leave None


def append_arrhenius(rf, term):
    """Append Arrhenius term to rate function string."""
    # Avoid double-adding
    if "1/Temperature" in rf:
        return rf
    return f"{rf} * {term}"


def patch_model(path, vols):
    with open(path) as f:
        m = json.load(f)

    # ── PLACES ──────────────────────────────────────────────────────────────
    for p in m["places"]:
        pid = p["id"]

        # compartment string
        if pid in COMPARTMENT_MAP:
            p["compartment"] = COMPARTMENT_MAP[pid]

        # compartment_volume — only set if currently None/missing
        if p.get("compartment_volume") is None:
            cv = compartment_volume(pid, vols)
            if cv is not None:
                p["compartment_volume"] = cv

        # is_energy_place flag
        if pid in ENERGY_PLACES:
            p["is_energy_place"] = True

    # ── TRANSITIONS ─────────────────────────────────────────────────────────
    for t in m["transitions"]:
        tid = t["id"]
        props = t.get("properties", {})

        rf = props.get("rate_function", t.get("rate_function", ""))
        new_rf = rf

        # ── degradation: Ea/R = 6012 K (Ea=50 kJ/mol)
        if tid in {"T19","T20","T21","T22","T23","T24","T25","T26","T33"}:
            new_rf = append_arrhenius(rf, ARRH_DEG)

        # ── energy synthesis: Ea/R = 3608 K (Ea=30 kJ/mol)
        elif tid in {"T27","T28"}:
            new_rf = append_arrhenius(rf, ARRH_SYNTH)

        if new_rf != rf:
            props["rate_function"] = new_rf
            t["properties"] = props
            # also update legacy top-level rate_function if present
            if "rate_function" in t:
                t["rate_function"] = new_rf

            # adaptive transitions: add P27 to signal_places if Temperature now referenced
            if t.get("transition_type") == "adaptive":
                sp = t.get("signal_places", [])
                if "P27" not in sp:
                    sp.append("P27")
                    t["signal_places"] = sp

    return m


if __name__ == "__main__":
    import os
    base = "workspace/projects/gata/models"

    for fname, vols in MODELS.items():
        path = os.path.join(base, fname)
        print(f"Patching {fname} ...")
        m = patch_model(path, vols)
        with open(path, "w") as f:
            json.dump(m, f, indent=2, ensure_ascii=False)
        print(f"  Saved {path}")

    print("\nDone. Verifying ...")
    for fname in MODELS:
        path = os.path.join(base, fname)
        with open(path) as f:
            m = json.load(f)
        print(f"\n  {fname}")
        for p in m["places"]:
            pid = p["id"]
            cv  = p.get("compartment_volume")
            comp = p.get("compartment", "-")
            ep   = p.get("is_energy_place", False)
            flag = " [ENERGY]" if ep else ""
            print(f"    {pid:4s} {p['name']:<30s}  comp={comp:<20s}  vol={cv}{flag}")
        print()
        for t in m["transitions"]:
            tid = t["id"]
            if tid in {"T19","T20","T21","T22","T23","T24","T25","T26","T27","T28","T33"}:
                rf = t.get("properties",{}).get("rate_function", t.get("rate_function",""))
                sp = t.get("signal_places",[])
                has_arr = "exp(-" in rf
                mark = "OK" if has_arr else "MISSING"
                print(f"    {tid:4s} Arrhenius={mark}  sp={sp}  rf={rf[:80]}")
