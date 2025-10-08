# Workspace Directory

This directory contains all user-accessible content for the shypn application.

## Structure

```
workspace/
├── examples/       # Demo Petri net models and pathways
├── projects/       # User-created projects
└── cache/          # Downloaded data and temporary files
    └── kegg/       # KEGG pathway cache
```

## Purpose

The workspace directory is designed to:

1. **Isolate user content** from application code
2. **Prevent accidental corruption** of critical files (src/, tests/, ui/)
3. **Organize user data** in a clear, predictable structure
4. **Provide a safe sandbox** for file operations

## Directories

### examples/
Contains demonstration models that ship with shypn:
- `simple.shy` - Basic Petri net example
- `pathways/` - KEGG pathway examples

These files are tracked in version control and provide starting points for learning.

### projects/
User-created project directories. Each project contains:
- `project.shy` - Project metadata
- `*.shy` - Petri net models
- Other project-specific files

This directory is NOT tracked in version control (see `.gitignore`).

### cache/
Temporary and downloaded data:
- `kegg/` - Cached KEGG pathway data (prevents repeated API calls)

This directory is NOT tracked in version control.

## File Explorer Navigation

The shypn file explorer is restricted to the workspace directory:
- You can navigate freely within `workspace/`
- You cannot navigate to parent directories (`src/`, `tests/`, `ui/`, etc.)
- This prevents accidental deletion or modification of application code

## Security Note

**Important**: The workspace directory is the ONLY location where users can:
- Create files
- Delete files
- Modify content

All application code, UI definitions, and tests are protected outside this directory.
