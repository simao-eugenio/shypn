# Topology System - Visual Roadmap

**Date**: October 19, 2025

---

## 🗺️ Project Timeline

```
Phases 1-4 COMPLETE ✅           Current Phase ⏳              Future Phases 🔮
├─────────────────────┤├──────────────────────┤├──────────────────────────────┤
│                     ││                      ││                              │
│ ✅ Base Classes     ││ Phase 5: Static      ││ Phase 6: Highlighting        │
│ ✅ 4 Analyzers      ││ Analyzers (3 weeks)  ││ (1 week)                     │
│ ✅ UI Architecture  ││                      ││                              │
│ ✅ 46 Tests Passing ││ 8 more analyzers     ││ Visual feedback on canvas    │
│                     ││                      ││                              │
└─────────────────────┘└──────────────────────┘│                              │
                                               │ Phase 7: Runtime Panel       │
Oct 15-19, 2025         Oct 19 - Nov 9         │ (2 weeks)                    │
                                               │                              │
                                               │ Phase 8: Topology Palette    │
                                               │ (3 weeks)                    │
                                               │                              │
                                               └──────────────────────────────┘
                                               Nov 9 - Dec 28, 2025
```

---

## 📊 Component Development Timeline

```
Component                 Week 1  Week 2  Week 3  Week 4  Week 5  Week 6  Week 7-9
─────────────────────────────────────────────────────────────────────────────────
Static Analyzers (A)      ████    ████    ████    
  T-Invariants            ██
  Siphons                 ████
  Traps                   ██
  DAG Analysis                    ██
  Centrality                      ████
  Communities                     ████
  Clustering                              ██

Property Dialogs          ████    ████    ████
  UI Polish                                 ██
  Testing                                   ██

Highlighting Infrastructure               ████
  HighlightingManager                     ████
  Integration                             ██

Dynamic Analyzers (B)                             ████    ████
  Reachability                                    ████
  Boundedness                                     ████
  Liveness                                                ████
  Deadlock Detection                                      ████

Runtime Dynamics Panel                            ████    ████
  Panel Creation                                  ██
  Integration                                     ████

Topology Tools Palette                                            ████  ████  ██
  UI Design                                                       ██
  Implementation                                                  ████  ████
  Integration                                                                 ██

Documentation             ██      ██      ██      ██      ██      ██    ██    ██
```

---

## 🏗️ Architecture Layers

```
┌────────────────────────────────────────────────────────────────────┐
│                        USER INTERFACE                              │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌──────────────────┐  ┌─────────────────┐  ┌──────────────────┐  │
│  │ Property Dialogs │  │ Runtime Panel   │  │ Topology Palette │  │
│  │                  │  │                 │  │                  │  │
│  │ ┌──────────────┐ │  │ ┌─────────────┐ │  │ ┌──────────────┐ │  │
│  │ │ Topology Tab │ │  │ │ Runtime Tab │ │  │ │ Global Tools │ │  │
│  │ │              │ │  │ │             │ │  │ │              │ │  │
│  │ │ Static Props │ │  │ │ Dynamic     │ │  │ │ All 20 Tools │ │  │
│  │ │ + Highlight  │ │  │ │ Properties  │ │  │ │ + Actions    │ │  │
│  │ └──────────────┘ │  │ └─────────────┘ │  │ └──────────────┘ │  │
│  └──────────────────┘  └─────────────────┘  └──────────────────┘  │
│           │                     │                      │           │
└───────────┼─────────────────────┼──────────────────────┼───────────┘
            │                     │                      │
            ▼                     ▼                      ▼
┌────────────────────────────────────────────────────────────────────┐
│                     COORDINATION LAYER                             │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │              HighlightingManager                             │  │
│  │  - highlight_cycle()                                         │  │
│  │  - highlight_path()                                          │  │
│  │  - highlight_invariant()                                     │  │
│  │  - highlight_deadlock()                                      │  │
│  │  - clear_highlights()                                        │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                              │                                     │
│           ┌──────────────────┼──────────────────┐                 │
│           ▼                  ▼                  ▼                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │
│  │ Topology Tab │  │  Runtime     │  │  Topology    │            │
│  │   Loaders    │  │   Panel      │  │   Palette    │            │
│  │              │  │   Loader     │  │   Loader     │            │
│  └──────────────┘  └──────────────┘  └──────────────┘            │
│           │                  │                  │                 │
└───────────┼──────────────────┼──────────────────┼─────────────────┘
            │                  │                  │
            ▼                  ▼                  ▼
┌────────────────────────────────────────────────────────────────────┐
│                      ANALYSIS LAYER                                │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌───────────────────────────┐  ┌────────────────────────────┐    │
│  │  Category A: Static (12)  │  │ Category B: Dynamic (8)    │    │
│  │                           │  │                            │    │
│  │  A1: Structural           │  │  B1: State Space           │    │
│  │   - P-Invariants      ✅   │  │   - Reachability           │    │
│  │   - T-Invariants           │  │   - Boundedness            │    │
│  │   - Siphons                │  │   - Coverability           │    │
│  │   - Traps                  │  │                            │    │
│  │                           │  │  B2: Liveness              │    │
│  │  A2: Graph                │  │   - Liveness Analysis      │    │
│  │   - Cycles            ✅   │  │   - Deadlock Detection     │    │
│  │   - Paths             ✅   │  │                            │    │
│  │   - DAG Analysis           │  │  B3: Performance           │    │
│  │   - Connectivity           │  │   - Throughput             │    │
│  │                           │  │   - Response Time          │    │
│  │  A3: Network              │  │   - Bottlenecks            │    │
│  │   - Hubs              ✅   │  │                            │    │
│  │   - Centrality             │  │                            │    │
│  │   - Communities            │  │                            │    │
│  │   - Clustering             │  │                            │    │
│  └───────────────────────────┘  └────────────────────────────┘    │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
            ┌─────────────────────────────────┐
            │    Model (Petri Net)            │
            │  + Simulation Engine            │
            └─────────────────────────────────┘
```

---

## 🔄 Data Flow Diagram

```
┌──────────────┐
│    Model     │
│  (Petri Net) │
└──────┬───────┘
       │
       │ Structure
       ├──────────────────────────────┐
       │                              │
       ▼                              │
┌──────────────────┐                  │
│ Static Analyzers │                  │
│  (Category A)    │                  │
│                  │                  │
│  - P-Invariants  │                  │
│  - Cycles        │                  │
│  - Paths         │                  │
│  - Hubs          │                  │
│  - T-Invariants  │                  │
│  - Siphons       │                  │
│  - etc.          │                  │
└──────┬───────────┘                  │
       │                              │
       │ Results                      │ Runtime
       ├──────────────┐               │
       ▼              ▼               ▼
┌─────────────┐  ┌────────────┐  ┌──────────────┐
│  Property   │  │  Topology  │  │  Simulation  │
│   Dialogs   │  │   Palette  │  │    Engine    │
│             │  │            │  │              │
│  Show:      │  │  Show:     │  └──────┬───────┘
│  - Per elem │  │  - Global  │         │
│  - Static   │  │  - All net │         │ Events
│             │  │            │         │
└─────┬───────┘  └──────┬─────┘         ▼
      │                 │         ┌──────────────────┐
      │                 │         │ Dynamic Analyzers│
      │                 │         │  (Category B)    │
      │                 │         │                  │
      │                 │         │  - Reachability  │
      │                 │         │  - Liveness      │
      │                 │         │  - Deadlock      │
      │                 │         │  - Boundedness   │
      │                 │         └──────┬───────────┘
      │                 │                │
      │                 │                │ Results
      │                 │                ▼
      │                 │         ┌─────────────────┐
      │                 │         │  Runtime Panel  │
      │                 │         │  (Right Panel)  │
      │                 │         │                 │
      │                 │         │  Show:          │
      │                 │         │  - Live data    │
      │                 │         │  - Dynamic      │
      │                 │         └─────────────────┘
      │                 │
      └────────┬────────┴────────────────┐
               │                         │
               ▼                         ▼
      ┌────────────────┐        ┌────────────────┐
      │  Highlighting  │        │     Canvas     │
      │    Manager     │◄───────│   Rendering    │
      └────────────────┘        └────────────────┘
               │
               │ Visual Feedback
               ▼
          [User sees highlighted elements on canvas]
```

---

## 📈 Progress Dashboard

```
OVERALL PROGRESS: 20% ████░░░░░░░░░░░░░░░░

┌────────────────────────────────────────────────────────────┐
│ Phase              Progress    Status       Deadline       │
├────────────────────────────────────────────────────────────┤
│ Phase 1-4         ████████   ✅ DONE       Oct 19, 2025   │
│                     100%                                   │
│                                                            │
│ Phase 5           ████░░░░   🟡 IN WORK    Nov 9, 2025    │
│ Static Analyzers    33%                                    │
│                                                            │
│ Phase 6           ░░░░░░░░   🔴 PENDING    Nov 16, 2025   │
│ Highlighting         0%                                    │
│                                                            │
│ Phase 7           ░░░░░░░░   🔴 PENDING    Nov 30, 2025   │
│ Runtime Panel        0%                                    │
│                                                            │
│ Phase 8           ░░░░░░░░   🔴 PENDING    Dec 28, 2025   │
│ Topology Palette     0%                                    │
└────────────────────────────────────────────────────────────┘

ANALYZER COMPLETION: 4 / 20 Tools
████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  20%

Category A (Static):   ████████░░░░░░░░  4/12 (33%)
  ✅ P-Invariants
  ⬜ T-Invariants
  ⬜ Siphons
  ⬜ Traps
  ✅ Cycles
  ✅ Paths
  ⬜ DAG
  ⬜ Connectivity
  ✅ Hubs
  ⬜ Centrality
  ⬜ Communities
  ⬜ Clustering

Category B (Dynamic):  ░░░░░░░░░░░░░░░░  0/8 (0%)
  ⬜ Reachability
  ⬜ Boundedness
  ⬜ Coverability
  ⬜ Liveness
  ⬜ Deadlock
  ⬜ Throughput
  ⬜ Response Time
  ⬜ Bottlenecks
```

---

## 🎯 Weekly Milestones

```
Week 1 (Oct 19-25)
├─ ✅ Plan Revision Complete
├─ ⬜ T-Invariants Analyzer
├─ ⬜ Siphons Analyzer
└─ ⬜ Traps Analyzer
   Goal: 7/12 static analyzers (58%)

Week 2 (Oct 26-Nov 1)
├─ ⬜ DAG Analyzer
├─ ⬜ Centrality Analyzer
├─ ⬜ Communities Analyzer
└─ ⬜ Clustering Analyzer
   Goal: 11/12 static analyzers (92%)

Week 3 (Nov 2-8)
├─ ⬜ Connectivity Analyzer
├─ ⬜ Property Dialog Polish
├─ ⬜ Integration Testing
└─ ⬜ Documentation
   Goal: Phase 5 Complete ✅

Week 4 (Nov 9-15)
├─ ⬜ HighlightingManager Implementation
├─ ⬜ Canvas Integration
├─ ⬜ Property Dialog Buttons
└─ ⬜ Visual Testing
   Goal: Phase 6 Complete ✅

Weeks 5-6 (Nov 16-29)
├─ ⬜ Runtime Panel UI
├─ ⬜ Dynamic Analyzers (B1, B2, B3)
├─ ⬜ Simulation Integration
└─ ⬜ Real-time Updates
   Goal: Phase 7 Complete ✅

Weeks 7-9 (Nov 30-Dec 28)
├─ ⬜ Topology Palette UI
├─ ⬜ Global Analysis
├─ ⬜ Integration Testing
└─ ⬜ User Documentation
   Goal: Phase 8 Complete ✅
```

---

## 🔗 Integration Points

```
Topology System Integration Points:

1. Property Dialogs
   ├─ Place Properties Dialog
   │  └─ Topology Tab (Static properties for this place)
   ├─ Transition Properties Dialog
   │  └─ Topology Tab (Static properties for this transition)
   └─ Arc Properties Dialog
      └─ Topology Tab (Static properties for this arc)

2. Right Panel
   └─ New "Runtime Dynamics" Tab
      └─ Dynamic properties (updates during simulation)

3. Canvas
   ├─ Highlighting Overlay
   │  ├─ Cycles (blue outline)
   │  ├─ Paths (green arrows)
   │  ├─ Invariants (yellow fill)
   │  └─ Issues (red alerts)
   └─ Click handlers
      └─ Show topology info on click

4. Floating Palettes
   └─ New "Topology Tools" Palette
      ├─ Static Analysis Buttons
      ├─ Dynamic Analysis Buttons
      └─ Global Actions
```

---

## 📚 Document Map

```
doc/topology/
├─ EXECUTIVE_SUMMARY_OCT2025.md      ← Quick overview
├─ REVISED_PLAN_OCT2025.md           ← Detailed plan (this revision)
├─ VISUAL_ROADMAP.md                 ← This document
├─ PHASES_1_TO_4_COMPLETE.md         ← What's done
├─ QUICK_RESUME_GUIDE.md             ← How to implement analyzer
└─ CURRENT_STATUS.md                 ← Progress tracking
```

---

**Status**: 🟢 Ready to Execute  
**Current Focus**: Phase 5 - Complete Static Analyzers  
**Next Milestone**: 7/12 analyzers by end of Week 1

**Last Updated**: October 19, 2025
