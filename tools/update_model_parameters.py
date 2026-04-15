#!/usr/bin/env python3
"""
Utility for programmatically updating model parameters using proper DTO classes.

This script demonstrates the CORRECT way to modify model files:
1. Load model using DocumentModel.load_from_file() (respects DTOs)
2. Modify objects using their class properties (type-safe)
3. Save using DocumentModel.save_to_file() (respects DTOs)

This approach is superior to direct JSON manipulation because:
- Type safety: Properties validate inputs
- Compatibility: DTOs handle legacy format migrations
- Consistency: to_dict()/from_dict() ensure proper serialization
- Events: save_to_file() emits EventBus notifications for cache invalidation
"""

import sys
from pathlib import Path
from typing import Optional, Dict, Any

# Add shypn to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from shypn.data.canvas.document_model import DocumentModel


class ModelParameterEditor:
    """Helper class for safe programmatic model editing using DTOs.
    
    ⭐ MODEL-INDEPENDENT: Works with ANY .shy model file.
    
    This class uses generic DTO properties that exist in all models:
    - Transition.rate_function (universal property)
    - Place.initial_marking (universal property)
    - DocumentModel.load_from_file() (universal loader)
    
    Examples:
        # Glycolysis model
        editor = ModelParameterEditor('glycolysis.shy')
        editor.update_transition_rate_function('hexokinase', 'Vmax * glucose / (Km + glucose)')
        
        # MAPK cascade
        editor = ModelParameterEditor('mapk.shy')
        editor.update_transition_rate_function('RAF_activation', 'kcat * RAS * RAF')
        
        # Gene network
        editor = ModelParameterEditor('lac_operon.shy')
        editor.update_transition_rate_function('transcription', 'basal + induced * TF')
        
        # ANY custom model
        editor = ModelParameterEditor('my_model.shy')
        editor.update_transition_rate_function('T1', '0.5 * P1')
    """
    
    def __init__(self, model_path: str):
        """Initialize editor with model file.
        
        Args:
            model_path: Path to .shy model file
        """
        self.model_path = Path(model_path)
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model file not found: {model_path}")
        
        # Load using DTO (respects from_dict() logic)
        self.model = DocumentModel.load_from_file(str(self.model_path))
        print(f"✅ Loaded model: {self.model_path.name}")
        print(f"   Places: {len(self.model.places)}, Transitions: {len(self.model.transitions)}")
    
    def update_transition_rate_function(
        self, 
        transition_name: str, 
        new_rate_function: str
    ) -> bool:
        """Update transition rate function using proper DTO property.
        
        Args:
            transition_name: Name of transition to update (e.g., "GATA1_transcription")
            new_rate_function: New rate function expression
            
        Returns:
            bool: True if updated, False if transition not found
        """
        for transition in self.model.transitions:
            if transition.name == transition_name:
                # Use property setter (validates input, handles _properties dict)
                old_rate = transition.rate_function
                transition.rate_function = new_rate_function
                print(f"✅ Updated {transition_name}:")
                print(f"   Old: {old_rate}")
                print(f"   New: {new_rate_function}")
                return True
        
        print(f"❌ Transition '{transition_name}' not found")
        return False
    
    def update_place_initial_marking(
        self, 
        place_name: str, 
        new_marking: float
    ) -> bool:
        """Update place initial marking using proper DTO property.
        
        Args:
            place_name: Name of place to update (e.g., "ATP")
            new_marking: New initial marking value
            
        Returns:
            bool: True if updated, False if place not found
        """
        for place in self.model.places:
            if place.name == place_name:
                old_marking = place.initial_marking
                # Use property setter (validates input)
                place.initial_marking = new_marking
                # Also update current tokens
                place.tokens = new_marking
                print(f"✅ Updated {place_name}:")
                print(f"   Old: {old_marking} mM")
                print(f"   New: {new_marking} mM")
                return True
        
        print(f"❌ Place '{place_name}' not found")
        return False
    
    def update_transition_property(
        self,
        transition_name: str,
        property_name: str,
        property_value: Any
    ) -> bool:
        """Update arbitrary transition property.
        
        Args:
            transition_name: Name of transition
            property_name: Property name (e.g., 'Vmax', 'Km')
            property_value: New value
            
        Returns:
            bool: True if updated
        """
        for transition in self.model.transitions:
            if transition.name == transition_name:
                # Access _properties dict through properties property
                if not hasattr(transition, 'properties'):
                    transition.properties = {}
                
                old_value = transition.properties.get(property_name, 'N/A')
                transition.properties[property_name] = property_value
                print(f"✅ Updated {transition_name}.{property_name}:")
                print(f"   Old: {old_value}")
                print(f"   New: {property_value}")
                return True
        
        print(f"❌ Transition '{transition_name}' not found")
        return False
    
    def save(self, backup: bool = True) -> bool:
        """Save model using proper DTO serialization.
        
        Args:
            backup: Whether to create backup before saving
            
        Returns:
            bool: True if saved successfully
        """
        try:
            if backup:
                import shutil
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = self.model_path.with_name(
                    f"{self.model_path.stem}_backup_{timestamp}.shy"
                )
                shutil.copy2(self.model_path, backup_path)
                print(f"📁 Backup created: {backup_path.name}")
            
            # Save using DTO (respects to_dict() logic + emits EventBus event)
            self.model.save_to_file(str(self.model_path))
            print(f"💾 Model saved: {self.model_path.name}")
            print(f"   EventBus 'file.saved' event emitted → cache invalidated")
            return True
            
        except Exception as e:
            print(f"❌ Save failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def show_transition_info(self, transition_name: str) -> None:
        """Display transition information for debugging.
        
        Args:
            transition_name: Name of transition to inspect
        """
        for transition in self.model.transitions:
            if transition.name == transition_name:
                print(f"\n{'='*70}")
                print(f"Transition: {transition_name}")
                print(f"{'='*70}")
                print(f"  ID: {transition.id}")
                print(f"  Type: {transition.transition_type}")
                print(f"  Rate Function: {transition.rate_function}")
                print(f"  Properties: {transition.properties if hasattr(transition, 'properties') else {}}")
                print(f"{'='*70}\n")
                return
        
        print(f"❌ Transition '{transition_name}' not found")


# ============================================================================
# MODEL-SPECIFIC CONVENIENCE FUNCTIONS
# ============================================================================
# The functions below are model-specific wrappers for convenience.
# The ModelParameterEditor class above is completely model-independent.
# ============================================================================


def apply_gata_fixes(model_path: str) -> bool:
    """Apply all GATA model parameter fixes using proper DTO editing.
    
    ⚠️  MODEL-SPECIFIC: This function is specific to the GATA1/PU.1 model.
    
    The ModelParameterEditor class it uses is model-independent - you can
    create similar functions for your own models:
    
    Example:
        def apply_glycolysis_fixes(model_path: str):
            editor = ModelParameterEditor(model_path)
            editor.update_transition_rate_function('hexokinase', 'Vmax * glucose / Km')
            editor.save()
    
    Args:
        model_path: Path to phase3a_spatial_clean.shy
        
    Returns:
        bool: True if all fixes applied and saved
    """
    print("="*70)
    print("Applying GATA Model Parameter Fixes (DTO-based)")
    print("="*70)
    
    editor = ModelParameterEditor(model_path)
    
    # Fix 1: Transcription basal rates (1.2 → 0.08, 15× slower)
    print("\n📝 TRANSCRIPTION RATE FIXES:")
    editor.update_transition_rate_function(
        "GATA1_transcription",
        "0.08 * (1 + 0.5*GATA1_Protein_nuc/(5+GATA1_Protein_nuc)) / (1+(PU1_Protein_nuc/15)**2) * (1 + 2*EPO_external/(50+EPO_external))"
    )
    editor.update_transition_rate_function(
        "PU1_transcription",
        "0.08 * (1 + 0.5*PU1_Protein_nuc/(5+PU1_Protein_nuc)) / (1+(GATA1_Protein_nuc/15)**2) * (1 + 2*GCSF_external/(50+GCSF_external))"
    )
    
    # Fix 2: Protein degradation rates (nuclear: 0.01 → 0.05, cytoplasmic: 0.015 → 0.075)
    print("\n🗑️  DEGRADATION RATE FIXES:")
    editor.update_transition_rate_function(
        "GATA1_Protein_nuc_degradation",
        "0.05 * GATA1_Protein_nuc"
    )
    editor.update_transition_rate_function(
        "GATA1_Protein_cyto_degradation",
        "0.075 * GATA1_Protein_cyto"
    )
    editor.update_transition_rate_function(
        "PU1_Protein_nuc_degradation",
        "0.05 * PU1_Protein_nuc"
    )
    editor.update_transition_rate_function(
        "PU1_Protein_cyto_degradation",
        "0.075 * PU1_Protein_cyto"
    )
    
    # Save using DTO (emits EventBus event)
    print("\n" + "="*70)
    success = editor.save(backup=True)
    print("="*70)
    
    return success


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("┌─────────────────────────────────────────────────────────────────────┐")
        print("│ ModelParameterEditor - DTO-Based Model Editing                     │")
        print("│ ⭐ MODEL-INDEPENDENT: Works with ANY .shy model                     │")
        print("└─────────────────────────────────────────────────────────────────────┘")
        print("\nUsage:")
        print("  python update_model_parameters.py <model.shy>")
        print("\nExamples:")
        print("  # Auto-apply GATA model fixes (model-specific)")
        print("  python update_model_parameters.py workspace/projects/gata/models/phase3a_spatial_clean.shy")
        print()
        print("  # Use generically with ANY model in Python")
        print("  from update_model_parameters import ModelParameterEditor")
        print("  editor = ModelParameterEditor('glycolysis.shy')")
        print("  editor.update_transition_rate_function('hexokinase', 'Vmax * substrate / Km')")
        print("  editor.save()")
        print()
        print("  # Works with MAPK cascades")
        print("  editor = ModelParameterEditor('mapk.shy')")
        print("  editor.update_transition_rate_function('RAF_activation', 'kcat * RAS * RAF')")
        print()
        print("  # Works with gene networks")
        print("  editor = ModelParameterEditor('gene_network.shy')")
        print("  editor.update_transition_rate_function('transcription', 'basal + induced * TF')")
        print()
        print("  # Works with YOUR custom model")
        print("  editor = ModelParameterEditor('my_model.shy')")
        print("  editor.update_transition_rate_function('T1', '0.5 * P1')")
        print("  editor.update_place_initial_marking('P1', 100.0)")
        print("  editor.save()")
        sys.exit(1)
    
    model_path = sys.argv[1]
    
    # Check if this is the GATA model (convenience auto-apply)
    if 'gata' in model_path.lower() and 'phase3a' in model_path.lower():
        print("\n🎯 Detected GATA model - applying pre-configured fixes...")
        apply_gata_fixes(model_path)
    else:
        print(f"\n📂 Model: {model_path}")
        print("\n✅ ModelParameterEditor is model-independent!")
        print("   Use the class directly in Python for custom editing:")
        print()
        print("   from update_model_parameters import ModelParameterEditor")
        print("   editor = ModelParameterEditor('your_model.shy')")
        print("   editor.update_transition_rate_function('transition_name', 'new_rate')")
        print("   editor.save()")
        print()
        print("   See: examples/model_independent_editing.py for more examples")
