# KEGG Kinetic Enrichment Plan

**Date**: October 27, 2025  
**Status**: Planning Phase  
**Goal**: Automatically pre-fill transition kinetic functions based on KEGG pathway information, locality analysis, and biological knowledge

## Overview

Enhance the KEGG import pipeline to automatically generate biologically meaningful kinetic functions for transitions, leveraging:
- Locality analysis (input/output places)
- Stoichiometry information
- KEGG kinetic parameters (when available)
- Established biological kinetic models (Michaelis-Menten, exponential distributions)
- Mathematical formulations (NumPy/SymPy)

## Current State (Baseline)

### KEGG Import Pipeline (Existing)
```
Parse KEGG → Validate → Post-Process → Convert → Instantiate → Display
```

**Current Capabilities**:
- ✅ Topology extraction (reactions, compounds, relations)
- ✅ Stoichiometry parsing (coefficients)
- ✅ Transition type assignment (immediate, timed, stochastic)
- ❌ No kinetic function pre-filling
- ❌ No parameter estimation
- ❌ Manual kinetic configuration required

### Available KEGG Information
1. **Reaction Information**:
   - Enzyme Commission (EC) numbers
   - Reaction equations with stoichiometry
   - Substrate and product identities
   - Reaction type (reversible/irreversible)

2. **Compound Information**:
   - Compound IDs (C00001, etc.)
   - Molecular formulas
   - Names and synonyms

3. **Kinetic Data** (when available):
   - KM values (Michaelis constant)
   - Vmax values (maximum velocity)
   - kcat values (turnover number)
   - Ki values (inhibition constants)

## Proposed Enhancement Architecture

### Phase 1: Locality-Based Kinetic Inference

**Goal**: Use network topology to infer appropriate kinetic models

#### 1.1 Locality Analysis Engine
```python
class LocalityKineticAnalyzer:
    """Analyzes transition locality to determine kinetic model."""
    
    def analyze_transition(self, transition):
        """
        Returns:
            {
                'input_places': [P1, P2, ...],
                'output_places': [P3, P4, ...],
                'input_stoichiometry': {P1: 2, P2: 1, ...},
                'output_stoichiometry': {P3: 1, P4: 1, ...},
                'suggested_model': 'michaelis_menten' | 'mass_action' | 'hill' | 'exponential',
                'parameters': {...}
            }
        """
```

**Inference Rules**:
- **Single substrate → Single product**: Michaelis-Menten
- **Multiple substrates → Multiple products**: Mass action or Hill kinetics
- **Stochastic transitions**: Exponential distribution (Gillespie algorithm)
- **Inhibition present**: Competitive/Non-competitive inhibition models

#### 1.2 Stoichiometry-Aware Function Generation
```python
class StoichiometryFunction:
    """Generates rate functions respecting stoichiometry."""
    
    def generate_mass_action(self, inputs, stoich):
        """
        Example: 2A + B → C
        Rate = k * [A]^2 * [B]
        """
        
    def generate_michaelis_menten(self, substrate, enzyme, km, vmax):
        """
        Rate = (Vmax * [S]) / (Km + [S])
        """
```

### Phase 2: KEGG Kinetic Database Integration

**Goal**: Fetch and use experimental kinetic parameters from KEGG

#### 2.1 KEGG API Kinetic Data Fetcher
```python
class KEGGKineticFetcher:
    """Fetches kinetic parameters from KEGG databases."""
    
    def fetch_enzyme_parameters(self, ec_number):
        """
        Fetches from KEGG ENZYME database:
        - KM values
        - Kcat values
        - Optimal pH, temperature
        - Cofactors
        """
        
    def fetch_reaction_kinetics(self, reaction_id):
        """
        Fetches from KEGG REACTION database:
        - Rate constants
        - Equilibrium constants
        - Thermodynamic data
        """
```

**Data Sources**:
- KEGG ENZYME database (EC-specific parameters)
- KEGG REACTION database (reaction-specific data)
- BRENDA database (comprehensive enzyme data - external)
- SABIO-RK database (kinetic data repository - external)

#### 2.2 Parameter Estimation Fallbacks
When experimental data unavailable:
- **Literature-based defaults** (curated database)
- **Similarity-based estimation** (from similar EC numbers)
- **Order-of-magnitude estimates** (biologically plausible ranges)

### Phase 3: Kinetic Model Templates

**Goal**: Implement common biological kinetic models as pre-filled templates

#### 3.1 Template Library

##### Michaelis-Menten (Enzymatic Reactions)
```python
def michaelis_menten_rate(substrate_tokens, km, vmax):
    """
    Classic Michaelis-Menten kinetics.
    
    Formula: v = (Vmax * [S]) / (Km + [S])
    
    Args:
        substrate_tokens: Current substrate place marking
        km: Michaelis constant (affinity parameter)
        vmax: Maximum reaction velocity
    
    Returns:
        Reaction rate (tokens/time)
    """
    import numpy as np
    S = substrate_tokens
    return (vmax * S) / (km + S)
```

##### Mass Action Kinetics
```python
def mass_action_rate(input_tokens, stoichiometry, k):
    """
    Mass action law for elementary reactions.
    
    Formula: v = k * ∏([Xi]^ni)
    
    Args:
        input_tokens: Dict of {place_id: marking}
        stoichiometry: Dict of {place_id: coefficient}
        k: Rate constant
    
    Returns:
        Reaction rate
    """
    import numpy as np
    rate = k
    for place_id, coeff in stoichiometry.items():
        rate *= np.power(input_tokens[place_id], coeff)
    return rate
```

##### Hill Equation (Cooperative Binding)
```python
def hill_equation_rate(substrate_tokens, km, vmax, n):
    """
    Hill equation for cooperative binding.
    
    Formula: v = (Vmax * [S]^n) / (Km^n + [S]^n)
    
    Args:
        substrate_tokens: Current substrate marking
        km: Half-saturation constant
        vmax: Maximum velocity
        n: Hill coefficient (cooperativity)
    
    Returns:
        Reaction rate
    """
    import numpy as np
    S = substrate_tokens
    return (vmax * np.power(S, n)) / (np.power(km, n) + np.power(S, n))
```

##### Competitive Inhibition
```python
def competitive_inhibition_rate(substrate_tokens, inhibitor_tokens, km, vmax, ki):
    """
    Michaelis-Menten with competitive inhibition.
    
    Formula: v = (Vmax * [S]) / (Km * (1 + [I]/Ki) + [S])
    
    Args:
        substrate_tokens: Substrate place marking
        inhibitor_tokens: Inhibitor place marking
        km: Michaelis constant
        vmax: Maximum velocity
        ki: Inhibition constant
    
    Returns:
        Reaction rate
    """
    import numpy as np
    S = substrate_tokens
    I = inhibitor_tokens
    return (vmax * S) / (km * (1 + I/ki) + S)
```

##### Exponential Distribution (Stochastic)
```python
def stochastic_exponential_rate(propensity):
    """
    Gillespie algorithm exponential distribution.
    
    Formula: τ ~ Exp(a0), where a0 is total propensity
    
    Args:
        propensity: Reaction propensity (mass action * stochastic rate)
    
    Returns:
        Time to next firing (exponentially distributed)
    """
    import numpy as np
    return np.random.exponential(1.0 / propensity)
```

##### Threshold Functions
```python
def threshold_activation(input_tokens, threshold, max_rate):
    """
    Threshold-based activation (all-or-nothing).
    
    Formula: v = max_rate if [S] >= threshold else 0
    
    Args:
        input_tokens: Current input marking
        threshold: Activation threshold
        max_rate: Maximum rate above threshold
    
    Returns:
        Reaction rate
    """
    return max_rate if input_tokens >= threshold else 0.0
```

#### 3.2 Transition Type to Model Mapping

| Transition Type | Default Kinetic Model | Alternative Models |
|----------------|----------------------|-------------------|
| **Immediate** | Mass action | Threshold |
| **Timed** | Michaelis-Menten | Mass action, Hill |
| **Stochastic** | Exponential (Gillespie) | Mass action (discrete) |
| **Continuous** | Michaelis-Menten | Mass action, ODE |

### Phase 4: Pre-filling Pipeline

**Goal**: Automated kinetic function generation during KEGG import

#### 4.1 Enhanced Import Flow
```
KEGG Import → Topology Extraction → 
    ↓
Locality Analysis → 
    ↓
EC Number Lookup → Kinetic Data Fetch → 
    ↓
Parameter Estimation → 
    ↓
Model Selection → 
    ↓
Function Pre-filling → 
    ↓
User Review & Adjustment →
    ↓
Model Instantiation
```

#### 4.2 Pre-filling Algorithm
```python
class KineticPreFillingEngine:
    """Orchestrates kinetic function pre-filling."""
    
    def prefill_transition_kinetics(self, transition, kegg_data):
        """
        Main pre-filling logic.
        
        Steps:
        1. Analyze locality (input/output places, stoichiometry)
        2. Determine transition type
        3. Fetch kinetic data (if available)
        4. Select appropriate kinetic model
        5. Estimate parameters
        6. Generate function code (NumPy/SymPy)
        7. Store in transition.rate_function
        8. Store metadata (model type, parameters, confidence)
        """
        
        # Step 1: Locality analysis
        locality = self.analyze_locality(transition)
        
        # Step 2: Fetch KEGG kinetics
        kinetic_data = self.fetch_kegg_kinetics(
            ec_number=kegg_data.get('ec'),
            reaction_id=kegg_data.get('reaction_id')
        )
        
        # Step 3: Select model
        model = self.select_kinetic_model(
            transition_type=transition.transition_type,
            locality=locality,
            kinetic_data=kinetic_data
        )
        
        # Step 4: Estimate parameters
        parameters = self.estimate_parameters(
            model=model,
            kinetic_data=kinetic_data,
            locality=locality
        )
        
        # Step 5: Generate function
        function_code = self.generate_function_code(
            model=model,
            parameters=parameters,
            locality=locality
        )
        
        # Step 6: Store
        transition.rate_function = function_code
        transition.kinetic_metadata = {
            'model': model.name,
            'parameters': parameters,
            'confidence': kinetic_data.get('confidence', 'estimated'),
            'source': kinetic_data.get('source', 'auto-generated')
        }
```

### Phase 5: User Interface Integration

**Goal**: Allow users to review and customize pre-filled kinetics

#### 5.1 Enhanced Transition Property Dialog

**New UI Elements**:
- **Kinetic Model Selector**: Dropdown (Michaelis-Menten, Mass Action, Hill, etc.)
- **Parameter Fields**: Editable fields for KM, Vmax, k, etc.
- **Function Preview**: Read-only code view of generated function
- **Confidence Indicator**: Badge showing data source (experimental/estimated/manual)
- **Parameter Estimation Button**: Re-run estimation with different assumptions

#### 5.2 Batch Review Interface

**New Panel**: "Kinetic Review Panel"
- List all transitions with pre-filled kinetics
- Color-coded by confidence level:
  - 🟢 Green: Experimental data
  - 🟡 Yellow: Literature-based estimate
  - 🟠 Orange: Similarity-based estimate
  - 🔴 Red: Order-of-magnitude estimate
- Batch edit capabilities
- Export/import parameter sets

### Phase 6: Validation & Testing

#### 6.1 Validation Approaches

1. **Biological Plausibility**:
   - Parameter ranges within biological bounds
   - Rate constants reasonable for enzyme kinetics
   - Steady-state analysis

2. **Literature Comparison**:
   - Compare generated models with published pathway models
   - Validate against experimental time-series data

3. **Simulation Testing**:
   - Run simulations with pre-filled kinetics
   - Check for numerical stability
   - Verify conservation laws

#### 6.2 Test Cases
- **Test Pathway 1**: Glycolysis (well-studied, rich kinetic data)
- **Test Pathway 2**: MAPK cascade (signaling, cooperative binding)
- **Test Pathway 3**: Simple metabolic pathway (basic Michaelis-Menten)

## Implementation Roadmap

### Milestone 1: Foundation (2-3 weeks)
- [ ] Implement LocalityKineticAnalyzer
- [ ] Create kinetic model template library
- [ ] Develop parameter estimation fallback system
- [ ] Unit tests for kinetic functions

### Milestone 2: KEGG Integration (2-3 weeks)
- [ ] Implement KEGGKineticFetcher
- [ ] Parse KEGG ENZYME and REACTION databases
- [ ] Handle API rate limiting and caching
- [ ] Integration tests with real KEGG data

### Milestone 3: Pre-filling Engine (2 weeks)
- [ ] Implement KineticPreFillingEngine
- [ ] Integrate with existing KEGG import pipeline
- [ ] Model selection heuristics
- [ ] End-to-end tests

### Milestone 4: UI Integration (2 weeks)
- [ ] Enhance transition property dialog
- [ ] Create kinetic review panel
- [ ] Implement confidence indicators
- [ ] User acceptance testing

### Milestone 5: Validation (1-2 weeks)
- [ ] Test with well-characterized pathways
- [ ] Compare with literature models
- [ ] Performance benchmarking
- [ ] Documentation

**Total Estimated Time**: 9-12 weeks

## Technical Requirements

### Dependencies
```python
# New dependencies to add to requirements.txt
numpy>=1.21.0          # Numerical computations
sympy>=1.10           # Symbolic mathematics
requests>=2.26.0      # KEGG API calls
beautifulsoup4>=4.10  # HTML parsing (if needed)
lxml>=4.6.3           # XML parsing (KEGG data)
```

### Data Storage

**New Fields in Transition Model**:
```python
class Transition:
    # Existing fields...
    
    # New kinetic fields
    rate_function: str = None  # Python code as string
    kinetic_model: str = None  # 'michaelis_menten', 'mass_action', etc.
    kinetic_parameters: dict = None  # {param_name: value}
    kinetic_metadata: dict = None  # {confidence, source, ec_number, etc.}
```

### File Format Extensions

**Enhanced .shy format**:
```json
{
  "transitions": [
    {
      "id": "T1",
      "label": "Hexokinase",
      "type": "timed",
      "kinetic": {
        "model": "michaelis_menten",
        "function": "lambda S: (0.5 * S) / (0.1 + S)",
        "parameters": {
          "Vmax": 0.5,
          "Km": 0.1
        },
        "metadata": {
          "confidence": "experimental",
          "source": "KEGG:E:2.7.1.1",
          "ec_number": "2.7.1.1",
          "timestamp": "2025-10-27T12:00:00Z"
        }
      }
    }
  ]
}
```

## Benefits

### For Users
1. **Reduced Manual Work**: Automatic generation of biologically relevant kinetics
2. **Scientific Accuracy**: Parameter-based on experimental data when available
3. **Biological Realism**: Models respect stoichiometry and enzyme mechanisms
4. **Simulation Ready**: Models can be simulated immediately after import
5. **Transparency**: Clear indication of data sources and confidence levels

### For Research
1. **Reproducibility**: Standardized kinetic models
2. **Comparability**: Same pathway from different sources uses consistent kinetics
3. **Hypothesis Testing**: Easy parameter sensitivity analysis
4. **Publication Ready**: Models with documented parameter sources

### For the Project
1. **Differentiation**: Unique feature not available in other Petri net tools
2. **Systems Biology Focus**: Clear positioning in computational biology space
3. **Community Value**: Lower barrier to systems biology modeling
4. **Citation Potential**: Novel integration of KEGG data with Petri nets

## Challenges & Mitigations

### Challenge 1: Data Availability
**Issue**: Many reactions lack experimental kinetic parameters  
**Mitigation**: 
- Implement robust estimation fallbacks
- Use literature-curated default values
- Clearly indicate estimation confidence

### Challenge 2: Model Complexity
**Issue**: Some reactions require complex kinetic models  
**Mitigation**:
- Start with common models (Michaelis-Menten, mass action)
- Allow custom user-defined functions
- Provide model library that users can extend

### Challenge 3: Computational Cost
**Issue**: Fetching data for large pathways may be slow  
**Mitigation**:
- Implement local caching of KEGG data
- Background fetching with progress indicators
- Batch API requests when possible

### Challenge 4: Parameter Units
**Issue**: Kinetic parameters have different units across sources  
**Mitigation**:
- Standardize on SI units internally
- Implement unit conversion utilities
- Document unit assumptions clearly

## Future Extensions

### Extension 1: SBML Integration
Import kinetic parameters from SBML models that include rate laws

### Extension 2: Machine Learning Parameter Estimation
Train models to predict kinetic parameters from reaction structure

### Extension 3: Sensitivity Analysis Tools
Automatic parameter sensitivity and uncertainty quantification

### Extension 4: Time-Series Data Fitting
Fit kinetic parameters to experimental time-series data

### Extension 5: Multi-Compartment Kinetics
Handle compartment-specific parameters and transport kinetics

## References

### Kinetic Modeling
1. Cornish-Bowden, A. (2012). "Fundamentals of Enzyme Kinetics" (4th ed.)
2. Segel, I. H. (1993). "Enzyme Kinetics: Behavior and Analysis of Rapid Equilibrium and Steady-State Enzyme Systems"
3. Wilkinson, D. J. (2018). "Stochastic Modelling for Systems Biology" (3rd ed.)

### Databases
1. KEGG: https://www.kegg.jp/kegg/docs/relnote.html
2. BRENDA: https://www.brenda-enzymes.org/
3. SABIO-RK: http://sabiork.h-its.org/

### Methods
1. Gillespie, D. T. (1977). "Exact stochastic simulation of coupled chemical reactions"
2. Michaelis, L., & Menten, M. L. (1913). "Die Kinetik der Invertinwirkung"
3. Hill, A. V. (1910). "The possible effects of the aggregation of the molecules of haemoglobin"

## Related Documentation
- [KEGG Import Pipeline](KEGG_COMPLETE_IMPORT_FLOW.md)
- [Firing Policies](FIRING_POLICIES.md)
- [SBML Flow Analysis](SBML_COMPLETE_FLOW_ANALYSIS.md)
- [Pathway Enhancement Pipeline](PATHWAY_IMPORT_DESIGN_COMPLETE.md)

## Status Tracking

- [ ] **Phase 1**: Foundation - Not started
- [ ] **Phase 2**: KEGG Integration - Not started
- [ ] **Phase 3**: Pre-filling Engine - Not started
- [ ] **Phase 4**: UI Integration - Not started
- [ ] **Phase 5**: Validation - Not started

**Next Steps**:
1. Review plan with stakeholders
2. Create detailed Phase 1 implementation tickets
3. Set up development branch: `feature/kegg-kinetic-enrichment`
4. Begin LocalityKineticAnalyzer implementation
