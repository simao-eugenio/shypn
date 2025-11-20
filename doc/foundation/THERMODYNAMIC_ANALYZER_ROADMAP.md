# Thermodynamic Feasibility Analyzer - Implementation Roadmap

**Status**: ⚙️ BASIC IMPLEMENTATION COMPLETE (Phase 1)  
**Date**: November 20, 2025  
**File**: `src/shypn/topology/biological/thermodynamics.py`

---

## Overview

The Thermodynamic Feasibility Analyzer validates biochemical reactions against thermodynamic principles, ensuring that modeled pathways are energetically feasible and properly coupled.

---

## Current Implementation (Phase 1: Heuristic Checks) ✅

### Capabilities

1. **Reversibility Consistency Checks**
   - Detects mismatches between configured reversibility and likely thermodynamics
   - Uses heuristic keywords (kinase, isomerase, etc.)
   - Identifies reactions that should/shouldn't be reversible

2. **ATP Coupling Detection**
   - Identifies biosynthetic reactions lacking energy input
   - Checks for ATP/GTP coupling in unfavorable reactions
   - Suggests ATP coupling for energy-requiring processes

3. **Futile Cycle Identification**
   - Detects cycles that consume ATP without net product
   - Warns about potential energy-wasting loops
   - Validates biological function of cycles

4. **Equilibrium State Detection**
   - Identifies reactions likely operating near equilibrium (ΔG ≈ 0)
   - Flags isomerases, mutases, and other near-equilibrium enzymes
   - Explains normal flux behavior at equilibrium

5. **Energy Flow Analysis**
   - Counts ATP-producing vs ATP-consuming reactions
   - Checks overall energy balance in network
   - Identifies energy imbalances

### Limitations

- **Heuristic-based**: Uses pattern matching, not actual thermodynamic calculations
- **No ΔG°' values**: Cannot compute actual Gibbs free energy
- **No concentration dependence**: Cannot calculate ΔG from Q (reaction quotient)
- **Limited compound recognition**: Uses hardcoded lists of high/low energy compounds
- **No pH/temperature corrections**: Assumes standard conditions

### Output Format

```
==============================================
THERMODYNAMIC FEASIBILITY ANALYSIS
==============================================

⚠️  BASIC IMPLEMENTATION - Heuristic checks only
🔮 FUTURE: Full ΔG°' calculations with compound database

SUMMARY
----------------------------------------------
Total transitions analyzed: 12
Issues found: 0 errors, 2 warnings, 3 info

⚠️  WARNINGS (Potential issues)
----------------------------------------------
  • Biosynthetic reaction 'Glucose-6-phosphate synthesis' lacks ATP/GTP coupling
    → Consider adding ATP → ADP coupling for unfavorable biosynthetic reactions

ℹ️  INFORMATION
----------------------------------------------
  • Reaction 'Glucose-6-phosphate isomerase' likely operates near equilibrium (ΔG ≈ 0)
    → Near-equilibrium reactions are normal, flux depends on substrate/product concentrations
  • Energy flow: 3 ATP-producing, 5 ATP-consuming reactions
```

---

## Future Implementation (Phase 2: Full Thermodynamic Calculations) 🔮

### Required Dependencies

#### 1. Chemical Databases

**ChEBI (Chemical Entities of Biological Interest)**
- **Purpose**: Compound metadata, formulas, charges
- **Access**: REST API (https://www.ebi.ac.uk/chebi/)
- **Python Library**: `libchebipy`
- **Data**: Compound IDs, names, formulas, structures

**MetaCyc / BioCyc**
- **Purpose**: Reaction database with thermodynamic data
- **Access**: File downloads or web services
- **Data**: Reaction definitions, ΔG°' values, cofactors

**KEGG Compound Database**
- **Purpose**: Metabolite identifiers and cross-references
- **Access**: REST API (already integrated in SHYPN)
- **Data**: Compound IDs, names, pathways

#### 2. Thermodynamic Calculation Tools

**eQuilibrator API**
- **Purpose**: Calculate ΔG°' for biochemical reactions
- **Python Library**: `equilibrator-api`
- **Install**: `pip install equilibrator-api`
- **Features**:
  - Component contribution method (Noor et al. 2013)
  - Group contribution estimation for missing compounds
  - pH and ionic strength corrections
  - Pseudoisomer handling (protonation states)
  - Uncertainty quantification

**Example Usage**:
```python
from equilibrator_api import ComponentContribution

cc = ComponentContribution()
reaction = cc.parse_reaction_formula("glucose + ATP = glucose-6-phosphate + ADP")
dG_prime = cc.standard_dg_prime(reaction, pH=7.4, ionic_strength=0.25)
print(f"ΔG°' = {dG_prime:.2f} kJ/mol")
```

#### 3. Required Python Packages

```bash
# Install full thermodynamic analysis dependencies
pip install equilibrator-api  # eQuilibrator thermodynamics
pip install libchebipy        # ChEBI compound database
pip install python-libsbml    # SBML parsing (already installed)
pip install numpy scipy       # Scientific computing (already installed)
```

### Enhanced Capabilities (Phase 2)

#### 1. Standard Gibbs Free Energy (ΔG°')

```python
def calculate_standard_dg_prime(self, transition) -> float:
    """Calculate ΔG°' for a reaction at pH 7, 25°C, 1M concentrations.
    
    Uses eQuilibrator component contribution method.
    """
    # Get reactants and products from transition
    reactants = self._get_compound_ids(transition, is_reactant=True)
    products = self._get_compound_ids(transition, is_reactant=False)
    
    # Build reaction formula
    formula = self._build_reaction_formula(reactants, products)
    
    # Calculate using eQuilibrator
    reaction = self.component_contribution.parse_reaction_formula(formula)
    dg_prime = self.component_contribution.standard_dg_prime(
        reaction,
        pH=self.pH,
        ionic_strength=self.ionic_strength,
        temperature=self.temperature
    )
    
    return dg_prime.value  # kJ/mol
```

#### 2. Concentration-Dependent ΔG

```python
def calculate_physiological_dg(self, transition, concentrations: dict) -> float:
    """Calculate ΔG at physiological concentrations.
    
    ΔG = ΔG°' + RT ln(Q)
    where Q = [products]/[reactants]
    """
    dg_prime = self.calculate_standard_dg_prime(transition)
    
    # Calculate reaction quotient Q
    Q = self._calculate_reaction_quotient(transition, concentrations)
    
    # ΔG = ΔG°' + RT ln(Q)
    R = 8.314  # J/(mol·K)
    T = self.temperature + 273.15  # Convert °C to K
    dg = dg_prime + (R * T * np.log(Q)) / 1000  # kJ/mol
    
    return dg
```

#### 3. Thermodynamic Feasibility Validation

```python
def validate_reaction_direction(self, transition) -> dict:
    """Validate if reaction direction is thermodynamically favorable.
    
    Returns:
        dict with thermodynamic properties:
        - dg_prime: ΔG°' (kJ/mol)
        - dg: ΔG at current concentrations (kJ/mol)
        - keq: Equilibrium constant
        - favorable: bool (ΔG < 0)
        - reversible: bool (|ΔG| < threshold)
    """
    dg_prime = self.calculate_standard_dg_prime(transition)
    concentrations = self._get_current_concentrations()
    dg = self.calculate_physiological_dg(transition, concentrations)
    
    # Calculate equilibrium constant: ΔG°' = -RT ln(Keq)
    R = 8.314  # J/(mol·K)
    T = self.temperature + 273.15
    keq = np.exp(-dg_prime * 1000 / (R * T))
    
    # Determine favorability
    # ΔG < -5 kJ/mol: strongly favorable
    # -5 < ΔG < +5 kJ/mol: near equilibrium (reversible)
    # ΔG > +5 kJ/mol: unfavorable (needs coupling)
    
    return {
        'dg_prime': dg_prime,
        'dg': dg,
        'keq': keq,
        'favorable': dg < -5,
        'reversible': -5 <= dg <= 5,
        'needs_coupling': dg > 5
    }
```

#### 4. ATP Coupling Validation

```python
def validate_atp_coupling(self, transition) -> dict:
    """Check if ATP coupling is sufficient to drive unfavorable reaction.
    
    For reaction: A → B (ΔG > 0, unfavorable)
    Coupled with: ATP → ADP + Pi (ΔG ≈ -30 kJ/mol)
    Net: A + ATP → B + ADP + Pi (ΔG_net = ΔG_rxn + ΔG_ATP)
    
    Favorable if: ΔG_net < 0
    """
    # Get ΔG for main reaction
    dg_rxn = self.calculate_standard_dg_prime(transition)
    
    # Check if ATP is involved
    has_atp = self._has_compound(transition, 'ATP', is_reactant=True)
    has_adp = self._has_compound(transition, 'ADP', is_reactant=False)
    
    if not (has_atp and has_adp):
        return {'coupled': False, 'sufficient': False}
    
    # ΔG for ATP hydrolysis ≈ -30 kJ/mol (cellular conditions)
    dg_atp_hydrolysis = -30.5  # kJ/mol
    
    # Net ΔG
    dg_net = dg_rxn + dg_atp_hydrolysis
    
    return {
        'coupled': True,
        'dg_reaction': dg_rxn,
        'dg_atp': dg_atp_hydrolysis,
        'dg_net': dg_net,
        'sufficient': dg_net < 0
    }
```

#### 5. Pathway Thermodynamic Analysis

```python
def analyze_pathway_thermodynamics(self, pathway_transitions: list) -> dict:
    """Analyze thermodynamics of entire pathway.
    
    Calculates:
    - Total ΔG for pathway
    - Rate-limiting steps (highest ΔG)
    - Thermodynamic bottlenecks
    - Overall feasibility
    """
    pathway_dg = 0
    steps = []
    
    for transition in pathway_transitions:
        dg = self.calculate_standard_dg_prime(transition)
        pathway_dg += dg
        steps.append({
            'transition_id': transition.id,
            'label': transition.label,
            'dg': dg,
            'favorable': dg < -5
        })
    
    # Find rate-limiting step (most unfavorable)
    bottleneck = max(steps, key=lambda x: x['dg'])
    
    return {
        'pathway_dg_total': pathway_dg,
        'pathway_favorable': pathway_dg < 0,
        'steps': steps,
        'bottleneck': bottleneck,
        'num_unfavorable': len([s for s in steps if not s['favorable']])
    }
```

### Enhanced Output Format (Phase 2)

```
==============================================
THERMODYNAMIC FEASIBILITY ANALYSIS
==============================================

✅ FULL IMPLEMENTATION - Quantitative ΔG calculations
📊 Database: ChEBI + eQuilibrator

SUMMARY
----------------------------------------------
Total transitions analyzed: 12
Thermodynamically favorable: 8 (67%)
Near equilibrium: 3 (25%)
Unfavorable (need coupling): 1 (8%)

REACTION THERMODYNAMICS
----------------------------------------------
T1: Hexokinase (Glucose + ATP → G6P + ADP)
  ΔG°' (pH 7.4, 25°C): -16.7 kJ/mol
  ΔG (physiological): -33.5 kJ/mol
  Keq: 2.0 × 10³
  Status: ✅ FAVORABLE (irreversible)
  Coupling: ATP hydrolysis sufficient

T5: Phosphoglucose isomerase (G6P ⇌ F6P)
  ΔG°' (pH 7.4, 25°C): +1.7 kJ/mol
  ΔG (physiological): -0.6 kJ/mol
  Keq: 0.50
  Status: ⚖️ NEAR EQUILIBRIUM (reversible)

T8: Hypothetical synthesis (A → B)
  ΔG°' (pH 7.4, 25°C): +25.3 kJ/mol
  ΔG (physiological): +18.2 kJ/mol
  Status: ❌ UNFAVORABLE (needs coupling)
  ⚠️ WARNING: No ATP coupling detected
  → Suggestion: Add ATP → ADP coupling

PATHWAY ANALYSIS
----------------------------------------------
Glycolysis (Glucose → 2 Pyruvate):
  Total ΔG°': -73.3 kJ/mol
  Overall: ✅ FAVORABLE
  Bottleneck: T3 (Phosphofructokinase, ΔG = -14.2 kJ/mol)
  Unfavorable steps: 0/10

ENERGY BALANCE
----------------------------------------------
ATP produced: 4 (T7, T10)
ATP consumed: 2 (T1, T3)
Net ATP: +2 per glucose
Energy yield: -146.6 kJ/mol glucose
```

---

## Implementation Phases

### Phase 1: Heuristic Checks (COMPLETED ✅)
- Basic pattern matching
- Reversibility heuristics
- ATP coupling detection (keyword-based)
- Futile cycle detection
- Energy flow analysis

**Dependencies**: None (pure Python)  
**Status**: ✅ Implemented (November 20, 2025)

### Phase 2: Database Integration (FUTURE)
- Integrate ChEBI compound database
- Map place labels to ChEBI IDs
- Fetch chemical formulas and charges
- Cross-reference with KEGG compounds

**Dependencies**: `libchebipy`  
**Estimated effort**: 2-3 weeks

### Phase 3: ΔG°' Calculations (FUTURE)
- Integrate eQuilibrator API
- Calculate standard Gibbs free energy
- Handle pH and ionic strength corrections
- Pseudoisomer handling
- Group contribution for missing compounds

**Dependencies**: `equilibrator-api`  
**Estimated effort**: 3-4 weeks

### Phase 4: Concentration-Dependent ΔG (FUTURE)
- Get concentrations from marking
- Calculate reaction quotient Q
- Compute physiological ΔG
- Validate against known cellular concentrations

**Dependencies**: Simulation results  
**Estimated effort**: 2 weeks

### Phase 5: Pathway Analysis (FUTURE)
- Multi-reaction thermodynamic analysis
- Identify thermodynamic bottlenecks
- Validate pathway feasibility
- Suggest optimal flux distributions

**Dependencies**: Path detection tools  
**Estimated effort**: 2-3 weeks

---

## Scientific References

1. **Component Contribution Method**:
   - Noor, E. et al. (2013). "Consistent estimation of Gibbs energy using component contributions." *PLoS Computational Biology* 9(7): e1003098.
   - DOI: 10.1371/journal.pcbi.1003098

2. **eQuilibrator**:
   - Beber, M. E. et al. (2021). "eQuilibrator 3.0: a database of thermodynamic parameters for biochemical reactions." *Nucleic Acids Research* 50(D1): D603-D609.
   - URL: http://equilibrator.weizmann.ac.il/

3. **Biochemical Thermodynamics**:
   - Alberty, R. A. (2003). *Thermodynamics of Biochemical Reactions*. Wiley-Interscience.
   - Standard reference for biochemical thermodynamics

4. **Metabolic Pathway Thermodynamics**:
   - Beard, D. A. & Qian, H. (2008). *Chemical Biophysics: Quantitative Analysis of Cellular Systems*. Cambridge University Press.
   - Chapter 5: Thermodynamics of biochemical networks

5. **ChEBI Database**:
   - Hastings, J. et al. (2016). "ChEBI in 2016: Improved services and an expanding collection of metabolites." *Nucleic Acids Research* 44(D1): D1214-D1219.
   - DOI: 10.1093/nar/gkv1031

---

## Example Use Cases

### Use Case 1: Validate Model 15 (Enzyme Competition)

**Current (Phase 1)**:
```python
from shypn.topology.biological import ThermodynamicAnalyzer

analyzer = ThermodynamicAnalyzer(model)
result = analyzer.analyze()
print(result.report)
```

**Future (Phase 2+)**:
```python
# Get quantitative ΔG values
result = analyzer.analyze()
for transition_id, thermo in result.data['reaction_data'].items():
    print(f"{transition_id}: ΔG°' = {thermo['dg_prime']:.1f} kJ/mol")
    if thermo['unfavorable']:
        print(f"  ⚠️ Needs coupling: ΔG = {thermo['dg']:.1f} kJ/mol")
```

### Use Case 2: Glycolysis Pathway Analysis

**Future (Phase 5)**:
```python
# Analyze complete glycolysis pathway
glycolysis_transitions = model.get_pathway_transitions('glycolysis')
pathway_result = analyzer.analyze_pathway_thermodynamics(glycolysis_transitions)

print(f"Pathway ΔG: {pathway_result['pathway_dg_total']:.1f} kJ/mol")
print(f"Bottleneck: {pathway_result['bottleneck']['label']}")
print(f"ΔG (bottleneck): {pathway_result['bottleneck']['dg']:.1f} kJ/mol")
```

---

## Summary

**Current Status**: Basic thermodynamic analyzer is functional and provides useful heuristic-based checks for model validation.

**Future Work**: Full quantitative thermodynamic analysis requires integration with chemical databases (ChEBI, eQuilibrator) but will provide gold-standard validation of biochemical pathway models.

**Recommendation**: The basic implementation is sufficient for most modeling needs. Implement Phase 2+ when:
1. Models require quantitative ΔG validation
2. Working with novel/synthetic pathways
3. Optimizing pathway engineering designs
4. Publishing biochemical modeling research

**Total Estimated Effort for Full Implementation**: 10-15 weeks (including testing and validation)
