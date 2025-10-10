"""Enhancement pipeline orchestrator.

This module implements the pipeline that chains multiple enhancement
processors together and manages their execution.
"""

from typing import List, Optional, Dict, Any
import logging
import time

from shypn.pathway.base import PostProcessorBase, ProcessorError
from shypn.pathway.options import EnhancementOptions


logger = logging.getLogger(__name__)


class EnhancementPipeline:
    """Pipeline for chaining multiple enhancement processors.
    
    Orchestrates execution of processors in sequence, handling:
    - Processor ordering
    - Error handling (fail-fast vs. continue-on-error)
    - Statistics collection
    - Logging and reporting
    - Timeout management
    
    Example:
        from shypn.pathway import EnhancementPipeline, EnhancementOptions
        from shypn.pathway.layout_optimizer import LayoutOptimizer
        from shypn.pathway.arc_router import ArcRouter
        
        options = EnhancementOptions()
        pipeline = EnhancementPipeline(options)
        
        # Add processors (order matters!)
        pipeline.add_processor(LayoutOptimizer(options))
        pipeline.add_processor(ArcRouter(options))
        
        # Process document
        enhanced = pipeline.process(document, pathway)
        
        # Check results
        print(pipeline.get_report())
    """
    
    def __init__(self, options: Optional[EnhancementOptions] = None):
        """Initialize the enhancement pipeline.
        
        Args:
            options: Configuration options for pipeline behavior.
                    If None, uses default options.
        """
        self.options = options or EnhancementOptions()
        self.processors: List[PostProcessorBase] = []
        self.execution_log: List[Dict[str, Any]] = []
        self.logger = logging.getLogger(f"{__name__}.EnhancementPipeline")
        
        # Configure logging based on options
        if self.options.verbose:
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger.setLevel(logging.INFO)
    
    def add_processor(self, processor: PostProcessorBase):
        """Add a processor to the pipeline.
        
        Processors run in the order they are added.
        
        Args:
            processor: Processor instance to add.
        
        Raises:
            TypeError: If processor doesn't implement PostProcessorBase.
        """
        if not isinstance(processor, PostProcessorBase):
            raise TypeError(f"Processor must inherit from PostProcessorBase, got {type(processor)}")
        
        self.processors.append(processor)
        self.logger.debug(f"Added processor: {processor.get_name()}")
    
    def remove_processor(self, processor_name: str) -> bool:
        """Remove a processor by name.
        
        Args:
            processor_name: Name returned by processor.get_name()
        
        Returns:
            True if processor was found and removed, False otherwise.
        """
        for i, proc in enumerate(self.processors):
            if proc.get_name() == processor_name:
                del self.processors[i]
                self.logger.debug(f"Removed processor: {processor_name}")
                return True
        return False
    
    def clear_processors(self):
        """Remove all processors from the pipeline."""
        self.processors.clear()
        self.logger.debug("Cleared all processors")
    
    def get_processor_names(self) -> List[str]:
        """Get names of all processors in the pipeline.
        
        Returns:
            List of processor names in execution order.
        """
        return [proc.get_name() for proc in self.processors]
    
    def process(self, document: 'DocumentModel', pathway: Optional['KEGGPathway'] = None) -> 'DocumentModel':
        """Run all processors on the document.
        
        Processors run in the order they were added.
        Each processor receives the output of the previous one.
        
        Args:
            document: Petri net document to enhance.
            pathway: Optional KEGG pathway data for context.
        
        Returns:
            Enhanced DocumentModel.
        
        Raises:
            ProcessorError: If a processor fails and fail_fast=True.
        """
        # Clear previous execution log
        self.execution_log.clear()
        
        # Check if enhancements are disabled
        if not self.options.enable_enhancements:
            self.logger.info("Enhancements disabled, returning document unchanged")
            return document
        
        # Check if any processors registered
        if not self.processors:
            self.logger.warning("No processors registered, returning document unchanged")
            return document
        
        # Start timing
        pipeline_start = time.time()
        
        self.logger.info(f"Starting enhancement pipeline with {len(self.processors)} processors")
        
        current_document = document
        
        for i, processor in enumerate(self.processors):
            try:
                # Check timeout
                if self.options.max_processing_time_seconds:
                    elapsed = time.time() - pipeline_start
                    if elapsed > self.options.max_processing_time_seconds:
                        self.logger.warning(
                            f"Pipeline timeout ({self.options.max_processing_time_seconds}s) "
                            f"exceeded, stopping at processor {i+1}/{len(self.processors)}"
                        )
                        break
                
                # Check if processor is applicable
                if not processor.is_applicable(current_document, pathway):
                    self.logger.info(f"Processor {i+1}/{len(self.processors)}: "
                                   f"{processor.get_name()} - SKIPPED (not applicable)")
                    self._log_processor_execution(processor, skipped=True)
                    continue
                
                # Run processor
                self.logger.info(f"Processor {i+1}/{len(self.processors)}: "
                               f"{processor.get_name()} - RUNNING")
                
                proc_start = time.time()
                
                # Validate inputs
                processor.validate_inputs(current_document, pathway)
                
                # Process
                current_document = processor.process(current_document, pathway)
                
                proc_time = time.time() - proc_start
                
                # Log execution
                self.logger.info(f"Processor {i+1}/{len(self.processors)}: "
                               f"{processor.get_name()} - COMPLETED ({proc_time:.2f}s)")
                
                self._log_processor_execution(
                    processor,
                    success=True,
                    processing_time=proc_time
                )
                
            except ProcessorError as e:
                # Processor raised critical error
                self.logger.error(f"Processor {i+1}/{len(self.processors)}: "
                                f"{processor.get_name()} - FAILED: {str(e)}")
                
                self._log_processor_execution(
                    processor,
                    success=False,
                    error=str(e)
                )
                
                if self.options.fail_fast:
                    raise  # Re-raise to stop pipeline
                else:
                    # Continue with remaining processors
                    continue
            
            except Exception as e:
                # Unexpected error
                self.logger.error(f"Processor {i+1}/{len(self.processors)}: "
                                f"{processor.get_name()} - UNEXPECTED ERROR: {str(e)}",
                                exc_info=True)
                
                self._log_processor_execution(
                    processor,
                    success=False,
                    error=f"Unexpected error: {str(e)}"
                )
                
                if self.options.fail_fast:
                    raise ProcessorError(processor.get_name(), f"Unexpected error: {str(e)}", e)
                else:
                    continue
        
        # Pipeline complete
        pipeline_time = time.time() - pipeline_start
        self.logger.info(f"Enhancement pipeline completed in {pipeline_time:.2f}s")
        
        return current_document
    
    def _log_processor_execution(
        self,
        processor: PostProcessorBase,
        success: bool = True,
        skipped: bool = False,
        processing_time: float = 0.0,
        error: Optional[str] = None
    ):
        """Log execution of a processor.
        
        Args:
            processor: The processor that ran.
            success: Whether processor succeeded.
            skipped: Whether processor was skipped.
            processing_time: Time taken in seconds.
            error: Error message if failed.
        """
        log_entry = {
            'processor': processor.get_name(),
            'success': success,
            'skipped': skipped,
            'processing_time': processing_time,
            'stats': processor.get_stats() if not skipped else {},
            'error': error
        }
        
        self.execution_log.append(log_entry)
    
    def get_report(self) -> Dict[str, Any]:
        """Generate report of pipeline execution.
        
        Returns:
            Dictionary with:
            - processors_run: Number of processors that ran
            - processors_succeeded: Number that succeeded
            - processors_failed: Number that failed
            - processors_skipped: Number that were skipped
            - total_time: Total processing time
            - execution_log: Detailed log of each processor
        """
        run = len([e for e in self.execution_log if not e['skipped']])
        succeeded = len([e for e in self.execution_log if e['success'] and not e['skipped']])
        failed = len([e for e in self.execution_log if not e['success'] and not e['skipped']])
        skipped = len([e for e in self.execution_log if e['skipped']])
        total_time = sum(e['processing_time'] for e in self.execution_log)
        
        return {
            'processors_run': run,
            'processors_succeeded': succeeded,
            'processors_failed': failed,
            'processors_skipped': skipped,
            'total_time': total_time,
            'execution_log': self.execution_log.copy()
        }
    
    def print_report(self):
        """Print human-readable report to console."""
        report = self.get_report()
        
        print("\n" + "="*60)
        print("ENHANCEMENT PIPELINE REPORT")
        print("="*60)
        print(f"Processors run:      {report['processors_run']}")
        print(f"Succeeded:           {report['processors_succeeded']}")
        print(f"Failed:              {report['processors_failed']}")
        print(f"Skipped:             {report['processors_skipped']}")
        print(f"Total time:          {report['total_time']:.2f}s")
        print("\nProcessor Details:")
        print("-"*60)
        
        for entry in report['execution_log']:
            status = "SKIPPED" if entry['skipped'] else ("SUCCESS" if entry['success'] else "FAILED")
            print(f"{entry['processor']:30} {status:10} {entry['processing_time']:6.2f}s")
            
            if entry['error']:
                print(f"  Error: {entry['error']}")
            
            if entry['stats']:
                print(f"  Stats: {entry['stats']}")
        
        print("="*60 + "\n")
    
    def __str__(self) -> str:
        """String representation."""
        return f"<EnhancementPipeline: {len(self.processors)} processors>"
    
    def __repr__(self) -> str:
        """Detailed representation."""
        names = self.get_processor_names()
        return f"EnhancementPipeline(processors={names})"
