# Layout Parametrization - Implementation Summary

**Date**: October 14, 2025

## Plan Overview

**Goal**: Create centralized, UI-independent configuration system for all force-directed layout parameters.

---

## Architecture

```
┌─────────────────────────────────────┐
│      layout_config.py               │
│  ┌───────────────────────────────┐  │
│  │  ForceDirectedConfig          │  │
│  │  - k, iterations, threshold   │  │
│  │  - scale, seed, weight_mode   │  │
│  └───────────────────────────────┘  │
│  ┌───────────────────────────────┐  │
│  │  ProjectionConfig             │  │
│  │  - layer_threshold, spacing   │  │
│  │  - canvas_width, margins      │  │
│  └───────────────────────────────┘  │
│  ┌───────────────────────────────┐  │
│  │  LayoutConfig                 │  │
│  │  - force_directed             │  │
│  │  - projection                 │  │
│  │  - use_spiral                 │  │
│  └───────────────────────────────┘  │
│  ┌───────────────────────────────┐  │
│  │  LayoutPresets                │  │
│  │  - compact()                  │  │
│  │  - balanced()                 │  │
│  │  - spacious()                 │  │
│  │  - spiral()                   │  │
│  │  - auto(num_nodes)            │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
          ↓
┌─────────────────────────────────────┐
│  pathway_postprocessor.py           │
│  LayoutProcessor(config)            │
└─────────────────────────────────────┘
          ↓
┌─────────────────────────────────────┐
│  layout_projector.py                │
│  LayoutProjector(config.projection) │
└─────────────────────────────────────┘
```

---

## Named Presets

### **Compact** (≤10 nodes)
```python
k=1.0, scale=300px, iterations=80
layer_spacing=150px, canvas=1500px
```

### **Balanced** (11-20 nodes) - DEFAULT
```python
k=1.5, scale=400px, iterations=100
layer_spacing=200px, canvas=2000px
```

### **Spacious** (>20 nodes)
```python
k=2.0, scale=600px, iterations=120
layer_spacing=250px, canvas=2500px
```

### **Auto** (size-adaptive)
```python
LayoutPresets.auto(num_nodes)
→ compact/balanced/spacious
```

---

## Key Features

✅ **Centralized**: Single source of truth  
✅ **Typed**: Dataclasses with validation  
✅ **Presets**: Named configurations ready to use  
✅ **UI-Independent**: No GTK coupling  
✅ **Flexible**: Easy to customize  
✅ **Testable**: Clean objects for tests  

---

## Usage

### Before (Current):
```python
postprocessor = PathwayPostProcessor(
    spacing=150.0,
    use_spiral_layout=False
)
# Parameters scattered and hardcoded
```

### After (Planned):
```python
config = LayoutPresets.auto(num_nodes)
postprocessor = PathwayPostProcessor(config=config)
# Clean, centralized, configurable
```

---

## Implementation Status

| Phase | Task | Status |
|-------|------|--------|
| 1 | Create layout_config.py | 📋 Planned |
| 1 | Define dataclasses | 📋 Planned |
| 1 | Create presets | 📋 Planned |
| 2 | Refactor LayoutProcessor | 📋 Planned |
| 2 | Refactor LayoutProjector | 📋 Planned |
| 3 | Update SBML import | 📋 Planned |
| 3 | Add validation | 📋 Planned |
| 4 | Documentation | 📋 Planned |

---

## Next Steps

1. ✅ **Create** `layout_config.py` with dataclasses
2. ✅ **Implement** presets (compact/balanced/spacious)
3. ✅ **Add** weight calculation strategies
4. 🔄 **Refactor** pathway_postprocessor to use config
5. 🔄 **Refactor** layout_projector to use config
6. 🔄 **Update** SBML import panel
7. 📝 **Document** configuration system

---

## Timeline

- **Phase 1**: Create config module (~2 hours)
- **Phase 2**: Refactor core (~3 hours)
- **Phase 3**: Integration (~1 hour)
- **Phase 4**: Documentation (~1 hour)

**Total**: ~6 hours focused work

---

## Benefits

🎯 **Developer Experience**:
- Easy to find all parameters
- Simple to test different configs
- Clear parameter relationships

🔧 **Maintainability**:
- No more scattered hardcoded values
- Version control friendly
- Type-safe with dataclasses

🚀 **Future Ready**:
- Easy to add UI controls later
- Can support config files (JSON/YAML)
- Command-line tool possible

---

**See full plan**: `doc/layout/LAYOUT_PARAMETRIZATION_PLAN.md`
