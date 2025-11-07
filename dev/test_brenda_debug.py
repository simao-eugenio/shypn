#!/usr/bin/env python3
"""Debug BRENDA API responses to understand why no Km data is returned.

This script tests BRENDA authentication and queries, with extensive logging
to see the raw SOAP responses.
"""

import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from shypn.data.brenda_soap_client import BRENDAAPIClient, ZEEP_AVAILABLE

# Set up detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Test BRENDA API with debug output."""
    
    print("=" * 80)
    print("BRENDA API Debug Test")
    print("=" * 80)
    
    if not ZEEP_AVAILABLE:
        print("\n❌ ERROR: zeep library not available")
        print("Install with: pip install zeep")
        return 1
    
    print("\n✓ zeep library available")
    
    # Get credentials from user
    print("\n" + "=" * 80)
    print("Enter BRENDA credentials:")
    print("=" * 80)
    email = input("Email: ").strip()
    password = input("Password: ").strip()
    
    if not email or not password:
        print("\n❌ ERROR: Email and password required")
        return 1
    
    # Create client
    client = BRENDAAPIClient()
    
    # Test authentication
    print("\n" + "=" * 80)
    print("Testing Authentication")
    print("=" * 80)
    
    if not client.authenticate(email, password):
        print("\n❌ Authentication FAILED")
        return 1
    
    print("\n✓ Authentication SUCCEEDED")
    
    # Test EC numbers from glycolysis
    test_ec_numbers = [
        ("2.7.1.1", "Hexokinase"),
        ("5.3.1.9", "Glucose-6-phosphate isomerase"),
        ("2.7.1.11", "6-Phosphofructokinase"),
        ("4.1.2.13", "Fructose-bisphosphate aldolase"),
    ]
    
    print("\n" + "=" * 80)
    print("Testing Km Queries")
    print("=" * 80)
    
    for ec_number, name in test_ec_numbers:
        print(f"\n--- Testing EC {ec_number} ({name}) ---")
        
        try:
            km_values = client.get_km_values(ec_number, organism=None)
            
            if km_values:
                print(f"✓ Found {len(km_values)} Km values:")
                for i, km in enumerate(km_values[:3], 1):  # Show first 3
                    print(f"  {i}. {km.get('substrate', 'Unknown')} = {km.get('value', '?')} {km.get('unit', 'mM')}")
            else:
                print(f"❌ No Km data found for EC {ec_number}")
                print(f"   Check the logs above for [BRENDA_RAW] messages")
                
        except Exception as e:
            print(f"❌ Error querying EC {ec_number}: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("Test Complete")
    print("=" * 80)
    print("\nIf you see empty results for all EC numbers, this indicates:")
    print("1. Your BRENDA account may have LIMITED access")
    print("2. Free academic accounts often can authenticate but NOT retrieve data via SOAP")
    print("3. Full SOAP API access may require a paid/institutional account")
    print("\nContact BRENDA support for full API access:")
    print("  Email: info@brenda-enzymes.org")
    print("  Web: https://www.brenda-enzymes.org/contact.php")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
