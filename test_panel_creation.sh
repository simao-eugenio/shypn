#!/bin/bash
# Test if _setup_plotting_panels() is called when creating a model

echo "========================================================================"
echo "Testing Analyses Panel Creation"
echo "========================================================================"
echo ""
echo "This will:"
echo "  1. Start the app in background"
echo "  2. Look for debug messages in output"
echo "  3. Report if _setup_plotting_panels() was called"
echo ""
echo "Press Ctrl+C after you've done 'File → New'"
echo ""

# Clear old log
rm -f /tmp/shypn_output.log

# Start app with output to log
python3 src/shypn.py 2>&1 | tee /tmp/shypn_output.log &
APP_PID=$!

echo "App started (PID: $APP_PID)"
echo "Waiting for you to click File → New..."
echo ""
echo "After you create a model, press Ctrl+C here to check results"
echo ""

# Wait for user to interrupt
trap "echo ''; echo 'Checking results...'; kill $APP_PID 2>/dev/null; sleep 1" INT

wait $APP_PID 2>/dev/null

echo ""
echo "========================================================================"
echo "RESULTS"
echo "========================================================================"
echo ""

# Check for our debug message
if grep -q "RIGHT_PANEL.*_setup_plotting_panels" /tmp/shypn_output.log; then
    echo "✅ SUCCESS: _setup_plotting_panels() WAS called!"
    echo ""
    echo "Messages found:"
    grep "RIGHT_PANEL" /tmp/shypn_output.log
    echo ""
    echo "This means the panels SHOULD have been created."
    echo "If you don't see them in the UI, there may be a visibility issue."
else
    echo "❌ PROBLEM: _setup_plotting_panels() was NOT called"
    echo ""
    echo "This means either:"
    echo "  1. You didn't click File → New to create a model"
    echo "  2. The wiring code in _setup_edit_palettes() didn't run"
    echo "  3. set_data_collector() wasn't called"
    echo ""
    echo "Checking for other clues in the output..."
    echo ""
    if grep -q "add_document" /tmp/shypn_output.log; then
        echo "Found 'add_document' - model creation was attempted"
    fi
    if grep -q "_setup_edit_palettes" /tmp/shypn_output.log; then
        echo "Found '_setup_edit_palettes' - palette setup ran"
    fi
fi

echo ""
echo "Full log saved to: /tmp/shypn_output.log"
echo "You can view it with: cat /tmp/shypn_output.log"
echo ""
