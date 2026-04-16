#!/usr/bin/env python3
"""CurvedSignalFlowArc - Signal flow arc with bezier curve path.

Combines signal flow semantics (information transfer with token consumption)
with curved rendering for bidirectional opposite arcs. Inherits curve geometry
from CurvedArc and signal flow behavior/styling from SignalFlowArc.

Typical Use Case:
- ATP → Transition (signal_flow, straight)
- Transition → ADP (normal, straight)
When these form opposing flows, both should use curved_opposite_signal_flow:
- ATP ⟿ Transition (dashed curved)
- Transition ⟿ ADP (dashed curved)

Visual Appearance:
- Dashed line (like SignalFlowArc)
- Bezier curve (like CurvedArc)  
- Light gray color (0.7, 0.7, 0.7)
- Angled arrowhead (signal flow style)
"""

from shypn.netobjs.curved_arc import CurvedArc
from shypn.netobjs.signal_flow_arc import SignalFlowArc


class CurvedSignalFlowArc(CurvedArc):
    """Signal flow arc rendered with bezier curve.
    
    Inherits:
    - Curve geometry and rendering from CurvedArc
    - Signal flow semantics and validation from SignalFlowArc
    - Dashed line rendering (overrides CurvedArc's solid line)
    
    Properties:
    - Connects to signal places (is_signal_place=True)
    - Consumes tokens (signal flow behavior)
    - Rendered with dashed curve (distinguishes from solid curved normal arcs)
    - Light gray color (0.7, 0.7, 0.7)
    
    Biological Example:
    - ATP_pool ⟿ T_cortex_synthesis (energy consumption)
    - T_cortex_synthesis ⟿ ADP_pool (energy product)
    Both arcs curve opposite to avoid visual overlap.
    """
    
    # Default styling matches SignalFlowArc
    DEFAULT_COLOR = SignalFlowArc.DEFAULT_COLOR  # (0.7, 0.7, 0.7) light gray
    
    def __init__(self, source, target, id: str, name: str, weight: float = 1):
        """Initialize a curved signal flow arc.
        
        Args:
            source: Source object (Place or Transition)
            target: Target object (Transition or Place)
            id: Unique identifier
            name: Unique name (e.g., "A1", "A2")
            weight: Arc weight (default 1.0, can be formula)
            
        Raises:
            ValueError: If neither source nor target is a signal place
        """
        # Initialize with CurvedArc geometry
        super().__init__(source, target, id, name, weight)

        # Thermodynamic constraint tuple Γ = (K, n, ε)
        # Mirrors SignalFlowArc: per-arc enzyme kinetics for θ_eff.
        # Default ε = 0 ⇒ θ_eff = 0 (backward compatible).
        self.michaelis_K: float = 0.0
        self.hill_n: float = 1.0
        self.suppression_epsilon: float = 0.0

        # Arrhenius temperature dependence (Phase 5)
        self.activation_energy: float = 0.0     # E_a in kJ/mol
        self.reference_temperature: float = 298.15  # T_ref in Kelvin

        # Enforce semantic color via ColorSchemaManager (light gray for signal flow)
        from shypn.utils.color_schema_manager import ColorSchemaManager
        ColorSchemaManager.reset_arc_color(self)

        # Enforce that every Place endpoint is a signal place (Ψ).
        # Signal flow arcs MUST connect to signal places — this is the one
        # structural restriction of the formalism.
        self._validate_signal_connection()
    
    def _validate_signal_connection(self):
        """Verify arc connects to at least one signal place.
        
        Reuses validation logic from SignalFlowArc.
        
        Raises:
            ValueError: If neither source nor target is a signal place
        """
        from shypn.netobjs.place import Place
        
        is_source_signal = (isinstance(self.source, Place) and 
                           getattr(self.source, 'is_signal_place', False))
        is_target_signal = (isinstance(self.target, Place) and 
                           getattr(self.target, 'is_signal_place', False))
        
        if not (is_source_signal or is_target_signal):
            raise ValueError(
                f"CurvedSignalFlowArc {self.id} must connect to at least one signal place. "
                f"Source: {self.source.name} (is_signal_place={is_source_signal}), "
                f"Target: {self.target.name} (is_signal_place={is_target_signal}). "
                f"Use CurvedArc for normal mass transfer or TestArc for catalytic read."
            )
    
    def consumes_tokens(self) -> bool:
        """Signal flow arcs consume tokens (unlike test arcs).
        
        Returns:
            bool: Always True (signal flow behavior)
        """
        return True

    # ── Thermodynamic constraint tuple Γ ──────────────────────────────

    @property
    def theta_eff(self) -> float:
        """Effective basin boundary from thermodynamic constraint tuple Γ.

        See SignalFlowArc.theta_eff for full documentation.

        Returns:
            float: Effective threshold in same units as marking (e.g. mM)
        """
        eps = self.suppression_epsilon
        if eps <= 0.0 or eps >= 1.0:
            return 0.0
        ratio = eps / (1.0 - eps)
        return self.michaelis_K * (ratio ** (1.0 / self.hill_n))

    def theta_eff_at(self, temperature: float) -> float:
        """Temperature-dependent θ_eff via Arrhenius K(T).

        See SignalFlowArc.theta_eff_at for full documentation.

        Args:
            temperature: Current temperature in Kelvin

        Returns:
            float: θ_eff at the given temperature
        """
        eps = self.suppression_epsilon
        if eps <= 0.0 or eps >= 1.0:
            return 0.0
        if temperature <= 0:
            return 0.0
        K_T = self._arrhenius_K(temperature)
        ratio = eps / (1.0 - eps)
        return K_T * (ratio ** (1.0 / self.hill_n))

    def _arrhenius_K(self, temperature: float) -> float:
        """Compute K(T) via Arrhenius equation.

        See SignalFlowArc._arrhenius_K for full documentation.
        """
        import math
        if self.activation_energy == 0.0 or temperature == self.reference_temperature:
            return self.michaelis_K
        R = 0.008314  # kJ/(mol·K)
        exponent = -(self.activation_energy / R) * (
            1.0 / temperature - 1.0 / self.reference_temperature
        )
        return self.michaelis_K * math.exp(exponent)

    @property
    def commitment_marking(self) -> float:
        """Minimum marking for transition enablement: θ_eff + Ws."""
        try:
            ws = float(self.weight)
        except (TypeError, ValueError):
            ws = 0.0
        return self.theta_eff + ws

    def to_dict(self) -> dict:
        """Serialize to dictionary with arc_type='curved_opposite_signal_flow'.
        
        Returns:
            dict: Arc data with curved signal flow type identifier
        """
        data = super().to_dict()
        data['arc_type'] = 'curved_opposite_signal_flow'
        # Thermodynamic constraint tuple Γ (only when non-default)
        if self.michaelis_K != 0.0 or self.hill_n != 1.0 or self.suppression_epsilon != 0.0:
            data['michaelis_K'] = self.michaelis_K
            data['hill_n'] = self.hill_n
            data['suppression_epsilon'] = self.suppression_epsilon
        if self.activation_energy != 0.0:
            data['activation_energy'] = self.activation_energy
        if self.reference_temperature != 298.15:
            data['reference_temperature'] = self.reference_temperature
        return data

    @classmethod
    def from_dict(cls, data: dict, places: dict, transitions: dict) -> 'CurvedSignalFlowArc':
        """Create curved signal flow arc from dictionary, restoring Γ.

        Args:
            data: Dictionary containing arc properties
            places: Dictionary mapping place IDs to Place instances
            transitions: Dictionary mapping transition IDs to Transition instances

        Returns:
            CurvedSignalFlowArc with restored Γ = (K, n, ε)
        """
        arc = super().from_dict(data, places, transitions)
        arc.michaelis_K = float(data.get('michaelis_K', 0.0))
        arc.hill_n = float(data.get('hill_n', 1.0))
        arc.suppression_epsilon = float(data.get('suppression_epsilon', 0.0))
        arc.activation_energy = float(data.get('activation_energy', 0.0))
        arc.reference_temperature = float(data.get('reference_temperature', 298.15))
        return arc
    
    def render(self, cr, zoom):
        """Render curved signal flow arc with dashed line.
        
        Overrides CurvedArc.render() to add dashed line pattern for signal flow arcs.
        CurvedArc doesn't check _is_signal_arc() like Arc does, so we must manually
        set the dash pattern before calling the parent render.
        
        Args:
            cr: Cairo context
            zoom: Zoom factor for line widths
        """
        # Import here to get access to parent's render internals
        import math
        
        # Ensure clean Cairo context state
        cr.new_path()
        
        # Get source and target positions in world space
        src_world_x, src_world_y = self.source.x, self.source.y
        tgt_world_x, tgt_world_y = self.target.x, self.target.y
        
        # Check if manual control point is set (from transformation)
        if hasattr(self, 'manual_control_point') and self.manual_control_point is not None:
            # Use manual control point directly
            control_point = self.manual_control_point
        else:
            # Check for parallel arcs and calculate offset for control point
            offset_distance = None  # None = use default 20% offset
            if hasattr(self, '_manager') and self._manager:
                parallels = self._manager.detect_parallel_arcs(self)
                if parallels:
                    offset_distance = self._manager.calculate_arc_offset(self, parallels)
            
            # Calculate control point with optional offset
            control_point = self._calculate_curve_control_point(offset=offset_distance)
        
        if control_point is None:
            # Degenerate case: render as straight dashed line
            cr.set_dash([8.0 / zoom, 4.0 / zoom])
            super(CurvedArc, self).render(cr, zoom)  # Call Arc.render()
            cr.set_dash([])
            return
        
        cp_x, cp_y = control_point
        
        # Calculate direction for boundary points
        # Tangent at start: direction from source to control point
        dx_start = cp_x - src_world_x
        dy_start = cp_y - src_world_y
        length_start = math.sqrt(dx_start*dx_start + dy_start*dy_start)
        
        if length_start < 1e-6:
            cr.set_dash([8.0 / zoom, 4.0 / zoom])
            super(CurvedArc, self).render(cr, zoom)
            cr.set_dash([])
            return
        
        dx_start /= length_start
        dy_start /= length_start
        
        # Tangent at end: direction from control point to target
        dx_end = tgt_world_x - cp_x
        dy_end = tgt_world_y - cp_y
        length_end = math.sqrt(dx_end*dx_end + dy_end*dy_end)
        
        if length_end < 1e-6:
            cr.set_dash([8.0 / zoom, 4.0 / zoom])
            super(CurvedArc, self).render(cr, zoom)
            cr.set_dash([])
            return
        
        dx_end /= length_end
        dy_end /= length_end
        
        # Get boundary points in world space
        start_world_x, start_world_y = self._get_boundary_point(
            self.source, src_world_x, src_world_y, dx_start, dy_start)
        
        # Get arrowhead position at target boundary
        arrowhead_x, arrowhead_y = self._get_boundary_point(
            self.target, tgt_world_x, tgt_world_y, -dx_end, -dy_end)
        
        # Draw curve to a point just before the boundary
        pullback = 3.0 / zoom
        end_world_x = arrowhead_x - dx_end * pullback
        end_world_y = arrowhead_y - dy_end * pullback
        
        # Add glow effect for colored arcs (with same dash pattern as main line)
        if self.color != self.DEFAULT_COLOR:
            cr.move_to(start_world_x, start_world_y)
            cr.curve_to(cp_x, cp_y, cp_x, cp_y, end_world_x, end_world_y)
            r, g, b = self.color
            cr.set_source_rgba(r, g, b, 0.3)
            cr.set_line_width((self.width + 2) / max(zoom, 1e-6))
            cr.set_dash([8.0 / zoom, 4.0 / zoom])  # Match dashed pattern for glow
            cr.stroke()
        
        # Draw curved arc with DASHED pattern (signal flow style)
        cr.set_dash([8.0 / zoom, 4.0 / zoom])  # Match Arc._is_signal_arc() dash pattern
        cr.move_to(start_world_x, start_world_y)
        cr.curve_to(cp_x, cp_y, cp_x, cp_y, end_world_x, end_world_y)
        cr.set_source_rgb(*self.color)
        cr.set_line_width(self.width / max(zoom, 1e-6))
        cr.stroke()
        
        # Reset dash for arrowhead (always solid)
        cr.set_dash([])
        
        # Draw arrowhead at target boundary
        self._render_arrowhead(cr, arrowhead_x, arrowhead_y, dx_end, dy_end, zoom)
        
        # Draw weight label if != 1
        if abs(self.weight - 1.0) > 1e-6:
            offset_distance = None
            if hasattr(self, '_manager') and self._manager:
                parallels = self._manager.detect_parallel_arcs(self)
                if parallels:
                    offset_distance = self._manager.calculate_arc_offset(self, parallels)
            self._render_weight_curved(cr, start_world_x, start_world_y, 
                                      cp_x, cp_y, end_world_x, end_world_y, 
                                      zoom, offset_distance)
