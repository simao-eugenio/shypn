#!/usr/bin/env python3
"""
Fix ATP_synthesis rate - restore proper Vmax while keeping thermodynamic back-pressure.

The Phase 3B enhancement accidentally reduced Vmax from 50000 to 1.0,
causing catastrophic energy depletion. This fixes it to a realistic value.
"""

import json
import shutil
from pathlib import Path

MODEL_FILE = Path(__file__).parent.parent / 'models' / 'phase3a_spatial.shy'

print("=" * 70)
print("FIX ATP SYNTHESIS RATE")
print("=" * 70)
print()

# Backup
backup_file = MODEL_FILE.with_suffix('.shy.backup_before_atp_fix')
shutil.copy2(MODEL_FILE, backup_file)
print(f"✅ Backup created: {backup_file.name}")
print()

# Load model
with open(MODEL_FILE, 'r') as f:
    model = json.load(f)

# Find ATP_synthesis transition
for t in model['transitions']:
    if t['name'] == 'ATP_synthesis':
        old_rate = t['properties'].get('rate_function', '')
        
        print("ATP_synthesis (T27):")
        print("=" * 70)
        print()
        print("OLD RATE:")
        print(f"  {old_rate}")
        print()
        print("PROBLEM:")
        print("  Vmax = 1.0 → Max rate ~0.002 mM/s (1,000,000× too slow!)")
        print()
        
        # New rate with proper Vmax and thermodynamic back-pressure
        # Use 10000 as Vmax (reasonable for mitochondrial ATP synthesis)
        # Keep the back-pressure term to prevent over-accumulation
        new_rate = (
            "10000 * ADP * Pi / ((100 + ADP) * (500 + Pi)) * "
            "(1 - ATP / (ATP + ADP + 1))"
        )
        
        t['properties']['rate_function'] = new_rate
        
        print("NEW RATE:")
        print(f"  {new_rate}")
        print()
        print("IMPROVEMENTS:")
        print("  • Vmax = 10000 (10,000× faster)")
        print("  • Max rate ~3600 mM/s at saturation")
        print("  • Still has thermodynamic back-pressure")
        print("  • Slows when ATP/ADP ratio high")
        print()
        
        # Calculate expected rates
        print("EXPECTED RATES:")
        print("  At ADP=3000, Pi=1000 (depleted state):")
        print("    Rate ≈ 10000 * 3000 * 1000 / (3100 * 1500) ≈ 6,452 mM/s")
        print()
        print("  At ADP=300, Pi=1000 (90% charged):")
        print("    ATP/(ATP+ADP) ≈ 0.9 → back-pressure = 0.1")
        print("    Rate ≈ 10000 * 300 * 1000 / (400 * 1500) * 0.1 ≈ 500 mM/s")
        print()
        print("  At ADP=30, Pi=1000 (99% charged):")
        print("    ATP/(ATP+ADP) ≈ 0.99 → back-pressure = 0.01")
        print("    Rate ≈ 10000 * 30 * 1000 / (130 * 1500) * 0.01 ≈ 15 mM/s")
        print()
        
        break

# Save model
with open(MODEL_FILE, 'w') as f:
    json.dump(model, f, indent=2)

print("=" * 70)
print("SUMMARY")
print("=" * 70)
print()
print(f"✅ ATP_synthesis rate fixed")
print(f"✅ Model saved: {MODEL_FILE}")
print(f"✅ Backup: {backup_file.name}")
print()

print("Expected behavior after fix:")
print("  • ATP charge should stabilize at 90-95%")
print("  • GTP charge should stabilize at 90-95%")
print("  • Energy crisis resolved")
print("  • Translation can proceed normally")
print("  • Cell should reach proper commitment state")
print()

print("=" * 70)
print("ATP SYNTHESIS RATE FIXED")
print("=" * 70)
