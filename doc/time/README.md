# Time and Simulation Documentation

This directory contains all documentation related to time management, simulation timing, and time-related features in Shypn.

## Quick Navigation

### 🎯 Quick Reference
- **[TIME_COMPUTATION_QUICK_REF.md](TIME_COMPUTATION_QUICK_REF.md)** - Quick reference for time computation
- **[TIME_SCALE_QUICK_REFERENCE.md](TIME_SCALE_QUICK_REFERENCE.md)** - Quick reference for time scale feature

### 📊 Analysis & Design
- **[SIMULATION_TIME_SCALING_ANALYSIS.md](SIMULATION_TIME_SCALING_ANALYSIS.md)** - ⭐ **NEW** - How to watch a 2-hour process in 1 second
- **[REAL_WORLD_TIME_PLAYBACK_ANALYSIS.md](REAL_WORLD_TIME_PLAYBACK_ANALYSIS.md)** - Real-world time playback analysis
- **[TIME_ABSTRACTIONS_IN_SIMULATION.md](TIME_ABSTRACTIONS_IN_SIMULATION.md)** - Time abstractions and concepts
- **[TIME_ABSTRACTION_CODE_ANALYSIS.md](TIME_ABSTRACTION_CODE_ANALYSIS.md)** - Code-level time abstraction analysis
- **[TIME_SETTINGS_UI_DESIGN.md](TIME_SETTINGS_UI_DESIGN.md)** - UI design for time settings

### 📋 Implementation Summaries
- **[TIME_COMPUTATION_FINAL_SUMMARY.md](TIME_COMPUTATION_FINAL_SUMMARY.md)** - Final summary of time computation work
- **[TIME_COMPUTATION_EXECUTIVE_SUMMARY.md](TIME_COMPUTATION_EXECUTIVE_SUMMARY.md)** - Executive summary
- **[TIME_COMPUTATION_FINAL_STATUS.md](TIME_COMPUTATION_FINAL_STATUS.md)** - Final status report
- **[TIME_SCALE_FINAL_SUMMARY.md](TIME_SCALE_FINAL_SUMMARY.md)** - Time scale feature final summary
- **[SIMULATION_TIMING_IMPLEMENTATION_SUMMARY.md](SIMULATION_TIMING_IMPLEMENTATION_SUMMARY.md)** - Implementation summary
- **[SIMULATION_TIMING_FINAL_CHECKLIST.md](SIMULATION_TIMING_FINAL_CHECKLIST.md)** - Final checklist

### 🔧 Session Reports & Progress
- **[TIME_COMPUTATION_SESSION2_COMPLETE.md](TIME_COMPUTATION_SESSION2_COMPLETE.md)** - Session 2 completion report
- **[TIME_COMPUTATION_PROGRESS_REPORT.md](TIME_COMPUTATION_PROGRESS_REPORT.md)** - Progress tracking
- **[TIME_SCALE_PHASE1_COMPLETE.md](TIME_SCALE_PHASE1_COMPLETE.md)** - Phase 1 completion
- **[SESSION_SUMMARY_2025_10_08_EVENING.md](SESSION_SUMMARY_2025_10_08_EVENING.md)** - Evening session summary

### 🧪 Testing & Analysis
- **[TIME_COMPUTATION_TEST_RESULTS.md](TIME_COMPUTATION_TEST_RESULTS.md)** - Test results
- **[TIME_COMPUTATION_ANALYSIS_AND_TEST_PLAN.md](TIME_COMPUTATION_ANALYSIS_AND_TEST_PLAN.md)** - Analysis and test plan
- **[ANALYSIS_SUMMARY.md](ANALYSIS_SUMMARY.md)** - General analysis summary

### 🐛 Bug Fixes
- **[TIMED_TRANSITION_REENABLEMENT_FIX.md](TIMED_TRANSITION_REENABLEMENT_FIX.md)** - Timed transition re-enablement fix
- **[TIMED_TRANSITION_RUN_STOP_FIX.md](TIMED_TRANSITION_RUN_STOP_FIX.md)** - Run/stop behavior fix
- **[TIMED_TRANSITION_RATE_PROPERTY_FIX.md](TIMED_TRANSITION_RATE_PROPERTY_FIX.md)** - Rate property fix
- **[TIMED_TRANSITION_FLOATING_POINT_FIX.md](TIMED_TRANSITION_FLOATING_POINT_FIX.md)** - Floating point precision fix
- **[TIMED_SINK_DEBUG.md](TIMED_SINK_DEBUG.md)** - Timed sink debugging
- **[SIMULATION_DISPLAY_TIMESCALE_ISSUE.md](SIMULATION_DISPLAY_TIMESCALE_ISSUE.md)** - Display timescale issue
- **[BUGFIX_WINDOW_CROSSING.md](BUGFIX_WINDOW_CROSSING.md)** - Window crossing bug fix

### 📖 Explanations & Guides
- **[TIMED_TRANSITION_BEHAVIOR_EXPLAINED.md](TIMED_TRANSITION_BEHAVIOR_EXPLAINED.md)** - How timed transitions work
- **[TIME_PLAYBACK_VISUAL_GUIDE.md](TIME_PLAYBACK_VISUAL_GUIDE.md)** - Visual guide to time playback

### 🎨 UI & Requirements
- **[UI_REQUIREMENTS_TIME_SCALE.md](UI_REQUIREMENTS_TIME_SCALE.md)** - UI requirements for time scale
- **[SIMULATION_PALETTE_REFINEMENTS.md](SIMULATION_PALETTE_REFINEMENTS.md)** - Simulation palette refinements
- **[SIMULATION_PALETTE_REFINEMENTS_SUMMARY.md](SIMULATION_PALETTE_REFINEMENTS_SUMMARY.md)** - Refinements summary
- **[SETTINGS_SUB_PALETTE_REFACTORING_PLAN.md](SETTINGS_SUB_PALETTE_REFACTORING_PLAN.md)** - Settings refactoring plan

---

## Key Concepts

### Time Scale
**Time scale** controls the playback speed of simulation visualization:
- `time_scale = model_seconds / real_seconds`
- Example: `time_scale=60` means 60 seconds of model time per 1 second of wall-clock time
- Allows watching slow processes quickly or fast processes slowly
- See: [SIMULATION_TIME_SCALING_ANALYSIS.md](SIMULATION_TIME_SCALING_ANALYSIS.md)

### Time Units
Model time can be expressed in different units:
- Seconds, minutes, hours, days, etc.
- Internally converted to seconds for computation
- UI displays in user-selected units

### Time Step (dt)
- Integration step size for continuous transitions
- Can be auto-calculated (duration/1000) or manual
- Affects accuracy and performance
- See: [TIME_COMPUTATION_QUICK_REF.md](TIME_COMPUTATION_QUICK_REF.md)

### Timed Transitions
Transitions that fire after a specific time delay:
- Fixed delay: `delay=5.0` (fires 5 seconds after enabled)
- Window: `[earliest, latest]` timing constraints
- Re-enablement behavior: clock resets on each enablement
- See: [TIMED_TRANSITION_BEHAVIOR_EXPLAINED.md](TIMED_TRANSITION_BEHAVIOR_EXPLAINED.md)

### Continuous Transitions
Transitions with continuous token flow:
- Rate function: `r(t)` defines flow rate
- Integration: RK4 (Runge-Kutta 4th order) method
- Smooth evolution without discrete jumps
- Default for SBML import (as of Oct 2025)

---

## Recent Updates (October 2025)

### New Features
✅ **SBML Import**: Default to continuous transitions (better for biochemical pathways)  
✅ **Time Scaling Analysis**: Comprehensive guide to watching processes at any speed  

### Documentation Organization
📁 All time-related docs now in `doc/time/` for better organization

### Related Documentation
- **SBML Import**: `../SBML_DEFAULT_CONTINUOUS_TRANSITIONS.md`
- **Coordinate Fixes**: `../SBML_TREE_LAYOUT_REVERT.md`

---

## Getting Started

### For Users
1. Start with: [SIMULATION_TIME_SCALING_ANALYSIS.md](SIMULATION_TIME_SCALING_ANALYSIS.md)
2. Quick reference: [TIME_SCALE_QUICK_REFERENCE.md](TIME_SCALE_QUICK_REFERENCE.md)
3. Timed transitions: [TIMED_TRANSITION_BEHAVIOR_EXPLAINED.md](TIMED_TRANSITION_BEHAVIOR_EXPLAINED.md)

### For Developers
1. Code analysis: [TIME_ABSTRACTION_CODE_ANALYSIS.md](TIME_ABSTRACTION_CODE_ANALYSIS.md)
2. Implementation: [SIMULATION_TIMING_IMPLEMENTATION_SUMMARY.md](SIMULATION_TIMING_IMPLEMENTATION_SUMMARY.md)
3. Testing: [TIME_COMPUTATION_TEST_RESULTS.md](TIME_COMPUTATION_TEST_RESULTS.md)

### For Bug Fixing
1. Check: Bug fix documentation (see list above)
2. Reference: [TIME_COMPUTATION_QUICK_REF.md](TIME_COMPUTATION_QUICK_REF.md)
3. Tests: [TIME_COMPUTATION_ANALYSIS_AND_TEST_PLAN.md](TIME_COMPUTATION_ANALYSIS_AND_TEST_PLAN.md)

---

## File Organization

```
doc/time/
├── README.md (this file)
│
├── Quick References (2 files)
│   ├── TIME_COMPUTATION_QUICK_REF.md
│   └── TIME_SCALE_QUICK_REFERENCE.md
│
├── Analysis & Design (5 files)
│   ├── SIMULATION_TIME_SCALING_ANALYSIS.md ⭐ NEW
│   ├── REAL_WORLD_TIME_PLAYBACK_ANALYSIS.md
│   ├── TIME_ABSTRACTIONS_IN_SIMULATION.md
│   ├── TIME_ABSTRACTION_CODE_ANALYSIS.md
│   └── TIME_SETTINGS_UI_DESIGN.md
│
├── Implementation Summaries (6 files)
│   ├── TIME_COMPUTATION_FINAL_SUMMARY.md
│   ├── TIME_COMPUTATION_EXECUTIVE_SUMMARY.md
│   ├── TIME_COMPUTATION_FINAL_STATUS.md
│   ├── TIME_SCALE_FINAL_SUMMARY.md
│   ├── SIMULATION_TIMING_IMPLEMENTATION_SUMMARY.md
│   └── SIMULATION_TIMING_FINAL_CHECKLIST.md
│
├── Session Reports (4 files)
│   ├── TIME_COMPUTATION_SESSION2_COMPLETE.md
│   ├── TIME_COMPUTATION_PROGRESS_REPORT.md
│   ├── TIME_SCALE_PHASE1_COMPLETE.md
│   └── SESSION_SUMMARY_2025_10_08_EVENING.md
│
├── Testing (3 files)
│   ├── TIME_COMPUTATION_TEST_RESULTS.md
│   ├── TIME_COMPUTATION_ANALYSIS_AND_TEST_PLAN.md
│   └── ANALYSIS_SUMMARY.md
│
├── Bug Fixes (7 files)
│   ├── TIMED_TRANSITION_REENABLEMENT_FIX.md
│   ├── TIMED_TRANSITION_RUN_STOP_FIX.md
│   ├── TIMED_TRANSITION_RATE_PROPERTY_FIX.md
│   ├── TIMED_TRANSITION_FLOATING_POINT_FIX.md
│   ├── TIMED_SINK_DEBUG.md
│   ├── SIMULATION_DISPLAY_TIMESCALE_ISSUE.md
│   └── BUGFIX_WINDOW_CROSSING.md
│
├── Explanations (2 files)
│   ├── TIMED_TRANSITION_BEHAVIOR_EXPLAINED.md
│   └── TIME_PLAYBACK_VISUAL_GUIDE.md
│
└── UI & Requirements (4 files)
    ├── UI_REQUIREMENTS_TIME_SCALE.md
    ├── SIMULATION_PALETTE_REFINEMENTS.md
    ├── SIMULATION_PALETTE_REFINEMENTS_SUMMARY.md
    └── SETTINGS_SUB_PALETTE_REFACTORING_PLAN.md
```

**Total**: 33 documentation files organized by category

---

Last updated: October 12, 2025
