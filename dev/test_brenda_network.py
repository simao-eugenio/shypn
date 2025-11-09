#!/usr/bin/env python3
"""
BRENDA Network Diagnostic Tool

Tests network connectivity to BRENDA services to diagnose 403 Forbidden errors.
"""

import sys
import requests

def test_brenda_access():
    """Test access to BRENDA services."""
    
    print("=" * 70)
    print("BRENDA Network Diagnostic")
    print("=" * 70)
    print()
    
    tests = [
        ("Main website", "https://www.brenda-enzymes.org/"),
        ("SOAP WSDL", "https://www.brenda-enzymes.org/soap/brenda_zeep.wsdl"),
        ("SOAP endpoint", "https://www.brenda-enzymes.org/soap/brenda.php"),
    ]
    
    all_passed = True
    
    for name, url in tests:
        print(f"Testing {name}...")
        print(f"  URL: {url}")
        
        try:
            response = requests.get(url, timeout=10)
            status = response.status_code
            
            if status == 200:
                print(f"  ✓ Status: {status} OK")
                print(f"  ✓ Content-Type: {response.headers.get('content-type', 'unknown')}")
                print(f"  ✓ Size: {len(response.content)} bytes")
            elif status == 403:
                print(f"  ✗ Status: {status} FORBIDDEN")
                print(f"  ✗ BRENDA is blocking your access")
                all_passed = False
            else:
                print(f"  ⚠ Status: {status} ({response.reason})")
                all_passed = False
                
        except requests.exceptions.Timeout:
            print(f"  ✗ TIMEOUT - Server not responding")
            all_passed = False
        except requests.exceptions.ConnectionError as e:
            print(f"  ✗ CONNECTION ERROR: {e}")
            all_passed = False
        except Exception as e:
            print(f"  ✗ ERROR: {type(e).__name__}: {e}")
            all_passed = False
        
        print()
    
    print("=" * 70)
    
    if all_passed:
        print("✓ All tests passed - BRENDA is accessible")
        print("  → Your credentials might be the issue")
        print("  → Try resetting password at: https://www.brenda-enzymes.org/remember.php")
        return 0
    else:
        print("✗ Network access issues detected")
        print()
        print("Possible solutions:")
        print("  1. Try from a different network (home vs university vs mobile hotspot)")
        print("  2. Check if you're behind a firewall or VPN that blocks BRENDA")
        print("  3. Wait a few hours - you might be temporarily rate-limited")
        print("  4. Contact BRENDA support: info@brenda-enzymes.org")
        print("     - Mention: '403 Forbidden on SOAP WSDL access'")
        print("     - Include: Your email (eugenio.simao@ufsc.br)")
        print("     - Ask: 'Is my IP/network blocked from SOAP API access?'")
        return 1

if __name__ == "__main__":
    sys.exit(test_brenda_access())
