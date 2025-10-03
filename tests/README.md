```markdown
# tests/

This directory contains all test scripts and test modules for the SHYpn project.

## Organization

Tests are organized to mirror the structure of the main codebase in `src/shypn/`:
- Unit tests for specific modules
- Integration tests for component interactions
- UI tests for GTK widgets and panels
- API tests for business logic

## Recent Changes (October 2, 2025)

### Test Consolidation
All test files have been consolidated into this directory from `scripts/`:
- `test_context_menu.py` - Context menu functionality tests
- `test_file_explorer.py` - File explorer panel tests
- `test_file_operations.py` - File operation API tests
- `test_gesture_simple.py` - GTK gesture tests
- `test_popover_methods.py` - Popover widget tests
- `test_relative_paths.py` - Path handling tests
- `test_right_click.py` - Right-click interaction tests

### Test Structure
```
tests/
├── README.md (this file)
├── scripts/          # Test utility scripts
├── test_*.py         # Individual test modules
└── fixtures/         # Test data and fixtures (if needed)
```

## Running Tests

### All Tests
```bash
python3 -m pytest tests/
```

### Specific Test File
```bash
python3 -m pytest tests/test_file_explorer.py
```

### With Coverage
```bash
python3 -m pytest --cov=src/shypn tests/
```

### Verbose Output
```bash
python3 -m pytest -v tests/
```

## Writing Tests

### Guidelines
1. **Naming**: Test files must start with `test_`
2. **Structure**: Mirror the source code structure
3. **Coverage**: Aim for high code coverage
4. **Isolation**: Tests should be independent
5. **Clean Code**: No debug prints, use assertions

### Example Test Structure
```python
import pytest
from shypn.api.file.explorer import FileExplorer

class TestFileExplorer:
    def setup_method(self):
        """Set up test fixtures."""
        self.explorer = FileExplorer()
    
    def test_navigation(self):
        """Test directory navigation."""
        result = self.explorer.navigate_to("/tmp")
        assert result == True
    
    def teardown_method(self):
        """Clean up after tests."""
        pass
```

### GTK Testing
For GTK-related tests:
- Use GTK test utilities
- Mock UI interactions when possible
- Test business logic separately from UI
- Ensure X server or Wayland is available

## Test Requirements

### Dependencies
```bash
pip install pytest pytest-cov pytest-gtk
```

### System Requirements
- Python 3.8+
- GTK 3.22+
- PyGObject
- Display server (for UI tests)

## CI/CD Integration

Tests are run automatically on:
- Pull requests
- Commits to main branches
- Tagged releases

Ensure all tests pass before submitting pull requests.

## Troubleshooting

### No Display Server
If running tests in headless environment:
```bash
xvfb-run python3 -m pytest tests/
```

### Import Errors
Ensure the project root is in PYTHONPATH:
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
```

### GTK Warnings
Some GTK warnings are normal during testing. Focus on test failures and errors.

```