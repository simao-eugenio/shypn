# Transition Search with Automatic Locality - Quick Guide

## What You Get Now

### When you search for a transition, you automatically get the **entire locality**!

```
┌─────────────────────────────────────────────────────────────────┐
│  Transition Analysis Tab - Search Box                           │
└─────────────────────────────────────────────────────────────────┘
   │
   │  User types: "T1"
   │  User presses Enter
   │
   ▼
┌─────────────────────────────────────────────────────────────────┐
│  Search Results                                                  │
│  ✓ Added T1 with locality (4 places)                           │
└─────────────────────────────────────────────────────────────────┘
   │
   │  Automatic Locality Detection
   │
   ▼
┌─────────────────────────────────────────────────────────────────┐
│  Plot Shows Complete P-T-P Pattern                              │
│                                                                  │
│    ↓ P1 (input) - - - - - -  (dashed, lighter shade)          │
│    ↓ P2 (input) - - - - - -  (dashed, lighter shade)          │
│    T1 [CON] ───────────────  (solid, base color)              │
│    ↑ P3 (output) · · · · · ·  (dotted, darker shade)          │
│    ↑ P4 (output) · · · · · ·  (dotted, darker shade)          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Before vs After

### BEFORE (Without Auto-Locality)
```
Step 1: Search for "T1"
Step 2: Result: "✓ Added T1 to analysis"
Step 3: Plot shows only T1 line
Step 4: Right-click T1 in model
Step 5: Select "With Locality" from menu
Step 6: Now plot shows T1 + places
```
**Total: 6 steps** ❌

### AFTER (With Auto-Locality)
```
Step 1: Search for "T1"
Step 2: Result: "✓ Added T1 with locality (4 places)"
Step 3: Plot shows T1 + all connected places
```
**Total: 3 steps** ✅

## Visual Example

### Model Structure
```
     P1 (5 tokens)
      ↓
     P2 (3 tokens)
      ↓
    [T1] ← Continuous Transition
      ↓
     P3 (0 tokens)
      ↓
     P4 (0 tokens)
```

### What You See in Plot
```
Transition Rate Analysis
─────────────────────────────────────────────────────

Rate (tokens/s)
│
│  ↓ P1 (input) - - - - - - (lighter red, 5 tokens)
│  ↓ P2 (input) - - - - - - (lighter red, 3 tokens)
│  T1 [CON] ──────────────── (red, rate function)
│  ↑ P3 (output) · · · · · · (darker red, 0 tokens)
│  ↑ P4 (output) · · · · · · (darker red, 0 tokens)
│
└──────────────────────────────────────────────> Time (s)

Legend:
  ─── Transition (solid line)
  - - Input places (dashed, pre-conditions)
  · · Output places (dotted, post-conditions)
  ↓   Token flow direction (incoming)
  ↑   Token flow direction (outgoing)
```

## Key Features

✅ **Automatic Detection**: Locality detected instantly when transition found  
✅ **Complete Context**: See transition behavior with input/output places  
✅ **Color Coordination**: Places colored relative to transition  
✅ **Visual Distinction**: Line styles show input (dashed) vs output (dotted)  
✅ **Smart Fallback**: Works even if transition has no inputs/outputs  
✅ **Clear Feedback**: Status message shows how many places added  

## Usage

1. **Open your Petri net model**
2. **Click on "Transition Analysis" tab** (right panel)
3. **Type transition name** in search box (e.g., "consume", "T1", "fire")
4. **Press Enter** or click Search button
5. **Done!** Plot shows transition + all connected places

## Technical Details

- **Detection**: Uses `LocalityDetector` to scan arc connections
- **Valid Locality**: Transition must have both inputs AND outputs
- **Invalid Locality**: If no inputs or no outputs, only transition plotted
- **Performance**: Instant detection, no user wait time

## Benefits

🚀 **3x Faster Workflow**  
🎯 **Complete Context Every Time**  
👁️ **Better Understanding of Token Flow**  
🔄 **Consistent with Context Menu**  
✨ **No Extra Configuration Needed**  

---

**You asked for it, you got it!** 

Search for a transition → Get the entire locality automatically! 🎉
