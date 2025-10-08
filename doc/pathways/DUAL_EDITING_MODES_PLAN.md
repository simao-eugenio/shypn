# Dual Editing Modes - Implementation Plan

**Date**: October 7, 2025  
**Context**: Support two editing modes with visual guidance for pathway hierarchy

---

## 🎯 Overview: Two Editing Contexts

### 1. **Interactive Creation Mode** (Existing)
- **Purpose**: Build Petri nets from scratch
- **Operations**: Add places/transitions, connect arcs, set properties
- **Visual**: Standard editing (selection, resize, transform)
- **Current Status**: ✅ Fully implemented

### 2. **Pathway Editing Mode** (New)
- **Purpose**: Refine imported KEGG pathways
- **Operations**: Layout adjustment, abstraction, annotation
- **Visual**: Hierarchy coloring, overlay effects, hide/show levels
- **Current Status**: ❌ Not implemented

---

## 🎨 Part 1: Visual Guidance System for Pathway Hierarchy

### 1.1 Color Coding by Hierarchy Level

**Concept**: Use color intensity to show importance

```
Level 0 (Main Backbone):
  Places: Dark blue (#2563EB) - High saturation
  Transitions: Dark green (#059669) - High saturation
  Arcs: Thick (3px), solid, dark gray (#1F2937)

Level 1 (Primary Branches):
  Places: Medium blue (#60A5FA) - Medium saturation
  Transitions: Medium green (#34D399) - Medium saturation
  Arcs: Medium (2px), solid, medium gray (#6B7280)

Level 2 (Secondary/Leafs):
  Places: Light blue (#DBEAFE) - Low saturation
  Transitions: Light green (#D1FAE5) - Low saturation
  Arcs: Thin (1px), dashed, light gray (#D1D5DB)
```

**Implementation**:
```python
# Color scheme definition
HIERARCHY_COLORS = {
    0: {  # Main backbone
        'place_fill': '#2563EB',
        'place_stroke': '#1E40AF',
        'transition_fill': '#059669',
        'transition_stroke': '#047857',
        'arc_color': '#1F2937',
        'arc_width': 3.0
    },
    1: {  # Primary branches
        'place_fill': '#60A5FA',
        'place_stroke': '#3B82F6',
        'transition_fill': '#34D399',
        'transition_stroke': '#10B981',
        'arc_color': '#6B7280',
        'arc_width': 2.0
    },
    2: {  # Secondary/leafs
        'place_fill': '#DBEAFE',
        'place_stroke': '#93C5FD',
        'transition_fill': '#D1FAE5',
        'transition_stroke': '#6EE7B7',
        'arc_color': '#D1D5DB',
        'arc_width': 1.0
    }
}
```

---

### 1.2 Visual Effects for Editing Guidance

#### **Highlight Mode** (Keyboard: `H`)
- **Effect**: Dim all except selected hierarchy level
- **Use case**: "Show me only the main backbone"

```python
def apply_highlight_mode(manager, target_level):
    """
    Highlight specific hierarchy level, dim others.
    """
    for place in manager.places:
        level = place.metadata.get('hierarchy_level', 0)
        if level == target_level:
            place.opacity = 1.0
            place.highlight = True
        else:
            place.opacity = 0.3
            place.highlight = False
    
    for transition in manager.transitions:
        level = transition.metadata.get('hierarchy_level', 0)
        if level == target_level:
            transition.opacity = 1.0
            transition.highlight = True
        else:
            transition.opacity = 0.3
            transition.highlight = False
    
    manager.mark_dirty()
```

#### **Ghost Mode** (Keyboard: `G`)
- **Effect**: Show hidden elements as semi-transparent ghosts
- **Use case**: "I hid secondary pathways, but want to see where they were"

```python
def apply_ghost_mode(manager, show_hidden=True):
    """
    Show hidden elements as ghosts (50% opacity, dotted outline).
    """
    for obj in manager.places + manager.transitions:
        if obj.metadata.get('hidden', False):
            if show_hidden:
                obj.opacity = 0.5
                obj.stroke_dasharray = [5, 5]  # Dotted
                obj.ghost_mode = True
            else:
                obj.opacity = 0.0  # Fully hidden
```

#### **Heatmap Mode** (Keyboard: `M`)
- **Effect**: Color by centrality score (continuous gradient)
- **Use case**: "Show me exactly how important each node is"

```python
def apply_heatmap_mode(manager):
    """
    Color nodes by centrality score (red=high, yellow=medium, blue=low).
    """
    # Get centrality scores (0.0 to 1.0)
    scores = {obj: obj.metadata.get('centrality_score', 0.0) 
              for obj in manager.places + manager.transitions}
    
    for obj, score in scores.items():
        # Map score to color (0.0=blue, 0.5=yellow, 1.0=red)
        if score > 0.5:
            # High importance: yellow to red
            t = (score - 0.5) * 2
            obj.fill_color = interpolate_color('#FBBF24', '#DC2626', t)
        else:
            # Low importance: blue to yellow
            t = score * 2
            obj.fill_color = interpolate_color('#3B82F6', '#FBBF24', t)
```

#### **Focus Mode** (Keyboard: `F`)
- **Effect**: Blur background, focus on selected sub-pathway
- **Use case**: "I'm editing this branch, hide distractions"

```python
def apply_focus_mode(manager, selected_objects):
    """
    Blur everything except selected objects and their neighbors.
    """
    focus_set = set(selected_objects)
    
    # Add neighbors to focus set
    for obj in selected_objects:
        focus_set.update(get_neighbors(obj, manager))
    
    for obj in manager.places + manager.transitions:
        if obj in focus_set:
            obj.blur = 0
            obj.opacity = 1.0
        else:
            obj.blur = 3  # Gaussian blur radius
            obj.opacity = 0.4
```

---

### 1.3 Overlay System for Visual Cues

**Concept**: Draw information overlay on top of canvas

```
┌─────────────────────────────────────────┐
│  Pathway Canvas (below)                 │
│  [Place] → (Transition) → [Place]       │
│                                          │
│  Overlay Layer (above):                 │
│  • Hierarchy labels: "Level 0", "Level 1"│
│  • Bounding boxes around groups         │
│  • Flow arrows showing main path        │
│  • Minimap in corner                    │
└─────────────────────────────────────────┘
```

**Implementation**:
```python
class PathwayOverlayRenderer:
    """
    Renders visual guidance overlays on top of pathway canvas.
    """
    
    def __init__(self, manager):
        self.manager = manager
        self.show_labels = True
        self.show_bounding_boxes = True
        self.show_flow_arrows = True
        self.show_minimap = True
    
    def render(self, cr, viewport):
        """
        Render overlay using Cairo context.
        
        Args:
            cr: Cairo context
            viewport: Current viewport (x, y, width, height, zoom)
        """
        if self.show_bounding_boxes:
            self.render_hierarchy_bounding_boxes(cr)
        
        if self.show_flow_arrows:
            self.render_main_flow_arrows(cr)
        
        if self.show_labels:
            self.render_hierarchy_labels(cr)
        
        if self.show_minimap:
            self.render_minimap(cr, viewport)
    
    def render_hierarchy_bounding_boxes(self, cr):
        """Draw boxes around each hierarchy level."""
        for level in [0, 1, 2]:
            objects = [obj for obj in self.manager.places + self.manager.transitions
                      if obj.metadata.get('hierarchy_level') == level]
            
            if not objects:
                continue
            
            # Calculate bounding box
            min_x = min(obj.x for obj in objects)
            min_y = min(obj.y for obj in objects)
            max_x = max(obj.x + obj.width for obj in objects)
            max_y = max(obj.y + obj.height for obj in objects)
            
            # Draw rounded rectangle
            padding = 20
            cr.set_source_rgba(*HIERARCHY_COLORS[level]['place_fill'], 0.1)
            self.draw_rounded_rect(cr, 
                                   min_x - padding, 
                                   min_y - padding, 
                                   max_x - min_x + 2*padding, 
                                   max_y - min_y + 2*padding, 
                                   radius=10)
            cr.fill()
            
            # Draw border
            cr.set_source_rgba(*HIERARCHY_COLORS[level]['place_stroke'], 0.5)
            cr.set_line_width(2)
            self.draw_rounded_rect(cr, 
                                   min_x - padding, 
                                   min_y - padding, 
                                   max_x - min_x + 2*padding, 
                                   max_y - min_y + 2*padding, 
                                   radius=10)
            cr.stroke()
    
    def render_main_flow_arrows(self, cr):
        """Draw arrows showing main metabolic flow."""
        main_backbone = [obj for obj in self.manager.transitions
                        if obj.metadata.get('hierarchy_level') == 0]
        
        # Sort by position to find flow direction
        sorted_transitions = sorted(main_backbone, key=lambda t: t.y)
        
        # Draw curved arrows between consecutive transitions
        for i in range(len(sorted_transitions) - 1):
            t1 = sorted_transitions[i]
            t2 = sorted_transitions[i + 1]
            
            # Draw thick curved arrow
            cr.set_source_rgba(1.0, 0.5, 0.0, 0.6)  # Orange
            cr.set_line_width(8)
            self.draw_curved_arrow(cr, 
                                   (t1.x, t1.y), 
                                   (t2.x, t2.y), 
                                   curvature=0.3)
            cr.stroke()
    
    def render_hierarchy_labels(self, cr):
        """Draw text labels for each hierarchy level."""
        labels = {
            0: "Main Backbone",
            1: "Primary Branches",
            2: "Secondary Pathways"
        }
        
        for level, label in labels.items():
            objects = [obj for obj in self.manager.places + self.manager.transitions
                      if obj.metadata.get('hierarchy_level') == level]
            
            if not objects:
                continue
            
            # Position label at top-left of bounding box
            min_x = min(obj.x for obj in objects)
            min_y = min(obj.y for obj in objects)
            
            # Draw text
            cr.set_source_rgba(*HIERARCHY_COLORS[level]['place_fill'], 1.0)
            cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            cr.set_font_size(16)
            cr.move_to(min_x - 20, min_y - 30)
            cr.show_text(label)
    
    def render_minimap(self, cr, viewport):
        """Draw minimap in corner showing full pathway."""
        # Minimap in bottom-right corner
        minimap_width = 200
        minimap_height = 150
        minimap_x = viewport.width - minimap_width - 20
        minimap_y = viewport.height - minimap_height - 20
        
        # Draw minimap background
        cr.set_source_rgba(0.1, 0.1, 0.1, 0.8)
        cr.rectangle(minimap_x, minimap_y, minimap_width, minimap_height)
        cr.fill()
        
        # Calculate scale factor
        all_objects = self.manager.places + self.manager.transitions
        if not all_objects:
            return
        
        min_x = min(obj.x for obj in all_objects)
        min_y = min(obj.y for obj in all_objects)
        max_x = max(obj.x + obj.width for obj in all_objects)
        max_y = max(obj.y + obj.height for obj in all_objects)
        
        scale_x = minimap_width / (max_x - min_x) if max_x > min_x else 1
        scale_y = minimap_height / (max_y - min_y) if max_y > min_y else 1
        scale = min(scale_x, scale_y) * 0.9  # Leave margin
        
        # Draw simplified objects
        for obj in all_objects:
            x = minimap_x + (obj.x - min_x) * scale
            y = minimap_y + (obj.y - min_y) * scale
            size = 3
            
            level = obj.metadata.get('hierarchy_level', 0)
            color = HIERARCHY_COLORS[level]['place_fill']
            cr.set_source_rgb(*color)
            cr.rectangle(x, y, size, size)
            cr.fill()
        
        # Draw viewport indicator
        vp_x = minimap_x + (viewport.x - min_x) * scale
        vp_y = minimap_y + (viewport.y - min_y) * scale
        vp_w = viewport.width * scale / viewport.zoom
        vp_h = viewport.height * scale / viewport.zoom
        
        cr.set_source_rgba(1.0, 1.0, 1.0, 0.5)
        cr.rectangle(vp_x, vp_y, vp_w, vp_h)
        cr.stroke()
```

---

## 🔧 Part 2: Editing Mode Management

### 2.1 Mode Switcher

**UI Element**: Toggle button in toolbar

```
┌────────────────────────────────────────┐
│ File  Edit  View  [Simulate]  Help    │
│ ┌────────────────────────────────────┐ │
│ │ Mode: (●) Create  ( ) Edit Pathway │ │
│ └────────────────────────────────────┘ │
└────────────────────────────────────────┘
```

**Implementation**:
```python
class EditingModeManager:
    """
    Manages switching between creation and pathway editing modes.
    """
    
    def __init__(self, main_window):
        self.main_window = main_window
        self.current_mode = 'create'  # 'create' or 'pathway_edit'
        self.overlay_renderer = None
        
        # Create mode toggle in UI
        self.mode_toggle = Gtk.RadioButton.new_with_label(None, "Create Mode")
        self.pathway_edit_toggle = Gtk.RadioButton.new_with_label_from_widget(
            self.mode_toggle, "Edit Pathway Mode"
        )
        
        self.mode_toggle.connect('toggled', self.on_mode_changed)
        self.pathway_edit_toggle.connect('toggled', self.on_mode_changed)
    
    def on_mode_changed(self, button):
        """Switch editing mode."""
        if self.mode_toggle.get_active():
            self.switch_to_create_mode()
        else:
            self.switch_to_pathway_edit_mode()
    
    def switch_to_create_mode(self):
        """
        Switch to interactive creation mode.
        - Standard editing operations
        - No hierarchy coloring
        - No visual guidance overlays
        """
        self.current_mode = 'create'
        
        # Disable overlay
        if self.overlay_renderer:
            self.overlay_renderer.enabled = False
        
        # Reset colors to defaults
        manager = self.main_window.get_active_canvas_manager()
        if manager:
            for obj in manager.places + manager.transitions:
                obj.fill_color = obj.default_fill_color
                obj.stroke_color = obj.default_stroke_color
                obj.opacity = 1.0
            manager.mark_dirty()
        
        # Show create palette
        self.main_window.show_create_palette()
        
        print("[EditMode] Switched to CREATE mode")
    
    def switch_to_pathway_edit_mode(self):
        """
        Switch to pathway editing mode.
        - Hierarchy-aware operations
        - Color coding by level
        - Visual guidance overlays
        - Hide/show level controls
        """
        self.current_mode = 'pathway_edit'
        
        manager = self.main_window.get_active_canvas_manager()
        if not manager:
            print("[EditMode] No active canvas, cannot switch to pathway edit mode")
            return
        
        # Check if current document has pathway metadata
        has_hierarchy = any(
            hasattr(obj, 'metadata') and 'hierarchy_level' in obj.metadata
            for obj in manager.places + manager.transitions
        )
        
        if not has_hierarchy:
            # Prompt user to compute hierarchy first
            dialog = Gtk.MessageDialog(
                transient_for=self.main_window,
                flags=0,
                message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.OK_CANCEL,
                text="Pathway Hierarchy Not Found"
            )
            dialog.format_secondary_text(
                "This document doesn't have pathway hierarchy information. "
                "Would you like to compute it now?\n\n"
                "(This analyzes the network to identify main backbone vs. branches)"
            )
            response = dialog.run()
            dialog.destroy()
            
            if response == Gtk.ResponseType.OK:
                self.compute_hierarchy(manager)
            else:
                # Switch back to create mode
                self.mode_toggle.set_active(True)
                return
        
        # Apply hierarchy coloring
        self.apply_hierarchy_colors(manager)
        
        # Enable overlay
        self.overlay_renderer = PathwayOverlayRenderer(manager)
        self.overlay_renderer.enabled = True
        
        # Show pathway editing panel
        self.main_window.show_pathway_edit_panel()
        
        print("[EditMode] Switched to PATHWAY EDIT mode")
    
    def compute_hierarchy(self, manager):
        """
        Compute hierarchy levels for current document.
        Uses centrality analysis from research.
        """
        from shypn.layout.hierarchy_analyzer import classify_pathway_hierarchy
        
        # Convert to graph and analyze
        hierarchy = classify_pathway_hierarchy(manager)
        
        # Assign levels to objects
        for obj in manager.places:
            if obj in hierarchy['main_backbone']:
                obj.metadata['hierarchy_level'] = 0
            elif obj in hierarchy['primary_branches']:
                obj.metadata['hierarchy_level'] = 1
            else:
                obj.metadata['hierarchy_level'] = 2
        
        for obj in manager.transitions:
            if obj in hierarchy['main_backbone']:
                obj.metadata['hierarchy_level'] = 0
            elif obj in hierarchy['primary_branches']:
                obj.metadata['hierarchy_level'] = 1
            else:
                obj.metadata['hierarchy_level'] = 2
        
        manager.mark_dirty()
        print(f"[Hierarchy] Computed: {len(hierarchy['main_backbone'])} main, "
              f"{len(hierarchy['primary_branches'])} primary, "
              f"{len(hierarchy['secondary_leafs'])} secondary")
    
    def apply_hierarchy_colors(self, manager):
        """Apply color scheme based on hierarchy levels."""
        for place in manager.places:
            level = place.metadata.get('hierarchy_level', 0)
            colors = HIERARCHY_COLORS[level]
            place.fill_color = colors['place_fill']
            place.stroke_color = colors['place_stroke']
        
        for transition in manager.transitions:
            level = transition.metadata.get('hierarchy_level', 0)
            colors = HIERARCHY_COLORS[level]
            transition.fill_color = colors['transition_fill']
            transition.stroke_color = colors['transition_stroke']
        
        for arc in manager.arcs:
            # Arc inherits level from source or target (use minimum)
            source_level = arc.source.metadata.get('hierarchy_level', 0)
            target_level = arc.target.metadata.get('hierarchy_level', 0)
            level = min(source_level, target_level)
            
            colors = HIERARCHY_COLORS[level]
            arc.color = colors['arc_color']
            arc.width = colors['arc_width']
        
        manager.mark_dirty()
```

---

### 2.2 Pathway Edit Panel (New)

**UI Location**: Right side panel (like Analyses, Pathways)

**Structure**:
```
┌─────────────────────────────────┐
│ Pathway Editing                 │
├─────────────────────────────────┤
│                                 │
│ Visibility Control:             │
│ ┌─────────────────────────────┐ │
│ │ [ ] Level 0: Main Backbone  │ │
│ │ [✓] Level 1: Primary        │ │
│ │ [✓] Level 2: Secondary      │ │
│ └─────────────────────────────┘ │
│                                 │
│ Visual Mode:                    │
│ ┌─────────────────────────────┐ │
│ │ (●) Color by Hierarchy      │ │
│ │ ( ) Heatmap (Centrality)    │ │
│ │ ( ) Uniform (No colors)     │ │
│ └─────────────────────────────┘ │
│                                 │
│ Overlay Options:                │
│ ┌─────────────────────────────┐ │
│ │ [✓] Bounding boxes          │ │
│ │ [✓] Flow arrows             │ │
│ │ [✓] Level labels            │ │
│ │ [✓] Minimap                 │ │
│ └─────────────────────────────┘ │
│                                 │
│ Actions:                        │
│ ┌─────────────────────────────┐ │
│ │ [Abstract Selected]         │ │
│ │ [Expand Abstraction]        │ │
│ │ [Re-compute Hierarchy]      │ │
│ │ [Auto-layout]               │ │
│ └─────────────────────────────┘ │
│                                 │
│ Statistics:                     │
│ ┌─────────────────────────────┐ │
│ │ Main backbone: 12 nodes     │ │
│ │ Primary: 18 nodes           │ │
│ │ Secondary: 8 nodes          │ │
│ │ Hidden: 5 abstractions      │ │
│ └─────────────────────────────┘ │
└─────────────────────────────────┘
```

**Implementation** (`pathway_edit_panel.ui` + `pathway_edit_panel_loader.py`):

```python
class PathwayEditPanelLoader:
    """
    Controller for Pathway Editing panel.
    """
    
    def __init__(self, main_window):
        self.main_window = main_window
        
        # Load UI
        builder = Gtk.Builder()
        builder.add_from_file('ui/panels/pathway_edit_panel.ui')
        
        self.panel = builder.get_object('pathway_edit_panel')
        
        # Get controls
        self.level0_check = builder.get_object('level0_visible')
        self.level1_check = builder.get_object('level1_visible')
        self.level2_check = builder.get_object('level2_visible')
        
        self.color_mode_hierarchy = builder.get_object('color_hierarchy')
        self.color_mode_heatmap = builder.get_object('color_heatmap')
        self.color_mode_uniform = builder.get_object('color_uniform')
        
        self.overlay_boxes = builder.get_object('overlay_boxes')
        self.overlay_arrows = builder.get_object('overlay_arrows')
        self.overlay_labels = builder.get_object('overlay_labels')
        self.overlay_minimap = builder.get_object('overlay_minimap')
        
        self.btn_abstract = builder.get_object('btn_abstract')
        self.btn_expand = builder.get_object('btn_expand')
        self.btn_recompute = builder.get_object('btn_recompute')
        self.btn_layout = builder.get_object('btn_layout')
        
        self.stats_label = builder.get_object('stats_label')
        
        # Connect signals
        self.level0_check.connect('toggled', self.on_visibility_changed)
        self.level1_check.connect('toggled', self.on_visibility_changed)
        self.level2_check.connect('toggled', self.on_visibility_changed)
        
        self.color_mode_hierarchy.connect('toggled', self.on_color_mode_changed)
        self.color_mode_heatmap.connect('toggled', self.on_color_mode_changed)
        self.color_mode_uniform.connect('toggled', self.on_color_mode_changed)
        
        self.overlay_boxes.connect('toggled', self.on_overlay_changed)
        self.overlay_arrows.connect('toggled', self.on_overlay_changed)
        self.overlay_labels.connect('toggled', self.on_overlay_changed)
        self.overlay_minimap.connect('toggled', self.on_overlay_changed)
        
        self.btn_abstract.connect('clicked', self.on_abstract_clicked)
        self.btn_expand.connect('clicked', self.on_expand_clicked)
        self.btn_recompute.connect('clicked', self.on_recompute_clicked)
        self.btn_layout.connect('clicked', self.on_layout_clicked)
    
    def on_visibility_changed(self, checkbox):
        """Show/hide hierarchy levels."""
        manager = self.main_window.get_active_canvas_manager()
        if not manager:
            return
        
        visible_levels = []
        if self.level0_check.get_active():
            visible_levels.append(0)
        if self.level1_check.get_active():
            visible_levels.append(1)
        if self.level2_check.get_active():
            visible_levels.append(2)
        
        # Update visibility
        for obj in manager.places + manager.transitions:
            level = obj.metadata.get('hierarchy_level', 0)
            obj.visible = (level in visible_levels)
        
        manager.mark_dirty()
    
    def on_color_mode_changed(self, radio):
        """Change coloring scheme."""
        if not radio.get_active():
            return
        
        manager = self.main_window.get_active_canvas_manager()
        if not manager:
            return
        
        if self.color_mode_hierarchy.get_active():
            self.apply_hierarchy_colors(manager)
        elif self.color_mode_heatmap.get_active():
            self.apply_heatmap_colors(manager)
        elif self.color_mode_uniform.get_active():
            self.apply_uniform_colors(manager)
    
    def on_overlay_changed(self, checkbox):
        """Toggle overlay elements."""
        overlay = self.main_window.editing_mode_manager.overlay_renderer
        if not overlay:
            return
        
        overlay.show_bounding_boxes = self.overlay_boxes.get_active()
        overlay.show_flow_arrows = self.overlay_arrows.get_active()
        overlay.show_labels = self.overlay_labels.get_active()
        overlay.show_minimap = self.overlay_minimap.get_active()
        
        manager = self.main_window.get_active_canvas_manager()
        if manager:
            manager.mark_dirty()
    
    def update_statistics(self):
        """Update statistics display."""
        manager = self.main_window.get_active_canvas_manager()
        if not manager:
            return
        
        counts = {0: 0, 1: 0, 2: 0}
        hidden_count = 0
        
        for obj in manager.places + manager.transitions:
            level = obj.metadata.get('hierarchy_level', 0)
            counts[level] += 1
            if obj.metadata.get('hidden', False):
                hidden_count += 1
        
        text = (f"Main backbone: {counts[0]} nodes\n"
                f"Primary: {counts[1]} nodes\n"
                f"Secondary: {counts[2]} nodes\n"
                f"Hidden: {hidden_count} abstractions")
        
        self.stats_label.set_text(text)
```

---

## 📋 Part 3: Implementation Roadmap

### Phase 1: Mode Management Infrastructure (2 days)

**Goal**: Basic mode switching

**Tasks**:
1. Create `EditingModeManager` class
2. Add mode toggle to main window toolbar
3. Implement `switch_to_create_mode()` and `switch_to_pathway_edit_mode()`
4. Test mode switching doesn't break existing functionality

**Files to create**:
- `src/shypn/helpers/editing_mode_manager.py`

**Files to modify**:
- `src/shypn/helpers/main_window_loader.py` (add mode manager)
- `ui/main/main_window.ui` (add mode toggle)

---

### Phase 2: Hierarchy Color Coding (2-3 days)

**Goal**: Color objects by hierarchy level

**Tasks**:
1. Define `HIERARCHY_COLORS` scheme
2. Implement `apply_hierarchy_colors(manager)`
3. Add `hierarchy_level` metadata to imported pathways
4. Test with KEGG pathways (glycolysis, TCA, etc.)

**Files to create**:
- `src/shypn/visualization/hierarchy_colors.py`

**Files to modify**:
- `src/shypn/importer/kegg/pathway_converter.py` (add hierarchy metadata)

---

### Phase 3: Visual Guidance Overlays (3-4 days)

**Goal**: Overlay system for visual cues

**Tasks**:
1. Create `PathwayOverlayRenderer` class
2. Implement bounding boxes rendering
3. Implement flow arrows rendering
4. Implement hierarchy labels rendering
5. Implement minimap rendering
6. Integrate with canvas rendering pipeline

**Files to create**:
- `src/shypn/visualization/overlay_renderer.py`

**Files to modify**:
- `src/shypn/canvas/canvas_manager.py` (add overlay rendering)

---

### Phase 4: Pathway Edit Panel (3-4 days)

**Goal**: UI controls for pathway editing

**Tasks**:
1. Design `pathway_edit_panel.ui` (Glade)
2. Create `PathwayEditPanelLoader` class
3. Implement visibility controls (checkboxes)
4. Implement color mode controls (radio buttons)
5. Implement overlay controls (checkboxes)
6. Implement action buttons (abstract, expand, etc.)
7. Implement statistics display
8. Integrate with main window (right dock area)

**Files to create**:
- `ui/panels/pathway_edit_panel.ui`
- `src/shypn/helpers/pathway_edit_panel_loader.py`

**Files to modify**:
- `src/shypn/helpers/main_window_loader.py` (add panel)

---

### Phase 5: Visual Effect Modes (2-3 days)

**Goal**: Implement highlight, ghost, heatmap, focus modes

**Tasks**:
1. Implement `apply_highlight_mode(manager, level)`
2. Implement `apply_ghost_mode(manager, show_hidden)`
3. Implement `apply_heatmap_mode(manager)`
4. Implement `apply_focus_mode(manager, selected)`
5. Add keyboard shortcuts (H, G, M, F)
6. Test visual modes work correctly

**Files to create**:
- `src/shypn/visualization/visual_modes.py`

**Files to modify**:
- `src/shypn/helpers/pathway_edit_panel_loader.py` (add mode controls)

---

### Phase 6: Integration & Testing (2 days)

**Goal**: Ensure both modes work seamlessly

**Tasks**:
1. Test switching between create and pathway edit modes
2. Test that create mode doesn't show hierarchy colors
3. Test that pathway edit mode works with imported pathways
4. Test that non-pathway documents can compute hierarchy
5. Test all visual modes and overlays
6. Performance testing with large pathways

**Files to create**:
- `tests/test_editing_modes.py`
- `tests/test_visual_overlays.py`

---

### Phase 7: Documentation (2 days)

**Goal**: Document dual editing system

**Tasks**:
1. Create `doc/EDITING_MODES_GUIDE.md`
2. Create `doc/PATHWAY_VISUAL_GUIDANCE.md`
3. Update main README with mode switching info
4. Add screenshots and examples
5. Create video tutorial (optional)

---

## 📊 Summary

### Key Features

| Feature | Purpose | Implementation |
|---------|---------|----------------|
| **Mode Switcher** | Toggle between create/edit modes | Toggle button in toolbar |
| **Hierarchy Colors** | Show importance by color | 3-level color scheme |
| **Visual Overlays** | Guide editing with visual cues | Overlay renderer |
| **Edit Panel** | Control visibility and visual modes | Right side panel |
| **Visual Modes** | Highlight, ghost, heatmap, focus | Keyboard shortcuts |
| **Statistics** | Show pathway composition | Live counter in panel |

### Timeline

| Phase | Days | Priority | Dependencies |
|-------|------|----------|--------------|
| 1. Mode Management | 2 | **HIGH** | None |
| 2. Hierarchy Colors | 2-3 | **HIGH** | Phase 1 |
| 3. Visual Overlays | 3-4 | **MEDIUM** | Phase 2 |
| 4. Edit Panel | 3-4 | **HIGH** | Phase 1, 2 |
| 5. Visual Modes | 2-3 | **MEDIUM** | Phase 2, 4 |
| 6. Integration | 2 | **HIGH** | All above |
| 7. Documentation | 2 | **MEDIUM** | All above |
| **TOTAL** | **16-20 days** | | |

### Integration with Existing Features

**Builds on**:
- ✅ Source/sink transitions (for abstraction)
- ✅ Transformation handlers (for editing)
- ✅ Canvas rendering (for overlays)
- ✅ KEGG import (provides hierarchy metadata)

**Enables**:
- 🎯 Hierarchical pathway editing
- 🎯 Visual guidance for complex pathways
- 🎯 Progressive disclosure (hide/show levels)
- 🎯 Better understanding of imported pathways

---

## 🎨 Visual Design Mockup

```
┌─────────────────────────────────────────────────────────────────┐
│ File  Edit  View  Simulate  Help                                │
│ Mode: (●) Create  ( ) Edit Pathway                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Main Canvas Area:                    │ Pathway Edit Panel:      │
│                                       │                          │
│  ┌─────────────────────────────────┐ │ Visibility:             │
│  │ Main Backbone (Level 0) ───────┐│ │ [✓] Level 0: Main       │
│  │                                 ││ │ [✓] Level 1: Primary    │
│  │  ●───▶[■]───▶●───▶[■]───▶●    ││ │ [ ] Level 2: Secondary  │
│  │  │    Dark   │    Dark   │     ││ │                          │
│  │  │    Blue   │    Green  │     ││ │ Visual Mode:            │
│  │  └────┘      └────┘      └─────┘│ │ (●) Hierarchy Colors    │
│  │                                  │ │ ( ) Heatmap             │
│  │ Primary Branch (Level 1) ───────┐│ │                          │
│  │                                  ││ │ Overlays:              │
│  │  ●───▶[■]───▶●                  ││ │ [✓] Bounding boxes     │
│  │     Med    Med                   ││ │ [✓] Flow arrows        │
│  │     Blue   Green                 ││ │ [✓] Labels             │
│  │                                  ││ │ [ ] Minimap            │
│  │ (Secondary paths hidden)         │ │                          │
│  │                                  │ │ Actions:                │
│  │ [Minimap]                        │ │ [Abstract Selected]     │
│  │ ┌─────┐                          │ │ [Expand]                │
│  │ │▓▓▓▓▓│ ← You are here           │ │ [Re-compute]            │
│  │ │░░▓▓░│                          │ │ [Auto-layout]           │
│  │ └─────┘                          │ │                          │
│  └──────────────────────────────────┘ │ Stats:                  │
│                                        │ Main: 12 nodes          │
│  Overlay: Flow arrows shown in orange │ Primary: 18 nodes       │
│           Bounding boxes in blue      │ Secondary: 8 nodes      │
│           Level labels at top-left    │ Hidden: 5 abstractions  │
└────────────────────────────────────────┴─────────────────────────┘
```

---

**Ready to implement?** Recommend starting with Phase 1 (Mode Management) - it's foundational and low-risk! 🚀
