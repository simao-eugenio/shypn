# Timed Transition Validation

**Transition Type:** Timed  
**Status:** Not Yet Planned  
**Priority:** Phase 2

---

## Overview

This directory will contain validation documentation and test plans for **timed transitions** in SHYpn Petri nets.

**Timed transitions** fire after a deterministic delay when enabled.

---

## Coming Soon

- Benchmark plan with test categories
- Properties specific to timed transitions
- Delay mechanism validation
- Clock-based testing

---

## Timed Transition Characteristics

**Key Properties:**
- `transition_type` = 'timed'
- `rate` - Delay duration (deterministic)
- `guard` - Enable condition
- `priority` - Conflict resolution
- `firing_policy` - 'earliest' or 'latest'

**Behavior:**
- Fires after fixed delay when enabled
- Delay specified by `rate` property
- Multiple timed transitions may compete

---

## Status

🔜 **Planning not yet started**

After completing immediate transition validation, timed transitions will be the next focus.

---

## Related

- [Immediate Transitions](../immediate/) - Current focus
- Main validation framework: [../README.md](../README.md)
