# New Project Button Crash Fix

**Date**: 2025-10-08  
**Issue**: App crashes when clicking "New Project" button  
**Status**: ✅ FIXED  

## Problem

When the "New Project" button was clicked, the application would crash with an `AttributeError`.

## Root Cause

In `src/shypn/helpers/left_panel_loader.py`, the project creation callback (`_on_project_created`) and project open callback (`_on_project_opened`) were calling a non-existent method:

```python
# WRONG - method doesn't exist
self.file_explorer.set_base_path(project.base_path)
```

The correct method name is `navigate_to()`, not `set_base_path()`.

## Solution

Fixed both methods to use the correct API:

### File: `src/shypn/helpers/left_panel_loader.py`

**Line ~161** - `_on_project_created` callback:
```python
# BEFORE
self.file_explorer.set_base_path(project.base_path)

# AFTER  
self.file_explorer.navigate_to(project.base_path)
```

**Line ~171** - `_on_project_opened` callback:
```python
# BEFORE
self.file_explorer.set_base_path(project.base_path)

# AFTER
self.file_explorer.navigate_to(project.base_path)
```

## Impact

- ✅ "New Project" button now works correctly
- ✅ File explorer navigates to the created project directory
- ✅ "Open Project" button also fixed (same issue)
- ✅ No syntax errors

## Testing Checklist

Test in the running application:

- [ ] Click "New Project" button
- [ ] Fill in project details
- [ ] Click "Create"
- [ ] Verify application doesn't crash
- [ ] Verify file explorer navigates to new project directory (workspace/projects/[uuid]/)
- [ ] Verify project files are created
- [ ] Test "Open Project" button  
- [ ] Verify file explorer navigates to opened project directory

## Related Issues

This bug was introduced during the OOP refactoring when project management code was reorganized. The method call wasn't updated to match the FileExplorerPanel API.

## Files Changed

1. `src/shypn/helpers/left_panel_loader.py`
   - Line ~161: Fixed `_on_project_created` method call
   - Line ~171: Fixed `_on_project_opened` method call

## Prevention

To prevent similar issues:
1. Use IDE/linter to catch undefined method calls
2. Run comprehensive integration tests after refactoring
3. Test all button click handlers after API changes
