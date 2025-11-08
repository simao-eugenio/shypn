#!/usr/bin/env python3
"""
Test BRENDA SOAP connection and authentication.

This script helps diagnose BRENDA API connection issues:
1. Tests network connectivity to BRENDA server
2. Verifies SOAP endpoint is accessible
3. Tests authentication with provided credentials
4. Performs a lightweight data query to verify API access

Usage:
    # Interactive (prompts for credentials):
    python test_brenda_connection.py
    
    # With command-line arguments:
    python test_brenda_connection.py --email your@email.com --password yourpass
    
    # With environment variables:
    export BRENDA_EMAIL="your@email.com"
    export BRENDA_PASSWORD="yourpass"
    python test_brenda_connection.py
"""

import sys
import logging
import argparse
import os
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / 'src'
sys.path.insert(0, str(src_path))

from shypn.data.brenda_soap_client import BRENDAAPIClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def get_credentials(args):
    """Get BRENDA credentials from various sources.
    
    Priority:
    1. Command-line arguments
    2. Environment variables
    3. Interactive prompt
    """
    email = args.email or os.environ.get('BRENDA_EMAIL')
    password = args.password or os.environ.get('BRENDA_PASSWORD')
    
    # If still missing, prompt interactively
    if not email:
        email = input("BRENDA Email: ").strip()
    else:
        print(f"Using email: {email}")
    
    if not email:
        print("✗ Email is required")
        return None, None
    
    if not password:
        import getpass
        password = getpass.getpass("BRENDA Password: ").strip()
    else:
        print("Using password from arguments/environment")
    
    if not password:
        print("✗ Password is required")
        return None, None
    
    return email, password


def test_brenda_connection(email, password):
    """Test BRENDA API connection step by step."""
    
    print("=" * 70)
    print("BRENDA SOAP API Connection Test")
    print("=" * 70)
    print()
    
    # Step 1: Check zeep availability
    print("Step 1: Checking dependencies...")
    try:
        import zeep
        print(f"✓ zeep library installed (version {zeep.__version__})")
    except ImportError:
        print("✗ zeep library NOT installed")
        print("  Install with: pip install zeep")
        return False
    print()
    
    # Step 2: Get credentials
    print("Step 2: BRENDA Credentials")
    print("-" * 70)
    print(f"Email: {email}")
    print(f"Password: {'*' * len(password)}")
    print()
    
    # Step 3: Test WSDL access
    print("Step 3: Testing WSDL endpoint access...")
    print("-" * 70)
    try:
        from zeep import Client
        wsdl_url = "https://www.brenda-enzymes.org/soap/brenda_zeep.wsdl"
        print(f"Connecting to: {wsdl_url}")
        client = Client(wsdl_url)
        print("✓ WSDL endpoint accessible")
        print(f"✓ SOAP service loaded: {len(client.wsdl.services)} service(s)")
    except Exception as e:
        print(f"✗ Failed to access WSDL: {e}")
        print("  This suggests network connectivity issues or BRENDA server is down")
        return False
    print()
    
    # Step 4: Test authentication
    print("Step 4: Testing BRENDA authentication...")
    print("-" * 70)
    
    api_client = BRENDAAPIClient()
    success = api_client.authenticate(email=email, password=password)
    
    if not success:
        print()
        print("=" * 70)
        print("AUTHENTICATION FAILED")
        print("=" * 70)
        print()
        print("Troubleshooting tips:")
        print("1. Verify your credentials at https://www.brenda-enzymes.org/")
        print("2. Check if your BRENDA account is active")
        print("3. Free accounts may have limited SOAP API access")
        print("4. Contact BRENDA support: info@brenda-enzymes.org")
        return False
    
    print()
    print("✓ Authentication successful!")
    print()
    
    # Step 5: Test data query
    print("Step 5: Testing data retrieval...")
    print("-" * 70)
    print("Querying Km values for EC 2.7.1.1 (hexokinase)...")
    
    try:
        km_values = api_client.get_km_values(ec_number="2.7.1.1", organism="Homo sapiens")
        
        if km_values:
            print(f"✓ Query successful! Retrieved {len(km_values)} Km value(s)")
            print()
            print("Sample data:")
            for i, km in enumerate(km_values[:3], 1):
                substrate = km.get('substrate', 'N/A')
                value = km.get('kmValue', 'N/A')
                organism = km.get('organism', 'N/A')
                print(f"  {i}. {substrate}: {value} ({organism})")
            if len(km_values) > 3:
                print(f"  ... and {len(km_values) - 3} more")
        else:
            print("⚠ Query successful but returned no data")
            print("  This may indicate limited API access for your account")
    except Exception as e:
        print(f"✗ Query failed: {e}")
        print("  Authentication worked but data retrieval failed")
        print("  Your account may not have SOAP API data access")
        return False
    
    print()
    print("=" * 70)
    print("CONNECTION TEST COMPLETE")
    print("=" * 70)
    print()
    print("✓ All tests passed!")
    print("✓ BRENDA SOAP API is working correctly with your credentials")
    print()
    
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Test BRENDA SOAP API connection',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Interactive mode:
  python test_brenda_connection.py
  
  # With arguments (password visible in process list):
  python test_brenda_connection.py --email user@example.com --password mypass
  
  # With environment variables (more secure):
  export BRENDA_EMAIL="user@example.com"
  export BRENDA_PASSWORD="mypass"
  python test_brenda_connection.py
        '''
    )
    parser.add_argument('--email', help='BRENDA account email')
    parser.add_argument('--password', help='BRENDA account password')
    
    args = parser.parse_args()
    
    try:
        email, password = get_credentials(args)
        if not email or not password:
            sys.exit(1)
        
        success = test_brenda_connection(email, password)
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.exception("Unexpected error during connection test")
        sys.exit(1)
