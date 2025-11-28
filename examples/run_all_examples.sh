#!/bin/bash
# Run all SHYpn examples sequentially

echo "╔══════════════════════════════════════════════════════════╗"
echo "║          SHYpn Examples - Batch Execution               ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# Change to examples directory
cd "$(dirname "$0")"

# Counter for completed examples
completed=0
total=4

# Run each example
for example in 01_*.py 02_*.py 03_*.py 04_*.py; do
    if [ -f "$example" ]; then
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "▶ Running: $example"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        python "$example"
        
        if [ $? -eq 0 ]; then
            completed=$((completed + 1))
            echo "✓ $example completed successfully"
        else
            echo "✗ $example failed with exit code $?"
        fi
        echo ""
    fi
done

# Summary
echo "╔══════════════════════════════════════════════════════════╗"
echo "║                  Execution Summary                       ║"
echo "╠══════════════════════════════════════════════════════════╣"
echo "║  Completed: $completed / $total examples                        ║"
echo "╚══════════════════════════════════════════════════════════╝"

if [ $completed -eq $total ]; then
    echo ""
    echo "✓ All examples executed successfully!"
    echo ""
    echo "Generated plots:"
    ls -lh *.pdf 2>/dev/null | awk '{print "  - " $9 " (" $5 ")"}'
    exit 0
else
    echo ""
    echo "⚠ Some examples failed. Check output above for details."
    exit 1
fi
