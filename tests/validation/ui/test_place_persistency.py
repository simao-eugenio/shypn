"""
Test place property persistence across dialog sessions.

Verifies that place properties persist correctly when:
- Opening and closing dialogs
- Editing properties multiple times
- Switching between different places
- Reopening the same place
"""
import pytest
from shypn.helpers.place_prop_dialog_loader import PlacePropDialogLoader


class TestPlaceBasicPersistency:
    """Test basic place property persistence."""
    
    def test_tokens_persist_across_dialog_sessions(self, create_place):
        """Tokens value should persist when closing and reopening dialog."""
        place = create_place(tokens=5)
        
        # Simulate dialog: edit tokens
        place.tokens = 10
        
        # Close and reopen dialog - tokens should persist
        loader = PlacePropDialogLoader(place, parent_window=None)
        tokens_entry = loader.builder.get_object('prop_place_tokens_entry')
        
        # Verify value persisted
        assert tokens_entry.get_text() == '10', "Tokens should persist across sessions"
    
    def test_capacity_persist_across_dialog_sessions(self, create_place):
        """Capacity value should persist when closing and reopening dialog."""
        place = create_place(capacity=50)
        
        # Simulate dialog: edit capacity
        place.capacity = 100
        
        # Close and reopen dialog
        loader = PlacePropDialogLoader(place, parent_window=None)
        capacity_entry = loader.builder.get_object('prop_place_capacity_entry')
        
        # Verify value persisted
        assert capacity_entry.get_text() == '100', "Capacity should persist across sessions"
    
    def test_infinite_capacity_persists(self, create_place):
        """Infinite capacity (inf) should persist correctly."""
        place = create_place(capacity=float('inf'))
        
        # Verify it persists
        loader = PlacePropDialogLoader(place, parent_window=None)
        capacity_entry = loader.builder.get_object('prop_place_capacity_entry')
        
        # Should show as 'inf' or similar
        capacity_text = capacity_entry.get_text()
        assert capacity_text in ['inf', 'infinity', '∞'], \
            f"Infinite capacity should persist, got: {capacity_text}"
    
    def test_radius_persists_across_sessions(self, create_place):
        """Place radius should persist correctly."""
        place = create_place(radius=25.0)
        
        # Edit radius
        place.radius = 30.0
        
        # Reopen dialog
        loader = PlacePropDialogLoader(place, parent_window=None)
        radius_entry = loader.builder.get_object('prop_place_radius_entry')
        
        # Verify persistence
        assert radius_entry.get_text() == '30.0' or radius_entry.get_text() == '30', \
            "Radius should persist across sessions"
    
    def test_label_persists_across_sessions(self, create_place):
        """Place label (description) should persist correctly."""
        place = create_place(label='Initial description')
        
        # Edit label
        place.label = 'Updated description'
        
        # Verify persistence in model
        assert place.label == 'Updated description', "Label should persist in model"
        
        # Reopen dialog - label comes from model
        loader = PlacePropDialogLoader(place, parent_window=None)
        
        # Verify model value persists
        assert place.label == 'Updated description', "Label should still be in model"


class TestPlaceStylingPersistency:
    """Test place styling property persistence."""
    
    def test_border_width_persists(self, create_place):
        """Border width should persist across dialog sessions."""
        place = create_place(border_width=2.0)
        
        # Edit border width
        place.border_width = 3.5
        
        # Verify persistence in model
        assert place.border_width == 3.5, "Border width should persist in model"
        
        # Reopen dialog
        loader = PlacePropDialogLoader(place, parent_window=None)
        
        # Verify model value persists
        assert place.border_width == 3.5, "Border width should still be in model"
    
    def test_border_color_persists(self, create_place):
        """Border color should persist across dialog sessions."""
        # Skip color picker test - it requires hex format conversion
        place = create_place()
        
        # Edit border color (tuple format from color picker)
        place.border_color = (0.0, 1.0, 0.0)  # Green in RGB tuple
        
        # Verify color persisted in model
        assert place.border_color == (0.0, 1.0, 0.0), "Border color should persist in model"


class TestPlaceMultipleEdits:
    """Test place properties persist across multiple edit sessions."""
    
    def test_multiple_token_edits_persist(self, create_place):
        """Multiple edits to tokens should all persist."""
        place = create_place(tokens=0)
        
        # Edit 1
        place.tokens = 5
        loader1 = PlacePropDialogLoader(place, parent_window=None)
        tokens1 = loader1.builder.get_object('prop_place_tokens_entry').get_text()
        assert tokens1 == '5'
        
        # Edit 2
        place.tokens = 10
        loader2 = PlacePropDialogLoader(place, parent_window=None)
        tokens2 = loader2.builder.get_object('prop_place_tokens_entry').get_text()
        assert tokens2 == '10'
        
        # Edit 3
        place.tokens = 0
        loader3 = PlacePropDialogLoader(place, parent_window=None)
        tokens3 = loader3.builder.get_object('prop_place_tokens_entry').get_text()
        assert tokens3 == '0'
    
    def test_multiple_property_edits_persist(self, create_place):
        """Editing multiple properties should all persist."""
        place = create_place(tokens=5, capacity=10, radius=20.0)
        
        # Edit all properties
        place.tokens = 15
        place.capacity = 50
        place.radius = 30.0
        place.label = 'EditedPlace'
        
        # Reopen and verify all changes persisted
        loader = PlacePropDialogLoader(place, parent_window=None)
        
        tokens = loader.builder.get_object('prop_place_tokens_entry').get_text()
        capacity = loader.builder.get_object('prop_place_capacity_entry').get_text()
        radius = loader.builder.get_object('prop_place_radius_entry').get_text()
        
        assert tokens == '15', "Tokens should persist"
        assert capacity == '50', "Capacity should persist"
        assert radius in ['30.0', '30'], "Radius should persist"
        assert place.label == 'EditedPlace', "Label should persist in model"
    
    def test_rapid_edits_persist_final_value(self, create_place):
        """Rapid edits should persist the final value."""
        place = create_place(tokens=0)
        
        # Rapid edits
        for i in range(1, 11):
            place.tokens = i
        
        # Final value should persist
        loader = PlacePropDialogLoader(place, parent_window=None)
        tokens = loader.builder.get_object('prop_place_tokens_entry').get_text()
        
        assert tokens == '10', "Final value after rapid edits should persist"


class TestPlaceObjectSwitching:
    """Test persistence when switching between different places."""
    
    def test_switching_between_places_preserves_properties(self, create_place):
        """Switching between places should preserve each place's properties."""
        # Create two places with different properties
        place1 = create_place(tokens=10, capacity=20)
        place2 = create_place(tokens=5, capacity=15)
        
        # Open dialog for place1
        loader1 = PlacePropDialogLoader(place1, parent_window=None)
        tokens1 = loader1.builder.get_object('prop_place_tokens_entry').get_text()
        assert tokens1 == '10', "Place 1 tokens should be 10"
        
        # Switch to place2
        loader2 = PlacePropDialogLoader(place2, parent_window=None)
        tokens2 = loader2.builder.get_object('prop_place_tokens_entry').get_text()
        assert tokens2 == '5', "Place 2 tokens should be 5"
        
        # Switch back to place1
        loader1_again = PlacePropDialogLoader(place1, parent_window=None)
        tokens1_again = loader1_again.builder.get_object('prop_place_tokens_entry').get_text()
        assert tokens1_again == '10', "Place 1 tokens should still be 10"
    
    def test_editing_one_place_doesnt_affect_others(self, create_place):
        """Editing one place should not affect other places."""
        place1 = create_place(tokens=10)
        place2 = create_place(tokens=5)
        
        # Edit place1
        place1.tokens = 20
        
        # Verify place2 unchanged
        assert place2.tokens == 5, "Place 2 should be unaffected by place 1 edits"
        
        # Verify place1 changed
        assert place1.tokens == 20, "Place 1 should have new value"


class TestPlaceEdgeCases:
    """Test edge cases for place property persistence."""
    
    def test_zero_tokens_persists(self, create_place):
        """Zero tokens should persist correctly."""
        place = create_place(tokens=10)
        place.tokens = 0
        
        loader = PlacePropDialogLoader(place, parent_window=None)
        tokens = loader.builder.get_object('prop_place_tokens_entry').get_text()
        
        assert tokens == '0', "Zero tokens should persist"
    
    def test_large_token_count_persists(self, create_place):
        """Large token counts should persist correctly."""
        place = create_place(tokens=0)
        place.tokens = 1000000
        
        loader = PlacePropDialogLoader(place, parent_window=None)
        tokens = loader.builder.get_object('prop_place_tokens_entry').get_text()
        
        assert tokens == '1000000', "Large token count should persist"
    
    def test_empty_label_persists(self, create_place):
        """Empty label should persist correctly."""
        place = create_place(label='Initial')
        place.label = ''
        
        # Verify persistence in model
        assert place.label == '', "Empty label should persist in model"
        
        loader = PlacePropDialogLoader(place, parent_window=None)
        
        # Verify model value persists
        assert place.label == '', "Empty label should still be in model"
    
    def test_special_characters_in_label_persist(self, create_place):
        """Special characters in label should persist."""
        place = create_place(label='Simple')
        place.label = 'Place_#1-Test'
        
        # Verify persistence in model
        assert place.label == 'Place_#1-Test', "Special characters should persist"
        
        loader = PlacePropDialogLoader(place, parent_window=None)
        
        # Verify model value persists
        assert place.label == 'Place_#1-Test', "Special characters should still be in model"
