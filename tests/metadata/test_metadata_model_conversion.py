"""Test metadata generator with DocumentModel conversion.

Verifies that DocumentModel objects are properly converted to dictionary
format before being passed to metadata sections.

This test addresses the bug where ModelCanvasManager/DocumentModel was
being passed directly to metadata sections, causing AttributeError when
sections tried to call .get() method.
"""

import pytest
from shypn.data.canvas.document_model import DocumentModel
from shypn.metadata import SweepHeaderGenerator
from shypn.metadata.model import ModelMetadata
from shypn.metadata.properties import ParametrizationState
from shypn.builders import PetriNetBuilder


def test_model_metadata_accepts_dict(tmp_path):
    """ModelMetadata.collect() should accept model as dictionary."""
    # Create a temporary model file for hash computation
    model_file = tmp_path / "test_model.shy"
    model_file.write_text('{"version": "2.0"}')
    
    context = {
        'model_path': str(model_file),
        'model': {
            'formalism': 'Signal_Hierarchical_Petri_Net',
            'metadata': {'version': '1.0'},
            'places': [
                {'id': 'P1', 'name': 'Place1', 'initial_marking': 100}
            ],
            'transitions': [
                {'id': 'T1', 'name': 'Trans1'}
            ],
            'arcs': []
        }
    }
    
    section = ModelMetadata()
    section.collect(context)  # Should not raise AttributeError
    
    # Verify fields collected
    assert 'Model_Name' in section._fields
    assert 'N_Places' in section._fields
    assert section._fields['N_Places']['value'] == 1


def test_parametrization_state_accepts_dict():
    """ParametrizationState.collect() should accept model as dictionary."""
    context = {
        'model': {
            'places': [
                {'id': 'P1', 'name': 'ATP', 'initial_marking': 500}
            ],
            'arcs': [
                {'id': 'A1', 'source_id': 'T1', 'target_id': 'P1', 'weight': 1}
            ],
            'transitions': [
                {'id': 'T1', 'name': 'Reaction'}
            ]
        },
        'critical_places': ['P1']
    }
    
    section = ParametrizationState()
    section.collect(context)  # Should not raise AttributeError


def test_document_model_to_dict_conversion(tmp_path):
    """DocumentModel.to_dict() should return format compatible with metadata."""
    # Create document with some objects
    builder = PetriNetBuilder()
    
    builder.create_place("ATP").with_tokens(100).done()
    builder.create_place("ADP").with_tokens(50).done()
    builder.create_transition("Hydrolysis").done()
    
    # Build model
    model = builder.build()
    
    # Convert to dict
    model_dict = model.to_dict()
    
    # Verify it has expected structure
    assert 'places' in model_dict
    assert 'transitions' in model_dict
    assert 'arcs' in model_dict
    assert 'metadata' in model_dict
    
    # Verify places are dicts, not objects
    assert len(model_dict['places']) == 2
    assert isinstance(model_dict['places'][0], dict)
    assert 'id' in model_dict['places'][0]
    
    # Verify this format works with metadata
    model_file = tmp_path / "test.shy"
    model_file.write_text('{"version": "2.0"}')
    
    context = {
        'model_path': str(model_file),
        'model': model_dict
    }
    
    section = ModelMetadata()
    section.collect(context)  # Should not raise AttributeError
    
    assert section._fields['N_Places']['value'] == 2
    assert section._fields['N_Transitions']['value'] == 1


def test_sweep_header_generator_with_document_model_dict(tmp_path):
    """SweepHeaderGenerator should work with DocumentModel.to_dict()."""
    # Create document
    builder = PetriNetBuilder()
    
    builder.create_place("Species_A").with_tokens(100).done()
    builder.create_transition("Reaction_1").done()
    
    # Build and convert to dict (this is what batch_executor should do)
    model = builder.build()
    model_dict = model.to_dict()
    
    # Create temporary model file
    model_file = tmp_path / "experiment.shy"
    model_file.write_text('{"version": "2.0"}')
    
    # Create context
    context = {
        'model_path': str(model_file),
        'model': model_dict,  # Dictionary, not DocumentModel object
        'n_replicates': 10,
        'experiment_name': 'Test_Experiment',
        'simulation_config': {
            'duration': 100,
            'time_units': 'second',
            'use_tau_leaping': True
        }
    }
    
    # Generate header
    generator = SweepHeaderGenerator()
    generator.set_context(context)
    header = generator.generate()
    
    # Should complete without errors
    assert header is not None
    assert len(header.sections) > 0


def test_batch_executor_model_conversion_pattern(tmp_path):
    """Test the conversion pattern used in batch_executor.py."""
    # Simulate what batch_executor does
    builder = PetriNetBuilder()
    
    builder.create_place("P1").with_tokens(50).done()
    builder.create_transition("T1").done()
    
    # Build and convert to dict (this is the pattern from batch_executor.py fix)
    model = builder.build()
    model_dict = model.to_dict()
    
    # Verify conversion worked
    assert isinstance(model_dict, dict)
    assert 'places' in model_dict
    assert len(model_dict['places']) == 1
    assert isinstance(model_dict['places'][0], dict)
    
    # Verify it works with metadata
    model_file = tmp_path /"test.shy"
    model_file.write_text('{"version": "2.0"}')
    
    context = {
        'model_path': str(model_file),
        'model': model_dict
    }
    
    section = ModelMetadata()
    section.collect(context)  # Should not raise AttributeError
    assert section._fields['N_Places']['value'] == 1


def test_prevents_attribute_error_on_model_get():
    """Verify fix prevents AttributeError: 'DocumentModel' has no attribute 'get'."""
    # This was the original bug - passing DocumentModel directly
    doc = DocumentModel()
    
    # This would fail before the fix
    with pytest.raises(AttributeError, match="'DocumentModel' object has no attribute 'get'"):
        # Simulate what metadata section tries to do
        _ = doc.get('formalism')  # DocumentModel doesn't have .get()
    
    # But with conversion, it works
    model_dict = doc.to_dict()
    assert model_dict.get('formalism') is None  # Dictionary has .get()
    
    # And metadata can process it (we can't test without a file, so just verify dict structure)
    assert isinstance(model_dict, dict)
    assert 'places' in model_dict
    assert 'transitions' in model_dict
    assert 'arcs' in model_dict
