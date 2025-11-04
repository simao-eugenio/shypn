#!/usr/bin/env python3
"""Test SABIO-RK EC number query to debug format."""

import requests
from urllib.parse import quote

# Test different query formats
ec_number = "2.7.1.1"
organism = "Homo sapiens"

test_cases = [
    # Case 1: Quotes around values (current implementation)
    f'ECNumber:"{ec_number}" AND Organism:"{organism}"',
    
    # Case 2: No quotes
    f'ECNumber:{ec_number} AND Organism:{organism}',
    
    # Case 3: Just EC number with quotes
    f'ECNumber:"{ec_number}"',
    
    # Case 4: Just EC number without quotes
    f'ECNumber:{ec_number}',
]

base_url = "https://sabiork.h-its.org/sabioRestWebServices"

for i, query in enumerate(test_cases, 1):
    print(f"\n{'='*70}")
    print(f"TEST CASE {i}: {query}")
    print(f"{'='*70}")
    
    try:
        # Test count endpoint first
        encoded_query = quote(query)
        url = f"{base_url}/searchKineticLaws/count?q={encoded_query}&format=txt"
        print(f"URL: {url}")
        
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        count_text = response.text.strip()
        print(f"Response: {count_text}")
        
        if "No results" in count_text or count_text == "0":
            print("❌ NO RESULTS")
        else:
            try:
                count = int(count_text)
                print(f"✅ Found {count} results")
            except ValueError:
                print(f"⚠️  Unexpected response: {count_text}")
                
    except Exception as e:
        print(f"❌ Error: {e}")

print(f"\n{'='*70}")
print("CONCLUSION:")
print("Check which format returns results successfully.")
