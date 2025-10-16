# Project Management Documentation

This directory contains documentation related to shypn's project management system.

## Overview

Shypn uses a **project-based workflow** where users organize their Petri net models, pathways, and simulations within projects. Projects are stored in `workspace/projects/` and managed through a project index system.

---

## Documentation Files

### Core Implementation

**[PROJECT_MANAGEMENT_IMPLEMENTATION.md](PROJECT_MANAGEMENT_IMPLEMENTATION.md)**
- Complete implementation documentation for the project management system
- Architecture overview (ProjectManager, Project, ModelDocument classes)
- Dialog implementations (New Project, Open Project, Properties)
- File structure and organization
- Phase-by-phase implementation details
- Status: ✅ COMPLETE (Phases 1-6)

### Project Creation & Templates

**[PROJECT_TEMPLATES_DECISION.md](PROJECT_TEMPLATES_DECISION.md)** ⭐ **NEW**
- Strategic decision to defer template implementation
- Rationale: Templates = file operations (needs mature architecture)
- Future vision: Templates + import workflow integration
- Timeline: Implement after File Operations Phase 2+
- Status: ✅ DECISION DOCUMENTED (2025-10-16)

**[PROJECT_TEMPLATES_REMOVAL_SUMMARY.md](PROJECT_TEMPLATES_REMOVAL_SUMMARY.md)** ⭐ **NEW**
- Implementation details for removing template dropdown
- Code changes in project_models.py, project_dialog_manager.py, project_dialogs.ui
- Before/after comparison
- Testing checklist
- Status: ✅ IMPLEMENTATION COMPLETE (2025-10-16)

**[PROJECT_TYPES_EXPLAINED.md](PROJECT_TYPES_EXPLAINED.md)**
- User-facing guide explaining project types and templates
- Originally described 3 templates: Empty, Basic, KEGG
- Updated (2025-10-16): Templates removed, now creates empty projects only
- Current user workflow for importing data
- Status: ✅ UPDATED - Historical reference maintained

### Project Naming & Display

**[PROJECT_NAME_ALIAS_SYSTEM.md](PROJECT_NAME_ALIAS_SYSTEM.md)**
- Design document for project naming and aliasing system
- UUID vs human-readable names
- Directory naming strategy
- Display name vs filesystem name

**[PROJECT_NAME_DISPLAY_IMPLEMENTATION.md](PROJECT_NAME_DISPLAY_IMPLEMENTATION.md)**
- Implementation details for project name display
- UI integration (File Explorer, dialogs, etc.)
- Name conflict resolution
- Status: Part of overall project management system

---

## Architecture Overview

### Key Components

```
ProjectManager (Singleton)
├── project_index       # Maps UUID → project metadata
├── recent_projects     # MRU list of project IDs
├── current_project     # Active Project instance
└── projects_root       # Path to workspace/projects/

Project
├── id                  # UUID
├── name               # Display name
├── base_path          # Path to project directory
├── models/            # Dict: model_id → ModelDocument
├── pathways/          # List of pathway files
└── simulations/       # List of simulation results

ModelDocument
├── id                 # UUID
├── name              # Display name
├── file_path         # Path to .shy file
└── metadata          # Created, modified dates, tags
```

### Directory Structure

```
workspace/
├── projects/                    # User projects
│   ├── My_Project_Name/        # Sanitized project name
│   │   ├── project.shy         # Project metadata
│   │   ├── models/             # Petri net models
│   │   ├── pathways/           # Imported pathways
│   │   ├── simulations/        # Simulation results
│   │   └── exports/            # Exported files
│   └── ...
├── .project_index.json         # Project registry
└── .recent_projects.json       # Recent projects MRU list
```

---

## Recent Changes (2025-10-16)

### ✅ Project Templates Removed

**Rationale:** Templates were UI placeholders that didn't affect project creation. All three template options (Empty, Basic, KEGG) created identical empty projects.

**Decision:** Remove templates now, implement properly later as part of file operations architecture.

**Changes:**
- Removed template dropdown from New Project dialog
- Simplified `create_project()` signature (removed unused `template` parameter)
- Updated documentation to reflect current behavior
- Deferred implementation until file operations Phase 2+

**User Impact:**
- Clearer, simpler project creation experience
- No false expectations from non-functional features
- Existing import workflows (KEGG/SBML panels) already work perfectly

---

## User Workflows

### Creating a Project with Data

**Current Recommended Workflow:**

1. **Create Empty Project**
   ```
   Click "New Project" → Enter name/description → Click "Create"
   ```

2. **Import Data**
   - **For KEGG pathways:** Pathway Panel → KEGG Import tab
   - **For SBML models:** Pathway Panel → SBML Import tab  
   - **For .shy files:** File → Open or File Explorer

3. **Work with Model**
   - Edit, simulate, analyze
   - Save to project's models/ directory

**This workflow is fully functional today!**

---

## Future Roadmap

### Templates (Phase 3+)

When file operations architecture matures:

1. **Template System Design**
   - Template file format (`.shy` + metadata)
   - Template library in `data/templates/`
   - Template discovery/validation

2. **Import Workflow Integration**
   - Templates can trigger KEGG import wizard
   - Templates can trigger SBML import wizard
   - Project creation becomes workflow orchestrator

3. **Advanced Features**
   - User-contributed templates
   - Template marketplace/sharing
   - Project-as-template export
   - Template categories (education, research, domains)

**Goal:** Seamless integration of project creation + data import

---

## Related Documentation

### In Other Directories

- `doc/FILE_OPERATIONS_PHASE1_IMPLEMENTATION.md` - Per-document state system
- `doc/WORKSPACE_ISOLATION_COMPLETE.md` - Workspace directory structure
- `doc/DIRECTORY_STRUCTURE.md` - Overall repository layout

### Implementation Files

- `src/shypn/data/project_models.py` - Core classes
- `src/shypn/helpers/project_dialog_manager.py` - Dialog management
- `src/shypn/helpers/project_actions_controller.py` - Button handlers
- `ui/dialogs/project_dialogs.ui` - GTK dialog definitions

---

## Status Summary

| Component | Status | Phase |
|-----------|--------|-------|
| Project Management Core | ✅ Complete | 1-6 |
| New Project Dialog | ✅ Complete | 1 |
| Open Project Dialog | ✅ Complete | 2 |
| Recent Projects | ✅ Complete | 3 |
| Project Properties | ✅ Complete | 4 |
| Project Index | ✅ Complete | 5 |
| File Explorer Integration | ✅ Complete | 6 |
| **Templates** | ⏸️ **Deferred** | **3+ (Future)** |
| Archive/Export | ✅ Complete | 7 |
| Multi-project Management | ✅ Complete | - |

---

## Key Decisions

### Template Deferral (2025-10-16)

**Why defer templates?**
- Templates require mature file operations architecture
- Import workflows need proper integration
- Better to ship simple, working features than broken complex ones
- Clear path forward when architecture is ready

**What users should know:**
- All projects are created empty (by design)
- Use existing import panels to add data
- This workflow already works perfectly
- Templates will streamline this in the future

---

**Last Updated:** 2025-10-16  
**Maintained By:** Development Team  
**Status:** Active - Living Documentation
