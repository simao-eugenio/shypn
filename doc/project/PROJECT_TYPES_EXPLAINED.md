# Project Types in shypn

## Overview

**Status Update (2025-10-16):** Template dropdown has been **removed** from the New Project dialog. All projects are created empty. See `PROJECT_TEMPLATES_DECISION.md` for the rationale.

**Current Behavior:** When you click **"New Project"**, you create an empty project. You then import data using the KEGG/SBML import panels.

**Historical Note:** This document previously described template options that were never implemented. Templates are deferred until the file operations architecture matures.

---

## Template Types

### 1. **Empty Project** (Default)
**Current Status**: ✅ **Fully Implemented**

**What it does:**
- Creates a blank project with no pre-existing content
- Provides clean slate for building Petri nets from scratch
- Creates the following directory structure:
  ```
  workspace/projects/<project-uuid>/
  ├── project.shy          # Project metadata (name, description, created date)
  ├── models/              # Directory for .shy model files
  ├── pathways/            # Directory for imported pathway data
  ├── simulations/         # Directory for simulation results
  └── analysis/            # Directory for analysis outputs
  ```

**Best for:**
- Learning shypn from scratch
- Creating custom Petri net models
- Building models not based on biological pathways
- Maximum control over model design

**Workflow:**
1. Create project
2. Use **Place tool** to add places (circles)
3. Use **Transition tool** to add transitions (rectangles)
4. Use **Arc tool** to connect them
5. Save your model in `models/` directory

---

### 2. **Basic Petri Net**
**Current Status**: ⚠️ **Planned (Not Yet Implemented)**

**What it will do:**
- Create a project with a simple example Petri net already included
- Provide a starter model demonstrating basic Petri net concepts
- Include sample places, transitions, and arcs pre-configured

**Intended starter content:**
```
Simple Producer-Consumer Model:
- Place: "Buffer" (capacity: 10, initial tokens: 0)
- Transition: "Producer" (rate: 1/s)
- Arc: Producer → Buffer (weight: 1)
- Transition: "Consumer" (rate: 0.5/s)
- Arc: Buffer → Consumer (weight: 1)
```

**Best for (when implemented):**
- New users learning Petri net concepts
- Quick testing of simulation features
- Template for simple models
- Understanding shypn's model structure

**Implementation TODO:**
```python
# In project_models.py create_project():
if template == 'basic':
    self._apply_basic_template(project)

def _apply_basic_template(self, project):
    """Create a simple producer-consumer Petri net."""
    # 1. Create a new .shy file in models/
    # 2. Add basic places (Buffer, etc.)
    # 3. Add basic transitions (Producer, Consumer)
    # 4. Connect with arcs
    # 5. Save the model
```

---

### 3. **KEGG Import Template**
**Current Status**: ⚠️ **Partially Implemented**

**What it will do:**
- Create a project configured for importing biological pathways from KEGG database
- Pre-configure connection to KEGG API
- Set up directory structure optimized for pathway analysis
- Possibly include example KEGG pathway

**KEGG Integration (Already Available):**
shypn has a **KEGG Import** feature in the **Pathway Panel** (right side):
- Search for pathways by ID (e.g., `hsa00010` for Glycolysis)
- Fetch pathway data from KEGG database
- Automatically convert KEGG XML (KGML) to Petri net
- Import compounds, reactions, and enzymes as places/transitions

**Example KEGG Pathways Already Included:**
```
workspace/examples/pathways/
├── hsa00010.kgml/.shy  # Glycolysis / Gluconeogenesis
├── hsa00020.kgml/.shy  # Citrate cycle (TCA cycle)
└── hsa00030.kgml/.shy  # Pentose phosphate pathway
```

**Best for (when implemented):**
- Systems biology research
- Metabolic pathway analysis
- Converting biological pathways to Petri nets
- KEGG database users

**Current Workaround:**
1. Create **Empty Project**
2. Go to **Pathway Panel** → **KEGG Import** tab
3. Enter pathway ID (e.g., `hsa00010`)
4. Click "Fetch from KEGG"
5. Click "Convert to Petri Net"
6. Import into your project

**Implementation TODO:**
```python
# In project_models.py create_project():
if template == 'kegg':
    self._apply_kegg_template(project)

def _apply_kegg_template(self, project):
    """Set up project for KEGG pathway import."""
    # 1. Copy example pathway (hsa00010) to project
    # 2. Add README explaining KEGG import workflow
    # 3. Pre-configure pathway import settings
    # 4. Create analysis templates for pathway analysis
```

---

## Project Structure Details

### What Gets Created

When you create **any** project (currently), the following is generated:

#### 1. **Project Directory**
Location: `workspace/projects/<uuid>/`
- UUID ensures unique directory name
- Example: `workspace/projects/014d31e3-1342-4794-9950-97480b2c8784/`

#### 2. **project.shy** (Project Metadata)
```json
{
  "id": "014d31e3-1342-4794-9950-97480b2c8784",
  "name": "My Project",
  "description": "Optional description",
  "created_date": "2025-10-08T18:51:40.123456",
  "modified_date": "2025-10-08T18:51:40.123456",
  "base_path": "/path/to/workspace/projects/<uuid>",
  "models": {},
  "pathways": [],
  "simulations": [],
  "tags": [],
  "settings": {}
}
```

#### 3. **Subdirectories**
```
<project-uuid>/
├── models/       # Petri net model files (.shy)
├── pathways/     # Imported pathway data (KGML, etc.)
├── simulations/  # Simulation result files
└── analysis/     # Analysis outputs (P-invariants, T-invariants, etc.)
```

---

## Workspace vs Project Structure

### The Big Picture

```
shypn/
├── workspace/              # User workspace (gitignored)
│   ├── examples/          # Example models (git tracked)
│   │   ├── simple.shy
│   │   └── pathways/
│   │       ├── hsa00010.shy
│   │       └── ...
│   ├── projects/          # User projects (gitignored)
│   │   ├── <uuid-1>/
│   │   ├── <uuid-2>/
│   │   └── ...
│   └── cache/             # Downloaded data (gitignored)
│       └── kegg/
│           ├── pathways/
│           └── compounds/
├── src/                   # Application code
├── ui/                    # UI definitions
└── tests/                 # Test files
```

### Directory Purposes

| Directory | Purpose | Git Tracked? |
|-----------|---------|--------------|
| `workspace/examples/` | Demo models, tutorials | ✅ Yes |
| `workspace/projects/` | User-created projects | ❌ No (private) |
| `workspace/cache/` | Downloaded pathway data | ❌ No (regenerable) |

---

## How Templates Should Work (Future)

### User Experience Flow

1. **Click "New Project"**
2. **Choose Template:**
   - Empty → Start from scratch
   - Basic → Get example model
   - KEGG → Get pathway import setup

3. **Project Created with:**
   - Empty: Just directory structure
   - Basic: Directory + example model loaded on canvas
   - KEGG: Directory + example pathway + import settings

4. **File Explorer Updates:**
   - Navigates to new project directory
   - Shows project contents

5. **Ready to Work:**
   - Canvas shows template content (if any)
   - Can start editing/adding immediately

---

## Implementation Status

### ✅ Currently Working
- Empty project creation
- Project directory structure
- Project metadata (project.shy)
- Project management (open, close, properties)
- KEGG import (via Pathway Panel)

### ⚠️ Not Yet Implemented
- Basic Petri Net template content
- KEGG template pre-configuration
- Template selection actually affecting project creation
- Automatic canvas loading of template models

### 🔧 To Implement Templates

**File to modify**: `src/shypn/data/project_models.py`

**Changes needed:**
```python
def create_project(self, name: str, description: str = "",
                  template: str = None) -> Project:
    """Create a new project."""
    project = Project(name=name, description=description)
    project.base_path = os.path.join(self.projects_root, project.id)
    project.create_directory_structure()
    
    # NEW: Apply template
    if template == 'basic':
        self._apply_basic_template(project)
    elif template == 'kegg':
        self._apply_kegg_template(project)
    # else: 'empty' or None - do nothing extra
    
    project.save()
    # ... rest of method

def _apply_basic_template(self, project):
    """Create a basic producer-consumer Petri net."""
    from shypn.netobjs import Place, Transition, Arc
    
    # Create model file
    model_path = os.path.join(project.base_path, 'models', 'basic_example.shy')
    
    # Create basic elements
    buffer = Place(id='p1', name='Buffer', x=200, y=150, tokens=0, capacity=10)
    producer = Transition(id='t1', name='Producer', x=100, y=150, rate=1.0)
    consumer = Transition(id='t2', name='Consumer', x=300, y=150, rate=0.5)
    
    arc1 = Arc(source=producer, target=buffer, weight=1)
    arc2 = Arc(source=buffer, target=consumer, weight=1)
    
    # Save to file
    # ... serialization code

def _apply_kegg_template(self, project):
    """Set up KEGG import template."""
    import shutil
    
    # Copy example pathway
    example_src = 'workspace/examples/pathways/hsa00010.shy'
    example_dst = os.path.join(project.base_path, 'models', 'glycolysis_example.shy')
    shutil.copy(example_src, example_dst)
    
    # Create README
    readme_path = os.path.join(project.base_path, 'README.md')
    with open(readme_path, 'w') as f:
        f.write("""# KEGG Pathway Project
        
This project is set up for importing biological pathways from KEGG.

## Quick Start
1. Open the Pathway Panel (right side)
2. Go to KEGG Import tab
3. Enter pathway ID (e.g., hsa00010)
4. Click 'Fetch from KEGG'
5. Click 'Convert to Petri Net'

## Example Pathway
An example (Glycolysis) has been included in models/glycolysis_example.shy
""")
```

---

## Best Practices

### When to Use Each Template

| Use Case | Recommended Template |
|----------|---------------------|
| Learning Petri nets | Basic (when implemented) |
| Custom model from scratch | Empty |
| Biological pathway analysis | KEGG (when implemented) |
| Testing shypn features | Basic (when implemented) |
| Research project | Empty (full control) |

### Project Organization Tips

1. **One project per analysis**
   - Don't mix unrelated models in same project

2. **Use descriptive names**
   - Good: "Glucose Metabolism Analysis"
   - Bad: "Project 1", "Test", "asdf"

3. **Add descriptions**
   - Future you will thank you
   - Helps when returning to old projects

4. **Use models/ subdirectory properly**
   - Save model variations: `model_v1.shy`, `model_v2.shy`
   - Keep original imports separate from edited versions

5. **Leverage pathways/ directory**
   - Store original KGML files
   - Keep pathway metadata

6. **Document in project properties**
   - Use Project Settings button
   - Update description as project evolves

---

## Related Documentation

- **Directory Structure**: See `doc/DIRECTORY_STRUCTURE.md`
- **Project Management**: See `PROJECT_MANAGEMENT_IMPLEMENTATION.md`
- **KEGG Import**: See Pathway Panel documentation
- **Workspace Isolation**: See `WORKSPACE_ISOLATION_COMPLETE.md`

---

## FAQ

### Q: Why can't I select a different location for my project?
**A:** Projects are managed by shypn in `workspace/projects/` to:
- Keep workspace organized
- Enable project indexing and recent projects
- Prevent accidental corruption of application code
- Allow automatic backups and exports

### Q: Can I move a project after creation?
**A:** Not recommended. The project path is stored in metadata. If you need to:
1. Use "Export Project Archive" in project properties
2. Create new project
3. Import the archive

### Q: What's the difference between a project and a model?
**A:**
- **Project** = Container (directory) holding multiple models, pathways, simulations
- **Model** = Single Petri net (.shy file)
- One project can contain many models

### Q: Can I have multiple models in one project?
**A:** Yes! Save different .shy files in the `models/` subdirectory:
- `initial_design.shy`
- `refined_model.shy`
- `final_version.shy`

### Q: How do I share a project?
**A:**
1. Open project
2. Click "Project Settings" button
3. Go to "Content" tab
4. Click "Export Project Archive..."
5. Share the .zip file

### Q: Can I edit the template dropdown?
**A:** Templates are defined in `ui/dialogs/project_dialogs.ui`. You can add custom templates there, then implement them in `project_models.py`.

---

**Last Updated**: 2025-10-08  
**Status**: Templates are UI placeholders - implementation pending
