# Topology Analysis → Report Panel Integration

## 📋 Requirements Summary

**Goal**: Topology analysis results should be:
1. **Aggregated into metadata** for Report Panel consumption
2. **Formatted for final printable reports**
3. **Cached and reusable** across sessions
4. **Summarized** for quick overview

---

## 🏗️ Architecture: Unified Reporting System

```
┌─────────────────────────────────────────────────────────────────┐
│                    TOPOLOGY ANALYSIS FLOW                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────┐
        │   12 Topology Analyzers             │
        │   (P-Inv, T-Inv, Siphons, ...)     │
        └─────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────┐
        │   Result Aggregator                 │
        │   • Per-element properties          │
        │   • Organized by place/transition   │
        └─────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────┐
        │   Metadata Generator                │
        │   • Model summary statistics        │
        │   • Key findings & warnings         │
        │   • Performance metrics             │
        └─────────────────────────────────────┘
                              │
                    ┌─────────┴──────────┐
                    ▼                    ▼
        ┌──────────────────┐   ┌──────────────────┐
        │  METADATA FILE   │   │  REPORT PANEL    │
        │  .topology.json  │──▶│  Consumption     │
        └──────────────────┘   └──────────────────┘
                    │                    │
                    │                    ▼
                    │          ┌──────────────────┐
                    │          │  Report Builder  │
                    │          │  • HTML Report   │
                    │          │  • PDF Export    │
                    └─────────▶│  • Print Format  │
                               └──────────────────┘
```

---

## 📄 Metadata File Format

### File: `model_name.topology.json`

**Location**: `workspace/topology_cache/model_hash.topology.json`

**Structure**:
```json
{
    "metadata": {
        "model_name": "glycolysis.xml",
        "model_hash": "abc123def456",
        "analysis_date": "2025-10-29T14:30:00",
        "analysis_duration": 12.5,
        "shypn_version": "1.0.0"
    },
    
    "model_summary": {
        "places": 25,
        "transitions": 18,
        "arcs": 67,
        "initial_tokens": 150
    },
    
    "topology_summary": {
        "structural": {
            "p_invariants": {
                "count": 5,
                "coverage": 0.92,
                "status": "success"
            },
            "t_invariants": {
                "count": 3,
                "coverage": 0.88,
                "status": "success"
            },
            "siphons": {
                "count": 2,
                "empty_siphons": 0,
                "status": "blocked",
                "reason": "model_too_large"
            },
            "traps": {
                "count": 3,
                "marked_traps": 2,
                "status": "success"
            }
        },
        "graph": {
            "cycles": {
                "count": 12,
                "longest": 8,
                "status": "success"
            },
            "hubs": {
                "count": 4,
                "max_degree": 9,
                "status": "success"
            },
            "paths": {
                "count": 45,
                "status": "success"
            }
        },
        "behavioral": {
            "reachability": {
                "states": 8543,
                "is_bounded": true,
                "deadlock_states": 0,
                "status": "success"
            },
            "liveness": {
                "is_live": true,
                "dead_transitions": 0,
                "status": "success"
            },
            "boundedness": {
                "is_bounded": true,
                "unbounded_places": [],
                "status": "success"
            },
            "deadlocks": {
                "has_deadlock": false,
                "deadlock_type": "none",
                "status": "success"
            },
            "fairness": {
                "is_fair": true,
                "unfair_transitions": [],
                "status": "success"
            }
        }
    },
    
    "key_findings": [
        {
            "severity": "info",
            "category": "structural",
            "message": "Model has 5 P-invariants covering 92% of places",
            "details": "Good conservation properties"
        },
        {
            "severity": "warning",
            "category": "graph",
            "message": "4 hub transitions detected",
            "details": "T1 (degree=9), T5 (degree=7), T8 (degree=6), T12 (degree=5)"
        },
        {
            "severity": "success",
            "category": "behavioral",
            "message": "Model is live, bounded, and deadlock-free",
            "details": "All transitions can fire infinitely often"
        }
    ],
    
    "warnings": [
        {
            "analyzer": "siphons",
            "message": "Analysis blocked due to model size (25 places > 20 limit)",
            "suggestion": "Use batch analysis or smaller subnetwork"
        }
    ],
    
    "per_element_data": {
        "places": {
            "P1": {
                "name": "ATP",
                "id": 1,
                "p_invariants": [
                    {"invariant_id": 1, "weight": 1, "expression": "ATP + 2*ADP"},
                    {"invariant_id": 3, "weight": 2, "expression": "2*ATP + NADH"}
                ],
                "in_siphons": [],
                "in_traps": [{"trap_id": 1, "is_marked": true}],
                "boundedness": "bounded",
                "can_deadlock": false
            },
            "P2": {...}
        },
        "transitions": {
            "T1": {
                "name": "Hexokinase",
                "id": 1,
                "t_invariants": [
                    {"invariant_id": 1, "weight": 1, "sequence": "T1 → T2 → T3"}
                ],
                "is_hub": true,
                "hub_degree": 9,
                "in_cycles": [
                    {"cycle_id": 1, "length": 5},
                    {"cycle_id": 4, "length": 8}
                ],
                "liveness_level": "L3",
                "liveness_description": "Live - can fire infinitely often",
                "fairness": "fair"
            },
            "T2": {...}
        }
    },
    
    "performance_metrics": {
        "analysis_times": {
            "p_invariants": 0.45,
            "t_invariants": 0.38,
            "cycles": 0.92,
            "hubs": 0.12,
            "paths": 0.67,
            "boundedness": 0.05,
            "reachability": 8.34,
            "liveness": 1.23,
            "deadlocks": 0.78,
            "fairness": 0.34
        },
        "total_time": 12.5,
        "cached": false
    }
}
```

---

## 🔧 Implementation Components

### 1. **Metadata Generator**

**File**: `src/shypn/topology/reporting/metadata_generator.py`

```python
class TopologyMetadataGenerator:
    """Generate metadata file from topology analysis results."""
    
    def generate_metadata(
        self,
        model,
        all_results: Dict[str, AnalysisResult],
        element_data: Dict,
        output_path: str
    ) -> Dict:
        """Generate complete metadata file.
        
        Args:
            model: PetriNetModel instance
            all_results: Raw analyzer results
            element_data: Aggregated per-element data
            output_path: Where to save .topology.json file
        
        Returns:
            Metadata dictionary (also saved to file)
        """
        metadata = {
            "metadata": self._build_metadata_section(model),
            "model_summary": self._build_model_summary(model),
            "topology_summary": self._build_topology_summary(all_results),
            "key_findings": self._extract_key_findings(all_results),
            "warnings": self._extract_warnings(all_results),
            "per_element_data": element_data,
            "performance_metrics": self._build_performance_metrics(all_results)
        }
        
        # Save to file
        with open(output_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        return metadata
    
    def _extract_key_findings(self, all_results: Dict) -> List[Dict]:
        """Extract most important findings for summary."""
        findings = []
        
        # P-Invariants
        if 'p_invariants' in all_results:
            result = all_results['p_invariants']
            if result.success:
                count = result.data.get('count', 0)
                coverage = result.data.get('coverage_ratio', 0)
                findings.append({
                    "severity": "info" if coverage > 0.8 else "warning",
                    "category": "structural",
                    "message": f"Model has {count} P-invariants covering {coverage:.0%} of places",
                    "details": "Good conservation properties" if coverage > 0.8 else "Some places not conserved"
                })
        
        # Hubs
        if 'hubs' in all_results:
            result = all_results['hubs']
            if result.success:
                hubs = result.data.get('hubs', [])
                if len(hubs) > 0:
                    hub_list = ', '.join([f"{h['name']} (degree={h['degree']})" for h in hubs[:3]])
                    findings.append({
                        "severity": "warning",
                        "category": "graph",
                        "message": f"{len(hubs)} hub transitions detected",
                        "details": hub_list
                    })
        
        # Liveness & Deadlocks
        liveness_ok = False
        deadlock_ok = False
        
        if 'liveness' in all_results:
            result = all_results['liveness']
            if result.success:
                liveness_ok = result.data.get('is_live', False)
        
        if 'deadlocks' in all_results:
            result = all_results['deadlocks']
            if result.success:
                deadlock_ok = not result.data.get('has_deadlock', True)
        
        if liveness_ok and deadlock_ok:
            findings.append({
                "severity": "success",
                "category": "behavioral",
                "message": "Model is live and deadlock-free",
                "details": "All transitions can fire infinitely often"
            })
        
        return findings
```

---

### 2. **Report Panel Integration**

**File**: `src/shypn/ui/panels/report/topology_section.py`

```python
class TopologyReportSection:
    """Topology analysis section in Report Panel."""
    
    def __init__(self):
        self.section = self._build_section()
    
    def load_topology_metadata(self, metadata_path: str):
        """Load topology metadata and update display.
        
        Args:
            metadata_path: Path to .topology.json file
        """
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        self._display_summary(metadata['topology_summary'])
        self._display_key_findings(metadata['key_findings'])
        self._display_warnings(metadata['warnings'])
    
    def _build_section(self) -> Gtk.Box:
        """Build the topology section UI."""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        
        # Header
        header = Gtk.Label()
        header.set_markup("<b>Topology Analysis Summary</b>")
        box.pack_start(header, False, False, 0)
        
        # Summary table
        self.summary_table = Gtk.Grid()
        box.pack_start(self.summary_table, False, False, 0)
        
        # Key findings
        self.findings_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box.pack_start(self.findings_box, False, False, 0)
        
        return box
    
    def _display_summary(self, summary: Dict):
        """Display topology summary statistics."""
        row = 0
        
        # Structural
        if 'structural' in summary:
            self._add_category_header("Structural Properties", row)
            row += 1
            
            for analyzer, data in summary['structural'].items():
                status_icon = "✓" if data['status'] == 'success' else "⚠️"
                label = Gtk.Label(label=f"{status_icon} {analyzer.replace('_', ' ').title()}")
                value = Gtk.Label(label=f"{data.get('count', 'N/A')}")
                
                self.summary_table.attach(label, 0, row, 1, 1)
                self.summary_table.attach(value, 1, row, 1, 1)
                row += 1
        
        # Similar for graph and behavioral...
    
    def _display_key_findings(self, findings: List[Dict]):
        """Display key findings as colored badges."""
        for finding in findings:
            finding_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            
            # Severity icon
            icons = {
                'success': '✓',
                'info': 'ℹ️',
                'warning': '⚠️',
                'error': '⚠️'
            }
            icon_label = Gtk.Label(label=icons.get(finding['severity'], ''))
            finding_box.pack_start(icon_label, False, False, 0)
            
            # Message
            msg_label = Gtk.Label(label=finding['message'])
            msg_label.set_line_wrap(True)
            finding_box.pack_start(msg_label, True, True, 0)
            
            self.findings_box.pack_start(finding_box, False, False, 6)
```

---

### 3. **Report Builder (Print/Export)**

**File**: `src/shypn/reporting/report_builder.py`

```python
class TopologyReportBuilder:
    """Build printable/exportable reports from topology metadata."""
    
    def generate_html_report(self, metadata: Dict, output_path: str):
        """Generate HTML report for printing/viewing.
        
        Args:
            metadata: Topology metadata dict
            output_path: Where to save HTML file
        """
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Topology Analysis Report - {metadata['metadata']['model_name']}</title>
    <style>
        {self._get_css_styles()}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Topology Analysis Report</h1>
            <h2>{metadata['metadata']['model_name']}</h2>
            <p class="meta">Generated: {metadata['metadata']['analysis_date']}</p>
        </header>
        
        <section class="summary">
            <h2>Model Summary</h2>
            {self._build_model_summary_html(metadata['model_summary'])}
        </section>
        
        <section class="findings">
            <h2>Key Findings</h2>
            {self._build_findings_html(metadata['key_findings'])}
        </section>
        
        <section class="topology">
            <h2>Topology Analysis Results</h2>
            {self._build_topology_tables_html(metadata['topology_summary'])}
        </section>
        
        <section class="elements">
            <h2>Per-Element Properties</h2>
            {self._build_element_tables_html(metadata['per_element_data'])}
        </section>
        
        <footer>
            <p>Generated by Shypn v{metadata['metadata']['shypn_version']}</p>
            <p>Analysis time: {metadata['performance_metrics']['total_time']:.2f}s</p>
        </footer>
    </div>
</body>
</html>
"""
        
        with open(output_path, 'w') as f:
            f.write(html)
    
    def generate_pdf_report(self, metadata: Dict, output_path: str):
        """Generate PDF report (via HTML → PDF conversion)."""
        # Generate HTML first
        html_path = output_path.replace('.pdf', '.html')
        self.generate_html_report(metadata, html_path)
        
        # Convert to PDF using weasyprint or similar
        try:
            from weasyprint import HTML
            HTML(html_path).write_pdf(output_path)
        except ImportError:
            print("Install weasyprint for PDF export: pip install weasyprint")
```

---

## 🔄 Workflow Integration

### When User Analyzes a Model:

```python
# 1. Run all topology analyzers
all_results = {}
for analyzer_name in ANALYZERS:
    analyzer = create_analyzer(analyzer_name, model)
    all_results[analyzer_name] = analyzer.analyze()

# 2. Aggregate to per-element view
aggregator = TopologyResultAggregator()
element_data = aggregator.aggregate(all_results)

# 3. Generate metadata file
metadata_gen = TopologyMetadataGenerator()
metadata = metadata_gen.generate_metadata(
    model=model,
    all_results=all_results,
    element_data=element_data,
    output_path=f"workspace/topology_cache/{model_hash}.topology.json"
)

# 4. Update Report Panel
report_panel.load_topology_section(metadata)

# 5. Enable report export
# User can now:
# - View summary in Report Panel
# - Export to HTML/PDF
# - Print formatted report
```

---

## 📊 Report Panel Display

**Visual Layout**:

```
┌────────────────────────────────────────────────────────────┐
│ REPORT PANEL                                    [Export ▼] │
├────────────────────────────────────────────────────────────┤
│                                                             │
│ ┌─ Topology Analysis Summary ──────────────────────────┐  │
│ │                                                        │  │
│ │ ✓ Analysis Complete (12.5s)                          │  │
│ │ Model: glycolysis.xml (25 places, 18 transitions)    │  │
│ │                                                        │  │
│ │ Structural Properties                                 │  │
│ │   ✓ P-Invariants:     5 (92% coverage)               │  │
│ │   ✓ T-Invariants:     3 (88% coverage)               │  │
│ │   ⚠️ Siphons:          BLOCKED (model too large)      │  │
│ │   ✓ Traps:            3 (2 marked)                   │  │
│ │                                                        │  │
│ │ Graph Properties                                      │  │
│ │   ✓ Cycles:           12 (longest: 8)                │  │
│ │   ⚠️ Hubs:             4 transitions                  │  │
│ │   ✓ Paths:            45                             │  │
│ │                                                        │  │
│ │ Behavioral Properties                                 │  │
│ │   ✓ Reachability:     8,543 states (bounded)         │  │
│ │   ✓ Liveness:         LIVE (all transitions)         │  │
│ │   ✓ Deadlocks:        NONE detected                  │  │
│ │   ✓ Fairness:         FAIR system                    │  │
│ │                                                        │  │
│ └────────────────────────────────────────────────────────┘  │
│                                                             │
│ ┌─ Key Findings ──────────────────────────────────────┐  │
│ │                                                        │  │
│ │ ✓ Model is live, bounded, and deadlock-free          │  │
│ │   All transitions can fire infinitely often           │  │
│ │                                                        │  │
│ │ ℹ️  5 P-invariants covering 92% of places             │  │
│ │   Good conservation properties                        │  │
│ │                                                        │  │
│ │ ⚠️  4 hub transitions detected                         │  │
│ │   T1 (degree=9), T5 (degree=7), T8, T12              │  │
│ │                                                        │  │
│ └────────────────────────────────────────────────────────┘  │
│                                                             │
│ [View Detailed Report] [Export HTML] [Export PDF] [Print] │
│                                                             │
└────────────────────────────────────────────────────────────┘
```

---

## 📝 Implementation Plan

### Phase 1: Metadata Generation (2-3 hours)
1. Create `TopologyMetadataGenerator` class
2. Implement metadata file format
3. Save to `workspace/topology_cache/`
4. Test with various models

### Phase 2: Report Panel Integration (3-4 hours)
1. Create `TopologyReportSection` widget
2. Add to existing Report Panel
3. Load and display metadata
4. Add "Refresh Topology" button

### Phase 3: Report Export (2-3 hours)
1. Create `TopologyReportBuilder` class
2. Implement HTML generation
3. Add PDF export (optional)
4. Add Print functionality

### Total Time: 7-10 hours

---

## ✅ Benefits

1. **Unified Reporting**: All topology data in one place
2. **Persistent Cache**: Results survive across sessions
3. **Report Panel**: Professional summary view
4. **Export/Print**: Share results with colleagues
5. **Reusable Data**: Metadata can be processed by other tools

---

## 🎯 Summary

**Data Flow**:
```
Analyzers → Aggregator → Metadata File → Report Panel → Exported Report
```

**File Products**:
- `.topology.json` - Machine-readable metadata
- `.html` - Web viewable report
- `.pdf` - Printable document

**User Experience**:
- Analyze model → See summary in Report Panel → Export/Print
- All topology data organized and accessible
- Professional reports ready to share

