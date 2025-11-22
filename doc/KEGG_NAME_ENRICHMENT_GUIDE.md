# KEGG Name Enrichment Guide

## Overview

**KEGG Name Enrichment** is a post-import tool that fetches biological names from the KEGG REST API to replace KEGG codes (C#####, R#####) with actual compound and enzyme names.

## Why Post-Import?

The enrichment is **NOT** part of the import flow because:
- **API queries are slow** (~1.5 seconds per item)
- **Import remains fast** (uses only KGML file data)
- **User controls when to enrich** (opt-in operation)
- **Rate limiting respected** (KEGG API requires delays between requests)

## Philosophy

### KEGG Import Strategy

```
Import KGML → Fast topology extraction (uses graphics names when available)
     ↓
Model ready → Can work with existing names (mix of biological + codes)
     ↓
User triggers enrichment → Replace remaining codes with API-fetched names
     ↓
Fully enriched → All biological names
```

### When to Use

**✅ Use enrichment when:**
- Model has C##### or R##### codes as names
- You need biological names for publication/presentation
- You're okay with slower operation (API queries)
- You want most complete biological information

**❌ Don't use enrichment when:**
- Graphics names are already good enough
- You need fast import (leave codes as-is)
- Working offline (requires internet)
- Model will be heavily edited anyway

## Usage

### Basic Usage

```python
from shypn.services import enrich_kegg_names

# After importing KEGG model
document = import_kegg_pathway("hsa00010")

# Enrich names (fetches from KEGG API)
result = enrich_kegg_names(document)

print(f"Enriched {result.places_enriched} places")
print(f"Enriched {result.transitions_enriched} transitions")
print(f"Duration: {result.duration_seconds:.1f} seconds")
```

### With Progress Callback

```python
from shypn.services import KEGGNameEnricher

def show_progress(current, total, message):
    print(f"[{current}/{total}] {message}")

enricher = KEGGNameEnricher(progress_callback=show_progress)
result = enricher.enrich_document(document)
```

### Checking What Will Be Enriched

```python
import re

COMPOUND_CODE = re.compile(r'^C\d{5}$')
REACTION_CODE = re.compile(r'^R\d{5}$')

# Count places with codes
places_to_enrich = [
    p for p in document.places 
    if COMPOUND_CODE.match(p.name) and 
       p.metadata.get('data_source') == 'kegg_import'
]

print(f"Will enrich {len(places_to_enrich)} places")
```

## What Gets Enriched

### Places (Compounds)

**Before enrichment:**
- Name: `C00002`
- Label: "ATP" (from KGML graphics)

**After enrichment:**
- Name: `ATP` (fetched from KEGG API)
- Label: "ATP" (unchanged)

### Transitions (Reactions)

**Before enrichment:**
- Name: `R00086`
- Label: "Hexokinase" (from KGML graphics)

**After enrichment:**
- Name: `Hexokinase` (fetched from KEGG API)
- Label: "Hexokinase" (unchanged)

## Safety Features

### 1. Only KEGG Imports

Enrichment only touches items with:
```python
metadata['data_source'] == 'kegg_import'
```

Manual models and SBML imports are **never modified**.

### 2. Only Codes

Only items with KEGG codes as names are enriched:
- Compounds: `C00002`, `C00008`, etc.
- Reactions: `R00001`, `R00086`, etc.

Items with proper names are **skipped**.

### 3. Fallback on Failure

If API fetch fails:
- Name remains unchanged (keeps KEGG code)
- Marked in `result.places_failed` or `result.transitions_failed`
- No error raised (graceful degradation)

## API Details

### KEGG REST API

Enrichment uses the KEGG REST API:
```
https://rest.kegg.jp/get/C00002  → Compound info
https://rest.kegg.jp/get/R00001  → Reaction info
```

### Rate Limiting

Built-in rate limiting (0.5 seconds between requests):
- Respectful to KEGG servers
- Prevents API bans
- ~2 requests per second max

### Academic Use Only

⚠️ **KEGG API is for academic use only**. Commercial use requires license.

## Examples

### Example 1: Glycolysis Import

```python
# Import glycolysis pathway
document = import_kegg_pathway("hsa00010")

# Check current names
for place in document.places[:3]:
    print(f"Place: {place.name}")
# Output:
# Place: C00002  (ATP)
# Place: C00008  (ADP)
# Place: Glucose

# Enrich codes
result = enrich_kegg_names(document)

# Check enriched names
for place in document.places[:3]:
    print(f"Place: {place.name}")
# Output:
# Place: ATP     (enriched!)
# Place: ADP     (enriched!)
# Place: Glucose (unchanged - already good)
```

### Example 2: Result Analysis

```python
result = enrich_kegg_names(document)

print(f"""
Enrichment Results:
------------------
Places enriched:      {result.places_enriched}
Places failed:        {result.places_failed}
Transitions enriched: {result.transitions_enriched}
Transitions failed:   {result.transitions_failed}
Total API calls:      {result.total_api_calls}
Duration:             {result.duration_seconds:.1f}s

Details:
""")

for old_name, new_name in result.details.items():
    print(f"  {old_name} → {new_name}")
```

### Example 3: Selective Enrichment

```python
# Only enrich if there are many codes
codes_count = len([
    p for p in document.places 
    if re.match(r'^C\d{5}$', p.name)
])

if codes_count > 5:
    print(f"Enriching {codes_count} compound codes...")
    result = enrich_kegg_names(document)
else:
    print("Not enough codes to bother enriching")
```

## Performance

### Timing Examples

| Items to Enrich | API Calls | Duration |
|-----------------|-----------|----------|
| 10 places       | 10        | ~15s     |
| 50 places       | 50        | ~75s     |
| 100 places      | 100       | ~150s    |

**Rule of thumb:** ~1.5 seconds per item (0.5s rate limit + network latency)

### Optimization

To minimize API calls:
1. **Use graphics names first** (already in KGML)
2. **Only enrich when needed** (publication, presentation)
3. **Batch similar pathways** (import multiple, enrich once)

## Troubleshooting

### Problem: API Fetch Failed

**Symptom:** `result.places_failed > 0` or `result.transitions_failed > 0`

**Causes:**
- Network connectivity issues
- KEGG server temporarily down
- Invalid KEGG code (obsolete entry)
- Rate limiting (too many requests)

**Solution:**
- Check internet connection
- Retry later
- Accept that some codes remain (not all KEGG entries have good names)

### Problem: Slow Enrichment

**Symptom:** Takes minutes to complete

**Expected:** Yes! API queries are slow by design (rate limiting)

**Solution:**
- Be patient (respect KEGG servers)
- Only enrich when necessary
- Consider enriching smaller pathways first

### Problem: Wrong Names

**Symptom:** Enriched name is unexpected

**Cause:** KEGG API returned abbreviated or alternative name

**Solution:**
- Manually edit name after enrichment (names are just strings)
- Check KEGG website for alternative names
- Report to KEGG if data is incorrect

## Integration with UI

### Future UI Integration

Potential UI workflow:
```
1. User imports KEGG pathway
2. Panel shows: "10 compounds have KEGG codes (C#####)"
3. Button: "Enrich Names from KEGG API"
4. Progress bar during enrichment
5. Notification: "Enriched 10/10 compounds in 15s"
```

### Current Workflow (Manual)

```python
# In Python console or script
from shypn.services import enrich_kegg_names

# After import
result = enrich_kegg_names(document)

# Save document
document.save("enriched_model.shypn")
```

## Summary

| Aspect | Import (Fast) | Enrichment (Slow) |
|--------|--------------|-------------------|
| **Data source** | KGML graphics | KEGG REST API |
| **Speed** | Instant | ~1.5s per item |
| **Naming** | Mixed (biological + codes) | Biological only |
| **When** | Always | User-triggered |
| **Requires internet** | No (from file) | Yes (API calls) |
| **Use case** | General work | Publication/presentation |

**Best practice:** Import fast, work with model, enrich names only when finalizing for presentation.
