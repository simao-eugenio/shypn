#!/usr/bin/env python3
"""Batch Processor for processing multiple models.

Provides error isolation and progress tracking for batch operations
on collections of Petri net models.
"""
import csv
import json
import logging
from pathlib import Path
from typing import List, Tuple, Dict, Any, Callable, Optional
from concurrent.futures import ProcessPoolExecutor, as_completed
import traceback


class BatchProcessor:
    """Process batches of models with error isolation.
    
    Features:
    - Load batch specification from CSV
    - Process models with custom function
    - Error isolation (failed models don't stop batch)
    - Optional parallel processing
    - Export results summary
    
    Example:
        processor = BatchProcessor()
        models = processor.load_from_csv('models.csv')
        results = processor.process_batch(models, process_func)
        processor.export_results(results, Path('output/'))
    """
    
    def __init__(self, verbose: bool = False):
        """Initialize batch processor.
        
        Args:
            verbose: Enable verbose logging (default: False)
        """
        self.verbose = verbose
        self.logger = logging.getLogger(self.__class__.__name__)
        if verbose:
            logging.basicConfig(level=logging.INFO)
    
    def load_from_csv(self, csv_path: str) -> List[Tuple[str, Path]]:
        """Load batch specification from CSV file.
        
        CSV Format:
            model_id,model_path
            Model1,/path/to/model1.sbml
            Model2,/path/to/model2.xml
            ...
        
        The CSV must have a header row with columns 'model_id' and 'model_path'.
        
        Args:
            csv_path: Path to CSV file
            
        Returns:
            List of (model_id, model_path) tuples
            
        Raises:
            FileNotFoundError: If CSV file doesn't exist
            ValueError: If CSV format is invalid
        """
        csv_path = Path(csv_path)
        
        if not csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")
        
        models = []
        
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            # Validate header
            if 'model_id' not in reader.fieldnames or 'model_path' not in reader.fieldnames:
                raise ValueError(
                    f"CSV must have 'model_id' and 'model_path' columns. "
                    f"Found: {reader.fieldnames}"
                )
            
            for i, row in enumerate(reader, start=2):  # Start at 2 (1 is header)
                model_id = row['model_id'].strip()
                model_path_str = row['model_path'].strip()
                
                if not model_id:
                    self.logger.warning(f"Row {i}: Empty model_id, skipping")
                    continue
                
                if not model_path_str:
                    self.logger.warning(f"Row {i}: Empty model_path for '{model_id}', skipping")
                    continue
                
                model_path = Path(model_path_str)
                models.append((model_id, model_path))
        
        if self.verbose:
            self.logger.info(f"Loaded {len(models)} models from {csv_path}")
        
        return models
    
    def process_batch(
        self,
        models: List[Tuple[str, Path]],
        processor_func: Callable[[str, Path], Any],
        parallel: bool = False,
        max_workers: Optional[int] = None
    ) -> Dict[str, Any]:
        """Process batch of models with error isolation.
        
        Each model is processed independently. If one fails, others continue.
        
        Args:
            models: List of (model_id, model_path) tuples
            processor_func: Function to apply to each model
                           Signature: func(model_id: str, model_path: Path) -> result
                           Should return any JSON-serializable result
            parallel: Use multiprocessing (default: False)
            max_workers: Max parallel workers (default: CPU count)
            
        Returns:
            Dict with:
            {
                'successful': {model_id: result, ...},
                'failed': {model_id: error_message, ...},
                'n_successful': int,
                'n_failed': int,
                'n_total': int
            }
        """
        successful = {}
        failed = {}
        
        if parallel:
            # Parallel processing with multiprocessing
            results = self._process_parallel(
                models, processor_func, max_workers
            )
            
            for model_id, result, error in results:
                if error:
                    failed[model_id] = error
                else:
                    successful[model_id] = result
        else:
            # Sequential processing
            for i, (model_id, model_path) in enumerate(models, start=1):
                if self.verbose:
                    self.logger.info(f"Processing [{i}/{len(models)}]: {model_id}")
                
                try:
                    result = processor_func(model_id, model_path)
                    successful[model_id] = result
                    
                    if self.verbose:
                        self.logger.info(f"  ✓ Success: {model_id}")
                        
                except Exception as e:
                    error_msg = f"{type(e).__name__}: {str(e)}"
                    failed[model_id] = error_msg
                    
                    self.logger.error(f"  ✗ Failed: {model_id} - {error_msg}")
                    
                    if self.verbose:
                        self.logger.debug(traceback.format_exc())
        
        return {
            'successful': successful,
            'failed': failed,
            'n_successful': len(successful),
            'n_failed': len(failed),
            'n_total': len(models)
        }
    
    def _process_parallel(
        self,
        models: List[Tuple[str, Path]],
        processor_func: Callable,
        max_workers: Optional[int]
    ) -> List[Tuple[str, Any, Optional[str]]]:
        """Process models in parallel using multiprocessing.
        
        Args:
            models: List of (model_id, model_path) tuples
            processor_func: Function to apply
            max_workers: Max parallel workers
            
        Returns:
            List of (model_id, result, error_message) tuples
        """
        results = []
        
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_model = {
                executor.submit(self._safe_process, model_id, model_path, processor_func): 
                (model_id, model_path)
                for model_id, model_path in models
            }
            
            # Collect results as they complete
            for i, future in enumerate(as_completed(future_to_model), start=1):
                model_id, model_path = future_to_model[future]
                
                if self.verbose:
                    self.logger.info(f"Completed [{i}/{len(models)}]: {model_id}")
                
                result, error = future.result()
                results.append((model_id, result, error))
        
        return results
    
    @staticmethod
    def _safe_process(
        model_id: str,
        model_path: Path,
        processor_func: Callable
    ) -> Tuple[Any, Optional[str]]:
        """Safely process a model with error catching.
        
        Args:
            model_id: Model identifier
            model_path: Path to model file
            processor_func: Processing function
            
        Returns:
            Tuple of (result, error_message)
            If successful: (result, None)
            If failed: (None, error_message)
        """
        try:
            result = processor_func(model_id, model_path)
            return result, None
        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}"
            return None, error_msg
    
    def export_results(
        self,
        results: Dict[str, Any],
        output_dir: Path,
        include_details: bool = True
    ) -> None:
        """Export batch processing results to files.
        
        Creates:
        - batch_summary.json: Overall statistics and results
        - successful_models.csv: List of successful models
        - failed_models.csv: List with error messages (if any failures)
        
        Args:
            results: Results dict from process_batch()
            output_dir: Output directory path
            include_details: Include detailed results in JSON (default: True)
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 1. Export summary JSON
        summary_path = output_dir / 'batch_summary.json'
        summary = {
            'n_total': results['n_total'],
            'n_successful': results['n_successful'],
            'n_failed': results['n_failed'],
            'success_rate': results['n_successful'] / results['n_total'] if results['n_total'] > 0 else 0.0
        }
        
        if include_details:
            summary['successful_models'] = list(results['successful'].keys())
            summary['failed_models'] = list(results['failed'].keys())
            summary['results'] = results['successful']
            summary['errors'] = results['failed']
        
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)
        
        if self.verbose:
            self.logger.info(f"Exported summary: {summary_path}")
        
        # 2. Export successful models CSV
        if results['successful']:
            success_path = output_dir / 'successful_models.csv'
            with open(success_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['model_id'])
                for model_id in sorted(results['successful'].keys()):
                    writer.writerow([model_id])
            
            if self.verbose:
                self.logger.info(f"Exported successful models: {success_path}")
        
        # 3. Export failed models CSV (if any)
        if results['failed']:
            failed_path = output_dir / 'failed_models.csv'
            with open(failed_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['model_id', 'error'])
                for model_id in sorted(results['failed'].keys()):
                    error = results['failed'][model_id]
                    writer.writerow([model_id, error])
            
            if self.verbose:
                self.logger.info(f"Exported failed models: {failed_path}")
        
        if self.verbose:
            self.logger.info(
                f"Batch summary: {results['n_successful']}/{results['n_total']} successful "
                f"({100*summary['success_rate']:.1f}%)"
            )
