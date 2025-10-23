# Master Palette Refactoring - REVISED Plan

**Date**: October 20, 2025 (Revised)  
**Objective**: Vertical master toolbar on far left with category buttons  
**Branch**: feature/property-dialogs-and-simulation-palette  
**Backup**: legacy/shypn_backup_20251020_131029.tar.gz ✅

---

## 🔄 REFINEMENTS (October 20, 2025)

### Critical Changes to Original Plan

#### 1. **Master Palette Positioning** 🎯
- **TOP**: Starts **below HeaderBar** (not overlapping title)
- **BOTTOM**: Ends **above status bar** (leaves status bar visible)
- **HEIGHT**: Full height between HeaderBar and status bar
- **VISIBLE**: Always visible on startup (not toggleable)

#### 2. **Button Population** 📍
- **Direction**: Top to bottom
- **Order**: Files → Pathways → Analyses → Topology
- **Alignment**: Buttons packed from top (valign: start)

#### 3. **Panel Float/Attach Buttons** 🔘
- **Location**: Top-right corner of **each panel**
- **Applies to**: Analyses, Pathway, Topology panels (NOT master palette)
- **Current behavior**: Keep existing float/attach button in each panel's toolbar
- **Master palette buttons**: Only control show/hide, NOT float/attach

#### 4. **Terminology Clarification** 📚
- **Master Palette**: The new vertical toolbar (this refactoring)
- **Panels**: Analyses, Pathway, Topology, Files (complex components with own toolbars)
- **Dock Areas**: Left dock, Right dock (containers where panels attach)

---

## 🎨 REVISED Architecture

### Visual Layout (CORRECTED)

```
┌──────────────────────────────────────────────────┐
│  Shypn                          [_][□][×]        │ ← HeaderBar
├──┬───────────────────────────────────────────────┤
│📁│ ┌──────────┬───────────────────┬────────────┐ │
│  │ │          │                   │  [Float]   │ │ ← Panel has float button
│🗺│ │   Left   │                   │ ┌────────┐ │ │
│  │ │   Dock   │      Canvas       │ │Analyses│ │ │
│📊│ │  (Files) │                   │ │ Panel  │ │ │
│  │ │          │                   │ └────────┘ │ │
│🔬│ └──────────┴───────────────────┴────────────┘ │
│  │                                                │
├──┼────────────────────────────────────────────────┤
│  │ Status: Ready                                  │ ← Status Bar
└──┴────────────────────────────────────────────────┘
 ↑
Master Palette
- Below HeaderBar
- Above Status Bar
- Always visible
- Controls panel show/hide only
```

### Layout Structure (CORRECTED)

```
GtkApplicationWindow (main_window)
├── GtkHeaderBar ────────────────────────────────┐
│                                                 │
├── GtkBox (root_container) - HORIZONTAL ────────┤
│   │                                             │
│   ├── GtkBox (master_palette_container) ───────┤ ← NEW: 48px wide
│   │   ├── Button (Files)    📁                 │   Top-aligned
│   │   ├── Button (Pathways) 🗺                 │   Packed from top
│   │   ├── Button (Analyses) 📊                 │
│   │   ├── Button (Topology) 🔬                 │
│   │   └── [Spacer] ───────────────────────────┤   Pushes to top
│   │                                             │
│   └── GtkPaned (left_paned) ───────────────────┤
│       ├── GtkBox (left_dock_area)              │
│       │   └── Files Panel (when docked)        │
│       │                                         │
│       └── GtkPaned (right_paned) ──────────────┤
│           ├── GtkBox (main_workspace)          │
│           │   ├── Canvas                       │
│           │   └── Status Bar ──────────────────┤ ← At bottom
│           │                                     │
│           └── GtkBox (right_dock_area)         │
│               └── Analyses/Pathway Panel       │
│                   └── [Float] button ──────────┤ ← Top-right of panel
│                                                 │
└─────────────────────────────────────────────────┘
```

---

## 🔧 REVISED Implementation Details

### Refinement 1: Master Palette Positioning

#### Current (WRONG) Layout:
```xml
<child>
  <object class="GtkBox" id="root_container">
    <child>
      <object class="GtkBox" id="master_palette_slot">
        <!-- Palette here spans full window height -->
      </object>
    </child>
    <child>
      <object class="GtkPaned" id="left_paned">
        <!-- ... -->
      </object>
    </child>
  </object>
</child>
```

**Problem**: Palette would overlap HeaderBar and Status Bar

#### Revised (CORRECT) Layout:
```xml
<child type="titlebar">
  <object class="GtkHeaderBar" id="header_bar">
    <!-- HeaderBar content -->
  </object>
</child>

<child>
  <object class="GtkBox" id="root_container" orientation="horizontal">
    <property name="visible">True</property>
    
    <!-- Master Palette: Between HeaderBar and Status Bar -->
    <child>
      <object class="GtkBox" id="master_palette_container">
        <property name="visible">True</property>
        <property name="orientation">vertical</property>
        <property name="width-request">48</property>
        <property name="hexpand">False</property>
        <property name="vexpand">True</property>
        <property name="valign">fill</property>
        <!-- Palette buttons will be added programmatically from top -->
      </object>
      <packing>
        <property name="expand">False</property>
        <property name="fill">True</property>
      </packing>
    </child>
    
    <!-- Main content area with paned layout -->
    <child>
      <object class="GtkBox" id="content_with_statusbar" orientation="vertical">
        <property name="visible">True</property>
        <property name="hexpand">True</property>
        <property name="vexpand">True</property>
        
        <!-- Paned layout (left dock + workspace + right dock) -->
        <child>
          <object class="GtkPaned" id="left_paned">
            <property name="visible">True</property>
            <property name="orientation">horizontal</property>
            <property name="vexpand">True</property>
            <!-- ... existing paned content ... -->
          </object>
          <packing>
            <property name="expand">True</property>
            <property name="fill">True</property>
          </packing>
        </child>
        
        <!-- Status Bar at bottom -->
        <child>
          <object class="GtkStatusbar" id="status_bar">
            <property name="visible">True</property>
            <property name="vexpand">False</property>
          </object>
          <packing>
            <property name="expand">False</property>
            <property name="fill">True</property>
          </packing>
        </child>
        
      </object>
      <packing>
        <property name="expand">True</property>
        <property name="fill">True</property>
      </packing>
    </child>
    
  </object>
</child>
```

**Key Points**:
- Master palette is in `root_container` (horizontal box)
- Palette gets `vexpand=True` to fill height between HeaderBar and Status Bar
- Status bar is in `content_with_statusbar` vertical box
- Palette is **always visible** (no toggle to hide it)

---

### Refinement 2: Button Population (Top to Bottom)

#### MasterPalette Class (REVISED)

```python
class MasterPalette:
    """Master vertical palette - always visible, controls panel visibility."""
    
    def __init__(self, ui_path: Optional[Path] = None):
        self.container = None
        self.buttons: Dict[str, 'PaletteButton'] = {}
        self.active_category: Optional[str] = None
        self._callbacks: Dict[str, Callable] = {}
        
        self._create_container()  # Create programmatically (no UI file needed)
        self._apply_css()
    
    def _create_container(self):
        """Create palette container programmatically."""
        self.container = Gtk.Box()
        self.container.set_name('master_palette_container')
        self.container.set_visible(True)  # ALWAYS VISIBLE
        self.container.set_orientation(Gtk.Orientation.VERTICAL)
        self.container.set_spacing(0)
        self.container.set_size_request(48, -1)  # Fixed width, expand height
        self.container.set_hexpand(False)
        self.container.set_vexpand(True)
        self.container.set_valign(Gtk.Align.FILL)
        
        # Add spacer at bottom to keep buttons at top
        spacer = Gtk.Box()
        spacer.set_vexpand(True)
        self.container.pack_end(spacer, True, True, 0)
    
    def add_button(
        self,
        category: str,
        icon_name: str,
        tooltip: str,
        callback: Callable[[bool], None]
    ) -> 'PaletteButton':
        """Add button to palette (packed from top).
        
        Buttons are added in order:
        1. Files (top)
        2. Pathways
        3. Analyses
        4. Topology (bottom of buttons, but spacer pushes all to top)
        """
        button = PaletteButton(category, icon_name, tooltip)
        button.connect_toggled(lambda active: self._on_button_toggled(category, active))
        
        self.buttons[category] = button
        self._callbacks[category] = callback
        
        # Pack from START (top) with spacing
        self.container.pack_start(button.widget, False, False, self.BUTTON_SPACING)
        
        return button
```

**Usage in shypn.py**:
```python
# Create master palette
master_palette = MasterPalette()

# Add buttons in order (top to bottom)
master_palette.add_button('files', 'folder-symbolic', 'File Operations', on_files_toggled)
master_palette.add_button('pathways', 'network-workgroup-symbolic', 'Pathway Import', on_pathways_toggled)
master_palette.add_button('analyses', 'utilities-system-monitor-symbolic', 'Dynamic Analyses', on_analyses_toggled)
master_palette.add_button('topology', 'applications-science-symbolic', 'Topology Analysis', on_topology_toggled)

# Insert into main window (will be visible on startup)
palette_container = main_builder.get_object('master_palette_container')
palette_container.pack_start(master_palette.get_widget(), True, True, 0)
```

---

### Refinement 3: Panel Float/Attach Buttons

#### Current Panel Structure (Keep This!)

Each panel (Analyses, Pathway, Topology) has its own toolbar with float/attach button:

**Example: right_panel.ui (Analyses Panel)**
```xml
<object class="GtkWindow" id="right_panel_window">
  <child>
    <object class="GtkBox" orientation="vertical">
      <!-- Panel Toolbar (top of panel) -->
      <child>
        <object class="GtkToolbar">
          <child>
            <object class="GtkToolButton">
              <property name="label">Refresh</property>
            </object>
          </child>
          <child>
            <object class="GtkSeparatorToolItem"/>
          </child>
          <child>
            <object class="GtkToggleToolButton" id="float_button">  ← TOP RIGHT
              <property name="label">Float</property>
              <property name="icon-name">window-new</property>
            </object>
            <packing>
              <property name="pack-type">end</property>  ← Packs to right
            </packing>
          </child>
        </object>
      </child>
      
      <!-- Panel Content -->
      <child>
        <object class="GtkBox" id="right_panel_content">
          <!-- ... panel content ... -->
        </object>
      </child>
    </object>
  </child>
</object>
```

**No Changes Needed**: Existing panel float buttons stay where they are (top-right of each panel).

#### Responsibility Separation

| Component | Responsibility |
|-----------|---------------|
| **Master Palette Button** | Show/Hide panel (toggle visibility) |
| **Panel Float Button** | Float/Attach panel (change docking state) |

**Example Interaction**:
1. User clicks 📊 Analyses button in master palette
   - Panel becomes visible (docks to right dock area)
   - Master palette button shows active state
   
2. User clicks [Float] button in Analyses panel toolbar
   - Panel undocks and becomes floating window
   - Master palette button stays active (panel still visible, just floating)
   
3. User closes floating Analyses window
   - Panel becomes hidden
   - Master palette button becomes inactive

---

### Refinement 4: Terminology & Clarifications

#### Components Hierarchy

```
Application
├── Main Window
│   ├── HeaderBar
│   ├── Master Palette ─────────────────┐ NEW: This refactoring
│   │   └── Category Buttons            │ (Show/hide panels)
│   │       ├── Files                    │
│   │       ├── Pathways                 │
│   │       ├── Analyses                 │
│   │       └── Topology                 │
│   │                                     │
│   ├── Dock Areas                       │
│   │   ├── Left Dock ──────────────────┤ Contains Files panel
│   │   │   └── Files Panel              │
│   │   │       └── [Minimal UI]         │
│   │   │                                 │
│   │   └── Right Dock ─────────────────┤ Contains Analyses/Pathway/Topology
│   │       └── Analyses Panel           │
│   │       │   ├── Panel Toolbar        │
│   │       │   │   └── [Float] button ──┤ Top-right of panel
│   │       │   └── Panel Content        │
│   │       │                             │
│   │       └── Pathway Panel            │
│   │       │   ├── Panel Toolbar        │
│   │       │   │   └── [Float] button ──┤ Top-right of panel
│   │       │   └── Panel Content        │
│   │       │                             │
│   │       └── Topology Panel (FUTURE)  │
│   │           ├── Panel Toolbar        │
│   │           │   └── [Float] button ──┤ Top-right of panel
│   │           └── Panel Content        │
│   │                                     │
│   ├── Canvas (Main Workspace)          │
│   └── Status Bar                       │
│                                         │
└── Floating Windows (when panels float) │
    ├── Analyses Window (detached) ──────┤ Has [Dock] button
    ├── Pathway Window (detached) ───────┤ Has [Dock] button
    └── Topology Window (detached) ──────┤ Has [Dock] button
```

#### Terminology Table

| Term | Definition | Example |
|------|------------|---------|
| **Master Palette** | Vertical toolbar at far left | The new component we're building |
| **Category Button** | Button in master palette | 📁 Files, 🗺 Pathways, 📊 Analyses, 🔬 Topology |
| **Panel** | Complex UI component with toolbar and content | Analyses panel, Pathway panel, Topology panel |
| **Dock Area** | Container where panels attach | Left dock (for Files), Right dock (for others) |
| **Float Button** | Button in panel toolbar (top-right) | [Float] / [Dock] toggle in panel |
| **Panel Loader** | Python class managing panel lifecycle | `RightPanelLoader`, `PathwayPanelLoader` |
| **Status Bar** | Bottom info bar | "Ready", "Loading...", etc. |

---

## 🎯 REVISED Success Criteria

### Visual Layout (MUST HAVE)

✅ **Master Palette Positioning**:
- [ ] Starts below HeaderBar (no overlap)
- [ ] Ends above Status Bar (status bar always visible)
- [ ] 48px wide, full height between HeaderBar and Status Bar
- [ ] Always visible on startup (not hidden)
- [ ] Fixed position (doesn't move)

✅ **Button Layout**:
- [ ] Buttons packed from top to bottom
- [ ] Order: Files → Pathways → Analyses → Topology
- [ ] 48x48px buttons with 32px icons
- [ ] 6px spacing between buttons
- [ ] Buttons stay at top (spacer at bottom)

✅ **Panel Float Buttons**:
- [ ] Each panel keeps its own float button
- [ ] Float button is in top-right of panel toolbar
- [ ] Float button works independently of master palette
- [ ] Master palette button stays active when panel floats

✅ **Status Bar**:
- [ ] Always visible at bottom
- [ ] Below all dock areas and canvas
- [ ] Master palette doesn't cover it

---

## 🔧 REVISED Implementation Checklist

### Phase 1: Infrastructure (REVISED)

#### 1.1 Master Palette Container (Simplified)
```python
# No UI file needed - create programmatically
def _create_container(self):
    self.container = Gtk.Box()
    self.container.set_orientation(Gtk.Orientation.VERTICAL)
    self.container.set_spacing(0)
    self.container.set_size_request(48, -1)  # Width 48px, height auto
    self.container.set_hexpand(False)
    self.container.set_vexpand(True)  # Expand to fill height
    self.container.set_valign(Gtk.Align.FILL)
    self.container.set_visible(True)  # ALWAYS VISIBLE
    
    # Spacer to keep buttons at top
    spacer = Gtk.Box()
    spacer.set_vexpand(True)
    self.container.pack_end(spacer, True, True, 0)
```

#### 1.2 Button Population (From Top)
```python
# Add buttons in order
self.container.pack_start(button1, False, False, 6)  # Files (top)
self.container.pack_start(button2, False, False, 6)  # Pathways
self.container.pack_start(button3, False, False, 6)  # Analyses
self.container.pack_start(button4, False, False, 6)  # Topology
# Spacer is at end, pushing buttons to top
```

### Phase 2: Main Window Integration (REVISED)

#### 2.1 main_window.ui Structure
```xml
<object class="GtkApplicationWindow" id="main_window">
  <!-- HeaderBar (titlebar) -->
  <child type="titlebar">
    <object class="GtkHeaderBar" id="header_bar">
      <property name="show-close-button">True</property>
      <property name="title">Shypn</property>
      <!-- NO toggle buttons here anymore -->
    </object>
  </child>
  
  <!-- Main content -->
  <child>
    <object class="GtkBox" id="root_container">
      <property name="orientation">horizontal</property>
      <property name="visible">True</property>
      
      <!-- Master Palette (48px, full height) -->
      <child>
        <object class="GtkBox" id="master_palette_container">
          <property name="visible">True</property>
          <property name="orientation">vertical</property>
          <property name="width-request">48</property>
          <property name="hexpand">False</property>
          <property name="vexpand">True</property>
          <!-- Palette inserted here programmatically -->
        </object>
      </child>
      
      <!-- Content + Status Bar -->
      <child>
        <object class="GtkBox" id="content_area">
          <property name="orientation">vertical</property>
          <property name="visible">True</property>
          <property name="hexpand">True</property>
          <property name="vexpand">True</property>
          
          <!-- Paned layout (existing) -->
          <child>
            <object class="GtkPaned" id="left_paned">
              <property name="vexpand">True</property>
              <!-- ... left dock + workspace + right dock ... -->
            </object>
          </child>
          
          <!-- Status Bar (moved here from shypn.py) -->
          <child>
            <object class="GtkStatusbar" id="status_bar">
              <property name="visible">True</property>
              <property name="vexpand">False</property>
            </object>
          </child>
          
        </object>
      </child>
      
    </object>
  </child>
</object>
```

#### 2.2 shypn.py Changes
```python
# Create master palette
master_palette = MasterPalette()

# Get container from main window
palette_container = main_builder.get_object('master_palette_container')
if palette_container:
    # Remove any children (should be empty)
    for child in palette_container.get_children():
        palette_container.remove(child)
    
    # Add palette
    palette_container.pack_start(master_palette.get_widget(), True, True, 0)
    palette_container.show_all()

# Add buttons (top to bottom order)
master_palette.add_button('files', 'folder-symbolic', 'File Operations', on_files_toggled)
master_palette.add_button('pathways', 'network-workgroup-symbolic', 'Pathway Import', on_pathways_toggled)
master_palette.add_button('analyses', 'utilities-system-monitor-symbolic', 'Dynamic Analyses', on_analyses_toggled)
master_palette.add_button('topology', 'applications-science-symbolic', 'Topology Analysis (Coming Soon)', on_topology_toggled)

# Status bar moved to main_window.ui (no longer created here)
status_bar = main_builder.get_object('status_bar')
status_context_id = status_bar.get_context_id("main")
```

### Phase 3: Panel Float Button (NO CHANGES)

**Keep existing float button implementation**:
- Already in top-right of each panel toolbar
- Already has float/dock functionality
- No modifications needed

**Just verify**:
```bash
# Check panel float buttons are in top-right
grep -A 10 'float_button' ui/panels/right_panel.ui
grep -A 10 'float_button' ui/panels/pathway_panel.ui
```

Expected output should show `pack-type=end` (right side).

---

## 📊 REVISED Visual Specification

### Layout Measurements

```
┌─────────────────────────────────────────────────┐
│ HeaderBar (32px height)                         │ ← GTK default
├──┬──────────────────────────────────────────────┤
│48│                                              ││
│px│              Canvas Area                     ││ Variable height
│  │                                              ││ (window - header - status)
│  │                                              ││
├──┼──────────────────────────────────────────────┤
│  │ Status Bar (24px height)                     │ ← GTK default
└──┴──────────────────────────────────────────────┘
   ↑
   Master Palette
   - 48px wide
   - Full height minus HeaderBar and Status Bar
   - Always visible
```

### Spacing Details

```
Master Palette (48px wide)
┌────────────────────┐
│  ┌──────────────┐  │ ← 3px margin top
│  │              │  │
│  │   Files 📁   │  │ ← 48x48px button
│  │              │  │
│  └──────────────┘  │
│       6px gap      │ ← BUTTON_SPACING
│  ┌──────────────┐  │
│  │              │  │
│  │ Pathways 🗺  │  │ ← 48x48px button
│  │              │  │
│  └──────────────┘  │
│       6px gap      │
│  ┌──────────────┐  │
│  │              │  │
│  │ Analyses 📊  │  │ ← 48x48px button
│  │              │  │
│  └──────────────┘  │
│       6px gap      │
│  ┌──────────────┐  │
│  │              │  │
│  │ Topology 🔬  │  │ ← 48x48px button
│  │              │  │
│  └──────────────┘  │
│                    │
│    [Spacer fills   │ ← Expands to bottom
│     remaining      │
│     space]         │
│                    │
└────────────────────┘
```

---

## ✅ REVISED Implementation Summary

### Key Changes from Original Plan

| Aspect | Original Plan | REVISED Plan |
|--------|---------------|--------------|
| **Palette Height** | Full window height | HeaderBar → Status Bar |
| **Status Bar** | Created in shypn.py | Defined in main_window.ui |
| **Palette Visibility** | Not specified | ALWAYS visible on startup |
| **Button Packing** | Not specified | pack_start (top to bottom) |
| **Float Buttons** | Not specified | Keep in panel top-right (no changes) |
| **UI File** | master_palette.ui | Not needed (create programmatically) |

### Simplified File Structure

**Files to Create**:
```
src/shypn/panels/
├── __init__.py
├── master_palette.py        ← ~200 lines (simplified)
└── palette_button.py        ← ~100 lines (unchanged)
```

**Files to Modify**:
```
ui/main/main_window.ui       ← Add palette container + move status bar
src/shypn.py                 ← Create palette, remove status bar creation
```

**Files to Keep Unchanged**:
```
ui/panels/right_panel.ui     ← Float button already in top-right ✓
ui/panels/pathway_panel.ui   ← Float button already in top-right ✓
ui/panels/left_panel.ui      ← (if has float button)
```

---

## 🚀 Next Steps (REVISED)

### Immediate Action Items

1. **Review this revised plan** ✓
2. **Create directory structure**:
   ```bash
   mkdir -p src/shypn/panels
   mkdir -p tests/panels
   ```
3. **Implement MasterPalette** (simplified - no UI file)
4. **Implement PaletteButton** (unchanged from original)
5. **Modify main_window.ui** (add palette container, move status bar)
6. **Modify shypn.py** (create palette, integrate)
7. **Test visual layout** (palette height, button order, status bar)
8. **Migrate toggle logic** (from HeaderBar to palette)
9. **Clean up** (remove HeaderBar toggles)

### Timeline (REVISED)

| Phase | Time | Tasks |
|-------|------|-------|
| 1: Infrastructure | 4-6h | Simplified (no UI file needed) |
| 2: Integration | 6-8h | main_window.ui + shypn.py |
| 3: Migration | 6-8h | Toggle logic (unchanged) |
| 4: Cleanup | 4-6h | Remove legacy (unchanged) |
| **TOTAL** | **20-28h** | **Slightly faster than original** |

---

## 📋 Questions Answered

### Q: Where exactly does the Master Palette start and end?
**A**: Starts below HeaderBar title, ends above Status Bar. Full height between them.

### Q: How are buttons populated?
**A**: Top to bottom using `pack_start()`. Order: Files, Pathways, Analyses, Topology. Spacer at bottom keeps them at top.

### Q: Is the Master Palette visible on startup?
**A**: YES, always visible. No toggle to hide it.

### Q: Where are the panel float/attach buttons?
**A**: Top-right corner of each panel's toolbar. No changes needed - already there.

### Q: What's the difference between master palette buttons and panel float buttons?
**A**:
- **Master palette button**: Show/hide panel (visibility)
- **Panel float button**: Float/attach panel (docking state)

### Q: What if a panel is floating and I click its master palette button again?
**A**: Button toggles off, floating window closes (panel becomes hidden).

---

**Status**: 🟢 REVISED - Ready to Implement  
**Changes**: Positioning, height, status bar, visibility  
**Risk**: 🟡 Same as before (well-planned)  
**Backup**: ✅ Complete

**Last Updated**: October 20, 2025 (Revised)  
**Version**: 2.0 (Refined)
