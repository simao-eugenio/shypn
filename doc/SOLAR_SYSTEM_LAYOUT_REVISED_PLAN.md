# Solar System Layout Algorithm - Revised Plan (SCC-Inspired)

## Executive Summary - Clarified Vision

We are creating a **new layout algorithm** called **"Solar System Layout"** that is **inspired by** (not built on top of) force-directed principles. This is a standalone algorithm specifically designed for Petri nets.

### Key Clarifications

❌ **NOT:** Force-directed layout + SCC post-processing
✅ **YES:** New physics-based algorithm with Petri net-specific rules

### Petri Net Role Assignments

```
┌────────────────────────────────────────────────────┐
│  PETRI NET OBJECT → SOLAR SYSTEM ROLE              │
├────────────────────────────────────────────────────┤
│  SCCs (cycles)     → ⭐ Stars (gravitational cores)│
│  Places            → 🌍 Planets (orbit stars)      │
│  Transitions       → 🛸 Satellites (orbit planets) │
│  Arcs              → ⚡ Gravitational forces       │
│                       (weight = force strength)    │
└────────────────────────────────────────────────────┘
```

### Visual Metaphor

```
Before (Manual):              After (Solar System Layout):

P1 → T1 → P2                        🛸 T2
                                     ↓
T2 → P3 → T3              🌍 P2 ← ⭐ SCC ⭐ → 🌍 P3
                                     ↑
P4 → T4 → P5                      🛸 T3

(Random scatter)            (Structured orbital system)
```

## 1. Physics Model - Custom Rules

### 1.1 Gravitational Forces (Arc-Based)

Unlike traditional force-directed (uniform repulsion/attraction), our model uses **arc weights as gravitational strength**:

```python
# Traditional Force-Directed
force_attractive = distance² / k
force_repulsive = k² / distance

# Solar System Layout (NEW)
force_gravitational = (arc.weight * G * mass_source * mass_target) / distance²
# Where:
# - arc.weight = user-defined multiplicity (1, 2, 3, ...)
# - G = gravitational constant (tunable parameter)
# - mass_source/target = "mass" of objects (SCC > Place > Transition)
```

### 1.2 Object Mass Hierarchy

```python
MASS_SCC = 1000.0        # Stars are massive (strong gravity)
MASS_PLACE = 100.0       # Planets have medium mass
MASS_TRANSITION = 10.0   # Satellites have low mass
MASS_ARC_MULTIPLIER = 1.0  # Each arc weight unit adds to mass
```

### 1.3 Physics Simulation Loop

```python
def solar_system_simulation(places, transitions, arcs, sccs, iterations=1000):
    """
    Custom physics simulation for Solar System Layout.
    
    Unlike force-directed (springs + coulombic), this uses:
    - Gravitational attraction (arc-based, weighted)
    - Orbital mechanics (angular momentum conservation)
    - Mass-based hierarchy (SCCs > Places > Transitions)
    """
    
    # Initialize positions randomly
    positions = initialize_random_positions()
    velocities = initialize_zero_velocities()
    
    # Assign masses
    masses = {}
    for scc in sccs:
        masses[scc.id] = MASS_SCC
    for place in places:
        masses[place.id] = MASS_PLACE
    for transition in transitions:
        masses[transition.id] = MASS_TRANSITION
    
    # Physics loop
    for iteration in range(iterations):
        forces = {obj_id: (0.0, 0.0) for obj_id in masses}
        
        # Calculate gravitational forces (arc-based)
        for arc in arcs:
            source_id = arc.source_id
            target_id = arc.target_id
            
            # Distance vector
            dx = positions[target_id][0] - positions[source_id][0]
            dy = positions[target_id][1] - positions[source_id][1]
            distance = sqrt(dx² + dy²) + 0.01  # Avoid division by zero
            
            # Gravitational force (weighted by arc.weight)
            F = (G * arc.weight * masses[source_id] * masses[target_id]) / distance²
            
            # Force components
            Fx = F * (dx / distance)
            Fy = F * (dy / distance)
            
            # Apply to both objects (Newton's 3rd law)
            forces[source_id] = (forces[source_id][0] - Fx, forces[source_id][1] - Fy)
            forces[target_id] = (forces[target_id][0] + Fx, forces[target_id][1] + Fy)
        
        # Update velocities and positions
        for obj_id in masses:
            # F = ma → a = F/m
            ax = forces[obj_id][0] / masses[obj_id]
            ay = forces[obj_id][1] / masses[obj_id]
            
            # Update velocity (with damping for stability)
            velocities[obj_id] = (
                velocities[obj_id][0] * DAMPING + ax * DT,
                velocities[obj_id][1] * DAMPING + ay * DT
            )
            
            # Update position
            positions[obj_id] = (
                positions[obj_id][0] + velocities[obj_id][0] * DT,
                positions[obj_id][1] + velocities[obj_id][1] * DT
            )
    
    return positions
```

## 2. Algorithm Architecture (Revised)

### 2.1 Component Structure

```
SolarSystemLayoutEngine (NEW - standalone algorithm)
    ├── SCCDetector
    │   └── find_strongly_connected_components()
    │       → Identifies cycles (feedback loops)
    │       → These become "stars" in the solar system
    │
    ├── MassAssigner
    │   └── assign_masses(sccs, places, transitions)
    │       → SCC: 1000.0 (massive stars)
    │       → Place: 100.0 (medium planets)
    │       → Transition: 10.0 (light satellites)
    │
    ├── GravitationalSimulator
    │   └── simulate(objects, arcs, masses, iterations)
    │       → Arc-based gravitational forces
    │       → Weighted by arc.weight (multiplicity)
    │       → Velocity Verlet integration
    │
    └── OrbitStabilizer
        └── apply_orbital_constraints(positions, sccs)
            → Pin SCCs at stable positions
            → Ensure circular orbits for places
            → Prevent collision/overlap
```

### 2.2 Key Differences from Force-Directed

| Aspect | Force-Directed | Solar System (NEW) |
|--------|---------------|-------------------|
| **Forces** | Springs (edges) + Coulombic repulsion | Gravitational (arc-weighted) |
| **All pairs?** | Yes (all nodes repel) | No (only arc-connected) |
| **Weight** | Ignored or uniform | **Arc.weight determines force** |
| **Hierarchy** | Emergent (random) | **Explicit (SCC=star, Place=planet, Transition=satellite)** |
| **Role-based** | No | **Yes (Petri net semantics)** |

## 3. Petri Net Specific Rules

### 3.1 SCC as Stars (Gravitational Cores)

**Detection:**
```python
def detect_sccs(places, transitions, arcs):
    """Find strongly connected components (cycles)."""
    graph = build_graph(places, transitions, arcs)
    sccs = tarjan_algorithm(graph)
    
    # Filter: Only SCCs with 2+ nodes are "stars"
    # Single nodes are just regular places/transitions
    stars = [scc for scc in sccs if len(scc.nodes) >= 2]
    
    return stars
```

**Positioning:**
```python
# SCCs are pinned at the origin (center of solar system)
for scc in sccs:
    centroid = (0.0, 0.0)  # Fixed at center
    for node in scc.nodes:
        # Arrange SCC nodes in a circle around centroid
        angle = (2 * pi * i) / len(scc.nodes)
        positions[node.id] = (
            centroid[0] + SCC_RADIUS * cos(angle),
            centroid[1] + SCC_RADIUS * sin(angle)
        )
```

### 3.2 Places as Planets

**Mass:** `MASS_PLACE = 100.0`

**Behavior:**
- Attracted to SCCs (stars) via arcs
- Orbit SCCs at distance determined by arc weight
- Can have their own satellites (transitions)

**Orbital Radius:**
```python
# Heavier arc weight → closer orbit (stronger gravity)
orbital_radius = BASE_ORBIT_RADIUS / (arc.weight ** 0.5)
```

### 3.3 Transitions as Satellites

**Mass:** `MASS_TRANSITION = 10.0`

**Behavior:**
- Attracted to Places (planets) via arcs
- Orbit Places at small radius
- Lightweight → easily influenced by gravity

**Positioning:**
```python
# Transitions orbit the places they're connected to
for arc in arcs:
    if isinstance(arc.source, Place) and isinstance(arc.target, Transition):
        # Transition orbits its source place
        place = arc.source
        transition = arc.target
        
        # Small orbital radius (close to planet)
        orbit_radius = SATELLITE_ORBIT_RADIUS / arc.weight
        angle = random_angle()
        
        positions[transition.id] = (
            positions[place.id][0] + orbit_radius * cos(angle),
            positions[place.id][1] + orbit_radius * sin(angle)
        )
```

### 3.4 Arcs as Gravitational Forces

**Force Calculation:**
```python
def calculate_gravitational_force(arc, positions, masses):
    """
    Arc weight determines gravitational strength.
    Higher weight → stronger attraction → closer orbit.
    """
    source = arc.source
    target = arc.target
    
    # Distance
    dx = positions[target.id][0] - positions[source.id][0]
    dy = positions[target.id][1] - positions[source.id][1]
    distance = sqrt(dx**2 + dy**2) + 0.01
    
    # Gravitational force (arc.weight is the key multiplier)
    G = GRAVITATIONAL_CONSTANT
    F = (G * arc.weight * masses[source.id] * masses[target.id]) / distance**2
    
    return F, (dx/distance, dy/distance)  # magnitude, direction
```

## 4. UI Integration

### 4.1 Layout Palette Button

**New Button:** `SSCC` (Solar System SCC Layout)

**Location:** Layout tools palette (bottom of canvas)

**Visual:**
```
┌─────────────────────────────────────────┐
│  Layout Tools Palette                    │
├─────────────────────────────────────────┤
│  [Grid] [Tree] [Circle] [SSCC] ← NEW!  │
└─────────────────────────────────────────┘
```

**Implementation:**
```python
# In layout_palette.py
class LayoutPalette(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL)
        
        # Existing buttons
        self.grid_button = Gtk.Button(label="Grid")
        self.tree_button = Gtk.Button(label="Tree")
        self.circle_button = Gtk.Button(label="Circle")
        
        # NEW: Solar System SCC button
        self.sscc_button = Gtk.Button(label="SSCC")
        self.sscc_button.set_tooltip_text("Solar System Layout (SCC-based)")
        self.sscc_button.connect("clicked", self._on_sscc_clicked)
        
        # Pack buttons
        self.pack_start(self.grid_button, False, False, 2)
        self.pack_start(self.tree_button, False, False, 2)
        self.pack_start(self.circle_button, False, False, 2)
        self.pack_start(self.sscc_button, False, False, 2)  # NEW
    
    def _on_sscc_clicked(self, button):
        """Handle SSCC layout button click."""
        if self.on_layout_requested:
            self.on_layout_requested("solar_system_scc")
```

### 4.2 Settings Dialog

```
┌─────────────────────────────────────────────┐
│  Solar System Layout Settings               │
├─────────────────────────────────────────────┤
│  ⭐ SCC (Stars):                            │
│    Mass:          [1000.0  ]               │
│    Radius:        [50.0    ] px            │
│    Pin to center: [✓]                       │
│                                             │
│  🌍 Places (Planets):                       │
│    Mass:          [100.0   ]               │
│    Base orbit:    [300.0   ] px            │
│                                             │
│  🛸 Transitions (Satellites):               │
│    Mass:          [10.0    ]               │
│    Orbit radius:  [50.0    ] px            │
│                                             │
│  ⚡ Gravitational:                          │
│    G constant:    [1000.0  ]               │
│    Arc weight:    [✓] Use as multiplier    │
│                                             │
│  🔧 Simulation:                             │
│    Iterations:    [1000    ]               │
│    Damping:       [0.95    ]               │
│    Time step:     [0.01    ]               │
│                                             │
│  [ Preview ] [ Apply ] [ Cancel ]          │
└─────────────────────────────────────────────┘
```

## 5. Implementation Plan (8 Weeks)

### Week 1: Foundation
**Goal:** Basic infrastructure + SCC detection

**Tasks:**
- [ ] Create `src/shypn/layout/` package
- [ ] Implement `SCCDetector` (Tarjan's algorithm)
- [ ] Unit tests for SCC detection on test graphs
- [ ] Verify SCC detection on real Petri nets

**Deliverable:** SCC detection working, returns cycles

### Week 2: Mass Assignment
**Goal:** Object hierarchy and mass system

**Tasks:**
- [ ] Implement `MassAssigner` class
- [ ] Define mass constants (SCC=1000, Place=100, Transition=10)
- [ ] Create mass calculation logic
- [ ] Unit tests for mass assignment

**Deliverable:** Each object has assigned mass value

### Week 3-4: Gravitational Simulator
**Goal:** Core physics engine

**Tasks:**
- [ ] Implement `GravitationalSimulator` class
- [ ] Arc-weighted force calculation
- [ ] Velocity Verlet integration
- [ ] Position/velocity update loop
- [ ] Damping and stability controls
- [ ] Performance optimization (spatial hashing if needed)

**Deliverable:** Physics simulation produces positions

### Week 5: Orbit Stabilizer
**Goal:** Refine layout for clean orbits

**Tasks:**
- [ ] Implement `OrbitStabilizer` class
- [ ] Pin SCCs at origin
- [ ] Enforce circular orbits for places
- [ ] Ensure transitions orbit places
- [ ] Collision detection/prevention

**Deliverable:** Clean orbital structure

### Week 6: Layout Engine Integration
**Goal:** Complete algorithm pipeline

**Tasks:**
- [ ] Implement `SolarSystemLayoutEngine` orchestrator
- [ ] Wire all components together
- [ ] Integration tests with various Petri net topologies
- [ ] Visual verification on canvas

**Deliverable:** End-to-end layout working

### Week 7: UI Integration
**Goal:** User-facing features

**Tasks:**
- [ ] Create `SSCC` button in layout palette
- [ ] Create settings dialog
- [ ] Wire button → engine → canvas
- [ ] Add undo/redo support
- [ ] Add progress indicator for large models

**Deliverable:** Feature accessible from UI

### Week 8: Polish & Documentation
**Goal:** Production ready

**Tasks:**
- [ ] Add animation (smooth transition to new positions)
- [ ] Performance tuning for 100+ node models
- [ ] User documentation
- [ ] Tutorial examples
- [ ] Final testing

**Deliverable:** Shipped feature

## 6. File Structure

```
src/shypn/layout/
├── __init__.py
├── solar_system_layout_engine.py    # Main orchestrator
├── scc_detector.py                  # Tarjan's SCC detection
├── mass_assigner.py                 # Object mass hierarchy
├── gravitational_simulator.py       # Physics engine
└── orbit_stabilizer.py              # Orbital refinement

src/shypn/ui/palettes/
└── layout_palette.py                # Add SSCC button

src/shypn/dialogs/
└── solar_system_settings_dialog.py  # Settings UI

src/shypn/helpers/
└── model_canvas_loader.py           # Wire layout → canvas
```

## 7. Algorithm Pseudocode

```python
class SolarSystemLayoutEngine:
    """
    Solar System Layout - Custom physics-based algorithm for Petri nets.
    
    Roles:
    - SCCs → Stars (massive, at origin)
    - Places → Planets (medium mass, orbit stars)
    - Transitions → Satellites (light mass, orbit planets)
    - Arcs → Gravitational forces (weighted)
    """
    
    def apply_layout(self, places, transitions, arcs):
        # Step 1: Detect SCCs (stars)
        sccs = self.scc_detector.find_sccs(places, transitions, arcs)
        
        # Step 2: Assign masses
        masses = self.mass_assigner.assign_masses(sccs, places, transitions)
        
        # Step 3: Initialize positions randomly
        positions = self.initialize_positions(sccs, places, transitions)
        
        # Step 4: Run gravitational simulation
        positions = self.gravitational_simulator.simulate(
            objects=sccs + places + transitions,
            arcs=arcs,
            masses=masses,
            positions=positions,
            iterations=1000
        )
        
        # Step 5: Stabilize orbits
        positions = self.orbit_stabilizer.stabilize(
            positions=positions,
            sccs=sccs,
            places=places,
            transitions=transitions,
            arcs=arcs
        )
        
        # Step 6: Apply to canvas
        for place in places:
            place.x, place.y = positions[place.id]
        for transition in transitions:
            transition.x, transition.y = positions[transition.id]
        
        return positions
```

## 8. Example Scenarios

### Scenario 1: Producer-Consumer with Feedback

**Input:**
```
P1 (buffer) → T1 (consume) → P2 (empty)
                ↓
P2 (empty) → T2 (produce) → P1 (buffer)  ← SCC!
```

**Layout Result:**
```
        🛸 T1 (satellite)
         ↓
    ⭐ SCC ⭐ (P1 ↔ T2 ↔ P2 cycle)
         ↑
        🛸 T1 (satellite orbiting SCC)
```

### Scenario 2: Manufacturing Line

**Input:**
```
P1 → T1 → P2 → T2 → P3 → T3 → P4
```

**Layout Result:**
```
🌍 P1 → 🛸 T1 → 🌍 P2 → 🛸 T2 → 🌍 P3 → 🛸 T3 → 🌍 P4
(Linear chain with alternating planets/satellites)
```

### Scenario 3: Multi-SCC System

**Input:**
```
SCC1: P1 ↔ T1 ↔ P2  (cycle)
SCC2: P3 ↔ T2 ↔ P4  (cycle)
Arc: P2 → P3 (weight=5, strong connection)
```

**Layout Result:**
```
    ⭐ SCC1 ⭐ ───────(strong gravity)──────→ ⭐ SCC2 ⭐
    (P1,T1,P2)                                (P3,T2,P4)
    
(Two star systems, close together due to high arc weight)
```

## 9. Configuration Parameters

```python
# Masses
MASS_SCC = 1000.0           # Stars (massive)
MASS_PLACE = 100.0          # Planets (medium)
MASS_TRANSITION = 10.0      # Satellites (light)

# Radii
SCC_INTERNAL_RADIUS = 50.0  # SCC nodes arranged in circle
PLANET_ORBIT_BASE = 300.0   # Base orbit for places
SATELLITE_ORBIT = 50.0      # Transitions orbit close

# Physics
GRAVITATIONAL_CONSTANT = 1000.0
DAMPING_FACTOR = 0.95       # Velocity damping (0.9-0.99)
TIME_STEP = 0.01            # Integration time step
ITERATIONS = 1000           # Simulation iterations

# Arc weight multiplier
ARC_WEIGHT_ENABLED = True   # Use arc.weight in force calc
```

## 10. Testing Strategy

### Unit Tests
```python
def test_scc_detection():
    """Verify SCC detection finds cycles."""
    # Create cycle: P1 → T1 → P2 → T2 → P1
    assert len(sccs) == 1
    assert len(sccs[0].nodes) == 4

def test_mass_assignment():
    """Verify mass hierarchy."""
    assert masses[scc.id] == 1000.0
    assert masses[place.id] == 100.0
    assert masses[transition.id] == 10.0

def test_gravitational_force():
    """Verify force calculation uses arc weight."""
    arc.weight = 2
    force = calculate_force(arc, positions, masses)
    assert force == 2 * base_force  # Weight doubles force
```

### Integration Tests
```python
def test_full_layout():
    """End-to-end layout on test net."""
    engine = SolarSystemLayoutEngine()
    positions = engine.apply_layout(places, transitions, arcs)
    
    # Verify: SCCs at origin
    # Verify: Places orbit SCCs
    # Verify: Transitions orbit places
```

## Summary of Key Changes from Original Plan

| Original Plan | Revised Plan |
|--------------|-------------|
| Force-directed + SCC post-processing | **New algorithm (SCC-inspired physics)** |
| Generic graph algorithm | **Petri net specific (Places/Transitions/Arcs)** |
| All nodes same role | **Hierarchical roles (Stars/Planets/Satellites)** |
| Uniform forces | **Arc-weighted gravitational forces** |
| Generic UI | **SSCC button in layout palette** |
| Post-processing step | **Integrated orbital mechanics** |

---

**Status:** ✅ Plan Revised - Ready for Implementation
**Next Step:** Create layout package structure + SCC detector (Week 1)
