# Version Synchronization & API Regression Prevention Plan

**Date**: January 6, 2026  
**Issue**: Code regression due to APIs not synced with tagged shypn versions  
**Status**: 📋 PLAN - Ready for Implementation

---

## Problem Analysis

### Current State
- **Main version**: `2.5.4` (in `pyproject.toml` and `src/shypn/__init__.py`)
- **CITATION.cff version**: `2.4.6` (OUTDATED)
- **Last git tag**: `v2.5.4`
- **Submodule versions**:
  - `src/shypn/engine/__init__.py`: `1.0.0`
  - `src/shypn/crossfetch/__init__.py`: `1.0.0`
  - `src/shypn/crossfetch/metadata/__init__.py`: `1.0.0`

### Issues Identified
1. **Version Drift**: CITATION.cff is 2 minor versions behind (2.4.6 vs 2.5.4)
2. **No Submodule Versioning**: Engine and crossfetch use static `1.0.0`
3. **No API Compatibility Checks**: No runtime verification of compatible versions
4. **No Deprecation System**: Changes marked in code but no programmatic tracking
5. **No Version Validation**: Dependencies can import mismatched API versions

---

## Root Causes

### 1. Multiple Version Sources (Single Source of Truth Missing)
```
pyproject.toml:         version = "2.5.4"
src/shypn/__init__.py:  __version__ = "2.5.4"
CITATION.cff:           version: 2.4.6        ← DRIFT!
git tags:               v2.5.4               ✓ OK
```

### 2. Submodule Independence
- `engine` and `crossfetch` have independent `__version__`
- No compatibility matrix between main and submodules
- Breaking changes in submodules not tracked

### 3. No API Contract System
- Public APIs not explicitly declared
- No semantic versioning enforcement
- No compatibility layer for API changes

---

## Solution: 5-Layer Version Management System

### Layer 1: Single Source of Truth ✓ **Highest Priority**

**Goal**: One canonical version file that propagates to all others

**Implementation**:
```python
# src/shypn/version.py (NEW FILE)
"""Canonical version source for SHYpn.

This is the ONLY place where version numbers should be manually updated.
All other files (pyproject.toml, __init__.py, CITATION.cff) are generated
from this source.
"""

# Main package version (Semantic Versioning: MAJOR.MINOR.PATCH)
__version__ = "2.5.4"
__version_name__ = "Pulsating Singularity Dynamics"
__version_date__ = "2025-10-17"

# API version (changes only when public API breaks)
__api_version__ = "2.5"  # MAJOR.MINOR (no PATCH)

# Submodule compatibility (min required versions)
__required_engine_version__ = "1.0.0"
__required_crossfetch_version__ = "1.0.0"

# Version info for tools
def get_version_info():
    """Get complete version information."""
    return {
        'version': __version__,
        'name': __version_name__,
        'date': __version_date__,
        'api_version': __api_version__,
        'engine_version': __required_engine_version__,
        'crossfetch_version': __required_crossfetch_version__,
    }
```

**Auto-sync script**:
```bash
#!/bin/bash
# scripts/sync_versions.sh
# Auto-sync version from version.py to all files

VERSION=$(python -c "from src.shypn.version import __version__; print(__version__)")
VERSION_DATE=$(python -c "from src.shypn.version import __version_date__; print(__version_date__)")

# Update pyproject.toml
sed -i "s/^version = .*/version = \"$VERSION\"/" pyproject.toml

# Update CITATION.cff
sed -i "s/^version: .*/version: $VERSION/" CITATION.cff
sed -i "s/^date-released: .*/date-released: $VERSION_DATE/" CITATION.cff

# Verify __init__.py imports from version.py
echo "✓ Versions synced to $VERSION"
```

---

### Layer 2: API Compatibility Checks ✓ **High Priority**

**Goal**: Runtime verification that loaded modules are compatible

**Implementation**:
```python
# src/shypn/compatibility.py (NEW FILE)
"""API compatibility verification system."""

from typing import Tuple, List, Optional
import logging

logger = logging.getLogger(__name__)


class CompatibilityError(Exception):
    """Raised when incompatible versions are detected."""
    pass


def parse_version(version_str: str) -> Tuple[int, int, int]:
    """Parse semantic version string."""
    parts = version_str.split('.')
    return (int(parts[0]), int(parts[1]), int(parts[2]) if len(parts) > 2 else 0)


def check_compatibility(
    module_name: str,
    actual_version: str,
    required_version: str,
    strict: bool = False
) -> bool:
    """Check if module version is compatible.
    
    Args:
        module_name: Name of the module being checked
        actual_version: Version of loaded module
        required_version: Required version
        strict: If True, MAJOR and MINOR must match exactly
    
    Returns:
        True if compatible
        
    Raises:
        CompatibilityError: If incompatible (when strict=True)
    """
    actual = parse_version(actual_version)
    required = parse_version(required_version)
    
    # Semantic versioning rules:
    # - MAJOR version: Breaking API changes
    # - MINOR version: Backward-compatible additions
    # - PATCH version: Backward-compatible fixes
    
    if strict:
        # Strict mode: MAJOR.MINOR must match exactly
        compatible = (actual[0] == required[0] and actual[1] == required[1])
    else:
        # Lenient mode: MAJOR must match, MINOR >= required
        compatible = (actual[0] == required[0] and actual[1] >= required[1])
    
    if not compatible:
        msg = (f"{module_name} version {actual_version} is incompatible "
               f"with required version {required_version}")
        if strict:
            raise CompatibilityError(msg)
        else:
            logger.warning(msg)
    
    return compatible


def verify_submodule_versions() -> List[str]:
    """Verify all submodule versions are compatible.
    
    Returns:
        List of warning messages (empty if all compatible)
    """
    from shypn.version import (
        __version__,
        __required_engine_version__,
        __required_crossfetch_version__
    )
    
    warnings = []
    
    # Check engine version
    try:
        from shypn.engine import __version__ as engine_version
        check_compatibility('shypn.engine', engine_version, __required_engine_version__)
    except CompatibilityError as e:
        warnings.append(str(e))
    except ImportError:
        warnings.append("shypn.engine not found (optional module)")
    
    # Check crossfetch version
    try:
        from shypn.crossfetch import __version__ as crossfetch_version
        check_compatibility('shypn.crossfetch', crossfetch_version, __required_crossfetch_version__)
    except CompatibilityError as e:
        warnings.append(str(e))
    except ImportError:
        warnings.append("shypn.crossfetch not found (optional module)")
    
    return warnings


def verify_on_import():
    """Run compatibility checks when shypn is imported."""
    warnings = verify_submodule_versions()
    if warnings:
        logger.warning("Version compatibility issues detected:")
        for warning in warnings:
            logger.warning(f"  - {warning}")
```

**Auto-run on import**:
```python
# src/shypn/__init__.py (UPDATE)
from shypn.version import __version__, __version_name__, __version_date__

# Auto-verify compatibility on import
from shypn.compatibility import verify_on_import
verify_on_import()
```

---

### Layer 3: Deprecation System ✓ **Medium Priority**

**Goal**: Programmatic tracking of deprecated APIs with warnings

**Implementation**:
```python
# src/shypn/deprecation.py (NEW FILE)
"""Deprecation tracking and warning system."""

import warnings
import functools
from typing import Optional, Callable


class DeprecationRegistry:
    """Central registry for deprecated APIs."""
    
    def __init__(self):
        self.deprecated_apis = {}
    
    def register(
        self,
        api_name: str,
        deprecated_in: str,
        removed_in: str,
        replacement: Optional[str] = None,
        reason: Optional[str] = None
    ):
        """Register a deprecated API."""
        self.deprecated_apis[api_name] = {
            'deprecated_in': deprecated_in,
            'removed_in': removed_in,
            'replacement': replacement,
            'reason': reason
        }
    
    def get_deprecation_message(self, api_name: str) -> str:
        """Get deprecation message for an API."""
        if api_name not in self.deprecated_apis:
            return ""
        
        info = self.deprecated_apis[api_name]
        msg = (f"{api_name} is deprecated since version {info['deprecated_in']} "
               f"and will be removed in version {info['removed_in']}.")
        
        if info['replacement']:
            msg += f" Use {info['replacement']} instead."
        
        if info['reason']:
            msg += f" Reason: {info['reason']}"
        
        return msg


# Global registry
_registry = DeprecationRegistry()


def deprecated(
    deprecated_in: str,
    removed_in: str,
    replacement: Optional[str] = None,
    reason: Optional[str] = None
):
    """Decorator to mark functions/methods as deprecated.
    
    Usage:
        @deprecated(
            deprecated_in="2.5.0",
            removed_in="3.0.0",
            replacement="new_function()",
            reason="Old implementation was inefficient"
        )
        def old_function():
            pass
    """
    def decorator(func: Callable) -> Callable:
        api_name = f"{func.__module__}.{func.__qualname__}"
        _registry.register(api_name, deprecated_in, removed_in, replacement, reason)
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            msg = _registry.get_deprecation_message(api_name)
            warnings.warn(msg, DeprecationWarning, stacklevel=2)
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator


# Example usage:
# from shypn.deprecation import deprecated
#
# @deprecated(
#     deprecated_in="2.5.0",
#     removed_in="3.0.0",
#     replacement="KEGGCategory.auto_resolve_names()",
#     reason="Name enrichment now handled by cross-reference database"
# )
# def _on_enrich_names_clicked(self, button):
#     pass
```

---

### Layer 4: Pre-commit Version Validation ✓ **Medium Priority**

**Goal**: Prevent commits with version drift

**Implementation**:
```bash
# .git/hooks/pre-commit (or use pre-commit framework)
#!/bin/bash
# Verify versions are in sync before committing

echo "Checking version synchronization..."

# Extract versions from key files
PYPROJECT_VER=$(grep '^version = ' pyproject.toml | cut -d'"' -f2)
INIT_VER=$(grep '^__version__ = ' src/shypn/__init__.py | cut -d'"' -f2)
CITATION_VER=$(grep '^version: ' CITATION.cff | awk '{print $2}')

# Check for drift
if [ "$PYPROJECT_VER" != "$INIT_VER" ] || [ "$PYPROJECT_VER" != "$CITATION_VER" ]; then
    echo "❌ VERSION DRIFT DETECTED!"
    echo "  pyproject.toml: $PYPROJECT_VER"
    echo "  __init__.py:    $INIT_VER"
    echo "  CITATION.cff:   $CITATION_VER"
    echo ""
    echo "Run: ./scripts/sync_versions.sh"
    exit 1
fi

echo "✓ Versions in sync ($PYPROJECT_VER)"
```

---

### Layer 5: CI/CD Version Checks ✓ **Low Priority**

**Goal**: Automated verification in GitHub Actions

**Implementation**:
```yaml
# .github/workflows/version-check.yml (NEW FILE)
name: Version Synchronization Check

on: [push, pull_request]

jobs:
  version-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Check version synchronization
        run: |
          PYPROJECT_VER=$(grep '^version = ' pyproject.toml | cut -d'"' -f2)
          INIT_VER=$(python -c "from src.shypn.version import __version__; print(__version__)")
          CITATION_VER=$(grep '^version: ' CITATION.cff | awk '{print $2}')
          
          if [ "$PYPROJECT_VER" != "$INIT_VER" ] || [ "$PYPROJECT_VER" != "$CITATION_VER" ]; then
            echo "Version drift detected!"
            exit 1
          fi
          
          echo "Versions synchronized: $PYPROJECT_VER"
      
      - name: Check API compatibility
        run: |
          python -c "from shypn.compatibility import verify_submodule_versions; \
                     warnings = verify_submodule_versions(); \
                     exit(1 if warnings else 0)"
```

---

## Implementation Phases

### Phase 1: Immediate Fixes (Day 1) 🔥 **CRITICAL**

1. ✅ Create `src/shypn/version.py` as single source of truth
2. ✅ Fix CITATION.cff version drift (`2.4.6` → `2.5.4`)
3. ✅ Update `src/shypn/__init__.py` to import from `version.py`
4. ✅ Create `scripts/sync_versions.sh` script
5. ✅ Run sync script and verify

**Time**: 1-2 hours

---

### Phase 2: Compatibility System (Day 2-3)

1. ✅ Create `src/shypn/compatibility.py` with version checking
2. ✅ Add submodule version requirements to `version.py`
3. ✅ Wire up auto-verification in `__init__.py`
4. ✅ Test with intentionally mismatched versions
5. ✅ Document compatibility matrix in `doc/VERSION.md`

**Time**: 4-6 hours

---

### Phase 3: Deprecation Tracking (Day 4-5)

1. ✅ Create `src/shypn/deprecation.py` decorator system
2. ✅ Apply `@deprecated` to known deprecated methods:
   - `KEGGCategory._on_enrich_names_clicked()`
   - `mode_events.py` functions (already archived)
   - Other deprecated APIs (audit needed)
3. ✅ Update documentation with deprecation policy
4. ✅ Test deprecation warnings fire correctly

**Time**: 4-6 hours

---

### Phase 4: Automation (Week 2)

1. ✅ Create pre-commit hook for version validation
2. ✅ Create GitHub Actions workflow
3. ✅ Test on feature branches
4. ✅ Document setup process for contributors

**Time**: 3-4 hours

---

### Phase 5: Documentation (Week 2)

1. ✅ Update `README.md` with versioning policy
2. ✅ Create `doc/VERSION.md` with:
   - Semantic versioning guidelines
   - API compatibility matrix
   - Deprecation lifecycle
   - Release checklist
3. ✅ Add version info to error messages

**Time**: 2-3 hours

---

## Success Metrics

### After Phase 1 (Immediate):
- ✅ All version files show `2.5.4`
- ✅ `sync_versions.sh` script works
- ✅ CITATION.cff matches pyproject.toml

### After Phase 2 (Week 1):
- ✅ Import warnings when submodules are mismatched
- ✅ Clear error messages for incompatibilities
- ✅ Documentation of required versions

### After Phase 3 (Week 1):
- ✅ Deprecated methods emit warnings
- ✅ Warnings include replacement suggestions
- ✅ Deprecation registry tracks all deprecated APIs

### After Phase 4 (Week 2):
- ✅ Pre-commit hooks prevent version drift
- ✅ CI fails on version mismatches
- ✅ Automated checks run on every PR

### After Phase 5 (Week 2):
- ✅ Complete versioning documentation
- ✅ Clear contributor guidelines
- ✅ Users understand deprecation policy

---

## Risk Mitigation

### Risk 1: Breaking Existing Code
**Mitigation**: All new systems are additive. Old code continues to work with warnings.

### Risk 2: CI/CD Overhead
**Mitigation**: Version checks are fast (<5s). Cached in GitHub Actions.

### Risk 3: Developer Friction
**Mitigation**: 
- Auto-sync script makes version updates easy
- Pre-commit hooks catch issues early
- Clear documentation

---

## Rollout Strategy

### Week 1: Foundation
- Implement Phases 1-2 (version source + compatibility)
- Test on current branch (Usability-and-Manuscripts)
- Merge to main after validation

### Week 2: Enhancement
- Implement Phases 3-5 (deprecation + automation + docs)
- Deploy to production
- Monitor for issues

### Week 3: Adoption
- Audit existing code for deprecated APIs
- Add `@deprecated` decorators where needed
- Update submodule versions

---

## Long-term Maintenance

### Every Release:
1. Update `src/shypn/version.py` ONLY
2. Run `scripts/sync_versions.sh`
3. Commit all changed files together
4. Create git tag matching version
5. Verify CI passes

### Every Quarter:
1. Audit deprecated APIs
2. Remove APIs past removal date
3. Update compatibility matrix
4. Review submodule versions

---

## Related Issues

This plan addresses:
- ✅ Version drift between files
- ✅ CITATION.cff outdated
- ✅ No API compatibility checks
- ✅ No deprecation tracking
- ✅ Manual version sync errors
- ✅ Submodule version independence

---

## Next Steps

1. **Review this plan** for approval
2. **Start Phase 1** (immediate fixes)
3. **Test Phase 1** on current branch
4. **Commit Phase 1** before proceeding
5. **Continue with Phases 2-5** incrementally

---

**Status**: 📋 PLAN COMPLETE - Ready for Review & Implementation  
**Estimated Total Time**: 20-25 hours over 2 weeks  
**Priority**: HIGH - Prevents future regressions
