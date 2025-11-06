# Simulation Palette Initialization Order Fix

## Problem Report

User reported: "after last two patches simulation tools are not revealing" when clicking the Simulate button in SwissKnife palette.

**Symptoms:**
- Application crashed with AttributeError on startup
- Simulation tools palette never appeared
- Error: `AttributeError: 'SimulateToolsPaletteLoader' object has no attribute 'duration_entry'`

## Analysis Process

### 1. Version Comparison

Compared current HEAD with v0.9.0-global-sync-multi-canvas (commit `b3e7c7d`) which was confirmed working.

**Commits since v0.9.0:**
```
eb9c32f - Fix simulation tools palette not revealing (incorrect diagnosis)
52a04c2 - fix: enable progress bar by applying default duration on initialization  
6556415 - feat: integrate BufferedSimulationSettings for atomic parameter updates
5ab3555 - fix: add TIME_EPSILON precision tolerance for simulation ending
e3e9f5a - docs: comprehensive analysis of simulation parameters
fe223d3 - feat: add playback speed spinner to simulation parameters panel
6658373 - refactor: remove Conflict Policy and action buttons from parameters panel
9d52da2 - refactor: remove playback speed buttons from simulation parameters panel
```

### 2. Initial Hypothesis (Wrong)

Initially suspected GTK widget visibility issues:
- Missing `show_all()` call
- Nested revealer visibility problems  
- GTK widget hierarchy issues

**Evidence that disproved this:**
- v0.9.0 also didn't have `show_all()` call
- SwissKnifePalette code was identical between versions
- Revealer setup was unchanged

### 3. Actual Root Cause Discovery

Running the application revealed the true problem:

```python
Traceback (most recent call last):
  File "/home/simao/projetos/shypn/src/shypn/helpers/simulate_tools_palette_loader.py", line 82, in __init__
    self._init_simulation_controller()
  File "/home/simao/projetos/shypn/src/shypn/helpers/simulate_tools_palette_loader.py", line 428, in _init_simulation_controller
    self._apply_ui_defaults_to_settings()
  File "/home/simao/projetos/shypn/src/shypn/helpers/simulate_tools_palette_loader.py", line 444, in _apply_ui_defaults_to_settings
    if self.duration_entry:
       ^^^^^^^^^^^^^^^^^^^
AttributeError: 'SimulateToolsPaletteLoader' object has no attribute 'duration_entry'
```

## Root Cause

### Initialization Order Bug

**File:** `src/shypn/helpers/simulate_tools_palette_loader.py`

**Broken sequence (commits 52a04c2 + 6556415):**

```python
def __init__(self, model=None, ui_dir=None):
    super().__init__()
    # ... path setup ...
    self.ui_path = os.path.join(ui_dir, 'simulate_tools_palette.ui')
    self.simulation = None
    self._model = model
    self.data_collector = SimulationDataCollector()
    
    # ❌ PROBLEM: Called TOO EARLY!
    if model is not None:
        self._init_simulation_controller()  # Tries to access UI widgets
    
    # ❌ UI widgets not loaded yet!
    self.builder = None
    self.duration_entry = None  # Just setting to None, not loading from UI
    self.progress_bar = None
    # ... other widgets ...
    
    self._load_ui()  # ← UI actually loaded HERE!
```

**What happens:**
1. `_init_simulation_controller()` is called on line 82
2. It calls `_apply_ui_defaults_to_settings()` (added in 52a04c2)
3. That tries to access `self.duration_entry`
4. But `duration_entry` is just `None` - not loaded yet!
5. UI widgets are only loaded when `_load_ui()` is called on line 95

### Why This Was Introduced

**Commit 52a04c2:** "fix: enable progress bar by applying default duration on initialization"

This commit added `_apply_ui_defaults_to_settings()` which reads `duration_entry` from the UI:

```python
def _apply_ui_defaults_to_settings(self):
    """Apply default UI values to simulation settings on initialization."""
    if self.simulation is None:
        return
    
    # ❌ Assumes duration_entry exists!
    if self.duration_entry:
        try:
            duration_text = self.duration_entry.get_text().strip()
            duration = float(duration_text)
            # ...
```

This method is called from `_init_simulation_controller()`, which was being called BEFORE `_load_ui()`.

### v0.9.0 Comparison

In v0.9.0, `_init_simulation_controller()` existed but didn't try to access UI widgets during initialization. The progress bar fix added that requirement.

## Solution

Move `_init_simulation_controller()` call to **AFTER** `_load_ui()`:

```python
def __init__(self, model=None, ui_dir=None):
    super().__init__()
    # ... path setup ...
    self.ui_path = os.path.join(ui_dir, 'simulate_tools_palette.ui')
    self.simulation = None
    self._model = model
    self.data_collector = SimulationDataCollector()
    
    # Set widget references to None first
    self.builder = None
    self.duration_entry = None
    self.progress_bar = None
    # ... other widgets ...
    
    # Load UI widgets from file
    self._load_ui()
    
    # ✅ NOW it's safe to initialize simulation controller
    # Initialize simulation controller AFTER UI is loaded
    if model is not None:
        self._init_simulation_controller()
```

**Why this works:**
1. UI widgets are loaded first via `_load_ui()`
2. `duration_entry`, `progress_bar`, etc. are now actual GTK widgets (not None)
3. `_init_simulation_controller()` can safely call `_apply_ui_defaults_to_settings()`
4. `_apply_ui_defaults_to_settings()` can now read from `self.duration_entry`

## Changes Made

### File: `src/shypn/helpers/simulate_tools_palette_loader.py`

**Before:**
```python
        self.data_collector = SimulationDataCollector()
        if model is not None:
            self._init_simulation_controller()  # Line 82
        self.builder = None
        # ... widget declarations ...
        self._load_ui()  # Line 95
```

**After:**
```python
        self.data_collector = SimulationDataCollector()
        self.builder = None
        # ... widget declarations ...
        self._load_ui()
        
        # Initialize simulation controller AFTER UI is loaded
        if model is not None:
            self._init_simulation_controller()
```

### File: `src/shypn/helpers/model_canvas_loader.py`

Removed unnecessary `show_all()` call that was added in eb9c32f (incorrect fix attempt):

```python
        # Add to overlay
        overlay_widget.add_overlay(swissknife_widget)
        # Removed: swissknife_widget.show_all()  # Wasn't in v0.9.0
```

## Testing

**Before fix:**
```
$ python src/shypn.py
AttributeError: 'SimulateToolsPaletteLoader' object has no attribute 'duration_entry'
[Application crash]
```

**After fix:**
```
$ python src/shypn.py
[Application starts successfully]
[Can load models and open Simulate palette]
```

## Lesson Learned

**Initialization Order Matters!**

When adding new functionality that accesses UI widgets (like `_apply_ui_defaults_to_settings()`), ensure:

1. ✅ UI is loaded first (`_load_ui()`)
2. ✅ Widget references exist before accessing them
3. ✅ Any initialization that depends on UI happens AFTER UI load
4. ✅ Consider the order of operations in `__init__()`

**Red Flags:**
- Accessing `self.some_widget` before it's loaded from UI
- Calling methods that assume widgets exist
- Early initialization with side effects

**Best Practice:**
```python
def __init__(self):
    # 1. Set up basic state
    self._setup_basic_state()
    
    # 2. Load UI and create widgets
    self._load_ui()
    
    # 3. Initialize components that depend on UI
    self._init_dependent_components()
```

## Commit

```
eac6a1a fix: simulation tools palette not revealing - initialization order bug
```

**Fixes:** Simulation tools palette not revealing after commits 52a04c2 and 6556415

**Related Commits:**
- eb9c32f - Incorrect fix attempt (added show_all())
- 52a04c2 - Introduced _apply_ui_defaults_to_settings()
- 6556415 - Added BufferedSimulationSettings integration
