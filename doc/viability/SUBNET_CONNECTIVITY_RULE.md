# Subnet Connectivity Requirement

**Date:** November 12, 2025  
**Critical Design Decision**

---

## Rule: Only Connected Localities Can Form Subnets

### The Problem
Initially, the design allowed forming subnets from any selected localities, even if they were completely disconnected in the model. This would create "artificial" subnets that don't represent real connected pathways.

### The Solution
**Subnets are only formed when localities are ACTUALLY CONNECTED in the model.**

A subnet is valid only if:
1. All selected localities share at least one place
2. They form a connected graph through shared places
3. This represents a real connected pathway in the model

---

## Implementation

### Connectivity Check (BFS Algorithm)
```python
def _are_localities_connected(self, localities: List[Any]) -> bool:
    """Check if localities form connected graph through shared places."""
    
    # Build adjacency: locality i → localities sharing places with i
    adjacency = {i: set() for i in range(len(localities))}
    
    for i in range(len(localities)):
        places_i = self._get_all_places(localities[i])
        for j in range(i + 1, len(localities)):
            places_j = self._get_all_places(localities[j])
            if places_i & places_j:  # Share places?
                adjacency[i].add(j)
                adjacency[j].add(i)
    
    # BFS to check if all reachable from first
    visited = {0}
    queue = [0]
    while queue:
        current = queue.pop(0)
        for neighbor in adjacency[current]:
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)
    
    return len(visited) == len(localities)
```

### build_subnet() Enforcement
```python
def build_subnet(self, localities: List[Any]) -> Subnet:
    if len(localities) > 1:
        if not self._are_localities_connected(localities):
            raise ValueError(
                "Cannot form subnet: selected localities are not connected. "
                "Localities must share at least one place to form a valid subnet."
            )
    # ... proceed with subnet construction
```

---

## User Experience

### Valid Selection (Connected)
```
User selects: T3, T7, T12
- T3 output P5 → T7 input P5  ✓ connected
- T7 output P9 → T12 input P9 ✓ connected
Result: Forms valid subnet with 3 transitions
```

### Invalid Selection (Disconnected)
```
User selects: T3, T15
- T3 has places {P1, P2, P5, P6}
- T15 has places {P20, P21, P22}
- No shared places ✗
Result: Error message + suggestions
```

### Error Message with Suggestions
```
❌ Cannot form subnet: selected localities are not connected.

Suggested groups that CAN form subnets:
  Group 1: T3, T7, T12 (connected via glycolysis pathway)
  Group 2: T15 (isolated)

Tip: Select localities that are part of the same pathway.
```

---

## Connected Components Detection

### Purpose
Help users understand which localities can be grouped together.

```python
def find_connected_components(self, localities: List[Any]) -> List[List[int]]:
    """Find connected components among localities.
    
    Returns:
        List of components, e.g., [[0, 1, 2], [3], [4, 5]]
        Means: loc0+loc1+loc2 connected, loc3 isolated, loc4+loc5 connected
    """
```

### Example
```python
# User selected 6 localities
localities = [loc_T1, loc_T2, loc_T3, loc_T4, loc_T5, loc_T6]

components = builder.find_connected_components(localities)
# Result: [[0, 1, 2], [3, 4], [5]]

# Interpretation:
# - T1, T2, T3 form connected subnet (e.g., upper glycolysis)
# - T4, T5 form connected subnet (e.g., TCA cycle)
# - T6 is isolated (e.g., separate pathway)

# User should investigate each group separately:
builder.build_subnet([loc_T1, loc_T2, loc_T3])  # ✓ Valid
builder.build_subnet([loc_T4, loc_T5])          # ✓ Valid
builder.build_subnet([loc_T6])                  # ✓ Valid (single)
builder.build_subnet([loc_T1, loc_T6])          # ✗ Error (disconnected)
```

---

## Benefits

### 1. **Biological Correctness**
- Subnets represent real pathways
- Analysis reflects actual metabolic flow
- No artificial groupings

### 2. **Meaningful Analysis**
- Boundary analysis makes sense (inputs/outputs of pathway)
- Conservation laws apply to connected subnet
- Dependencies are real flow relationships

### 3. **Clear Feedback**
- User understands why selection is invalid
- Suggestions guide correct grouping
- Prevents confusion from meaningless results

### 4. **Scalability**
- Can analyze large connected pathways
- Can identify isolated modules
- Helps understand model structure

---

## Edge Cases

### Single Locality
```python
# Always valid (trivially connected)
builder.build_subnet([loc1])  # ✓ Always succeeds
```

### Two Localities Sharing Multiple Places
```python
# T1 → {P1, P2, P3}
# T2 ← {P2, P3} → {P4}
# Share P2 and P3 → connected ✓
```

### Chain of Localities
```python
# T1 → P2 → T2 → P5 → T3 → P7 → T4
# All connected through chain ✓
# BFS will visit all from T1
```

### Star Topology
```python
# T1 → P_central ← T2, T3, T4, T5
# All share P_central → connected ✓
```

### Disconnected Groups
```python
# Group A: T1 → P2 → T2
# Group B: T3 → P5 → T4
# No shared places → disconnected ✗
# Must analyze separately
```

---

## Testing

### Test Coverage
```python
test_disconnected_localities_rejected()
  - Two localities with no shared places
  - Expects ValueError

test_are_localities_connected()
  - Connected localities → True
  - Single locality → True
  - Empty → True

test_find_connected_components()
  - 3 localities: [T1-T2 connected, T3 isolated]
  - Returns [[0,1], [2]]
```

---

## Summary

**Key Rule:** Subnets = Connected Localities Only

**Validation:** BFS graph traversal through shared places

**User Benefit:** Clear, biologically meaningful subnet analysis

**Error Handling:** Helpful suggestions for valid groupings

---

**This constraint ensures viability analysis provides REAL biological insights, not artificial groupings.** ✅
