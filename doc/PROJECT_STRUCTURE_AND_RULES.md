# Project Structure and Module Distribution Rules

**Generated:** October 1, 2025  
**Purpose:** Comprehensive analysis of the shypn repository structure, module organization guidelines, and architectural policies.

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Repository Structure Overview](#repository-structure-overview)
3. [Module Distribution Rules](#module-distribution-rules)
4. [Architectural Principles](#architectural-principles)
5. [UI Organization Rules](#ui-organization-rules)
6. [Code Style and Conventions](#code-style-and-conventions)
7. [Migration and Legacy Code](#migration-and-legacy-code)
8. [Development Workflow](#development-workflow)

---

## Executive Summary

The shypn project follows a strict object-oriented architecture with clear separation between:
- **Declarative UI** (GTK Builder XML files in `ui/`)
- **Core business logic** (Python classes in `src/shypn/`)
- **Runtime scripts** (developer tools in `scripts/`)
- **Legacy code** (reference implementation in `legacy/`)

**Key Policies:**
- **UI-first decoupling**: All UI definitions must be declarative (no programmatic widget creation in runtime code)
- **No-fallbacks**: Fail fast and loudly; never silently substitute missing resources
- **Object-oriented design**: All core modules use classes, encapsulation, inheritance, and polymorphism
- **GTK4 migration**: All new/refactored UI code must target GTK4

---

## Repository Structure Overview

```
shypn/
├── data/              # Data models, schemas, ORM models, sample data
├── doc/               # Documentation (guides, architecture notes, API docs)
├── legacy/            # Old codebase (reference only, do not modify directly)
├── scripts/           # Developer tools, migration helpers, standalone utilities
├── src/
│   ├── shypn.py       # Application entry point (minimal GTK4 loader)
│   └── shypn/         # Main Python package
│       ├── api/       # Object-oriented API classes and interfaces
│       ├── data/      # Data model files (schemas, ORM models)
│       ├── dev/       # Experimental or in-development code
│       ├── helpers/   # Functional programming helpers (pure functions)
│       └── utils/     # Specific code routines and specialized utilities
├── tests/             # Test suite (mirrors src/ structure)
│   └── scripts/       # General-purpose test scripts
└── ui/                # User interface resources (declarative only)
    ├── canvas/        # Document model interfaces (drawing, canvas)
    ├── dialogs/       # Instantly loadable dialogs (modal/pop-up)
    ├── main/          # Main window interface
    ├── palettes/      # Control interfaces (toolbars, color pickers)
    └── panels/        # Dockable/undockable panels (sidebars, inspectors)
```

---

## Module Distribution Rules

### 1. **src/shypn/api/** — Object-Oriented APIs
- **Purpose:** Main API classes and interfaces
- **Content:** Classes, abstract base classes, interfaces
- **Use OOP:** encapsulation, inheritance, polymorphism
- **Import pattern:** `from shypn.api import ClassName`

### 2. **src/shypn/helpers/** — Functional Helpers
- **Purpose:** Pure functions, stateless utilities
- **Content:** Helper functions without side effects
- **Style:** Functional programming approach
- **Import pattern:** `from shypn.helpers import helper_function`

### 3. **src/shypn/utils/** — Specialized Utilities
- **Purpose:** Specific code routines and specialized utilities
- **Content:** General utility modules, specific algorithms
- **Import pattern:** `from shypn.utils import utility_module`

### 4. **src/shypn/dev/** — Experimental Code
- **Purpose:** In-development code, experimental features
- **Content:** Code under active development, not yet stable
- **Warning:** May be unstable, use with caution in production

### 5. **src/shypn/data/** — Data Models
- **Purpose:** Data structures, schemas, ORM models
- **Content:** Data classes, database models, sample data
- **Import pattern:** `from shypn.data import ModelClass`

### 6. **scripts/** — Developer Tools
- **Purpose:** Standalone scripts not part of core package
- **Content:** Migration helpers, analysis scripts, diagnostic tools
- **Usage:** Run directly, not imported by production code
- **Examples:** `debug_shypn_env.py`, migration utilities

### 7. **tests/** — Test Suite
- **Purpose:** All test code
- **Organization:** Mirror structure of `src/shypn/`
- **Content:** Unit tests, integration tests, test utilities
- **Subdirectory:** `tests/scripts/` for general-purpose test scripts

### 8. **data/** (root level) — Application Data
- **Purpose:** Data files and resources used by the application
- **Content:** Static data, user models, non-code assets
- **Note:** Different from `src/shypn/data/` (which contains code/schemas)

### 9. **doc/** — Documentation
- **Purpose:** Project documentation
- **Content:** Guides, architecture notes, API documentation
- **Format:** Markdown files
- **Audience:** Users and developers

### 10. **legacy/** — Legacy Codebase
- **Purpose:** Old version for reference and migration
- **Policy:** **DO NOT MODIFY DIRECTLY**
- **Workflow:**
  1. Identify useful code in `legacy/`
  2. Refactor and adapt to new OOP structure in `src/shypn/`
  3. Add tests in `tests/`
  4. Remove legacy code only after successful migration and validation

---

## Architectural Principles

### 1. Object-Oriented Design (OOP)

**Policy:** The project is designed with an object-oriented programming approach.

**Requirements:**
- Core logic, APIs, and UI components implemented as **classes**
- Utilize principles: **encapsulation**, **inheritance**, **polymorphism**
- Structure new modules using OOP best practices
- Ensure maintainability and extensibility

**Application:**
- All modules in `src/shypn/api/` must be object-oriented
- Controllers and business logic use class-based design
- Avoid procedural-only modules in core code

### 2. UI-First Decoupling Rule

**Policy:** UI definitions must live in declarative UI files under `ui/`. Project code must not embed UI structure or markup.

**Why:**
- Keeps design editable by non-programmers and designers
- Easier to replace UI frameworks or regenerate views from tools
- Reduces accidental divergence between layout and runtime behavior

**Requirements:**
- Store widget hierarchies, CSS classes, and IDs in `ui/` files (GTK Builder XML, GtkTemplate)
- Controllers (`controller.py`) should:
  - Import the UI file
  - Query widgets by ID
  - Connect signals
  - Expose a small public API
- **DO NOT** create top-level widgets in code except for dynamic containers (rare, must be documented)
- Use data-only objects (dicts/dataclasses) for state between panels/adapters
- Avoid passing GTK objects across adapters or between panels

**Naming convention:** Use `panel_<name>__widget` for widget IDs in UI files

**Good example:**
```python
panel = builder.get_object("panel_transitions_root")
controller = TransitionsController(panel, bus)
```

**Bad example (DO NOT DO):**
```python
panel = Gtk.Box()
panel.append(Gtk.Label("Transitions"))
```

**Enforcement:**
- During code reviews, prefer diffs where `ui/` files change for layout modifications
- `controller.py` should only wire behavior (signal handlers, bus registration)
- Optional lint check: scan for `Gtk.` constructor calls outside `scripts/` or controllers and flag for review

### 3. No-Fallbacks Rule

**Policy:** Do not include runtime fallbacks in application code, especially UI code. Fail fast and loudly instead of silently falling back.

**Definition:** A fallback is any runtime behavior that silently substitutes an alternative implementation, different UI layout, or legacy script when the primary resource (UI file, module, adapter) is missing or fails to load.

**Why:**
- Silent fallbacks hide defects and make debugging/testing harder
- Create inconsistent user experiences depending on runtime state
- Defeat the "UI-first" rule by masking missing or incorrect UI files

**Requirements:**
- On missing UI files or import errors: **raise a clear exception** and fail startup
- Log explicit error with filename, module, and remediation suggestion
- Avoid subprocess-based fallback runners for UI behavior
- Keep legacy test scripts as developer tools in `tools/` or `scripts/`
- **NEVER** call them from production code paths
- Prefer explicit feature flags and staged migration builds over runtime fallback switches

**Error-handling pattern:**
```python
try:
    builder = Gtk.Builder.new_from_file(UI_PATH)
    window = builder.get_object('main_window')
    if window is None:
        raise UIResourceMissingError(f"Object 'main_window' not found in {UI_PATH}")
except Exception as e:
    print(f'ERROR: {e}', file=sys.stderr)
    sys.exit(1)  # Fail loudly, no fallback
```

**Enforcement:**
- CI should run smoke startup test ensuring all declared `ui/` files load correctly
- Failure should block merge
- Code reviews should flag subprocess-launched fallback UI scripts in main runtime

**Migration note:**
- Keep developer-only fallback harnesses in `scripts/` (not `src/`)
- Use only for manual testing
- Mark clearly with README guidance
- Do not wire into `src/shypn.py` or production startup

### 4. GTK4 Migration

**Policy:** This project is incrementally migrating from GTK 3.2+ to GTK 4.

**Requirements:**
- All **new development** and **refactoring** must target **GTK 4**
- When contributing to UI or GTK-related code:
  - Prefer GTK 4 APIs and widgets
  - Update legacy GTK 3 code to GTK 4 when possible
  - Test UI changes thoroughly
- If unsure how to migrate a component:
  - Consult official GTK 3→4 migration guide
  - Open an issue for discussion

**Status:** During transition, some legacy code may still use GTK 3

---

## UI Organization Rules

### UI Directory Structure

```
ui/
├── DOCK_UNDOCK_DESIGN.md    # UI architecture documentation
├── README.md                # UI folder overview
├── main/                    # Main window interface
│   └── main_window.ui       # GTK4 ApplicationWindow
├── canvas/                  # Document model interfaces (canvas, drawing)
├── dialogs/                 # Instantly loadable dialogs (modal/pop-up)
├── palettes/                # Control interfaces (toolbars, color pickers)
│   ├── left_panel.ui
│   ├── right_panel.ui
│   └── transition.ui
└── panels/                  # Dockable/undockable panels (sidebars, inspectors)
```

### UI File Rules

1. **Declarative only:** `ui/` contains **NO Python code**, only UI resource files
2. **Format:** GTK Builder XML (`.ui` files), CSS, images, icons
3. **Organization:**
   - `main/` — main application window
   - `canvas/` — drawing/document interfaces
   - `dialogs/` — modal dialogs, pop-ups (instant load)
   - `palettes/` — toolbars, color pickers, control panels
   - `panels/` — dockable/undockable panels (sidebars, inspectors)

### Panel Architecture (GTK4)

See `ui/DOCK_UNDOCK_DESIGN.md` for full specification.

**High-level architecture:**
- **Main Window** (GTK4): contains `DockManager` and central workspace
- **Panels:** independent UI modules (one per panel) producing a GTK widget
- **DockManager:** API to add/remove/dock/undock panels and persist layout
- **Application Bus:** lightweight pub/sub + request/response for panel communication
- **Adapters:** thin shims exposing legacy logic with new contracts

**Panel contract:**
- Init signature: `init(panel_bus) -> (panel_id, Gtk.Widget)`
- Events on bus: `emit(event_name, payload)`, `on(event_name, handler)`, `request(name, payload) -> result`
- Data shapes: JSON-serializable dicts or Python dataclasses

**Suggested panel layout:**
```
ui/panels/<panel_name>/
  controller.py       # Panel implementation
  ui/                 # Optional UI definitions
  tests/              # Small unit tests
```

**Docking behaviors:**
- Docked panels: direct children within main layout (left/right/top/bottom)
- Floating panels: separate `Gtk.Window` instances owned by `DockManager`
- Drag-and-drop: implement drag preview and drop targets in `DockManager`

**Persistence:**
- Save layout as JSON: `panel_id -> { mode: docked|floating, position, geometry }`
- On startup: recreate panels and call `dock_panel`/`undock_panel` accordingly

---

## Code Style and Conventions

### Python Style

**Standard:** Follow **PEP 8** for Python code

**Key points:**
- Use meaningful variable/function/class names
- Write clear comments
- Add docstrings to all modules, classes, and functions
- Consistent indentation (4 spaces)
- Maximum line length: 79-100 characters (flexible)

### Import Patterns

```python
# From main package
from shypn.api import ClassName
from shypn.helpers import helper_function
from shypn.utils import utility_module
from shypn.data import ModelClass

# GTK imports (for GTK4)
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk
```

### Naming Conventions

- **Classes:** `PascalCase` (e.g., `DockManager`, `TransitionsController`)
- **Functions/methods:** `snake_case` (e.g., `dock_panel`, `on_activate`)
- **Constants:** `UPPER_SNAKE_CASE` (e.g., `UI_PATH`, `REPO_ROOT`)
- **Widget IDs in UI files:** `panel_<name>__widget` (e.g., `panel_transitions_root`)

---

## Migration and Legacy Code

### Legacy Code Policy

**Location:** `legacy/` directory

**Rules:**
1. **DO NOT MODIFY** legacy code directly
2. Legacy code is for **reference and migration only**
3. Extract useful modules/classes/functions
4. Refactor to fit new OOP structure in `src/shypn/`
5. Add/update tests in `tests/`
6. Remove legacy code **only after** successful migration and validation

### Migration Workflow

1. **Identify** useful code in `legacy/`
2. **Extract** and understand the business logic
3. **Refactor** to fit new architecture:
   - Use OOP design
   - Separate UI from logic
   - Follow UI-first and no-fallbacks rules
4. **Implement** in `src/shypn/` with appropriate module placement
5. **Test** thoroughly in `tests/`
6. **Document** changes and migration notes
7. **Validate** all functionality works correctly
8. **Deprecate** legacy code (mark clearly, add migration note)
9. **Remove** legacy code only when safe

### Adapter Strategy for Legacy Logic

**Purpose:** Reuse legacy business logic while building new GTK4 UI

**Approach:**
1. Define small data contracts that panels use (inputs/outputs)
2. Implement adapter module providing these functions
3. Adapters internally call legacy logic (or port of it)
4. Adapter tests validate the mapping
5. Panels call adapter functions via bus
6. Adapter returns plain Python data structures (no GTK objects)

**Advantages:**
- Keeps new UI code clean and GTK4-native
- Limits migration effort to adapters translating legacy to new contracts

---

## Development Workflow

### Contributing Workflow

1. **Fork** the repository
2. **Create** a new branch for your feature or fix
3. **Make changes** following structure and style guidelines
4. **Run tests** to ensure nothing is broken
5. **Submit** a pull request with clear description

### Where to Place New Code

| Type of Code | Location | Notes |
|--------------|----------|-------|
| API class/interface | `src/shypn/api/` | OOP design required |
| Helper function (pure) | `src/shypn/helpers/` | Functional, stateless |
| Utility routine | `src/shypn/utils/` | Specialized utilities |
| Data model/schema | `src/shypn/data/` | Data classes, ORM |
| Experimental code | `src/shypn/dev/` | Under development |
| UI definition | `ui/<category>/` | GTK Builder XML only |
| Test | `tests/` | Mirror `src/` structure |
| Developer script | `scripts/` | Standalone tools |
| Documentation | `doc/` | Markdown files |
| Application data | `data/` | Static resources |

### Testing Requirements

- Add or update tests for any new code
- Organize tests to mirror source structure
- Unit tests for modules
- Integration tests for features
- Adapter tests to validate legacy mappings
- Panel tests using mock bus (no GTK3 dependency)
- Manual smoke tests for UI layout and docking

### Documentation Requirements

- Document new modules and functions with clear docstrings
- Update relevant README.md when adding new folder or major feature
- Add architecture notes to `doc/` for significant changes
- Keep `ui/DOCK_UNDOCK_DESIGN.md` updated for UI changes

### Code Review Guidelines

- Verify correct module placement
- Check OOP design for core modules
- Ensure UI-first rule: layout changes in `ui/` files, not Python code
- Flag any fallback behavior for review
- Confirm GTK4 usage for new/refactored UI code
- Validate test coverage
- Check for clear error messages (fail loudly)

---

## Summary of Key Rules

### ✅ DO:
- Use object-oriented design for core modules
- Place UI definitions in declarative files under `ui/`
- Fail fast and loudly on missing resources
- Target GTK4 for all new UI work
- Mirror source structure in tests
- Follow PEP 8 style guide
- Add clear docstrings
- Update documentation

### ❌ DON'T:
- Embed UI structure in Python code
- Use silent fallbacks for missing resources
- Modify legacy code directly
- Use GTK3 for new code
- Pass GTK objects between adapters/panels
- Create subprocess-based UI fallback runners
- Skip tests for new code
- Place runtime code in `ui/` directory

---

## Quick Reference

### Important Files
- `README.md` — Project overview
- `CONTRIBUTING.md` — Contribution guidelines
- `ui/DOCK_UNDOCK_DESIGN.md` — UI architecture spec
- `src/shypn.py` — Application entry point
- `.vscode/` — VS Code workspace configuration

### Key Contacts
- For GTK4 migration questions: consult GTK 3→4 migration guide or open issue
- For architecture questions: refer to `doc/` or design documents
- For module placement questions: refer to this document

---

**Document Version:** 1.0  
**Last Updated:** October 1, 2025  
**Maintained by:** Project contributors
