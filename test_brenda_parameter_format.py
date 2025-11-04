#!/usr/bin/env python3
"""Test BRENDA SOAP parameter format.

Verify if BRENDA expects:
1. Multiple separate parameters (current implementation)
2. Single concatenated parameter string (BrendaSOAP Java approach)
"""

import os
import logging
import hashlib
from zeep import Client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

WSDL_URL = "https://www.brenda-enzymes.org/soap/brenda_zeep.wsdl"

email = os.getenv('BRENDA_EMAIL')
password = os.getenv('BRENDA_PASSWORD')

if not email or not password:
    print("❌ Set BRENDA_EMAIL and BRENDA_PASSWORD environment variables")
    exit(1)

# Calculate password hash
password_hash = hashlib.sha256(password.encode()).hexdigest()

print("=" * 80)
print("BRENDA SOAP Parameter Format Test")
print("=" * 80)
print(f"Email: {email}")
print(f"Password hash: {password_hash[:20]}...")
print()

# Initialize zeep client
client = Client(WSDL_URL)

print("\n--- Test 1: Current Implementation (Multiple Parameters) ---")
try:
    result = client.service.getKmValue(
        email,
        password_hash,
        'ecNumber*2.7.1.1#',  # Hexokinase
        '',  # organism
        '',  # kmValue
        '',  # kmValueMaximum
        '',  # substrate
        '',  # commentary
        '',  # ligandStructureId
        ''   # literature
    )
    print(f"Result type: {type(result)}")
    print(f"Result: {result}")
    print(f"Result length: {len(str(result)) if result else 0} chars")
    if result:
        print("✅ Multiple parameters approach returned data")
    else:
        print("❌ Multiple parameters approach returned empty/None")
except Exception as e:
    print(f"❌ Multiple parameters failed: {e}")

print("\n--- Test 2: BrendaSOAP Approach (Concatenated String) ---")
try:
    # Build parameter string like BrendaSOAP Java
    # Format: "email,hexString,ecNumber*2.7.1.1#organism*"
    parameter_string = f"{email},{password_hash},ecNumber*2.7.1.1#organism*"
    print(f"Parameter string: {parameter_string}")
    
    # Try calling with single concatenated parameter
    # Note: This may not work with zeep's service proxy, might need raw SOAP
    result = client.service.getKmValue(parameter_string)
    
    print(f"Result type: {type(result)}")
    print(f"Result: {result}")
    print(f"Result length: {len(str(result)) if result else 0} chars")
    if result:
        print("✅ Concatenated string approach returned data")
    else:
        print("❌ Concatenated string approach returned empty/None")
except Exception as e:
    print(f"❌ Concatenated string approach failed: {e}")

print("\n--- Test 3: Inspect WSDL Service Definition ---")
try:
    print("\nAvailable service methods:")
    for service in client.wsdl.services.values():
        print(f"  Service: {service.name}")
        for port in service.ports.values():
            print(f"    Port: {port.name}")
            for operation in port.binding._operations.values():
                print(f"      Operation: {operation.name}")
                # Try to get operation details
                if hasattr(operation, 'input'):
                    print(f"        Input signature: {operation.input.signature()}")
except Exception as e:
    print(f"Error inspecting WSDL: {e}")

print("\n--- Test 4: Check getEcNumber Method (Simpler) ---")
try:
    # Test with getEcNumber (used in authentication test)
    print("\nTrying getEcNumber with multiple parameters:")
    result = client.service.getEcNumber(
        email,
        password_hash,
        'ecNumber*2.7.1.1',
        'organism*',
        'transferredToEc*'
    )
    print(f"Result: {result}")
    print(f"Result length: {len(str(result)) if result else 0} chars")
    if result:
        print("✅ getEcNumber returned data")
    else:
        print("❌ getEcNumber returned empty/None")
except Exception as e:
    print(f"❌ getEcNumber failed: {e}")

print("\n" + "=" * 80)
print("Test Summary")
print("=" * 80)
print("""
If Test 1 (current approach) returns data:
  → Your implementation is correct, empty results are due to API access restrictions
  
If Test 2 (concatenated string) returns data:
  → BRENDA expects BrendaSOAP format, need to fix parameter passing
  
If both fail:
  → Your account lacks SOAP API data access (common with free accounts)
  → Contact BRENDA support: https://www.brenda-enzymes.org/support.php
""")
