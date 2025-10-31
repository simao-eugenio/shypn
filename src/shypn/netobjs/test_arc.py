#!/usr/bin/env python3
"""Test Arc (Read Arc) - Non-consuming arc for catalyst behavior.

Test arcs allow transitions to check token presence without consuming them.
Essential for modeling catalysts, enzymes, and regulatory molecules in biological Petri nets.
"""

from shypn.netobjs.arc import Arc


class TestArc(Arc):
    """
    Represents a test arc (read arc) in a Petri net - Biological PN / Catalyst Semantics.
    
    **BIOLOGICAL SEMANTICS** (Catalyst/Enzyme Behavior):
    A test arc allows a transition to fire based on the presence of tokens
    WITHOUT consuming them. This models catalysts that enable reactions but
    are not consumed in the process.
    
    **Key Properties**:
    - **Enabling Condition**: source.tokens >= weight (must have enough)
    - **Token Transfer**: NO - tokens are NOT consumed (catalyst behavior)
    - **Read-Only**: Catalyst concentration affects rate but remains unchanged
    
    **Visual Rendering**:
    - Dashed line with hollow diamond at target end
    - Clearly distinguishable from normal and inhibitor arcs
    - Diamond size scales with marker size
    
    **Biological Use Cases**:
    1. **Enzymes**: Hexokinase catalyzes glucose phosphorylation but isn't consumed
       ```
       Glucose + ATP --[enzyme: Hexokinase]--> Glucose-6-P + ADP
       Hexokinase modeled as test arc (read concentration, not consumed)
       ```
    
    2. **Cofactors**: NAD+ enables reactions but recycles
       ```
       Substrate --[cofactor: NAD+]--> Product
       NAD+ concentration affects rate but isn't depleted
       ```
    
    3. **Regulatory Proteins**: Transcription factors enable gene expression
       ```
       Gene --[TF: p53]--> mRNA
       p53 presence enables transcription but isn't consumed
       ```
    
    **Rate Formula Integration**:
    Test arcs model places that appear in rate formulas WITHOUT consumption arcs:
    ```python
    rate = k * [Substrate] * [Enzyme] / (Km + [Substrate])
                            ↑ Enzyme as test arc
    ```
    
    **Comparison with Other Arc Types**:
    
    | Arc Type | Consumes? | Enables When | Use Case |
    |----------|-----------|--------------|----------|
    | Normal   | YES       | tokens ≥ weight | Substrates, reactants |
    | Test     | NO        | tokens ≥ weight | Catalysts, enzymes |
    | Inhibitor| YES*      | tokens ≥ weight | Cooperation, sharing |
    
    *Inhibitor in Shypn uses Living Systems semantics (consumes).
    
    **Classical Petri Net Semantics** (for reference):
    In classical PNs, test arcs are also called "read arcs" and serve similar
    purpose but in discrete token semantics. Our implementation extends this
    to continuous biological semantics.
    
    **Implementation Notes**:
    - Direction: **Place → Transition ONLY** (testing source place)
    - Validation: Enforced in __init__ (raises ValueError if target is Place)
    - Simulation: Behavior classes must check arc type and skip consumption
    - Formula: Rate functions can reference test arc places without explicit arcs
    
    Example:
        >>> enzyme_place = Place(tokens=10, name="Hexokinase")
        >>> reaction = Transition(name="Glucose_phosphorylation")
        >>> test_arc = TestArc(enzyme_place, reaction, id="TA1", name="TestArc1", weight=1)
        >>> 
        >>> # Check enablement (like normal arc)
        >>> enabled = enzyme_place.tokens >= test_arc.weight  # True (10 >= 1)
        >>> 
        >>> # Fire transition
        >>> reaction.fire()
        >>> 
        >>> # Enzyme NOT consumed (key difference!)
        >>> print(enzyme_place.tokens)  # Still 10 (unchanged)
    """
    
    def __init__(self, source, target, id: str, name: str, weight: int = 1):
        """Initialize a test (read) arc.
        
        Args:
            source: Source Place (catalyst, enzyme, regulator)
            target: Target Transition (reaction that requires catalyst)
            id: Unique string identifier
            name: Unique name in format "TA1", "TA2", etc.
            weight: Minimum catalyst concentration required (default 1)
        
        Raises:
            ValueError: If source is not a Place or target is not a Transition
        
        Note:
            Test arcs can ONLY go from Place → Transition (not Transition → Place)
            because testing output places has no semantic meaning.
        """
        # Initialize as normal arc first (validation happens there)
        super().__init__(source, target, id, name, weight)
        
        # Additional validation: Test arcs can only be Place → Transition
        from shypn.netobjs.place import Place
        from shypn.netobjs.transition import Transition
        
        if not isinstance(source, Place):
            raise ValueError(
                f"Test arc source must be a Place (got {type(source).__name__}). "
                "Test arcs check token presence without consuming."
            )
        
        if not isinstance(target, Transition):
            raise ValueError(
                f"Test arc target must be a Transition (got {type(target).__name__}). "
                "Test arcs enable transitions based on catalyst presence."
            )
        
        # Visual styling for test arcs (distinguishable from normal arcs)
        self.color = (0.4, 0.4, 0.4)  # Gray (less prominent than normal arcs)
        self.width = 2.5  # Slightly thinner to indicate non-consumption
    
    @property
    def arc_type(self) -> str:
        """Get arc type identifier.
        
        Returns:
            str: "test" for test arcs
        """
        return "test"
    
    def is_test_arc(self) -> bool:
        """Check if this is a test arc.
        
        Returns:
            bool: Always True for TestArc instances
        """
        return True
    
    def consumes_tokens(self) -> bool:
        """Check if this arc consumes tokens on firing.
        
        Returns:
            bool: False - test arcs never consume (catalyst behavior)
        """
        return False
    
    def to_dict(self):
        """Serialize test arc to dictionary.
        
        Returns:
            dict: Arc data with arc_type="test"
        """
        data = super().to_dict()
        data['arc_type'] = 'test'
        data['consumes'] = False  # Explicit marker for simulation
        return data
    
    def _render_arrow(self, cr, x2: float, y2: float, dx: float, dy: float, zoom: float = 1.0):
        """Render hollow diamond endpoint for test arcs.
        
        Test arcs use a hollow diamond to clearly distinguish from:
        - Normal arcs (solid triangle)
        - Inhibitor arcs (hollow circle)
        
        Args:
            cr: Cairo context
            x2: End point X coordinate
            y2: End point Y coordinate
            dx: Direction vector X component
            dy: Direction vector Y component
            zoom: Current zoom level (default 1.0)
        """
        # Diamond size (scales with zoom)
        diamond_size = 12.0 / zoom  # Base size 12px
        
        # Normalize direction vector
        length = (dx * dx + dy * dy) ** 0.5
        if length > 0:
            dx = dx / length
            dy = dy / length
        
        # Calculate diamond points
        # Diamond oriented with long axis along arc direction
        half_width = diamond_size * 0.4  # Width perpendicular to arc
        
        # Point 1: Tip (at arc end)
        tip_x = x2
        tip_y = y2
        
        # Point 2: Left (perpendicular)
        left_x = x2 - dx * diamond_size * 0.5 - dy * half_width
        left_y = y2 - dy * diamond_size * 0.5 + dx * half_width
        
        # Point 3: Base (back along arc)
        base_x = x2 - dx * diamond_size
        base_y = y2 - dy * diamond_size
        
        # Point 4: Right (perpendicular)
        right_x = x2 - dx * diamond_size * 0.5 + dy * half_width
        right_y = y2 - dy * diamond_size * 0.5 - dx * half_width
        
        # Draw hollow diamond
        cr.move_to(tip_x, tip_y)
        cr.line_to(left_x, left_y)
        cr.line_to(base_x, base_y)
        cr.line_to(right_x, right_y)
        cr.close_path()
        
        # Fill with white (hollow)
        cr.set_source_rgb(1.0, 1.0, 1.0)
        cr.fill_preserve()
        
        # Stroke with arc color
        cr.set_source_rgb(*self.color)
        cr.set_line_width(self.width / zoom)
        cr.stroke()
    
    def render(self, cr, zoom: float = 1.0, selected: bool = False):
        """Render test arc with dashed line and hollow diamond.
        
        Test arcs use:
        - Dashed line pattern (indicates non-consumption)
        - Hollow diamond endpoint (catalyst symbol)
        - Gray color (less prominent than normal arcs)
        - Perimeter-to-perimeter connection (like normal arcs)
        
        Args:
            cr: Cairo context for rendering
            zoom: Current zoom level (default 1.0)
            selected: Whether arc is selected (default False)
        """
        # Get source and target CENTER positions
        src_world_x, src_world_y = self.source.x, self.source.y
        tgt_world_x, tgt_world_y = self.target.x, self.target.y
        
        # Calculate direction from centers
        dx_world = tgt_world_x - src_world_x
        dy_world = tgt_world_y - src_world_y
        length_world = (dx_world * dx_world + dy_world * dy_world) ** 0.5
        
        if length_world < 1:
            return  # Zero-length arc, skip rendering
        
        # Normalize direction
        dx_world /= length_world
        dy_world /= length_world
        
        # Get BOUNDARY points (perimeter-to-perimeter connection)
        start_world_x, start_world_y = self._get_boundary_point(
            self.source, src_world_x, src_world_y, dx_world, dy_world)
        end_world_x, end_world_y = self._get_boundary_point(
            self.target, tgt_world_x, tgt_world_y, -dx_world, -dy_world)
        
        # Use boundary points for rendering (not centers)
        x1, y1 = start_world_x, start_world_y
        x2, y2 = end_world_x, end_world_y
        
        # Recalculate direction and length from boundary points
        dx = x2 - x1
        dy = y2 - y1
        length = (dx * dx + dy * dy) ** 0.5
        
        if length < 1:
            return  # Too short after boundary adjustment
        
        # Normalize direction
        dx = dx / length
        dy = dy / length
        
        # Shorten line to stop before diamond (12px in world space)
        diamond_offset = 12.0 / zoom
        end_x = x2 - dx * diamond_offset
        end_y = y2 - dy * diamond_offset
        
        # Draw dashed line
        cr.save()
        if selected:
            cr.set_source_rgb(1.0, 0.5, 0.0)  # Orange when selected
        else:
            cr.set_source_rgb(*self.color)
        
        cr.set_line_width(self.width / zoom)
        
        # Set dash pattern: [dash_length, gap_length]
        dash_length = 8.0 / zoom
        gap_length = 4.0 / zoom
        cr.set_dash([dash_length, gap_length])
        
        cr.move_to(x1, y1)
        cr.line_to(end_x, end_y)
        cr.stroke()
        cr.restore()
        
        # Draw hollow diamond at target boundary
        self._render_arrow(cr, x2, y2, dx, dy, zoom)
        
        # Render weight label if not 1 (use boundary points for positioning)
        if self.weight != 1:
            self._render_weight(cr, x1, y1, x2, y2, zoom)
    
    def __repr__(self):
        """String representation for debugging.
        
        Returns:
            str: Description of test arc
        """
        return (
            f"TestArc(id={self.id}, name={self.name}, "
            f"source={self.source.name}, target={self.target.name}, "
            f"weight={self.weight}, consumes=False)"
        )
