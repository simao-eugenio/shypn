# Petri Net Object Models

This directory contains the core object models for Petri Net elements. All objects inherit from a common base class and support rendering, serialization, and property editing.

## Base Class

### `petri_net_object.py`
**Base Petri Net Object**

Abstract base class for all Petri Net objects:
- Unique ID generation
- Position (x, y coordinates)
- Selection state
- Color and rendering properties
- Serialization interface (to_dict/from_dict)
- Drawing interface (draw method with Cairo)
- Bounding box calculations
- Hit testing for selection

## Node Types

### `place.py`
**Place Nodes**

Represents place nodes in the Petri Net:
- **Tokens**: Current marking (number of tokens)
- **Initial Marking**: Baseline marking for simulation reset
- **Capacity**: Optional maximum token limit
- **Name and Label**: Identification and display text
- **Rendering**: Circle with token dots or numeric display
- **Properties Dialog**: Edit via `place_prop_dialog_loader.py`

**Token Persistence:**
- Both `tokens` and `initial_marking` are saved/loaded
- Properties dialog updates both when user edits tokens
- Ensures user's manual token inputs persist as simulation baseline

**Rendering Modes:**
- Dots for small token counts (≤ 5)
- Numeric display for larger counts
- Capacity indicator when set

### `transition.py`
**Transition Nodes**

Represents transition nodes in the Petri Net:
- **Type**: Immediate, Timed, Stochastic, or Continuous
- **Priority**: For immediate transitions (higher = fires first)
- **Delay**: Deterministic delay for timed transitions
- **Rate Function**: Stochastic rate or continuous flow rate
- **Name and Label**: Identification and display text
- **Rendering**: Rectangle with type-specific styling
- **Properties Dialog**: Edit via `transition_prop_dialog_loader.py`

**Transition Types:**
1. **Immediate**: Fires instantly when enabled (priority-based)
2. **Timed**: Fires after fixed delay
3. **Stochastic**: Fires after exponentially distributed delay
4. **Continuous**: Continuous firing with rate function

**Rendering Styles:**
- Immediate: Thin rectangle (black)
- Timed: Thick rectangle (blue)
- Stochastic: Thick rectangle (green)
- Continuous: Double-bordered rectangle (red)

## Arc Types

### `arc.py`
**Normal Arcs**

Standard directed arcs connecting places and transitions:
- **Weight**: Number of tokens consumed/produced
- **Multiplicity**: Visual representation of weight
- **Direction**: Place → Transition or Transition → Place
- **Rendering**: Line with arrow, weight label
- **Properties Dialog**: Edit via `arc_prop_dialog_loader.py`

**Behavior:**
- Place → Transition: Consumes tokens (enables transition)
- Transition → Place: Produces tokens (fires transition)

### `inhibitor_arc.py`
**Inhibitor Arcs**

Inhibitor arcs that test without consuming:
- **Weight**: Inhibition threshold
- **Direction**: Place → Transition only
- **Rendering**: Line with circle endpoint
- **Behavior**: Disables transition when place has ≥ weight tokens

**Use Case:** Modeling mutual exclusion and resource conflicts

### `curved_arc.py`
**Curved Normal Arcs**

Normal arcs with Bézier curve rendering:
- All features of normal arcs
- **Control Points**: Define curve shape
- **Rendering**: Smooth Bézier curve with arrow
- **Interaction**: Draggable control points for curve adjustment

**Use Case:** Avoiding visual clutter when multiple arcs exist between same objects

### `curved_inhibitor_arc.py`
**Curved Inhibitor Arcs**

Inhibitor arcs with Bézier curve rendering:
- All features of inhibitor arcs
- **Control Points**: Define curve shape
- **Rendering**: Smooth Bézier curve with circle endpoint
- **Interaction**: Draggable control points for curve adjustment

## Common Features

All Petri Net objects support:

### Serialization
```python
# Save to dictionary
data = obj.to_dict()

# Load from dictionary
obj = ObjectClass.from_dict(data)
```

### Rendering
```python
# Draw on Cairo context
obj.draw(cr, zoom_level, is_selected=False, is_highlighted=False)
```

### Selection
```python
# Check if point is inside object
if obj.contains_point(x, y):
    obj.selected = True
```

### Properties
```python
# Get/set common properties
obj.name = "P1"
obj.color = (1.0, 0.0, 0.0, 1.0)  # RGBA
obj.position = (100, 100)
```

## Object Lifecycle

1. **Creation**: User selects tool and clicks canvas
2. **Editing**: Properties dialog for detailed configuration
3. **Connection**: Arcs connect places and transitions
4. **Simulation**: Engine modifies token markings
5. **Persistence**: Save/load via JSON serialization

## Import Patterns

```python
from shypn.netobjs.place import Place
from shypn.netobjs.transition import Transition
from shypn.netobjs.arc import Arc
from shypn.netobjs.inhibitor_arc import InhibitorArc
from shypn.netobjs.curved_arc import CurvedArc
from shypn.netobjs.curved_inhibitor_arc import CurvedInhibitorArc
from shypn.netobjs.petri_net_object import PetriNetObject
```

## File Format Example

```json
{
  "places": [
    {
      "id": "place_001",
      "name": "P1",
      "x": 100,
      "y": 100,
      "marking": 5,
      "initial_marking": 5,
      "capacity": null,
      "color": [1.0, 0.0, 0.0, 1.0]
    }
  ],
  "transitions": [
    {
      "id": "trans_001",
      "name": "T1",
      "x": 200,
      "y": 100,
      "type": "immediate",
      "priority": 1,
      "color": [0.0, 0.0, 0.0, 1.0]
    }
  ],
  "arcs": [
    {
      "id": "arc_001",
      "source": "place_001",
      "target": "trans_001",
      "weight": 1,
      "type": "normal"
    }
  ]
}
```
