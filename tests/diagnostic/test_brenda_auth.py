#!/usr/bin/env python3
"""Test BRENDA authentication manually."""

import sys
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

sys.path.insert(0, 'src')

from shypn.data.brenda_soap_client import BRENDAAPIClient, ZEEP_AVAILABLE

print("="*60)
print("BRENDA Authentication Test")
print("="*60)

print(f"\n1. ZEEP_AVAILABLE: {ZEEP_AVAILABLE}")

if not ZEEP_AVAILABLE:
    print("ERROR: zeep library not installed!")
    print("Install with: pip install zeep")
    sys.exit(1)

print("\n2. Creating BRENDAAPIClient...")
client = BRENDAAPIClient()
print("   ✓ Client created")

print("\n3. Enter your BRENDA credentials:")
email = input("   Email: ").strip()
password = input("   Password: ").strip()

if not email or not password:
    print("ERROR: Email and password are required")
    sys.exit(1)

print(f"\n4. Attempting authentication for {email}...")
print("   (This may take a few seconds...)")

try:
    success = client.authenticate(email, password)
    
    if success:
        print("\n" + "="*60)
        print("✓ AUTHENTICATION SUCCESSFUL!")
        print("="*60)
        print(f"   Authenticated: {client.is_authenticated()}")
        print(f"   Client has SOAP connection: {client.client is not None}")
        
        # Try a simple query
        print("\n5. Testing query capability...")
        try:
            km_data = client.get_km_values("2.7.1.1")
            print(f"   ✓ Query successful! Retrieved {len(km_data)} Km values")
            if km_data:
                print(f"   Sample: {km_data[0]}")
        except Exception as e:
            print(f"   ✗ Query failed: {e}")
    else:
        print("\n" + "="*60)
        print("✗ AUTHENTICATION FAILED")
        print("="*60)
        print("   Please check your credentials")
        
except Exception as e:
    print("\n" + "="*60)
    print("✗ ERROR DURING AUTHENTICATION")
    print("="*60)
    print(f"   Error: {e}")
    import traceback
    traceback.print_exc()
