#!/usr/bin/env python3
"""Debug SABIO-RK count discrepancy."""

import requests
from urllib.parse import quote

ec_tests = [
    ("2.7.1.1", "Homo sapiens"),
    ("1.1.1.1", "Homo sapiens"),
]

base_url = "https://sabiork.h-its.org/sabioRestWebServices"

for ec, org in ec_tests:
    query = f'ECNumber:"{ec}" AND Organism:"{org}"'
    encoded = quote(query)
    url = f"{base_url}/searchKineticLaws/count?q={encoded}&format=txt"
    
    print(f"\nEC {ec} + {org}:")
    print(f"Query: {query}")
    
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        count = resp.text.strip()
        print(f"Count: {count}")
    except Exception as e:
        print(f"Error: {e}")
