"""Test suite for PlaceBuilder - Fluent interface for Place construction.

Tests cover:
- Basic place creation with minimal properties
- Signal place designation (SHPN formalism)
- Hierarchical layer assignment (SHPN)
- Spatial properties
- Regulatory places
- Module and compartment assignment
- Custom properties and metadata
- Validation and error handling
"""

import pytest
from shypn.builders.place_builder import PlaceBuilder
from shypn.netobjs.place import Place, BoundaryType
from shypn.netobjs.signal_type import SignalType


class TestPlaceBuilderBasics:
    """Test basic place construction functionality."""
    
    def test_minimal_place(self):
        """Test creating place with minimal configuration."""
        place = PlaceBuilder("P1").build()
        
        assert place.id == "P1"
        assert place.name == "P1"
        assert place.tokens == 0
        assert place.x == 0.0
        assert place.y == 0.0
        assert not place.is_signal_place
    
    def test_place_with_tokens(self):
        """Test place with initial tokens."""
        place = (PlaceBuilder("glucose")
                 .with_tokens(50)
                 .build())
        
        assert place.tokens == 50
        assert place.initial_marking == 50  # Should match tokens
    
    def test_place_at_position(self):
        """Test place positioning."""
        place = (PlaceBuilder("P1")
                 .at_position(150.5, 200.3)
                 .build())
        
        assert place.x == 150.5
        assert place.y == 200.3
    
    def test_place_with_label(self):
        """Test place with custom label."""
        place = (PlaceBuilder("ATP")
                 .with_label("ATP Pool")
                 .build())
        
        assert place.label == "ATP Pool"
    
    def test_place_with_capacity(self):
        """Test place with token capacity."""
        place = (PlaceBuilder("P1")
                 .with_capacity(1000)
                 .build())
        
        assert place.capacity == 1000
    
    def test_negative_tokens_raises_error(self):
        """Test that negative token count raises ValueError."""
        with pytest.raises(ValueError, match="non-negative"):
            PlaceBuilder("P1").with_tokens(-5).build()


class TestPlaceBuilderSignalPlaces:
    """Test SHPN signal place functionality."""
    
    def test_signal_place_energy_type(self):
        """Test signal place with ENERGY type."""
        place = (PlaceBuilder("ATP")
                 .as_signal_place("ENERGY")
                 .build())
        
        assert place.is_signal_place is True
        assert place.signal_type == SignalType.ENERGY
    
    def test_signal_place_spatial_type(self):
        """Test signal place with SPATIAL type."""
        place = (PlaceBuilder("calcium")
                 .as_signal_place("SPATIAL")
                 .build())
        
        assert place.is_signal_place is True
        assert place.signal_type == SignalType.SPATIAL
    
    def test_signal_place_quorum_type(self):
        """Test signal place with QUORUM type."""
        place = (PlaceBuilder("cAMP")
                 .as_signal_place("QUORUM")
                 .build())
        
        assert place.is_signal_place is True
        assert place.signal_type == SignalType.QUORUM
    
    def test_signal_place_regulatory_type(self):
        """Test signal place with REGULATORY type."""
        place = (PlaceBuilder("Spo0A_P")
                 .as_signal_place("REGULATORY")
                 .build())
        
        assert place.is_signal_place is True
        assert place.signal_type == SignalType.REGULATORY
    
    def test_signal_place_no_type(self):
        """Test signal place without explicit type."""
        place = (PlaceBuilder("signal")
                 .as_signal_place()
                 .build())
        
        assert place.is_signal_place is True
        assert place.signal_type is None  # Type not set
    
    def test_invalid_signal_type_raises_error(self):
        """Test that invalid signal type raises ValueError."""
        with pytest.raises(ValueError, match="Invalid signal_type"):
            PlaceBuilder("P1").as_signal_place("INVALID_TYPE").build()
    
    def test_signal_place_case_insensitive(self):
        """Test signal type is case-insensitive."""
        place1 = PlaceBuilder("P1").as_signal_place("energy").build()
        place2 = PlaceBuilder("P2").as_signal_place("ENERGY").build()
        place3 = PlaceBuilder("P3").as_signal_place("Energy").build()
        
        assert place1.signal_type == SignalType.ENERGY
        assert place2.signal_type == SignalType.ENERGY
        assert place3.signal_type == SignalType.ENERGY


class TestPlaceBuilderSHPNLayers:
    """Test SHPN hierarchical layer assignment."""
    
    def test_layer_0_metabolism(self):
        """Test Layer 0 (metabolism) signal place."""
        place = (PlaceBuilder("ATP")
                 .as_signal_place("ENERGY")
                 .with_layer(0)
                 .build())
        
        assert place.layer == 0
    
    def test_layer_1_sensing(self):
        """Test Layer 1 (sensing) signal place."""
        place = (PlaceBuilder("CodY_active")
                 .as_signal_place("REGULATORY")
                 .with_layer(1)
                 .build())
        
        assert place.layer == 1
    
    def test_layer_2_integration(self):
        """Test Layer 2 (integration) signal place."""
        place = (PlaceBuilder("Spo0A_P")
                 .as_signal_place("REGULATORY")
                 .with_layer(2)
                 .build())
        
        assert place.layer == 2
    
    def test_layer_3_execution(self):
        """Test Layer 3 (execution) signal place."""
        place = (PlaceBuilder("sigmaF")
                 .as_signal_place("REGULATORY")
                 .with_layer(3)
                 .build())
        
        assert place.layer == 3
    
    def test_layer_without_signal_place(self):
        """Test setting layer on non-signal place (layer only set if signal place)."""
        place = (PlaceBuilder("P1")
                 .with_layer(2)
                 .build())
        
        # Layer is only stored for signal places in the current implementation
        # Non-signal places don't have layer attribute
        assert not place.is_signal_place
        assert not hasattr(place, 'layer') or getattr(place, 'layer', None) == 2
    
    def test_negative_layer_raises_error(self):
        """Test that negative layer raises ValueError."""
        with pytest.raises(ValueError, match="non-negative"):
            PlaceBuilder("P1").with_layer(-1).build()


class TestPlaceBuilderSpatialProperties:
    """Test spatial properties for SPATIAL signal places."""
    
    def test_diffusion_coefficient(self):
        """Test setting diffusion coefficient."""
        place = (PlaceBuilder("calcium")
                 .as_signal_place("SPATIAL")
                 .with_spatial_properties(
                     diffusion_coefficient=220.0
                 )
                 .build())
        
        assert place.diffusion_coefficient == 220.0
    
    def test_compartment_volume(self):
        """Test setting compartment volume."""
        place = (PlaceBuilder("calcium")
                 .as_signal_place("SPATIAL")
                 .with_spatial_properties(
                     volume=1.5
                 )
                 .build())
        
        assert place.compartment_volume == 1.5
    
    def test_boundary_type_permeable(self):
        """Test permeable boundary type."""
        place = (PlaceBuilder("ion")
                 .as_signal_place("SPATIAL")
                 .with_spatial_properties(
                     boundary_type="permeable"
                 )
                 .build())
        
        assert place.boundary_type == BoundaryType.PERMEABLE
    
    def test_boundary_type_selective(self):
        """Test selective boundary type."""
        place = (PlaceBuilder("ion")
                 .as_signal_place("SPATIAL")
                 .with_spatial_properties(
                     boundary_type="selective"
                 )
                 .build())
        
        assert place.boundary_type == BoundaryType.SELECTIVE
    
    def test_boundary_type_impermeable(self):
        """Test impermeable boundary type."""
        place = (PlaceBuilder("ion")
                 .as_signal_place("SPATIAL")
                 .with_spatial_properties(
                     boundary_type="impermeable"
                 )
                 .build())
        
        assert place.boundary_type == BoundaryType.IMPERMEABLE
    
    def test_spatial_position(self):
        """Test 3D spatial position."""
        place = (PlaceBuilder("calcium")
                 .as_signal_place("SPATIAL")
                 .with_spatial_properties(
                     position=(1.0, 2.5, 3.2)
                 )
                 .build())
        
        assert place.spatial_position == (1.0, 2.5, 3.2)
    
    def test_spatial_compartment(self):
        """Test compartment assignment via spatial properties."""
        place = (PlaceBuilder("ATP")
                 .as_signal_place("ENERGY")
                 .with_spatial_properties(
                     compartment="mitochondria"
                 )
                 .build())
        
        assert place.properties.get("compartment") == "mitochondria"
    
    def test_gradient_vector(self):
        """Test concentration gradient vector."""
        place = (PlaceBuilder("morphogen")
                 .as_signal_place("SPATIAL")
                 .with_gradient(1.0, 0.5, 0.0)
                 .build())
        
        assert place.gradient_vector == (1.0, 0.5, 0.0)
    
    def test_neighbor_compartments(self):
        """Test adjacent compartment specification."""
        place = (PlaceBuilder("diffusible")
                 .as_signal_place("SPATIAL")
                 .with_neighbors("C_left", "C_right")
                 .build())
        
        assert place.neighbor_compartments == ["C_left", "C_right"]
    
    def test_invalid_spatial_position_raises_error(self):
        """Test that invalid position tuple raises ValueError."""
        with pytest.raises(ValueError, match="must be \\(x, y, z\\) tuple"):
            (PlaceBuilder("P1")
             .with_spatial_properties(position=(1.0, 2.0))  # Missing z
             .build())


class TestPlaceBuilderRegulatoryPlaces:
    """Test regulatory place functionality."""
    
    def test_regulatory_place(self):
        """Test marking place as regulatory."""
        place = (PlaceBuilder("spo0A_gene")
                 .as_regulatory_place()
                 .with_tokens(1)  # 1 gene copy
                 .build())
        
        assert place.is_regulatory_place is True
        assert place.tokens == 1


class TestPlaceBuilderModulesAndCompartments:
    """Test module and compartment assignment."""
    
    def test_module_assignment(self):
        """Test assigning place to module."""
        place = (PlaceBuilder("ATP")
                 .with_module("M_mitochondria")
                 .build())
        
        assert place.module_id == "M_mitochondria"
    
    def test_compartment_place(self):
        """Test marking as compartment place."""
        place = (PlaceBuilder("extracellular_glucose")
                 .in_compartment()
                 .build())
        
        assert place.is_compartment_place is True


class TestPlaceBuilderCustomPropertiesAndMetadata:
    """Test custom properties and metadata."""
    
    def test_custom_property(self):
        """Test setting custom property."""
        place = (PlaceBuilder("enzyme")
                 .with_property("km", 5.0)
                 .with_property("vmax", 10.0)
                 .build())
        
        assert place.properties["km"] == 5.0
        assert place.properties["vmax"] == 10.0
    
    def test_metadata(self):
        """Test setting metadata."""
        place = (PlaceBuilder("ATP")
                 .with_metadata(
                     source="KEGG",
                     kegg_id="C00002",
                     description="Adenosine triphosphate"
                 )
                 .build())
        
        assert place.metadata["source"] == "KEGG"
        assert place.metadata["kegg_id"] == "C00002"
        assert place.metadata["description"] == "Adenosine triphosphate"


class TestPlaceBuilderComplexExamples:
    """Test complex real-world examples combining multiple features."""
    
    def test_bacillus_subtilis_atp_signal(self):
        """Test B. subtilis ATP signal place (Layer 0 metabolism).
        
        This is the canonical SHPN example from the formalism:
        - ATP as energy signal at Layer 0
        - Participates in glycolysis (normal arcs)
        - Gates sporulation commitment (signal flow arc with θ=2.21 mM)
        """
        atp = (PlaceBuilder("ATP")
               .with_tokens(100)  # 100 mM initial
               .at_position(150, 200)
               .as_signal_place("ENERGY")
               .with_layer(0)  # Metabolic layer
               .with_label("ATP Pool")
               .with_metadata(
                   source="KEGG",
                   kegg_id="C00002",
                   commitment_threshold=2.38  # M_commit = θ + W_s = 2.21 + 0.17
               )
               .build())
        
        assert atp.id == "ATP"
        assert atp.tokens == 100
        assert atp.is_signal_place
        assert atp.signal_type == SignalType.ENERGY
        assert atp.layer == 0
        assert atp.label == "ATP Pool"
        assert atp.metadata["commitment_threshold"] == 2.38
    
    def test_bacillus_subtilis_cody_signal(self):
        """Test B. subtilis CodY sensor (Layer 1 sensing)."""
        cody = (PlaceBuilder("CodY_active")
                .with_tokens(0)  # Initially inactive
                .at_position(200, 250)
                .as_signal_place("REGULATORY")
                .with_layer(1)  # Sensing layer
                .with_label("CodY (active)")
                .build())
        
        assert cody.is_signal_place
        assert cody.signal_type == SignalType.REGULATORY
        assert cody.layer == 1
    
    def test_bacillus_subtilis_spo0a_signal(self):
        """Test B. subtilis Spo0A~P integration signal (Layer 2)."""
        spo0a = (PlaceBuilder("Spo0A_P")
                 .with_tokens(0)
                 .at_position(250, 300)
                 .as_signal_place("REGULATORY")
                 .with_layer(2)  # Integration layer
                 .with_label("Spo0A~P")
                 .build())
        
        assert spo0a.is_signal_place
        assert spo0a.layer == 2
    
    def test_calcium_spatial_signal_with_diffusion(self):
        """Test calcium SPATIAL signal with full diffusion properties."""
        calcium = (PlaceBuilder("calcium")
                   .with_tokens(100)  # 100 nM baseline
                   .at_position(300, 150)
                   .as_signal_place("SPATIAL")
                   .with_layer(0)  # Source layer for spatial gradient
                   .with_spatial_properties(
                       compartment="cytoplasm",
                       volume=1.5,  # fL
                       diffusion_coefficient=220.0,  # μm²/s (Ca²⁺ typical)
                       boundary_type="selective",
                       position=(10.0, 15.0, 5.0)
                   )
                   .with_gradient(1.0, 0.0, 0.0)  # X-direction gradient
                   .with_neighbors("C_ER", "C_mitochondria")
                   .with_label("Ca²⁺")
                   .build())
        
        assert calcium.is_signal_place
        assert calcium.signal_type == SignalType.SPATIAL
        assert calcium.diffusion_coefficient == 220.0
        assert calcium.boundary_type == BoundaryType.SELECTIVE
        assert calcium.gradient_vector == (1.0, 0.0, 0.0)
    
    def test_method_chaining_readability(self):
        """Test that method chaining creates readable, expressive code."""
        place = (PlaceBuilder("example")
                 .with_tokens(50)
                 .at_position(100, 200)
                 .as_signal_place("ENERGY")
                 .with_layer(0)
                 .with_label("Example Signal")
                 .with_metadata(description="Test place")
                 .build())
        
        assert isinstance(place, Place)
        assert place.tokens == 50


class TestPlaceBuilderRepr:
    """Test __repr__ for debugging."""
    
    def test_repr_basic(self):
        """Test repr for basic place."""
        builder = PlaceBuilder("P1").with_tokens(10).at_position(50, 100)
        repr_str = repr(builder)
        
        assert "P1" in repr_str
        assert "10" in repr_str
        assert "50" in repr_str
        assert "100" in repr_str
    
    def test_repr_signal_place(self):
        """Test repr for signal place."""
        builder = (PlaceBuilder("ATP")
                   .as_signal_place("ENERGY")
                   .with_layer(0))
        repr_str = repr(builder)
        
        assert "ATP" in repr_str
        assert "ENERGY" in repr_str
        assert "layer=0" in repr_str


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])

