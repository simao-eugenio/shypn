"""BiGG Models importer for shypn.

This package provides services for importing curated genome-scale metabolic
models from the BiGG Models database (http://bigg.ucsd.edu).

Architecture:
    - Service classes: Business logic, no UI dependencies
    - Base classes: Shared functionality for all services
    - Data classes: Type-safe model representation
"""

from .base_bigg_service import BaseBiGGService
from .bigg_model_fetcher import BiGGModelFetcher, BiGGModelInfo
from .bigg_downloader import BiGGDownloader
from .bigg_namespace_parser import BiGGNamespaceParser
from .bigg_signal_classifier import BiGGSignalClassifier

__all__ = [
    'BaseBiGGService',
    'BiGGModelFetcher',
    'BiGGModelInfo',
    'BiGGDownloader',
    'BiGGNamespaceParser',
    'BiGGSignalClassifier',
]
