"""Configuration options for pathway enhancement.

This module defines the configuration dataclass that controls how
enhancement processors behave.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class EnhancementOptions:
    """Configuration options for pathway enhancement pipeline.
    
    Controls which processors run and how they behave.
    Each processor checks relevant flags and parameters.
    
    Example:
        options = EnhancementOptions(
            enable_layout_optimization=True,
            layout_min_spacing=80.0,
            enable_arc_routing=False
        )
    """
    
    # ============================================================
    # Global Options
    # ============================================================
    
    enable_enhancements: bool = True
    """Master switch: if False, all enhancements are disabled."""
    
    fail_fast: bool = False
    """If True, stop pipeline on first processor error.
    If False, log errors and continue with remaining processors."""
    
    verbose: bool = False
    """Enable verbose logging of enhancement steps."""
    
    # ============================================================
    # Layout Optimization Options
    # ============================================================
    
    enable_layout_optimization: bool = True
    """Enable layout optimization processor."""
    
    layout_min_spacing: float = 60.0
    """Minimum spacing between elements in pixels."""
    
    layout_max_iterations: int = 100
    """Maximum iterations for force-directed layout refinement."""
    
    layout_repulsion_strength: float = 1000.0
    """Strength of repulsive forces between overlapping elements."""
    
    layout_attraction_strength: float = 0.1
    """Strength of attraction to original positions (preserve structure)."""
    
    layout_convergence_threshold: float = 1.0
    """Stop iterating when max movement per iteration < threshold."""
    
    # ============================================================
    # Arc Routing Options
    # ============================================================
    
    enable_arc_routing: bool = True
    """Enable arc routing processor for curved arcs."""
    
    arc_curve_style: str = 'curved'
    """Arc curvature style: 'straight', 'curved', 'orthogonal'."""
    
    arc_parallel_offset: float = 30.0
    """Offset in pixels for parallel arcs (same source/target)."""
    
    arc_obstacle_clearance: float = 20.0
    """Minimum clearance from obstacles when routing arcs."""
    
    arc_max_control_points: int = 2
    """Maximum control points for Bezier curves (2 = quadratic, 4 = cubic)."""
    
    # ============================================================
    # Metadata Enhancement Options
    # ============================================================
    
    enable_metadata_enhancement: bool = True
    """Enable metadata enhancement processor."""
    
    metadata_extract_names: bool = True
    """Extract compound/reaction names from pathway."""
    
    metadata_extract_colors: bool = True
    """Extract color information from graphics data."""
    
    metadata_extract_kegg_ids: bool = True
    """Store KEGG identifiers for linking back to database."""
    
    metadata_detect_compartments: bool = True
    """Attempt to detect cellular compartments from graphics."""
    
    # ============================================================
    # Visual Validation Options
    # ============================================================
    
    enable_visual_validation: bool = False
    """Enable visual validation processor (requires image)."""
    
    validation_image_url: Optional[str] = None
    """URL to pathway image for validation.
    If None, will attempt to construct from pathway ID."""
    
    validation_download_images: bool = False
    """Whether to download images (if False, must be pre-downloaded)."""
    
    validation_position_tolerance: float = 20.0
    """Position tolerance in pixels for validation."""
    
    validation_warn_only: bool = True
    """If True, validation errors are warnings.
    If False, validation errors stop the pipeline."""
    
    # ============================================================
    # Image Processing Options
    # ============================================================
    
    image_cache_dir: Optional[str] = None
    """Directory to cache downloaded pathway images.
    If None, uses system temp directory."""
    
    image_analysis_resolution: tuple = field(default_factory=lambda: (800, 600))
    """Target resolution for image analysis (width, height)."""
    
    # ============================================================
    # Performance Options
    # ============================================================
    
    use_spatial_indexing: bool = True
    """Use R-tree spatial indexing for overlap detection (faster)."""
    
    max_processing_time_seconds: Optional[float] = None
    """Maximum time for enhancement pipeline (None = unlimited).
    If exceeded, return partially enhanced document."""
    
    # ============================================================
    # Helper Methods
    # ============================================================
    
    def get_enabled_processors(self) -> list:
        """Return list of processor names that are enabled.
        
        Returns:
            List of strings like ['LayoutOptimizer', 'ArcRouter', ...]
        """
        enabled = []
        
        if not self.enable_enhancements:
            return enabled
        
        if self.enable_layout_optimization:
            enabled.append('LayoutOptimizer')
        
        if self.enable_arc_routing:
            enabled.append('ArcRouter')
        
        if self.enable_metadata_enhancement:
            enabled.append('MetadataEnhancer')
        
        if self.enable_visual_validation:
            enabled.append('VisualValidator')
        
        return enabled
    
    def to_dict(self) -> dict:
        """Convert options to dictionary.
        
        Returns:
            Dictionary representation of all options.
        """
        from dataclasses import asdict
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'EnhancementOptions':
        """Create options from dictionary.
        
        Args:
            data: Dictionary with option values.
        
        Returns:
            EnhancementOptions instance.
        """
        return cls(**data)
    
    def __str__(self) -> str:
        """String representation."""
        enabled = self.get_enabled_processors()
        return f"<EnhancementOptions: {len(enabled)} processors enabled>"
    
    def __repr__(self) -> str:
        """Detailed representation."""
        enabled = self.get_enabled_processors()
        return f"EnhancementOptions(enabled={enabled})"


# Preset configurations for common use cases

def get_minimal_options() -> EnhancementOptions:
    """Get minimal enhancement options (fastest).
    
    Only layout optimization, no arc routing or validation.
    """
    return EnhancementOptions(
        enable_layout_optimization=True,
        enable_arc_routing=False,
        enable_metadata_enhancement=False,
        enable_visual_validation=False,
        verbose=False
    )


def get_standard_options() -> EnhancementOptions:
    """Get standard enhancement options (balanced).
    
    Layout optimization + arc routing + metadata.
    No visual validation (requires images).
    """
    return EnhancementOptions(
        enable_layout_optimization=True,
        enable_arc_routing=True,
        enable_metadata_enhancement=True,
        enable_visual_validation=False,
        verbose=False
    )


def get_maximum_options(image_url: Optional[str] = None) -> EnhancementOptions:
    """Get maximum enhancement options (slowest, highest quality).
    
    All processors enabled including visual validation.
    
    Args:
        image_url: Optional URL to pathway image for validation.
    """
    return EnhancementOptions(
        enable_layout_optimization=True,
        enable_arc_routing=True,
        enable_metadata_enhancement=True,
        enable_visual_validation=True if image_url else False,
        validation_image_url=image_url,
        validation_download_images=True,
        verbose=True
    )
