# Dock / Undock UI Design (GTK4)

This document describes a componentized GTK4 UI architecture using dockable
and undockable panels. The purpose is to rewrite UIs directly in GTK4 and
reuse legacy GTK3 business logic via adapters. Panels are independent UIs
that can be integrated incrementally.

## Goals

- Build a modern GTK4 UI with dock/undock behavior.
- Split the UI into small, independent panels so integration is incremental.
- Avoid porting legacy GTK3 UI code; instead import legacy non-UI logic via
  adapters once the new GTK4 panels are ready.

## High-level architecture

- `Main Window` (GTK4): contains the `DockManager` and the central workspace.
- `Panels`: independent UI modules (one per panel) that produce a GTK widget
  and register on the application bus.
- `DockManager`: API to add/remove/dock/undock panels and persist layout.
- `Application Bus`: lightweight pub/sub + request/response for panel-to-panel
  communication and to call adapters.
- `Adapters`: thin shims that expose legacy logic with the new contracts.

### Responsibilities

- Main Window: manage top-level layout, boot panels, and persist layout.
- DockManager: manage panel docking, floating windows, serialization.
- Panel modules: self-contained UI + controller; expose a small public API
  and accept a `panel_bus` for communication.
- Adapters: provide functions that the panels call to fetch/modify domain
  data; adapters call into legacy business logic or its port.

## Component contracts

- Panel init signature: `init(panel_bus) -> (panel_id, Gtk.Widget)`
- Events on bus: `emit(event_name, payload)`, `on(event_name, handler)`,
  `request(name, payload) -> result` (sync/async depending on implementation).
- Data shapes: use JSON-serializable dicts or Python dataclasses for domain
  entities (e.g., `TransitionProps`). Keep them explicit and simple.

## UI files and layout

Suggested layout under `ui/`:

- `ui/main_window.py` — GTK4 bootstrap + DockManager
- `ui/panels/<panel_name>/` — each panel in own folder
  - `ui/` optional UI definitions
  - `controller.py` panel implementation
  - `tests/` small unit tests

Example file layout:

```
ui/
  DOCK_UNDOCK_DESIGN.md
  main_window.py
  panels/
    properties/
      controller.py
      ui/  # optional
    inspector/
    graph/
```

## Docking behaviours

- Docked panels are direct children within the main layout (left/right/top/bottom).
- Floating panels are separate Gtk.Window instances owned by the DockManager.
- Drag-and-drop docking: implement a drag preview and drop targets in the
  DockManager. On drop, call `dock_panel(panel_id, position)`.

## Persistence

- Save layout as a small JSON mapping: `panel_id -> { mode: docked|floating, position, geometry }`.
- On startup, recreate panels and call `dock_panel`/`undock_panel` accordingly.

## Legacy logic adapter strategy

1. Define small data contracts that panels use (inputs/outputs).
2. Implement an adapter module that provides these functions and internally
   calls legacy logic (or a port of it). Adapter tests should validate the
   mapping.
3. Panels call adapter functions via the bus; the adapter returns plain
   Python data structures (no GTK objects).

Advantages:

- Keeps new UI code clean and GTK4-native.
- Limits migration effort to adapters that translate legacy logic to new
  contracts.

## Testing and verification

- Unit tests for adapters mapping legacy functions to new contracts.
- Panel tests using a mock bus (no GTK3 dependency).
- Manual smoke tests for layout persistence and docking UX.

## Optional scaffold (if you want me to create it)

- `ui/main_window.py` — minimal GTK4 window + DockManager API.
- `ui/panels/sample_panel/controller.py` — simple panel demonstrating
  add/remove and dock/undock.
- `gtk4_app.py` — tiny bootstrap that starts the GTK4 app.

If you'd like the scaffold, tell me and I'll create a lightweight GTK4
example that runs under your environment.

## Next steps

- Decide if you want the GTK4 scaffold created now.
- If yes, I will scaffold the files and run a small smoke test.
- Otherwise, start implementing panels following the contracts above and
  I can help implement adapters for legacy logic as needed.

## UI-first decoupling rule

Policy: UI definitions must live in declarative UI files under `ui/` (GTK
builder XML, GtkTemplate, or other UI formats). Project code (Python modules)
must not embed UI structure or markup; code should only load UI files and
wire behaviour (signal handlers, bus registration, and controller logic).

Why:
- Keeps design and layout editable by non-programmers and designers.
- Makes it easier to replace UI frameworks or regenerate views from tools.
- Reduces accidental divergence between layout and runtime behaviour.

Practical guidance:
- Store widget hierarchies, CSS classes, and IDs in `ui/` files. Keep
  naming consistent using the `panel_<name>__widget` convention for IDs.
- Controllers (e.g., `controller.py`) should import the UI, query widgets by
  ID, connect signals, and expose a small public API. They should not create
  top-level widgets except when a panel needs a dynamic container.
- Use data-only objects (dicts/dataclasses) for state passed between panels
  or adapters; avoid passing GTK objects across adapters or between panels.
- When a small bit of UI must be generated programmatically (rare), wrap it
  behind a factory function and document why the code path is necessary.

Examples:
- Good: `panel = builder.get_object("panel_transitions_root")`
  `controller = TransitionsController(panel, bus)`
- Bad: `panel = Gtk.Box()` + `panel.append(Gtk.Label("Transitions"))`

Enforcement suggestions (manual/team rules):
- During code reviews, prefer diffs where `ui/` files change for layout
  modifications and `controller.py` changes only wire behaviour.
- Add a lightweight lint check (optional): scan for `Gtk.` constructor calls
  outside `scripts/` or `ui/panels/*/controller.py` and flag them for review.

Add this rule to the project handbook and follow it when implementing new
panels or migrating legacy views.

--
DOCK/UNDOCK design document created by the migration planning session.

## No-fallbacks rule

Policy: Do not include runtime fallbacks in application code, and especially
not in UI code. A fallback is any runtime behavior that silently substitutes
an alternative implementation, a different UI layout, or a legacy script
when the primary resource (UI file, module, adapter) is missing or fails to
load. The project must fail fast and loudly instead of silently falling back.

Rationale:
- Silent fallbacks hide defects and make debugging and testing harder.
- They create inconsistent user experiences depending on runtime state or
  environment differences.
- They defeat the "UI-first" rule by masking missing or incorrect UI files.

Practical guidance:
- On missing UI files or import errors, raise a clear exception and fail
  application startup. Log an explicit error with the filename, module, and
  a short remediation suggestion.
- Avoid subprocess-based fallback runners for UI behavior. If you must keep
  legacy test scripts, keep them as developer tools (in `tools/` or
  `scripts/`) and never call them from production code paths.
- Prefer explicit feature flags and staged migration builds rather than
  runtime fallback switches.

Error-handling pattern (recommended):
- Attempt to load required resources during initialization. If load fails,
  log and raise a dedicated error type (e.g., `UIResourceMissingError`) so
  calling code can decide to abort startup or show a clearly defined
  diagnostic screen (not a silently different UI).

Enforcement suggestions:
- CI should run a smoke startup test that ensures all declared `ui/` files
  referenced by panels can be loaded. Failure should block merge.
- Code reviews should flag any code that attempts to `subprocess`-launch a
  fallback UI script from the main runtime path.

Migration note:
- During migration, keep developer-only fallback harnesses in `scripts/`
  (not in `src/`). Use them only for manual testing and clearly mark them
  with README guidance. Do not wire them into `src/shypn.py` or production
  startup code.
