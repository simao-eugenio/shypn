# Save Path Architecture - Quick Reference

## Storage Locations

```
┌─────────────────────────────────────────────────────────────────────┐
│ ~/.config/shypn/                    [USER CONFIGURATION]            │
│ ├── workspace.json                  Window state, preferences       │
│ └── (future: preferences.json)      User settings                   │
└─────────────────────────────────────────────────────────────────────┘
                                      ▲
                                      │ Managed by WorkspaceSettings
                                      │
┌─────────────────────────────────────────────────────────────────────┐
│ REPOSITORY ROOT                                                      │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ models/                         [LEGACY STANDALONE FILES]     │  │
│  │ ├── example1.shy                Individual Petri net files    │  │
│  │ ├── example2.shy                                              │  │
│  │ └── ...                                                        │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                      ▲                               │
│                                      │ Managed by NetObjPersistency  │
│                                      │                               │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ workspace/                      [PROJECT-BASED WORKSPACE]     │  │
│  │                                                                │  │
│  │  projects/                      Root for all projects         │  │
│  │  ├── project_index.json         Registry of all projects      │  │
│  │  ├── recent_projects.json       Recent projects list          │  │
│  │  │                                                             │  │
│  │  ├── MyFirstProject/            Individual project            │  │
│  │  │   ├── project.shy            Project metadata              │  │
│  │  │   ├── models/                Petri net models              │  │
│  │  │   │   ├── model1.shy                                       │  │
│  │  │   │   └── model2.shy                                       │  │
│  │  │   ├── pathways/              Analysis pathways             │  │
│  │  │   ├── simulations/           Simulation results            │  │
│  │  │   ├── exports/               Exported data                 │  │
│  │  │   └── metadata/              Project metadata & backups    │  │
│  │  │       └── backups/                                         │  │
│  │  │                                                             │  │
│  │  └── AnotherProject/            Another project               │  │
│  │      └── ...                    Same structure                │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                      ▲                               │
│                                      │ Managed by ProjectManager     │
└─────────────────────────────────────────────────────────────────────┘
```

## Path Resolution Flow

```
User Action: Save File
        ↓
┌───────────────────┐
│ Which Mode?       │
└───────────────────┘
        ↓
    ┌───┴───┐
    │       │
    │       │
┌───▼───┐ ┌▼──────────┐
│Legacy │ │Project    │
│Mode   │ │Mode       │
└───┬───┘ └┬──────────┘
    │       │
    │       │
┌───▼───────▼───────────┐
│ NetObjPersistency     │
│ Shows FileChooser     │
│ Default: models/ or   │
│ Last used directory   │
└───────┬───────────────┘
        │
        ↓
┌───────────────────────┐
│ User Selects Path     │
└───────┬───────────────┘
        │
        ↓
┌───────────────────────┐
│ DocumentModel         │
│ save_to_file()        │
│ Creates directories   │
│ Writes JSON           │
└───────────────────────┘
```

## Component Responsibilities

```
┌─────────────────────────────────────────────────────────────┐
│ PATH MANAGEMENT (Who decides where to save?)                 │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  NetObjPersistency     → models/ or last directory          │
│  ProjectManager        → workspace/projects/<name>/         │
│  WorkspaceSettings     → ~/.config/shypn/                   │
│                                                               │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ SERIALIZATION (How to save?)                                 │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  DocumentModel         → to_dict(), save_to_file()          │
│  Project               → to_dict(), save()                  │
│  WorkspaceSettings     → json.dump()                        │
│                                                               │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ USER INTERACTION (How to choose?)                            │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  NetObjPersistency     → FileChooserDialog, warnings        │
│  (Future: Project UI)  → Project selection dialog           │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## File Extensions

```
.shy   → Petri net model file (JSON)
       → Used in both legacy and project modes
       → project.shy is special (project metadata)

.json  → Configuration/index files
       → project_index.json
       → recent_projects.json
       → workspace.json
```

## Quick Examples

### Save New Model (Legacy Mode)
```python
persistency = NetObjPersistency()
document = DocumentModel(...)

# Opens dialog defaulting to: /repo/models/
persistency.save_document(document)
# Saves to: /repo/models/mymodel.shy
```

### Save New Model (Project Mode)
```python
manager = ProjectManager()
project = manager.current_project
document = DocumentModel(...)

model_path = os.path.join(project.get_models_dir(), "mymodel.shy")
document.save_to_file(model_path)
# Saves to: /repo/workspace/projects/MyProject/models/mymodel.shy
```

### Save Workspace Settings
```python
settings = WorkspaceSettings()
settings.set_window_geometry(1200, 800)
settings.save()
# Saves to: ~/.config/shypn/workspace.json
```

## Status: ✅ All Integrated

All save paths properly follow the architecture:
- ✅ User config in ~/.config/shypn/
- ✅ Projects in workspace/projects/
- ✅ Legacy models in models/
- ✅ No hardcoded paths
- ✅ Proper separation of concerns
