# Quick Start: Heuristic Parameters with BioModels Data

## 🎯 How It Works

The heuristic system uses BioModels data **internally** for intelligent parameter inference:

```
Canvas Transitions → Heuristic Analysis → Database Lookup/Inference → Results Table
       ↓                      ↓                      ↓                       ↓
    T1, T2, T3...    Read EC numbers,      Try exact match        One row per
                     reaction names         then infer           transition only
```

### The Smart Workflow:

1. **You draw** transitions on canvas (T1, T2, T3...)
2. **Heuristic reads** each transition's properties
3. **For each transition**:
   - Try to find **exact match** in database (by EC number, reaction ID)
   - If found: Use BioModels parameters (85% confidence) ⭐⭐⭐⭐
   - If not found: **Infer** from training data (50% confidence) ⭐⭐
4. **Display results**: One row per transition with best parameters
5. **You apply** selected parameters to transitions

## 🚀 See It Working

### Step 1: Verify Database
```bash
cd /home/simao/projetos/shypn
python test_heuristic_ui_integration.py
```

Expected output:
```
✅ ALL TESTS PASSED!
✓ Database has 254 parameters
✓ Engine can query parameters from database
```

### Step 2: Launch Shypn
```bash
python src/shypn.py
```

### Step 3: Create or Import a Model
- Draw some transitions on canvas, OR
- Import a pathway from KEGG/BioModels

### Step 4: Open Heuristic Parameters
1. Click **Pathway Operations** panel (right side)
2. Expand **HEURISTIC PARAMETERS** category
3. Select mode: **"Enhanced (Database Fetch)"**
4. Click **"Analyze & Infer Parameters"**

### Step 5: See the Results!
The table shows **one row per transition** with:
- **ID**: Your transition ID (T1, T2, T3...)
- **Type**: Continuous, Stochastic, Timed, Immediate
- **Source**: Where parameters came from:
  - "BioModels" = Direct match from database (high confidence)
  - "Database" = Found in local database
  - "Heuristic" = Inferred from training data (medium confidence)
- **EC/Enzyme**: Matched enzyme info (if found)
- **Parameters**: Vmax, Km, Kcat, Lambda, etc.
- **Confidence**: Shows match quality ⭐⭐⭐⭐

### Step 6: Apply Parameters
1. Click checkbox next to desired transitions
2. Click **"Apply Selected"**
3. Parameters are written to your transitions!

## 📊 What You'll See

### Example Table:
| ☐ | ID | Type | Source | EC/Enzyme | Vmax | Km | Kcat | Confidence |
|---|----|----|--------|-----------|------|----|----|------------|
| ☐ | T1 | Continuous | BioModels | EC 2.7.1.11<br>Phosphofructokinase | 550 | 0.1 | 1500 | 85% ⭐⭐⭐⭐ |
| ☐ | T2 | Continuous | Heuristic | - | 100 | 0.1 | 100 | 50% ⭐⭐ |
| ☐ | T3 | Stochastic | BioModels | EC 4.1.2.13<br>Aldolase | - | - | - | 85% ⭐⭐⭐⭐ |

**Notice**: 
- T1 got **exact match** from BioModels (85% confidence)
- T2 got **inferred** values from training data (50% confidence)
- T3 got **matched** stochastic parameters from BioModels

### Status Bar:
```
Found 3 transitions
```

## 🔍 Understanding the Results

### High Confidence (85% ⭐⭐⭐⭐)
- **Source**: BioModels or Database
- **Meaning**: Exact match found by EC number or reaction ID
- **Quality**: Peer-reviewed, curated parameters
- **Usage**: Use these values confidently!

### Medium Confidence (50% ⭐⭐)
- **Source**: Heuristic
- **Meaning**: Inferred from similar reactions in database
- **Quality**: Educated guess based on training data
- **Usage**: Good starting point, may need refinement

## 🧠 How Inference Works

The system is **smart** about matching:

1. **Exact Match** (Best):
   ```
   Your transition has EC 2.7.1.11
   → Database has EC 2.7.1.11 parameters
   → Use them! (85% confidence)
   ```

2. **Similar Match** (Good):
   ```
   Your transition type: Continuous enzyme kinetics
   → Database has 143 enzyme kinetics examples
   → Learn from them, suggest typical values (50% confidence)
   ```

3. **Generic Fallback** (Basic):
   ```
   No information available
   → Use literature defaults (40% confidence)
   ```

## 🔄 The Learning Loop

As you use the system:

1. **You apply** parameters from high-confidence matches
2. **System tracks** which parameters you selected
3. **Database learns** your preferences
4. **Future suggestions** improve based on your usage
5. **Confidence scores** adjust over time

## 🔍 Troubleshooting

**Q: All transitions show "Heuristic" source?**
- Your transitions don't have EC numbers or reaction IDs yet
- Add EC numbers to transitions for better matching
- Or use KEGG import which includes this metadata

**Q: Want to see what's in the database?**
```bash
python -c "
from src.shypn.crossfetch.database.heuristic_db import HeuristicDatabase
db = HeuristicDatabase()
params = db.query_parameters(ec_number='2.7.1.11', limit=5)
for p in params:
    print(f\"EC {p['ec_number']}: Vmax={p['parameters'].get('vmax')}\")
"
```

**Q: Can I add my own parameters to the database?**
- Yes! Manually measured parameters can be imported
- They'll be used for future inference
- Higher usage count = higher priority in suggestions

## 🎓 Best Practices

1. **Use KEGG Import**: Pathways from KEGG include EC numbers
2. **Check Source Column**: Prioritize BioModels matches
3. **Review Confidence**: ⭐⭐⭐⭐ = trust it, ⭐⭐ = verify
4. **Apply Selectively**: Don't blindly apply all suggestions
5. **Iterate**: Apply, simulate, refine based on results

## ✅ Success Indicators

You know it's working when:
- ✓ Table shows your transition IDs (T1, T2, not DB_*)
- ✓ Some transitions have "BioModels" source (exact matches)
- ✓ EC numbers appear when transitions are matched
- ✓ High confidence stars (⭐⭐⭐⭐) for matched parameters
- ✓ Status shows "Found X transitions" (your model's transitions)

---

**The database works behind the scenes to give you intelligent parameter suggestions!** 🧠✨

