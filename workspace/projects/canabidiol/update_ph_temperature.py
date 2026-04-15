#!/usr/bin/env python3
"""Add pH and Temperature compartment places to CBD-AD model v1.

These are 'ubiquitous' environment places:
  - No arcs connect to/from them
  - The engine auto-detects places named 'Temperature' and 'pH'
    and injects their token values into ALL rate evaluation contexts
  - Rate functions reference them as T, Temperature, T_celsius, pH

Biophysical rationale:
  - pH 7.0 (physiological): affects enzyme activity, protein folding, Aβ aggregation
  - Temperature 310.15 K (37°C): affects all reaction rates via Arrhenius/Q10
  - Acidosis (pH < 7.0) accelerates Aβ aggregation and neuroinflammation
  - Fever (T > 310.15 K) increases ROS production and metabolic stress

Rate function modifications:
  - Arrhenius-like T dependence: rate × Q10^((T_celsius - 37)/10)
  - pH modulation on key processes (aggregation, enzyme activity, inflammation)
  - Uses Q10 ≈ 2 (standard for biological reactions)
"""

import json
import sys
from pathlib import Path

MODEL_PATH = Path(__file__).parent / "models" / "cbd_ad_neuroprotection_v1.shy"


def main():
    with open(MODEL_PATH) as f:
        model = json.load(f)

    places = model["places"]
    transitions = model["transitions"]

    # --- Check existing place IDs to find next available ---
    max_place_id = max(int(p["id"].replace("P", "")) for p in places)
    next_id = max_place_id + 1

    # --- 1. Add Temperature place (compartment, ubiquitous) ---
    # Position: top-left corner, away from the main network
    # Token value = 310.15 K (37°C, physiological body temperature)
    temp_place = {
        "id": f"P{next_id}",
        "name": "Temperature",
        "tokens": 310.15,
        "x": -360.0,
        "y": -140.0,
        "radius": 40.0,
        "is_signal": False,
        "signal_type": None,
        "signal_hierarchy": None,
        "is_compartment_place": True,
        "compartment": "environment",
    }
    places.append(temp_place)
    print(f"  Added P{next_id}: Temperature = 310.15 K (37°C), compartment=environment")
    next_id += 1

    # --- 2. Add pH place (compartment, ubiquitous) ---
    # Token value = 7.0 (physiological cytoplasmic pH)
    ph_place = {
        "id": f"P{next_id}",
        "name": "pH",
        "tokens": 7.0,
        "x": -360.0,
        "y": -50.0,
        "radius": 40.0,
        "is_signal": False,
        "signal_type": None,
        "signal_hierarchy": None,
        "is_compartment_place": True,
        "compartment": "environment",
    }
    places.append(ph_place)
    print(f"  Added P{next_id}: pH = 7.0, compartment=environment")

    # --- 3. Update thermodynamic_settings to match ---
    model["thermodynamic_settings"] = {
        "ph": 7.0,
        "temperature": 310.15,  # Updated from 298.15 to physiological 37°C
        "ionic_strength": 0.1,
        "tolerance": 0.5,
        "enable_validation": True,
        "preset": "biochemical_standard",
    }
    print("  Updated thermodynamic_settings: T=310.15 K, pH=7.0")

    # --- 4. Update rate functions to include T and pH dependence ---
    # Q10 factor: Q10^((T_celsius - 37)/10)  — at 37°C this equals 1.0
    # pH factor varies per process

    rate_updates = {
        # === AMYLOID CASCADE ===
        # Aβ aggregation is STRONGLY pH-dependent: acidosis accelerates it
        # pH < 7 → faster aggregation (protonation of His residues)
        "Abeta_Aggregation": (
            "0.05 * Abeta_Monomer * Abeta_Monomer",
            "0.05 * Abeta_Monomer * Abeta_Monomer * 2**((T_celsius - 37)/10) * (1 + 0.5*(7.0 - pH))",
        ),
        # Aβ production via γ-secretase (enzyme, T-dependent via Arrhenius)
        "Abeta_Production": (
            "0.3 * Gamma_Secretase",
            "0.3 * Gamma_Secretase * 2**((T_celsius - 37)/10)",
        ),
        # Plaque formation: T-dependent, slightly pH-enhanced at low pH
        "Plaque_Formation": (
            "0.02 * Abeta_Oligomer",
            "0.02 * Abeta_Oligomer * 2**((T_celsius - 37)/10) * (1 + 0.3*(7.0 - pH))",
        ),

        # === INFLAMMATION ===
        # NFkB transcription: standard T dependence
        "NFkB_transcription": (
            "0.5 * NFkB_p65",
            "0.5 * NFkB_p65 * 2**((T_celsius - 37)/10)",
        ),
        # IKK phosphorylation: enzyme kinetics, T-dependent
        "IKK_phosphorylates_IkB": (
            "0.2 * IKK * NFkB_IkB / (20 + NFkB_IkB)",
            "0.2 * IKK * NFkB_IkB / (20 + NFkB_IkB) * 2**((T_celsius - 37)/10)",
        ),
        # M1 polarization: inflammation accelerated by acidosis
        "M2_to_M1_polarization": (
            "0.1 * Microglia_M2 * (Abeta_Oligomer / (10 + Abeta_Oligomer) + TNFa / (20 + TNFa))",
            "0.1 * Microglia_M2 * (Abeta_Oligomer / (10 + Abeta_Oligomer) + TNFa / (20 + TNFa)) * 2**((T_celsius - 37)/10) * (1 + 0.3*(7.0 - pH))",
        ),

        # === ANTIOXIDANT DEFENSE ===
        # ROS production: increases with temperature (mitochondrial leak)
        "Basal_ROS_Production": (
            "2.0 + 0.5 * Abeta_Oligomer",
            "(2.0 + 0.5 * Abeta_Oligomer) * 2**((T_celsius - 37)/10)",
        ),
        # Antioxidant scavenging: enzyme-catalyzed, T and pH dependent
        # SOD optimal pH ~7.0-7.8, loses activity at low pH
        "Antioxidant_Scavenging": (
            "0.1 * (SOD + HO1) * ROS / (5 + ROS) + 0.05 * Glutathione * ROS / (5 + ROS)",
            "(0.1 * (SOD + HO1) * ROS / (5 + ROS) + 0.05 * Glutathione * ROS / (5 + ROS)) * 2**((T_celsius - 37)/10) * (1 - 0.3*abs(pH - 7.4))",
        ),
        # Nrf2 release by ROS: redox-sensitive, T-dependent
        "ROS_releases_Nrf2": (
            "0.15 * Keap1_Nrf2 * (ROS / (10 + ROS) + 0.3 * CBD / (50 + CBD))",
            "0.15 * Keap1_Nrf2 * (ROS / (10 + ROS) + 0.3 * CBD / (50 + CBD)) * 2**((T_celsius - 37)/10)",
        ),
        # Nrf2 ARE transcription: gene regulation, T-dependent
        "Nrf2_ARE_transcription": (
            "0.4 * Nrf2_free",
            "0.4 * Nrf2_free * 2**((T_celsius - 37)/10)",
        ),

        # === NEUROTOXICITY ===
        # Neurotoxicity: compound effect, accelerated by acidosis and fever
        "Neurotoxicity": (
            "0.01 * (Abeta_Oligomer / (10 + Abeta_Oligomer)) * (ROS / (15 + ROS)) * (TNFa / (10 + TNFa))",
            "0.01 * (Abeta_Oligomer / (10 + Abeta_Oligomer)) * (ROS / (15 + ROS)) * (TNFa / (10 + TNFa)) * 2**((T_celsius - 37)/10) * (1 + 0.4*(7.0 - pH))",
        ),

        # === DEGRADATION / CLEARANCE ===
        # Cytokine degradation: enzymatic, T-dependent
        "Cytokine_Degradation": (
            "0.005 * (TNFa + IL1b + IL6 + COX2)",
            "0.005 * (TNFa + IL1b + IL6 + COX2) * 2**((T_celsius - 37)/10)",
        ),
        # Nrf2 proteasomal degradation: T-dependent
        "Nrf2_degradation": (
            "0.1 * Nrf2_free",
            "0.1 * Nrf2_free * 2**((T_celsius - 37)/10)",
        ),
        # IKK dephosphorylation: phosphatase, T-dependent
        "IKK_Dephosphorylation": (
            "0.008 * (IKK - 10) * (IKK > 10)",
            "0.008 * (IKK - 10) * (IKK > 10) * 2**((T_celsius - 37)/10)",
        ),
        # Aβ oligomer clearance by M2 microglia: T-dependent
        "Abeta_Oligomer_Clearance": (
            "0.003 * Microglia_M2 * Abeta_Oligomer / (10 + Abeta_Oligomer)",
            "0.003 * Microglia_M2 * Abeta_Oligomer / (10 + Abeta_Oligomer) * 2**((T_celsius - 37)/10)",
        ),
        # BDNF neuroprotection: T-dependent
        "BDNF_neuroprotection": (
            "0.05 * BDNF * (100 - Neuron_Health) / 100",
            "0.05 * BDNF * (100 - Neuron_Health) / 100 * 2**((T_celsius - 37)/10)",
        ),
    }

    updated_count = 0
    for t in transitions:
        name = t.get("name", t.get("label", ""))
        if name in rate_updates:
            old_rate, new_rate = rate_updates[name]
            current = t["properties"]["rate_function"]
            if current != old_rate:
                print(f"  WARNING: {name} rate mismatch!")
                print(f"    Expected: {old_rate}")
                print(f"    Found:    {current}")
                continue
            t["properties"]["rate_function"] = new_rate
            updated_count += 1
            print(f"  Updated {name}")

    print(f"\n  Summary: {updated_count}/{len(rate_updates)} rate functions updated")
    print(f"  Places: {len(places)} (was {len(places)-2})")

    # --- 5. Save ---
    with open(MODEL_PATH, "w") as f:
        json.dump(model, f, indent=2)
    print(f"\n  Saved to {MODEL_PATH}")


if __name__ == "__main__":
    main()
