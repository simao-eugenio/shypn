#!/bin/bash
# Install pytest and testing tools for SHYpn project

set -e  # Exit on error

echo "=================================================="
echo "  Installing pytest Testing Tools for SHYpn"
echo "=================================================="
echo ""

# Check if pip is available
if ! command -v pip3 &> /dev/null; then
    echo "❌ Error: pip3 not found. Please install it first:"
    echo "   sudo apt-get install python3-pip"
    exit 1
fi

echo "✓ pip3 found"
echo ""

# Install from requirements-test.txt
echo "📦 Installing testing packages..."
echo ""

pip3 install -r requirements-test.txt

echo ""
echo "=================================================="
echo "  ✅ Installation Complete!"
echo "=================================================="
echo ""

# Verify installations
echo "Verifying installations:"
echo ""

# Check pytest
if pytest --version &> /dev/null; then
    echo "✓ pytest:            $(pytest --version | grep pytest)"
else
    echo "❌ pytest:           NOT FOUND"
fi

# Check pytest-cov
if python3 -c "import pytest_cov" 2>/dev/null; then
    VERSION=$(python3 -c "import pytest_cov; print(pytest_cov.__version__)" 2>/dev/null || echo "unknown")
    echo "✓ pytest-cov:        $VERSION"
else
    echo "❌ pytest-cov:       NOT FOUND"
fi

# Check pytest-benchmark
if python3 -c "import pytest_benchmark" 2>/dev/null; then
    VERSION=$(python3 -c "import pytest_benchmark; print(pytest_benchmark.__version__)" 2>/dev/null || echo "unknown")
    echo "✓ pytest-benchmark:  $VERSION"
else
    echo "❌ pytest-benchmark: NOT FOUND"
fi

# Check pytest-html
if python3 -c "import pytest_html" 2>/dev/null; then
    VERSION=$(python3 -c "import pytest_html; print(pytest_html.__version__)" 2>/dev/null || echo "unknown")
    echo "✓ pytest-html:       $VERSION"
else
    echo "❌ pytest-html:      NOT FOUND"
fi

# Check pytest-timeout
if python3 -c "import pytest_timeout" 2>/dev/null; then
    VERSION=$(python3 -c "import pytest_timeout; print(pytest_timeout.__version__)" 2>/dev/null || echo "unknown")
    echo "✓ pytest-timeout:    $VERSION"
else
    echo "❌ pytest-timeout:   NOT FOUND"
fi

echo ""
echo "=================================================="
echo "  Next Steps:"
echo "=================================================="
echo ""
echo "1. Run existing tests:"
echo "   cd tests/validation/immediate"
echo "   pytest test_basic_firing.py -v"
echo ""
echo "2. Run with coverage:"
echo "   pytest test_basic_firing.py --cov=shypn"
echo ""
echo "3. Generate HTML report:"
echo "   pytest test_basic_firing.py --html=report.html"
echo ""
echo "4. Run benchmarks:"
echo "   cd tests/benchmark/immediate"
echo "   pytest bench_basic_firing.py --benchmark-only"
echo ""
echo "Happy testing! 🎉"
echo ""
