#!/usr/bin/env python3
"""
BRENDA SOAP API Connection Test (with config file)

This version reads credentials from a config file to avoid terminal password issues.

Setup:
    1. Create a file called 'brenda_credentials.txt' in the same directory
    2. Put your email on the first line
    3. Put your password on the second line
    4. Run: python test_brenda_soap_config.py

Example brenda_credentials.txt:
    your.email@example.com
    YourVeryComplicatedPassword123!@#

The credentials file will be ignored by git (in .gitignore).
"""

import sys
import hashlib
from datetime import datetime
from pathlib import Path

# Check if zeep is installed
try:
    from zeep import Client, Settings
    from zeep.exceptions import Fault
except ImportError:
    print("ERROR: zeep library not installed")
    print("Install with: source venv/bin/activate && pip install zeep")
    sys.exit(1)

# BRENDA SOAP API Configuration
BRENDA_WSDL = "https://www.brenda-enzymes.org/soap/brenda_zeep.wsdl"
CREDENTIALS_FILE = Path(__file__).parent / "brenda_credentials.txt"


def read_credentials():
    """Read credentials from config file."""
    if not CREDENTIALS_FILE.exists():
        print(f"ERROR: Credentials file not found: {CREDENTIALS_FILE}")
        print()
        print("Create a file called 'brenda_credentials.txt' with:")
        print("  Line 1: Your BRENDA email")
        print("  Line 2: Your BRENDA password")
        print()
        print("Example:")
        print("  your.email@example.com")
        print("  YourPassword123")
        print()
        sys.exit(1)
    
    with open(CREDENTIALS_FILE, 'r') as f:
        lines = f.read().strip().split('\n')
    
    if len(lines) < 2:
        print("ERROR: Credentials file must have 2 lines (email and password)")
        sys.exit(1)
    
    email = lines[0].strip()
    password = lines[1].strip()
    
    if not email or not password:
        print("ERROR: Email and password cannot be empty")
        sys.exit(1)
    
    return email, password


def test_brenda_connection(email: str, password: str):
    """Test BRENDA SOAP API connection."""
    print("=" * 70)
    print("BRENDA SOAP API Connection Test")
    print("=" * 70)
    print(f"Email: {email}")
    print(f"WSDL: {BRENDA_WSDL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # Step 1: Hash password (BRENDA requires SHA256)
        print("Step 1: Hashing password (SHA256)...")
        password_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
        print(f"  Hash: {password_hash[:16]}... (truncated)")
        print()
        
        # Step 2: Create SOAP client
        print("Step 2: Creating SOAP client...")
        settings = Settings(strict=False, xml_huge_tree=True)
        client = Client(BRENDA_WSDL, settings=settings)
        print(f"  ✓ Client created successfully")
        print(f"  ✓ Available methods: {len(client.service._operations)} operations")
        print()
        
        # Step 3: Test simple query - getKmValue (tests authentication)
        print("Step 3: Testing authentication with getKmValue...")
        print("  Query: EC 2.7.1.1 (Hexokinase) for Homo sapiens")
        
        # BRENDA requires ALL parameters even if searching for all (use * wildcard)
        result = client.service.getKmValue(
            email,                        # email
            password_hash,                # password hash
            "ecNumber*2.7.1.1",          # EC number filter
            "organism*Homo sapiens",      # organism filter
            "kmValue*",                   # all Km values (wildcard)
            "kmValueMaximum*",            # all maximum values (wildcard)
            "substrate*",                 # all substrates (wildcard)
            "commentary*",                # all comments (wildcard)
            "ligandStructureId*",         # all ligand IDs (wildcard)
            "literature*"                 # all literature refs (wildcard)
        )
        
        print(f"  ✓ Query successful!")
        print()
        
        # Step 4: Parse result
        print("Step 4: Result received:")
        if result:
            result_str = str(result)
            if len(result_str) > 300:
                print(f"  {result_str[:300]}...")
                print(f"  (truncated, total length: {len(result_str)} chars)")
            else:
                print(f"  {result_str}")
        else:
            print("  (empty result)")
        print()
        
        print("=" * 70)
        print("✅ SUCCESS!")
        print("=" * 70)
        print()
        print("Your BRENDA credentials are ACTIVE and working!")
        print()
        print("You can now:")
        print("  1. Query kinetic parameters (Km, kcat, Vmax)")
        print("  2. Get enzyme names and classifications")
        print("  3. Retrieve organism-specific data")
        print("  4. Access literature references (PMID)")
        print()
        print("Next: Integrate BRENDA into SHYpn's auto-enrichment pipeline")
        print("=" * 70)
        
        return True
        
    except Fault as e:
        error_msg = str(e)
        print("=" * 70)
        print("❌ SOAP FAULT")
        print("=" * 70)
        print(f"Error: {error_msg}")
        print()
        
        if "authentication" in error_msg.lower() or "password" in error_msg.lower():
            print("Possible reasons:")
            print("  1. Credentials not yet activated (wait 1-2 business days)")
            print("  2. Incorrect email or password")
            print("  3. Account not registered at brenda-enzymes.org")
            print()
            print("Check:")
            print("  - Registration: https://www.brenda-enzymes.org/register.php")
            print("  - Confirmation email received?")
            print("  - Wait 1-2 business days for admin approval")
        
        print("=" * 70)
        return False
        
    except Exception as e:
        print("=" * 70)
        print("❌ CONNECTION ERROR")
        print("=" * 70)
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        print()
        print("Possible causes:")
        print("  - Network connectivity issues")
        print("  - BRENDA server temporarily down")
        print("  - Invalid WSDL format")
        print("=" * 70)
        return False


def main():
    """Main test function."""
    print()
    print("╔════════════════════════════════════════════════════════════════════╗")
    print("║       BRENDA SOAP API Connection Test (Config File Mode)          ║")
    print("╚════════════════════════════════════════════════════════════════════╝")
    print()
    
    # Read credentials from file
    email, password = read_credentials()
    
    print(f"Credentials loaded from: {CREDENTIALS_FILE}")
    print()
    
    # Test connection
    success = test_brenda_connection(email, password)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
