# Layout Parametrization Plan

**Date**: October 14, 2025  
**Goal**: Centralize all force-directed layout parameters in configurable system, independent of UI

---

## Current State Analysis

### Problems:
1. **Hardcoded values** scattered across multiple files
2. **No single source of truth** for parameter defaults
3. **Tight UI coupling** (parameters initialized in SBML import panel)
4. **Difficult to experiment** with different configurations
5. **No parameter validation** or logging

### Current Parameter Locations:
```
pathway_postprocessor.py:
  - k_factor: 1.0-2.0 (adaptive)
  - iterations: 100
  - scale_factor: 300-600px (adaptive)
  - threshold: 1e-6
  - edge weights: stoichiometry-based

layout_projector.py:
  - layer_threshold: 50.0
  - layer_spacing: 200.0
  - min_horizontal_spacing: 120.0
  - canvas_width: 2000.0
  - top_margin: 800.0
```

---

## Proposed Architecture

### 1. Centralized Configuration Module

**File**: `src/shypn/data/pathway/layout_config.py`

```python
from dataclasses import dataclass
from typing import Optional
from enum import Enum


class WeightMode(Enum):
    """Edge weight calculation strategies."""
    UNIFORM = "uniform"              # All edges weight=1.0
    STOICHIOMETRY = "stoichiometry"  # Based on reaction stoichiometry
    REVERSIBILITY = "reversibility"  # Weaker for reversible reactions
    REGULATION = "regulation"        # Include regulatory interactions


@dataclass
class ForceDirectedConfig:
    """Configuration for force-directed (spring) layout physics."""
    
    # Physics parameters
    k: float = 1.5                    # Optimal node distance (spring rest length)
    iterations: int = 100             # Number of simulation steps
    threshold: float = 1e-6           # Convergence threshold
    scale: float = 400.0              # Output coordinate scale (px)
    seed: Optional[int] = 42          # Random seed (None=random)
    
    # Edge weights
    weight_mode: WeightMode = WeightMode.STOICHIOMETRY
    
    # Advanced
    temperature: float = 0.1          # Cooling factor (NetworkX hardcoded)
    min_distance: float = 0.01        # Minimum node distance (NetworkX hardcoded)


@dataclass
class ProjectionConfig:
    """Configuration for 2D projection post-processing."""
    
    # Layer detection
    layer_threshold: float = 50.0     # Y-clustering threshold (px)
    
    # Spacing
    layer_spacing: float = 200.0      # Vertical space between layers (px)
    min_horizontal_spacing: float = 120.0  # Min X spacing (px)
    
    # Canvas
    canvas_width: float = 2000.0      # Maximum width (px)
    canvas_center_x: float = 1000.0   # Horizontal center (px)
    top_margin: float = 800.0         # Y position of top layer (px)
    left_margin: float = 100.0        # Left padding (px)
    
    # Spiral-specific
    spiral_tightness: float = 0.5     # Radius growth rate
    spiral_base_radius: float = 100.0 # Starting radius (px)


@dataclass
class LayoutConfig:
    """Complete layout configuration."""
    
    force_directed: ForceDirectedConfig
    projection: ProjectionConfig
    use_spiral: bool = False
    
    def __post_init__(self):
        """Validate configuration."""
        if self.force_directed.k <= 0:
            raise ValueError("k must be positive")
        if self.force_directed.iterations <= 0:
            raise ValueError("iterations must be positive")
        if self.projection.layer_spacing <= 0:
            raise ValueError("layer_spacing must be positive")


# Preset configurations
class LayoutPresets:
    """Named configuration presets for different use cases."""
    
    @staticmethod
    def compact() -> LayoutConfig:
        """Dense layout for small pathways (≤10 nodes)."""
        return LayoutConfig(
            force_directed=ForceDirectedConfig(
                k=1.0,
                scale=300.0,
                iterations=80
            ),
            projection=ProjectionConfig(
                layer_spacing=150.0,
                min_horizontal_spacing=80.0,
                canvas_width=1500.0
            )
        )
    
    @staticmethod
    def balanced() -> LayoutConfig:
        """Balanced layout for medium pathways (11-20 nodes)."""
        return LayoutConfig(
            force_directed=ForceDirectedConfig(
                k=1.5,
                scale=400.0,
                iterations=100
            ),
            projection=ProjectionConfig(
                layer_spacing=200.0,
                min_horizontal_spacing=120.0,
                canvas_width=2000.0
            )
        )
    
    @staticmethod
    def spacious() -> LayoutConfig:
        """Loose layout for large pathways (>20 nodes)."""
        return LayoutConfig(
            force_directed=ForceDirectedConfig(
                k=2.0,
                scale=600.0,
                iterations=120
            ),
            projection=ProjectionConfig(
                layer_spacing=250.0,
                min_horizontal_spacing=150.0,
                canvas_width=2500.0,
                top_margin=1000.0
            )
        )
    
    @staticmethod
    def spiral() -> LayoutConfig:
        """Spiral layout (entry at center, products outward)."""
        config = LayoutPresets.balanced()
        config.use_spiral = True
        config.projection.spiral_tightness = 0.3  # Tighter spiral
        return config
    
    @staticmethod
    def auto(num_nodes: int) -> LayoutConfig:
        """Automatically choose config based on pathway size."""
        if num_nodes <= 10:
            return LayoutPresets.compact()
        elif num_nodes <= 20:
            return LayoutPresets.balanced()
        else:
            return LayoutPresets.spacious()
```

---

## Implementation Steps

### Phase 1: Core Configuration (Priority 1) ✅

1. **Create `layout_config.py`** with dataclasses
   - ForceDirectedConfig
   - ProjectionConfig
   - LayoutConfig
   - LayoutPresets

2. **Add weight calculation strategies**
   ```python
   class EdgeWeightCalculator:
       @staticmethod
       def calculate(reaction, species_id, stoich, mode: WeightMode) -> float:
           if mode == WeightMode.UNIFORM:
               return 1.0
           elif mode == WeightMode.STOICHIOMETRY:
               return max(1.0, float(stoich))
           elif mode == WeightMode.REVERSIBILITY:
               base = max(1.0, float(stoich))
               return base * 0.5 if reaction.reversible else base
           # etc...
   ```

### Phase 2: Refactor Core Components (Priority 2) 🔄

3. **Update `pathway_postprocessor.py`**
   ```python
   class LayoutProcessor(BaseProcessor):
       def __init__(self, pathway, config: LayoutConfig):
           self.config = config
           # Remove individual parameters
   
       def _calculate_force_directed_layout(self, ...):
           # Use self.config.force_directed.k
           # Use self.config.force_directed.iterations
           # etc...
   ```

4. **Update `layout_projector.py`**
   ```python
   class LayoutProjector:
       def __init__(self, config: ProjectionConfig):
           self.config = config
           # Replace individual params with config
   ```

### Phase 3: Integration (Priority 3) 🔌

5. **Update `sbml_import_panel.py`**
   ```python
   # Get user options or use defaults
   num_nodes = len(pathway.species) + len(pathway.reactions)
   config = LayoutPresets.auto(num_nodes)
   
   postprocessor = PathwayPostProcessor(
       config=config,
       scale_factor=scale_factor  # Keep token scaling separate
   )
   ```

6. **Add validation and logging**
   ```python
   def validate(self):
       """Validate all parameters."""
       # Check ranges, raise ValueError if invalid
   
   def log_config(self, logger):
       """Log active configuration for debugging."""
       logger.info(f"Layout config: {self}")
   ```

### Phase 4: Documentation (Priority 4) 📝

7. **Create `LAYOUT_CONFIGURATION.md`**
   - Architecture overview
   - Parameter explanations
   - Preset descriptions
   - How to customize
   - Examples

8. **Update existing docs**
   - Reference new config system
   - Migration guide

---

## Benefits

### ✅ **Centralization**
- Single source of truth for all parameters
- Easy to find and modify
- Version control friendly

### ✅ **Flexibility**
- Named presets for common cases
- Easy to add new configurations
- Simple to experiment

### ✅ **Maintainability**
- Parameters grouped logically
- Type safety with dataclasses
- Validation built-in

### ✅ **Testability**
- Config objects easy to create in tests
- Reproducible layouts (seed)
- Parameter sweep testing

### ✅ **UI Independence**
- Core logic not coupled to GTK
- Can add UI controls later
- Command-line tools possible

---

## Migration Strategy

### Current Code:
```python
# Scattered parameters
postprocessor = PathwayPostProcessor(
    spacing=150.0,
    scale_factor=1.0,
    use_tree_layout=True,
    use_spiral_layout=False
)

# Inside LayoutProcessor
if num_nodes > 20:
    k_factor = 2.0
    scale = 600.0
# ...
```

### New Code:
```python
# Single config object
config = LayoutPresets.auto(num_nodes)  # or .balanced(), .spiral(), etc
postprocessor = PathwayPostProcessor(
    config=config,
    scale_factor=1.0  # Token scaling separate
)

# Clean access
k = self.config.force_directed.k
scale = self.config.force_directed.scale
```

### Backwards Compatibility:
```python
# Add factory method for old API
@classmethod
def from_legacy(cls, spacing, use_tree_layout, use_spiral_layout):
    """Create config from legacy parameters."""
    config = LayoutPresets.balanced()
    config.projection.layer_spacing = spacing
    config.use_spiral = use_spiral_layout
    return config
```

---

## Future Extensions

### Phase 5: Advanced Features (Future)

1. **Compartment-aware clustering**
   ```python
   @dataclass
   class CompartmentConfig:
       enable_clustering: bool = True
       cluster_weight: float = 0.1  # Extra attraction
   ```

2. **Regulation-based forces**
   ```python
   @dataclass
   class RegulationConfig:
       inhibition_repulsion: float = -0.5  # Negative weight
       activation_attraction: float = 0.3   # Extra attraction
   ```

3. **Fixed node positions**
   ```python
   @dataclass
   class ConstraintConfig:
       pin_substrates: bool = True
       substrate_position: Tuple[float, float] = (500, 800)
   ```

4. **Config file support**
   ```python
   config = LayoutConfig.from_json("my_layout.json")
   config.to_yaml("layout_backup.yaml")
   ```

---

## Testing Strategy

### Unit Tests:
```python
def test_config_validation():
    with pytest.raises(ValueError):
        ForceDirectedConfig(k=-1.0)  # Invalid

def test_presets():
    compact = LayoutPresets.compact()
    assert compact.force_directed.k == 1.0
    
def test_auto_selection():
    small = LayoutPresets.auto(5)
    large = LayoutPresets.auto(30)
    assert small.force_directed.scale < large.force_directed.scale
```

### Integration Tests:
```python
def test_layout_with_config():
    config = LayoutPresets.balanced()
    postprocessor = PathwayPostProcessor(config=config)
    result = postprocessor.process(pathway)
    assert len(result.positions) == len(pathway.species)
```

---

## Summary

### Current State:
- ❌ Parameters scattered across files
- ❌ Hardcoded adaptive logic
- ❌ UI-coupled initialization
- ❌ No validation or logging

### Target State:
- ✅ Centralized configuration module
- ✅ Named presets (compact/balanced/spacious)
- ✅ UI-independent defaults
- ✅ Validated and logged
- ✅ Easy to customize and test

### Default Configuration:
```python
# Auto-select based on pathway size
config = LayoutPresets.auto(num_nodes)

# Force-directed physics:
# - k = 1.0-2.0 (adaptive)
# - iterations = 80-120
# - threshold = 1e-6
# - weights = stoichiometry-based

# 2D projection:
# - layer_spacing = 150-250px
# - canvas_width = 1500-2500px
# - layered or spiral
```

---

## Timeline

1. **Phase 1** (Create config): 1-2 hours
2. **Phase 2** (Refactor core): 2-3 hours
3. **Phase 3** (Integration): 1 hour
4. **Phase 4** (Documentation): 1 hour

**Total**: ~6 hours of focused work

---

## Next Steps

1. Start with Phase 1: Create `layout_config.py`
2. Implement dataclasses and presets
3. Add weight calculator
4. Test configuration objects
5. Proceed to Phase 2 refactoring

Ready to begin! 🚀
