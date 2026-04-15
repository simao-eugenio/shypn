#!/usr/bin/env python3
"""Standalone script for signal type classification.

This script provides command-line interface for automated signal classification.

Usage:
    python scripts/classify_signals.py model.shy
    python scripts/classify_signals.py model.shy --apply
    python scripts/classify_signals.py model.shy --threshold 0.6 --report

Author: Simão Eugénio
Date: December 31, 2025
"""

import sys
import argparse
import logging

# Add src to path
sys.path.insert(0, 'src')

from shypn.file.file_loader import FileLoader
from shypn.analysis.signal_classification import SignalClassifierManager


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Automated signal type classification for Bio-PNs'
    )
    parser.add_argument(
        'model_file',
        help='Path to .shy model file'
    )
    parser.add_argument(
        '--threshold',
        type=float,
        default=0.5,
        help='Confidence threshold (0.0-1.0, default: 0.5)'
    )
    parser.add_argument(
        '--apply',
        action='store_true',
        help='Apply classifications to model and save'
    )
    parser.add_argument(
        '--overwrite',
        action='store_true',
        help='Overwrite existing signal_type values'
    )
    parser.add_argument(
        '--report',
        action='store_true',
        help='Generate detailed classification report'
    )
    parser.add_argument(
        '--validate',
        action='store_true',
        help='Validate classifications and identify issues'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Configure logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(levelname)s: %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    
    # Load model
    logger.info(f"Loading model from {args.model_file}")
    loader = FileLoader()
    
    try:
        model = loader.load(args.model_file)
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        return 1
    
    logger.info(f"Loaded model with {len(model.places)} places")
    
    # Initialize classifier
    manager = SignalClassifierManager(model, confidence_threshold=args.threshold)
    
    # Classify signals
    logger.info("Classifying signals...")
    classifications = manager.classify_all_signals(signal_places_only=False)
    
    print(f"\nClassified {len(classifications)} signal places:")
    print("-" * 60)
    
    for place_name, (signal_type, confidence) in sorted(classifications.items()):
        print(f"{place_name:30s} -> {signal_type:12s} ({confidence:.2f})")
    
    # Generate report if requested
    if args.report:
        print("\n")
        print(manager.get_classification_report())
    
    # Validate if requested
    if args.validate:
        print("\nValidation Issues:")
        print("-" * 60)
        
        issues = manager.validate_classifications()
        
        for issue_type, places in issues.items():
            if places:
                print(f"\n{issue_type.replace('_', ' ').title()}:")
                for place_name in places:
                    print(f"  - {place_name}")
    
    # Apply classifications if requested
    if args.apply:
        logger.info("Applying classifications to model...")
        count = manager.apply_classifications(
            classifications=classifications,
            overwrite=args.overwrite
        )
        
        logger.info(f"Applied {count} classifications")
        
        # Save model
        output_file = args.model_file.replace('.shy', '_classified.shy')
        logger.info(f"Saving model to {output_file}")
        
        try:
            from shypn.file.file_saver import FileSaver
            saver = FileSaver()
            saver.save(model, output_file)
            logger.info("Model saved successfully")
        except Exception as e:
            logger.error(f"Failed to save model: {e}")
            return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
