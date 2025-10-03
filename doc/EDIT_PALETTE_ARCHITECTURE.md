# Edit Palette Architecture - Visual Overview

## Component Hierarchy

```
┌─────────────────────────────────────────────────────────────────┐
│ Canvas Tab (GtkNotebook Page)                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ GtkOverlay (Layered Container)                             │ │
│  │                                                             │ │
│  │  ╔═══╗ ← Edit Palette (Always Visible)                     │ │
│  │  ║ E ║    [E] = Edit button toggles tools                  │ │
│  │  ╚═══╝                                                      │ │
│  │     ↓                                                       │ │
│  │  ┌─────────────────┐ ← Edit Tools Palette (Toggleable)    │ │
│  │  │ [P] [T] [A]     │    [P] = Place tool                   │ │
│  │  └─────────────────┘    [T] = Transition tool              │ │
│  │                         [A] = Arc tool                      │ │
│  │                                                             │ │
│  │  ┌────────────────────────────────────────────────────┐    │ │
│  │  │                                                     │    │ │
│  │  │   GtkDrawingArea (Canvas - Base Layer)             │    │ │
│  │  │                                                     │    │ │
│  │  │   • Petri net drawing                               │    │ │
│  │  │   • Grid rendering                                  │    │ │
│  │  │   • Mouse interactions                              │    │ │
│  │  │                                                     │    │ │
│  │  └────────────────────────────────────────────────────┘    │ │
│  │                                                             │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Component Relationships

```
EditPaletteLoader ←──────────┐
    │                         │
    │ owns                    │ controls visibility
    │                         │
    ↓                         │
[E] Button ──────────────────┘
    │
    │ toggle signal
    │
    ↓
EditToolsLoader
    │
    │ owns
    │
    ↓
[P] [T] [A] Buttons ──────→ tool-changed signal ──→ ModelCanvasManager
                                                            │
                                                            │ stores
                                                            ↓
                                                     current_tool state
```

## File Structure

```
shypn/
├── ui/palettes/
│   ├── edit_palette.ui           ← XML: [E] button window
│   └── edit_tools_palette.ui     ← XML: [P][T][A] buttons window
│
├── src/shypn/
│   ├── helpers/
│   │   ├── edit_palette_loader.py      ← Loader: Manages [E] button
│   │   ├── edit_tools_loader.py        ← Loader: Manages [P][T][A] buttons
│   │   └── model_canvas_loader.py      ← Modified: Integrates palettes
│   │
│   └── data/
│       └── model_canvas_manager.py     ← Modified: Stores tool state
│
└── doc/
    ├── EDIT_PALETTE_DESIGN.md          ← Design document (this file's sibling)
    └── EDIT_PALETTE_ARCHITECTURE.md    ← Visual diagrams (this file)
```

## Signal Flow Diagram

```
User Interaction Flow:
═══════════════════════

1. Toggle Tools Palette:
   
   User clicks [E]
        │
        ↓
   edit_button.clicked signal
        │
        ↓
   EditPaletteLoader.toggle_tools()
        │
        ↓
   EditToolsLoader.show() / hide()
        │
        ↓
   GtkRevealer animation
        │
        ↓
   Tools palette appears/disappears


2. Select Tool:
   
   User clicks [P]
        │
        ↓
   place_button.toggled signal
        │
        ↓
   EditToolsLoader._on_place_toggled()
        │
        ├─→ Deactivate [T] and [A] buttons
        │
        ├─→ Update visual states (CSS classes)
        │
        └─→ emit('tool-changed', 'place')
             │
             ↓
        ModelCanvasLoader._on_tool_changed()
             │
             ↓
        ModelCanvasManager.set_tool('place')
             │
             ↓
        Current tool = 'place'


3. Use Tool on Canvas:
   
   User clicks canvas
        │
        ↓
   drawing_area.button-press-event
        │
        ↓
   ModelCanvasLoader._on_button_press()
        │
        ├─→ Check manager.get_tool()
        │
        └─→ if tool == 'place':
                create_place_at(x, y)
            elif tool == 'transition':
                create_transition_at(x, y)
            elif tool == 'arc':
                start_arc_creation(x, y)
            else:
                pan_mode()
```

## Layout Positioning

```
Canvas View (Top-Left Corner):
═══════════════════════════════

┌─────────────────────────────────────────┐
│ Canvas Window                           │
│                                         │
│  (10px margin)                          │
│     ↓                                   │
│  ┌──╔═══╗──────────────────────┐        │
│  │  ║ E ║ ← Edit Palette       │        │
│  │  ╚═══╝                       │        │
│  │    ↓ (5px gap)               │        │
│  │  ┌─────────────────┐         │        │
│  │  │ [P] [T] [A]     │ ←─┐     │        │
│  │  └─────────────────┘   │     │        │
│  │         ↑              │     │        │
│  │         │              │     │        │
│  │    Revealed when       │     │        │
│  │    [E] is clicked      │     │        │
│  │                   Edit Tools │        │
│  │                     Palette  │        │
│  └──────────────────────────────┘        │
│                                         │
│  Rest of Canvas                         │
│  (Drawing Area)                         │
│                                         │
└─────────────────────────────────────────┘
```

## State Machine

```
Tool Selection States:
═══════════════════════

    ┌──────────────┐
    │   NO TOOL    │ ← Initial state (pan mode)
    │   SELECTED   │
    └──────┬───────┘
           │
           │ User clicks [P]
           ↓
    ┌──────────────┐
    │    PLACE     │
    │    ACTIVE    │
    └──────┬───────┘
           │
           │ User clicks [T]
           ↓
    ┌──────────────┐
    │  TRANSITION  │
    │    ACTIVE    │
    └──────┬───────┘
           │
           │ User clicks [A]
           ↓
    ┌──────────────┐
    │     ARC      │
    │    ACTIVE    │
    └──────┬───────┘
           │
           │ User clicks active button again
           │ or presses Esc
           ↓
    ┌──────────────┐
    │   NO TOOL    │
    │   SELECTED   │
    └──────────────┘

States can transition to any other state directly.
Only one tool can be active at a time (radio behavior).
```

## CSS Styling Strategy

```css
/* Default tool button */
.tool-button {
    min-width: 40px;
    min-height: 40px;
    font-size: 14px;
    font-weight: normal;
    background-color: #f0f0f0;
    border: 1px solid #ccc;
    border-radius: 4px;
}

/* Active tool button */
.tool-button.active-tool {
    background-color: #4a90e2;
    color: white;
    border: 2px solid #2a70c2;
    font-weight: bold;
    box-shadow: 0 0 8px rgba(74, 144, 226, 0.5);
}

/* Edit button */
.edit-button {
    min-width: 36px;
    min-height: 36px;
    font-size: 16px;
    font-weight: bold;
    background-color: #2ecc71;
    color: white;
    border: 2px solid #27ae60;
    border-radius: 6px;
}

/* Edit button hover */
.edit-button:hover {
    background-color: #27ae60;
    box-shadow: 0 2px 8px rgba(46, 204, 113, 0.4);
}

/* Palette windows */
.palette-window {
    background-color: rgba(255, 255, 255, 0.95);
    border: 1px solid #999;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    padding: 4px;
}
```

## Integration Points

```
Modified Files:
═══════════════

1. src/shypn/helpers/model_canvas_loader.py
   
   Changes:
   - Import EditPaletteLoader, EditToolsLoader
   - Replace GtkDrawingArea with GtkOverlay
   - Create palette instances per tab
   - Connect tool-changed signals
   - Update _on_button_press() to check tool mode

2. src/shypn/data/model_canvas_manager.py
   
   Changes:
   - Add current_tool property
   - Add set_tool(tool_name) method
   - Add get_tool() method
   - Add clear_tool() method

3. ui/canvas/model_canvas.ui
   
   Changes (if needed):
   - May need to adjust structure to accommodate overlay
   - Or keep as-is and modify in loader code
```

## Testing Checklist

```
Visual Tests:
═════════════
□ Edit palette visible on startup
□ [E] button properly styled
□ [E] button positioned correctly (top-left)
□ Tools palette hidden initially
□ Tools palette appears on [E] click
□ Tools palette positioned next to [E]
□ [P], [T], [A] buttons properly styled
□ Active tool has visual indicator
□ Palettes don't overlap with canvas content inappropriately
□ Window resize maintains palette positions

Functional Tests:
══════════════════
□ [E] button toggles tools palette on/off
□ Clicking [P] selects Place tool
□ Clicking [T] selects Transition tool
□ Clicking [A] selects Arc tool
□ Only one tool active at a time
□ Clicking active tool deselects it
□ Tool state persists during canvas operations
□ Different tabs have independent tool states
□ Switching tabs preserves tool selection

Integration Tests:
═══════════════════
□ Canvas interactions respect tool mode
□ Pan mode works when no tool selected
□ (Future) Place creation works with [P] active
□ (Future) Transition creation works with [T] active
□ (Future) Arc creation works with [A] active
□ No console errors or warnings
□ No memory leaks
□ Smooth animations
```

## Performance Considerations

```
Optimization Points:
═══════════════════

1. Lazy Loading:
   - Create palettes only when tab is created
   - Don't create unnecessary instances

2. Event Handling:
   - Use signal blocking during programmatic changes
   - Avoid redundant style updates

3. Rendering:
   - Palettes shouldn't trigger canvas redraws
   - Use opacity/visibility for show/hide (not recreate)

4. Memory:
   - One palette pair per tab
   - Clean up on tab close
   - No circular references
```

---

**Created**: October 2, 2025
**Last Updated**: October 2, 2025
**Version**: 1.0
