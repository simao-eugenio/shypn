# Directory Structure Guide

## Overview
This document explains the organization of directories in the shypn project. The structure has been designed to clearly separate different types of data and avoid confusion.

## Root Directory Structure

```
shypn/
├── workspace/         # User workspace (NEW)
│   ├── examples/      # Demo files (formerly models/)
│   │   ├── simple.shy     # Simple example Petri net
│   │   └── pathways/      # KEGG pathway examples
│   ├── projects/      # User-created projects (gitignored)
│   └── cache/         # Transient external data (gitignored)
│       └── kegg/      # Downloaded KEGG data
├── src/               # Source code
├── tests/             # Unit tests
├── ui/                # GTK UI definitions
├── doc/               # Documentation
└── ...
```

## Directory Purposes

### 1. `workspace/` (NEW - User Workspace Container)
**Purpose**: Single directory containing all user-facing data (examples, projects, cache)

**Why workspace/?**
- **Isolation**: Keeps user data completely separate from application code
- **Safety**: Users can't accidentally modify `src/`, `ui/`, `tests/`
- **Clarity**: Everything in workspace/ is user-accessible
- **Git-friendly**: Easy to track examples/ while ignoring projects/ and cache/

**Structure**:
```
workspace/
├── examples/     (git tracked) - Demo files for learning
├── projects/     (gitignored)  - User's work
└── cache/        (gitignored)  - Downloaded external data
```

### 2. `workspace/examples/` (formerly `models/`)
**Purpose**: Demonstration files and examples for users to learn from

**Contents**:
- `simple.shy` - Basic Petri net example
- `pathways/` - KEGG pathway examples (hsa00010, hsa00020, hsa00030)

**Usage**:
- Read-only (from user perspective)
- Shipped with the application
- Default directory when browsing files
- Used for tutorials and documentation

**Git Tracking**: ✅ Yes (committed to repository)

**Why renamed?**
- Original name `models/` was ambiguous (data models vs example models?)
- `examples/` clearly indicates these are demo/sample files
- Reduces confusion with application code

### 3. `workspace/projects/` (NEW)
**Purpose**: Storage for user-created project files

**Contents**:
- User Petri net projects (.shy files)
- Project-specific data
- Organized by project name

**Structure**:
```
workspace/projects/
├── <uuid-1>/
│   ├── project.shy
│   ├── models/
│   ├── pathways/
│   ├── simulations/
│   └── analysis/
├── <uuid-2>/
│   └── ...
└── ...
```

**Usage**:
- User workspace
- Created automatically by ProjectManager
- Saved/restored across sessions
- Recent projects tracked

**Git Tracking**: ❌ No (user's private work)

**Why in workspace/?**
- Grouped with other user-facing directories
- Protected from accidental modification of app code
- Easy to backup (just backup workspace/)
- Clear separation: workspace/ = user data, everything else = app

### 4. `workspace/cache/` (NEW)
**Purpose**: Temporary/downloaded external data that can be regenerated

**Contents**:
- `kegg/` - Downloaded KEGG pathway data (.kgml files)
- Other transient external resources

**Usage**:
- Auto-populated on demand
- Can be deleted and regenerated
- Not tracked in git (add to .gitignore)
- Keeps external data separate from examples

**Git Tracking**: ❌ No (regenerable data)

**Why in workspace/?**
- Grouped with other user data
- Users can safely delete entire workspace/cache/
- Won't interfere with application code

### 5. `src/`, `ui/`, `tests/`, `doc/` (Application Code)
**Purpose**: Application source code, UI definitions, tests, and documentation

**Git Tracking**: ✅ Yes (part of application)

**Why separate from workspace/?**
- Users should not modify these
- Prevents accidental corruption
- Clear distinction: app vs user data

## Migration from Old Structure

### Before (Confusing - Multiple Attempts)
```
# Version 1: Original
shypn/
├── models/            # Examples? Data models? Unclear!
│   ├── simple.shy
│   └── pathways/
├── data/              # What kind of data?
│   └── projects/      # User projects buried here
└── ...

# Version 2: Flat top-level
shypn/
├── examples/          # Demo files
├── projects/          # User work (mixed with app code)
├── cache/             # Cache (mixed with app code)
└── ...
```

### After (Clear - Current)
```
shypn/
├── workspace/         # ALL user data here
│   ├── examples/      # Demos (git tracked)
│   ├── projects/      # User work (gitignored)
│   └── cache/         # Transient (gitignored)
├── src/               # App code
├── ui/                # App UI
└── ...
```

**Key Improvement**: Single `workspace/` directory contains everything users interact with,
completely separate from application code.

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
# Clear: workspace/examples/ for demos
repo_root / 'workspace' / 'examples'

# Clear: workspace/projects/ for user work
repo_root / 'workspace' / 'projects'

# Clear: workspace/cache/ for transient data
repo_root / 'workspace' / 'cache' / 'kegg'
```

### Files Changed
1. **src/shypn/data/project_models.py** (line ~290):
   - Changed: `projects_root = repo_root / 'data' / 'projects'`
   - To: `projects_root = repo_root / 'workspace' / 'projects'`

2. **src/shypn/helpers/left_panel_loader.py** (line ~60):
   - Changed: `base_path = repo_root / 'models'`
   - To: `base_path = repo_root / 'workspace'`  (starts at workspace root)

3. **File browser default path**:
   - Shows `workspace/` with examples/, projects/, cache/ visible
   - User can only navigate within workspace/ (root_boundary set)

4. **.gitignore**:
   ```
   # User data (not committed)
   /workspace/projects/
   /workspace/cache/
   
   # Examples ARE committed
   # /workspace/examples/ is tracked
   ```

## Usage Guidelines

### For Users
- **Browse files**: File Explorer starts in `workspace/`, shows all user-accessible data
- **Examples**: Located in `workspace/examples/` - read-only demo files
- **Create project**: Use "New Project" button, saves to `workspace/projects/<uuid>/`
- **Find your work**: All user projects are in `workspace/projects/`
- **Backup**: Just backup the `workspace/` folder (or just `workspace/projects/`)

### For Developers
- **Add examples**: Put in `workspace/examples/`, commit to git
- **User data**: Always use ProjectManager for `workspace/projects/` access
- **External data**: Download to `workspace/cache/`, add to .gitignore
- **App code**: Keep in `src/`, `ui/`, `tests/` - separate from workspace/

## Best Practices

### 1. Never Mix User Data with Application Code
- ❌ Don't save user projects outside `workspace/`
- ✅ All user data stays in `workspace/` (examples, projects, cache)

### 2. Never Commit User Data or Cache
- ❌ Don't commit `workspace/projects/` or `workspace/cache/` to git
- ✅ Add to .gitignore, only track `workspace/examples/`

### 3. Workspace Boundary Enforcement
- ❌ Don't let file browser navigate to `src/`, `ui/`, `tests/`
- ✅ Set `root_boundary` to `workspace/` in file explorer

### 4. Clear Directory Purpose
- ❌ Don't create ambiguous directory names
- ✅ Name directories by their clear purpose
- ✅ Group related data (all user data in workspace/)

## .gitignore Configuration

```gitignore
# User projects (not committed)
/workspace/projects/

# Cache (regenerated)
/workspace/cache/

# Examples ARE tracked (omit from .gitignore)
# /workspace/examples/ should be committed

# Python cache
__pycache__/
*.pyc

# OS files
.DS_Store
Thumbs.db
```

## Future Considerations

### Workspace Advantages
1. **Security**: Users can't accidentally modify app code
2. **Portability**: Easy to backup/restore just workspace/
3. **Clarity**: Single location for all user-facing data
4. **Flexibility**: Can add new user data types to workspace/ easily

### Potential Enhancements
1. **Multiple workspaces**: Allow users to switch workspaces
2. **Workspace settings**: Per-workspace configuration
3. **Workspace export**: Package entire workspace for sharing
4. **Remote workspaces**: Cloud storage integration

## Related Documentation
- `DIRECTORY_STRUCTURE_ANALYSIS.md` - Full analysis and options considered
- `PROJECT_MANAGEMENT_IMPLEMENTATION.md` - Project management system
- `PATHWAY_DATA_ISOLATION_PLAN.md` - KEGG data handling (needs update)

## Summary

**The Goal**: Isolate user data from application code with a clear workspace container

| Directory | Purpose | Type | Git Tracked |
|-----------|---------|------|-------------|
| `workspace/` | User data container | Container | Partial |
| `workspace/examples/` | Demo files | Read-only | ✅ Yes |
| `workspace/projects/` | User work | Read-write | ❌ No |
| `workspace/cache/` | External data | Transient | ❌ No |
| `src/`, `ui/`, etc. | App code | App-only | ✅ Yes |

**User Mental Model**: 
- "Everything I need is in workspace/"
- "Examples are for learning"
- "Projects are my work"
- "Cache can be deleted"
- "I don't need to touch anything outside workspace/"

**Developer Mental Model**:
- "User data lives in workspace/ only"
- "App code lives outside workspace/"
- "File explorer is sandboxed to workspace/"
- "Never let users modify src/, ui/, tests/"

Simple, clear, secure, unambiguous. ✨
