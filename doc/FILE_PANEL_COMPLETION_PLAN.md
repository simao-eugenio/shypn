# File Panel Completion Plan

## Overview

The File Panel has three main categories:
1. ✅ **FILES** - File explorer (COMPLETE - tagged as "file-explorer-pattern")
2. ⚠️ **PROJECT INFORMATION** - Display current project details (TODO)
3. ⚠️ **PROJECT ACTIONS** - Project management buttons (TODO)

This document outlines the remaining work to complete the File Panel validation.

---

## Current State

### ✅ Completed: FILES Category

**Status**: Fully implemented and tested  
**Git Tag**: `file-explorer-pattern`  
**Commit**: 76b3342

**Features Working**:
- Folder expansion by clicking name or arrow
- Navigation bar: [Home] <Entry> [Refresh]
- Entry shows selected file with white background
- Context menu: Cut/Copy/Paste/Rename (all inline)
- Inline file/folder creation
- Category collapse (▼): navigates to workspace root
- Home button (⌂): quick collapse tree to workspace root
- No auto-selection issues
- Fixed GTK event handling

---

## Phase 1: Project Information Category (Priority: HIGH)

### Goal
Display information about the currently active project in the **PROJECT INFORMATION** category.

### Current Implementation

**File**: `src/shypn/helpers/file_panel_loader.py`

```python
def _create_project_info_category(self, container):
    """Create Project Information category.
    
    TODO: Create ProjectInfoController to populate this category with live data:
      - Project name
      - Project path  
      - Last modified date
      - Number of models
      - Current status (e.g., "3 unsaved changes")
    """
    self.project_info_category = CategoryFrame(
        title="PROJECT INFORMATION",
        expanded=False,
        placeholder=True  # Shows "TODO" message
    )
```

**UI Widgets** (`ui/panels/left_panel_vscode.ui`):
```xml
<object class="GtkBox" id="project_info_content">
  <object class="GtkLabel" id="project_name_label">
    <property name="label">Project: —</property>
  </object>
  <object class="GtkLabel" id="project_path_label">
    <property name="label">Path: —</property>
  </object>
  <object class="GtkLabel" id="project_status_label">
    <property name="label">No project open</property>
  </object>
</object>
```

### Implementation Tasks

#### Task 1.1: Create ProjectInfoController

**File**: `src/shypn/helpers/project_info_controller.py` (NEW)

**Responsibilities**:
- Get references to UI widgets from builder
- Listen to project manager events (project opened/closed)
- Update labels when project changes
- Format display strings

**Key Methods**:
```python
class ProjectInfoController:
    def __init__(self, builder, project_manager):
        self.builder = builder
        self.project_manager = project_manager
        self._get_widgets()
        self._connect_signals()
        self._update_display()
    
    def _get_widgets(self):
        """Get label references from builder."""
        self.project_name_label = self.builder.get_object('project_name_label')
        self.project_path_label = self.builder.get_object('project_path_label')
        self.project_status_label = self.builder.get_object('project_status_label')
    
    def _connect_signals(self):
        """Connect to project manager events."""
        # Listen for project open/close events
        pass
    
    def _update_display(self):
        """Update labels with current project info."""
        project = self.project_manager.current_project
        if project:
            self.project_name_label.set_text(f"Project: {project.name}")
            self.project_path_label.set_text(f"Path: {project.base_path}")
            
            # Count models
            model_count = len(project.models)
            self.project_status_label.set_text(f"{model_count} models")
        else:
            self.project_name_label.set_text("Project: —")
            self.project_path_label.set_text("Path: —")
            self.project_status_label.set_text("No project open")
    
    def on_project_opened(self, project):
        """Called when project is opened."""
        self._update_display()
    
    def on_project_closed(self):
        """Called when project is closed."""
        self._update_display()
```

#### Task 1.2: Integrate ProjectInfoController

**File**: `src/shypn/helpers/file_panel_loader.py`

**Changes**:
1. Import ProjectInfoController
2. Initialize in `_init_controllers()` method
3. Remove `placeholder=True` from CategoryFrame
4. Set category content to `project_info_content` widget

```python
from shypn.helpers.project_info_controller import ProjectInfoController

class FilePanelLoader:
    def __init__(self, ...):
        self.project_info_controller = None
    
    def _create_project_info_category(self, container):
        """Create Project Information category."""
        self.project_info_category = CategoryFrame(
            title="PROJECT INFORMATION",
            expanded=False
            # Remove placeholder=True
        )
        
        # Add content widget
        project_info_content = self.builder.get_object('project_info_content')
        if project_info_content:
            self.project_info_category.set_content(project_info_content)
        
        container.pack_start(self.project_info_category, False, False, 0)
    
    def _init_controllers(self):
        """Initialize all controllers."""
        # Existing controllers...
        self._init_file_explorer()
        
        # NEW: Initialize project info controller
        from shypn.data.project_models import get_project_manager
        project_manager = get_project_manager()
        self.project_info_controller = ProjectInfoController(
            self.builder,
            project_manager
        )
```

#### Task 1.3: Testing

**Manual Tests**:
1. Launch application with no project → labels show "—" and "No project open"
2. Open existing project → labels update with project name, path, model count
3. Close project → labels reset to "—"
4. Create new project → labels update immediately

**Expected Display**:
```
▼ PROJECT INFORMATION
  Project: Glycolysis Analysis
  Path: workspace/projects/Glycolysis_Analysis
  3 models
```

---

## Phase 2: Project Actions Category (Priority: HIGH)

### Goal
Make the **PROJECT ACTIONS** buttons functional for creating, opening, and managing projects.

### Current Implementation

**File**: `src/shypn/helpers/file_panel_loader.py`

```python
def _create_project_actions_category(self, container):
    """Create Project Actions category.
    
    TODO: Create ProjectActionsController to handle:
      - New Project button
      - Open Project button  
      - Project Settings button
    """
    self.project_actions_category = CategoryFrame(
        title="PROJECT ACTIONS",
        expanded=False,
        placeholder=True  # Shows "TODO" message
    )
```

**UI Widgets** (`ui/panels/left_panel_vscode.ui`):
```xml
<object class="GtkBox" id="project_actions_content">
  <object class="GtkButton" id="new_project_button">
    <property name="label">New Project</property>
  </object>
  <object class="GtkButton" id="open_project_button">
    <property name="label">Open Project</property>
  </object>
  <object class="GtkButton" id="project_settings_button">
    <property name="label">Project Settings</property>
  </object>
</object>
```

### Implementation Tasks

#### Task 2.1: Verify ProjectActionsController Exists

**File**: `src/shypn/helpers/project_actions_controller.py`

This file already exists! Check if it's complete or needs updates.

```bash
# Check what's already implemented
cat src/shypn/helpers/project_actions_controller.py
```

#### Task 2.2: Integrate ProjectActionsController

**File**: `src/shypn/helpers/file_panel_loader.py`

**Changes**:
1. Import ProjectActionsController (if not already imported)
2. Initialize in `_init_controllers()` method
3. Remove `placeholder=True` from CategoryFrame
4. Set category content to `project_actions_content` widget

```python
from shypn.helpers.project_actions_controller import ProjectActionsController

class FilePanelLoader:
    def __init__(self, ...):
        self.project_actions_controller = None
    
    def _create_project_actions_category(self, container):
        """Create Project Actions category."""
        self.project_actions_category = CategoryFrame(
            title="PROJECT ACTIONS",
            expanded=False
            # Remove placeholder=True
        )
        
        # Add content widget
        project_actions_content = self.builder.get_object('project_actions_content')
        if project_actions_content:
            self.project_actions_category.set_content(project_actions_content)
        
        container.pack_start(self.project_actions_category, False, False, 0)
    
    def _init_controllers(self):
        """Initialize all controllers."""
        # Existing controllers...
        self._init_file_explorer()
        self._init_project_info_controller()
        
        # NEW: Initialize project actions controller
        from shypn.data.project_models import get_project_manager
        project_manager = get_project_manager()
        
        self.project_actions_controller = ProjectActionsController(
            self.builder,
            project_manager,
            parent_window=self.parent_window
        )
```

#### Task 2.3: Testing

**Manual Tests**:
1. Click "New Project" → dialog opens, create project → labels update
2. Click "Open Project" → project list dialog opens, select project → opens
3. Click "Project Settings" → settings dialog opens (only if project is open)
4. Click "Project Settings" with no project → shows error message

**Expected Behavior**:
```
▼ PROJECT ACTIONS
  [New Project]
  [Open Project]
  [Project Settings]
```

---

## Phase 3: Data Persistence for External Sources (Priority: MEDIUM)

### Goal
Ensure that imported data from KEGG, SBML, and BRENDA is automatically saved to the project structure BEFORE parsing. This is critical for report generation and data provenance.

### Problem

Currently, external data is NOT saved to project structure:
- ❌ KEGG: Fetches KGML but doesn't save to `project/pathways/`
- ❌ SBML: Loads file but doesn't copy to `project/pathways/`
- ❌ BRENDA: Not yet implemented

### Required Flow

```
1. User imports pathway (KEGG/SBML)
   ↓
2. Check if project is open
   ↓
3. Save raw external data to project/pathways/
   - hsa00010.kgml (KEGG)
   - hsa00010.meta.json (metadata)
   ↓
4. Parse and convert to Petri net
   ↓
5. Load to canvas
```

### Implementation Tasks

#### Task 3.1: Create ExternalDataPersistence Helper

**File**: `src/shypn/helpers/external_data_persistence.py` (NEW)

```python
"""Helper for persisting external data to project structure."""

import os
import json
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path

class ExternalDataPersistence:
    """Saves external data (KEGG, SBML, BRENDA) to project structure."""
    
    @staticmethod
    def save_kegg_data(project, pathway_id: str, kgml_data: str, 
                       organism: str = None) -> tuple[str, str]:
        """Save KEGG pathway data to project.
        
        Args:
            project: Current Project instance
            pathway_id: KEGG pathway ID (e.g., "hsa00010")
            kgml_data: Raw KGML XML string
            organism: Organism code (e.g., "hsa")
        
        Returns:
            (kgml_path, metadata_path): Paths to saved files
        """
        if not project:
            return None, None
        
        pathways_dir = project.get_pathways_dir()
        os.makedirs(pathways_dir, exist_ok=True)
        
        # Save KGML file
        kgml_path = os.path.join(pathways_dir, f"{pathway_id}.kgml")
        with open(kgml_path, 'w', encoding='utf-8') as f:
            f.write(kgml_data)
        
        # Save metadata
        metadata = {
            'source': 'KEGG',
            'pathway_id': pathway_id,
            'organism': organism,
            'fetch_date': datetime.now().isoformat(),
            'url': f'https://rest.kegg.jp/get/{pathway_id}/kgml',
            'format': 'KGML',
            'original_file': f"{pathway_id}.kgml"
        }
        
        metadata_path = os.path.join(pathways_dir, f"{pathway_id}.meta.json")
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
        
        # Add to project's pathway list
        if kgml_path not in project.pathways:
            project.pathways.append(kgml_path)
            project.save()
        
        return kgml_path, metadata_path
    
    @staticmethod
    def save_sbml_data(project, sbml_path: str, source: str = "local") -> tuple[str, str]:
        """Save/copy SBML file to project.
        
        Args:
            project: Current Project instance
            sbml_path: Path to SBML file (local or temp from BioModels)
            source: "local" or "biomodels"
        
        Returns:
            (sbml_path_in_project, metadata_path): Paths to saved files
        """
        if not project:
            return None, None
        
        pathways_dir = project.get_pathways_dir()
        os.makedirs(pathways_dir, exist_ok=True)
        
        # Copy SBML file to project
        filename = os.path.basename(sbml_path)
        dest_path = os.path.join(pathways_dir, filename)
        
        import shutil
        shutil.copy2(sbml_path, dest_path)
        
        # Save metadata
        metadata = {
            'source': 'SBML',
            'import_source': source,  # "local" or "biomodels"
            'import_date': datetime.now().isoformat(),
            'original_path': sbml_path,
            'format': 'SBML',
            'filename': filename
        }
        
        base_name = os.path.splitext(filename)[0]
        metadata_path = os.path.join(pathways_dir, f"{base_name}.meta.json")
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
        
        # Add to project's pathway list
        if dest_path not in project.pathways:
            project.pathways.append(dest_path)
            project.save()
        
        return dest_path, metadata_path
    
    @staticmethod
    def save_brenda_data(project, ec_number: str, brenda_data: Dict[str, Any]) -> str:
        """Save BRENDA kinetic data to project.
        
        Args:
            project: Current Project instance
            ec_number: EC number (e.g., "2.7.1.1")
            brenda_data: Dictionary with kinetic parameters
        
        Returns:
            metadata_path: Path to saved JSON file
        """
        if not project:
            return None
        
        pathways_dir = project.get_pathways_dir()
        os.makedirs(pathways_dir, exist_ok=True)
        
        # Save BRENDA data as JSON
        sanitized_ec = ec_number.replace('.', '_')
        metadata = {
            'source': 'BRENDA',
            'ec_number': ec_number,
            'fetch_date': datetime.now().isoformat(),
            'data': brenda_data
        }
        
        metadata_path = os.path.join(pathways_dir, f"brenda_ec_{sanitized_ec}.json")
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
        
        return metadata_path
```

#### Task 3.2: Update KEGG Import to Save Data

**File**: `src/shypn/helpers/kegg_import_panel.py`

**Changes in `_on_fetch_complete()`**:

```python
def _on_fetch_complete(self, pathway_id, kgml_data, parsed_pathway):
    """Called in main thread after fetch completes successfully."""
    self.current_kgml = kgml_data
    self.current_pathway = parsed_pathway
    
    # NEW: Save to project if one is open
    from shypn.data.project_models import get_project_manager
    from shypn.helpers.external_data_persistence import ExternalDataPersistence
    
    project_manager = get_project_manager()
    if project_manager.current_project:
        organism = self.organism_combo.get_active_id() if self.organism_combo else None
        kgml_path, meta_path = ExternalDataPersistence.save_kegg_data(
            project_manager.current_project,
            pathway_id,
            kgml_data,
            organism
        )
        if kgml_path:
            print(f"[KEGG] Saved to project: {kgml_path}", file=sys.stderr)
    
    # Update preview
    self._update_preview()
    
    # Enable import button
    self.import_button.set_sensitive(True)
    self._show_status(f"✅ Pathway {pathway_id} loaded successfully")
    
    # Re-enable fetch button
    self.fetch_button.set_sensitive(True)
    return False  # Don't repeat
```

#### Task 3.3: Update SBML Import to Save Data

**File**: `src/shypn/helpers/sbml_import_panel.py`

**Changes in `_on_parse_complete()`**:

```python
def _on_parse_complete(self, parsed_pathway, validation_result):
    """Handle successful parse completion (called in main thread)."""
    self.parsed_pathway = parsed_pathway
    
    # NEW: Save to project if one is open
    from shypn.data.project_models import get_project_manager
    from shypn.helpers.external_data_persistence import ExternalDataPersistence
    
    project_manager = get_project_manager()
    if project_manager.current_project and self.current_filepath:
        # Determine source (local file or BioModels)
        source = "biomodels" if "biomodels" in self.current_filepath.lower() else "local"
        
        sbml_path, meta_path = ExternalDataPersistence.save_sbml_data(
            project_manager.current_project,
            self.current_filepath,
            source
        )
        if sbml_path:
            print(f"[SBML] Saved to project: {sbml_path}", file=sys.stderr)
    
    # Update preview
    self._update_preview()
    
    # Show validation results
    if not validation_result.is_valid:
        self._show_validation_errors(validation_result)
        return False
    
    # Enable load button
    self.sbml_load_button.set_sensitive(True)
    self._show_status("✅ SBML file parsed successfully")
    self.sbml_parse_button.set_sensitive(True)
    return False
```

#### Task 3.4: Project Structure Verification

After implementation, the project structure should look like:

```
workspace/projects/Glycolysis_Analysis/
├── project.shy                    # Project metadata
├── models/                        # Converted Petri net models
│   └── glycolysis_v1.shy
├── pathways/                      # ⭐ External data stored here
│   ├── hsa00010.kgml              # Original KEGG KGML
│   ├── hsa00010.meta.json         # KEGG metadata
│   ├── glycolysis.sbml            # Original SBML file
│   ├── glycolysis.meta.json       # SBML metadata
│   └── brenda_ec_2_7_1_1.json    # BRENDA kinetics
├── simulations/                   # Simulation results
└── analysis/                      # Analysis outputs
```

---

## Phase 4: File Panel Validation Complete (Priority: HIGH)

### Goal
Verify all three categories of the File Panel are working correctly.

### Validation Checklist

#### FILES Category (Already Complete)
- [ ] ✅ Folder expansion works
- [ ] ✅ Navigation bar works
- [ ] ✅ Context menu works
- [ ] ✅ Inline operations work
- [ ] ✅ Home button works
- [ ] ✅ Collapse button works

#### PROJECT INFORMATION Category
- [ ] Shows "No project open" when no project is active
- [ ] Displays project name when project opens
- [ ] Displays project path correctly
- [ ] Shows model count
- [ ] Updates when project changes
- [ ] Category expands/collapses smoothly

#### PROJECT ACTIONS Category
- [ ] "New Project" button creates new project
- [ ] "Open Project" button shows project list
- [ ] "Project Settings" button opens settings (when project is open)
- [ ] Buttons are enabled/disabled appropriately
- [ ] All dialogs work correctly
- [ ] Category expands/collapses smoothly

#### Integration Tests
- [ ] Create new project → PROJECT INFORMATION updates
- [ ] Open existing project → PROJECT INFORMATION updates
- [ ] Close project → PROJECT INFORMATION resets
- [ ] Import KEGG pathway → file saved to project/pathways/
- [ ] Import SBML file → file copied to project/pathways/
- [ ] All three categories work together without conflicts

---

## Implementation Priority

### Week 1: Project Information & Actions (HIGH PRIORITY)
**Days 1-2**: Phase 1 - Project Information Category
- Create ProjectInfoController
- Integrate with FilePanelLoader
- Test display updates

**Days 3-4**: Phase 2 - Project Actions Category
- Verify/update ProjectActionsController
- Integrate with FilePanelLoader
- Test all buttons and dialogs

**Day 5**: Phase 4 - Validation & Testing
- Complete validation checklist
- Fix any issues
- Create git tag: "file-panel-complete"

### Week 2: Data Persistence (MEDIUM PRIORITY)
**Days 1-2**: Phase 3 - External Data Persistence
- Create ExternalDataPersistence helper
- Update KEGG import
- Update SBML import

**Days 3-4**: Testing & Verification
- Test with real imports
- Verify project structure
- Test report generation (next phase)

---

## Success Criteria

### File Panel Complete When:
1. ✅ All three categories functional (FILES, PROJECT INFORMATION, PROJECT ACTIONS)
2. ✅ No placeholder "TODO" messages
3. ✅ All buttons and controls work
4. ✅ Display updates automatically when project changes
5. ✅ No errors or warnings in console
6. ✅ User can create, open, and manage projects entirely from File Panel
7. ✅ External data is saved to project structure (for report generation)

### Ready for Next Phase (Reports) When:
1. ✅ File Panel validation complete
2. ✅ Data persistence implemented
3. ✅ Project structure contains all imported data
4. ✅ Metadata files created for provenance tracking

---

## Git Workflow

### Branch Strategy
- `main` branch - stable, tested code
- Feature branches for each phase

### Git Tags
- ✅ `file-explorer-pattern` (already created)
- `project-info-complete` (after Phase 1)
- `project-actions-complete` (after Phase 2)
- `file-panel-complete` (after Phase 4)
- `data-persistence-complete` (after Phase 3)

### Commit Messages
Use conventional commits:
- `feat: add ProjectInfoController`
- `feat: integrate project actions with file panel`
- `feat: save KEGG data to project structure`
- `fix: update project info when project changes`
- `test: validate file panel categories`

---

## Notes

### Why This Order?
1. **Project Info & Actions first** - These complete the File Panel UI/UX
2. **Data persistence second** - This supports future report generation but doesn't block File Panel validation

### Dependencies
- ProjectManager must be working (already implemented)
- Project creation/opening dialogs must work (already implemented)
- CategoryFrame must support content widgets (already implemented)

### Testing Strategy
- Manual testing during development
- Integration testing after each phase
- Full validation before tagging

---

**Last Updated**: October 25, 2025  
**Status**: Planning - Ready to implement  
**Next Step**: Phase 1 - Create ProjectInfoController
