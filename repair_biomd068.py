#!/usr/bin/env python3
"""Repair script for BIOMD0000000068 scientific notation bug."""

import sys
import re
import json

model_path = "/home/simao/projetos/shypn/workspace/projects/My_Project/models/BIOMD0000000068.shy"

print(f"Repairing: {model_path}")
print("="*80)

# Read file
with open(model_path, 'r') as f:
    content = f.read()

# Count occurrences before fix
before_count = content.count('e_')
print(f"Found {before_count} instances of 'e_' (malformed scientific notation)")

# Fix scientific notation: e_4 → e-4
fixed_content = re.sub(r'(\d)e_(\d)', r'\1e-\2', content)

# Count after fix  
after_count = fixed_content.count('e_')
fixes_applied = before_count - after_count
print(f"Applied {fixes_applied} fixes")

if fixes_applied > 0:
    # Write backup
    backup_path = model_path + ".backup"
    with open(backup_path, 'w') as f:
        f.write(content)
    print(f"✅ Backup saved to: {backup_path}")
    
    # Write fixed file
    with open(model_path, 'w') as f:
        f.write(fixed_content)
    print(f"✅ Repaired file saved")
    
    print("\n" + "="*80)
    print("SUCCESS: Model repaired!")
    print("Re-open the model in Shypn to use the fixed version.")
else:
    print("\nNo fixes needed - file already correct")
