# Directory Structure Analysis: `data/` vs `models/` Clarification

**Date:** October 8, 2025  
**Issue:** Ambiguous use of `data/` and `models/` directories causing user confusion

---

## Current Situation (PROBLEMATIC)

### Existing Repository Structure
```
shypn/
├── data/                    # ⚠️ AMBIGUOUS PURPOSE
│   ├── README.md           # Says "data models" but mixed usage
│   └── projects/           # NEW: Project management (our implementation)
│
├── models/                  # ⚠️ AMBIGUOUS PURPOSE
│   ├── simple.shy          # User's Petri net model file
│   └── pathways/           # Planned for external pathway cache
│
└── src/shypn/
    └── data/               # ⚠️ THIRD "data" location!
        └── project_models.py   # Our Python data model classes
```

### The Confusion

**Three different meanings of "data"/"models":**
1. **`data/`** (root) - Originally for "data files" but now has `projects/`
2. **`models/`** (root) - Originally for "user Petri net models" but plan wants it for cache
3. **`src/shypn/data/`** - Python module for data model classes

**Current plan mixes purposes:**
- `models/pathway/external/` → External pathway CACHE (transient)
- `data/projects/[id]/models/` → User's Petri net MODELS (persistent)
- `models/simple.shy` → Existing user model file (legacy)

---

## Original Plan Analysis (PATHWAY_DATA_ISOLATION_PLAN.md)

The plan specified:

### 1. External/Transient Data
```
models/pathway/external/kegg/    ← Cache for KEGG data
└── hsa00010.json                (auto-deleted after 30 days)
```

**Intention:** Temporary cache, not user data

### 2. Project/Persistent Data
```
data/projects/[uuid]/
├── project.shy
├── models/              ← User's Petri net models
├── pathways/            ← User's pathway edits
└── simulations/         ← Simulation results
```

**Intention:** User-owned, permanent project data

### 3. The Problem
The plan uses **`models/`** (root) for cache but **`data/projects/*/models/`** for user files.

**This is confusing because:**
- Root `models/` directory already has user file `simple.shy`
- Users expect `models/` to be for their Petri net models
- Cache data shouldn't be in a user-facing directory

---

## Recommended Solution

### Option A: Rename Root Directories (RECOMMENDED)

**Clear separation by purpose:**

```
shypn/
├── cache/                          # NEW: All transient/external data
│   ├── kegg/                       # KEGG pathway cache
│   │   └── hsa00010.json
│   └── other_sources/              # Future: Other external sources
│
├── projects/                       # RENAMED: User projects (was data/projects/)
│   ├── project_index.json
│   ├── recent_projects.json
│   └── [uuid]/
│       ├── project.shy
│       ├── models/                 # User's Petri net models
│       ├── pathways/               # User's pathway edits
│       ├── simulations/
│       └── metadata/
│
├── examples/                       # RENAMED: Example models (was models/)
│   └── simple.shy                  # Demo/tutorial models
│
├── data/                          # KEPT: Application data (if needed)
│   └── templates/                 # Model templates
│       ├── basic_petri_net.shy
│       └── kegg_template.shy
│
└── src/shypn/
    └── data/                      # Python data model classes (no change)
        └── project_models.py
```

**Benefits:**
- ✅ **`cache/`** - Clearly transient, auto-cleaned
- ✅ **`projects/`** - Clearly user projects
- ✅ **`examples/`** - Clearly demo files
- ✅ **`data/templates/`** - Application resources
- ✅ No ambiguity about what goes where

---

### Option B: Keep Current, Clarify Purpose (LESS IDEAL)

```
shypn/
├── data/                          # User data (projects + cache)
│   ├── projects/                  # User projects (persistent)
│   └── cache/                     # External cache (transient)
│       └── kegg/
│
├── models/                        # Example/demo models only
│   └── simple.shy
│
└── src/shypn/data/               # Python classes
```

**Benefits:**
- ✅ Less disruptive (fewer renames)
- ✅ `data/` becomes clear parent for all data

**Drawbacks:**
- ⚠️ `models/` becomes confusing (why just examples?)
- ⚠️ Cache hidden inside `data/` not obvious

---

### Option C: Minimal Change (QUICK FIX)

```
shypn/
├── data/                          # Keep as-is
│   ├── cache/                     # NEW: Move cache here
│   │   └── kegg/
│   └── projects/                  # Keep
│
├── models/                        # Keep for user models
│   ├── simple.shy                 # Legacy support
│   └── README.md                  # "Place user models here"
│
└── src/shypn/data/               # Keep
```

**Benefits:**
- ✅ Minimal disruption
- ✅ Cache clearly under `data/cache/`
- ✅ `models/` keeps intuitive meaning

**Drawbacks:**
- ⚠️ Still mixing concepts in root
- ⚠️ Plan must be updated

---

## Impact Analysis

### Files to Update (Option A - Recommended)

**Python Code:**
1. `src/shypn/data/project_models.py`
   - Change: `data/projects/` → `projects/`
   - Update: `ProjectManager.projects_root` default path

2. `src/shypn/helpers/left_panel_loader.py`
   - Change: `models/` → `examples/` for base_path default

3. Future KEGG importer (Phase 4):
   - Use: `cache/kegg/` instead of `models/pathway/external/kegg/`

**Documentation:**
1. `PATHWAY_DATA_ISOLATION_PLAN.md`
   - Update all directory references
   - Update diagrams

2. `PROJECT_MANAGEMENT_IMPLEMENTATION.md`
   - Update directory structure section

3. Create `DIRECTORY_STRUCTURE.md` (new)
   - Clear explanation of each directory
   - Migration guide for existing users

**Git Operations:**
```bash
git mv models/ examples/
git mv data/projects/ projects/
mkdir -p cache/kegg
mkdir -p data/templates
```

---

## Recommendation Summary

**RECOMMENDED: Option A - Rename Root Directories**

**Rationale:**
1. **Clarity:** Each directory has single, clear purpose
2. **User-Friendly:** Intuitive names (cache, projects, examples)
3. **Future-Proof:** Easy to add new data sources
4. **Professional:** Matches industry standards

**Next Steps:**
1. ✅ Discuss with user (confirm approach)
2. 🔄 Update Python code paths
3. 🔄 Rename directories with git mv
4. 🔄 Update documentation
5. 🔄 Create migration guide
6. 🔄 Test all functionality

**Estimated Time:** 30-60 minutes

---

## User Impact

### For Existing Users (if any)

**Before (confusing):**
```
Where do I put my models? → models/ or data/projects/[id]/models/?
What is models/pathway/? → Is this mine?
```

**After (clear):**
```
Where do I put my models? → Create project, save in projects/[id]/models/
What is cache/? → Automatic, ignore it
What is examples/? → Demo files, can delete
```

---

## Questions for Resolution

1. **Do we have existing users with files in `models/`?**
   - If yes: Need migration script
   - If no: Clean rename

2. **Is `simple.shy` important?**
   - If yes: Keep as example
   - If no: Can delete

3. **Do we need backward compatibility?**
   - If yes: Support old paths temporarily
   - If no: Clean break

4. **Timeline preference?**
   - Now: Clean slate (recommended)
   - Later: After more features

---

## Conclusion

The current dual use of `data/` and `models/` creates confusion. **Option A (rename to `cache/`, `projects/`, `examples/`)** provides the clearest structure for users and developers.

**Decision Required:** Which option to proceed with?
