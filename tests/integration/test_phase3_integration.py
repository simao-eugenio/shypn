"""
Integration Tests - Phase 3 Design Patterns

Tests complete workflows using builders, repositories, and dependency injection
together. These tests verify that all Phase 3 components work correctly when
integrated.

Part of Phase 3.4: Testing & Documentation.
"""

import pytest
import tempfile
import shutil
from pathlib import Path

from shypn.builders import (
    PlaceBuilder,
    ArcBuilder,
    TransitionBuilder,
    PetriNetBuilder,
    SimulationConfigBuilder,
)
from shypn.repositories import (
    ModelRepository,
    SimulationDataRepository,
    SimulationTrajectory,
    BatchResults,
)
from shypn.di import (
    ServiceContainer,
    get_container,
    set_container,
    reset_container,
    register_core_services,
)


# ===== Test Fixtures =====


@pytest.fixture
def workspace_dir():
    """Create temporary workspace directory."""
    temp_dir = tempfile.mkdtemp()
    try:
        yield temp_dir
    finally:
        shutil.rmtree(temp_dir)


@pytest.fixture
def container(workspace_dir):
    """Create fresh container with core services."""
    container = ServiceContainer()
    register_core_services(container, workspace_path=workspace_dir)
    return container


# ===== Workflow 1: Build → Save → Load =====


def test_build_save_load_workflow(workspace_dir):
    """Test complete workflow: Build model → Save to repository → Load from repository."""
    # Step 1: Build a simple model using builders
    place1 = PlaceBuilder('p1').with_label('Substrate').with_tokens(100).build()
    place2 = PlaceBuilder('p2').with_label('Product').with_tokens(0).build()
    
    transition = (TransitionBuilder('t1')
                  .with_label('Reaction')
                  .as_stochastic()
                  .with_rate(0.1)
                  .build())
    
    arc1 = (ArcBuilder()
            .from_place(place1)
            .to_transition(transition)
            .with_weight(1.0)
            .build())
    
    arc2 = (ArcBuilder()
            .from_transition(transition)
            .to_place(place2)
            .with_weight(1.0)
            .build())
    
    model = (PetriNetBuilder()
             .with_name('Simple Reaction')
             .add_place(place1)
             .add_place(place2)
             .add_transition(transition)
             .add_arc(arc1)
             .add_arc(arc2)
             .build())
    
    # Step 2: Save to repository
    repo = ModelRepository(workspace_path=workspace_dir)
    model_id = 'simple_reaction_001'
    model.metadata['id'] = model_id
    repo.save(model)
    
    # Step 3: Load from repository
    loaded_model = repo.get_by_id(model_id)
    
    # Step 4: Verify loaded model
    assert loaded_model is not None
    assert loaded_model.metadata['name'] == 'Simple Reaction'
    assert len(loaded_model.places) == 2
    assert len(loaded_model.transitions) == 1
    assert len(loaded_model.arcs) == 2
    
    # Verify places (IDs may be normalized, find by label)
    assert len(loaded_model.places) == 2
    place_labels = [p.label for p in loaded_model.places]
    assert 'Substrate' in place_labels
    assert 'Product' in place_labels
    
    # Find and verify specific places
    p1 = next(p for p in loaded_model.places if p.label == 'Substrate')
    p2 = next(p for p in loaded_model.places if p.label == 'Product')
    assert p1.tokens == 100
    assert p2.tokens == 0
    
    # Verify transition (check label, ID may be normalized during save/load)
    assert len(loaded_model.transitions) == 1
    assert loaded_model.transitions[0].label == 'Reaction'


def test_build_modify_save_workflow(workspace_dir):
    """Test workflow: Build model → Modify → Save → Load → Verify changes."""
    # Build initial model
    model = (PetriNetBuilder()
             .with_name('Test Model')
             .add_place(PlaceBuilder('p1').with_label('Place 1').build())
             .build())
    
    model.metadata['id'] = 'test_001'
    
    # Save initial version
    repo = ModelRepository(workspace_path=workspace_dir)
    repo.save(model)
    
    # Modify model - add another place directly to model
    place2 = model.create_place(x=100.0, y=200.0, label='Place 2')
    place2.tokens = 50
    
    # Save modified version
    repo.save(model)
    
    # Load and verify
    loaded = repo.get_by_id('test_001')
    assert len(loaded.places) == 2
    
    # Find place2 in list
    p2 = next((p for p in loaded.places if p.label == 'Place 2'), None)
    assert p2 is not None
    assert p2.tokens == 50


# ===== Workflow 2: Configure → Run → Save Results =====


def test_simulation_workflow(workspace_dir):
    """Test workflow: Build model → Save trajectory → Load results."""
    # Build simple model
    model = (PetriNetBuilder()
             .with_name('Decay Model')
             .add_place(PlaceBuilder('molecules').with_tokens(1000).build())
             .add_transition(TransitionBuilder('decay').as_stochastic().with_rate(0.01).build())
             .build())
    
    model.metadata['id'] = 'decay_001'
    
    # Create simulation trajectory (mock data - no actual config needed)
    trajectory = SimulationTrajectory(
        simulation_id='sim_001',
        model_id='decay_001',
        times=[0.0, 10.0, 20.0, 30.0],
        place_data={
            'molecules': [1000, 900, 810, 730]
        },
        transition_data={
            'decay': [100, 90, 80, 0]
        }
    )
    
    # Save trajectory to repository
    sim_repo = SimulationDataRepository(data_path=str(Path(workspace_dir) / 'data'))
    sim_repo.save_trajectory(trajectory)
    
    # Load trajectory
    loaded_trajectory = sim_repo.load_trajectory('sim_001')
    
    # Verify
    assert loaded_trajectory.simulation_id == 'sim_001'
    assert loaded_trajectory.model_id == 'decay_001'
    assert len(loaded_trajectory.times) == 4
    assert loaded_trajectory.place_data['molecules'] == [1000, 900, 810, 730]


def test_batch_results_workflow(workspace_dir):
    """Test workflow: Create batch results → Save → Load → Query statistics."""
    # Create mock batch results
    trajectories = []
    for i in range(3):
        traj = SimulationTrajectory(
            simulation_id=f'replicate_{i:03d}',
            model_id='batch_test',
            times=[0.0, 10.0, 20.0],
            place_data={'p1': [100, 90 + i, 80 + i*2]},
            transition_data={}
        )
        trajectories.append(traj)
    
    batch = BatchResults(
        experiment_id='exp_001',
        model_id='batch_test',
        replicate_count=3,
        trajectories=trajectories,
        statistics={
            'mean_p1': [100.0, 91.0, 82.0],
            'std_p1': [0.0, 0.82, 1.63]
        }
    )
    
    # Save batch results
    sim_repo = SimulationDataRepository(data_path=str(Path(workspace_dir) / 'data'))
    sim_repo.save_batch_results(batch)
    
    # Load batch results
    loaded_batch = sim_repo.load_batch_results('exp_001')
    
    # Verify
    assert loaded_batch.experiment_id == 'exp_001'
    assert loaded_batch.replicate_count == 3
    assert len(loaded_batch.trajectories) == 3
    assert 'mean_p1' in loaded_batch.statistics


# ===== Workflow 3: Dependency Injection Integration =====


def test_dependency_injection_workflow(container, workspace_dir):
    """Test workflow: DI container → Service resolution → Use services together."""
    # Resolve repositories from container
    model_repo = container.get('model_repository')
    sim_repo = container.get('simulation_data_repository')
    
    # Build model using builder classes from container
    ArcBuilderClass = container.get('arc_builder_class')
    PetriNetBuilderClass = container.get('petri_net_builder_class')
    
    # Create model
    model = (PetriNetBuilderClass('DI Test Model')
             .add_place(PlaceBuilder('p1').with_tokens(50).build())
             .add_place(PlaceBuilder('p2').with_tokens(0).build())
             .build())
    
    model.metadata['id'] = 'di_test_001'
    
    # Save using repository from DI
    model_repo.save(model)
    
    # Verify model saved
    assert model_repo.exists('di_test_001')
    
    # Create and save simulation data
    trajectory = SimulationTrajectory(
        simulation_id='di_sim_001',
        model_id='di_test_001',
        times=[0.0, 1.0],
        place_data={'p1': [50, 40], 'p2': [0, 10]},
        transition_data={}
    )
    
    sim_repo.save_trajectory(trajectory)
    
    # Verify trajectory saved
    assert 'di_sim_001' in sim_repo.list_simulations()


def test_global_container_workflow(workspace_dir):
    """Test workflow: Setup global container → Use throughout application."""
    # Setup global container
    reset_container()
    container = get_container()
    register_core_services(container, workspace_path=workspace_dir)
    
    # Use global container from anywhere
    def create_and_save_model():
        """Function that uses global container."""
        repo = get_container().get('model_repository')
        
        model = (PetriNetBuilder()
                 .with_name('Global Container Model')
                 .add_place(PlaceBuilder('p1').build())
                 .build())
        
        model.metadata['id'] = 'global_001'
        repo.save(model)
        return model.metadata['id']
    
    # Call function
    model_id = create_and_save_model()
    
    # Verify from different context
    repo = get_container().get('model_repository')
    assert repo.exists(model_id)
    loaded = repo.get_by_id(model_id)
    assert loaded.metadata['name'] == 'Global Container Model'


# ===== Workflow 4: Complex Model Building =====


def test_complex_model_building_workflow(workspace_dir):
    """Test building a model with signal places and hierarchy."""
    # Build signal-hierarchical model
    signal_place = (PlaceBuilder('signal')
                    .with_label('Signal Molecule')
                    .with_tokens(10)
                    .as_signal_place()
                    .with_layer(1)
                    .build())
    
    substrate = (PlaceBuilder('substrate')
                 .with_label('Substrate')
                 .with_tokens(100)
                 .with_layer(2)
                 .build())
    
    product = (PlaceBuilder('product')
               .with_label('Product')
               .with_tokens(0)
               .with_layer(2)
               .build())
    
    # Transition controlled by signal
    reaction = (TransitionBuilder('reaction')
                .with_label('Signal-Controlled Reaction')
                .as_stochastic()
                .with_rate(0.5)
                .with_enablement_threshold(5.0)  # Requires 5 signal molecules
                .build())
    
    # Signal flow arc
    signal_arc = (ArcBuilder()
                  .from_place(signal_place)
                  .to_transition(reaction)
                  .as_signal_flow()
                  .with_signal_weight(1.0)
                  .build())
    
    # Regular arcs
    substrate_arc = (ArcBuilder()
                     .from_place(substrate)
                     .to_transition(reaction)
                     .with_weight(1.0)
                     .build())
    
    product_arc = (ArcBuilder()
                   .from_transition(reaction)
                   .to_place(product)
                   .with_weight(1.0)
                   .build())
    
    # Build complete model
    builder = (PetriNetBuilder('Signal Hierarchical Model')
             .add_place(signal_place)
             .add_place(substrate)
             .add_place(product)
             .add_transition(reaction)
             .add_arc(signal_arc)
             .add_arc(substrate_arc)
             .add_arc(product_arc))
    
    # Compute layers (returns Dict, not builder)
    layers = builder.compute_layers()
    model = builder.build()
    
    # Verify SHPN model built successfully
    assert model is not None
    assert model.metadata['name'] == 'Signal Hierarchical Model'
    assert len(model.places) == 3
    assert len(model.transitions) == 1
    assert len(model.arcs) == 3
    
    # Save and load
    model.metadata['id'] = 'shpn_001'
    repo = ModelRepository(workspace_path=workspace_dir)
    repo.save(model)
    
    loaded = repo.get_by_id('shpn_001')
    assert loaded.metadata['name'] == 'Signal Hierarchical Model'
    assert len(loaded.places) == 3
    assert len(loaded.arcs) == 3


# ===== Workflow 5: Repository Query Integration =====


def test_repository_query_workflow(workspace_dir):
    """Test workflow: Create multiple models → Query with filters → Get results."""
    repo = ModelRepository(workspace_path=workspace_dir)
    
    # Create several models with different characteristics
    models = [
        (PetriNetBuilder('Small Model')
         .add_place(PlaceBuilder('p1').build())
         .add_place(PlaceBuilder('p2').build())
         .build()),
        
        (PetriNetBuilder('Large Model')
         .add_place(PlaceBuilder('p1').build())
         .add_place(PlaceBuilder('p2').build())
         .add_place(PlaceBuilder('p3').build())
         .add_place(PlaceBuilder('p4').build())
         .add_place(PlaceBuilder('p5').build())
         .build()),
        
        (PetriNetBuilder('Signal Model')
         .add_place(PlaceBuilder('sig').as_signal_place().build())
         .add_place(PlaceBuilder('reg').build())
         .build()),
    ]
    
    # Save all models
    for i, model in enumerate(models):
        model.metadata['id'] = f'query_test_{i:03d}'
        repo.save(model)
    
    # Query: Find models with exactly 2 places
    from shypn.repositories import ModelQuery
    
    query = ModelQuery().with_place_count(min_count=2, max_count=2)
    results = repo.search(query)
    
    # Should find 'Small Model' and 'Signal Model'
    assert len(results) == 2
    names = [m.metadata['name'] for m in results]
    assert 'Small Model' in names
    assert 'Signal Model' in names
    
    # Query: Find models with signal places
    query_signal = ModelQuery().with_signal_places(has_signal_places=True)
    signal_results = repo.search(query_signal)
    
    assert len(signal_results) == 1
    assert signal_results[0].metadata['name'] == 'Signal Model'


# ===== Workflow 6: End-to-End Application Simulation =====


def test_full_application_workflow(workspace_dir):
    """
    Test complete application workflow:
    1. Setup DI container
    2. Build model with builders
    3. Save model to repository
    4. Configure simulation
    5. Create simulation results
    6. Save results to repository
    7. Query and analyze
    """
    # Step 1: Setup DI
    container = ServiceContainer()
    register_core_services(container, workspace_path=workspace_dir)
    
    # Step 2: Build model
    model = (PetriNetBuilder('Enzyme Kinetics')
             .add_place(PlaceBuilder('E').with_label('Enzyme').with_tokens(10).build())
             .add_place(PlaceBuilder('S').with_label('Substrate').with_tokens(100).build())
             .add_place(PlaceBuilder('ES').with_label('Complex').with_tokens(0).build())
             .add_place(PlaceBuilder('P').with_label('Product').with_tokens(0).build())
             .add_transition(TransitionBuilder('bind').as_stochastic().with_rate(0.1).build())
             .add_transition(TransitionBuilder('catalyze').as_stochastic().with_rate(0.05).build())
             .build())
    
    model.metadata['id'] = 'enzyme_001'
    model.metadata['description'] = 'Simple enzyme kinetics model'
    
    # Step 3: Save model
    model_repo = container.get('model_repository')
    model_repo.save(model)
    
    # Step 4: Configure simulation (simplified - seed set separately if needed)
    config = (SimulationConfigBuilder()
              .with_duration(50.0)
              .with_manual_dt(0.5)
              .build())
    
    # Step 5: Create simulation results (mock)
    trajectory = SimulationTrajectory(
        simulation_id='enzyme_sim_001',
        model_id='enzyme_001',
        times=[0.0, 10.0, 20.0, 30.0, 40.0, 50.0],
        place_data={
            'E': [10, 8, 9, 9, 10, 10],
            'S': [100, 70, 45, 25, 10, 2],
            'ES': [0, 2, 1, 1, 0, 0],
            'P': [0, 28, 54, 74, 90, 98]
        },
        transition_data={
            'bind': [0, 30, 25, 20, 10, 2],
            'catalyze': [0, 28, 26, 21, 10, 2]
        },
        metadata={'config': config}
    )
    
    # Step 6: Save results
    sim_repo = container.get('simulation_data_repository')
    sim_repo.save_trajectory(trajectory)
    
    # Step 7: Query and analyze
    # Load model
    loaded_model = model_repo.get_by_id('enzyme_001')
    assert loaded_model.metadata['name'] == 'Enzyme Kinetics'
    
    # Load simulation
    loaded_trajectory = sim_repo.load_trajectory('enzyme_sim_001')
    assert loaded_trajectory.model_id == 'enzyme_001'
    
    # Analyze results
    product_tokens = loaded_trajectory.place_data['P']
    assert product_tokens[0] == 0  # No product initially
    assert product_tokens[-1] == 98  # Product formed at end
    
    # Verify enzyme conservation
    enzyme_total = [
        loaded_trajectory.place_data['E'][i] + loaded_trajectory.place_data['ES'][i]
        for i in range(len(loaded_trajectory.times))
    ]
    assert all(total == 10 for total in enzyme_total)  # Enzyme conserved


# ===== Performance & Error Handling =====


def test_repository_caching_performance(workspace_dir):
    """Test that repository caching improves performance."""
    repo = ModelRepository(workspace_path=workspace_dir, cache_size=10)
    
    # Create and save model
    model = (PetriNetBuilder('Cache Test')
             .add_place(PlaceBuilder('p1').build())
             .build())
    model.metadata['id'] = 'cache_001'
    repo.save(model)
    
    # First load - cache miss
    model1 = repo.get_by_id('cache_001')
    stats1 = repo.get_cache_stats()
    
    # Second load - cache hit
    model2 = repo.get_by_id('cache_001')
    stats2 = repo.get_cache_stats()
    
    # Verify caching worked
    assert stats2['hits'] > stats1['hits']
    assert model1 is model2  # Same instance from cache


def test_error_handling_workflow(workspace_dir):
    """Test error handling in integrated workflows."""
    repo = ModelRepository(workspace_path=workspace_dir)
    
    # Try to load nonexistent model (returns None, not exception)
    result = repo.get_by_id('nonexistent_model')
    assert result is None
    
    # Try to build model with validation
    # Model with only places (no transitions) should build successfully
    model = (PetriNetBuilder('Valid')
             .add_place(PlaceBuilder('p1').build())
             .build())
    
    assert model is not None
    assert model.metadata['name'] == 'Valid'
