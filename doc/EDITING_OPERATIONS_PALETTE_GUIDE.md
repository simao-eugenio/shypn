# Editing Operations Palette - Quick Reference

## Location
- **Top-left corner** of the canvas
- Small button labeled **[O] Ops**

## How to Use

### Toggle the Palette
1. **Click** the [O] Ops button, OR
2. **Press [O]** on your keyboard

### When Revealed
The palette slides down showing these sections:

#### Selection Tools
- **[S] Select** - Rectangle selection
- **[L] Lasso** - Freeform lasso selection

#### History
- **[U] Undo** - Undo last operation (Ctrl+Z)
- **[R] Redo** - Redo operation (Ctrl+Y)

#### Object Operations
- **[D] Duplicate** - Duplicate selected objects
- **[G] Group** - Group selected objects
- **[A] Align** - Align selected objects

#### Clipboard
- **[X] Cut** - Cut to clipboard (Ctrl+X)
- **[C] Copy** - Copy to clipboard (Ctrl+C)
- **[V] Paste** - Paste from clipboard (Ctrl+V)

## Troubleshooting

### If you don't see the [O] Ops button:
1. Make sure you're in **Edit mode** (not Simulate mode)
2. Check the **top-left corner** of the canvas area
3. It should appear as a small button next to or above the zoom controls

### If pressing [O] doesn't work:
1. Make sure the canvas has focus (click on it first)
2. Try clicking the [O] Ops button with your mouse instead

### If the palette doesn't reveal when clicked:
1. Check if the button changes visual state when clicked (toggle on/off)
2. The revealer animation takes 250ms to slide down
3. Try pressing [O] again to toggle it

## Architecture Notes

The editing operations palette is managed by:
- **CanvasOverlayManager** - Creates and positions the palette
- **EditingOperationsPaletteLoader** - Loads the UI from .ui file
- **EditingOperationsPalette** - Manages state and behavior
- **EditOperations** - Executes the actual operations (currently stubs)
- **LassoSelector** - Handles lasso selection logic

This follows proper OOP with separation of concerns.
