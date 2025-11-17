# Phase 2: User Feedback UI - Architecture Diagram
**REVISED after SHYPN architecture reconnaissance**

## Actual SHYPN Architecture (Discovered)

### Master Palette + Panel System

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        SHYPN Main Window (GtkApplicationWindow)             │
├─────────┬───────────────────────────────────────────────────────────────────┤
│ Master  │                                                                     │
│ Palette │  ┌──────────────────────┐         ┌─────────────────────────────┐ │
│ (48px)  │  │ Left Dock (GtkStack) │         │  Model Canvas Workspace     │ │
│         │  │ ──────────────────── │         │  (Petri Net Editor)         │ │
│ ┌─────┐ │  │                      │         │                             │ │
│ │Files│◄┼──┼► Files Panel         │         │   ●────[T1]────●           │ │
│ └─────┘ │  │  • File explorer     │         │        │                    │ │
│ ┌─────┐ │  │  • New/Open/Save     │         │   ●────[T2]────●           │ │
│ │Path.│◄┼──┼► Pathway Operations  │         │                             │ │
│ └─────┘ │  │  • KEGG (category)   │         └─────────────────────────────┘ │
│ ┌─────┐ │  │  • SBML (category)   │                                          │
│ │Anly.│◄┼──┼► Dynamic Analyses     │                                          │
│ └─────┘ │  │  • BRENDA (category) │                                          │
│ ┌─────┐ │  │  • SABIO-RK (cat.)   │                                          │
│ │Topo.│◄┼──┼► Topology Panel       │  • Heuristic (cat.) │                                          │
│ └─────┘ │  │  • Cycles analysis   │         │  • Transitions (category)    │ │
│ ┌─────┐ │  │  • P-Invariants      │         │  • Places (category)         │ │
│ │Viab.│◄┼──┼► Viability Panel      │         │  • Diagnostics (category)    │ │
│ └─────┘ │  │  • Auto-repair       │         └──────────────────────────────┘ │
│ ┌─────┐ │  │                      │                                          │
│ │Rept.│◄┼──┼► Report Panel        │  **All panels use CategoryFrame         │
│ └─────┘ │  │  • Document gen      │    architecture (collapsible sections)**│
│         │  └──────────────────────┘                                          │
└─────────┴───────────────────────────────────────────────────────────────────┘

**Key Insight**: Panels use **CategoryFrame** pattern (collapsible expanders),
not tabs! Each category (KEGG, SBML, BRENDA, SABIO-RK, Heuristic) is its own
expandable section within Pathway Operations panel.

## Where Does History Panel Go?

### Option 1: New Category in Pathway Operations Panel ⭐ RECOMMENDED
```
Pathway Operations Panel (Left Dock, GtkStack)
├── KEGG Category (collapsed)
├── SBML Category (collapsed)
├── BRENDA Category (collapsed)
├── SABIO-RK Category (collapsed)
├── Heuristic Parameters Category (collapsed)
└── 🆕 Enrichment History Category (NEW - collapsed by default)
    ├── Filters (source, pathway, date, rating)
    ├── History list (TreeView)
    └── Detail view with Undo button
```

**Rationale**:
- All enrichment-related operations in ONE panel
- Follows existing CategoryFrame pattern
- Natural workflow: Import → Enrich → Review History
- No new Master Palette button needed
- Consistent with other panel architectures

### Option 2: New Category in Dynamic Analyses Panel
```
Dynamic Analyses Panel (Left Dock, GtkStack)
├── Transitions Category
├── Places Category
├── Diagnostics Category
└── 🆕 Enrichment History Category (NEW)
```

**Issues**:
- Dynamic Analyses is for real-time simulation data
- History is for enrichment provenance (different domain)
- Would mix concerns

### Option 3: New Standalone Panel (NOT Recommended)
- Would need new Master Palette button
- Adds UI complexity
- Breaks workflow (switch panels to review history)

---

## Revised Integration Flow

### User Workflow

```
1. User clicks "Pathways" in Master Palette
2. Pathway Operations panel shows in left dock
3. User expands SABIO-RK category
4. User enriches transition with SABIO-RK data
                 ↓
5. Parameter applied → Rating dialog appears (optional)
                 ↓
6. User rates parameter or skips
                 ↓
7. User can expand "Enrichment History" category to review
                 ↓
8. User can undo/change rating from history view
```

### Technical Flow

```
User Action                   Component                     Database Operation
───────────                   ─────────                     ──────────────────

ENRICHMENT:
Apply params via    →    SabioRKCategory.on_enrich()
SABIO-RK category        ↓
                         SabioRKEnrichmentController
                         .apply_parameters()
                         ↓
                         ParameterTracker.track_application()
                         ↓                                →  INSERT INTO 
                         Show ParameterRatingDialog            transition_parameters
                         ↓
User rates          →    Dialog.get_rating()
                         ↓
                         ParameterTracker.update_rating()
                         ↓                                →  UPDATE transition_parameters
                                                              SET user_rating = ?

HISTORY VIEWING:
User expands        →    EnrichmentHistoryCategory
"Enrichment              .load_history()
History" category        ↓
                         ParameterTracker
                         .get_filtered_history()
                         ↓                                →  SELECT * FROM
                         Display in TreeView                  transition_parameters
                         with filters                         WHERE ...

UNDO:
User selects entry  →    HistoryCategory.on_undo_clicked()
and clicks Undo          ↓
                         Show confirmation dialog
                         ↓
                         ParameterTracker.undo_application()
                         • Get previous values
                         • Revert transition state
                         ↓                                →  UPDATE transition_parameters
                         Update canvas                        SET undone = true,
                         Refresh history                      undo_timestamp = NOW()
```

---

## Enrichment Controllers Layer

```
Pathway Operations Panel Categories:

┌──────────────────────────────────────────────────────────┐
│  SABIO-RK Category                                       │
│  ├─ UI controls (organism, EC, search)                  │
│  ├─ Results display                                     │
│  └─ Enrich button                                       │
│       ↓                                                  │
│  SabioRKEnrichmentController                            │
│  • query_for_transition() → checks cache first         │
│  • apply_parameters() → tracks application             │
│  • show_rating_dialog() → collects user feedback ✨NEW │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│  BRENDA Category                                         │
│  ├─ UI controls (EC search, filters)                    │
│  ├─ Results display                                     │
│  └─ Enrich button                                       │
│       ↓                                                  │
│  BRENDAEnrichmentController                             │
│  • query_database() → checks cache first               │
│  • apply_parameters() → tracks application             │
│  • show_rating_dialog() → collects user feedback ✨NEW │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│  🆕 Enrichment History Category                          │
│  ├─ Filters (dropdown combos)                           │
│  ├─ History TreeView (scrollable list)                  │
│  ├─ Detail view (selected entry)                        │
│  └─ Action buttons (View, Rate, Undo)                   │
│       ↓                                                  │
│  EnrichmentHistoryController                            │
│  • load_history() → gets filtered data                 │
│  • on_undo() → reverts application                     │
│  • on_change_rating() → updates rating                 │
└──────────────────────────────────────────────────────────┘
```

---
## Component Details

### 🆕 1. ParameterRatingDialog (Modal Dialog)
**Status**: ✅ Already created (`src/shypn/ui/dialogs/parameter_rating_dialog.py`)


│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  ParameterRatingDialog (Modal GTK Dialog)                             │  │
│  │                                                                         │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │  Parameter Details                                               │  │  │
│  │  │  • Source: SABIO-RK / BRENDA / Heuristic                         │  │  │
│  │  │  • EC Number: 2.7.1.1                                            │  │  │
│  │  │  • Organism: Homo sapiens                                        │  │  │
│  │  │  • Applied Parameters: {Km: 0.1 mM, Vmax: 226 mM/s}             │  │  │
│  │  │  • Confidence: 85%                                               │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                         │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │  Your Rating                                                     │  │  │
│  │  │  ┌──────────┐  ┌──────────┐  ┌──────────┐                       │  │  │
│  │  │  │ 👎 Poor  │  │ 🤷 Unsure│  │ 👍 Good  │                       │  │  │
│  │  │  │  (-1)    │  │   (0)    │  │   (+1)   │                       │  │  │
│  │  │  └──────────┘  └──────────┘  └──────────┘                       │  │  │
│  │  │                                                                   │  │  │
│  │  │  Optional comment: ┌────────────────────────────────────┐       │  │  │
│  │  │                    │ Text area for user feedback        │       │  │  │
│  │  │                    └────────────────────────────────────┘       │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                         │  │
│  │  [ Skip ]                                               [ Submit ]     │  │
## Component Details

### 🆕 1. ParameterRatingDialog (Modal Dialog)
**Status**: ✅ Already created (`src/shypn/ui/dialogs/parameter_rating_dialog.py`)

**Architecture**:
```python
class ParameterRatingDialog(Gtk.Dialog):
    """Modal dialog for rating parameter applications.
    
    Shows after parameter application (optional - can skip).
    Collects thumbs up/down/neutral + optional comment.
    """
    - Parent: Gtk.Dialog (modal, transient_for=parent_window)
    - Size: 500x400px
    - Buttons: Skip (Cancel), Submit (OK)
    - Rating: -1 (poor), 0 (unsure), 1 (good)
    - Comment: Optional text area
```

**Integration Points**:
- Called by SABIO-RK/BRENDA controllers after `apply_parameters()`
- Results stored via `ParameterTracker.update_rating()`
- Wayland-safe (proper parent window handling)

**UI Flow**:
```
SabioRKCategory.on_enrich()
  ↓
controller.apply_parameters(transition, params)
  ↓
tracker.track_application(...)  # Initial record
  ↓
dialog = ParameterRatingDialog(parent_window, param_info)
feedback = dialog.run_and_get_feedback()
  ↓
if feedback:
    tracker.update_rating(record_id, feedback['rating'], feedback['comment'])
```

---

### 🆕 2. EnrichmentHistoryCategory (CategoryFrame)
**Status**: ⏳ TO BE CREATED

**Location**: `src/shypn/ui/panels/pathway_operations/enrichment_history_category.py`

**Architecture**:
```python
from shypn.ui.category_frame import CategoryFrame

class EnrichmentHistoryCategory(BasePathwayCategory):
    """Enrichment history viewer category.
    
    Displays all parameter applications with filters and undo capability.
    Follows the same pattern as KEGG, SBML, BRENDA categories.
    """
    def __init__(self, model_canvas_loader=None):
        super().__init__(
            title="Enrichment History",
            expanded=False  # Collapsed by default
        )
        self.model_canvas_loader = model_canvas_loader
        self.tracker = ParameterTracker(HeuristicDatabase())
        
        # UI components
        self.source_filter = None  # ComboBox
        self.pathway_filter = None  # ComboBox
        self.date_filter = None  # ComboBox
        self.rating_filter = None  # ComboBox
        self.history_tree = None  # TreeView
        self.detail_view = None  # TextBuffer
        
    def _build_content(self) -> Gtk.Widget:
        """Build history viewer UI with filters and tree view."""
        # Returns Gtk.Box with:
        # 1. Filter controls (H-box with ComboBoxes)
        # 2. History TreeView (scrollable)
        # 3. Detail panel (selected entry info)
        # 4. Action buttons (View in Canvas, Change Rating, Undo)
```

**UI Layout**:
```
┌────────────────────────────────────────────────────────────┐
│  ▶ Enrichment History                            [Refresh] │
├────────────────────────────────────────────────────────────┤
│  Filters:                                                  │
│  Source: [All ▼] Pathway: [All ▼] Rating: [All ▼]        │
│  Date: [Last 7 days ▼]                   [Clear Filters]  │
│                                                            │
│  ┌────────────────────────────────────────────────────┐   │
│  │ Date     │ Source    │ Transition │ Rating  │ Conf │   │
│  ├──────────┼───────────┼────────────┼─────────┼──────┤   │
│  │ 11/16... │ SABIO-RK  │ trans_001  │   👍    │ 88%  │   │
│  │ 11/16... │ BRENDA    │ trans_002  │   👎    │ 75%  │   │
│  │ 11/15... │ Heuristic │ trans_003  │   👍    │ 92%  │   │
│  │ ...      │ ...       │ ...        │   ...   │ ...  │   │
│  └────────────────────────────────────────────────────┘   │
│                                                            │
│  Selected Entry:                                          │
│  ┌────────────────────────────────────────────────────┐   │
│  │ Transition: trans_glycolysis_001                   │   │
│  │ Pathway: Glycolysis                                │   │
│  │ EC: 1.1.1.1 | Organism: E. coli                  │   │
│  │ Parameters: {Km: 0.15 mM, kcat: 125 1/s}         │   │
│  │ Applied: 2025-11-16 18:51:36                      │   │
│  │ User Comment: "Works well for this reaction"      │   │
│  │                                                    │   │
│  │ [View in Canvas] [Change Rating] [⟲ Undo]        │   │
│  └────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────┘
```

**Features**:
- Filter by: source, pathway, date range, rating
- Sort by: date (newest first), confidence, usage count
- TreeView columns: Date, Source, Transition, Rating (emoji), Confidence
- Detail view: Full parameter info + comment
- Actions:
  - **View in Canvas**: Scroll canvas to show transition
  - **Change Rating**: Re-open rating dialog
  - **Undo**: Revert parameter application

**Data Binding**:
```python
def load_history(self, filters=None):
    """Load history from ParameterTracker with filters."""
    history = self.tracker.get_filtered_history(
        source=filters.get('source'),
        pathway_id=filters.get('pathway'),
        date_range=filters.get('date_range'),
        rating=filters.get('rating')
    )
    
    # Populate TreeView
    self.history_store.clear()
    for entry in history:
        self.history_store.append([
            entry['applied_date'],
            entry['source'],
            entry['transition_id'],
            self._rating_to_emoji(entry['user_rating']),
            f"{entry['confidence_score']:.0%}"
        ])
```

---

### 🆕 3. Undo Functionality
**Status**: ⏳ TO BE CREATED

**Implementation Approach**: Add methods to existing modules (no separate module needed)

**Location**: Add to `ParameterTracker` class

**Methods to Add**:
```python
class ParameterTracker:
    # Existing methods...
    
    def undo_application(self, record_id: int) -> bool:
        """Undo a parameter application.
        
        Marks the application as undone (doesn't delete for audit trail).
        Returns previous parameter values for reverting transition.
        
        Args:
            record_id: ID of parameter application to undo
            
        Returns:
            bool: True if undo successful
        """
        # 1. Get the record
        record = self.get_record_by_id(record_id)
        if not record or record['undone']:
            return False
        
        # 2. Get previous parameters (look for earlier application)
        previous = self.get_previous_parameters(
            transition_id=record['transition_id'],
            before_date=record['applied_date']
        )
        
        # 3. Mark as undone
        self.db.execute("""
            UPDATE transition_parameters
            SET undone = true,
                undo_timestamp = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (record_id,))
        
        # 4. Return previous values for UI to revert
        return {
            'success': True,
            'previous_parameters': previous,
            'transition_id': record['transition_id']
        }
    
    def get_filtered_history(self, 
                            source=None,
                            pathway_id=None,
                            transition_id=None,
                            date_range=None,
                            rating=None,
                            include_undone=False) -> List[Dict]:
        """Get enrichment history with filters.
        
        Returns list of parameter applications matching filters.
        """
        query = "SELECT * FROM transition_parameters WHERE 1=1"
        params = []
        
        if source:
            query += " AND source = ?"
            params.append(source)
        
        if pathway_id:
            query += " AND pathway_id = ?"
            params.append(pathway_id)
        
        if transition_id:
            query += " AND transition_id = ?"
            params.append(transition_id)
        
        if not include_undone:
            query += " AND (undone IS NULL OR undone = 0)"
        
        if rating is not None:
            query += " AND user_rating = ?"
            params.append(rating)
        
        if date_range:
            start, end = date_range
            query += " AND applied_date BETWEEN ? AND ?"
            params.extend([start, end])
        
        query += " ORDER BY applied_date DESC"
        
        return self.db.execute_query(query, params)
```

**UI Integration**:
```python
class EnrichmentHistoryCategory:
    
    def on_undo_clicked(self, button):
        """Handle undo button click."""
        selected = self._get_selected_record()
        if not selected:
            return
        
        # Show confirmation
        dialog = Gtk.MessageDialog(
            transient_for=self.get_toplevel(),
            modal=True,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            text="Undo Parameter Application?"
        )
        dialog.format_secondary_text(
            f"This will revert parameters for {selected['transition_id']}."
        )
        
        response = dialog.run()
        dialog.destroy()
        
        if response != Gtk.ResponseType.YES:
            return
        
        # Perform undo
        result = self.tracker.undo_application(selected['id'])
        
        if result['success']:
            # Revert transition in canvas
            self._revert_transition(
                result['transition_id'],
                result['previous_parameters']
            )
            
            # Refresh history view
            self.load_history()
            
            # Show confirmation
            self._show_message("Parameters reverted successfully")
    
    def _revert_transition(self, transition_id, previous_params):
        """Revert transition parameters in canvas."""
        if not self.model_canvas_loader:
            return
        
        # Get current document and model
        doc = self.model_canvas_loader.current_document
        if not doc:
            return
        
        model = doc.model
        transition = model.get_transition_by_id(transition_id)
        
        if not transition:
            return
        
        # Apply previous parameters
        if previous_params:
            for key, value in previous_params.items():
                setattr(transition, key, value)
        else:
            # No previous params = reset to defaults
            transition.reset_parameters()
        
        # Refresh canvas
        doc.model_canvas.queue_draw()
```

---

### 🆕 4. Rating Storage & Confidence Scoring

**Database Schema** (already exists in `transition_parameters`):
```sql
-- Existing columns used:
user_rating INTEGER        -- -1 (poor), 0 (neutral/unsure), 1 (good)
notes TEXT                 -- User comment
usage_count INTEGER        -- Incremented each time params used
confidence_score REAL      -- 0.0-1.0
undone BOOLEAN            -- Whether application was undone
undo_timestamp TIMESTAMP   -- When it was undone
```

**Confidence Scoring Algorithm**:
```python
def calculate_confidence(source: str, 
                        usage_count: int, 
                        user_rating: Optional[int]) -> float:
    """Calculate parameter confidence score.
    
    Factors:
    - Source baseline (SABIO-RK: 0.85, BRENDA: 0.80, Heuristic: 0.70)
    - Usage boost (+1% per use, max +10%)
    - User rating influence (-15% poor, 0% neutral, +10% good)
    
    Returns:
        float: Confidence score 0.0-1.0
    """
    # Base confidence by source
    base_confidence = {
        'SABIO-RK': 0.85,
        'BRENDA': 0.80,
        'Heuristic': 0.70
    }.get(source, 0.60)
    
    # Usage boost (max +10%)
    usage_boost = min(0.10, usage_count * 0.01)
    
    # Rating influence
    rating_factor = {
        -1: -0.15,  # Poor rating
        0: 0.0,     # Neutral/unsure
        1: +0.10,   # Good rating
        None: 0.0   # No rating yet
    }.get(user_rating, 0.0)
    
    # Calculate final confidence
    confidence = base_confidence + usage_boost + rating_factor
    
    # Clamp to [0, 1]
    return max(0.0, min(1.0, confidence))
```

**Auto-Update on Rating**:
```python
class ParameterTracker:
    
    def update_rating(self, record_id: int, rating: int, comment: str = ""):
        """Update user rating and recalculate confidence."""
        # Get current record
        record = self.get_record_by_id(record_id)
        
        # Update rating and comment
        self.db.execute("""
            UPDATE transition_parameters
            SET user_rating = ?,
                notes = ?,
                usage_count = usage_count + 1
            WHERE id = ?
        """, (rating, comment, record_id))
        
        # Recalculate confidence
        new_confidence = calculate_confidence(
            source=record['source'],
            usage_count=record['usage_count'] + 1,
            user_rating=rating
        )
        
        self.db.execute("""
            UPDATE transition_parameters
            SET confidence_score = ?
            WHERE id = ?
        """, (new_confidence, record_id))
```

---

## File Organization (Updated for SHYPN Structure)

```
src/shypn/
├── ui/
│   ├── dialogs/
│   │   ├── __init__.py
│   │   └── parameter_rating_dialog.py        ← ✅ DONE
│   └── panels/
│       └── pathway_operations/
│           ├── __init__.py
│           ├── base_pathway_category.py      ← Existing
│           ├── kegg_category.py              ← Existing
│           ├── sbml_category.py              ← Existing
│           ├── brenda_category.py            ← Existing
│           ├── sabio_rk_category.py          ← Existing
│           ├── heuristic_parameters_category.py ← Existing
│           └── enrichment_history_category.py   ← 🆕 NEW
│
├── crossfetch/
│   ├── cache/
│   │   ├── base_cache_manager.py             ← Existing (Phase 1)
│   │   ├── sabio_rk_cache_manager.py         ← Existing (Phase 1)
│   │   └── brenda_cache_manager.py           ← Existing (Phase 1)
│   └── tracking/
│       └── parameter_tracker.py              ← Extend in Phase 2
│           • Add: update_rating()
│           • Add: get_filtered_history()
│           • Add: undo_application()
│           • Add: get_previous_parameters()
│
├── helpers/
│   ├── sabio_rk_enrichment_controller.py     ← Modify to show rating dialog
│   └── brenda_enrichment_controller.py       ← Modify to show rating dialog
│
tests/
├── test_rating_dialog.py                     ← 🆕 NEW
├── test_enrichment_history_category.py       ← 🆕 NEW
├── test_undo_functionality.py                ← 🆕 NEW
└── test_confidence_scoring.py                ← 🆕 NEW

doc/KB/
├── KB_COMPLETION_PLAN.md                     ← Existing
├── PHASE1_SUMMARY.md                         ← Existing
├── PHASE1_VERIFICATION.md                    ← Existing
├── PHASE2_UI_ARCHITECTURE.md                 ← This document (revised)
├── PHASE2_IMPLEMENTATION_GUIDE.md            ← 🆕 Create next
└── QUICK_REFERENCE.md                        ← Update with new APIs
```

---

## Implementation Order (Revised)

### ✅ Task 0: Rating Dialog (DONE)
- File: `src/shypn/ui/dialogs/parameter_rating_dialog.py`
- Status: ✅ Created and tested
- Integration: Ready for controller wiring

### 🔨 Task 1: Extend ParameterTracker (4 hours)
**Priority**: HIGH (needed by all other tasks)

1. Add `update_rating()` method
2. Add `get_filtered_history()` method  
3. Add `undo_application()` method
4. Add `get_previous_parameters()` helper
5. Add `calculate_confidence()` function
6. Unit tests for new methods

**Files Modified**:
- `src/shypn/crossfetch/tracking/parameter_tracker.py`
- `tests/test_parameter_tracker.py` (extend existing)

### 🔨 Task 2: Integrate Rating Dialog with Controllers (3 hours)
**Priority**: HIGH (user-facing feature)

1. Modify `sabio_rk_enrichment_controller.py`:
   - Import `ParameterRatingDialog`
   - After `apply_parameters()`, show dialog
   - Store rating via `tracker.update_rating()`

2. Modify `brenda_enrichment_controller.py`:
   - Same pattern as SABIO-RK

3. Test integration:
   - Apply parameters
   - Rating dialog appears
   - Skip works
   - Submit stores rating

**Files Modified**:
- `src/shypn/helpers/sabio_rk_enrichment_controller.py`
- `src/shypn/helpers/brenda_enrichment_controller.py`

### 🔨 Task 3: Create Enrichment History Category (10 hours)
**Priority**: MEDIUM (power-user feature)

1. Create `enrichment_history_category.py`:
   - Inherit from `BasePathwayCategory`
   - Build filters UI (ComboBoxes)
   - Build TreeView for history list
   - Build detail panel for selected entry
   - Wire undo button

2. Add to `pathway_operations_panel.py`:
   - Instantiate `EnrichmentHistoryCategory`
   - Pack into categories_box (after Heuristic)
   - Wire signals if needed

3. Test:
   - Category expands/collapses
   - Filters work
   - History loads
   - Selection shows details
   - Undo works

**Files Created**:
- `src/shypn/ui/panels/pathway_operations/enrichment_history_category.py`

**Files Modified**:
- `src/shypn/ui/panels/pathway_operations_panel.py`
- `src/shypn/ui/panels/pathway_operations/__init__.py`

### 🔨 Task 4: Undo Functionality (6 hours)
**Priority**: MEDIUM (integrated with Task 3)

1. Implement undo in `EnrichmentHistoryCategory`:
   - Confirmation dialog
   - Call `tracker.undo_application()`
   - Revert transition in canvas
   - Refresh history view

2. Canvas integration:
   - Get transition from model
   - Apply previous parameters
   - Queue redraw

3. Test:
   - Undo reverts parameters
   - Canvas updates
   - History shows "Undone" status
   - Can't undo twice

### 🔨 Task 5: Testing (6 hours)
**Priority**: HIGH (quality assurance)

1. Create test files:
   - `test_rating_dialog.py` - Dialog UI and behavior
   - `test_enrichment_history_category.py` - History view
   - `test_undo_functionality.py` - Undo workflow
   - `test_confidence_scoring.py` - Algorithm correctness

2. Integration tests:
   - Full workflow: enrich → rate → view history → undo
   - Wayland safety checks
   - Multiple sources (SABIO-RK, BRENDA, Heuristic)

3. Performance tests:
   - History view with 1000+ entries
   - Filter response time
   - TreeView scrolling performance

### 🔨 Task 6: Documentation (3 hours)
**Priority**: MEDIUM (user adoption)

1. Create `PHASE2_IMPLEMENTATION_GUIDE.md`:
   - Step-by-step implementation instructions
   - Code examples for each component
   - Testing procedures

2. Update `QUICK_REFERENCE.md`:
   - New ParameterTracker methods
   - EnrichmentHistoryCategory usage
   - Rating dialog API

3. Create user documentation:
   - How to rate parameters
   - How to view history
   - How to undo applications

---

## Total Estimated Time: 32 hours

| Task | Priority | Hours | Status |
|------|----------|-------|--------|
| 0. Rating Dialog | HIGH | 4 | ✅ DONE |
| 1. Extend ParameterTracker | HIGH | 4 | ⏳ TODO |
| 2. Integrate Rating Dialog | HIGH | 3 | ⏳ TODO |
| 3. Enrichment History Category | MEDIUM | 10 | ⏳ TODO |
| 4. Undo Functionality | MEDIUM | 6 | ⏳ TODO |
| 5. Testing | HIGH | 6 | ⏳ TODO |
| 6. Documentation | MEDIUM | 3 | ⏳ TODO |
| **TOTAL** | | **32** | |

---

## Key Design Decisions (Updated)

### 1. **History Panel Location**: Pathway Operations Panel ✅
- Keeps all enrichment operations in one place
- Follows CategoryFrame pattern (like KEGG, SBML, BRENDA)
- No new Master Palette button needed
- Natural workflow progression

### 2. **Rating Dialog Timing**: Immediately After Application ✅
- Optional (can skip)
- Non-blocking workflow
- Modal prevents confusion about what's being rated
- Wayland-safe (proper parent handling)

### 3. **Undo Strategy**: Mark as Undone (Don't Delete) ✅
- Preserves full audit trail
- Can analyze what users undo (learning signal)
- Supports potential redo in future
- Previous parameters stored for reversion

### 4. **Confidence Scoring**: Multi-Factor Algorithm ✅
- Base score by source quality
- Usage count boost (popularity signal)
- User rating influence (quality signal)
- Clamped to [0, 1] range

### 5. **CategoryFrame Architecture**: Consistent with SHYPN ✅
- All panels use CategoryFrame (collapsible sections)
- No tabs needed
- Vertical scrolling for many categories
- Wayland-safe (no window reparenting)

---

## Next Steps

1. ✅ Review this architecture with team/user
2. ⏳ Create `PHASE2_IMPLEMENTATION_GUIDE.md` with code examples
3. ⏳ Implement Task 1 (Extend ParameterTracker)
4. ⏳ Implement Task 2 (Integrate Rating Dialog)
5. ⏳ Implement Task 3 (History Category)
6. ⏳ Testing and refinement

---

**Date**: 2025-11-16  
**Status**: Architecture revised after SHYPN reconnaissance  
**Ready For**: Implementation

│  │                                                                         │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │  Filters & Controls                                              │  │  │
│  │  │  Source: [All ▼] | Pathway: [All ▼] | Transition: [All ▼]      │  │  │
│  │  │  Date: [Last 7 days ▼] | Rating: [All ▼]                        │  │  │
│  │  │  [ Clear Filters ]                        [ Refresh ]            │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                         │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │  History List (Scrollable TreeView)                             │  │  │
│  │  │  ┌─────┬────────┬───────────┬───────────┬────────┬──────────┐  │  │  │
│  │  │  │Date │ Source │Transition │Parameters │Rating  │Confidence│  │  │  │
│  │  │  ├─────┼────────┼───────────┼───────────┼────────┼──────────┤  │  │  │
│  │  │  │11/16│SABIO-RK│trans_001  │Km:0.1 mM  │👍      │ 88%      │  │  │  │
│  │  │  │11/16│BRENDA  │trans_002  │Vmax:226   │👎      │ 75%      │  │  │  │
│  │  │  │11/15│Heuristic│trans_003 │Km:0.05 mM │👍      │ 92%      │  │  │  │
│  │  │  │11/15│SABIO-RK│trans_001  │kcat:125/s │🤷      │ 80%      │  │  │  │
│  │  │  │...  │...     │...        │...        │...     │...       │  │  │  │
│  │  │  └─────┴────────┴───────────┴───────────┴────────┴──────────┘  │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                         │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │  Detail View (Selected Entry)                                   │  │  │
│  │  │  Entry ID: #425                                                 │  │  │
│  │  │  Transition: trans_glycolysis_001                               │  │  │
│  │  │  Pathway: Glycolysis                                            │  │  │
│  │  │  EC: 1.1.1.1 | Organism: E. coli                               │  │  │
│  │  │  Parameters: {Km: 0.15 mM, kcat: 125 1/s}                      │  │  │
│  │  │  Applied: 2025-11-16 18:51:36                                  │  │  │
│  │  │  User Comment: "Works well for this reaction"                  │  │  │
│  │  │                                                                 │  │  │
│  │  │  [ View in Canvas ] [ Change Rating ] [ ⟲ Undo Application ]  │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                  │                                           │
└──────────────────────────────────┼───────────────────────────────────────────┘
                                   │ User clicks "Undo Application"
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    🆕 PHASE 2: UNDO FUNCTIONALITY                            │
│                                                                               │
│  1. Retrieve previous parameter values from history                          │
│  2. Revert transition to previous state                                      │
│  3. Mark application as "undone" in database                                 │
│  4. Update canvas visualization                                              │
│  5. Optionally show confirmation dialog                                      │
│                                                                               │
└─────────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Knowledge Base Layer                                 │
│                                                                               │
│  ┌────────────────────┐  ┌──────────────────┐  ┌──────────────────────┐    │
│  │  Cache Managers    │  │ Parameter Tracker│  │ HeuristicDatabase    │    │
│  │  • SABIO-RK Cache  │  │ • Track apps     │  │ • SQLite storage     │    │
│  │  • BRENDA Cache    │  │ • Get history    │  │ • Schema management  │    │
│  │  • Query with cache│  │ • Store ratings  │  │ • Connection pool    │    │
│  └────────────────────┘  └──────────────────┘  └──────────────────────┘    │
│                                  │                                            │
│                                  ▼                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  Database: ~/.shypn/heuristic_parameters.db                         │    │
│  │                                                                       │    │
│  │  Tables:                                                              │    │
│  │  • transition_parameters (provenance + ratings)                      │    │
│  │  • sabio_rk_cache (cached SABIO-RK results)                          │    │
│  │  • brenda_raw_data (BRENDA measurements)                             │    │
│  │  • brenda_statistics (BRENDA aggregates)                             │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Component Integration Flow

```
User Action                   Component                     Database Operation
───────────                   ─────────                     ──────────────────

1. ENRICHMENT WORKFLOW
   ↓
Apply Parameters    →    Controller.apply_parameters()
                         Cache check via CacheManager
                         ↓
                         ParameterTracker.track_application()
                         ↓                                →  INSERT INTO 
                         Show ParameterRatingDialog            transition_parameters
                         ↓
User rates params   →    Dialog.get_rating()
                         ↓
                         ParameterTracker.update_rating()
                         ↓                                →  UPDATE transition_parameters
                         Close dialog                         SET user_rating = ?


2. HISTORY VIEWING WORKFLOW
   ↓
Open History Panel  →    EnrichmentHistoryPanel.load()
                         ↓
                         ParameterTracker.get_pathway_history()
                         or .get_transition_history()
                         ↓                                →  SELECT * FROM
                         Display in TreeView                  transition_parameters
                         ↓                                    WHERE ...
Apply filters       →    Panel.refresh_with_filters()
                         ↓
                         Tracker query with WHERE clauses
                         ↓                                →  SELECT with filters
                         Update TreeView


3. UNDO WORKFLOW
   ↓
Select history      →    Panel.on_row_selected()
entry                    Display detail view
   ↓
Click Undo button   →    Panel.on_undo_clicked()
                         Show confirmation dialog
                         ↓
                         UndoManager.undo_application()
                         • Get previous parameter values
                         • Revert transition state
                         ↓                                →  UPDATE transition_parameters
                         Update canvas                        SET undone = true
                         Refresh history panel                SET undo_timestamp = NOW()
```

## UI Layout Integration

```
┌─────────────────────────────────────────────────────────────────────────┐
│  SHYPN Main Window                                          [_][□][X]   │
├─────────────────────────────────────────────────────────────────────────┤
│  File  Edit  View  Model  Analyses  Help                                │
├──────────┬──────────────────────────────────────────────────┬──────────┤
│          │                                                   │          │
│  Left    │           Model Canvas                           │  Right   │
│  Panel   │           (Petri Net Diagram)                    │  Panel   │
│          │                                                   │          │
│  Files   │     ┌───┐         ┌───┐                         │ ┌──────┐ │
│  ├─proj1 │  ●──┤ T1├──●──────┤ T2├──●                      │ │Tabs: │ │
│  ├─proj2 │     └───┘         └───┘                         │ │      │ │
│  └─proj3 │                                                  │ │Analy │ │
│          │                                                   │ │ses   │ │
│          │                                                   │ │      │ │
│          │                                                   │ │🆕    │ │
│          │                                                   │ │Hist- │ │
│          │                                                   │ │ory   │ │
│          │                                                   │ │      │ │
│          │                                                   │ └──────┘ │
│          │                                                   │          │
└──────────┴──────────────────────────────────────────────────┴──────────┘

When "History" tab selected:
┌──────────────────────────────────────────────────────────────┐
│  Right Panel > History Tab                                    │
│                                                                │
│  Filters: [Source▼] [Pathway▼] [Date▼] [Rating▼] [Refresh]  │
│                                                                │
│  ┌────────────────────────────────────────────────────────┐   │
│  │ Date     │ Source    │ Transition │ Rating │ Conf      │   │
│  ├──────────┼───────────┼────────────┼────────┼───────────┤   │
│  │ 11/16    │ SABIO-RK  │ trans_001  │ 👍     │ 88%       │   │
│  │ 11/16    │ BRENDA    │ trans_002  │ 👎     │ 75%       │   │
│  │ ...      │ ...       │ ...        │ ...    │ ...       │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                                │
│  Selected Entry Details:                                      │
│  ┌────────────────────────────────────────────────────────┐   │
│  │ Transition: trans_001                                  │   │
│  │ Parameters: {Km: 0.1 mM, Vmax: 226 mM/s}             │   │
│  │ Comment: "Works well"                                  │   │
│  │                                                        │   │
│  │ [View] [Change Rating] [⟲ Undo]                      │   │
│  └────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
```

## Data Flow Diagram

```
┌──────────────────┐
│   User Rates     │
│   Parameter      │
│   Application    │
└────────┬─────────┘
         │
         ▼
┌────────────────────────────────┐
│  ParameterRatingDialog         │
│  • Displays parameter info     │
│  • Collects rating (-1, 0, 1)  │
│  • Collects optional comment   │
└────────┬───────────────────────┘
         │ User clicks Submit
         ▼
┌────────────────────────────────┐
│  ParameterTracker              │
│  .update_rating()              │
│  • Store rating in DB          │
│  • Update usage_count          │
│  • Recalculate confidence      │
└────────┬───────────────────────┘
         │
         ▼
┌────────────────────────────────┐
│  Database Update               │
│  UPDATE transition_parameters  │
│  SET user_rating = ?,          │
│      notes = ?,                │
│      usage_count = usage_count│
│      + 1                       │
│  WHERE parameter_id = ?        │
└────────┬───────────────────────┘
         │
         ▼
┌────────────────────────────────┐
│  Confidence Scoring            │
│  Calculate new confidence:     │
│  • Base confidence (source)    │
│  • Usage count weight          │
│  • User rating influence       │
│  • Time decay factor           │
└────────┬───────────────────────┘
         │
         ▼
┌────────────────────────────────┐
│  UI Updates                    │
│  • Refresh history panel       │
│  • Update canvas if visible    │
│  • Show confirmation toast     │
└────────────────────────────────┘
```

## Key Design Decisions

### 1. **Rating Dialog Timing**
- **Immediately after parameter application** (optional, can skip)
- Non-blocking: User can skip and continue working
- Modal dialog prevents confusion about what's being rated

### 2. **History Panel Location**
- **Right Panel as new tab** (alongside Analyses)
- Always accessible without blocking main workflow
- Scrollable list with filters for large datasets

### 3. **Undo Mechanism**
- **Track previous state** before each application
- Undo reverts to previous values (not delete)
- Mark as "undone" in database for audit trail
- Preserve history for learning

### 4. **Data Persistence**
- All ratings stored in `transition_parameters.user_rating`
- Comments in `transition_parameters.notes`
- Undo state in `transition_parameters.undone` (boolean)
- Full audit trail maintained

### 5. **Wayland Safety**
- Rating dialog has proper parent window
- History panel is standard GTK widget (no special window)
- No popup windows that could cause Error 71
- All dialogs use modal + transient_for pattern

### 6. **Confidence Scoring Algorithm**
```python
base_confidence = {
    'SABIO-RK': 0.85,
    'BRENDA': 0.80,
    'Heuristic': 0.70
}

usage_boost = min(0.1, usage_count * 0.01)  # +1% per use, max +10%
rating_factor = {-1: -0.15, 0: 0.0, 1: +0.10}

final_confidence = (
    base_confidence[source] 
    + usage_boost 
    + rating_factor[user_rating]
)

final_confidence = max(0.0, min(1.0, final_confidence))  # Clamp [0,1]
```

## File Organization

```
src/shypn/ui/dialogs/
├── __init__.py
└── parameter_rating_dialog.py        ← 🆕 Phase 2

src/shypn/ui/panels/
└── enrichment_history_panel.py       ← 🆕 Phase 2

src/shypn/helpers/
├── enrichment_history_panel_loader.py ← 🆕 Phase 2
└── undo_manager.py                    ← 🆕 Phase 2

src/shypn/crossfetch/tracking/
└── parameter_tracker.py               ← Extended in Phase 2
    • add update_rating()
    • add get_filtered_history()
    • add mark_undone()

tests/
├── test_rating_dialog.py              ← 🆕 Phase 2
├── test_history_panel.py              ← 🆕 Phase 2
└── test_undo_manager.py               ← 🆕 Phase 2

doc/KB/
└── PHASE2_UI_ARCHITECTURE.md         ← This document
```

## Implementation Order

1. ✅ **Rating Dialog** (6 hours)
   - parameter_rating_dialog.py
   - Integration with controllers
   - Test dialog standalone

2. **History Panel** (8 hours)
   - enrichment_history_panel.py
   - Panel loader
   - Integration with right panel
   - Filters and search

3. **Undo Functionality** (6 hours)
   - undo_manager.py
   - Integration with history panel
   - Canvas refresh after undo

4. **Confidence Scoring** (4 hours)
   - Algorithm in parameter_tracker
   - Update on rating
   - Display in UI

5. **Testing** (6 hours)
   - Unit tests for all components
   - Integration tests
   - Wayland safety verification

**Total: 30 hours estimated**
