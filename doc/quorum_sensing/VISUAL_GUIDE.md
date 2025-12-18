# Signal Place Visualization Guide

## Overview

Signal places (Ψ) in the 13-tuple Bio-PN formalism are rendered as **hexagons** instead of circles to distinguish them from regular places. This visual guide explains the rendering system.

---

## Visual Comparison

### Regular Place (Circle)
```
          ┌─────────────────┐
          │                 │
          │    ●●●●●●●      │  ← Black circle
          │   ●       ●     │
          │  ●    50   ●    │  ← Tokens displayed
          │   ●       ●     │
          │    ●●●●●●●      │
          │                 │
          │     AHL_int     │  ← Label
          └─────────────────┘
          
Connected by arcs (•t or t•)
Color: Black (0.0, 0.0, 0.0)
Shape: Circle (360°)
```

### Signal Place (Hexagon)
```
          ┌─────────────────┐
          │                 │
          │      ╱▔▔▔╲      │  ← Blue hexagon
          │     ╱     ╲     │
          │    │   50  │    │  ← Tokens displayed
          │     ╲     ╱     │
          │      ╲___╱      │
          │                 │
          │     AHL_ext     │  ← Label
          └─────────────────┘
          
Referenced in rate formulas (Ψ)
Color: Blue (0.0, 0.4, 0.8)
Shape: Hexagon (6 vertices)
Orientation: Flat top/bottom
```

---

## Technical Specifications

### Hexagon Geometry

**Vertex Calculation:**
```python
for i in range(6):
    angle = π/6 + i * π/3  # 30°, 90°, 150°, 210°, 270°, 330°
    vertex_x = center_x + radius * cos(angle)
    vertex_y = center_y + radius * sin(angle)
```

**Vertex Positions (relative to center):**
```
         V0 (30°)
          /\
         /  \
    V5 /    \ V1
      |      |
    V4 \    / V2
         \  /
          \/
         V3 (210°)

Flat edges: top (V5-V0), bottom (V3-V4)
```

### Color Scheme

| Element | Regular Place | Signal Place |
|---------|---------------|--------------|
| Border | Black (0, 0, 0) | Blue (0, 0.4, 0.8) |
| Fill | None (hollow) | None (hollow) |
| Glow | Transparent border color | Transparent blue (0, 0.4, 0.8, 0.3) |
| Line width | 3.0px | 3.0px |

### Hit Testing

**Circle:**
```python
distance = sqrt((x - center_x)² + (y - center_y)²)
inside = distance <= radius
```

**Hexagon (approximation):**
```python
# Use inscribed circle for conservative hit testing
inscribed_radius = radius * 0.866  # ≈ √3/2
distance = sqrt((x - center_x)² + (y - center_y)²)
inside = distance <= inscribed_radius
```

---

## Usage Examples

### Example 1: Bacterial Quorum Sensing

```python
# Model structure
Places:
  P1: AHL_internal    (circle)   ← Connected by arcs
  P2: AHL_external    (hexagon)  ← Signal place (Ψ)
  P3: LuxR_AHL        (circle)   ← Connected by arcs

Transition T1:
  Rate: "k * LuxR_AHL / (1 + AHL_external)"
  Signal places: {P2}  ← P2 referenced but not connected
  
Result:
  P2 renders as BLUE HEXAGON
  P1, P3 render as BLACK CIRCLES
```

### Example 2: Mammalian Paracrine Signaling

```python
# Model structure
Places:
  P1: IL2_intracellular  (circle)   ← Connected by arcs
  P2: IL2_extracellular  (hexagon)  ← Signal place (Ψ)
  P3: IL2R_bound        (circle)   ← Connected by arcs

Transition T1:
  Rate: "k * IL2R_bound / (1 + IL2_extracellular)"
  Signal places: {P2}  ← P2 referenced but not connected
  
Result:
  P2 renders as BLUE HEXAGON
  P1, P3 render as BLACK CIRCLES
```

---

## Code Implementation

### Marking Places as Signal Places

**Automatic Detection:**
```python
from shypn.analysis.quorum_sensing import mark_signal_places_in_model

# After loading model
signal_places = mark_signal_places_in_model(model)
# Returns: {'P2', 'P5', 'P8'}  ← Place IDs marked

# Places are now marked
model.places['P2'].is_signal_place == True  # Renders as hexagon
model.places['P1'].is_signal_place == False # Renders as circle
```

**Manual Marking:**
```python
# Manually mark a place as signal place
place = model.places['P2']
place.is_signal_place = True  # Will render as hexagon
```

### Rendering Logic

**Place.render() method:**
```python
def render(self, cr, zoom=1.0):
    # Choose color based on type
    display_color = (0.0, 0.4, 0.8) if self.is_signal_place else self.border_color
    
    # Draw shape based on type
    if self.is_signal_place:
        self._draw_hexagon_path(cr, self.x, self.y, self.radius)
    else:
        cr.arc(self.x, self.y, self.radius, 0, 2 * math.pi)
    
    # Stroke the path
    cr.set_source_rgb(*display_color)
    cr.set_line_width(self.border_width / max(zoom, 1e-6))
    cr.stroke()
    
    # Draw tokens and label (same for both types)
    if self.tokens > 0:
        self._render_tokens(cr, self.x, self.y, self.radius, zoom)
    if self.label:
        self._render_label(cr, self.x, self.y, self.radius, zoom)
```

---

## Biological Interpretation

### Signal Place (Hexagon) Indicates:

1. **Environment Sensing**
   - Place represents external signal not directly produced/consumed
   - Example: Ambient temperature, pH, oxygen level

2. **Quorum Sensing**
   - Place represents population-level signal (e.g., AHL)
   - Transitions sense cell density via this signal

3. **Paracrine Signaling**
   - Place represents signal from other cells (e.g., IL-2)
   - Enables cell-to-cell communication modeling

4. **Non-Local Dependency**
   - Transition rate depends on place without arc connection
   - Mathematical: Ψ(t) = Referenced(Φ) \ (•t ∪ t• ∪ Σ(t))

### Regular Place (Circle) Indicates:

- Direct substrate consumption (•t)
- Direct product generation (t•)
- Regulatory control (Σ(t) via test/inhibitor arcs)
- Local interaction with transition

---

## Troubleshooting

### Q: My signal place renders as a circle, not hexagon
**A:** Check that `is_signal_place` is set:
```python
place.is_signal_place  # Should be True
```

If False, run:
```python
from shypn.analysis.quorum_sensing import mark_signal_places_in_model
mark_signal_places_in_model(model)
```

### Q: Hexagon doesn't appear blue
**A:** Check rendering context:
```python
# Debug rendering
place = model.places['P2']
print(f"is_signal_place: {place.is_signal_place}")  # Should be True
print(f"border_color: {place.border_color}")        # Ignored if signal place
```

Signal places always use blue (0.0, 0.4, 0.8) regardless of border_color.

### Q: Hit testing doesn't work for hexagons
**A:** Hexagons use inscribed circle approximation:
```python
# Effective click radius
effective_radius = place.radius * 0.866  # ≈ 86.6% of circumradius
```

Click near the center for better hit detection.

### Q: How do I save/load signal place annotations?
**A:** Automatic via serialization:
```python
# Save
data = place.to_dict()
# data['is_signal_place'] == True

# Load
place = Place.from_dict(data)
# place.is_signal_place restored automatically
```

---

## Visual Examples from Literature

### Bacterial QS (*V. fischeri*)
```
[LuxI] ──synthesis──> (AHL_int) ──export──> ⬢AHL_ext⬢
                                                │
                                                │ senses
                                                ↓
                     [LuxR] + (AHL_int) ──> (LuxR-AHL)
                                                │
                                                │ activates
                                                ↓
                                           [luxAB operon]
                                                │
                                                ↓
                                         (Luciferase)
                                                │
                                                ↓
                                            Bioluminescence

Legend:
  [Transition] = Rectangle
  (Place)      = Circle
  ⬢Place⬢      = Hexagon (signal place)
  ─→           = Arc (normal)
  ··→          = Sensing (no arc, rate formula dependency)
```

### Mammalian IL-2 System
```
[T cell activation] ──secretion──> (IL2_int) ──> ⬢IL2_ext⬢
                                                      │
                                                      │ senses
                                                      ↓
              [IL2R binding] + (IL2R_free) ──> (IL2R_bound)
                                                      │
                                                      │
                                                      ↓
                            [STAT5 activation] ──> (STAT5_P)
                                                      │
                                                      ↓
                                              [T cell proliferation]
```

---

## References

1. **Place Class:** `src/shypn/netobjs/place.py`
2. **Detection Algorithm:** `src/shypn/analysis/quorum_sensing.py`
3. **Tests:** `tests/test_quorum_sensing_ui.py`
4. **Theory:** `doc/quorum_sensing/THEORY.md`

---

**Last Updated:** December 18, 2025  
**Feature Status:** Production-ready (Phase 3 complete)
