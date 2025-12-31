#!/usr/bin/env python3
"""Quick demonstration of Signal Classification system.

This script demonstrates the automated signal classification on a mock model.
"""

import sys
sys.path.insert(0, 'src')

from unittest.mock import Mock
from shypn.analysis.signal_classification import SignalClassifierManager


def create_mock_model():
    """Create a simple mock model for demonstration."""
    model = Mock()
    
    # Create places
    atp = Mock()
    atp.name = "ATP"
    atp.is_signal = True
    
    ahl = Mock()
    ahl.name = "AHL"
    ahl.is_signal = True
    
    luxr = Mock()
    luxr.name = "LuxR"
    luxr.is_signal = True
    
    membrane = Mock()
    membrane.name = "MEMBRANE"
    membrane.is_signal = True
    membrane.constant = True
    
    glucose = Mock()
    glucose.name = "Glucose"
    glucose.is_signal = False
    
    model.places = [atp, ahl, luxr, membrane, glucose]
    
    # Create transitions with rate functions
    t1 = Mock()
    t1.name = "Synthesis"
    t1.rate = "2.0 * ATP * Glucose"
    
    t2 = Mock()
    t2.name = "AHL_production"
    t2.rate = "k * AHL"  # Positive feedback
    
    t3 = Mock()
    t3.name = "Activation"
    t3.rate = "Vmax * LuxR^3 / (K^3 + LuxR^3)"  # Hill function
    
    model.transitions = [t1, t2, t3]
    
    # Create arcs (simplified)
    arcs = []
    
    # ATP consumed by many transitions (hub)
    for i in range(6):
        arc = Mock()
        arc.source = atp
        arc.target = Mock(name=f"T{i}")
        arcs.append(arc)
    
    # AHL positive feedback
    arc = Mock()
    arc.source = ahl
    arc.target = t2
    arcs.append(arc)
    
    arc = Mock()
    arc.source = t2
    arc.target = ahl
    arcs.append(arc)
    
    # LuxR regulatory (convergent)
    for i in range(3):
        arc = Mock()
        arc.source = Mock(name=f"Signal{i}")
        arc.target = luxr
        arcs.append(arc)
    
    model.arcs = arcs
    
    return model


def main():
    """Run demonstration."""
    print("=" * 70)
    print("AUTOMATED SIGNAL CLASSIFICATION DEMONSTRATION")
    print("=" * 70)
    print()
    
    # Create mock model
    model = create_mock_model()
    
    print(f"Model: {len(model.places)} places, {len(model.transitions)} transitions")
    print()
    
    # Initialize classifier
    manager = SignalClassifierManager(model, confidence_threshold=0.5)
    
    # Classify all signals
    print("Classifying signals...")
    classifications = manager.classify_all_signals()
    
    print()
    print("RESULTS:")
    print("-" * 70)
    
    for place_name, (signal_type, confidence) in sorted(classifications.items()):
        bar_length = int(confidence * 20)
        bar = "█" * bar_length + "░" * (20 - bar_length)
        print(f"{place_name:15s} → {signal_type:12s} [{bar}] {confidence:.2f}")
    
    print()
    print("=" * 70)
    print()
    
    # Show detailed report
    print(manager.get_classification_report())
    
    # Validate
    print("\nValidation:")
    print("-" * 70)
    issues = manager.validate_classifications()
    
    if any(issues.values()):
        for issue_type, places in issues.items():
            if places:
                print(f"{issue_type}: {', '.join(places)}")
    else:
        print("✓ No issues detected")
    
    print()
    print("Demonstration complete!")
    print()


if __name__ == '__main__':
    main()
