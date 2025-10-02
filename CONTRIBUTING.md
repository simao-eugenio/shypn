# Contributing to shypn

Thank you for considering contributing to this project! To keep the codebase organized and maintainable, please follow these guidelines:

## GTK 4 Migration
This project is incrementally migrating from GTK 3.2+ to GTK 4. When contributing to UI or GTK-related code, please:
- Prefer GTK 4 APIs and widgets for all new or refactored code.
- Update legacy GTK 3 code to GTK 4 when possible.
- Test UI changes thoroughly to ensure compatibility and correct behavior.
If you are unsure how to migrate a component, consult the official GTK 3→4 migration guide or open an issue for discussion.

## Repository Structure
- **src/shypn/api/**: Main object-oriented API classes and interfaces.
- **src/shypn/helpers/**: Functional helper functions.
- **src/shypn/utils/**: Specialized utility routines.
- **src/shypn/dev/**: Experimental or in-development code.
- **data/**: Data models, schemas, or sample data.
- **ui/**: User interface components, organized by type.
- **legacy/**: Old code for reference and migration only.
- **tests/**: All tests, organized to mirror the source structure.
	- **tests/scripts/**: General-purpose scripts and utilities that do not belong to the core source code.

## Contribution Rules
- Place new features, classes, or modules in the correct directory as described above.
- Use object-oriented design for all new core modules.
- Add or update tests for any new code.
- Document new modules and functions with clear docstrings.
- Update the relevant README.md if you add a new folder or major feature.

## Workflow
1. Fork the repository and create a new branch for your feature or fix.
2. Make your changes, following the structure and style guidelines.
3. Run tests to ensure nothing is broken.
4. Submit a pull request with a clear description of your changes.

## Code Style
- Follow PEP8 for Python code.
- Use meaningful names and clear comments.

Thank you for helping keep this project clean and maintainable!
