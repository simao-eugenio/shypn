#!/usr/bin/env python3
"""Value Objects for reducing parameter list complexity.

These immutable data classes bundle related parameters to reduce
cognitive load and improve code readability. They are safe to use
anywhere and don't affect the pseudo-MDI architecture.

USAGE:
    # Instead of:
    render_arc(arc, x1, y1, x2, y2, zoom, pan_x, pan_y, rotation)
    
    # Use:
    source = Point(x1, y1)
    target = Point(x2, y2)
    ctx = RenderContext(zoom, pan_x, pan_y, rotation)
    render_arc(arc, source, target, ctx)

Phase 1 Implementation: Basic geometric and rendering value objects
"""
from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass(frozen=True)
class Point:
    """Immutable 2D point.
    
    Attributes:
        x: X coordinate
        y: Y coordinate
    """
    x: float
    y: float
    
    def distance_to(self, other: 'Point') -> float:
        """Calculate Euclidean distance to another point."""
        import math
        return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)
    
    def __add__(self, other: 'Point') -> 'Point':
        """Add two points (vector addition)."""
        return Point(self.x + other.x, self.y + other.y)
    
    def __sub__(self, other: 'Point') -> 'Point':
        """Subtract two points (vector subtraction)."""
        return Point(self.x - other.x, self.y - other.y)
    
    def __mul__(self, scalar: float) -> 'Point':
        """Multiply point by scalar."""
        return Point(self.x * scalar, self.y * scalar)


@dataclass(frozen=True)
class RenderContext:
    """Canvas rendering context.
    
    Bundles viewport transformation parameters.
    
    Attributes:
        zoom: Zoom level (1.0 = 100%)
        pan_x: Pan offset X in world units
        pan_y: Pan offset Y in world units
        rotation: Rotation angle in degrees (0-360)
        scale: Additional scale factor (default: 1.0)
    """
    zoom: float
    pan_x: float
    pan_y: float
    rotation: float = 0.0
    scale: float = 1.0
    
    @property
    def total_scale(self) -> float:
        """Combined zoom and scale factor."""
        return self.zoom * self.scale
    
    def with_zoom(self, new_zoom: float) -> 'RenderContext':
        """Create new context with different zoom."""
        return RenderContext(new_zoom, self.pan_x, self.pan_y, self.rotation, self.scale)
    
    def with_pan(self, new_pan_x: float, new_pan_y: float) -> 'RenderContext':
        """Create new context with different pan."""
        return RenderContext(self.zoom, new_pan_x, new_pan_y, self.rotation, self.scale)


@dataclass(frozen=True)
class ViewportState:
    """Complete viewport state snapshot.
    
    Immutable snapshot of viewport configuration.
    Useful for undo/redo and state restoration.
    
    Attributes:
        zoom: Current zoom level
        pan_x: Pan offset X
        pan_y: Pan offset Y
        rotation: Rotation angle in degrees
        width: Viewport width in pixels
        height: Viewport height in pixels
    """
    zoom: float
    pan_x: float
    pan_y: float
    rotation: float
    width: int
    height: int
    
    def to_render_context(self) -> RenderContext:
        """Convert to RenderContext."""
        return RenderContext(self.zoom, self.pan_x, self.pan_y, self.rotation)


@dataclass(frozen=True)
class RenderStyle:
    """Visual style for rendering objects.
    
    Attributes:
        color: RGB color tuple (r, g, b) in [0, 1] range
        width: Line width in pixels
        dash_pattern: Optional dash pattern (None = solid line)
        alpha: Transparency (0.0 = transparent, 1.0 = opaque)
    """
    color: Tuple[float, float, float]
    width: float
    dash_pattern: Optional[Tuple[float, ...]] = None
    alpha: float = 1.0
    
    @classmethod
    def solid(cls, color: Tuple[float, float, float], width: float = 1.0) -> 'RenderStyle':
        """Create solid line style."""
        return cls(color, width, None, 1.0)
    
    @classmethod
    def dashed(cls, color: Tuple[float, float, float], width: float = 1.0) -> 'RenderStyle':
        """Create dashed line style."""
        return cls(color, width, (5.0, 3.0), 1.0)


@dataclass(frozen=True)
class Rectangle:
    """Immutable rectangle.
    
    Attributes:
        x: Left edge X coordinate
        y: Top edge Y coordinate
        width: Rectangle width
        height: Rectangle height
    """
    x: float
    y: float
    width: float
    height: float
    
    @property
    def center(self) -> Point:
        """Center point of rectangle."""
        return Point(self.x + self.width / 2, self.y + self.height / 2)
    
    @property
    def top_left(self) -> Point:
        """Top-left corner."""
        return Point(self.x, self.y)
    
    @property
    def bottom_right(self) -> Point:
        """Bottom-right corner."""
        return Point(self.x + self.width, self.y + self.height)
    
    def contains(self, point: Point) -> bool:
        """Check if point is inside rectangle."""
        return (self.x <= point.x <= self.x + self.width and
                self.y <= point.y <= self.y + self.height)
    
    def intersects(self, other: 'Rectangle') -> bool:
        """Check if this rectangle intersects with another."""
        return not (self.x + self.width < other.x or
                   other.x + other.width < self.x or
                   self.y + self.height < other.y or
                   other.y + other.height < self.y)


# ═══════════════════════════════════════════════════════════════════════════
# SIMULATION VALUE OBJECTS (To be expanded in future phases)
# ═══════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class SimulationConfig:
    """Simulation configuration parameters.
    
    Bundles simulation settings to reduce parameter lists.
    
    Attributes:
        duration: Simulation duration in time units
        dt: Time step (None = adaptive)
        mode: Simulation mode ('stochastic', 'deterministic', 'hybrid')
        use_tau_leaping: Enable tau-leaping for stochastic simulations
        tau_epsilon: Epsilon parameter for tau-leaping
        random_seed: Random seed for reproducibility (None = random)
    """
    duration: float
    dt: Optional[float] = None
    mode: str = 'stochastic'
    use_tau_leaping: bool = True
    tau_epsilon: float = 0.03
    random_seed: Optional[int] = None
    
    @property
    def is_adaptive(self) -> bool:
        """Check if using adaptive timestep."""
        return self.dt is None


@dataclass(frozen=True)
class BatchConfig:
    """Batch execution configuration.
    
    Attributes:
        n_replicates: Number of replicate runs
        settings: Simulation settings
        recorded_objects: List of object IDs to record
        parallel: Enable parallel execution
        n_workers: Number of parallel workers (None = auto)
    """
    n_replicates: int
    settings: SimulationConfig
    recorded_objects: Tuple[str, ...] = ()
    parallel: bool = False
    n_workers: Optional[int] = None


@dataclass(frozen=True)
class RecordingConfig:
    """Data recording configuration for simulation data collection.
    
    Bundles all recording-related parameters for DataCollector.
    
    Attributes:
        recording_interval: Record state every Nth call to record_state
                           (1=every step, 10=every 10th step, ignored if time_based=True)
        time_based_recording: If True, record at fixed model-time intervals
                             Guarantees consistent data density regardless of playback speed
        recording_time_interval: Model-time interval between recordings (default 0.05s = 20 Hz)
        recorded_objects: Optional set of place/transition IDs to record
                        If None or empty, records ALL objects
        adaptive_tau_threshold: S5 (engine_stability_audit 2026-04-29).
            When set, the data collector force-records any step whose previous
            engine τ was below this threshold (transient regime).  Lets long
            simulation horizons keep coarse decimation while still capturing
            sub-second transients.  ``None`` disables (default).
    """
    recording_interval: int = 1
    time_based_recording: bool = True
    recording_time_interval: float = 0.05
    recorded_objects: Optional[set] = None
    adaptive_tau_threshold: Optional[float] = None
    
    @classmethod
    def default(cls) -> 'RecordingConfig':
        """Create default recording config (20 Hz time-based, all objects)."""
        return cls()
    
    @classmethod
    def step_based(cls, interval: int = 1, recorded_objects: Optional[set] = None) -> 'RecordingConfig':
        """Create step-based recording config (for high-performance batch mode)."""
        return cls(
            recording_interval=interval,
            time_based_recording=False,
            recording_time_interval=0.05,
            recorded_objects=recorded_objects
        )


# ═══════════════════════════════════════════════════════════════════════════
# WAYLAND SAFETY VALUE OBJECTS (Future phase)
# ═══════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class ParentWindowState:
    """Wayland parent window state for safe transient_for operations.
    
    Tracks parent window state to prevent Wayland Error 71.
    
    Attributes:
        is_mapped: Whether parent window is mapped
        is_realized: Whether parent window is realized
        is_visible: Whether parent window is visible
        window_id: Window identifier
    """
    is_mapped: bool
    is_realized: bool
    is_visible: bool
    window_id: Optional[int] = None
    
    @property
    def is_ready_for_transient(self) -> bool:
        """Check if parent is ready for set_transient_for()."""
        return self.is_mapped and self.is_realized
