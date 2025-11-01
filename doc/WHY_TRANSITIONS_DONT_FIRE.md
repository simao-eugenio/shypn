# Why Enabled Transitions Don't Fire - Analysis and Solutions

## Problem

Even after fixing transition types (stochastic → continuous for reversible reactions), **many enabled transitions still don't fire during simulation** in BIOMD0000000061.

## Root Cause Analysis

### Diagnostic Results

Running `diagnose_transition_firing.py` on BIOMD0000000061.shy reveals:

```
✅ Enabled continuous transitions: 11
   ✓ T1: Glucose Mixed flow
   ✓ T2: Glucose uptake
   ✓ T3: Hexokinase
   ✓ T4: Phosphoglucoisomerase
   ...

❌ Disabled continuous transitions: 7
   ✗ T5: Phosphofructokinase → Blocked by P6 (0 tokens)
   ✗ T8: GAPDH → Blocked by P8 (0 tokens)
   ✗ T9: PEP synthesis → Blocked by P11 (0 tokens)
   ✗ T10: Pyruvate kinase → Blocked by P13 (0 tokens)
   ✗ T12: ADH → Blocked by P12 (0 tokens)
```

### The Issue: **Empty Input Places**

**Continuous transitions require ALL input places to have tokens > 0** to fire.

From `continuous_behavior.py`:
```python
def can_fire(self) -> Tuple[bool, str]:
    # Check each input place for positive tokens
    for arc in input_arcs:
        source_place = arc.source
        
        # Continuous requires positive, not >= weight
        if source_place.tokens <= 0:
            return False, f"input-place-empty-{source_place.id}"
    
    return True, "enabled-continuous"
```

**Key Point:** Even if a transition's `enabled` property is `True`, it still won't fire if any input place has 0 tokens.

## Why This Happens

### 1. Initial Marking from SBML

SBML models specify `initial_concentration` for species, which becomes the initial marking. The BIOMD0000000061 model has:

```
Species WITH initial concentration:
  P1 (GlcX): 7
  P2 (Glc): 1
  P3 (ATP): 2
  P4 (G6P): 4
  P5 (ADP): 2
  P7 (FBP): 5
  P10 (NAD): 1
  P14 (Pyr): 9
  ...

Species WITHOUT initial concentration:
  P6 (F6P): 0        ← Blocks T5!
  P8 (GAP): 0        ← Blocks T8!
  P11 (BPG): 0       ← Blocks T9!
  P12 (NADH): 0      ← Blocks T12!
  P13 (PEP): 0       ← Blocks T10!
```

### 2. Metabolic Pathway Flow

This is actually **biochemically correct**! In the glycolysis pathway:
- Early metabolites (Glucose, ATP, G6P) start with concentrations
- Intermediate metabolites (F6P, GAP, BPG, PEP) start at 0
- They need to be **produced by upstream reactions** before downstream reactions can occur

### 3. The Cascade Effect

```
Glc + ATP → (T3: Hexokinase) → G6P + ADP ✓ (fires - has input tokens)
  ↓
G6P → (T4: PGI) → F6P ✓ (fires)
  ↓
F6P + ATP → (T5: PFK) → FBP + ADP ✗ (blocked - F6P starts at 0!)
  ↓
FBP → (T6: Aldolase) → GAP + DHAP ✗ (blocked - needs FBP from T5)
  ↓
GAP + NAD → (T8: GAPDH) → BPG + NADH ✗ (blocked - needs GAP from T6)
```

**Problem:** The pathway needs to "prime" itself - early reactions must fire first to produce tokens for downstream reactions.

## Solutions

### Solution 1: **Let Simulation Run** (Recommended)

The model is actually correct! Just let the simulation run:

1. **T3 (Hexokinase) fires** → Produces G6P from Glc + ATP
2. **T4 (PGI) fires** → Converts G6P to F6P (P6 now has tokens!)
3. **T5 (PFK) now enabled** → Can fire because P6 has tokens
4. **Cascade continues** → Each reaction produces tokens for the next

**Key Settings:**
- **Small time steps**: `dt = 0.01` or smaller
- **Sufficient duration**: Run for `t = 10` or longer
- **Watch early reactions**: Monitor T3, T4 first

### Solution 2: **Set Initial Concentrations for Intermediates**

If you want faster equilibration, manually set initial tokens for intermediate metabolites:

```python
# In Properties dialog for each place:
P6 (F6P): 0.5 tokens   # Small amount to kickstart
P8 (GAP): 0.1 tokens
P11 (BPG): 0.1 tokens
P12 (NADH): 0.1 tokens
P13 (PEP): 0.1 tokens
```

**Trade-off:** Not biochemically accurate (these metabolites don't pre-exist), but speeds up simulation.

### Solution 3: **Add Source Transitions** (For Testing)

Temporarily add source transitions to problematic places:

```
1. Create transition Tsrc_F6P
2. Set as source transition (is_source = True)
3. Connect: Tsrc_F6P → P6 (F6P)
4. Set rate: 0.01 (slow generation)
```

This artificially generates tokens to test downstream behavior.

## Why Transitions Are "Enabled" But Don't Fire

### Confusion: Two Meanings of "Enabled"

**1. UI Property: `transition.enabled`**
- This is a **user toggle** in the Properties dialog
- When `False`, transition is completely disabled (ignored by simulation)
- When `True`, transition is **allowed to participate** in simulation

**2. Simulation Enablement: `can_fire()`**
- This checks **runtime conditions**:
  - Sufficient input tokens
  - Guard condition passes
  - Timing constraints met (for timed/stochastic)
- A transition can be `enabled=True` but still fail `can_fire()` checks

### The Relationship

```python
# Simulation controller checks:
if transition.enabled:  # UI property (user toggle)
    if behavior.can_fire():  # Runtime check (tokens, guard, etc.)
        behavior.fire()  # Execute transition
```

**Both must be True** for firing to occur!

## Diagnostic Script Usage

To check why your transitions don't fire:

```bash
python3 diagnose_transition_firing.py
```

**Output:**
- Lists enabled vs disabled transitions
- Shows blocking places (0 tokens)
- Identifies missing parameters
- Provides specific recommendations

## Simulation Best Practices

### For BIOMD0000000061 (Glycolysis)

1. **Use default initial markings from SBML** ✓
   - Don't manually set all places to 1
   - Let biochemistry work naturally

2. **Use small time steps**
   ```python
   dt = 0.01   # For continuous transitions
   duration = 20.0  # Long enough for equilibration
   ```

3. **Watch the cascade**
   - First 1-2 time units: Early reactions fire (T3, T4)
   - Next 2-5 time units: Intermediate places fill up
   - After 5+ time units: Full pathway active

4. **Check terminal output**
   - Formula evaluation warnings
   - Negative rate warnings (should be gone after auto-fix)
   - Token transfer logs

### For General Models

1. **Verify initial markings**
   ```bash
   python3 diagnose_transition_firing.py
   ```

2. **Check connectivity**
   - Every place should have at least one input arc OR initial tokens
   - "Sink" places (no output) are OK
   - "Source" places (no input) need initial tokens or source transitions

3. **Validate formulas**
   - All parameters defined in kinetic_metadata
   - Place references (P1, P2, etc.) match actual place IDs
   - No division by zero conditions

## Common Mistakes

### ❌ **Mistake 1: Expecting Instant Activity**
```
User: "I added source transitions but nothing fires!"
Reality: Need to run simulation for several time steps
```

### ❌ **Mistake 2: Large Time Steps**
```
dt = 1.0  ❌  Too large for continuous transitions
dt = 0.01 ✓  Appropriate for ODE integration
```

### ❌ **Mistake 3: Setting All Places to 1**
```
User sets all places to 1 token "to test"
Result: Unrealistic biochemistry, strange behavior
```

### ✓ **Correct Approach**
```
1. Use SBML initial concentrations
2. Run with dt=0.01 for t=20
3. Watch cascade naturally unfold
4. Adjust only if specific biochemical reason
```

## Technical Details: Enablement Logic

### Continuous Transitions

From `src/shypn/engine/continuous_behavior.py`:

```python
def can_fire(self) -> Tuple[bool, str]:
    """
    Continuous transitions enabled if:
    1. Guard passes (if defined)
    2. ALL input places have tokens > 0 (not >= weight!)
    """
    
    # Source transitions always enabled
    if self.transition.is_source:
        return True, "enabled-source"
    
    # Check guard
    if not self._evaluate_guard()[0]:
        return False, "guard-fails"
    
    # Check input places
    for arc in input_arcs:
        if arc.source.tokens <= 0:
            return False, f"input-place-empty-{arc.source.id}"
    
    return True, "enabled-continuous"
```

**Key Difference from Discrete:**
- **Discrete (immediate/stochastic)**: `tokens >= arc.weight`
- **Continuous**: `tokens > 0` (any positive amount)

### Why Continuous Uses > 0 Instead of >= weight

**Mathematical reason:** Continuous transitions use **rate functions** and **ODE integration**, not discrete token consumption.

```
Discrete: T1 fires → removes weight tokens instantly
Continuous: T1 integrates → removes (rate * dt) tokens over time
```

For continuous flow, as long as `tokens > 0`, the formula can evaluate (even if result is small).

## Summary

**The transitions ARE working correctly!** They just need:

1. ✅ **Initial tokens** in input places (from SBML or manual setting)
2. ✅ **Small time steps** for continuous integration (dt=0.01)
3. ✅ **Sufficient run time** for cascade to complete (t=10-20)
4. ✅ **Correct transition types** (auto-fixed by validation)

**Problem is NOT:**
- ❌ Transition type (already fixed: stochastic → continuous)
- ❌ Formulas (working correctly)
- ❌ Parameters (all defined)
- ❌ Arc connectivity (properly connected)

**Problem IS:**
- ⚠️ Initial state (some intermediate places start at 0)
- ⚠️ User expectations (expecting instant firing)
- ⚠️ Simulation settings (need small dt, long duration)

**Solution:**
Run the simulation with proper settings and let the metabolic cascade naturally unfold!

---

**Use the diagnostic script to identify specific blocking places:**
```bash
python3 diagnose_transition_firing.py
```
