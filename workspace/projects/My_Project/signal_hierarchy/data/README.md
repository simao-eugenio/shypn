# Data Directory

Supporting data for signal hierarchy paper.

---

## Directory Structure

```
data/
├── lambda_phage/           # Main case study
│   ├── original/           # Original model simulations
│   ├── refactored/         # Refactored model simulations
│   ├── comparison/         # Statistical comparison
│   └── README.md
│
├── quorum_sensing/         # Additional example
│   └── README.md
│
├── metabolic_integration/  # Additional example
│   └── README.md
│
└── statistics/             # Statistical analysis
    ├── chi_square_tests.csv
    ├── ks_tests.csv
    └── summary_statistics.csv
```

---

## Lambda Phage Data

**Source:** `workspace/projects/Biochemical-Examples/22_Lambda_Phage_Switch/`

**Original model:** `model_balanced_UV.shy`  
**Refactored model:** `model_balanced_UV_signal_hierarchy.shy`

**Simulations:**
- n=100 replicates per condition
- Duration: 3000 seconds
- Algorithm: Gillespie tau-leaping (ε=0.03)

**Conditions:**
1. ZERO initial (CI=0, Cro=0), no UV
2. BALANCED initial (CI=10, Cro=10), with UV

**Outcomes:**
- Lysogenic: [CI_Dimer] > [Cro_Dimer] at t=3000s
- Lytic: [Cro_Dimer] > [CI_Dimer] at t=3000s
- Undecided: |CI_Dimer - Cro_Dimer| < 5 mM

---

## Statistical Tests

**Chi-square test:**
- Null hypothesis: Original and refactored have same outcome distribution
- Expected result: p > 0.05 (no significant difference)

**Kolmogorov-Smirnov test:**
- Compare time course distributions
- Test for both lysogenic and lytic trajectories

---

## Data Format

**Time course files:** CSV format
```
time,CI_mRNA,CI_Protein,CI_Dimer,Cro_mRNA,Cro_Protein,Cro_Dimer,...
0.0,0.0,0.0,0.0,0.0,0.0,0.0,...
0.1,0.2,0.1,0.0,0.3,0.1,0.0,...
...
```

**Outcome files:** JSON format
```json
{
  "replicate_id": 1,
  "outcome": "lysogenic",
  "final_CI_Dimer": 87.3,
  "final_Cro_Dimer": 2.1,
  "simulation_time": 3000.0
}
```

---

## TODO

- [ ] Copy validated simulation data from lambda phage project
- [ ] Run refactored model simulations (100 replicates)
- [ ] Perform statistical comparisons
- [ ] Generate summary statistics
- [ ] Document any discrepancies
