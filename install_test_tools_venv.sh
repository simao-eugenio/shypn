#!/bin/bash
# Install pytest and testing tools using virtual environment (recommended)

set -e  # Exit on error

echo "=================================================="
echo "  Installing pytest Tools (Virtual Environment)"
echo "=================================================="
echo ""

VENV_DIR="venv"

# Check if virtual environment already exists
if [ -d "$VENV_DIR" ]; then
    echo "✓ Virtual environment '$VENV_DIR' already exists"
    echo ""
else
    echo "📦 Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
    echo "✓ Virtual environment created"
    echo ""
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip

echo ""
echo "📦 Installing testing packages from requirements-test.txt..."
echo ""
pip install -r requirements-test.txt

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
if python -c "import pytest_cov" 2>/dev/null; then
    VERSION=$(python -c "import pytest_cov; print(pytest_cov.__version__)" 2>/dev/null || echo "unknown")
    echo "✓ pytest-cov:        $VERSION"
else
    echo "❌ pytest-cov:       NOT FOUND"
fi

# Check pytest-benchmark
if python -c "import pytest_benchmark" 2>/dev/null; then
    VERSION=$(python -c "import pytest_benchmark; print(pytest_benchmark.__version__)" 2>/dev/null || echo "unknown")
    echo "✓ pytest-benchmark:  $VERSION"
else
    echo "❌ pytest-benchmark: NOT FOUND"
fi

# Check pytest-html
if python -c "import pytest_html" 2>/dev/null; then
    VERSION=$(python -c "import pytest_html; print(pytest_html.__version__)" 2>/dev/null || echo "unknown")
    echo "✓ pytest-html:       $VERSION"
else
    echo "❌ pytest-html:      NOT FOUND"
fi

# Check pytest-timeout
if python -c "import pytest_timeout" 2>/dev/null; then
    VERSION=$(python -c "import pytest_timeout; print(pytest_timeout.__version__)" 2>/dev/null || echo "unknown")
    echo "✓ pytest-timeout:    $VERSION"
else
    echo "❌ pytest-timeout:   NOT FOUND"
fi

echo ""
echo "=================================================="
echo "  🎯 How to Use:"
echo "=================================================="
echo ""
echo "1. ACTIVATE the virtual environment first:"
echo "   source venv/bin/activate"
echo ""
echo "2. Then run tests:"
echo "   cd tests/validation/immediate"
echo "   pytest test_basic_firing.py -v"
echo ""
echo "3. Run with coverage:"
echo "   pytest test_basic_firing.py --cov=shypn"
echo ""
echo "4. Generate HTML report:"
echo "   pytest test_basic_firing.py --html=report.html"
echo ""
echo "5. DEACTIVATE when done:"
echo "   deactivate"
echo ""
echo "=================================================="
echo ""
echo "✨ Virtual environment path: $(pwd)/$VENV_DIR"
echo ""
echo "To activate anytime: source $VENV_DIR/bin/activate"
echo ""
