"""Unit tests for EnhancementPipeline."""

import pytest
import time

from shypn.pathway.pipeline import EnhancementPipeline
from shypn.pathway.base import PostProcessorBase, ProcessorError
from shypn.pathway.options import EnhancementOptions
from shypn.data.canvas.document_model import DocumentModel


class MockProcessor(PostProcessorBase):
    """Mock processor for testing."""
    
    def __init__(self, name, options=None, fail=False, delay=0):
        super().__init__(options)
        self._name = name
        self.fail = fail
        self.delay = delay
        self.process_called = False
    
    def get_name(self):
        return self._name
    
    def process(self, document, pathway=None):
        self.process_called = True
        if self.delay:
            time.sleep(self.delay)
        if self.fail:
            raise ProcessorError(self._name, "failed")
        self.stats = {'items_processed': 1}
        return document


class TestEnhancementPipeline:
    """Test EnhancementPipeline orchestrator."""
    
    def test_pipeline_creation(self):
        """Can create pipeline."""
        opts = EnhancementOptions()
        pipeline = EnhancementPipeline(opts)
        assert pipeline is not None
        assert pipeline.options is opts
    
    def test_add_processor(self):
        """Can add processor to pipeline."""
        pipeline = EnhancementPipeline()
        proc = MockProcessor("Test")
        pipeline.add_processor(proc)
        assert len(pipeline.processors) == 1
    
    def test_add_multiple_processors(self):
        """Can add multiple processors."""
        pipeline = EnhancementPipeline()
        proc1 = MockProcessor("First")
        proc2 = MockProcessor("Second")
        pipeline.add_processor(proc1)
        pipeline.add_processor(proc2)
        assert len(pipeline.processors) == 2
    
    def test_remove_processor(self):
        """Can remove processor by name."""
        pipeline = EnhancementPipeline()
        proc1 = MockProcessor("First")
        proc2 = MockProcessor("Second")
        pipeline.add_processor(proc1)
        pipeline.add_processor(proc2)
        
        pipeline.remove_processor("First")
        assert len(pipeline.processors) == 1
        assert pipeline.processors[0].get_name() == "Second"
    
    def test_clear_processors(self):
        """Can clear all processors."""
        pipeline = EnhancementPipeline()
        pipeline.add_processor(MockProcessor("First"))
        pipeline.add_processor(MockProcessor("Second"))
        
        pipeline.clear_processors()
        assert len(pipeline.processors) == 0
    
    def test_process_empty_pipeline(self):
        """Process with no processors returns document unchanged."""
        pipeline = EnhancementPipeline()
        document = DocumentModel()
        result = pipeline.process(document, None)
        assert result is document
    
    def test_process_single_processor(self):
        """Process with single processor calls it."""
        pipeline = EnhancementPipeline()
        proc = MockProcessor("Test")
        pipeline.add_processor(proc)
        
        document = DocumentModel()
        result = pipeline.process(document, None)
        
        assert proc.process_called is True
        assert result is document
    
    def test_process_multiple_processors_sequential(self):
        """Process with multiple processors calls them in order."""
        pipeline = EnhancementPipeline()
        proc1 = MockProcessor("First")
        proc2 = MockProcessor("Second")
        proc3 = MockProcessor("Third")
        
        pipeline.add_processor(proc1)
        pipeline.add_processor(proc2)
        pipeline.add_processor(proc3)
        
        document = DocumentModel()
        result = pipeline.process(document, None)
        
        assert proc1.process_called is True
        assert proc2.process_called is True
        assert proc3.process_called is True
        assert result is document
    
    def test_fail_fast_on_error(self):
        """With fail_fast=True, stops on first error."""
        opts = EnhancementOptions(fail_fast=True)
        pipeline = EnhancementPipeline(opts)
        
        proc1 = MockProcessor("First", fail=False)
        proc2 = MockProcessor("Second", fail=True)  # This will fail
        proc3 = MockProcessor("Third", fail=False)
        
        pipeline.add_processor(proc1)
        pipeline.add_processor(proc2)
        pipeline.add_processor(proc3)
        
        document = DocumentModel()
        
        with pytest.raises(ProcessorError, match="Second"):
            pipeline.process(document, None)
        
        # First was called, third was not
        assert proc1.process_called is True
        assert proc2.process_called is True
        assert proc3.process_called is False
    
    def test_continue_on_error(self):
        """With fail_fast=False, continues after errors."""
        opts = EnhancementOptions(fail_fast=False)
        pipeline = EnhancementPipeline(opts)
        
        proc1 = MockProcessor("First", fail=False)
        proc2 = MockProcessor("Second", fail=True)  # This will fail
        proc3 = MockProcessor("Third", fail=False)
        
        pipeline.add_processor(proc1)
        pipeline.add_processor(proc2)
        pipeline.add_processor(proc3)
        
        document = DocumentModel()
        result = pipeline.process(document, None)
        
        # All were called despite error
        assert proc1.process_called is True
        assert proc2.process_called is True
        assert proc3.process_called is True
        assert result is document
    
    def test_get_report_after_process(self):
        """get_report() returns execution statistics."""
        pipeline = EnhancementPipeline()
        proc1 = MockProcessor("First")
        proc2 = MockProcessor("Second")
        
        pipeline.add_processor(proc1)
        pipeline.add_processor(proc2)
        
        document = DocumentModel()
        pipeline.process(document, None)
        
        report = pipeline.get_report()
        assert 'processors_run' in report
        assert report['processors_run'] == 2
        assert 'processors_failed' in report
        assert 'execution_log' in report
        assert len(report['execution_log']) == 2
    
    def test_report_contains_execution_time(self):
        """Report contains execution time."""
        pipeline = EnhancementPipeline()
        proc = MockProcessor("Test")
        pipeline.add_processor(proc)
        
        document = DocumentModel()
        pipeline.process(document, None)
        
        report = pipeline.get_report()
        assert 'total_time' in report
        assert report['total_time'] > 0
    
    def test_report_per_processor(self):
        """Report contains per-processor statistics."""
        pipeline = EnhancementPipeline()
        proc = MockProcessor("Test")
        pipeline.add_processor(proc)
        
        document = DocumentModel()
        pipeline.process(document, None)
        
        report = pipeline.get_report()
        exec_log = report['execution_log']
        assert len(exec_log) == 1
        
        proc_report = exec_log[0]
        assert proc_report['processor'] == "Test"
        assert proc_report['success'] is True
        assert 'processing_time' in proc_report
        assert 'stats' in proc_report
    
    def test_print_report_no_error(self):
        """print_report() does not raise error."""
        pipeline = EnhancementPipeline()
        proc = MockProcessor("Test")
        pipeline.add_processor(proc)
        
        document = DocumentModel()
        pipeline.process(document, None)
        
        # Should not raise
        pipeline.print_report()
    
    def test_skip_inapplicable_processors(self):
        """Processors that return False from is_applicable are skipped."""
        
        class InapplicableProcessor(MockProcessor):
            def is_applicable(self, document, pathway=None):
                return False
        
        pipeline = EnhancementPipeline()
        proc1 = MockProcessor("Applicable")
        proc2 = InapplicableProcessor("Inapplicable")
        
        pipeline.add_processor(proc1)
        pipeline.add_processor(proc2)
        
        document = DocumentModel()
        pipeline.process(document, None)
        
        assert proc1.process_called is True
        assert proc2.process_called is False  # Skipped
