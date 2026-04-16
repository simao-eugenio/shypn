#!/usr/bin/env python3
"""Quick fix: Add compound mappings to MAPK model.

This script updates the MAPK model file to include proper compound mappings
for thermodynamic validation.
"""

import json
from pathlib import Path
import shutil
from datetime import datetime

# Model file path
MODEL_FILE = Path("mapk/models/erk_cascade_oscillation_timed.shy")

# Backup suffix
BACKUP_SUFFIX = f".backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

# Compound mappings to add
COMPOUND_MAPPINGS = {
    # Energy compounds (have real thermodynamic data)
    "ATP": "C00002",  # Adenosine triphosphate
    "ADP": "C00008",  # Adenosine diphosphate
    
    # Proteins/enzymes (typically abstracted, but good to document)
    # Note: These don't have KEGG compound IDs, so we use descriptive placeholders
    # The validator will skip them if no database entry exists
    "Raf_inactive": "PROTEIN:RAF1",
    "Raf_active": "PROTEIN:RAF1_P",
    "MEK_inactive": "PROTEIN:MAP2K1",
    "MEK_PP": "PROTEIN:MAP2K1_PP",
    "ERK_inactive": "PROTEIN:MAPK1",
    "ERK_PP": "PROTEIN:MAPK1_PP",
    "ERK_PP_nuc": "PROTEIN:MAPK1_PP_NUCLEAR",
    
    # Phosphatases
    "PP2A": "PROTEIN:PPP2CA",
    "MKP": "PROTEIN:DUSP1",
    
    # Signal (doesn't need biochemical ID, but document for completeness)
    "Growth_Factor": "SIGNAL:EGF"
}

def main():
    print("=" * 80)
    print("MAPK Model: Adding Compound Mappings for Thermodynamic Validation")
    print("=" * 80)
    
    # Check if file exists
    if not MODEL_FILE.exists():
        print(f"❌ Error: Model file not found: {MODEL_FILE}")
        return 1
    
    # Create backup
    backup_file = Path(str(MODEL_FILE) + BACKUP_SUFFIX)
    print(f"\n1. Creating backup: {backup_file.name}")
    shutil.copy2(MODEL_FILE, backup_file)
    print(f"   ✅ Backup created")
    
    # Load model
    print(f"\n2. Loading model: {MODEL_FILE}")
    with open(MODEL_FILE, 'r') as f:
        model_data = json.load(f)
    
    # Check current mappings
    current_mappings = model_data.get("compound_mappings", {})
    print(f"   Current mappings: {len(current_mappings)}")
    if current_mappings:
        for name, cid in current_mappings.items():
            print(f"      {name} → {cid}")
    else:
        print(f"      (empty)")
    
    # Add new mappings
    print(f"\n3. Adding compound mappings:")
    model_data["compound_mappings"] = COMPOUND_MAPPINGS
    for name, compound_id in sorted(COMPOUND_MAPPINGS.items()):
        status = "✅" if compound_id.startswith("C") else "ℹ️ "
        print(f"   {status} {name:20s} → {compound_id}")
    
    # Save updated model
    print(f"\n4. Saving updated model...")
    with open(MODEL_FILE, 'w') as f:
        json.dump(model_data, f, indent=2)
    print(f"   ✅ Model saved")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"✅ Added {len(COMPOUND_MAPPINGS)} compound mappings")
    print(f"✅ Real biochemical compounds: ATP, ADP (have KEGG IDs)")
    print(f"ℹ️  Protein placeholders: RAF, MEK, ERK, PP2A, MKP")
    print(f"   (Will be skipped if no database entry)")
    print(f"\n📁 Backup saved as: {backup_file.name}")
    print(f"\n🧪 Test thermodynamic validation:")
    print(f"   1. Open model in SHYPN")
    print(f"   2. Go to Pathway Operations → THERMODYNAMICS")
    print(f"   3. Check compound mappings section")
    print(f"   4. Run topology analysis → Thermodynamic Validation")
    print("=" * 80)
    
    return 0

if __name__ == "__main__":
    exit(main())
