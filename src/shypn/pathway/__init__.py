"""Pathway enhancement module for post-processing Petri nets.

This module provides a pipeline for enhancing Petri nets generated from
KEGG pathways. It uses image-guided techniques to improve layout, arc routing,
metadata, and validation.

Architecture:
    - PostProcessorBase: Abstract base class for all processors
    - EnhancementPipeline: Orchestrates multiple processors
    - EnhancementOptions: Configuration for enhancement behavior
    - Concrete processors: LayoutOptimizer, ArcRouter, MetadataEnhancer, VisualValidator

Usage:
    from shypn.pathway import EnhancementPipeline, EnhancementOptions
    from shypn.pathway.layout_optimizer import LayoutOptimizer
    from shypn.pathway.arc_router import ArcRouter
    
    # Create pipeline
    options = EnhancementOptions(
        enable_layout_optimization=True,
        enable_arc_routing=True
    )
    
    pipeline = EnhancementPipeline(options)
    pipeline.add_processor(LayoutOptimizer())
    pipeline.add_processor(ArcRouter())
    
    # Process document
    enhanced_document = pipeline.process(document, pathway)
"""

from shypn.pathway.base import PostProcessorBase
from shypn.pathway.options import EnhancementOptions
from shypn.pathway.pipeline import EnhancementPipeline

__all__ = [
    'PostProcessorBase',
    'EnhancementOptions',
    'EnhancementPipeline',
]
