# Lambda Phage Simulation Data

This directory contains stochastic simulation results for the lambda phage bistable switch.

## Batch Results Structure

Each subdirectory contains results from 100 stochastic simulation replicates:

### zero_no_uv/
- **Model**: Symmetric rates (ZERO balance), no UV stress
- **Result**: **Bistability** - 42% lysogenic, 48% lytic, 10% intermediate
- **Key**: Demonstrates CI-Cro symmetry produces near-equal outcomes

### zero_with_uv/
- **Model**: Symmetric rates (ZERO balance) + UV stress (RecA cleavage)
- **Result**: **Lytic bias** - 4% lysogenic, 86% lytic
- **Key**: UV stress breaks symmetry by degrading CI repressor

### balanced_with_uv/
- **Model**: Balanced rates + UV stress
- **Result**: **CI vulnerable** - 2% lysogenic, 98% lytic
- **Key**: Alternative rate configuration, CI more susceptible to UV

## Data Not Included

The actual simulation result files (100 replicates × 3 conditions = 300 files) are **not included** because:
- Large file size (~50+ MB total)
- Can be regenerated from models using SHYpn

## Reproducing Results

To regenerate the simulation data:

```bash
# Run 100 replicates for each model
shypn models/lambda_symmetric_bistable.shy --batch 100 --output data/batch_results/zero_no_uv/
shypn models/lambda_symmetric_UV.shy --batch 100 --output data/batch_results/zero_with_uv/
shypn models/lambda_balanced_UV.shy --batch 100 --output data/batch_results/balanced_with_uv/
```

## Figure Generation

Once data is generated, create all paper figures:

```bash
python scripts/generate_paper_figures.py
```

This reads from `batch_results/` and generates:
- Figure 1: Outcome distributions (pie charts)
- Figure 2: CI-Cro scatter plots (state space)
- Figure 3: Time courses (representative trajectories)
- Figure 4: Rate symmetry analysis
- Figure 5: Summary bar charts

## Paper Results

The published results showed:

| Condition | Lysogenic | Lytic | Interpretation |
|-----------|-----------|-------|----------------|
| ZERO (no UV) | 42% | 48% | Bistability from symmetry |
| ZERO + UV | 4% | 86% | UV breaks symmetry |
| BALANCED + UV | 2% | 98% | CI vulnerable configuration |
