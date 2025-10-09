# Project Name Alias System

## Overview

The project system uses **project names as user-facing aliases** while keeping **UUIDs as internal identifiers** for version control and unique identification.

**Design Philosophy:**
- **UUID**: Internal, immutable, unique identifier (like a database primary key)
- **Name**: External, user-friendly, mutable alias (like a display name)

## Architecture

### Project Identity Structure

```
Project:
  ├─ id:   "a1b2c3d4-e5f6-7890-1234-567890abcdef"  ← Internal (UUID)
  ├─ name: "MySimulation"                           ← External (alias)
  └─ base_path: "workspace/projects/MySimulation/"  ← Uses sanitized name
```

### Storage

**project_index.json:**
```json
{
  "a1b2c3d4-e5f6-7890-1234-567890abcdef": {
    "id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
    "name": "MySimulation",
    "path": "workspace/projects/MySimulation",
    "created_date": "2025-01-15T10:30:00",
    "modified_date": "2025-01-15T14:45:00"
  }
}
```

Both UUID and name are indexed for efficient lookup.

### Display Methods

The `Project` class provides built-in display methods:

```python
class Project:
    def __str__(self) -> str:
        """Returns the project name (user-friendly)."""
        return self.name
    
    def __repr__(self) -> str:
        """Returns detailed representation (debugging)."""
        return f"Project(name='{self.name}', id='{self.id[:8]}...', models={len(self.models)})"
```

**Usage:**
```python
project = manager.open_project(uuid)
print(str(project))   # "MySimulation" ✓
print(repr(project))  # "Project(name='MySimulation', id='a1b2c3d4...', models=5)"
```

## API Reference

### Lookup by Name

#### `get_project_by_name(name: str) -> Optional[Project]`

Look up a project by its name (case-insensitive).

**Parameters:**
- `name`: Project name to search for

**Returns:**
- `Project` instance if found
- `None` if not found

**Example:**
```python
manager = get_project_manager()
project = manager.get_project_by_name("MySimulation")
if project:
    print(f"Found: {project.name} (ID: {project.id})")
else:
    print("Project not found")
```

**Notes:**
- Case-insensitive: "mysimulation" matches "MySimulation"
- Exact match only (no partial matching)
- Returns first match if multiple projects have same name

---

#### `find_projects_by_name(name_pattern: str) -> List[Dict]`

Find projects matching a partial name pattern.

**Parameters:**
- `name_pattern`: Partial name to search for

**Returns:**
- List of project info dictionaries containing:
  - `id`: Project UUID
  - `name`: Project name
  - `path`: Project directory path
  - `created_date`: Creation timestamp
  - `modified_date`: Last modification timestamp

**Example:**
```python
manager = get_project_manager()
matches = manager.find_projects_by_name("Sim")

for info in matches:
    print(f"- {info['name']} (ID: {info['id'][:8]}...)")

# Output:
# - MySimulation (ID: a1b2c3d4...)
# - BioSimulation (ID: f9e8d7c6...)
```

**Notes:**
- Case-insensitive partial matching
- Searches within project names (substring match)
- Returns empty list if no matches

---

#### `get_project_display_name(project_id: str) -> str`

Get the human-friendly display name for a project UUID.

**Parameters:**
- `project_id`: Project UUID

**Returns:**
- Project name if UUID found
- Truncated UUID string if not found (fallback)

**Example:**
```python
manager = get_project_manager()
uuid = "a1b2c3d4-e5f6-7890-1234-567890abcdef"

name = manager.get_project_display_name(uuid)
print(name)  # "MySimulation"

# For unknown UUID:
name = manager.get_project_display_name("unknown-uuid")
print(name)  # "Project unknown-u..."
```

**Use Case:**
Perfect for UI components that have a UUID and need to display a name.

---

#### `list_all_projects() -> List[Dict[str, Any]]`

Get a sorted list of all projects with display information.

**Returns:**
- List of project info dictionaries, sorted by name (alphabetically)
- Each dict contains: `id`, `name`, `path`, `created_date`, `modified_date`

**Example:**
```python
manager = get_project_manager()
projects = manager.list_all_projects()

for info in projects:
    print(f"{info['name']:30} {info['path']}")

# Output (sorted by name):
# BioSimulation                 workspace/projects/BioSimulation
# MySimulation                  workspace/projects/MySimulation
# TestProject                   workspace/projects/TestProject
```

**Notes:**
- Sorted alphabetically by name (case-insensitive)
- Returns all projects in the index
- Useful for building project selection UI

---

### Recent Projects

#### `get_recent_projects_info() -> List[Dict[str, Any]]`

Get information about recent projects with human-friendly names.

**Returns:**
- List of project info dicts for recently accessed projects
- Ordered by most recent access (newest first)

**Example:**
```python
manager = get_project_manager()
recent = manager.get_recent_projects_info()

for info in recent:
    print(f"Recently opened: {info['name']}")
```

**UI Integration:**
The `ProjectDialogManager` uses this method to populate the "Recent Projects" tree view with **project names** (not UUIDs).

---

## Directory Naming

Project directories use **sanitized project names**, not UUIDs:

```python
def _sanitize_directory_name(self, name: str) -> str:
    """Convert project name to valid directory name."""
    # "My Project!" → "My_Project"
    # "Analysis (v2)" → "Analysis__v2_"
```

**Rules:**
- Spaces → underscores
- Invalid chars → underscores
- Leading/trailing spaces → stripped
- Name conflicts → append counter (`MyProject_2`, `MyProject_3`)

**Example:**
```python
project = manager.create_project("My Simulation")
print(project.base_path)
# workspace/projects/My_Simulation/
```

---

## UI Integration

### Current Integration

**Project Selection Dialog** (`project_dialog_manager.py`):
- ✅ "Recent Projects" tree shows **project names** (not UUIDs)
- ✅ Location column shows project path (includes name)
- ✅ "New Project" dialog uses name as primary identifier

**Implementation:**
```python
# Line 290 in project_dialog_manager.py
for project_info in self.project_manager.get_recent_projects_info():
    list_store.append([
        project_info['name'],     # Display name ✓
        project_info['path'],     # Shows name-based path ✓
        project_info['modified_date'][:10],
        project_info['id']        # UUID stored but not displayed ✓
    ])
```

### Recommended UI Updates

For any UI components displaying project identifiers:

**Before:**
```python
label.set_text(project.id)  # "a1b2c3d4-e5f6-7890..."
```

**After:**
```python
label.set_text(str(project))  # "MySimulation"
# or
label.set_text(project.name)
# or
name = manager.get_project_display_name(project.id)
label.set_text(name)
```

---

## Best Practices

### When to Use UUID vs Name

**Use UUID (project.id) for:**
- ✅ File paths (project files, internal references)
- ✅ Database keys (project_index lookups)
- ✅ API calls (unique identification)
- ✅ Logging/debugging (unambiguous)
- ✅ Persistence (immutable identifier)

**Use Name (project.name) for:**
- ✅ User interface display
- ✅ Dialog titles
- ✅ User prompts/messages
- ✅ Project selection lists
- ✅ Window titles

### Example: Complete Workflow

```python
# Create project with user-friendly name
manager = get_project_manager()
project = manager.create_project(name="Neural Network Model")

# Display in UI (shows name)
window.set_title(f"ShyPN - {project.name}")  # "ShyPN - Neural Network Model"

# Save uses UUID internally
project.save()  # Saves to workspace/projects/Neural_Network_Model/.project

# Open from recent (lookup by UUID)
uuid = recent_projects[0]
project = manager.open_project(uuid)

# Display name in UI
print(f"Opened: {project.name}")  # "Opened: Neural Network Model"

# Search by name if UUID unknown
project = manager.get_project_by_name("Neural Network")
if project:
    print(f"Found: {project.name} (ID: {project.id[:8]}...)")
```

---

## Migration Notes

### Existing Code Compatibility

**No Breaking Changes:**
- Existing code using `project.id` continues to work
- `project.name` has always been available
- Only new **convenience methods** added for name-based lookup

**Gradual Migration:**
You can update UI components gradually:
1. Identify places displaying `project.id` to users
2. Replace with `project.name` or `str(project)`
3. Internal code using UUID unchanged

### Testing

**Verify Name Display:**
```bash
# Create a project
project = manager.create_project("Test Display")
assert str(project) == "Test Display"
assert project.name == "Test Display"

# Lookup by name
found = manager.get_project_by_name("Test Display")
assert found.id == project.id

# Display name from UUID
name = manager.get_project_display_name(project.id)
assert name == "Test Display"
```

---

## Summary

| Aspect | UUID | Name |
|--------|------|------|
| **Purpose** | Internal identifier | User-facing alias |
| **Mutability** | Immutable | Mutable (via properties dialog) |
| **Uniqueness** | Guaranteed unique (UUID4) | Can have duplicates* |
| **Display** | Development/debugging | User interface |
| **Storage** | Primary key in index | Indexed for lookup |
| **Directory** | Not used | Used (sanitized) |

*Note: While duplicate names are possible, the system handles this gracefully using UUIDs as the true identifier.

---

## Implementation Status

✅ **Completed:**
- UUID vs Name architecture
- Display methods (`__str__`, `__repr__`)
- Name-based lookup methods
- Directory naming uses sanitized names
- Recent projects UI shows names
- Documentation

**Future Enhancements:**
- Project renaming (update name while keeping UUID)
- Name conflict resolution UI
- Project templates with default names
- Import/export preserving both UUID and name
