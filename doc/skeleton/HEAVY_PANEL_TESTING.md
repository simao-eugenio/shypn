# Heavy Panel Testing - Architecture Validation

**Date**: October 22, 2025  
**Status**: ✅ **TESTING COMPLETE - NO ERROR 71**

---

## Test Enhancement

Added **HEAVY STUFF** to panels to test real-world complexity:

### Heavy Panel Features

1. **FileChooserButton Widget**
   - Embedded file chooser in panel
   - Tests widget state during hang/detach cycles

2. **Dialog Operations**
   - Info Dialog (MessageDialog)
   - Question Dialog (MessageDialog with YES/NO)
   - File Open Dialog (FileChooserDialog OPEN)
   - File Save Dialog (FileChooserDialog SAVE)
   - Color Chooser Dialog (ColorChooserDialog)

3. **Main Hanger Interaction**
   - Send Message to Hanger
   - Trigger Action in Hanger (opens dialog from main window)
   - Get Info from Hanger (bidirectional communication)

4. **State Awareness**
   - Panel knows if it's HANGED or FLOATING
   - Dialogs use correct parent window (main window when hanged, panel window when floating)
   - State indicator updates on hang/detach

5. **Message Logging**
   - ScrolledWindow with TextView
   - Logs all operations
   - Shows state during each action

---

## Test Scenarios

### Scenario 1: Dialogs When Hanged
**Setup**: Panel attached to main window  
**Actions**: Click dialog buttons (Info, Question, File Open/Save, Color)  
**Expected**: Dialogs parent to main window, no Error 71  
**Result**: ✅ **PASS**

### Scenario 2: Dialogs When Floating
**Setup**: Panel detached as independent window  
**Actions**: Click dialog buttons  
**Expected**: Dialogs parent to panel window, no Error 71  
**Result**: ✅ **PASS**

### Scenario 3: Hang/Detach with FileChooserButton
**Setup**: FileChooserButton with selected file  
**Actions**: Hang panel → detach panel → hang again  
**Expected**: FileChooser state preserved, no Error 71  
**Result**: ✅ **PASS**

### Scenario 4: Main Hanger Interaction (Hanged)
**Setup**: Panel attached to main window  
**Actions**: 
- Send message to hanger → hanger receives and displays
- Trigger action → hanger opens its own dialog
- Get info → hanger provides data back to panel  
**Expected**: Bidirectional communication works  
**Result**: ✅ **PASS**

### Scenario 5: Main Hanger Interaction (Floating)
**Setup**: Panel floating as independent window  
**Actions**: Same as Scenario 4  
**Expected**: Communication still works (panel has main window reference)  
**Result**: ✅ **PASS**

### Scenario 6: Rapid Toggle with Heavy Widgets
**Setup**: Panel with all heavy widgets  
**Actions**: Rapid hang/detach cycle (10x)  
**Expected**: No Error 71, widgets remain functional  
**Result**: ✅ **PASS**

---

## Critical Code Pattern: Dynamic Parent Window

```python
def _get_parent_window(self):
    """Get the appropriate parent window for dialogs."""
    if self.is_hanged and self.main_window:
        return self.main_window  # Use main window when hanged
    else:
        return self.window  # Use panel window when floating

def _on_open_dialog(self, button):
    """Open a dialog with correct parent."""
    parent = self._get_parent_window()  # Dynamic parent selection
    
    dialog = Gtk.MessageDialog(
        transient_for=parent,  # Correct parent for current state
        ...
    )
    dialog.run()
    dialog.destroy()
```

**Why this matters**:
- Dialogs need correct parent for proper modal behavior
- Wrong parent can cause Wayland protocol errors
- Dynamic selection based on `is_hanged` state ensures correctness

---

## Main Hanger API

The hanger provides these methods for panels:

```python
# In TestWindow (main hanger)

def receive_message_from_panel(self, panel_name, message):
    """Receive and display messages from panels."""
    self.panel_messages.append(f"{panel_name}: {message}")
    self._update_hanger_messages()

def panel_triggered_action(self, panel_name):
    """Execute action triggered by panel."""
    # Can open dialog, update state, etc.
    dialog = Gtk.MessageDialog(
        transient_for=self,  # Hanger is parent
        text=f"Action triggered by {panel_name}"
    )
    dialog.run()
    dialog.destroy()

def get_info_for_panel(self, panel_name):
    """Provide information to requesting panel."""
    return {
        "hanger_title": self.get_title(),
        "hanger_size": self.get_size(),
        "total_panels": ...,
        ...
    }
```

**Usage in Panel**:
```python
# Panel can call hanger methods in both states
self.main_window.receive_message_from_panel(self.name, "Hello!")
self.main_window.panel_triggered_action(self.name)
info = self.main_window.get_info_for_panel(self.name)
```

---

## Widget State Preservation

**Tested widgets maintain state across hang/detach cycles**:

✅ **FileChooserButton**:
- Selected file preserved
- No widget realization issues

✅ **TextBuffer/TextView**:
- Message history preserved
- Scrolled position maintained

✅ **Button states**:
- Sensitivity preserved
- Connections remain active

✅ **Container hierarchy**:
- Child widgets remain connected
- Parent relationships update correctly

---

## Wayland Compatibility Results

| Operation | Hanged State | Floating State | Error 71? |
|-----------|--------------|----------------|-----------|
| Open Info Dialog | ✅ Works | ✅ Works | ❌ NO |
| Open Question Dialog | ✅ Works | ✅ Works | ❌ NO |
| Open File Dialog | ✅ Works | ✅ Works | ❌ NO |
| Save File Dialog | ✅ Works | ✅ Works | ❌ NO |
| Color Chooser | ✅ Works | ✅ Works | ❌ NO |
| FileChooserButton | ✅ Works | ✅ Works | ❌ NO |
| Send Message | ✅ Works | ✅ Works | ❌ NO |
| Trigger Action | ✅ Works | ✅ Works | ❌ NO |
| Get Info | ✅ Works | ✅ Works | ❌ NO |
| Rapid Toggle (10x) | ✅ Works | N/A | ❌ NO |

**ALL TESTS PASS WITHOUT WAYLAND ERROR 71!**

---

## Key Findings

### ✅ What Works

1. **Complex widgets in hanged panels** - FileChooserButton, ScrolledWindow, TextView
2. **Modal dialogs with dynamic parent** - All dialog types work correctly
3. **Bidirectional communication** - Panel ↔ Hanger interaction stable
4. **State preservation** - Widgets maintain state across hang/detach
5. **Rapid operations** - Fast toggle cycles don't cause errors

### ✅ Architecture Validation

The "hanger" pattern works with:
- **Heavy UI widgets** (FileChoosers, ScrolledWindows)
- **Modal dialogs** (correct parent selection)
- **Inter-window communication** (panel ↔ hanger)
- **Rapid state changes** (stress testing)
- **Complex widget hierarchies** (nested containers)

### 🎯 Critical Success Factors

1. **Dynamic parent window selection** for dialogs based on hang state
2. **Preserving main window reference** in panel even when floating
3. **Proper container operations** (remove/pack_start, not destroy)
4. **State tracking** (is_hanged flag) for conditional behavior

---

## Test Files

**Main test**: `dev/test_architecture_principle.py`

**Run tests**:
```bash
# Mode 1: Palette as window + Heavy panel
./dev/test_architecture_principle.py 1

# Mode 2: Palette as widget + Heavy panel (RECOMMENDED)
./dev/test_architecture_principle.py 2

# Mode 3: Everything as windows + Heavy panel
./dev/test_architecture_principle.py 3
```

**Interactive testing**:
1. Launch test
2. Panel auto-hangs after 1 second
3. Click dialog buttons to test modal dialogs
4. Click "Send Message" to test hanger communication
5. Click "Detach Files Panel" to float panel
6. Repeat dialog tests in floating state
7. Click "Hang Files Panel" to re-attach
8. Click "⚡ Rapid Test" for stress testing

---

## Comparison: Simple vs Heavy Panel

| Feature | Simple Panel | Heavy Panel |
|---------|--------------|-------------|
| Widget Count | 2-3 | 15+ |
| Dialog Operations | None | 5 types |
| Hanger Communication | None | 3 methods |
| State Tracking | Basic | Detailed |
| Message Logging | None | Full log |
| FileChoosers | None | 2 types |
| Wayland Error 71 | ❌ NO | ❌ NO |

**Both pass all tests!** Heavy panel proves the architecture scales to real-world complexity.

---

## Conclusion

✅ **The "hanger" architecture is PRODUCTION-READY**

**It handles**:
- Complex widget hierarchies
- Modal dialogs with proper parenting
- Bidirectional panel ↔ hanger communication
- Rapid hang/detach operations
- Real-world UI complexity (FileChoosers, TextViews, etc.)

**No Wayland Error 71 in any scenario!**

**Recommendation**: Proceed with Mode 2 (Master Palette as native widget) for production implementation.

---

## Next Steps for Production

1. ✅ Architecture validated with heavy testing
2. ⏭️ Implement Mode 2 in main application
3. ⏭️ Wire Master Palette signals to real panel loaders
4. ⏭️ Add persistent state (remember which panels were hanged)
5. ⏭️ Add panel-specific hanger communication APIs
6. ⏭️ Test with real application data and operations

**Risk**: LOW - Heavy testing proves architecture is sound  
**Confidence**: HIGH - All scenarios pass without errors
