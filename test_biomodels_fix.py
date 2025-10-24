#!/usr/bin/env python3
"""
Test BioModels fetch fix - verify URL order and ZIP detection.

This test verifies the fix for the "XML content is not well-formed" error
that occurred when BioModels changed their API to return COMBINE archives
(ZIP files) by default instead of raw XML.
"""

import urllib.request
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from shypn.data.pathway.sbml_parser import SBMLParser


def test_url_order():
    """Test that the new URL order correctly gets XML, not ZIP."""
    print("=" * 70)
    print("TEST 1: URL Order and ZIP Detection")
    print("=" * 70)
    
    biomodels_id = "BIOMD0000000061"
    
    # URLs in the order used by the fixed code
    urls = [
        f"https://www.ebi.ac.uk/biomodels/model/download/{biomodels_id}?filename={biomodels_id}_url.xml",
        f"https://www.ebi.ac.uk/biomodels/model/download/{biomodels_id}?filename={biomodels_id}.xml",
        f"https://www.ebi.ac.uk/biomodels-main/download?mid={biomodels_id}",
    ]
    
    print(f"\nTesting BioModels ID: {biomodels_id}")
    print(f"Number of URLs to try: {len(urls)}\n")
    
    for idx, url in enumerate(urls, 1):
        print(f"URL {idx}: {url}")
        try:
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'SHYpn/2.0 (Python urllib)')
            req.add_header('Accept', 'application/xml, text/xml, */*')
            
            response = urllib.request.urlopen(req, timeout=15)
            content = response.read()
            
            # Check for ZIP magic number (PK)
            if content[:2] == b'PK':
                print(f"  ❌ FAILED: Content is ZIP archive (COMBINE format)")
                print(f"     This would cause 'XML not well-formed' error")
                continue
            
            # Check for XML
            if b'<?xml' in content[:200]:
                print(f"  ✅ SUCCESS: Content is valid XML")
                print(f"     Content-Type: {response.headers.get('Content-Type')}")
                print(f"     Size: {len(content):,} bytes")
                
                # Try to parse it
                print(f"\n  Attempting to parse SBML...")
                parser = SBMLParser()
                
                # Save to temp file
                import tempfile
                with tempfile.NamedTemporaryFile(mode='wb', suffix='.xml', delete=False) as f:
                    f.write(content)
                    temp_path = Path(f.name)
                
                try:
                    pathway_data = parser.parse_file(temp_path)
                    print(f"  ✅ PARSE SUCCESS!")
                    print(f"     Model: {pathway_data.metadata.get('model_name', 'Unknown')}")
                    print(f"     Species: {len(pathway_data.species)}")
                    print(f"     Reactions: {len(pathway_data.reactions)}")
                    return True
                finally:
                    temp_path.unlink()
            else:
                print(f"  ❌ FAILED: Content is not XML")
                
        except Exception as e:
            print(f"  ❌ ERROR: {e}")
    
    return False


def test_old_url_problem():
    """Demonstrate the problem with the old URL (without filename parameter)."""
    print("\n" + "=" * 70)
    print("TEST 2: Old URL Problem (for comparison)")
    print("=" * 70)
    
    biomodels_id = "BIOMD0000000061"
    old_url = f"https://www.ebi.ac.uk/biomodels/model/download/{biomodels_id}"
    
    print(f"\nOld URL (WITHOUT filename parameter): {old_url}")
    
    try:
        req = urllib.request.Request(old_url)
        req.add_header('User-Agent', 'SHYpn/2.0 (Python urllib)')
        
        response = urllib.request.urlopen(req, timeout=15)
        content = response.read()
        
        print(f"Content-Type: {response.headers.get('Content-Type')}")
        print(f"Size: {len(content):,} bytes")
        
        # Check what we got
        if content[:2] == b'PK':
            print("❌ PROBLEM CONFIRMED: This URL returns a ZIP archive!")
            print("   This is why we got 'XML not well-formed' error")
            print("   BioModels now defaults to COMBINE archive format")
            return True
        else:
            print("⚠️  URL behavior may have changed")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
    
    return False


def main():
    """Run all tests."""
    print("BioModels Fetch Fix Verification")
    print("Testing fix for 'XML content is not well-formed' error")
    print()
    
    test1_passed = test_url_order()
    test2_passed = test_old_url_problem()
    
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    if test1_passed:
        print("✅ NEW URL ORDER: Works correctly - fetches valid XML")
    else:
        print("❌ NEW URL ORDER: Failed - needs investigation")
    
    if test2_passed:
        print("✅ OLD URL PROBLEM: Confirmed - returns ZIP, not XML")
    else:
        print("⚠️  OLD URL PROBLEM: Could not reproduce")
    
    print("\nFIX STATUS:")
    if test1_passed:
        print("✅ The BioModels fetch fix is working correctly!")
        print("   Users can now fetch models without 'XML not well-formed' errors")
    else:
        print("❌ The fix needs more work")
    
    return 0 if test1_passed else 1


if __name__ == "__main__":
    sys.exit(main())
