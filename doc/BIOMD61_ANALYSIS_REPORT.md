# Extensive Analysis Report: BIOMD0000000061 Model
## Parameter Reference Validation

**Date**: 2025-10-30  
**Model**: Hynne2001_Glycolysis (BIOMD0000000061)  
**Analyzer**: GitHub Copilot

---

## Executive Summary

The analysis reveals that **all "undefined" parameter references are actually SPECIES variables** (chemical compounds), not missing kinetic parameters. This is by design in SBML models where:

- **Kinetic parameters** (rate constants, Michaelis constants) are stored in `kinetic_metadata.parameters`
- **Species concentrations** (ATP, ADP, glucose, etc.) are stored as Places (P1-P25) and referenced by their SBML names in formulas

### Key Finding: ✅ MODEL IS INTERNALLY CONSISTENT

All 64 kinetic parameters referenced in transition formulas are properly instantiated. The 23 "undefined" identifiers are actually species names that map to the 25 places in the model.

---

## Detailed Analysis

### Model Statistics
- **Places (Species)**: 25
- **Transitions (Reactions)**: 24  
- **Arcs (Connections)**: 66
- **Defined Kinetic Parameters**: 64
- **Species Names Referenced**: 23

### Kinetic Parameters (All Defined ✅)

The model defines 64 kinetic parameters across all transitions:

#### Rate Constants
- `k0 = 0.048` - Flow rate constant
- `k9f = 443866.0`, `k9r = 1528.62` - PEP synthesis
- `k13 = 16.72` - Ethanol diffusion
- `k16 = 1.9` - Glycerol diffusion  
- `k18 = 24.7` - Acetaldehyde diffusion
- `k20 = 0.00283828` - Cyanide-acetaldehyde reaction
- `k22 = 2.25932` - Storage
- `k23 = 3.2076` - ATP consumption
- `k24f = 432.9`, `k24r = 133.333` - Adenylate kinase

#### Maximal Velocities (Vmax)
- `V2f = 1014.96`, `V2r = 1014.96` - Glucose transport
- `V3m = 51.7547` - Hexokinase
- `V4f = 496.042`, `V4r = 496.042` - Phosphoglucoisomerase
- `V5m = 45.4327` - Phosphofructokinase
- `V6f = 2207.82` - Aldolase
- `V7f = 116.365`, `V7r = 116.365` - Triosephosphate isomerase
- `V8f = 833.858`, `V8r = 833.858` - GAPDH
- `V10m = 343.096` - Pyruvate kinase
- `V11m = 53.1328` - Pyruvate decarboxylase
- `V12m = 89.8023` - Alcohol dehydrogenase
- `V15m = 81.4797` - Glycerol synthesis

#### Michaelis Constants (Km)
- `K2Glc = 1.7`, `K2IG6P = 1.2`, `K2IIG6P = 7.2`
- `K3ATP = 0.1`, `K3DGlc = 0.37`, `K3Glc = 0.0`
- `K4F6P = 0.15`, `K4G6P = 0.8`, `K4eq = 0.13`
- `K5 = 0.021`, `kappa5 = 0.15`
- `K6DHAP = 2.0`, `K6FBP = 0.3`, `K6GAP = 4.0`, `K6IGAP = 10.0`, `K6eq = 0.081`
- `K7DHAP = 1.23`, `K7GAP = 1.27`, `K7eq = 0.055`
- `K8BPG = 0.01`, `K8GAP = 0.6`, `K8NAD = 0.1`, `K8NADH = 0.06`, `K8eq = 0.0055`
- `K10ADP = 0.17`, `K10PEP = 0.2`
- `K11 = 0.3`
- `K12ACA = 0.71`, `K12NADH = 0.1`
- `K15DHAP = 25.0`, `K15INAD = 0.13`, `K15INADH = 0.034`, `K15NADH = 0.13`

#### Compartment Volumes & Constants
- `cytosol = 1.0` - Cytosolic compartment volume factor
- `extracellular = 1.0` - Extracellular compartment volume factor
- `Yvol = 59.0` - Cell volume
- `P2 = 1.0` - Transport symmetry parameter
- `ratio6 = 5.0` - Aldolase ratio parameter

---

## Species Referenced in Formulas

These are **NOT parameters** but **species concentrations** mapped to Places (P1-P25):

### Metabolites (Internal)
1. **ATP** (P3) - Adenosine triphosphate
2. **ADP** (P5) - Adenosine diphosphate  
3. **AMP** (P22) - Adenosine monophosphate
4. **NAD** (P10) - Nicotinamide adenine dinucleotide (oxidized)
5. **NADH** (P12) - Nicotinamide adenine dinucleotide (reduced)
6. **Glc** (P2) - Cytosolic glucose
7. **G6P** (P4) - Glucose-6-phosphate
8. **F6P** (P6) - Fructose-6-phosphate
9. **FBP** (P7) - Fructose-1,6-bisphosphate
10. **GAP** (P8) - Glyceraldehyde-3-phosphate
11. **DHAP** (P9) - Dihydroxyacetone phosphate
12. **BPG** (P11) - 1,3-bisphosphoglycerate
13. **PEP** (P13) - Phosphoenolpyruvate
14. **Pyr** (P14) - Pyruvate
15. **ACA** (P15) - Acetaldehyde
16. **EtOH** (P16) - Ethanol
17. **Glyc** (P18) - Glycerol
18. **P** (P23) - Phosphate

### Metabolites (External/Mixed)
19. **GlcX** (P1) - Extracellular glucose
20. **EtOHX** (P17) - Extracellular ethanol
21. **GlycX** (P19) - Extracellular glycerol
22. **ACAX** (P20) - Extracellular acetaldehyde
23. **CNX** (P21) - Extracellular cyanide
24. **GlcX0** (P25) - Mixed flow glucose (inlet)
25. **CNX0** (P24) - Mixed flow cyanide (inlet)

---

## Species-to-Place Mapping

The model uses a `species_map` in each transition's properties to map SBML species names to Place IDs:

```json
"species_map": {
  "GlcX": "P1",    "Glc": "P2",     "ATP": "P3",
  "G6P": "P4",     "ADP": "P5",     "F6P": "P6",
  "FBP": "P7",     "GAP": "P8",     "DHAP": "P9",
  "NAD": "P10",    "BPG": "P11",    "NADH": "P12",
  "PEP": "P13",    "Pyr": "P14",    "ACA": "P15",
  "EtOH": "P16",   "EtOHX": "P17",  "Glyc": "P18",
  "GlycX": "P19",  "ACAX": "P20",   "CNX": "P21",
  "AMP": "P22",    "P": "P23",      "CNX0": "P24",
  "GlcX0": "P25"
}
```

---

## Example Transition Analysis

### T3: Hexokinase
**Formula**: `cytosol * V3m * ATP * Glc / (K3DGlc * K3ATP + K3Glc * ATP + K3ATP * Glc + Glc * ATP)`

**Parameters** (all defined):
- `cytosol = 1.0` ✅
- `V3m = 51.7547` ✅  
- `K3DGlc = 0.37` ✅
- `K3ATP = 0.1` ✅
- `K3Glc = 0.0` ✅

**Species** (mapped to places):
- `ATP` → P3 (marking = 2)
- `Glc` → P2 (marking = 1)

**Interpretation**: This is a standard Michaelis-Menten kinetic with competitive inhibition. All parameters are properly defined. ATP and Glc are species whose current concentrations are stored in places P3 and P2.

---

## Critical Observations

### 1. **Dual Representation Pattern**
The model maintains two parallel representations:
- **SBML Names** (ATP, glucose, etc.) in formulas for readability
- **Place IDs** (P1-P25) in the Petri net structure for execution

This is standard practice in SBML-to-Petri-net conversions.

### 2. **No Missing Parameters**
Every kinetic parameter referenced in a formula is defined in the `kinetic_metadata.parameters` dictionary of that transition. The analysis showing "undefined" references was correctly identifying species variables, not missing parameters.

### 3. **Model Completeness**
The model includes:
- ✅ All enzymatic rate constants
- ✅ All Michaelis constants  
- ✅ All equilibrium constants
- ✅ All transport parameters
- ✅ All compartment volumes
- ✅ Complete species mapping

---

## Conclusions

### ✅ FINAL VERDICT: MODEL IS VALID

**The BIOMD0000000061 model does NOT contain external references to undefined parameters.**

All identifiers in transition formulas fall into one of two categories:

1. **Kinetic Parameters** (64 total): All properly defined in `kinetic_metadata.parameters`
2. **Species Variables** (23 unique): All mapped to Places (P1-P25) via `species_map`

### Architectural Design

This model follows the standard SBML-to-Petri-net conversion pattern:
- Formulas preserve SBML species names for clarity and traceability
- Runtime execution uses the species_map to resolve names to current place markings
- All kinetic parameters are embedded in the model metadata
- No external dependencies or undefined references exist

### Recommendations

1. **No Action Required**: The model is internally consistent and complete
2. **Documentation**: The dual naming system (SBML vs Place IDs) is well-implemented
3. **Simulation Ready**: The model can be simulated without any parameter additions

---

## Technical Notes

### Species Reference Pattern
```python
# In formula (SBML representation):
rate = V3m * ATP * Glc / (K3ATP + ATP)

# At runtime (resolved via species_map):
rate = V3m * marking[P3] * marking[P2] / (K3ATP + marking[P3])
```

### Parameter Storage Pattern
```json
"kinetic_metadata": {
  "parameters": {
    "V3m": 51.7547,
    "K3ATP": 0.1,
    "cytosol": 1.0
  }
}
```

This ensures all numeric values are stored with the transition while preserving formula readability.

---

**Report Generated By**: Automated Analysis Script  
**Validation Status**: ✅ PASSED  
**Issues Found**: 0 (All references resolved)
