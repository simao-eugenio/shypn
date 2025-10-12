# Diagnostic Documentation Index

**Quick navigation for diagnostic paths and troubleshooting**

---

## 📋 Quick Start

**Need to diagnose an issue? Start here:**

1. **Quick problem?** → [`DIAGNOSTIC_QUICK_REFERENCE.md`](./DIAGNOSTIC_QUICK_REFERENCE.md)
2. **Need visual flow?** → [`DIAGNOSTIC_VISUALIZATION.md`](./DIAGNOSTIC_VISUALIZATION.md)
3. **Want summary?** → [`DIAGNOSTIC_SUMMARY.md`](./DIAGNOSTIC_SUMMARY.md)
4. **Full details?** → [`SOURCE_SINK_DIAGNOSTIC_PATH.md`](./SOURCE_SINK_DIAGNOSTIC_PATH.md)

---

## 📚 Documentation Files

### Master Index
**[`DIAGNOSTIC_PATH_REVIEW.md`](./DIAGNOSTIC_PATH_REVIEW.md)**
- Overview of entire diagnostic review
- Links to all other documents
- Status summary
- Architecture overview
- Test results

### Complete Diagnostic Path
**[`SOURCE_SINK_DIAGNOSTIC_PATH.md`](./SOURCE_SINK_DIAGNOSTIC_PATH.md)**
- Full source/sink recognition path (7 checkpoints)
- Full simulation time tracking path (7 checkpoints)
- All diagnostic points with code locations
- Testing commands
- Known issues and gaps
- Recommended improvements

### Quick Summary
**[`DIAGNOSTIC_SUMMARY.md`](./DIAGNOSTIC_SUMMARY.md)**
- What's working / what's pending
- Quick diagnostic steps
- Key code locations (tables)
- Common issues and fixes
- Test coverage summary

### Visual Diagrams
**[`DIAGNOSTIC_VISUALIZATION.md`](./DIAGNOSTIC_VISUALIZATION.md)**
- ASCII flowcharts for both paths
- Phase-by-phase visualization
- Checkpoint tables
- Python diagnostic script
- Visual summary diagrams

### Quick Reference Card
**[`DIAGNOSTIC_QUICK_REFERENCE.md`](./DIAGNOSTIC_QUICK_REFERENCE.md)**
- Copy-paste diagnostic commands
- Quick checks for common problems
- Key file locations
- Test commands
- Status indicators

---

## 🎯 Use Cases

### "Tokens not moving in my source/sink model"
→ Start with [`DIAGNOSTIC_QUICK_REFERENCE.md`](./DIAGNOSTIC_QUICK_REFERENCE.md) - Check 1-5

### "I need to understand how source/sink works"
→ Read [`DIAGNOSTIC_VISUALIZATION.md`](./DIAGNOSTIC_VISUALIZATION.md) - See flowcharts

### "Simulation time not advancing"
→ Use [`DIAGNOSTIC_QUICK_REFERENCE.md`](./DIAGNOSTIC_QUICK_REFERENCE.md) - Time checks

### "I'm adding new source/sink feature"
→ Study [`SOURCE_SINK_DIAGNOSTIC_PATH.md`](./SOURCE_SINK_DIAGNOSTIC_PATH.md) - Full architecture

### "Need overview of diagnostic system"
→ Read [`DIAGNOSTIC_PATH_REVIEW.md`](./DIAGNOSTIC_PATH_REVIEW.md) - Master document

---

## ✅ Status at a Glance

### Source/Sink Recognition
- ✅ Data model (flags)
- ✅ Validation method
- ✅ Persistence (JSON)
- ✅ Simulation engine (locality)
- ✅ Behavior layer (token ops)
- ✅ Tests (22/22 passing)
- ⏳ UI integration (pending)

### Simulation Time
- ✅ Initialization
- ✅ Advancement
- ✅ Display
- ✅ Timed behaviors
- ✅ Data logging
- ✅ Reset
- ✅ All functionality working

---

## 🧪 Quick Test Commands

```bash
# Test source/sink
cd /home/simao/projetos/shypn
python3 tests/test_source_sink_strict.py

# Expected: "✅ ALL TESTS PASSED!"

# Launch application
python3 src/shypn.py
```

---

## 📍 Key Diagnostic Checkpoints

### Source/Sink (7 checkpoints)
1. Flag set (`transition.is_source/is_sink`)
2. Validation (`validate_source_sink_structure()`)
3. JSON persistence (save/load)
4. Behavior creation (factory)
5. Locality detection (minimal localities)
6. Independence (parallel execution)
7. Token operations (skip consumption/production)

### Time (7 checkpoints)
1. Initialization (`time = 0.0`)
2. Advancement (`time += dt`)
3. Consistency (all behaviors see same time)
4. Timed enablement (delays work)
5. UI display (shows correct time)
6. Data collection (timestamps)
7. Reset (back to 0.0)

**All 14 checkpoints passing** ✅

---

## 🔧 Developer Resources

### Code Locations

**Source/Sink:**
- Definition: `src/shypn/netobjs/transition.py:63-64`
- Validation: `src/shypn/netobjs/transition.py:370-425`
- Locality: `src/shypn/engine/simulation/controller.py:565-600`
- Behavior: `src/shypn/engine/*_behavior.py`

**Time:**
- Storage: `src/shypn/engine/simulation/controller.py:120`
- Advance: `src/shypn/engine/simulation/controller.py:466`
- Display: `src/shypn/helpers/simulate_tools_palette_loader.py:880`

### Test Files
- `tests/test_source_sink.py` - Basic functionality
- `tests/test_timed_source.py` - Timed source
- `tests/test_timed_sink.py` - Timed sink
- `tests/test_source_sink_strict.py` - Structural validation

---

## 📖 Related Documentation

### Theory and Formalism
- [`SOURCE_SINK_FORMAL_DEFINITIONS.md`](./SOURCE_SINK_FORMAL_DEFINITIONS.md) - Petri net theory
- [`SOURCE_SINK_STRICT_IMPLEMENTATION_PLAN.md`](./SOURCE_SINK_STRICT_IMPLEMENTATION_PLAN.md) - Implementation plan

### Implementation
- [`SOURCE_SINK_IMPLEMENTATION.md`](./SOURCE_SINK_IMPLEMENTATION.md) - Implementation details
- [`SOURCE_SINK_SIMULATION_IMPLEMENTATION.md`](./SOURCE_SINK_SIMULATION_IMPLEMENTATION.md) - Original work

### User Guides
- [`SOURCE_SINK_TROUBLESHOOTING.md`](./SOURCE_SINK_TROUBLESHOOTING.md) - User troubleshooting
- [`SOURCE_SINK_VISUAL_MARKERS_EXPLANATION.md`](./SOURCE_SINK_VISUAL_MARKERS_EXPLANATION.md) - Visual indicators

---

## 🎓 Learning Path

**New to the system?** Follow this order:

1. **Start:** [`DIAGNOSTIC_SUMMARY.md`](./DIAGNOSTIC_SUMMARY.md)
   - Get overview of what's working
   - Understand the systems

2. **Visualize:** [`DIAGNOSTIC_VISUALIZATION.md`](./DIAGNOSTIC_VISUALIZATION.md)
   - See the flows
   - Understand the phases

3. **Deep Dive:** [`SOURCE_SINK_DIAGNOSTIC_PATH.md`](./SOURCE_SINK_DIAGNOSTIC_PATH.md)
   - Understand all checkpoints
   - Learn code locations

4. **Practice:** [`DIAGNOSTIC_QUICK_REFERENCE.md`](./DIAGNOSTIC_QUICK_REFERENCE.md)
   - Try the commands
   - Run diagnostics

5. **Master:** [`DIAGNOSTIC_PATH_REVIEW.md`](./DIAGNOSTIC_PATH_REVIEW.md)
   - See complete picture
   - Understand architecture

---

## 💡 Tips

- **Bookmark this file** for quick access
- **Start with Quick Reference** for immediate problems
- **Use Visualization** when explaining to others
- **Refer to Complete Path** when adding features
- **Check Summary** for current status

---

## ⚡ Common Scenarios

| Scenario | Document | Section |
|----------|----------|---------|
| Debug source not working | Quick Reference | Check 1-5 |
| Debug sink not working | Quick Reference | Check 1-5 |
| Time not advancing | Quick Reference | Time checks |
| Understand architecture | Visualization | Phase diagrams |
| Add new feature | Complete Path | Architecture summary |
| Check status | Summary | Status tables |
| Get overview | Review | All sections |

---

## 🔄 Document Updates

**Last updated:** 2025-10-11

**Documents created:**
- ✅ DIAGNOSTIC_PATH_REVIEW.md
- ✅ SOURCE_SINK_DIAGNOSTIC_PATH.md
- ✅ DIAGNOSTIC_SUMMARY.md
- ✅ DIAGNOSTIC_VISUALIZATION.md
- ✅ DIAGNOSTIC_QUICK_REFERENCE.md
- ✅ DIAGNOSTIC_INDEX.md (this file)

**Next updates:**
- UI integration documentation (when completed)
- Enhanced diagnostic panel (future feature)

---

## 📞 Support

**Found an issue?**
1. Check [`DIAGNOSTIC_QUICK_REFERENCE.md`](./DIAGNOSTIC_QUICK_REFERENCE.md) first
2. Try commands in [`SOURCE_SINK_DIAGNOSTIC_PATH.md`](./SOURCE_SINK_DIAGNOSTIC_PATH.md)
3. Review flowcharts in [`DIAGNOSTIC_VISUALIZATION.md`](./DIAGNOSTIC_VISUALIZATION.md)

**Still stuck?**
- Review all 14 checkpoints in complete path document
- Check test results
- Examine code locations provided

---

**This diagnostic documentation set covers everything you need to understand, debug, and extend the source/sink recognition and simulation time tracking systems.** ✅
