"""Experiment automation components for Viability Panel.

This module provides batch experiment automation capabilities:
- Parameter sweep configuration
- Experiment queue management
- Batch execution
- Results browser

Author: Simão Eugénio
Date: December 7, 2025
"""

from .experiment_automation_category import ExperimentAutomationCategory
from .parameter_sweep_builder import ParameterSweepBuilder
from .experiment_queue_view import ExperimentQueueView
from .batch_executor import BatchExecutor
from .results_browser_view import ResultsBrowserView
from .remote_results_proxy import RemoteResultsProxy, FetchState
from .remote_sweep_dispatcher import FetchMode

__all__ = [
    'ExperimentAutomationCategory',
    'ParameterSweepBuilder',
    'ExperimentQueueView',
    'BatchExecutor',
    'ResultsBrowserView',
    'RemoteResultsProxy',
    'FetchState',
    'FetchMode',
]
