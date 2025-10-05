# Simulation Quick Reference Guide

**Version**: October 2025  
**For**: shypn Petri Net Simulator

---

## 🎮 Simulation Controls

### Run Button [R]
- **Function**: Start continuous simulation
- **Behavior**: Fires transitions automatically until deadlock or Stop pressed
- **Console**: `▶️ [RUN] Starting simulation at t=X.XXX`

### Step Button [P]
- **Function**: Execute one simulation step (0.1 seconds)
- **Use case**: Manual control, debugging, step-by-step analysis

### Stop Button [S]
- **Function**: Pause simulation
- **Behavior**: Finishes current step then stops
- **Console**: `⏸️ [STOP] Stopping simulation at t=X.XXX`

### Reset Button [T]
- **Function**: Reset to initial marking
- **Behavior**: Restores all places to initial token count, time returns to 0.0

---

## 🔥 Transition Types & Firing

### Immediate Transitions
- **Fires**: Instantly (zero time delay)
- **Use**: Logic, routing, instant token movement
- **Console**: `⚡ [IMMEDIATE] T1 fired instantly at t=X.XXX`
- **Behavior**: ALL enabled immediate transitions fire before any other type

**Example**: Token routing, conditional logic
```
P1 → T1(immediate) → P2 → T2(immediate) → P3
Both T1 and T2 fire in same step (<1ms)
```

### Timed Transitions (TPN)
- **Fires**: After specified delay (deterministic)
- **Parameters**: `earliest` and `latest` time bounds
- **Use**: Scheduled events, time-constrained processes
- **Console**: `🔥 [FIRED] T1 at t=X.XXX`
- **Default**: 1.0 second delay if no rate specified

**Example**: Manufacturing delay, transport time
```
P1 → T1(timed, delay=2.0) → P2
Fires exactly 2.0 seconds after T1 enabled
```

### Stochastic Transitions (SPN)
- **Fires**: After exponentially-sampled delay (random)
- **Parameters**: `rate` (λ) and `max_burst`
- **Use**: Random processes, failures, arrivals
- **Console**: `🔥 [FIRED] T1 at t=X.XXX`
- **Distribution**: Exp(λ), mean delay = 1/λ

**Example**: Random arrivals (λ=0.5 means avg 2 seconds)
```
P1 → T1(stochastic, rate=0.5) → P2
Fires after random delay (mean=2.0s)
```

### Continuous Transitions (HPN)
- **Fires**: Continuously (fluid flow)
- **Parameters**: `rate` function
- **Use**: Continuous processes, fluid dynamics
- **Console**: No individual firing message (continuous)
- **Integration**: Euler method with small time steps

**Example**: Fluid tank filling
```
P1 → T1(continuous, rate=0.5) → P2
Transfers 0.5 tokens per second continuously
```

---

## ⏱️ Time Control

### Simulation Time
- **Starts**: t = 0.0
- **Advances**: 0.1 seconds per step (when using Run)
- **Display**: Console messages show current time
- **Precision**: ±0.1 seconds for timed transitions

### Time Behavior
- **Immediate transitions**: Fire at same time they're enabled (zero delay)
- **Timed transitions**: Fire when `elapsed ≥ delay`
- **Stochastic transitions**: Fire when `current_time ≥ scheduled_time`
- **Continuous transitions**: Integrate every step

---

## 🚦 Simulation States

### Running
- **Indicator**: Continuous canvas updates
- **Console**: Step messages, firing notifications
- **Behavior**: Automatically fires enabled transitions

### Stopped (Paused)
- **Indicator**: Canvas static
- **Console**: `⏸️ [STOP]` message
- **Behavior**: Can resume with Run, or advance with Step

### Deadlocked
- **Indicator**: Simulation stops automatically
- **Console**: `⏸️ [DEADLOCK] Simulation stopped at t=X.XXX`
- **Cause**: No transitions can fire (no tokens or timing constraints not met)
- **Recovery**: Press Reset to restore initial state

---

## 📊 Console Messages Guide

### Success Messages
- `▶️ [RUN]` - Simulation started
- `⚡ [IMMEDIATE] T1 fired` - Immediate transition fired
- `🔥 [FIRED] T1` - Timed/stochastic transition fired

### Status Messages
- `⏸️ [STOP]` - User stopped simulation
- `⏸️ [DEADLOCK]` - No transitions can fire (normal end state)

### Warning Messages
- `⚠️ [WARNING] Immediate transition loop limit reached` - Possible infinite loop in model
- `[TimedBehavior] WARNING: Transition T1 has no rate` - Using default delay

---

## 🐛 Troubleshooting

### "Simulation doesn't start"
**Problem**: Press Run but nothing happens  
**Check**:
1. Do transitions have input tokens?
2. Are timed transitions configured with delays?
3. Check console for error messages

### "Deadlock immediately"
**Problem**: Simulation stops right after starting  
**Cause**: No enabled transitions (no tokens in input places)  
**Fix**: Add tokens to input places, or check arc connections

### "Timed transition never fires"
**Problem**: Waiting a long time but transition doesn't fire  
**Check**:
1. Is delay too large? (Default is 1.0 second)
2. Are there enough tokens in input places?
3. Check transition properties dialog

### "Warning: Immediate loop limit"
**Problem**: See warning about 1000 iteration limit  
**Cause**: Immediate transitions forming infinite loop  
**Example**: T1→P1→T2→P2→T1 (cycle of immediate transitions)  
**Fix**: Add timed transition to break cycle, or redesign model

---

## 💡 Best Practices

### Model Design
1. **Use immediate for logic** - Zero-time decisions and routing
2. **Use timed for delays** - Known, deterministic delays
3. **Use stochastic for random** - Unknown, random delays
4. **Use continuous for flow** - Fluid-like continuous processes

### Simulation
1. **Start with Step** - Understand model behavior before using Run
2. **Watch console** - Messages show what's happening
3. **Use Reset often** - Return to initial state for repeated tests
4. **Check for deadlock** - Ensure model can reach desired end state

### Performance
1. **Limit immediate chains** - Very long chains (100+) may slow startup
2. **Use appropriate delays** - Very small delays increase CPU usage
3. **Consider model size** - Models with 100+ transitions may be slower

---

## 📐 Example Workflows

### Testing a Timed Transition
```
1. Create model: P1(1 token) → T1(timed, 1.0s) → P2
2. Press Run
3. Wait ~1 second
4. Observe: 🔥 [FIRED] T1 at t=1.000
5. Observe: ⏸️ [DEADLOCK] (P1 empty)
6. Press Reset
7. Repeat as needed
```

### Debugging with Step Mode
```
1. Press Step (not Run)
2. Observe token movement
3. Read console messages
4. Press Step again
5. Repeat until understand behavior
6. Then use Run for continuous execution
```

### Analyzing Cyclic Behavior
```
1. Create cycle: P1 → T1 → P2 → T2 → P1
2. Add initial token to P1
3. Press Run
4. Observe continuous cycling
5. Press Stop when ready
6. Check analysis panels for statistics
```

---

## 🔧 Advanced Features

### Conflict Resolution
When multiple transitions are enabled:
- **Priority**: Higher priority fires first
- **Random**: If same priority, random selection

### Enablement Tracking
- Each transition tracks when it became enabled
- Used for timing calculations
- Cleared when transition fires or becomes disabled

### Data Collection
- Automatically tracks place markings over time
- Records transition firings
- Available in analysis panels

---

## 📚 Further Reading

- **Legacy Analysis**: `doc/LEGACY_FIRING_SYSTEM_ANALYSIS.md`
- **Floating-Point Fix**: `doc/TIMED_TRANSITION_FLOATING_POINT_FIX.md`
- **Behavior Details**: `doc/TIMED_TRANSITION_BEHAVIOR_EXPLAINED.md`
- **Complete Fix**: `doc/TIMED_TRANSITION_RUN_STOP_FIX.md`

---

**Last Updated**: October 5, 2025  
**Version**: 1.0 - Initial Release
