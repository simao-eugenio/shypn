#!/usr/bin/env python3
"""Annotate iJO1366 model with signal types for hierarchical analysis.

This script identifies key metabolites that act as regulatory signals
and annotates them with appropriate signal types:
- ENERGY: ATP, ADP, NAD+, NADH, etc.
- REGULATORY: cAMP, cGMP, ppGpp, (p)ppGpp, etc.
- SPATIAL: Compartment-specific signals

Runs headless (no GUI) and saves annotated model.
"""

import sys
import os
from pathlib import Path
from typing import Set, Dict, List

# Add src to path
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from shypn.data.canvas.document_model import DocumentModel
from shypn.netobjs.place import Place


# Energy currency metabolites (universal energy carriers)
ENERGY_SIGNALS = {
    'ATP', 'ADP', 'AMP',
    'GTP', 'GDP', 'GMP',
    'CTP', 'CDP', 'CMP',
    'UTP', 'UDP', 'UMP',
    'NAD+', 'NADH', 'NAD', 'NADH',
    'NADP+', 'NADPH', 'NADP', 'NADPH',
    'FAD', 'FADH2', 'FADH',
    'CoA', 'Acetyl-CoA', 'Coenzyme A',
    'Phosphate', 'Pyrophosphate', 'PPi',
    'H+', 'Proton'
}

# Regulatory signaling molecules (second messengers, alarmones)
REGULATORY_SIGNALS = {
    'cAMP', "3',5'-Cyclic AMP", 'Cyclic AMP',
    'cGMP', "3',5'-Cyclic GMP", 'Cyclic GMP',
    'ppGpp', 'pppGpp', 'Guanosine tetraphosphate',
    'Acetyl phosphate',
    'Fructose 1,6-bisphosphate',
    'Phosphoenolpyruvate', 'PEP'
}

# Key metabolic hubs that regulate multiple pathways
METABOLIC_HUB_SIGNALS = {
    'Pyruvate',
    'Glucose 6-phosphate', 'G6P',
    'Fructose 6-phosphate', 'F6P',
    'Citrate',
    'Oxaloacetate',
    'Succinate',
    'Malate',
    'Alpha-Ketoglutarate', '2-Oxoglutarate'
}


def normalize_metabolite_name(label: str) -> str:
    """Normalize metabolite name for matching.
    
    Args:
        label: Original label
        
    Returns:
        Normalized label (lowercase, no compartment suffix)
    """
    # Remove compartment suffixes (_c, _e, _p)
    if '_' in label:
        label = label.rsplit('_', 1)[0]
    
    # Convert to lowercase for case-insensitive matching
    return label.lower().strip()


def classify_signal_type(place: Place) -> str:
    """Classify place as ENERGY, REGULATORY, or METABOLIC hub.
    
    Args:
        place: Place to classify
        
    Returns:
        Signal type string or None if not a signal
    """
    label = getattr(place, 'label', '').strip()
    if not label:
        return None
    
    # Check against known signal sets
    normalized = normalize_metabolite_name(label)
    
    # Check for exact matches in signal sets
    for signal_name in ENERGY_SIGNALS:
        if signal_name.lower() in normalized or normalized in signal_name.lower():
            return 'energy'
    
    for signal_name in REGULATORY_SIGNALS:
        if signal_name.lower() in normalized or normalized in signal_name.lower():
            return 'regulatory'
    
    for signal_name in METABOLIC_HUB_SIGNALS:
        if signal_name.lower() in normalized or normalized in signal_name.lower():
            return 'regulatory'  # Metabolic hubs act as regulatory signals
    
    return None


def annotate_signal_places(doc: DocumentModel) -> Dict[str, int]:
    """Annotate places with signal types based on metabolite identity.
    
    Args:
        doc: DocumentModel to annotate
        
    Returns:
        Dictionary with counts per signal type
    """
    counts = {'energy': 0, 'regulatory': 0, 'kept_existing': 0}
    
    for place in doc.places:
        # Check if already marked as signal place
        is_signal = getattr(place, 'is_signal_place', False)
        
        # Classify based on metabolite name
        signal_type = classify_signal_type(place)
        
        if signal_type:
            # Mark as signal place with type
            place.is_signal_place = True
            
            # Import SignalType enum
            try:
                from shypn.netobjs.place import SignalType
                if signal_type == 'energy':
                    place.signal_type = SignalType.ENERGY
                    counts['energy'] += 1
                elif signal_type == 'regulatory':
                    place.signal_type = SignalType.REGULATORY
                    counts['regulatory'] += 1
            except ImportError:
                # Fallback: set as string
                place.signal_type = signal_type
                counts[signal_type] += 1
        elif is_signal and not signal_type:
            # Keep existing signal designation
            counts['kept_existing'] += 1
    
    return counts


def main():
    """Main annotation workflow."""
    print("=" * 70)
    print("iJO1366 SIGNAL ANNOTATION (Headless)")
    print("=" * 70)
    
    # Paths
    input_path = REPO_ROOT / "workspace" / "projects" / "My_Project" / "models" / "iJO1366.shy"
    output_path = REPO_ROOT / "workspace" / "projects" / "My_Project" / "models" / "iJO1366_annotated.shy"
    
    if not input_path.exists():
        print(f"\n❌ Error: Model not found at {input_path}")
        print("   Please import iJO1366 from BiGG first.")
        sys.exit(1)
    
    print(f"\nInput:  {input_path}")
    print(f"Output: {output_path}")
    
    # Load model
    print(f"\n📖 Loading iJO1366 model...")
    doc = DocumentModel.load_from_file(str(input_path))
    
    print(f"   ✓ Loaded: {len(doc.places)} places, {len(doc.transitions)} transitions, {len(doc.arcs)} arcs")
    
    # Count existing signal annotations
    existing_signals = sum(1 for p in doc.places if getattr(p, 'is_signal_place', False))
    print(f"   ✓ Existing signal places: {existing_signals}")
    
    # Annotate signal types
    print(f"\n🔬 Annotating signal types based on metabolite identity...")
    counts = annotate_signal_places(doc)
    
    print(f"\n📊 Annotation Results:")
    print(f"   Energy signals:     {counts['energy']}")
    print(f"   Regulatory signals: {counts['regulatory']}")
    print(f"   Kept existing:      {counts['kept_existing']}")
    print(f"   Total signals:      {sum(counts.values())}")
    
    # Sample annotated places
    energy_places = [p for p in doc.places if hasattr(p, 'signal_type') 
                     and str(getattr(p, 'signal_type', '')).lower() == 'energy']
    regulatory_places = [p for p in doc.places if hasattr(p, 'signal_type') 
                         and str(getattr(p, 'signal_type', '')).lower() in ['regulatory', 'signaltype.regulatory']]
    
    if energy_places:
        print(f"\n   Sample ENERGY signals:")
        for place in energy_places[:5]:
            label = getattr(place, 'label', 'unnamed')
            print(f"      • {label}")
    
    if regulatory_places:
        print(f"\n   Sample REGULATORY signals:")
        for place in regulatory_places[:5]:
            label = getattr(place, 'label', 'unnamed')
            print(f"      • {label}")
    
    # Save annotated model
    print(f"\n💾 Saving annotated model...")
    doc.save_to_file(str(output_path))
    
    file_size = output_path.stat().st_size / (1024 * 1024)
    print(f"   ✓ Saved: {output_path.name} ({file_size:.1f} MB)")
    
    print("\n" + "=" * 70)
    print("✅ ANNOTATION COMPLETE")
    print("=" * 70)
    print(f"\n💡 Next steps:")
    print(f"   1. Load annotated model: {output_path.name}")
    print(f"   2. Run hierarchical analysis: python scripts/test_ijo1366_hierarchical.py")
    print(f"   3. Verify signal layer detection with {sum(counts.values())} typed signals")


if __name__ == "__main__":
    main()
