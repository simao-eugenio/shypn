"""Sweep dispatch package — OOP layer for local + remote sweep execution.

Module map:
    types        — typed dataclasses (SimulationParams, DispatchRequest)
    observer     — DispatchObserver protocol
    param_collector — pull SimulationParams from sweep-builder widgets
    base         — SweepDispatchController (ABC, lifecycle + cancel)
    local        — LocalSweepDispatchController (delegates to BatchExecutor)
    remote       — RemoteSweepDispatchController (delegates to RemoteSweepDispatcher)

The category panel keeps only:
    - the observer methods (queue UI updates)
    - thin entry points that build a DispatchRequest and call
      controller.start(request)

All widget-reading, regex parsing of CLI progress lines, and dispatch
state management lives inside this package.
"""

from .types import SimulationParams, DispatchRequest, DispatchKind
from .observer import DispatchObserver
from .param_collector import WidgetParamCollector
from .base import SweepDispatchController, DispatchAlreadyActive, DispatchValidationError
from .local import LocalSweepDispatchController
from .remote import RemoteSweepDispatchController

__all__ = [
    'SimulationParams',
    'DispatchRequest',
    'DispatchKind',
    'DispatchObserver',
    'WidgetParamCollector',
    'SweepDispatchController',
    'LocalSweepDispatchController',
    'RemoteSweepDispatchController',
    'DispatchAlreadyActive',
    'DispatchValidationError',
]
