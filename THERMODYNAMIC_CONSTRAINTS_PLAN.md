# Thermodynamic Constraints Implementation Plan
## Gibbs Free Energy Validation for Biochemical Networks

**Branch**: `Thermodynamic-Constraints-Gibbs-Free-Energy`  
**Status**: Planning Phase  
**Prerequisites**: ✅ Skellam distribution for reversible reactions (v0.3.0)

---

## 1. Overview

### Objective
Implement thermodynamic feasibility constraints using Gibbs free energy (ΔG) calculations to validate biochemical reaction networks. Ensure rate constants are consistent with equilibrium constants derived from thermodynamics.

### Scientific Foundation

**Gibbs Free Energy Relationship**:
```
ΔG = ΔG° + RT ln(Q)
```
where:
- **ΔG°**: Standard Gibbs free energy change (kJ/mol)
- **R**: Gas constant (8.314 J/(mol·K))
- **T**: Temperature (K)
- **Q**: Reaction quotient ([products]/[reactants])

**Equilibrium Constant**:
```
K_eq = e^(-ΔG°/RT)
```

**Thermodynamic Consistency Check**:
For reversible reaction: A ⇌ B with forward rate k_f and reverse rate k_r:
```
k_f / k_r ≈ K_eq
```

### Why This Matters

1. **Physical Realism**: Models should respect thermodynamic laws
2. **Equilibrium Validation**: Rate ratios must match experimental thermodynamics
3. **Feasibility**: Reactions with positive ΔG shouldn't proceed spontaneously
4. **Integration with Skellam**: Validates forward/reverse rate pairs in reversible reactions

---

## 2. Architecture Design

### Module Structure
```
src/shypn/thermodynamics/
├── __init__.py                      # Package exports, version 0.1.0
├── gibbs_calculator.py              # Core ΔG calculations
├── equilibrium_validator.py         # K_eq vs rate ratio validation
├── database_interface.py            # Biochemical database API client
├── compound_resolver.py             # Compound ID mapping (KEGG ↔ ChEBI)
├── thermodynamic_corrector.py       # pH, temperature, ionic strength corrections
└── data/
    ├── compound_gibbs.json          # Local cache of ΔG°_f values
    └── reaction_gibbs.json          # Local cache of ΔG°_r values
```

### Integration Points

**SBML/KEGG Import Pipeline**:
```
SBML/KEGG → pathway_converter.py → thermodynamic_validator
                                         ↓
                              ValidationIssue (thermodynamic)
```

**Simulation Initialization**:
```
Simulation.setup() → check_thermodynamic_feasibility()
                          ↓
                     Warnings for ΔG violations
```

**Skellam Integration**:
```
τ-leaping engine detects reversible → validate K_eq = k_f/k_r
                                            ↓
                                   Log thermodynamic consistency
```

---

## 3. Implementation Phases

### Phase 1: Core Gibbs Free Energy Calculator (Week 1)

**File**: `gibbs_calculator.py`

**Key Classes**:
```python
@dataclass
class CompoundThermodynamics:
    """Thermodynamic properties of a biochemical compound."""
    compound_id: str           # KEGG/ChEBI ID
    name: str
    delta_g_formation: float   # ΔG°_f (kJ/mol)
    source: str                # Database source
    uncertainty: float         # Experimental error (kJ/mol)
    conditions: dict           # pH, T, ionic strength

@dataclass
class ReactionThermodynamics:
    """Thermodynamic properties of a biochemical reaction."""
    reaction_id: str
    delta_g_standard: float    # ΔG°_r (kJ/mol)
    delta_g_prime: float       # ΔG'° (biochemical standard, pH 7)
    k_eq: float                # Equilibrium constant
    temperature: float         # Kelvin
    ph: float
    ionic_strength: float      # M

class GibbsCalculator:
    """Calculate Gibbs free energy changes for biochemical reactions."""
    
    def calculate_delta_g_reaction(
        self,
        reactants: dict[str, float],  # {compound_id: stoichiometry}
        products: dict[str, float],
        concentrations: dict[str, float] = None,  # Current [M]
        temperature: float = 298.15,
        ph: float = 7.0
    ) -> ReactionThermodynamics:
        """Calculate ΔG for a reaction.
        
        Steps:
        1. Get ΔG°_f for all compounds from database
        2. Calculate ΔG°_r = Σ(ν_products·ΔG°_f) - Σ(ν_reactants·ΔG°_f)
        3. Apply biochemical corrections (ΔG'°)
        4. Calculate K_eq = e^(-ΔG°/RT)
        5. If concentrations given: ΔG = ΔG° + RT ln(Q)
        """
        pass
    
    def calculate_k_eq(self, delta_g_standard: float, temperature: float) -> float:
        """K_eq = exp(-ΔG° / RT)"""
        R = 8.314  # J/(mol·K)
        return np.exp(-delta_g_standard * 1000 / (R * temperature))
    
    def calculate_reaction_quotient(
        self,
        reactants: dict[str, float],
        products: dict[str, float],
        concentrations: dict[str, float]
    ) -> float:
        """Q = [products]^ν / [reactants]^ν"""
        pass
```

**Tests**: `tests/test_gibbs_calculator.py`
- Test 1: Simple ATP hydrolysis (ΔG° ≈ -30.5 kJ/mol)
- Test 2: Glucose-6-phosphate isomerization
- Test 3: K_eq calculation accuracy (compare to experimental)
- Test 4: Reaction quotient with concentration effects

---

### Phase 2: Biochemical Database Integration (Week 2)

**File**: `database_interface.py`

**Supported Databases**:

1. **eQuilibrator** (primary, free API)
   - REST API: `https://equilibrator.weizmann.ac.il/`
   - Python client: `equilibrator-api`
   - Coverage: ~10,000 biochemical reactions
   - Features: pH correction, ionic strength, uncertainty

2. **MetaCyc** (backup, requires license)
   - Local SQLite database
   - Coverage: ~17,000 reactions
   - Features: Experimental conditions, references

3. **ChEBI** (compound data)
   - REST API: `https://www.ebi.ac.uk/chebi/`
   - Compound properties, structures, synonyms
   - Free access, no authentication

**Implementation**:
```python
class ThermodynamicDatabase:
    """Interface to biochemical thermodynamic databases."""
    
    def __init__(
        self,
        primary_source: str = "equilibrator",
        cache_dir: Path = Path("~/.shypn/thermodynamics/cache")
    ):
        self.equilibrator = EquilibratorAPI()
        self.cache = ThermodynamicCache(cache_dir)
    
    def get_compound_gibbs(
        self,
        compound_id: str,
        ph: float = 7.0,
        ionic_strength: float = 0.1,
        temperature: float = 298.15
    ) -> CompoundThermodynamics:
        """Get ΔG°_f for a compound with biochemical corrections."""
        # Check local cache first
        if cached := self.cache.get_compound(compound_id, ph, temperature):
            return cached
        
        # Query eQuilibrator API
        result = self.equilibrator.get_compound(compound_id)
        thermo = self._parse_compound_response(result, ph, temperature)
        
        # Cache result
        self.cache.store_compound(thermo)
        return thermo
    
    def get_reaction_gibbs(
        self,
        reactants: dict[str, float],
        products: dict[str, float],
        ph: float = 7.0,
        temperature: float = 298.15
    ) -> ReactionThermodynamics:
        """Get ΔG°_r for a reaction from database or calculate from compounds."""
        pass
```

**Installation Requirements**:
```toml
# pyproject.toml additions
[project]
dependencies = [
    # ... existing deps ...
    "equilibrator-api>=0.4.5",  # Thermodynamic database access
    "requests>=2.31.0",          # HTTP client for APIs
    "diskcache>=5.6.3",          # Local caching
]

[project.optional-dependencies]
thermodynamics = [
    "biopython>=1.83",           # BioPAX/ChEBI parsing
    "rdkit>=2023.9.1",           # Chemical structure handling
]
```

---

### Phase 3: Compound ID Resolution (Week 2)

**File**: `compound_resolver.py`

**Problem**: Different databases use different identifiers
- KEGG: `C00002` (ATP)
- ChEBI: `CHEBI:15422` (ATP)
- IUPAC names: "Adenosine triphosphate"
- Common names: "ATP"

**Solution**: ID mapping service

```python
class CompoundResolver:
    """Resolve compound identifiers across databases."""
    
    def __init__(self):
        self.kegg_to_chebi = self._load_kegg_chebi_mapping()
        self.name_to_kegg = self._load_name_mapping()
        self.cache = {}
    
    def resolve_to_chebi(self, compound_id: str) -> str:
        """Convert any ID format to ChEBI ID."""
        # KEGG format: C00002
        if compound_id.startswith("C") and len(compound_id) == 6:
            return self.kegg_to_chebi.get(compound_id)
        
        # Already ChEBI
        if compound_id.startswith("CHEBI:"):
            return compound_id
        
        # Try as compound name
        if kegg_id := self.name_to_kegg.get(compound_id.lower()):
            return self.kegg_to_chebi.get(kegg_id)
        
        # Query ChEBI web service
        return self._query_chebi_web_service(compound_id)
    
    def get_compound_names(self, compound_id: str) -> list[str]:
        """Get all known names/synonyms for a compound."""
        pass
```

**Data Sources**:
- KEGG ↔ ChEBI mapping: Download from KEGG API or use BioCyc
- Local JSON files: `compound_ids.json` (pre-built mappings)
- Web service fallback: ChEBI REST API

---

### Phase 4: Thermodynamic Corrections (Week 3)

**File**: `thermodynamic_corrector.py`

**Biochemical Corrections**:

1. **pH Correction** (most important):
```
ΔG'° = ΔG° + n_H+ · RT ln(10) · (pH - pH_standard)
```
where n_H+ is the number of protons consumed/produced.

2. **Temperature Correction** (Van 't Hoff equation):
```
ΔG(T2) = ΔG(T1) + ΔH · (1/T2 - 1/T1)
```

3. **Ionic Strength Correction** (Debye-Hückel):
```
ΔG(I) = ΔG(I=0) + correction_term(I, charges)
```

**Implementation**:
```python
class ThermodynamicCorrector:
    """Apply biochemical corrections to standard ΔG values."""
    
    def apply_ph_correction(
        self,
        delta_g_standard: float,
        n_protons: int,
        ph: float,
        ph_standard: float = 0.0
    ) -> float:
        """Convert ΔG° (pH 0) to ΔG'° (physiological pH)."""
        R = 8.314  # J/(mol·K)
        T = 298.15  # K
        return delta_g_standard + n_protons * R * T * np.log(10) * (ph - ph_standard)
    
    def apply_temperature_correction(
        self,
        delta_g: float,
        delta_h: float,  # Enthalpy change
        temp_initial: float,
        temp_final: float
    ) -> float:
        """Correct ΔG for temperature change."""
        return delta_g + delta_h * (1/temp_final - 1/temp_initial)
    
    def apply_ionic_strength_correction(
        self,
        delta_g: float,
        ionic_strength: float,
        reactant_charges: list[int],
        product_charges: list[int]
    ) -> float:
        """Debye-Hückel correction for ionic strength."""
        pass
```

---

### Phase 5: Equilibrium Validator (Week 3)

**File**: `equilibrium_validator.py`

**Core Logic**:
```python
@dataclass
class EquilibriumValidation:
    """Result of thermodynamic equilibrium validation."""
    reaction_id: str
    k_eq_thermodynamic: float     # From ΔG°
    k_eq_kinetic: float            # From k_f/k_r
    ratio_difference: float        # |k_eq_thermo - k_eq_kinetic| / k_eq_thermo
    is_consistent: bool            # Difference < threshold
    severity: str                  # "OK", "WARNING", "ERROR"
    message: str

class EquilibriumValidator:
    """Validate kinetic rate constants against thermodynamic equilibrium."""
    
    def __init__(
        self,
        gibbs_calculator: GibbsCalculator,
        tolerance: float = 0.5  # 50% tolerance (orders of magnitude vary)
    ):
        self.calculator = gibbs_calculator
        self.tolerance = tolerance
    
    def validate_reversible_reaction(
        self,
        reaction_id: str,
        k_forward: float,
        k_reverse: float,
        reactants: dict[str, float],
        products: dict[str, float],
        temperature: float = 298.15,
        ph: float = 7.0
    ) -> EquilibriumValidation:
        """Check if k_f/k_r matches thermodynamic K_eq."""
        
        # Calculate thermodynamic K_eq
        thermo = self.calculator.calculate_delta_g_reaction(
            reactants, products, temperature=temperature, ph=ph
        )
        k_eq_thermo = thermo.k_eq
        
        # Calculate kinetic K_eq
        k_eq_kinetic = k_forward / k_reverse
        
        # Compare
        relative_diff = abs(k_eq_thermo - k_eq_kinetic) / k_eq_thermo
        
        is_consistent = relative_diff <= self.tolerance
        
        if is_consistent:
            severity = "OK"
            message = f"Thermodynamic consistency verified (Δ = {relative_diff:.1%})"
        elif relative_diff <= 1.0:
            severity = "WARNING"
            message = (
                f"Moderate thermodynamic inconsistency (Δ = {relative_diff:.1%}).\n"
                f"K_eq(thermo) = {k_eq_thermo:.2e}, K_eq(kinetic) = {k_eq_kinetic:.2e}"
            )
        else:
            severity = "ERROR"
            message = (
                f"SEVERE thermodynamic inconsistency (Δ = {relative_diff:.1%})!\n"
                f"K_eq(thermo) = {k_eq_thermo:.2e}, K_eq(kinetic) = {k_eq_kinetic:.2e}\n"
                f"Rate constants violate thermodynamic equilibrium laws."
            )
        
        return EquilibriumValidation(
            reaction_id=reaction_id,
            k_eq_thermodynamic=k_eq_thermo,
            k_eq_kinetic=k_eq_kinetic,
            ratio_difference=relative_diff,
            is_consistent=is_consistent,
            severity=severity,
            message=message
        )
    
    def validate_pathway(
        self,
        pathway: Pathway,
        temperature: float = 298.15,
        ph: float = 7.0
    ) -> list[EquilibriumValidation]:
        """Validate all reversible reactions in a pathway."""
        validations = []
        
        for transition in pathway.transitions:
            # Only check reversible reactions
            if not transition.metadata.get('reversible', False):
                continue
            
            # Extract forward/reverse rates from formula
            k_forward, k_reverse = self._extract_rates(transition.formula)
            
            # Extract reactants/products from arcs
            reactants, products = self._extract_stoichiometry(pathway, transition)
            
            validation = self.validate_reversible_reaction(
                reaction_id=transition.name,
                k_forward=k_forward,
                k_reverse=k_reverse,
                reactants=reactants,
                products=products,
                temperature=temperature,
                ph=ph
            )
            
            validations.append(validation)
        
        return validations
```

---

### Phase 6: Integration with SBML/KEGG Import (Week 4)

**Integration Point 1**: SBML Validator

Modify `sbml_validator.py` to add thermodynamic validation:

```python
# In sbml_validator.py

from shypn.thermodynamics import EquilibriumValidator, GibbsCalculator

class SBMLValidator:
    def __init__(self, ...):
        # ... existing code ...
        self.thermo_validator = EquilibriumValidator(
            gibbs_calculator=GibbsCalculator()
        )
    
    def validate(self, model, pathway, options):
        # ... existing validations ...
        
        # NEW: Thermodynamic validation
        if options.check_thermodynamics:
            self._check_thermodynamic_feasibility(pathway, options)
    
    def _check_thermodynamic_feasibility(self, pathway, options):
        """Validate thermodynamic consistency of reversible reactions."""
        validations = self.thermo_validator.validate_pathway(
            pathway,
            temperature=options.temperature,
            ph=options.ph
        )
        
        for validation in validations:
            if validation.severity == "ERROR":
                self.issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category="thermodynamic_violation",
                    message=f"Reaction {validation.reaction_id}: {validation.message}",
                    suggestion="Adjust rate constants to match K_eq from thermodynamics"
                ))
            elif validation.severity == "WARNING":
                self.issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    category="thermodynamic_inconsistency",
                    message=f"Reaction {validation.reaction_id}: {validation.message}",
                    suggestion="Consider refining rate constants for thermodynamic accuracy"
                ))
```

**Integration Point 2**: Simulation Initialization

Add thermodynamic check to simulation setup:

```python
# In simulation.py

def setup(self, pathway: Pathway, options: SimulationOptions):
    # ... existing setup ...
    
    # NEW: Optional thermodynamic check
    if options.check_thermodynamics:
        from shypn.thermodynamics import EquilibriumValidator, GibbsCalculator
        
        validator = EquilibriumValidator(GibbsCalculator())
        validations = validator.validate_pathway(
            pathway,
            temperature=options.temperature,
            ph=options.ph
        )
        
        # Log warnings
        for v in validations:
            if v.severity in ["WARNING", "ERROR"]:
                logger.warning(f"{v.reaction_id}: {v.message}")
```

---

### Phase 7: Testing & Validation (Week 5)

**Test Suite**: `tests/thermodynamics/`

**Test Files**:

1. `test_gibbs_calculator.py`
   - ATP hydrolysis (experimental ΔG° = -30.5 kJ/mol)
   - Glucose phosphorylation
   - Glycolysis pathway (multi-step)
   - Temperature dependence

2. `test_database_interface.py`
   - eQuilibrator API connectivity
   - Cache functionality
   - Compound lookup (ATP, glucose, NADH)
   - Error handling (compound not found)

3. `test_compound_resolver.py`
   - KEGG → ChEBI conversion
   - Name → ChEBI conversion
   - Ambiguous name handling
   - Cache performance

4. `test_equilibrium_validator.py`
   - Simple reversible reaction (A ⇌ B)
   - Thermodynamically consistent rates (pass)
   - Thermodynamically inconsistent rates (fail)
   - Glycolysis reversible steps

5. `test_sbml_integration.py`
   - Load SBML with reversible reactions
   - Validate thermodynamics
   - Check ValidationIssue generation
   - Test BIOMD0000000061 (circadian clock)

**Example Test**:
```python
def test_atp_hydrolysis_thermodynamics():
    """Test ATP → ADP + Pi thermodynamics."""
    calculator = GibbsCalculator()
    
    # ATP + H2O → ADP + Pi
    reactants = {"C00002": 1, "C00001": 1}  # ATP, H2O
    products = {"C00008": 1, "C00009": 1}    # ADP, Pi
    
    thermo = calculator.calculate_delta_g_reaction(
        reactants, products, temperature=310.15, ph=7.4
    )
    
    # Expected: ΔG'° ≈ -30.5 kJ/mol at pH 7, 37°C
    assert -35 < thermo.delta_g_prime < -25, f"Got {thermo.delta_g_prime}"
    
    # K_eq should be very large (>> 1)
    assert thermo.k_eq > 1e5
```

---

## 4. Data Requirements

### Minimal Data for MVP

**Priority 1 Compounds** (glycolysis/TCA cycle):
- ATP, ADP, AMP (C00002, C00008, C00020)
- NAD+, NADH (C00003, C00004)
- Glucose, G6P, F6P (C00031, C00092, C00085)
- Pyruvate, Acetyl-CoA (C00022, C00024)

**Data Collection Strategy**:
1. **eQuilibrator API**: Primary source (free, automated)
2. **Manual curation**: Literature values for key metabolites
3. **Local JSON cache**: Ship with shypn for offline use

**File**: `src/shypn/thermodynamics/data/core_metabolites.json`
```json
{
  "compounds": {
    "C00002": {
      "name": "ATP",
      "chebi_id": "CHEBI:15422",
      "delta_g_formation": {
        "value": -2292.2,
        "unit": "kJ/mol",
        "conditions": {"pH": 7.0, "T": 298.15, "I": 0.1},
        "source": "Alberty 2003"
      }
    }
  }
}
```

---

## 5. User Interface

### CLI Commands

**New Commands**:
```bash
# Validate thermodynamics of SBML model
shypn validate --thermodynamics --sbml model.xml

# Check specific reaction thermodynamics
shypn thermo check-reaction --kegg "R00200" --ph 7.4 --temp 310

# Export thermodynamic report
shypn thermo export --pathway glycolysis.xml --output thermo_report.json
```

### GUI Integration

**Validation Panel Enhancement**:
```
Validation Results
├── Structure (✓ 15 checks passed)
├── Kinetics (⚠ 2 warnings)
└── Thermodynamics (NEW)
    ├── ✓ 12 reactions thermodynamically consistent
    ├── ⚠ 3 reactions with moderate inconsistency
    └── ✗ 1 reaction violates equilibrium laws
        └── R00200 (glucose phosphorylation)
            K_eq(thermo) = 3.9e-4
            K_eq(kinetic) = 2.1e-2
            Suggestion: Increase k_reverse by 54×
```

**Transition Properties Panel**:
```
Transition: hexokinase (R00200)
├── Kinetics
│   ├── k_forward: 0.5 s⁻¹
│   └── k_reverse: 0.01 s⁻¹
└── Thermodynamics (NEW)
    ├── ΔG°: +13.8 kJ/mol
    ├── K_eq: 3.9e-4
    ├── Consistency: ⚠ WARNING
    └── Ratio k_f/k_r: 50 (expected: 0.00039)
```

---

## 6. Configuration Options

### `pyproject.toml` Settings

```toml
[tool.shypn.thermodynamics]
# Enable thermodynamic validation by default
enabled = true

# Tolerance for K_eq matching (0.5 = 50%)
equilibrium_tolerance = 0.5

# Default physiological conditions
default_ph = 7.4
default_temperature = 310.15  # 37°C
default_ionic_strength = 0.15  # M

# Database preferences
database_priority = ["equilibrator", "metacyc", "manual"]
cache_directory = "~/.shypn/thermodynamics/cache"
cache_expiry_days = 30

# Warnings/errors behavior
warn_on_missing_data = true
error_on_severe_violation = false  # Don't block simulation
```

### Simulation Options

```python
@dataclass
class SimulationOptions:
    # ... existing options ...
    
    # NEW thermodynamic options
    check_thermodynamics: bool = True
    ph: float = 7.4
    temperature: float = 310.15  # Kelvin
    ionic_strength: float = 0.15  # M
    thermodynamic_tolerance: float = 0.5
```

---

## 7. Performance Considerations

### Optimization Strategies

1. **Caching**:
   - Disk cache: `diskcache` library
   - Memory cache: `functools.lru_cache`
   - Cache key: `(compound_id, pH, T, I)` → ΔG°_f

2. **Batch Queries**:
   - Query eQuilibrator API in batches (100 compounds/request)
   - Parallel requests with `asyncio` or `aiohttp`

3. **Lazy Loading**:
   - Only calculate thermodynamics if requested
   - Skip validation for irreversible reactions
   - Optional validation step (not mandatory)

4. **Offline Mode**:
   - Ship with pre-computed ΔG° for common metabolites (~500 compounds)
   - Graceful degradation if API unavailable

### Expected Performance

- **Initial validation** (100 reactions): ~5-10 seconds (with cold cache)
- **Subsequent validations**: ~0.1-0.5 seconds (warm cache)
- **Memory overhead**: ~50-100 MB (loaded thermodynamic data)
- **Disk cache size**: ~10-50 MB (for typical user)

---

## 8. Documentation

### New Documentation Files

1. **User Guide**: `doc/thermodynamics/USER_GUIDE.md`
   - What are thermodynamic constraints?
   - When to use thermodynamic validation
   - Interpreting validation results
   - Fixing thermodynamic violations

2. **API Reference**: `doc/thermodynamics/API_REFERENCE.md`
   - GibbsCalculator class
   - EquilibriumValidator class
   - ThermodynamicDatabase class
   - Configuration options

3. **Scientific Background**: `doc/thermodynamics/THEORY.md`
   - Gibbs free energy fundamentals
   - Biochemical standard state
   - pH and ionic strength corrections
   - Literature references

4. **Examples**: `examples/thermodynamics/`
   - `validate_glycolysis.py`
   - `check_atp_hydrolysis.py`
   - `custom_conditions.py`

---

## 9. Testing Strategy

### Unit Tests (80% coverage target)

**Critical Paths**:
- ✓ Gibbs calculation accuracy (±2 kJ/mol)
- ✓ K_eq calculation (±10%)
- ✓ pH correction (±1 kJ/mol)
- ✓ Database API connectivity
- ✓ Cache read/write

### Integration Tests

**End-to-End Scenarios**:
1. Import SBML → Validate thermodynamics → Generate report
2. KEGG pathway → Check all reversible reactions
3. Simulation with thermodynamic check enabled

### Validation Tests (Real Models)

**BIOMD Models**:
- BIOMD0000000061: Circadian clock (reversible reactions)
- BIOMD0000000010: Glycolysis (Teusink 2000)
- BIOMD0000000064: Citric acid cycle

**Expected Outcomes**:
- Models should pass validation (literature-curated)
- Some warnings expected (approximate kinetics)
- No severe errors (K_eq off by >2 orders of magnitude)

---

## 10. Implementation Timeline

### Week 1: Core Calculator
- [x] Create module structure
- [ ] Implement `GibbsCalculator`
- [ ] Write unit tests for ΔG and K_eq
- [ ] Test with ATP hydrolysis

### Week 2: Database Integration
- [ ] Set up eQuilibrator API client
- [ ] Implement `CompoundResolver`
- [ ] Create local cache system
- [ ] Download/curate core metabolite data

### Week 3: Validation & Corrections
- [ ] Implement `EquilibriumValidator`
- [ ] Add pH/temperature corrections
- [ ] Write validation tests
- [ ] Test with glycolysis pathway

### Week 4: SBML/KEGG Integration
- [ ] Modify `sbml_validator.py`
- [ ] Add simulation options
- [ ] Update GUI validation panel
- [ ] Integration tests

### Week 5: Testing & Documentation
- [ ] Comprehensive test suite
- [ ] User guide documentation
- [ ] API reference
- [ ] Example scripts

### Week 6: Polish & Review
- [ ] Performance optimization
- [ ] Code review
- [ ] User testing feedback
- [ ] Manuscript section draft

---

## 11. Success Criteria

### MVP Requirements
- ✓ Calculate ΔG° for simple reactions (A → B)
- ✓ Query eQuilibrator API for compound data
- ✓ Validate K_eq vs k_f/k_r for reversible reactions
- ✓ Integration with SBML import pipeline
- ✓ Basic test coverage (>80%)

### Extended Goals
- ◯ Support multi-step pathway validation
- ◯ GUI visualization of thermodynamic consistency
- ◯ Auto-suggest rate constant corrections
- ◯ pH/temperature/ionic strength corrections
- ◯ Offline mode with local database

### Manuscript Integration
- ◯ Methods section: Thermodynamic validation algorithm
- ◯ Results: Validation of BIOMD models
- ◯ Discussion: Importance of thermodynamic constraints
- ◯ Supplementary: Full thermodynamic data tables

---

## 12. Risks & Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| eQuilibrator API unavailable | High | Low | Local cache + offline mode |
| Compound ID mapping incomplete | Medium | Medium | Manual curation + fallback to names |
| Thermodynamic data missing | Medium | High | Graceful degradation, warn user |
| Performance too slow | Low | Low | Caching + batch queries |
| pH correction errors | High | Low | Validate against literature |

---

## 13. Future Enhancements

### Post-MVP Features
1. **Auto-correction**: Suggest rate constant adjustments to match K_eq
2. **Pathway energy landscapes**: Visualize ΔG along reaction path
3. **Metabolic flux analysis**: Integrate with FBA constraints
4. **Machine learning**: Predict missing ΔG° values
5. **Experimental data**: Import calorimetry measurements

### Database Expansion
- BRENDA integration (Km, kcat values)
- Reactome pathway annotations
- SABIO-RK kinetic parameters
- PubChem compound properties

---

## 14. References

### Key Papers
1. Alberty, R.A. (2003). *Thermodynamics of Biochemical Reactions*. Wiley.
2. Flamholz et al. (2012). eQuilibrator—the biochemical thermodynamics calculator. *Nucleic Acids Res*.
3. Noor et al. (2013). Consistent estimation of Gibbs energy using component contributions. *PLoS Comp Bio*.
4. Beard & Qian (2008). *Chemical Biophysics: Quantitative Analysis of Cellular Systems*.

### Database Documentation
- eQuilibrator: https://equilibrator.readthedocs.io/
- ChEBI: https://www.ebi.ac.uk/chebi/
- MetaCyc: https://metacyc.org/

---

## 15. Contact & Questions

**Implementation Lead**: [Assign after review]  
**Scientific Advisor**: [Domain expert in thermodynamics]  
**Code Review**: [Senior developer]

**Questions?** Open GitHub issue with label `thermodynamics-plan`

---

**Status**: ⏳ Awaiting Approval  
**Last Updated**: 2024 (post-Skellam implementation)  
**Version**: 1.0 (Initial Plan)
