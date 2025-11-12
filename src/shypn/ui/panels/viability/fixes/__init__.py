"""Fix application system for viability investigations.

This module provides tools for:
- Sequencing fixes by dependencies
- Applying fixes to the model
- Predicting fix impact
- Undoing applied fixes
"""

from .fix_sequencer import FixSequencer, FixSequence
from .fix_applier import FixApplier, AppliedFix
from .fix_predictor import FixPredictor, FixPrediction

__all__ = [
    'FixSequencer',
    'FixSequence',
    'FixApplier',
    'AppliedFix',
    'FixPredictor',
    'FixPrediction',
]
