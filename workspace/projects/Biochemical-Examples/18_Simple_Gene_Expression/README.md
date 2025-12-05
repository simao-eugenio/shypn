# Simple Gene Expression Model

**Model Type:** Stochastic Gene Expression  
**Category:** Biochemical Networks  
**Complexity:** Simple (4 transitions, 3 places)

## Description

This model demonstrates basic stochastic gene expression with:
- **Transcription:** Gene produces mRNA
- **Translation:** mRNA produces Protein
- **Degradation:** Both mRNA and Protein degrade over time

All transitions are **stochastic** with rate formulas that depend on molecule counts.

## Model Structure

### Places
- **Gene** (1 molecule) - Template for transcription (constant)
- **mRNA** (0 initial) - Messenger RNA transcripts
- **Protein** (0 initial) - Translated proteins

### Transitions (All Stochastic)
1. **Transcription** - Rate: 0.5 (constant production)
2. **Translation** - Rate: 2.0 × mRNA (proportional to mRNA count)
3. **mRNA Degradation** - Rate: 0.1 × mRNA (first-order decay)
4. **Protein Degradation** - Rate: 0.05 × Protein (first-order decay)

## Expected Behavior

- **mRNA** reaches steady state ~5 molecules (production rate / degradation rate = 0.5/0.1)
- **Protein** reaches steady state ~200 molecules (2.0 × 5 / 0.05)
- **Stochastic fluctuations** around steady state due to discrete molecule counts
- **Burst dynamics** possible with τ-leaping algorithm

## Simulation Settings

**Recommended:**
- Duration: 100 time units
- Enable τ-leaping: Yes (for faster simulation)
- Enable parallel: Yes (for multi-transition models)

**Key Metrics:**
- mRNA half-life: ~7 time units (ln(2)/0.1)
- Protein half-life: ~14 time units (ln(2)/0.05)

## Biological Relevance

This represents the central dogma of molecular biology in its simplest stochastic form:
```
DNA → RNA → Protein
```

The model captures:
- **Transcriptional bursts** (discrete mRNA production events)
- **Translation amplification** (each mRNA produces multiple proteins)
- **Molecular noise** (stochastic fluctuations in low-copy molecules)

## Testing τ-Leaping

This model is ideal for testing the τ-leaping algorithm because:
1. All transitions are stochastic (no continuous/timed interference)
2. Rate formulas are simple (linear dependencies)
3. Weak independence structure allows parallel sampling
4. Observable steady-state behavior for validation

## Notes

- Gene uses a **test arc** (catalyst) - not consumed during transcription
- mRNA uses a **test arc** for translation - template mechanism
- Degradation reactions consume their substrates
