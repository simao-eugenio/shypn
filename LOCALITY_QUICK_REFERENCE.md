# Locality-Based Analysis - Quick Reference

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         User Interactions                            │
└─────────────────────────────────────────────────────────────────────┘
           │                                    │
           │ Double-click                       │ Right-click
           │ Transition                         │ Transition
           ▼                                    ▼
┌──────────────────────────┐         ┌──────────────────────────┐
│ Transition Properties    │         │  Context Menu            │
│ Dialog                   │         │  Handler                 │
│                          │         │                          │
│  ┌──────────────────┐   │         │  Add to Analysis ▶       │
│  │ Diagnostics Tab  │   │         │  ├─ Transition Only      │
│  │                  │   │         │  └─ With Locality        │
│  │  Locality Info   │   │         │     (N places)           │
│  │  Widget          │   │         └──────────────────────────┘
│  │                  │   │                    │
│  │  [Shows P-T-P]   │   │                    │
│  └──────────────────┘   │                    │
└──────────────────────────┘                    │
           │                                    │
           │ Uses                               │ Calls
           ▼                                    ▼
┌──────────────────────────────────────────────────────────────────────┐
│              src/shypn/diagnostic/ (OOP Business Logic)              │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌─────────────────────┐    ┌─────────────────────┐                │
│  │ LocalityDetector    │───▶│ Locality            │                │
│  │                     │    │ (dataclass)         │                │
│  │ • get_locality_for_ │    │                     │                │
│  │   transition()      │    │ • transition        │                │
│  │ • get_all_          │    │ • input_places      │                │
│  │   localities()      │    │ • output_places     │                │
│  │ • find_shared_      │    │ • is_valid          │                │
│  │   places()          │    │ • place_count       │                │
│  └─────────────────────┘    └─────────────────────┘                │
│           │                           │                              │
│           │                           │ Analyzes                     │
│           │ Detects                   ▼                              │
│           │                  ┌─────────────────────┐                │
│           │                  │ LocalityAnalyzer    │                │
│           │                  │                     │                │
│           │                  │ • analyze_locality()│                │
│           │                  │ • get_token_flow_   │                │
│           │                  │   description()     │                │
│           │                  │ • _count_tokens()   │                │
│           │                  │ • _check_firing()   │                │
│           │                  └─────────────────────┘                │
│           │                           │                              │
│           │ Used by                   │ Used by                      │
│           ▼                           ▼                              │
│  ┌──────────────────────────────────────────────┐                   │
│  │ LocalityInfoWidget (GTK Component)           │                   │
│  │                                              │                   │
│  │ • set_transition()                           │                   │
│  │ • _update_display()                          │                   │
│  │ • _show_valid_locality()                     │                   │
│  │ • _show_invalid_locality()                   │                   │
│  └──────────────────────────────────────────────┘                   │
│                                                                       │
└──────────────────────────────────────────────────────────────────────┘
           │                                    │
           │ Used by                            │ Used by
           ▼                                    ▼
┌──────────────────────────┐         ┌──────────────────────────┐
│ transition_prop_dialog   │         │ context_menu_handler     │
│ _loader (Wiring Only)    │         │ (Wiring Only)            │
│                          │         │                          │
│ • Instantiates Widget    │         │ • Detects localities     │
│ • Adds to container      │         │ • Creates submenu        │
│ • Passes model           │         │ • Calls panel methods    │
└──────────────────────────┘         └──────────────────────────┘
                                               │
                                               │ Calls
                                               ▼
                                     ┌──────────────────────────┐
                                     │ TransitionRatePanel      │
                                     │ (Plotting Logic)         │
                                     │                          │
                                     │ • add_locality_places()  │
                                     │ • update_plot()          │
                                     │ • _plot_locality_places()│
                                     └──────────────────────────┘
                                               │
                                               │ Renders to
                                               ▼
                                     ┌──────────────────────────┐
                                     │  Matplotlib Canvas       │
                                     │  (Right Panel)           │
                                     │                          │
                                     │  T1 [CON] ────────       │
                                     │  ↓ P1 (in) - - - -       │
                                     │  ↑ P2 (out) · · · ·      │
                                     └──────────────────────────┘
```

## Data Flow

### Flow 1: View Locality in Dialog

```
User double-clicks Transition
    ↓
model_canvas_loader._on_object_properties()
    ↓
create_transition_prop_dialog(obj, model=manager)
    ↓
TransitionPropDialogLoader.__init__(model=model)
    ↓
_setup_locality_widget()
    ↓
LocalityInfoWidget(model)
    ├─ LocalityDetector.get_locality_for_transition()
    │   └─ Returns: Locality(transition, input_places, output_places)
    │
    └─ LocalityAnalyzer.analyze_locality()
        └─ Returns: {token_count, balance, can_fire, ...}
    ↓
Widget displays in locality_info_container
```

### Flow 2: Add Transition with Locality

```
User right-clicks Transition
    ↓
model_canvas_loader._show_object_context_menu()
    ↓
context_menu_handler.add_analysis_menu_items(menu, obj)
    ↓
LocalityDetector.get_locality_for_transition(obj)
    ├─ If valid: Create submenu
    │   ├─ "Transition Only"
    │   └─ "With Locality (N places)"
    │
    └─ If invalid: Simple menu item
    ↓
User selects "With Locality"
    ↓
context_menu_handler._add_transition_with_locality()
    ↓
transition_panel.add_object(transition)
transition_panel.add_locality_places(transition, locality)
    ↓
TransitionRatePanel stores locality places
TransitionRatePanel.needs_update = True
    ↓
Periodic update triggers
    ↓
TransitionRatePanel.update_plot()
    ├─ Plot transition (solid line)
    └─ _plot_locality_places()
        ├─ Plot input places (dashed, lighter)
        └─ Plot output places (dotted, darker)
```

## Key Design Patterns

### 1. **Separation of Concerns**
- **Detection:** LocalityDetector (pure logic)
- **Analysis:** LocalityAnalyzer (pure logic)
- **Visualization:** LocalityInfoWidget (GTK component)
- **Wiring:** Loaders (instantiation only)

### 2. **Dependency Injection**
- Model passed to detector, analyzer, widget
- No global state
- Easy to test

### 3. **Strategy Pattern**
- Context menu adapts based on locality validity
- Plot rendering adapts based on data availability

### 4. **Observer Pattern**
- Panel.needs_update flag
- Periodic update timer
- Event-driven rendering

## Color Scheme Logic

```python
# TransitionRatePanel._plot_locality_places()

Base Color (Transition): '#e74c3c' (Red)
    │
    ├─ Input Places: Lighter (+0.2 RGB)
    │   └─ '#ff7c6c' (Light Red)
    │   └─ Style: Dashed (--), Alpha 0.7
    │
    └─ Output Places: Darker (-0.2 RGB)
        └─ '#c73c2c' (Dark Red)
        └─ Style: Dotted (··), Alpha 0.7

Result: Visual cohesion + clear distinction
```

## Testing Scenarios

### Scenario A: Simple Locality (P → T → P)
```
Model:
  P1 (5 tokens) ──[1]──> T1 ──[1]──> P2 (0 tokens)

Dialog Diagnostics Tab:
  ┌────────────────────────────────┐
  │ Locality: 1 inputs → T1 → 1   │
  │ outputs                        │
  │                                │
  │ Input Flows:                   │
  │   P1 (5 tokens) --[1]--> T1   │
  │                                │
  │ Output Flows:                  │
  │   T1 --[1]--> P2 (0 tokens)   │
  │                                │
  │ Analysis:                      │
  │   Token Balance: +5            │
  │   Can Fire: ✓ Yes              │
  └────────────────────────────────┘

Context Menu:
  Add to Transition Analysis ▶
    ├─ Transition Only
    └─ With Locality (2 places)

Plot (if "With Locality" selected):
  T1 [CON] ────────────  (solid)
  ↓ P1 (input) - - - -   (dashed, lighter)
  ↑ P2 (output) · · · ·  (dotted, darker)
```

### Scenario B: Complex Locality (Multiple P-T-P)
```
Model:
  P1, P2 ──> T1 ──> P3, P4

Dialog Diagnostics Tab:
  Locality: 2 inputs → T1 → 2 outputs

Context Menu:
  Add to Transition Analysis ▶
    ├─ Transition Only
    └─ With Locality (4 places)

Plot (if "With Locality" selected):
  T1 [CON] ────────────
  ↓ P1 (input) - - - -
  ↓ P2 (input) - - - -
  ↑ P3 (output) · · · ·
  ↑ P4 (output) · · · ·
```

### Scenario C: Invalid Locality (No Outputs)
```
Model:
  P1 ──> T1 (isolated, no outputs)

Dialog Diagnostics Tab:
  ⚠ Invalid Locality
  
  Current state:
    ✓ 1 input place (P1)
    ✗ 0 output places

Context Menu:
  Add to Transition Analysis  (simple item, no submenu)
```

## Benefits Summary

### For Users
✅ **Understand structure** - See transition neighborhoods at a glance  
✅ **Analyze patterns** - Token flow visualization  
✅ **Quick plotting** - One-click add transition + places  
✅ **Clear visualization** - Distinct line styles for inputs/outputs  

### For Developers
✅ **Clean architecture** - OOP, no spaghetti code  
✅ **Testable** - Each class independently testable  
✅ **Reusable** - LocalityDetector usable anywhere  
✅ **Extensible** - Easy to add more diagnostic features  

---

**Implementation Status:** ✅ COMPLETE  
**Code Quality:** ✅ High (documented, typed, tested)  
**Ready for:** User testing and feedback
