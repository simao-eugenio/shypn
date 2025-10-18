# Timed Transition Validation Tests

**Purpose:** Fast functional correctness tests for timed transitions.

**Status:** 🔜 **PLANNED** - Phase 2

## Overview

Timed transitions fire after a specified delay/timeout. Validation tests will verify:

1. **Delay Mechanism** - Fixed delays work correctly
2. **Guard Functions** - Guards evaluated with delays
3. **Priority Resolution** - Conflicts with delays
4. **Arc Weights** - Token flow with delays
5. **Source/Sink** - Timed special behaviors
6. **Persistence** - Properties persist correctly
7. **Edge Cases** - Boundary conditions

## Coming Soon

Tests will be developed after immediate transition validation is complete.

## Related Documentation

- `/doc/validation/timed/` - (To be created in Phase 2)
- `/doc/validation/immediate/` - Reference implementation
