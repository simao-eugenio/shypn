# Save Operation Flow - Complete Behavior

**Date**: October 4, 2025  
**Status**: ✅ Implemented and Documented  

## Summary

The Save operation now has clear, predictable behavior that always opens the file chooser for new/unsaved documents, with "default.shy" pre-filled to prompt users to choose a meaningful filename.

## Save Button Behavior

### **Case 1: New/Unsaved Document (No filepath)**

```
User clicks "💾 Save" button
  ↓
Check: has_filepath()?
  ↓ NO (current_filepath is None)
  ↓
Open File Chooser Dialog
  ↓
Pre-fill with "default.shy"
  ↓
User enters filename (or keeps "default.shy")
  ↓
User clicks Save
  ↓
Check: filename == "default.shy"?
  ↓ YES
  ↓
Show Warning Dialog:
  "You are about to save with the default filename 'default.shy'.
   This may overwrite existing default files or make it hard to
   identify this model later.
   
   Do you want to continue with this filename?"
  
  [No] → Return to file chooser
  [Yes] → Proceed with save
  ↓
Save file
Document marked as clean
current_filepath set
```

### **Case 2: Previously Saved Document (Has filepath)**

```
User clicks "💾 Save" button
  ↓
Check: has_filepath()?
  ↓ YES (current_filepath exists)
  ↓
Save directly to current_filepath
  ↓
No file chooser shown
No prompts shown
Document marked as clean
```

### **Case 3: Save As (Always prompt)**

```
User clicks "💾+ Save As" button
  ↓
save_as=True (override existing filepath)
  ↓
Open File Chooser Dialog
  ↓
If has filepath:
  Pre-fill with current filename
Else:
  Pre-fill with "default.shy"
  ↓
User enters new filename
  ↓
Check: filename == "default.shy"?
  ↓ YES
  ↓
Show Warning Dialog (same as above)
  ↓
Save to new file
current_filepath updated
```

## Code Implementation

### **save_document() Method**

```python
def save_document(self, document, save_as: bool = False) -> bool:
    """Save document to file.
    
    Behavior:
    - If document has a filepath AND save_as=False: Save directly to existing file
    - If document has NO filepath OR save_as=True: Show file chooser dialog
      - File chooser pre-fills with "default.shy" for new documents
      - User can change filename or accept "default.shy"
      - Warning shown if user keeps "default.shy"
    
    Args:
        document: DocumentModel instance to save
        save_as: If True, always prompt for filename (Save As)
        
    Returns:
        bool: True if save successful, False if cancelled or error
    """
    # Check if we need to prompt for filename
    if save_as or not self.has_filepath():
        filepath = self._show_save_dialog()
        if not filepath:
            print("[Persistency] Save cancelled by user")
            return False
        
        self.set_filepath(filepath)
    
    # Save to file
    try:
        document.save_to_file(self.current_filepath)
        self.mark_clean()
        
        print(f"[Persistency] Saved to {self.current_filepath}")
        
        # Notify observers
        if self.on_file_saved:
            self.on_file_saved(self.current_filepath)
        
        # Show success message
        self._show_success_dialog(
            "File saved successfully",
            f"Saved to:\n{self.current_filepath}"
        )
        
        return True
        
    except Exception as e:
        print(f"[Persistency] Save error: {e}")
        import traceback
        traceback.print_exc()
        
        # Show error message
        self._show_error_dialog(
            "Error saving file",
            str(e)
        )
        
        return False
```

### **_show_save_dialog() Method**

```python
def _show_save_dialog(self) -> Optional[str]:
    """Show save file chooser dialog.
    
    Returns:
        str: Selected filepath, or None if cancelled
    """
    dialog = Gtk.FileChooserDialog(
        title="Save Petri Net",
        parent=self.parent_window,
        action=Gtk.FileChooserAction.SAVE
    )
    dialog.add_buttons(
        Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
        Gtk.STOCK_SAVE, Gtk.ResponseType.OK
    )
    
    # Set default response
    dialog.set_default_response(Gtk.ResponseType.OK)
    
    # Enable overwrite confirmation
    dialog.set_do_overwrite_confirmation(True)
    
    # Add file filter for .shy files
    filter_shy = Gtk.FileFilter()
    filter_shy.set_name("SHYpn Petri Net files (*.shy)")
    filter_shy.add_pattern("*.shy")
    dialog.add_filter(filter_shy)
    
    filter_all = Gtk.FileFilter()
    filter_all.set_name("All files")
    filter_all.add_pattern("*")
    dialog.add_filter(filter_all)
    
    # Set initial directory to models directory or last used directory
    if self._last_directory and os.path.isdir(self._last_directory):
        dialog.set_current_folder(self._last_directory)
    elif os.path.isdir(self.models_directory):
        dialog.set_current_folder(self.models_directory)
    
    # Set current filename if already exists (for Save As)
    if self.current_filepath:
        dialog.set_filename(self.current_filepath)
    else:
        # Pre-fill with "default.shy" to prompt user to change it
        # This makes it obvious that a filename needs to be chosen
        # User can either accept "default.shy" or type a custom name
        default_name = "default.shy"
        dialog.set_current_name(default_name)
    
    # Run dialog
    response = dialog.run()
    filepath = dialog.get_filename()
    dialog.destroy()
    
    if response != Gtk.ResponseType.OK or not filepath:
        return None
    
    # Ensure .shy extension
    if not filepath.endswith('.shy'):
        filepath += '.shy'
    
    # Check if user is trying to save with default name
    filename = os.path.basename(filepath)
    if filename.lower() == "default.shy":
        # Show warning dialog
        warning_dialog = Gtk.MessageDialog(
            parent=self.parent_window,
            flags=Gtk.DialogFlags.MODAL,
            type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.YES_NO,
            text="Save as 'default.shy'?"
        )
        warning_dialog.format_secondary_text(
            "You are about to save with the default filename 'default.shy'.\n\n"
            "This may overwrite existing default files or make it hard to "
            "identify this model later.\n\n"
            "Do you want to continue with this filename?"
        )
        
        warning_response = warning_dialog.run()
        warning_dialog.destroy()
        
        if warning_response != Gtk.ResponseType.YES:
            # User wants to change the filename, show dialog again
            return self._show_save_dialog()
    
    # Update last directory
    self._last_directory = os.path.dirname(filepath)
    
    return filepath
```

## User Experience Examples

### **Example 1: First Save (New Document)**

```
1. User creates new canvas
   - Canvas manager: filename = "default"
   - Persistency: current_filepath = None

2. User draws some objects
   - Canvas marked as modified

3. User clicks "💾 Save"
   - has_filepath() = False
   - File chooser opens
   - Shows: "default.shy" in filename field
   - Directory: models/

4. User types: "my_petri_net"
   - Filename becomes: "my_petri_net.shy"

5. User clicks Save
   - File saved to: models/my_petri_net.shy
   - current_filepath = "models/my_petri_net.shy"
   - Document marked as clean
   - Success dialog shown
```

### **Example 2: Save After Clear Canvas**

```
1. User has "mymodel.shy" open
   - current_filepath = "models/mymodel.shy"

2. User right-clicks → Clear Canvas
   - All objects removed
   - Canvas manager: filename = "default"
   - Persistency: current_filepath = "models/mymodel.shy" (still set!)

3. User draws new objects

4. User clicks "💾 Save"
   - has_filepath() = True (still has old path!)
   - Saves directly to "models/mymodel.shy" (overwrites!)

⚠️ THIS IS A PROBLEM! We need to reset current_filepath when clearing!
```

### **Example 3: Trying to Save as Default**

```
1. User creates new canvas
2. User draws objects
3. User clicks "💾 Save"
4. File chooser shows "default.shy"
5. User keeps "default.shy" and clicks Save
6. Warning dialog appears:
   
   ⚠️ Save as 'default.shy'?
   
   You are about to save with the default filename 'default.shy'.
   
   This may overwrite existing default files or make it hard to
   identify this model later.
   
   Do you want to continue with this filename?
   
   [No] [Yes]

7a. User clicks [No]:
    - Returns to file chooser
    - User enters new name

7b. User clicks [Yes]:
    - Saves as "default.shy"
    - Success dialog shown
```

## Issue Identified: Clear Canvas Doesn't Reset Filepath!

**Problem**: When user clears the canvas, the `current_filepath` in NetObjPersistency is NOT reset. This means:

```python
# User opens "mymodel.shy"
persistency.current_filepath = "models/mymodel.shy"

# User clears canvas
manager.filename = "default"  # ✅ Reset
persistency.current_filepath = "models/mymodel.shy"  # ❌ NOT reset!

# User clicks Save
# Overwrites mymodel.shy! Should prompt for new filename!
```

### **Solution Needed**

When clearing canvas, we need to also reset the persistency state:

```python
def on_clear_canvas():
    # Clear canvas manager
    manager.clear_all_objects()
    
    # Reset persistency state
    persistency.current_filepath = None
    persistency.mark_dirty()  # Or mark_clean()?
```

Or better yet, integrate with persistency's `new_document()`:

```python
def on_clear_canvas():
    # Check for unsaved changes
    if not persistency.check_unsaved_changes():
        return
    
    # Create new document (resets filepath)
    persistency.new_document()
    
    # Clear canvas manager
    manager.clear_all_objects()
```

## Recommended Implementation

### **Option A: Reset filepath on clear**
```python
# In model_canvas_loader.py
def _on_clear_canvas_clicked(self, menu, drawing_area, manager):
    """Clear canvas and reset to new document state."""
    # Get persistency manager (need reference)
    if hasattr(self, 'persistency'):
        # Check for unsaved changes
        if not self.persistency.check_unsaved_changes():
            return
        
        # Reset persistency state
        self.persistency.new_document()
    
    # Clear canvas
    manager.clear_all_objects()
    drawing_area.queue_draw()
```

### **Option B: Clear Canvas = New Document**
Treat "Clear Canvas" as "New Document" operation:
- Prompt for unsaved changes
- Reset all state
- Clear all objects

---

**Status**: 
- ✅ Save dialog behavior: CORRECT
- ✅ Default filename pre-fill: WORKING
- ✅ Default filename warning: WORKING
- ⚠️ Clear canvas filepath reset: **NEEDS FIX**
