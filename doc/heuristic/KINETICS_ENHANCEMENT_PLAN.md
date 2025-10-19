# Kinetics Import Enhancement Plan

**Date**: October 19, 2025  
**Goal**: Complement missing kinetic data while respecting curated models  
**Approach**: Follow SBML's scientific method

---

## Core Principle

> **"Import as-is for curated models, enhance only when data is missing"**

Never override explicit kinetic data. Only fill gaps with scientifically-based heuristics.

---

## Current State Analysis

### SBML Import ✅ (Reference Implementation)

**File**: `src/shypn/data/pathway/pathway_converter.py`

**Strategy** (lines 230-400):
```python
def _setup_kinetics(self, transition, reaction):
    if not reaction.kinetic_law:
        # NO kinetic law → Use heuristics
        self._setup_heuristic_kinetics(transition, reaction)
        return
    
    kinetic = reaction.kinetic_law
    
    # HAS kinetic law → Use it as-is
    if kinetic.rate_type == "michaelis_menten":
        self._setup_michaelis_menten(transition, reaction, kinetic)  # Continuous
    elif kinetic.rate_type == "mass_action":
        self._setup_mass_action(transition, reaction, kinetic)        # Stochastic
    else:
        # Unknown type → Default to continuous
        transition.transition_type = "continuous"
```

**Key Insight**: SBML respects explicit data, only fills gaps with heuristics ✓

### KEGG Import ⚠️ (Needs Enhancement)

**File**: `src/shypn/importer/kegg/reaction_mapper.py`

**Current** (lines 70-85):
```python
def _create_single_transition(self, reaction, x, y, base_name):
    transition = Transition(x, y, transition_id, transition_name, label=name)
    # Does NOT set kinetics at all
    # Relies on Transition.__init__() defaults:
    #   - transition_type = 'continuous'
    #   - rate = 1.0
    return transition
```

**Issue**: No kinetic setup, all defaults

---

## Proposed Solution: Tiered Enhancement Strategy

### Tier 1: Explicit Data (Highest Priority)
**Source**: SBML kinetic laws, curated databases  
**Action**: **Import as-is, never override**  
**Example**: BioModels SBML with `<kineticLaw>` elements

```python
if has_explicit_kinetics(reaction):
    # Use exactly as provided
    apply_explicit_kinetics(transition, reaction)
    return  # Done, don't enhance
```

### Tier 2: Database Lookup (High Priority)
**Source**: KEGG ENZYME database, BRENDA, SABIO-RK  
**Action**: Lookup by EC number, use literature values  
**Example**: EC 2.7.1.1 (Hexokinase) → Known Vmax, Km values

```python
if reaction.has_ec_number():
    # Lookup in kinetics database
    params = lookup_ec_kinetics(reaction.ec_number)
    if params:
        apply_database_kinetics(transition, params)
        return  # Done
```

### Tier 3: Heuristic Analysis (Medium Priority)
**Source**: Reaction structure, stoichiometry  
**Action**: Scientifically-based heuristics (like SBML does)  
**Example**: Simple 1:1 reaction → Likely mass action

```python
# Analyze reaction structure
if is_simple_conversion(reaction):
    # A → B (no enzyme)
    transition.transition_type = "stochastic"  # Mass action
    transition.rate = 1.0  # Default lambda
elif has_enzyme_annotation(reaction):
    # Enzymatic reaction
    transition.transition_type = "continuous"  # Michaelis-Menten
    transition.properties['rate_function'] = f"michaelis_menten({substrate}, 10.0, 0.5)"
else:
    # Unknown → Safe default
    transition.transition_type = "continuous"
    transition.rate = 1.0
```

### Tier 4: User Override (Lowest Priority)
**Source**: User configuration in properties dialog  
**Action**: Always respect user's explicit choices  
**Example**: User manually sets transition to stochastic

```python
# Never auto-enhance if user has configured
if transition.has_user_configuration():
    return  # Don't touch it
```

---

## Implementation Plan

### Phase 1: Foundation (This Session/Next)

#### 1.1 Add Kinetics Metadata Tracking
```python
# In Transition class
class Transition:
    def __init__(self, ...):
        # ...existing code...
        
        # Kinetics metadata (NEW)
        if not hasattr(self, 'metadata'):
            self.metadata = {}
        
        self.metadata['kinetics_source'] = None  # None, 'explicit', 'database', 'heuristic', 'user'
        self.metadata['kinetics_confidence'] = None  # None, 'high', 'medium', 'low'
```

**Purpose**: Track where kinetic data came from, enable smart override decisions

#### 1.2 Create Kinetics Assignment Module
```python
# New file: src/shypn/importer/kinetics_assigner.py

class KineticsAssigner:
    """Assigns kinetic properties to transitions based on available data."""
    
    def assign(self, transition, reaction, source='kegg'):
        """
        Assign kinetics using tiered strategy.
        
        Args:
            transition: Transition object to configure
            reaction: Reaction data (KEGG or SBML)
            source: Data source ('kegg', 'sbml', 'biomodels')
        
        Returns:
            Assignment result with confidence level
        """
        # Tier 1: Explicit kinetics (SBML only)
        if hasattr(reaction, 'kinetic_law') and reaction.kinetic_law:
            return self._assign_explicit(transition, reaction)
        
        # Tier 2: Database lookup (if EC number available)
        if hasattr(reaction, 'ec_numbers') and reaction.ec_numbers:
            result = self._assign_from_database(transition, reaction)
            if result.success:
                return result
        
        # Tier 3: Heuristics
        return self._assign_heuristic(transition, reaction, source)
```

#### 1.3 Implement Heuristic Rules (SBML Style)

Based on SBML's `_setup_heuristic_kinetics()`:

```python
def _assign_heuristic(self, transition, reaction, source):
    """Assign using scientific heuristics."""
    
    # Rule 1: Simple stoichiometry → Mass action
    if self._is_simple_mass_action(reaction):
        transition.transition_type = "stochastic"
        transition.rate = 1.0  # Default lambda
        transition.metadata['kinetics_source'] = 'heuristic'
        transition.metadata['kinetics_confidence'] = 'low'
        transition.metadata['kinetics_rule'] = 'simple_mass_action'
        return AssignmentResult(success=True, confidence='low')
    
    # Rule 2: Has enzyme/EC → Michaelis-Menten
    if self._has_enzyme(reaction):
        transition.transition_type = "continuous"
        substrate_place = self._get_primary_substrate(reaction)
        transition.properties['rate_function'] = \
            f"michaelis_menten({substrate_place}, 10.0, 0.5)"  # Heuristic params
        transition.metadata['kinetics_source'] = 'heuristic'
        transition.metadata['kinetics_confidence'] = 'medium'
        transition.metadata['kinetics_rule'] = 'enzymatic_mm'
        return AssignmentResult(success=True, confidence='medium')
    
    # Rule 3: Default → Continuous (safe)
    transition.transition_type = "continuous"
    transition.rate = 1.0
    transition.metadata['kinetics_source'] = 'heuristic'
    transition.metadata['kinetics_confidence'] = 'low'
    transition.metadata['kinetics_rule'] = 'default_continuous'
    return AssignmentResult(success=True, confidence='low')
```

**Heuristic Rules**:

| Condition | Assignment | Confidence | Rationale |
|-----------|------------|------------|-----------|
| Simple 1:1, no enzyme | Stochastic (λ=1.0) | Low | Likely mass action |
| Has EC number | Continuous (MM) | Medium | Enzymatic reaction |
| Multiple substrates | Continuous (sequential MM) | Medium | Complex kinetics |
| Unknown | Continuous (rate=1.0) | Low | Safe default |

### Phase 2: Database Integration (Future)

#### 2.1 EC Number → Kinetics Database

**Source**: BRENDA, SABIO-RK, or local curated database

```python
# src/shypn/data/kinetics_database.py

ENZYME_KINETICS = {
    # EC 2.7.1.1 - Hexokinase
    "2.7.1.1": {
        "type": "continuous",
        "law": "michaelis_menten",
        "vmax": 10.0,  # μM/s (typical)
        "km": 0.1,     # mM (glucose)
        "source": "BRENDA",
        "confidence": "high"
    },
    # EC 2.7.1.11 - Phosphofructokinase
    "2.7.1.11": {
        "type": "continuous",
        "law": "michaelis_menten",
        "vmax": 15.0,
        "km": 0.2,
        "source": "BRENDA",
        "confidence": "high"
    },
    # Add more enzymes...
}

def lookup_ec_kinetics(ec_number):
    """Lookup kinetics by EC number."""
    return ENZYME_KINETICS.get(ec_number)
```

#### 2.2 Integration with KEGG Import

```python
# In kegg/reaction_mapper.py

def _create_single_transition(self, reaction, x, y, base_name):
    transition = Transition(x, y, transition_id, transition_name, label=name)
    
    # NEW: Assign kinetics
    from shypn.importer.kinetics_assigner import KineticsAssigner
    assigner = KineticsAssigner()
    assigner.assign(transition, reaction, source='kegg')
    
    return transition
```

### Phase 3: User Interface (Future)

#### 3.1 Confidence Indicator in Properties Dialog

```
┌─────────────────────────────────────────┐
│ Transition Properties: T1 (R00710)     │
├─────────────────────────────────────────┤
│ Type: [Continuous ▼]                    │
│                                          │
│ Rate Function:                           │
│ ┌────────────────────────────────────┐  │
│ │ michaelis_menten(P105, 10.0, 0.5) │  │
│ └────────────────────────────────────┘  │
│                                          │
│ ⓘ Kinetics: Heuristic (Medium confidence)│
│   EC 2.7.1.1 - Hexokinase               │
│   [View Details] [Override]             │
└─────────────────────────────────────────┘
```

#### 3.2 Bulk Enhancement Tool

```
Tools → Enhance Kinetics...

┌─────────────────────────────────────────┐
│ Enhance Pathway Kinetics                │
├─────────────────────────────────────────┤
│ Transitions to enhance: 34              │
│                                          │
│ [ ] Use database (EC numbers)           │
│     Found: 12 transitions with EC       │
│                                          │
│ [x] Use heuristics for remaining        │
│     Simple reactions → Stochastic       │
│     Enzymatic → Michaelis-Menten        │
│                                          │
│ [ ] Override existing assignments       │
│                                          │
│ [Cancel] [Preview] [Apply]              │
└─────────────────────────────────────────┘
```

---

## Safety Guarantees

### 1. Never Override Explicit Data
```python
def should_enhance(transition):
    """Check if enhancement is safe."""
    
    # Don't enhance if user configured
    if transition.metadata.get('kinetics_source') == 'user':
        return False
    
    # Don't enhance if from explicit kinetics
    if transition.metadata.get('kinetics_source') == 'explicit':
        return False
    
    # Don't enhance if from curated database (high confidence)
    if transition.metadata.get('kinetics_confidence') == 'high':
        return False
    
    # Safe to enhance
    return True
```

### 2. Track Changes for Undo
```python
# Before enhancing, save original state
transition.metadata['original_kinetics'] = {
    'transition_type': transition.transition_type,
    'rate': transition.rate,
    'rate_function': transition.properties.get('rate_function')
}

# Allow rollback
def rollback_kinetics(transition):
    """Restore original kinetics."""
    orig = transition.metadata.get('original_kinetics')
    if orig:
        transition.transition_type = orig['transition_type']
        transition.rate = orig['rate']
        if 'rate_function' in orig:
            transition.properties['rate_function'] = orig['rate_function']
```

### 3. Validation Before Simulation
```python
def validate_kinetics(transitions):
    """Warn about low-confidence kinetics."""
    
    low_conf = [t for t in transitions 
                if t.metadata.get('kinetics_confidence') == 'low']
    
    if low_conf:
        show_warning(
            f"{len(low_conf)} transitions have low-confidence kinetics.\n"
            "Consider reviewing in Properties dialog before simulation."
        )
```

---

## Migration Strategy

### For Existing Models

**Problem**: Existing KEGG-imported models have no kinetics metadata

**Solution**: Detect and offer enhancement

```python
def detect_needs_enhancement(model):
    """Check if model needs kinetic enhancement."""
    
    needs_enhancement = []
    for t in model.transitions:
        # Skip source/sink
        if t.is_source or t.is_sink:
            continue
        
        # Check if has default values
        if t.transition_type == 'continuous' and t.rate == 1.0:
            if not t.properties.get('rate_function'):
                needs_enhancement.append(t)
    
    return needs_enhancement

# On model load
needs_enh = detect_needs_enhancement(model)
if needs_enh:
    show_dialog(
        f"Found {len(needs_enh)} transitions with default kinetics.\n"
        "Would you like to enhance them using heuristics?",
        buttons=["Enhance", "Review Manually", "Keep As-Is"]
    )
```

---

## Testing Plan

### Test 1: Respect Explicit Data (SBML)
```python
def test_sbml_explicit_kinetics():
    """Verify SBML kinetics are not overridden."""
    
    # Import SBML with mass action kinetic law
    model = import_sbml("model_with_mass_action.sbml")
    
    # Check transition is stochastic (from explicit kinetic law)
    assert model.transitions[0].transition_type == "stochastic"
    assert model.transitions[0].metadata['kinetics_source'] == 'explicit'
    
    # Try to enhance (should skip)
    enhance_kinetics(model)
    
    # Verify still stochastic (not changed)
    assert model.transitions[0].transition_type == "stochastic"
```

### Test 2: Enhance Missing Data (KEGG)
```python
def test_kegg_heuristic_enhancement():
    """Verify KEGG gets heuristic enhancement."""
    
    # Import KEGG pathway (no explicit kinetics)
    model = import_kegg("hsa00010")
    
    # Initially all continuous with rate=1.0
    assert all(t.transition_type == 'continuous' for t in model.transitions)
    
    # Enhance with heuristics
    enhance_kinetics(model)
    
    # Check some are now stochastic (simple mass action)
    stochastic = [t for t in model.transitions if t.transition_type == 'stochastic']
    assert len(stochastic) > 0
    
    # Check metadata
    assert model.transitions[0].metadata['kinetics_source'] == 'heuristic'
    assert model.transitions[0].metadata['kinetics_confidence'] in ['low', 'medium']
```

### Test 3: Database Lookup
```python
def test_ec_database_lookup():
    """Verify EC number lookup works."""
    
    # Create reaction with EC 2.7.1.1 (hexokinase)
    reaction = KEGGReaction(ec_numbers=["2.7.1.1"])
    transition = Transition(0, 0, "T1", "T1")
    
    # Assign kinetics
    assigner = KineticsAssigner()
    result = assigner.assign(transition, reaction)
    
    # Check used database values
    assert result.confidence == 'high'
    assert transition.transition_type == 'continuous'
    assert 'michaelis_menten' in transition.properties['rate_function']
    assert transition.metadata['kinetics_source'] == 'database'
```

---

## Documentation Requirements

### 1. User Guide Section
```markdown
# Kinetic Properties

## Automatic Assignment

SHYPN automatically assigns kinetic properties based on available data:

1. **Explicit kinetics** (SBML models): Used as-is ✓
2. **Database lookup** (EC numbers): High confidence values
3. **Heuristics** (missing data): Medium/low confidence estimates

## Confidence Levels

- **High**: From curated databases or explicit SBML
- **Medium**: From structural analysis (has enzyme)
- **Low**: Default fallback values

## Manual Override

You can always override in Properties dialog:
1. Right-click transition → Properties
2. Change Type and Rate
3. System marks as 'user' confidence (won't auto-enhance)
```

### 2. Developer Documentation
```markdown
# Kinetics Assignment Architecture

## Never Override Principle

```python
if kinetics_source in ['explicit', 'user']:
    return  # Don't touch!
```

## Enhancement Flow

1. Check explicit data → Use it
2. Try database lookup → Use if found
3. Apply heuristics → Fill gaps
4. Track source & confidence → For transparency
```

---

## Summary

### ✅ Recommended Approach

1. **Phase 1** (Immediate): Implement heuristic enhancement for KEGG
   - Simple reactions → Stochastic (mass action)
   - Enzymatic → Continuous (Michaelis-Menten with heuristic params)
   - Track source and confidence in metadata

2. **Phase 2** (Soon): Add EC number database lookup
   - Build curated database of common enzymes
   - High confidence assignments from literature

3. **Phase 3** (Future): User interface improvements
   - Show confidence in properties dialog
   - Bulk enhancement tool
   - Validation warnings

### 🔒 Safety Guarantees

- ✅ Never override explicit SBML kinetics
- ✅ Never override user configurations
- ✅ Never override high-confidence database values
- ✅ Track all enhancements with metadata
- ✅ Allow rollback to original state

### 📊 Expected Impact

**Before Enhancement**:
- KEGG: All continuous, rate=1.0 (unrealistic)
- SBML: Correct (already has explicit kinetics)

**After Enhancement**:
- KEGG: Mixed stochastic/continuous with reasonable defaults
- SBML: Unchanged (respects explicit data) ✓
- Better simulation accuracy
- Clear confidence indicators

### 🎯 Next Steps

1. ✅ Document strategy (this file)
2. ⏭️ Implement Phase 1 (heuristic rules)
3. ⏭️ Add metadata tracking
4. ⏭️ Test with fresh KEGG import
5. ⏭️ Update KEGG importer to use assigner

---

**Status**: 📋 **PLANNED**  
**Priority**: High (improves simulation accuracy)  
**Risk**: Low (only enhances missing data, never overrides)
