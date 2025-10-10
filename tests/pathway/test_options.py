"""Unit tests for EnhancementOptions."""

import pytest
from shypn.pathway.options import (
    EnhancementOptions,
    get_minimal_options,
    get_standard_options,
    get_maximum_options
)


class TestEnhancementOptions:
    """Test EnhancementOptions dataclass."""
    
    def test_default_options(self):
        """Default options are sensible."""
        opts = EnhancementOptions()
        
        # Global defaults
        assert opts.enable_enhancements is True
        assert opts.verbose is False
        assert opts.fail_fast is False
        
        # Layout defaults
        assert opts.enable_layout_optimization is True
        assert opts.layout_min_spacing == 60.0
        assert opts.layout_max_iterations == 100
        
        # Arc defaults
        assert opts.enable_arc_routing is True
        assert opts.arc_curve_style == 'curved'
        assert opts.arc_parallel_offset == 30.0
        
        # Metadata defaults
        assert opts.enable_metadata_enhancement is True
        assert opts.metadata_extract_names is True
        
        # Validation defaults
        assert opts.enable_visual_validation is False
    
    def test_custom_options(self):
        """Can create custom options."""
        opts = EnhancementOptions(
            verbose=True,
            layout_min_spacing=80.0,
            arc_curve_style='bezier'
        )
        
        assert opts.verbose is True
        assert opts.layout_min_spacing == 80.0
        assert opts.arc_curve_style == 'bezier'
        # Others remain default
        assert opts.enable_enhancements is True
    
    def test_disable_all_enhancements(self):
        """Can disable all enhancements."""
        opts = EnhancementOptions(enable_enhancements=False)
        assert opts.enable_enhancements is False
    
    def test_disable_individual_processors(self):
        """Can disable individual processors."""
        opts = EnhancementOptions(
            enable_layout_optimization=False,
            enable_arc_routing=False
        )
        
        assert opts.enable_enhancements is True
        assert opts.enable_layout_optimization is False
        assert opts.enable_arc_routing is False
    
    def test_get_enabled_processors(self):
        """get_enabled_processors() returns correct list."""
        opts = EnhancementOptions(
            enable_layout_optimization=True,
            enable_arc_routing=False,
            enable_metadata_enhancement=True,
            enable_visual_validation=False
        )
        
        enabled = opts.get_enabled_processors()
        assert 'LayoutOptimizer' in enabled
        assert 'ArcRouter' not in enabled
        assert 'MetadataEnhancer' in enabled
        assert 'VisualValidator' not in enabled
    
    def test_get_enabled_processors_none_enabled(self):
        """get_enabled_processors() returns empty if all disabled."""
        opts = EnhancementOptions(
            enable_layout_optimization=False,
            enable_arc_routing=False,
            enable_metadata_enhancement=False,
            enable_visual_validation=False
        )
        
        enabled = opts.get_enabled_processors()
        assert enabled == []
    
    def test_to_dict(self):
        """to_dict() converts to dictionary."""
        opts = EnhancementOptions(
            verbose=True,
            layout_min_spacing=100.0
        )
        
        d = opts.to_dict()
        assert isinstance(d, dict)
        assert d['verbose'] is True
        assert d['layout_min_spacing'] == 100.0
        assert 'enable_enhancements' in d
    
    def test_from_dict(self):
        """from_dict() creates options from dictionary."""
        d = {
            'verbose': True,
            'layout_min_spacing': 100.0,
            'arc_curve_style': 'bezier'
        }
        
        opts = EnhancementOptions.from_dict(d)
        assert opts.verbose is True
        assert opts.layout_min_spacing == 100.0
        assert opts.arc_curve_style == 'bezier'
    
    def test_from_dict_with_extra_keys(self):
        """from_dict() passes extra keys (dataclass ignores them in __init__)."""
        d = {
            'verbose': True
        }
        
        # Should not raise
        opts = EnhancementOptions.from_dict(d)
        assert opts.verbose is True
    
    def test_get_minimal_options(self):
        """get_minimal_options() returns minimal preset."""
        opts = get_minimal_options()
        
        assert opts.enable_enhancements is True
        assert opts.enable_layout_optimization is True
        assert opts.enable_arc_routing is False
        assert opts.enable_metadata_enhancement is False
        assert opts.enable_visual_validation is False
    
    def test_get_standard_options(self):
        """get_standard_options() returns standard preset."""
        opts = get_standard_options()
        
        assert opts.enable_enhancements is True
        assert opts.enable_layout_optimization is True
        assert opts.enable_arc_routing is True
        assert opts.enable_metadata_enhancement is True
        assert opts.enable_visual_validation is False
    
    def test_get_maximum_options(self):
        """get_maximum_options() returns maximum preset."""
        opts = get_maximum_options(image_url="https://example.com/pathway.png")
        
        assert opts.enable_enhancements is True
        assert opts.enable_layout_optimization is True
        assert opts.enable_arc_routing is True
        assert opts.enable_metadata_enhancement is True
        assert opts.enable_visual_validation is True
        assert opts.verbose is True
        assert opts.validation_image_url == "https://example.com/pathway.png"
