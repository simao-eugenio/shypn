"""Test suite for PetriNetBuilder - Fluent interface for complete model construction.

Tests cover:
- Adding pre-built objects (places, transitions, arcs)
- Fluent nested construction with builders
- Connection methods
- Module/compartment management
- SHPN signal hierarchy (layers, acyclicity, commitment thresholds)
- Validation and integrity checking
- Metadata and configuration
- Complex real-world models
"""

import pytest
from shypn.builders.petri_net_builder import PetriNetBuilder
from shypn.builders.place_builder import PlaceBuilder
from shypn.builders.transition_builder import TransitionBuilder
from shypn.builders.arc_builder import ArcBuilder
from shypn.data.canvas.document_model import DocumentModel
from shypn.netobjs import Place, Transition, Arc
from shypn.netobjs.signal_flow_arc import SignalFlowArc


# ========== Test Basic Model Construction ==========

class TestPetriNetBuilderBasics:
    """Test basic model construction functionality."""
    
    def test_empty_model(self):
        """Test creating empty model."""
        model = PetriNetBuilder().build()
        
        assert isinstance(model, DocumentModel)
        assert len(model.places) == 0
        assert len(model.transitions) == 0
        assert len(model.arcs) == 0
    
    def test_add_single_place(self):
        """Test adding a single place."""
        place = PlaceBuilder("P1").at_position(100, 100).build()
        model = (PetriNetBuilder()
                 .add_place(place)
                 .build())
        
        assert len(model.places) == 1
        assert model.places[0] == place
    
    def test_add_single_transition(self):
        """Test adding a single transition."""
        transition = TransitionBuilder("T1").at_position(200, 200).build()
        model = (PetriNetBuilder()
                 .add_transition(transition)
                 .build())
        
        assert len(model.transitions) == 1
        assert model.transitions[0] == transition
    
    def test_add_single_arc(self):
        """Test adding place, transition, and arc."""
        place = PlaceBuilder("P1").at_position(100, 100).build()
        transition = TransitionBuilder("T1").at_position(200, 200).build()
        arc = (ArcBuilder()
               .from_place(place)
               .to_transition(transition)
               .build())
        
        model = (PetriNetBuilder()
                 .add_place(place)
                 .add_transition(transition)
                 .add_arc(arc)
                 .build())
        
        assert len(model.places) == 1
        assert len(model.transitions) == 1
        assert len(model.arcs) == 1
    
    def test_add_multiple_places(self):
        """Test adding multiple places at once."""
        places = [
            PlaceBuilder(f"P{i}").at_position(i*50, 100).build()
            for i in range(3)
        ]
        
        model = (PetriNetBuilder()
                 .add_places(places)
                 .build())
        
        assert len(model.places) == 3
    
    def test_model_with_name(self):
        """Test model with name."""
        model = (PetriNetBuilder("TestModel")
                 .build())
        
        assert model.metadata.get('name') == "TestModel"


# ========== Test Connection Methods ==========

class TestPetriNetBuilderConnections:
    """Test connection convenience methods."""
    
    def test_connect_by_id(self):
        """Test connecting objects by ID."""
        place = PlaceBuilder("P1").at_position(100, 100).build()
        transition = TransitionBuilder("T1").at_position(200, 200).build()
        
        model = (PetriNetBuilder()
                 .add_place(place)
                 .add_transition(transition)
                 .connect("P1", "T1", weight=2.0)
                 .build())
        
        assert len(model.arcs) == 1
        assert model.arcs[0].weight == 2.0
    
    def test_connect_last_to_last(self):
        """Test connecting last added objects."""
        place = PlaceBuilder("P1").at_position(100, 100).build()
        transition = TransitionBuilder("T1").at_position(200, 200).build()
        
        model = (PetriNetBuilder()
                 .add_place(place)
                 .add_transition(transition)
                 .connect_last_to_last(weight=3.0)
                 .build())
        
        assert len(model.arcs) == 1
        assert model.arcs[0].weight == 3.0
    
    def test_connect_signal_flow_by_id(self):
        """Test creating signal flow arc by ID."""
        place = PlaceBuilder("ATP").at_position(100, 100).as_signal_place("ENERGY").build()
        transition = TransitionBuilder("commit").at_position(200, 200).build()
        
        model = (PetriNetBuilder()
                 .add_place(place)
                 .add_transition(transition)
                 .connect("ATP", "commit", arc_type="signal_flow", signal_weight=0.17)
                 .build())
        
        assert len(model.arcs) == 1
        assert isinstance(model.arcs[0], SignalFlowArc)
    
    def test_connect_last_with_signal_weight(self):
        """Test connecting with signal weight auto-detects signal flow."""
        place = PlaceBuilder("P_signal").at_position(100, 100).as_signal_place("ENERGY").build()
        transition = TransitionBuilder("T1").at_position(200, 200).build()
        
        model = (PetriNetBuilder()
                 .add_place(place)
                 .add_transition(transition)
                 .connect_last_to_last(signal_weight=0.5)
                 .build())
        
        assert len(model.arcs) == 1
        assert isinstance(model.arcs[0], SignalFlowArc)


# ========== Test Module Management ==========

class TestPetriNetBuilderModules:
    """Test module/compartment management."""
    
    def test_create_module(self):
        """Test creating a module."""
        model = (PetriNetBuilder()
                 .create_module("Cytoplasm")
                 .build())
        
        assert len(model.modules) == 1
        module = model.get_module_by_name("Cytoplasm")
        assert module is not None
        assert module.name == "Cytoplasm"
    
    def test_assign_place_to_module(self):
        """Test assigning place to module."""
        place = PlaceBuilder("P1").at_position(100, 100).build()
        
        builder = (PetriNetBuilder()
                   .create_module("Cytoplasm")
                   .add_place(place))
        
        module = builder._model.get_module_by_name("Cytoplasm")
        builder.assign_to_module(place, module.module_id)
        
        model = builder.build()
        
        assert place.module_id == module.module_id
        assert place in module.places
    
    def test_assign_transition_to_module(self):
        """Test assigning transition to module."""
        transition = TransitionBuilder("T1").at_position(200, 200).build()
        
        builder = (PetriNetBuilder()
                   .create_module("Mitochondria")
                   .add_transition(transition))
        
        module = builder._model.get_module_by_name("Mitochondria")
        builder.assign_to_module(transition, module.module_id)
        
        model = builder.build()
        
        assert transition.module_id == module.module_id
        assert transition in module.transitions


# ========== Test SHPN Signal Hierarchy ==========

class TestPetriNetBuilderSHPN:
    """Test SHPN signal hierarchy functionality."""
    
    def test_compute_layers_simple(self):
        """Test layer computation for simple 2-layer hierarchy."""
        # Layer 0: ATP (metabolism)
        atp = PlaceBuilder("ATP").at_position(100, 100).as_signal_place("ENERGY").build()
        atp.layer = 0  # Initialize
        
        # Layer 1: CodY (sensing)
        cody = PlaceBuilder("CodY").at_position(200, 100).as_signal_place("REGULATORY").build()
        cody.layer = 0  # Will be updated
        
        # Transition between layers
        sense = TransitionBuilder("sense").at_position(150, 100).build()
        
        # Signal flow arcs
        arc1 = (ArcBuilder()
                .from_place(atp)
                .to_transition(sense)
                .as_signal_flow()
                .build())
        
        arc2 = (ArcBuilder()
                .from_transition(sense)
                .to_place(cody)
                .as_signal_flow()
                .build())
        
        builder = (PetriNetBuilder()
                   .add_place(atp)
                   .add_place(cody)
                   .add_transition(sense)
                   .add_arc(arc1)
                   .add_arc(arc2))
        
        layers = builder.compute_layers()
        
        assert layers['ATP'] == 0
        assert layers['CodY'] == 1
    
    def test_validate_acyclicity_pass(self):
        """Test acyclicity validation passes for DAG."""
        atp = PlaceBuilder("ATP").at_position(100, 100).as_signal_place("ENERGY").build()
        atp.layer = 0
        
        t = TransitionBuilder().at_position(150, 100).build()
        
        arc = (ArcBuilder()
               .from_place(atp)
               .to_transition(t)
               .as_signal_flow()
               .build())
        
        builder = (PetriNetBuilder()
                   .add_place(atp)
                   .add_transition(t)
                   .add_arc(arc))
        
        assert builder.validate_acyclicity() is True
    
    def test_compute_commitment_thresholds(self):
        """Test commitment threshold computation M_commit = θ + W_s."""
        # B. subtilis example
        atp = PlaceBuilder("ATP").at_position(100, 100).as_signal_place("ENERGY").build()
        
        commit = (TransitionBuilder("commit")
                  .at_position(200, 200)
                  .with_id("commit")  # Explicitly set ID
                  .with_enablement_threshold(2.21)  # θ(commit) = 2.21 mM
                  .build())
        
        arc = (ArcBuilder()
               .from_place(atp)
               .to_transition(commit)
               .as_signal_flow()
               .with_signal_weight(0.17)  # W_s = 0.17 mM
               .build())
        
        builder = (PetriNetBuilder()
                   .add_place(atp)
                   .add_transition(commit)
                   .add_arc(arc))
        
        thresholds = builder.compute_commitment_thresholds()
        
        assert ('ATP', 'commit') in thresholds
        assert abs(thresholds[('ATP', 'commit')] - 2.38) < 0.01  # θ + W_s = 2.21 + 0.17 = 2.38


# ========== Test Validation ==========

class TestPetriNetBuilderValidation:
    """Test validation and integrity checking."""
    
    def test_validate_integrity_pass(self):
        """Test integrity validation passes for valid model."""
        place = PlaceBuilder("P1").at_position(100, 100).build()
        transition = TransitionBuilder("T1").at_position(200, 200).build()
        arc = (ArcBuilder()
               .from_place(place)
               .to_transition(transition)
               .build())
        
        builder = (PetriNetBuilder()
                   .add_place(place)
                   .add_transition(transition)
                   .add_arc(arc))
        
        assert builder.validate_integrity() is True
    
    def test_validate_integrity_fail_missing_source(self):
        """Test integrity validation fails for arc with missing source."""
        place = PlaceBuilder("P1").at_position(100, 100).build()
        transition = TransitionBuilder("T1").at_position(200, 200).build()
        orphan_transition = TransitionBuilder("T_orphan").at_position(300, 300).build()
        
        arc = (ArcBuilder()
               .from_place(place)
               .to_transition(orphan_transition)  # Not in model!
               .build())
        
        builder = (PetriNetBuilder()
                   .add_place(place)
                   .add_transition(transition)
                   .add_arc(arc))
        
        with pytest.raises(ValueError, match="not in model"):
            builder.validate_integrity()


# ========== Test Metadata and Configuration ==========

class TestPetriNetBuilderMetadata:
    """Test metadata and configuration."""
    
    def test_with_metadata(self):
        """Test setting metadata."""
        model = (PetriNetBuilder()
                 .with_metadata(
                     source="KEGG",
                     pathway="Glycolysis",
                     organism="E. coli"
                 )
                 .build())
        
        assert model.metadata["source"] == "KEGG"
        assert model.metadata["pathway"] == "Glycolysis"
        assert model.metadata["organism"] == "E. coli"
    
    def test_with_name_and_metadata(self):
        """Test setting name and metadata."""
        model = (PetriNetBuilder("EcoliGlycolysis")
                 .with_metadata(organism="E. coli")
                 .build())
        
        assert model.metadata["name"] == "EcoliGlycolysis"
        assert model.metadata["organism"] == "E. coli"


# ========== Test Complex Real-World Examples ==========

class TestPetriNetBuilderComplexExamples:
    """Test complex real-world model construction."""
    
    def test_simple_metabolic_network(self):
        """Test simple metabolic network (Glucose → ATP)."""
        glucose = PlaceBuilder("Glucose").at_position(50, 100).with_tokens(10).build()
        atp = PlaceBuilder("ATP").at_position(150, 100).with_tokens(0).build()
        glycolysis = TransitionBuilder("Glycolysis").at_position(100, 100).as_continuous().build()
        
        arc1 = (ArcBuilder()
                .from_place(glucose)
                .to_transition(glycolysis)
                .with_weight(1)
                .build())
        
        arc2 = (ArcBuilder()
                .from_transition(glycolysis)
                .to_place(atp)
                .with_weight(2)  # 1 glucose → 2 ATP
                .build())
        
        model = (PetriNetBuilder("SimpleMetabolism")
                 .add_places([glucose, atp])
                 .add_transition(glycolysis)
                 .add_arcs([arc1, arc2])
                 .with_metadata(pathway="Glycolysis")
                 .build())
        
        assert len(model.places) == 2
        assert len(model.transitions) == 1
        assert len(model.arcs) == 2
        assert model.metadata["name"] == "SimpleMetabolism"
    
    def test_bacillus_subtilis_sporulation_hierarchy(self):
        """Test B. subtilis sporulation 4-layer signal hierarchy.
        
        Layer 0: ATP (metabolism)
        Layer 1: CodY (sensing)
        Layer 2: Spo0A (integration)
        Layer 3: sigmaF (execution)
        """
        # Layer 0: ATP
        atp = PlaceBuilder("ATP").at_position(100, 100).with_tokens(100).as_signal_place("ENERGY").build()
        atp.layer = 0
        
        # Layer 1: CodY
        cody = PlaceBuilder("CodY").at_position(200, 100).with_tokens(0).as_signal_place("REGULATORY").build()
        cody.layer = 0  # Will be computed
        
        # Layer 2: Spo0A
        spo0a = PlaceBuilder("Spo0A").at_position(300, 100).with_tokens(0).as_signal_place("REGULATORY").build()
        spo0a.layer = 0
        
        # Transitions
        sense = TransitionBuilder("sense").at_position(150, 100).as_continuous().build()
        integrate = TransitionBuilder("integrate").at_position(250, 100).as_continuous().build()
        
        # Signal flow arcs
        signal_arcs = [
            ArcBuilder().from_place(atp).to_transition(sense).as_signal_flow().with_signal_weight(0.1).build(),
            ArcBuilder().from_transition(sense).to_place(cody).as_signal_flow().build(),
            ArcBuilder().from_place(cody).to_transition(integrate).as_signal_flow().with_signal_weight(0.2).build(),
            ArcBuilder().from_transition(integrate).to_place(spo0a).as_signal_flow().build(),
        ]
        
        builder = (PetriNetBuilder("BacillusSporulation")
                   .add_places([atp, cody, spo0a])
                   .add_transitions([sense, integrate])
                   .add_arcs(signal_arcs)
                   .with_metadata(
                       organism="Bacillus subtilis",
                       process="sporulation",
                       reference="Veening et al. 2008"
                   ))
        
        # Compute layers
        layers = builder.compute_layers()
        
        assert layers['ATP'] == 0
        assert layers['CodY'] == 1
        assert layers['Spo0A'] == 2
        
        # Validate acyclicity
        assert builder.validate_acyclicity() is True
        
        model = builder.build()
        assert model.metadata["organism"] == "Bacillus subtilis"
    
    def test_enzyme_catalysis_with_test_arc(self):
        """Test enzyme catalysis model with test arc."""
        substrate = PlaceBuilder("Substrate").at_position(50, 100).with_tokens(100).build()
        enzyme = PlaceBuilder("Enzyme").at_position(100, 50).with_tokens(1).build()
        product = PlaceBuilder("Product").at_position(150, 100).with_tokens(0).build()
        
        reaction = (TransitionBuilder("Catalysis")
                    .at_position(100, 100)
                    .as_continuous()
                    .with_rate_function("k_cat * [Enzyme] * [Substrate] / (K_m + [Substrate])")
                    .build())
        
        # Normal arcs for mass transfer
        consume = ArcBuilder().from_place(substrate).to_transition(reaction).with_weight(1).build()
        produce = ArcBuilder().from_transition(reaction).to_place(product).with_weight(1).build()
        
        # Test arc for enzyme (non-consuming catalyst)
        catalyze = ArcBuilder().from_place(enzyme).to_transition(reaction).as_test().build()
        
        model = (PetriNetBuilder("EnzymeCatalysis")
                 .add_places([substrate, enzyme, product])
                 .add_transition(reaction)
                 .add_arcs([consume, produce, catalyze])
                 .with_metadata(reaction_type="enzyme_catalysis")
                 .build())
        
        assert len(model.places) == 3
        assert len(model.arcs) == 3
    
    def test_multi_compartment_model(self):
        """Test multi-compartment model with modules."""
        # Cytoplasm compartment
        glucose_cyt = PlaceBuilder("Glucose_cyt").at_position(100, 100).build()
        
        # Mitochondria compartment
        atp_mito = PlaceBuilder("ATP_mito").at_position(100, 200).build()
        
        # Transitions
        transport = TransitionBuilder("Transport").at_position(100, 150).build()
        
        builder = (PetriNetBuilder("MultiCompartment")
                   .create_module("Cytoplasm", compartment_id="c")
                   .create_module("Mitochondria", compartment_id="m")
                   .add_place(glucose_cyt)
                   .add_place(atp_mito)
                   .add_transition(transport))
        
        # Assign to modules
        cyt_module = builder._model.get_module_by_name("Cytoplasm")
        mito_module = builder._model.get_module_by_name("Mitochondria")
        
        builder.assign_to_module(glucose_cyt, cyt_module.module_id)
        builder.assign_to_module(atp_mito, mito_module.module_id)
        
        model = builder.build()
        
        assert len(model.modules) == 2
        assert glucose_cyt.module_id == cyt_module.module_id
        assert atp_mito.module_id == mito_module.module_id


# ========== Test Repr ==========

class TestPetriNetBuilderRepr:
    """Test __repr__ for debugging."""
    
    def test_repr_empty(self):
        """Test repr for empty builder."""
        builder = PetriNetBuilder()
        repr_str = repr(builder)
        
        assert "places=0" in repr_str
        assert "transitions=0" in repr_str
        assert "arcs=0" in repr_str
    
    def test_repr_with_objects(self):
        """Test repr with objects."""
        place = PlaceBuilder("P1").at_position(100, 100).build()
        transition = TransitionBuilder("T1").at_position(200, 200).build()
        
        builder = (PetriNetBuilder()
                   .add_place(place)
                   .add_transition(transition))
        
        repr_str = repr(builder)
        
        assert "places=1" in repr_str
        assert "transitions=1" in repr_str


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
