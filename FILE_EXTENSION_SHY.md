# File Extension Change: .json → .shy

**Date**: October 4, 2025  
**Status**: ✅ Implemented  
**Extension**: `.shy` (SHYpn Petri net files)

## Summary

Changed the file extension for SHYpn Petri net documents from `.json` to `.shy` to:
1. Establish a unique file type for SHYpn
2. Enable proper file type association
3. Make it clear which files are SHYpn documents

## Changes Made

### 1. **NetObjPersistency** (`src/shypn/file/netobj_persistency.py`)

#### Save Dialog
- **Filter**: Changed from "Petri Net files (*.json)" to "SHYpn Petri Net files (*.shy)"
- **Default Name**: Changed from "default.json" to "default.shy"
- **Extension Check**: Changed from `.endswith('.json')` to `.endswith('.shy')`
- **Warning Dialog**: Updated default filename warning to use "default.shy"

#### Open Dialog
- **Filter**: Changed from "Petri Net files (*.json)" to "SHYpn Petri Net files (*.shy)"
- File chooser now filters to show `.shy` files by default

### 2. **File Explorer Panel** (`src/shypn/ui/panels/file_explorer_panel.py`)

#### File Opening
- **Double-click check**: Changed from `.endswith('.json')` to `.endswith('.shy')`
- **Context menu**: Updated "Open" action to check for `.shy` extension
- **Error message**: Changed to "Can only open .shy Petri net files"

### 3. **File Explorer API** (`src/shypn/file/explorer.py`)

#### Icon Assignment
- Added `.shy` extension to icon map with special icon: `'application-x-executable-symbolic'`
- Positioned as first entry to indicate it's the primary format
- `.shy` files now display with application icon in file browser

## Default Filename Warning

When users try to save with the default filename "default.shy", they see:

```
⚠️ Save as 'default.shy'?

You are about to save with the default filename 'default.shy'.

This may overwrite existing default files or make it hard to 
identify this model later.

Do you want to continue with this filename?

[No] [Yes]
```

If user clicks "No", the file chooser dialog reopens for them to enter a custom name.

## File Format

The `.shy` files remain JSON format internally:

```json
{
  "metadata": {
    "version": "1.0",
    "created": "2025-10-04T10:30:00",
    "modified": "2025-10-04T12:45:00"
  },
  "places": [...],
  "transitions": [...],
  "arcs": [...]
}
```

The `.shy` extension is purely for file type identification and OS integration.

## Backwards Compatibility

**Note**: Existing `.json` files will need to be:
1. Renamed to `.shy` extension, OR
2. Opened via "All files" filter in file chooser

The application does not automatically migrate old files.

## Testing

To test the new extension:

1. **Create New File**:
   ```bash
   ./run.sh
   # Click "📄 New" → Draw something → Click "💾 Save"
   # File chooser shows "default.shy" pre-filled
   ```

2. **Default Name Warning**:
   ```bash
   # Try to save as "default.shy"
   # Warning dialog appears
   # Click "No" to change name
   ```

3. **File Explorer**:
   ```bash
   # .shy files show with application icon
   # Double-click .shy file to open
   # Context menu "Open" only works for .shy files
   ```

## Future Enhancements

### File Type Association (Linux)
Create `.desktop` file for system integration:

```desktop
[Desktop Entry]
Name=SHYpn
Exec=shypn %f
MimeType=application/x-shypn;
Icon=shypn
Type=Application
```

Register MIME type:
```xml
<?xml version="1.0"?>
<mime-info xmlns='http://www.freedesktop.org/standards/shared-mime-info'>
  <mime-type type="application/x-shypn">
    <comment>SHYpn Petri Net</comment>
    <glob pattern="*.shy"/>
  </mime-type>
</mime-info>
```

### Custom Icon
Design and register a custom `.shy` file icon instead of using generic application icon.

## Files Modified

1. `src/shypn/file/netobj_persistency.py` - Save/load dialogs and extension handling
2. `src/shypn/ui/panels/file_explorer_panel.py` - File opening and validation
3. `src/shypn/file/explorer.py` - Icon assignment for `.shy` files

---

**Status**: ✅ All changes complete and ready for testing!
