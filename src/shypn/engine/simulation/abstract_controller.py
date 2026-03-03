"""Abstract base class for simulation controllers.

Sprint 23 — Phase 7 OOP refactor.

Defines the minimal public contract that every simulation controller must
satisfy, independently of the underlying execution strategy (continuous,
stochastic, synchronous, etc.).
"""

from __future__ import annotations

__all__ = ["AbstractSimulationController"]

from abc import ABC, abstractmethod
from typing import Any, Callable, List, Optional, Set


class AbstractSimulationController(ABC):
    """Contract for Petri-net simulation controllers.

    Concrete controllers must implement the lifecycle (``step`` / ``reset``),
    enablement query, strategy selection, and listener registration API.

    Instance attributes that every concrete controller is expected to provide
    (not enforced by Python, but documented here for type-checking tools):

    .. code-block:: python

        self.time: float          # current simulation clock
        self.data_collector: Any  # records token/marking trajectories
        self.document_id: int     # canvas scope identifier
    """

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    @abstractmethod
    def step(self, time_step: Optional[float] = None) -> bool:
        """Advance simulation by one logical step.

        Args:
            time_step: Explicit ``dt`` override.  ``None`` means use the
                controller's own effective ``dt``.

        Returns:
            ``True`` if step fired at least one transition, ``False``
            otherwise (e.g. deadlock or end of duration).
        """

    @abstractmethod
    def reset(self) -> None:
        """Reset the simulation to its initial marking and clear the clock."""

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------

    @abstractmethod
    def is_running(self) -> bool:
        """Return ``True`` while the simulation loop is executing."""

    @abstractmethod
    def is_simulation_complete(self) -> bool:
        """Return ``True`` when the configured end condition has been met."""

    # ------------------------------------------------------------------
    # Enablement and conflict
    # ------------------------------------------------------------------

    @abstractmethod
    def get_enabled_transitions(
        self, dirty_places: Optional[Set[Any]] = None
    ) -> List[Any]:
        """Return the list of currently enabled transitions.

        Args:
            dirty_places: Optional set of places whose token counts changed
                since the last query (performance optimisation hint).

        Returns:
            ``list`` of enabled transition objects.
        """

    @abstractmethod
    def set_conflict_policy(self, policy: Any) -> None:
        """Set the conflict-resolution policy.

        Args:
            policy: A :class:`~shypn.engine.simulation.conflict_policy.ConflictResolutionPolicy`
                instance (or compatible object).
        """

    # ------------------------------------------------------------------
    # Timing
    # ------------------------------------------------------------------

    @abstractmethod
    def get_effective_dt(self) -> float:
        """Return the time increment that will be used for the next step."""

    # ------------------------------------------------------------------
    # Strategy
    # ------------------------------------------------------------------

    @abstractmethod
    def get_strategy(self) -> Optional[Any]:
        """Return the active execution strategy, or ``None`` if none is set."""

    @abstractmethod
    def set_strategy(self, strategy: Any) -> None:
        """Replace the active execution strategy.

        Args:
            strategy: New strategy instance.
        """

    @abstractmethod
    def auto_select_strategy(self) -> Any:
        """Analyse the model and select the most appropriate strategy.

        Returns:
            The strategy that was chosen and activated.
        """

    # ------------------------------------------------------------------
    # Step listeners
    # ------------------------------------------------------------------

    @abstractmethod
    def add_step_listener(self, callback: Callable[[], None]) -> None:
        """Register *callback* to be called after every simulation step.

        Args:
            callback: Zero-argument callable invoked post-step.
        """

    @abstractmethod
    def remove_step_listener(self, callback: Callable[[], None]) -> None:
        """De-register a previously registered step listener.

        Args:
            callback: The callable to remove.  Silently ignored if not
                registered.
        """
