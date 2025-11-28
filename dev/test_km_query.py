#!/usr/bin/env python3
"""Quick test for BRENDA Km data retrieval with corrected query format."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from shypn.data.brenda_soap_client import BRENDAAPIClient

def main():
    print("=" * 70)
    print("🧪 Testing BRENDA Km Data Retrieval")
    print("=" * 70)
    
    # Get credentials
    email = input("\n📧 Email: ").strip()
    password = input("🔐 Password: ").strip()
    
    # Create and authenticate client
    print("\n🔐 Authenticating...")
    client = BRENDAAPIClient()
    
    if not client.authenticate(email, password):
        print("❌ Authentication failed!")
        return 1
    
    print("✅ Authentication successful!")
    
    # Test Km query for hexokinase (should have lots of data)
    print("\n" + "=" * 70)
    print("📊 Querying Km values for EC 2.7.1.1 (Hexokinase)")
    print("=" * 70)
    
    km_data = client.get_km_values("2.7.1.1", organism=None)
    
    if km_data:
        print(f"\n✅ SUCCESS! Found {len(km_data)} Km values!")
        print("\n📋 First 3 results:")
        for i, km in enumerate(km_data[:3], 1):
            print(f"\n  {i}. Substrate: {km.get('substrate', 'Unknown')}")
            print(f"     Km value: {km.get('value', '?')} {km.get('unit', 'mM')}")
            print(f"     Organism: {km.get('organism', 'Unknown')}")
            if km.get('literature'):
                print(f"     Reference: {km.get('literature')}")
    else:
        print("\n❌ No Km data found!")
        print("This might mean:")
        print("  1. Query format still incorrect")
        print("  2. BRENDA has no Km data for this EC (unlikely for hexokinase)")
        print("  3. Account access issue")
    
    print("\n" + "=" * 70)
    return 0

if __name__ == "__main__":
    sys.exit(main())
