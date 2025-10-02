# Project Title

A brief description of your project.
 
## GTK 4 Migration Notice

This project is in the process of incrementally migrating from GTK 3.2+ to GTK 4. During this transition, some legacy code and UI components may still use GTK 3, but all new development and refactoring should target GTK 4 for long-term maintainability and compatibility. Contributors are encouraged to update modules to GTK 4 as they are migrated or refactored.
 
## Architectural Guideline: Object-Oriented Design

This project is designed with an object-oriented programming (OOP) approach. Core logic, APIs, and UI components are implemented as classes, utilizing principles such as encapsulation, inheritance, and polymorphism. Contributors are encouraged to structure new modules and features using OOP best practices to ensure maintainability and extensibility.
## Repository Structure Overview

```
shypn/
├── data/         # Data model files (schemas, ORM models, sample data)
├── doc/          # Main documentation in Markdown format
├── src/
│   ├── apis/     # Object-oriented modules (classes, interfaces)
│   ├── dev/      # Experimental or in-development code
│   ├── helpers/  # Functional programming helpers (pure functions)
│   └── utils/    # Specific code routines and specialized utilities
├── tests/        # Test suite
├── ui/
│   ├── main/     # Main window interface
│   ├── canvas/   # Document model interfaces (canvas, drawing, etc.)
│   ├── dialogs/  # Instantly loadable dialogs (modal/pop-up)
│   ├── palettes/ # Control interfaces (toolbars, color pickers, etc.)
│   └── panels/   # Dockable/undockable panels (sidebars, inspectors)
```

## Installation

Instructions for installing dependencies and setting up the environment.

## Usage

How to use the project.

## Running the GTK4 UI under WSLg / Windows

If you run the project from WSL (WSLg) you may see inconsistencies when using a Conda Python environment because Conda-provided GTK/GLib stacks can be isolated from the system Wayland backend. A reliable workaround is to create a small virtualenv that uses the system site-packages (so it picks up the system GTK/GI installation that works with WSLg).

Steps (one-time):

1. Create the venv (uses system Python and system GTK):

```bash
python3 -m venv venv/shypnenv --system-site-packages
```

2. Activate and run the UI (use system python inside the venv):

```bash
. venv/shypnenv/bin/activate
/usr/bin/python3 src/shypn.py
```

Notes:
- This approach keeps your Conda environment untouched while allowing GTK4 apps to use the system Wayland backend (WSLg). It is the recommended approach when working on Windows+WSL development if the Conda GTK stack misbehaves.
- If you prefer to work with Conda, you can attempt to fix the Conda environment (rebuild PyGObject + GTK packages) but that is more involved and may be fragile.

## Contributing

Guidelines for contributing.

## License

Specify the license here.
