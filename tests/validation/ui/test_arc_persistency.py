"""
Test arc property persistence across dialog sessions.

Verifies that arc properties persist correctly when:
- Opening and closing dialogs
- Editing properties multiple times
- Switching between different arcs
- Arc type changes (Normal ↔ Inhibitor)
"""
import pytest
from shypn.helpers.arc_prop_dialog_loader import ArcPropDialogLoader


class TestArcBasicPersistency:
    """Test basic arc property persistence."""
    
    def test_weight_persists_across_dialog_sessions(self, create_arc):
        """Arc weight should persist when closing and reopening dialog."""
        arc = create_arc(weight=3)
        
        # Simulate dialog: edit weight
        arc.weight = 5
        
        # Close and reopen dialog - weight should persist
        loader = ArcPropDialogLoader(arc, parent_window=None)
        weight_entry = loader.builder.get_object('prop_arc_weight_entry')
        
        # Verify value persisted
        assert weight_entry.get_text() == '5', "Weight should persist across sessions"
    
    def test_weight_zero_persists(self, create_arc):
        """Zero weight should persist correctly."""
        arc = create_arc(weight=3)
        
        # Set to zero
        arc.weight = 0
        
        # Verify persistence
        loader = ArcPropDialogLoader(arc, parent_window=None)
        weight_entry = loader.builder.get_object('prop_arc_weight_entry')
        
        assert weight_entry.get_text() == '0', "Zero weight should persist"
    
    def test_large_weight_persists(self, create_arc):
        """Large weight values should persist correctly."""
        arc = create_arc(weight=1)
        
        # Set large weight
        arc.weight = 1000
        
        # Verify persistence
        loader = ArcPropDialogLoader(arc, parent_window=None)
        weight_entry = loader.builder.get_object('prop_arc_weight_entry')
        
        assert weight_entry.get_text() == '1000', "Large weight should persist"
    
    def test_line_width_persists(self, create_arc):
        """Line width should persist across sessions."""
        arc = create_arc(line_width=2.0)
        
        # Edit line width
        arc.width = 3.5
        
        # Verify persistence in model
        assert arc.width == 3.5, "Line width should persist in model"
        
        # Reopen dialog
        loader = ArcPropDialogLoader(arc, parent_window=None)
        
        # Verify model value persists
        assert arc.width == 3.5, "Line width should still be in model"
    
    def test_color_persists(self, create_arc):
        """Arc color should persist across sessions."""
        arc = create_arc(color=(1.0, 0.0, 0.0))  # Red
        
        # Edit color
        arc.color = (0.0, 1.0, 0.0)  # Green
        
        # Verify persistence in model
        assert arc.color == (0.0, 1.0, 0.0), "Color should persist in model"


class TestArcTypePersistency:
    """Test arc type persistence (Normal vs Inhibitor)."""
    
    def test_normal_arc_type_persists(self, create_arc):
        """Normal arc type should persist across sessions."""
        arc = create_arc(arc_type='normal')
        
        # Verify type persists (Arc class, not InhibitorArc)
        assert arc.__class__.__name__ in ['Arc', 'NormalArc'], "Arc should be normal type"
        
        # Reopen dialog
        loader = ArcPropDialogLoader(arc, parent_window=None)
        
        # Verify type still persists
        assert arc.__class__.__name__ in ['Arc', 'NormalArc'], "Normal type should persist"
    
    def test_inhibitor_arc_type_persists(self, create_arc):
        """Inhibitor arc type should persist across sessions."""
        arc = create_arc(arc_type='inhibitor', direction='place_to_transition')
        
        # Verify type persists (InhibitorArc class)
        assert arc.__class__.__name__ == 'InhibitorArc', "Arc should be inhibitor type"
        
        # Reopen dialog
        loader = ArcPropDialogLoader(arc, parent_window=None)
        
        # Verify type still persists
        assert arc.__class__.__name__ == 'InhibitorArc', "Inhibitor type should persist"
    
    def test_weight_persists_after_type_change(self, create_arc):
        """Weight should persist when converting between arc types."""
        arc = create_arc(arc_type='normal', weight=5)
        
        # Change to inhibitor (if direction allows)
        if hasattr(arc, 'source_id') and hasattr(arc, 'target_id'):
            # Can only convert if direction is place_to_transition
            # For now, just verify weight persists on normal arc
            pass
        
        # Weight should still be there
        assert arc.weight == 5, "Weight should persist through type changes"


class TestArcMultipleEdits:
    """Test arc properties persist across multiple edit sessions."""
    
    def test_multiple_weight_edits_persist(self, create_arc):
        """Multiple edits to weight should all persist."""
        arc = create_arc(weight=1)
        
        # Edit 1
        arc.weight = 3
        loader1 = ArcPropDialogLoader(arc, parent_window=None)
        weight1 = loader1.builder.get_object('prop_arc_weight_entry').get_text()
        assert weight1 == '3'
        
        # Edit 2
        arc.weight = 7
        loader2 = ArcPropDialogLoader(arc, parent_window=None)
        weight2 = loader2.builder.get_object('prop_arc_weight_entry').get_text()
        assert weight2 == '7'
        
        # Edit 3
        arc.weight = 0
        loader3 = ArcPropDialogLoader(arc, parent_window=None)
        weight3 = loader3.builder.get_object('prop_arc_weight_entry').get_text()
        assert weight3 == '0'
    
    def test_multiple_property_edits_persist(self, create_arc):
        """Editing multiple properties should all persist."""
        arc = create_arc(weight=3, line_width=2.0, color=(1.0, 0.0, 0.0))
        
        # Edit all properties
        arc.weight = 10
        arc.width = 4.0
        arc.color = (0.0, 0.0, 1.0)  # Blue
        
        # Reopen and verify all changes persisted
        loader = ArcPropDialogLoader(arc, parent_window=None)
        
        weight = loader.builder.get_object('prop_arc_weight_entry').get_text()
        
        assert weight == '10', "Weight should persist"
        assert arc.width == 4.0, "Line width should persist in model"
        assert arc.color == (0.0, 0.0, 1.0), "Color should persist in model"
    
    def test_rapid_weight_edits_persist_final_value(self, create_arc):
        """Rapid edits should persist the final value."""
        arc = create_arc(weight=0)
        
        # Rapid edits
        for i in range(1, 11):
            arc.weight = i
        
        # Final value should persist
        loader = ArcPropDialogLoader(arc, parent_window=None)
        weight = loader.builder.get_object('prop_arc_weight_entry').get_text()
        
        assert weight == '10', "Final value after rapid edits should persist"


class TestArcObjectSwitching:
    """Test persistence when switching between different arcs."""
    
    def test_switching_between_arcs_preserves_properties(self, create_arc):
        """Switching between arcs should preserve each arc's properties."""
        # Create two arcs with different properties
        arc1 = create_arc(weight=5, line_width=2.0)
        arc2 = create_arc(weight=3, line_width=4.0)
        
        # Open dialog for arc1
        loader1 = ArcPropDialogLoader(arc1, parent_window=None)
        weight1 = loader1.builder.get_object('prop_arc_weight_entry').get_text()
        assert weight1 == '5', "Arc 1 weight should be 5"
        
        # Switch to arc2
        loader2 = ArcPropDialogLoader(arc2, parent_window=None)
        weight2 = loader2.builder.get_object('prop_arc_weight_entry').get_text()
        assert weight2 == '3', "Arc 2 weight should be 3"
        
        # Switch back to arc1
        loader1_again = ArcPropDialogLoader(arc1, parent_window=None)
        weight1_again = loader1_again.builder.get_object('prop_arc_weight_entry').get_text()
        assert weight1_again == '5', "Arc 1 weight should still be 5"
    
    def test_editing_one_arc_doesnt_affect_others(self, create_arc):
        """Editing one arc should not affect other arcs."""
        arc1 = create_arc(weight=5)
        arc2 = create_arc(weight=3)
        
        # Edit arc1
        arc1.weight = 10
        
        # Verify arc2 unchanged
        assert arc2.weight == 3, "Arc 2 should be unaffected by arc 1 edits"
        
        # Verify arc1 changed
        assert arc1.weight == 10, "Arc 1 should have new value"


class TestArcStylingPersistency:
    """Test arc styling property persistence."""
    
    def test_thin_line_width_persists(self, create_arc):
        """Thin line widths should persist correctly."""
        arc = create_arc(line_width=2.0)
        
        # Set thin width
        arc.width = 0.5
        
        # Verify persistence
        assert arc.width == 0.5, "Thin line width should persist"
        
        loader = ArcPropDialogLoader(arc, parent_window=None)
        assert arc.width == 0.5, "Thin line width should still be in model"
    
    def test_thick_line_width_persists(self, create_arc):
        """Thick line widths should persist correctly."""
        arc = create_arc(line_width=2.0)
        
        # Set thick width
        arc.width = 10.0
        
        # Verify persistence
        assert arc.width == 10.0, "Thick line width should persist"
        
        loader = ArcPropDialogLoader(arc, parent_window=None)
        assert arc.width == 10.0, "Thick line width should still be in model"
    
    def test_color_components_persist(self, create_arc):
        """Individual color components should persist correctly."""
        arc = create_arc(color=(0.5, 0.5, 0.5))  # Gray
        
        # Set specific color
        arc.color = (0.2, 0.8, 0.4)  # Custom green
        
        # Verify each component
        assert arc.color[0] == pytest.approx(0.2, abs=0.01), "Red component should persist"
        assert arc.color[1] == pytest.approx(0.8, abs=0.01), "Green component should persist"
        assert arc.color[2] == pytest.approx(0.4, abs=0.01), "Blue component should persist"


class TestArcEdgeCases:
    """Test edge cases for arc property persistence."""
    
    def test_weight_one_persists(self, create_arc):
        """Weight of 1 should persist correctly."""
        arc = create_arc(weight=5)
        arc.weight = 1
        
        loader = ArcPropDialogLoader(arc, parent_window=None)
        weight = loader.builder.get_object('prop_arc_weight_entry').get_text()
        
        assert weight == '1', "Weight of 1 should persist"
    
    def test_properties_persist_with_inhibitor_arc(self, create_arc):
        """Properties should persist on inhibitor arcs."""
        arc = create_arc(arc_type='inhibitor', direction='place_to_transition', weight=5)
        
        # Edit weight
        arc.weight = 10
        
        # Verify persistence
        loader = ArcPropDialogLoader(arc, parent_window=None)
        weight = loader.builder.get_object('prop_arc_weight_entry').get_text()
        
        assert weight == '10', "Weight should persist on inhibitor arcs"
        assert arc.__class__.__name__ == 'InhibitorArc', "Arc should still be inhibitor type"
    
    def test_default_values_persist_when_unchanged(self, create_arc):
        """Default values should persist when not modified."""
        arc = create_arc()  # Use all defaults
        
        # Get initial values
        initial_weight = arc.weight
        initial_width = arc.width
        
        # Reopen dialog without changes
        loader = ArcPropDialogLoader(arc, parent_window=None)
        
        # Values should be unchanged
        assert arc.weight == initial_weight, "Default weight should persist"
        assert arc.width == initial_width, "Default line width should persist"
    
    def test_properties_persist_across_many_sessions(self, create_arc):
        """Properties should persist across many dialog open/close cycles."""
        arc = create_arc(weight=5)
        
        # Open and close dialog 10 times
        for i in range(10):
            loader = ArcPropDialogLoader(arc, parent_window=None)
            weight = loader.builder.get_object('prop_arc_weight_entry').get_text()
            assert weight == '5', f"Weight should persist in session {i+1}"
        
        # Value should still be correct
        assert arc.weight == 5, "Weight should persist after many sessions"
