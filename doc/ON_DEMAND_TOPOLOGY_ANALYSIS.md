# On-Demand Topology Analysis - Revised Strategy

**Date**: October 19, 2025  
**Status**: 🎯 REVISED DESIGN - USER-CONTROLLED  
**Priority**: HIGH

---

## 🎯 Strategic Revision

### Why NOT Auto-Analysis?

**Original Proposal Issues**:
- ❌ Import from websites is already slow
- ❌ Would add lag to every model load
- ❌ User may not need topology analysis
- ❌ Some analyses not implemented (T-invariants)
- ❌ Results currently unstable/incomplete
- ❌ Wastes resources on models user won't analyze

**Key Insight**: **Let the user decide when to analyze!**

---

## ✅ Revised Approach: On-Demand Analysis

### Core Principle
**Don't analyze until user explicitly requests it**

```
User opens model → No analysis → Fast load ✓
User clicks "Analyze Topology" button → Background analysis → Results displayed
```

---

## 🎨 UI Design

### 1. Topology Tab - Initial State (Default)

```
┌─────────────────────────────────────────────┐
│ Basic │ Visual │ Topology                   │
├─────────────────────────────────────────────┤
│                                             │
│            Topology Analysis                │
│                                             │
│  Topology analysis provides insights into   │
│  network structure, cycles, and properties. │
│                                             │
│  ┌───────────────────────────────────────┐ │
│  │  [🔍 Analyze Topology]               │ │
│  └───────────────────────────────────────┘ │
│                                             │
│  Note: Analysis may take 5-30 seconds for  │
│  large models.                              │
│                                             │
└─────────────────────────────────────────────┘
```

### 2. During Analysis (User Triggered)

```
┌─────────────────────────────────────────────┐
│ Basic │ Visual │ Topology                   │
├─────────────────────────────────────────────┤
│                                             │
│  🔄 Analyzing topology...                   │
│                                             │
│  ┌────────────────────────────────────────┐│
│  │████████░░░░░░░░░░░░░░  45%            ││
│  └────────────────────────────────────────┘│
│                                             │
│  ✓ Cycles: Found 12                        │
│  ✓ Paths: Found 45                         │
│  🔄 P-Invariants: Computing...              │
│  ⏳ Hubs: Pending...                        │
│                                             │
│  [❌ Cancel]                                │
│                                             │
└─────────────────────────────────────────────┘
```

### 3. Analysis Complete

```
┌─────────────────────────────────────────────┐
│ Basic │ Visual │ Topology                   │
├─────────────────────────────────────────────┤
│                                             │
│  ✓ Analysis Complete                        │
│                                             │
│  Cycles                                     │
│  Found 12 cycles containing this place      │
│  Longest: 8 nodes                           │
│  [View Details]                             │
│                                             │
│  Conservation Laws (P-Invariants)           │
│  ⚠️ Not yet implemented                     │
│                                             │
│  Paths                                      │
│  45 paths pass through this place           │
│  [View Details]                             │
│                                             │
│  [🔄 Re-analyze]  [💾 Export Results]       │
│                                             │
└─────────────────────────────────────────────┘
```

### 4. Analysis Timeout/Error

```
┌─────────────────────────────────────────────┐
│ Basic │ Visual │ Topology                   │
├─────────────────────────────────────────────┤
│                                             │
│  ⚠️ Analysis Timeout                        │
│                                             │
│  Network too complex for full analysis      │
│  (exceeded 30 second limit).                │
│                                             │
│  Partial results:                           │
│  ✓ Paths: 45 found                          │
│  ✓ Hubs: Degree 8                           │
│  ⏱ Cycles: Timeout                          │
│  ⏱ P-Invariants: Timeout                    │
│                                             │
│  [🔄 Retry]  [⚙️ Analyze with Limits]       │
│                                             │
└─────────────────────────────────────────────┘
```

---

## 🏗️ Implementation

### Component 1: TopologyAnalysisRunner (NEW - Simpler)

**Location**: `src/shypn/topology/analysis_runner.py`

**Purpose**: Run analysis suite on-demand (triggered by button)

```python
class TopologyAnalysisRunner:
    """Runs topology analysis suite on user demand.
    
    Does NOT auto-run. Only executes when user clicks button.
    Runs in background thread to keep UI responsive.
    """
    
    def __init__(self):
        self.current_analysis = None
        self.results = {}
    
    def analyze(self, model, element_id, element_type,
                on_progress=None, on_complete=None, on_error=None):
        """Run analysis suite for an element.
        
        Args:
            model: DocumentModel to analyze
            element_id: ID of place/transition/arc
            element_type: 'place', 'transition', or 'arc'
            on_progress: Callback(analyzer_name, status, progress)
            on_complete: Callback(results_dict)
            on_error: Callback(error)
        """
        # Create worker thread
        worker = threading.Thread(
            target=self._run_analysis_suite,
            args=(model, element_id, element_type),
            daemon=True
        )
        
        self.current_analysis = worker
        worker.start()
    
    def cancel(self):
        """Cancel ongoing analysis."""
        if self.current_analysis:
            # Set cancellation flag
            self._cancelled = True
    
    def _run_analysis_suite(self, model, element_id, element_type):
        """Run all applicable analyzers."""
        results = {}
        
        # Run each analyzer with timeout
        analyzers = self._get_analyzers_for_type(element_type)
        
        for analyzer_name, analyzer_class, timeout in analyzers:
            if self._cancelled:
                break
            
            try:
                # Run with timeout
                result = self._run_with_timeout(
                    analyzer_class, model, element_id, timeout
                )
                results[analyzer_name] = result
                
                # Report progress
                if self.on_progress:
                    GLib.idle_add(self.on_progress, analyzer_name, 'complete', result)
            
            except TimeoutError:
                results[analyzer_name] = {'status': 'timeout'}
                if self.on_progress:
                    GLib.idle_add(self.on_progress, analyzer_name, 'timeout', None)
            
            except Exception as e:
                results[analyzer_name] = {'status': 'error', 'error': str(e)}
                if self.on_progress:
                    GLib.idle_add(self.on_progress, analyzer_name, 'error', str(e))
        
        # Report completion
        if self.on_complete:
            GLib.idle_add(self.on_complete, results)
    
    def _get_analyzers_for_type(self, element_type):
        """Get list of analyzers to run for element type."""
        if element_type == 'place':
            return [
                ('cycles', CycleAnalyzer, 10),
                ('paths', PathAnalyzer, 10),
                ('p_invariants', PInvariantAnalyzer, 20),  # May not be implemented
                ('hubs', HubAnalyzer, 5),
            ]
        elif element_type == 'transition':
            return [
                ('cycles', CycleAnalyzer, 10),
                ('paths', PathAnalyzer, 10),
                ('t_invariants', TInvariantAnalyzer, 20),  # Not implemented yet
                ('liveness', LivenessAnalyzer, 15),
            ]
        else:  # arc
            return [
                ('connectivity', ConnectivityAnalyzer, 5),
                ('critical_path', CriticalPathAnalyzer, 10),
            ]
```

### Component 2: TopologyTabLoader - Add Button Handler

**Modify**: `src/shypn/ui/topology_tab_loader.py`

**Changes**:
1. Add "Analyze Topology" button to UI
2. Handle button click → start analysis
3. Update UI with progress/results
4. Handle cancel button

```python
class PlaceTopologyTabLoader(TopologyTabLoader):
    
    def __init__(self, model, element_id, ui_dir=None):
        super().__init__(model, element_id, ui_dir)
        self.runner = None
        self.results = None
        self._show_initial_state()
    
    def _show_initial_state(self):
        """Show 'Analyze Topology' button."""
        # Get button from UI
        self.analyze_button = self.builder.get_object('analyze_button')
        if self.analyze_button:
            self.analyze_button.connect('clicked', self._on_analyze_clicked)
            self.analyze_button.set_sensitive(True)
        
        # Hide results area, show button area
        self._switch_to_view('initial')
    
    def _on_analyze_clicked(self, button):
        """User clicked 'Analyze Topology' button."""
        # Disable button during analysis
        button.set_sensitive(False)
        
        # Show progress view
        self._switch_to_view('analyzing')
        
        # Create runner
        from shypn.topology.analysis_runner import TopologyAnalysisRunner
        self.runner = TopologyAnalysisRunner()
        
        # Start analysis
        self.runner.analyze(
            model=self.model,
            element_id=self.element_id,
            element_type='place',
            on_progress=self._on_analysis_progress,
            on_complete=self._on_analysis_complete,
            on_error=self._on_analysis_error
        )
    
    def _on_analysis_progress(self, analyzer_name, status, data):
        """Update progress UI (called from worker thread via GLib.idle_add)."""
        # Update progress bar
        progress = self._calculate_progress()
        self.progress_bar.set_fraction(progress)
        
        # Update analyzer status
        label = self.builder.get_object(f'{analyzer_name}_status_label')
        if label:
            if status == 'complete':
                label.set_markup(f"✓ {analyzer_name}: Complete")
            elif status == 'timeout':
                label.set_markup(f"⏱ {analyzer_name}: Timeout")
            elif status == 'error':
                label.set_markup(f"✗ {analyzer_name}: Error")
    
    def _on_analysis_complete(self, results):
        """Analysis finished (called from worker thread via GLib.idle_add)."""
        self.results = results
        
        # Switch to results view
        self._switch_to_view('results')
        
        # Populate with results
        self._display_results(results)
        
        # Enable re-analyze button
        self.reanalyze_button.set_sensitive(True)
    
    def _on_analysis_error(self, error):
        """Analysis failed (called from worker thread via GLib.idle_add)."""
        self._switch_to_view('error')
        self.error_label.set_text(f"Analysis failed: {error}")
    
    def _switch_to_view(self, view_name):
        """Switch between initial/analyzing/results/error views."""
        # Hide all views
        for view in ['initial', 'analyzing', 'results', 'error']:
            widget = self.builder.get_object(f'{view}_view')
            if widget:
                widget.set_visible(view == view_name)
```

---

## 📁 Updated UI Files

### topology_tab_place.ui - Add Views

```xml
<?xml version="1.0" encoding="UTF-8"?>
<interface>
  <object class="GtkBox" id="place_topology_tab_root">
    <property name="orientation">vertical</property>
    
    <!-- Initial View: Analyze Button -->
    <child>
      <object class="GtkBox" id="initial_view">
        <property name="visible">True</property>
        <property name="orientation">vertical</property>
        <property name="spacing">12</property>
        <property name="margin">24</property>
        
        <child>
          <object class="GtkLabel">
            <property name="visible">True</property>
            <property name="label">Topology Analysis</property>
            <property name="xalign">0.5</property>
            <attributes>
              <attribute name="weight" value="bold"/>
              <attribute name="scale" value="1.2"/>
            </attributes>
          </object>
        </child>
        
        <child>
          <object class="GtkLabel">
            <property name="visible">True</property>
            <property name="label">Topology analysis provides insights into network structure, cycles, and properties.</property>
            <property name="wrap">True</property>
            <property name="xalign">0.5</property>
          </object>
        </child>
        
        <child>
          <object class="GtkButton" id="analyze_button">
            <property name="visible">True</property>
            <property name="label">🔍 Analyze Topology</property>
            <property name="halign">center</property>
            <style>
              <class name="suggested-action"/>
            </style>
          </object>
        </child>
        
        <child>
          <object class="GtkLabel">
            <property name="visible">True</property>
            <property name="label">Note: Analysis may take 5-30 seconds for large models.</property>
            <property name="wrap">True</property>
            <property name="xalign">0.5</property>
            <attributes>
              <attribute name="style" value="italic"/>
              <attribute name="scale" value="0.9"/>
            </attributes>
          </object>
        </child>
      </object>
    </child>
    
    <!-- Analyzing View: Progress -->
    <child>
      <object class="GtkBox" id="analyzing_view">
        <property name="visible">False</property>
        <property name="orientation">vertical</property>
        <property name="spacing">12</property>
        <property name="margin">24</property>
        
        <child>
          <object class="GtkLabel">
            <property name="visible">True</property>
            <property name="label">🔄 Analyzing topology...</property>
          </object>
        </child>
        
        <child>
          <object class="GtkProgressBar" id="progress_bar">
            <property name="visible">True</property>
            <property name="show-text">True</property>
          </object>
        </child>
        
        <child>
          <object class="GtkLabel" id="cycles_status_label">
            <property name="visible">True</property>
            <property name="label">⏳ Cycles: Pending...</property>
            <property name="xalign">0</property>
          </object>
        </child>
        
        <child>
          <object class="GtkLabel" id="paths_status_label">
            <property name="visible">True</property>
            <property name="label">⏳ Paths: Pending...</property>
            <property name="xalign">0</property>
          </object>
        </child>
        
        <child>
          <object class="GtkButton" id="cancel_button">
            <property name="visible">True</property>
            <property name="label">❌ Cancel</property>
            <property name="halign">center</property>
          </object>
        </child>
      </object>
    </child>
    
    <!-- Results View: Display Results -->
    <child>
      <object class="GtkScrolledWindow" id="results_view">
        <property name="visible">False</property>
        <property name="hscrollbar-policy">never</property>
        <property name="vscrollbar-policy">automatic</property>
        
        <child>
          <object class="GtkBox" id="results_container">
            <property name="visible">True</property>
            <property name="orientation">vertical</property>
            <property name="spacing">12</property>
            <property name="margin">12</property>
            
            <!-- Results populated dynamically -->
          </object>
        </child>
      </object>
    </child>
    
    <!-- Error View: Show Error -->
    <child>
      <object class="GtkBox" id="error_view">
        <property name="visible">False</property>
        <property name="orientation">vertical</property>
        <property name="spacing">12</property>
        <property name="margin">24</property>
        
        <child>
          <object class="GtkLabel">
            <property name="visible">True</property>
            <property name="label">⚠️ Analysis Error</property>
          </object>
        </child>
        
        <child>
          <object class="GtkLabel" id="error_label">
            <property name="visible">True</property>
            <property name="wrap">True</property>
          </object>
        </child>
        
        <child>
          <object class="GtkButton" id="retry_button">
            <property name="visible">True</property>
            <property name="label">🔄 Retry</property>
            <property name="halign">center</property>
          </object>
        </child>
      </object>
    </child>
  </object>
</interface>
```

---

## 🎯 Key Benefits

### 1. **User Control** ✓
- User decides when to analyze
- No automatic lag on import
- Can skip analysis entirely if not needed

### 2. **Fast Model Loading** ✓
- Import/open is fast (no analysis)
- User can start working immediately
- Analysis only when requested

### 3. **Clear Feedback** ✓
- Button makes it obvious ("Analyze Topology")
- Progress bar shows what's happening
- Can cancel if taking too long

### 4. **Handles Incomplete Features** ✓
- Can show "Not implemented" for T-invariants
- Graceful degradation for missing analyzers
- Easy to add new analyzers later

### 5. **Handles Instability** ✓
- Timeout after 30 seconds
- Show partial results if some analyzers fail
- User can retry with different settings

---

## 📊 User Experience Comparison

| Scenario | Auto-Analysis (Original) | On-Demand (Revised) |
|----------|-------------------------|---------------------|
| **Import model** | Slow (analysis runs) ❌ | **Fast (no analysis)** ✓ |
| **Open dialog** | Instant if cached ✓ | **Instant (always)** ✓ |
| **View topology** | Auto-available ✓ | **Click button** (intentional) |
| **Unstable analysis** | Confusing (shows errors) ❌ | **User knows they triggered it** ✓ |
| **Don't need topology** | Wasted resources ❌ | **No waste** ✓ |
| **Large model** | Auto-lag ❌ | **User chooses when** ✓ |

---

## 🔧 Implementation Effort

### Phase 1: Add Button & Runner (3 hours)
1. Create `TopologyAnalysisRunner` class (1h)
2. Update topology tab UI files with button (1h)
3. Wire button to runner (1h)

### Phase 2: Progress & Results Display (2 hours)
1. Progress bar updates (0.5h)
2. Results display (1h)
3. Error handling (0.5h)

### Phase 3: Polish (1 hour)
1. Cancel functionality (0.5h)
2. Retry with limits (0.5h)

**Total: ~6 hours** (half the original proposal)

---

## ✅ Success Criteria

### User Experience
- ✅ Model import/open is **fast** (no auto-analysis)
- ✅ Dialog opens **instantly** (always <50ms)
- ✅ **Clear button** to trigger analysis when wanted
- ✅ **Progress visible** during analysis
- ✅ Can **cancel** if taking too long
- ✅ **Graceful handling** of incomplete/failed analyzers

### Technical
- ✅ Analysis runs in background thread
- ✅ UI remains responsive
- ✅ Timeout after 30 seconds
- ✅ Partial results on timeout
- ✅ No automatic resource waste

---

## 🎯 Summary

### What Changed from Original Proposal

**REMOVED**:
- ❌ Auto-analysis on model load
- ❌ Background analysis manager (too complex)
- ❌ Automatic cache population
- ❌ Status bar progress

**ADDED**:
- ✅ "Analyze Topology" button (explicit user action)
- ✅ Simpler on-demand runner
- ✅ Clear progress UI in dialog
- ✅ User control over when analysis runs

**Why This is Better**:
1. **Faster imports** - no auto-lag
2. **User control** - analyze only when needed
3. **Simpler code** - less infrastructure
4. **Handles instability** - user triggers explicitly
5. **Less resource waste** - only analyze when requested

---

## 📝 Next Steps

1. **Approve revised design** ✓
2. **Implement Phase 1** (add button & runner) - 3 hours
3. **Test with Glycolysis model** - verify button works
4. **Implement Phase 2** (progress & results) - 2 hours
5. **Polish & deploy** - 1 hour

**Total implementation**: ~6 hours

---

**This approach respects user choice, keeps imports fast, and handles incomplete/unstable features gracefully.** 🎯
