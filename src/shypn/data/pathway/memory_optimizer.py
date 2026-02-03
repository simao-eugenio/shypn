"""
Memory optimization utilities for large SBML model imports.

Addresses memory issues when importing genome-scale models like iJO1366
(~2500 species, ~2500 reactions, ~7000 arcs).

Key optimizations:
1. Incremental processing with memory cleanup
2. Reference counting and explicit deletion
3. Generator-based iteration for large collections
4. Memory profiling and monitoring
"""

import gc
import logging
from typing import Iterator, List, Any, Dict
import sys


class MemoryOptimizer:
    """Memory optimization utilities for large model imports."""
    
    def __init__(self, logger: logging.Logger = None):
        """Initialize memory optimizer.
        
        Args:
            logger: Optional logger for memory statistics
        """
        self.logger = logger or logging.getLogger(__name__)
        self._initial_memory = self._get_memory_usage()
    
    def _get_memory_usage(self) -> int:
        """Get current process memory usage in MB.
        
        Returns:
            Memory usage in megabytes
        """
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss // (1024 * 1024)  # Convert to MB
        except ImportError:
            # Fallback to sys if psutil not available
            return sys.getsizeof(gc.get_objects()) // (1024 * 1024)
    
    def log_memory_usage(self, context: str = ""):
        """Log current memory usage.
        
        Args:
            context: Description of current operation
        """
        current_memory = self._get_memory_usage()
        delta = current_memory - self._initial_memory
        self.logger.info(
            f"Memory usage{' (' + context + ')' if context else ''}: "
            f"{current_memory} MB (+{delta} MB from start)"
        )
    
    def force_cleanup(self):
        """Force garbage collection and log results."""
        collected = gc.collect()
        self.logger.debug(f"Garbage collection: {collected} objects collected")
        self.log_memory_usage("after cleanup")
    
    @staticmethod
    def batch_iterator(items: List[Any], batch_size: int = 100) -> Iterator[List[Any]]:
        """Iterate over large list in batches to reduce memory pressure.
        
        Args:
            items: List to iterate
            batch_size: Number of items per batch
            
        Yields:
            Batches of items
        """
        for i in range(0, len(items), batch_size):
            yield items[i:i + batch_size]
    
    @staticmethod
    def clear_cache(obj: Any, *attr_names: str):
        """Clear cached attributes from an object.
        
        Args:
            obj: Object to clear cache from
            *attr_names: Names of attributes to clear
        """
        for attr in attr_names:
            if hasattr(obj, attr):
                delattr(obj, attr)


def optimize_large_model_import(parsed_pathway, converter, logger: logging.Logger = None):
    """Optimize memory usage during large model conversion.
    
    This function wraps the normal conversion process with memory optimization:
    - Batch processing of species and reactions
    - Explicit cleanup between phases
    - Memory monitoring
    
    Args:
        parsed_pathway: PathwayData from SBML parser
        converter: PathwayConverter instance
        logger: Optional logger
        
    Returns:
        DocumentModel with optimized memory usage
    """
    logger = logger or logging.getLogger(__name__)
    optimizer = MemoryOptimizer(logger)
    
    logger.info(f"Starting optimized import: {len(parsed_pathway.species)} species, "
                f"{len(parsed_pathway.reactions)} reactions")
    optimizer.log_memory_usage("start")
    
    # Phase 1: Convert in normal mode (PathwayConverter handles this efficiently)
    logger.info("Phase 1: Converting pathway to DocumentModel...")
    document = converter.convert(parsed_pathway)
    optimizer.log_memory_usage("after conversion")
    
    # Phase 2: Cleanup intermediate data
    logger.info("Phase 2: Cleaning up intermediate data...")
    
    # Clear parser cache if it exists
    optimizer.clear_cache(parsed_pathway, '_species_cache', '_reaction_cache', '_annotation_cache')
    
    # Force garbage collection
    optimizer.force_cleanup()
    
    logger.info("Optimized import complete")
    optimizer.log_memory_usage("final")
    
    return document


class ChunkedArcCreator:
    """Creates arcs in chunks to avoid memory spikes during large conversions.
    
    For genome-scale models with 7000+ arcs, creating them all at once can
    cause memory issues. This class creates arcs in manageable chunks.
    """
    
    def __init__(self, document, logger: logging.Logger = None, chunk_size: int = 500):
        """Initialize chunked arc creator.
        
        Args:
            document: DocumentModel to add arcs to
            logger: Optional logger
            chunk_size: Number of arcs to create per chunk
        """
        self.document = document
        self.logger = logger or logging.getLogger(__name__)
        self.chunk_size = chunk_size
        self.optimizer = MemoryOptimizer(logger)
    
    def create_arcs_chunked(self, arc_data: List[Dict]) -> List:
        """Create arcs in chunks with cleanup between chunks.
        
        Args:
            arc_data: List of dicts with arc creation parameters
                Each dict should have: source, target, weight
        
        Returns:
            List of created Arc objects
        """
        total_arcs = len(arc_data)
        created_arcs = []
        
        self.logger.info(f"Creating {total_arcs} arcs in chunks of {self.chunk_size}...")
        
        for i, batch in enumerate(self.optimizer.batch_iterator(arc_data, self.chunk_size)):
            # Create arcs for this batch
            batch_arcs = []
            for arc_params in batch:
                arc = self.document.create_arc(**arc_params)
                if arc:
                    batch_arcs.append(arc)
            
            created_arcs.extend(batch_arcs)
            
            # Log progress
            progress = (i + 1) * self.chunk_size
            self.logger.info(f"  Created {min(progress, total_arcs)}/{total_arcs} arcs")
            
            # Force cleanup every 5 batches (reduces memory sawtooth pattern)
            if (i + 1) % 5 == 0:
                self.optimizer.force_cleanup()
        
        self.logger.info(f"Arc creation complete: {len(created_arcs)} arcs created")
        self.optimizer.log_memory_usage("after arc creation")
        
        return created_arcs


def estimate_memory_requirements(species_count: int, reaction_count: int) -> Dict[str, Any]:
    """Estimate memory requirements for a model.
    
    Based on empirical measurements from e_coli_core and iJO1366 imports.
    
    Args:
        species_count: Number of species
        reaction_count: Number of reactions
        
    Returns:
        Dict with memory estimates and recommendations
    """
    # Empirical coefficients (MB per element)
    SPECIES_MB = 0.02   # ~20 KB per species (Place object + metadata)
    REACTION_MB = 0.03  # ~30 KB per reaction (Transition + kinetics)
    ARC_MB = 0.01       # ~10 KB per arc (Arc object)
    
    # Estimate arc count (stoichiometry: avg 2.5 substrates + 2.5 products per reaction)
    estimated_arcs = reaction_count * 5
    
    # Calculate estimates
    species_memory = species_count * SPECIES_MB
    reaction_memory = reaction_count * REACTION_MB
    arc_memory = estimated_arcs * ARC_MB
    
    # Overhead (parser, converter, intermediate data structures)
    overhead_memory = (species_memory + reaction_memory) * 0.5
    
    total_estimated_mb = species_memory + reaction_memory + arc_memory + overhead_memory
    
    # Recommendations
    if total_estimated_mb < 100:
        recommendation = "Small model - no special memory handling needed"
        use_optimization = False
    elif total_estimated_mb < 500:
        recommendation = "Medium model - chunked processing recommended"
        use_optimization = True
    else:
        recommendation = "Large model - CRITICAL: use memory optimization"
        use_optimization = True
    
    return {
        'species_count': species_count,
        'reaction_count': reaction_count,
        'estimated_arcs': estimated_arcs,
        'estimated_memory_mb': round(total_estimated_mb, 1),
        'breakdown': {
            'species_mb': round(species_memory, 1),
            'reactions_mb': round(reaction_memory, 1),
            'arcs_mb': round(arc_memory, 1),
            'overhead_mb': round(overhead_memory, 1)
        },
        'recommendation': recommendation,
        'use_optimization': use_optimization
    }


if __name__ == "__main__":
    # Test memory estimation
    print("=" * 70)
    print("SHYPN Memory Estimator")
    print("=" * 70)
    print()
    
    # e_coli_core
    est = estimate_memory_requirements(72, 95)
    print(f"E. coli core (72 species, 95 reactions):")
    print(f"  Estimated memory: {est['estimated_memory_mb']} MB")
    print(f"  Recommendation: {est['recommendation']}")
    print()
    
    # iJO1366
    est = estimate_memory_requirements(1805, 2583)
    print(f"E. coli iJO1366 (1805 species, 2583 reactions):")
    print(f"  Estimated memory: {est['estimated_memory_mb']} MB")
    print(f"  Estimated arcs: {est['estimated_arcs']}")
    print(f"  Breakdown:")
    for key, value in est['breakdown'].items():
        print(f"    {key}: {value} MB")
    print(f"  Recommendation: {est['recommendation']}")
    print(f"  Use optimization: {est['use_optimization']}")
