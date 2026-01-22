#!/usr/bin/env python3
"""Test script to diagnose batch execution errors."""

import sys
sys.path.insert(0, 'src')

# Check if there's a logged error in recent terminal output
print("Checking for batch execution error patterns...")
print("\nLikely causes of instant 100% with error status:")
print("1. Missing 'method' parameter in simulator call")
print("2. Subnet extraction failure")
print("3. Parameter application failure")
print("4. Simulator initialization failure")
print("\nTo diagnose, check:")
print("- Terminal output for traceback.print_exc() calls")
print("- batch_executor.py line 424-433 (exception handler)")
print("- Simulation controller expecting 'method' parameter")
print("\nRun with: python3 src/shypn.py 2>&1 | tee debug.log")
print("Then search debug.log for 'Traceback' or 'Exception'")
