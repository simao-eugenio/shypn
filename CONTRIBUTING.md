# Contributing to SHYPN

Thank you for your interest in contributing to SHYPN! This document provides guidelines for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Architecture Protection Zones](#architecture-protection-zones)
- [Development Workflow](#development-workflow)
- [Code Quality Standards](#code-quality-standards)
- [Testing Requirements](#testing-requirements)
- [Pull Request Process](#pull-request-process)

## Code of Conduct

Please be respectful and constructive in all interactions with the community.

## Getting Started

1. **Fork and clone the repository**:
   ```bash
   git clone https://github.com/simao-eugenio/shypn.git
   cd shypn
   ```

2. **Set up development environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -e ".[dev]"
   ```

3. **Install pre-commit hooks**:
   ```bash
   pip install pre-commit
   pre-commit install
   ```

4. **Read architecture documentation** (REQUIRED before contributing):
   - `ARCHITECTURE_ENHANCEMENTS_RECON.md` - Understand the A+ architecture
   - `QUALITY_ACTION_PLAN_REVISED.md` - Quality improvement guidelines

## Architecture Protection Zones

⚠️ **CRITICAL: DO NOT TOUCH WITHOUT ARCHITECTURE REVIEW**

SHYPN has world-class architecture (A+ grade) with 26/26 architecture tests passing. The following files implement core architectural patterns and must NOT be refactored without explicit architectural review:

### Protected Files (❌ DO NOT REFACTOR)

#### EventBus System
- **`src/shypn/events/event_bus.py`** (327 lines)
  - Document-scoped publish-subscribe system
  - Tested: 12/12 unit tests passing
  - Achievement: -71% code reduction in panel coordination
  - Complexity is INTENTIONAL: Document filtering, wildcard support, priority ordering

#### Per-Document Panel Architecture
- **`src/shypn/helpers/base_panel_loader.py`** (638 lines)
  - Abstract base class for per-document panels
  - Template Method + Strategy patterns
  - 5 implementations (Pathway, Analyses, Topology, Viability, Report)
  - Complexity is INTENTIONAL: Complete lifecycle management

- **`src/shypn/helpers/pathway_panel_loader.py`**
- **`src/shypn/helpers/analyses_panel_loader.py`**
- **`src/shypn/helpers/topology_panel_loader.py`**
- **`src/shypn/helpers/viability_panel_loader.py`**
- **`src/shypn/helpers/report_panel_loader.py`**
  - Per-document panel implementations
  - Each maintains independent state for its document
  - EventBus integration for coordination

#### MDI Orchestration
- **`src/shypn/helpers/model_canvas_loader.py`**
  - Multi-document interface initialization hub
  - Creates 5 per-document panel instances
  - Sets up EventBus subscriptions
  - Complexity 70 is INTENTIONAL: Coordinate 5 panels + controllers
  - Function `_setup_edit_palettes()` is an architectural hub, NOT technical debt

#### Data Model
- **`src/shypn/data/canvas/document_model.py`**
  - Per-document data model with isolated IDManager
  - Tested: 8/8 architecture tests passing

- **`src/shypn/data/canvas/id_manager.py`**
  - Per-document ID sequence management (P1, T1, A1 per document)
  - Lifecycle event emission

### Why These Files Are Protected

1. **They implement proven architecture**: 26/26 tests passing, zero multi-document bugs
2. **High complexity is intentional**: Coordination logic, not spaghetti code
3. **Refactoring risks breaking isolation**: Changes could cause cross-document contamination
4. **Already optimized**: -71% code reduction achieved through EventBus

### Safe Refactoring Zones (✅ OK to Improve)

These areas can be refactored without architectural risk:

#### Simulation Algorithms
- ✅ `src/shypn/engine/` - Simulation core (not architecture-dependent)
- ✅ `src/shypn/engine/continuous_behavior.py` - ODE solvers
- ✅ `src/shypn/engine/stochastic_behavior.py` - SSA algorithms

#### Domain Logic
- ✅ `src/shypn/thermodynamics/` - Thermodynamic calculations (isolated)
- ✅ `src/shypn/crossfetch/` - External API integration (KEGG, BRENDA, etc.)

#### Import/Export
- ✅ `src/shypn/export/` - Export functionality
- ✅ `src/shypn/import/` - Import functionality

#### UI Components (Non-Architectural)
- ✅ `src/shypn/ui/panels/*` - Panel UI components (not loaders)
- ✅ Property dialogs (validation logic)

## Development Workflow

### Before Making Changes

1. **Check if files are in protection zones** (see above)
2. **If in protection zone**: Request architecture review first
3. **If in safe zone**: Proceed with normal development

### Making Changes

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following code quality standards

3. **Run tests** (REQUIRED):
   ```bash
   # Unit tests
   pytest tests/ -v
   
   # Architecture tests (CRITICAL - must pass)
   pytest tests/test_multi_document_isolation.py -v
   pytest tests/test_eventbus_document_scoping.py -v
   
   # If 26/26 architecture tests don't pass, STOP and investigate
   ```

4. **Run quality checks**:
   ```bash
   # Pre-commit hooks
   pre-commit run --all-files
   
   # Linting (excludes architecture zones)
   pylint src/shypn/
   flake8 src/shypn/
   
   # Type checking (safe zones only)
   mypy src/shypn/
   ```

## Code Quality Standards

### Style Guidelines

- **Line length**: 120 characters (consistent with Black)
- **Formatting**: Use Black for code formatting
- **Imports**: Use isort for import sorting
- **Naming**: Snake_case for functions/variables, PascalCase for classes

### Type Hints

- **Target**: 80% coverage in safe zones
- **Focus areas**: Engine, thermodynamics, import/export
- **Architecture zones**: Already well-typed, avoid changes

### Documentation

- **All public classes**: Must have docstrings
- **All public methods**: Must have docstrings
- **Complex logic**: Add inline comments explaining WHY, not WHAT

### Complexity Limits

- **Target**: Cyclomatic complexity < 15
- **Architecture zones**: EXEMPT (complexity is intentional)
- **Safe zones**: Refactor if > 20

## Testing Requirements

### Architecture Tests (CRITICAL)

**These tests MUST pass before merging any PR**:

```bash
# Run architecture test suite
pytest tests/test_multi_document_isolation.py -v       # 5 tests
pytest tests/test_eventbus_document_scoping.py -v      # 12 tests
pytest tests/test_architecture_validation.py -v        # 26 tests (if exists)

# Expected result: 43+ tests passing
```

If ANY architecture test fails:
1. ❌ **STOP** immediately
2. ❌ **REVERT** your changes
3. ⚠️ **Request architecture review** before proceeding

### Unit Tests

- Add tests for new features in safe zones
- Maintain test coverage > 80%
- Use real EventBus in tests (don't mock architecture)
- Use real per-document panels (don't mock architecture)

### Test Structure

```python
# Good test (uses real architecture)
def test_simulation_algorithm():
    model = create_test_model()
    controller = SimulationController(model)
    controller.run()
    assert controller.time > 0

# Bad test (mocks architecture)
def test_with_mock_eventbus():
    with patch('shypn.events.EventBus'):  # ❌ Don't mock architecture
        # ... test code ...
```

## Pull Request Process

### Before Submitting

1. ✅ All tests pass (including 26+ architecture tests)
2. ✅ Pre-commit hooks pass
3. ✅ No changes to protected files (unless approved)
4. ✅ Documentation updated (if needed)
5. ✅ CHANGELOG.md updated (for user-facing changes)

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix (non-breaking change)
- [ ] New feature (non-breaking change)
- [ ] Breaking change
- [ ] Architecture change (requires review)

## Testing
- [ ] All architecture tests pass (26+)
- [ ] Unit tests added/updated
- [ ] Manual testing completed

## Architecture Impact
- [ ] No architecture files touched (safe zone only)
- [ ] Architecture files modified (review required)
- [ ] Architecture tests still pass: [YES/NO]

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-reviewed the code
- [ ] Commented complex logic
- [ ] Documentation updated
- [ ] No breaking changes to existing APIs
```

### Review Criteria

PRs will be reviewed for:
1. **Architecture safety**: No unintended changes to protected zones
2. **Test coverage**: New code has tests
3. **Code quality**: Follows standards, readable
4. **Documentation**: Clear and complete

## Security

### Reporting Security Issues

Please report security vulnerabilities to the maintainers directly, not in public issues.

### Known Security Work

The following security issues are being addressed (see QUALITY_ACTION_PLAN_REVISED.md):
- 18 `eval()` calls (tracked for replacement)
- Exception handling improvements

## Getting Help

- **Architecture questions**: Read `ARCHITECTURE_ENHANCEMENTS_RECON.md`
- **Quality questions**: Read `QUALITY_ACTION_PLAN_REVISED.md`
- **Bug reports**: Create GitHub issue
- **Feature requests**: Create GitHub issue with [Feature Request] tag

## License

By contributing, you agree that your contributions will be licensed under the project's license.

---

**Thank you for contributing to SHYPN!** 🚀

Your respect for the architecture ensures we maintain the A+ quality that makes this project special.
