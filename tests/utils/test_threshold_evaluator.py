"""
Unit tests for ThresholdEvaluator

Tests dynamic threshold evaluation for arcs, including:
- Fixed numeric thresholds
- Expression-based thresholds with place references
- Function-based thresholds with dependencies
- Backward compatibility (threshold=None)
- Error handling
"""

import pytest
from shypn.utils.threshold_evaluator import ThresholdEvaluator
from shypn.netobjs.place import Place
from shypn.netobjs.inhibitor_arc import InhibitorArc
from shypn.netobjs.transition import Transition


class MockModel:
    """Mock model for testing threshold evaluator."""
    
    def __init__(self, places_list):
        # Store places as dict keyed by ID
        self.places = {p.id: p for p in places_list}


class TestThresholdEvaluator:
    """Test suite for ThresholdEvaluator class."""
    
    def test_backward_compatibility_no_threshold(self):
        """Test that arc.weight is used when threshold is None."""
        # Create mock model with places
        p1 = Place(x=100, y=100, id=1, name="P1", label="Place1")
        p1.tokens = 10.0
        model = MockModel([p1])
        
        # Create arc with weight but no threshold
        p_source = Place(x=100, y=100, id=2, name="Source", label="Source")
        t_target = Transition(x=200, y=100, id=1, name="T1", label="Trans1")
        arc = InhibitorArc(source=p_source, target=t_target, id=1, name="A1", weight=5.0)
        arc.threshold = None
        
        # Evaluate threshold
        evaluator = ThresholdEvaluator(model)
        result = evaluator.evaluate(arc, {'time': 0.0})
        
        # Should return weight (backward compatible)
        assert result == 5.0, f"Expected 5.0, got {result}"
    
    def test_numeric_threshold_supersedes_weight(self):
        """Test that numeric threshold supersedes weight."""
        p1 = Place(x=100, y=100, id=1, name="P1", label="Place1")
        model = MockModel([p1])
        
        p_source = Place(x=100, y=100, id=2, name="Source", label="Source")
        t_target = Transition(x=200, y=100, id=1, name="T1", label="Trans1")
        arc = InhibitorArc(source=p_source, target=t_target, id=1, name="A1", weight=1.0)
        arc.threshold = 10.0  # Numeric threshold
        
        evaluator = ThresholdEvaluator(model)
        result = evaluator.evaluate(arc, {'time': 0.0})
        
        # Should return threshold (10.0), NOT weight (1.0)
        assert result == 10.0, f"Expected 10.0 (threshold), got {result}"
    
    def test_expression_with_place_id(self):
        """Test expression evaluation with place ID references."""
        p1 = Place(x=100, y=100, id=1, name="ATP", label="ATP")
        p1.tokens = 5.0
        model = MockModel([p1])
        
        p_source = Place(x=100, y=100, id=2, name="Source", label="Source")
        t_target = Transition(x=200, y=100, id=1, name="T1", label="Trans1")
        arc = InhibitorArc(source=p_source, target=t_target, id=1, name="A1", weight=1.0)
        arc.threshold = "P1 * 2.0"  # Expression: 5.0 * 2.0 = 10.0
        
        evaluator = ThresholdEvaluator(model)
        result = evaluator.evaluate(arc, {'time': 0.0})
        
        assert result == 10.0, f"Expected 10.0, got {result}"
    
    def test_expression_with_place_name(self):
        """Test expression evaluation with place name references."""
        atp = Place(x=100, y=100, id=1, name="ATP", label="ATP")
        atp.tokens = 5.0
        amp = Place(x=150, y=100, id=2, name="AMP", label="AMP")
        amp.tokens = 0.1
        model = MockModel([atp, amp])
        
        p_source = Place(x=100, y=100, id=3, name="Source", label="Source")
        t_target = Transition(x=200, y=100, id=1, name="T1", label="Trans1")
        arc = InhibitorArc(source=p_source, target=t_target, id=1, name="A1", weight=1.0)
        arc.threshold = "4.0 * (1.0 + AMP / 0.1)"  # Real PFK example
        
        evaluator = ThresholdEvaluator(model)
        result = evaluator.evaluate(arc, {'time': 0.0})
        
        # 4.0 * (1.0 + 0.1/0.1) = 4.0 * 2.0 = 8.0
        assert result == 8.0, f"Expected 8.0, got {result}"
    
    def test_expression_with_math_functions(self):
        """Test expression with math module functions."""
        p1 = Place(x=100, y=100, id=1, name="P1", label="P1")
        p1.tokens = 16.0
        model = MockModel([p1])
        
        p_source = Place(x=100, y=100, id=2, name="Source", label="Source")
        t_target = Transition(x=200, y=100, id=1, name="T1", label="Trans1")
        arc = InhibitorArc(source=p_source, target=t_target, id=1, name="A1", weight=1.0)
        arc.threshold = "math.sqrt(P1)"  # sqrt(16) = 4
        
        evaluator = ThresholdEvaluator(model)
        result = evaluator.evaluate(arc, {'time': 0.0})
        
        assert result == 4.0, f"Expected 4.0, got {result}"
    
    def test_expression_with_conditional(self):
        """Test expression with conditional (if-else)."""
        p1 = Place(x=100, y=100, id=1, name="P1", label="P1")
        p1.tokens = 60.0
        p2 = Place(x=150, y=100, id=2, name="P2", label="P2")
        p2.tokens = 30.0
        model = MockModel([p1, p2])
        
        p_source = Place(x=100, y=100, id=3, name="Source", label="Source")
        t_target = Transition(x=200, y=100, id=1, name="T1", label="Trans1")
        arc = InhibitorArc(source=p_source, target=t_target, id=1, name="A1", weight=1.0)
        arc.threshold = "P1 * (0.2 if P2 > 50 else 0.5)"
        
        evaluator = ThresholdEvaluator(model)
        result = evaluator.evaluate(arc, {'time': 0.0})
        
        # P2=30 < 50, so use 0.5: 60 * 0.5 = 30.0
        assert result == 30.0, f"Expected 30.0, got {result}"
    
    def test_function_based_threshold(self):
        """Test function-based threshold with dependencies."""
        atp = Place(x=100, y=100, id=5, name="ATP", label="ATP")
        atp.tokens = 5.0
        amp = Place(x=150, y=100, id=6, name="AMP", label="AMP")
        amp.tokens = 0.05
        model = MockModel([atp, amp])
        
        p_source = Place(x=100, y=100, id=7, name="Source", label="Source")
        t_target = Transition(x=200, y=100, id=1, name="T1", label="Trans1")
        arc = InhibitorArc(source=p_source, target=t_target, id=1, name="A1", weight=1.0)
        arc.threshold = {
            "type": "function",
            "formula": "lambda ATP, AMP: 4.0 * (1.0 + AMP / 0.1)",
            "dependencies": ["ATP", "AMP"]
        }
        
        evaluator = ThresholdEvaluator(model)
        result = evaluator.evaluate(arc, {'time': 0.0})
        
        # 4.0 * (1.0 + 0.05/0.1) = 4.0 * 1.5 = 6.0
        assert result == 6.0, f"Expected 6.0, got {result}"
    
    def test_invalid_threshold_type(self):
        """Test that invalid threshold type raises ValueError."""
        p1 = Place(x=100, y=100, id=1, name="P1", label="P1")
        model = MockModel([p1])
        
        p_source = Place(x=100, y=100, id=2, name="Source", label="Source")
        t_target = Transition(x=200, y=100, id=1, name="T1", label="Trans1")
        arc = InhibitorArc(source=p_source, target=t_target, id=1, name="A1", weight=1.0)
        arc.threshold = ['invalid', 'list']  # Invalid type
        
        evaluator = ThresholdEvaluator(model)
        
        with pytest.raises(ValueError, match="Invalid threshold type"):
            evaluator.evaluate(arc, {'time': 0.0})
    
    def test_expression_with_undefined_place(self):
        """Test that undefined place in expression raises RuntimeError."""
        p1 = Place(x=100, y=100, id=1, name="P1", label="P1")
        model = MockModel([p1])
        
        p_source = Place(x=100, y=100, id=2, name="Source", label="Source")
        t_target = Transition(x=200, y=100, id=1, name="T1", label="Trans1")
        arc = InhibitorArc(source=p_source, target=t_target, id=1, name="A1", weight=1.0)
        arc.threshold = "P999 * 2.0"  # P999 doesn't exist
        
        evaluator = ThresholdEvaluator(model)
        
        with pytest.raises(RuntimeError, match="Failed to evaluate threshold expression"):
            evaluator.evaluate(arc, {'time': 0.0})
    
    def test_threshold_supersedes_weight_in_simulation(self):
        """Integration test: threshold supersedes weight for enablement."""
        # This test verifies the key behavior: threshold OVERRIDES weight
        atp_high = Place(x=100, y=100, id=5, name="ATP_high", label="ATP_high")
        atp_high.tokens = 5.0  # Current ATP concentration
        amp = Place(x=150, y=100, id=6, name="AMP", label="AMP")
        amp.tokens = 0.05  # Energy demand signal
        model = MockModel([atp_high, amp])
        
        # Create inhibitor arc with low weight but high dynamic threshold
        p_source = Place(x=100, y=100, id=7, name="Source", label="Source")
        t_target = Transition(x=200, y=100, id=1, name="PFK", label="PFK")
        arc = InhibitorArc(source=atp_high, target=t_target, id=1, name="A5", weight=1.0)
        
        # Dynamic threshold: ATP inhibition relieved by AMP
        arc.threshold = "4.0 * (1.0 + AMP / 0.1)"
        
        evaluator = ThresholdEvaluator(model)
        effective_threshold = evaluator.evaluate(arc, {'time': 0.0})
        
        # At AMP=0.05: threshold = 4.0 * (1.0 + 0.05/0.1) = 4.0 * 1.5 = 6.0
        assert effective_threshold == 6.0
        
        # Inhibitor check: ATP_high (5.0) < threshold (6.0) → ENABLED
        # If we used weight (1.0): ATP_high (5.0) >= weight (1.0) → DISABLED
        # This demonstrates threshold SUPERSEDING weight
        
        is_inhibited_by_threshold = (atp_high.tokens >= effective_threshold)
        is_inhibited_by_weight = (atp_high.tokens >= arc.weight)
        
        assert not is_inhibited_by_threshold, "Should be enabled (ATP < dynamic threshold)"
        assert is_inhibited_by_weight, "Would be disabled if using weight (demonstrates supersede)"
        print(f"✓ Threshold ({effective_threshold}) supersedes weight ({arc.weight})")


if __name__ == "__main__":
    # Run tests
    test = TestThresholdEvaluator()
    
    print("Running threshold evaluator tests...")
    test.test_backward_compatibility_no_threshold()
    print("✓ Backward compatibility (threshold=None)")
    
    test.test_numeric_threshold_supersedes_weight()
    print("✓ Numeric threshold supersedes weight")
    
    test.test_expression_with_place_id()
    print("✓ Expression with place ID")
    
    test.test_expression_with_place_name()
    print("✓ Expression with place name")
    
    test.test_expression_with_math_functions()
    print("✓ Expression with math functions")
    
    test.test_expression_with_conditional()
    print("✓ Expression with conditional")
    
    test.test_function_based_threshold()
    print("✓ Function-based threshold")
    
    test.test_threshold_supersedes_weight_in_simulation()
    print("✓ Threshold supersedes weight (integration test)")
    
    print("\nTesting error cases...")
    test.test_invalid_threshold_type()
    print("✓ Invalid threshold type raises ValueError")
    
    test.test_expression_with_undefined_place()
    print("✓ Undefined place raises RuntimeError")
    
    print("\n✅ All tests passed!")
