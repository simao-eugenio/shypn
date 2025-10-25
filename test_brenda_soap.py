#!/usr/bin/env python3
"""
BRENDA SOAP API Connection Test

This script tests BRENDA SOAP API access using the zeep library.
It will help verify if your BRENDA credentials are active.

Requirements:
    pip install zeep

Usage:
    python test_brenda_soap.py

BRENDA Registration Info:
- Registration: https://www.brenda-enzymes.org/register.php
- SOAP API Docs: https://www.brenda-enzymes.org/soap.php
- Activation: Takes 1-2 business days after registration
"""

import sys
import hashlib
import getpass
from datetime import datetime

# Check if zeep is installed
try:
    from zeep import Client, Settings
    from zeep.exceptions import Fault
except ImportError:
    print("ERROR: zeep library not installed")
    print("Install with: pip install zeep")
    print()
    print("Then run this script again.")
    sys.exit(1)

# BRENDA SOAP API Configuration
BRENDA_WSDL = "https://www.brenda-enzymes.org/soap/brenda_zeep.wsdl"


def test_brenda_connection(email: str, password: str, verbose: bool = True):
    """
    Test BRENDA SOAP API connection with credentials.
    
    Args:
        email: BRENDA registration email
        password: BRENDA password (plain text, will be hashed)
        verbose: Print detailed progress
    
    Returns:
        tuple: (success: bool, message: str, data: dict or None)
    """
    if verbose:
        print("=" * 70)
        print("BRENDA SOAP API Connection Test")
        print("=" * 70)
        print(f"Email: {email}")
        print(f"WSDL: {BRENDA_WSDL}")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
    
    try:
        # Step 1: Hash password (BRENDA requires SHA256)
        if verbose:
            print("Step 1: Hashing password (SHA256)...")
        
        password_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
        
        if verbose:
            print(f"  Hash: {password_hash[:16]}... (truncated)")
            print()
        
        # Step 2: Create SOAP client
        if verbose:
            print("Step 2: Creating SOAP client...")
        
        settings = Settings(strict=False, xml_huge_tree=True)
        client = Client(BRENDA_WSDL, settings=settings)
        
        if verbose:
            print(f"  Client created successfully")
            print(f"  Available methods: {len(client.service._operations)} operations")
            print()
        
        # Step 3: Test simple query (check if EC number exists)
        if verbose:
            print("Step 3: Testing query (EC 2.7.1.1 - Hexokinase)...")
        
        # BRENDA SOAP requires a specific string format with all fields
        # Based on official examples: https://www.brenda-enzymes.org/soap.php
        result = client.service.getEcNumber(
            email,                      # User email
            password_hash,              # Hashed password
            "ecNumber*2.7.1.1",        # EC number filter  
            "organism*",                # Organism (empty but required)
            "transferredToEc*"          # Additional required field
        )
        
        if verbose:
            print(f"  Query successful!")
            print(f"  Result type: {type(result)}")
            print()
        
        # Parse result
        if result:
            if verbose:
                print("Step 4: Parsing result...")
                print(f"  Raw result: {result[:200]}..." if len(str(result)) > 200 else f"  Raw result: {result}")
                print()
            
            return (
                True,
                "Connection successful! BRENDA credentials are active.",
                {
                    'raw_result': str(result),
                    'email': email,
                    'timestamp': datetime.now().isoformat(),
                    'test_ec': '2.7.1.1',
                    'test_organism': 'Homo sapiens'
                }
            )
        else:
            return (
                False,
                "Query returned empty result. Credentials may not be activated yet.",
                None
            )
    
    except Fault as e:
        # SOAP fault (authentication error, invalid parameters, etc.)
        error_msg = str(e)
        
        if "authentication" in error_msg.lower() or "password" in error_msg.lower():
            return (
                False,
                f"Authentication failed: {error_msg}\n"
                "Possible reasons:\n"
                "  1. Credentials not yet activated (wait 1-2 business days)\n"
                "  2. Incorrect email or password\n"
                "  3. Account not registered at brenda-enzymes.org",
                None
            )
        else:
            return (
                False,
                f"SOAP Fault: {error_msg}",
                None
            )
    
    except Exception as e:
        # Network error, WSDL parsing error, etc.
        return (
            False,
            f"Connection error: {type(e).__name__}: {str(e)}",
            None
        )


def main():
    """Interactive BRENDA SOAP test."""
    print()
    print("╔════════════════════════════════════════════════════════════════════╗")
    print("║          BRENDA SOAP API Connection Test                          ║")
    print("╚════════════════════════════════════════════════════════════════════╝")
    print()
    print("This script will test your BRENDA credentials.")
    print("Registration takes 1-2 business days to activate.")
    print()
    
    # Get credentials
    email = input("BRENDA Email: ").strip()
    if not email:
        print("ERROR: Email is required")
        sys.exit(1)
    
    password = getpass.getpass("BRENDA Password: ").strip()
    if not password:
        print("ERROR: Password is required")
        sys.exit(1)
    
    print()
    
    # Test connection
    success, message, data = test_brenda_connection(email, password, verbose=True)
    
    # Print result
    print("=" * 70)
    print("RESULT")
    print("=" * 70)
    
    if success:
        print("✅ SUCCESS!")
        print()
        print(message)
        print()
        if data:
            print("Sample data retrieved:")
            print(f"  EC Number: {data.get('test_ec')}")
            print(f"  Organism: {data.get('test_organism')}")
            print(f"  Timestamp: {data.get('timestamp')}")
    else:
        print("❌ FAILED")
        print()
        print(message)
        print()
        print("Next steps:")
        print("  1. Verify you registered at: https://www.brenda-enzymes.org/register.php")
        print("  2. Check confirmation email (spam folder too)")
        print("  3. Wait 1-2 business days for admin approval")
        print("  4. Try this test again after activation")
    
    print("=" * 70)
    print()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
