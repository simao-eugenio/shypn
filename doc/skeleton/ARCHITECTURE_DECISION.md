# Architecture Decision Summary

**Date**: October 22, 2025  
**Status**: ✅ **PRINCIPLE VALIDATED**

---

## The Answer to Your Questions

### Q1: What is the main window?
**A**: The main window is a **HANGER** (empty GtkApplicationWindow container)
- It doesn't own widgets
- It provides "slots" where things can be hanged
- It's just the frame/structure

### Q2: What are panels?
**A**: Panels are **independent GtkWindow instances** that can be:
- Floating as independent windows
- "Hanged" on the main window (content reparented)
- Detached and returned to floating state

### Q3: What is Master Palette?
**A**: Master Palette should be a **native Gtk.Box widget** (Mode 2 ⭐)
- NOT an independent window
- Just a toolbar widget packed in main window
- Always visible (logical for main controls)
- Simpler than making it a window

### Q4: Is this structure Wayland-free?
**A**: ✅ **YES! ALL TESTS PASS WITHOUT Error 71**

---

## Architecture Diagram (Recommended: Mode 2)

```
┌─────────────────────────────────────────────────────────────────┐
│ Main Window (GtkApplicationWindow) = THE HANGER                │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │                        HEADER BAR                           │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│ ┌───────┬───────────────────────────────────────────────────┐   │
│ │ MASTER│         CONTENT AREA (Paned)                      │   │
│ │ PALE  │ ┌──────────┬────────────────────┬──────────────┐  │   │
│ │ TTE   │ │  PANEL   │      CANVAS        │   PANEL      │  │   │
│ │       │ │  SLOT 1  │      (Drawing)     │   SLOT 2     │  │   │
│ │ [📁]  │ │          │                    │              │  │   │
│ │ Files │ │ ┌──────┐ │  ┌──────────────┐  │              │  │   │
│ │       │ │ │Files │ │  │              │  │              │  │   │
│ │ [🗺️]  │ │ │Panel │ │  │   Network    │  │              │  │   │
│ │ Path  │ │ │      │ │  │   Diagram    │  │              │  │   │
│ │       │ │ │      │ │  │              │  │              │  │   │
│ │ [📊]  │ │ └──────┘ │  └──────────────┘  │              │  │   │
│ │ Analy │ │          │                    │              │  │   │
│ │       │ │          │                    │              │  │   │
│ │ [🔷]  │ │          │                    │              │  │   │
│ │ Topo  │ │          │                    │              │  │   │
│ │       │ │          │                    │              │  │   │
│ └───────┘ └──────────┴────────────────────┴──────────────┘  │   │
│  Native    ↑                                                 │   │
│  Widget    Independent GtkWindow "hanged" here             │   │
│            (can detach and become floating window)          │   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Key Technical Points

### Master Palette (Native Widget)
```python
class MasterPalette:
    def __init__(self):
        self.widget = Gtk.Box()  # Just a widget, no window!
        # Add buttons to widget
    
    def get_widget(self):
        return self.widget  # Pack directly in main window
```

### Panel (Independent Window)
```python
class Panel:
    def __init__(self):
        self.window = Gtk.Window()  # Independent window
        self.content = Gtk.Box()    # The actual panel UI
        self.window.add(self.content)
    
    def attach_to(self, container):
        """Hang panel on main window."""
        self.window.hide()           # Hide independent window
        self.window.remove(self.content)  # Remove content
        container.pack_start(self.content, ...)  # Hang on container
    
    def detach(self):
        """Return to floating independent window."""
        container.remove(self.content)  # Un-hang from container
        self.window.add(self.content)   # Return to window
        self.window.show_all()          # Show as floating window
```

### Main Window (Hanger)
```python
class MainWindow(Gtk.ApplicationWindow):
    def __init__(self):
        super().__init__()
        
        # Create hanger structure
        main_box = Gtk.Box()
        
        # Add Master Palette (native widget)
        self.master_palette = MasterPalette()
        main_box.pack_start(self.master_palette.get_widget(), False, False, 0)
        
        # Add panel slots
        self.left_slot = Gtk.Box()
        main_box.pack_start(self.left_slot, False, False, 0)
        
        # Create panels (independent windows)
        self.files_panel = create_files_panel()
        
        # Wire Master Palette to panels
        self.master_palette.connect('files', self.on_files_clicked)
    
    def on_files_clicked(self, active):
        if active:
            self.files_panel.attach_to(self.left_slot)  # Hang it
        else:
            self.files_panel.hide()  # Hide it
```

---

## What Changed Our Understanding

### Before Testing
**We thought**:
- ❌ Separate windows + reparenting = Error 71
- ✅ Monolithic structure (everything embedded) = Safe

### After Testing
**We learned**:
- ✅ Separate windows + reparenting = NO Error 71 (works perfectly!)
- ❌ Monolithic GtkStack/GtkRevealer = CAUSES Error 71
- ✅ "Hanger" pattern (window.remove → container.pack) = Safe
- ✅ Both native widgets AND independent windows work as hanged items

---

## Test Results Summary

| Architecture | Wayland Error 71? | Recommendation |
|--------------|-------------------|----------------|
| **Mode 1**: Palette as window | ✅ NO ERROR | ⚠️ Works but unnecessary complexity |
| **Mode 2**: Palette as widget | ✅ NO ERROR | ⭐ **RECOMMENDED** (simplest) |
| **Mode 3**: Everything as windows | ✅ NO ERROR | ⚠️ Works but overkill |
| **Monolithic** (Phase 1-2) | ❌ ERROR 71 | ❌ **ABANDONED** |

---

## Implementation Next Steps

1. ✅ **Principle validated** (testing complete)
2. ⏭️ **Revert main_window.ui** to original structure
3. ⏭️ **Add Master Palette slot** (48px box in main_window.ui)
4. ⏭️ **Wire Master Palette signals** to existing panel loaders
5. ⏭️ **Test each panel** (Files → Pathways → Analyses → Topology)

**Estimated time**: 2-4 hours  
**Risk level**: LOW (reusing proven code)  
**Confidence**: HIGH (built on validated principle)

---

## Files

- **Test script**: `dev/test_architecture_principle.py`
- **Test results**: All 3 modes PASS without Error 71
- **Documentation**: 
  - `doc/refactor/ARCHITECTURE_PRINCIPLE_VALIDATED.md` (detailed)
  - `doc/refactor/ARCHITECTURE_DECISION.md` (this file - summary)
  - `doc/refactor/MONOLITHIC_REFACTOR_STATUS.md` (what failed and why)

---

## Conclusion

✅ **The "Hanger" architecture is the correct design.**

**Main window = Hanger (container)**  
**Master Palette = Native widget (toolbar)**  
**Panels = Independent windows (can be hanged)**

**This design is Wayland-safe and matches existing working code!**
