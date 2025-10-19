# EC Enrichment: Default Behavior vs Checkbox Control

**Date**: October 19, 2025  
**Question**: "One doubt, enrichment it is by default or it is marker dependent?"

---

## Answer: CHECKBOX DEPENDENT (But Checked by Default)

EC enrichment is **controlled by the UI checkbox** but the checkbox is **CHECKED BY DEFAULT**, so enrichment runs unless the user explicitly unchecks it.

---

## How It Works

### 1. UI Layer (User Control)

**File**: `src/shypn/helpers/kegg_import_panel.py`

**Checkbox**: "Metadata enhancement" (`enhancement_metadata_check`)

```python
# Line 98: Get checkbox widget
self.enhancement_metadata_check = self.builder.get_object('enhancement_metadata_check')

# Line 260: Read checkbox value when importing
enable_metadata = self.enhancement_metadata_check.get_active() if self.enhancement_metadata_check else True
#                                                                                                      ^^^^
#                                                                                        DEFAULT: True if widget missing!
```

**Key Line 260**: 
- If checkbox exists: Use its value
- **If checkbox missing/None: Default to `True`** ← This is the failsafe!

---

### 2. Enhancement Options Layer

**File**: `src/shypn/pathway/options.py`

**Default**: `enable_metadata_enhancement: bool = True`

```python
@dataclass
class EnhancementOptions:
    """Configuration options for pathway enhancement pipeline."""
    
    # Line 85: Metadata enhancement enabled by default
    enable_metadata_enhancement: bool = True
    """Enable metadata enhancement processor."""
```

This is used for the post-processing enhancement pipeline (layout, arcs, metadata).

---

### 3. Conversion Options Layer (Core EC Fetching)

**File**: `src/shypn/importer/kegg/converter_base.py`

**Default**: `enhance_kinetics: bool = True`

```python
@dataclass
class ConversionOptions:
    """Configuration options for pathway conversion."""
    
    # Line 53: Kinetics enhancement enabled by default
    enhance_kinetics: bool = True  # Auto-enhance kinetics for better simulation
    """Apply heuristic kinetics enhancement to transitions (default: True)
    When True, analyzes reaction structure to assign appropriate kinetic types
    (stochastic vs continuous) and reasonable parameter defaults
    Uses the heuristic system to fill gaps since KEGG lacks explicit kinetic data"""
```

**This is what actually controls EC number fetching!**

---

### 4. Pathway Converter (Where EC Fetching Happens)

**File**: `src/shypn/importer/kegg/pathway_converter.py`

**Lines 75-76**: Check if enhancement is enabled

```python
# Phase 1.5: Pre-fetch EC numbers in parallel (if metadata enhancement enabled)
if options.enhance_kinetics:  # ← This controls EC fetching!
    reaction_ids = [r.name for r in pathway.reactions]
    logger.info(f"Pre-fetching EC numbers for {len(reaction_ids)} reactions...")
    
    # Fetch all EC numbers in parallel
    ec_cache = fetch_ec_numbers_parallel(reaction_ids, max_workers=5)
    
    # Pass cache to reaction mapper
    self.reaction_mapper.set_ec_cache(ec_cache)
```

**Line 113**: Also checked for kinetics assignment

```python
# Phase 3: Enhance transitions with kinetic properties
if options.enhance_kinetics:
    self._enhance_transition_kinetics(document, reaction_transition_map, pathway)
```

---

## The Connection Chain

Here's how the UI checkbox connects to EC fetching:

```
User Interface
    │
    ├─> [✓] Metadata enhancement (checked by default)
    │                            ↓
Enhancement Options              │
    │                            │
    ├─> enable_metadata_enhancement = True (from checkbox)
    │                            │
    │                            ↓
Convert Pathway Enhanced         │
    │                            │
    ├─> Uses enhancement_options.enable_metadata_enhancement
    │   ↓ (passed as parameter)  │
    │   estimate_kinetics = True (default parameter)
    │                            │
    │                            ↓
Conversion Options               │
    │                            │
    ├─> enhance_kinetics = True  │ (from estimate_kinetics parameter)
    │                            │
    │                            ↓
Pathway Converter                │
    │                            │
    ├─> if options.enhance_kinetics:  ← GATE: Controls EC fetching
    │       fetch_ec_numbers_parallel()
    │                            │
    │                            ↓
EC Fetcher                       │
    │                            │
    └─> Fetches EC numbers from KEGG API
        └─> Stores in transition.metadata['ec_numbers']
```

---

## Current Behavior

### Scenario 1: Default (Checkbox Checked) ✅

**User Action**: Import pathway without touching checkbox

**Result**:
1. ✅ `enhancement_metadata_check.get_active()` → `True`
2. ✅ `enhance_kinetics` → `True`
3. ✅ EC numbers are fetched
4. ✅ EC numbers stored in transition metadata
5. ✅ EC numbers persist to .shy file (after bug fix)

**Example**:
```python
# Glycolysis import with default settings
Transitions: 29
EC enriched: 20/29 (69%)
```

---

### Scenario 2: Checkbox Unchecked ❌

**User Action**: Uncheck "Metadata enhancement" before import

**Result**:
1. ❌ `enhancement_metadata_check.get_active()` → `False`
2. ❌ `enhance_kinetics` → `False`
3. ❌ EC numbers NOT fetched
4. ❌ No EC numbers in metadata
5. ❌ No kinetics enhancement

**Example**:
```python
# Glycolysis import with metadata enhancement disabled
Transitions: 29
EC enriched: 0/29 (0%)
```

---

### Scenario 3: Checkbox Widget Missing (Failsafe)

**User Action**: Widget doesn't load (error case)

**Result**:
```python
enable_metadata = self.enhancement_metadata_check.get_active() if self.enhancement_metadata_check else True
#                                                                                                      ^^^^
#                                                                              Failsafe: Default to True!
```

1. ✅ Falls back to `True`
2. ✅ EC numbers are fetched
3. ✅ Enrichment continues normally

This ensures enrichment works even if UI has issues.

---

## Code Evidence

### UI Panel Line 260 (kegg_import_panel.py)
```python
enable_metadata = self.enhancement_metadata_check.get_active() if self.enhancement_metadata_check else True
```

**Translation**: 
- If checkbox exists: Use user's choice
- **If checkbox missing: Default to `True`** (enrichment ON)

### Conversion Options Line 53 (converter_base.py)
```python
enhance_kinetics: bool = True  # Auto-enhance kinetics for better simulation
```

**Translation**: Enrichment is ON by default

### Pathway Converter Line 76 (pathway_converter.py)
```python
if options.enhance_kinetics:
    # Pre-fetch EC numbers in parallel
```

**Translation**: This is the gate that controls EC fetching

---

## Historical Context

### Before Bug Fix (Pre-commit fe1ef96)

**Problem**: Even with checkbox checked, EC numbers were being fetched but NOT SAVED

**Timeline**:
- User checks "Metadata enhancement" ✓
- EC numbers fetched from KEGG API ✓
- EC numbers stored in memory ✓
- **EC numbers lost on save** ❌ (to_dict() didn't serialize metadata)
- Result: 0% enrichment in saved files

### After Bug Fix (Commit fe1ef96)

**Fixed**: EC numbers now persist correctly

**Timeline**:
- User checks "Metadata enhancement" ✓
- EC numbers fetched from KEGG API ✓
- EC numbers stored in memory ✓
- **EC numbers saved to .shy file** ✓ (to_dict() now serializes metadata)
- Result: 69% enrichment in saved files (for Glycolysis)

---

## Summary Table

| Component | Setting | Default | Controls |
|-----------|---------|---------|----------|
| UI Checkbox | `enhancement_metadata_check` | ✓ Checked | User preference |
| Enhancement Options | `enable_metadata_enhancement` | `True` | Post-processing |
| **Conversion Options** | **`enhance_kinetics`** | **`True`** | **EC fetching** ← KEY |
| Pathway Converter | `if options.enhance_kinetics:` | Checked | EC fetch gate |

**Key Point**: `enhance_kinetics` in `ConversionOptions` is what actually controls EC number fetching!

---

## Answer to Your Question

> "One doubt, enrichment it is by default or it is marker dependent?"

**Answer**: **BOTH!**

1. **Checkbox Dependent**: EC enrichment is controlled by the "Metadata enhancement" checkbox in the UI
2. **Checked by Default**: The checkbox is checked by default, so enrichment runs automatically
3. **Default Behavior**: If checkbox is missing or code path doesn't use UI, `enhance_kinetics=True` by default

**In Practice**:
- ✅ Most users will have enrichment ON (checkbox checked by default)
- ✅ Power users can turn it OFF (uncheck the box)
- ✅ Programmatic imports have enrichment ON (default parameter value)
- ✅ Failsafe: If UI widget fails, enrichment defaults to ON

**So the answer is**: 
- **User-configurable** (checkbox)
- **But defaults to ON** (checked by default)
- **Best of both worlds** (opt-out, not opt-in)

---

## How to Check Current Setting

### In UI:
Look for checkbox: **"Metadata enhancement"** (should be checked by default)

### In Code:
```python
# Check conversion options
from shypn.importer.kegg.converter_base import ConversionOptions
options = ConversionOptions()
print(f"Enrichment enabled: {options.enhance_kinetics}")
# Output: Enrichment enabled: True
```

### In Saved File:
```python
# Check if transitions have EC numbers
import json
with open('pathway.shy', 'r') as f:
    data = json.load(f)
    
enriched = 0
for t in data['transitions']:
    if 'metadata' in t and 'ec_numbers' in t['metadata']:
        enriched += 1

print(f"EC enrichment: {enriched}/{len(data['transitions'])} ({enriched/len(data['transitions'])*100:.1f}%)")
```

---

**Conclusion**: EC enrichment is **checkbox dependent** but **enabled by default**, with multiple failsafes to ensure it works even if the UI has issues.

**Date**: October 19, 2025  
**Status**: ✅ Verified in code  
**Files Checked**: 
- `src/shypn/helpers/kegg_import_panel.py` (line 260)
- `src/shypn/importer/kegg/converter_base.py` (line 53)
- `src/shypn/importer/kegg/pathway_converter.py` (lines 75-76)
- `src/shypn/pathway/options.py` (line 85)
