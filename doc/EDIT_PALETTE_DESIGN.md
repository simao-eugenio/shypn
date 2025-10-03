# Edit Palette Design - Object Net Design Implementation

## Overview

This document describes the design and implementation of the floating overlayed edit palette system for the SHYpn Petri Net editor. The system consists of two interconnected palettes that provide quick access to editing tools.

## Architecture

### Component Structure

```
Edit Palette System
├── Edit Button Palette (Always Visible)
│   └── [E] Button - Toggles tools palette
│
└── Edit Tools Palette (Toggleable)
    ├── [P] Button - Place tool
    ├── [T] Button - Transition tool
    └── [A] Button - Arc tool
```

### Files to Create

```
ui/palettes/
├── edit_palette.ui         # Main [E] button palette (always visible)
└── edit_tools_palette.ui   # Tools palette [P], [T], [A] (revealed)

src/shypn/helpers/
├── edit_palette_loader.py       # Loader for edit_palette.ui
└── edit_tools_loader.py         # Loader for edit_tools_palette.ui
```

## Implementation Plan

### Phase 1: UI Design (Tasks 1-2)

#### 1.1 edit_palette.ui
**Location**: `ui/palettes/edit_palette.ui`

**Requirements**:
- Single button labeled [E]
- Compact size (30-40px)
- Floating style (frame/border)
- GtkRevealer for smooth show/hide
- Professional styling

**XML Structure**:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<interface>
  <object class="GtkWindow" id="edit_palette_window">
    <property name="type">popup</property>
    <property name="decorated">False</property>
    <child>
      <object class="GtkBox" id="edit_palette_box">
        <child>
          <object class="GtkButton" id="edit_button">
            <property name="label">E</property>
            <!-- Styling properties -->
          </object>
        </child>
      </object>
    </child>
  </object>
</interface>
```

#### 1.2 edit_tools_palette.ui
**Location**: `ui/palettes/edit_tools_palette.ui`

**Requirements**:
- Three toggle buttons: [P], [T], [A]
- Horizontal or vertical layout
- Group buttons (only one active at a time)
- Visual feedback for active tool
- Compact and professional

**XML Structure**:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<interface>
  <object class="GtkWindow" id="edit_tools_window">
    <property name="type">popup</property>
    <property name="decorated">False</property>
    <child>
      <object class="GtkBox" id="tools_box">
        <child>
          <object class="GtkToggleButton" id="place_button">
            <property name="label">P</property>
            <!-- Styling -->
          </object>
        </child>
        <child>
          <object class="GtkToggleButton" id="transition_button">
            <property name="label">T</property>
          </object>
        </child>
        <child>
          <object class="GtkToggleButton" id="arc_button">
            <property name="label">A</property>
          </object>
        </child>
      </object>
    </child>
  </object>
</interface>
```

### Phase 2: Loader Implementation (Tasks 3-4)

#### 2.1 edit_palette_loader.py
**Location**: `src/shypn/helpers/edit_palette_loader.py`

**Class**: `EditPaletteLoader`

**Responsibilities**:
- Load `edit_palette.ui`
- Manage [E] button state
- Show/hide tools palette
- Position palette over canvas
- Handle window events (resize, focus)

**Key Methods**:
```python
class EditPaletteLoader:
    def __init__(self, ui_path='ui/palettes/edit_palette.ui'):
        """Load the edit palette UI."""
        
    def attach_to(self, overlay, tools_palette):
        """Attach palette to a GtkOverlay over canvas."""
        
    def toggle_tools(self):
        """Show/hide the edit tools palette."""
        
    def set_position(self, x, y):
        """Position the palette at specific coordinates."""
```

#### 2.2 edit_tools_loader.py
**Location**: `src/shypn/helpers/edit_tools_loader.py`

**Class**: `EditToolsLoader`

**Responsibilities**:
- Load `edit_tools_palette.ui`
- Manage tool buttons (P, T, A)
- Handle tool selection (radio behavior)
- Emit tool change signals
- Manage button visual states

**Key Methods**:
```python
class EditToolsLoader:
    def __init__(self, ui_path='ui/palettes/edit_tools_palette.ui'):
        """Load the edit tools palette UI."""
        
    def get_selected_tool(self):
        """Return currently selected tool: 'place', 'transition', 'arc', or None."""
        
    def set_tool(self, tool_name):
        """Programmatically select a tool."""
        
    def attach_to(self, overlay):
        """Attach to a GtkOverlay."""
        
    def show(self):
        """Show the tools palette."""
        
    def hide(self):
        """Hide the tools palette."""
```

### Phase 3: Integration (Tasks 5-7)

#### 3.1 Canvas Integration
**File**: `src/shypn/helpers/model_canvas_loader.py`

**Changes**:
1. Import palette loaders
2. Create GtkOverlay for each canvas tab
3. Add drawing area to overlay
4. Add edit palette to overlay
5. Position palette appropriately (top-left corner, with margins)

**Code Structure**:
```python
# In add_document() method
overlay = Gtk.Overlay()
drawing_area = Gtk.DrawingArea()
overlay.add(drawing_area)  # Base layer

# Create and attach edit palette
edit_palette = EditPaletteLoader()
edit_tools = EditToolsLoader()
edit_palette.attach_to(overlay, edit_tools)
edit_tools.attach_to(overlay)

# Connect signals
edit_tools.connect('tool-changed', self._on_tool_changed)
```

#### 3.2 State Management
**File**: `src/shypn/data/model_canvas_manager.py`

**New Properties**:
```python
self.current_tool = None  # 'place', 'transition', 'arc', or None
```

**New Methods**:
```python
def set_tool(self, tool_name):
    """Set the current editing tool."""
    self.current_tool = tool_name

def get_tool(self):
    """Get the current editing tool."""
    return self.current_tool

def clear_tool(self):
    """Deselect current tool."""
    self.current_tool = None
```

#### 3.3 Canvas Interaction
**File**: `src/shypn/helpers/model_canvas_loader.py`

**Modify Click Handlers**:
```python
def _on_button_press(self, widget, event, manager):
    """Handle button press based on current tool."""
    tool = manager.get_tool()
    
    if tool == 'place':
        self._create_place_at(event.x, event.y, manager)
    elif tool == 'transition':
        self._create_transition_at(event.x, event.y, manager)
    elif tool == 'arc':
        self._start_arc_creation(event.x, event.y, manager)
    else:
        # Pan mode (existing behavior)
        pass
```

### Phase 4: Visual Feedback (Task 8)

#### 4.1 Active Tool Styling
**Requirements**:
- Active button: Different background color
- Active button: Border or outline
- Active button: Possibly icon change
- Smooth transitions

**CSS Approach**:
```python
# In edit_tools_loader.py
def _update_button_styles(self):
    """Update visual appearance of buttons based on selection."""
    for button, tool in [(self.place_button, 'place'), ...]:
        if self.current_tool == tool:
            button.get_style_context().add_class('active-tool')
        else:
            button.get_style_context().remove_class('active-tool')
```

**CSS Definition** (in code or separate file):
```css
.active-tool {
    background-color: #4a90e2;
    border: 2px solid #2a70c2;
    font-weight: bold;
}
```

### Phase 5: Testing (Task 9)

#### 5.1 Test Cases
1. **Visibility Tests**
   - [ ] Edit palette appears on canvas
   - [ ] [E] button toggles tools palette
   - [ ] Tools palette positioned correctly
   - [ ] Palettes don't interfere with canvas

2. **Interaction Tests**
   - [ ] [E] button responds to clicks
   - [ ] Tool buttons toggle correctly
   - [ ] Only one tool active at a time
   - [ ] Tool deselection works

3. **Multi-Tab Tests**
   - [ ] Each tab has its own palette
   - [ ] Tool selection independent per tab
   - [ ] Switching tabs preserves tool state

4. **Resize Tests**
   - [ ] Palettes reposition on window resize
   - [ ] Palettes remain visible after resize
   - [ ] No z-order issues

### Phase 6: Documentation (Task 10)

#### 6.1 User Documentation
**File**: `doc/EDIT_PALETTE_USAGE.md`

**Contents**:
- How to access editing tools
- Explanation of each tool (P, T, A)
- Keyboard shortcuts (future)
- Tips and best practices

#### 6.2 Developer Documentation
**File**: `doc/EDIT_PALETTE_ARCHITECTURE.md`

**Contents**:
- System architecture
- Component relationships
- How to add new tools
- Extension points
- Signal/callback flow

## Technical Specifications

### Positioning Strategy

**Edit Button Palette**:
- Position: Top-left corner of canvas
- Offset: 10px from top, 10px from left
- Z-index: Above canvas, below dialogs

**Edit Tools Palette**:
- Position: Adjacent to [E] button (right or below)
- Offset: 5px gap from [E] button
- Animation: Slide in/fade in
- Z-index: Same as [E] button

### State Management

**Tool Selection**:
- Radio button behavior (only one tool active)
- Clicking active tool deselects it (returns to pan mode)
- Tool state stored in canvas manager
- State persists when switching tabs

**Event Flow**:
```
User clicks [E] button
  └─> EditPaletteLoader.toggle_tools()
      └─> EditToolsLoader.show() or hide()

User clicks [P] button
  └─> EditToolsLoader._on_place_clicked()
      └─> EditToolsLoader.set_tool('place')
          └─> Emit 'tool-changed' signal
              └─> ModelCanvasLoader._on_tool_changed()
                  └─> ModelCanvasManager.set_tool('place')
```

### GTK3 Considerations

1. **GtkOverlay**: Used to layer palettes over canvas
2. **GtkRevealer**: For smooth show/hide animations
3. **GtkToggleButton**: For tool buttons with toggle behavior
4. **CSS**: For styling active/inactive states
5. **Signals**: Custom signals for tool change notifications

## Implementation Order

### Recommended Sequence:

1. **Create UI files first** (easier to iterate on XML)
   - Start with `edit_palette.ui`
   - Then `edit_tools_palette.ui`
   - Test loading in Glade

2. **Create loaders** (implement business logic)
   - Start with `edit_tools_loader.py` (simpler)
   - Then `edit_palette_loader.py`
   - Test independently before integration

3. **Integrate into canvas**
   - Modify `model_canvas_loader.py`
   - Add GtkOverlay structure
   - Connect signals

4. **Add state management**
   - Update `model_canvas_manager.py`
   - Add tool properties and methods

5. **Implement canvas interaction**
   - Modify click handlers
   - Add tool-specific actions

6. **Polish and test**
   - Add visual feedback
   - Test all scenarios
   - Fix positioning issues

7. **Document**
   - Write user guide
   - Write developer guide

## Success Criteria

- [ ] Edit palette visible on canvas
- [ ] [E] button toggles tools palette smoothly
- [ ] Tools palette shows [P], [T], [A] buttons
- [ ] Only one tool can be active at a time
- [ ] Active tool has clear visual indication
- [ ] Canvas responds to tool selection (future: actually create objects)
- [ ] Works across multiple tabs independently
- [ ] No performance impact on canvas rendering
- [ ] Clean, professional appearance
- [ ] Documented and tested

## Future Enhancements

1. **Keyboard Shortcuts**: E, P, T, A keys
2. **More Tools**: Delete, Select, Move tools
3. **Tool Properties**: Right-click for tool options
4. **Drag and Drop**: Drag tools from palette to canvas
5. **Undo/Redo**: Integration with tool actions
6. **Templates**: Pre-configured place/transition types
7. **Customization**: User-configurable palette layout

## Notes

- Keep palettes minimal and unobtrusive
- Follow existing code patterns (similar to zoom palette)
- Ensure GTK3 compatibility
- No debug prints (production code)
- Follow OOP principles
- Test thoroughly before committing

---

**Created**: October 2, 2025
**Status**: Planning Phase
**Priority**: High - Core editing functionality
