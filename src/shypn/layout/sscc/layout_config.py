"""Solar System Layout - Easy Parameter Configuration

Quick parameter adjustment without editing the main simulator code.
Just uncomment and modify the preset you want to use!
"""

# =============================================================================
# CHOOSE YOUR PRESET (uncomment one)
# =============================================================================

# # Preset 1: COMPACT (Small Canvas, < 2000px)
# PROXIMITY_CONSTANT = 50.0
# EQUILIBRIUM_SCALE = 150.0
# UNIVERSAL_REPULSION_MULTIPLIER = 200.0

# Preset 2: BALANCED (Medium Canvas, 2000-4000px) ⭐ DEFAULT
PROXIMITY_CONSTANT = 100.0
EQUILIBRIUM_SCALE = 200.0
UNIVERSAL_REPULSION_MULTIPLIER = 200.0

# # Preset 3: WIDE (Large Canvas, > 4000px)
# PROXIMITY_CONSTANT = 200.0
# EQUILIBRIUM_SCALE = 250.0
# UNIVERSAL_REPULSION_MULTIPLIER = 250.0

# # Preset 4: MAXIMUM (Presentation/Demo)
# PROXIMITY_CONSTANT = 300.0
# EQUILIBRIUM_SCALE = 300.0
# UNIVERSAL_REPULSION_MULTIPLIER = 300.0


# =============================================================================
# ADVANCED TUNING (modify carefully)
# =============================================================================

# Arc attraction (0.01-0.1, default: 0.05)
GRAVITY_CONSTANT = 0.05

# Spring repulsion (100-1000, default: 500)
SPRING_CONSTANT = 500.0

# Simulation quality (500-2000, default: 1000)
NUM_ITERATIONS = 1000

# Velocity damping (0.8-0.95, default: 0.9)
DAMPING = 0.9


# =============================================================================
# EXPECTED RESULTS
# =============================================================================

"""
With PROXIMITY_CONSTANT = 100 (Balanced preset):
- Hub-to-hub separation: ~1200-1400 units
- Place orbital radius: ~200-400 units  
- Canvas-friendly scale
- Good for general use

Adjust PROXIMITY_CONSTANT up/down for wider/tighter layouts.
"""
