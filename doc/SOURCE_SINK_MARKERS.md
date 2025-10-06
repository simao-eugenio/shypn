# Source/Sink Transition Markers

## Overview

Source and sink markers are special properties that can be applied to transitions in Petri Net models to indicate external token generation or consumption.

## Feature Description

### Source Transitions
**Visual:** Incoming arrow pointing into the transition from outside
**Meaning:** Generates tokens without requiring input tokens
**Use cases:**
- External arrivals (customers entering a system)
- Job creation (new jobs added to a queue)
- Message generation (external messages arriving)
- Resource replenishment (periodic restocking)

### Sink Transitions
**Visual:** Outgoing arrow pointing out of the transition
**Meaning:** Consumes tokens without producing output tokens
**Use cases:**
- External departures (customers leaving a system)
- Job completion (finished jobs removed)
- Message consumption (messages delivered to external system)
- Resource disposal (expired or discarded resources)

### Combined Source+Sink
A transition can be both source and sink simultaneously, useful for:
- Pass-through nodes
- External exchange points
- Boundary conditions

## Implementation

### Model Properties

**File:** `src/shypn/netobjs/transition.py`

```python
class Transition(PetriNetObject):
    def __init__(self, ...):
        # Source/Sink markers
        self.is_source = False  # Source transition (generates tokens without input)
        self.is_sink = False    # Sink transition (consumes tokens without output)
```

### Persistence

Properties are serialized to JSON:

```json
{
  "type": "transition",
  "id": 1,
  "name": "T1",
  "is_source": true,
  "is_sink": false,
  ...
}
```

**Backward Compatibility:** Old files without these fields default to `False` for both properties.

### User Interface

**Location:** Transition Properties Dialog → Basic Properties Tab

**Controls:**
- ☐ Source (generates tokens) - Checkbox
- ☐ Sink (consumes tokens) - Checkbox

**Tooltips:**
- Source: "Source transition generates tokens without consuming input (models external arrivals)"
- Sink: "Sink transition consumes tokens without producing output (models external departures)"

### Visual Rendering

**File:** `src/shypn/netobjs/transition.py` → `_render_source_sink_markers()`

#### Source Marker (Horizontal Transition)
```
      →|■■■|
       ^
       |
    Source
```
- Arrow points INTO left side of transition
- Arrow length: 20px (zoom-compensated)
- Arrow head: 6px triangle
- Color: Uses transition border color

#### Sink Marker (Horizontal Transition)
```
       |■■■|→
           ^
           |
         Sink
```
- Arrow points OUT OF right side of transition
- Arrow length: 20px (zoom-compensated)
- Arrow head: 6px triangle
- Color: Uses transition border color

#### Vertical Transitions
For vertical transitions, arrows are rotated 90°:
- Source: Arrow points down into top
- Sink: Arrow points down from bottom

## Usage Examples

### Example 1: Manufacturing System

```
[Raw Materials]  ──→  T_Source  →  [Buffer]  →  T_Machine  →  [Finished]  →  T_Sink  ─→  [External]
                      (source)                                                (sink)
```

- **T_Source**: Source transition - models arrival of raw materials from supplier
- **T_Sink**: Sink transition - models shipping of finished goods to customer

### Example 2: Queueing System

```
 T_Arrival (source)  →  [Queue]  →  T_Service  →  T_Departure (sink)
     ↓                                                   ↓
  Customers                                        Served Customers
  arrive                                           leave system
```

- **T_Arrival**: Source - customers arriving from outside
- **T_Departure**: Sink - customers leaving the system

### Example 3: Communication Protocol

```
 T_Generate (source)  →  [Messages]  →  T_Send  →  [Network]  →  T_Receive  →  T_Deliver (sink)
      ↓                                                                              ↓
   New messages                                                                 Delivered
```

## Simulation Behavior

### Source Transitions
When a source transition fires:
1. **Normal behavior**: Consumes input tokens (if any input arcs exist)
2. **Source behavior**: Additionally generates tokens as if from external source
3. Useful for modeling open systems with external input

### Sink Transitions
When a sink transition fires:
1. **Normal behavior**: Produces output tokens (if any output arcs exist)
2. **Sink behavior**: Additionally consumes tokens as if to external sink
3. Useful for modeling open systems with external output

### Implementation Note
The source/sink markers are **visual indicators** and **model documentation**.
The actual simulation behavior depends on the arc connections:
- Transitions with no input arcs naturally act as sources
- Transitions with no output arcs naturally act as sinks
- The markers help clarify the intended model semantics

## Testing

**Test Script:** `test_source_sink.py`

Tests performed:
1. ✅ Source transition serialization
2. ✅ Sink transition serialization
3. ✅ Combined source+sink serialization
4. ✅ Normal transition (no markers)
5. ✅ Backward compatibility (old files)

**Results:** All tests passed ✅

## Files Modified

### Model Layer
- `src/shypn/netobjs/transition.py`
  - Added `is_source` and `is_sink` properties
  - Updated `to_dict()` serialization
  - Updated `from_dict()` deserialization
  - Added `_render_source_sink_markers()` method

### UI Layer
- `ui/dialogs/transition_prop_dialog.ui`
  - Added `is_source_check` checkbox
  - Added `is_sink_check` checkbox
  - Positioned in General Properties frame

- `src/shypn/helpers/transition_prop_dialog_loader.py`
  - Added `_populate_fields()` for checkboxes
  - Added `_apply_changes()` for checkboxes

### Testing
- `test_source_sink.py` (new)
  - Comprehensive serialization tests
  - Backward compatibility tests

## Future Enhancements

Possible future additions:
1. **Validation**: Warn if source has no output arcs
2. **Validation**: Warn if sink has no input arcs
3. **Auto-detection**: Suggest marking transitions with no input/output
4. **Simulation Integration**: Special handling in simulation engine
5. **Analysis**: Include in structural analysis (boundary nodes)
6. **Alternative Visuals**: Configuration for different marker styles
7. **Documentation Export**: Include markers in model documentation

## Related Documentation

- [Transition Properties Dialog](TRANSITION_PROPERTIES_DIALOG.md)
- [Petri Net Object Models](src/shypn/netobjs/README.md)
- [File Format Specification](FILE_FORMAT_SPEC.md)

## Version History

- **October 6, 2025**: Initial implementation
  - Added is_source and is_sink boolean properties
  - Implemented visual arrow markers
  - Added UI controls in properties dialog
  - Full serialization support
  - Backward compatibility maintained

---

**Status:** ✅ Implemented and tested
**Version:** 1.0
**Date:** October 6, 2025
