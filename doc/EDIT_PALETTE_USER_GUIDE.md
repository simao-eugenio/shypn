# Edit Palette System - User Guide

**Version**: 1.0  
**Created**: October 2, 2025  
**Last Updated**: October 2, 2025

## Overview

The Edit Palette System provides an intuitive interface for creating Petri net objects (Places, Transitions, and Arcs) on the canvas. The system consists of two floating palettes that overlay the canvas:

1. **Edit Palette**: A single [E] button that toggles the tools palette
2. **Edit Tools Palette**: Three tool buttons [P], [T], [A] for object creation

## User Interface

### Edit Palette ([E] Button)

Located in the **top-left corner** of the canvas, the Edit Palette provides a green [E] button:

- **Position**: Top-left (10px margin from edges)
- **Size**: 36×36 pixels
- **Color**: Green gradient background
- **Function**: Toggle button - click to show/hide the Edit Tools palette

### Edit Tools Palette ([P], [T], [A] Buttons)

Appears **below** the [E] button when activated:

- **[P] - Place Tool**: Create circular places on the canvas
- **[T] - Transition Tool**: Create rectangular transitions on the canvas
- **[A] - Arc Tool**: Create directed arcs between places and transitions

## How to Use

### Basic Workflow

1. **Activate Editing Mode**
   - Click the green **[E]** button in the top-left corner
   - The Edit Tools palette will slide down, showing [P], [T], [A] buttons

2. **Select a Tool**
   - Click one of the tool buttons:
     - **[P]** for Place tool
     - **[T]** for Transition tool
     - **[A]** for Arc tool
   - The selected button will highlight in **blue** with a glow effect

3. **Create Objects** (Future Implementation)
   - With a tool selected, **left-click** on the canvas to create the object
   - The object will be created at the clicked position

4. **Deselect Tool**
   - Click the **active tool button** again to deselect it
   - Or select a different tool to switch
   - Or click the **[E]** button to hide the palette

5. **Return to Pan Mode**
   - When no tool is selected, the canvas is in **pan mode**
   - **Right-click and drag** to pan the canvas
   - **Scroll** to zoom in/out

### Tool Selection Behavior

The Edit Tools implement **radio button behavior**:

- ✅ **Only ONE tool can be active at a time**
- ✅ Selecting a new tool automatically deselects the previous one
- ✅ Clicking the active tool again deselects it (return to pan mode)

### Visual Feedback

#### Inactive Tool Button
- White background
- Gray border
- Normal text

#### Active Tool Button
- **Blue background** (#4a90e2)
- **White text**
- **Bold font**
- **Thick border** (2px, darker blue)
- **Glow effect** (soft blue shadow)

#### Edit Button States
- **Inactive**: Green gradient
- **Hover**: Brighter green with glow
- **Active/Toggled**: Darker green with inset shadow

## Keyboard Shortcuts

Currently, there are no keyboard shortcuts for tool selection. This feature may be added in future versions:

- **Planned**: `P` key for Place tool
- **Planned**: `T` key for Transition tool
- **Planned**: `A` key for Arc tool
- **Planned**: `Esc` key to deselect tool

## Multiple Canvas Tabs

Each canvas tab maintains its **own independent tool state**:

- ✅ Selecting a tool in Tab 1 doesn't affect Tab 2
- ✅ Each tab has its own Edit Palette instance
- ✅ Switching tabs preserves the tool selection per tab

## Canvas Interaction Modes

### Pan Mode (Default)
**Active When**: No tool is selected

**Controls**:
- **Right-click + Drag**: Pan the canvas
- **Middle-click + Drag**: Pan the canvas
- **Shift + Left-click + Drag**: Pan the canvas
- **Scroll Wheel**: Zoom in/out
- **Left-click**: No action (safe to click without creating objects)

### Tool Mode (Tool Selected)
**Active When**: [P], [T], or [A] is selected

**Controls**:
- **Left-click**: Create object at cursor position (future implementation)
- **Right-click**: Still available for panning
- **Scroll Wheel**: Still available for zooming
- **Escape**: Deselect tool (planned)

**Important**: While in tool mode, **left-click creates objects** instead of starting a pan operation.

## Technical Details

### File Locations

```
shypn/
├── ui/palettes/
│   ├── edit_palette.ui           # [E] button UI definition
│   └── edit_tools_palette.ui     # [P][T][A] buttons UI definition
│
└── src/shypn/
    ├── helpers/
    │   ├── edit_palette_loader.py      # [E] button controller
    │   ├── edit_tools_loader.py        # [P][T][A] buttons controller
    │   └── model_canvas_loader.py      # Canvas integration
    │
    └── data/
        └── model_canvas_manager.py     # Tool state management
```

### Architecture

The system uses a **layered overlay architecture**:

```
┌─────────────────────────────────┐
│ Canvas Tab                      │
│                                 │
│  ┌───────────────────────────┐  │
│  │ GtkOverlay                │  │
│  │   ╔═══╗ ← Edit Palette    │  │
│  │   ║ E ║                    │  │
│  │   ╚═══╝                    │  │
│  │     ↓                      │  │
│  │   ┌─────────────┐          │  │
│  │   │ [P][T][A]   │ ← Tools │  │
│  │   └─────────────┘          │  │
│  │                            │  │
│  │   ┌──────────────────────┐ │  │
│  │   │ Canvas (Base Layer)  │ │  │
│  │   └──────────────────────┘ │  │
│  └───────────────────────────┘  │
└─────────────────────────────────┘
```

### Signal Flow

```
User clicks [P] button
    ↓
EditToolsLoader._on_place_toggled()
    ↓
Emit 'tool-changed' signal with 'place'
    ↓
ModelCanvasLoader._on_tool_changed()
    ↓
ModelCanvasManager.set_tool('place')
    ↓
Tool state updated, button highlighted
```

## Future Enhancements

The following features are planned for future releases:

### Object Creation (Next Phase)
- [ ] Create Place objects on canvas (circular nodes)
- [ ] Create Transition objects (rectangular bars)
- [ ] Create Arc connections between objects
- [ ] Object selection and manipulation
- [ ] Drag-to-reposition objects

### Keyboard Shortcuts
- [ ] Press `P` to activate Place tool
- [ ] Press `T` to activate Transition tool
- [ ] Press `A` to activate Arc tool
- [ ] Press `Esc` to deselect current tool
- [ ] Press `E` to toggle Edit Tools palette

### Enhanced Interaction
- [ ] Tooltip preview when hovering over canvas with tool active
- [ ] Ghost object preview following cursor
- [ ] Click-and-drag to size objects
- [ ] Double-click to edit object properties
- [ ] Context menu for object operations

### Visual Improvements
- [ ] Tool cursor changes (custom cursors for each tool)
- [ ] Animated palette transitions
- [ ] Status bar showing active tool
- [ ] Tool count badges on buttons

## Troubleshooting

### Edit Palette Not Appearing

**Problem**: The [E] button doesn't appear on the canvas.

**Solutions**:
1. Ensure you're using the first canvas tab (default document)
2. Check that the canvas is using the overlay structure (not legacy layout)
3. Restart the application

### Tools Palette Doesn't Show

**Problem**: Clicking [E] doesn't reveal the [P][T][A] buttons.

**Solutions**:
1. Check that [E] button is visibly toggled (darker green)
2. Wait for the slide-down animation (200ms duration)
3. Try clicking [E] again to toggle off, then on

### Multiple Tools Active Simultaneously

**Problem**: More than one tool button appears highlighted.

**Solutions**:
1. This should not happen (bug if it does)
2. Click each tool button to reset them
3. Report the issue with reproduction steps

### Tool Selection Not Working

**Problem**: Clicking tool buttons has no effect.

**Solutions**:
1. Ensure Edit Tools palette is visible (click [E] first)
2. Check console for JavaScript/GTK errors
3. Verify all palette loader files are loaded correctly

## Support

For additional help or to report issues:

- **Documentation**: See `doc/EDIT_PALETTE_DESIGN.md` for technical details
- **Architecture**: See `doc/EDIT_PALETTE_ARCHITECTURE.md` for visual diagrams
- **Contributing**: See `doc/CONTRIBUTING.md` for development guidelines

---

**Note**: This is Phase 1 implementation. Object creation functionality (Places, Transitions, Arcs) will be implemented in future phases. Currently, the system provides the UI framework and tool selection mechanism.
