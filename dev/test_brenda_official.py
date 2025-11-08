#!/usr/bin/env python3
"""
Test BRENDA SOAP using EXACT official example format.

This uses the exact parameter format from:
https://www.brenda-enzymes.org/soap.php
"""

import sys
import hashlib
import argparse

try:
    from zeep import Client, Settings
    print("✓ zeep available")
except ImportError:
    print("✗ zeep not available - install with: pip install zeep")
    sys.exit(1)


def test_official_format(email, password):
    """Test using exact official BRENDA documentation format."""
    
    print("=" * 70)
    print("BRENDA SOAP - Official Format Test")
    print("=" * 70)
    print()
    
    print(f"Email: {email}")
    print(f"Password: {'*' * len(password)}")
    print()
    
    # Hash password exactly as in official docs
    print("Hashing password with SHA256...")
    password_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
    print(f"Hash: {password_hash[:20]}...")
    print()
    
    # Connect to WSDL
    print("Connecting to BRENDA WSDL...")
    wsdl = "https://www.brenda-enzymes.org/soap/brenda_zeep.wsdl"
    settings = Settings(strict=False)
    client = Client(wsdl, settings=settings)
    print("✓ Connected")
    print()
    
    # Test 1: getKmValue - EXACT format from official docs
    print("Test 1: getKmValue() - Official Format")
    print("-" * 70)
    print("Using official parameter format:")
    print('  parameters = (email, password_hash, "ecNumber*", "kmValue*", ...)')
    print()
    
    try:
        # EXACT format from official Python 3 example:
        # https://www.brenda-enzymes.org/soap.php
        parameters = (
            email,
            password_hash,
            "ecNumber*1.1.1.1",
            "organism*Homo sapiens",
            "kmValue*",
            "kmValueMaximum*",
            "substrate*",
            "commentary*",
            "ligandStructureId*",
            "literature*"
        )
        
        print(f"Calling: client.service.getKmValue(*parameters)")
        resultString = client.service.getKmValue(*parameters)
        
        print("✅ SUCCESS!")
        print(f"Result type: {type(resultString)}")
        
        if isinstance(resultString, list):
            print(f"Returned {len(resultString)} results")
            if resultString:
                print("\nFirst result:")
                print(resultString[0])
        else:
            result_str = str(resultString)
            print(f"Result length: {len(result_str)} chars")
            print("\nFirst 300 chars:")
            print(result_str[:300])
        
        print()
        print("=" * 70)
        print("✅ BRENDA SOAP API WORKING - CREDENTIALS VALID")
        print("=" * 70)
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {type(e).__name__}")
        print(f"Error: {str(e)}")
        print()
        
        # Check error message
        error_msg = str(e).lower()
        
        if "credentials" in error_msg or "authentication" in error_msg:
            print("💡 This looks like an authentication error")
            print()
            print("Possible causes:")
            print("  1. SOAP API access not enabled for your account")
            print("  2. Account not fully activated (check email)")
            print("  3. Different password for SOAP vs website")
            print()
            print("📧 Contact BRENDA support:")
            print("   Email: info@brenda-enzymes.org")
            print("   Subject: SOAP API access for [your email]")
            print()
            print("Important: SOAP API access is separate from website access!")
            print("You may need to specifically request SOAP API permissions.")
        
        elif "fault" in error_msg:
            print("💡 SOAP Fault - likely invalid credentials or no API access")
        
        elif "403" in error_msg or "forbidden" in error_msg:
            print("💡 403 Forbidden - server rejected connection")
            print("   This could be rate limiting or blocked access")
        
        print()
        print("=" * 70)
        print("❌ AUTHENTICATION FAILED")
        print("=" * 70)
        return False


def test_simple_method(email, password):
    """Try an even simpler method - getEcNumbersFromKmValue (no parameters)."""
    
    print()
    print("Test 2: Trying simpler method - getEcNumbersFromKmValue()")
    print("-" * 70)
    print("This method only requires email and password (no query parameters)")
    print()
    
    try:
        password_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
        wsdl = "https://www.brenda-enzymes.org/soap/brenda_zeep.wsdl"
        settings = Settings(strict=False)
        client = Client(wsdl, settings=settings)
        
        # Simple method with just credentials
        parameters = (email, password_hash)
        
        print("Calling: client.service.getEcNumbersFromKmValue(email, password_hash)")
        result = client.service.getEcNumbersFromKmValue(*parameters)
        
        print("✅ SUCCESS!")
        print(f"Result type: {type(result)}")
        
        if isinstance(result, list):
            print(f"Returned {len(result)} EC numbers")
            if result:
                print(f"Sample EC numbers: {result[:5]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Also failed: {type(e).__name__}: {str(e)}")
        return False


def main():
    parser = argparse.ArgumentParser(description='Test BRENDA SOAP with official format')
    parser.add_argument('--email', required=True, help='BRENDA email')
    parser.add_argument('--password', required=True, help='BRENDA password')
    
    args = parser.parse_args()
    
    success1 = test_official_format(args.email, args.password)
    
    if not success1:
        success2 = test_simple_method(args.email, args.password)
        sys.exit(0 if success2 else 1)
    
    sys.exit(0)


if __name__ == '__main__':
    main()
