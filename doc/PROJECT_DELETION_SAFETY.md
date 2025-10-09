# Project Deletion Safety Guidelines

## ⚠️ Critical Safety Concern

Deleting projects with `delete_files=True` is equivalent to running `rm -rf` on the project directory. **This operation is PERMANENT and CANNOT be undone.**

## Risk Assessment

### High-Risk Operations

1. **`delete_project(project_id, delete_files=True)`**
   - ⚠️ **DANGER**: Permanently deletes all project files
   - Equivalent to: `rm -rf /path/to/project/`
   - **Cannot be recovered** unless backed up externally
   - Risk level: **CRITICAL**

2. **No built-in backup**
   - Current implementation has no automatic backup before deletion
   - User error can result in data loss
   - No "undo" functionality

### Medium-Risk Operations

1. **`delete_project(project_id, delete_files=False)`**
   - Removes project from index only
   - Files remain on disk
   - Can be recovered by re-importing
   - Risk level: **MODERATE**

## Safety Measures Implemented

### 1. Path Validation

```python
# Verify path is within projects directory
project_path = os.path.abspath(project_info['path'])
projects_root_abs = os.path.abspath(self.projects_root)

if not project_path.startswith(projects_root_abs + os.sep):
    raise ValueError("SAFETY ERROR: Path outside projects directory")
```

**Protects against:**
- Deleting files outside the projects workspace
- Symbolic link attacks
- Path traversal exploits

### 2. Identifier Verification

```python
# Check path contains UUID or project name
if project_id not in project_path and project_name_sanitized not in path_basename:
    raise ValueError("SAFETY ERROR: Path doesn't match expected identifiers")
```

**Protects against:**
- Wrong directory deletion
- Corrupted index entries
- Manual path modifications

### 3. Error Recovery

```python
try:
    shutil.rmtree(project_path)
except Exception as e:
    # Re-add to index if deletion failed
    self.project_index[project_id] = project_info
    self.save_index()
    raise  # Let caller handle
```

**Protects against:**
- Partial deletions
- Index corruption
- Inconsistent state

## Recommended Approach: Archive Instead of Delete

### ✅ SAFE: Archive Project

```python
# Creates ZIP backup, then removes from index
archive_path = manager.archive_project(project_id)
print(f"Project safely archived to: {archive_path}")

# Files can be recovered by extracting the ZIP
```

**Advantages:**
- ✅ Data is preserved in ZIP file
- ✅ Can be restored later
- ✅ Automatic timestamped filename
- ✅ Stored in `workspace/projects/archives/`
- ✅ No accidental data loss

### ⚠️ RISKY: Delete Project

```python
# Only remove from index (files remain)
manager.delete_project(project_id, delete_files=False)

# DANGEROUS: Permanently delete files
manager.delete_project(project_id, delete_files=True)  # ⚠️ USE WITH EXTREME CAUTION
```

## UI/UX Safety Guidelines

### Required Confirmations

When implementing delete functionality in UI, require:

1. **Two-step confirmation**
   ```
   Step 1: "Are you sure you want to delete this project?"
   Step 2: "This will PERMANENTLY delete all files. Type the project name to confirm: ____"
   ```

2. **Visual warnings**
   - Use ⚠️ WARNING icons
   - Red color scheme for destructive actions
   - Clear explanation of consequences

3. **Default to safe option**
   ```python
   # UI should offer these options in order:
   [ ] Archive project (keep ZIP backup) ✓ RECOMMENDED
   [ ] Remove from list only (keep files)
   [ ] Permanently delete all files ⚠️ CANNOT UNDO
   ```

### Example Dialog Code

```python
def confirm_project_deletion(self, project_name: str, delete_files: bool) -> bool:
    """Show confirmation dialog for project deletion.
    
    Args:
        project_name: Name of project to delete
        delete_files: Whether files will be deleted
        
    Returns:
        True if user confirms, False otherwise
    """
    if delete_files:
        # CRITICAL: Require explicit confirmation
        dialog = Gtk.MessageDialog(
            transient_for=self.parent_window,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.NONE,
            text=f"⚠️ PERMANENTLY DELETE PROJECT?"
        )
        
        dialog.format_secondary_text(
            f"This will delete ALL files in project '{project_name}'.\n\n"
            f"This action CANNOT be undone!\n\n"
            f"Consider archiving instead to keep a backup.\n\n"
            f"Type the project name to confirm:"
        )
        
        # Add entry for name confirmation
        content_area = dialog.get_content_area()
        entry = Gtk.Entry()
        entry.set_placeholder_text(project_name)
        content_area.pack_start(entry, False, False, 6)
        
        dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
        delete_button = dialog.add_button("Delete Forever", Gtk.ResponseType.YES)
        delete_button.get_style_context().add_class("destructive-action")
        
        dialog.show_all()
        response = dialog.run()
        confirmed_name = entry.get_text()
        dialog.destroy()
        
        # Require exact name match
        return response == Gtk.ResponseType.YES and confirmed_name == project_name
        
    else:
        # Simple confirmation for index removal only
        dialog = Gtk.MessageDialog(
            transient_for=self.parent_window,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            text=f"Remove project '{project_name}' from list?"
        )
        
        dialog.format_secondary_text(
            "Project files will remain on disk.\n"
            "You can re-import the project later."
        )
        
        response = dialog.run()
        dialog.destroy()
        
        return response == Gtk.ResponseType.YES
```

## Safety Checklist for Developers

Before implementing project deletion UI:

- [ ] **Use `archive_project()` by default** (not `delete_project()`)
- [ ] **Require two-step confirmation** for permanent deletion
- [ ] **Show warning icons and red colors** for destructive actions
- [ ] **Require typing project name** for file deletion confirmation
- [ ] **Explain consequences clearly** ("cannot be undone")
- [ ] **Offer "Archive" as recommended option**
- [ ] **Log deletion actions** for audit trail
- [ ] **Test with valuable data** to ensure confirmation works
- [ ] **Consider "trash" system** (soft delete with 30-day retention)
- [ ] **Document recovery procedures** if available

## Alternative Approaches

### 1. Soft Delete (Recommended)

```python
def soft_delete_project(self, project_id: str) -> bool:
    """Move project to 'deleted' state with 30-day retention.
    
    Project can be restored within 30 days, then permanently deleted.
    """
    # Move to .trash/ directory
    # Add deletion_date to metadata
    # Implement auto-cleanup after 30 days
```

### 2. Trash System

```
workspace/
  projects/         ← Active projects
  archives/         ← Archived projects (ZIP files)
  trash/            ← Deleted projects (recoverable for 30 days)
    project_name_deleted_20251008/
      .metadata     ← Contains deletion date
      [project files]
```

### 3. Export Before Delete

```python
# Always export/archive before allowing deletion
archive = manager.archive_project(project_id)
print(f"Backup created: {archive}")

# Now safe to delete
manager.delete_project(project_id, delete_files=True)
```

## Recovery Procedures

### If Deletion Was Accidental

1. **Index-only deletion** (`delete_files=False`):
   ```python
   # Files still exist, can be re-imported
   manager.open_project_by_path('/path/to/project/project.shy')
   ```

2. **File deletion** (`delete_files=True`):
   - ❌ Cannot recover without backup
   - Check OS trash/recycle bin (may not work for `shutil.rmtree`)
   - Restore from external backup if available
   - Use disk recovery tools (low success rate)

### If Archive Exists

```python
# Extract archive to original location
import shutil
shutil.unpack_archive('archive.zip', 'workspace/projects/restored_project/')

# Re-import to index
manager.open_project_by_path('workspace/projects/restored_project/project.shy')
```

## Security Considerations

### Path Traversal Prevention

```python
# VULNERABLE (DON'T DO THIS):
user_path = input("Enter path: ")
shutil.rmtree(user_path)  # ⚠️ DANGEROUS!

# SAFE (with validation):
if not os.path.abspath(user_path).startswith(projects_root):
    raise ValueError("Invalid path")
```

### Symbolic Link Protection

```python
# Check for symbolic links
if os.path.islink(project_path):
    raise ValueError("Cannot delete symbolic links")

# Resolve real path
real_path = os.path.realpath(project_path)
if not real_path.startswith(projects_root):
    raise ValueError("Link points outside projects directory")
```

## Summary

| Method | Safety Level | Reversible | Use Case |
|--------|-------------|-----------|----------|
| `archive_project()` | ✅ SAFE | ✅ Yes | **Recommended default** |
| `delete_project(delete_files=False)` | ⚠️ MODERATE | ✅ Yes | Remove from list |
| `delete_project(delete_files=True)` | ❌ DANGEROUS | ❌ No | Use with extreme caution |

**ALWAYS prefer archiving over deletion to prevent accidental data loss!**

## Best Practices

1. ✅ **Default to archive**: Make archiving the primary action
2. ✅ **Require confirmation**: Multiple steps for permanent deletion
3. ✅ **Visual warnings**: Use ⚠️ icons and red colors
4. ✅ **Type to confirm**: Require typing project name
5. ✅ **Educate users**: Explain consequences clearly
6. ✅ **Log actions**: Audit trail for deletions
7. ✅ **Test thoroughly**: Ensure confirmations work as expected
8. ✅ **Consider trash system**: 30-day recovery window

**Remember:** It's better to have users complain about "too many confirmations" than to lose their data permanently!
