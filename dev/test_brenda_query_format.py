#!/usr/bin/env python3
"""Test different BRENDA query formats to find the correct syntax.

According to BRENDA SOAP documentation, the query format matters!
"""

import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from shypn.data.brenda_soap_client import ZEEP_AVAILABLE

if not ZEEP_AVAILABLE:
    print("ERROR: zeep library not available")
    sys.exit(1)

from zeep import Client
import hashlib

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_query_formats():
    """Test different BRENDA query string formats."""
    
    print("=" * 80)
    print("BRENDA Query Format Test")
    print("=" * 80)
    
    # Get credentials
    email = input("\nEmail: ").strip()
    password = input("Password: ").strip()
    
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    # Connect
    print("\n✓ Connecting to BRENDA...")
    client = Client("https://www.brenda-enzymes.org/soap/brenda_zeep.wsdl")
    
    # Test different query formats for EC 2.7.1.1 (hexokinase)
    test_formats = [
        ("ecNumber*2.7.1.1#", "Current format (with hash)"),
        ("ecNumber*2.7.1.1", "Without hash"),
        ("2.7.1.1", "Just EC number"),
        ("ecNumber*2.7.1.1#organism*#", "With empty organism"),
        ("ecNumber*2.7.1.1#organism*Homo sapiens#", "With specific organism"),
    ]
    
    print("\n" + "=" * 80)
    print("Testing Query Formats for EC 2.7.1.1 (Hexokinase)")
    print("=" * 80)
    
    for query_format, description in test_formats:
        print(f"\n--- Format: {description} ---")
        print(f"Query string: '{query_format}'")
        
        try:
            result = client.service.getKmValue(
                email,
                password_hash,
                query_format,  # EC number query
                '',            # organism filter
                '',            # kmValue
                '',            # kmValueMaximum
                '',            # substrate
                '',            # commentary
                '',            # ligandStructureId
                ''             # literature
            )
            
            result_list = list(result) if result else []
            print(f"Result: {len(result_list)} records")
            
            if result_list:
                print(f"✓ SUCCESS! Got {len(result_list)} Km values")
                print(f"First record: {result_list[0]}")
                break
            else:
                print(f"❌ Empty result")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n" + "=" * 80)
    print("Test Complete")
    print("=" * 80)

if __name__ == "__main__":
    test_query_formats()
