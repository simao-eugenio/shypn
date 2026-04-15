#!/usr/bin/env python3
"""
Fix GTP Depletion in Phase 3A Model

Problem: GTP drops to 8.4% charge (depleted)
Solution: Increase GTP regeneration rate

Date: 2026-02-17
"""

import json
from pathlib import Path

def fix_gtp_depletion():
    """Increase GTP regeneration to prevent depletion"""
    
    model_path = Path("workspace/projects/gata/models/phase3a_spatial.shy")
    backup_path = model_path.with_suffix('.shy.backup_before_gtp_fix')
    
    print("🔧 Fixing GTP Depletion in Phase 3A Model\n")
    
    # Load model
    with open(model_path, 'r') as f:
        model = json.load(f)
    
    # Create backup
    with open(backup_path, 'w') as f:
        json.dump(model, f, indent=2)
    print(f"✅ Backup created: {backup_path}\n")
    
    # Find and fix GTP_regeneration
    print("=" * 60)
    print("GTP REGENERATION FIX")
    print("=" * 60)
    
    for transition in model['transitions']:
        if transition.get('name') == 'GTP_regeneration':
            old_rate = transition['properties'].get('rate_function', 'N/A')
            
            # Current rate: 100 * GDP * ATP / ((25 + GDP) * (500 + ATP))
            # This saturates at ~82 mM/s with high GDP and ATP
            # But GTP consumption is higher due to protein import (nuclear transport)
            
            # New rate: Increase by 5×
            # - Higher Vmax: 100 → 500
            # - Lower Km for GDP: 25 → 10 (binds more easily)
            new_rate = "500 * GDP * ATP / ((10 + GDP) * (500 + ATP))"
            
            transition['properties']['rate_function'] = new_rate
            
            print(f"✅ {transition.get('name', 'unnamed')} (ID: {transition['id']})")
            print(f"   OLD: {old_rate}")
            print(f"   NEW: {new_rate}")
            print()
            print(f"   Expected improvement:")
            print(f"   - Max rate: ~82 mM/s → ~410 mM/s (5× faster)")
            print(f"   - Should maintain GTP > 70% charge")
            print()
            
            break
    
    # Also check protein import transitions (consume GTP)
    print("=" * 60)
    print("GTP CONSUMPTION CHECK")
    print("=" * 60)
    print()
    
    import_count = 0
    for transition in model['transitions']:
        name = transition.get('name', '')
        if 'import' in name.lower() or 'nuclear' in name.lower():
            import_count += 1
            rate = transition['properties'].get('rate_function', 'N/A')
            print(f"📥 {name}:")
            print(f"   Rate: {rate[:60]}..." if len(rate) > 60 else f"   Rate: {rate}")
            print()
    
    print(f"Total import transitions: {import_count}")
    print("(These consume GTP for nuclear transport)")
    print()
    
    # Save updated model
    print("=" * 60)
    print("SAVING FIXED MODEL")
    print("=" * 60)
    
    # Update metadata
    if 'metadata' not in model:
        model['metadata'] = {}
    
    if 'provenance' not in model['metadata']:
        model['metadata']['provenance'] = []
    
    model['metadata']['provenance'].append({
        'timestamp': '2026-02-17T12:00:00Z',
        'action': 'fix_gtp_depletion',
        'description': 'Increased GTP regeneration rate to prevent depletion',
        'changes': [
            'GTP_regeneration: Vmax 100 → 500 (5× faster)',
            'GTP_regeneration: Km_GDP 25 → 10 (better binding)'
        ]
    })
    
    with open(model_path, 'w') as f:
        json.dump(model, f, indent=2)
    
    print(f"✅ Model saved: {model_path}")
    print(f"✅ Backup: {backup_path}")
    print()
    
    print("=" * 60)
    print("NEXT: TEST SIMULATION")
    print("=" * 60)
    print()
    print("Run a short test (500s) to verify GTP balance:")
    print("  1. Load phase3a_spatial.shy in shypn")
    print("  2. Set duration: 500s")
    print("  3. Run simulation")
    print("  4. Check final GTP charge (should be > 70%)")
    print()
    print("Expected results:")
    print("  ✅ GTP: ~350-400 mM (70-80% charge)")
    print("  ✅ GDP: ~150-200 mM")
    print("  ✅ Steady state achieved faster")

if __name__ == '__main__':
    fix_gtp_depletion()
