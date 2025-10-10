"""Unit tests for PostProcessorBase and ProcessorError."""

import pytest
from abc import ABC

from shypn.pathway.base import PostProcessorBase, ProcessorError
from shypn.pathway.options import EnhancementOptions
from shypn.data.canvas.document_model import DocumentModel


class MockProcessor(PostProcessorBase):
    """Mock processor for testing."""
    
    def __init__(self, options=None, fail=False):
        super().__init__(options)
        self.fail = fail
        self.process_called = False
    
    def get_name(self):
        return "Mock Processor"
    
    def process(self, document, pathway=None):
        self.process_called = True
        if self.fail:
            raise ProcessorError("Mock failure")
        return document


class TestPostProcessorBase:
    """Test PostProcessorBase abstract class."""
    
    def test_cannot_instantiate_abstract_base(self):
        """Cannot instantiate abstract base class directly."""
        with pytest.raises(TypeError):
            PostProcessorBase()
    
    def test_concrete_processor_instantiation(self):
        """Can instantiate concrete processor."""
        processor = MockProcessor()
        assert processor is not None
        assert processor.get_name() == "Mock Processor"
    
    def test_options_stored(self):
        """Options are stored in processor."""
        options = EnhancementOptions(verbose=True)
        processor = MockProcessor(options)
        assert processor.options is options
        assert processor.options.verbose is True
    
    def test_stats_initialization(self):
        """Stats are initialized to empty dict."""
        processor = MockProcessor()
        assert processor.stats == {}
    
    def test_reset_stats(self):
        """reset_stats() clears stats."""
        processor = MockProcessor()
        processor.stats = {'foo': 'bar'}
        processor.reset_stats()
        assert processor.stats == {}
    
    def test_get_stats(self):
        """get_stats() returns stats dict."""
        processor = MockProcessor()
        processor.stats = {'items_processed': 42}
        stats = processor.get_stats()
        assert stats == {'items_processed': 42}
    
    def test_process_method_called(self):
        """process() method is called."""
        processor = MockProcessor()
        document = DocumentModel()
        result = processor.process(document, None)
        assert processor.process_called is True
        assert result is document
    
    def test_is_applicable_default_true(self):
        """is_applicable() returns True by default."""
        processor = MockProcessor()
        document = DocumentModel()
        assert processor.is_applicable(document, None) is True
    
    def test_validate_inputs_success(self):
        """validate_inputs() passes with valid document."""
        processor = MockProcessor()
        document = DocumentModel()
        # Should not raise
        processor.validate_inputs(document, None)
    
    def test_validate_inputs_none_document(self):
        """validate_inputs() raises on None document."""
        processor = MockProcessor()
        with pytest.raises(ValueError, match="document cannot be None"):
            processor.validate_inputs(None, None)
    
    def test_validate_inputs_invalid_document(self):
        """validate_inputs() raises on invalid document."""
        processor = MockProcessor()
        with pytest.raises(ValueError, match="must have 'places' attribute"):
            processor.validate_inputs("not a document", None)


class TestProcessorError:
    """Test ProcessorError exception."""
    
    def test_raise_processor_error(self):
        """ProcessorError can be raised."""
        with pytest.raises(ProcessorError, match="TestProcessor: Test error"):
            raise ProcessorError("TestProcessor", "Test error")
    
    def test_processor_error_is_exception(self):
        """ProcessorError is an Exception."""
        error = ProcessorError("TestProcessor", "test message")
        assert isinstance(error, Exception)
    
    def test_processor_error_with_cause(self):
        """ProcessorError can store underlying cause."""
        cause = ValueError("underlying error")
        error = ProcessorError("TestProcessor", "test message", cause)
        assert error.cause is cause
        assert error.processor_name == "TestProcessor"
