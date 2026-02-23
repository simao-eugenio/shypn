"""
Single source of truth for version information across the shypn package.

This module centralizes all version declarations to prevent drift and
support runtime compatibility checking between components.

Usage:
    from shypn.version import __version__, __api_version__
"""

# Main package version (semantic versioning: MAJOR.MINOR.PATCH)
__version__ = "2.6.0"

# Version metadata
__version_name__ = "GATA Project & DTO Editing Infrastructure"
__version_date__ = "2026-02-23"

# API version for compatibility checking (MAJOR.MINOR)
# Increment MAJOR when breaking API changes occur
# Increment MINOR when backward-compatible features are added
__api_version__ = "2.6"

# Required submodule versions
__required_engine_version__ = "1.0.0"
__required_crossfetch_version__ = "1.0.0"

# Version history
__version_history__ = """
Version History:
2.6.0 (Feb 23, 2026): GATA Project & DTO Editing Infrastructure - Event-driven cache, model-independent editing
2.5.9 (Feb 17, 2026): Property Sweep & Batch Automation - Enhanced batch execution
2.5.8 (Feb 16, 2026): Batch results saver and metadata improvements
2.5.7 (Feb 15, 2026): Viability panel automation enhancements
2.5.6 (Feb 14, 2026): Event-Driven Cache & DTO Editing - GATA project validation
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
