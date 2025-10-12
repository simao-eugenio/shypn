# Source and Sink Transitions: Formal Definitions Research

**Date**: October 11, 2025  
**Purpose**: Establish correct formal definitions for source/sink transitions in Petri nets

---

## 1. Classical Petri Net Theory

### Standard Definitions

In classical Petri net theory:

**Place Definitions:**
- **Source Place**: A place with no input arcs (•p = ∅)
  - Cannot receive tokens from any transition
  - Initial marking only
  - Used to model initial resources

- **Sink Place**: A place with no output arcs (p• = ∅)
  - Cannot provide tokens to any transition
  - Accumulates tokens permanently
  - Used to model final states or completed work

**Transition Definitions:**
- **Standard transitions**: Have both input and output places
- **No "source transition" or "sink transition" in classical theory**

### Notation
- •x = preset of x (incoming neighbors)
- x• = postset of x (outgoing neighbors)
- For a transition t:
  - •t = {p | (p,t) ∈ F} (input places)
  - t• = {p | (t,p) ∈ F} (output places)

---

## 2. Extended Petri Net Models

### Open Petri Nets (Interface Transitions)

Some extensions introduce **interface transitions** for open systems:

**Input Transition (Source-like)**:
- Models external input to the system
- Structure: NO input places, only output places
- Formal: •t = ∅, t• ≠ ∅
- Semantics: Always enabled (structurally)
- Purpose: Interface with environment, external arrivals

**Output Transition (Sink-like)**:
- Models external output from the system  
- Structure: Only input places, NO output places
- Formal: •t ≠ ∅, t• = ∅
- Semantics: Enabled by normal rules (needs tokens)
- Purpose: Interface with environment, external departures

### Workflow Nets

In Workflow Nets (van der Aalst):
- **Source place** i: •i = ∅ (no incoming arcs)
- **Sink place** o: o• = ∅ (no outgoing arcs)
- Used to mark start and end of process
- Transitions are NOT categorized as source/sink

---

## 3. Stochastic and Timed Petri Nets

### Queueing Petri Nets (QPNs)

QPNs explicitly model arrivals and departures:

**Arrival Transition**:
- Represents external arrival process
- Structure: NO input places
- Firing: Creates tokens (models arrival)
- Rate: Often exponentially distributed
- Example: Customer arrivals in queue

**Departure Transition**:
- Represents external departure/completion
- Structure: NO output places
- Firing: Removes tokens (models departure)
- Rate: Service rate
- Example: Customer leaving system

**Key Insight**: These match the "no input/no output" structure!

### Continuous Petri Nets

In Continuous PNs (fluid models):

**Source Transition**:
- Continuously generates flow
- No input places needed
- Models: Constant input rate, external supply
- Semantics: Always enabled, produces at constant rate

**Sink Transition**:
- Continuously consumes flow
- No output places needed
- Models: Demand, external consumption
- Semantics: Consumes at constant rate (if enabled)

---

## 4. Colored Petri Nets (CPNs)

CPNs (Jensen) don't define source/sink transitions explicitly, but:

**Environment Interface**:
- Input transitions: Receive tokens from outside (colored values)
- Output transitions: Send tokens to outside
- Structure: May or may not have local places
- Focus: Data flow and token colors, not structure

---

## 5. Manufacturing and Process Modeling

### IDEF3 and Process Petri Nets

In manufacturing models:

**Source Node**:
- Represents start of material flow
- No predecessors (no input)
- Generates parts/materials
- Analogous to: Raw material arrival

**Sink Node**:
- Represents end of material flow
- No successors (no output)
- Consumes finished products
- Analogous to: Shipping/delivery

---

## 6. Formal Semantics Analysis

### Structural Definition (Recommended)

Based on open nets and queueing theory:

```
Source Transition (Input Interface):
  • Preset: •t = ∅ (NO input places)
  • Postset: t• ≠ ∅ (has output places)
  • Enablement: Always enabled (no prerequisites)
  • Firing: Creates tokens in output places
  • Models: External arrivals, token generation

Sink Transition (Output Interface):
  • Preset: •t ≠ ∅ (has input places)
  • Postset: t• = ∅ (NO output places)
  • Enablement: Requires sufficient input tokens
  • Firing: Removes tokens from input places
  • Models: External departures, token consumption
```

### Behavioral Definition (Current Implementation)

Alternative approach (used in our current code):

```
Source Transition:
  • Structure: May have input places (•t can be non-empty)
  • Enablement: Ignores input tokens, always enabled
  • Firing: Skips consumption, produces to outputs
  • Models: External generation overlaid on normal structure

Sink Transition:
  • Structure: May have output places (t• can be non-empty)
  • Enablement: Requires input tokens (normal rules)
  • Firing: Consumes from inputs, skips production
  • Models: External consumption overlaid on normal structure
```

**Trade-offs:**
- **Structural approach**: Cleaner semantics, enforces correct usage
- **Behavioral approach**: More flexible, can convert existing transitions

---

## 7. Recommended Formal Definition

### Pure Definition (Mathematically Correct)

```
Source Transition t:
  1. •t = ∅ (no input arcs)
  2. t• ≠ ∅ (at least one output arc)
  3. Always structurally enabled
  4. Firing: M' = M + Post(t, ·)
  5. No token consumption
  
Sink Transition t:
  1. •t ≠ ∅ (at least one input arc)
  2. t• = ∅ (no output arcs)
  3. Enabled when: ∀p ∈ •t: M(p) ≥ Pre(p,t)
  4. Firing: M' = M - Pre(·, t)
  5. No token production
```

**Advantages:**
- Mathematically clean
- Matches queueing theory
- Clear structural constraint
- Prevents misuse (e.g., source with input shouldn't make sense)

**Disadvantages:**
- More restrictive
- Can't convert existing transition to source/sink without rewiring
- May not handle all use cases (e.g., conditional sources)

### Hybrid Definition (Practical)

```
Source Transition t:
  1. Structural: •t = ∅ recommended (but not enforced)
  2. Behavioral: Ignores input arcs if present
  3. Enablement: Always enabled
  4. Firing: Skips consumption, produces to t•
  5. Warning if •t ≠ ∅ (suggests incorrect model)
  
Sink Transition t:
  1. Structural: t• = ∅ recommended (but not enforced)
  2. Behavioral: Ignores output arcs if present
  3. Enablement: Requires input tokens from •t
  4. Firing: Consumes from •t, skips production
  5. Warning if t• ≠ ∅ (suggests incorrect model)
```

**Advantages:**
- Flexible: Can mark existing transitions
- Backward compatible
- Handles edge cases
- User-friendly: No forced rewiring

**Disadvantages:**
- Less strict
- Can lead to confusion (source with inputs?)
- May hide modeling errors

---

## 8. Literature References

### Key Papers and Books

1. **Petri, C.A. (1962)**: "Kommunikation mit Automaten"
   - Original Petri net theory
   - No source/sink transitions defined

2. **Murata, T. (1989)**: "Petri Nets: Properties, Analysis and Applications"
   - Comprehensive survey
   - Defines source/sink PLACES, not transitions

3. **van der Aalst, W.M.P. (1998)**: "The Application of Petri Nets to Workflow Management"
   - Workflow nets with source/sink places
   - Interface transitions not explicitly named

4. **Balbo, G. (2007)**: "Introduction to Generalized Stochastic Petri Nets"
   - GSPN models
   - Mentions external arrivals/departures (implicit source/sink)

5. **Jensen, K. & Kristensen, L.M. (2009)**: "Coloured Petri Nets"
   - CPN theory
   - Environment interactions (input/output transitions)

6. **Marsan, M.A. et al. (1995)**: "Modelling with Generalized Stochastic Petri Nets"
   - Queueing systems in GSPN
   - Explicit arrival/departure transitions (source/sink semantics)

### Common Usage in Tools

**CPN Tools** (University of Aarhus):
- No explicit source/sink marking
- Users manually create input/output transitions
- Convention: Transitions with no inputs = sources

**PIPE** (Platform Independent Petri net Editor):
- No source/sink concept
- Uses immediate transitions for all

**GreatSPN**:
- Supports "input" and "output" transition types
- Structural requirement: Input = no preset, Output = no postset

**TimeNET**:
- Queueing Petri Nets support
- Explicit "source" and "sink" places
- Transitions connected to these are effectively source/sink

---

## 9. Recommendation for Shypn

### Option A: Pure Structural (Strict)

**Definition:**
- Source: •t = ∅, t• ≠ ∅
- Sink: •t ≠ ∅, t• = ∅

**Implementation:**
1. Validation: Reject if structure doesn't match
2. UI: Disable checkbox if arcs exist on wrong side
3. Auto-fix: Offer to remove incompatible arcs

**Pros:** Mathematically correct, clear semantics  
**Cons:** Less flexible, requires rewiring

### Option B: Behavioral with Warnings (Flexible)

**Definition:**
- Source: Ignores inputs (if any), produces to outputs
- Sink: Consumes inputs, ignores outputs (if any)

**Implementation:**
1. Allow any structure
2. Show warning icon if •t ≠ ∅ for source
3. Show warning icon if t• ≠ ∅ for sink
4. Tooltip: "Recommended structure: source has only outputs"

**Pros:** Flexible, backward compatible  
**Cons:** Can be confusing, allows "incorrect" models

### Option C: Hybrid (Recommended) ⭐

**Definition:**
- **Strict mode**: Enforce structure (•t = ∅ for source)
- **Permissive mode**: Allow but warn

**Implementation:**
1. Default: Structural validation enabled
2. Settings: Option to allow flexible source/sink
3. Visual indicator: Different color if structure is non-standard
4. Tooltip: Explain why input arcs on source are unusual

**Pros:** Best of both worlds  
**Cons:** More complex to implement

---

## 10. Conclusion

### Formal Definition (Recommended)

Based on queueing Petri net literature and common practice:

```
SOURCE TRANSITION:
  Formal Structure: •t = ∅ ∧ t• ≠ ∅
  Meaning: Transition has no input places, only output places
  Enablement: Always structurally enabled
  Firing: Produces tokens to output places
  Use: External arrivals, token generation, system inputs

SINK TRANSITION:
  Formal Structure: •t ≠ ∅ ∧ t• = ∅
  Meaning: Transition has input places, but no output places
  Enablement: Requires tokens in input places
  Firing: Consumes tokens from input places
  Use: External departures, token consumption, system outputs
```

### Implementation Strategy

**Recommendation: Start with Option C (Hybrid)**

**Phase 1: Add validation with warnings**
1. Check arc structure when source/sink is set
2. Show warning if structure doesn't match formal definition
3. Allow user to proceed (for backward compatibility)

**Phase 2: Add auto-correction**
1. Offer to remove incompatible arcs
2. "This is a source transition. Remove input arcs? [Yes] [No] [Cancel]"

**Phase 3: Add strict mode (optional)**
1. Settings toggle: "Enforce strict source/sink structure"
2. When enabled, prevent setting source if •t ≠ ∅

### Next Steps

1. ✅ Document formal definitions (this file)
2. ⏳ Update implementation to match formal structure
3. ⏳ Add validation warnings in UI
4. ⏳ Update user documentation with correct usage
5. ⏳ Add examples showing proper source/sink structure

---

## References

- Murata, T. (1989). Petri nets: Properties, analysis and applications. Proceedings of the IEEE, 77(4), 541-580.
- Marsan, M.A., et al. (1995). Modelling with generalized stochastic Petri nets. Wiley.
- van der Aalst, W.M.P. (1998). The application of Petri nets to workflow management. Journal of Circuits, Systems, and Computers, 8(01), 21-66.
- Jensen, K., & Kristensen, L.M. (2009). Coloured Petri nets: modelling and validation of concurrent systems. Springer Science & Business Media.

