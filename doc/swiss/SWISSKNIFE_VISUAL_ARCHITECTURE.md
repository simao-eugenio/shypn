# SwissKnifePalette - Visual Architecture Diagrams

## Current Architecture (PROBLEM)

```
┌─────────────────────────────────────────────────────────────┐
│                    CANVAS OVERLAY                           │
│                                                             │
│   ┌─────────────────────────────────────────────────────┐  │
│   │  SwissKnifePalette (CENTER-BOTTOM, margin=20px)     │  │
│   │                                                     │  │
│   │  ┌─────────────────────────────────────────────┐   │  │
│   │  │  Sub-Palette Area (VARIABLE HEIGHT) ⚠️      │   │  │
│   │  │                                              │   │  │
│   │  │  IF Edit category:                           │   │  │
│   │  │    [P][T][A][S][L] ────────────> 50px       │   │  │
│   │  │                                              │   │  │
│   │  │  IF Simulate category:                       │   │  │
│   │  │    [Step][Reset][Play]                       │   │  │
│   │  │    ┌──────────────────────────┐             │   │  │
│   │  │    │ Settings (INSIDE) ⚠️     │             │   │  │
│   │  │    │ - Time scale             │             │   │  │
│   │  │    │ - Token speed            │             │   │  │
│   │  │    └──────────────────────────┘             │   │  │
│   │  │    ────────────────────────────> 120px ⚠️   │   │  │
│   │  │                                              │   │  │
│   │  │  IF Layout category:                         │   │  │
│   │  │    [Auto][Hier][Force] ─────────> 50px      │   │  │
│   │  │                                              │   │  │
│   │  └─────────────────────────────────────────────┘   │  │
│   │  ┌─────────────────────────────────────────────┐   │  │
│   │  │  Category Buttons (44px fixed)              │   │  │
│   │  │  [Edit] [Simulate] [Layout]                 │   │  │
│   │  └─────────────────────────────────────────────┘   │  │
│   └─────────────────────────────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘

PROBLEM: Height jumps from 139px → 209px → 139px when switching!
```

## Refactored Architecture (SOLUTION)

```
┌─────────────────────────────────────────────────────────────┐
│                    CANVAS OVERLAY                           │
│                                                             │
│   ┌─────────────────────────────────────────────────────┐  │
│   │  Parameter Panel (ABOVE palette, slides UP/DOWN)    │  │
│   │  ┌────────────────────────────────────────────────┐ │  │
│   │  │ Settings Panel (VISIBLE when requested)        │ │  │
│   │  │ ┌────────────────────────────────────────────┐ │ │  │
│   │  │ │ ⚙️ Simulation Settings                      │ │ │  │
│   │  │ │ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │ │ │  │
│   │  │ │ Time Scale: [════════░░░] 1.0x             │ │ │  │
│   │  │ │ Token Speed: [══════░░░░] 0.6x             │ │ │  │
│   │  │ │ Visualization: [✓] Smooth transitions       │ │ │  │
│   │  │ └────────────────────────────────────────────┘ │ │  │
│   │  └────────────────────────────────────────────────┘ │  │
│   │  ▲ Slides UP with 400ms animation                   │  │
│   └──┼──────────────────────────────────────────────────┘  │
│      │                                                     │
│   ┌──┴──────────────────────────────────────────────────┐  │
│   │  SwissKnifePalette (114px CONSTANT) ✅              │  │
│   │                                                     │  │
│   │  ┌─────────────────────────────────────────────┐   │  │
│   │  │  Sub-Palette Area (50px FIXED) ✅           │   │  │
│   │  │                                              │   │  │
│   │  │  ALL categories: 50px height                 │   │  │
│   │  │  ┌────────────────────────────────────────┐ │   │  │
│   │  │  │ Edit: [P][T][A][S][L]          50px ✅ │ │   │  │
│   │  │  │ Simulate: [Step][Reset][Play]  50px ✅ │ │   │  │
│   │  │  │ Layout: [Auto][Hier][Force]    50px ✅ │ │   │  │
│   │  │  └────────────────────────────────────────┘ │   │  │
│   │  │                                              │   │  │
│   │  │  (Settings moved ABOVE ▲)                    │   │  │
│   │  └─────────────────────────────────────────────┘   │  │
│   │  ┌─────────────────────────────────────────────┐   │  │
│   │  │  Category Buttons (44px fixed)              │   │  │
│   │  │  [Edit] [Simulate] [Layout]                 │   │  │
│   │  └─────────────────────────────────────────────┘   │  │
│   │                                                     │  │
│   │  20px margin (bottom) + 50px (sub) + 44px (cats)   │  │
│   │  = 114px CONSTANT HEIGHT ✅                         │  │
│   └─────────────────────────────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘

SOLUTION: Constant 114px height, parameter panels slide above!
```

## Widget Hierarchy (Refactored)

```
Gtk.Overlay (canvas overlay)
  └─ SwissKnifePalette.get_widget() → Gtk.Box(VERTICAL)
      ├─ 1️⃣ parameter_panel_revealer (GtkRevealer, SLIDE_UP)
      │   └─ [Dynamic parameter panel widget]
      │       (Built on-demand via factory function)
      │       ▲ Slides UP from here, appears ABOVE sub-palettes
      │
      ├─ 2️⃣ sub_palette_area (Gtk.Box, 50px FIXED)
      │   ├─ edit_revealer (GtkRevealer, SLIDE_UP, 50px)
      │   │   └─ [P][T][A][S][L] buttons
      │   ├─ simulate_revealer (GtkRevealer, SLIDE_UP, 50px)
      │   │   └─ [Step][Reset][Play][⚙️] buttons
      │   │       (⚙️ triggers parameter panel above ▲)
      │   └─ layout_revealer (GtkRevealer, SLIDE_UP, 50px)
      │       └─ [Auto][Hier][Force] buttons
      │
      └─ 3️⃣ category_box (Gtk.Box, 44px fixed)
          ├─ [Edit] button
          ├─ [Simulate] button
          └─ [Layout] button
```

## Parameter Panel Lifecycle

```
┌─────────────────────────────────────────────────────────────┐
│  User Action: Click [⚙️] settings button                     │
└────────────┬────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────┐
│  ParameterPanelManager.toggle_panel('simulate_settings')    │
└────────────┬────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────┐
│  IF panel already shown:                                    │
│    → hide_panel() → slide DOWN → remove widget → destroy   │
│  ELSE:                                                      │
│    → Get factory function from registry                     │
│    → panel = factory()  ← Fresh widget built                │
│    → parameter_panel_revealer.add(panel)                    │
│    → parameter_panel_revealer.set_reveal_child(True)        │
│    → Slide UP animation (400ms)                             │
│    → Emit signal: 'parameter-panel-shown'                   │
└─────────────────────────────────────────────────────────────┘

✅ Wayland-safe: Panel built in same parent (parameter_panel_revealer)
✅ No reparenting: Panel created/destroyed, never moved
```

## Animation Sequence

### Opening Simulate + Settings Panel

```
Time 0ms:
┌────────────────────────┐
│ [Edit][Simulate][Layout]│  ← Click [Simulate]
└────────────────────────┘
Height: 44px (categories only)

Time 300ms (mid-animation):
┌────────────────────────┐
│ [Step][Reset]          │  ← Sliding UP
│────────────────────────│
│ [Edit][Simulate][Layout]│
└────────────────────────┘
Height: 44px + 25px (partial reveal)

Time 600ms (animation complete):
┌────────────────────────┐
│ [Step][Reset][Play][⚙️] │  ← Fully revealed (50px)
│────────────────────────│
│ [Edit][Simulate][Layout]│
└────────────────────────┘
Height: 44px + 25px + 50px = 119px ✅ (close to 114px target)

User clicks [⚙️]:

Time 0ms:
┌────────────────────────────┐
│ [Step][Reset][Play][⚙️]     │  ← Click [⚙️]
│────────────────────────────│
│ [Edit][Simulate][Layout]    │
└────────────────────────────┘
Height: 119px

Time 200ms (mid-animation):
┌────────────────────────────┐
│ ⚙️ Settings (partial)        │  ← Sliding UP
│────────────────────────────│
│ [Step][Reset][Play][⚙️]     │
│────────────────────────────│
│ [Edit][Simulate][Layout]    │
└────────────────────────────┘

Time 400ms (animation complete):
┌────────────────────────────┐
│ ⚙️ Simulation Settings      │  ← ABOVE main palette ✅
│ Time Scale: [═══════░]     │
│ Token Speed: [══════░░]    │
│────────────────────────────│
│ [Step][Reset][Play][⚙️]     │  ← Main palette unchanged (119px)
│────────────────────────────│
│ [Edit][Simulate][Layout]    │
└────────────────────────────┘
Height: 119px (main) + [variable panel above]

Main palette height: STILL 119px! ✅
```

## State Transitions

```
                        ┌──────────────────┐
                        │  Initial State   │
                        │  No category     │
                        │  Height: 44px    │
                        └────────┬─────────┘
                                 │
                         Click [Simulate]
                                 │
                                 ▼
                        ┌──────────────────┐
                        │  Simulate Open   │
                        │  Height: 119px   │
                        │  Settings: Hidden│
                        └────────┬─────────┘
                                 │
                         Click [⚙️]
                                 │
                                 ▼
        ┌────────────────────────────────────────┐
        │  Simulate + Settings Panel             │
        │  Height: 119px (main) + panel above    │
        │  Panel: Visible above                  │
        └───────┬────────────────┬───────────────┘
                │                │
        Click [⚙️] again    Click [Edit]
                │                │
                ▼                ▼
        ┌───────────────┐  ┌─────────────┐
        │ Settings hide │  │ Auto-hide   │
        │ slide DOWN    │  │ panel       │
        │ return to     │  │ switch to   │
        │ Simulate Open │  │ Edit Open   │
        └───────────────┘  └─────────────┘
```

## Universal Parameter Panel Pattern (Future)

```
┌─────────────────────────────────────────────────────────────┐
│  ANY Tool Can Register Parameter Panel                     │
└────────────┬────────────────────────────────────────────────┘
             │
   ┌─────────┴──────────┬──────────────┬─────────────┐
   │                    │              │             │
   ▼                    ▼              ▼             ▼
┌──────────┐    ┌───────────────┐  ┌────────┐  ┌──────────┐
│Simulation│    │Layout         │  │Analysis│  │Transform │
│Settings  │    │Algorithm      │  │Options │  │Settings  │
│          │    │Parameters     │  │        │  │          │
│- Time    │    │- Spacing      │  │- Type  │  │- Rotate  │
│- Speed   │    │- Direction    │  │- Depth │  │- Scale   │
│- Visual  │    │- Force        │  │- Graph │  │- Flip    │
└──────────┘    └───────────────┘  └────────┘  └──────────┘

All use same ParameterPanelManager!
All slide ABOVE sub-palettes!
Main palette height: ALWAYS 114px! ✅
```

## Summary

### Before: Variable Height ❌
- Edit: 139px
- **Simulate: 209px** ⚠️ (jumps!)
- Layout: 139px
- Settings **INSIDE** sub-palette

### After: Constant Height ✅
- Edit: 114px
- **Simulate: 114px** ✅ (stable!)
- Layout: 114px
- Settings **ABOVE** palette (slides in/out)

**Space savings: 70px (33% reduction on Simulate)**
**UX improvement: No height jumps (predictable position)**
**Architecture: Universal pattern (extensible to all tools)**
