# Phase 6 Quality Plan — God Class Reduction via OOP Extraction

**Status:** Sprint 15 next (Sprint 14 ✅ complete)  
**Branch:** Usability-and-enhancements  
**Precursor:** Sprint 12 (CSV normalization, metadata fixes) — committed `834ec18`  
**Methodology:** Extract cohesive clusters into typed service classes (ABC + concrete), one module per service.

---

## Context — God Class Audit Results

*Full audit performed post-Sprint 12. Top findings:*

### Tier 1 — Severe (> 3 000 lines)

| Class | File | Lines | Methods | Attrs |
|---|---|---|---|---|
| `ModelCanvasLoader` | `helpers/model_canvas_loader.py` | 5 370 | 135 | 32 |
| `ModelCanvasManager` | `data/model_canvas_manager.py` | 3 281 | 190 | 35 |

### Tier 2 — Major (1 700–2 900 lines)

| Class | File | Lines | Methods |
|---|---|---|---|
| `FileExplorerPanel` | `ui/panels/file_explorer_panel.py` | 2 910 | 109 |
| `ViabilityPanel` | `ui/panels/viability_panel.py` | 2 832 | 74 |
| `SimulationController` | `engine/simulation/controller.py` | 2 822 | 64 |
| `SBMLCategory` | `data/pathway/sbml_category.py` | 2 771 | 66 |
| `KEGGCategory` | `data/pathway/kegg_category.py` | 2 262 | 59 |

---

## Priority Queue

| Priority | Target class | Extraction | Risk | Module |
|---|---|---|---|---|
| 🔴 **P1** | `ModelCanvasManager` | `ArcGeometryService` | Low — pure math, no GTK | `core/services/arc_geometry_service.py` |
| 🔴 **P2** | `SimulationController` | `ConflictResolver` | Low — pure algorithm, no UI | `engine/simulation/conflict_resolver.py` |
| 🟠 P3 | `ModelCanvasManager` | `ViewportController` split | Medium | Refactor existing `viewport_controller.py` | ✅ Sprint 14 |
| 🟠 P4 | `ModelCanvasLoader` | `CanvasInputHandler` | Medium | New `helpers/canvas_input_handler.py` |
| 🟡 P5 | `ViabilityPanel` | `LocalityController` | Medium | New `ui/locality_controller.py` |
| 🟡 P6 | `SBMLCategory`/`KEGGCategory` | `PathwayImportService` | Low | New `data/pathway/import_service.py` |

---

## OOP Hierarchy Requirements

Each extracted service **must** follow this pattern:

```
AbstractXxxService (ABC)        ← defines the public contract
    └── XxxService               ← concrete implementation in the SAME module
```

*Services go in their own module. The ABC lives at the top of that module, the concrete below it.*

### Design rules

1. `from __future__ import annotations` at top of every new module.
2. Full type annotations on all public and private methods.
3. `ABC` from `abc`, `@abstractmethod` for every public operation.
4. Dependency injection via constructor — never import the caller's class.
5. Stateless pure-math methods stay `@staticmethod` in the concrete class.
6. The God class keeps only a thin delegation wrapper (`self._service.method(args)`).
7. Backward compatibility: where callers already use standalone functions (e.g. `detect_parallel_arcs`), keep the functions as module-level shims that call the class.

---

## Sprint 13 — P1 + P2 Implementation

### 1. `ArcGeometryService` (`src/shypn/core/services/arc_geometry_service.py`)

**Cluster extracted from `ModelCanvasManager` lines 1 268–1 692:**

| Method | Static? | Notes |
|---|---|---|
| `detect_parallel_arcs` | no | reads `arcs` list |
| `_auto_convert_parallel_arcs_to_curved` | no | orchestrator |
| `_validate_arc_references` | no | guard |
| `_convert_loop_arc` | no | mutates arcs |
| `_find_opposite_direction_arc` | no | search |
| `_calculate_perpendicular_offset` | no | uses statics |
| `_compute_direction_vector` | **yes** | pure math |
| `_normalize_vector` | **yes** | pure math |
| `_compute_perpendicular_vector` | **yes** | pure math |
| `_compute_offset_pair` | **yes** | pure math |
| `_convert_opposite_direction_pair` | no | mutates arcs |
| `_convert_same_direction_parallels` | no | mutates arcs |
| `_replace_arc_in_list` | no | mutates arcs |
| `_separate_parallel_arcs` | **yes** | pure sort |
| `_calculate_opposite_direction_offset` | **yes** | pure math |
| `_calculate_same_direction_offset` | **yes** | pure math |
| `calculate_arc_offset` | no | delegates |
| `replace_arc` | no | mutates + dirty |
| `ensure_arc_references` | no | repairs refs |

**Constructor signature:**
```python
ArcGeometryService(
    manager: Any,            # ModelCanvasManager (for arcs list + callbacks)
)
```

`self._manager` gives access to `manager.arcs`, `manager._on_object_changed`,
`manager.mark_modified()`, and `manager.mark_dirty()`.

**`ModelCanvasManager` delegation pattern:**
```python
# __init__ (after document_controller setup):
from shypn.core.services.arc_geometry_service import ArcGeometryService
self._arc_geometry = ArcGeometryService(manager=self)

# Method body replaces inline code:
def detect_parallel_arcs(self, arc):
    return self._arc_geometry.detect_parallel_arcs(arc)
```

---

### 2. `ConflictResolver` (`src/shypn/engine/simulation/conflict_resolver.py`)

**Cluster extracted from `SimulationController` lines 1 711–2 363:**

| Method group | Phase | Methods |
|---|---|---|
| Conflict graph | Phase 1 | `_are_independent`, `_compute_conflict_sets`, `_get_independent_transitions` |
| Maximal sets | Phase 2 | `_find_maximal_concurrent_sets`, `_greedy_maximal_set`, `_sort_by_conflict_degree`, `_is_concurrent_set_maximal` |
| Atomic execution | Phase 3 | `_select_maximal_set`, `_validate_all_can_fire`, `_snapshot_marking`, `_restore_marking`, `_execute_maximal_step` |

Also requires `_get_all_places_for_transition` (helper used by `_are_independent`).

**Constructor signature:**
```python
ConflictResolver(
    model: Any,              # Petri net model (places, transitions, arcs)
    viability_checker: Any,  # ViabilityChecker instance
)
```

**`SimulationController` delegation pattern:**
```python
# __init__ (after _viability_checker is set):
from shypn.engine.simulation.conflict_resolver import ConflictResolver
self._conflict_resolver = ConflictResolver(
    model=self.model,
    viability_checker=self._viability_checker,
)

# Method body:
def _compute_conflict_sets(self, transitions):
    return self._conflict_resolver.compute_conflict_sets(transitions)
```

---

## Planned Sprints P3–P6

### Sprint 14 — `ViewportController` cleanup (P3)

*`ModelCanvasManager` ADR explicitly allows viewport-algorithm extraction.*  
Extract zoom math and hit-test formulas into the existing `ViewportController` class.  
Target: remove ~180 lines from `ModelCanvasManager`.

### Sprint 15 — `CanvasInputHandler` (P4)

Extract raw GDK event dispatch from `ModelCanvasLoader` into a stateless handler.  
Covers: button press/release, motion, scroll, key events (~420 lines).  
Risk: must preserve focus-management semantics (pseudo-MDI constraint).

### Sprint 16 — `LocalityController` (P5)

Extract locality management (add/remove/validate localities) from `ViabilityPanel`.  
Also decouple simulation proxy calls from UI bindings.

### Sprint 17 — `PathwayImportService` (P6)

Common ABC for `SBMLCategory` and `KEGGCategory` import pipeline:  
fetch → parse → validate → persist → display metadata.  
Reduces duplication of ~600 lines shared between the two classes.

---

## Quality Enforcement Checklist (per extraction)

### Sprint 13 — P1 `ArcGeometryService` + P2 `ConflictResolver` ✅

- [x] `from __future__ import annotations` present
- [x] All parameters type-annotated (no bare `Any` except true duck-typing boundaries)
- [x] All return types annotated
- [x] `mypy --strict` passes on the new module (or justified `# type: ignore` with comment)
- [x] `@abstractmethod` for every interface method in the ABC
- [x] Existing tests still pass (`pytest tests/engine/ tests/engine_core/` — 37 passed)
- [x] God class line count decreased by extracted cluster size
- [x] Module-level docstring describing the service's single responsibility

### Sprint 14 — `ViewportController` cleanup (P3) ✅

- [x] Coordinate-transform methods (`screen_to_world`, `world_to_screen`, `get_visible_bounds`, `get_visible_bounds_no_rotation`, `get_grid_spacing`) moved from `ModelCanvasManager` to `ViewportController`
- [x] Private rotation helpers (`_calculate_rotation_center`, `_apply_rotation_to_point`) deleted from MCM, reimplemented in VC
- [x] Dead duplicate methods (`find_object_at_position`, `clear_all_selections`) removed from MCM
- [x] Unused imports (`import math`, `coord_screen_to_world`, `coord_world_to_screen`) removed from MCM
- [x] `cast(float, ...)` / `cast(Tuple[float, float], ...)` added to silence `no-any-return` in new VC methods
- [x] `mypy --strict --follow-imports=skip` — no new errors introduced
- [x] `pytest tests/engine/ tests/engine_core/` — 37 passed
- [x] `ModelCanvasManager` reduced from 2 480 → 2 341 lines (−139 lines; target ~180)

### Future sprints checklist template

- [ ] `from __future__ import annotations` present
- [ ] All parameters type-annotated (no bare `Any` except true duck-typing boundaries)
- [ ] All return types annotated
- [ ] `mypy --strict` passes on the new module (or justified `# type: ignore` with comment)
- [ ] `@abstractmethod` for every interface method in the ABC
- [ ] Existing tests still pass (`pytest tests/`)
- [ ] God class line count decreased by extracted cluster size
- [ ] Module-level docstring describing the service's single responsibility

---

*Next action: implement Sprint 15 — `CanvasInputHandler` (P4).*
