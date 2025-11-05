#!/usr/bin/env python3
"""Test SABIO-RK EC query with updated threshold."""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from shypn.data.sabio_rk_client import SabioRKClient

client = SabioRKClient()

print("="*70)
print("TEST 1: EC 2.7.1.1 with Homo sapiens (149 results)")
print("="*70)
result = client.query_by_ec_number("2.7.1.1", "Homo sapiens")
if result:
    print(f"✅ SUCCESS: Got {len(result.get('parameters', []))} parameters")
else:
    print("❌ FAILED: No results (check if threshold rejected it)")

print("\n" + "="*70)
print("TEST 2: EC 2.7.1.1 without organism (799 results - should be rejected)")
print("="*70)
result = client.query_by_ec_number("2.7.1.1", None)
if result:
    print(f"✅ Got {len(result.get('parameters', []))} parameters")
else:
    print("✅ CORRECTLY REJECTED: Too many results (>150)")

print("\n" + "="*70)
print("TEST 3: EC 1.1.1.1 with Homo sapiens (likely fewer results)")
print("="*70)
result = client.query_by_ec_number("1.1.1.1", "Homo sapiens")
if result:
    print(f"✅ SUCCESS: Got {len(result.get('parameters', []))} parameters")
else:
    print("❌ FAILED: No results")
