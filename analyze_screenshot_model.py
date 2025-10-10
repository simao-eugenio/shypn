#!/usr/bin/env python3
"""Ask user to provide the file path to analyze the actual model."""

print("""
To analyze the model shown in your screenshot, please:

1. Save the current model if you haven't (File → Save)
2. Provide the file path to the saved .shypn file

Or tell me:
- Which pathway did you import? (e.g., hsa00010)
- Did you use the GUI import or load a saved file?
- Can you export and send me the model file?

I need to see the actual DocumentModel to verify if:
a) Place-to-place arcs exist in the data (BUG!)
b) Transitions are too small to see (VISUAL ISSUE)
c) This is from an old file with legacy conversion (LEGACY)

Based on the screenshot, I can see compound IDs like:
- C01159, C00236, C00085, C00074, C00236, C15973
- Gene/enzyme labels like: PCK1, FBP1, BPGM, MINPP1, PKLR, LDHAL6A, ALDH3A1

This looks like Glycolysis or Pyruvate metabolism pathway.
""")

# Try to find recent .shypn files
import os
import glob
from pathlib import Path

home = Path.home()
possible_locations = [
    home / "projetos/shypn/data",
    home / "Documents",
    home / "Desktop",
    home,
]

print("\nSearching for recent .shypn files...")
found_files = []

for location in possible_locations:
    if location.exists():
        pattern = str(location / "**/*.shypn")
        files = glob.glob(pattern, recursive=True)
        found_files.extend(files)

if found_files:
    print(f"\nFound {len(found_files)} .shypn files:")
    # Sort by modification time
    found_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    for i, f in enumerate(found_files[:5], 1):
        mtime = os.path.getmtime(f)
        from datetime import datetime
        mod_date = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M')
        print(f"  {i}. {f}")
        print(f"     Modified: {mod_date}")
else:
    print("\nNo .shypn files found in common locations.")

print("\nPlease provide the file path or pathway ID to continue investigation.")

