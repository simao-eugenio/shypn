```markdown
# tests/

This directory contains all test scripts and test modules for the SHYpn project. **104+ test files** covering various aspects of the application.

## Organization

Tests are organized by functionality:
- **Arc tests**: Arc transformations, hit detection, boundary calculations
- **KEGG tests**: Pathway import, relation conversion, rendering
- **Workspace tests**: Isolation, state persistence
- **Feature tests**: Filtering, compound handling, layout algorithms
- **Check scripts**: Validation scripts for specific features

## Recent Changes (October 2025)

### Test Consolidation
All test files consolidated from repository root into this directory:
- 18 `.py` test files moved from root
- 1 `.sh` test script moved from root
- Organized into logical groupings

### Test Categories

#### Arc System Tests
- `test_arc_types.py` - All arc type transformations
- `test_arc_transformation.py` - Arc geometry transformations
- `test_arc_hit_detection.py` - Arc selection and hit detection
- `test_long_arc_hit_detection.py` - Long arc click detection
- `test_curved_arc_handle_position.py` - Curved arc control points
- `test_all_arc_types_transformation.py` - Comprehensive arc testing
- `check_arc_endpoints.py` - Arc endpoint validation

#### KEGG Import Tests
- `test_real_kegg_pathways.py` - Real KEGG pathway import
- `test_phase0_relations_analysis.py` - Relation analysis
- `test_phase0_rendering_search.py` - Rendering verification
- `check_kegg_relations.py` - Relations validation
- `check_kegg_relations_rendering.py` - Relations rendering check
- `check_relation_conversion.py` - Conversion validation
- `check_pathway_structure.py` - Pathway structure check
- `check_specific_chain.py` - Chain validation
- `check_specific_compounds.py` - Compound validation

#### Feature Tests
- `test_enhanced_filtering.py` - Enhanced filtering features
- `test_filtering_option.py` - Filter options
- `test_isolated_compounds.py` - Isolated compound handling
- `test_isolated_filtering.py` - Isolated node filtering
- `test_with_enhancements.py` - Enhancement pipeline

#### Source/Sink Tests
- `test_source_sink.py` - Source/sink place types
- `test_timed_source.py` - Timed source places
- `test_timed_sink.py` - Timed sink places

#### Transformation Handler Tests
- `test_transformation_handlers.py` - Arc transformation handlers

#### Workspace Tests
- `test_workspace_isolation.sh` - Workspace isolation validation

#### Check Scripts
- `check_old_converter.py` - Legacy converter validation
- `check_transition_sizes.py` - Transition size validation

### Test Structure
```
tests/
├── README.md (this file)
├── scripts/          # Test utility scripts
├── test_*.py         # Individual test modules (100+)
├── check_*.py        # Validation scripts
└── *.sh              # Shell test scripts
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