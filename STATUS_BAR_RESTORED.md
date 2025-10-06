# Status Bar Restoration

## Overview

The status bar has been restored to the main application window. It displays messages about application state and user actions at the bottom of the window.

## Changes Made

### 1. UI Changes (`ui/main/main_window.ui`)

Added `GtkStatusbar` widget at the bottom of the main workspace:

```xml
<!-- Status bar at bottom -->
<child>
  <object class="GtkStatusbar" id="status_bar">
    <property name="visible">True</property>
    <property name="margin-start">6</property>
    <property name="margin-end">6</property>
    <property name="margin-top">3</property>
    <property name="margin-bottom">3</property>
  </object>
  <packing>
    <property name="expand">False</property>
    <property name="fill">True</property>
    <property name="position">999</property>
  </packing>
</child>
```

**Location**: Bottom of `main_workspace` box (position 999 ensures it's last)

**Properties**:
- Small margins for visual spacing
- Non-expanding (stays at natural height)
- Always visible

### 2. Python Code Changes (`src/shypn.py`)

#### Status Bar Initialization

Added status bar retrieval and initialization after loading main window:

```python
# Get status bar
status_bar = main_builder.get_object('status_bar')
status_context_id = None
if status_bar:
    status_context_id = status_bar.get_context_id("main")
    
    # Helper function to update status bar
    def update_status(message):
        """Update the status bar with a message."""
        if status_bar and status_context_id:
            status_bar.pop(status_context_id)
            if message:
                status_bar.push(status_context_id, message)
    
    # Set initial status
    update_status("Ready")
else:
    print("WARNING: status_bar not found in UI file", file=sys.stderr)
    update_status = lambda msg: None  # No-op if status bar not found
```

**Context ID**: Uses "main" context for all messages

**Initial Message**: "Ready" displayed on startup

**Fallback**: If status bar not found, `update_status()` becomes a no-op function

#### Wiring to Components

**Model Canvas Loader**:
```python
# Wire status bar to canvas loader (if status bar available)
if status_bar:
    model_canvas_loader.status_bar = status_bar
    model_canvas_loader.status_context_id = status_context_id
    model_canvas_loader.update_status = update_status
```

**File Explorer**:
```python
def on_file_open_requested(filepath):
    """Handle file open request from file explorer."""
    update_status(f"Opening {os.path.basename(filepath)}...")
    file_explorer._open_file_from_path(filepath)
    update_status(f"Opened {os.path.basename(filepath)}")

file_explorer.on_file_open_requested = on_file_open_requested
```

## Usage

### From Main Application (`src/shypn.py`)

The `update_status()` function is available in the `on_activate()` scope:

```python
update_status("Your message here")
```

### From Canvas Loader

Components that have the canvas loader reference can update status:

```python
if hasattr(self.canvas_loader, 'update_status'):
    self.canvas_loader.update_status("Operation in progress...")
```

### From Any Component

If you have access to the status bar and context ID:

```python
status_bar.pop(context_id)
status_bar.push(context_id, "Your message")
```

## Status Bar API (GTK3)

### Key Methods

- `get_context_id(description)`: Get/create a context ID for message stack
- `push(context_id, text)`: Add a message to the stack (displays newest)
- `pop(context_id)`: Remove top message from context's stack
- `remove(context_id, message_id)`: Remove specific message by ID

### Context Stack Behavior

- Each context has its own message stack
- Only the newest message across all contexts is displayed
- `pop()` removes the top message from that context
- Always `pop()` before `push()` to avoid stack buildup

## Example Messages

**Startup**:
- "Ready"

**File Operations**:
- "Opening model.shy..."
- "Opened model.shy"
- "Saving model.shy..."
- "Saved model.shy"

**Canvas Operations**:
- "Place added"
- "Transition created"
- "Arc connected"
- "Selection cleared"

**Simulation**:
- "Simulation started"
- "Simulation paused"
- "Simulation step complete"
- "Simulation reset"

**Errors** (can use status bar for non-critical errors):
- "Cannot connect arc: invalid target"
- "No place selected"
- "Invalid token count"

## Visual Design

**Location**: Bottom of main window, below canvas area

**Height**: Natural height (~25-30px with margins)

**Styling**: Default GTK3 statusbar appearance with subtle margins

**Visibility**: Always visible (not collapsible)

## Future Enhancements

### Potential Additions

1. **Progress Bar**: Add `GtkProgressBar` for long operations
2. **Multiple Contexts**: Use different contexts for different message types
3. **Message Queue**: Queue messages with timed display
4. **Icon Support**: Add status icons for different message types
5. **Tooltips**: Extended messages in tooltips for truncated text

### Advanced Status Bar Layout

Could upgrade to custom box layout:

```xml
<object class="GtkBox" id="status_bar_box">
  <child>
    <object class="GtkStatusbar" id="status_bar">
      <!-- Messages -->
    </object>
  </child>
  <child>
    <object class="GtkProgressBar" id="status_progress">
      <!-- Progress indicator -->
    </object>
  </child>
  <child>
    <object class="GtkLabel" id="status_info">
      <!-- Additional info (e.g., zoom level, coordinates) -->
    </object>
  </child>
</object>
```

## Testing

### Manual Tests

1. **Startup**: Launch app, verify "Ready" appears
2. **File Open**: Double-click file, verify "Opening..." then "Opened..."
3. **Canvas Operations**: Add place, verify status updates
4. **Long Messages**: Test with long filenames (should truncate gracefully)

### Visual Tests

- Check status bar is visible at bottom
- Verify margins look good
- Test with maximized/resized window
- Check text readability

## Reference

**Original Implementation**: `legacy/shypnpy/interface/shypn.ui` line 838

**GTK3 StatusBar Docs**: https://docs.gtk.org/gtk3/class.Statusbar.html

## Status

✅ Status bar widget added to UI  
✅ Status bar wired to main application  
✅ Update function available to components  
✅ File open messages implemented  
⏳ Canvas operation messages (future)  
⏳ Simulation messages (future)  

## Files Modified

- `ui/main/main_window.ui` - Added GtkStatusbar widget
- `src/shypn.py` - Added status bar initialization and update function
