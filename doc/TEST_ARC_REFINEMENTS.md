# Test Arc Refinement Analysis

## Overview

User reported 4 refinement issues with test arcs:
1. Test arcs rendered center-to-center (should be perimeter-to-perimeter)
2. Isolated catalyst places with no test arcs
3. Isolated places included in layout algorithms
4. Isolated places disrupting layout algorithms

## Issue 1: Test Arc Rendering (Center-to-Center)

### Problem
Test arcs currently render lines from the **center** of source place to the **center** of target transition, rather than from **perimeter to perimeter** like normal arcs.

### Root Cause
`TestArc.render()` in `src/shypn/netobjs/test_arc.py` directly uses node positions:

```python
# Line 242-243 in test_arc.py
x1, y1 = self.source.x, self.source.y  # CENTER
x2, y2 = self.target.x, self.target.y  # CENTER
```

Normal arcs use `_get_boundary_point()` method (inherited from Arc) to calculate perimeter intersections:

```python
# Arc.render() approach (lines 180-195 in arc.py)
src_world_x, src_world_y = self.source.x, self.source.y
tgt_world_x, tgt_world_y = self.target.x, self.target.y
dx_world = tgt_world_x - src_world_x
dy_world = tgt_world_y - src_world_y
# ... normalize direction ...
start_world_x, start_world_y = self._get_boundary_point(
    self.source, src_world_x, src_world_y, dx_world, dy_world)
end_world_x, end_world_y = self._get_boundary_point(
    self.target, tgt_world_x, tgt_world_y, -dx_world, -dy_world)
```

### Fix
Update `TestArc.render()` to use the same boundary calculation approach as normal arcs:

```python
def render(self, cr, zoom: float = 1.0, selected: bool = False):
    """Render test arc with dashed line and hollow diamond."""
    # Get source and target CENTER positions
    src_world_x, src_world_y = self.source.x, self.source.y
    tgt_world_x, tgt_world_y = self.target.x, self.target.y
    
    # Calculate direction from centers
    dx_world = tgt_world_x - src_world_x
    dy_world = tgt_world_y - src_world_y
    length_world = (dx_world * dx_world + dy_world * dy_world) ** 0.5
    
    if length_world < 1:
        return  # Too short to draw
    
    # Normalize direction
    dx_world /= length_world
    dy_world /= length_world
    
    # Get BOUNDARY points (perimeter intersection)
    start_world_x, start_world_y = self._get_boundary_point(
        self.source, src_world_x, src_world_y, dx_world, dy_world)
    end_world_x, end_world_y = self._get_boundary_point(
        self.target, tgt_world_x, tgt_world_y, -dx_world, -dy_world)
    
    # Use boundary points for rendering (not centers)
    x1, y1 = start_world_x, start_world_y
    x2, y2 = end_world_x, end_world_y
    
    # ... rest of rendering code ...
```

**File to modify**: `src/shypn/netobjs/test_arc.py` (lines 228-286)

**Priority**: MEDIUM (visual quality improvement)

---

## Issue 2: Isolated Catalyst Places (No Test Arcs)

### Problem
When importing SBML/KEGG with `create_enzyme_places=True`, some enzyme places are created but do NOT have test arcs connecting them to transitions. These are truly isolated (disconnected from network).

### Root Cause
Test arc creation can fail in converters:

**SBML ModifierConverter** (`pathway_converter.py` lines 617-650):
```python
for modifier_species_id in reaction.modifiers:
    place = self.species_to_place.get(modifier_species_id)
    if not place:
        # Place not created → skip test arc
        continue
    
    transition = self.reaction_to_transition.get(reaction.id)
    if not transition:
        # Transition not created → skip test arc
        continue
    
    # Create test arc...
```

**KEGG EnzymeConverter** (`kegg/pathway_converter.py` lines 64-102):
```python
for entry_id, entry in self.pathway.entries.items():
    if not entry.is_gene():
        continue  # Not an enzyme
    
    if not entry.reaction:
        continue  # No reaction attribute → skip
    
    enzyme_place = self.entry_to_place.get(entry_id)
    if not enzyme_place:
        continue  # Place filtered out → skip test arc
    
    reaction_transition = self.reaction_name_to_transition.get(entry.reaction)
    if not reaction_transition:
        # Reaction doesn't match any transition → skip test arc
        continue
    
    # Create test arc...
```

**Scenarios leading to isolated enzymes:**
1. Enzyme entry has no `reaction` attribute
2. Enzyme `reaction` doesn't match any transition ID
3. Transition was filtered out by `filter_isolated_compounds`
4. Species/entry was created but corresponding transition wasn't

### Current Behavior
Converters log warnings and continue:
```python
self.logger.debug(
    f"Skipping enzyme entry {entry_id}: "
    f"reaction {entry.reaction} not found in transitions"
)
```

Result: Enzyme place exists in document but has no arcs (isolated).

### Fix Options

**Option 1: Don't Create Isolated Enzyme Places** (Recommended)
```python
# In KEGG converter: check if test arc can be created BEFORE creating place
enzyme_entries_with_reactions = []
for entry_id, entry in pathway.entries.items():
    if entry.is_gene() and entry.reaction:
        if entry.reaction in reaction_name_to_transition:
            enzyme_entries_with_reactions.append(entry_id)

# Only create places for enzymes that will have test arcs
for entry_id in enzyme_entries_with_reactions:
    # Create enzyme place...
```

**Option 2: Visual Indicator** (Alternative)
- Create enzyme place anyway
- Add metadata: `place.metadata['orphaned_enzyme'] = True`
- UI shows warning icon or gray color for orphaned enzymes

**Option 3: Log and Accept** (Current)
- Keep current behavior
- Document that some enzymes may be isolated
- Users can manually delete or connect them

**Priority**: LOW (edge case in malformed/incomplete data)

---

## Issue 3: Catalysts Not Positioned by Layout

### Problem
Enzyme/catalyst places are **NOT positioned** by hierarchical layout algorithm, even when they have test arcs connecting them to transitions.

### Root Cause
Hierarchical layout only processes species in **dependency graph**, which is built from reactants and products:

**`hierarchical_layout.py` lines 146-157:**
```python
def _build_dependency_graph(self):
    """Build directed graph of species dependencies."""
    graph = defaultdict(list)
    in_degree = defaultdict(int)
    
    # Initialize all species
    for species in self.pathway.species:
        in_degree[species.id] = 0
    
    # Build edges from reactions
    for reaction in self.pathway.reactions:
        reactants = [species_id for species_id, _ in reaction.reactants]
        products = [species_id for species_id, _ in reaction.products]
        # ❌ NOTE: Modifiers are NOT extracted here!
        
        # Build edges reactant → product
        for reactant_id in reactants:
            for product_id in products:
                graph[reactant_id].append(product_id)
                in_degree[product_id] += 1
```

**Algorithm flow:**
1. `_build_dependency_graph()` - Creates graph from reactants/products only
2. `_assign_layers()` - Uses topological sort on dependency graph
3. `_position_layers()` - Positions species assigned to layers

**Result**: Catalysts/modifiers are:
- ❌ Not in dependency graph
- ❌ Not assigned to any layer
- ❌ Not positioned by `_position_layers()`
- ⚠️ Keep original positions from KGML/SBML (or default to 0,0)

### Current Behavior

**KEGG Import:**
- Enzyme place created at KGML `<graphics x="150" y="50"/>`
- Layout runs, positions reactants/products
- Enzyme keeps original position (150, 50)
- May look correct if KGML had good layout
- May look wrong if KGML layout was poor

**SBML Import:**
- Modifier place created at default position or SBML layout
- Layout runs, positions reactants/products
- Modifier keeps original position
- Often appears at (0, 0) if no SBML layout info

### Impact
- Test arcs may be drawn from wrong positions
- Enzyme places may overlap with other nodes
- Visual layout appears broken for biological models

### Fix
Add enzyme/catalyst positioning after main layout:

**`hierarchical_layout.py` - Add new method:**
```python
def _position_enzymes(self, species_positions: Dict[str, Tuple[float, float]],
                     reaction_positions: Dict[str, Tuple[float, float]]) -> None:
    """Position enzyme/catalyst species that were not positioned by main layout.
    
    Enzymes/catalysts (modifiers) are not in the dependency graph, so they're
    not assigned to layers. This method positions them based on:
    1. Original source position (KGML/SBML) if available
    2. Position "above" catalyzed reaction (fallback)
    3. Top-left corner (last resort)
    """
    for species in self.pathway.species:
        # Skip if already positioned
        if species.id in species_positions:
            continue
        
        # Check if this is an enzyme/catalyst
        is_enzyme = False
        catalyzes_reaction = None
        
        # Check modifiers field (SBML)
        for reaction in self.pathway.reactions:
            if species.id in reaction.modifiers:
                is_enzyme = True
                catalyzes_reaction = reaction.id
                break
        
        # Check metadata (KEGG)
        if hasattr(species, 'metadata') and species.metadata.get('is_enzyme'):
            is_enzyme = True
            catalyzes_reaction = species.metadata.get('catalyzes_reaction')
        
        if not is_enzyme:
            # Not an enzyme, skip positioning
            continue
        
        # Strategy 1: Use original position from source
        if hasattr(self.pathway, 'positions') and species.id in self.pathway.positions:
            x, y = self.pathway.positions[species.id]
            species_positions[species.id] = (x, y)
            self.logger.debug(
                f"Positioned enzyme {species.id} at original position ({x:.1f}, {y:.1f})"
            )
            continue
        
        # Strategy 2: Position "above" catalyzed reaction
        if catalyzes_reaction and catalyzes_reaction in reaction_positions:
            rx, ry = reaction_positions[catalyzes_reaction]
            # Place enzyme 80px above reaction
            x = rx
            y = ry - 80.0
            species_positions[species.id] = (x, y)
            self.logger.debug(
                f"Positioned enzyme {species.id} above reaction "
                f"{catalyzes_reaction} at ({x:.1f}, {y:.1f})"
            )
            continue
        
        # Strategy 3: Last resort - top-left corner
        x, y = 50.0, 50.0
        species_positions[species.id] = (x, y)
        self.logger.warning(
            f"Positioned enzyme {species.id} at default position ({x:.1f}, {y:.1f})"
        )
```

**Call from `calculate_hierarchical_layout()` after Phase 4:**
```python
def calculate_hierarchical_layout(self):
    """Calculate hierarchical layout with layers."""
    # ... existing phases 1-4 ...
    
    # Phase 4: Position transitions between layers
    reaction_positions = self._position_transitions(species_positions, layers)
    
    # Phase 5: Position enzymes/catalysts (NEW)
    self._position_enzymes(species_positions, reaction_positions)
    
    # Return final layout
    return LayoutData(species_positions, reaction_positions)
```

**Files to modify:**
- `src/shypn/data/pathway/hierarchical_layout.py` (add `_position_enzymes()` method)
- `src/shypn/importer/kegg/pathway_converter.py` (ensure enzyme positions stored in pathway.positions)

**Priority**: HIGH (affects all biological models with catalysts)

---

## Issue 4: Layout "Disruption" Clarification

### Problem Statement
User reported: "Isolated places disrupted layout algorithms"

### Analysis
This is the **same issue as Issue 3** - not actual "disruption" but **missing positioning**.

**What was expected:**
- Enzyme places disrupt layout by interfering with positioning of reactants/products

**What actually happens:**
- Enzyme places are **ignored** by layout algorithm
- Reactants/products are positioned correctly
- Enzymes keep original positions (or 0,0)
- Visual appears "disrupted" because enzymes in wrong places

### Evidence
From `hierarchical_layout.py` line 190:
```python
if not current_layer:
    # Cyclic graph or isolated species - add all to layer 0
    self.logger.warning("No initial substrates found, using all species in layer 0")
    return [[species.id for species in self.pathway.species]]
```

This fallback is for **truly isolated species** (no connections at all). Enzymes with test arcs are **not** isolated - they have connections. They're just not included in the dependency graph that layout uses.

### Conclusion
- Issues 3 and 4 are the **same problem**: catalysts not positioned
- Solution is the same: implement `_position_enzymes()` method
- Priority: HIGH

---

## Summary & Action Plan

| Issue | Description | Root Cause | Priority | Fix |
|-------|-------------|------------|----------|-----|
| **1** | Test arcs render center-to-center | TestArc.render() doesn't use boundary calculation | MEDIUM | Update render() to use _get_boundary_point() |
| **2** | Isolated enzyme places (no test arcs) | Test arc creation skipped when reaction doesn't match | LOW | Skip enzyme place creation if no test arc |
| **3** | Enzymes not positioned by layout | Layout only processes dependency graph (reactants/products) | HIGH | Add _position_enzymes() method |
| **4** | Layout "disruption" | Same as Issue 3 - enzymes not positioned | HIGH | Same fix as Issue 3 |

### Recommended Implementation Order

1. **Fix Issue 3/4 (HIGH)**: Implement enzyme positioning
   - Add `_position_enzymes()` method to `hierarchical_layout.py`
   - Ensure KEGG stores enzyme positions in `pathway.positions`
   - Test with KEGG glycolysis (has multiple enzymes)
   - Test with SBML models containing modifiers

2. **Fix Issue 1 (MEDIUM)**: Update test arc rendering
   - Modify `TestArc.render()` to use boundary calculations
   - Test visual rendering with places and transitions of different sizes
   - Verify hollow diamond still appears at correct position

3. **Fix Issue 2 (LOW)**: Handle isolated enzymes
   - Add validation in converters to skip enzyme places without test arcs
   - Add unit test for enzyme with invalid reaction ID
   - Document expected behavior in converter docstrings

### Test Cases Needed

```python
def test_test_arc_perimeter_rendering():
    """Verify test arcs connect at node perimeters, not centers."""
    # Create place (radius 30) at (100, 100)
    # Create transition (rect 20x40) at (200, 100)
    # Create test arc
    # Verify arc starts at (130, 100) not (100, 100)
    # Verify arc ends at (190, 100) not (200, 100)

def test_enzyme_positioning_hierarchical_layout():
    """Verify enzymes positioned by hierarchical layout."""
    # Import KEGG with create_enzyme_places=True
    # Run hierarchical layout
    # Verify enzyme places have positions != (0, 0)
    # Verify enzymes positioned "above" their reactions

def test_no_isolated_enzyme_places():
    """Verify isolated enzyme places not created."""
    # Create enzyme entry with invalid reaction ID
    # Convert with create_enzyme_places=True
    # Verify enzyme place NOT created
    # Verify converter logs warning
```

---

## References

- **ENZYME_LAYOUT_ISSUE.md**: Original analysis of enzyme positioning problem
- **Test Arc Implementation**: `src/shypn/netobjs/test_arc.py`
- **Hierarchical Layout**: `src/shypn/data/pathway/hierarchical_layout.py`
- **SBML Converter**: `src/shypn/data/pathway/pathway_converter.py` (ModifierConverter)
- **KEGG Converter**: `src/shypn/importer/kegg/pathway_converter.py` (KEGGEnzymeConverter)
