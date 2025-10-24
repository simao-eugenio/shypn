#!/usr/bin/env python3
"""Test BioModels Fetch Functionality

Tests fetching BIOMD0000000061 from BioModels database.
"""

import sys
import os
from pathlib import Path

# Add src to path
repo_root = Path(__file__).parent
sys.path.insert(0, str(repo_root / 'src'))

print("=" * 70)
print("BIOMODELS FETCH TEST")
print("=" * 70)

biomodels_id = "BIOMD0000000061"
print(f"\nAttempting to fetch: {biomodels_id}")
print(f"URL: https://www.ebi.ac.uk/biomodels/model/download/{biomodels_id}?filename={biomodels_id}_url.xml")

# Test 1: Check if we can reach BioModels website
print("\n" + "=" * 70)
print("TEST 1: Check BioModels Website Availability")
print("=" * 70)

try:
    import urllib.request
    import urllib.error
    
    # Try to fetch the main page first
    test_url = "https://www.ebi.ac.uk/biomodels/"
    print(f"Testing connection to: {test_url}")
    
    req = urllib.request.Request(test_url, headers={'User-Agent': 'Shypn/1.0'})
    response = urllib.request.urlopen(req, timeout=10)
    status = response.getcode()
    
    print(f"✅ BioModels website is reachable (HTTP {status})")
    
except urllib.error.URLError as e:
    print(f"❌ Cannot reach BioModels website: {e}")
    print("   This could indicate:")
    print("   - Internet connection issues")
    print("   - BioModels server is down")
    print("   - Firewall blocking access")
    sys.exit(1)
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    sys.exit(1)

# Test 2: Try to fetch the actual model
print("\n" + "=" * 70)
print("TEST 2: Fetch Model SBML File")
print("=" * 70)

try:
    # Construct download URL
    download_url = f"https://www.ebi.ac.uk/biomodels/model/download/{biomodels_id}?filename={biomodels_id}_url.xml"
    print(f"Fetching: {download_url}")
    
    req = urllib.request.Request(download_url, headers={'User-Agent': 'Shypn/1.0'})
    response = urllib.request.urlopen(req, timeout=30)
    
    if response.getcode() == 200:
        content = response.read()
        content_type = response.headers.get('Content-Type', 'unknown')
        
        print(f"✅ Successfully fetched model!")
        print(f"   HTTP Status: {response.getcode()}")
        print(f"   Content-Type: {content_type}")
        print(f"   Content size: {len(content)} bytes")
        
        # Check if it looks like SBML
        content_str = content.decode('utf-8', errors='ignore')
        if '<sbml' in content_str.lower():
            print(f"   ✅ Content appears to be SBML XML")
            
            # Show first 500 chars
            print(f"\n   First 500 characters:")
            print("   " + "-" * 66)
            for line in content_str[:500].split('\n'):
                print(f"   {line}")
            print("   " + "-" * 66)
            
            # Save to temp file
            temp_file = repo_root / f"{biomodels_id}_test.xml"
            with open(temp_file, 'wb') as f:
                f.write(content)
            print(f"\n   💾 Saved to: {temp_file}")
            
        else:
            print(f"   ⚠️  Content doesn't appear to be SBML")
            print(f"   First 200 chars: {content_str[:200]}")
    else:
        print(f"❌ Unexpected HTTP status: {response.getcode()}")
        
except urllib.error.HTTPError as e:
    print(f"❌ HTTP Error {e.code}: {e.reason}")
    if e.code == 404:
        print(f"   Model {biomodels_id} not found in BioModels database")
    elif e.code == 503:
        print(f"   BioModels service temporarily unavailable")
    print(f"   URL: {download_url}")
    
except urllib.error.URLError as e:
    print(f"❌ URL Error: {e.reason}")
    print("   Possible causes:")
    print("   - DNS resolution failed")
    print("   - Connection timeout")
    print("   - Network unreachable")
    
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: Try to parse the fetched SBML
print("\n" + "=" * 70)
print("TEST 3: Parse Fetched SBML")
print("=" * 70)

temp_file = repo_root / f"{biomodels_id}_test.xml"
if temp_file.exists():
    try:
        from shypn.data.pathway.sbml_parser import SBMLParser
        
        parser = SBMLParser()
        pathway_data = parser.parse_file(temp_file)
        
        print(f"✅ Successfully parsed SBML!")
        print(f"   Model name: {pathway_data.metadata.get('name', 'Unknown')}")
        print(f"   Species: {len(pathway_data.species)}")
        print(f"   Reactions: {len(pathway_data.reactions)}")
        print(f"   Compartments: {len(pathway_data.compartments)}")
        print(f"   Parameters: {len(pathway_data.parameters)}")
        
        if pathway_data.species:
            print(f"\n   First 5 species:")
            for species in pathway_data.species[:5]:
                print(f"     - {species.id}: {species.name}")
        
        if pathway_data.reactions:
            print(f"\n   First 3 reactions:")
            for reaction in pathway_data.reactions[:3]:
                print(f"     - {reaction.id}: {reaction.name}")
                
    except Exception as e:
        print(f"❌ Parse failed: {e}")
        import traceback
        traceback.print_exc()
else:
    print("⚠️  No file to parse (fetch may have failed)")

print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)

if temp_file.exists():
    print(f"\n✅ BioModels fetch test PASSED")
    print(f"   Model {biomodels_id} successfully fetched and saved")
    print(f"   File: {temp_file}")
    print(f"\nYou can now:")
    print(f"   1. Open Shypn application")
    print(f"   2. Go to Pathway Panel → SBML Tab")
    print(f"   3. Enter BioModels ID: {biomodels_id}")
    print(f"   4. Click 'Fetch from BioModels'")
else:
    print(f"\n❌ BioModels fetch test FAILED")
    print(f"   Could not fetch model {biomodels_id}")
    print(f"   Check the error messages above")

print("\n" + "=" * 70)
