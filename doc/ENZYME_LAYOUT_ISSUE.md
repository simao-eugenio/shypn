# Enzyme/Catalyst Layout Issue

## Problem

**Enzyme places connected only via test arcs are NOT positioned by hierarchical layout.**

### Root Cause

The hierarchical layout algorithm (`hierarchical_layout.py`) only considers:
- **Reactants**: Input species consumed by reactions
- **Products**: Output species produced by reactions

```python
# Line 154 in _build_dependency_graph()
reactants = [species_id for species_id, _ in reaction.reactants]
products = [species_id for species_id, _ in reaction.products]
# NOTE: Modifiers/catalysts are IGNORED!
```

**Result**: Enzyme/catalyst places (modifiers) are:
1. ❌ Not included in dependency graph
2. ❌ Not assigned to any layer
3. ❌ Not positioned by hierarchical layout
4. ⚠️ May appear at (0, 0) or be missing from final layout

## Current Behavior

### SBML Example
```xml
<reaction id="R1">
  <listOfReactants>
    <speciesReference species="Glucose"/>  <!-- Positioned ✓ -->
  </listOfReactants>
  <listOfProducts>
    <speciesReference species="G6P"/>      <!-- Positioned ✓ -->
  </listOfProducts>
  <listOfModifiers>
    <modifierSpeciesReference species="Hexokinase"/>  <!-- NOT positioned ❌ -->
  </listOfModifiers>
</reaction>
```

### KEGG Example (when create_enzyme_places=True)
```python
# Compound places: Positioned correctly ✓
# Enzyme places: NOT positioned ❌
```

## Impact

**When importing SBML/KEGG with catalysts:**
1. Compound places: Arranged hierarchically ✓
2. Transitions: Positioned between layers ✓
3. Normal arcs: Connect properly ✓
4. **Enzyme places: Missing positions or at (0,0)** ❌
5. **Test arcs: Drawn but from wrong position** ⚠️

## Why This Wasn't Noticed Before

1. **KEGG default**: `create_enzyme_places=False` → no enzyme places created
2. **SBML**: Modifiers rare in test files
3. **Manual models**: Users position catalysts manually

## Detection

**Enzyme places have test arcs but no position:**
```python
# Check for unpositioned enzyme places
for place in document.places:
    if place.metadata.get('is_enzyme'):
        if place.id not in positions:
            print(f"⚠️ Enzyme {place.name} not positioned!")
```

## Solution Options

### Option 1: Position Catalysts Above Reactions (Recommended)

**Concept**: Enzymes/catalysts should appear "above" the reactions they catalyze

```python
def _build_dependency_graph(self):
    # ... existing code ...
    
    # NEW: Include modifiers
    for reaction in self.pathway.reactions:
        reactants = [species_id for species_id, _ in reaction.reactants]
        products = [species_id for species_id, _ in reaction.products]
        modifiers = reaction.modifiers  # NEW
        
        # Position modifiers "above" reactants (earlier layer)
        for modifier_id in modifiers:
            # Modifiers should appear before their reactions
            # Give them in_degree = 0 (place in first layer)
            if modifier_id in in_degree:
                in_degree[modifier_id] = 0  # Force to first layer
```

**Result**: Enzymes appear at top of pathway (as regulatory layer)

### Option 2: Position Catalysts Beside Reactions

**Concept**: Enzymes positioned horizontally near the reactions they catalyze

```python
def _position_reactions(self, species_positions):
    # ... existing code ...
    
    # NEW: Position modifiers beside reactions
    for reaction in self.pathway.reactions:
        reaction_pos = positions[reaction.id]
        
        for i, modifier_id in enumerate(reaction.modifiers):
            # Position to the side of reaction
            offset_x = 50 + (i * 30)  # Offset horizontally
            positions[modifier_id] = (
                reaction_pos[0] + offset_x,
                reaction_pos[1]
            )
```

**Result**: Enzymes clustered near their reactions

### Option 3: Use Original KEGG/SBML Positions for Enzymes

**Concept**: Keep enzyme positions from source (KEGG/SBML layout)

```python
# In SBML parser: Store modifier positions from layout extension
# In KEGG parser: Already have graphics.x, graphics.y

# In hierarchical layout: Don't move enzymes
def calculate_hierarchical_layout(self):
    positions = {}
    
    # Position regular species hierarchically
    # ...
    
    # Keep enzyme positions from source
    for species in self.pathway.species:
        if species.metadata.get('is_enzyme'):
            if species.id in self.pathway.positions:
                positions[species.id] = self.pathway.positions[species.id]
```

**Result**: Enzymes stay where they were in original diagram

### Option 4: Separate Enzyme Layer

**Concept**: Create dedicated layer(s) for regulatory elements

```python
def _assign_layers(self, graph, in_degree):
    # ... existing layers for substrates/products ...
    
    # NEW: Create enzyme layer(s)
    enzyme_layer = []
    for species in self.pathway.species:
        if species.metadata.get('is_enzyme'):
            enzyme_layer.append(species.id)
    
    if enzyme_layer:
        # Insert enzyme layer at top (before first substrate layer)
        layers.insert(0, enzyme_layer)
```

**Result**: All enzymes in dedicated regulatory layer at top

## Recommendation

**Use Option 3 (Preserve Source Positions) + Fallback to Option 1**

**Rationale**:
1. KEGG pathways already have enzyme positions (graphics.x, graphics.y)
2. SBML may have layout extensions with modifier positions
3. If no source position available, fall back to "above reactions" logic

**Implementation**:
```python
def _position_enzymes(self, species_positions, reaction_positions):
    """Position enzyme/catalyst places."""
    for species in self.pathway.species:
        if species.metadata.get('is_enzyme'):
            species_id = species.id
            
            # Option A: Use original position if available
            if species_id in self.pathway.positions:
                species_positions[species_id] = self.pathway.positions[species_id]
                continue
            
            # Option B: Position above catalyzed reaction
            catalyzes = species.metadata.get('catalyzes_reaction')
            if catalyzes and catalyzes in reaction_positions:
                rx, ry = reaction_positions[catalyzes]
                # Position above reaction (negative Y offset)
                species_positions[species_id] = (rx, ry - self.vertical_spacing * 0.5)
            else:
                # Option C: Fallback to top-left corner
                species_positions[species_id] = (0, 0)
```

## Testing

**Test case**:
```python
def test_enzyme_positioning_hierarchical_layout():
    # Create pathway with enzyme
    pathway = PathwayData()
    
    glucose = Species(id="S1", name="Glucose")
    g6p = Species(id="S2", name="G6P")
    hexokinase = Species(id="E1", name="Hexokinase")
    hexokinase.metadata['is_enzyme'] = True
    
    pathway.species = [glucose, g6p, hexokinase]
    
    reaction = Reaction(
        id="R1",
        reactants=[("S1", 1)],
        products=[("S2", 1)],
        modifiers=["E1"]  # Enzyme
    )
    pathway.reactions = [reaction]
    
    # Calculate layout
    layout = HierarchicalLayoutProcessor(pathway)
    positions = layout.calculate_hierarchical_layout()
    
    # Verify enzyme is positioned
    assert "E1" in positions, "Enzyme must have position"
    assert positions["E1"] != (0, 0), "Enzyme should not be at origin"
    
    # Verify enzyme is "above" reaction (lower Y in graphics coords)
    assert positions["E1"][1] < positions["R1"][1], \
        "Enzyme should appear above reaction"
```

## Files to Modify

1. **`src/shypn/data/pathway/hierarchical_layout.py`**
   - Add `_position_enzymes()` method
   - Call from `calculate_hierarchical_layout()`
   - Handle modifiers in graph building

2. **`src/shypn/data/pathway/pathway_converter.py`** (SBML)
   - Ensure enzyme positions stored in pathway.positions
   - Pass positions to hierarchical layout

3. **`src/shypn/importer/kegg/pathway_converter.py`** (KEGG)
   - Store enzyme graphics.x, graphics.y in pathway.positions
   - Already done for compounds, extend to enzymes

## Priority

**HIGH** - This affects visual quality of biological models

**Impact**:
- SBML with modifiers: Broken layout
- KEGG with create_enzyme_places=True: Broken layout
- Manual models with catalysts: May work if users positioned manually

## Related Issues

- Enzyme places ARE connected (test arcs count)
- Enzyme places are NOT isolated (locality detector sees them)
- Issue is specifically with LAYOUT algorithms that use reaction structure
