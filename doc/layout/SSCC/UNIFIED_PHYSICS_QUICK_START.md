# Quick Start: Testing Unified Physics Algorithm

## 🎯 What is it?

**ONE algorithm** that combines ALL physics forces:
- ✅ Oscillatory forces (arcs)
- ✅ Proximity repulsion (hubs)
- ✅ Ambient tension (global)

**Graph properties → Physics properties → Natural layouts!**

---

## 🚀 How to Test (3 Minutes)

### Step 1: Open Shypn
```bash
cd /home/simao/projetos/shypn
python3 -m shypn.main
```

### Step 2: Load Test Model
- **File → Open**
- Navigate to: `workspace/Test_flow/model/`
- Choose one:
  - `hub_constellation.json` (3 hubs)
  - `scc_with_hubs.json` (SCC + hubs)

### Step 3: Apply Layout
- **Right-click** on canvas background
- Select: **"Layout: Solar System (SSCC)"**
- Wait 1-2 seconds

### Step 4: Observe
- ✅ Hubs spread widely (constellation pattern)
- ✅ No clustering
- ✅ Natural orbital structure
- ✅ Beautiful layout!

---

## 📊 Test Models

### Model 1: Hub Constellation
**File:** `hub_constellation.shy`
- 3 hubs (7+ connections each)
- 21 satellites
- Tests hub separation

**Expected:**
- Hubs 700-1500 units apart
- Each hub with ring of satellites
- Constellation pattern

### Model 2: SCC with Hubs
**File:** `scc_with_hubs.shy`
- 6-node SCC (center)
- 2 external hubs (sides)
- Tests SCC as gravitational center

**Expected:**
- SCC at center (hexagonal)
- Hubs pushed to sides
- Balanced layout

---

## ✅ What to Look For

**Good Signs:**
- ✓ Hubs well-separated
- ✓ No overlapping nodes
- ✓ Clear structure
- ✓ Natural spacing

**Bad Signs:**
- ✗ Hubs clustered together
- ✗ Nodes overlapping
- ✗ Dense pockets
- ✗ Messy layout

---

## 🔧 If Issues Occur

**Hubs too close:**
- Expected: 700+ units apart
- If less: Report for parameter tuning

**Layout too spread:**
- Nodes very far apart
- Empty canvas areas
- Report for tuning

**Layout too compact:**
- Everything bunched up
- Nodes too close
- Report for tuning

---

## 📝 Feedback

**Please note:**
1. Which model tested?
2. What looks good?
3. What looks bad?
4. Hub separation distance?
5. Overall impression?

---

## 🎉 Success!

**If you see:**
- ✅ Hubs in constellation (spread widely)
- ✅ Clean orbital patterns
- ✅ No clustering
- ✅ Beautiful layout

**Then the unified physics algorithm is working!** 🌌⚡

---

**Quick Reference:**
- Test models: `workspace/Test_flow/model/`
- Apply layout: Right-click → "Layout: Solar System (SSCC)"
- Expected: Natural, stable, aesthetic layouts
- ONE algorithm, ALL forces, AUTOMATIC!

**Go test it now!** 🚀
