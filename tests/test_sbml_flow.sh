#!/bin/bash
# Test script for SBML import flow verification
# Tests the canvas pre-creation architecture

set -e

echo "========================================================================"
echo "SBML Import Flow Test"
echo "========================================================================"
echo ""
echo "Testing canvas pre-creation architecture:"
echo "  - Canvas created BEFORE parsing"
echo "  - State initialized immediately"
echo "  - No duplicate canvas creation"
echo ""
echo "========================================================================"
echo ""

# Run the test
cd "$(dirname "$0")"
python3 test_sbml_import_flow.py

# Capture exit code
EXIT_CODE=$?

echo ""
echo "========================================================================"
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ TEST PASSED"
else
    echo "❌ TEST FAILED"
fi
echo "========================================================================"

exit $EXIT_CODE
