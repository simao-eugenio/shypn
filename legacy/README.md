# Legacy Code

This directory contains the old version of the codebase. Relevant code will be reviewed, refactored, and migrated into the new object-oriented structure as needed. Do not modify legacy code directly unless extracting or adapting it for the new architecture.

## Migration Workflow
1. Identify useful modules/classes/functions in `legacy/`.
2. Refactor and adapt them to fit the new OOP structure in `src/shypn/`.
3. Add or update tests in `tests/` as code is migrated.
4. Remove legacy code only after successful migration and validation.
