# Python Packaging Rules and Conventions

**Date:** October 3, 2025  
**Topic:** Directory structure and naming for Python packages

---

## The Short Answer

**There are NO fixed rules enforced by Python**, but there are **strong conventions** that tools expect. The package structure is primarily a matter of:

1. ✅ **Convention** - What the community expects
2. ✅ **Tool compatibility** - What packaging tools understand
3. ✅ **Import paths** - How Python resolves imports
4. ⚠️ **Personal preference** - Your project's needs

---

## Python Package Mechanics

### What Makes a Package?

A Python package is simply:
```
directory/
├── __init__.py      # This file makes it a package
└── module.py        # Regular Python module
```

**Key Rule:** Any directory with `__init__.py` is a package.

### Import Resolution

Python finds packages using:
1. `sys.path` - List of directories to search
2. Relative position to your project root
3. `PYTHONPATH` environment variable (optional)

---

## Directory Naming Rules

### Technical Rules (Python enforces these):

1. **Valid Python identifiers:**
   - ✅ Letters, numbers, underscores
   - ✅ Must start with letter or underscore
   - ❌ No hyphens, spaces, or special characters
   
   ```python
   # Valid:
   my_package/
   mypackage/
   _internal/
   module123/
   
   # Invalid (import error):
   my-package/      # Hyphens not allowed
   my package/      # Spaces not allowed
   123module/       # Can't start with number
   ```

2. **Avoid Python keywords:**
   - ❌ Don't name packages: `class/`, `import/`, `def/`, etc.

3. **Case sensitivity:**
   - ⚠️ Linux/Mac: case-sensitive (`Data/` ≠ `data/`)
   - ⚠️ Windows: case-insensitive (but preserves case)
   - **Best practice:** Always use lowercase for consistency

---

## Conventional Structure (PEP 8 Guidelines)

### Standard Project Layout

```
project_root/
├── src/                    # Source code (modern convention)
│   └── myproject/         # Main package
│       ├── __init__.py
│       ├── module1.py
│       └── subpackage/
│           ├── __init__.py
│           └── module2.py
├── tests/                  # Test directory (outside src/)
├── docs/                   # Documentation
├── setup.py               # Package configuration (old style)
├── pyproject.toml         # Package configuration (new style)
└── README.md
```

### Common Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| **Packages** | `lowercase` or `lowercase_with_underscores` | `requests/`, `data_processing/` |
| **Modules** | `lowercase` or `lowercase_with_underscores` | `utils.py`, `file_handler.py` |
| **Classes** | `PascalCase` | `class DocumentCanvas:` |
| **Functions** | `snake_case` | `def calculate_bounds():` |
| **Constants** | `UPPER_CASE` | `MAX_ZOOM = 3.0` |

---

## Your Specific Case: `src/shypn/data/canvas/`

### Is This Structure Valid?

**YES, absolutely!** ✅

```python
# This will work perfectly:
from shypn.data.canvas import DocumentCanvas
from shypn.data.canvas.document_model import DocumentModel
```

### Why It Works:

1. **All names are valid identifiers:**
   - `shypn` ✅
   - `data` ✅
   - `canvas` ✅
   - `document_canvas` ✅

2. **Follows Python conventions:**
   - All lowercase
   - Uses underscores for multi-word names
   - Clear, descriptive names

3. **Nested packages are standard:**
   - Python fully supports deep nesting
   - Django, Flask, etc. use similar structures

---

## Packaging Tools and Structure

### setup.py / pyproject.toml

These files tell packaging tools what to include:

#### Option 1: Automatic discovery (modern)
```toml
# pyproject.toml
[tool.setuptools.packages.find]
where = ["src"]  # Look for packages here
include = ["shypn*"]  # Include all shypn packages
```

**Result:** Automatically finds:
- `shypn/`
- `shypn/data/`
- `shypn/data/canvas/`
- `shypn/controllers/`
- etc.

#### Option 2: Explicit listing (old style)
```python
# setup.py
from setuptools import setup, find_packages

setup(
    name="shypn",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
)
```

**Result:** Same automatic discovery.

#### Option 3: Manual listing
```python
# setup.py
setup(
    name="shypn",
    packages=[
        "shypn",
        "shypn.data",
        "shypn.data.canvas",  # Must list explicitly
        "shypn.controllers",
        # ... etc
    ],
)
```

### Your Choice Matters When:

1. **Using find_packages()** - It automatically discovers all packages with `__init__.py`
2. **Manual listing** - You control exactly what's included
3. **Excluding packages** - Use `exclude` parameter

---

## Best Practices for Your Project

### 1. Use Descriptive Names ✅

```python
# Good:
src/shypn/data/canvas/document_canvas.py
src/shypn/controllers/editing_controller.py

# Avoid:
src/shypn/d/c/dc.py  # Too cryptic
src/shypn/stuff/things.py  # Too vague
```

### 2. Consistent Depth ✅

```python
# Consistent:
src/shypn/data/canvas/
src/shypn/controllers/tools/
src/shypn/renderers/

# Inconsistent (confusing):
src/shypn/data/canvas/things/stuff/
src/shypn/controllers/  # Much shallower
```

### 3. Avoid Deep Nesting ⚠️

```python
# Reasonable (3-4 levels):
from shypn.data.canvas.document_model import DocumentModel

# Too deep (hard to import):
from shypn.data.models.canvas.documents.petri.nets.model import X
```

**Rule of thumb:** 3-4 levels of nesting is good, 5+ is questionable.

### 4. Use __init__.py for Convenience ✅

```python
# src/shypn/data/canvas/__init__.py
"""Canvas data models."""
from .document_canvas import DocumentCanvas
from .document_model import DocumentModel
from .canvas_state import DocumentState, ViewportState

__all__ = ['DocumentCanvas', 'DocumentModel', 'DocumentState', 'ViewportState']

# Now you can do:
from shypn.data.canvas import DocumentCanvas  # ✅ Clean import
# Instead of:
from shypn.data.canvas.document_canvas import DocumentCanvas  # ❌ Verbose
```

---

## Common Patterns in Python Projects

### 1. Django Style (app-based)
```
myproject/
├── myapp/
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   └── product.py
│   ├── views/
│   └── controllers/
```

### 2. Flask Style (feature-based)
```
myapp/
├── auth/
│   ├── __init__.py
│   ├── routes.py
│   └── models.py
├── blog/
│   ├── __init__.py
│   ├── routes.py
│   └── models.py
```

### 3. MVC Style (layer-based) ← Your approach
```
myapp/
├── models/        # Data layer
├── views/         # UI layer
├── controllers/   # Logic layer
└── utils/         # Helpers
```

**Your choice (`data/`, `controllers/`, `renderers/`)** is perfectly valid! ✅

---

## Packaging Your Project

### Modern Approach (pyproject.toml)

```toml
# pyproject.toml
[build-system]
requires = ["setuptools>=45", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "shypn"
version = "0.1.0"
description = "Petri Net Editor"
requires-python = ">=3.8"

[tool.setuptools]
package-dir = {"" = "src"}

[tool.setuptools.packages.find]
where = ["src"]
include = ["shypn*"]
```

**Result:** All packages under `src/shypn/` are automatically discovered.

### What Gets Packaged:

```
Distribution includes:
✅ shypn/__init__.py
✅ shypn/data/__init__.py
✅ shypn/data/canvas/__init__.py
✅ shypn/data/canvas/document_canvas.py
✅ shypn/data/canvas/document_model.py
✅ shypn/controllers/__init__.py
✅ ... (all packages with __init__.py)

Excluded by default:
❌ tests/
❌ docs/
❌ __pycache__/
❌ *.pyc files
```

---

## Special Considerations

### 1. Namespace Packages (Advanced)

If you want split packages across directories:
```python
# No __init__.py needed (PEP 420)
# But we recommend always using __init__.py for clarity
```

### 2. Entry Points

For executable scripts:
```toml
[project.scripts]
shypn = "shypn.main:main"  # Creates `shypn` command
```

### 3. Data Files

Include non-Python files:
```toml
[tool.setuptools.package-data]
shypn = ["ui/**/*.ui", "data/**/*.json"]
```

---

## Answer to Your Question

### Can you choose file structure freely?

**YES!** ✅ With these guidelines:

1. **Names must be valid Python identifiers** (no hyphens, no spaces)
2. **Add `__init__.py` to every package directory**
3. **Follow conventions** (lowercase, underscores for multi-word)
4. **Configure packaging tool** (usually automatic with `find_packages()`)

### Your proposed structure is PERFECT:

```
src/shypn/data/canvas/
├── __init__.py
├── canvas_state.py
├── document_model.py
└── document_canvas.py
```

**Why it's good:**
- ✅ Valid Python identifiers
- ✅ Follows conventions
- ✅ Clear, descriptive names
- ✅ Reasonable depth (3 levels)
- ✅ Will be auto-discovered by `find_packages()`

---

## Recommendation for Your Project

**Keep your proposed structure!** It's:
- Professional
- Conventional
- Maintainable
- Tool-friendly

Just ensure:
1. Every directory has `__init__.py`
2. Use descriptive names
3. Keep consistent depth
4. Document your structure (you're already doing this!)

---

## Summary

| Aspect | Rule Type | Your Structure |
|--------|-----------|----------------|
| **Valid identifiers** | ✅ Required | ✅ Perfect |
| **__init__.py files** | ✅ Required | ✅ Will add |
| **Lowercase names** | ⭐ Convention | ✅ Yes |
| **Clear names** | ⭐ Convention | ✅ Excellent |
| **Reasonable depth** | ⭐ Best practice | ✅ Good |
| **Tool compatibility** | ⭐ Important | ✅ Compatible |

**Verdict:** Your structure is excellent! Proceed with confidence. ✅
