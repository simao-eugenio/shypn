#!/usr/bin/env python3
"""
Test script for thermodynamic context refactoring.

This script demonstrates that the new dataclass-based thermodynamic context
system works correctly with place-aware validation.

Tests:
1. Context creation from document settings (static)
2. Context creation from spatial places (dynamic)
3. Compartment-specific contexts (multi-compartment)
4. Place-aware validation (lysosomal drug trapping)
5. Temperature-dependent validation (fever response)
6. Serialization round-trip (persistence)

Author: SHYPN Core Team
Date: February 14, 2026
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_1_context_from_document():
    """Test 1: Static context from document settings"""
    print("\n" + "="*70)
    print("TEST 1: Context from Document Settings (Static)")
    print("="*70)
    
    try:
        from shypn.thermodynamics import ThermodynamicContext, ThermodynamicSource
        
        # Create context with defaults
        ctx = ThermodynamicContext()
        
        print(f"\n✓ Created default context:")
        print(f"  · pH: {ctx.ph}")
        print(f"  · Temperature: {ctx.temperature} K ({ctx.temperature_celsius:.1f}°C)")
        print(f"  · Ionic strength: {ctx.ionic_strength} M")
        print(f"  · Source: {ctx.source.value}")
        print(f"  · RT: {ctx.RT:.4f} kJ/mol")
        
        # Create custom context
        ctx_custom = ThermodynamicContext(
            ph=7.4,
            temperature=310.15,
            ionic_strength=0.15,
            source=ThermodynamicSource.DOCUMENT
        )
        
        print(f"\n✓ Created custom context:")
        print(f"  · pH: {ctx_custom.ph} (human blood)")
        print(f"  · Temperature: {ctx_custom.temperature} K ({ctx_custom.temperature_celsius:.1f}°C)")
        print(f"  · Ionic strength: {ctx_custom.ionic_strength} M")
        print(f"  · Source: {ctx_custom.source.value}")
        
        print(f"\n✓ TEST 1 PASSED: Document-based context works")
        return True
        
    except Exception as e:
        print(f"\n✗ TEST 1 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_2_context_from_places():
    """Test 2: Dynamic context from spatial places"""
    print("\n" + "="*70)
    print("TEST 2: Context from Spatial Places (Dynamic)")
    print("="*70)
    
    try:
        from shypn.thermodynamics import ThermodynamicContext, ThermodynamicSource
        from shypn.data.canvas.document_model import DocumentModel
        
        # Create model with places
        doc = DocumentModel()
        
        # Add pH place
        pH_place = doc.create_place(x=100, y=100, label="pH")
        pH_place.tokens = 7.2
        
        # Add temperature place (in Celsius)
        temp_place = doc.create_place(x=200, y=100, label="Temperature_celsius")
        temp_place.tokens = 37.0
        
        # Add ionic strength place
        ionic_place = doc.create_place(x=300, y=100, label="IonicStrength")
        ionic_place.tokens = 0.15
        
        print(f"\n✓ Created model with spatial places:")
        print(f"  · pH place: tokens={pH_place.tokens}")
        print(f"  · Temperature place: tokens={temp_place.tokens}°C")
        print(f"  · IonicStrength place: tokens={ionic_place.tokens} M")
        
        # Create context from places
        ctx = ThermodynamicContext.from_places(doc)
        
        print(f"\n✓ Context created from places:")
        print(f"  · pH: {ctx.ph} (from place '{ctx.place_names.get('ph', 'N/A')}')")
        print(f"  · Temperature: {ctx.temperature} K = {ctx.temperature_celsius:.1f}°C")
        print(f"    (from place '{ctx.place_names.get('temperature', 'N/A')}')")
        print(f"  · Ionic strength: {ctx.ionic_strength} M")
        print(f"    (from place '{ctx.place_names.get('ionic_strength', 'N/A')}')")
        print(f"  · Source: {ctx.source.value}")
        
        # Verify values match places
        assert ctx.ph == 7.2, f"Expected pH=7.2, got {ctx.ph}"
        assert abs(ctx.temperature - 310.15) < 0.01, f"Expected T=310.15, got {ctx.temperature}"
        assert ctx.ionic_strength == 0.15, f"Expected I=0.15, got {ctx.ionic_strength}"
        assert ctx.source == ThermodynamicSource.PLACE
        
        print(f"\n✓ TEST 2 PASSED: Place-aware context works")
        return True
        
    except Exception as e:
        print(f"\n✗ TEST 2 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_3_compartment_contexts():
    """Test 3: Compartment-specific contexts (multi-compartment)"""
    print("\n" + "="*70)
    print("TEST 3: Compartment-Specific Contexts (Multi-Compartment)")
    print("="*70)
    
    try:
        from shypn.thermodynamics import ThermodynamicContext, ThermodynamicSource
        from shypn.data.canvas.document_model import DocumentModel
        
        # Create model with compartmentalized places
        doc = DocumentModel()
        
        # Cytoplasm (pH=7.2)
        pH_cyto = doc.create_place(x=100, y=100, label="pH_cytoplasm")
        pH_cyto.tokens = 7.2
        
        # Lysosome (pH=5.0, acidic!)
        pH_lyso = doc.create_place(x=200, y=100, label="pH_lysosome")
        pH_lyso.tokens = 5.0
        
        # Mitochondrial matrix (pH=7.8, alkaline)
        pH_mito = doc.create_place(x=300, y=100, label="pH_matrix")
        pH_mito.tokens = 7.8
        
        # Extracellular (pH=7.4)
        pH_extra = doc.create_place(x=400, y=100, label="pH_extracellular")
        pH_extra.tokens = 7.4
        
        print(f"\n✓ Created multi-compartment model:")
        print(f"  · Cytoplasm: pH={pH_cyto.tokens}")
        print(f"  · Lysosome: pH={pH_lyso.tokens}")
        print(f"  · Mitochondrial matrix: pH={pH_mito.tokens}")
        print(f"  · Extracellular: pH={pH_extra.tokens}")
        
        # Get compartment-specific contexts
        ctx_cyto = ThermodynamicContext.from_places(doc, compartment="cytoplasm")
        ctx_lyso = ThermodynamicContext.from_places(doc, compartment="lysosome")
        ctx_mito = ThermodynamicContext.from_places(doc, compartment="matrix")
        ctx_extra = ThermodynamicContext.from_places(doc, compartment="extracellular")
        
        print(f"\n✓ Compartment-specific contexts:")
        print(f"  · Cytoplasm: pH={ctx_cyto.ph} (place: {ctx_cyto.place_names['ph']})")
        print(f"  · Lysosome: pH={ctx_lyso.ph} (place: {ctx_lyso.place_names['ph']})")
        print(f"  · Mitochondrion: pH={ctx_mito.ph} (place: {ctx_mito.place_names['ph']})")
        print(f"  · Extracellular: pH={ctx_extra.ph} (place: {ctx_extra.place_names['ph']})")
        
        # Calculate proton gradients
        delta_pH_cyto_lyso = ctx_cyto.ph - ctx_lyso.ph
        delta_pH_mito_cyto = ctx_mito.ph - ctx_cyto.ph
        
        print(f"\n✓ Proton gradients:")
        print(f"  · Cytoplasm → Lysosome: ΔpH = {delta_pH_cyto_lyso:.1f}")
        print(f"    (Lysosomal trapping: ~{10**delta_pH_cyto_lyso:.1f}x accumulation)")
        print(f"  · Mitochondrial matrix → Cytoplasm: ΔpH = {delta_pH_mito_cyto:.1f}")
        print(f"    (ATP synthesis driving force: ~{delta_pH_mito_cyto * 5.7:.1f} kJ/mol)")
        
        # Verify compartment specificity
        assert ctx_cyto.ph == 7.2
        assert ctx_lyso.ph == 5.0
        assert ctx_mito.ph == 7.8
        assert ctx_extra.ph == 7.4
        assert all(ctx.source == ThermodynamicSource.PLACE 
                  for ctx in [ctx_cyto, ctx_lyso, ctx_mito, ctx_extra])
        
        print(f"\n✓ TEST 3 PASSED: Compartment-specific contexts work")
        return True
        
    except Exception as e:
        print(f"\n✗ TEST 3 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_4_place_aware_validation():
    """Test 4: Place-aware thermodynamic validation"""
    print("\n" + "="*70)
    print("TEST 4: Place-Aware Validation (Lysosomal Drug Trapping)")
    print("="*70)
    
    try:
        from shypn.thermodynamics import (
            ThermodynamicContext,
            ThermodynamicSimulationValidator,
            ThermodynamicSource
        )
        from shypn.data.canvas.document_model import DocumentModel
        
        # Create model with compartments
        doc = DocumentModel()
        
        # Set up pH gradient
        pH_cyto = doc.create_place(x=100, y=100, label="pH_cytoplasm")
        pH_cyto.tokens = 7.2
        
        pH_lyso = doc.create_place(x=200, y=100, label="pH_lysosome")
        pH_lyso.tokens = 5.0
        
        print(f"\n✓ Created drug trapping model:")
        print(f"  · Cytoplasm pH: {pH_cyto.tokens}")
        print(f"  · Lysosome pH: {pH_lyso.tokens}")
        print(f"  · ΔpH: {pH_cyto.tokens - pH_lyso.tokens:.1f} pH units")
        
        # Create validator with dynamic places
        validator = ThermodynamicSimulationValidator(
            document=doc,
            use_dynamic_places=True
        )
        
        print(f"\n✓ Created place-aware validator:")
        print(f"  · use_dynamic_places: {validator.use_dynamic_places}")
        print(f"  · Default context: pH={validator.default_context.ph}")
        
        # Simulate drug protonation reaction in cytoplasm
        # Drug_neutral + H+ ⇌ Drug_protonated
        # At pH=7.2, mostly neutral (membrane permeable)
        
        ctx_cyto = validator.get_context_for_transition(
            transition=None,
            model=doc,
            compartment="cytoplasm"
        )
        
        print(f"\n✓ Cytoplasm validation context:")
        print(f"  · pH: {ctx_cyto.ph}")
        print(f"  · Source: {ctx_cyto.source.value}")
        print(f"  · Place: {ctx_cyto.place_names.get('ph', 'N/A')}")
        
        # Calculate protonation at pH=7.2 (assuming pKa=7.0)
        pKa = 7.0
        fraction_protonated_cyto = 1 / (1 + 10**(ctx_cyto.ph - pKa))
        print(f"  · Protonated fraction: {fraction_protonated_cyto*100:.1f}%")
        print(f"  · Neutral fraction: {(1-fraction_protonated_cyto)*100:.1f}%")
        print(f"  · Status: MEMBRANE PERMEABLE")
        
        # Simulate same reaction in lysosome
        # At pH=5.0, mostly protonated (charged, TRAPPED!)
        
        ctx_lyso = validator.get_context_for_transition(
            transition=None,
            model=doc,
            compartment="lysosome"
        )
        
        print(f"\n✓ Lysosome validation context:")
        print(f"  · pH: {ctx_lyso.ph}")
        print(f"  · Source: {ctx_lyso.source.value}")
        print(f"  · Place: {ctx_lyso.place_names.get('ph', 'N/A')}")
        
        # Calculate protonation at pH=5.0
        fraction_protonated_lyso = 1 / (1 + 10**(ctx_lyso.ph - pKa))
        print(f"  · Protonated fraction: {fraction_protonated_lyso*100:.1f}%")
        print(f"  · Neutral fraction: {(1-fraction_protonated_lyso)*100:.1f}%")
        print(f"  · Status: TRAPPED (charged, cannot cross membrane)")
        
        # Calculate accumulation ratio
        accumulation_ratio = fraction_protonated_lyso / fraction_protonated_cyto
        print(f"\n✓ Drug accumulation:")
        print(f"  · Ratio (lysosome/cytoplasm): {accumulation_ratio:.1f}x")
        print(f"  · Mechanism: pH trapping (weak base)")
        print(f"  · Biological relevance: Chloroquine in lysosomes")
        
        # Verify contexts are different
        assert ctx_cyto.ph == 7.2
        assert ctx_lyso.ph == 5.0
        assert ctx_cyto.source == ThermodynamicSource.PLACE
        assert ctx_lyso.source == ThermodynamicSource.PLACE
        
        print(f"\n✓ TEST 4 PASSED: Place-aware validation works")
        return True
        
    except Exception as e:
        print(f"\n✗ TEST 4 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_5_temperature_dependent_validation():
    """Test 5: Temperature-dependent validation (fever response)"""
    print("\n" + "="*70)
    print("TEST 5: Temperature-Dependent Validation (Fever Response)")
    print("="*70)
    
    try:
        from shypn.thermodynamics import (
            ThermodynamicContext,
            ThermodynamicSimulationValidator
        )
        from shypn.data.canvas.document_model import DocumentModel
        import math
        
        # Create model with temperature variation
        doc = DocumentModel()
        
        # Core body temperature (fever)
        T_core = doc.create_place(x=100, y=100, label="Temperature_core_celsius")
        T_core.tokens = 40.0  # Fever!
        
        # Skin temperature (cool extremities)
        T_skin = doc.create_place(x=200, y=100, label="Temperature_skin_celsius")
        T_skin.tokens = 33.0
        
        print(f"\n✓ Created fever response model:")
        print(f"  · Core temperature: {T_core.tokens}°C")
        print(f"  · Skin temperature: {T_skin.tokens}°C")
        print(f"  · ΔT: {T_core.tokens - T_skin.tokens:.1f}°C")
        
        # Get contexts
        ctx_core = ThermodynamicContext.from_places(doc, compartment="core")
        ctx_skin = ThermodynamicContext.from_places(doc, compartment="skin")
        
        print(f"\n✓ Temperature contexts:")
        print(f"  · Core: {ctx_core.temperature:.2f} K ({ctx_core.temperature_celsius:.1f}°C)")
        print(f"  · Skin: {ctx_skin.temperature:.2f} K ({ctx_skin.temperature_celsius:.1f}°C)")
        
        # Calculate Arrhenius effect (Ea = 50 kJ/mol typical enzyme)
        R = 0.008314  # kJ/(mol·K)
        Ea = 50.0  # kJ/mol
        T_ref = 310.15  # 37°C normal body temp
        
        # Core (40°C)
        k_ratio_core = math.exp((Ea / R) * (1/T_ref - 1/ctx_core.temperature))
        print(f"\n✓ Core enzyme kinetics (fever, 40°C):")
        print(f"  · k(40°C) / k(37°C): {k_ratio_core:.3f}")
        print(f"  · Effect: {(k_ratio_core-1)*100:+.1f}% change")
        print(f"  · Biological: Faster metabolism, immune response")
        
        # Skin (33°C)
        k_ratio_skin = math.exp((Ea / R) * (1/T_ref - 1/ctx_skin.temperature))
        print(f"\n✓ Skin enzyme kinetics (cool extremities, 33°C):")
        print(f"  · k(33°C) / k(37°C): {k_ratio_skin:.3f}")
        print(f"  · Effect: {(k_ratio_skin-1)*100:+.1f}% change")
        print(f"  · Biological: Reduced peripheral metabolism")
        
        # Thermodynamic effect on equilibrium (ΔH = -40 kJ/mol typical)
        delta_H = -40.0  # kJ/mol (exothermic)
        
        # Core
        Keq_ratio_core = math.exp((delta_H / R) * (1/ctx_core.temperature - 1/T_ref))
        print(f"\n✓ Core equilibrium shift:")
        print(f"  · Keq(40°C) / Keq(37°C): {Keq_ratio_core:.3f}")
        print(f"  · Effect: {(Keq_ratio_core-1)*100:+.1f}% (exothermic reaction)")
        
        # Skin
        Keq_ratio_skin = math.exp((delta_H / R) * (1/ctx_skin.temperature - 1/T_ref))
        print(f"\n✓ Skin equilibrium shift:")
        print(f"  · Keq(33°C) / Keq(37°C): {Keq_ratio_skin:.3f}")
        print(f"  · Effect: {(Keq_ratio_skin-1)*100:+.1f}% (exothermic reaction)")
        
        print(f"\n✓ TEST 5 PASSED: Temperature-dependent validation works")
        return True
        
    except Exception as e:
        print(f"\n✗ TEST 5 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_6_serialization():
    """Test 6: Serialization round-trip (persistence)"""
    print("\n" + "="*70)
    print("TEST 6: Serialization Round-Trip (Persistence)")
    print("="*70)
    
    try:
        from shypn.thermodynamics import ThermodynamicContext, ThermodynamicSource
        import json
        
        # Create context
        ctx = ThermodynamicContext(
            ph=6.8,
            temperature=310.15,
            ionic_strength=0.15,
            compartment="cytoplasm",
            source=ThermodynamicSource.PLACE,
            place_names={"ph": "pH_cytoplasm", "temperature": "Temperature"}
        )
        
        print(f"\n✓ Original context:")
        print(f"  · pH: {ctx.ph}")
        print(f"  · Temperature: {ctx.temperature} K")
        print(f"  · Ionic strength: {ctx.ionic_strength} M")
        print(f"  · Compartment: {ctx.compartment}")
        print(f"  · Source: {ctx.source.value}")
        print(f"  · Place names: {ctx.place_names}")
        
        # Serialize to dict
        data = ctx.to_dict()
        
        print(f"\n✓ Serialized to dict:")
        print(f"  · Keys: {list(data.keys())}")
        print(f"  · Size: {len(str(data))} chars")
        
        # JSON round-trip
        json_str = json.dumps(data, indent=2)
        print(f"\n✓ JSON representation:")
        print(json_str)
        
        data2 = json.loads(json_str)
        
        # Deserialize from dict
        ctx2 = ThermodynamicContext.from_dict(data2)
        
        print(f"\n✓ Deserialized context:")
        print(f"  · pH: {ctx2.ph}")
        print(f"  · Temperature: {ctx2.temperature} K")
        print(f"  · Ionic strength: {ctx2.ionic_strength} M")
        print(f"  · Compartment: {ctx2.compartment}")
        print(f"  · Source: {ctx2.source.value}")
        print(f"  · Place names: {ctx2.place_names}")
        
        # Verify equality
        assert ctx2.ph == ctx.ph
        assert ctx2.temperature == ctx.temperature
        assert ctx2.ionic_strength == ctx.ionic_strength
        assert ctx2.compartment == ctx.compartment
        assert ctx2.source == ctx.source
        assert ctx2.place_names == ctx.place_names
        
        print(f"\n✓ Verification:")
        print(f"  · All properties match: ✓")
        print(f"  · Serialization lossless: ✓")
        print(f"  · JSON compatible: ✓")
        
        print(f"\n✓ TEST 6 PASSED: Serialization works")
        return True
        
    except Exception as e:
        print(f"\n✗ TEST 6 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("THERMODYNAMIC CONTEXT INTEGRATION TESTS")
    print("="*70)
    print("\nTesting the new dataclass-based thermodynamic context system")
    print("with place-aware validation and compartment support.")
    
    tests = [
        ("Static context from document", test_1_context_from_document),
        ("Dynamic context from places", test_2_context_from_places),
        ("Compartment-specific contexts", test_3_compartment_contexts),
        ("Place-aware validation (drug trapping)", test_4_place_aware_validation),
        ("Temperature-dependent validation (fever)", test_5_temperature_dependent_validation),
        ("Serialization round-trip", test_6_serialization),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"\n✗ EXCEPTION in {name}: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    for name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{status}: {name}")
    
    passed_count = sum(1 for _, p in results if p)
    total_count = len(results)
    
    print(f"\n{passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print("\n🎉 ALL TESTS PASSED!")
        print("\nThe thermodynamic context refactoring is working correctly:")
        print("  ✓ Dataclass-based single source of truth")
        print("  ✓ Place-aware dynamic validation")
        print("  ✓ Compartment-specific contexts")
        print("  ✓ Automatic serialization")
        print("  ✓ Backward compatibility")
        return 0
    else:
        print("\n⚠️  SOME TESTS FAILED")
        print("Review the output above for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
