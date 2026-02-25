"""Per-canvas interaction state, collected into a single value object.

Replaces four separate per-document dicts that were scattered across
ModelCanvasLoader (_drag_state, _arc_state, _click_state, _lasso_state)
with one registry entry keyed by drawing_area.
"""


class CanvasInteractionContext:
    """Collects all mutable per-canvas interaction state into one object.

    Attributes:
        drag:  Panning / object-dragging / rect-selection state.
        arc:   Arc creation in-progress state.
        click: Double-click detection and pending-click timeout state.
        lasso: Lasso selection mode state.
    """

    __slots__ = ('drag', 'arc', 'click', 'lasso')

    def __init__(self) -> None:
        self.drag: dict = {
            'active': False,
            'button': 0,
            'start_x': 0,
            'start_y': 0,
            'start_pan_x': 0,
            'start_pan_y': 0,
            'is_panning': False,
            'is_rect_selecting': False,
            'is_transforming': False,
        }
        self.arc: dict = {
            'source': None,
            'cursor_pos': (0, 0),
            'target_valid': None,
            'hovered_target': None,
            'ignore_next_release': False,
        }
        self.click: dict = {
            'last_click_time': 0.0,
            'last_click_obj': None,
            'double_click_threshold': 0.3,
            'pending_timeout': None,
            'pending_click_data': None,
        }
        self.lasso: dict = {
            'active': False,
            'selector': None,
        }

    # ------------------------------------------------------------------
    # Reset helpers (called from _reset_manager_for_load)
    # ------------------------------------------------------------------

    def reset_drag(self) -> None:
        """Reset drag state (prevents stuck panning/dragging after file load)."""
        self.drag.update({
            'active': False,
            'button': 0,
            'start_x': 0,
            'start_y': 0,
            'is_panning': False,
            'is_rect_selecting': False,
            'is_transforming': False,
        })

    def reset_arc(self) -> None:
        """Reset arc creation state (prevents stuck arc drawing after file load)."""
        self.arc.update({
            'source': None,
            'cursor_pos': (0, 0),
            'target_valid': None,
            'hovered_target': None,
            'ignore_next_release': False,
        })
