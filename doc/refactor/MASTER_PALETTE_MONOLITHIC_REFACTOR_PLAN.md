# Master Palette Monolithic UI Refactor Plan

**Date**: October 21, 2025  
**Status**: Planning Phase  
**Objective**: Implement Master Palette with all panels embedded in main window (no floating windows)  
**Wayland Compatibility**: Zero Error 71 risk

---

## Executive Summary

This plan outlines the refactoring of Shypn's UI to use a **single monolithic `main_window.ui`** file with all panels embedded. The Master Palette (54px vertical toolbar) controls panel visibility through GtkRevealer animations and GtkStack switching. All panels dock exclusively on the LEFT side of the workspace.

### Key Goals
- ✅ Restore Master Palette as primary panel control
- ✅ Embed all panels directly in main window
- ✅ Eliminate widget reparenting (Wayland Error 71)
- ✅ Smooth slide-in/slide-out animations
- ✅ Exclusive panel behavior (one visible at a time)
- ❌ No floating windows (acceptable trade-off)

---

## Architecture Overview

### Visual Layout

```
┌─────────────────────────────────────────────────────────────┐
│ HeaderBar: Shypn                          [_] [□] [×]        │
├──┬──────────────────────────────────────────────────────────┤
│  │                                                           │
│M │  ┌─────────────────┐                                     │
│a │  │                 │                                     │
│s │  │  Files Panel    │      Main Workspace                │
│t │  │  (or other)     │      (Canvas Area)                 │
│e │  │                 │                                     │
│r │  │                 │                                     │
│  │  │                 │                                     │
│P │  │                 │                                     │
│a │  │                 │                                     │
│l │  └─────────────────┘                                     │
│e │   (reveals/hides)                                        │
│t │                                                           │
│t │                                                           │
│e │                                                           │
└──┴───────────────────────────────────────────────────────────┘
│54px│    300-400px     │         Remaining Space            │
      (adjustable per panel)
```

### Component Hierarchy

```
GtkApplicationWindow (main_window)
├── GtkHeaderBar
│   ├── GtkLabel (title: "Shypn")
│   ├── GtkButton (minimize)
│   ├── GtkButton (maximize)
│   └── Close button (implicit)
│
├── GtkBox (root_container, horizontal)
│   ├── GtkBox (master_palette_slot, 54px width)
│   │   └── MasterPalette widget (inserted programmatically)
│   │       ├── Files button
│   │       ├── Analyses button
│   │       ├── Pathways button
│   │       └── Topology button
│   │
│   └── GtkBox (content_with_statusbar, vertical)
│       ├── GtkPaned (left_paned, horizontal)
│       │   ├── GtkRevealer (panels_revealer, slide-right)
│       │   │   └── GtkStack (panels_stack, no transition)
│       │   │       ├── GtkBox (name="files")
│       │   │       │   ├── GtkBox (file_explorer_container)
│       │   │       │   └── GtkBox (project_controls_container)
│       │   │       │
│       │   │       ├── GtkBox (name="analyses")
│       │   │       │   └── GtkNotebook (plots_notebook)
│       │   │       │       ├── Time Series tab
│       │   │       │       ├── Histogram tab
│       │   │       │       ├── Scatter Plot tab
│       │   │       │       └── Phase Plot tab
│       │   │       │
│       │   │       ├── GtkBox (name="pathways")
│       │   │       │   └── GtkNotebook (import_notebook)
│       │   │       │       ├── KEGG Import tab
│       │   │       │       └── SBML Import tab
│       │   │       │
│       │   │       └── GtkBox (name="topology")
│       │   │           └── GtkBox (topology_container)
│       │   │               └── Topology analysis widgets
│       │   │
│       │   └── GtkBox (main_workspace)
│       │       └── GtkNotebook (canvas_notebook, inserted programmatically)
│       │
│       └── GtkStatusbar (status_bar)
```

---

## Technical Specifications

### GtkRevealer Configuration

```xml
<object class="GtkRevealer" id="panels_revealer">
  <property name="visible">True</property>
  <property name="transition-type">slide-right</property>
  <property name="transition-duration">250</property>
  <property name="reveal-child">False</property>
  <property name="vexpand">True</property>
  <property name="hexpand">False</property>
</object>
```

**Behavior**:
- Starts hidden (`reveal-child=False`)
- Slides from left to right (250ms animation)
- Width determined by active panel in stack

### GtkStack Configuration

```xml
<object class="GtkStack" id="panels_stack">
  <property name="visible">True</property>
  <property name="transition-type">none</property>
  <property name="vexpand">True</property>
  <property name="hexpand">True</property>
  <property name="homogeneous">False</property>
</object>
```

**Behavior**:
- Instant switching between panels (no cross-fade)
- Each panel can have different width
- Only one child visible at a time

### GtkPaned Configuration

```xml
<object class="GtkPaned" id="left_paned">
  <property name="orientation">horizontal</property>
  <property name="position">0</property>
  <property name="visible">True</property>
  <property name="can-focus">True</property>
  <property name="vexpand">True</property>
</object>
```

**Behavior**:
- Position=0: Panel hidden
- Position=300-400: Panel visible (width varies by panel type)
- User can resize with mouse when visible

---

## Panel Specifications

### Files Panel (300px)
**Content**:
- File explorer tree view
- Project controls (New, Open, Save)
- Recent files list

**Controllers Needed**:
- FileExplorerPanel
- ProjectActionsController
- PersistencyManager

### Analyses Panel (350px)
**Content**:
- GtkNotebook with 4 tabs
- Time Series plotting
- Histogram plotting
- Scatter plot plotting
- Phase plot plotting

**Controllers Needed**:
- TimeSeriesController
- HistogramController
- ScatterPlotController
- PhasePlotController

### Pathways Panel (320px)
**Content**:
- GtkNotebook with 2 tabs
- KEGG pathway import interface
- SBML file import interface

**Controllers Needed**:
- KEGGImportController
- SBMLImportController

### Topology Panel (400px)
**Content**:
- Topology analysis interface
- Network visualization controls
- Analysis results display

**Controllers Needed**:
- TopologyPanelController

---

## Implementation Phases

### Phase 1: Main Window UI Rebuild (90 minutes)

**Objective**: Create clean `main_window.ui` structure

**Tasks**:
1. Backup current `ui/main/main_window.ui`
2. Remove HeaderBar toggle buttons (keep only window controls)
3. Create root container structure:
   - Master Palette slot (54px)
   - Content area with paned layout
4. Add GtkRevealer with slide-right transition
5. Add GtkStack for panel switching
6. Create placeholder containers for each panel
7. Wire up Master Palette slot
8. Add status bar at bottom

**Files Modified**:
- `ui/main/main_window.ui`

**Testing**:
- Load UI, verify structure
- Check that Master Palette slot exists
- Verify revealer and stack are accessible

---

### Phase 2: Panel Content Migration (90 minutes)

**Objective**: Move panel content from separate UI files into main_window.ui

#### 2.1: Files Panel (25 min)
**Source**: `ui/panels/left_panel.ui`

**Extract**:
- File explorer GtkTreeView
- Project controls toolbar
- Recent files section

**Integrate**:
- Place in `panels_stack` with name="files"
- Maintain widget IDs for controller access
- Test file operations still work

#### 2.2: Analyses Panel (25 min)
**Source**: `ui/panels/right_panel.ui`

**Extract**:
- GtkNotebook with 4 tabs
- Plot configuration widgets
- Plot display areas

**Integrate**:
- Place in `panels_stack` with name="analyses"
- Wire plotting controllers
- Test plot generation

#### 2.3: Pathways Panel (20 min)
**Source**: `ui/panels/pathway_panel.ui`

**Extract**:
- GtkNotebook with KEGG/SBML tabs
- Import forms
- Progress indicators

**Integrate**:
- Place in `panels_stack` with name="pathways"
- Wire import controllers
- Test KEGG/SBML import

#### 2.4: Topology Panel (20 min)
**Source**: `ui/panels/topology_panel.ui`

**Extract**:
- Topology analysis interface
- Result display widgets

**Integrate**:
- Place in `panels_stack` with name="topology"
- Wire topology controller
- Test analysis functions

**Files Modified**:
- `ui/main/main_window.ui` (all panels integrated)

**Files Deprecated** (keep for reference):
- `ui/panels/left_panel.ui`
- `ui/panels/right_panel.ui`
- `ui/panels/pathway_panel.ui`
- `ui/panels/topology_panel.ui`

---

### Phase 3: Master Palette Integration (30 minutes)

**Objective**: Wire Master Palette to control panel visibility

#### 3.1: Restore Master Palette Creation (10 min)

**File**: `src/shypn.py`

```python
# Create Master Palette (already exists in codebase)
from shypn.ui import MasterPalette

master_palette = MasterPalette()
master_palette_slot = main_builder.get_object('master_palette_slot')
master_palette_slot.pack_start(master_palette.get_widget(), True, True, 0)
```

#### 3.2: Get UI References (5 min)

```python
# Get main window widgets
panels_revealer = main_builder.get_object('panels_revealer')
panels_stack = main_builder.get_object('panels_stack')
left_paned = main_builder.get_object('left_paned')
```

#### 3.3: Wire Toggle Handlers (15 min)

```python
def on_files_toggle(is_active):
    """Handle Files button toggle from Master Palette."""
    if is_active:
        # Switch stack to Files page
        panels_stack.set_visible_child_name('files')
        # Show revealer with animation
        panels_revealer.set_reveal_child(True)
        # Adjust paned to Files width
        left_paned.set_position(300)
    else:
        # Hide revealer with animation
        panels_revealer.set_reveal_child(False)
        # Collapse paned
        left_paned.set_position(0)

def on_analyses_toggle(is_active):
    """Handle Analyses button toggle from Master Palette."""
    if is_active:
        panels_stack.set_visible_child_name('analyses')
        panels_revealer.set_reveal_child(True)
        left_paned.set_position(350)
    else:
        panels_revealer.set_reveal_child(False)
        left_paned.set_position(0)

def on_pathways_toggle(is_active):
    """Handle Pathways button toggle from Master Palette."""
    if is_active:
        panels_stack.set_visible_child_name('pathways')
        panels_revealer.set_reveal_child(True)
        left_paned.set_position(320)
    else:
        panels_revealer.set_reveal_child(False)
        left_paned.set_position(0)

def on_topology_toggle(is_active):
    """Handle Topology button toggle from Master Palette."""
    if is_active:
        panels_stack.set_visible_child_name('topology')
        panels_revealer.set_reveal_child(True)
        left_paned.set_position(400)
    else:
        panels_revealer.set_reveal_child(False)
        left_paned.set_position(0)

# Connect Master Palette signals
master_palette.connect('files', on_files_toggle)
master_palette.connect('analyses', on_analyses_toggle)
master_palette.connect('pathways', on_pathways_toggle)
master_palette.connect('topology', on_topology_toggle)
```

**Files Modified**:
- `src/shypn.py`

---

### Phase 4: Controller Integration (60 minutes)

**Objective**: Wire controllers to embedded panels

#### 4.1: Files Panel Controllers (20 min)

```python
# Get Files panel widgets from builder
file_explorer_container = main_builder.get_object('file_explorer_container')
project_controls_container = main_builder.get_object('project_controls_container')

# Create FileExplorerPanel
from shypn.helpers.file_explorer import FileExplorerPanel
file_explorer = FileExplorerPanel(main_builder, base_path=models_dir)
file_explorer.set_parent_window(window)

# Create ProjectActionsController
from shypn.helpers.project_actions import ProjectActionsController
project_controller = ProjectActionsController(main_builder, parent_window=window)

# Wire file operations to canvas
file_explorer.on_file_open_requested = lambda path: open_file(path)
```

#### 4.2: Analyses Panel Controllers (15 min)

```python
# Get Analyses panel widgets
plots_notebook = main_builder.get_object('plots_notebook')

# Create plotting controllers (already exist in codebase)
from shypn.helpers.plotting import (
    TimeSeriesController,
    HistogramController,
    ScatterPlotController,
    PhasePlotController
)

time_series_ctrl = TimeSeriesController(main_builder)
histogram_ctrl = HistogramController(main_builder)
scatter_ctrl = ScatterPlotController(main_builder)
phase_ctrl = PhasePlotController(main_builder)
```

#### 4.3: Pathways Panel Controllers (15 min)

```python
# Get Pathways panel widgets
import_notebook = main_builder.get_object('import_notebook')

# Create import controllers
from shypn.helpers.kegg_import import KEGGImportController
from shypn.helpers.sbml_import import SBMLImportController

kegg_ctrl = KEGGImportController(main_builder, model_canvas=model_canvas_loader)
sbml_ctrl = SBMLImportController(main_builder, model_canvas=model_canvas_loader)
sbml_ctrl.set_parent_window(window)
```

#### 4.4: Topology Panel Controllers (10 min)

```python
# Get Topology panel widgets
topology_container = main_builder.get_object('topology_container')

# Create topology controller
from shypn.helpers.topology_panel_loader import TopologyPanelController
topology_ctrl = TopologyPanelController(main_builder, model=None)
topology_ctrl.model_canvas_loader = model_canvas_loader
```

**Files Modified**:
- `src/shypn.py`

---

### Phase 5: Startup State Configuration (15 minutes)

**Objective**: Set proper initial state

```python
# Hide all panels at startup
panels_revealer.set_reveal_child(False)
left_paned.set_position(0)

# Optional: Show Analyses panel at startup
def show_default_panel():
    """Show Analyses panel after window is mapped."""
    master_palette.set_active('analyses', True)
    return False  # Don't repeat

GLib.idle_add(show_default_panel)
```

**Files Modified**:
- `src/shypn.py`

---

### Phase 6: Cleanup Deprecated Code (30 minutes)

**Objective**: Remove old panel loader infrastructure

**Files to Deprecate** (move to `archive/` or delete):
- `src/shypn/helpers/left_panel_loader.py`
- `src/shypn/helpers/right_panel_loader.py`
- `src/shypn/helpers/pathway_panel_loader.py`
- `src/shypn/helpers/topology_panel_loader.py` (keep controller class)

**Code to Remove from `src/shypn.py`**:
- All `create_left_panel()` calls
- All `create_right_panel()` calls
- All `attach_to()` / `detach()` logic
- All `on_float_callback` / `on_attach_callback` setup
- All transient window configuration code
- All `_on_float_toggled` handlers

**Files to Keep**:
- Controller classes (FileExplorerPanel, ProjectActionsController, etc.)
- Master Palette implementation
- Plotting controllers
- Import controllers

---

## Testing Plan

### Unit Tests

1. **UI Loading**
   - ✅ `main_window.ui` loads without errors
   - ✅ All widget IDs are accessible
   - ✅ Master Palette slot exists

2. **Master Palette**
   - ✅ All 4 buttons are clickable
   - ✅ Exclusive toggle behavior works
   - ✅ Signal emission works

3. **Panel Switching**
   - ✅ Stack switches to correct page
   - ✅ Revealer animates smoothly
   - ✅ Paned adjusts to correct width

### Integration Tests

1. **Files Panel**
   - ✅ File tree loads
   - ✅ Files can be opened
   - ✅ Project operations work
   - ✅ FileChooserDialog doesn't cause Error 71

2. **Analyses Panel**
   - ✅ All plot tabs accessible
   - ✅ Plots can be generated
   - ✅ Data updates correctly

3. **Pathways Panel**
   - ✅ KEGG import works
   - ✅ SBML import works
   - ✅ Progress indicators work

4. **Topology Panel**
   - ✅ Analysis can be run
   - ✅ Results display correctly

### Wayland Compatibility Tests

1. **No Error 71**
   - ✅ Switch between all panels rapidly
   - ✅ Open/close panels repeatedly
   - ✅ Open FileChooserDialogs
   - ✅ Resize window while panel visible
   - ✅ Maximize/unmaximize window

2. **Performance**
   - ✅ Revealer animation is smooth
   - ✅ Stack switching is instant
   - ✅ No lag when toggling panels

---

## Risk Assessment

### Low Risk ✅
- UI structure changes (reversible with git)
- Master Palette re-integration (already exists)
- Revealer animations (standard GTK)

### Medium Risk ⚠️
- Panel content migration (requires careful testing)
- Controller rewiring (need to verify all connections)
- Widget ID conflicts (may need renaming)

### Mitigation Strategies
1. **Incremental Implementation**: Complete one phase fully before starting next
2. **Git Branching**: Create feature branch for refactor
3. **Backup**: Keep old UI files in `archive/` folder
4. **Testing**: Test each panel independently after migration

---

## Rollback Plan

If refactor fails or introduces critical bugs:

1. **Immediate Rollback**:
   ```bash
   git checkout main
   git branch -D monolithic-ui-refactor
   ```

2. **Partial Rollback**:
   - Restore `main_window.ui` from git history
   - Restore panel loader files
   - Remove embedded panel content

3. **Safe State**: Tagged version `v2.2.0-wayland-fix` remains available

---

## Benefits vs. Trade-offs

### Benefits ✅
| Benefit | Impact |
|---------|--------|
| No Error 71 | Critical - prevents crashes |
| Simpler architecture | Easier maintenance |
| Single UI file | Centralized structure |
| Smooth animations | Better UX |
| Master Palette control | Unified interface |
| Less code complexity | Fewer bugs |

### Trade-offs ❌
| Trade-off | Impact |
|-----------|--------|
| No floating windows | Users can't undock panels |
| Larger UI file | More complex XML |
| All panels left side | Less flexible layout |
| One panel at a time | Can't see multiple panels |

### Overall Assessment
**Benefits strongly outweigh trade-offs** for a stable, crash-free Wayland experience.

---

## Post-Implementation Tasks

1. **Documentation**
   - Update user manual with Master Palette usage
   - Document new architecture for developers
   - Create GIF demos of panel animations

2. **Performance Optimization**
   - Profile panel switching speed
   - Optimize revealer animation duration
   - Test with large models

3. **Future Enhancements**
   - Add panel width persistence (save user preferences)
   - Add keyboard shortcuts for panel switching
   - Consider adding panel preview on hover

---

## Timeline Summary

| Phase | Duration | Dependencies |
|-------|----------|--------------|
| 1. UI Rebuild | 90 min | None |
| 2. Content Migration | 90 min | Phase 1 |
| 3. Master Palette | 30 min | Phase 1 |
| 4. Controllers | 60 min | Phase 2 |
| 5. Startup Config | 15 min | Phase 3, 4 |
| 6. Cleanup | 30 min | Phase 5 |
| **Total** | **5 hours** | - |

**Recommended Schedule**: 
- Day 1: Phases 1-2 (3 hours)
- Day 2: Phases 3-5 (1.75 hours)
- Day 3: Phase 6 + testing (1.5 hours)

---

## Success Criteria

### Must Have ✅
1. ✅ All panels accessible via Master Palette
2. ✅ No Wayland Error 71 crashes
3. ✅ Smooth revealer animations
4. ✅ All existing functionality preserved
5. ✅ FileChooserDialogs work correctly

### Nice to Have 🎯
1. Configurable panel widths
2. Remember last active panel
3. Keyboard shortcuts
4. Panel preview on hover

### Success Metrics
- **Zero Error 71 crashes** in 1 hour of continuous use
- **<300ms** panel switching time
- **All unit tests passing**
- **All integration tests passing**

---

## Conclusion

This monolithic UI refactor represents the **correct architectural approach** for Master Palette on Wayland. By embedding all panels in a single window and using GTK's standard reveal/stack mechanisms, we eliminate the root cause of Error 71 while maintaining a clean, professional UI.

The trade-off of losing floating windows is acceptable given the stability and simplicity gains. Future enhancements can be added incrementally without compromising the core architecture.

**Recommendation**: Proceed with implementation following this plan.

---

## Appendix A: Code Snippets

### Complete Toggle Handler Template

```python
def create_panel_toggle_handler(panel_name, panel_width):
    """Factory function to create panel toggle handlers.
    
    Args:
        panel_name: Name of the stack child (e.g., 'files', 'analyses')
        panel_width: Width in pixels when panel is revealed
        
    Returns:
        Toggle handler function
    """
    def on_toggle(is_active):
        if is_active:
            # Show panel
            panels_stack.set_visible_child_name(panel_name)
            panels_revealer.set_reveal_child(True)
            left_paned.set_position(panel_width)
            print(f"[PANEL] {panel_name} revealed (width={panel_width})", file=sys.stderr)
        else:
            # Hide panel
            panels_revealer.set_reveal_child(False)
            left_paned.set_position(0)
            print(f"[PANEL] {panel_name} hidden", file=sys.stderr)
    
    return on_toggle

# Usage
on_files_toggle = create_panel_toggle_handler('files', 300)
on_analyses_toggle = create_panel_toggle_handler('analyses', 350)
on_pathways_toggle = create_panel_toggle_handler('pathways', 320)
on_topology_toggle = create_panel_toggle_handler('topology', 400)
```

### Panel Stack Page Template

```xml
<!-- Template for each panel in stack -->
<child>
  <object class="GtkBox" id="[PANEL_NAME]_panel">
    <property name="orientation">vertical</property>
    <property name="visible">True</property>
    <property name="vexpand">True</property>
    <property name="hexpand">True</property>
    <property name="margin">0</property>
    
    <!-- Panel-specific content goes here -->
    
  </object>
  <packing>
    <property name="name">[PANEL_NAME]</property>
  </packing>
</child>
```

---

## Appendix B: Widget ID Reference

### Main Window Widgets
- `main_window` - GtkApplicationWindow
- `header_bar` - GtkHeaderBar
- `root_container` - GtkBox (horizontal)
- `master_palette_slot` - GtkBox (vertical, 54px)
- `content_with_statusbar` - GtkBox (vertical)
- `left_paned` - GtkPaned (horizontal)
- `panels_revealer` - GtkRevealer
- `panels_stack` - GtkStack
- `main_workspace` - GtkBox
- `status_bar` - GtkStatusbar

### Panel Widgets (in stack)
- `files_panel` - GtkBox (stack child name="files")
- `analyses_panel` - GtkBox (stack child name="analyses")
- `pathways_panel` - GtkBox (stack child name="pathways")
- `topology_panel` - GtkBox (stack child name="topology")

### Controller Access Points
- `file_explorer_container` - Files panel content area
- `project_controls_container` - Files panel toolbar
- `plots_notebook` - Analyses panel notebook
- `import_notebook` - Pathways panel notebook
- `topology_container` - Topology panel content area

---

**Document Version**: 1.0  
**Last Updated**: October 21, 2025  
**Author**: Development Team  
**Status**: Ready for Implementation
