# Tools Directory

Utility tools for programmatic interaction with SHYpn models.

## Overview

This directory contains Python tools for **model-independent** parameter editing, model comparison, and automated batch operations on .shy model files.

## Tools

### 1. **update_model_parameters.py** ⭐ MODEL-INDEPENDENT
**Purpose:** DTO-based model parameter editor that works with ANY .shy model file

**Features:**
- ✅ Model-independent: Uses universal DTO properties (Transition.rate_function, Place.initial_marking)
- ✅ Type-safe: Respects Transition/Place data class structure with validation
- ✅ Automatic cache invalidation: Emits EventBus events on save
- ✅ Dual-location updates: Handles backward compatibility (top-level + properties dict)
- ✅ Backup creation: Automatic timestamped backups before editing

**Core Class: `ModelParameterEditor`**
```python
from tools.update_model_parameters import ModelParameterEditor

# Works with ANY model type
editor = ModelParameterEditor('workspace/projects/your_model/model.shy')

# Update transition rates (uses Transition.rate_function property)
editor.update_transition_rate_function(
    transition_name='My_Transition',
    rate_function='0.5 * substrate * enzyme'
)

# Update place initial markings (uses Place.initial_marking property)
editor.update_place_initial_marking(
    place_name='ATP',
    initial_marking=3000.0
)

# Save with automatic backup and EventBus notification
editor.save(backup=True)
```

**Model Independence:**
The editor works identically for ALL model types:
- ✅ Glycolysis models
- ✅ MAPK cascades
- ✅ Gene regulatory networks
- ✅ Signal transduction pathways
- ✅ GATA1/PU.1 lineage commitment
- ✅ ANY custom .shy model

**Architecture:**
- **Layer 1:** Universal DTOs (Transition, Place) - built into SHYpn
- **Layer 2:** ModelParameterEditor - 100% model-independent tool
- **Layer 3:** Model-specific convenience wrappers (optional)

**Example: Model-Specific Wrapper**
```python
def apply_gata_fixes():
    """GATA1/PU.1 specific convenience wrapper"""
    editor = ModelParameterEditor('workspace/projects/gata/models/phase3a.shy')
    
    # Energy metabolism fixes
    editor.update_transition_rate_function('ATP_synthesis',
        '10000 * ADP / (ADP + 0.5) * 0.1 / (0.1 + ADP)')
    editor.update_transition_rate_function('GTP_regeneration', '500')
    
    # Transcription/degradation fixes
    editor.update_transition_rate_function('GATA1_transcription',
        '0.08 * GATA1_gene * EPO * GATA1_Protein_nuc / ...')
    
    editor.save()
```

**Documentation:**
- [PROGRAMMATIC_MODEL_EDITING.md](../doc/PROGRAMMATIC_MODEL_EDITING.md) - Complete guide
- [MODEL_INDEPENDENCE.md](../doc/MODEL_INDEPENDENCE.md) - Architecture explanation
- [EVENT_DRIVEN_CACHE_INVALIDATION.md](../doc/EVENT_DRIVEN_CACHE_INVALIDATION.md) - Cache system

**Usage:**
```bash
# Custom editing (model-independent)
python tools/update_model_parameters.py

# GATA-specific convenience wrapper
python tools/update_model_parameters.py gata
```

---

### 2. **compare_editing_approaches.py**
**Purpose:** Educational demonstration comparing direct JSON vs DTO-based editing

**Features:**
- Side-by-side comparison of editing approaches
- Feature comparison table (type safety, validation, events, cache invalidation)
- Shows why DTO-based editing is superior

**Usage:**
```bash
python tools/compare_editing_approaches.py
```

**Output:**
- Comparison of direct JSON manipulation vs DTO property access
- Feature matrix showing advantages of DTO approach
- Code examples for both methods

---

### 3. **demo_metadata_system.py**
**Purpose:** Demonstrates metadata tracking system

**Features:**
- Model creation timestamp tracking
- Author/version metadata
- Simulation parameter history

**Usage:**
```bash
python tools/demo_metadata_system.py
```

---

## Best Practices

### ✅ DO:
1. **Use `ModelParameterEditor`** for programmatic model editing
2. **Create model-specific wrappers** for repeated parameter sets (like `apply_gata_fixes()`)
3. **Enable backups** when editing important models (`backup=True`)
4. **Use DTO properties** (rate_function, initial_marking) for type-safe access
5. **Rely on automatic EventBus emission** for cache invalidation

### ❌ DON'T:
1. **Don't manipulate JSON directly** - bypasses validation and events
2. **Don't skip backups** for production models
3. **Don't assume transition names** - check your model first
4. **Don't forget** that the editor is model-independent (same API for all models)

---

## Architecture

### Why DTO-Based Editing?

**Problem with Direct JSON:**
```python
# ❌ WRONG: Direct JSON manipulation
with open('model.shy', 'r') as f:
    data = json.load(f)
data['transitions'][0]['rate_function'] = '0.5'  # No validation!
# Missing: Dual-location update, type checking, EventBus emission
```

**Solution with DTOs:**
```python
# ✅ CORRECT: DTO-based editing
editor = ModelParameterEditor('model.shy')
editor.update_transition_rate_function('T1', '0.5')
# Automatic: Validation, dual-location, EventBus, cache invalidation
editor.save()
```

### Benefits:
1. **Type Safety:** Property setters validate inputs
2. **Dual-Location Updates:** Handles backward compatibility automatically
3. **EventBus Notification:** Triggers cache invalidation in GUI
4. **Model Independence:** Same API for all .shy models

---

## Directory Contents

```
tools/
├── README.md                          # This file
├── update_model_parameters.py         # ⭐ Model-independent DTO-based editor
├── compare_editing_approaches.py      # Educational: JSON vs DTO comparison
└── demo_metadata_system.py            # Metadata tracking demonstration
```

---

## Related Documentation

📚 **[PROGRAMMATIC_MODEL_EDITING.md](../doc/PROGRAMMATIC_MODEL_EDITING.md)** - Complete editing guide  
📚 **[MODEL_INDEPENDENCE.md](../doc/MODEL_INDEPENDENCE.md)** - Architecture layers  
📚 **[EVENT_DRIVEN_CACHE_INVALIDATION.md](../doc/EVENT_DRIVEN_CACHE_INVALIDATION.md)** - Cache system  
📚 **[GATA_PU1_MECHANISTIC_ANALYSIS.md](../doc/GATA_PU1_MECHANISTIC_ANALYSIS.md)** - Use case example

---

## Examples

### Example 1: Glycolysis Model
```python
editor = ModelParameterEditor('workspace/glycolysis/model.shy')
editor.update_transition_rate_function('Hexokinase', 'Vmax * Glucose / (Km + Glucose)')
editor.update_place_initial_marking('ATP', 5000.0)
editor.save()
```

### Example 2: MAPK Cascade
```python
editor = ModelParameterEditor('workspace/mapk/cascade.shy')
editor.update_transition_rate_function('MEK_phosphorylation', 'k1 * RAF * MEK')
editor.update_transition_rate_function('MEK_dephosphorylation', 'k2 * MKP * pMEK')
editor.save()
```

### Example 3: Gene Network
```python
editor = ModelParameterEditor('workspace/gene_network/network.shy')
editor.update_transition_rate_function('gene_transcription', '0.1 * promoter_activity')
editor.update_transition_rate_function('mRNA_degradation', '0.05 * mRNA')
editor.save()
```

---

## Support

**Questions?** See [PROGRAMMATIC_MODEL_EDITING.md](../doc/PROGRAMMATIC_MODEL_EDITING.md)  
**Architecture?** See [MODEL_INDEPENDENCE.md](../doc/MODEL_INDEPENDENCE.md)  
**Issues?** Check [EVENT_DRIVEN_CACHE_INVALIDATION.md](../doc/EVENT_DRIVEN_CACHE_INVALIDATION.md)

**Contact:** Eugênio Simão (eugenio.simao@ufsc.br)
