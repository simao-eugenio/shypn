# Master Palette - Floating Window Extension

**Date**: October 21, 2025  
**Status**: Extension to Monolithic Refactor Plan  
**Prerequisite**: Complete MASTER_PALETTE_MONOLITHIC_REFACTOR_PLAN.md first  
**Wayland Compatibility**: Zero Error 71 risk (no reparenting)

---

## Overview

This document extends the monolithic UI architecture to support **floating panel windows** for multi-monitor workflows. Users can "float" any panel to a separate window without losing the embedded version.

### Key Principle: Dual Build, No Reparenting

**WRONG Approach** (causes Error 71):
```python
# ❌ NEVER DO THIS
container.remove(panel_content)      # Remove from main window
floating_window.add(panel_content)   # Add to different window
```

**CORRECT Approach** (Wayland safe):
```python
# ✅ BUILD DUPLICATE
embedded_panel = build_panel_content(builder)  # Original stays in main window
floating_panel = build_panel_content(builder2) # NEW instance in floating window
sync_state(embedded_panel, floating_panel)     # Keep data in sync
```

---

## Architecture Changes

### Add Float Button to Each Panel

```xml
<!-- Each panel in stack gets a float button -->
<object class="GtkBox" id="files_panel">
  <property name="orientation">vertical</property>
  
  <!-- Header with float button -->
  <child>
    <object class="GtkBox" id="files_header">
      <property name="orientation">horizontal</property>
      <child>
        <object class="GtkLabel">
          <property name="label">Files</property>
          <property name="hexpand">True</property>
          <property name="xalign">0</property>
        </object>
      </child>
      <child>
        <object class="GtkButton" id="files_float_button">
          <property name="label">⇱</property>
          <property name="tooltip-text">Float to separate window</property>
          <property name="relief">none</property>
        </object>
      </child>
    </object>
  </child>
  
  <!-- Panel content -->
  <child>
    <object class="GtkBox" id="files_content">
      <!-- Actual panel widgets here -->
    </object>
  </child>
</object>
```

### Floating Window Template

```xml
<!-- Template for floating panel windows (created programmatically) -->
<object class="GtkWindow" id="floating_panel_window">
  <property name="type">normal</property>
  <property name="title">[Panel Name] - Shypn</property>
  <property name="default-width">400</property>
  <property name="default-height">600</property>
  <property name="decorated">True</property>
  <property name="icon-name">shypn</property>
  
  <child>
    <object class="GtkBox">
      <property name="orientation">vertical</property>
      
      <!-- Floating panel header -->
      <child>
        <object class="GtkBox">
          <property name="orientation">horizontal</property>
          <property name="spacing">6</property>
          <property name="margin">6</property>
          
          <child>
            <object class="GtkLabel">
              <property name="label">[Panel Name]</property>
              <property name="hexpand">True</property>
              <property name="xalign">0</property>
              <attributes>
                <attribute name="weight" value="bold"/>
              </attributes>
            </object>
          </child>
          
          <child>
            <object class="GtkButton" id="dock_button">
              <property name="label">⇲</property>
              <property name="tooltip-text">Close floating window</property>
            </object>
          </child>
        </object>
      </child>
      
      <!-- Duplicated panel content goes here -->
      <child>
        <object class="GtkBox" id="floating_content_container">
          <property name="vexpand">True</property>
          <property name="hexpand">True</property>
        </object>
      </child>
      
    </object>
  </child>
</object>
```

---

## Implementation

### Phase 1: Panel Factory Functions (2 hours)

Create factory functions to build panel content that can be called multiple times.

#### 1.1: Files Panel Factory

```python
class FilesPanelFactory:
    """Factory to create Files panel instances (embedded or floating)."""
    
    @staticmethod
    def build(parent_container, parent_window, models_dir):
        """Build Files panel content.
        
        Args:
            parent_container: GtkBox to add content to
            parent_window: Parent window for dialogs
            models_dir: Base directory for file explorer
            
        Returns:
            FilesPanelInstance with controllers and widgets
        """
        # Create UI programmatically (no .ui file reparenting)
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        
        # File explorer tree view
        file_explorer = FileExplorerPanel.build_standalone(
            parent_window=parent_window,
            base_path=models_dir
        )
        main_box.pack_start(file_explorer.get_widget(), True, True, 0)
        
        # Project controls toolbar
        project_controls = ProjectActionsController.build_standalone(
            parent_window=parent_window
        )
        main_box.pack_start(project_controls.get_widget(), False, False, 0)
        
        # Add to container
        parent_container.add(main_box)
        
        # Return instance wrapper
        return FilesPanelInstance(
            widget=main_box,
            file_explorer=file_explorer,
            project_controls=project_controls
        )

class FilesPanelInstance:
    """Wrapper for Files panel instance."""
    
    def __init__(self, widget, file_explorer, project_controls):
        self.widget = widget
        self.file_explorer = file_explorer
        self.project_controls = project_controls
        
    def sync_from(self, other_instance):
        """Sync state from another Files panel instance."""
        # Sync current directory
        current_path = other_instance.file_explorer.get_current_path()
        self.file_explorer.set_current_path(current_path)
        
        # Sync expansion state
        expanded = other_instance.file_explorer.get_expanded_paths()
        self.file_explorer.set_expanded_paths(expanded)
```

#### 1.2: Analyses Panel Factory

```python
class AnalysesPanelFactory:
    """Factory to create Analyses panel instances."""
    
    @staticmethod
    def build(parent_container, parent_window, data_collector):
        """Build Analyses panel content.
        
        Returns:
            AnalysesPanelInstance with controllers
        """
        # Create notebook with plot tabs
        notebook = Gtk.Notebook()
        
        # Time Series tab
        time_series = TimeSeriesController.build_standalone(
            parent_window=parent_window,
            data_collector=data_collector
        )
        notebook.append_page(
            time_series.get_widget(),
            Gtk.Label(label="Time Series")
        )
        
        # Histogram tab
        histogram = HistogramController.build_standalone(
            parent_window=parent_window,
            data_collector=data_collector
        )
        notebook.append_page(
            histogram.get_widget(),
            Gtk.Label(label="Histogram")
        )
        
        # Similar for other plot types...
        
        parent_container.add(notebook)
        
        return AnalysesPanelInstance(
            widget=notebook,
            time_series=time_series,
            histogram=histogram,
            # ...other controllers
        )

class AnalysesPanelInstance:
    """Wrapper for Analyses panel instance."""
    
    def __init__(self, widget, time_series, histogram, scatter, phase):
        self.widget = widget
        self.time_series = time_series
        self.histogram = histogram
        self.scatter = scatter
        self.phase = phase
        
    def sync_from(self, other_instance):
        """Sync state from another Analyses panel instance."""
        # Sync active tab
        active_page = other_instance.widget.get_current_page()
        self.widget.set_current_page(active_page)
        
        # Each controller can sync its own state
        self.time_series.sync_from(other_instance.time_series)
        self.histogram.sync_from(other_instance.histogram)
        # etc...
```

#### 1.3: Similar Factories for Pathways and Topology

---

### Phase 2: Floating Window Manager (1.5 hours)

Centralized manager for floating panel windows.

```python
class FloatingPanelManager:
    """Manages floating panel windows (create, track, destroy)."""
    
    def __init__(self, main_window):
        self.main_window = main_window
        self.floating_windows = {}  # panel_name -> FloatingWindow instance
        
    def float_panel(self, panel_name, factory, factory_args):
        """Create floating window for panel.
        
        Args:
            panel_name: 'files', 'analyses', 'pathways', or 'topology'
            factory: Panel factory class (FilesPanelFactory, etc.)
            factory_args: Dict of args to pass to factory.build()
            
        Returns:
            FloatingWindow instance
        """
        # Check if already floating
        if panel_name in self.floating_windows:
            existing = self.floating_windows[panel_name]
            existing.window.present()  # Bring to front
            return existing
        
        # Create new floating window
        window = Gtk.Window(
            type=Gtk.WindowType.TOPLEVEL,
            title=f"{panel_name.capitalize()} - Shypn",
            default_width=400,
            default_height=600,
            decorated=True,
            transient_for=self.main_window
        )
        
        # Create container for content
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        window.add(content_box)
        
        # Add header with dock button
        header = self._build_float_header(panel_name, window)
        content_box.pack_start(header, False, False, 0)
        
        # Build panel content using factory
        container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        content_box.pack_start(container, True, True, 0)
        
        panel_instance = factory.build(
            parent_container=container,
            **factory_args
        )
        
        # Connect window close event
        window.connect('delete-event', lambda w, e: self._on_float_close(panel_name))
        
        # Show window
        window.show_all()
        
        # Track floating window
        floating = FloatingWindow(
            window=window,
            panel_instance=panel_instance,
            panel_name=panel_name
        )
        self.floating_windows[panel_name] = floating
        
        return floating
    
    def _build_float_header(self, panel_name, window):
        """Build header bar for floating window."""
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        header.set_margin_top(6)
        header.set_margin_bottom(6)
        header.set_margin_start(6)
        header.set_margin_end(6)
        
        # Title label
        title = Gtk.Label(label=panel_name.capitalize())
        title.set_hexpand(True)
        title.set_xalign(0)
        title_attrs = Pango.AttrList()
        title_attrs.insert(Pango.attr_weight_new(Pango.Weight.BOLD))
        title.set_attributes(title_attrs)
        header.pack_start(title, True, True, 0)
        
        # Dock button (closes window)
        dock_btn = Gtk.Button(label="⇲")
        dock_btn.set_tooltip_text("Close floating window")
        dock_btn.set_relief(Gtk.ReliefStyle.NONE)
        dock_btn.connect('clicked', lambda b: window.close())
        header.pack_start(dock_btn, False, False, 0)
        
        return header
    
    def _on_float_close(self, panel_name):
        """Handle floating window close."""
        if panel_name in self.floating_windows:
            # Remove from tracking
            del self.floating_windows[panel_name]
        return False  # Allow window to close
    
    def close_all(self):
        """Close all floating windows."""
        for floating in list(self.floating_windows.values()):
            floating.window.close()
        self.floating_windows.clear()

class FloatingWindow:
    """Represents a floating panel window."""
    
    def __init__(self, window, panel_instance, panel_name):
        self.window = window
        self.panel_instance = panel_instance
        self.panel_name = panel_name
```

---

### Phase 3: Wire Float Buttons (30 minutes)

Connect float buttons in embedded panels to floating manager.

```python
# In main shypn.py, after building main window

# Create floating manager
floating_manager = FloatingPanelManager(window)

# Get float buttons from embedded panels
files_float_btn = main_builder.get_object('files_float_button')
analyses_float_btn = main_builder.get_object('analyses_float_button')
pathways_float_btn = main_builder.get_object('pathways_float_button')
topology_float_btn = main_builder.get_object('topology_float_button')

# Wire float button handlers
def on_files_float_clicked(button):
    """Float Files panel to separate window."""
    floating_manager.float_panel(
        panel_name='files',
        factory=FilesPanelFactory,
        factory_args={
            'parent_window': window,
            'models_dir': models_dir
        }
    )
    # Sync state from embedded to floating
    embedded_panel = embedded_files_instance
    floating = floating_manager.floating_windows['files']
    floating.panel_instance.sync_from(embedded_panel)

def on_analyses_float_clicked(button):
    """Float Analyses panel to separate window."""
    floating_manager.float_panel(
        panel_name='analyses',
        factory=AnalysesPanelFactory,
        factory_args={
            'parent_window': window,
            'data_collector': data_collector
        }
    )
    embedded_panel = embedded_analyses_instance
    floating = floating_manager.floating_windows['analyses']
    floating.panel_instance.sync_from(embedded_panel)

# Similar for pathways and topology...

# Connect signals
files_float_btn.connect('clicked', on_files_float_clicked)
analyses_float_btn.connect('clicked', on_analyses_float_clicked)
pathways_float_btn.connect('clicked', on_pathways_float_clicked)
topology_float_btn.connect('clicked', on_topology_float_clicked)

# Clean up floating windows on app exit
window.connect('destroy', lambda w: floating_manager.close_all())
```

---

### Phase 4: Bidirectional State Sync (1 hour)

Keep embedded and floating panels in sync.

```python
class PanelStateSynchronizer:
    """Synchronizes state between embedded and floating panel instances."""
    
    def __init__(self, embedded_instance, floating_instance):
        self.embedded = embedded_instance
        self.floating = floating_instance
        self._setup_sync()
    
    def _setup_sync(self):
        """Set up bidirectional state synchronization."""
        # Example for Files panel
        if isinstance(self.embedded, FilesPanelInstance):
            self._sync_files_panel()
    
    def _sync_files_panel(self):
        """Sync Files panel state bidirectionally."""
        # Sync directory changes from embedded to floating
        self.embedded.file_explorer.connect(
            'directory-changed',
            lambda fe, path: self.floating.file_explorer.set_current_path(path)
        )
        
        # Sync directory changes from floating to embedded
        self.floating.file_explorer.connect(
            'directory-changed',
            lambda fe, path: self.embedded.file_explorer.set_current_path(path)
        )
        
        # Sync file selection
        self.embedded.file_explorer.connect(
            'file-selected',
            lambda fe, path: self.floating.file_explorer.select_file(path)
        )
        
        self.floating.file_explorer.connect(
            'file-selected',
            lambda fe, path: self.embedded.file_explorer.select_file(path)
        )
```

---

## Benefits of This Approach

### ✅ Advantages

1. **Wayland Safe**: No widget reparenting = no Error 71
2. **Multi-Monitor**: Float panels to different displays
3. **Independent Windows**: Resize, move, minimize separately
4. **State Sync**: Changes in one reflected in the other
5. **Embedded Always Available**: Can use both simultaneously
6. **Clean Destruction**: Close floating window without affecting embedded

### ⚠️ Considerations

1. **Memory Overhead**: Each floating panel duplicates widgets
2. **State Management**: Need to keep instances in sync
3. **Implementation Complexity**: More code to maintain
4. **Sync Delay**: Minimal but exists (signals propagate)

---

## Usage Scenarios

### Scenario 1: Multi-Monitor Workflow
```
Monitor 1: Main window with Master Palette + embedded Files panel
Monitor 2: Floating Analyses panel for continuous monitoring
Monitor 3: Floating Pathways panel for KEGG import

User can:
- Use Master Palette to switch embedded panels
- Keep Analyses floating on secondary monitor
- Import pathway on tertiary monitor
- All panels sync state automatically
```

### Scenario 2: Focused Work
```
User floats Files panel to keep file tree visible
Main window shows workspace with embedded Analyses panel
User can browse files while analyzing data side-by-side
```

---

## Testing Plan

### Unit Tests

1. **Factory Functions**
   - ✅ Each factory builds valid panel instance
   - ✅ Multiple instances can coexist
   - ✅ Instances are independent

2. **Floating Manager**
   - ✅ Can create floating window
   - ✅ Prevents duplicate floating windows
   - ✅ Tracks all floating instances
   - ✅ Cleans up on close

3. **State Sync**
   - ✅ Changes in embedded reflect in floating
   - ✅ Changes in floating reflect in embedded
   - ✅ No infinite loops

### Integration Tests

1. **Files Panel**
   - ✅ Float panel, navigate directories in floating
   - ✅ Verify embedded panel follows
   - ✅ Navigate in embedded, verify floating follows
   - ✅ Open file from floating, verify canvas updates

2. **Analyses Panel**
   - ✅ Float panel, switch plot tabs
   - ✅ Generate plot in floating, verify it appears
   - ✅ Switch tab in embedded, verify floating follows

3. **Multi-Monitor**
   - ✅ Move floating to different monitor
   - ✅ Verify state sync still works
   - ✅ Close floating, verify embedded continues

### Wayland Safety Tests

1. **No Error 71**
   - ✅ Float/close panels rapidly
   - ✅ Float all panels simultaneously
   - ✅ Resize main window while panels floating
   - ✅ Close main window with panels floating

---

## Implementation Timeline

| Task | Duration | Dependencies |
|------|----------|--------------|
| 1. Panel Factories | 2 hours | Monolithic refactor complete |
| 2. Floating Manager | 1.5 hours | Panel factories done |
| 3. Wire Float Buttons | 30 min | Floating manager done |
| 4. State Sync | 1 hour | All above |
| 5. Testing | 1 hour | All above |
| **Total** | **6 hours** | - |

---

## Optional Enhancements

### Enhancement 1: Remember Floating State

```python
# Save floating window positions on close
def save_floating_state():
    config = {}
    for name, floating in floating_manager.floating_windows.items():
        x, y = floating.window.get_position()
        w, h = floating.window.get_size()
        config[name] = {'x': x, 'y': y, 'width': w, 'height': h}
    
    with open('floating_state.json', 'w') as f:
        json.dump(config, f)

# Restore on startup
def restore_floating_state():
    if os.path.exists('floating_state.json'):
        with open('floating_state.json') as f:
            config = json.load(f)
        
        for name, state in config.items():
            if should_restore_panel(name):  # User preference
                floating = floating_manager.float_panel(name, ...)
                floating.window.move(state['x'], state['y'])
                floating.window.resize(state['width'], state['height'])
```

### Enhancement 2: Keyboard Shortcuts

```python
# Add accelerators for floating panels
accel_group = Gtk.AccelGroup()
window.add_accel_group(accel_group)

# Ctrl+Shift+F: Float Files panel
files_float_btn.add_accelerator(
    'clicked',
    accel_group,
    Gdk.KEY_F,
    Gdk.ModifierType.CONTROL_MASK | Gdk.ModifierType.SHIFT_MASK,
    Gtk.AccelFlags.VISIBLE
)

# Ctrl+Shift+A: Float Analyses panel
# etc...
```

### Enhancement 3: Drag-to-Float

```python
# Allow dragging panel header to create floating window
panel_header.connect('button-press-event', on_header_press)
panel_header.connect('motion-notify-event', on_header_drag)
panel_header.connect('button-release-event', on_header_release)

def on_header_drag(widget, event):
    """If dragged far enough from window, create floating panel."""
    if event.state & Gdk.ModifierType.BUTTON1_MASK:
        # Check if dragged outside main window bounds
        if is_outside_main_window(event.x_root, event.y_root):
            # Create floating panel at cursor position
            create_floating_panel_at_cursor(panel_name, event.x_root, event.y_root)
```

---

## Conclusion

The **Dual Build Pattern** allows floating panels in the monolithic architecture while maintaining Wayland safety. By building duplicate panel instances instead of reparenting widgets, we get:

- ✅ Multi-monitor support
- ✅ Zero Error 71 risk
- ✅ Clean state management
- ✅ Professional UX

This extension is **fully compatible** with the monolithic refactor plan and can be implemented incrementally after the base architecture is stable.

**Recommendation**: 
1. Complete monolithic refactor first (5 hours)
2. Test thoroughly without floating
3. Add floating capability as enhancement (6 hours)

---

**Document Version**: 1.0  
**Last Updated**: October 21, 2025  
**Status**: Extension Plan - Ready for Implementation  
**Prerequisite**: MASTER_PALETTE_MONOLITHIC_REFACTOR_PLAN.md
