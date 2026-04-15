#!/usr/bin/env python3
"""
Comprehensive certification of tumor N-methylation series (0-7).
Verifies spatial properties, parameters, rate functions, and stochastic transitions.
"""

import json
from pathlib import Path
from typing import Dict, List, Tuple, Any
from collections import defaultdict

# Configuration
BASE_PATH = Path("workspace/projects/My_Project/drug_discovery/models/manuscript")
NME_VARIANTS = list(range(8))  # 0-7

# Expected spatial configuration
EXPECTED_SPATIAL = {
    'P3': {'compartment_volume': 0.8, 'diffusion_coefficient': 150.0, 'boundary_type': 'impermeable', 'gradient_vector': None},
    'P4': {'compartment_volume': 0.5, 'diffusion_coefficient': 80.0, 'boundary_type': 'impermeable', 'gradient_vector': None},
    'P7': {'compartment_volume': 5.0, 'diffusion_coefficient': 300.0, 'boundary_type': 'impermeable', 'gradient_vector': None},
    'P8': {'compartment_volume': 5.0, 'diffusion_coefficient': 400.0, 'boundary_type': 'impermeable', 'gradient_vector': None},
    'P9': {'compartment_volume': 5.0, 'diffusion_coefficient': 600.0, 'boundary_type': 'impermeable', 'gradient_vector': None},
    'P10': {'compartment_volume': 1000.0, 'diffusion_coefficient': 2200.0, 'boundary_type': 'permeable', 'gradient_vector': None},
    'P11': {'compartment_volume': 0.1, 'diffusion_coefficient': 0.0, 'boundary_type': 'selective', 'gradient_vector': [1.0, 0.0, 0.0]},
    'P12': {'compartment_volume': 0.1, 'diffusion_coefficient': 0.0, 'boundary_type': 'selective', 'gradient_vector': [1.0, 0.0, 0.0]},
}

# Expected continuous transitions (should have rate functions)
CONTINUOUS_TRANSITIONS = ['T1', 'T2', 'T3', 'T4', 'T7', 'T8', 'T9']

# Expected adaptive transitions (should have rate_function in properties)
ADAPTIVE_TRANSITIONS = ['T5', 'T6', 'T10', 'T11']

class ModelCertifier:
    def __init__(self, model_path: Path, variant_num: int, cell_type: str):
        self.model_path = model_path
        self.variant_num = variant_num
        self.cell_type = cell_type
        self.model = None
        self.issues = []
        self.warnings = []
        self.info = []
        
    def load_model(self) -> bool:
        """Load model JSON."""
        try:
            with open(self.model_path, 'r') as f:
                self.model = json.load(f)
            return True
        except Exception as e:
            self.issues.append(f"Failed to load model: {e}")
            return False
    
    def check_spatial_properties(self) -> Dict[str, int]:
        """Verify spatial properties on all places."""
        results = {'pass': 0, 'fail': 0, 'warn': 0}
        
        places = {p['id']: p for p in self.model.get('places', [])}
        
        for place_id, expected in EXPECTED_SPATIAL.items():
            if place_id not in places:
                self.issues.append(f"Missing place: {place_id}")
                results['fail'] += 1
                continue
            
            place = places[place_id]
            place_ok = True
            
            # Check compartment_volume
            if 'compartment_volume' not in place:
                self.issues.append(f"{place_id}: Missing compartment_volume")
                place_ok = False
            elif place['compartment_volume'] != expected['compartment_volume']:
                self.issues.append(f"{place_id}: compartment_volume = {place['compartment_volume']}, expected {expected['compartment_volume']}")
                place_ok = False
            
            # Check diffusion_coefficient
            if 'diffusion_coefficient' not in place:
                self.issues.append(f"{place_id}: Missing diffusion_coefficient")
                place_ok = False
            elif place['diffusion_coefficient'] != expected['diffusion_coefficient']:
                self.issues.append(f"{place_id}: diffusion_coefficient = {place['diffusion_coefficient']}, expected {expected['diffusion_coefficient']}")
                place_ok = False
            
            # Check boundary_type
            if 'boundary_type' not in place:
                self.issues.append(f"{place_id}: Missing boundary_type")
                place_ok = False
            elif place['boundary_type'] != expected['boundary_type']:
                self.issues.append(f"{place_id}: boundary_type = {place['boundary_type']}, expected {expected['boundary_type']}")
                place_ok = False
            
            # Check gradient_vector
            place_gradient = place.get('gradient_vector')
            if expected['gradient_vector'] is None:
                if place_gradient is not None:
                    self.warnings.append(f"{place_id}: Has gradient_vector but shouldn't")
                    results['warn'] += 1
            else:
                if place_gradient != expected['gradient_vector']:
                    self.issues.append(f"{place_id}: gradient_vector = {place_gradient}, expected {expected['gradient_vector']}")
                    place_ok = False
            
            if place_ok:
                results['pass'] += 1
            else:
                results['fail'] += 1
        
        return results
    
    def check_parameters(self) -> Dict[str, int]:
        """Verify place parameters (markings, capacities)."""
        results = {'pass': 0, 'fail': 0, 'warn': 0}
        
        for place in self.model.get('places', []):
            place_id = place['id']
            place_ok = True
            
            # Check initial_marking exists
            if 'initial_marking' not in place:
                self.issues.append(f"{place_id}: Missing initial_marking")
                place_ok = False
            
            # Check marking exists
            if 'marking' not in place:
                self.issues.append(f"{place_id}: Missing marking")
                place_ok = False
            
            # Check capacity
            if 'capacity' not in place:
                self.issues.append(f"{place_id}: Missing capacity")
                place_ok = False
            
            # Warn if marking != initial_marking (should be reset)
            if 'marking' in place and 'initial_marking' in place:
                if place['marking'] != place['initial_marking']:
                    self.warnings.append(f"{place_id}: marking ({place['marking']}) != initial_marking ({place['initial_marking']})")
                    results['warn'] += 1
            
            if place_ok:
                results['pass'] += 1
            else:
                results['fail'] += 1
        
        return results
    
    def check_rate_functions(self) -> Dict[str, int]:
        """Verify rate functions on continuous transitions (must be in properties, optionally at top level)."""
        results = {'pass': 0, 'fail': 0, 'warn': 0}
        
        transitions = {t['id']: t for t in self.model.get('transitions', [])}
        
        for trans_id in CONTINUOUS_TRANSITIONS:
            if trans_id not in transitions:
                self.issues.append(f"Missing transition: {trans_id}")
                results['fail'] += 1
                continue
            
            trans = transitions[trans_id]
            trans_ok = True
            
            # Check transition_type
            trans_type = trans.get('transition_type', trans.get('type', ''))
            if trans_type != 'continuous':
                self.issues.append(f"{trans_id}: transition_type = '{trans_type}', expected 'continuous'")
                trans_ok = False
            
            # Check rate_function in properties dict (REQUIRED)
            if 'properties' not in trans:
                self.issues.append(f"{trans_id}: Missing properties dict")
                trans_ok = False
            elif 'rate_function' not in trans.get('properties', {}):
                self.issues.append(f"{trans_id}: Missing rate_function in properties (REQUIRED)")
                trans_ok = False
            elif not trans['properties']['rate_function']:
                self.issues.append(f"{trans_id}: Empty rate_function in properties")
                trans_ok = False
            
            # Top-level rate_function is OPTIONAL (some models have it, some don't)
            # Both patterns are valid for shypn
            
            # Verify rate_function is non-trivial
            if 'properties' in trans and 'rate_function' in trans['properties']:
                rate_func = trans['properties']['rate_function']
                if len(rate_func) < 10:
                    self.warnings.append(f"{trans_id}: Suspiciously short rate_function: '{rate_func}'")
                    results['warn'] += 1
            
            if trans_ok:
                results['pass'] += 1
            else:
                results['fail'] += 1
        
        return results
    
    def check_adaptive_transitions(self) -> Dict[str, int]:
        """Verify adaptive transitions (should have rate_function in properties)."""
        results = {'pass': 0, 'fail': 0, 'warn': 0}
        
        transitions = {t['id']: t for t in self.model.get('transitions', [])}
        
        # Check all adaptive transitions
        for trans_id in ADAPTIVE_TRANSITIONS:
            if trans_id not in transitions:
                self.issues.append(f"Missing adaptive transition: {trans_id}")
                results['fail'] += 1
                continue
            
            trans = transitions[trans_id]
            trans_ok = True
            trans_type = trans.get('transition_type', trans.get('type', ''))
            
            # Should be adaptive
            if trans_type != 'adaptive':
                self.issues.append(f"{trans_id}: transition_type = '{trans_type}', expected 'adaptive'")
                trans_ok = False
            
            # Should have rate_function in properties
            if 'properties' not in trans or 'rate_function' not in trans.get('properties', {}):
                self.issues.append(f"{trans_id}: Missing rate_function in properties (required for adaptive)")
                trans_ok = False
            elif not trans['properties']['rate_function']:
                self.issues.append(f"{trans_id}: Empty rate_function in properties")
                trans_ok = False
            
            # Should NOT have top-level rate_function (only in properties for adaptive non-hybrid)
            if 'rate_function' in trans:
                self.warnings.append(f"{trans_id}: Has top-level rate_function (not needed for simple adaptive)")
                results['warn'] += 1
            
            if trans_ok:
                results['pass'] += 1
            else:
                results['fail'] += 1
        
        return results
    
    def check_model_integrity(self) -> Dict[str, int]:
        """General model integrity checks."""
        results = {'pass': 0, 'fail': 0, 'warn': 0}
        
        # Check metadata
        if 'metadata' in self.model:
            results['pass'] += 1
        else:
            self.warnings.append("Missing metadata")
            results['warn'] += 1
        
        # Check places
        places = self.model.get('places', [])
        if len(places) >= 12:
            results['pass'] += 1
            self.info.append(f"Found {len(places)} places")
        else:
            self.issues.append(f"Only {len(places)} places, expected at least 12")
            results['fail'] += 1
        
        # Check transitions
        transitions = self.model.get('transitions', [])
        if len(transitions) >= 11:
            results['pass'] += 1
            self.info.append(f"Found {len(transitions)} transitions")
        else:
            self.issues.append(f"Only {len(transitions)} transitions, expected at least 11")
            results['fail'] += 1
        
        # Check arcs
        arcs = self.model.get('arcs', [])
        if len(arcs) >= 40:
            results['pass'] += 1
            self.info.append(f"Found {len(arcs)} arcs")
        else:
            self.warnings.append(f"Only {len(arcs)} arcs, expected at least 40")
            results['warn'] += 1
        
        return results
    
    def certify(self) -> Tuple[bool, Dict[str, Any]]:
        """Run full certification."""
        if not self.load_model():
            return False, {'issues': self.issues}
        
        print(f"\n{'=' * 80}")
        print(f"Certifying: N-Me {self.variant_num} ({self.cell_type})")
        print(f"File: {self.model_path.name}")
        print(f"{'=' * 80}")
        
        all_results = {}
        
        # 1. Spatial properties
        print("\n[1/5] Checking spatial properties...")
        spatial_results = self.check_spatial_properties()
        all_results['spatial'] = spatial_results
        print(f"  ✓ Pass: {spatial_results['pass']}, ✗ Fail: {spatial_results['fail']}, ⚠ Warn: {spatial_results['warn']}")
        
        # 2. Parameters
        print("\n[2/5] Checking place parameters...")
        param_results = self.check_parameters()
        all_results['parameters'] = param_results
        print(f"  ✓ Pass: {param_results['pass']}, ✗ Fail: {param_results['fail']}, ⚠ Warn: {param_results['warn']}")
        
        # 3. Rate functions
        print("\n[3/5] Checking rate functions...")
        rate_results = self.check_rate_functions()
        all_results['rate_functions'] = rate_results
        print(f"  ✓ Pass: {rate_results['pass']}, ✗ Fail: {rate_results['fail']}, ⚠ Warn: {rate_results['warn']}")
        
        # 4. Adaptive transitions
        print("\n[4/5] Checking adaptive transitions...")
        adaptive_results = self.check_adaptive_transitions()
        all_results['adaptive'] = adaptive_results
        print(f"  ✓ Pass: {adaptive_results['pass']}, ✗ Fail: {adaptive_results['fail']}, ⚠ Warn: {adaptive_results['warn']}")
        
        # 5. Model integrity
        print("\n[5/5] Checking model integrity...")
        integrity_results = self.check_model_integrity()
        all_results['integrity'] = integrity_results
        print(f"  ✓ Pass: {integrity_results['pass']}, ✗ Fail: {integrity_results['fail']}, ⚠ Warn: {integrity_results['warn']}")
        
        # Summary
        total_pass = sum(r['pass'] for r in all_results.values())
        total_fail = sum(r['fail'] for r in all_results.values())
        total_warn = sum(r['warn'] for r in all_results.values())
        
        print(f"\n{'─' * 80}")
        print(f"TOTALS: ✓ {total_pass} pass, ✗ {total_fail} fail, ⚠ {total_warn} warnings")
        
        # Display issues
        if self.issues:
            print(f"\n❌ ISSUES ({len(self.issues)}):")
            for issue in self.issues:
                print(f"  • {issue}")
        
        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  • {warning}")
        
        if self.info:
            print(f"\nℹ️  INFO:")
            for info in self.info:
                print(f"  • {info}")
        
        passed = total_fail == 0
        if passed:
            print(f"\n✅ CERTIFICATION PASSED")
        else:
            print(f"\n❌ CERTIFICATION FAILED")
        
        return passed, {
            'results': all_results,
            'issues': self.issues,
            'warnings': self.warnings,
            'info': self.info,
            'total_pass': total_pass,
            'total_fail': total_fail,
            'total_warn': total_warn
        }


def main():
    """Certify all tumor models."""
    print("=" * 80)
    print("COMPREHENSIVE TUMOR SERIES CERTIFICATION")
    print("=" * 80)
    print("\nVerifying:")
    print("  1. Spatial properties (volume, diffusion, boundary, gradients)")
    print("  2. Place parameters (markings, capacities)")
    print("  3. Rate functions (continuous transitions)")
    print("  4. Adaptive transitions (T5, T6, T10, T11)")
    print("  5. Model integrity (structure, counts)")
    
    certification_results = []
    
    for i in NME_VARIANTS:
        model_path = BASE_PATH / f'macrocycle_transport_tumor_nme_{i}_enhanced.shy'
        
        if not model_path.exists():
            print(f"\n❌ N-Me {i} (tumor): File not found")
            certification_results.append((i, False, None))
            continue
        
        certifier = ModelCertifier(model_path, i, 'tumor')
        passed, details = certifier.certify()
        certification_results.append((i, passed, details))
    
    # Final summary
    print("\n" + "=" * 80)
    print("CERTIFICATION SUMMARY - ALL TUMOR MODELS")
    print("=" * 80)
    
    total_passed = sum(1 for _, passed, _ in certification_results if passed)
    total_failed = len(certification_results) - total_passed
    
    print(f"\nResults: {total_passed}/8 passed, {total_failed}/8 failed\n")
    
    for variant, passed, details in certification_results:
        icon = "✅" if passed else "❌"
        if details:
            print(f"{icon} N-Me {variant} (tumor): Pass={details['total_pass']}, Fail={details['total_fail']}, Warn={details['total_warn']}")
        else:
            print(f"{icon} N-Me {variant} (tumor): Not checked")
    
    print("\n" + "=" * 80)
    
    if total_passed == 8:
        print("🎯 ALL TUMOR MODELS CERTIFIED")
        print("   Ready for simulation in UI")
        return 0
    else:
        print("⚠️  CERTIFICATION INCOMPLETE")
        print("   Review and fix issues before simulation")
        return 1

if __name__ == "__main__":
    exit(main())
