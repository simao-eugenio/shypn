#!/usr/bin/env python3
"""Look up compound names from KEGG."""

import sys
import urllib.request
import time

sys.path.insert(0, 'src')

compound_ids = ['C06186', 'C06187', 'C06188', 'C06189']

print("Looking up compound information from KEGG...\n")

for cpd_id in compound_ids:
    try:
        url = f"http://rest.kegg.jp/get/cpd:{cpd_id}"
        with urllib.request.urlopen(url) as response:
            data = response.read().decode('utf-8')
            
        # Parse basic info
        lines = data.split('\n')
        name = None
        formula = None
        
        for line in lines:
            if line.startswith('NAME'):
                name = line.replace('NAME', '').strip().rstrip(';')
            elif line.startswith('FORMULA'):
                formula = line.replace('FORMULA', '').strip()
        
        print(f"{cpd_id}: {name}")
        if formula:
            print(f"  Formula: {formula}")
        print()
        
        time.sleep(0.5)  # Be nice to KEGG API
        
    except Exception as e:
        print(f"{cpd_id}: Error - {e}\n")

