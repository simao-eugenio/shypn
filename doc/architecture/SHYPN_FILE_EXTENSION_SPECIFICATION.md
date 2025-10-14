# Shypn File Extension Specification

**Date**: October 2025  
**Status**: ✅ Official Specification

## Official File Extension

**Primary Extension**: `.shy`

**Legacy Extension**: `.shypn` (supported for backward compatibility)

## Rationale

The `.shy` extension was chosen as the primary Shypn file extension for the following reasons:

1. **Brevity**: Shorter extension is easier to type and cleaner in file listings
2. **Uniqueness**: `.shy` is distinctive and less likely to conflict with other formats
3. **Branding**: Closely matches the project name "SHYpn"
4. **User Experience**: Simpler for users to remember and use

## Format Specification

### File Type
- **Type**: Stochastic Hybrid Petri Net model file
- **Format**: JSON-based structured data
- **Encoding**: UTF-8
- **MIME Type**: `application/x-shypn` (proposed)

### File Structure
```json
{
  "version": "1.0",
  "model_type": "petri_net",
  "places": [...],
  "transitions": [...],
  "arcs": [...],
  "metadata": {...}
}
```

## Extension Registration

### Metadata Manager Factory

The metadata management system recognizes both `.shy` and `.shypn` extensions:

```python
# From metadata_manager_factory.py
_extension_preferences = {
    ".shy": MetadataFormat.JSON,      # Primary extension ✅
    ".shypn": MetadataFormat.JSON,    # Legacy support ✅
    ".sbml": MetadataFormat.XML,
    ".xml": MetadataFormat.XML,
}
```

### Auto-Detection

The system automatically detects the file extension and applies appropriate metadata format:

```python
from shypn.crossfetch.metadata import create_metadata_manager

# Works with .shy (primary)
manager = create_metadata_manager(Path("model.shy"))

# Also works with .shypn (legacy)
manager = create_metadata_manager(Path("model.shypn"))
```

## File Naming Conventions

### Recommended Naming

**Best Practices**:
```
✅ glycolysis.shy              # Good: descriptive, lowercase
✅ tca_cycle.shy               # Good: underscore for spaces
✅ glycolysis_v2.shy           # Good: version suffix
✅ human_glycolysis.shy        # Good: organism prefix

❌ Glycolysis.shy              # Avoid: mixed case
❌ glycolysis pathway.shy      # Avoid: spaces
❌ glycolysis-model.shy        # OK but prefer underscore
```

### Project Structure

```
project_name/
├── models/
│   ├── glycolysis.shy
│   ├── tca_cycle.shy
│   └── pentose_phosphate.shy
├── metadata/
│   ├── glycolysis.shy.meta.json
│   ├── tca_cycle.shy.meta.json
│   └── pentose_phosphate.shy.meta.json
└── README.md
```

## Metadata Files

### Naming Pattern

Metadata files follow the pattern: `<model_name>.shy.meta.json`

**Examples**:
- Model: `glycolysis.shy` → Metadata: `glycolysis.shy.meta.json`
- Model: `tca_cycle.shy` → Metadata: `tca_cycle.shy.meta.json`
- Model: `my_model.shypn` → Metadata: `my_model.shypn.meta.json` (legacy)

### Location

Metadata files are stored in the `metadata/` subdirectory at the project root:

```
project/
├── models/                    # Model files
│   └── glycolysis.shy
└── metadata/                  # Metadata files
    └── glycolysis.shy.meta.json
```

## Migration Guide

### From .shypn to .shy

To migrate existing `.shypn` files to `.shy`:

#### Option 1: Manual Rename (Simple)

```bash
# In project directory
for f in models/*.shypn; do
    mv "$f" "${f%.shypn}.shy"
done
```

#### Option 2: Using Tracker (Recommended)

```python
from pathlib import Path
from shypn.crossfetch.metadata import FileOperationsTracker

tracker = FileOperationsTracker()

# Rename each file (automatically updates metadata)
for old_file in Path("models").glob("*.shypn"):
    new_file = old_file.with_suffix(".shy")
    tracker.rename_file(old_file, new_file, user="migration_script")
```

#### Option 3: Batch Script

```python
#!/usr/bin/env python3
"""Migrate .shypn files to .shy extension."""

from pathlib import Path
from shypn.crossfetch.metadata import FileOperationsTracker

def migrate_project(project_dir: Path):
    """Migrate all .shypn files in project to .shy."""
    tracker = FileOperationsTracker()
    
    # Find all .shypn files
    shypn_files = list(project_dir.rglob("*.shypn"))
    
    if not shypn_files:
        print("No .shypn files found")
        return
    
    print(f"Found {len(shypn_files)} files to migrate")
    
    for old_file in shypn_files:
        new_file = old_file.with_suffix(".shy")
        print(f"  {old_file.name} → {new_file.name}")
        tracker.rename_file(old_file, new_file, user="migration")
    
    print(f"\n✅ Migration complete: {len(shypn_files)} files")

if __name__ == "__main__":
    migrate_project(Path("workspace/projects"))
```

## Backward Compatibility

### Legacy Support

The system maintains full backward compatibility with `.shypn` files:

**Supported Operations**:
- ✅ Open/Load `.shypn` files
- ✅ Save `.shypn` files
- ✅ Create metadata for `.shypn` files
- ✅ All operations work with both extensions

**No Breaking Changes**:
- Existing `.shypn` files continue to work
- No forced migration required
- Users can migrate at their own pace

### Recommendation

**For New Projects**: Use `.shy` extension  
**For Existing Projects**: Migrate when convenient or keep `.shypn`

## OS-Specific Considerations

### Linux/Unix
```bash
# File association (example for GNOME)
xdg-mime default shypn.desktop application/x-shypn
```

### Windows
```
# File association can be set in:
# Settings → Apps → Default apps → Choose default apps by file type
# Associate .shy with SHYpn application
```

### macOS
```bash
# Use duti or manual association in Finder
duti -s org.shypn.editor .shy all
```

## IDE Integration

### VS Code

Create `.vscode/settings.json`:
```json
{
  "files.associations": {
    "*.shy": "json",
    "*.shypn": "json"
  },
  "files.defaultLanguage": "json"
}
```

### PyCharm

Settings → Editor → File Types → Add pattern `*.shy` to JSON file type

## Summary

| Aspect | Details |
|--------|---------|
| **Primary Extension** | `.shy` |
| **Legacy Extension** | `.shypn` (supported) |
| **Format** | JSON-based |
| **MIME Type** | `application/x-shypn` |
| **Metadata Pattern** | `<name>.shy.meta.json` |
| **Backward Compatible** | ✅ Yes |
| **Migration Required** | ❌ No (optional) |
| **Status** | ✅ Official |

## References

- **Metadata Management**: `METADATA_MANAGEMENT_USAGE_GUIDE.md`
- **Quick Reference**: `METADATA_MANAGEMENT_QUICK_REFERENCE.md`
- **Implementation**: `src/shypn/crossfetch/metadata/metadata_manager_factory.py`

---

**Specification Version**: 1.0  
**Last Updated**: October 2025  
**Status**: ✅ Official Shypn File Extension Specification
