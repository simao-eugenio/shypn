# Solar System Layout Algorithm - Quick Reference

## Core Concept (Revised & Clarified)

**New standalone algorithm** for Petri nets, inspired by gravitational physics.

### Petri Net Object Roles

```
┌──────────────────────────────────────────────┐
│  PETRI NET    →    SOLAR SYSTEM ROLE         │
├──────────────────────────────────────────────┤
│  SCC (cycle)  →  ⭐ Star (massive center)   │
│  Place        →  🌍 Planet (orbits stars)   │
│  Transition   →  🛸 Satellite (orbits plan.) │
│  Arc          →  ⚡ Gravity (weighted force) │
└──────────────────────────────────────────────┘
```

## Physics Model

### Forces (NOT Force-Directed!)

```python
# Traditional Force-Directed (springs + repulsion)
F_attr = distance² / k
F_rep = k² / distance

# Solar System (gravitational, arc-weighted) ← OUR MODEL
F_gravity = (G * arc.weight * mass1 * mass2) / distance²
```

### Mass Hierarchy

```
MASS_SCC = 1000.0        ⭐ Stars (massive)
MASS_PLACE = 100.0       🌍 Planets (medium)
MASS_TRANSITION = 10.0   🛸 Satellites (light)
```

### Arc Weight Effect

```
Arc weight=1 → Normal gravity → Standard orbit
Arc weight=5 → Strong gravity → Closer orbit (5x force!)
Arc weight=0.1 → Weak gravity → Distant orbit
```

## Visual Examples

### Example 1: Producer-Consumer Cycle

**Petri Net:**
```
P1 (buffer) →(w=1)→ T1 (consume) →(w=1)→ P2 (empty)
                                            ↓ (w=1)
P1 (buffer) ←(w=1)← T2 (produce) ←(w=1)← P2 (empty)

Result: SCC = {P1, T1, P2, T2} (4-node cycle)
```

**Solar System Layout:**
```
         🛸 External transitions
              ↓
         ⭐ SCC Star ⭐
      /  (P1 T1 P2 T2)  \
     ↓                    ↓
   Orbiting           Orbiting
   planets           satellites
```

### Example 2: Linear Workflow

**Petri Net:**
```
P1 →(w=1)→ T1 →(w=2)→ P2 →(w=1)→ T2 →(w=3)→ P3
```

**Solar System Layout:**
```
🌍P1 → 🛸T1 →(strong)→ 🌍P2 → 🛸T2 →(very strong)→ 🌍P3

Note: Higher weight → closer spacing (stronger gravity)
```

### Example 3: Multiple SCCs

**Petri Net:**
```
SCC1: {P1, T1, P2}  (3-node cycle)
SCC2: {P3, T2, P4}  (3-node cycle)
Connection: P2 →(w=10)→ P3  (very strong link)
```

**Solar System Layout:**
```
    ⭐ SCC1 ⭐ ←──(strong gravity)──→ ⭐ SCC2 ⭐
    (P1 T1 P2)                        (P3 T2 P4)
    
Two star systems pulled close together by high arc weight
```

## Algorithm Pipeline

```
INPUT: Places, Transitions, Arcs
   ↓
[1] DETECT SCCs (Tarjan)
   → Find cycles (feedback loops)
   → These become "stars"
   ↓
[2] ASSIGN MASSES
   → SCC: 1000
   → Place: 100
   → Transition: 10
   ↓
[3] INITIALIZE POSITIONS
   → Random starting positions
   → Or intelligent placement
   ↓
[4] GRAVITATIONAL SIMULATION
   → For each arc:
       F = (G * arc.weight * m1 * m2) / r²
   → Update velocities
   → Update positions
   → Repeat 1000 iterations
   ↓
[5] ORBIT STABILIZATION
   → Pin SCCs at origin
   → Enforce circular orbits
   → Prevent collisions
   ↓
OUTPUT: Final (x,y) positions
```

## UI Integration

### Layout Palette Button

```
┌────────────────────────────────┐
│   Layout Tools                  │
├────────────────────────────────┤
│  [Grid] [Tree] [Circle] [SSCC] │  ← NEW!
└────────────────────────────────┘
        └─ Tooltip: "Solar System Layout (SCC-based)"
```

### User Workflow

```
1. User creates/imports Petri net
2. User clicks [SSCC] button
3. Dialog appears with settings:
   - SCC mass: 1000
   - Place mass: 100
   - Transition mass: 10
   - G constant: 1000
   - Iterations: 1000
   - Use arc weights: [✓]
4. User clicks "Apply"
5. Algorithm runs (shows progress bar)
6. Positions animate to new layout
7. User can Undo if unsatisfied
```

## Key Differences from Force-Directed

| Aspect | Force-Directed | Solar System |
|--------|---------------|--------------|
| **Inspiration** | Springs + charges | Gravity + orbits |
| **Forces** | All-pairs repulsion | Arc-only gravity |
| **Roles** | All nodes equal | Hierarchical (SCC>Place>Trans) |
| **Arc weight** | Usually ignored | **Core feature (force multiplier)** |
| **Result** | Aesthetic scatter | **Orbital structure** |
| **Petri net** | Generic graph | **Specific to Petri nets** |

## Configuration Quick Ref

```python
# Physics Constants
G = 1000.0              # Gravitational constant
DAMPING = 0.95          # Velocity damping
DT = 0.01               # Time step
ITERATIONS = 1000       # Simulation iterations

# Masses
MASS_SCC = 1000.0       # Stars
MASS_PLACE = 100.0      # Planets  
MASS_TRANSITION = 10.0  # Satellites

# Radii
SCC_RADIUS = 50.0       # Internal SCC layout
PLANET_ORBIT = 300.0    # Base planet orbit
SATELLITE_ORBIT = 50.0  # Satellite orbit

# Arc Weight
USE_ARC_WEIGHT = True   # Multiply force by arc.weight
```

## Implementation Checklist

### Week 1: Foundation
- [ ] Create `src/shypn/layout/` package
- [ ] Implement `SCCDetector` (Tarjan's algorithm)
- [ ] Unit tests for SCC detection

### Week 2: Mass System
- [ ] Implement `MassAssigner`
- [ ] Define mass constants
- [ ] Tests for mass assignment

### Week 3-4: Physics Engine
- [ ] Implement `GravitationalSimulator`
- [ ] Arc-weighted force calculation
- [ ] Velocity Verlet integration
- [ ] Performance optimization

### Week 5: Orbit Stabilizer
- [ ] Pin SCCs at origin
- [ ] Circular orbit enforcement
- [ ] Collision prevention

### Week 6: Integration
- [ ] `SolarSystemLayoutEngine` orchestrator
- [ ] End-to-end pipeline
- [ ] Visual testing

### Week 7: UI
- [ ] SSCC button in palette
- [ ] Settings dialog
- [ ] Undo/redo support

### Week 8: Polish
- [ ] Animation
- [ ] Documentation
- [ ] User guide

## Success Metrics

**Performance:**
- ✅ < 5 sec for 100-node model
- ✅ < 60 sec for 1000-node model

**Quality:**
- ✅ SCCs clearly centered
- ✅ Places orbit SCCs in rings
- ✅ Transitions close to places
- ✅ Arc weights visible (spacing)

**Usability:**
- ✅ One-click operation
- ✅ Intuitive results
- ✅ Reproducible

## Code Skeleton

```python
class SolarSystemLayoutEngine:
    """Main orchestrator for Solar System Layout."""
    
    def __init__(self):
        self.scc_detector = SCCDetector()
        self.mass_assigner = MassAssigner()
        self.simulator = GravitationalSimulator()
        self.stabilizer = OrbitStabilizer()
    
    def apply_layout(self, places, transitions, arcs):
        # 1. Find SCCs (stars)
        sccs = self.scc_detector.find(places, transitions, arcs)
        
        # 2. Assign masses
        masses = self.mass_assigner.assign(sccs, places, transitions)
        
        # 3. Initialize
        positions = self.initialize_positions()
        
        # 4. Simulate gravity
        positions = self.simulator.run(
            objects=sccs+places+transitions,
            arcs=arcs,
            masses=masses,
            iterations=1000
        )
        
        # 5. Stabilize orbits
        positions = self.stabilizer.stabilize(positions, sccs)
        
        # 6. Apply
        self.apply_positions(places, transitions, positions)
        
        return positions
```

## FAQ

**Q: Why not just use force-directed?**
A: Force-directed treats all nodes equally. We want **semantic hierarchy** where important structures (SCCs) are central.

**Q: What if there are no SCCs?**
A: Linear chains work fine - places and transitions alternate in a line, weighted by arc forces.

**Q: What about arc weight=0?**
A: Zero weight = no force = nodes drift apart (rare in practice).

**Q: Can I disable arc weight?**
A: Yes, settings dialog has checkbox. All weights become 1.0.

**Q: How to undo?**
A: Ctrl+Z or Edit → Undo. Stores previous positions.

---

**Document:** Quick reference for Solar System Layout
**Status:** ✅ Ready for implementation
**Next:** Begin Week 1 (SCC detection)
