# Property Dialogs Persistency - Visual Guide

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐ │
│  │    Place     │      │  Transition  │      │     Arc      │ │
│  │  Properties  │      │  Properties  │      │  Properties  │ │
│  │    Dialog    │      │    Dialog    │      │    Dialog    │ │
│  └──────┬───────┘      └──────┬───────┘      └──────┬───────┘ │
│         │                     │                     │          │
│         └─────────────────────┴─────────────────────┘          │
│                               │                                │
│                    ┌──────────▼──────────┐                     │
│                    │  Dialog Loaders     │                     │
│                    │  - Load UI          │                     │
│                    │  - Populate fields  │                     │
│                    │  - Apply changes    │                     │
│                    │  - Mark dirty       │                     │
│                    │  - Emit signal      │                     │
│                    └──────────┬──────────┘                     │
│                               │                                │
└───────────────────────────────┼────────────────────────────────┘
                                │
                ┌───────────────┼───────────────┐
                │               │               │
                ▼               ▼               ▼
    ┌─────────────────┐  ┌──────────────┐  ┌──────────────┐
    │  Persistency    │  │   Canvas     │  │ File System  │
    │   Manager       │  │   Manager    │  │   Tracking   │
    │                 │  │              │  │              │
    │  mark_dirty()   │  │ queue_draw() │  │ Show (*) in  │
    │  is_dirty       │  │              │  │ file tree    │
    │  callbacks      │  │              │  │              │
    └─────────────────┘  └──────────────┘  └──────────────┘
```

## Data Flow - Property Change Scenario

```
┌────────────────────────────────────────────────────────────────────┐
│  Step 1: User Opens Properties Dialog                             │
└────────────────────────────────────────────────────────────────────┘
    User right-clicks object → Context menu → "Properties"
                                      │
                                      ▼
            ModelCanvasLoader._on_object_properties(obj)
                                      │
                                      ▼
            Create dialog loader with persistency_manager
                                      │
                                      ▼
                    dialog_loader = create_place_prop_dialog(
                        obj,
                        parent_window=self.parent_window,
                        persistency_manager=self.persistency  ← PASS IT!
                    )

┌────────────────────────────────────────────────────────────────────┐
│  Step 2: Dialog Displays Current Properties                       │
└────────────────────────────────────────────────────────────────────┘
                    Dialog loads from place_prop_dialog.ui
                                      │
                                      ▼
                    _populate_fields() fills in current values
                                      │
                                      ▼
                        Dialog shows to user

┌────────────────────────────────────────────────────────────────────┐
│  Step 3: User Modifies Properties                                 │
└────────────────────────────────────────────────────────────────────┘
            User changes: Name: "P1" → "Input Place"
            User changes: Marking: 0 → 5
                                      │
                                      ▼
                        User clicks [OK]

┌────────────────────────────────────────────────────────────────────┐
│  Step 4: Apply Changes                                            │
└────────────────────────────────────────────────────────────────────┘
                    _on_response(dialog, OK)
                                      │
                                      ▼
                    _apply_changes()
                                      │
                    ┌─────────────────┴─────────────────┐
                    │                                   │
                    ▼                                   ▼
            place_obj.name = "Input Place"    place_obj.marking = 5
                    │                                   │
                    └─────────────────┬─────────────────┘
                                      │
                                      ▼
┌────────────────────────────────────────────────────────────────────┐
│  Step 5: Mark Document as Dirty                                   │
└────────────────────────────────────────────────────────────────────┘
            if self.persistency_manager:
                self.persistency_manager.mark_dirty()
                                      │
                                      ▼
                    NetObjPersistency.mark_dirty()
                                      │
                    ┌─────────────────┴─────────────────┐
                    │                                   │
                    ▼                                   ▼
            self._is_dirty = True        if self.on_dirty_changed:
                                            self.on_dirty_changed(True)
                                                        │
                                                        ▼
                            FileExplorerPanel._on_dirty_changed_callback(True)
                                                        │
                                                        ▼
                                        Update tree view: "file.shy" → "file.shy (*)"

┌────────────────────────────────────────────────────────────────────┐
│  Step 6: Notify Observers                                         │
└────────────────────────────────────────────────────────────────────┘
                    self.emit('properties-changed')
                                      │
                                      ▼
            Signal handler: lambda _: drawing_area.queue_draw()
                                      │
                                      ▼
                        Canvas redraws with new properties

┌────────────────────────────────────────────────────────────────────┐
│  Step 7: Cleanup                                                  │
└────────────────────────────────────────────────────────────────────┘
                        dialog.destroy()
                                      │
                                      ▼
                            User sees:
                            - Updated canvas
                            - File marked with (*)
                            - Unsaved changes tracked
```

## Code Interaction Diagram

```
PlacePropDialogLoader                NetObjPersistency           FileExplorerPanel
        │                                    │                           │
        │ __init__(persistency_manager)     │                           │
        ├───────────────────────────────────►│                           │
        │                                    │                           │
        │ User clicks OK                     │                           │
        │                                    │                           │
        │ _on_response(OK)                   │                           │
        │   │                                │                           │
        │   └─ _apply_changes()              │                           │
        │         │                          │                           │
        │         └─ obj.name = new_name     │                           │
        │                                    │                           │
        │ persistency_manager.mark_dirty()   │                           │
        ├───────────────────────────────────►│                           │
        │                                    │                           │
        │                                    │ self._is_dirty = True     │
        │                                    │                           │
        │                                    │ on_dirty_changed(True)    │
        │                                    ├──────────────────────────►│
        │                                    │                           │
        │                                    │                    Update tree view
        │                                    │                    Show asterisk (*)
        │                                    │                           │
        │ emit('properties-changed')         │                           │
        │   │                                │                           │
        │   └─► Signal → queue_draw()        │                           │
        │                                    │                           │
        │ dialog.destroy()                   │                           │
        │                                    │                           │
```

## State Transitions

```
┌─────────────────────────────────────────────────────────────────┐
│                     Document State Machine                      │
└─────────────────────────────────────────────────────────────────┘

    [CLEAN STATE]
    is_dirty = False
    File tree: "model.shy"
         │
         │ User opens property dialog
         │ and makes changes
         ▼
    _apply_changes()
         │
         ▼
    mark_dirty()
         │
         ▼
    [DIRTY STATE]
    is_dirty = True
    File tree: "model.shy (*)"
         │
         │ User saves file
         │
         ▼
    save_document()
         │
         ▼
    mark_clean()
         │
         ▼
    [CLEAN STATE]
    is_dirty = False
    File tree: "model.shy"

Alternative paths from DIRTY STATE:

    [DIRTY STATE]
         │
         ├─── User clicks "Discard Changes" ──►  mark_clean()  ──► [CLEAN STATE]
         │
         ├─── User saves file ─────────────────►  mark_clean()  ──► [CLEAN STATE]
         │
         └─── User cancels close ──────────────►  Stay in DIRTY STATE
```

## Signal Flow Diagram

```
Dialog Loader                  ModelCanvasLoader              DrawingArea
     │                                │                            │
     │ __init__()                     │                            │
     │                                │                            │
     │ run() → shows dialog           │                            │
     │                                │                            │
     │ User clicks OK                 │                            │
     │                                │                            │
     │ emit('properties-changed')     │                            │
     ├───────────────────────────────►│                            │
     │                                │                            │
     │                                │ Signal handler triggered   │
     │                                │                            │
     │                                │ lambda _: drawing_area.queue_draw()
     │                                ├───────────────────────────►│
     │                                │                            │
     │                                │                      Redraw canvas
     │                                │                      with new props
     │                                │                            │
     │ Backup: if OK:                 │                            │
     │   drawing_area.queue_draw()    │                            │
     ├───────────────────────────────────────────────────────────►│
     │                                │                            │
```

## Key Design Decisions

### 1. **Optional Persistency Manager**
```python
if self.persistency_manager:
    self.persistency_manager.mark_dirty()
```
- **Why**: Allows testing without full setup
- **Benefit**: Backward compatibility
- **Trade-off**: Need to check for None

### 2. **GObject Signal System**
```python
__gsignals__ = {
    'properties-changed': (GObject.SignalFlags.RUN_FIRST, None, ())
}
```
- **Why**: Loose coupling between components
- **Benefit**: Easy to add more observers
- **Trade-off**: More complex than direct calls

### 3. **Dual Redraw Strategy**
```python
# Primary: Signal-based
dialog_loader.connect('properties-changed', lambda _: drawing_area.queue_draw())

# Backup: Direct call
if response == Gtk.ResponseType.OK:
    drawing_area.queue_draw()
```
- **Why**: Ensure canvas always redraws
- **Benefit**: Reliability
- **Trade-off**: Potential double-redraw (minimal cost)

## Implementation Checklist

✅ **Dialog Loaders**
- [x] Add `persistency_manager` parameter to `__init__`
- [x] Store `persistency_manager` as instance variable
- [x] Define `__gsignals__` with `properties-changed`
- [x] Call `mark_dirty()` in `_on_response()` when OK
- [x] Emit `properties-changed` signal after changes
- [x] Update factory functions to accept `persistency_manager`

✅ **ModelCanvasLoader**
- [x] Pass `self.persistency` to dialog loaders
- [x] Connect to `properties-changed` signal
- [x] Call `queue_draw()` on signal
- [x] Keep backup `queue_draw()` call

✅ **Testing**
- [x] Application starts without errors
- [ ] Property changes mark document dirty
- [ ] File tree shows asterisk (*)
- [ ] Canvas redraws after changes
- [ ] Save operation clears dirty state

✅ **Documentation**
- [x] Implementation guide created
- [x] Visual guide created
- [x] Code examples provided
- [x] Architecture diagrams included
