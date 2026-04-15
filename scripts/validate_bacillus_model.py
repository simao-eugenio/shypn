#!/usr/bin/env python3
"""
Validate Bacillus subtilis Sporulation Model

Tests for:
1. Signal Hierarchy Theory (5-layer structure)
2. Hierarchical Preemption (energy constraints)
3. Thermodynamic constraints
4. Signal Flow architecture
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple


class BacillusModelValidator:
    """Validator for Bacillus sporulation stress-test model."""
    
    def __init__(self, model_path: str):
        """Load model from file."""
        self.model_path = Path(model_path)
        with open(self.model_path, 'r') as f:
            self.model = json.load(f)
        
        self.places = self.model.get('places', [])
        self.transitions = self.model.get('transitions', [])
        self.arcs = self.model.get('arcs', [])
        
        self.issues = []
        self.warnings = []
        self.successes = []
    
    def validate_all(self) -> bool:
        """Run all validation checks."""
        print("=" * 80)
        print("BACILLUS SUBTILIS SPORULATION MODEL VALIDATION")
        print("=" * 80)
        print(f"\nModel: {self.model_path}")
        print(f"Places: {len(self.places)}, Transitions: {len(self.transitions)}, Arcs: {len(self.arcs)}")
        
        self.validate_signal_hierarchy()
        self.validate_hierarchical_preemption()
        self.validate_thermodynamic_data()
        self.validate_signal_flow_architecture()
        self.validate_energy_budget()
        self.validate_commitment_point()
        self.validate_spatial_compartments()
        
        # Report results
        print("\n" + "=" * 80)
        print("VALIDATION SUMMARY")
        print("=" * 80)
        
        if self.successes:
            print(f"\n✅ PASSED ({len(self.successes)}):")
            for success in self.successes:
                print(f"   ✓ {success}")
        
        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"   ! {warning}")
        
        if self.issues:
            print(f"\n❌ ISSUES ({len(self.issues)}):")
            for issue in self.issues:
                print(f"   ✗ {issue}")
            print("\n" + "=" * 80)
            return False
        else:
            print(f"\n{'=' * 80}")
            print("🎉 MODEL VALIDATION PASSED - Ready for stress testing!")
            print("=" * 80)
            return True
    
    def validate_signal_hierarchy(self):
        """Check 5-layer hierarchical structure."""
        print("\n" + "-" * 80)
        print("1. SIGNAL HIERARCHY THEORY (5 Layers)")
        print("-" * 80)
        
        signal_places = [p for p in self.places if p.get('is_signal_place')]
        
        if not signal_places:
            self.issues.append("No signal places found")
            return
        
        # Extract hierarchy layers
        layers = {}
        for p in signal_places:
            metadata = p.get('metadata', {})
            layer = metadata.get('hierarchy_layer')
            signal_type = metadata.get('signal_type', 'unknown')
            
            if layer is None:
                self.warnings.append(f"Place {p['name']} missing hierarchy_layer in metadata")
                continue
            
            if layer not in layers:
                layers[layer] = []
            layers[layer].append((p['name'], signal_type))
        
        # Check for 5-layer structure (L0-L5)
        expected_layers = [0, 1, 2, 3, 4, 5]
        found_layers = sorted(layers.keys())
        
        print(f"Signal places: {len(signal_places)}")
        print(f"Hierarchy layers found: {found_layers}")
        
        for layer in found_layers:
            print(f"\n  Layer {layer} ({len(layers[layer])} places):")
            for name, stype in sorted(layers[layer]):
                print(f"    - {name} [{stype}]")
        
        if found_layers == expected_layers:
            self.successes.append("5-layer hierarchy (L0-L5) correctly implemented")
        else:
            missing = set(expected_layers) - set(found_layers)
            if missing:
                self.issues.append(f"Missing hierarchy layers: {sorted(missing)}")
        
        # Validate layer semantics (refined with SPATIAL)
        expected_layer_types = {
            0: ['ENERGY'],
            1: ['QUORUM', 'SPATIAL'],  # SPATIAL for Nutrients (compartment resource)
            2: ['REGULATORY'],
            3: ['REGULATORY'],
            4: ['REGULATORY', 'SPATIAL'],  # SPATIAL for Septum (compartment marker)
            5: ['REGULATORY', 'SPATIAL']   # SPATIAL for compartments and products
        }
        
        for layer, places_list in layers.items():
            types_in_layer = set(stype for _, stype in places_list)
            expected = set(expected_layer_types.get(layer, []))
            
            if layer in expected_layer_types:
                if not types_in_layer.issubset(expected):
                    unexpected = types_in_layer - expected
                    self.warnings.append(
                        f"Layer {layer}: unexpected signal types {unexpected} "
                        f"(expected {expected})"
                    )
    
    def validate_hierarchical_preemption(self):
        """Check that energy (L0) can preempt all downstream layers."""
        print("\n" + "-" * 80)
        print("2. HIERARCHICAL PREEMPTION (Energy Override)")
        print("-" * 80)
        
        # Find energy places (ATP, GTP)
        energy_places = [
            p for p in self.places 
            if p.get('metadata', {}).get('signal_type') == 'ENERGY'
        ]
        
        if not energy_places:
            self.issues.append("No energy signal places (ENERGY type) found")
            return
        
        print(f"Energy places: {[p['name'] for p in energy_places]}")
        
        # Check signal flow arcs from energy places
        energy_place_ids = {p['id'] for p in energy_places}
        
        signal_flow_arcs_from_energy = [
            arc for arc in self.arcs
            if arc.get('source_id') in energy_place_ids
            and arc.get('arc_type') in ['signal_flow', 'curved_opposite_signal_flow']
        ]
        
        print(f"Signal flow arcs from energy places: {len(signal_flow_arcs_from_energy)}")
        
        if signal_flow_arcs_from_energy:
            # Check which transitions consume energy
            energy_consuming_transitions = set()
            for arc in signal_flow_arcs_from_energy:
                target_id = arc.get('target_id')
                trans = next((t for t in self.transitions if t['id'] == target_id), None)
                if trans:
                    energy_consuming_transitions.add(trans['name'])
            
            print(f"Transitions consuming energy: {len(energy_consuming_transitions)}")
            for tname in sorted(energy_consuming_transitions):
                print(f"  - {tname}")
            
            # Energy should reach multiple layers
            if len(energy_consuming_transitions) >= 5:
                self.successes.append(
                    f"Energy preemption: {len(energy_consuming_transitions)} transitions "
                    "consume ATP/GTP (hierarchical override)"
                )
            else:
                self.warnings.append(
                    f"Only {len(energy_consuming_transitions)} transitions consume energy. "
                    "Expected more for deep hierarchy preemption."
                )
        else:
            self.issues.append(
                "No signal_flow arcs from energy places - hierarchical preemption not implemented"
            )
    
    def validate_thermodynamic_data(self):
        """Check that transitions have thermodynamic data."""
        print("\n" + "-" * 80)
        print("3. THERMODYNAMIC CONSTRAINTS")
        print("-" * 80)
        
        # Check for thermodynamic data in transitions
        # It could be in properties or metadata or root
        transitions_with_thermo = []
        
        for trans in self.transitions:
            has_thermo = (
                'thermodynamic_data' in trans.get('properties', {}) or
                'thermodynamic_data' in trans.get('metadata', {}) or
                'thermodynamic_data' in trans
            )
            
            if has_thermo:
                transitions_with_thermo.append(trans['name'])
        
        print(f"Transitions with thermodynamic data: {len(transitions_with_thermo)} / {len(self.transitions)}")
        
        if transitions_with_thermo:
            for tname in transitions_with_thermo:
                print(f"  - {tname}")
            
            if len(transitions_with_thermo) == len(self.transitions):
                self.successes.append(
                    "All transitions have thermodynamic data (ΔG values)"
                )
            else:
                self.warnings.append(
                    f"Only {len(transitions_with_thermo)}/{len(self.transitions)} transitions "
                    "have thermodynamic data"
                )
        else:
            self.warnings.append(
                "No transitions have thermodynamic_data field. "
                "This is optional but recommended for thermodynamic validation."
            )
    
    def validate_signal_flow_architecture(self):
        """Check signal sensing vs signal flow distinction."""
        print("\n" + "-" * 80)
        print("4. SIGNAL FLOW ARCHITECTURE")
        print("-" * 80)
        
        # Count arc types
        arc_types = {}
        for arc in self.arcs:
            arc_type = arc.get('arc_type', 'normal')
            arc_types[arc_type] = arc_types.get(arc_type, 0) + 1
        
        print("Arc type distribution:")
        for arc_type in sorted(arc_types.keys()):
            count = arc_types[arc_type]
            print(f"  {arc_type}: {count}")
        
        signal_flow_count = arc_types.get('signal_flow', 0) + arc_types.get('curved_opposite_signal_flow', 0)
        test_arc_count = arc_types.get('test', 0)
        
        if signal_flow_count > 0:
            self.successes.append(
                f"Signal flow arcs: {signal_flow_count} (active token consumption)"
            )
        else:
            self.issues.append("No signal_flow arcs - energy consumption not modeled")
        
        if test_arc_count > 0:
            self.successes.append(
                f"Test arcs: {test_arc_count} (signal sensing without consumption)"
            )
        
        # Check that we have both paradigms
        if signal_flow_count > 0 and test_arc_count > 0:
            self.successes.append(
                "Model correctly distinguishes SIGNAL SENSING (test arcs) "
                "from SIGNAL FLOW (signal_flow arcs)"
            )
    
    def validate_energy_budget(self):
        """Check initial energy pools."""
        print("\n" + "-" * 80)
        print("5. ENERGY BUDGET")
        print("-" * 80)
        
        atp_place = next((p for p in self.places if 'ATP' in p['name'].upper()), None)
        gtp_place = next((p for p in self.places if 'GTP' in p['name'].upper()), None)
        
        if atp_place:
            atp_initial = atp_place.get('initial_marking', 0)
            print(f"ATP pool: {atp_initial} tokens")
            
            if atp_initial >= 500:
                self.successes.append(f"ATP pool ({atp_initial}) sufficient for sporulation (>500)")
            else:
                self.warnings.append(f"ATP pool ({atp_initial}) may be insufficient for full cascade")
        else:
            self.issues.append("No ATP pool found")
        
        if gtp_place:
            gtp_initial = gtp_place.get('initial_marking', 0)
            print(f"GTP pool: {gtp_initial} tokens")
            
            if gtp_initial >= 200:
                self.successes.append(f"GTP pool ({gtp_initial}) sufficient for FtsZ dynamics (>200)")
            else:
                self.warnings.append(f"GTP pool ({gtp_initial}) may be insufficient for septation")
        else:
            self.warnings.append("No GTP pool found")
    
    def validate_commitment_point(self):
        """Check for irreversible commitment (SigmaF)."""
        print("\n" + "-" * 80)
        print("6. COMMITMENT POINT (Irreversibility)")
        print("-" * 80)
        
        sigma_f = next((p for p in self.places if 'SigmaF' in p['name']), None)
        
        if sigma_f:
            print(f"SigmaF found: {sigma_f['name']}")
            layer = sigma_f.get('metadata', {}).get('hierarchy_layer')
            print(f"  Hierarchy layer: {layer}")
            
            if layer == 4:
                self.successes.append("SigmaF at Layer 4 (commitment point)")
            else:
                self.warnings.append(f"SigmaF at Layer {layer}, expected Layer 4")
        else:
            self.warnings.append("No SigmaF place found - commitment point not modeled")
    
    def validate_spatial_compartments(self):
        """Check spatial compartmentalization."""
        print("\n" + "-" * 80)
        print("7. SPATIAL COMPARTMENTS")
        print("-" * 80)
        
        compartments = set()
        for p in self.places:
            comp = p.get('metadata', {}).get('compartment')
            if comp:
                compartments.add(comp)
        
        print(f"Compartments found: {sorted(compartments)}")
        
        expected = {'cytoplasm', 'forespore', 'mother_cell'}
        if expected.issubset(compartments):
            self.successes.append(
                f"Spatial compartments: {sorted(compartments)} "
                "(cytoplasm, forespore, mother_cell)"
            )
        else:
            missing = expected - compartments
            if missing:
                self.warnings.append(f"Missing compartments: {sorted(missing)}")


def main():
    """Main validation entry point."""
    if len(sys.argv) > 1:
        model_path = sys.argv[1]
    else:
        model_path = "workspace/projects/My_Project/thermodynamics/bacillus_sporulation.shy"
    
    validator = BacillusModelValidator(model_path)
    success = validator.validate_all()
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
