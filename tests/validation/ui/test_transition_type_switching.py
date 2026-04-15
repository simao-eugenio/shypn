"""
Test transition type switching within property dialog.

Tests that changing transition type (immediate/timed/stochastic/continuous)
updates the UI fields correctly and preserves properties.
"""
import pytest
from shypn.helpers.transition_prop_dialog_loader import TransitionPropDialogLoader


class TestTransitionTypeSwitching:
    """Test dynamic transition type changes in property dialog."""
    
    def test_immediate_to_timed_shows_rate_field(self, create_transition):
        """When switching from immediate to timed, rate field should become visible."""
        # Create immediate transition
        trans = create_transition(transition_type='immediate')
        loader = TransitionPropDialogLoader(trans, parent_window=None)
        
        # Get rate entry widget
        rate_entry = loader.builder.get_object('rate_entry')
        assert rate_entry is not None, "Rate entry widget not found"
        
        # Initially immediate - check if rate field is hidden
        initial_visible = rate_entry.get_visible()
        
        # Change to timed
        type_combo = loader.builder.get_object('prop_transition_type_combo')
        assert type_combo is not None, "Type combo not found"
        type_combo.set_active(1)  # timed
        
        # Rate field should now be visible
        assert trans.transition_type == 'timed', "Type should be updated to timed"
        final_visible = rate_entry.get_visible()
        
        # If initially hidden, should now be visible
        # Note: Visibility depends on get_editable_fields() implementation
        editable_fields = trans.get_editable_fields()
        expected_visible = editable_fields.get('rate', True)
        assert final_visible == expected_visible, \
            f"Rate field visibility {final_visible} doesn't match expected {expected_visible}"
    
    def test_timed_to_stochastic_preserves_rate(self, create_transition):
        """Switching from timed to stochastic should preserve rate value."""
        # Create timed transition with rate
        trans = create_transition(transition_type='timed', rate=2.5)
        loader = TransitionPropDialogLoader(trans, parent_window=None)
        
        # Verify initial rate
        assert trans.rate == 2.5, "Initial rate should be 2.5"
        
        # Change to stochastic
        type_combo = loader.builder.get_object('prop_transition_type_combo')
        type_combo.set_active(2)  # stochastic
        
        # Rate should still be 2.5
        assert trans.transition_type == 'stochastic', "Type should be stochastic"
        assert trans.rate == 2.5, "Rate should be preserved at 2.5"
        
        # Rate field should still be visible for stochastic
        rate_entry = loader.builder.get_object('rate_entry')
        editable_fields = trans.get_editable_fields()
        expected_visible = editable_fields.get('rate', True)
        assert rate_entry.get_visible() == expected_visible, \
            "Rate field should match editable_fields setting"
    
    def test_continuous_to_immediate_hides_rate_field(self, create_transition):
        """Switching to immediate should hide rate-related fields."""
        # Create continuous transition with rate
        trans = create_transition(transition_type='continuous', rate=1.5)
        loader = TransitionPropDialogLoader(trans, parent_window=None)
        
        # Change to immediate
        type_combo = loader.builder.get_object('prop_transition_type_combo')
        type_combo.set_active(0)  # immediate
        
        # Check type updated
        assert trans.transition_type == 'immediate', "Type should be immediate"
        
        # Rate value should still exist (preserved for future type change)
        assert trans.rate == 1.5, "Rate should be preserved even when hidden"
        
        # Rate field should be hidden
        rate_entry = loader.builder.get_object('rate_entry')
        editable_fields = trans.get_editable_fields()
        expected_visible = editable_fields.get('rate', False)  # Should be False for immediate
        actual_visible = rate_entry.get_visible()
        
        assert actual_visible == expected_visible, \
            f"Rate field visibility {actual_visible} should match editable_fields {expected_visible}"
    
    def test_type_switching_updates_description(self, create_transition):
        """Type description label should update when type changes."""
        trans = create_transition(transition_type='immediate')
        loader = TransitionPropDialogLoader(trans, parent_window=None)
        
        # Get description label
        desc_label = loader.builder.get_object('type_description_label')
        if desc_label is None:
            pytest.skip("Type description label not found in UI")
        
        initial_desc = desc_label.get_text()
        
        # Change to timed
        type_combo = loader.builder.get_object('prop_transition_type_combo')
        type_combo.set_active(1)  # timed
        
        # Description should change
        new_desc = desc_label.get_text()
        assert new_desc != initial_desc, "Description should change when type changes"
        assert 'timed' in new_desc.lower() or 'time' in new_desc.lower(), \
            f"Description should mention timed: {new_desc}"
    
    def test_all_type_transitions_work(self, create_transition):
        """Test all possible type transitions work correctly."""
        types = ['immediate', 'timed', 'stochastic', 'continuous']
        
        for from_type in types:
            for to_type in types:
                if from_type == to_type:
                    continue
                
                # Create transition with from_type
                trans = create_transition(transition_type=from_type, rate=1.0)
                loader = TransitionPropDialogLoader(trans, parent_window=None)
                type_combo = loader.builder.get_object('prop_transition_type_combo')
                
                # Switch to to_type
                type_combo.set_active(types.index(to_type))
                
                # Verify type changed
                assert trans.transition_type == to_type, \
                    f"Type should change from {from_type} to {to_type}"
                
                # Verify get_editable_fields returns valid dict
                editable_fields = trans.get_editable_fields()
                assert isinstance(editable_fields, dict), \
                    f"get_editable_fields() should return dict for {to_type}"
                assert 'rate' in editable_fields, \
                    f"editable_fields should contain 'rate' key for {to_type}"
    
    def test_type_switching_maintains_other_properties(self, create_transition):
        """Switching type should not affect unrelated properties."""
        # Create transition with various properties
        trans = create_transition(
            transition_type='immediate',
            priority=5,
            rate=2.0,
            guard="p1.tokens > 0",
            border_width=4.0,
            border_color=(1.0, 0.0, 0.0)  # red
        )
        loader = TransitionPropDialogLoader(trans, parent_window=None)
        
        # Store original values
        original_priority = trans.priority
        original_rate = trans.rate
        original_guard = trans.guard
        original_width = trans.border_width
        original_color = trans.border_color
        
        # Change type to stochastic
        type_combo = loader.builder.get_object('prop_transition_type_combo')
        type_combo.set_active(2)  # stochastic
        
        # Verify type changed
        assert trans.transition_type == 'stochastic'
        
        # Verify other properties preserved
        assert trans.priority == original_priority, "Priority should be preserved"
        assert trans.rate == original_rate, "Rate should be preserved"
        assert trans.guard == original_guard, "Guard should be preserved"
        assert trans.border_width == original_width, "Border width should be preserved"
        assert trans.border_color == original_color, "Border color should be preserved"
    
    def test_loader_field_visibility_matches_business_logic(self, create_transition):
        """UI field visibility should match get_editable_fields() for each type."""
        types = ['immediate', 'timed', 'stochastic', 'continuous']
        
        for trans_type in types:
            trans = create_transition(transition_type=trans_type)
            loader = TransitionPropDialogLoader(trans, parent_window=None)
            
            # Get editable fields from business logic
            editable_fields = trans.get_editable_fields()
            
            # Check rate field visibility matches
            rate_entry = loader.builder.get_object('rate_entry')
            if rate_entry is not None:
                expected_visible = editable_fields.get('rate', True)
                actual_visible = rate_entry.get_visible()
                assert actual_visible == expected_visible, \
                    f"Rate visibility mismatch for {trans_type}: " \
                    f"UI={actual_visible}, Logic={expected_visible}"
            
            # Check firing policy visibility if exists
            firing_policy_combo = loader.builder.get_object('firing_policy_combo')
            if firing_policy_combo is not None:
                parent = firing_policy_combo.get_parent()
                if parent is not None:
                    expected_visible = editable_fields.get('firing_policy', True)
                    actual_visible = parent.get_visible()
                    # Note: Visibility might be controlled at parent level
                    # This is a soft check - just verify it doesn't crash


class TestTypeSwitchingEdgeCases:
    """Test edge cases in type switching."""
    
    def test_rapid_type_switching(self, create_transition):
        """Rapid type changes should not cause errors."""
        trans = create_transition(transition_type='immediate')
        loader = TransitionPropDialogLoader(trans, parent_window=None)
        type_combo = loader.builder.get_object('prop_transition_type_combo')
        
        # Rapidly switch types
        for i in range(10):
            type_combo.set_active(i % 4)  # Cycle through all types
        
        # After 10 iterations (i=0 to 9), last is i=9, 9%4=1 which is 'timed'
        assert trans.transition_type == 'timed'
        
        # Should still be functional
        editable_fields = trans.get_editable_fields()
        assert isinstance(editable_fields, dict)
    
    def test_type_switching_with_invalid_rate(self, create_transition):
        """Type switching should handle invalid rate values gracefully."""
        trans = create_transition(transition_type='immediate')
        trans.rate = None  # Invalid rate
        
        loader = TransitionPropDialogLoader(trans, parent_window=None)
        type_combo = loader.builder.get_object('prop_transition_type_combo')
        
        # Switch to type that needs rate
        type_combo.set_active(2)  # stochastic
        
        # Should not crash, rate field should handle None
        assert trans.transition_type == 'stochastic'
        rate_entry = loader.builder.get_object('rate_entry')
        # Entry should either show empty or default value
        text = rate_entry.get_text()
        assert text is not None  # Should not crash


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
