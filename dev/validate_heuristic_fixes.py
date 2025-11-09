#!/usr/bin/env python3
"""
Validation script for heuristic algorithm fixes.

Tests the enhanced type detection and stoichiometry validation
on KEGG hsa00010 (glycolysis) pathway.

Expected results:
- Before: 0/34 transitions correctly typed (all IMMEDIATE)
- After: 32-34/34 transitions correctly typed (CONTINUOUS)
- Confidence: 0.60 → 0.78 average (+30%)
"""

import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from shypn.core.models.petri_net import PetriNet
from shypn.crossfetch.inference.heuristic_engine import HeuristicInferenceEngine, TransitionType

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

def load_hsa00010():
    """Load KEGG hsa00010 pathway model."""
    model_path = Path(__file__).parent.parent / 'workspace' / 'examples' / 'pathways' / 'hsa00010.shy'
    
    if not model_path.exists():
        logger.error(f"Model not found: {model_path}")
        return None
    
    logger.info(f"Loading model: {model_path}")
    
    # Load Petri net
    try:
        pn = PetriNet.load(str(model_path))
        logger.info(f"Loaded: {len(pn.transitions)} transitions, {len(pn.places)} places")
        return pn
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        return None

def validate_type_detection(pn: PetriNet):
    """Validate type detection on hsa00010 transitions."""
    logger.info("\n" + "="*80)
    logger.info("VALIDATING TYPE DETECTION")
    logger.info("="*80)
    
    # Initialize inference engine
    engine = HeuristicInferenceEngine(use_background_fetch=False)
    
    # Known glycolysis enzymes (should all be CONTINUOUS)
    expected_continuous = {
        'T61': 'GAPDH (glyceraldehyde-3-phosphate dehydrogenase)',
        'T63': 'PFK (phosphofructokinase)',
        'T57': 'PK (pyruvate kinase)',
        'T53': 'HK (hexokinase)',
        'T62': 'PGK (phosphoglycerate kinase)',
        'T64': 'ALDOA (aldolase)',
        'T58': 'PGAM (phosphoglycerate mutase)',
        'T59': 'ENO (enolase)',
        'T60': 'TPI (triose-phosphate isomerase)',
    }
    
    type_counts = {
        TransitionType.CONTINUOUS: 0,
        TransitionType.IMMEDIATE: 0,
        TransitionType.TIMED: 0,
        TransitionType.STOCHASTIC: 0,
        TransitionType.UNKNOWN: 0,
    }
    
    confidence_scores = []
    mistyped = []
    
    logger.info(f"\nAnalyzing {len(pn.transitions)} transitions...\n")
    
    for transition in pn.transitions:
        # Detect type
        detected_type = engine.type_detector.detect_type(transition)
        type_counts[detected_type] += 1
        
        # Infer parameters (includes stoichiometry validation)
        result = engine.infer_parameters(transition, organism="Homo sapiens", use_cache=False)
        
        final_type = result.parameters.transition_type
        confidence = result.parameters.confidence_score
        confidence_scores.append(confidence)
        
        # Check if expected to be CONTINUOUS
        if transition.id in expected_continuous:
            expected_desc = expected_continuous[transition.id]
            status = "✓" if final_type == TransitionType.CONTINUOUS else "✗"
            
            if final_type != TransitionType.CONTINUOUS:
                mistyped.append((transition.id, expected_desc, final_type))
            
            logger.info(f"{status} {transition.id:6s} | {expected_desc:50s} | {final_type.value:12s} | Conf: {confidence:.2f}")
        else:
            logger.debug(f"  {transition.id:6s} | {transition.label:50s} | {final_type.value:12s} | Conf: {confidence:.2f}")
    
    # Summary
    logger.info("\n" + "="*80)
    logger.info("SUMMARY")
    logger.info("="*80)
    
    total = len(pn.transitions)
    continuous_count = type_counts[TransitionType.CONTINUOUS]
    continuous_pct = (continuous_count / total) * 100
    
    logger.info(f"\nType Distribution:")
    for type_enum, count in type_counts.items():
        pct = (count / total) * 100
        logger.info(f"  {type_enum.value:12s}: {count:2d} / {total} ({pct:5.1f}%)")
    
    avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
    logger.info(f"\nAverage Confidence: {avg_confidence:.3f}")
    
    # Expected results
    logger.info(f"\nExpected Key Enzymes (should be CONTINUOUS):")
    logger.info(f"  Checked: {len(expected_continuous)}")
    logger.info(f"  Correct: {len(expected_continuous) - len(mistyped)}")
    logger.info(f"  Accuracy: {((len(expected_continuous) - len(mistyped)) / len(expected_continuous)) * 100:.1f}%")
    
    if mistyped:
        logger.warning(f"\nMistyped Transitions:")
        for trans_id, desc, wrong_type in mistyped:
            logger.warning(f"  {trans_id}: {desc} → {wrong_type.value} (expected CONTINUOUS)")
    
    # Overall assessment
    logger.info("\n" + "="*80)
    if continuous_pct >= 90 and avg_confidence >= 0.70 and len(mistyped) <= 2:
        logger.info("✓ VALIDATION PASSED")
        logger.info(f"  - {continuous_pct:.1f}% transitions typed as CONTINUOUS (target: ≥90%)")
        logger.info(f"  - Average confidence {avg_confidence:.2f} (target: ≥0.70)")
        logger.info(f"  - {len(mistyped)} key enzyme(s) mistyped (target: ≤2)")
    else:
        logger.warning("✗ VALIDATION FAILED")
        if continuous_pct < 90:
            logger.warning(f"  - Only {continuous_pct:.1f}% CONTINUOUS (target: ≥90%)")
        if avg_confidence < 0.70:
            logger.warning(f"  - Confidence {avg_confidence:.2f} too low (target: ≥0.70)")
        if len(mistyped) > 2:
            logger.warning(f"  - {len(mistyped)} key enzymes mistyped (target: ≤2)")
    
    logger.info("="*80)
    
    return {
        'total': total,
        'continuous_count': continuous_count,
        'continuous_pct': continuous_pct,
        'avg_confidence': avg_confidence,
        'mistyped_count': len(mistyped),
        'passed': continuous_pct >= 90 and avg_confidence >= 0.70 and len(mistyped) <= 2
    }

def main():
    """Main validation routine."""
    logger.info("Heuristic Algorithm Fix Validation")
    logger.info("Testing: KEGG hsa00010 (Glycolysis pathway)")
    logger.info("")
    
    # Load model
    pn = load_hsa00010()
    if not pn:
        logger.error("Cannot proceed without model")
        return 1
    
    # Validate type detection
    results = validate_type_detection(pn)
    
    # Exit code
    return 0 if results['passed'] else 1

if __name__ == '__main__':
    sys.exit(main())
