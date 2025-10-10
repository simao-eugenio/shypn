# Petri Net Arc Semantics

**Date**: 2025-10-09  
**Topic**: Understanding arc connections and the bipartite property

---

## 🎯 Quick Answer: Place-to-Place Arcs

**Place-to-place arcs are INVALID in Petri nets!**

Petri nets follow a **bipartite graph** structure, meaning:
- ✅ **Valid:** Place → Transition
- ✅ **Valid:** Transition → Place  
- ❌ **Invalid:** Place → Place
- ❌ **Invalid:** Transition → Transition

---

## 📖 The Bipartite Property

### What is a Bipartite Graph?

A **bipartite graph** has two types of nodes where edges only connect nodes of **different types**.

In Petri nets:
- **Node Type 1:** Places (circles, represent states/resources)
- **Node Type 2:** Transitions (rectangles, represent events/actions)
- **Edges:** Arcs (directed arrows)

### The Rule

```
Arcs can ONLY connect:
  Place ──► Transition    (input arc)
  Transition ──► Place    (output arc)

Arcs CANNOT connect:
  Place ──► Place         ❌ INVALID
  Transition ──► Transition   ❌ INVALID
```

---

## 🔍 Why This Restriction?

### 1. Formal Semantics

**Places** represent:
- System states
- Resource availability
- Conditions
- Data storage

**Transitions** represent:
- System events
- Actions/operations
- State changes
- Process steps

**Arcs** represent:
- **Input arcs (Place→Transition):** Required resources/conditions for firing
- **Output arcs (Transition→Place):** Produced resources/new states after firing

### 2. Execution Model

A transition fires when:
1. **All input places** have sufficient tokens (≥ arc weight)
2. Firing **consumes** tokens from input places
3. Firing **produces** tokens in output places

**Why Place→Place doesn't make sense:**
- Places are passive (don't "do" anything)
- No firing mechanism to transfer tokens
- Violates the state/event separation

**Why Transition→Transition doesn't make sense:**
- Transitions are instantaneous events
- No intermediate state to hold tokens
- Violates the event/condition separation

### 3. Visual Example

```
Valid Petri Net:
    ●────►[T1]────►●
   P1            P2
   
   - P1 has tokens
   - T1 checks P1 (input arc)
   - T1 fires: consumes from P1, produces in P2
   - P2 receives tokens
```

```
Invalid (Place-to-Place):
    ●────►●
   P1    P2
   
   - How do tokens move?
   - No firing mechanism!
   - No event modeled!
```

```
Invalid (Transition-to-Transition):
    [T1]────►[T2]
    
   - Where are tokens stored between T1 and T2?
   - No state representation!
   - Missing intermediate place!
```

---

## 🛠️ Implementation in Shypn

### Arc Validation Code

From `src/shypn/netobjs/arc.py`:

```python
@staticmethod
def _validate_connection(source, target):
    """Validate that connection follows bipartite property.
    
    Petri nets are bipartite graphs: arcs must connect Place↔Transition only.
    - Valid: Place → Transition
    - Valid: Transition → Place
    - Invalid: Place → Place
    - Invalid: Transition → Transition
    
    Args:
        source: Source object
        target: Target object
    
    Raises:
        ValueError: If source and target are of the same type
    """
    from shypn.netobjs.place import Place
    from shypn.netobjs.transition import Transition
    
    source_is_place = isinstance(source, Place)
    target_is_place = isinstance(target, Place)
    
    # Both are places or both are transitions → invalid
    if source_is_place == target_is_place:
        source_type = "Place" if source_is_place else "Transition"
        target_type = "Place" if target_is_place else "Transition"
        raise ValueError(
            f"Invalid connection: {source_type} → {target_type}. "
            f"Arcs must connect Place↔Transition (bipartite property). "
            f"Valid connections: Place→Transition or Transition→Place."
        )
```

### What Happens if You Try?

If you attempt to create an invalid arc in the GUI:
1. The validation check in `Arc.__init__()` is called
2. A `ValueError` is raised with a descriptive message
3. The arc creation is prevented
4. User sees an error (if GUI handles it properly)

---

## 📚 Special Arc Types

Even special arc types must follow the bipartite rule:

### 1. Normal Arcs
- **Place → Transition:** Input arc (consume tokens)
- **Transition → Place:** Output arc (produce tokens)
- **Semantics:** Token transfer

### 2. Inhibitor Arcs
- **ONLY Place → Transition**
- **Cannot be Transition → Place** (no semantic meaning)
- **Semantics:** Transition can only fire if place has < threshold tokens
- **Validation:** `convert_to_inhibitor()` checks source is Place

### 3. Test Arcs (Future)
- **Place → Transition:** Check tokens without consuming
- **Transition → Place:** Not valid
- **Semantics:** Read-only check

### 4. Reset Arcs (Future)
- **Transition → Place:** Clear all tokens
- **Place → Transition:** Not valid
- **Semantics:** Reset place to zero

---

## 🎨 Visual Representation

### Valid Petri Net Patterns

#### Pattern 1: Simple Chain
```
●────►[T]────►●
P1           P2

Flow: P1 provides tokens → T fires → P2 receives tokens
```

#### Pattern 2: Merge (Multiple Inputs)
```
●────►\
P1     [T]────►●
      /        P3
●────►
P2

Flow: T requires tokens from BOTH P1 and P2 to fire
```

#### Pattern 3: Split (Multiple Outputs)
```
        ────►●
       /     P2
●────►[T]
P1     \────►●
            P3

Flow: When T fires, produces tokens in BOTH P2 and P3
```

#### Pattern 4: Synchronization
```
●────►[T1]────►●────►[T2]────►●
P1           P2            P3

Flow: Chain of state changes
```

### Invalid Patterns (Attempting Place-to-Place)

#### ❌ Wrong: Direct Token Transfer
```
●────►●
P1    P2

Problem: No mechanism to transfer tokens!
```

#### ✅ Correct: Use Intermediate Transition
```
●────►[T]────►●
P1           P2

Solution: T models the transfer event
```

#### ❌ Wrong: Bypassing State
```
[T1]────►[T2]

Problem: No place to store tokens between events!
```

#### ✅ Correct: Add Intermediate State
```
[T1]────►●────►[T2]
        P1

Solution: P1 models the intermediate state
```

---

## 🔄 KEGG Pathway Conversion

When converting KEGG pathways to Petri nets, the bipartite property is maintained:

### KEGG Elements → Petri Net Mapping

| KEGG Element | Petri Net Element | Notes |
|--------------|-------------------|-------|
| Compound | **Place** | Represents molecular species |
| Reaction | **Transition** | Represents biochemical reaction |
| Gene/Enzyme | Label on **Transition** | Catalyzes reaction |
| Substrate arc | **Place → Transition** | Input compound |
| Product arc | **Transition → Place** | Output compound |

### Example: Simple Reaction

KEGG Reaction:
```
Glucose + ATP → Glucose-6-phosphate + ADP
   (hexokinase)
```

Petri Net Model:
```
  ●───────►\
Glucose     [Hexokinase]────►●
            /             G6P
  ●───────►
 ATP

(Two output arcs from Hexokinase to ADP place not shown for clarity)
```

**Note:** All connections follow Place↔Transition rules!

---

## 🧪 Testing Arc Semantics

### Automated Tests

From `tests/pathway/test_integration.py`:

```python
def test_no_disconnected_arcs(self):
    """Verify all arcs connect valid nodes."""
    # Get all valid node IDs
    all_node_ids = set([p.id for p in document.places] + 
                       [t.id for t in document.transitions])
    
    # Check each arc
    for arc in document.arcs:
        self.assertIn(arc.source_id, all_node_ids, 
                     f"Arc {arc.id} has invalid source")
        self.assertIn(arc.target_id, all_node_ids,
                     f"Arc {arc.id} has invalid target")
```

### Manual Validation

In GUI, try to create invalid arcs:
1. Select arc tool
2. Click a place
3. Try to click another place
4. **Expected:** Error message or prevention of connection

---

## 📊 Arc Statistics in Enhancement Pipeline

The arc router processor reports statistics:

```python
{
    'total_arcs': 52,
    'parallel_arc_groups': 5,      # Groups of parallel arcs
    'arcs_in_parallel_groups': 12,  # Arcs that are parallel
    'arcs_with_curves': 12,         # Curved arcs (for visibility)
    'arcs_routed_around_obstacles': 0
}
```

**All arcs** (straight or curved) still follow the bipartite property!

---

## 🎓 Theoretical Background

### Petri Net Definition (Formal)

A Petri net is a 5-tuple: **PN = (P, T, F, W, M₀)**

Where:
- **P** = Set of places (circles)
- **T** = Set of transitions (rectangles)  
- **F** ⊆ (P × T) ∪ (T × P) = Flow relation (arcs)
- **W: F → ℕ⁺** = Arc weight function
- **M₀: P → ℕ** = Initial marking (token distribution)

**Key property:** F ⊆ (P × T) ∪ (T × P)

This means:
- F can contain pairs from **P × T** (Place → Transition)
- F can contain pairs from **T × P** (Transition → Place)
- F **cannot** contain **P × P** (Place → Place)
- F **cannot** contain **T × T** (Transition → Transition)

### Why Bipartite?

1. **Separation of Concerns:**
   - Places: Static states
   - Transitions: Dynamic events

2. **Clear Semantics:**
   - Input arcs: Preconditions
   - Output arcs: Postconditions

3. **Analysis Properties:**
   - Structural analysis (invariants, deadlocks)
   - Behavioral analysis (reachability, liveness)
   - Easier to verify and simulate

4. **Executable Model:**
   - Well-defined firing rules
   - Deterministic token game
   - Unambiguous state evolution

---

## 🚀 Practical Implications

### For GUI Users

1. **Creating Arcs:**
   - Must alternate: Place → Transition → Place → Transition...
   - Cannot shortcut with Place → Place

2. **Modeling Patterns:**
   - Every action needs a transition
   - Every state needs a place
   - Direct resource transfer = add intermediate transition

3. **Error Messages:**
   - "Invalid connection: Place → Place"
   - "Arcs must connect Place↔Transition"

### For Developers

1. **Arc Creation:**
   - Always validate source/target types
   - Raise ValueError for invalid connections
   - Provide clear error messages

2. **Import/Export:**
   - Maintain bipartite property during conversion
   - KEGG compounds → Places
   - KEGG reactions → Transitions

3. **Analysis:**
   - Leverage bipartite structure for optimization
   - Separate place and transition algorithms
   - Use matrix representations (incidence matrix)

---

## 📖 References

### Standard Petri Net Theory

1. **Peterson, J. L.** (1981). *Petri Net Theory and the Modeling of Systems*. Prentice Hall.
   - Classic reference on Petri net foundations
   - Defines bipartite property formally

2. **Murata, T.** (1989). "Petri nets: Properties, analysis and applications." *Proceedings of the IEEE*, 77(4), 541-580.
   - Comprehensive survey paper
   - Explains why bipartite structure is essential

3. **Reisig, W., & Rozenberg, G.** (Eds.). (1998). *Lectures on Petri nets I: Basic models*. Springer.
   - Advanced treatise on Petri net theory
   - Mathematical foundations of the bipartite property

### Biological Pathway Modeling

4. **Chaouiya, C.** (2007). "Petri net modelling of biological networks." *Briefings in bioinformatics*, 8(4), 210-219.
   - Application to biochemical networks
   - Shows why Place (compound) ↔ Transition (reaction) is natural

---

## 💡 Summary

### Key Takeaways

1. ✅ **Petri nets are bipartite graphs**
   - Two node types: Places and Transitions
   - Arcs only connect different types

2. ❌ **Place-to-place arcs are invalid**
   - No semantic meaning
   - No execution mechanism
   - Violates formal definition

3. ✅ **Solution: Add intermediate transitions**
   - Models the transfer/transformation event
   - Maintains bipartite property
   - Preserves clear semantics

4. 🔒 **Shypn enforces this rule**
   - Validation in `Arc.__init__()`
   - ValueError raised for invalid connections
   - GUI should prevent such connections

5. 🧬 **KEGG conversion respects this**
   - Compounds → Places
   - Reactions → Transitions
   - Natural bipartite structure

---

## ❓ FAQ

**Q: Why can't I connect two places directly?**  
A: Because places represent states, not actions. You need a transition to model the event that changes state.

**Q: What if I just want to move tokens from P1 to P2?**  
A: Create an intermediate transition: P1 → T → P2. The transition models the "move" event.

**Q: Can inhibitor arcs connect transition to place?**  
A: No! Inhibitor arcs are only Place → Transition. They check if a place has < threshold tokens before allowing transition to fire.

**Q: Does this apply to curved arcs too?**  
A: Yes! Curved arcs are just visual enhancements. They still follow Place↔Transition rules.

**Q: What about test arcs or reset arcs?**  
A: All special arc types must follow the bipartite property, just with different firing semantics.

**Q: Why do other modeling formalisms allow state-to-state connections?**  
A: Different formalisms have different semantics:
- **State machines:** Allow state-to-state transitions (events implicit)
- **Petri nets:** Explicit events (transitions) between states (places)
- **Neither is "wrong"** - just different modeling approaches

---

**Remember:** The bipartite property is fundamental to Petri nets. It's not a limitation, but a design choice that provides clear semantics, executable models, and powerful analysis capabilities! 🎯
