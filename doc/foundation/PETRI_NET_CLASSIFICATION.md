# Petri Net Model Hierarchy - Where Shypn Fits

## 1. CLASSICAL PETRI NETS (Foundation - 1962)
└─ Place/Transition Nets (P/T Nets)
   - Discrete tokens
   - Integer markings
   - Synchronous firing
   └─ Applications: Manufacturing, protocols, workflows

## 2. COLORED PETRI NETS (CPNs - 1980s)
└─ Tokens carry data (colors)
   - Type system for tokens
   - More compact models
   └─ Applications: Software design, communication protocols

## 3. CONTINUOUS PETRI NETS (1987)
└─ Real-valued markings
   - Fluid approximation
   - Continuous flow
   └─ Applications: Traffic systems, production lines

## 4. STOCHASTIC PETRI NETS (SPNs - 1980s)
└─ Exponentially distributed firing times
   - Markovian dynamics
   - Performance analysis
   └─ Applications: Reliability, queueing systems

## 5. GENERALIZED STOCHASTIC PETRI NETS (GSPNs - 1984)
└─ Immediate + Timed transitions
   - Semi-Markov processes
   - More modeling power
   └─ Applications: Computer systems, manufacturing

## 6. HYBRID PETRI NETS (HPNs - 1990s)
└─ Discrete + Continuous places
   - Mixed token semantics
   - Multi-scale systems
   └─ Applications: Chemical processes, power systems

## 7. STOCHASTIC HYBRID PETRI NETS (SHPNs - 2000s)

### ★ SHYPN FITS HERE ★

**Combines:**
- Discrete places (molecules, species counts)
- Continuous places (concentrations)
- Stochastic firing (biochemical reactions)
- Deterministic transitions (mass action)
- Rate functions (Michaelis-Menten, Hill, etc.)

└─ Applications: Systems biology, biochemical pathways

## 8. SPECIALIZED EXTENSIONS
- Timed Petri Nets (deterministic delays)
- Fuzzy Petri Nets (uncertain knowledge)
- Object-Oriented Petri Nets (modularity)
- Algebraic Petri Nets (formal verification)

---

## SHYPN CHARACTERISTICS

**📊 Model Type:** Stochastic Hybrid Petri Net (SHPN)

**🔬 Domain:** Biological/Biochemical Systems Modeling

### Key Features:

#### 1. HYBRID NATURE
- Discrete tokens (molecule counts)
- Continuous concentrations (molar quantities)
- Mixed semantics in same model

#### 2. STOCHASTIC BEHAVIOR
- Gillespie algorithm for discrete reactions
- Stochastic simulation (SSA, tau-leaping)
- Probability distributions over trajectories

#### 3. KINETIC RATE FUNCTIONS
- Mass action (k * [S1] * [S2])
- Michaelis-Menten (Vmax * [S] / (Km + [S]))
- Hill equation (cooperativity)
- Custom rate laws

#### 4. BIOLOGICAL SEMANTICS
- Places = Chemical species/compounds
- Transitions = Biochemical reactions
- Arcs = Stoichiometric coefficients
- Test arcs = Catalysts/enzymes (not consumed)

#### 5. PATHWAY MODELING
- SBML import/export
- KEGG pathway integration
- Compartmentalization
- Conservation laws

---

## COMPARISON MATRIX

| Feature                | Classical | SPN | HPN | SHPN (Shypn) |
|------------------------|-----------|-----|-----|--------------|
| Discrete tokens        |     ✓     |  ✓  |  ✓  |      ✓       |
| Continuous tokens      |     ✗     |  ✗  |  ✓  |      ✓       |
| Stochastic firing      |     ✗     |  ✓  |  ✗  |      ✓       |
| Rate functions         |     ✗     |  ✗  |  ✓  |      ✓       |
| Biological semantics   |     ✗     |  ✗  |  ✗  |      ✓       |
| SBML integration       |     ✗     |  ✗  |  ✗  |      ✓       |
| Gillespie algorithm    |     ✗     |  ✗  |  ✗  |      ✓       |
| Compartments           |     ✗     |  ✗  |  ✗  |      ✓       |
| Test arcs (catalysts)  |     ✗     |  ✗  |  ✗  |      ✓       |

---

## THEORETICAL FOUNDATIONS

Shypn builds on:

### 1. Petri Net Theory (Carl Adam Petri, 1962)
└─ Concurrent systems, partial orders

### 2. Stochastic Process Theory (Gillespie, 1977)
└─ Chemical master equation, SSA

### 3. Hybrid Systems Theory (1990s)
└─ Discrete-continuous interaction

### 4. Systems Biology (2000s)
└─ SBML, pathway databases, kinetic modeling

---

## POSITIONING IN RESEARCH LANDSCAPE

### Academic Category:
- Formal Methods
- Systems Biology
- Computational Biology
- Stochastic Modeling

### Research Communities:
- Petri Net Community (Petri Net conferences)
- Systems Biology (ICSB, COMBINE)
- Computational Systems Biology
- Bioinformatics

### Similar Tools/Systems:
- **Snoopy** (Hybrid Petri Nets)
- **Cell Illustrator** (Hybrid Functional Petri Nets)
- **CPN Tools** (Colored Petri Nets)
- **Charlie** (Stochastic Petri Nets)
- **COPASI** (biochemical simulation, not PN-based)

### Unique Position:
✓ Focus on BIOLOGICAL pathways (not generic PN)  
✓ SBML/KEGG integration (standards compliance)  
✓ Biochemical rate functions (domain-specific)  
✓ Visual workflow (not just simulation engine)  
✓ Parameter enrichment (database integration)

---

## CLASSIFICATION SUMMARY

**Shypn = Stochastic Hybrid Petri Net + Biological Domain Specialization**

**Formal:** SHPN ⊂ HPN ∪ SPN ⊂ Extended Petri Nets

**Position:** Domain-Specific Modeling Tool for Systems Biology using Stochastic Hybrid Petri Net formalism
