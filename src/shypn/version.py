"""
Single source of truth for version information across the shypn package.

This module centralizes all version declarations to prevent drift and
support runtime compatibility checking between components.

Usage:
    from shypn.version import __version__, __api_version__
"""

# Main package version (semantic versioning: MAJOR.MINOR.PATCH)
__version__ = "2.5.6"

# Version metadata
__version_name__ = "Pulsating Singularity Dynamics"
__version_date__ = "2026-01-06"

# API version for compatibility checking (MAJOR.MINOR)
# Increment MAJOR when breaking API changes occur
# Increment MINOR when backward-compatible features are added
__api_version__ = "2.5"

# Required submodule versions
__required_engine_version__ = "1.0.0"
__required_crossfetch_version__ = "1.0.0"

# Version history
__version_history__ = """
Version History:
2.5.5 (Jan 06, 2026): Version synchronization system - prevents code regressions
2.5.4 (Oct 17, 2025): Pulsating Singularity Dynamics - Version sync implementation
2.2.0 (Oct 17, 2025): Pulsating singularity - stochastic dynamics & variance tracking
2.1.0 (Oct 17, 2025): Black hole whirlwind - spiral orbital patterns ("clogged sink drain")
2.0.0 (Oct 17, 2025): Black hole galaxy with arc weakening (prevents ternary clustering)
1.5.0: SCC gravity and event horizon mechanics
1.4.0: Black hole damping wave
1.3.0: Hub group repulsion
1.2.0: SCC cohesion forces
1.1.0: Oscillatory forces with equilibrium
1.0.0: Initial unified physics implementation
"""
