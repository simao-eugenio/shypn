#!/usr/bin/env python3
"""Debug mass action parsing"""

import re

pattern = r'mass_action\(([^,]+)(?:,\s*([^,)]+))?(?:,\s*rate_constant=([^)]+))?\)'

test_cases = [
    "mass_action(A, rate_constant=0.1)",
    "mass_action(A, B, rate_constant=0.5)",
]

for test in test_cases:
    print(f"\nTest: {test}")
    match = re.search(pattern, test)
    if match:
        print(f"  Groups: {match.groups()}")
    else:
        print("  NO MATCH")
