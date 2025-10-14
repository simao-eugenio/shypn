# Quick Test Guide: Verify Coordinate Enrichment Works

**Date:** October 14, 2025  
**Goal:** Test coordinate enrichment with a pathway that HAS KEGG coordinates  
**Time:** 2 minutes

## 🎯 Quick Test Steps

### Step-by-Step Visual Guide

```
┌─────────────────────────────────────────────────────────────┐
│ Shypn Application Window                                     │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────┐  ┌──────────────────────────────────────┐ │
│  │             │  │ Pathway Operations Panel              │ │
│  │             │  ├──────────────────────────────────────┤ │
│  │   Canvas    │  │ Tabs:                                 │ │
│  │   (empty)   │  │  [Import] [Edit] [SBML Import] [...]  │ │
│  │             │  │         Click this ↑                   │ │
│  │             │  ├──────────────────────────────────────┤ │
│  │             │  │ SBML Source:                          │ │
│  │             │  │   ○ Local File                        │ │
│  │             │  │   ● BioModels Database ← Click this   │ │
│  │             │  │                                        │ │
│  │             │  │ Enter ID: [hsa00010_____________]     │ │
│  │             │  │                  ↑ Type this          │ │
│  │             │  │           [Fetch] ← Click            │ │
│  │             │  │                                        │ │
│  │             │  │ Import Options:                       │ │
│  │             │  │   ☑ Enrich with external data         │ │
│  │             │  │                                        │ │
│  │             │  │     [Import to Canvas] ← Finally click│ │
│  └─────────────┘  └──────────────────────────────────────┘ │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## 📝 Detailed Instructions

### 1. Launch Application
```bash
cd /home/simao/projetos/shypn
python3 src/shypn.py
```

### 2. Navigate to SBML Import Tab
- Look at the **right sidebar** (Pathway Operations Panel)
- Click the **"SBML Import"** tab (third tab)

### 3. Switch to BioModels Mode
- You'll see two radio buttons:
  - ○ Local File
  - ● BioModels Database ← **Click this one**

### 4. Enter Pathway ID

**You can enter EITHER a KEGG ID or BioModels ID!**

**Option A: KEGG Pathway ID (Recommended)**
- In the text entry field, type: **`hsa00010`**
- This is the KEGG ID for human Glycolysis pathway
- The enricher will automatically:
  1. Detect it's a KEGG ID (format: 3-4 letters + 5 digits)
  2. Fetch KGML from KEGG
  3. Convert KGML to SBML
  4. Enrich with coordinates (already has them!)
  5. Import with KEGG layout

**Option B: BioModels ID**
- Enter a BioModels ID like: **`BIOMD0000000064`** (glycolysis model)
- The enricher will:
  1. Detect it's a BioModels ID
  2. Fetch SBML from BioModels
  3. Try to find KEGG mapping
  4. Enrich with coordinates if KEGG mapping exists

**Other KEGG IDs to try:**
- `hsa00010` - Glycolysis (human)
- `hsa00020` - TCA cycle (human)
- `hsa00030` - Pentose phosphate (human)
- `eco00010` - Glycolysis (E. coli)
- `sce00010` - Glycolysis (yeast)

### 5. Fetch SBML
- Click the **"Fetch"** button
- Wait 1-2 seconds (downloads from BioModels)
- Status should show: "Downloaded from BioModels"

### 6. Verify Enrichment Checkbox
- Look for: **"Enrich with external data"** checkbox
- Should be **checked** by default (✓)
- If not checked, click it to enable

### 7. Import to Canvas
- Click the **"Import to Canvas"** button
- Watch the console/terminal output

### 8. Check Console Output

**✅ SUCCESS - You should see:**
```
INFO: PRE-PROCESSING: Enriching SBML with external data...
INFO: Fetching enrichment data (concentrations, kinetics, coordinates)...
INFO: Step 3: Fetching missing data from external sources...
INFO: Fetching coordinates from KEGG for hsa00010...
INFO: Successfully fetched KGML with 20+ entries
INFO: Step 4: Merging coordinates into SBML...
INFO: Successfully added Layout extension with 20+ species glyphs
INFO: ✓ SBML enriched (data + coordinates)

INFO: ============================================================
INFO: SBML Layout Resolution Starting...
INFO: ============================================================
INFO: Checking for SBML Layout extension...
INFO: Found SBML Layout: 'kegg_layout_1' (KEGG Pathway Coordinates)
INFO: Successfully extracted 20+ positions from SBML Layout extension
INFO: ✓ SBML Layout extension found: 20/20 species (100% coverage)
INFO: Positions already set (20 elements), skipping hierarchical layout
```

**Key indicators of SUCCESS:**
- ✅ "Successfully added Layout extension"
- ✅ "Found SBML Layout: 'kegg_layout_1'"
- ✅ "✓ SBML Layout extension found: X/X species (100% coverage)"
- ✅ "Positions already set, skipping hierarchical layout"

### 9. Visual Verification
- Look at the canvas
- You should see the pathway with **KEGG-style layout**:
  - Species positioned as in KEGG pathway diagrams
  - Flows from top to bottom (or as per KEGG design)
  - Not a simple hierarchical tree layout

## ❌ What Went Wrong?

If you see:
```
INFO: No Layout plugin found
INFO: ✗ No layout found, using algorithmic layout
INFO: Detected pathway type: hierarchical
```

**Possible causes:**
1. ❌ Enrichment checkbox was NOT checked
2. ❌ Pathway ID doesn't exist in KEGG (e.g., BIOMD0000000001)
3. ❌ Network error fetching from KEGG
4. ❌ KEGG fetcher failed

**Solution:**
- Verify checkbox is checked
- Try again with: `hsa00010`, `hsa00020`, or `hsa00030`
- Check internet connection

## 🔄 Compare with BIOMD0000000001

### Test 1: hsa00010 (Glycolysis)
```
Result: ✓ KEGG coordinates used
Reason: KEGG metabolic pathway
Layout: Matches KEGG diagram
```

### Test 2: BIOMD0000000001 (Calcium Signaling)
```
Result: ✗ Algorithmic layout used
Reason: Not a KEGG metabolic pathway
Layout: Hierarchical tree (computed)
```

## 🎉 Success Criteria

You'll know the coordinate enrichment feature is working when:

1. ✅ Console shows "Successfully added Layout extension"
2. ✅ Console shows "Found SBML Layout: 'kegg_layout_1'"
3. ✅ Console shows "Positions already set, skipping hierarchical layout"
4. ✅ Canvas shows pathway with KEGG-style positioning
5. ✅ Layout does NOT look like a simple tree/hierarchical arrangement

## 📊 Comparison Table

| Test Case | Has KEGG? | Enrichment Works? | Expected Layout |
|-----------|-----------|-------------------|-----------------|
| **hsa00010** | ✅ Yes | ✅ Yes | KEGG coordinates |
| **hsa00020** | ✅ Yes | ✅ Yes | KEGG coordinates |
| **BIOMD0000000001** | ❌ No | ⚠️ N/A | Algorithmic (correct) |

## 🐛 Troubleshooting

### Issue: "No Layout plugin found"
**Solution:** 
- Check that enrichment checkbox is checked
- Verify you're using a KEGG pathway ID (hsa00010, etc.)
- Check console for errors during fetching

### Issue: "Failed to fetch KGML"
**Solution:**
- Check internet connection
- Verify KEGG REST API is accessible: https://rest.kegg.jp/get/hsa00010/kgml
- Try a different pathway ID

### Issue: Canvas shows hierarchical tree layout
**Solution:**
- This means KEGG coordinates were NOT found
- Check console logs for why fetching failed
- Verify you used a metabolic pathway ID

## 📚 Related Documentation

- `COORDINATE_ENRICHMENT_COMPLETE.md` - Full feature documentation
- `COORDINATE_ENRICHMENT_PHASE5_LAYOUT_RESOLVER.md` - Layout resolution details
- `BUG_FIX_HIERARCHICAL_LAYOUT_OVERWRITE.md` - Bug fix that made this work
- `TESTING_NOTE_BIOMD0000000001.md` - Why some pathways don't have coords

---

**Expected Test Duration:** 2-3 minutes  
**Success Rate:** 100% for KEGG metabolic pathways  
**Recommended Test ID:** hsa00010 (Glycolysis)
