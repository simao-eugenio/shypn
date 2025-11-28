# Example 09: Implementation Notes

## Status: ✅ IMPLEMENTED (Rate Tuning Needed)

### Completed
- [x] 15 metabolite places with normalized concentrations (0.05-5.0 mM range)
- [x] 12 transitions: T0 (glucose source), T1-T10 (10 enzymatic steps), T11 (pyruvate sink)
- [x] 48 arcs with correct connectivity
- [x] 3 curved inhibitor arcs for regulatory checkpoints:
  - A6: G6P ⊸ HK (weight=2.0 mM)
  - A15: ATP ⊸ PFK (weight=3.0 mM)
  - A47: ATP ⊸ PK (weight=3.5 mM)
- [x] 5 reversible reactions with rate_forward/rate_reverse
- [x] Source/sink transitions for pathway endpoints
- [x] JSON format corrected (source_id/target_id, proper capacity field)

### Current Simulation Behavior (t=1.0s)

**Metabolite Changes:**
- Glucose: 5.0 → 4.32 mM (consumed: 0.68 mM) ✓
- Pyruvate: 0.2 → 0.16 mM (DECREASED by 0.04 mM) ✗
- G6P: 0.8 → 0.007 mM (strongly decreased)
- ATP: 2.5 → 1.64 mM (net loss: -0.86 mM) ✗
- NADH: 0.05 → 0.056 mM (tiny gain: +0.006 mM) ✗

**Issues Identified:**
1. **Pyruvate sink too strong**: Rate=0.05 mM/s drains faster than PK produces
2. **ATP net negative**: Should be +2 per glucose, currently -0.86 (efficiency: -63%)
3. **NADH barely accumulates**: Should be +2 per glucose, only +0.006 (efficiency: 0.5%)
4. **Unbalanced pathway flux**: Upper glycolysis (HK, PFK) faster than lower (GAPDH, PK)

### Rate Constants (Current)

**Investment Phase:**
- T0 (GlcSource): 0.1 (source)
- T1 (HK): 0.5 * Glucose * ATP
- T2 (PGI): 0.3 * G6P ⇌ 0.1 * F6P
- T3 (PFK): 0.4 * F6P * ATP
- T4 (Aldolase): 0.8 * F16BP
- T5 (TPI): 1.5 * DHAP ⇌ 1.5 * G3P

**Payoff Phase:**
- T6 (GAPDH): 0.6 * G3P * NAD
- T7 (PGK): 1.0 * BPG13 * ADP ⇌ 0.05 * PG3 * ATP
- T8 (PGM): 0.5 * PG3 ⇌ 0.3 * PG2
- T9 (Enolase): 0.4 * PG2 ⇌ 0.05 * PEP
- T10 (PK): 1.2 * PEP * ADP
- T11 (PyrSink): 0.05 (sink)

### Recommended Rate Adjustments

**Priority 1 - Fix ATP Balance:**
1. Increase GAPDH rate: 0.6 → 1.2 (double NADH production)
2. Increase PGK forward rate: 1.0 → 2.0 (more ATP generation)
3. Increase PK rate: 1.2 → 1.8 (more ATP generation)

**Priority 2 - Fix Pyruvate Sink:**
4. Decrease pyruvate sink: 0.05 → 0.01 (slow constant drainage)
   - OR make sink rate depend on pyruvate concentration

**Priority 3 - Balance Upper/Lower Glycolysis:**
5. Decrease HK rate: 0.5 → 0.3 (slow glucose consumption)
6. Decrease PFK rate: 0.4 → 0.25 (bottleneck at commitment step)

### Expected Stoichiometry

For 1 molecule glucose → 2 pyruvate:
- **ATP balance**: -2 (HK, PFK) + 2 (PGK) + 2 (PK) = **+2 net**
- **NADH balance**: +2 (GAPDH x2)
- **Pyruvate**: +2

Current simulation shows pathway is active but unbalanced. With rate adjustments, should achieve proper stoichiometry.

### Testing Inhibitor Arcs

Inhibitor arcs ARE present in model (verified in JSON):
- A6: P2 (G6P) → T1 (HK), weight=2.0
- A15: P12 (ATP) → T3 (PFK), weight=3.0
- A47: P12 (ATP) → T10 (PK), weight=3.5

Test script warning is false positive - it looks for arcs by place NAME but arcs reference place OBJECTS after loading. Inhibitor functionality confirmed working in Examples 07-08.

### Next Steps

1. Adjust rate constants per recommendations above
2. Run longer simulation (t=5-10s) to reach steady state
3. Verify ATP +2 net per glucose consumed
4. Verify NADH +2 per glucose consumed
5. Test inhibitor activation when G6P or ATP exceeds thresholds
6. Document final validated parameters

### Related Examples

- **Example 07**: Reversible reactions with equilibrium (F6P ⇌ G6P)
- **Example 08**: ATP inhibitor arcs and energy sensing
- **Example 09**: Complete 10-step glycolysis (THIS FILE)
- **Example 10** (future): Glycolysis + TCA cycle integration

### Implementation Insights

**Learned from Examples 07-08:**
- Float weights for precise biological thresholds (2.5 mM ATP)
- CurvedInhibitorArc requires explicit type checking in engine
- Bidirectional arcs filtered by rate formula substrate identification
- Source/sink transitions for pathway endpoints
- Normalized concentration ranges (0.05-5.0 mM) for stability

**Critical Bug Fixed:**
- JSON capacity field must be `Infinity` (not `"Infinity"` string)
- Caused ValueError in place.set_tokens() trying int("Infinity")
- Example 08 had correct format, Example 09 Python script wrapped in quotes
- Fixed with: `sed -i 's/"capacity": "Infinity"/"capacity": Infinity/g'`

## File Structure

```
09_Complete_Glycolysis/
├── README.md                # Complete pathway specification
├── model.shy                # Petri net model (48 arcs, 15 places, 12 transitions)
└── IMPLEMENTATION_NOTES.md  # This file
```

## Model Statistics

- **Places**: 15 (11 metabolites + 4 cofactors)
- **Transitions**: 12 (1 source + 10 enzymes + 1 sink)
- **Arcs**: 48 total
  - Normal arcs: 45 (substrates + products, including bidirectional)
  - Inhibitor arcs: 3 (curved_inhibitor_arc type)
- **Reversible reactions**: 5 (PGI, TPI, PGK, PGM, Enolase)
- **Regulatory checkpoints**: 3 (HK product inhibition, PFK+PK ATP inhibition)

## Validation Checklist

- [x] Model loads without errors
- [x] All transitions have valid rate formulas
- [x] Source transition feeds glucose
- [x] Sink transition drains pyruvate  
- [x] Pathway flux observable (metabolites changing)
- [ ] ATP net balance = +2 per glucose (needs rate tuning)
- [ ] NADH balance = +2 per glucose (needs rate tuning)
- [ ] Pyruvate accumulates (needs slower sink or faster production)
- [ ] Inhibitor arcs activate at correct thresholds (validation script needs fix)
- [ ] Steady state reached within reasonable time

**Overall Progress**: 70% complete. Core structure functional, rate tuning required for correct stoichiometry.
