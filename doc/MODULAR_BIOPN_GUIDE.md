# Modular Bio-PN Architecture - User Guide

## Overview

SHYPN now supports **modular Biological Petri Nets** based on the 13-tuple formalism with **Ψ (Psi) signal places**. This architecture enables:

- **Compartmentalization**: Organize networks into modules representing cellular compartments
- **Information flow without mass transfer**: Signal places broadcast state without token consumption
- **Hierarchical modeling**: Nest modules for multi-scale biological systems
- **Architectural validation**: Analyze module coupling and independence

---

## Core Concepts

### 1. Modules

**Modules** partition a Petri net into subsystems, typically representing:
- Cellular compartments (cytoplasm, nucleus, mitochondria)
- Functional units (glycolysis pathway, TCA cycle)
- Spatial regions (extracellular space, membrane)

**Properties:**
- `module_id`: Unique identifier (e.g., `M1`, `M_cytoplasm`)
- `places`: Set of places belonging to this module
- `transitions`: Set of transitions belonging to this module
- `boundary_signals`: Set of signal places at module boundaries
- `collapsed`: Boolean for visualization state

**Architectural Rules:**
- Regular arcs **must NOT** cross module boundaries
- Only **signal arcs** (to/from Ψ places) can cross boundaries
- Each place/transition belongs to exactly one module (or none)

### 2. Signal Places (Ψ)

**Signal places** represent information without mass transfer:
- **Read-only**: Transitions can read signal values but do NOT consume tokens
- **Broadcast**: Multiple transitions across modules can read the same signal simultaneously
- **External control**: Signal token values are set externally (environment, user, regulatory logic)

**Visual representation:**
- Hexagon shape (vs. circle for regular places)
- Blue border color
- Ψ symbol with subscript indicating type
- Dashed arcs connecting to transitions

### 3. Signal Types

Four signal classifications based on biological function:

#### Ψₑ - Energy Signals (`ENERGY`)
Metabolic state indicators:
- **Examples**: ATP/ADP ratio, NADH/NAD+ ratio, energy charge
- **Usage**: Coordinate metabolic pathways based on cell energy status
- **Typical values**: Ratios (0.0-1.0) or concentrations

#### Ψᵣ - Regulatory Signals (`REGULATORY`)
Gene expression and regulation:
- **Examples**: Transcription factors, kinases, cAMP levels
- **Usage**: Control gene expression, signaling cascades
- **Typical values**: Active/inactive (0/1) or concentrations

#### Ψq - Quorum Signals (`QUORUM`)
Cell-cell communication:
- **Examples**: AHL (acyl-homoserine lactone), pheromones, autoinducers
- **Usage**: Coordinate population-level behaviors (biofilm formation, virulence)
- **Typical values**: Concentrations (threshold-dependent)

#### Ψₛ - Spatial Signals (`SPATIAL`)
Location and compartment sensing:
- **Examples**: Membrane markers, location tags, positional information
- **Usage**: Enable compartment-aware reactions
- **Typical values**: Binary (present/absent) or gradients

---

## Usage Patterns

### Pattern 1: SBML Auto-Import (Automatic)

When importing SBML models with compartments:

```python
from shypn.services.sbml_compartment_module_service import SBMLCompartmentModuleService

# Service automatically:
# 1. Creates modules from compartments
# 2. Assigns places/transitions to modules
# 3. Detects cross-compartment modifiers as REGULATORY signals
# 4. Validates module boundaries
service = SBMLCompartmentModuleService()
warnings = service.convert_compartments_to_modules(document, pathway, model_id)

# Check results
for module_id, module in document.modules.items():
    print(f"{module.name}: {len(module.places)} places, {len(module.boundary_signals)} signals")
```

**What gets auto-detected:**
- **Modules**: One per SBML compartment
- **Signal places**: Cross-compartment modifiers (e.g., transcription factors)
- **Signal type**: REGULATORY (for modifiers), ENERGY (ATP, NADH patterns)

### Pattern 2: Manual Module Creation (Interactive)

For hand-drawn networks or custom modules:

```python
# 1. Create module
module = document.create_module(
    name="Glycolysis",
    compartment_id="cytoplasm"  # Optional
)

# 2. Assign places to module
for place in [glucose, g6p, f6p, fbp]:
    place.module_id = module.module_id
    module.places.add(place)

# 3. Assign transitions to module
for transition in [hexokinase, pgi, pfk]:
    transition.module_id = module.module_id
    module.transitions.add(transition)

# 4. Designate signal places
atp_signal = document.places["ATP"]
atp_signal.is_signal_place = True
atp_signal.signal_type = SignalType.ENERGY
module.boundary_signals.add(atp_signal)
```

### Pattern 3: Signal Detection (Semi-automatic)

Suggest signal places based on network topology:

```python
from shypn.services.signal_detection_service import SignalDetectionService

detector = SignalDetectionService()
suggestions = detector.detect_signals(
    places=document.places.values(),
    transitions=document.transitions.values(),
    arcs=document.arcs,
    strategies=['modifier_only', 'energy_metabolites', 'regulatory_factors']
)

# Review suggestions
for suggestion in suggestions:
    print(f"{suggestion.place_id}: {suggestion.signal_type} "
          f"(confidence: {suggestion.confidence:.2f})")
    print(f"  Reason: {suggestion.reason}")

# Apply high-confidence suggestions
applied = detector.apply_signal_suggestions(
    suggestions,
    confidence_threshold=0.75
)
print(f"Applied {applied} signal place designations")
```

### Pattern 4: Module Validation

Check architectural quality:

```python
from shypn.services.module_coupling_service import ModuleCouplingValidationService

validator = ModuleCouplingValidationService()
result = validator.validate_coupling(
    modules=document.modules.values(),
    places=document.places.values(),
    transitions=document.transitions.values(),
    arcs=document.arcs
)

print(f"Architecture Quality: {result.independence_score:.2%}")
print(f"Signal-only coupling: {result.is_signal_only_coupling}")

if result.violations:
    print(f"\n⚠ Found {len(result.violations)} violations:")
    for v in result.violations:
        print(f"  {v.violation_type}: {v.description}")
```

---

## Simulation Semantics

### Signal Place Behavior

During simulation (all modes: continuous, stochastic, immediate, timed):

**Consumption Phase:**
- Regular places: Tokens are consumed (subtracted)
- **Signal places: Tokens are NOT consumed** ✓
- Consumed map records signal reads (informational only)

**Production Phase:**
- Regular places: Tokens are produced (added)
- **Signal places: Tokens are NOT produced** ✓
- Produced map records write attempts (informational only)

**Enablement Check:**
- Regular places: Require sufficient tokens
- **Signal places: Do NOT block enablement** ✓
- Transitions can fire even if signal has 0 tokens

**Example: Quorum Sensing**

```
Before:  AHL (signal) = 10 tokens
Fire T1: Consumes 1 AHL, produces 1 Enzyme
After:   AHL (signal) = 10 tokens  ← Unchanged!

Fire T2: Also consumes 1 AHL, produces 1 Reporter
After:   AHL (signal) = 10 tokens  ← Still unchanged!

Result: Both T1 and T2 can read the same AHL signal simultaneously
```

### Module Isolation

Modules remain isolated during simulation:
- Transitions only affect places within their module (or signals)
- No regular arcs cross module boundaries
- Signal places enable information flow without violating isolation

---

## Analysis Tools

### CLI Module Analysis

```bash
# Generate comprehensive report
python -m cli.analysis.module_analysis model.json

# JSON output for programmatic use
python -m cli.analysis.module_analysis model.json --format json

# Save report
python -m cli.analysis.module_analysis model.json > report.txt
```

**Report sections:**
1. **Module Connectivity**: Adjacency matrix, isolated modules, hub modules
2. **Signal Coupling Strength**: Coupling matrix, strongest couplings by signal count
3. **Module Independence**: Per-module scores, arc violations, quality score
4. **Boundary Signal Usage**: Signal distribution, broadcast signals, unused signals

**Key metrics:**
- **Independence score** (0-1): Higher = more self-contained modules
- **Coupling strength**: Number of signals between module pairs
- **Broadcast ratio**: Fraction of signals read by multiple modules
- **Architecture quality** (0-1): Overall design quality score

### Validation Service

```python
from shypn.services.module_coupling_service import ModuleCouplingValidationService

validator = ModuleCouplingValidationService()
result = validator.validate_coupling(modules, places, transitions, arcs)

# Check results
if result.is_signal_only_coupling:
    print("✓ Architecture follows signal-only coupling principle")
else:
    print(f"✗ Found {len(result.violations)} boundary violations")

# Independence matrix
for mod_i in modules:
    for mod_j in modules:
        coupling = result.coupling_matrix.get((mod_i.module_id, mod_j.module_id), 0)
        print(f"{mod_i.name} → {mod_j.name}: {coupling} signals")
```

---

## Visualization

### Module Rendering

Modules appear as colored boundary boxes on canvas:

**Expanded state:**
- Rounded rectangle around all module contents
- Header bar with module name and collapse button (▼)
- Color-coded by compartment (9 predefined colors)
- Subtle border and shadow

**Collapsed state:**
- Compact box showing only boundary signals
- Header with expand button (▶)
- Internal places/transitions hidden
- Useful for large multi-module models

### Visual Elements

**Signal places:**
- **Shape**: Hexagon (6-sided polygon)
- **Border**: Blue (0.0, 0.4, 0.8)
- **Symbol**: Ψ with type subscript (Ψₑ, Ψᵣ, Ψq, Ψₛ)
- **Glow**: Blue halo effect

**Signal arcs:**
- **Style**: Dashed line (8px dash, 4px gap)
- **vs. Regular arcs**: Solid lines
- **Arrowheads**: Always solid

**Module colors** (by compartment):
- Cytosol: Light blue
- Nucleus: Light green
- Mitochondria: Orange
- ER: Purple
- Golgi: Yellow
- Peroxisome: Pink
- Lysosome: Red
- Extracellular: Gray
- Membrane: Teal

---

## Examples

### Example 1: Glycolysis with Energy Sensing

```python
# Module: Glycolysis
module_glycolysis = document.create_module("Glycolysis", "cytoplasm")

# Regular places (mass transfer)
glucose = create_place("Glucose", module=module_glycolysis)
g6p = create_place("G6P", module=module_glycolysis)
pyruvate = create_place("Pyruvate", module=module_glycolysis)

# Signal place (energy state)
atp_adp_ratio = create_place("ATP_ADP_Ratio", module=module_glycolysis)
atp_adp_ratio.is_signal_place = True
atp_adp_ratio.signal_type = SignalType.ENERGY
atp_adp_ratio.tokens = 0.8  # High energy state

# Transitions sense energy state
pfk = create_transition("Phosphofructokinase", module=module_glycolysis)
pfk.rate_function = "Vmax * Glucose * (1 - ATP_ADP_Ratio)"  # Inhibited by high ATP

# Energy signal modulates flux without being consumed
```

### Example 2: Quorum Sensing (Multi-cell)

```python
# Module per cell
cell1 = document.create_module("Cell_1", "cytoplasm")
cell2 = document.create_module("Cell_2", "cytoplasm")

# Shared signal place (quorum molecule)
ahl = create_place("AHL", module=None)  # Global/extracellular
ahl.is_signal_place = True
ahl.signal_type = SignalType.QUORUM
ahl.tokens = 0  # Initially no quorum

# Each cell senses AHL and responds
for cell_module in [cell1, cell2]:
    sensor = create_transition(f"AHL_Sensor", module=cell_module)
    sensor.rate_function = "k_sense * AHL / (K_d + AHL)"  # Hill-like
    
    # AHL is read but not consumed - all cells see the same value
```

### Example 3: Nucleus-Cytoplasm Regulation

```python
# Module: Nucleus
nucleus = document.create_module("Nucleus", "nucleus")
transcription = create_transition("Transcribe_Gene", module=nucleus)

# Module: Cytoplasm  
cytoplasm = document.create_module("Cytoplasm", "cytoplasm")
translation = create_transition("Translate_mRNA", module=cytoplasm)

# Signal: Transcription factor (crosses boundary)
tf_active = create_place("TF_Active", module=nucleus)
tf_active.is_signal_place = True
tf_active.signal_type = SignalType.REGULATORY

# TF regulates transcription in nucleus
create_arc(tf_active, transcription, weight=1, kind='modifier')  # Dashed arc

# mRNA transported from nucleus to cytoplasm (regular arc within modules)
mrna_nuclear = create_place("mRNA", module=nucleus)
mrna_cyto = create_place("mRNA_cyto", module=cytoplasm)
export = create_transition("Export", module=None)  # Boundary transition
create_arc(mrna_nuclear, export)
create_arc(export, mrna_cyto)
```

---

## Best Practices

### 1. Module Design

**Do:**
- ✓ Keep modules cohesive (related processes together)
- ✓ Use signals for information flow between modules
- ✓ Name modules after biological compartments or pathways
- ✓ Validate architecture with analysis tools

**Don't:**
- ✗ Create regular arcs crossing module boundaries
- ✗ Make modules too small (overhead) or too large (defeats purpose)
- ✗ Use signals for mass transfer (they're read-only)

### 2. Signal Place Usage

**When to use signals:**
- ✓ Environmental sensing (nutrients, stress)
- ✓ Regulatory control (transcription factors)
- ✓ Cell-cell communication (quorum molecules)
- ✓ Metabolic state (energy charge, redox state)

**When NOT to use signals:**
- ✗ Metabolites that are consumed/produced
- ✗ Intermediate species in reactions
- ✗ Places with complex token dynamics

### 3. SBML Import

**Auto-detection works best when:**
- ✓ SBML has explicit compartments
- ✓ Modifiers are used for regulatory interactions
- ✓ Compartment boundaries are meaningful

**Manual refinement needed for:**
- ⚠ Energy signals (ATP/NADH) - often not explicit modifiers
- ⚠ Quorum signals - typically extracellular species
- ⚠ Spatial signals - abstract concepts not in SBML

### 4. Simulation

**Remember:**
- ✓ Signal token values should be set externally before simulation
- ✓ Use formula parameters or manual token updates for dynamic signals
- ✓ Check event logs to verify signal broadcast behavior
- ✓ Module isolation is maintained automatically

---

## Troubleshooting

### Issue: "Arc crosses module boundary"

**Problem**: Regular arc connects places/transitions in different modules

**Solution**:
1. Check if target should be a signal place
2. Rethink module boundaries - should these be in the same module?
3. Use validation service to identify all violations

```python
result = validator.validate_coupling(modules, places, transitions, arcs)
for violation in result.violations:
    if violation.violation_type == 'ARC_CROSSES_BOUNDARY':
        print(f"Arc {violation.arc.id}: {violation.description}")
```

### Issue: "Signal place has tokens changing during simulation"

**Problem**: Signal place is being consumed/produced by transitions

**Check**:
1. Verify `is_signal_place = True` or `signal_type` is set
2. Check simulation event logs - should show reads but no token changes
3. Signal changes should only come from external updates

### Issue: "Module independence score is low"

**Problem**: Modules have too many external dependencies

**Analysis**:
```bash
python -m cli.analysis.module_analysis model.json
```

**Solutions**:
- Increase module size (merge related submodules)
- Convert cross-module connections to signals
- Rethink module boundaries

### Issue: "Unused signals detected"

**Problem**: Signal places with no reading transitions

**Solution**:
1. Remove unused signals (cleanup)
2. Add transitions that sense the signal
3. Check if signal scope should be broadened

---

## API Reference

### Key Classes

**Module** (`src/shypn/netobjs/module.py`):
```python
class Module:
    module_id: str
    name: str
    places: Set[Place]
    transitions: Set[Transition]
    boundary_signals: Set[Place]
    collapsed: bool
    color: Tuple[float, float, float]
    parent_module: Optional[str]
    child_modules: Set[str]
```

**SignalType** (`src/shypn/netobjs/signal_type.py`):
```python
class SignalType(Enum):
    QUORUM = "quorum"
    ENERGY = "energy"
    REGULATORY = "regulatory"
    SPATIAL = "spatial"
```

**Place** (signal extensions in `src/shypn/netobjs/place.py`):
```python
class Place(PetriNetObject):
    is_signal_place: bool
    signal_type: Optional[SignalType]
    signal_scope: List[str]
    module_id: Optional[str]
```

### Key Services

**SBMLCompartmentModuleService**:
```python
convert_compartments_to_modules(document, pathway, model_id) -> List[str]
```

**SignalDetectionService**:
```python
detect_signals(places, transitions, arcs, strategies) -> List[SignalSuggestion]
apply_signal_suggestions(suggestions, confidence_threshold) -> int
```

**ModuleCouplingValidationService**:
```python
validate_coupling(modules, places, transitions, arcs) -> ValidationResult
```

---

## Further Reading

- **INTEGRATION_PLAN_SIGNAL_ARCHITECTURE.md**: Implementation phases and design decisions
- **SIGNAL_HIERARCHY_THEORY.md**: Mathematical formalism (13-tuple Bio-PN)
- **cli/analysis/module_analysis.py**: Analysis tool source code

---

## Changelog

**Version 1.0** (December 2025):
- Initial modular Bio-PN implementation
- Signal place support in all simulation modes
- Module visualization with collapse/expand
- CLI analysis tools
- SBML auto-import with compartment mapping
