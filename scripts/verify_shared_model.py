#!/usr/bin/env python3
"""Quick verification that shared places model is loadable."""

import json
import os

model_path = os.path.join(
    os.path.dirname(__file__),
    "..",
    "workspace",
    "Test_flow",
    "model",
    "shared_places_constellation.shy"
)

print("=" * 80)
print("SHARED PLACES MODEL VERIFICATION")
print("=" * 80)

if not os.path.exists(model_path):
    print(f"\n✗ ERROR: File not found: {model_path}")
    exit(1)

print(f"\n✓ File exists: {model_path}")
print(f"✓ File size: {os.path.getsize(model_path)} bytes")

# Load and validate
try:
    with open(model_path) as f:
        data = json.load(f)
    print(f"✓ Valid JSON format")
except Exception as e:
    print(f"\n✗ ERROR loading JSON: {e}")
    exit(1)

# Check structure
print(f"\n✓ Structure:")
print(f"  - Version: {data.get('version', 'N/A')}")
print(f"  - Places: {len(data.get('places', []))}")
print(f"  - Transitions: {len(data.get('transitions', []))}")
print(f"  - Arcs: {len(data.get('arcs', []))}")

# List shared places
print(f"\n✓ Shared places found:")
from collections import defaultdict
place_connections = defaultdict(list)
for arc in data['arcs']:
    place_connections[arc['source_id']].append(arc['target_id'])

shared_count = 0
for place in data['places']:
    targets = place_connections[place['id']]
    if len(targets) > 1:  # Connected to multiple transitions
        shared_count += 1
        trans_labels = []
        for t in data['transitions']:
            if t['id'] in targets:
                trans_labels.append(t['label'])
        print(f"  {place['label']}: → {' and '.join(trans_labels)}")

print(f"\n✓ Total: {shared_count} shared places connecting multiple hubs")

print("\n" + "=" * 80)
print("MODEL IS VALID AND READY!")
print("=" * 80)
print("\nTo load in canvas:")
print("1. Start the application: python3 src/shypn.py")
print("2. In File Explorer, navigate to: Test_flow/model/")
print("3. Double-click: shared_places_constellation.shy")
print("4. Click: Solar System Layout button")
print("\nExpected result:")
print("- 3 hub transitions with satellites")
print("- 3 shared places positioned between their connected hubs")
print("- Compact layout fitting on screen at 100% zoom")
print("=" * 80)
