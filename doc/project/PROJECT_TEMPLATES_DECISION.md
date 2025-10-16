# Project Templates - Design Decision

**Date:** 2025-10-16  
**Status:** DEFERRED - Awaiting File Operations Architecture  
**Decision:** Remove template dropdown from New Project dialog until proper implementation

---

## Context

The New Project dialog currently has a template dropdown with three options:
- Empty Project
- Basic Petri Net  
- KEGG Import Template

**Current Reality:** All templates create identical empty projects. The `template` parameter is accepted but never used in `project_models.py::create_project()`.

---

## The Problem

Templates involve **file operations** (copying template files, creating sample models, importing external data), which requires:

1. **Proper file loading architecture** - How to programmatically load .shy files into a project
2. **Import system integration** - KEGG/SBML importers need to work from project creation context
3. **Model initialization** - Template models need to be loaded into canvas or saved properly
4. **Error handling** - What if template files are missing or corrupted?
5. **Template maintenance** - Who creates and maintains template .shy files?

**Core Insight:** This is fundamentally about **file operations workflow**, not just UI placeholders.

---

## User's Strategic Vision

> "The idea about importing from any external source KEGG, SBML, etc., from project creation is excellent, since data importing/saving/opening is much file operations work, but we must plan for that in the near future."

### Key Points

1. **Templates = File Operations**
   - Template application involves copying, loading, and saving files
   - This intersects with the broader file operations architecture

2. **External Data Sources**
   - KEGG import
   - SBML import
   - Other pathway databases (Reactome, BioCyc, etc.)
   - Template library system

3. **Integration Point**
   - Templates should integrate with existing import panels
   - Project creation dialog could trigger import workflows
   - Need unified file operations system first

4. **Future Planning**
   - Design templates properly as part of file operations architecture
   - Don't rush half-baked implementation
   - Better to defer than to create technical debt

---

## Decision: Option 1 - Remove Template Dropdown

### Rationale

1. **Avoid User Confusion**
   - Users see three options but all do the same thing
   - Creates false expectations
   - Better to remove until it works properly

2. **Technical Debt Prevention**
   - Quick implementation now = refactoring later
   - File operations architecture is in flux (Phase 1 just completed)
   - Templates need stable foundation

3. **Clear User Experience**
   - "New Project" creates empty project (simple, predictable)
   - Users then import data using existing import panels
   - No broken promises

4. **Enables Future Planning**
   - Can design templates properly with file operations in mind
   - Can integrate with import system cleanly
   - Can build template library/marketplace later

---

## Implementation Plan

### Immediate (Today)

1. ✅ Document this decision
2. ✅ Remove template dropdown from `project_dialogs.ui`
3. ✅ Simplify `create_project()` signature (remove unused `template` parameter)
4. ✅ Update New Project dialog layout
5. ✅ Test project creation still works

### Near Future (After File Operations Phase 2+)

When file operations architecture stabilizes:

1. **Design Template System**
   - Template file format (.shy + metadata)
   - Template discovery/loading mechanism
   - Template validation

2. **Create Template Library**
   ```
   data/templates/
   ├── basic/
   │   ├── template.json        # Metadata (name, description, preview)
   │   ├── model.shy            # The actual Petri net
   │   └── thumbnail.png        # Preview image
   ├── producer_consumer/
   ├── biological_pathway/
   └── README.md
   ```

3. **Implement Template Application**
   ```python
   def _apply_template(self, project, template_id):
       """Apply a template to a newly created project."""
       # 1. Locate template files
       template_path = self._find_template(template_id)
       
       # 2. Copy/load template model
       model_file = os.path.join(template_path, 'model.shy')
       target_file = os.path.join(project.base_path, 'models', 'initial_model.shy')
       
       # 3. Use existing file operations to load
       shutil.copy(model_file, target_file)
       
       # 4. Register in project
       project.add_model(target_file)
       
       # 5. Open in canvas (optional)
       if auto_open:
           self._load_model_in_canvas(target_file)
   ```

4. **Integrate with Import Panels**
   - Template can specify "run KEGG import wizard"
   - Template can specify "run SBML import wizard"
   - Project creation becomes workflow launcher

5. **Advanced Features**
   - User-contributed templates
   - Template marketplace/sharing
   - Project-as-template (save project as reusable template)
   - Template categories (education, research, specific domains)

---

## Future Vision: Templates + Import Workflows

### Example: "KEGG Pathway Analysis" Template

**User Experience:**
1. Click "New Project"
2. Enter project name
3. Click "Create"
4. Project created, immediately shows **KEGG Import Wizard**
5. User enters pathway ID
6. Wizard fetches, converts, imports
7. Project now contains imported pathway
8. Canvas shows the model
9. User can start working immediately

**Implementation:**
```python
# In template.json
{
  "id": "kegg_analysis",
  "name": "KEGG Pathway Analysis",
  "description": "Start with a KEGG pathway import",
  "workflow": [
    {"action": "create_project"},
    {"action": "open_kegg_import_wizard"},
    {"action": "wait_for_import"},
    {"action": "load_imported_model"}
  ]
}
```

This integrates **project creation** with **data import** seamlessly.

---

## Related Architecture

### File Operations Phases

- **Phase 1 (DONE):** Per-document state (filepath, dirty tracking)
- **Phase 2 (PLANNED):** Multi-document save/close workflows
- **Phase 3 (FUTURE):** Template system integration

### Import System

Current importers work but are **not integrated** with project creation:
- KEGG Import Panel (Pathway Panel → KEGG tab)
- SBML Import Panel (Pathway Panel → SBML tab)

**Future:** Project creation can **launch** import workflows automatically.

### Template File Format

Should extend existing .shy format:
```json
{
  "type": "template",
  "version": "1.0",
  "metadata": {
    "name": "Basic Producer-Consumer",
    "author": "shypn",
    "description": "Simple example for learning",
    "tags": ["beginner", "tutorial", "simple"],
    "thumbnail": "thumbnail.png"
  },
  "content": {
    "places": [...],
    "transitions": [...],
    "arcs": [...]
  },
  "on_create": {
    "actions": [
      "load_model",
      "center_view",
      "show_tutorial_dialog"
    ]
  }
}
```

---

## Benefits of Waiting

1. **Better Integration**
   - Templates can use mature file operations API
   - Import workflows can be orchestrated properly
   - No need to refactor twice

2. **User Experience**
   - No broken features now
   - Better features later
   - Clear, simple project creation today

3. **Code Quality**
   - No technical debt from rushed implementation
   - Proper abstraction from the start
   - Testable, maintainable system

4. **Future Flexibility**
   - Can add advanced features (template marketplace, etc.)
   - Can integrate with external template sources
   - Can build on solid foundation

---

## What Users Should Do Now

**To create a project with imported data:**

1. **Create Empty Project**
   - Click "New Project"
   - Enter name and description
   - Click "Create"

2. **Import Data**
   - For KEGG: Use Pathway Panel → KEGG Import tab
   - For SBML: Use Pathway Panel → SBML Import tab
   - For .shy files: Use File → Open or File Explorer

3. **Work with Model**
   - Edit, simulate, analyze as usual
   - Save to project's models/ directory

**This workflow already works perfectly!** Templates would just streamline it.

---

## Summary

**Decision:** Remove template dropdown now, implement properly later

**Reasoning:** 
- Templates = file operations (needs architectural maturity)
- Better to defer than ship broken features
- Clear path forward when ready

**Timeline:**
- Today: Remove UI elements, simplify code
- Phase 2: Design template system
- Phase 3+: Implement with import integration

**Vision:** Templates should orchestrate import workflows, not just copy static files

---

**Status:** ✅ Decision documented, ready to implement UI changes

