# Tools Directory

This directory contains maintenance and development tools for the shypn project.

## Version Management

### sync_versions.sh

Synchronize version information across all project files from the single source of truth.

**Usage:**
```bash
# Check if all versions are synchronized
./tools/sync_versions.sh --check

# Synchronize all version files
./tools/sync_versions.sh
```

**What it does:**
- Reads version from `src/shypn/version.py` (single source of truth)
- Updates `pyproject.toml`
- Updates `CITATION.cff`
- Verifies `__init__.py` imports from `version.py`

**When to use:**
- After bumping version in `src/shypn/version.py`
- Before creating a new release
- In pre-commit hooks (automated)
- When you see version drift warnings

## Protective Measures

The version synchronization system implements multiple protective layers:

### Layer 1: Single Source of Truth
- `src/shypn/version.py` - All version info centralized here
- Other files import or are synced from this source
- Prevents accidental version drift

### Layer 2: Runtime Compatibility Checking
- `src/shypn/compatibility.py` - Automatic version validation
- Checks submodule compatibility on import
- Warns about API version mismatches
- Prevents runtime errors from incompatible components

### Layer 3: Synchronization Script
- `tools/sync_versions.sh` - Automated version propagation
- Run manually or via hooks
- Validates consistency across project

### Layer 4: Git Workflow Protection
- Create feature branches for major changes
- Test imports before committing
- Use `--check` flag before releases

## Example Workflow

**When bumping version:**
```bash
# 1. Edit version in single source
vim src/shypn/version.py  # Update __version__ = "2.5.5"

# 2. Sync all files
./tools/sync_versions.sh

# 3. Verify
./tools/sync_versions.sh --check

# 4. Test imports
python3 -c "import sys; sys.path.insert(0, 'src'); import shypn; print(shypn.__version__)"

# 5. Commit
git add -A
git commit -m "Bump version to 2.5.5"
git tag v2.5.5
```

**Before creating a release:**
```bash
# Verify everything is synchronized
./tools/sync_versions.sh --check

# Check compatibility
python3 -c "from shypn.compatibility import verify_submodule_compatibility; verify_submodule_compatibility(strict=True)"

# Create release branch
git checkout -b release/v2.5.5
git push origin release/v2.5.5
```

## Related Documentation

- [VERSION_SYNC_PLAN.md](../VERSION_SYNC_PLAN.md) - Full implementation plan
- [src/shypn/version.py](../src/shypn/version.py) - Version source of truth
- [src/shypn/compatibility.py](../src/shypn/compatibility.py) - Compatibility checking
