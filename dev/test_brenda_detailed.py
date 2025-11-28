#!/usr/bin/env python3
"""
Detailed BRENDA SOAP diagnostic tool.

Performs step-by-step testing with verbose output to diagnose connection issues.
"""

import sys
import hashlib
import argparse
from pathlib import Path

# Check zeep first
try:
    from zeep import Client, Settings
    from zeep.exceptions import Fault, TransportError
    ZEEP_AVAILABLE = True
    print("✓ zeep library available")
except ImportError as e:
    print(f"✗ zeep library NOT available: {e}")
    print("  Install with: pip install zeep")
    sys.exit(1)


def test_detailed(email, password):
    """Perform detailed step-by-step BRENDA test."""
    
    print("=" * 70)
    print("BRENDA SOAP API - Detailed Diagnostic")
    print("=" * 70)
    print()
    
    # Step 1: Display credentials (masked)
    print("Step 1: Credentials")
    print("-" * 70)
    print(f"Email: {email}")
    print(f"Password: {'*' * min(len(password), 20)}")
    print()
    
    # Step 2: Hash password
    print("Step 2: Hash password with SHA256")
    print("-" * 70)
    password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
    print(f"Hash (first 20 chars): {password_hash[:20]}...")
    print(f"Hash (full): {password_hash}")
    print()
    
    # Step 3: Connect to WSDL
    print("Step 3: Connect to BRENDA WSDL")
    print("-" * 70)
    wsdl_url = "https://www.brenda-enzymes.org/soap/brenda_zeep.wsdl"
    print(f"WSDL URL: {wsdl_url}")
    
    try:
        settings = Settings(strict=False, xml_huge_tree=True)
        client = Client(wsdl_url, settings=settings)
        print("✓ WSDL loaded successfully")
        print(f"✓ Service: {client.service}")
        print()
    except Exception as e:
        print(f"✗ Failed to load WSDL: {e}")
        print(f"  Error type: {type(e).__name__}")
        return False
    
    # Step 4: List available operations
    print("Step 4: Available SOAP operations")
    print("-" * 70)
    try:
        # Show some key methods
        methods = ['getEcNumber', 'getKmValue', 'getKcatKmValue', 'getTurnoverNumber']
        for method in methods:
            if hasattr(client.service, method):
                print(f"  ✓ {method}")
        print()
    except Exception as e:
        print(f"  Warning: Could not list methods: {e}")
        print()
    
    # Step 5: Test with getEcNumber (lightweight)
    print("Step 5: Test authentication with getEcNumber()")
    print("-" * 70)
    print("Calling: getEcNumber(email, password_hash, 'ecNumber*2.7.1.1', 'organism*', 'transferredToEc*')")
    print()
    
    try:
        result = client.service.getEcNumber(
            email,
            password_hash,
            'ecNumber*2.7.1.1',
            'organism*',
            'transferredToEc*'
        )
        
        print("✓ Call succeeded!")
        print(f"✓ Result type: {type(result)}")
        print(f"✓ Result length: {len(str(result))} chars")
        print()
        print("Result preview (first 500 chars):")
        print("-" * 70)
        result_str = str(result)
        print(result_str[:500])
        if len(result_str) > 500:
            print(f"... ({len(result_str) - 500} more chars)")
        print()
        print("=" * 70)
        print("✅ SUCCESS - BRENDA authentication working!")
        print("=" * 70)
        return True
        
    except Fault as e:
        print("✗ SOAP Fault occurred")
        print(f"  Fault code: {e.code}")
        print(f"  Fault string: {e.message}")
        print()
        print("This usually means:")
        print("  • Invalid credentials (wrong email or password)")
        print("  • Account not activated yet")
        print("  • Account access expired")
        print()
        print("=" * 70)
        print("❌ AUTHENTICATION FAILED")
        print("=" * 70)
        return False
        
    except TransportError as e:
        print("✗ Transport Error occurred")
        print(f"  Status code: {e.status_code}")
        print(f"  Message: {e.message}")
        print()
        print("This usually means:")
        print("  • Network connectivity issue")
        print("  • BRENDA server temporarily unavailable")
        print("  • Firewall blocking connection")
        print()
        print("=" * 70)
        print("❌ CONNECTION FAILED")
        print("=" * 70)
        return False
        
    except Exception as e:
        print(f"✗ Unexpected error: {type(e).__name__}")
        print(f"  Message: {str(e)}")
        print()
        
        # Try to provide more details
        if hasattr(e, '__dict__'):
            print("Error details:")
            for key, value in e.__dict__.items():
                print(f"  {key}: {value}")
        print()
        print("=" * 70)
        print("❌ TEST FAILED")
        print("=" * 70)
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Detailed BRENDA SOAP diagnostic',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--email', required=True, help='BRENDA account email')
    parser.add_argument('--password', required=True, help='BRENDA account password')
    
    args = parser.parse_args()
    
    success = test_detailed(args.email, args.password)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
