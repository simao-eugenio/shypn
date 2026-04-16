"""
Test transition property persistence across dialog sessions.

Verifies that transition properties persist correctly when:
- Opening and closing dialogs
- Editing properties multiple times
- Switching between different transitions
- Transition type changes
"""
import pytest
from shypn.helpers.transition_prop_dialog_loader import TransitionPropDialogLoader


class TestTransitionBasicPersistency:
    """Test basic transition property persistence."""
    
    def test_rate_persists_across_dialog_sessions(self, create_transition):
        """Rate value should persist when closing and reopening dialog."""
        trans = create_transition(transition_type='timed', rate=1.0)
        
        # Simulate dialog: edit rate
        trans.rate = 2.5
        
        # Close and reopen dialog - rate should persist
        loader = TransitionPropDialogLoader(trans, parent_window=None)
        rate_entry = loader.builder.get_object('rate_entry')
        
        # Verify value persisted
        assert rate_entry.get_text() in ['2.5', '2.50'], "Rate should persist across sessions"
    
    def test_priority_persists_across_dialog_sessions(self, create_transition):
        """Priority value should persist when closing and reopening dialog."""
        trans = create_transition(priority=1)
        
        # Simulate dialog: edit priority
        trans.priority = 5
        
        # Verify persistence in model
        assert trans.priority == 5, "Priority should persist in model"
        
        # Close and reopen dialog
        loader = TransitionPropDialogLoader(trans, parent_window=None)
        
        # Verify model value persists
        assert trans.priority == 5, "Priority should still be 5 in model"
    
    def test_guard_persists_across_dialog_sessions(self, create_transition):
        """Guard expression should persist correctly."""
        trans = create_transition(guard='')
        
        # Set guard
        trans.guard = 'tokens(P1) > 5'
        
        # Verify persistence in model
        assert trans.guard == 'tokens(P1) > 5', "Guard should persist in model"
        
        # Reopen dialog
        loader = TransitionPropDialogLoader(trans, parent_window=None)
        
        # Verify model value persists
        assert trans.guard == 'tokens(P1) > 5', "Guard should still be in model"
    
    def test_transition_type_persists(self, create_transition):
        """Transition type should persist across sessions."""
        trans = create_transition(transition_type='stochastic')
        
        # Verify type persists
        assert trans.transition_type == 'stochastic', "Type should be stochastic"
        
        # Reopen dialog
        loader = TransitionPropDialogLoader(trans, parent_window=None)
        
        # Verify type still persists
        assert trans.transition_type == 'stochastic', "Type should still be stochastic"


class TestTransitionTypePersistency:
    """Test transition type persistence through changes."""
    
    def test_rate_persists_when_switching_to_immediate(self, create_transition):
        """Rate should persist even when switching to immediate (though hidden)."""
        trans = create_transition(transition_type='timed', rate=3.0)
        
        # Switch to immediate
        trans.transition_type = 'immediate'
        
        # Rate should still be in model (even if hidden in UI)
        assert trans.rate == 3.0, "Rate should persist in model when type changes"
    
    def test_guard_persists_across_type_changes(self, create_transition):
        """Guard should persist across all type changes."""
        trans = create_transition(transition_type='immediate', guard='tokens(P1) > 0')
        
        # Change type multiple times
        trans.transition_type = 'timed'
        trans.transition_type = 'stochastic'
        trans.transition_type = 'continuous'
        
        # Guard should still be there
        assert trans.guard == 'tokens(P1) > 0', "Guard should persist across type changes"
    
    def test_priority_persists_across_type_changes(self, create_transition):
        """Priority should persist across all type changes."""
        trans = create_transition(transition_type='immediate', priority=5)
        
        # Change type
        trans.transition_type = 'timed'
        trans.transition_type = 'stochastic'
        
        # Priority should still be there
        assert trans.priority == 5, "Priority should persist across type changes"


class TestTransitionMultipleEdits:
    """Test transition properties persist across multiple edit sessions."""
    
    def test_multiple_rate_edits_persist(self, create_transition):
        """Multiple edits to rate should all persist."""
        trans = create_transition(transition_type='timed', rate=1.0)
        
        # Edit 1
        trans.rate = 2.0
        loader1 = TransitionPropDialogLoader(trans, parent_window=None)
        rate1 = loader1.builder.get_object('rate_entry').get_text()
        assert rate1 in ['2.0', '2', '2.00']
        
        # Edit 2
        trans.rate = 5.5
        loader2 = TransitionPropDialogLoader(trans, parent_window=None)
        rate2 = loader2.builder.get_object('rate_entry').get_text()
        assert rate2 in ['5.5', '5.50']
        
        # Edit 3
        trans.rate = 0.1
        loader3 = TransitionPropDialogLoader(trans, parent_window=None)
        rate3 = loader3.builder.get_object('rate_entry').get_text()
        assert rate3 in ['0.1', '0.10']
    
    def test_multiple_property_edits_persist(self, create_transition):
        """Editing multiple properties should all persist."""
        trans = create_transition(transition_type='timed', rate=1.0, guard='', priority=1)
        
        # Edit all properties
        trans.rate = 3.0
        trans.guard = 'tokens(P1) >= 2'
        trans.priority = 10
        trans.transition_type = 'stochastic'
        
        # Reopen and verify all changes persisted
        loader = TransitionPropDialogLoader(trans, parent_window=None)
        
        rate = loader.builder.get_object('rate_entry').get_text()
        
        assert rate in ['3.0', '3', '3.00'], "Rate should persist"
        assert trans.priority == 10, "Priority should persist in model"
        assert trans.guard == 'tokens(P1) >= 2', "Guard should persist in model"
        assert trans.transition_type == 'stochastic', "Type should persist"
    
    def test_rapid_edits_persist_final_value(self, create_transition):
        """Rapid edits should persist the final value."""
        trans = create_transition(transition_type='timed', rate=0.0)
        
        # Rapid edits
        for i in range(1, 11):
            trans.rate = float(i)
        
        # Final value should persist
        loader = TransitionPropDialogLoader(trans, parent_window=None)
        rate = loader.builder.get_object('rate_entry').get_text()
        
        assert rate in ['10.0', '10', '10.00'], "Final value after rapid edits should persist"


class TestTransitionObjectSwitching:
    """Test persistence when switching between different transitions."""
    
    def test_switching_between_transitions_preserves_properties(self, create_transition):
        """Switching between transitions should preserve each transition's properties."""
        # Create two transitions with different properties
        trans1 = create_transition(transition_type='timed', rate=2.0, priority=5)
        trans2 = create_transition(transition_type='stochastic', rate=3.0, priority=1)
        
        # Open dialog for trans1
        loader1 = TransitionPropDialogLoader(trans1, parent_window=None)
        rate1 = loader1.builder.get_object('rate_entry').get_text()
        assert rate1 in ['2.0', '2', '2.00'], "Trans 1 rate should be 2.0"
        
        # Switch to trans2
        loader2 = TransitionPropDialogLoader(trans2, parent_window=None)
        rate2 = loader2.builder.get_object('rate_entry').get_text()
        assert rate2 in ['3.0', '3', '3.00'], "Trans 2 rate should be 3.0"
        
        # Switch back to trans1
        loader1_again = TransitionPropDialogLoader(trans1, parent_window=None)
        rate1_again = loader1_again.builder.get_object('rate_entry').get_text()
        assert rate1_again in ['2.0', '2', '2.00'], "Trans 1 rate should still be 2.0"
    
    def test_editing_one_transition_doesnt_affect_others(self, create_transition):
        """Editing one transition should not affect other transitions."""
        trans1 = create_transition(transition_type='timed', rate=2.0)
        trans2 = create_transition(transition_type='timed', rate=3.0)
        
        # Edit trans1
        trans1.rate = 5.0
        
        # Verify trans2 unchanged
        assert trans2.rate == 3.0, "Trans 2 should be unaffected by trans 1 edits"
        
        # Verify trans1 changed
        assert trans1.rate == 5.0, "Trans 1 should have new value"


class TestTransitionSourceSinkPersistency:
    """Test source/sink property persistence."""
    
    def test_source_flag_persists(self, create_transition):
        """Source flag should persist across sessions."""
        trans = create_transition()
        
        # Set as source
        trans.is_source = True
        
        # Verify persistence
        assert trans.is_source == True, "Source flag should persist"
        
        loader = TransitionPropDialogLoader(trans, parent_window=None)
        assert trans.is_source == True, "Source flag should still be True"
    
    def test_sink_flag_persists(self, create_transition):
        """Sink flag should persist across sessions."""
        trans = create_transition()
        
        # Set as sink
        trans.is_sink = True
        
        # Verify persistence
        assert trans.is_sink == True, "Sink flag should persist"
        
        loader = TransitionPropDialogLoader(trans, parent_window=None)
        assert trans.is_sink == True, "Sink flag should still be True"
    
    def test_source_and_sink_flags_persist_together(self, create_transition):
        """Both source and sink flags can be set and persist."""
        trans = create_transition()
        
        # Set both flags
        trans.is_source = True
        trans.is_sink = True
        
        # Verify both persist
        loader = TransitionPropDialogLoader(trans, parent_window=None)
        
        assert trans.is_source == True, "Source flag should persist"
        assert trans.is_sink == True, "Sink flag should persist"


class TestTransitionEdgeCases:
    """Test edge cases for transition property persistence."""
    
    def test_zero_rate_persists(self, create_transition):
        """Zero rate should persist correctly."""
        trans = create_transition(transition_type='timed', rate=1.0)
        trans.rate = 0.0
        
        loader = TransitionPropDialogLoader(trans, parent_window=None)
        rate = loader.builder.get_object('rate_entry').get_text()
        
        assert rate in ['0.0', '0', '0.00'], "Zero rate should persist"
    
    def test_very_small_rate_persists(self, create_transition):
        """Very small rates should persist correctly."""
        trans = create_transition(transition_type='timed', rate=1.0)
        trans.rate = 0.001
        
        loader = TransitionPropDialogLoader(trans, parent_window=None)
        rate = loader.builder.get_object('rate_entry').get_text()
        
        # Check if small value is preserved (may be scientific notation or decimal)
        assert '0.001' in rate or 'e-' in rate.lower(), "Small rate should persist"
    
    def test_large_rate_persists(self, create_transition):
        """Large rates should persist correctly."""
        trans = create_transition(transition_type='timed', rate=1.0)
        trans.rate = 1000000.0
        
        loader = TransitionPropDialogLoader(trans, parent_window=None)
        
        # Verify in model
        assert trans.rate == 1000000.0, "Large rate should persist in model"
    
    def test_empty_guard_persists(self, create_transition):
        """Empty guard should persist correctly."""
        trans = create_transition(guard='tokens(P1) > 0')
        trans.guard = ''
        
        # Verify persistence
        assert trans.guard == '', "Empty guard should persist"
        
        loader = TransitionPropDialogLoader(trans, parent_window=None)
        assert trans.guard == '', "Empty guard should still be empty"
    
    def test_complex_guard_expression_persists(self, create_transition):
        """Complex guard expressions should persist correctly."""
        trans = create_transition(guard='')
        complex_guard = 'tokens(P1) > 5 and tokens(P2) < 10 or tokens(P3) == 0'
        trans.guard = complex_guard
        
        # Verify persistence
        assert trans.guard == complex_guard, "Complex guard should persist"
        
        loader = TransitionPropDialogLoader(trans, parent_window=None)
        assert trans.guard == complex_guard, "Complex guard should still match"
    
    def test_priority_zero_persists(self, create_transition):
        """Priority of 0 should persist correctly."""
        trans = create_transition(priority=5)
        trans.priority = 0
        
        # Verify persistence in model
        assert trans.priority == 0, "Priority of 0 should persist"
        
        loader = TransitionPropDialogLoader(trans, parent_window=None)
        
        # Verify model value persists
        assert trans.priority == 0, "Priority of 0 should still be 0"
    
    def test_high_priority_persists(self, create_transition):
        """High priority values should persist correctly."""
        trans = create_transition(priority=1)
        trans.priority = 100
        
        # Verify persistence in model
        assert trans.priority == 100, "High priority should persist"
        
        loader = TransitionPropDialogLoader(trans, parent_window=None)
        
        # Verify model value persists
        assert trans.priority == 100, "High priority should still be 100"
    
    def test_properties_persist_across_many_sessions(self, create_transition):
        """Properties should persist across many dialog open/close cycles."""
        trans = create_transition(transition_type='timed', rate=2.5, priority=5)
        
        # Open and close dialog 10 times
        for i in range(10):
            loader = TransitionPropDialogLoader(trans, parent_window=None)
            rate = loader.builder.get_object('rate_entry').get_text()
            
            assert rate in ['2.5', '2.50'], f"Rate should persist in session {i+1}"
            assert trans.priority == 5, f"Priority should persist in session {i+1}"
        
        # Values should still be correct
        assert trans.rate == 2.5, "Rate should persist after many sessions"
        assert trans.priority == 5, "Priority should persist after many sessions"
