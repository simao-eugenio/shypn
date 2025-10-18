# Deprecated Mode System Files

This directory contains archived files from the old explicit mode system that has been replaced with context-aware behavior.

## Why Deprecated

The original system required users to manually switch between "Edit" and "Simulate" modes using a mode palette. This created:
- Workflow friction (constant mode switching)
- Cognitive overhead (remembering current mode)
- Rigid separation (many actions could work in both modes)

## New System

The application now uses **context-aware behavior** based on simulation state:
- No explicit mode switching needed
- System detects what user is doing and adapts automatically
- Simulation state determines what actions are allowed

See: `doc/modes/MODE_ELIMINATION_PLAN.md`

## Files

### mode_events.py
- Original: `src/shypn/events/mode_events.py`
- Contains: `ModeChangedEvent`, `ToolChangedEvent`
- Replaced by: `SimulationState` enum and state detector

### mode_palette_loader.py
- Original: `src/ui/palettes/mode/mode_palette_loader.py`
- Contains: Mode switcher UI with [E] and [S] buttons
- Replaced by: Always-visible simulation controls

## Migration

**Old code**:
```python
if current_mode == 'edit':
    # Edit behavior
elif current_mode == 'simulate':
    # Simulate behavior
```

**New code**:
```python
from shypn.engine.simulation.state import SimulationStateDetector

if state_detector.can_edit_structure():
    # Edit behavior
else:
    # Show restriction message
```

## Timeline

- **Deprecated**: October 18, 2025
- **Archived**: October 18, 2025
- **Planned Removal**: After mode elimination complete (Phase 9)

## Documentation

- Analysis: `doc/modes/MODE_SYSTEM_ANALYSIS.md`
- Implementation: `doc/modes/MODE_ELIMINATION_PLAN.md`
- Critical: `doc/modes/PARAMETER_PERSISTENCE_ANALYSIS.md`
