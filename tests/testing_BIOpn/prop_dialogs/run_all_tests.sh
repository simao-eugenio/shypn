#!/bin/bash
# Run all property dialog integration tests

echo "========================================"
echo "Property Dialog Integration Test Suite"
echo "========================================"
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TESTS_PASSED=0
TESTS_FAILED=0

# Function to run a test
run_test() {
    local test_file=$1
    local test_name=$2
    
    echo ""
    echo "Running: $test_name"
    echo "----------------------------------------"
    
    if python3 "$test_file"; then
        echo "✓ $test_name PASSED"
        ((TESTS_PASSED++))
    else
        echo "✗ $test_name FAILED"
        ((TESTS_FAILED++))
    fi
}

# Run all tests
run_test "$SCRIPT_DIR/test_place_dialog_integration.py" "Place Dialog Integration"
run_test "$SCRIPT_DIR/test_arc_dialog_integration.py" "Arc Dialog Integration"
run_test "$SCRIPT_DIR/test_transition_dialog_integration.py" "Transition Dialog Integration"

# Summary
echo ""
echo "========================================"
echo "TEST SUITE SUMMARY"
echo "========================================"
echo "Tests Passed: $TESTS_PASSED"
echo "Tests Failed: $TESTS_FAILED"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo "🎉 ALL TESTS PASSED!"
    exit 0
else
    echo "⚠ Some tests failed"
    exit 1
fi
