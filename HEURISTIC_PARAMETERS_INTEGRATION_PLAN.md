# Heuristic Parameters Integration - Strategic Plan (DATA-CENTRIC)

**Date**: November 4, 2025  
**Status**: 📋 **PLANNING PHASE - REVISED FOR DATA-CENTRICITY**  
**Goal**: Create intelligent kinetic parameter inference system with local database

---

## Executive Summary

### The Vision (REVISED)

Create a new **"Heuristic Parameters"** category in the Pathway Operations panel that:
1. **Analyzes ALL transition types** (immediate, timed, stochastic, continuous) in the model
2. **Identifies transition semantics** (burst, deterministic, mass action, differential equations)
3. **Fetches/infers appropriate parameters** per transition type from multiple sources
4. **Cross-references** multiple biochemical databases (KEGG, SABIO-RK, BioModels)
5. **Reconciles** organism differences (human, yeast, E. coli, generic)
6. **Stores** curated results in a local database for reuse
7. **Learns** from user selections to improve recommendations

### Key Architectural Principle: **DATA-CENTRIC, TYPE-AWARE**

Instead of treating all transitions uniformly, the system:
- ✅ **Detects** transition type from model (immediate, timed, stochastic, continuous)
- ✅ **Infers** biological semantics (burst, deterministic, mass action, differential)
- ✅ **Fetches** type-appropriate parameters (rate, delay, lambda, Vmax/Km)
- ✅ **Applies** parameters correctly based on transition type

---

## Transition Type Analysis (NEW - CORE ARCHITECTURE)

### The Four Transition Types in Petri Nets

Shypn supports 4 transition types, each with different semantics and parameter needs:

#### 1. **Immediate Transitions** (Priority-Based, Zero Time)

**Biological Semantics**: **Burst Events** - Instantaneous reactions with priority
- Examples: Ion channel opening, allosteric activation, binding events
- Behavior: Fire instantly when enabled, resolved by priority/weight

**Parameters to Fetch/Infer**:
```python
{
    "type": "immediate",
    "priority": int,           # Conflict resolution (1-100)
    "weight": float,           # Probabilistic firing (0.0-1.0)
    "ec_number": str,          # Optional: "2.7.1.1"
    "reaction_id": str,        # Optional: "R00299"
    "organism": str,           # For documentation
    "biological_note": str     # "Burst activation of hexokinase"
}
```

**Data Sources**:
- 🔍 **KEGG**: Reaction topology, EC numbers (no timing)
- 🔍 **Literature**: Priority/weight from biological knowledge
- 🔍 **User Rules**: Default priorities for enzyme classes

**Heuristic Strategy**:
- **Heuristic 1**: Regulatory events → High priority (90-100)
- **Heuristic 2**: Enzyme catalysis → Medium priority (50-70)
- **Heuristic 3**: Transport → Low priority (10-30)
- **Heuristic 4**: Default weight = 1.0 (deterministic)

---

#### 2. **Timed Transitions** (Deterministic Delays)

**Biological Semantics**: **Timed/Deterministic Events** - Fixed delays
- Examples: Transcription delay, cell cycle phases, transport delays
- Behavior: Fire after fixed time delay when enabled

**Parameters to Fetch/Infer**:
```python
{
    "type": "timed",
    "delay": float,            # Time units (e.g., seconds, minutes)
    "time_unit": str,          # "seconds", "minutes", "hours"
    "ec_number": str,          # Optional
    "reaction_id": str,        # Optional
    "organism": str,
    "biological_note": str     # "mRNA maturation delay: 5 minutes"
}
```

**Data Sources**:
- 🔍 **BioModels**: Delay parameters from SBML models
- 🔍 **Literature**: Experimental measurements of delays
- 🔍 **User Input**: Manual delays for synthetic systems

**Heuristic Strategy**:
- **Heuristic 1**: Transcription delays → 5-20 minutes (eukaryotic)
- **Heuristic 2**: Translation delays → 2-10 minutes
- **Heuristic 3**: Transport delays → 1-5 minutes
- **Heuristic 4**: Cell cycle phases → 30-60 minutes

---

#### 3. **Stochastic Transitions** (Exponential Distribution)

**Biological Semantics**: **Mass Action Kinetics** - Probabilistic firing
- Examples: Gene expression, protein degradation, binding reactions
- Behavior: Fire with exponential distribution (rate parameter λ)

**Parameters to Fetch/Infer**:
```python
{
    "type": "stochastic",
    "lambda": float,           # Rate parameter (1/time)
    "rate_function": str,      # "mass_action(P1, P2, k)" for display
    "k_forward": float,        # Forward rate constant
    "k_reverse": float,        # Optional: Reverse rate constant
    "ec_number": str,
    "reaction_id": str,
    "organism": str,
    "temperature": float,      # 37.0°C for human
    "ph": float,               # 7.4 for physiological
    "biological_note": str     # "Stochastic gene expression"
}
```

**Data Sources**:
- ✅ **SABIO-RK**: Mass action rate constants (k values)
- ✅ **BioModels**: Stochastic parameters from genetic networks
- ✅ **Literature**: Measured rate constants

**Heuristic Strategy**:
- **Heuristic 1**: Extract k from SABIO-RK mass action kinetics
- **Heuristic 2**: Convert deterministic rates to stochastic (scaling by volume)
- **Heuristic 3**: Gene expression: λ = 0.001-0.1 (1/s) typical range
- **Heuristic 4**: Protein degradation: λ = 0.0001-0.01 (1/s)

---

#### 4. **Continuous Transitions** (Differential Equations)

**Biological Semantics**: **Enzyme Kinetics** - Continuous rates with functions
- Examples: Michaelis-Menten, Hill equations, complex regulations
- Behavior: Continuous token flow based on rate function

**Parameters to Fetch/Infer**:
```python
{
    "type": "continuous",
    "rate": float,             # Vmax (for display)
    "rate_function": str,      # "michaelis_menten(S, 100, 0.5)"
    "vmax": float,             # Maximum velocity
    "km": float,               # Michaelis constant
    "kcat": float,             # Catalytic constant (turnover number)
    "ki": float,               # Optional: Inhibition constant
    "hill_coefficient": float, # Optional: Cooperativity
    "ec_number": str,
    "reaction_id": str,
    "organism": str,
    "temperature": float,
    "ph": float,
    "enzyme_concentration": float,  # Optional: for scaling
    "biological_note": str     # "Michaelis-Menten kinetics"
}
```

**Data Sources**:
- ✅ **SABIO-RK**: Vmax, Km, Kcat, Ki (PRIMARY SOURCE)
- ✅ **BioModels**: Complete enzyme kinetic laws from SBML
- ✅ **Literature**: Published enzyme kinetics

**Heuristic Strategy**:
- **Heuristic 1**: Exact organism + EC match from SABIO-RK (95% confidence)
- **Heuristic 2**: Cross-species scaling (yeast→human, 70% confidence)
- **Heuristic 3**: BioModels SBML kinetic law extraction (85% confidence)
- **Heuristic 4**: Statistical median of multiple measurements
- **Heuristic 5**: Literature defaults by enzyme class

---

## Data Model (REVISED - TYPE-AWARE)

### Universal Parameter Schema

**Table 1: `transition_parameters` (REVISED)**
```sql
CREATE TABLE transition_parameters (
    id INTEGER PRIMARY KEY,
    
    -- Transition Type Classification
    transition_type TEXT NOT NULL CHECK(transition_type IN 
        ('immediate', 'timed', 'stochastic', 'continuous')),
    
    biological_semantics TEXT,        -- "burst", "deterministic", "mass_action", "enzyme_kinetics"
    
    -- Universal Identifiers
    ec_number TEXT,                   -- "2.7.1.1" (optional)
    enzyme_name TEXT,                 -- "hexokinase"
    reaction_id TEXT,                 -- "R00299" (KEGG)
    organism TEXT,                    -- "Homo sapiens"
    
    -- Type-Specific Parameters (JSON for flexibility)
    parameters JSON NOT NULL,         -- Type-specific parameter blob
    /*
    For immediate:   {"priority": 50, "weight": 1.0}
    For timed:       {"delay": 5.0, "time_unit": "minutes"}
    For stochastic:  {"lambda": 0.05, "k_forward": 0.05, "k_reverse": 0.01}
    For continuous:  {"vmax": 226.0, "km": 0.1, "kcat": 1500, "ki": null}
    */
    
    -- Experimental Conditions (mainly for continuous/stochastic)
    temperature REAL,                 -- 37.0 (Celsius)
    ph REAL,                          -- 7.4
    
    -- Source & Confidence
    source TEXT NOT NULL,             -- "SABIO-RK", "BioModels", "Literature", "Heuristic"
    source_id TEXT,                   -- "123456" (SABIO entry ID)
    pubmed_id TEXT,                   -- "PMID:12345678"
    confidence_score REAL,            -- 0.0-1.0
    
    -- Usage Tracking
    import_date TIMESTAMP,
    last_used TIMESTAMP,
    usage_count INTEGER DEFAULT 0,
    user_rating INTEGER,              -- 1-5 stars
    notes TEXT
);

CREATE INDEX idx_type_ec ON transition_parameters(transition_type, ec_number);
CREATE INDEX idx_ec_organism ON transition_parameters(ec_number, organism);
CREATE INDEX idx_type_confidence ON transition_parameters(transition_type, confidence_score DESC);
```

---

## Workflow: Type-Aware Parameter Inference

### Step 1: Model Analysis (NEW)

**Objective**: Scan model and classify all transitions by type

```python
def analyze_model_transitions(document_model):
    """Analyze all transitions in model and classify by type.
    
    Returns:
        {
            'immediate': [T1, T3, T5],      # Burst events
            'timed': [T2, T7],              # Deterministic delays
            'stochastic': [T4, T8, T9],     # Mass action
            'continuous': [T6, T10, T11]    # Enzyme kinetics
        }
    """
    classification = {
        'immediate': [],
        'timed': [],
        'stochastic': [],
        'continuous': []
    }
    
    for transition in document_model.transitions:
        # Check transition_type property
        t_type = transition.transition_type
        
        if t_type == 'immediate':
            classification['immediate'].append(transition)
        elif t_type == 'timed':
            classification['timed'].append(transition)
        elif t_type == 'stochastic':
            classification['stochastic'].append(transition)
        elif t_type == 'continuous':
            classification['continuous'].append(transition)
    
    return classification
```

**UI Display**:
```
┌─────────────────────────────────────────────────────┐
│ Model Analysis Results                              │
├─────────────────────────────────────────────────────┤
│ Total Transitions: 23                               │
│                                                     │
│ • Immediate (Burst):       5 transitions            │
│ • Timed (Deterministic):   2 transitions            │
│ • Stochastic (Mass Action): 8 transitions           │
│ • Continuous (Enzyme):     8 transitions            │
└─────────────────────────────────────────────────────┘
```

---

### Step 2: Type-Specific Parameter Fetching

#### 2.1 Immediate Transitions (Burst)

**Strategy**: Use biological heuristics + user rules

```python
def infer_immediate_parameters(transition):
    """Infer priority and weight for immediate transitions.
    
    Heuristics:
    1. Check if transition has EC number → Enzyme priority rules
    2. Check label for keywords (regulatory, transport, etc.)
    3. Apply default priorities by biological function
    """
    
    # Default
    priority = 50
    weight = 1.0
    confidence = 0.6
    
    # Heuristic 1: Regulatory events (high priority)
    if 'regulat' in transition.label.lower() or 'activat' in transition.label.lower():
        priority = 90
        confidence = 0.8
    
    # Heuristic 2: Enzyme catalysis (medium priority)
    elif transition.ec_number:
        priority = 60
        confidence = 0.7
    
    # Heuristic 3: Transport (low priority)
    elif 'transport' in transition.label.lower():
        priority = 30
        confidence = 0.7
    
    return {
        'priority': priority,
        'weight': weight,
        'confidence': confidence,
        'source': 'Heuristic'
    }
```

---

#### 2.2 Timed Transitions (Deterministic)

**Strategy**: Literature defaults + BioModels extraction

```python
def infer_timed_parameters(transition):
    """Infer delay for timed transitions.
    
    Sources:
    1. BioModels SBML (if equivalent reaction found)
    2. Literature defaults by biological process type
    3. User manual input (highest priority)
    """
    
    # Default
    delay = 5.0  # minutes
    confidence = 0.4
    
    # Heuristic 1: Transcription delays
    if 'transcription' in transition.label.lower() or 'mRNA' in transition.label.lower():
        delay = 10.0  # minutes (eukaryotic)
        confidence = 0.7
    
    # Heuristic 2: Translation delays
    elif 'translation' in transition.label.lower() or 'protein' in transition.label.lower():
        delay = 5.0  # minutes
        confidence = 0.7
    
    # Heuristic 3: Transport delays
    elif 'transport' in transition.label.lower():
        delay = 2.0  # minutes
        confidence = 0.6
    
    # Heuristic 4: Check BioModels for matching delay
    biomodels_delay = query_biomodels_for_delay(transition.ec_number)
    if biomodels_delay:
        delay = biomodels_delay
        confidence = 0.85
    
    return {
        'delay': delay,
        'time_unit': 'minutes',
        'confidence': confidence,
        'source': 'Heuristic' if confidence < 0.8 else 'BioModels'
    }
```

---

#### 2.3 Stochastic Transitions (Mass Action)

**Strategy**: SABIO-RK + BioModels + scaling heuristics

```python
def infer_stochastic_parameters(transition, organism='Homo sapiens'):
    """Infer lambda (rate) for stochastic transitions.
    
    Sources:
    1. SABIO-RK: Query by EC number for mass action kinetics
    2. BioModels: Extract stochastic parameters from genetic network models
    3. Scaling: Convert continuous rates to stochastic
    """
    
    # Step 1: Query SABIO-RK for mass action rates
    sabio_results = query_sabio_rk_mass_action(
        ec_number=transition.ec_number,
        organism=organism
    )
    
    if sabio_results:
        # Extract k_forward (rate constant)
        k_forward = extract_rate_constant(sabio_results)
        lambda_param = k_forward  # For first-order reactions
        
        return {
            'lambda': lambda_param,
            'k_forward': k_forward,
            'rate_function': f'mass_action({get_place_names(transition)}, {k_forward})',
            'confidence': 0.90,
            'source': 'SABIO-RK',
            'source_id': sabio_results['entry_id']
        }
    
    # Step 2: Check BioModels for stochastic parameters
    biomodels_lambda = query_biomodels_stochastic(transition.reaction_id)
    if biomodels_lambda:
        return {
            'lambda': biomodels_lambda,
            'confidence': 0.85,
            'source': 'BioModels'
        }
    
    # Step 3: Use literature defaults by process type
    if 'expression' in transition.label.lower() or 'gene' in transition.label.lower():
        lambda_param = 0.01  # 1/s (typical gene expression rate)
        confidence = 0.60
    elif 'degradation' in transition.label.lower():
        lambda_param = 0.001  # 1/s (typical protein half-life ~10 min)
        confidence = 0.60
    else:
        lambda_param = 0.05  # Generic default
        confidence = 0.40
    
    return {
        'lambda': lambda_param,
        'confidence': confidence,
        'source': 'Heuristic'
    }
```

---

#### 2.4 Continuous Transitions (Enzyme Kinetics)

**Strategy**: SABIO-RK + BioModels + cross-species scaling (EXISTING LOGIC)

```python
def infer_continuous_parameters(transition, organism='Homo sapiens'):
    """Infer Vmax, Km, Kcat, Ki for continuous transitions.
    
    This is the EXISTING heuristic system from the original plan.
    
    Sources:
    1. SABIO-RK: Primary source for enzyme kinetics
    2. BioModels: Extract from SBML kinetic laws
    3. Cross-species scaling: Yeast → Human with confidence adjustment
    """
    
    # Use the 7 heuristics from original plan:
    # - Heuristic 1: Exact Match (EC + Organism + Conditions)
    # - Heuristic 2: Close Organism Match (mammalian)
    # - Heuristic 3: Evolutionary Conservation (yeast)
    # - Heuristic 4: Generic/In Vitro
    # - Heuristic 5: BioModels Cross-Reference
    # - Heuristic 6: Statistical Aggregation
    # - Heuristic 7: Fallback Defaults
    
    # [Implementation from original plan - see previous section]
    pass  # Full implementation as documented in original plan
```

---

## Universal Fetching Pipeline

### Unified Inference Function

```python
def infer_parameters_for_transition(transition, target_organism='Homo sapiens'):
    """Universal parameter inference based on transition type.
    
    Args:
        transition: Transition object from model
        target_organism: Target organism for queries
    
    Returns:
        {
            'transition_id': 'T5',
            'transition_type': 'continuous',
            'parameters': {...},  # Type-specific
            'confidence': 0.95,
            'source': 'SABIO-RK',
            'alternatives': [...]  # Other options
        }
    """
    
    t_type = transition.transition_type
    
    if t_type == 'immediate':
        result = infer_immediate_parameters(transition)
        result['biological_semantics'] = 'burst'
    
    elif t_type == 'timed':
        result = infer_timed_parameters(transition)
        result['biological_semantics'] = 'deterministic'
    
    elif t_type == 'stochastic':
        result = infer_stochastic_parameters(transition, target_organism)
        result['biological_semantics'] = 'mass_action'
    
    elif t_type == 'continuous':
        result = infer_continuous_parameters(transition, target_organism)
        result['biological_semantics'] = 'enzyme_kinetics'
    
    else:
        raise ValueError(f"Unknown transition type: {t_type}")
    
    # Add universal metadata
    result['transition_id'] = transition.id
    result['transition_type'] = t_type
    result['ec_number'] = getattr(transition, 'ec_number', None)
    result['reaction_id'] = getattr(transition, 'reaction_id', None)
    result['organism'] = target_organism
    
    return result
```

---

## Complete Workflow Example

### Scenario: Glycolysis Pathway (Mixed Types)

**Model** (after KEGG import + manual configuration):
- 8 continuous transitions (enzyme kinetics): hexokinase, PFK, pyruvate kinase, etc.
- 2 stochastic transitions (gene expression): HK gene → HK mRNA
- 1 timed transition (maturation delay): HK mRNA → HK protein (5 min delay)
- 1 immediate transition (activation): Glucose burst → activate HK

**User Action**: Click "Analyze & Enrich Pathway"

**System Execution**:

```
Step 1: Classify Transitions
  ✓ 8 continuous (enzyme kinetics)
  ✓ 2 stochastic (gene expression)
  ✓ 1 timed (maturation delay)
  ✓ 1 immediate (activation burst)

Step 2: Fetch Parameters by Type

  Continuous (8 transitions):
    • T1 (Hexokinase):
      - Query SABIO-RK by EC 2.7.1.1 + Homo sapiens
      - Found: Vmax=226, Km=0.1, Kcat=1500
      - Confidence: 95% ⭐⭐⭐⭐⭐
    
    • T2 (PFK):
      - Query SABIO-RK by EC 2.7.1.11 + Homo sapiens
      - Found: Vmax=180, Km=0.08
      - Confidence: 92% ⭐⭐⭐⭐⭐
    
    [... 6 more enzyme kinetics ...]

  Stochastic (2 transitions):
    • T9 (Gene Expression):
      - No SABIO-RK data (genetic process)
      - Use literature default: λ=0.01 (1/s)
      - Confidence: 60% ⭐⭐⭐
    
    • T10 (mRNA Degradation):
      - No SABIO-RK data
      - Use default: λ=0.001 (1/s, ~10 min half-life)
      - Confidence: 60% ⭐⭐⭐

  Timed (1 transition):
    • T11 (mRNA Maturation):
      - Literature default: 5 minutes
      - Confidence: 70% ⭐⭐⭐

  Immediate (1 transition):
    • T12 (Glucose Activation):
      - Heuristic: Regulatory event → Priority=90
      - Confidence: 80% ⭐⭐⭐⭐

Step 3: Present Results
  ✅ 8 high confidence (continuous - auto-apply)
  ⚠️  3 medium confidence (stochastic/timed - review)
  ✓ 1 high confidence (immediate - auto-apply)

Step 4: User Reviews & Applies
  • Accepts all 8 continuous (one-click)
  • Reviews 3 medium confidence (adjusts if needed)
  • Accepts immediate burst (one-click)

Result: 12/12 transitions enriched in ~2 minutes! ✨
```

---

## Data to Fetch/Infer (COMPLETE LIST)

### Universal Fields (All Types)
- ✅ `ec_number` - Enzyme Commission number
- ✅ `reaction_id` - KEGG R-ID or other identifier  
- ✅ `organism` - Species (Homo sapiens, S. cerevisiae, etc.)
- ✅ `temperature` - Experimental temperature (°C)
- ✅ `ph` - Experimental pH
- ✅ `source` - Data provenance (SABIO-RK, BioModels, etc.)
- ✅ `confidence_score` - 0.0-1.0

### Type-Specific Parameters

#### Immediate (Burst)
- ✅ `priority` - Integer (1-100)
- ✅ `weight` - Float (0.0-1.0)

#### Timed (Deterministic)
- ✅ `delay` - Float (time value)
- ✅ `time_unit` - String ("seconds", "minutes", "hours")

#### Stochastic (Mass Action)
- ✅ `lambda` - Float (rate parameter, 1/time)
- ✅ `k_forward` - Float (forward rate constant)
- ✅ `k_reverse` - Float (optional, reverse rate constant)
- ✅ `rate_function` - String (for display: "mass_action(P1, 0.05)")

#### Continuous (Enzyme Kinetics)
- ✅ `rate` - Float (Vmax, for display)
- ✅ `vmax` - Float (maximum velocity)
- ✅ `km` - Float (Michaelis constant)
- ✅ `kcat` - Float (catalytic constant / turnover number)
- ✅ `ki` - Float (optional, inhibition constant)
- ✅ `hill_coefficient` - Float (optional, cooperativity)
- ✅ `enzyme_concentration` - Float (optional, for scaling)
- ✅ `rate_function` - String (for display: "michaelis_menten(S, 100, 0.5)")

---

## Summary of Changes (REVISED PLAN)

### What Changed

1. **✅ Type-Aware**: System now handles all 4 transition types distinctly
2. **✅ Semantic Classification**: Identifies burst, deterministic, mass action, enzyme kinetics
3. **✅ Type-Specific Fetching**: Different data sources per type
4. **✅ Universal Schema**: One table with JSON for type-specific parameters
5. **✅ Complete Parameter List**: All parameters documented (priority, delay, lambda, Vmax/Km/Kcat/Ki)

### What Stayed the Same

1. ✅ Multi-source cross-referencing (KEGG, SABIO-RK, BioModels)
2. ✅ Organism reconciliation logic
3. ✅ Confidence scoring system
4. ✅ Local database for caching
5. ✅ Learning from user selections
6. ✅ UI with preview and alternatives

### Key Benefit

**Before**: Only continuous transitions (enzyme kinetics) could be enriched  
**After**: ALL transition types can be enriched with appropriate parameters

---

## Next Steps

1. ✅ Review revised plan with team
2. ⏭️ Implement `analyze_model_transitions()` function
3. ⏭️ Implement type-specific inference functions
4. ⏭️ Update database schema with `transition_type` field
5. ⏭️ Update UI to show type-specific results
6. ⏭️ Test with mixed-type pathways (glycolysis + gene regulation)

**Document Status**: ✅ **REVISED FOR DATA-CENTRICITY - ✅ CORE IMPLEMENTATION COMPLETE**

---

## ✅ IMPLEMENTATION STATUS (November 4, 2025)

### Core Architecture - ✅ COMPLETE

**Location**: `src/shypn/crossfetch/`

✅ **Models** (`models/transition_types.py`):
- 197 lines, 5 parameter classes, clean dataclasses

✅ **Fetchers** (`fetchers/sabio_rk_kinetics_fetcher.py`):
- 269 lines, SBML parsing, HTTP requests

✅ **Inference Engine** (`inference/heuristic_engine.py`):
- 382 lines, type detection + 12 heuristic rules

✅ **Controller** (`controllers/heuristic_parameters_controller.py`):
- 229 lines, model ↔ inference ↔ UI bridge

✅ **UI Category** (`ui/panels/pathway_operations/heuristic_parameters_category.py`):
- 309 lines, GTK3 widget, Wayland-safe

**Total**: ~1,586 lines of clean OOP code

**See**: `HEURISTIC_PARAMETERS_IMPLEMENTATION.md` for details

---

## Next Steps

1. ✅ Review revised plan with team → **DONE - IMPLEMENTED**
2. ✅ Implement `analyze_model_transitions()` function → **DONE - In HeuristicInferenceEngine**
3. ✅ Implement type-specific inference functions → **DONE - 4 methods**
4. ✅ Update database schema with `transition_type` field → **DEFERRED - Phase 2**
5. 🔄 Update UI to show type-specific results → **IN PROGRESS - Basic UI complete**
6. ⏭️ Test with mixed-type pathways (glycolysis + gene regulation)

**Document Status**: ✅ **REVISED FOR DATA-CENTRICITY - ✅ CORE IMPLEMENTATION COMPLETE**

### What We Have Now

#### Three Complementary Data Sources

| Database | Provides | Limitations | Query Method |
|----------|----------|-------------|--------------|
| **KEGG** | Topology, EC numbers, R-IDs | No kinetics | Pathway ID |
| **SABIO-RK** | Kinetics (organism-specific) | No topology, no R-ID query | EC Number → SBML |
| **BioModels** | Complete models + kinetics | Limited pathways, organism mismatch | File download |

#### Current Workflow (Manual)

```
User Workflow:
1. Import KEGG → Get topology
2. Right-click transition → Query SABIO-RK by EC
3. Browse 10-150 results (deduplicated by organism)
4. Manually select "best" row
5. Click "Apply Selected"
6. Repeat for each transition
```

**Pain Points**:
- ❌ Too many manual decisions
- ❌ No guidance on "which row is best?"
- ❌ Same queries repeated across projects
- ❌ No learning from user choices
- ❌ Organism mismatch unclear (yeast vs human)

---

## The Cross-Reference Problem

### Data Integration Challenges

#### 1. **Multiple Organisms**

**Example**: Human glycolysis pathway (KEGG hsa00010)

Available kinetic data:
- **SABIO-RK**: 
  - Homo sapiens (human) - 15 entries for hexokinase
  - Saccharomyces cerevisiae (yeast) - 45 entries
  - Rattus norvegicus (rat) - 8 entries
  - Generic/in vitro - 12 entries

- **BioModels**:
  - BIOMD0000000206 - Yeast glycolysis (full kinetics)
  - BIOMD0000000XXX - E. coli metabolism (partial)

**Questions**:
- Which organism's kinetics are most applicable?
- Can we use yeast Vmax for human enzyme?
- How to normalize across organisms?

#### 2. **Multiple Values for Same Parameter**

**Example**: Hexokinase (EC 2.7.1.1) in human

SABIO-RK returns:
```
Organism         Vmax (μmol/min/mg)    Km (mM)    Temperature    pH    Source
-----------------------------------------------------------------------------
Homo sapiens     226.0                 0.1        37°C           7.4   PMID:12345678
Homo sapiens     195.4                 0.08       37°C           7.4   PMID:23456789
Homo sapiens     310.0                 0.15       25°C           7.0   PMID:34567890
S. cerevisiae    180.0                 0.12       30°C           7.0   PMID:45678901
R. norvegicus    240.0                 0.09       37°C           7.4   PMID:56789012
```

**Questions**:
- Mean? Median? Mode?
- Filter by temperature (37°C for human)?
- Filter by pH (physiological 7.4)?
- Weight by publication date (newer = better)?
- Trust which source more?

#### 3. **Missing Data**

**Example**: Import KEGG pathway with 70 reactions

Data availability:
- 20 reactions: Full kinetics in SABIO-RK (Homo sapiens)
- 15 reactions: Only yeast kinetics available
- 25 reactions: Generic/in vitro data only
- 10 reactions: **NO DATA** in any database

**Questions**:
- Use yeast kinetics for human pathway?
- Use generic kinetics (no organism)?
- Use defaults? (but what defaults?)
- Skip enrichment (leave empty)?

---

## Proposed Heuristic System

### Phase 1: Data Inference Engine

#### Inference Heuristics (Priority Order)

**Heuristic 1: Exact Match (Highest Priority)**
```
IF EC Number matches
   AND Organism matches target (e.g., Homo sapiens)
   AND Temperature = physiological (37°C for human)
   AND pH = physiological (7.4)
THEN
   → Use this data (confidence: 95%)
```

**Heuristic 2: Close Organism Match**
```
IF EC Number matches
   AND Organism is mammalian (human, mouse, rat)
   AND Target is human
THEN
   → Use mammalian data (confidence: 80%)
   → Apply scaling factor: 0.9-1.1x
```

**Heuristic 3: Evolutionary Conservation**
```
IF EC Number matches
   AND Enzyme is highly conserved (e.g., glycolysis, TCA)
   AND Organism is eukaryotic (yeast)
THEN
   → Use yeast data for human (confidence: 70%)
   → Mark as "cross-species"
```

**Heuristic 4: Generic/In Vitro**
```
IF EC Number matches
   AND No organism-specific data
   AND Generic data available
THEN
   → Use generic data (confidence: 50%)
   → Mark as "in vitro" (may need adjustment)
```

**Heuristic 5: BioModels Cross-Reference**
```
IF KEGG pathway has BioModels equivalent
   AND EC numbers match
THEN
   → Extract kinetics from BioModels SBML (confidence: 85%)
   → Note organism difference
```

**Heuristic 6: Statistical Aggregation**
```
IF Multiple values available for same (EC, Organism)
THEN
   → Calculate median (robust to outliers)
   → Calculate std deviation (uncertainty measure)
   → Filter outliers (> 2 std dev)
   → Use median ± std dev (confidence: 60-80%)
```

**Heuristic 7: Fallback Defaults**
```
IF NO data in any source
THEN
   → Use literature defaults by enzyme class
   → EC 2.7.1.x (kinases): Vmax=100, Km=0.1 mM
   → EC 3.x.x.x (hydrolases): Vmax=50, Km=0.5 mM
   → Mark as "default" (confidence: 30%)
```

---

### Phase 2: Confidence Scoring System

#### Multi-Factor Confidence Score (0-100%)

**Factors**:

1. **Source Quality** (30%)
   - SABIO-RK (peer-reviewed): 100%
   - BioModels (curated): 95%
   - Generic/in vitro: 70%
   - Literature defaults: 50%
   - Guessed defaults: 30%

2. **Organism Match** (30%)
   - Exact match (human→human): 100%
   - Mammalian (rat→human): 85%
   - Eukaryotic (yeast→human): 70%
   - Prokaryotic (E. coli→human): 50%
   - Generic (no organism): 40%

3. **Experimental Conditions** (20%)
   - Temp = physiological (37°C human): 100%
   - Temp close (30-40°C): 80%
   - Temp different (25°C): 60%
   - pH = physiological (7.4 human): 100%
   - pH close (7.0-7.6): 90%

4. **Data Consensus** (20%)
   - Multiple sources agree: 100%
   - Some variation (CV < 20%): 80%
   - High variation (CV > 50%): 50%
   - Single data point: 70%

**Final Score Formula**:
```
Confidence = (Source × 0.3) + (Organism × 0.3) + (Conditions × 0.2) + (Consensus × 0.2)
```

**Example Scoring**:
```
Hexokinase (EC 2.7.1.1) for human pathway:

Option A: SABIO-RK, Homo sapiens, 37°C, pH 7.4, 3 sources (CV=15%)
  → (100 × 0.3) + (100 × 0.3) + (100 × 0.2) + (100 × 0.2) = 100% ✅

Option B: SABIO-RK, S. cerevisiae, 30°C, pH 7.0, 1 source
  → (100 × 0.3) + (70 × 0.3) + (60 × 0.2) + (70 × 0.2) = 77%

Option C: BioModels, S. cerevisiae (BIOMD206), curated model
  → (95 × 0.3) + (70 × 0.3) + (80 × 0.2) + (80 × 0.2) = 81%

Option D: Generic in vitro, no organism
  → (70 × 0.3) + (40 × 0.3) + (60 × 0.2) + (70 × 0.2) = 59%

Option E: Literature default for kinases
  → (50 × 0.3) + (0 × 0.3) + (0 × 0.2) + (50 × 0.2) = 25%
```

**Recommendation**: Use Option A (100% confidence) ✅

---

### Phase 3: Local Database Architecture

#### Schema Design

**Table 1: `kinetic_parameters`**
```sql
CREATE TABLE kinetic_parameters (
    id INTEGER PRIMARY KEY,
    ec_number TEXT NOT NULL,              -- "2.7.1.1"
    enzyme_name TEXT,                     -- "hexokinase"
    organism TEXT NOT NULL,               -- "Homo sapiens"
    parameter_type TEXT NOT NULL,         -- "Vmax", "Km", "Kcat", "Ki"
    value REAL NOT NULL,                  -- 226.0
    unit TEXT NOT NULL,                   -- "μmol/min/mg"
    temperature REAL,                     -- 37.0 (Celsius)
    ph REAL,                              -- 7.4
    source TEXT NOT NULL,                 -- "SABIO-RK", "BioModels", "Manual"
    source_id TEXT,                       -- "123456" (SABIO entry ID)
    pubmed_id TEXT,                       -- "PMID:12345678"
    confidence_score REAL,                -- 0.0-1.0 (calculated)
    import_date TIMESTAMP,                -- When added to local DB
    last_used TIMESTAMP,                  -- Last time user selected this
    usage_count INTEGER DEFAULT 0,        -- How many times user picked this
    user_rating INTEGER,                  -- 1-5 stars (optional user feedback)
    notes TEXT                            -- User/system annotations
);

CREATE INDEX idx_ec_organism ON kinetic_parameters(ec_number, organism);
CREATE INDEX idx_confidence ON kinetic_parameters(confidence_score DESC);
```

**Table 2: `pathway_enrichments`**
```sql
CREATE TABLE pathway_enrichments (
    id INTEGER PRIMARY KEY,
    pathway_id TEXT NOT NULL,             -- "hsa00010" (KEGG ID)
    pathway_name TEXT,                    -- "Glycolysis"
    reaction_id TEXT,                     -- "R00299" (KEGG R-ID)
    transition_id TEXT,                   -- "T5" (internal Shypn ID)
    parameter_id INTEGER,                 -- FK to kinetic_parameters
    applied_date TIMESTAMP,
    project_path TEXT,                    -- Where this enrichment was used
    FOREIGN KEY (parameter_id) REFERENCES kinetic_parameters(id)
);
```

**Table 3: `heuristic_cache`**
```sql
CREATE TABLE heuristic_cache (
    id INTEGER PRIMARY KEY,
    query_key TEXT UNIQUE NOT NULL,       -- Hash of (ec_number, organism, conditions)
    recommended_parameter_id INTEGER,     -- Best match from kinetic_parameters
    alternatives TEXT,                    -- JSON array of other options
    confidence_score REAL,
    last_updated TIMESTAMP,
    FOREIGN KEY (recommended_parameter_id) REFERENCES kinetic_parameters(id)
);
```

**Table 4: `organism_compatibility`**
```sql
CREATE TABLE organism_compatibility (
    source_organism TEXT,                 -- "S. cerevisiae"
    target_organism TEXT,                 -- "Homo sapiens"
    enzyme_class TEXT,                    -- "EC 2.7.1.x" (kinases)
    compatibility_score REAL,             -- 0.0-1.0
    notes TEXT                            -- "Glycolysis enzymes highly conserved"
);
```

---

### Phase 4: UI Design - "Heuristic Parameters" Category

#### Panel Layout

```
┌─────────────────────────────────────────────────────────┐
│  Pathway Operations Panel                              │
├─────────────────────────────────────────────────────────┤
│  Categories:                                            │
│    • KEGG Import                                        │
│    • SBML Import                                        │
│    • BRENDA Enrichment                                  │
│    • SABIO-RK Enrichment                                │
│  → • Heuristic Parameters ⭐ NEW                        │
│    • Pathway Visualization                              │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  Heuristic Parameters                                   │
├─────────────────────────────────────────────────────────┤
│  Target Pathway:  [hsa00010 - Glycolysis          ▼]   │
│  Target Organism: [Homo sapiens (human)           ▼]   │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │ Configuration                                    │  │
│  ├──────────────────────────────────────────────────┤  │
│  │ ☑ Use SABIO-RK (online queries)                 │  │
│  │ ☑ Use BioModels (local/downloaded)              │  │
│  │ ☑ Use local database cache                      │  │
│  │ ☐ Use generic/in vitro data (lower confidence)  │  │
│  │ ☐ Use cross-species data (e.g., yeast→human)    │  │
│  │                                                  │  │
│  │ Minimum Confidence: [70%              ][slider] │  │
│  │ Temperature Range:  [35-39°C          ][range]  │  │
│  │ pH Range:          [7.2-7.6           ][range]  │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  [🔍 Analyze Pathway] [⚙️ Advanced Options]            │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │ Analysis Results (23 transitions)                │  │
│  ├──────────────────────────────────────────────────┤  │
│  │ ✅ High Confidence (15) - Ready to apply         │  │
│  │ ⚠️  Medium Confidence (6) - Review recommended   │  │
│  │ ❌ Low/No Data (2) - Manual intervention needed  │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │ Preview (Hexokinase - T5)             [→ Next]  │  │
│  ├──────────────────────────────────────────────────┤  │
│  │ Transition: T5 (Hexokinase)                     │  │
│  │ EC Number:  2.7.1.1                              │  │
│  │ KEGG ID:    R00299                               │  │
│  │                                                  │  │
│  │ Recommended: SABIO-RK #123456                    │  │
│  │   Organism:   Homo sapiens                       │  │
│  │   Vmax:       226.0 μmol/min/mg                  │  │
│  │   Km:         0.1 mM                             │  │
│  │   Conditions: 37°C, pH 7.4                       │  │
│  │   Source:     PMID:12345678                      │  │
│  │   Confidence: ⭐⭐⭐⭐⭐ 95%                        │  │
│  │                                                  │  │
│  │ Alternatives (3):                                │  │
│  │   • Yeast data    (Confidence: 77%) [Use This]  │  │
│  │   • Rat data      (Confidence: 82%) [Use This]  │  │
│  │   • BioModels     (Confidence: 81%) [Use This]  │  │
│  │                                                  │  │
│  │ [✓ Accept] [✎ Edit] [⊗ Skip] [📊 Details]       │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  [✨ Apply All High Confidence] [📁 Save to Database]  │
│  [📋 Export Report] [❓ Help]                          │
└─────────────────────────────────────────────────────────┘
```

---

### Phase 5: Workflow Integration

#### User Workflow (Automated)

```
Step 1: Import Pathway
  User: Import KEGG hsa00010 (Glycolysis)
  → 70 transitions created

Step 2: Open Heuristic Parameters
  User: Click "Heuristic Parameters" category
  → Panel loads with pathway detected

Step 3: Configure & Analyze
  User: Select "Homo sapiens" as target organism
  User: Set minimum confidence to 70%
  User: Click "Analyze Pathway"
  
  System:
    1. Query local database cache (instant)
    2. For missing data: Query SABIO-RK (30 sec)
    3. For missing data: Check BioModels catalog (10 sec)
    4. Apply heuristic inference rules
    5. Calculate confidence scores
    6. Rank recommendations
  
  → Results: 15 high confidence, 6 medium, 2 low

Step 4: Review & Apply
  User: Review preview for each transition
  User: Accept recommendations (or choose alternatives)
  User: Click "Apply All High Confidence"
  
  System:
    1. Apply kinetic parameters to transitions
    2. Store selections in local database
    3. Increment usage_count for selected parameters
    4. Update last_used timestamp
  
  → 15 transitions enriched automatically! 🎉

Step 5: Handle Low-Confidence Cases
  User: Manually review 2 transitions with low data
  Options:
    • Use cross-species data (yeast)
    • Use generic/in vitro data
    • Use literature defaults
    • Leave empty (enrich later)

Step 6: Save & Reuse
  System: All parameters saved to local DB
  Next time: Same pathway analysis is instant (cached)
  Learning: User preferences influence future recommendations
```

---

## Implementation Roadmap

### Phase 1: Foundation (2-3 weeks)

**Deliverables**:
1. ✅ Cross-reference analysis document (this file)
2. Local SQLite database schema
3. Database migration scripts
4. Basic ORM/query layer (`heuristic_db.py`)

**Files**:
- `src/shypn/data/heuristic_db.py` - Database interface
- `src/shypn/data/heuristic_inference.py` - Inference engine
- `database/heuristic_parameters.db` - SQLite file

---

### Phase 2: Inference Engine (3-4 weeks)

**Deliverables**:
1. Implement 7 heuristic rules
2. Confidence scoring algorithm
3. Statistical aggregation (median, CV, outliers)
4. Organism compatibility matrix

**Files**:
- `src/shypn/heuristic/inference_engine.py`
- `src/shypn/heuristic/confidence_scorer.py`
- `src/shypn/heuristic/organism_compatibility.py`

---

### Phase 3: Data Ingestion (2-3 weeks)

**Deliverables**:
1. SABIO-RK batch importer
2. BioModels SBML parser integration
3. Manual entry interface
4. CSV/Excel import for literature data

**Files**:
- `src/shypn/data/importers/sabio_bulk_importer.py`
- `src/shypn/data/importers/biomodels_extractor.py`

---

### Phase 4: UI Implementation (3-4 weeks)

**Deliverables**:
1. "Heuristic Parameters" category in Pathway Panel
2. Configuration interface
3. Results preview widget
4. Alternative selection UI
5. Confidence visualization (stars, colors)

**Files**:
- `src/shypn/ui/panels/pathway_operations/heuristic_category.py`
- `ui/pathway_operations/heuristic_parameters.ui` (GTK)

---

### Phase 5: Learning & Optimization (2 weeks)

**Deliverables**:
1. Usage tracking (which parameters users prefer)
2. User rating system (1-5 stars)
3. Adaptive recommendations (learn from history)
4. Cache optimization

**Files**:
- `src/shypn/heuristic/learning_engine.py`

---

### Phase 6: Testing & Validation (2 weeks)

**Deliverables**:
1. Unit tests for inference engine
2. Integration tests with SABIO-RK/BioModels
3. Database migration tests
4. UI tests

**Files**:
- `tests/test_heuristic_inference.py`
- `tests/test_confidence_scoring.py`
- `tests/test_heuristic_ui.py`

---

## Scientific Validation

### Organism Compatibility Research

**Literature Review Needed**:
1. Enzyme conservation across species (glycolysis, TCA)
2. Kinetic parameter scaling factors (yeast→human)
3. Temperature/pH normalization methods
4. Reliability of generic/in vitro data

**Validation Approach**:
1. Compare predictions vs known human data
2. Test on well-studied pathways (glycolysis, TCA)
3. Expert review by biochemists
4. Confidence calibration (do 80% predictions actually work 80% of time?)

---

## Key Benefits

### For Users

✅ **Automation**: One-click enrichment instead of manual selection  
✅ **Transparency**: Confidence scores explain recommendations  
✅ **Flexibility**: Can override any recommendation  
✅ **Learning**: System gets smarter with use  
✅ **Speed**: Local cache makes repeated queries instant  
✅ **Quality**: Multi-source reconciliation improves accuracy  

### For Science

✅ **Traceability**: Every parameter has source + confidence  
✅ **Reproducibility**: Same query = same result  
✅ **Best Practices**: Encodes expert knowledge in heuristics  
✅ **Data Reuse**: Build community database over time  

---

## Risks & Mitigation

### Risk 1: Incorrect Cross-Species Extrapolation

**Mitigation**:
- Conservative organism compatibility scores
- Clear warnings for cross-species data
- Allow users to set organism restrictions
- Document which enzymes are conserved

### Risk 2: Overconfidence in Predictions

**Mitigation**:
- Confidence scores are conservative
- Always show alternatives
- Expert review mode (require manual approval)
- Validation against known benchmarks

### Risk 3: Database Maintenance Burden

**Mitigation**:
- Automated imports from SABIO-RK/BioModels
- Version control for database schema
- User contributions (optional)
- Periodic cleanup of unused entries

---

## Success Metrics

### Quantitative

- **Automation Rate**: % of transitions enriched without manual review
  - Target: 70% high confidence (auto-apply)
  - Threshold: 50% acceptable

- **Accuracy**: % of predictions validated correct
  - Target: 90% for high confidence (>80%)
  - Threshold: 75% acceptable

- **Speed**: Time to enrich 50-transition pathway
  - Target: <60 seconds (first time), <5 seconds (cached)

- **Coverage**: % of KEGG pathways with ≥50% data availability
  - Target: 80% of metabolic pathways

### Qualitative

- **User Satisfaction**: Survey feedback on usefulness
- **Adoption Rate**: % of users who use heuristic vs manual
- **Error Reports**: Frequency of incorrect recommendations

---

## Future Enhancements

### Version 2.0 (Future)

1. **Machine Learning**: Train ML model on user selections
2. **Pathway-Level Optimization**: Global parameter fitting for pathway flux
3. **Literature Mining**: Auto-extract parameters from papers (NLP)
4. **Cloud Database**: Community-shared parameter database
5. **Experimental Design**: Suggest missing measurements user should obtain

---

## Conclusion

The **Heuristic Parameters** system represents a major advancement in pathway enrichment:

1. **Intelligent**: Uses multiple data sources + scientific heuristics
2. **Transparent**: Confidence scores + source tracking
3. **Efficient**: Local caching + batch processing
4. **Extensible**: Easy to add new sources or heuristics
5. **User-Friendly**: One-click automation with manual override

**Next Step**: Implement Phase 1 (database schema + basic inference)

---

## Appendix: Example Heuristic Decision Tree

```
Query: EC 2.7.1.1 (hexokinase), Target: Homo sapiens, Pathway: hsa00010

Step 1: Check Local Cache
  → Cache miss (first query)

Step 2: Query SABIO-RK
  → Found 15 entries (3 human, 8 yeast, 4 rat)

Step 3: Apply Heuristic 1 (Exact Match)
  → 3 human entries found
  → Filter by temp (37°C): 2 entries remain
  → Filter by pH (7.4): 2 entries remain
  → Calculate median: Vmax=210.7, Km=0.09
  → Confidence: 95% ✅

Step 4: Identify Alternatives
  → Heuristic 2 (mammalian): Rat data (n=2, confidence=82%)
  → Heuristic 3 (yeast): Yeast data (n=8, confidence=77%)
  → Heuristic 5 (BioModels): BIOMD206 (confidence=81%)

Step 5: Rank & Present
  Recommendation: Human data (95%) ⭐⭐⭐⭐⭐
  Alternative 1:  Rat data (82%) ⭐⭐⭐⭐
  Alternative 2:  BioModels (81%) ⭐⭐⭐⭐
  Alternative 3:  Yeast data (77%) ⭐⭐⭐

Step 6: User Accepts
  → Apply Vmax=210.7, Km=0.09 to transition T5
  → Store in local DB (usage_count=1)
  → Cache result for future queries
```

---

**Document Status**: ✅ Ready for team review and Phase 1 implementation
