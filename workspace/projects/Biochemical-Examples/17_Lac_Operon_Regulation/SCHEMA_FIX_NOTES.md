# Example 17 Fix Summary - Schema Comparison

## Problem
Example 17 (Lac Operon) was not loading in SHYpn due to incorrect file format schema.

## Root Causes

### 1. **Wrong Schema Version**
- **Incorrect**: `"version": "1.0"`
- **Correct**: `"version": "2.0"`

### 2. **ID Format Mismatch**
- **Incorrect**: Integer IDs (`"id": 1, "id": 2`)
- **Correct**: String IDs (`"id": "P1", "id": "T1"`)

### 3. **Missing Required Place Fields**
| Field | Status in Example 17 | Status in Working Models |
|-------|---------------------|-------------------------|
| `object_type` | ❌ Missing | ✅ Required ("place") |
| `radius` | ❌ Missing | ✅ Required (30.0) |
| `marking` | ❌ Missing (used "tokens") | ✅ Required |
| `capacity` | ❌ Missing | ✅ Required ("Infinity") |
| `border_color` | ❌ Missing | ✅ Required ([0, 0, 0]) |
| `border_width` | ❌ Missing | ✅ Required (3.0) |
| `is_catalyst` | ❌ Missing | ✅ Required (true/false) |

### 4. **Missing Required Transition Fields**
| Field | Status in Example 17 | Status in Working Models |
|-------|---------------------|-------------------------|
| `object_type` | ❌ Missing | ✅ Required ("transition") |
| `width` | ❌ Missing | ✅ Required (60.0) |
| `height` | ❌ Missing | ✅ Required (15.0) |
| `horizontal` | ❌ Missing | ✅ Required (true) |
| `enabled` | ❌ Missing | ✅ Required (true) |
| `fill_color` | ❌ Missing | ✅ Required ([0, 0, 0]) |
| `border_color` | ❌ Missing | ✅ Required ([0, 0, 0]) |
| `border_width` | ❌ Missing | ✅ Required (2.0) |
| `transition_type` | ❌ Used "type" | ✅ "transition_type" |
| `priority` | ❌ Missing | ✅ Required (0) |
| `firing_policy` | ❌ Missing | ✅ Required ("race") |
| `is_source` | ❌ Missing | ✅ Required (false) |
| `is_sink` | ❌ Missing | ✅ Required (false) |
| `guard` | ❌ Missing | ✅ Required (1) |
| `rate` | ✅ Had "rate_function" | ✅ Should be "rate" |

### 5. **Missing Required Arc Fields**
| Field | Status in Example 17 | Status in Working Models |
|-------|---------------------|-------------------------|
| `name` | ❌ Missing | ✅ Required (same as id) |
| `object_type` | ❌ Missing | ✅ Required ("arc") |
| `source_type` | ❌ Missing | ✅ Required ("place"/"transition") |
| `target_type` | ❌ Missing | ✅ Required ("place"/"transition") |
| `color` | ❌ Missing | ✅ Required ([0, 0, 0]) |
| `width` | ❌ Missing | ✅ Required (3.0) |
| `control_points` | ❌ Missing | ✅ Required ([]) |

### 6. **Missing Top-Level Sections**
- **Incorrect**: Only had `places`, `transitions`, `arcs`, `simulation`
- **Correct**: Needs `metadata`, `view_state` sections

## Comparison: Before vs After

### Before (Broken Format)
```json
{
  "version": "1.0",
  "metadata": {
    "name": "...",
    "description": "...",
    "author": "..."
  },
  "places": [
    {
      "id": 1,
      "name": "Glucose",
      "tokens": 5.0,
      "initial_marking": 5.0
    }
  ]
}
```

### After (Working Format)
```json
{
  "version": "2.0",
  "metadata": {
    "created": "2025-11-24",
    "object_counts": {
      "places": 12,
      "transitions": 9,
      "arcs": 24
    }
  },
  "view_state": {
    "zoom": 1.0,
    "pan_x": 0.0,
    "pan_y": 0.0
  },
  "places": [
    {
      "id": "P1",
      "name": "Glucose",
      "label": "Glucose\\n5.0 mM",
      "object_type": "place",
      "x": 100.0,
      "y": 100.0,
      "radius": 30.0,
      "marking": 5.0,
      "initial_marking": 5.0,
      "capacity": "Infinity",
      "border_color": [0.0, 0.0, 0.0],
      "border_width": 3.0,
      "is_catalyst": false
    }
  ]
}
```

## Key Lessons

### 1. SHYpn File Format Requirements
- Use **version "2.0"**
- **String IDs** for all objects ("P1", "T1", "A1")
- **Complete metadata** with object counts
- **View state** for zoom/pan settings
- **All visual properties** (colors, widths, sizes)

### 2. Arc Special Cases
| Arc Type | `arc_type` | `color` | `threshold` |
|----------|-----------|---------|-------------|
| Normal | "normal" | [0, 0, 0] | null |
| Test | "test" | [0, 0, 255] (blue) | null or value |
| Inhibitor | "inhibitor" | [255, 0, 0] (red) | numeric value |

### 3. Transition Types
- Must use `"transition_type"` field (not `"type"`)
- Valid values: `"continuous"`, `"stochastic"`, `"timed"`, `"immediate"`
- Rate formula goes in `"rate"` field (not `"rate_function"`)

## Testing Procedure

To verify a model file is correctly formatted:

```python
import sys
sys.path.insert(0, 'src')
import json
from shypn.data.canvas.document_model import DocumentModel

# Load JSON
with open('model.shy', 'r') as f:
    data = json.load(f)

# Try to parse
doc = DocumentModel.from_dict(data)

# Success indicators
assert len(doc.places) > 0
assert len(doc.transitions) > 0
assert all(isinstance(p.id, str) for p in doc.places)
assert all(hasattr(t, 'transition_type') for t in doc.transitions)
```

## Result

✅ Example 17 now loads correctly  
✅ 12 places, 9 transitions, 24 arcs  
✅ Mixed transition types: continuous + stochastic  
✅ Mixed arc types: normal + test + inhibitor  
✅ Ready for simulation

---

**Date Fixed**: November 24, 2025  
**Root Cause**: Incorrect file schema (used abstract format instead of SHYpn v2.0 format)  
**Solution**: Regenerated file using Example 9 (Complete Glycolysis) as template
