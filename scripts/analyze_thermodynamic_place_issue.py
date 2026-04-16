#!/usr/bin/env python3
"""
Analysis: Why Thermodynamic Code Uses Hard-Coded Properties Instead of Places

This script identifies where the thermodynamic system uses static document settings
instead of reading from dynamic spatial places (like pH_cytoplasm, Temperature, etc.)

Issue: Inconsistency between rate functions (which can read places) and
thermodynamic validation (which uses hard-coded document settings)

Author: Analysis Pipeline  
Date: February 14, 2026
"""

def print_section(title: str, char: str = "="):
    """Print section header."""
    print(f"\n{char * 70}")
    print(title)
    print(f"{char * 70}\n")


def analyze_current_implementation():
    """Document where hard-coding happens."""
    
    print_section("CURRENT IMPLEMENTATION ANALYSIS", "=")
    
    print("1. RATE FUNCTION EVALUATION (Dynamic ✓)")
    print("-" * 70)
    print("""
Location: src/shypn/engine/stochastic_behavior.py, line 346-389

Current behavior:
  ✓ Reads from document thermodynamic_settings (static fallback)
  ✓ Then OVERRIDES with spatial places if they exist:
    • "temperature" in place name → context['T']
    • "ph" in place name → context['pH']  
    • "ionic_strength" or "I" → context['I']

Example:
  If model has place "pH_cytoplasm" with 7.2 tokens:
    → context['pH'] = 7.2 (DYNAMIC)
  
  If model has place "Temperature_celsius" with 37 tokens:
    → context['T'] = 37 + 273.15 = 310.15 K (DYNAMIC)

Code snippet:
```python
# DYNAMIC THERMODYNAMIC STATE: If places exist, they override settings
for place_name, tokens in places_dict.items():
    if 'temperature' in place_name.lower():
        if 'celsius' in place_name.lower():
            context['T_celsius'] = tokens
            context['T'] = tokens + 273.15
        else:
            context['T'] = tokens
            context['T_celsius'] = tokens - 273.15
    elif 'ph' in place_name.lower():
        context['pH'] = tokens
```

Result: Rate functions CAN use dynamic spatial properties! ✓

Example usage in rate function:
  rate = k_base * arrhenius(T=[Temperature], Ea=50) * [Substrate]
  rate = k_acid * ph_to_concentration([pH_cytoplasm]) * [Drug]
""")
    
    print("\n2. THERMODYNAMIC VALIDATION (Static ✗)")
    print("-" * 70)
    print("""
Location: src/shypn/thermodynamics/simulation_integration.py, line 80-92

Current behavior:
  ✗ Reads ONLY from document settings at initialization
  ✗ Never checks for spatial places
  ✗ pH, T, ionic_strength are STATIC throughout simulation

Code snippet:
```python
# In ThermodynamicSimulationValidator.__init__():
if document:
    self.ph = document.get_thermodynamic_setting('ph', 7.0)
    self.temperature = document.get_thermodynamic_setting('temperature', 298.15)
    self.ionic_strength = document.get_thermodynamic_setting('ionic_strength', 0.1)
else:
    # Use defaults
    self.ph = 7.0
    self.temperature = 298.15
    self.ionic_strength = 0.1
```

Problem:
  Even if model has "pH_lysosome" = 5.0 and "pH_cytoplasm" = 7.2,
  validation uses single static value (e.g., 7.0) for ALL reactions!

Impact:
  • Equilibrium validation uses wrong pH for compartment-specific reactions
  • ATP hydrolysis ΔG calculated with wrong pH
  • Temperature-dependent Keq corrections use static T
  • Spatial thermodynamics IGNORED
""")
    
    print("\n3. GIBBS FREE ENERGY CALCULATIONS (Static ✗)")
    print("-" * 70)
    print("""
Location: src/shypn/thermodynamics/gibbs_calculator.py

Current behavior:
  ✗ Uses pH/T passed as function arguments
  ✗ Typically comes from static document settings
  ✗ No awareness of spatial places

Example call chain:
  validator.validate_reversible_reaction(...)
    → uses self.ph (static from document)
    → calculator.calculate_delta_g_reaction(ph=self.ph, ...)
    → WRONG if reaction occurs in compartment with different pH!

Real-world scenario:
  Model: Lysosomal drug trapping
    • pH_cytoplasm = 7.2
    • pH_lysosome = 5.0
    • Drug_neutral ⇌ Drug_ionized (pH-dependent)
  
  Current: Uses pH=7.0 for BOTH compartments (WRONG)
  Should: Use pH=7.2 for cytoplasm, pH=5.0 for lysosome
""")
    
    print("\n4. COMPOUND DATA PROVIDER (Static ✗)")
    print("-" * 70)
    print("""
Location: src/shypn/data/canvas/document_model.py, line 781-804

Current behavior:
  ✗ Queries compounds with static document settings
  ✗ ΔGf cached at document pH/T, not place-specific

Code snippet:
```python
def enrich_place_thermodynamics(self, place: Place, compound_id: str):
    ph = self.thermodynamic_settings.get('ph', 7.0)  # STATIC
    temp = self.thermodynamic_settings.get('temperature', 298.15)  # STATIC
    
    compound_data = self._thermo_provider.get_compound(
        compound_id, ph=ph, temperature=temp
    )
```

Problem:
  • All places get ΔGf at same pH/T
  • No support for pH gradients affecting ΔGf
  • Mitochondrial vs cytoplasmic compounds treated identically
""")


def explain_why_this_matters():
    """Explain biological scenarios where this causes problems."""
    
    print_section("WHY THIS MATTERS: BIOLOGICAL SCENARIOS", "=")
    
    scenarios = [
        {
            'name': 'Lysosomal Drug Trapping',
            'description': """
Weak base drugs concentrate in acidic lysosomes:
  • Cytoplasm: pH 7.2, Drug mostly neutral → permeable
  • Lysosome: pH 5.0, Drug mostly ionized → trapped
  
Thermodynamic issue:
  Drug_neutral ⇌ Drug_ionized
  Keq = 10^(pH - pKa)
  
  At pH 7.2: Keq = 10^(7.2-7.0) = 1.58 (58% ionized)
  At pH 5.0: Keq = 10^(5.0-7.0) = 0.01 (99% ionized)
  
Current system: Uses single pH → CANNOT model this!
Should: Read pH from "pH_cytoplasm" and "pH_lysosome" places
""",
        },
        {
            'name': 'Mitochondrial Membrane Potential',
            'description': """
Proton gradient drives ATP synthesis:
  • Matrix: pH 7.8
  • Intermembrane space: pH 7.0
  • ΔpH = 0.8 → contributes to proton-motive force
  
Thermodynamic issue:
  ATP synthesis: ADP + Pi + H+ (IMS) → ATP + H2O + H+ (matrix)
  ΔG depends on pH difference!
  
  ΔG_ATP = ΔG°' + RT*ln([ATP]/([ADP][Pi])) + n*F*ΔΨ - n*RT*ΔpH
  
  If ΔpH = 0.8: Contributes ~4.5 kJ/mol (significant!)
  
Current system: Single pH → misses ΔpH contribution
Should: Read from "pH_matrix" and "pH_IMS" places
""",
        },
        {
            'name': 'Temperature Gradients (Fever)',
            'description': """
Core body temperature vs peripheral:
  • Core (brain, organs): 37°C (310.15 K)
  • Skin/extremities: 33°C (306.15 K)
  • During fever: Core can reach 40°C (313.15 K)
  
Thermodynamic issue:
  All enzyme rates scale with temperature (Arrhenius):
    k(T) = A * exp(-Ea / RT)
  
  Q10 ≈ 2-3 for most enzymes:
    • 37°C → 40°C: Rate increases ~15%
    • 37°C → 33°C: Rate decreases ~15%
  
Current system: Single T → all reactions same temp
Should: Read from "Temperature_core" and "Temperature_peripheral" places
""",
        },
        {
            'name': 'pH Oscillations in Glycolysis',
            'description': """
Yeast glycolysis shows pH oscillations:
  • pH cycles between 6.8 and 7.2 with ~5 min period
  • Due to H+ production/consumption
  
Thermodynamic issue:
  Many reactions pH-sensitive:
    • Phosphofructokinase: pH optimum 7.0
    • Pyruvate kinase: inhibited at low pH
  
  Reaction rates should oscillate with pH!
  
Current system: Fixed pH → cannot model oscillations
Should: Have dynamic "pH_cytoplasm" place that changes
""",
        },
        {
            'name': 'Ionic Strength Effects on Enzymes',
            'description': """
Charged molecules affected by ionic strength:
  • Blood plasma: I = 0.15 M (high [Na+], [Cl-])
  • Intracellular: I = 0.1-0.2 M
  • Extracellular matrix: I varies
  
Thermodynamic issue:
  Debye-Hückel correction to ΔG:
    ΔG_corrected = ΔG° + corrections(I)
  
  For charged substrates:
    • High I: Activity coefficient changes
    • Affects binding, catalysis
  
Current system: Single I globally
Should: Read from "IonicStrength_blood" vs "IonicStrength_ECM"
""",
        },
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"{i}. {scenario['name']}")
        print("-" * 70)
        print(scenario['description'])
        print()


def show_code_locations():
    """Show exact files and lines that need modification."""
    
    print_section("CODE LOCATIONS REQUIRING FIXES", "=")
    
    print("""
Files that use STATIC thermodynamic properties:
""")
    
    locations = [
        {
            'file': 'src/shypn/thermodynamics/simulation_integration.py',
            'lines': '80-92',
            'issue': 'ThermodynamicSimulationValidator uses static document pH/T',
            'fix': 'Add methods to query spatial places at validation time'
        },
        {
            'file': 'src/shypn/thermodynamics/simulation_integration.py',
            'lines': '114-150',
            'issue': 'validate_reversible_reaction() uses self.ph, self.temperature',
            'fix': 'Accept optional place names, query current state'
        },
        {
            'file': 'src/shypn/data/canvas/document_model.py',
            'lines': '781-804',
            'issue': 'enrich_place_thermodynamics() uses static settings',
            'fix': 'Allow per-place pH/T specification'
        },
        {
            'file': 'src/shypn/thermodynamics/gibbs_calculator.py',
            'lines': '126-200',
            'issue': 'calculate_delta_g_reaction() uses passed pH/T args',
            'fix': 'Add support for place-specific lookups'
        },
        {
            'file': 'src/shypn/engine/simulation/controller.py',
            'lines': '378-516',
            'issue': 'validate_thermodynamics() uses static settings',
            'fix': 'Query places during validation'
        },
    ]
    
    for loc in locations:
        print(f"📁 {loc['file']}")
        print(f"   Lines: {loc['lines']}")
        print(f"   Issue: {loc['issue']}")
        print(f"   Fix:   {loc['fix']}")
        print()


def propose_solution():
    """Propose implementation strategy."""
    
    print_section("PROPOSED SOLUTION: PLACE-AWARE THERMODYNAMICS", "=")
    
    print("""
DESIGN PRINCIPLES:
------------------

1. **Backward Compatibility**:
   • Keep static document settings as DEFAULT
   • Only use places if they exist
   • Fall back to document settings

2. **Hierarchical Lookup**:
   Priority order:
     1. Explicit place specified in transition properties
     2. Spatial place matching transition location
     3. Global spatial place (e.g., "pH_global")
     4. Document static settings
     5. Hard-coded defaults

3. **Transition-Specific Context**:
   Each transition can specify its compartment:
     transition.properties['compartment'] = 'lysosome'
     → Look for 'pH_lysosome', 'Temperature_lysosome'

4. **Dynamic Validation**:
   Run validation with current marking state, not static values


IMPLEMENTATION STEPS:
---------------------

Step 1: Add MarkingContext class
```python
@dataclass
class ThermodynamicContext:
    \"\"\"Thermodynamic conditions for a specific reaction.\"\"\"
    ph: float = 7.0
    temperature: float = 298.15  # K
    ionic_strength: float = 0.1  # M
    compartment: Optional[str] = None
    source: str = "default"  # "place", "document", "default"
```

Step 2: Add place lookup to ThermodynamicSimulationValidator
```python
def get_thermodynamic_context(
    self,
    transition,
    marking: Optional[Dict[str, int]] = None
) -> ThermodynamicContext:
    \"\"\"Get thermodynamic context from places or document.
    
    Priority:
      1. Transition compartment property → specific places
      2. Global thermodynamic places
      3. Document settings
      4. Defaults
    \"\"\"
    # Try transition-specific compartment
    compartment = transition.properties.get('compartment')
    if compartment and marking:
        ph_place = f"pH_{compartment}"
        temp_place = f"Temperature_{compartment}"
        
        if ph_place in marking:
            ph = marking[ph_place]
            source = "place"
        else:
            ph = self.ph  # Document default
            source = "document"
    
    # Try global places
    elif marking:
        if 'pH' in marking:
            ph = marking['pH']
            source = "place"
        elif 'pH_global' in marking:
            ph = marking['pH_global']
            source = "place"
        else:
            ph = self.ph
            source = "document"
    
    return ThermodynamicContext(
        ph=ph, temperature=temp, ionic_strength=ionic,
        compartment=compartment, source=source
    )
```

Step 3: Modify validate_reversible_reaction()
```python
def validate_reversible_reaction(
    self,
    reaction_id: str,
    k_forward: float,
    k_reverse: float,
    reactants: Dict[str, int],
    products: Dict[str, int],
    transition = None,  # NEW: pass transition
    marking: Dict[str, int] = None,  # NEW: current state
    ...
) -> ThermodynamicValidation:
    
    # Get context from places if available
    if transition and marking:
        context = self.get_thermodynamic_context(transition, marking)
        ph = context.ph
        temperature = context.temperature
    else:
        # Fallback to static
        ph = self.ph
        temperature = self.temperature
    
    # Continue with validation using dynamic pH/T...
```

Step 4: Update simulation controller
```python
# In validate_thermodynamics():
for transition in reversible_transitions:
    # Get current marking
    marking = {place.name: place.tokens for place in self.petri_net.places}
    
    validation = validator.validate_reversible_reaction(
        ...,
        transition=transition,  # Pass transition
        marking=marking  # Pass current state
    )
```

Step 5: Document usage
```
User guide addition:

SPATIAL THERMODYNAMICS
======================

To make pH/temperature dynamic:

1. Create places with special names:
   • "pH_cytoplasm" or "pH"
   • "Temperature" or "Temperature_celsius"
   • "IonicStrength" or "I"

2. Set transition compartment (optional):
   transition.properties['compartment'] = 'lysosome'
   → Will look for "pH_lysosome", "Temperature_lysosome"

3. Rate functions automatically use these places:
   rate = k * arrhenius(T=[Temperature], Ea=50) * [Substrate]

4. Validation now uses current place values:
   • Equilibrium checked with actual compartment pH
   • ΔG calculated with dynamic temperature
```


BENEFITS:
---------

✓ Biological realism: pH gradients, temperature variations
✓ Dynamic thermodynamics: Conditions change during simulation
✓ Compartment-specific: Organelles have different environments
✓ Backward compatible: Works without places (uses document settings)
✓ Validation accuracy: Checks thermodynamics under actual conditions


EXAMPLE MODELS ENABLED:
------------------------

1. Lysosomal drug trapping:
   Places: pH_cytoplasm=7.2, pH_lysosome=5.0
   → Drug ionization calculated correctly per compartment

2. Mitochondrial ATP synthesis:
   Places: pH_matrix=7.8, pH_IMS=7.0
   → Proton-motive force includes ΔpH contribution

3. Fever response:
   Places: Temperature_core=40°C, Temperature_skin=33°C
   → Different reaction rates in different tissues

4. pH oscillations:
   Place: pH_cytoplasm changes over time
   → Glycolytic oscillations emerge naturally

5. Thermal stress:
   Place: Temperature ramps 37°C → 42°C
   → Protein unfolding, heat shock response
""")


def show_quick_fix():
    """Show minimal fix for immediate improvement."""
    
    print_section("QUICK FIX (Minimal Change)", "=")
    
    print("""
For immediate improvement without full refactoring:

LOCATION: src/shypn/thermodynamics/simulation_integration.py

CHANGE: Make pH/T dynamic lookup optional

Current code:
```python
def __init__(self, tolerance=None, enable_web=False, emit_warnings=True, document=None):
    if document:
        self.ph = document.get_thermodynamic_setting('ph', 7.0)  # STATIC
        self.temperature = document.get_thermodynamic_setting('temperature', 298.15)
```

Quick fix:
```python
def __init__(self, tolerance=None, enable_web=False, emit_warnings=True, 
             document=None, use_dynamic_places=True):  # NEW flag
    self.document = document  # Store reference
    self.use_dynamic_places = use_dynamic_places
    
    if document:
        self.ph_default = document.get_thermodynamic_setting('ph', 7.0)
        self.temperature_default = document.get_thermodynamic_setting('temperature', 298.15)
    else:
        self.ph_default = 7.0
        self.temperature_default = 298.15

def _get_current_ph(self, model=None):
    \"\"\"Get pH from places or fallback to default.\"\"\"
    if not self.use_dynamic_places or model is None:
        return self.ph_default
    
    # Try to find pH place
    for place in model.places:
        if place.name.lower() in ['ph', 'ph_global', 'ph_cytoplasm']:
            return place.tokens
    
    return self.ph_default

def _get_current_temperature(self, model=None):
    \"\"\"Get temperature from places or fallback to default.\"\"\"
    if not self.use_dynamic_places or model is None:
        return self.temperature_default
    
    # Try to find temperature place
    for place in model.places:
        name_lower = place.name.lower()
        if 'temperature' in name_lower:
            if 'celsius' in name_lower:
                return place.tokens + 273.15  # Convert to Kelvin
            else:
                return place.tokens
    
    return self.temperature_default
```

Then modify validation calls:
```python
def validate_reversible_reaction(self, ..., model=None):
    ph = self._get_current_ph(model)  # Dynamic lookup
    temperature = self._get_current_temperature(model)  # Dynamic lookup
    # ... rest of validation
```

Benefits:
  ✓ Minimal code change (< 50 lines)
  ✓ Backward compatible (flag defaults to True)
  ✓ Enables spatial thermodynamics immediately
  ✓ No API breaking changes
""")


def main():
    """Main analysis."""
    print("=" * 70)
    print("THERMODYNAMIC PLACE INTEGRATION ANALYSIS")
    print("Why hard-coded properties instead of spatial places?")
    print("=" * 70)
    print()
    print("Issue: Thermodynamic validation uses static document settings")
    print("       instead of reading from dynamic spatial places.")
    print()
    
    # Analysis sections
    analyze_current_implementation()
    explain_why_this_matters()
    show_code_locations()
    propose_solution()
    show_quick_fix()
    
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print("""
CURRENT STATE:
  • Rate functions: ✓ CAN read from places (stochastic_behavior.py)
  • Validation: ✗ Uses static document settings
  • Gibbs calculations: ✗ Uses static values
  • Compound lookup: ✗ Uses static pH/T

IMPACT:
  • Cannot model pH gradients (lysosomes, mitochondria)
  • Cannot model temperature variations (fever, thermal stress)
  • Cannot model compartment-specific thermodynamics
  • Validation inaccurate for multi-compartment models

SOLUTION:
  1. Add dynamic place lookup to validation system
  2. Pass current marking state to thermodynamic calculations
  3. Use compartment-aware context lookup
  4. Maintain backward compatibility with document settings

RECOMMENDATION:
  Implement "Quick Fix" first (< 1 hour), then full refactoring later.
  This enables spatial thermodynamics without breaking existing models.
""")
    
    print("\nYour observation is CORRECT and IMPORTANT! 🎯")
    print("This is a missing feature that limits biological realism.")
    print("The fix is straightforward and highly beneficial.")


if __name__ == "__main__":
    main()
