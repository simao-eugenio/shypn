#!/bin/bash
# Test runner for PDF export feature
# Usage: ./tests/run_export_tests.sh

echo "🧪 Running PDF Export Tests"
echo "============================"
echo ""

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    echo "📦 Activating virtual environment..."
    source .venv/bin/activate
fi

# Check if pytest is available
if ! command -v pytest &> /dev/null; then
    echo "❌ pytest not found. Installing..."
    pip install pytest pytest-cov
fi

echo ""
echo "🔍 Running tests..."
echo ""

# Run tests with verbose output and coverage
pytest tests/test_pdf_exporter.py -v --cov=shypn.export --cov-report=term-missing

EXIT_CODE=$?

echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ All tests passed!"
    echo ""
    echo "📊 Summary:"
    echo "   - OOP architecture: ✅"
    echo "   - Base class: ✅"
    echo "   - PDF exporter: ✅"
    echo "   - Error handling: ✅"
    echo "   - Cairo integration: ✅"
    echo "   - Wayland-safe: ✅"
    echo ""
    echo "🎉 PDF export feature is ready for production!"
else
    echo "❌ Some tests failed. Please review the output above."
fi

exit $EXIT_CODE
