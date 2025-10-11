# Time Playback Visual Reference

**Date**: October 11, 2025  
**Purpose**: Visual diagrams for understanding time concepts

---

## The Three Times - Visual Diagram

```
┌───────────────────────────────────────────────────────────────────────┐
│                        TIME CONCEPT DIAGRAM                            │
└───────────────────────────────────────────────────────────────────────┘

                        REAL WORLD
                   (The Phenomenon)
                           │
                           │ A cell divides
                           │ This takes 24 hours in nature
                           ▼
                  ┌─────────────────┐
                  │  τ_real = 24 hr │
                  │                 │
                  │  [Biology]      │
                  │  [Physics]      │
                  │  [Chemistry]    │
                  └─────────────────┘
                           │
                           │ We MODEL this
                           │ in our simulation
                           ▼
                     SIMULATION
                    (The Model)
                           │
                  ┌─────────────────┐
                  │  τ_sim = 24 hr  │
                  │                 │
                  │  t = 0 → 24 hr  │
                  │  dt = 0.1 hr    │
                  │  240 steps      │
                  └─────────────────┘
                           │
                           │ We WATCH this
                           │ at different speeds
                           ▼
                      PLAYBACK
                   (Visualization)
                           │
          ┌────────────────┼────────────────┐
          │                │                │
          ▼                ▼                ▼
    ┌─────────┐      ┌─────────┐      ┌─────────┐
    │ 1x      │      │ 60x     │      │ 0.1x    │
    │         │      │         │      │         │
    │ Watch   │      │ Watch   │      │ Watch   │
    │ in 24hr │      │ in 24min│      │ in 240hr│
    │         │      │         │      │         │
    │ Real    │      │ Fast    │      │ Slow    │
    │ time    │      │ forward │      │ motion  │
    └─────────┘      └─────────┘      └─────────┘
```

---

## Time Scale Examples - Real World Scenarios

```
┌───────────────────────────────────────────────────────────────────────┐
│                  SCENARIO 1: ENZYME KINETICS                          │
└───────────────────────────────────────────────────────────────────────┘

Real-World:     Reaction completes in 10 milliseconds
                ├─────────────────────┤
                0ms                  10ms
                     τ_real = 10ms

Simulation:     Model all 10ms with dt=0.001ms (10,000 steps)
                ├─────────────────────┤
                0                    10ms
                     τ_sim = 10ms

Playback:       SLOW MOTION - Watch in 10 seconds (1000x slower)
                ├───────────────────────────────────────────┤
                0s                                         10s
                     τ_playback = 10s
                     time_scale = 0.001 (1000x slower)

Purpose: Analyze fast molecular interactions

═══════════════════════════════════════════════════════════════════════

┌───────────────────────────────────────────────────────────────────────┐
│                  SCENARIO 2: CELL DIVISION                            │
└───────────────────────────────────────────────────────────────────────┘

Real-World:     Cell cycle takes 24 hours
                ├───────────────────────────────────────┤
                0hr                                    24hr
                     τ_real = 24hr

Simulation:     Model all 24 hours with dt=6min (240 steps)
                ├───────────────────────────────────────┤
                0                                      24hr
                     τ_sim = 24hr

Playback:       FAST FORWARD - Watch in 5 minutes (288x faster)
                ├──────┤
                0     5min
                     τ_playback = 5min
                     time_scale = 288.0 (288x faster)

Purpose: Quick overview of entire cell cycle

═══════════════════════════════════════════════════════════════════════

┌───────────────────────────────────────────────────────────────────────┐
│                  SCENARIO 3: MANUFACTURING LINE                       │
└───────────────────────────────────────────────────────────────────────┘

Real-World:     Production run takes 8 hours (1 shift)
                ├────────────────────────────────┤
                0hr                             8hr
                     τ_real = 8hr

Simulation:     Model all 8 hours with dt=1min (480 steps)
                ├────────────────────────────────┤
                0                               8hr
                     τ_sim = 8hr

Playback:       COMPRESSED - Watch in 8 minutes (60x faster)
                ├──────┤
                0     8min
                     τ_playback = 8min
                     time_scale = 60.0 (60x faster)

Purpose: Review full shift for bottlenecks
```

---

## How Time Scale Works - Step by Step

```
┌───────────────────────────────────────────────────────────────────────┐
│              SIMULATION LOOP WITH TIME SCALE                          │
└───────────────────────────────────────────────────────────────────────┘

USER SETTINGS:
  duration = 60 seconds (1 minute phenomenon)
  dt = 1.0 seconds (1 second per step)
  time_scale = 10.0 (watch 10x faster)

CALCULATION:
  
  1. Fixed GUI update interval = 0.1 seconds (100ms)
     └─► This is real-world playback time
  
  2. Model time per GUI update = 0.1 × time_scale
                                = 0.1 × 10.0
                                = 1.0 seconds
     └─► How much simulation time advances per screen refresh
  
  3. Steps per GUI update = model_time / dt
                          = 1.0 / 1.0
                          = 1 step
     └─► How many simulation steps to execute

RESULT:
  
  Total steps: 60 / 1.0 = 60 steps
  GUI updates: 60 / 1.0 = 60 updates
  Playback time: 60 / 10.0 = 6 seconds
  
  ┌─────────────────────────────────────────────────────────────┐
  │ Real World:        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 60s  │
  │                    0s                                 60s   │
  │                                                              │
  │ Simulation:        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 60s  │
  │                    0s                                 60s   │
  │                                                              │
  │ Playback:          ━━━━━ 6s                                │
  │                    0s   6s                                  │
  │                                                              │
  │ User Experience: "60 seconds of process in 6 seconds!" ✅   │
  └─────────────────────────────────────────────────────────────┘
```

---

## The Problem - Before Implementation

```
┌───────────────────────────────────────────────────────────────────────┐
│                    CURRENT BEHAVIOR (BROKEN)                          │
└───────────────────────────────────────────────────────────────────────┘

User clicks: [60x] button

settings.time_scale = 60.0  ✅ Property updated

UI shows: "Speed: 60x"  ✅ Display updated

Controller runs:
  gui_interval = 0.1
  steps_per_callback = 0.1 / dt
  
  ❌ IGNORES time_scale!
  
  Result: Playback speed doesn't change!

┌─────────────────────────────────────────────────────────────────┐
│                                                                  │
│  User expects: 60x faster playback                              │
│  What happens: Same speed as before                             │
│                                                                  │
│  Why: Controller doesn't read settings.time_scale               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## The Solution - After Implementation

```
┌───────────────────────────────────────────────────────────────────────┐
│                    NEW BEHAVIOR (WORKING)                             │
└───────────────────────────────────────────────────────────────────────┘

User clicks: [60x] button

settings.time_scale = 60.0  ✅ Property updated

UI shows: "Speed: 60x"  ✅ Display updated

Controller runs:
  gui_interval = 0.1
  model_time_per_update = 0.1 × settings.time_scale  ⭐ NEW
  model_time_per_update = 0.1 × 60.0 = 6.0 seconds
  steps_per_callback = 6.0 / dt
  
  ✅ USES time_scale!
  
  Result: Playback is now 60x faster!

┌─────────────────────────────────────────────────────────────────┐
│                                                                  │
│  User expects: 60x faster playback                              │
│  What happens: 60x faster playback ✅                           │
│                                                                  │
│  Why: Controller now reads settings.time_scale                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Timeline Comparison

```
┌───────────────────────────────────────────────────────────────────────┐
│             REAL-TIME (1x) vs FAST FORWARD (60x)                      │
└───────────────────────────────────────────────────────────────────────┘

Phenomenon: Cell division (24 hours real-world)

─────────────────────────────────────────────────────────────────────────

REAL-TIME (time_scale = 1.0):

Real World:  ●━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━●
             0hr                                    24hr
             
Simulation:  ●━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━●
             0hr                                    24hr
             
Playback:    ●━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━●
             0hr                                    24hr
             
User waits:  24 HOURS to see entire process

─────────────────────────────────────────────────────────────────────────

FAST FORWARD (time_scale = 60.0):

Real World:  ●━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━●
             0hr                                    24hr
             
Simulation:  ●━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━●
             0hr                                    24hr
             
Playback:    ●━━━━━━━●
             0min    24min
             
User waits:  24 MINUTES to see entire process ✅

─────────────────────────────────────────────────────────────────────────

VERY FAST (time_scale = 288.0):

Real World:  ●━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━●
             0hr                                    24hr
             
Simulation:  ●━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━●
             0hr                                    24hr
             
Playback:    ●━━●
             0  5min
             
User waits:  5 MINUTES to see entire process ✅✅

─────────────────────────────────────────────────────────────────────────

SLOW MOTION (time_scale = 0.1):

Real World:  ●━━━●
             0  10s
             
Simulation:  ●━━━●
             0  10s
             
Playback:    ●━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━●
             0s                                   100s
             
User waits:  100 SECONDS to see 10 seconds (detailed analysis) ✅
```

---

## Code Change Visualization

```
┌───────────────────────────────────────────────────────────────────────┐
│                FILE: controller.py (line ~613)                        │
└───────────────────────────────────────────────────────────────────────┘

BEFORE (current code):
┌─────────────────────────────────────────────────────────────────────┐
│  gui_interval_s = 0.1                                                │
│  self._steps_per_callback = max(1, int(gui_interval_s / time_step)) │
│                                            ▲                          │
│                                            │                          │
│                                            └─ Ignores time_scale! ❌ │
└─────────────────────────────────────────────────────────────────────┘

AFTER (new code):
┌─────────────────────────────────────────────────────────────────────┐
│  gui_interval_s = 0.1                                                │
│  model_time_per_update = gui_interval_s * self.settings.time_scale  │
│                                            ▲                          │
│                                            │                          │
│                                            └─ Uses time_scale! ✅    │
│  self._steps_per_callback = max(1,                                  │
│      int(model_time_per_update / time_step))                        │
└─────────────────────────────────────────────────────────────────────┘

Impact: 3 lines added, 1 line modified
Time: 30 minutes
Result: All speed controls now work! 🎉
```

---

## UI Flow Diagram

```
┌───────────────────────────────────────────────────────────────────────┐
│                    USER INTERACTION FLOW                              │
└───────────────────────────────────────────────────────────────────────┘

1. User opens simulation palette
   │
   ├─► Clicks [S] button (simulate)
   │
   └─► Palette slides up
       │
       ├─► [R] Run
       ├─► [P] Step  
       ├─► [S] Stop
       ├─► [T] Reset
       └─► [⚙] Settings
           │
           └─► Settings panel slides down
               │
               ├─► TIME STEP
               │   ├─► [●] Auto
               │   └─► [○] Manual [____]
               │
               ├─► PLAYBACK SPEED ⭐
               │   ├─► [0.1x] Slow motion
               │   ├─► [0.5x] Half speed
               │   ├─► [1x]   Real-time (default)
               │   ├─► [10x]  Fast forward
               │   ├─► [60x]  Very fast
               │   └─► Custom: [____]
               │
               ├─► CONFLICT POLICY
               │   └─► [Random ▼]
               │
               └─► [Apply] [Reset]

2. User clicks [60x] button
   │
   ├─► Button activates (highlighted)
   │
   ├─► settings.time_scale = 60.0
   │
   ├─► Controller recalculates:
   │   └─► steps_per_callback = (0.1 × 60.0) / dt
   │
   └─► Simulation now runs 60x faster! ✅

3. User sees in UI:
   │
   └─► Time: 12.5 / 60.0 s @ 60x
              ▲      ▲       ▲
              │      │       └─ Speed indicator
              │      └───────── Duration
              └──────────────── Current time
```

---

## Summary Diagram

```
┌═══════════════════════════════════════════════════════════════════════┐
║                    COMPLETE ARCHITECTURE                              ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                        ║
║  ┌──────────────┐        ┌──────────────┐        ┌──────────────┐   ║
║  │  REAL WORLD  │   ≡    │  SIMULATION  │   ÷    │   PLAYBACK   │   ║
║  │  (τ_real)    │        │  (τ_sim)     │        │ (τ_playback) │   ║
║  └──────────────┘        └──────────────┘        └──────────────┘   ║
║        │                       │                        │             ║
║        │                       │                        │             ║
║        │                       │                        │             ║
║        ▼                       ▼                        ▼             ║
║  ┌──────────────┐        ┌──────────────┐        ┌──────────────┐   ║
║  │   DURATION   │        │   DURATION   │        │  TIME_SCALE  │   ║
║  │   24 hours   │        │   24 hours   │        │     60x      │   ║
║  └──────────────┘        └──────────────┘        └──────────────┘   ║
║        │                       │                        │             ║
║        │                       │                        │             ║
║        └───────────┬───────────┴────────────────────────┘             ║
║                    │                                                  ║
║                    ▼                                                  ║
║           ┌─────────────────┐                                        ║
║           │  USER WATCHES   │                                        ║
║           │  24 hours in    │                                        ║
║           │  24 minutes     │                                        ║
║           └─────────────────┘                                        ║
║                                                                        ║
║  STATUS:                                                              ║
║  ────────                                                             ║
║  Real World Modeling:  ✅ COMPLETE                                   ║
║  Simulation Time:      ✅ COMPLETE                                   ║
║  Time Scale Property:  ✅ EXISTS                                     ║
║  UI Controls:          ✅ COMPLETE                                   ║
║  Controller Wiring:    ❌ MISSING (Phase 1)                          ║
║                                                                        ║
║  READY FOR IMPLEMENTATION: YES ✅                                    ║
║                                                                        ║
╚═══════════════════════════════════════════════════════════════════════╝
```

---

**Next**: Proceed with Phase 1 implementation (2-3 hours)
