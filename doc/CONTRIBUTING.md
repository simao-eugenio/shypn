```markdown
# Contributing to SHYpn

Thank you for considering contributing to this project! To keep the codebase organized and maintainable, please follow these guidelines:

## Development Environment
This project uses GTK 3.22+ with Python 3.8+. The codebase is production-ready and follows modern Python OOP practices.

### Setting Up
1. Fork the repository
2. Clone your fork
3. Set up virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
4. Install system dependencies (GTK, PyGObject)

## Code Quality Standards

### No Debug Print Statements
- **NEVER** add `print()` statements for debugging
- Use logging with proper levels if needed
- Only ERROR messages to `sys.stderr` are allowed for critical failures
- The codebase has been cleaned of all debug prints

### Code Style
- Follow PEP8 for Python code
- Use type hints where appropriate
- Write clear docstrings for all public methods
- Use meaningful variable names

### Object-Oriented Design
- Prefer classes over functions for core logic
- Use encapsulation and proper access control
- Follow SOLID principles
- Keep business logic separate from UI code

## Repository Structure
- **src/shypn/api/**: Business logic APIs (file operations, data access)
- **src/shypn/data/**: Data models and canvas managers
- **src/shypn/helpers/**: UI loaders and helper functions
- **src/shypn/ui/**: UI component classes
- **src/shypn/utils/**: Specialized utility routines
- **src/shypn/dev/**: Experimental or in-development code
- **ui/**: GTK UI definition files (.ui XML)
- **tests/**: All test files (consolidated location)
- **scripts/**: Utility scripts, demos (non-test code)
- **legacy/**: Old code for reference only (do not modify)

## Contribution Workflow

1. **Create a Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Your Changes**
   - Follow the structure guidelines above
   - Add tests for new functionality
   - Update documentation as needed

3. **Test Your Changes**
   ```bash
   # Compile check
   python3 -m py_compile src/shypn.py
   
   # Run tests
   python3 -m pytest tests/
   
   # Test the application
   python3 src/shypn.py
   ```

4. **Commit with Clear Messages**
   ```bash
   git commit -m "feat: Add zoom reset functionality"
   ```

5. **Submit Pull Request**
   - Describe what your changes do
   - Reference any related issues
   - Include screenshots for UI changes

## Testing Requirements
- Add unit tests for new business logic
- Add integration tests for UI components
- Ensure all existing tests pass
- Test manually in the actual application

## Documentation Requirements
- Update relevant README.md files
- Add docstrings to new classes and methods
- Update REFINEMENTS_LOG.md for significant changes
- Document any breaking changes

## UI Development Guidelines

### GTK UI Files
- UI definitions go in `ui/` directory
- Use Glade to edit .ui files when possible
- Follow existing naming conventions
- Keep UI logic separate from business logic

### Panel Development
- Left panel: File operations, project navigation
- Right panel: Analysis tools, properties
- Both panels must support dock/undock
- Test visibility toggles thoroughly

### Canvas Development
- Canvas logic goes in `src/shypn/data/model_canvas_manager.py`
- UI loading in `src/shypn/helpers/model_canvas_loader.py`
- Support multiple documents with tabs
- Implement context menus for user actions

## Common Pitfalls to Avoid

❌ **Don't:**
- Add debug print statements
- Mix business logic with UI code
- Modify files in `legacy/` directory
- Commit commented-out code
- Use absolute paths (use os.path.join)
- Leave empty except blocks (use `pass` or handle properly)

✅ **Do:**
- Use proper error handling with informative messages
- Keep functions focused and single-purpose
- Write self-documenting code
- Test edge cases
- Update documentation

## Questions?

If you're unsure about any guideline:
1. Check existing code for examples
2. Review REFINEMENTS_LOG.md for recent patterns
3. Open an issue for discussion
4. Ask in pull request comments

Thank you for helping maintain a clean, professional codebase!

```
