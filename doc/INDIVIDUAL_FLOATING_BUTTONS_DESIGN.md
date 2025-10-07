# Individual Floating Buttons Architecture

## Concept
Instead of having buttons in a container (box), each button is added as a separate overlay widget with its own positioning properties.

## Benefits
- **True floating**: No container constraints
- **Individual control**: Each button positions independently
- **No negative width issues**: No box allocation problems
- **Flexible layout**: Can position buttons anywhere
- **No GTK warnings**: Each button manages its own size

## Architecture

### Current (Container-based)
```
Revealer
  └─> Box (container causing issues)
       ├─> Button [P]
       ├─> Button [T]
       ├─> Button [A]
       └─> ...
```

### New (Individual Floating)
```
Overlay Widget
  ├─> Button [P] (floating, halign, valign)
  ├─> Button [T] (floating, halign, valign)
  ├─> Button [A] (floating, halign, valign)
  ├─> Button [S] (floating, halign, valign)
  ├─> Button [L] (floating, halign, valign)
  ├─> Button [U] (floating, halign, valign)
  └─> Button [R] (floating, halign, valign)
```

## Implementation Strategy

### Option 1: Individual UI Files
- Create separate `.ui` file for each button
- Load each independently
- Add each as separate overlay

### Option 2: Programmatic Creation
- Create buttons in Python code
- No UI files needed
- Direct GTK widget creation
- Set properties programmatically

### Option 3: Multi-root UI File
- One UI file with multiple root objects
- Each button is a root object
- Load all, add each as overlay

## Positioning Strategy

### Layout Pattern: `[P][T][A] GAP [S][L] GAP [U][R]`

**Bottom Center Reference Point:**
- Base Y: `margin_bottom = 78` (above [E] button)
- Center X: `halign = center`

**Horizontal Offsets (from center):**
```
         [P]  [T]  [A]    [S]  [L]    [U]  [R]
Offset:  -180 -140 -100   -40  0      +60  +100
```

Each button:
- `valign = end`
- `margin_bottom = 78`
- `halign = center`
- `margin_start` or `margin_end` for horizontal positioning

## Recommended: Option 2 (Programmatic)

Create all buttons in Python, no UI file needed:

```python
class IndividualFloatingButtonsManager:
    def __init__(self):
        self.buttons = {}
        
    def create_button(self, label, tooltip, x_offset, callback):
        btn = Gtk.Button(label=label)
        btn.set_tooltip_text(tooltip)
        btn.set_size_request(40, 40)
        btn.set_halign(Gtk.Align.CENTER)
        btn.set_valign(Gtk.Align.END)
        btn.set_margin_bottom(78)
        
        if x_offset < 0:
            btn.set_margin_end(-x_offset)
        else:
            btn.set_margin_start(x_offset)
        
        btn.connect('clicked', callback)
        return btn
    
    def create_all_buttons(self):
        # [P] Place
        self.buttons['place'] = self.create_button(
            'P', 'Place Tool', -180, self._on_place_clicked
        )
        
        # [T] Transition
        self.buttons['transition'] = self.create_button(
            'T', 'Transition Tool', -140, self._on_transition_clicked
        )
        
        # [A] Arc
        self.buttons['arc'] = self.create_button(
            'A', 'Arc Tool', -100, self._on_arc_clicked
        )
        
        # [S] Select
        self.buttons['select'] = self.create_button(
            'S', 'Select Tool', -40, self._on_select_clicked
        )
        
        # [L] Lasso
        self.buttons['lasso'] = self.create_button(
            'L', 'Lasso Selection', 0, self._on_lasso_clicked
        )
        
        # [U] Undo
        self.buttons['undo'] = self.create_button(
            'U', 'Undo', 60, self._on_undo_clicked
        )
        
        # [R] Redo
        self.buttons['redo'] = self.create_button(
            'R', 'Redo', 100, self._on_redo_clicked
        )
```

## Visibility Control

All buttons hidden by default, revealed together:

```python
def show_all_buttons(self):
    for btn in self.buttons.values():
        btn.show()

def hide_all_buttons(self):
    for btn in self.buttons.values():
        btn.hide()
```

## Integration with [E] Button

The [E] button toggle handler:

```python
def _on_edit_toggled(self, is_active):
    if is_active:
        self.floating_buttons_manager.show_all_buttons()
    else:
        self.floating_buttons_manager.hide_all_buttons()
```

## Next Steps

1. Create `IndividualFloatingButtonsManager` class
2. Implement button creation and positioning
3. Wire to overlay manager
4. Connect to [E] button toggle
5. Test floating behavior

---

**Status**: Architecture defined  
**Ready for**: Implementation
