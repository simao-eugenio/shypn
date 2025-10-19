# Headless Testing - Quick Reference

Test .shy models without GUI - fast and simple!

## Quick Commands

```bash
# Test with shortcuts
./headless glycolysis                    # Fresh Glycolysis (34 transitions)
./headless glycolysis-sources            # With sources (39 transitions)

# Test your model
./headless path/to/model.shy             # Any .shy file

# Options
./headless model.shy -s 100              # 100 steps
./headless model.shy -v                  # Verbose
./headless model.shy -q                  # Quiet

# Multiple models
./headless model1.shy model2.shy model3.shy
```

## What It Tests

✓ Model loads correctly  
✓ All transitions have valid types  
✓ Canvas manager creates successfully  
✓ Simulation controller initializes  
✓ Behaviors are created  
✓ Model structure is analyzed  
✓ Simulation runs and tokens move  

## Output Modes

| Mode | Flag | Shows |
|------|------|-------|
| Normal | (default) | Key steps + summary |
| Verbose | `-v` | Every step + details |
| Quiet | `-q` | Summary only |

## Shortcuts

| Shortcut | Model |
|----------|-------|
| `glycolysis`, `gly` | Glycolysis fresh import |
| `glycolysis-sources`, `gly-src` | Glycolysis with 5 sources |

## Exit Codes

- `0` - All tests passed ✓
- `1` - Some tests failed ✗

Perfect for CI/CD!

## Full Documentation

See [`doc/headless/`](doc/headless/INDEX.md) for complete documentation.

---

**Created:** October 18-19, 2025  
**Purpose:** Quick reference for headless testing command
