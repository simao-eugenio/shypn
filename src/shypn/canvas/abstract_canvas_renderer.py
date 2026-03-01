"""Abstract base class for canvas rendering.

Sprint 21 — Phase 7 OOP refactor.
"""

from __future__ import annotations

__all__ = ["AbstractCanvasRenderer"]

from abc import ABC, abstractmethod
from typing import Any


class AbstractCanvasRenderer(ABC):
    """Contract for the canvas draw-frame and arc-preview pipelines."""

    @abstractmethod
    def render_frame(
        self,
        drawing_area: Any,
        cr: Any,
        width: int,
        height: int,
        manager: Any,
    ) -> None:
        """Execute one full frame draw into *cr*.

        Args:
            drawing_area: GtkDrawingArea being rendered.
            cr: Cairo drawing context.
            width: Viewport width in pixels.
            height: Viewport height in pixels.
            manager: :class:`~shypn.data.model_canvas_manager.ModelCanvasManager`
                bound to this canvas.
        """

    @abstractmethod
    def render_arc_preview(
        self,
        cr: Any,
        arc_state: dict,
        manager: Any,
    ) -> None:
        """Draw the orange in-progress arc preview line + arrowhead.

        Args:
            cr: Cairo drawing context (screen coordinates, no zoom transform).
            arc_state: ``ctx.arc`` dict with keys ``source``, ``cursor_pos``,
                ``hovered_target``, ``target_valid``.
            manager: :class:`~shypn.data.model_canvas_manager.ModelCanvasManager`
                bound to this canvas.
        """
