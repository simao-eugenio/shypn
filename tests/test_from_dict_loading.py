#!/usr/bin/env python3
"""Test transition from_dict loading order."""

import sys
# This is a script-style test intended to be run directly (not via pytest).
if __name__ != '__main__':
    import pytest
    pytest.skip('Script-style test, run directly with python3', allow_module_level=True)

sys.path.insert(0, 'src')

from shypn.netobjs.transition import Transition

# Simulate JSON data with both top-level and properties rate_function
data = {
    "id": "T10",
    "name": "ATP_synthesis",
    "label": "ATP Synthesis",
    "x": 100.0,
    "y": 200.0,
    "transition_type": "adaptive",
    "rate": None,
    "rate_function": "OLD_VALUE",  # Legacy top-level (should be ignored)
    "properties": {
        "rate_function": "0.5 * [ADP_pool]"  # Correct location (should win)
    }
}

print("=" * 60)
print("Testing from_dict Loading Order")
print("=" * 60)

# Create transition from dict
t = Transition.from_dict(data)

print(f"\n1. Transition loaded:")
print(f"   ID: {t.id}")
print(f"   Name: {t.name}")
print(f"   Type: {t.transition_type}")

print(f"\n2. Rate function access:")
print(f"   t.rate_function = '{t.rate_function}'")
print(f"   t.properties['rate_function'] = '{t.properties.get('rate_function')}'")
print(f"   t._properties['rate_function'] = '{t._properties.get('rate_function')}'")

print(f"\n3. Properties dict:")
print(f"   t.properties = {t.properties}")

if t.rate_function == "0.5 * [ADP_pool]":
    print("\n✓ SUCCESS: rate_function from properties dict loaded correctly!")
    print("  Properties dict took precedence over top-level rate_function")
else:
    print(f"\n✗ FAILURE: Expected '0.5 * [ADP_pool]', got '{t.rate_function}'")
    sys.exit(1)

# Test legacy file without properties dict
print("\n" + "=" * 60)
print("Testing Legacy File (no properties dict)")
print("=" * 60)

data_legacy = {
    "id": "T11",
    "name": "old_transition",
    "x": 100.0,
    "y": 200.0,
    "rate_function": "k * [S]"  # Only top-level, no properties dict
}

t2 = Transition.from_dict(data_legacy)
print(f"\n1. Legacy transition:")
print(f"   t2.rate_function = '{t2.rate_function}'")
print(f"   t2.properties = {t2.properties}")

if t2.rate_function == "k * [S]":
    print("\n✓ SUCCESS: Legacy top-level rate_function loaded correctly!")
else:
    print(f"\n✗ FAILURE: Expected 'k * [S]', got '{t2.rate_function}'")
    sys.exit(1)

print("\n" + "=" * 60)
print("ALL TESTS PASSED ✓")
print("=" * 60)
