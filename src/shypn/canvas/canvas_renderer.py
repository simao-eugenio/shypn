"""Concrete canvas renderer — full-frame draw and arc-preview pipeline.

Sprint 21 — Phase 7 OOP refactor.
Extracted from :class:`~shypn.helpers.model_canvas_loader.ModelCanvasLoader`.
"""

from __future__ import annotations

__all__ = ["CanvasRenderer"]

import math
import logging
from typing import Any, Dict

from shypn.canvas.abstract_canvas_renderer import AbstractCanvasRenderer

logger = logging.getLogger(__name__)

try:
    from shypn.netobjs import Place, Transition
except Exception:  # pragma: no cover
    Place = Transition = None


class CanvasRenderer(AbstractCanvasRenderer):  # type: ignore[misc]
    """Stateless-ish renderer; only dependency is the shared *canvas_ctx* dict.

    Args:
        canvas_ctx: The ``_canvas_ctx`` mapping
            ``{drawing_area: CanvasInteractionContext}`` owned by MCL.
    """

    __slots__ = ("_canvas_ctx",)

    def __init__(self, canvas_ctx: Dict[Any, Any]) -> None:
        self._canvas_ctx = canvas_ctx

    # ------------------------------------------------------------------
    # AbstractCanvasRenderer interface
    # ------------------------------------------------------------------

    def render_frame(
        self,
        drawing_area: Any,
        cr: Any,
        width: int,
        height: int,
        manager: Any,
    ) -> None:
        """Full-frame draw callback.

        Uses Cairo transformation approach (legacy-compatible):
        - Apply cr.scale() and cr.translate() for automatic coordinate
          transformation.
        - Objects render in world coordinates, Cairo scales them automatically.
        - Line widths compensated to maintain constant pixel size.
        - Grid drawn BEFORE rotation (stays fixed in screen space).
        - Model objects drawn AFTER rotation (rotate with canvas).
        """
        if manager.viewport_width != width or manager.viewport_height != height:
            manager.set_viewport_size(width, height)

        # Execute deferred fit_to_page if pending (after viewport size is known)
        if getattr(manager, '_fit_to_page_pending', False):
            horizontal_offset = getattr(manager, '_fit_to_page_horizontal_offset', 0)
            vertical_offset = getattr(manager, '_fit_to_page_vertical_offset', 0)
            manager._fit_to_page_pending = False
            manager.fit_to_page(
                padding_percent=manager._fit_to_page_padding,
                deferred=False,
                horizontal_offset_percent=horizontal_offset,
                vertical_offset_percent=vertical_offset,
            )

        cr.set_source_rgb(1.0, 1.0, 1.0)
        cr.paint()

        cr.save()

        # STEP 1: zoom + pan
        cr.translate(manager.pan_x * manager.zoom, manager.pan_y * manager.zoom)
        cr.scale(manager.zoom, manager.zoom)

        # STEP 2: rotation around viewport centre
        center_world_x = width / (2.0 * manager.zoom) - manager.pan_x
        center_world_y = height / (2.0 * manager.zoom) - manager.pan_y

        rotation = manager.transformation_manager.get_rotation()
        if rotation and rotation.angle_degrees != 0:
            cr.translate(center_world_x, center_world_y)
            cr.rotate(rotation.angle_radians)
            cr.translate(-center_world_x, -center_world_y)

        # STEP 3: grid (screen-space, stays fixed)
        manager.draw_grid(cr)

        # STEP 4: Petri net objects
        for obj in manager.get_all_objects():
            obj.render(cr, zoom=manager.zoom)

        manager.editing_transforms.render_selection_layer(cr, manager, manager.zoom)
        manager.rectangle_selection.render(cr, manager.zoom)

        # Lasso tool
        ctx = self._canvas_ctx.get(drawing_area)
        if ctx and ctx.lasso.get('active', False) and ctx.lasso.get('selector'):
            ctx.lasso['selector'].render_lasso(cr, manager.zoom)

        # Arc-creation highlights (source / hovered target)
        if ctx:
            arc_state = ctx.arc
            source = arc_state.get('source')

            if source is not None:
                cr.set_source_rgba(0.2, 0.9, 0.2, 0.6)
                cr.set_line_width(4.0 / manager.zoom)

                if isinstance(source, Place):
                    cr.arc(source.x, source.y, source.radius + 6, 0, 2 * math.pi)
                    cr.stroke()
                elif isinstance(source, Transition):
                    w = source.width if source.horizontal else source.height
                    h = source.height if source.horizontal else source.width
                    cr.rectangle(source.x - w / 2 - 6, source.y - h / 2 - 6,
                                 w + 12, h + 12)
                    cr.stroke()

            hovered = arc_state.get('hovered_target')
            target_valid = arc_state.get('target_valid')

            if hovered is not None and target_valid is not None:
                cr.set_source_rgba(
                    0.2, 0.9, 0.2, 0.5) if target_valid else cr.set_source_rgba(
                    0.9, 0.2, 0.2, 0.5)
                cr.set_line_width(3.0 / manager.zoom)

                if isinstance(hovered, Place):
                    cr.arc(hovered.x, hovered.y, hovered.radius + 4, 0, 2 * math.pi)
                    cr.stroke()
                elif isinstance(hovered, Transition):
                    w = hovered.width if hovered.horizontal else hovered.height
                    h = hovered.height if hovered.horizontal else hovered.width
                    cr.rectangle(hovered.x - w / 2 - 4, hovered.y - h / 2 - 4,
                                 w + 8, h + 8)
                    cr.stroke()

        cr.restore()

        # Arc preview drawn in screen coordinates (outside save/restore)
        if ctx:
            arc_state = ctx.arc
            if (manager.is_tool_active()
                    and manager.get_tool() == 'arc'
                    and arc_state['source'] is not None):
                self.render_arc_preview(cr, arc_state, manager)

        manager.mark_canvas_clean()

    def render_arc_preview(
        self,
        cr: Any,
        arc_state: Dict[str, Any],
        manager: Any,
    ) -> None:
        """Draw orange preview line + arrowhead for in-progress arc creation."""
        source = arc_state['source']
        cursor_x, cursor_y = arc_state['cursor_pos']
        hovered_target = arc_state.get('hovered_target')

        src_x, src_y = source.x, source.y
        dx = cursor_x - src_x
        dy = cursor_y - src_y
        dist = math.sqrt(dx * dx + dy * dy)
        if dist < 1:
            return
        ux, uy = dx / dist, dy / dist

        # Source boundary point
        if isinstance(source, Place):
            src_radius = source.radius
        elif isinstance(source, Transition):
            w = source.width if source.horizontal else source.height
            h = source.height if source.horizontal else source.width
            src_radius = max(w, h) / 2.0
        else:
            src_radius = 20.0
        start_x = src_x + ux * src_radius
        start_y = src_y + uy * src_radius

        end_x, end_y = cursor_x, cursor_y
        parallel_offset = 0.0

        if hovered_target and hovered_target != source:
            # Check for existing parallel arcs
            existing_arcs = [
                arc for arc in manager.arcs
                if (arc.source == source and arc.target == hovered_target)
                or (arc.source == hovered_target and arc.target == source)
            ]
            if existing_arcs:
                existing_arc = existing_arcs[0]
                same_direction = (
                    existing_arc.source == source and existing_arc.target == hovered_target
                )
                opposite_direction = (
                    existing_arc.source == hovered_target
                    and existing_arc.target == source
                )
                if opposite_direction:
                    parallel_offset = -50.0
                elif same_direction:
                    parallel_offset = 15.0

            if isinstance(hovered_target, (Place, Transition)):
                tgt_x, tgt_y = hovered_target.x, hovered_target.y
                dx_t = tgt_x - src_x
                dy_t = tgt_y - src_y
                dist_t = math.sqrt(dx_t * dx_t + dy_t * dy_t)
                if dist_t > 1e-6:
                    ux_t, uy_t = dx_t / dist_t, dy_t / dist_t
                    if isinstance(hovered_target, Place):
                        tgt_r = hovered_target.radius
                    elif isinstance(hovered_target, Transition):
                        w = (hovered_target.width if hovered_target.horizontal
                             else hovered_target.height)
                        h = (hovered_target.height if hovered_target.horizontal
                             else hovered_target.width)
                        tgt_r = max(w, h) / 2.0
                    else:
                        tgt_r = 20.0
                    end_x = tgt_x - ux_t * tgt_r
                    end_y = tgt_y - uy_t * tgt_r

        if abs(parallel_offset) > 1e-6:
            perp_x, perp_y = -uy, ux
            start_x += perp_x * parallel_offset
            start_y += perp_y * parallel_offset
            end_x += perp_x * parallel_offset
            end_y += perp_y * parallel_offset

        start_sx, start_sy = manager.world_to_screen(start_x, start_y)
        end_sx, end_sy = manager.world_to_screen(end_x, end_y)

        cr.set_source_rgba(0.95, 0.5, 0.1, 0.85)
        cr.set_line_width(2.0)
        cr.move_to(start_sx, start_sy)
        cr.line_to(end_sx, end_sy)
        cr.stroke()

        # Arrowhead
        arrow_len = 11.0
        arrow_width = 6.0
        angle = math.atan2(end_y - start_y, end_x - start_x)
        left_x = (end_sx - arrow_len * math.cos(angle)
                  + arrow_width * math.sin(angle))
        left_y = (end_sy - arrow_len * math.sin(angle)
                  - arrow_width * math.cos(angle))
        right_x = (end_sx - arrow_len * math.cos(angle)
                   - arrow_width * math.sin(angle))
        right_y = (end_sy - arrow_len * math.sin(angle)
                   + arrow_width * math.cos(angle))
        cr.move_to(end_sx, end_sy)
        cr.line_to(left_x, left_y)
        cr.line_to(right_x, right_y)
        cr.close_path()
        cr.fill()
