# Historical Test Shell Scripts

This directory contains historical test and debug shell scripts that were used during development but are no longer needed for regular testing.

## Archive Date

**Moved to archive:** October 22, 2025

## Scripts

### test_button_debug.sh
Debug script for Master Palette buttons.
- **Purpose**: Diagnosed button click issues in Master Palette system
- **Status**: Historical - Master Palette now working correctly
- **Related**: Master Palette refactoring (October 2025)

### test_buttons_interactive.sh
Interactive test for Master Palette buttons.
- **Purpose**: Manual testing of Master Palette button interactions
- **Status**: Historical - Automated tests now available in tests/
- **Related**: Master Palette integration tests

### test_manual.sh
Manual test instructions for property dialogs.
- **Purpose**: Guided manual testing of property dialogs with real models
- **Status**: Historical - Automated tests now available in tests/prop_dialogs/
- **Related**: Property dialog integration (December 2024)

### test_manual_dialog_fix.sh
Manual test for dialog freeze fix verification.
- **Purpose**: Verified dialog freeze fix with Glycolysis model
- **Status**: Historical - Dialog fixes validated and stable
- **Related**: Dialog performance optimization (December 2024)

## Why Archived

These scripts were valuable during development but are now superseded by:

1. **Automated Tests**: All functionality covered by automated tests in `tests/`
   - `tests/test_exclusive_master_palette.py` - Master Palette exclusive button logic
   - `tests/test_master_palette_integration.py` - Master Palette integration
   - `tests/test_dialog_speed.py` - Dialog performance tests
   - `tests/prop_dialogs/` - Complete property dialog test suite (34 tests)

2. **Stable Features**: The features these scripts tested are now stable and production-ready
   - Master Palette system working correctly
   - Property dialogs opening instantly
   - All panels supporting float/attach

3. **Better Testing Infrastructure**: Modern testing approach with pytest and headless execution
   - `tests/prop_dialogs/run_all_tests.sh` - Automated test runner
   - `scripts/run_headless_tests.py` - Headless test execution

## Current Testing

For current testing, use:

```bash
# Master Palette tests
python3 tests/test_exclusive_master_palette.py
python3 tests/test_master_palette_integration.py

# Dialog tests
python3 tests/test_dialog_speed.py
cd tests/prop_dialogs && ./run_all_tests.sh

# All tests
python3 -m pytest tests/
```

## Historical Context

These scripts were created during:
- **Master Palette Development** (October 2025): Button interaction debugging
- **Dialog Optimization** (December 2024): Performance testing with imported models

They served their purpose and helped validate the fixes but are no longer needed for regular development or testing.

## Notes

⚠️ **DO NOT USE** - These scripts are for historical reference only and may not work with the current codebase.

If you need to understand the historical development process or debugging approaches, these scripts provide valuable insight into the challenges faced and solutions tested.
