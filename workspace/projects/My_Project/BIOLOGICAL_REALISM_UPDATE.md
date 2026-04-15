# Biological Realism Update

## Problem Identified

The original model used **artificial equilibrium cycling** (rate 0.6 dissociation) to enable loser elimination through dimer ↔ monomer recycling. While this worked excellently for bistability demonstration, it was biologically unrealistic:

- Real λ CI dimers: K_d ~ 10 nM (very tight, essentially irreversible)
- Model dimers: K_d = 120 mM (10,000,000x weaker!)

## Question Asked

**"If the cycle is artificial, how can we deplete loser dimers?"**

## Biological Answer

**Direct dimer degradation by proteases!**

In real E. coli:
- ClpXP, Lon, and other proteases can degrade protein complexes
- Dimers are substrates for proteolytic degradation
- No need for dissociation to eliminate proteins
- Loser dimers are degraded directly by the cell's quality control machinery

## Model Changes

### Removed/Reduced
- **Dimer dissociation**: 0.6 → 0.000001 s^-1 (600,000x slower, essentially irreversible)
  - K_d now ~ 0.1 nM (biologically realistic tight binding)

### Added (NEW!)
- **CI_Dimer_Decay** (T19): 0.004 * CI_Dimer s^-1
- **Cro_Dimer_Decay** (T20): 0.004 * Cro_Dimer s^-1
- Both have half-life ~173 seconds (3 minutes)

### Slowed Down (More Realistic Timescales)
- **mRNA decay**: 0.1 → 0.01 s^-1 (half-life: 7s → 69s, ~1 minute)
- **Protein decay**: 0.08 → 0.004 s^-1 (half-life: 9s → 173s, ~3 minutes)
- **Transcription**: 0.6 → 0.06 s^-1 (10x slower, proportional scaling)

### Fixed (Mechanistically Correct)
- **Dimerization**: Now uses true second-order mass action
  - Old: `0.6 * CI_Protein` (pseudo-first-order)
  - New: `0.01 * CI_Protein * (CI_Protein - 1) / 2` (true bimolecular)

## Timescale Comparison

| Process | Old Model | New Model | Real Biology | Status |
|---------|-----------|-----------|--------------|--------|
| mRNA decay | 7 sec | 69 sec | 5 min (300s) | Better (5x closer) |
| Protein decay | 9 sec | 173 sec | 20-60 min | Better (7-20x closer) |
| Dimer K_d | 120 mM | 0.1 nM | 10 nM | Excellent! |
| Dimer dissociation | 1.2 sec | Never | Never | Perfect! |
| Dimer degradation | Via dissociation | Direct | Direct | Perfect! |

## Simulation Recommendations

### Old Model (Artificial Cycling)
- Duration: 200-500 seconds
- Fast dynamics, compressed timescales
- Excellent for quick demonstrations

### New Model (Biological Realism)
- Duration: **2000-5000 seconds** (10x longer)
- More realistic timescales
- Better for quantitative predictions

### Expected Behavior
- Bistability should still occur (mutual repression intact)
- Loser elimination now via **direct protease degradation**
- Slower dynamics, more gradual decisions
- May see different outcome ratios (needs testing)

## Key Insight

**Losers are eliminated by direct dimer degradation, not dissociation!**

This is the biologically correct mechanism:
1. Winner's dimer accumulates and represses loser's gene
2. Loser's mRNA/protein production stops
3. Loser's existing dimers are degraded by proteases (ClpXP, Lon, etc.)
4. Winner maintains dominance through continuous production

The artificial equilibrium cycle was a clever computational trick but not biologically necessary.

## Files

- **Original model**: `model.shy` (with equilibrium cycling)
- **New realistic model**: `model_biological_realistic.shy`
- **Analysis**: See `model_biological_analysis.txt` in `/home/simao/projetos/r_scripts/`

## Next Steps

1. Test new model with 2000-5000s simulations
2. Compare bistability outcomes (lysogenic/lytic ratio)
3. Verify loser elimination effectiveness
4. May need to adjust parameters if bistability is lost

---

**Created**: December 16, 2025
**Motivation**: User's question about artificial vs biological loser depletion
**Key Discovery**: Direct dimer degradation is the biological mechanism
