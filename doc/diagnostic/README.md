# Diagnostic System Documentation

This directory contains comprehensive documentation for Shypn's diagnostic and locality analysis system.

## Quick Start

| Document | Purpose |
|----------|---------|
| **[DIAGNOSTIC_UPDATE_SUMMARY.md](DIAGNOSTIC_UPDATE_SUMMARY.md)** | ⭐ **START HERE** - Latest update summary with transition default change |
| **[DIAGNOSTIC_FLOW_COMPLETE.md](DIAGNOSTIC_FLOW_COMPLETE.md)** | ⭐ **MAIN REFERENCE** - Complete diagnostic flow (500+ lines) |
| **[DIAGNOSTIC_QUICK_REFERENCE.md](DIAGNOSTIC_QUICK_REFERENCE.md)** | Quick reference card |
| **[REAL_TIME_DIAGNOSTICS_PANEL.md](REAL_TIME_DIAGNOSTICS_PANEL.md)** | Real-time panel usage guide |

## Documentation Index

### Core Diagnostic System

**Property Dialogs & Flow**:
- `DIAGNOSTIC_FLOW_COMPLETE.md` - Complete diagnostic flow reference (500+ lines)
  - Part 1: NetObject Property Dialogs (Place, Transition, Arc)
  - Part 2: Real-Time Diagnostic Panel
  - Part 3: Data Flow Integration
  - Part 4: Default Values Summary
  - Part 5: Diagnostic Features by Object Type
  - Part 6: Testing Checklist
  - Part 7: Files Summary

- `DIAGNOSTIC_UPDATE_SUMMARY.md` - Latest updates (October 12, 2025)
  - Transition default changed to **continuous** ⭐
  - Quick reference updated
  - Complete diagnostic documentation

**Quick References**:
- `DIAGNOSTIC_QUICK_REFERENCE.md` - Quick reference card
- `DIAGNOSTIC_INDEX.md` - Diagnostic system index
- `DIAGNOSTIC_SUMMARY.md` - System summary

**Specialized Topics**:
- `DIAGNOSTIC_PATH_REVIEW.md` - Path analysis review
- `DIAGNOSTIC_VISUALIZATION.md` - Visualization features
- `DIAGNOSTIC_WORK_SUMMARY.md` - Work summary

### Locality Analysis System

**Executive Summaries**:
- `LOCALITY_ANALYSIS_EXECUTIVE_SUMMARY.md` - High-level overview
- `LOCALITY_FINAL_SUMMARY_REVISED.md` - Final summary (revised)
- `LOCALITY_QUICK_REFERENCE.md` - Quick reference

**Implementation**:
- `LOCALITY_BASED_ANALYSIS_IMPLEMENTATION_COMPLETE.md` - Implementation complete
- `LOCALITY_IMPLEMENTATION_PLAN_REVISED.md` - Implementation plan (revised)
- `LOCALITY_BASED_PLOTTING_PLAN.md` - Plotting integration plan
- `LOCALITY_PLOTTING_SUMMARY.md` - Plotting summary

**Technical Details**:
- `LOCALITY_DETECTOR_FIX.md` - Detector bug fixes
- `LOCALITY_FEEDBACK_IMPROVEMENTS.md` - Feedback system improvements
- `LOCALITY_PARALLEL_PROCESSING_ANALYSIS.md` - Parallel processing analysis
- `LOCALITY_CONCERNS_CLARIFICATION.md` - Clarifications on concerns
- `LOCALITY_DIAGNOSTIC_COMPARISON.md` - Diagnostic comparison

### Real-Time Diagnostics

**Runtime Analysis**:
- `REAL_TIME_DIAGNOSTICS_PANEL.md` - Real-time panel guide
- `RUNTIME_DIAGNOSTICS_COMPLETE.md` - Runtime diagnostics implementation
- `AUTO_TRACKING_DIAGNOSTICS.md` - Automatic tracking system

## Architecture Overview

```
NetObject Property Dialogs (Static)
         ↓
    NetObjects (Model)
         ↓
  Simulation Engine
         ↓
  Data Collector
         ↓
Diagnostic Panel (Real-time)
```

### Three Analysis Layers

1. **LocalityDetector**: Structure detection (P-T-P pattern)
2. **LocalityAnalyzer**: Static analysis (tokens, weights, balance)
3. **LocalityRuntimeAnalyzer**: Runtime metrics (firings, throughput, enablement)

## Key Features

### Property Dialogs (Static Configuration)
- **Place Properties**: tokens, initial_marking, capacity, etc.
- **Transition Properties**: type (default: continuous ⭐), rate_function, guards
- **Arc Properties**: arc_type, weight, threshold

### Diagnostic Panel (Dynamic Monitoring)
- Real-time locality structure display
- Runtime metrics (firings, throughput)
- Enablement analysis with reasons
- Recent events log
- Updates every 500ms during simulation

## Default Values (Updated October 12, 2025)

| Object | Property | Default | Changed |
|--------|----------|---------|---------|
| Transition | transition_type | **'continuous'** | ⭐ YES |
| Place | initial_marking | 0 | No |
| Place | capacity | -1 (unlimited) | No |
| Arc | weight | 1 | No |
| Arc | arc_type | 'normal' | No |

## Testing Checklist

See `DIAGNOSTIC_FLOW_COMPLETE.md` Part 6 for complete testing procedures:
- [ ] Property dialog flow test
- [ ] Diagnostic panel flow test
- [ ] Integration flow test
- [ ] Source/sink diagnostics test

## Related Documentation

**Transition Behaviors**:
- `../behaviors/TRANSITION_BEHAVIORS_SUMMARY.md`
- `../behaviors/QUICK_REFERENCE.md`
- `../TRANSITION_TYPE_DEFAULT_CONTINUOUS.md`

**Simulation**:
- `../SIMULATION_QUICK_REFERENCE.md`
- `../MATPLOTLIB_PLOT_ANALYSIS.md`

**Architecture**:
- `../ARCHITECTURE_CONFIRMATION.md`
- `../MODEL_CANVAS_ARCHITECTURE.md`

## Code Locations

### Property Dialogs
```
src/shypn/helpers/
├── place_prop_dialog_loader.py
├── transition_prop_dialog_loader.py
└── arc_prop_dialog_loader.py
```

### Diagnostic System
```
src/shypn/diagnostic/
├── locality_detector.py
├── locality_analyzer.py
├── locality_runtime.py
└── locality_info_widget.py
```

### Analysis Panels
```
src/shypn/analyses/
├── diagnostics_panel.py
├── plot_panel.py
└── transition_rate_panel.py
```

## Development History

- **October 12, 2025**: Transition default changed to continuous, comprehensive documentation created
- **Earlier**: Locality analysis system, runtime diagnostics, real-time panel implementation

---

**Last Updated**: October 12, 2025  
**Status**: ✅ Complete and current  
**Maintainer**: Shypn Development Team
