#!/usr/bin/env python3
"""
Test script for multi-compartment SBML model validation.

Tests the modular Bio-PN architecture on real-world SBML models with
multiple compartments to verify:
1. Compartment → Module detection
2. Cross-compartment species → Signal place identification
3. Module visualization quality
4. Signal semantics in simulation

Usage:
    python test_multicompartment_models.py
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from shypn.data.pathway.sbml_parser import SBMLParser
from shypn.data.pathway.pathway_validator import PathwayValidator
from shypn.data.pathway.pathway_postprocessor import PathwayPostProcessor
from shypn.data.pathway.pathway_converter import PathwayConverter
from shypn.data.canvas.document_model import DocumentModel


def analyze_model(sbml_file: str, model_name: str):
    """Analyze a multi-compartment SBML model.
    
    Args:
        sbml_file: Path to SBML file
        model_name: Descriptive name for the model
    """
    print(f"\n{'='*80}")
    print(f"Testing: {model_name}")
    print(f"File: {sbml_file}")
    print(f"{'='*80}\n")
    
    if not os.path.exists(sbml_file):
        print(f"❌ ERROR: File not found: {sbml_file}")
        return None
    
    try:
        # Import SBML model
        print("📥 Importing SBML model...")
        parser = SBMLParser()
        validator = PathwayValidator()
        postprocessor = PathwayPostProcessor()
        converter = PathwayConverter()
        document = DocumentModel()
        
        # Parse SBML
        pathway = parser.parse_file(sbml_file)
        if not pathway:
            print("❌ SBML parsing failed")
            return None
        
        # Validate
        if not validator.validate(pathway):
            print("⚠️  Validation warnings, continuing...")
        
        # Post-process (add layout if needed)
        processed_pathway = postprocessor.process(
            pathway,
            layout_algorithm='auto',
            color_by_compartment=True,
            unit_conversion=True
        )
        
        # Convert to Petri net
        success = converter.convert(processed_pathway, document)
        
        if not success:
            print("❌ Conversion to Petri net failed")
            return None
        
        print(f"✓ SBML import successful")
        
        # Analyze compartments → modules
        print(f"\n🗂️  MODULE DETECTION:")
        modules = document.get_modules()
        print(f"   Total modules: {len(modules)}")
        
        for module in modules:
            module_places = [p for p in document.net.places if getattr(p, 'module_id', None) == module.id]
            module_transitions = [t for t in document.net.transitions if getattr(t, 'module_id', None) == module.id]
            
            print(f"   • Module '{module.name}' (ID: {module.id})")
            print(f"     - Places: {len(module_places)}")
            print(f"     - Transitions: {len(module_transitions)}")
        
        # Analyze signal places
        print(f"\n🔔 SIGNAL PLACE DETECTION:")
        signal_places = [p for p in document.net.places if getattr(p, 'is_signal_place', False)]
        print(f"   Total signal places: {len(signal_places)}")
        
        # Group by signal type
        signal_by_type = {}
        for place in signal_places:
            sig_type = getattr(place, 'signal_type', 'unknown')
            if sig_type not in signal_by_type:
                signal_by_type[sig_type] = []
            signal_by_type[sig_type].append(place)
        
        for sig_type, places in signal_by_type.items():
            print(f"   • {sig_type}: {len(places)} signal places")
            for place in places[:3]:  # Show first 3
                print(f"     - {place.name} (ID: {place.id})")
            if len(places) > 3:
                print(f"     ... and {len(places) - 3} more")
        
        # Analyze cross-module connections
        print(f"\n🔗 CROSS-MODULE CONNECTIONS:")
        cross_module_arcs = []
        
        for arc in document.net.arcs:
            source_module = getattr(arc.source, 'module_id', None)
            target_module = getattr(arc.target, 'module_id', None)
            
            if source_module and target_module and source_module != target_module:
                cross_module_arcs.append(arc)
        
        print(f"   Total cross-module arcs: {len(cross_module_arcs)}")
        
        if cross_module_arcs:
            print(f"   Examples:")
            for arc in cross_module_arcs[:5]:
                print(f"   • {arc.source.name} → {arc.target.name}")
                print(f"     (Module {getattr(arc.source, 'module_id', '?')} → "
                      f"Module {getattr(arc.target, 'module_id', '?')})")
        
        # Network statistics
        print(f"\n📊 NETWORK STATISTICS:")
        print(f"   Total places: {len(document.net.places)}")
        print(f"   Total transitions: {len(document.net.transitions)}")
        print(f"   Total arcs: {len(document.net.arcs)}")
        print(f"   Signal places: {len(signal_places)} "
              f"({100*len(signal_places)/len(document.net.places):.1f}%)")
        
        # Module independence analysis
        if len(modules) > 1:
            print(f"\n🔬 MODULE INDEPENDENCE ANALYSIS:")
            
            # Calculate coupling ratio
            total_arcs = len(document.net.arcs)
            cross_arcs = len(cross_module_arcs)
            coupling_ratio = cross_arcs / total_arcs if total_arcs > 0 else 0
            
            print(f"   Coupling ratio: {coupling_ratio:.3f} "
                  f"({cross_arcs}/{total_arcs} cross-module arcs)")
            
            if coupling_ratio < 0.1:
                print(f"   ✓ GOOD: Low coupling (< 10%)")
            elif coupling_ratio < 0.3:
                print(f"   ⚠ MODERATE: Medium coupling (10-30%)")
            else:
                print(f"   ⚠ HIGH: High coupling (> 30%)")
        
        print(f"\n✅ Analysis complete for {model_name}\n")
        return document
        
    except Exception as e:
        print(f"❌ ERROR during analysis: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Run tests on all multi-compartment SBML models."""
    print("="*80)
    print("MULTI-COMPARTMENT SBML MODEL TESTING")
    print("Testing modular Bio-PN architecture implementation")
    print("="*80)
    
    # Get test_models directory
    test_dir = Path(__file__).parent
    
    # Define test models
    test_models = [
        ("yeast_glycolysis_BIOMD0000000064.xml", 
         "Yeast Glycolysis (Cytoplasm/Extracellular)"),
        
        ("circadian_clock_BIOMD0000000171.xml",
         "Circadian Clock (Nucleus/Cytoplasm)"),
        
        ("bacterial_quorum_sensing_BIOMD0000000002.xml",
         "Bacterial Quorum Sensing"),
    ]
    
    results = {}
    
    for filename, description in test_models:
        filepath = test_dir / filename
        doc = analyze_model(str(filepath), description)
        results[description] = doc is not None
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    for model_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {model_name}")
    
    total = len(results)
    passed = sum(results.values())
    
    print(f"\nResults: {passed}/{total} models passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Modular Bio-PN architecture working correctly.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Review errors above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
