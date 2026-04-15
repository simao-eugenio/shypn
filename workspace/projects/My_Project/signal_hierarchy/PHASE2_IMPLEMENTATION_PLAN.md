# Phase 2 Implementation: Multi-Signal Integration

**Date Started:** December 25, 2025  
**Status:** In Progress  
**Goal:** Expand hierarchical model with metabolic and cell cycle sensors

---

## Phase 1 Achievements (Baseline)

✅ **Model:** lambda_hierarchical_v2.shy  
✅ **Compartments Implemented:**
- L0-C1A: RecA environmental sensor (DNA damage)
- L1-C2A: CII integration layer
- L2-C3: CI-Cro decision circuit

✅ **Validation Results:**
- UV depleted: 53.8% CI / 46.2% Cro (bistability preserved)
- UV cycle: 4% CI / 91% Cro (strong lytic response)
- CII integration layer functional (I(CII;CI) = 0.72 bits)

---

## Phase 2 Objectives

### 1. Metabolic Sensor Module (L0-C1B)
**Purpose:** Sense nutrient availability and metabolic stress

**Components:**
- P22: cAMP (cyclic AMP, low when glucose available)
- P23: ppGpp (stringent response, high under amino acid starvation)
- P24: Metabolic_Health (signal place, aggregates metabolic state)

**Logic:**
- High glucose → low cAMP → metabolic health good
- Amino acid starvation → high ppGpp → metabolic stress
- Metabolic_Health = f(cAMP, ppGpp) → affects CII stability

**Rate Parameters:**
- cAMP production: 2.0 (basal), inhibited by glucose
- ppGpp production: 1.0 (basal), increased by starvation
- Metabolic_Health calculation: (1 - ppGpp/10) * (1 + cAMP/5)

### 2. Cell Cycle Sensor Module (L0-C1C)
**Purpose:** Sense cell replication and division state

**Components:**
- P25: DnaA (replication initiator, high at cell birth)
- P26: FtsZ (division ring protein, high before division)
- P27: Cell_Cycle_Phase (signal place, early/mid/late cycle)

**Logic:**
- High DnaA → early cell cycle → favor lysogeny (integrate early)
- High FtsZ → late cell cycle → favor lysis (maximize progeny)

**Rate Parameters:**
- DnaA production: 3.0 initially, decays to 0.5
- FtsZ production: starts low (0.5), ramps to 3.0
- Cell_Cycle_Phase = DnaA / (DnaA + FtsZ + 1)

### 3. Enhanced CII Stability Control (L1-C2A)
**Purpose:** Make CII integration responsive to metabolic and stress signals

**New Components:**
- P28: CIII Protein (protease inhibitor)
- Modified T31 (CII_Degradation): rate depends on metabolic health and CIII

**Logic:**
- Good metabolism + high CIII → CII stable → lysogeny favored
- Poor metabolism or high RecA → CII unstable → lysis favored

**Rate Parameters:**
- CIII synthesis: 2.0 * Metabolic_Health
- CII degradation: base_rate * (1 - CIII/10) * (1 + RecA/50)

### 4. CI Cleavage Module (L1-C2B)
**Purpose:** RecA-dependent CI inactivation (DNA damage response)

**Components:**
- Split P3 (CI Monomer) → P3a (CI_Intact), P3b (CI_Cleaved)
- T32: CI_Cleavage (RecA-dependent)
- Modified T4 (CI_Dimerization): only uses CI_Intact

**Logic:**
- High RecA → CI cleavage → less CI dimer → lytic switch
- This is the primary UV-induced lytic mechanism

**Rate Parameters:**
- CI cleavage: 0.05 * RecA (RecA-dependent proteolysis)
- CI_Intact dimerization: uses only intact monomers

---

## Implementation Steps

### Step 1: Metabolic Sensor Module (Priority 1)
- [x] Add P22 (cAMP), P23 (ppGpp), P24 (Metabolic_Health)
- [x] Add transitions for cAMP/ppGpp dynamics
- [x] Mark P24 as signal place (blue hexagon)
- [ ] Test: Run with constant metabolic health = 1.0 (neutral)

### Step 2: Cell Cycle Sensor Module (Priority 2)
- [x] Add P25 (DnaA), P26 (FtsZ), P27 (Cell_Cycle_Phase)
- [x] Add transitions for DnaA/FtsZ dynamics
- [x] Mark P27 as signal place
- [ ] Test: Run with constant cell cycle phase = 0.5 (mid-cycle)

### Step 3: CIII Protease Inhibitor (Priority 1)
- [x] Add P28 (CIII Protein)
- [x] Add T33 (CIII_Synthesis), T34 (CIII_Degradation)
- [x] Modify T31 (CII_Degradation) to include CIII inhibition
- [ ] Test: Verify CII stability increases with CIII

### Step 4: CI Cleavage Mechanism (Priority 1)
- [x] Split P3 → P3a (CI_Intact), P3b (CI_Cleaved)
- [x] Add T32 (CI_Cleavage) with RecA-dependent rate
- [x] Modify T4 (CI_Dimerization) to use only P3a (already connects to P3)
- [x] T2 (CI_Translation) produces P3 (CI_Intact)
- [ ] Test: High RecA → CI cleavage → lytic bias

**Status: Steps 1-4 COMPLETE (December 25, 2025)**
- Model lambda_hierarchical_v3.shy created with 23 places, 28 transitions, 54 arcs
- All new modules implemented
- Ready for testing

### Step 5: Multi-Signal Integration Testing
- [ ] Run batch with all sensors at neutral values (baseline)
- [ ] Run batch with good metabolism (high cAMP, low ppGpp)
- [ ] Run batch with poor metabolism (low cAMP, high ppGpp)
- [ ] Run batch with early cell cycle (high DnaA)
- [ ] Run batch with late cell cycle (high FtsZ)
- [ ] Run batch with UV + good metabolism (conflicting signals)
- [ ] Run batch with UV + poor metabolism (synergistic signals)

### Step 6: Information Flow Analysis
- [ ] Calculate I(Metabolic_Health; Decision)
- [ ] Calculate I(Cell_Cycle_Phase; Decision)
- [ ] Calculate I(RecA; Decision) with all sensors active
- [ ] Calculate multi-information I(RecA, Metabolic, CellCycle; Decision)
- [ ] Compare with Phase 1 single-signal results

---

## Model Structure (Phase 2 Complete)

**Total Places:** ~28-30
- Layer 0: 9-10 places (RecA, Metabolic, Cell Cycle sensors)
- Layer 1: 6-8 places (CII, CIII, CI_Intact, CI_Cleaved)
- Layer 2: 8 places (existing CI-Cro circuit)
- Layer 3: 4-6 places (effector modules, future)

**Total Transitions:** ~35-40
- Layer 0: 8-10 (sensor dynamics)
- Layer 1: 8-10 (integration dynamics)
- Layer 2: 17 (existing decision circuit)
- Layer 3: 4-6 (effector modules, future)

**Signal Places (blue hexagons):**
- P14: RecA_Active
- P21: CII_Protein
- P24: Metabolic_Health (NEW)
- P27: Cell_Cycle_Phase (NEW)
- P7: CI_Dimer
- P8: Cro_Dimer

---

## Expected Outcomes

### Metabolic Effects
- **Good metabolism:** ~70% lysogenic (CII stable)
- **Poor metabolism:** ~70% lytic (CII degraded)

### Cell Cycle Effects
- **Early cycle:** ~65% lysogenic (favorable for integration)
- **Late cycle:** ~55% lytic (maximize progeny before division)

### Multi-Signal Integration
- **UV + good metabolism:** ~80% lytic (UV overrides metabolism)
- **UV + poor metabolism:** ~95% lytic (synergistic lytic signals)
- **No UV + good metabolism:** ~70% lysogenic (optimal for prophage)
- **No UV + poor metabolism:** ~60% lytic (escape stressed host)

### Information Flow
- **Single signals:** I(signal; decision) ≈ 0.1-0.3 bits each
- **Combined signals:** I(all; decision) ≈ 0.8-1.0 bits
- **Synergy test:** I(RecA,Meta,CellCycle; Decision) > sum of individual I values

---

## Validation Metrics

### Behavioral Tests
✓ Bistability preserved under neutral conditions (p > 0.05 vs Phase 1)  
✓ Metabolic stress shifts toward lysis (>60% Cro)  
✓ Good metabolism shifts toward lysogeny (>60% CI)  
✓ UV overrides metabolic signals (>80% lytic even with good metabolism)

### Information Theory Tests
✓ I(Meta; Decision) > 0 (metabolic signals carry information)  
✓ I(CellCycle; Decision) > 0 (cell cycle signals carry information)  
✓ I(RecA,Meta; Decision) > I(RecA; Decision) (multi-signal integration adds information)  
✓ Synergy: I(all; Decision) > Σ I(individual; Decision)

### Structural Tests
✓ 3 environmental sensors identifiable  
✓ CII stability visibly affected by metabolic health  
✓ CI cleavage mechanism functional (RecA-dependent)  
✓ Signal hierarchy clear: Environment → Integration → Decision

---

## Timeline

**Day 1 (Dec 25):** Steps 1-2 (Metabolic + Cell Cycle sensors)  
**Day 2 (Dec 26):** Steps 3-4 (CIII + CI cleavage)  
**Day 3 (Dec 27):** Step 5 (Multi-signal testing)  
**Day 4 (Dec 28):** Step 6 (Information flow analysis)  
**Day 5 (Dec 29):** Figure generation and documentation  

---

## Deliverables

### Model Files
- **lambda_hierarchical_v3.shy** - Complete Phase 2 model with all sensors

### Analysis Scripts
- **analyze_metabolic_response.py** - Metabolic stress vs lysogeny
- **analyze_cell_cycle_effects.py** - Cell cycle phase vs outcome
- **analyze_multi_signal_integration.py** - Combined signal information flow

### Figures
- **metabolic_response.png** - CII stability vs metabolic health
- **cell_cycle_effects.png** - Outcome distribution by cell cycle phase
- **multi_signal_phase_portrait.png** - 3D phase space (RecA, Meta, CellCycle)
- **information_flow_multi_signal.png** - Extended hierarchy with all sensors

### Documentation
- **PHASE2_PROGRESS.md** - Implementation tracking and results
- **PHASE2_COMPLETE_SUMMARY.md** - Final results and validation

---

## Success Criteria

✅ **Multi-sensor integration functional** - 3 environmental sensors operational  
✅ **Signal hierarchy preserved** - Information bottlenecks at layer boundaries  
✅ **Biological realism** - Metabolic/cell cycle effects match literature  
✅ **Synergistic processing** - Multi-signal information exceeds sum of parts  
✅ **Environmental override** - UV signal dominates conflicting signals  

---

**Status:** Ready to begin  
**Next Action:** Implement Step 1 (Metabolic Sensor Module)
