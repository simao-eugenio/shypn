# Directory Structure Guide

## Overview
This document explains the organization of directories in the shypn project. The structure has been designed to clearly separate different types of data and avoid confusion.

## Root Directory Structure

```
shypn/
├── examples/          # Demo files (formerly models/)
│   ├── simple.shy     # Simple example Petri net
│   └── pathways/      # KEGG pathway examples
├── projects/          # User-created projects (NEW)
├── cache/             # Transient external data (NEW)
│   └── kegg/          # Downloaded KEGG data
├── data/              # Application resources
│   └── templates/     # Project templates
├── src/               # Source code
├── tests/             # Unit tests
├── ui/                # GTK UI definitions
├── doc/               # Documentation
└── ...
```

## Directory Purposes

### 1. `examples/` (formerly `models/`)
**Purpose**: Demonstration files and examples for users to learn from

**Contents**:
- `simple.shy` - Basic Petri net example
- `pathways/` - KEGG pathway examples (hsa00010, hsa00020, hsa00030)

**Usage**:
- Read-only (from user perspective)
- Shipped with the application
- Default directory when browsing files
- Used for tutorials and documentation

**Why renamed?**
- Original name `models/` was ambiguous (data models vs example models?)
- `examples/` clearly indicates these are demo/sample files
- Reduces confusion with `data/` directory

### 2. `projects/` (NEW - Top Level)
**Purpose**: Storage for user-created project files

**Contents**:
- User Petri net projects (.shy files)
- Project-specific data
- Organized by project name

**Structure**:
```
projects/
├── my_project_1/
│   ├── main.shy
│   └── data/
├── my_project_2/
│   └── network.shy
└── ...
```

**Usage**:
- User workspace
- Created automatically by ProjectManager
- Saved/restored across sessions
- Recent projects tracked

**Why top-level?**
- User data should be prominent, not buried
- Easy to find and backup
- Separates user content from application data
- Mirrors common project structures (src/, docs/, projects/)

### 3. `cache/` (NEW)
**Purpose**: Temporary/downloaded external data that can be regenerated

**Contents**:
- `kegg/` - Downloaded KEGG pathway data (.kgml files)
- Other transient external resources

**Usage**:
- Auto-populated on demand
- Can be deleted and regenerated
- Not tracked in git (add to .gitignore)
- Keeps external data separate from examples

**Why separate?**
- Clear distinction: transient vs permanent data
- Large downloaded files don't clutter examples
- Easy to clear cache without affecting user work

### 4. `data/` (Application Resources)
**Purpose**: Application-level resources and templates

**Contents**:
- `templates/` - Project templates
- Other application data files

**Usage**:
- Shipped with application
- Configuration and resource files
- Templates for new projects

**Why minimal?**
- Most "data" moved to clearer locations
- Only truly application-level resources remain

## Migration from Old Structure

### Before (Confusing)
```
shypn/
├── models/            # Examples? Data models? Unclear!
│   ├── simple.shy
│   └── pathways/
├── data/              # What kind of data?
│   └── projects/      # User projects buried here
└── ...
```

### After (Clear)
```
shypn/
├── examples/          # Obviously demo files
├── projects/          # Obviously user work
├── cache/             # Obviously temporary
├── data/              # Obviously app resources
└── ...
```

## Code Changes Required

### Path Updates in Code

#### Before:
```python
# Confusing: models/ used for examples
repo_root / 'models'

# Confusing: user projects buried under data/
repo_root / 'data' / 'projects'
```

#### After:
```python
# Clear: examples/ for demos
repo_root / 'examples'

# Clear: projects/ at top level
repo_root / 'projects'

# Clear: cache/ for transient data
repo_root / 'cache' / 'kegg'
```

### Files Changed
1. **src/shypn/data/project_models.py** (line 417):
   - Changed: `projects_root = repo_root / 'data' / 'projects'`
   - To: `projects_root = repo_root / 'projects'`

2. **src/shypn/helpers/left_panel_loader.py** (line 50):
   - Changed: `base_path = repo_root / 'models'`
   - To: `base_path = repo_root / 'examples'`

3. **Future: KEGG downloaders**:
   - Change download path to: `cache/kegg/`

## Usage Guidelines

### For Users
- **Browse examples**: Use File Explorer, starts in `examples/`
- **Create project**: Use "New Project" button, saves to `projects/`
- **Find your work**: All user files are in `projects/`
- **Backup projects**: Just backup the `projects/` folder

### For Developers
- **Add examples**: Put in `examples/`, commit to git
- **User data**: Always use ProjectManager for `projects/` access
- **External data**: Download to `cache/`, add to .gitignore
- **App resources**: Put in `data/templates/`

## Best Practices

### 1. Never Mix User Data with Examples
- ❌ Don't save user projects in `examples/`
- ✅ Use `projects/` for all user work

### 2. Never Commit User Data or Cache
- ❌ Don't commit `projects/` or `cache/` to git
- ✅ Add to .gitignore

### 3. Clear Naming
- ❌ Avoid ambiguous directory names
- ✅ Name directories by their clear purpose

### 4. Flat Top-Level Structure
- ❌ Don't bury important directories (`data/projects/`)
- ✅ Keep user-facing directories at top level

## .gitignore Recommendations

```gitignore
# User projects (not committed)
/projects/

# Cache (regenerated)
/cache/

# Python cache
__pycache__/
*.pyc
```

## Future Considerations

### Should `data/` be removed entirely?
Currently `data/` only contains `templates/`. Consider:
- Move `templates/` to top level? (`templates/`)
- Move to `src/shypn/templates/`?
- Keep as-is if more app resources are planned

Decision: **Keep for now**, but monitor if it's truly needed.

## Related Documentation
- `DIRECTORY_STRUCTURE_ANALYSIS.md` - Full analysis and options considered
- `PROJECT_MANAGEMENT_IMPLEMENTATION.md` - Project management system
- `PATHWAY_DATA_ISOLATION_PLAN.md` - KEGG data handling (needs update)

## Summary

**The Goal**: Eliminate directory confusion with clear, purpose-driven names

| Directory | Purpose | Type | Git Tracked |
|-----------|---------|------|-------------|
| `examples/` | Demo files | Read-only | Yes |
| `projects/` | User work | Read-write | No |
| `cache/` | External data | Transient | No |
| `data/` | App resources | Read-only | Yes |

**User Mental Model**: 
- "Examples are for learning"
- "Projects are my work"
- "Cache can be deleted"
- "Data is the app's stuff"

Simple, clear, unambiguous. ✨
