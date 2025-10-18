# Michaelis-Menten Auto-Parameterization - Quick Reference

**Status**: 📋 PLANNING  
**Priority**: HIGH  
**Complexity**: 🔴 CHALLENGING

---

## Problem Statement

**Current**: SBML files without kinetic parameters → Generic `rate = 1.0`  
**Desired**: SBML files without kinetic parameters → Intelligent Michaelis-Menten with estimated Vmax/Km

---

## Requirements (User Request)

1. ✅ **Almost all biochemical reactions are Michaelis-Menten**
2. 🆕 **Auto-set MM on import** for continuous transitions
3. 🆕 **Pre-fill rate function** in transition dialog
4. 🆕 **Context-aware**: Consider input/output places
5. 🆕 **Infer Vmax, Km** from stoichiometry

---

## Solution Architecture

### Component 1: Parameter Estimator

**File**: `src/shypn/data/pathway/kinetic_parameter_estimator.py` (NEW)

```python
class KineticParameterEstimator:
    """Estimates Vmax/Km from stoichiometry when SBML lacks kinetics."""
    
    def estimate_michaelis_menten(reaction, substrate_places, product_places):
        """
        Heuristic Rules:
        - Vmax = 10.0 * max(product_stoichiometry)
        - Km = mean(substrate_concentrations) / 2
        """
        vmax = 10.0 * max(stoich for _, stoich in reaction.products)
        km = mean([p.tokens for p in substrate_places]) / 2.0
        return vmax, km
```

### Component 2: Integration with Converter

**File**: `src/shypn/data/pathway/pathway_converter.py` (MODIFY)

```python
class ReactionConverter:
    def _configure_transition_kinetics(transition, reaction):
        if not reaction.kinetic_law:
            # NEW: Estimate parameters and setup MM
            self._setup_michaelis_menten_estimated(transition, reaction)
```

### Component 3: Dialog Pre-filling

**File**: `src/shypn/helpers/transition_prop_dialog_loader.py` (MODIFY)

```python
def _populate_fields(self):
    rate_textview = self.builder.get_object('rate_textview')
    buffer = rate_textview.get_buffer()
    
    # PRIORITY 1: Load from properties['rate_function']
    if 'rate_function' in self.transition_obj.properties:
        buffer.set_text(self.transition_obj.properties['rate_function'])
    
    # PRIORITY 2: Fall back to rate attribute
    elif self.transition_obj.rate:
        buffer.set_text(str(self.transition_obj.rate))
```

---

## Implementation Phases

### Phase 1: Parameter Estimation (Week 1)

**Tasks**:
1. Create `KineticParameterEstimator` class
2. Integrate with `PathwayConverter`
3. Add unit tests

**Files**:
- `src/shypn/data/pathway/kinetic_parameter_estimator.py` (NEW, ~200 lines)
- `src/shypn/data/pathway/pathway_converter.py` (MODIFY, +50 lines)
- `tests/test_kinetic_parameter_estimator.py` (NEW, ~100 lines)

**Result**: SBML import automatically estimates Vmax/Km

### Phase 2: Dialog Pre-filling (Week 2)

**Tasks**:
1. Enhance dialog loader to prioritize `rate_function`
2. Add template generation for new transitions
3. Test dialog behavior

**Files**:
- `src/shypn/helpers/transition_prop_dialog_loader.py` (MODIFY, +80 lines)
- `tests/validation/ui/test_rate_function_prefill.py` (NEW, ~80 lines)

**Result**: Transition dialog shows Michaelis-Menten formula

### Phase 3: Product Inhibition (Week 3 - Optional)

**Tasks**:
1. Detect reversible reactions
2. Add product inhibition terms

**Files**:
- `src/shypn/data/pathway/pathway_converter.py` (MODIFY, +60 lines)

**Result**: Reversible reactions include product inhibition

---

## Before vs After

### Before Enhancement

**SBML Import** (no kinetics):
```python
transition.transition_type = "continuous"
transition.rate = 1.0
# No rate_function
```

**Dialog**: Empty rate function field

---

### After Enhancement ✨

**SBML Import** (no kinetics):
```python
transition.transition_type = "continuous"
transition.rate = 10.0  # Estimated
transition.properties['rate_function'] = "michaelis_menten(P_Glucose, 10.0, 5.0)"
```

**Dialog**: Shows formula immediately:
```
michaelis_menten(P_Glucose, 10.0, 5.0)
```

User can:
- ✅ See the formula
- ✅ Edit parameters
- ✅ Understand kinetics
- ✅ Simulate immediately

---

## Estimation Heuristics

### Vmax Estimation

```python
# Rule 1: Scale with product stoichiometry
max_stoich = max(stoich for _, stoich in reaction.products)
vmax = 10.0 * max_stoich

# Rule 2: Adjust for reversibility
if reaction.reversible:
    vmax *= 0.8  # Slightly slower
```

**Examples**:
- 1:1 reaction → Vmax = 10.0
- 1:2 reaction → Vmax = 20.0
- 2:3 reaction → Vmax = 30.0

### Km Estimation

```python
# Rule: Km ≈ half of mean substrate concentration
concentrations = [p.tokens for p in substrate_places]
km = mean(concentrations) / 2.0
km = max(0.5, km)  # Minimum 0.5
```

**Examples**:
- Substrate at 10 tokens → Km = 5.0
- Two substrates (10, 20) → Km = 7.5
- No concentration data → Km = 5.0 (default)

---

## Testing Strategy

### Unit Tests

```python
# Parameter estimation
test_estimate_vmax_from_stoichiometry()
test_estimate_km_from_concentrations()
test_defaults_when_no_data()

# Dialog pre-filling
test_load_rate_function_from_properties()
test_fallback_to_rate_attribute()
test_template_for_new_transitions()

# Integration
test_sbml_without_kinetics_gets_mm()
test_dialog_shows_estimated_formula()
```

### Manual Testing

1. Import SBML without kinetics
2. Check transition has `rate_function`
3. Open dialog → Verify formula shown
4. Edit Vmax/Km → Verify updates
5. Save/reload → Verify persistence

---

## Key Design Decisions

### Decision 1: Heuristics vs Database Lookup

**Choice**: Start with heuristics

**Rationale**:
- ✅ Fast, always works
- ✅ No external dependencies
- ✅ Good enough for most cases
- Future: Add BRENDA/SABIO-RK lookup later

### Decision 2: Single Km for All Substrates

**Choice**: Use same Km for all substrates in sequential MM

**Rationale**:
- ✅ Simpler formula
- ✅ Common assumption in multi-substrate kinetics
- Future: Support individual Km values (Km1, Km2, ...)

### Decision 3: Product Inhibition Optional

**Choice**: Phase 3 (optional)

**Rationale**:
- Not all reactions have product inhibition
- More complex formula
- Can be added by users manually

---

## Risks & Mitigation

| Risk | Mitigation |
|------|------------|
| Estimated parameters unrealistic | Document as estimates, allow editing |
| Heuristics don't match biology | Provide literature references for assumptions |
| Dialog doesn't update | Comprehensive UI tests |
| Performance on large pathways | Cache parameters, lazy evaluation |

---

## Success Criteria

✅ **Phase 1 Complete** when:
- SBML without kinetics → MM formula generated
- Parameters estimated from stoichiometry
- Tests pass

✅ **Phase 2 Complete** when:
- Dialog shows `rate_function` from properties
- Formula pre-filled for imported transitions
- Template suggested for new transitions

✅ **Phase 3 Complete** when:
- Reversible reactions include product inhibition
- Formula considers both substrates and products

---

## Next Steps

1. **Review plan** with team
2. **Implement Phase 1** (parameter estimation)
3. **Test** with real SBML files
4. **Iterate** based on results
5. **Implement Phase 2** (dialog pre-filling)
6. **Document** for users

---

**Full Details**: See `MICHAELIS_MENTEN_AUTO_PARAMETERIZATION.md`  
**Estimated Effort**: 2-3 weeks  
**Status**: 📋 Ready for Implementation
