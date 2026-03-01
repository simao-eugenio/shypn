"""Abstract base class for the canvas context-menu subsystem.

Sprint 22 — Phase 7 OOP refactor.
"""

from __future__ import annotations

__all__ = ["AbstractContextMenuController"]

from abc import ABC, abstractmethod
from typing import Any


class AbstractContextMenuController(ABC):
    """Contract for building, showing and tearing down canvas context menus."""

    @abstractmethod
    def setup_for_drawing_area(self, drawing_area: Any, manager: Any) -> None:
        """Build and register the canvas-level context menu for *drawing_area*.

        Called once per document during ``_setup_event_controllers``.
        """

    @abstractmethod
    def show_canvas_menu(self, x: float, y: float, drawing_area: Any) -> None:
        """Pop up the canvas context menu at the current pointer position.

        Args:
            x: Widget-relative x coordinate (informational).
            y: Widget-relative y coordinate (informational).
            drawing_area: GtkDrawingArea that received the click.
        """

    @abstractmethod
    def show_object_menu(
        self,
        x: float,
        y: float,
        drawing_area: Any,
        manager: Any,
        obj: Any,
    ) -> None:
        """Pop up the per-object context menu.

        Args:
            x: Widget-relative x coordinate (informational).
            y: Widget-relative y coordinate (informational).
            drawing_area: GtkDrawingArea that received the click.
            manager: :class:`~shypn.data.model_canvas_manager.ModelCanvasManager`.
            obj: The clicked Petri-net object (Place, Transition, or Arc).
        """

    @abstractmethod
    def popdown_canvas_menu(self) -> bool:
        """Dismiss the active canvas context menu (Escape handler).

        Returns:
            ``True`` if a menu was popped down, ``False`` otherwise.
        """
