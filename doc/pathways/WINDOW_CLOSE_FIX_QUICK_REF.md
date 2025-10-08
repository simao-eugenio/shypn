# Quick Reference: Window Close Fix

## The Problem
```
User clicks X → Segmentation fault (Exit Code 139)
```

## The Solution
```python
# In pathway_panel_loader.py

# 1. Connect handler (in load() method)
self.window.connect('delete-event', self._on_delete_event)

# 2. Implement handler
def _on_delete_event(self, window, event):
    """Hide window instead of destroying it."""
    self.hide()
    
    # Update float button
    if self.float_button and self.float_button.get_active():
        self._updating_button = True
        self.float_button.set_active(False)
        self._updating_button = False
    
    # Dock back
    if self.parent_container:
        self.attach_to(self.parent_container, self.parent_window)
    
    # Prevent destruction
    return True
```

## Why It Works
| Before | After |
|--------|-------|
| GTK destroys window | Handler intercepts signal |
| Invalid memory access | Window hidden, not destroyed |
| Segmentation fault | Clean closure ✅ |

## Testing
```bash
# Automated test
python3 test_window_close_fix.py

# Manual test
python3 src/shypn.py
# 1. Click "Pathways"
# 2. Click float (⇲)
# 3. Click X
# 4. ✅ No crash!
```

## Key Insight
> **Always handle `delete-event` for reusable GTK windows**
> 
> Return `True` to prevent default destruction behavior

## References
- Full documentation: `doc/KEGG/WINDOW_CLOSE_FIX.md`
- Integration guide: `doc/KEGG/PANEL_INTEGRATION_GUIDE.md`
- Code: `src/shypn/helpers/pathway_panel_loader.py` (lines ~93, ~148-175)
